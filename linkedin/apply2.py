"""LinkedIn Easy Apply driver.

Fills ONLY content derived from profile.py / the bot's tailored output:
  phone, email, headline, summary, cover letter, and the JD-tailored resume PDF.
Any required screening question that cannot be answered from that material is
reported as a blocker - never guessed. Submits only when --submit is passed.
"""
import json, os, re, sys, time
from playwright.sync_api import sync_playwright
from li import attach

# Phone comes from the profile, not a second copy of it.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "source"))
import profile as _P

def _phone():
    for c in _P.CONTACT:
        digits = re.sub(r"\D", "", c)
        if len(digits) >= 10:
            return digits[-10:]          # national number, LinkedIn holds the country code
    raise SystemExit("no phone number found in profile.CONTACT")

PHONE = _phone()
JS = open("dump2.js", encoding="utf-8").read()
CHECKED = open("checked.js", encoding="utf-8").read()
RADIOS  = open("radios.js", encoding="utf-8").read()

# User-supplied answers to screening questions: {regex: answer}. Nothing is
# invented - an empty/absent answer leaves the application blocked.
try:
    ANSWERS = {k: v for k, v in
               json.load(open("answers.json", encoding="utf-8")).items() if str(v).strip()}
except Exception:
    ANSWERS = {}


def sel_id(i):
    """Attribute selector - LinkedIn ids contain non-CSS chars like « r8 »."""
    return '[id="%s"]' % str(i).replace('"', '\\"')


def answer_for(label):
    for pat, val in ANSWERS.items():
        if re.search(pat, label, re.I):
            return str(val)
    return None

# Near-empty JD (aligner score 2) - not enough signal to tailor against.
EXCLUDE = {"4452932291"}


def selected_resume(pg):
    """Labels of the currently-checked radios, so we can prove OUR pdf is chosen."""
    try:
        return pg.evaluate(CHECKED)
    except Exception:
        return []

def modal(pg):
    """The Easy Apply dialog. Scoping matters: the job page has a carousel arrow
    with aria-label="Next" that otherwise steals the click."""
    d = pg.locator('dialog[data-testid="dialog"], dialog[open], [role="dialog"]')
    return d.last if d.count() else pg


def click(pg, pattern, timeout=4000):
    loc = modal(pg).get_by_role("button", name=re.compile(pattern, re.I)).first
    try:
        loc.wait_for(state="visible", timeout=timeout)
    except Exception:
        return False
    loc.click(); return True

def fill_known(pg, m, uploaded):
    """Fill everything we can legitimately source. Returns updated `uploaded`."""
    d = pg.evaluate(JS)
    tel = pg.locator("input[type=tel]")
    if tel.count() and not tel.first.input_value().strip():
        tel.first.fill(PHONE); pg.wait_for_timeout(900)

    # resume upload (button reveals a file chooser; no file input exists until then)
    if not uploaded and any(re.search(r"upload resume", b, re.I) for b in d["buttons"]):
        try:
            with pg.expect_file_chooser(timeout=8000) as fc:
                pg.get_by_role("button", name=re.compile(r"upload resume", re.I)).first.click()
            fc.value.set_files(m["resume"])
            pg.wait_for_timeout(4000); uploaded = True
        except Exception as e:
            print("      upload failed: %s" % str(e)[:80])

    for f in d["fields"]:
        if not f["visible"] or f["value"].strip() or f["type"] in ("radio", "checkbox", "file"):
            continue
        lab = f["label"].lower()
        val = None
        if re.search(r"^headline", lab):            val = m["headline_text"]
        elif re.search(r"^summary", lab):           val = m["summary_text"]
        elif re.search(r"cover letter", lab):       val = m["cover_text"]
        else:                                       val = answer_for(f["label"])
        if val and f["type"] == "select-one" and f.get("opts"):
            match = next((o for o in f["opts"] if val.lower() in o.lower()), None)
            if match:
                try:
                    pg.select_option(sel_id(f["id"]), label=match)
                    print("      selected %-14s = %s" % (f["label"][:14], match))
                except Exception:
                    pass
            continue
        if not val or not f["id"]:
            continue
        try:
            pg.locator(sel_id(f["id"])).fill(val)
            print("      filled %-14s (%d chars)" % (f["label"][:14], len(val)))
            pg.wait_for_timeout(700)
        except Exception:
            try:
                pg.get_by_label(f["label"], exact=False).first.fill(val)
                print("      filled %s via label" % f["label"][:20])
            except Exception as e:
                print("      could not fill %s: %s" % (f["label"][:20], str(e)[:50]))
    return uploaded

def dismiss(pg):
    if click(pg, r"^Dismiss$", 2500):
        pg.wait_for_timeout(1200)
        click(pg, r"^Discard$", 2500)
        pg.wait_for_timeout(1200)

def run(pg, m, allow_submit):
    jid = m["id"]
    pg.goto("https://www.linkedin.com/jobs/view/%s/" % jid, wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    # "Continue" appears instead of "Easy Apply" when a draft is already in progress.
    if not (click(pg, r"Easy Apply", 6000) or click(pg, r"^Continue$", 3000)):
        return {"status": "no_easy_apply"}
    pg.wait_for_timeout(3200)

    uploaded, pages, blockers = False, [], []
    resume_pick = ""
    for step in range(1, 12):
        uploaded = fill_known(pg, m, uploaded)
        # radio-group questions (Yes/No etc.) - these blocked pages silently before
        for g in pg.evaluate(RADIOS):
            if g["checked"] or not g["question"]:
                continue
            want = answer_for(g["question"])
            if not want:
                continue
            opt = next((o for o in g["options"]
                        if o["label"] and want.lower() in o["label"].lower()), None)
            if opt and opt["id"]:
                try:
                    pg.locator(sel_id(opt["id"])).check(force=True)
                    print("      radio %-30s -> %s" % (g["question"][:30], opt["label"][:20]))
                    pg.wait_for_timeout(600)
                except Exception:
                    pass

        # the resume radios only exist on the resume page - capture the choice there
        for lab in selected_resume(pg):
            if ".pdf" in lab.lower() or ".docx" in lab.lower():
                resume_pick = lab
                break

        d = pg.evaluate(JS)
        unanswered_radios = [g["question"] for g in pg.evaluate(RADIOS)
                             if not g["checked"] and g["question"]]
        miss = [f for f in d["fields"]
                if f["required"] and not f["value"].strip() and f["visible"]
                and f["type"] not in ("file", "checkbox", "radio") and f["label"].strip()]
        pages.append({"step": step, "page": d["step"],
                      "fields": [(f["label"][:70], f["type"], f["required"],
                                  (f["value"][:40] or ""))
                                 for f in d["fields"] if f["label"].strip()]})
        print("    step %-2d page %-4s fields=%-3d missing=%d resume=%s"
              % (step, d["step"], len(d["fields"]), len(miss), "Y" if uploaded else "-"))
        if unanswered_radios:
            for q in unanswered_radios:
                print("       ?? CANNOT ANSWER (choice): %s" % q[:85])
                blockers.append(q[:120])
        if miss or unanswered_radios:
            for f in miss:
                print("       ?? CANNOT ANSWER: %s" % f["label"][:85])
                blockers.append(f["label"][:120])
            dismiss(pg)
            return {"status": "blocked", "pages": pages, "blockers": blockers,
                    "uploaded": uploaded}

        if modal(pg).get_by_role("button",
                                 name=re.compile(r"^Submit application$", re.I)).count():
            if not allow_submit:
                dismiss(pg)
                return {"status": "ready_to_submit", "pages": pages, "uploaded": uploaded}
            import os
            want = os.path.basename(m["resume"])
            stem = want[:38]
            review_txt = pg.inner_text("body")[:6000]
            if stem not in resume_pick and stem not in review_txt:
                print("       !! cannot confirm our resume is attached "
                      "(picked=%r)" % resume_pick[:70])
                dismiss(pg)
                return {"status": "resume_mismatch", "pages": pages,
                        "uploaded": uploaded, "selected": resume_pick, "wanted": want}
            print("       verified resume: %s" % resume_pick[:60] or want)
            click(pg, r"^Submit application$", 5000)
            pg.wait_for_timeout(4500)
            body = pg.inner_text("body")[:2500]
            ok = bool(re.search(r"application was sent|Your application was sent"
                                r"|Application sent", body, re.I))
            # close the post-apply modal if present
            click(pg, r"^(Done|Dismiss|Not now|No thanks)$", 3000)
            return {"status": "submitted" if ok else "submit_unconfirmed",
                    "pages": pages, "uploaded": uploaded, "confirm": body[:200]}

        before = d["step"]
        if not (click(pg, r"^Next$", 4000) or click(pg, r"^Review$", 4000)):
            dismiss(pg)
            return {"status": "stuck", "pages": pages, "uploaded": uploaded,
                    "buttons": d["buttons"][:6]}
        pg.wait_for_timeout(2600)
        if pg.evaluate(JS)["step"] == before and step > 1:
            print("       (page %s did not advance)" % before)
    return {"status": "loop_end", "pages": pages, "uploaded": uploaded}

if __name__ == "__main__":
    allow = "--submit" in sys.argv
    only = [a for a in sys.argv[1:] if a.isdigit()]
    man = [m for m in json.load(open("manifest.json", encoding="utf-8"))
           if m["easy"] and m["id"] not in EXCLUDE and (not only or m["id"] in only)]
    print("MODE: %s | jobs: %d\n" % ("SUBMIT" if allow else "DRY RUN", len(man)))
    out = []
    with sync_playwright() as p:
        br, pg = attach(p)
        for m in man:
            print("[%s] %s @ %s" % (m["id"], m["title"][:48], m["company"][:26]))
            try:
                r = run(pg, m, allow)
            except Exception as e:
                r = {"status": "error", "err": str(e)[:200]}
                try: dismiss(pg)
                except Exception: pass
            r.update({k: m[k] for k in ("id", "title", "company", "resume", "cover",
                                        "score", "sim", "dir")})
            print("    => %s\n" % r["status"])
            out.append(r); time.sleep(2)
    json.dump(out, open("apply_%s.json" % ("submit" if allow else "dry"), "w",
                        encoding="utf-8"), indent=1, ensure_ascii=False)
    from collections import Counter
    print("SUMMARY:", dict(Counter(r["status"] for r in out)))
