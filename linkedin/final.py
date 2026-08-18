import json, os
V = json.load(open("verified.json", encoding="utf-8"))
man = {m["id"]: m for m in json.load(open("manifest.json", encoding="utf-8"))}
OUT = r"c:\Users\Charlie AI3\Downloads\Resume Bot\output\applications"

REASON = {
 "4378716652": "Blocked - CoverGo asks for the brand/model/RAM/SSD/OS of your computer. Not guessed.",
 "4452555748": "Blocked - asks years of experience in AI Strategy & Roadmap and in AI Governance separately. Your dedicated Agentic AI role runs 04/2026-present, so '8' would be false. Need your figure.",
 "4452932291": "Skipped - JD was near-empty (aligner score 2/100), nothing to tailor against.",
 "4451625864": "Part-completed - a draft is open on LinkedIn; its 'Continue' control is not a clickable button, so it needs one manual click.",
 "4455297498": "External ATS - Embrace routes off LinkedIn, cannot be auto-submitted. Pack is ready.",
 "4443232408": "External ATS - NTT DATA routes off LinkedIn. Pack is ready.",
}

applied = [v for v in V if v["applied"]]
pending = [v for v in V if not v["applied"]]

L = []
L.append("LINKEDIN APPLICATIONS - ANOOP SHEKHAR")
L.append("Run date: 18 Aug 2026")
L.append("")
L.append("APPLIED AND CONFIRMED BY LINKEDIN: %d" % len(applied))
L.append("")
for i, v in enumerate(applied, 1):
    m = man[v["id"]]
    L.append("%2d. %s" % (i, v["company"]))
    L.append("    Role      : %s" % v["title"])
    L.append("    CV sent   : %s" % os.path.basename(v["resume"]))
    L.append("    Match     : %s/100 (%s)" % (m["score"], m["rating"]))
    L.append("    Job link  : https://www.linkedin.com/jobs/view/%s/" % v["id"])
    L.append("    Folder    : %s" % os.path.basename(m["dir"]))
    L.append("")
L.append("-" * 60)
L.append("NOT APPLIED: %d" % len(pending))
L.append("")
for v in pending:
    m = man[v["id"]]
    L.append("  %s - %s" % (v["company"], v["title"]))
    L.append("     %s" % REASON.get(v["id"], "Not submitted."))
    L.append("     Tailored pack ready: %s" % os.path.basename(m["dir"]))
    L.append("")
L.append("-" * 60)
L.append("WHAT WAS SENT")
L.append("")
L.append("Each application used a CV re-tailored to that job description by the")
L.append("Resume Bot: bullets and projects re-ranked against the JD, and wording")
L.append("swapped to the JD's own vocabulary. Nothing was invented - the tailoring")
L.append("only re-words and re-orders claims already in profile.py.")
L.append("")
L.append("Also filled per application: LinkedIn Headline, Summary, and a tailored")
L.append("cover letter in the application's cover-letter box.")
L.append("")
# Screening answers are read from answers.json (gitignored - holds salary data),
# so no personal figures are hardcoded in this file.
try:
    _ans = json.load(open("answers.json", encoding="utf-8"))
except Exception:
    try:
        _ans = json.load(open(os.path.join(os.path.dirname(OUT), "answers.json"),
                              encoding="utf-8"))
    except Exception:
        _ans = {}
_used = [(k.split("|")[0], v) for k, v in _ans.items() if str(v).strip()]
if _used:
    L.append("Screening answers used (from answers.json):")
    for k, v in _used:
        v = str(v)
        L.append("  - %s: %s" % (k, v if len(v) < 90 else v[:87] + "..."))
    L.append("")
_blank = [k.split("|")[0] for k, v in _ans.items() if not str(v).strip()]
if _blank:
    L.append("Left deliberately unanswered (would not be truthful to guess):")
    for k in _blank:
        L.append("  - %s" % k)
L.append("")
L.append("All CVs, cover letters, JDs and match reports:")
L.append(OUT)
L.append("")
L.append("NOTE: a stray 'Anoop_Shekhar_Resume.pdf' from the first test upload is in")
L.append("your LinkedIn resume list - safe to delete.")

txt = "\n".join(L)
open(os.path.join(OUT, "APPLICATIONS_SUMMARY.txt"), "w", encoding="utf-8").write(txt)
open("email_body.txt", "w", encoding="utf-8").write(txt)
print(txt)
