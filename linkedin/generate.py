"""Per-job: tailor CV via the bot, build cover letter, save the JD. No network."""
import json, os, re, sys
SRC = r"c:\Users\Charlie AI3\Downloads\Resume Bot\source"
sys.path.insert(0, SRC)
import aligner, coverletter, pdf_render

OUT = r"c:\Users\Charlie AI3\Downloads\Resume Bot\output\applications"

# Curated shortlist: genuinely adjacent to the Embrace "AI Strategy, Transformation
# & Solutions Consultant" anchor for an insurance-ops / transformation / automation
# profile. Marketing, GTM, SEO, dev and credential-mismatch roles deliberately dropped.
EASY = [
 "4440049752",  # Business Process Consultant - Ajaia AI Consultancy
 "4453032620",  # Director - Enterprise AI Transformation - Jobgether
 "4378716652",  # Senior Business Analyst - AI & Health Insurance - CoverGo
 "4452555748",  # AI Strategy Governance Lead - Integrated Wireless
 "4433007244",  # Core Insurance SME (Process Advisory) - Muller's
 "4455584787",  # Insurance Operations & Quotation Specialist - Money Maximising
 "4454890880",  # AGM - AI Delivery & Enterprise Success - Aviate
 "4445945735",  # Banking & Payments Business Consultant - Qubika
 "4452932291",  # Management Consultant - Crossing Hurdles
 "4405097509",  # Insurance Domain expert - Crossing Hurdles
 "4404760263",  # Insurance Expert - Crossing Hurdles
 "4451625864",  # Strategy Associate - Exult Global
 "4454709652",  # Remote Business Analyst - Turing
 "4455710436",  # AI Product Manager - Aviate
]
OFFSITE = [
 "4455297498",  # THE ANCHOR - Embrace Software Inc (external ATS)
 "4443232408",  # ServiceNow Enterprise/Platform Architect - NTT DATA
 "4454880832",
]

jobs = {j["id"]: j for j in json.load(open("jobs_raw.json", encoding="utf-8"))}
scored = {r["id"]: r for r in json.load(open("scored.json", encoding="utf-8"))}

def slug(s, n=40):
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]+", "_", s or "")).strip("_")[:n]

man = []
for jid in EASY + OFFSITE:
    j = jobs.get(jid)
    if not j:
        print("  ! missing", jid); continue
    tailored, rep = aligner.align(j["jd"])
    d = os.path.join(OUT, "%s__%s" % (slug(j["company"], 28), slug(j["title"], 44)))
    os.makedirs(d, exist_ok=True)

    res = os.path.join(d, "Anoop_Shekhar_Resume.pdf")
    pdf_render.render(tailored, res)
    cl = coverletter.build(rep, company=j["company"], role=j["title"])
    cov = os.path.join(d, "Anoop_Shekhar_CoverLetter.pdf")
    pdf_render.render_cover(cl, cov)

    with open(os.path.join(d, "jd.txt"), "w", encoding="utf-8") as f:
        f.write("%s\n%s\n%s\nRemote: %s | Easy Apply: %s\nhttps://www.linkedin.com/jobs/view/%s\n%s\n\n%s\n"
                % (j["title"], j["company"], j["location"], bool(j["workplace"]),
                   j["easy_apply"], jid, "-"*70, j["jd"]))
    with open(os.path.join(d, "match_report.txt"), "w", encoding="utf-8") as f:
        f.write("score %s (%s)  themes %s%%  keywords %s%%  skills %s%%\n\nMATCHED: %s\n\nGAPS (never written into the CV): %s\n\nJD-vocabulary swaps applied:\n%s\n"
                % (rep["score"], rep["rating"], rep["themes_pct"], rep["keywords_pct"],
                   rep["skills_pct"], ", ".join(rep["matched"]), ", ".join(rep["gaps"]),
                   "\n".join("  " + x for x in rep["reworded"]) or "  (none)"))
    man.append({"id": jid, "title": j["title"], "company": j["company"],
                "dir": d, "resume": res, "cover": cov,
                "easy": bool(j["easy_apply"]), "remote": bool(j["workplace"]),
                "score": rep["score"], "rating": rep["rating"],
                "sim": scored.get(jid, {}).get("sim"),
                "headline": tailored["role"].replace("&amp;", "&"),
                "swaps": len(rep["reworded"]), "gaps": rep["gaps"]})
    print("%-28s %-44s score %-3s sim %-4s swaps %-3s %s"
          % (slug(j["company"],27), slug(j["title"],43), rep["score"],
             scored.get(jid,{}).get("sim"), len(rep["reworded"]),
             "EASY" if j["easy_apply"] else "offsite"))

json.dump(man, open("manifest.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\n%d application packs -> %s" % (len(man), OUT))
