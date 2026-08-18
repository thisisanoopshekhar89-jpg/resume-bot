"""Shared helper: attach to the already-open, already-logged-in Chrome."""
from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"

def attach(p):
    br = p.chromium.connect_over_cdp(CDP)
    pages = [pg for c in br.contexts for pg in c.pages]
    li = [pg for pg in pages if "linkedin.com" in (pg.url or "")
          and "lnkd" not in pg.url and "merchantpool" not in pg.url]
    if not li:
        raise SystemExit("No LinkedIn tab found. Open linkedin.com in the debugged Chrome.")
    return br, li[0]
