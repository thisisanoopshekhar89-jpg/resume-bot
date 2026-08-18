"""Score every harvested JD with the bot's own aligner + similarity to the Embrace anchor."""
import json, math, sys, re
sys.path.insert(0, r"c:\Users\Charlie AI3\Downloads\Resume Bot\source")
import aligner

ANCHOR = "4455297498"
jobs = json.load(open("jobs_raw.json", encoding="utf-8"))
by_id = {j["id"]: j for j in jobs}

def kw(jd):
    return set(aligner.jd_significant_keywords(aligner.normalize(jd)))

anchor_kw = kw(by_id[ANCHOR]["jd"])
print("anchor: %s @ %s" % (by_id[ANCHOR]["title"], by_id[ANCHOR]["company"]))
print("anchor keywords: %d\n" % len(anchor_kw))

# Titles that are clearly not this profile, regardless of keyword overlap.
BAD_TITLE = re.compile(
    r"\b(intern|trainee|fresher|sales (rep|executive|manager)|business development|"
    r"recruiter|talent acquisition|nurse|teacher|tutor|content writer|copywriter|"
    r"graphic design|video edit|customer (support|service) (rep|associate)|"
    r"telecall|telesales|field sales|insurance agent|advisor sales)\b", re.I)

rows = []
for j in jobs:
    if j["closed"] or len(j["jd"]) < 300:
        continue
    tailored, rep = aligner.align(j["jd"])
    k = kw(j["jd"])
    inter = len(k & anchor_kw)
    sim = round(100 * inter / math.sqrt(max(1, len(k)) * max(1, len(anchor_kw))))
    rows.append({
        "id": j["id"], "title": j["title"], "company": j["company"],
        "location": j["location"], "remote": bool(j["workplace"]),
        "easy": bool(j["easy_apply"]), "applies": j["applies"],
        "bot": rep["score"], "rating": rep["rating"], "sim": sim,
        "themes": rep["themes_pct"], "kw": rep["keywords_pct"],
        "matched": rep["matched"], "gaps": rep["gaps"],
        "bad_title": bool(BAD_TITLE.search(j["title"] or "")),
    })

# Rank: similarity to the anchor role dominates, bot score breaks ties.
for r in rows:
    r["rank"] = round(0.6 * r["sim"] + 0.4 * r["bot"], 1)
rows.sort(key=lambda r: -r["rank"])
json.dump(rows, open("scored.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

def show(label, sel):
    print("\n=== %s (%d) ===" % (label, len(sel)))
    print("%-5s %-6s %-5s %-4s %-46s %-26s %-5s %-5s" %
          ("rank", "sim", "bot", "easy", "title", "company", "rem", "appl"))
    for r in sel:
        print("%-5s %-6s %-5s %-4s %-46s %-26s %-5s %-5s" % (
            r["rank"], r["sim"], r["bot"], "Y" if r["easy"] else "-",
            (r["title"] or "")[:45], (r["company"] or "")[:25],
            "Y" if r["remote"] else "-", r["applies"]))

good = [r for r in rows if not r["bad_title"]]
show("TOP 20 overall", good[:20])
show("REMOTE + EASY APPLY, top 15", [r for r in good if r["remote"] and r["easy"]][:15])
print("\ntotals: scored %d | remote %d | remote+easy %d | filtered-out titles %d"
      % (len(rows), sum(1 for r in rows if r["remote"]),
         sum(1 for r in rows if r["remote"] and r["easy"]),
         sum(1 for r in rows if r["bad_title"])))
