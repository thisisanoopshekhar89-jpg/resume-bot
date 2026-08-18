"""Add plain-text headline / summary / cover-letter to every application pack."""
import json, os, re, sys
sys.path.insert(0, r"c:\Users\Charlie AI3\Downloads\Resume Bot\source")
import aligner, coverletter

def plain(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    for a, b in (("&amp;", "&"), ("&mdash;", "-"), ("&nbsp;", " "),
                 ("&lt;", "<"), ("&gt;", ">"), ("&#39;", "'")):
        s = s.replace(a, b)
    return re.sub(r"[ \t]+", " ", s).strip()

jobs = {j["id"]: j for j in json.load(open("jobs_raw.json", encoding="utf-8"))}
man = json.load(open("manifest.json", encoding="utf-8"))

for m in man:
    j = jobs[m["id"]]
    tailored, rep = aligner.align(j["jd"])
    cl = coverletter.build(rep, company=j["company"], role=j["title"])
    head = plain(tailored["role"])
    summ = plain(tailored["summary"])
    body = "\n\n".join(plain(p) for p in cl["paragraphs"])
    cover_full = "%s\n\n%s\n\n%s\n%s" % (plain(cl["greeting"]), body,
                                        plain(cl["signoff"]), plain(cl["name"]))
    m["headline_text"] = head[:127]          # LinkedIn Headline cap is 127 chars
    m["summary_text"]  = summ
    m["cover_text"]    = cover_full
    for fn, txt in (("headline.txt", head), ("summary.txt", summ),
                    ("cover_letter.txt", cover_full)):
        open(os.path.join(m["dir"], fn), "w", encoding="utf-8").write(txt)

json.dump(man, open("manifest.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
s = man[0]
print("sample pack: %s @ %s" % (s["title"], s["company"]))
print("\nHEADLINE (%d chars):\n%s" % (len(s["headline_text"]), s["headline_text"]))
print("\nSUMMARY (%d chars):\n%s" % (len(s["summary_text"]), s["summary_text"][:600]))
print("\nCOVER (%d chars):\n%s" % (len(s["cover_text"]), s["cover_text"][:500]))
print("\nupdated %d packs" % len(man))
