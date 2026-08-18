"""Harvest remote-first job IDs from LinkedIn search, then pull full JDs via Voyager."""
import json, re, time, html
from playwright.sync_api import sync_playwright
from li import attach

GEO_INDIA = "102713980"
QUERIES = [
    "Digital Transformation", "Business Transformation Consultant",
    "Intelligent Automation", "Insurance Operations", "AI Transformation",
]
# f_WT=2 -> Remote only.  sortBy=DD -> most recent.
def url(q):
    return ("https://www.linkedin.com/jobs/search/?keywords=" + q.replace(" ", "%20")
            + "&geoId=" + GEO_INDIA + "&f_WT=2&sortBy=DD")

HARVEST = """() => {
  const ids = new Set();
  document.querySelectorAll('[data-occludable-job-id]').forEach(e=>ids.add(e.getAttribute('data-occludable-job-id')));
  document.querySelectorAll('a[href*="/jobs/view/"]').forEach(a=>{
    const m=(a.getAttribute('href')||'').match(/\/jobs\/view\/(\d+)/); if(m) ids.add(m[1]);
  });
  return [...ids];
}"""

def scroll_list(pg):
    ids = set()
    for i in range(8):
        ids.update(pg.evaluate(HARVEST))
        pg.evaluate("""() => {
          const sel = ['.jobs-search-results-list','.scaffold-layout__list-detail-inner',
                       '.scaffold-layout__list','div[class*="jobs-search-results-list"]'];
          for (const s of sel) { const el=document.querySelector(s);
            if (el && el.scrollHeight > el.clientHeight) { el.scrollTop += el.clientHeight*0.85; return; } }
          window.scrollBy(0, window.innerHeight*0.85);
        }""")
        pg.wait_for_timeout(900)
    ids.update(pg.evaluate(HARVEST))
    return ids

VOY = """async ([job, csrf]) => {
  const u='/voyager/api/jobs/jobPostings/'+job+
    '?decorationId=com.linkedin.voyager.deco.jobs.web.shared.WebFullJobPosting-65';
  const r=await fetch(u,{headers:{'csrf-token':csrf,'accept':'application/json'}});
  if(!r.ok) return {status:r.status};
  return {status:200, body: await r.json()};
}"""

def strip(t):
    t = re.sub(r'<[^>]+>', ' ', t or '')
    return re.sub(r'[ \t]+', ' ', html.unescape(t)).strip()

with sync_playwright() as p:
    br, pg = attach(p)
    csrf = [c for c in pg.context.cookies() if c["name"]=="JSESSIONID"][0]["value"].strip('"')

    ids = {}
    for q in QUERIES:
        pg.goto(url(q), wait_until="domcontentloaded")
        pg.wait_for_timeout(2600)
        got = scroll_list(pg)
        for i in got: ids.setdefault(i, q)
        print("[search] %-38s -> %3d ids (total %d)" % (q, len(got), len(ids)), flush=True)
        time.sleep(1.2)

    print("\nfetching JDs for %d unique jobs...\n" % len(ids), flush=True)
    jobs = []
    for n, (jid, q) in enumerate(ids.items(), 1):
        try:
            r = pg.evaluate(VOY, [jid, csrf])
        except Exception as e:
            print("  !", jid, e); continue
        if r.get("status") != 200:
            print("  ! %s http %s" % (jid, r.get("status"))); continue
        b = r["body"]
        cd = b.get("companyDetails", {})
        cd = cd.get("com.linkedin.voyager.deco.jobs.web.shared.WebJobPostingCompany", cd)
        comp = (cd.get("companyResolutionResult") or {}).get("name") or cd.get("companyName") or "?"
        am = b.get("applyMethod", {}) or {}
        easy = "com.linkedin.voyager.jobs.ComplexOnsiteApply" in am or "OnsiteApply" in str(list(am.keys()))
        jobs.append({
            "id": jid, "query": q,
            "title": b.get("title"), "company": comp,
            "location": b.get("formattedLocation"),
            "workplace": b.get("workRemoteAllowed"),
            "easy_apply": easy,
            "apply_keys": list(am.keys()),
            "closed": bool(b.get("closedAt")),
            "applies": b.get("applies"), "views": b.get("views"),
            "jd": strip((b.get("description") or {}).get("text")),
        })
        if n % 10 == 0: print("  ..%d/%d" % (n, len(ids)), flush=True)
        time.sleep(0.35)

    with open("jobs_raw.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=1, ensure_ascii=False)
    print("\nsaved %d jobs -> jobs_raw.json" % len(jobs))
    rem = [j for j in jobs if j["workplace"]]
    print("remote-flagged: %d | easy-apply: %d | remote+easy: %d"
          % (len(rem), sum(1 for j in jobs if j["easy_apply"]),
             sum(1 for j in rem if j["easy_apply"])))
