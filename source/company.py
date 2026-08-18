"""Best-effort online company lookup to personalize the cover letter.

Uses Wikipedia's public REST summary endpoint (no API key). Sends ONLY the
company name (public info). Times out fast and returns None on any failure,
so the bot still works fully offline.
"""

import json
import re
import urllib.parse
import urllib.request

_UA = 'ResumeBot/1.0 (personal cover-letter helper)'
_TIMEOUT = 4.0


def _fetch_summary(title):
    url = 'https://en.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(title)
    req = urllib.request.Request(
        url, headers={'User-Agent': _UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))


def lookup(name):
    """Return {'name','description','extract','url'} for a company, or None."""
    name = (name or '').strip()
    if len(name) < 2:
        return None
    candidates = [name]
    if not re.search('(company|inc|ltd|group|plc)', name, re.I):
        candidates.append(name + ' (company)')
    for title in candidates:
        try:
            data = _fetch_summary(title)
        except Exception:
            continue
        if not data or data.get('type') == 'disambiguation':
            continue
        extract = (data.get('extract') or '').strip()
        if not extract:
            continue
        return {
            'name': data.get('title', name),
            'description': (data.get('description') or '').strip(),
            'extract': extract,
            'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
        }
    return None


def short_descriptor(info):
    """A concise noun-phrase describing the company, capitalization preserved
    (e.g. 'Irish professional services company'), for use in an appositive."""
    if not info:
        return ''
    desc = (info.get('description') or '').strip()
    if desc and len(desc) <= 90:
        return desc
    m = re.split(r'(?<=[.!?])\s', info.get('extract', ''))
    if m:
        return m[0].strip()
    return ''
