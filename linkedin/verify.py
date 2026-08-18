"""Independently confirm which jobs LinkedIn now records as applied.

Uses the authenticated jobPostings API - applyingInfo.applied is LinkedIn's own
record, not our script's opinion of what happened.
"""
import json
from playwright.sync_api import sync_playwright
from li import attach

man = json.load(open("manifest.json", encoding="utf-8"))
VOY = """async ([job, csrf]) => {
  const u = '/voyager/api/jobs/jobPostings/' + job +
    '?decorationId=com.linkedin.voyager.deco.jobs.web.shared.WebFullJobPosting-65';
  const r = await fetch(u, {headers: {'csrf-token': csrf, 'accept': 'application/json'}});
  if (!r.ok) return {status: r.status};
  const b = await r.json();
  return {status: 200, applying: b.applyingInfo || null, closed: !!b.closedAt};
}"""

with sync_playwright() as p:
    br, pg = attach(p)
    if "linkedin.com" not in pg.url:
        pg.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        pg.wait_for_timeout(2500)
    csrf = [c for c in pg.context.cookies() if c["name"] == "JSESSIONID"][0]["value"].strip('"')
    out = []
    for m in man:
        r = pg.evaluate(VOY, [m["id"], csrf])
        ai = r.get("applying") or {}
        applied = bool(ai.get("applied"))
        out.append({**{k: m[k] for k in ("id", "title", "company", "resume", "easy")},
                    "applied": applied, "appliedAt": ai.get("appliedAt"),
                    "http": r.get("status")})
        print("%-8s %-24s %-44s %s" % ("APPLIED" if applied else "-",
                                       m["company"][:23], m["title"][:43],
                                       "" if r.get("status") == 200 else r.get("status")))
    json.dump(out, open("verified.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    n = sum(1 for x in out if x["applied"])
    print("\nLinkedIn records %d of %d as applied." % (n, len(out)))
