# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal offline tool that tailors Anoop Shekhar's resume and cover letter to a pasted job
description (JD) and scores the match. Ships as a PyInstaller one-file `.exe`; the Python
source lives in [source/](source/).

    ResumeBot.exe          the built app (rebuild from source/, see below)
    source/                the real source - edit here
    backup-original/       the pre-fix exe and HOW-TO, kept for reference
    HOW-TO.txt             end-user instructions
    output/                generated PDFs (created at runtime, next to the exe)

The source was recovered by decompiling the original `.exe` (no original source existed).
Each recovered module was verified against the bundled bytecode before any change: `profile`,
`company`, `coverletter` byte-for-byte on output, `pdf_render` by byte-identical PDFs, and
`aligner` across 54 JDs.

## Run and build

```
python source/app.py                 # dev, opens http://127.0.0.1:5057
pip install flask reportlab winsdk pyinstaller
cd source && pyinstaller --noconfirm --clean --onefile --name ResumeBot \
  --add-data "templates;templates" --collect-all winsdk app.py
```

`--collect-all winsdk` is required — OCR imports `winsdk.windows.*` lazily inside a function,
so PyInstaller cannot see it. Do **not** add `--collect-all reportlab`; it inflates the exe
from 39 MB to 55 MB for nothing.

There is no test suite. The scratch harnesses used during the rewrite (`safety.py`,
`compare.py`, `verify_aligner.py`) are not shipped; re-create them if you make deep changes —
the useful invariants are: markup balanced, entities intact, all 24 bullets kept, PDFs render.

## Architecture

Single Flask process, one POST route doing all the work.

- [source/profile.py](source/profile.py) — **the only data file.** `NAME`, `CONTACT`, `SUMMARY`,
  `DEFAULT_ROLE`, `ROLE_THEMES`, `SKILLS`, `EXPERIENCE`, `PROJECTS`, `EDUCATION`, `CERTS`.
  Everything on every document comes from here. Adding experience means editing this file.
- [source/aligner.py](source/aligner.py) — all the intelligence. `align(jd)` returns
  `(tailored, report)`; `master()` returns the untailored full record.
- [source/pdf_render.py](source/pdf_render.py) — ReportLab two-column navy layout with manual
  pagination (`_paginate` measures flowables and packs them into columns). `render()` for
  resumes and master CV, `render_cover()` for letters.
- [source/app.py](source/app.py) — routes, OCR upload handling, filename slugs.
- [source/coverletter.py](source/coverletter.py), [source/company.py](source/company.py),
  [source/ocr.py](source/ocr.py) — letter assembly, optional Wikipedia company lookup,
  Windows OCR.

### How tailoring works

Three mechanisms, in `aligner.align()`:

1. **Ranking** — bullets and projects are scored by JD-token overlap and re-ordered. All 24
   bullets are always emitted; only projects are subset (`MAX_PROJECTS = 4`, the section is
   titled "Selected ... Projects").
2. **Vocabulary adoption** — `jd_lexicon()` picks, for each `SYNONYMS` group, the surface form
   *this JD* uses; `speak_jd()` rewrites the profile's wording to it. This is the fix for the
   original complaint that every JD produced a near-identical resume.
3. **Coverage report** — `IMPORTANT_TERMS` themes the JD wants are split into matched vs gaps;
   gaps are reported but **never** written into the resume.

### Invariants — do not break these

- **Nothing is invented.** A swap only ever exchanges interchangeable wordings for a claim the
  profile already makes. `SYNONYMS` groups must contain true synonyms only — the existing
  `ALIASES` table is *not* safe for this (it groups merely-related terms like `lean six sigma`
  with `kaizen`). Gap themes must never be injected into the document.
- **Markup safety.** Bullets carry `<b>` tags and `&amp;`/`&mdash;` entities. `speak_jd()` splits
  on `_MARKUP` and rewrites only the text between tags. Never regex over the raw string.
- **No bare two-letter acronyms in `SYNONYMS`** (`ai`, `ml`, `bi`). They occur inside longer
  names ("Agentic AI", "Power BI") and swapping them mangles the phrase.
- Scoring weights are the original `0.5 * themes + 0.35 * keywords + 0.15 * skills`. The score
  is generous — opposite JDs can both read "Strong match". Left as-is deliberately; changing it
  is a product decision, not a cleanup.

## Known limitation

Vocabulary adoption can only re-word phrases the profile actually contains. A JD asking for
something phrased in a way `profile.py` never says produces no swap — the fix is to add the
wording to `SYNONYMS` (if it's a synonym of something already there) or to `profile.py` (if it's
genuinely a new claim).
