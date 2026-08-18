# LinkedIn apply pipeline

Drives an **already-logged-in** Chrome to find remote jobs, tailor a CV per JD with
the Resume Bot, and submit LinkedIn Easy Apply applications.

Nothing here invents facts. It fills only what comes from [`../source/profile.py`](../source/profile.py),
the bot's tailored output, and `answers.json`. Any required question it cannot answer
from that material blocks the application instead of guessing.

## Setup

Start Chrome with remote debugging and log into LinkedIn in that window:

```
chrome.exe --remote-debugging-port=9222
```

`pip install playwright` (the bot's own deps are already required by `source/`).

## Run order

```
python harvest.py     # remote job search (f_WT=2) -> jobs_raw.json  (full JDs via voyager API)
python score.py       # aligner.align() per JD + similarity to an anchor job -> scored.json
python generate.py    # tailored CV + cover letter + jd.txt + match report per job
python gentext.py     # plain-text headline / summary / cover letter for the form fields
python rename2.py     # name each PDF after the company (role suffix if a company repeats)
python apply2.py                 # DRY RUN - walks to Submit, never clicks it
python apply2.py --submit        # actually applies
python verify.py      # confirm against LinkedIn's own applyingInfo.applied record
python final.py       # build APPLICATIONS_SUMMARY.txt
```

Add job ids as args to limit a run: `python apply2.py --submit 4440049752`.

## answers.json

Screening answers, `{regex: answer}`, first match wins so put specific patterns first.
Copy `answers.example.json` and fill it. **Keep it out of git** — it holds salary data;
the working copy lives in the gitignored `../output/answers.json`.

An empty answer means "do not answer this" — the application stops and reports it.
That is deliberate for anything not backed by the profile.

## Verify, don't trust

`apply2.py` reports `submit_unconfirmed` when it clicks Submit but cannot match the
success text — LinkedIn's wording does not match a reasonable regex, so this is normal
and does **not** mean failure. `verify.py` is the source of truth: it reads LinkedIn's
own `applyingInfo.applied` flag.

## DOM gotchas

Scope every control to `dialog[data-testid="dialog"]` — a job-card carousel arrow also
has `aria-label="Next"` and will silently eat the click. Ids look like `«r8»`, so use
`[id="..."]` not `#id`. The resume file input only exists after clicking "Upload resume";
the resume radio list only exists on the resume page. Many question radio groups have no
`<legend>`. Dropdown options can be in the employer's language. "Continue" replaces
"Easy Apply" once a draft exists.
