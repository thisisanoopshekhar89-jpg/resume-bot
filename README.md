# Resume Bot

An offline resume and cover-letter tailoring tool. Paste a job description — or a
screenshot of one — and it regenerates a two-column PDF resume that is re-ordered,
re-emphasized, and **re-worded into the job description's own vocabulary**, then scores
the match and reports the gaps.

No API key. No LLM. No network. Runs entirely on your machine.

![Python](https://img.shields.io/badge/python-3.12-blue)
![Flask](https://img.shields.io/badge/flask-3.1-lightgrey)
![Offline](https://img.shields.io/badge/network-none-green)

---

## Why it exists

Most "resume tailoring" scripts just re-sort your bullets. The document that comes out is
word-for-word the same one every time, which is exactly what a keyword-matching ATS fails to
match — because it is scanning for *the employer's* vocabulary, not yours.

This one changes the wording:

| The JD says | Your profile says | What gets printed |
|---|---|---|
| business process re-engineering | process study | process mapping / re-engineering |
| large language model | LLM | large language model |
| claims handling | claims documentation | claims handling |
| standard operating procedure | SOP | standard operating procedure |

Same claim, the reader's words. The results panel lists every swap it made.

## The rule it will not break

**Nothing is invented.** A swap only ever exchanges interchangeable wordings for a claim the
profile already makes. It never adds a skill you do not have. Anything the JD asks for that
your profile cannot evidence is reported as a **gap** and is never written into the document.
Certification names are treated as proper nouns and are never re-worded.

## What it produces

- **Tailored resume** — ~2 pages. Every experience bullet is kept and re-ranked; the most
  JD-relevant projects and skills lead.
- **Cover letter** — assembled from the themes the JD actually matched, with an optional
  offline-tolerant company lookup.
- **Master CV** — ~3 pages, no JD applied: the complete record the tailored version draws from.

Plus a match report: theme coverage, keyword overlap, skills alignment, and the gap list.

## Run it

```bash
pip install flask reportlab winsdk
python source/app.py          # opens http://127.0.0.1:5057
```

Build a standalone Windows executable:

```bash
pip install pyinstaller
cd source
pyinstaller --noconfirm --clean --onefile --name ResumeBot \
  --add-data "templates;templates" --collect-all winsdk app.py
```

`--collect-all winsdk` is required — OCR imports `winsdk.windows.*` lazily inside a function,
so PyInstaller cannot detect it statically.

## How it works

| Module | Role |
|---|---|
| `source/profile.py` | **The only data file.** Skills, experience, projects, education, certs. |
| `source/aligner.py` | Ranking, JD vocabulary adoption, match/gap scoring. |
| `source/pdf_render.py` | ReportLab two-column layout with manual pagination. |
| `source/coverletter.py` | Letter assembly from matched themes. |
| `source/company.py` | Optional Wikipedia company lookup (the only network call; fails silent). |
| `source/ocr.py` | Windows built-in OCR for JD screenshots (Windows 10/11). |
| `source/app.py` | Flask routes. |

Three mechanisms drive the tailoring, all in `aligner.align()`:

1. **Ranking** — bullets and projects scored by JD-token overlap and re-ordered.
2. **Vocabulary adoption** — `jd_lexicon()` picks the surface form *this* JD uses from each
   `SYNONYMS` group; `speak_jd()` rewrites the profile's wording to match. Markup-safe: it
   splits on HTML tags and entities so `<b>` and `&mdash;` are never corrupted.
3. **Coverage report** — JD themes split into matched vs. gaps.

## Make it yours

Everything on every document comes from `source/profile.py`. Replace its contents with your
own and the whole tool follows. Two knobs worth knowing:

- `MAX_PROJECTS` in `aligner.py` — how many projects the tailored resume shows.
- `SYNONYMS` in `aligner.py` — add a group to teach it another way of saying something you
  already do. Groups must contain **true synonyms only**.

## Notes

- Windows 10/11 only, for the OCR path — everything else is cross-platform.
- Runs on port 5057 to stay clear of other local dev servers.
