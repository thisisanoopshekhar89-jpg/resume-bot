"""Offline keyword-matching aligner.

Given a job description (plain text) and the master profile, produce a
'tailored' profile:
  * headline rebuilt from matched themes
  * skills within each category floated so JD-matched ones lead (and bolded)
  * categories re-ordered by number of matches
  * bullets within each job re-ranked by JD relevance (stable, all kept)
  * a coverage report: which themes the JD wants that the profile has / lacks
"""

import html
import re

import profile as P

_TAG = re.compile('<[^>]+>')

# How many projects the resume shows, highest JD-relevance first.
# Set to a large number (or len(P.PROJECTS)) to show every project.
MAX_PROJECTS = 4
ALIASES = {'bpm': ['bpm', 'business process management', 'business process re'],
 'business process management': ['bpm',
                                 'business process re-engineering',
                                 'business process reengineering'],
 'lean six sigma': ['lean six sigma',
                    'six sigma',
                    'dmaic',
                    'process excellence',
                    'continuous improvement',
                    'kaizen',
                    'process improvement'],
 'value stream': ['value stream', 'value-stream', 'vsm'],
 'customer journey': ['customer journey', 'journey mapping', 'cx mapping'],
 'balanced scorecard': ['balanced scorecard',
                        'balance score card',
                        'scorecard',
                        'kpi',
                        'kpis',
                        'metrics'],
 'transformation': ['transformation',
                    'digital transformation',
                    'process transformation',
                    'modernization'],
 'roadmap': ['roadmap', 'target operating model', 'operating model'],
 'raci': ['raci', 'responsibility matrix', 'operating model'],
 'sop': ['sop', 'standard operating', 'standardization', 'governance', 'documentation'],
 'change management': ['change management', 'change mindset', 'stakeholder buy', 'adoption'],
 'process study': ['process study',
                   'process mapping',
                   'process discovery',
                   'as-is',
                   'to-be',
                   'gap analysis'],
 'rpa': ['rpa', 'robotic process', 'uipath', 'automation anywhere', 'blue prism', 'automation'],
 'ai/ml': ['ai/ml', 'machine learning', 'cognition', 'ml', 'deep learning', 'predictive'],
 'cognition': ['cognition', 'ai/ml', 'machine learning', 'cognitive'],
 'rag': ['rag', 'retrieval-augmented', 'retrieval augmented', 'vector', 'embeddings'],
 'llm': ['llm', 'large language model', 'generative ai', 'genai', 'gen ai', 'prompt'],
 'agentic': ['agentic', 'generative ai', 'genai', 'ai agent', 'autonomous agent'],
 'playwright': ['playwright', 'browser automation', 'selenium', 'web automation'],
 'n8n': ['n8n', 'orchestration', 'workflow automation', 'zapier', 'make.com', 'power automate'],
 'workflow automation': ['workflow automation',
                         'process automation',
                         'workflow',
                         'orchestration'],
 'power bi': ['power bi',
              'powerbi',
              'business intelligence',
              'tableau',
              'looker',
              'dashboard',
              'dashboards'],
 'business intelligence': ['business intelligence',
                           'analytics',
                           'data analysis',
                           'reporting',
                           'insights'],
 'competitive intelligence': ['competitive intelligence',
                              'market analysis',
                              'market research',
                              'benchmarking'],
 'data-driven': ['data-driven', 'data driven', 'data-informed', 'decision making'],
 'sql': ['sql', 'database', 'queries'],
 'rest api': ['api', 'rest api', 'apis', 'integration', 'webhook', 'webhooks'],
 'python': ['python'],
 'flask': ['flask', 'backend', 'web app', 'webapp'],
 'google apps script': ['google apps script',
                        'apps script',
                        'google workspace',
                        'gmail api',
                        'google sheets'],
 'chrome extension': ['chrome extension', 'browser extension'],
 'beautifulsoup': ['beautifulsoup', 'web scraping', 'scraping', 'crawler'],
 'powershell': ['powershell', 'shell scripting', 'scripting'],
 'git': ['git', 'github', 'version control', 'ci/cd'],
 'google ads': ['google ads', 'google adwords', 'adwords', 'sem', 'ppc'],
 'underwriting': ['underwriting', 'underwrite', 'risk assessment', 'pricing'],
 'claims': ['claims', 'claim', 'fnol', 'settlement'],
 'insurance': ['insurance', 'insurer', 'policy', 'gwp', 'premium', 'broker', 'brokerage'],
 'operations management': ['operations management', 'operational', 'service delivery'],
 'renewals': ['renewal', 'renewals', 'policy issuance', 'client lifecycle'],
 'compliance': ['compliance', 'audit', 'regulatory', 'governance', 'kyc'],
 'stakeholder': ['stakeholder', 'cxo', 'c-suite', 'senior leadership', 'client-facing'],
 'business development': ['business development', 'sales', 'lead generation', 'consultative']}

IMPORTANT_TERMS = [('Value Stream Mapping', ['value stream', 'vsm']),
 ('Customer Journey Mapping', ['customer journey', 'journey mapping']),
 ('End-to-End Process Transformation',
  ['process transformation', 'end-to-end', 'end to end', 'digital transformation']),
 ('Transformation Roadmap', ['roadmap', 'target operating model', 'operating model']),
 ('Process Study / Redesign',
  ['process study',
   'reengineering',
   're-engineering',
   'redesign',
   'process mapping',
   'gap analysis']),
 ('RPA', ['rpa', 'robotic process', 'uipath', 'automation anywhere', 'blue prism']),
 ('Cognition (AI/ML)', ['cognition', 'ai/ml', 'machine learning', 'deep learning']),
 ('Generative AI / LLM', ['generative ai', 'genai', 'gen ai', 'llm', 'large language model']),
 ('BPM', ['bpm', 'business process management']),
 ('RACI Matrix', ['raci', 'responsibility matrix']),
 ('Balanced Scorecard / KPIs',
  ['balanced scorecard', 'balance score card', 'scorecard', 'kpi', 'metrics']),
 ('Workflow Automation',
  ['workflow automation', 'process automation', 'orchestration', 'power automate', 'zapier']),
 ('Underwriting (UW)', ['underwriting', 'underwrite', 'risk assessment']),
 ('Claims Management', ['claims', 'fnol', 'settlement']),
 ('Policy / Client Lifecycle', ['policy issuance', 'renewal', 'client lifecycle']),
 ('ERP', ['erp', 'sap', 'oracle erp', 'workday']),
 ('Insurance Domain', ['insurance', 'insurer', 'broker', 'premium', 'gwp']),
 ('Analytics / BI', ['analytics', 'business intelligence', 'power bi', 'tableau', 'dashboard']),
 ('Data / SQL', ['sql', 'database', 'data engineering']),
 ('Python / Development', ['python', 'flask', 'api', 'rest api']),
 ('Competitive Intelligence', ['competitive intelligence', 'market analysis', 'benchmarking']),
 ('Lean Six Sigma',
  ['six sigma', 'dmaic', 'process excellence', 'continuous improvement', 'kaizen']),
 ('Compliance / Audit', ['compliance', 'audit', 'regulatory', 'kyc']),
 ('Stakeholder / CXO', ['cxo', 'stakeholder', 'c-suite', 'senior leadership']),
 ('Change Management', ['change management', 'change mindset', 'adoption']),
 ('Team Leadership',
  ['high-performance team',
   'team management',
   'manage a team',
   'leading a team',
   'high performance team',
   'people management']),
 ('Large-scale / Global Delivery',
  ['global client', 'large scale', 'large-scale', 'mid/large', 'enterprise-wide'])]

SUMMARY_PHRASE = {'Value Stream Mapping': 'value stream mapping',
 'Customer Journey Mapping': 'customer journey mapping',
 'End-to-End Process Transformation': 'end-to-end process transformation',
 'Transformation Roadmap': 'automation and transformation roadmaps',
 'Process Study / Redesign': 'process study and redesign',
 'RPA': 'RPA and workflow automation',
 'Cognition (AI/ML)': 'Cognition (AI/ML)',
 'Generative AI / LLM': 'Agentic AI, LLM and RAG solutions',
 'BPM': 'BPM-led platform integration',
 'RACI Matrix': 'RACI-based delivery governance',
 'Balanced Scorecard / KPIs': 'Balanced-Scorecard KPI metrics',
 'Workflow Automation': 'workflow automation and orchestration',
 'Underwriting (UW)': 'underwriting across upstream and downstream processes',
 'Claims Management': 'claims and policy documentation workflows',
 'Policy / Client Lifecycle': 'policy servicing and client-lifecycle management',
 'Insurance Domain': 'insurance operations',
 'Analytics / BI': 'analytics and Power BI reporting',
 'Data / SQL': 'structured data processing',
 'Python / Development': 'Python, Flask and REST API development',
 'Competitive Intelligence': 'competitive intelligence and market analysis',
 'Lean Six Sigma': 'Lean Six Sigma (DMAIC) process excellence',
 'Compliance / Audit': 'compliance and audit-ready workflows',
 'Stakeholder / CXO': 'cross-functional and CXO stakeholder partnership',
 'Change Management': 'change management and stakeholder adoption'}

_STOP = {'of', 'a', 'with', 'amp', 'an', 'and', 'the', 'for', 'mdash', 'to'}

_GENERIC = {'ability',
 'across',
 'analytical',
 'based',
 'business',
 'client',
 'clients',
 'creative',
 'customer',
 'deliver',
 'delivered',
 'delivering',
 'drive',
 'driven',
 'end',
 'environment',
 'experience',
 'expertise',
 'focus',
 'focused',
 'from',
 'good',
 'have',
 'high',
 'improvement',
 'including',
 'into',
 'large',
 'lead',
 'leading',
 'level',
 'looking',
 'made',
 'make',
 'manage',
 'management',
 'must',
 'new',
 'opportunities',
 'our',
 'over',
 'people',
 'problem',
 'process',
 'processes',
 'proven',
 'record',
 'requirements',
 'resources',
 'responsibilities',
 'role',
 'scale',
 'self',
 'should',
 'skill',
 'skills',
 'solutions',
 'solving',
 'sound',
 'strong',
 'team',
 'teams',
 'that',
 'their',
 'them',
 'there',
 'they',
 'this',
 'track',
 'understanding',
 'using',
 'versed',
 'well',
 'what',
 'when',
 'where',
 'which',
 'while',
 'who',
 'will',
 'with',
 'within',
 'work',
 'working',
 'year',
 'years',
 'you',
 'your'}


# ---------------------------------------------------------------------------
# JD vocabulary adoption
# ---------------------------------------------------------------------------
# Each group holds surface forms that mean the SAME thing. When a JD uses one
# form, the resume is re-worded to that form. This never changes a claim - only
# the wording of a claim the profile already makes - so the "nothing is
# invented" guarantee is preserved while the resume speaks the JD's language
# (which is also what keyword-matching ATS filters score on).
#
# Plurals are handled by the matcher, so a group lists the singular only.
# Bare two-letter acronyms (AI, ML, BI) are deliberately absent: they occur
# inside longer names ("Agentic AI", "Power BI") and swapping them there would
# mangle the phrase.

SYNONYMS = [
    ['business process re-engineering', 'business process reengineering',
     'process re-engineering', 'process reengineering', 'process redesign'],
    ['end-to-end process transformation', 'process transformation'],
    ['digital transformation', 'digitalisation', 'digitalization'],
    ['process mapping', 'process study', 'process discovery'],
    ['gap analysis', 'as-is to-be analysis'],
    ['value stream mapping', 'value-stream mapping'],
    ['customer journey mapping', 'journey mapping', 'cx mapping'],
    ['robotic process automation', 'rpa'],
    ['business process automation', 'workflow automation', 'process automation'],
    ['workflow orchestration', 'orchestration'],
    ['generative ai', 'gen ai', 'genai'],
    ['large language model', 'llm'],
    ['retrieval-augmented generation', 'retrieval augmented generation', 'rag'],
    ['agentic ai', 'ai agent', 'autonomous agent'],
    ['key performance indicator', 'kpi'],
    ['balanced scorecard', 'balance score card'],
    ['standard operating procedure', 'sop'],
    ['responsibility assignment matrix', 'raci matrix'],
    ['lean six sigma', 'six sigma'],
    ['continuous improvement', 'process improvement'],
    ['organizational change management', 'change management'],
    ['stakeholder management', 'stakeholder engagement'],
    ['executive leadership', 'senior leadership', 'c-suite', 'cxo'],
    ['target operating model', 'operating model'],
    ['transformation roadmap', 'automation roadmap'],
    ['first notice of loss', 'fnol'],
    ['claims documentation', 'claims management', 'claims handling',
     'claims processing', 'claims administration'],
    ['policy servicing', 'policy administration', 'policy issuance',
     'policy management'],
    ['client lifecycle', 'customer lifecycle'],
    ['insurance operations management', 'insurance operations'],
    ['underwriting', 'uw'],
    ['risk assessment', 'risk evaluation', 'risk analysis'],
    ['know your customer', 'kyc'],
    ['business process management', 'bpm'],
    ['enterprise resource planning', 'erp'],
    ['restful api', 'rest api'],
    ['web scraping', 'data scraping'],
    ['browser automation', 'web automation'],
    ['data-driven', 'data driven', 'data-informed'],
    ['cross-functional', 'cross functional'],
    ['end-to-end', 'end to end'],
    ['audit-ready', 'audit ready'],
    ['gross written premium', 'gwp'],
    ['competitive intelligence', 'market intelligence'],
    ['market analysis', 'market research'],
    ['stakeholder relationship management', 'stakeholder management',
     'stakeholder engagement'],
    ['stakeholder buy-in', 'stakeholder adoption', 'user adoption'],
    ['process standardization', 'process standardisation',
     'workflow standardization', 'standardization', 'standardisation'],
    ['operational efficiency', 'process efficiency', 'operational excellence'],
    ['quality validation', 'quality assurance', 'quality control'],
    ['decision making', 'decision-making'],
    ['digitization', 'digitisation', 'digital enablement'],
    ['turnaround time', 'turnaround'],
    ['fraud prevention', 'fraud detection'],
    ['lead management', 'lead-handling', 'lead handling'],
    ['consultative sales', 'consultative selling', 'solution selling'],
    ['quote generation', 'quotation', 'quoting'],
]

# Tokens that stay upper-cased however the surrounding text is cased.
_ACRONYMS = {
    'rpa', 'bpm', 'llm', 'rag', 'kpi', 'sop', 'raci', 'erp', 'sql', 'fnol',
    'kyc', 'gwp', 'api', 'vsm', 'dmaic', 'genai', 'cx', 'rest', 'ocr', 'uw',
    'ai', 'ml', 'bi', 'crm', 'sla', 'qc', 'tat', 'seo', 'pdf', 'json',
}

# Split on HTML tags and character entities so replacements never corrupt them.
_MARKUP = re.compile(r'(<[^>]+>|&[a-zA-Z]+;|&#\d+;)')

_lex_cache = {}


def _plural(phrase):
    """English plural of the last word of a phrase ('study' -> 'studies')."""
    if phrase.endswith('y') and phrase[-2:-1] not in 'aeiou':
        return phrase[:-1] + 'ies'
    if phrase.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return phrase + 'es'
    return phrase + 's'


def _lex_pattern(lex):
    """Alternation over every surface form (singular AND plural) in the lexicon.

    Returns (pattern, variant -> (target, is_plural)). Longest form first so a
    specific phrase always beats a shorter one nested inside it.
    """
    keys = tuple(sorted(lex))
    cached = _lex_cache.get(keys)
    if cached is not None:
        return cached
    variants = {}
    for src, dst in lex.items():
        variants.setdefault(src, (dst, False))
        p = _plural(src)
        if p != src:
            variants.setdefault(p, (dst, True))
    ordered = sorted(variants, key=len, reverse=True)
    pat = re.compile(
        '(?<![A-Za-z0-9])(' + '|'.join(re.escape(k) for k in ordered) +
        ')(?![A-Za-z0-9])', re.I)
    _lex_cache[keys] = (pat, variants)
    return pat, variants


def _is_acronym(word):
    return word.lower().strip('-/(),.') in _ACRONYMS


def _recase(src, dst):
    """Render `dst` in the casing style of the text it replaces."""
    words = dst.split(' ')

    def fix(w, title):
        if _is_acronym(w):
            return w.upper()
        return (w[:1].upper() + w[1:]) if title else w

    if len(src) > 1 and src.isupper():
        # Source was written as an acronym. Shout back only if the target is
        # itself an acronym; otherwise Title Case, which reads correctly both
        # in a skills label and mid-sentence.
        if len(words) == 1 and _is_acronym(words[0]):
            return dst.upper()
        return ' '.join(fix(w, True) for w in words)

    return ' '.join(fix(w, src[:1].isupper()) for w in words)


def jd_lexicon(jd_lower):
    """Map every synonym the profile might use -> the form THIS JD uses.

    Preference goes to the form the JD repeats most; ties break toward the
    longer (more specific) phrase, which is the better ATS keyword.
    """
    lex = {}
    for group in SYNONYMS:
        found = []
        for form in group:
            n = len(re.findall(
                '(?<![a-z0-9])' + re.escape(form) + 's?(?![a-z0-9])', jd_lower))
            if n:
                found.append((n, len(form), form))
        if not found:
            continue
        found.sort(reverse=True)
        preferred = found[0][2]
        for form in group:
            if form != preferred:
                lex[form] = preferred
    return lex


def _tidy(text):
    """Clean up artefacts a swap can leave behind, e.g. 'RPA (RPA)'."""
    text = re.sub(r'\b([\w][\w /&-]{1,40}?)\s*\(\s*\1\s*\)', r'\1', text,
                  flags=re.I)
    text = re.sub(r'\b([\w][\w /&-]{2,40}?)\s+\1\b', r'\1', text, flags=re.I)
    return text


def speak_jd(text, lex, fired=None):
    """Re-word `text` into the JD's vocabulary, leaving markup untouched."""
    if not lex or not text:
        return text
    pat, variants = _lex_pattern(lex)
    segments = _MARKUP.split(text)

    def repl(m):
        src = m.group(1)
        hit = variants.get(src.lower())
        if hit is None:
            return src
        dst, is_plural = hit
        last = dst.split(' ')[-1]
        if is_plural and _is_acronym(last):
            out = _recase(src, dst) + 's'          # KPI -> KPIs, not KPIS
        elif is_plural and not last.lower().endswith('ing'):
            out = _recase(src, _plural(dst))       # gerunds stay mass nouns
        else:
            out = _recase(src, dst)
        if fired is not None and out.lower() != src.lower():
            fired.add((src.lower(), out.lower()))
        return out

    for i in range(0, len(segments), 2):
        segments[i] = _tidy(pat.sub(repl, segments[i]))
    return ''.join(segments)


def normalize(text):
    """Strip inline markup + unescape entities -> lowercase plain text."""
    return html.unescape(_TAG.sub(' ', text)).lower()


def has(term, text):
    """Word-boundary match of `term` in lowercased `text`, tolerating a plural 's'."""
    return re.search('(?<![a-z0-9])' + re.escape(term) + 's?(?![a-z0-9])', text) is not None


def skill_triggers(skill):
    """Derive lowercase match triggers for a skill string."""
    base = normalize(skill)
    core = re.sub(r'\(.*?\)', ' ', base)
    trigs = set()
    for part in re.split(r'[&/,·]|\band\b', core):
        part = part.strip()
        if not len(part) >= 4 or part in _STOP:
            continue
        trigs.add(part)
    core = core.strip()
    if len(core) >= 4:
        trigs.add(core)
    for key, al in ALIASES.items():
        if key not in base:
            continue
        trigs.update(al)
    return trigs


def skill_matches(skill, jd_lower):
    return any(has(t, jd_lower) for t in skill_triggers(skill))


def bullet_score(bullet, jd_tokens):
    """Count distinct JD tokens present in the bullet text."""
    b = normalize(bullet)
    return sum(1 for tok in jd_tokens if has(tok, b))


def jd_keyword_tokens(jd_lower):
    """Significant unigrams + bigrams from the JD for bullet ranking."""
    words = [w for w in re.findall('[a-z][a-z0-9/+-]{2,}', jd_lower) if w not in _STOP]
    toks = set(words)
    for i in range(len(words) - 1):
        toks.add(words[i] + ' ' + words[i + 1])
    return toks


def _tailored_text(tailored):
    """Full plain text of the tailored resume, for keyword-overlap scoring."""
    parts = [normalize(tailored['role']), normalize(tailored['summary'])]
    for _, items in tailored['skills']:
        parts += [normalize(s) for s, _ in items]
    for job in tailored['experience']:
        parts.append(normalize(job['title']))
        parts += [normalize(b) for b in job['bullets']]
    for t, d in tailored['projects']:
        parts.append(normalize(t + ' ' + d))
    parts += [normalize(c) for c in tailored['certs']]
    return ' '.join(parts)


def jd_significant_keywords(jd_lower):
    """Salient keywords a JD actually emphasizes, for resume keyword scoring.

    Uses repetition as the signal for importance: a term the JD mentions more than
    once is one it cares about (and one a matching resume should contain). This
    filters out one-off prose and OCR noise, so the overlap score is meaningful.
    """
    import collections
    words = [w for w in re.findall('[a-z][a-z0-9/+.-]{2,}', jd_lower)
             if w not in _STOP and w not in _GENERIC and len(w) >= 4]
    freq = collections.Counter(words)
    bigrams = collections.Counter(words[i] + ' ' + words[i + 1]
                                  for i in range(len(words) - 1))
    keys = {w for w, c in freq.items() if c >= 2}
    keys |= {b for b, c in bigrams.items() if c >= 2}

    for _, trigs in IMPORTANT_TERMS:
        for t in trigs:
            if not len(t) >= 4:
                continue
            if not has(t, jd_lower):
                continue
            keys.add(t)
    return keys


def _profile_text():
    parts = [normalize(P.SUMMARY), normalize(P.DEFAULT_ROLE)]
    for _, items in P.SKILLS:
        parts += [normalize(s) for s in items]
    for job in P.EXPERIENCE:
        parts += [normalize(b) for b in job['bullets']]
    for t, d in P.PROJECTS:
        parts.append(normalize(t + ' ' + d))
    return ' '.join(parts)


def build_headline(jd_lower, lex=None, fired=None):
    chosen = [phrase for _, trigs, phrase in P.ROLE_THEMES
              if any(has(t2, jd_lower) for t2 in trigs)]
    seen, out = set(), []
    for p in chosen:
        if p not in seen:
            seen.add(p)
            out.append(p)
        if len(out) == 3:
            break
    head = P.DEFAULT_ROLE if len(out) < 2 else '  |  '.join(out)
    return speak_jd(head, lex or {}, fired)


def align(jd_text):
    jd_lower = normalize(jd_text)
    jd_tokens = jd_keyword_tokens(jd_lower)

    # The JD's own vocabulary, applied to every piece of text we emit.
    lex = jd_lexicon(jd_lower)
    fired = set()

    tailored_skills = []
    for cat, items in P.SKILLS:
        marked = [(speak_jd(s, lex, fired), skill_matches(s, jd_lower))
                  for s in items]
        matched = [x for x in marked if x[1]]
        rest = [x for x in marked if not x[1]]
        tailored_skills.append((speak_jd(cat, lex, fired), matched + rest,
                                len(matched)))
    tailored_skills.sort(key=lambda c: c[2], reverse=True)
    skills_out = [(cat, items) for cat, items, _ in tailored_skills]

    exp_out = []
    for job in P.EXPERIENCE:
        scored = [(bullet_score(b, jd_tokens), i, b)
                  for i, b in enumerate(job['bullets'])]
        scored.sort(key=lambda x: (-x[0], x[1]))
        exp_out.append({'title': speak_jd(job['title'], lex, fired),
                        'meta': job['meta'],
                        'bullets': [speak_jd(b, lex, fired) for _, _, b in scored]})

    proj_scored = [(bullet_score(t + ' ' + d, jd_tokens), i, (t, d))
                   for i, (t, d) in enumerate(P.PROJECTS)]
    proj_scored.sort(key=lambda x: (-x[0], x[1]))
    # The section is titled "Selected ... Projects": show the ones this JD cares
    # about, not the whole back catalogue. Raise MAX_PROJECTS to show more.
    projects_out = [(speak_jd(t, lex, fired), speak_jd(d, lex, fired))
                    for _, _, (t, d) in proj_scored[:MAX_PROJECTS]]

    ptext = _profile_text()
    matched_terms, gap_terms = [], []
    for name, trigs in IMPORTANT_TERMS:
        if not any(has(t, jd_lower) for t in trigs):
            continue
        if any(has(t, ptext) for t in trigs):
            matched_terms.append(name)
        else:
            gap_terms.append(name)
    total = len(matched_terms) + len(gap_terms)
    themes_pct = round(100 * len(matched_terms) / total) if total else 0

    tailored = {
        'name': P.NAME,
        'role': build_headline(jd_lower, lex, fired),
        'summary': build_summary(jd_lower, matched_terms, lex, fired),
        'skills': skills_out,
        'experience': exp_out,
        'projects': projects_out,
        'education': P.EDUCATION,
        # Certification names are proper nouns - never re-worded.
        'certs': list(P.CERTS),
        'contact': P.CONTACT,
    }

    resume_text = _tailored_text(tailored)
    jd_keys = jd_significant_keywords(jd_lower)
    kw_hit = sorted(k for k in jd_keys if has(k, resume_text))
    kw_miss = sorted(k for k in jd_keys if k not in kw_hit)
    keywords_pct = round(100 * len(kw_hit) / len(jd_keys)) if jd_keys else 0

    n_matched_skills = sum(1 for _, items in skills_out for _, m in items if m)
    skills_pct = (min(100, round(100 * n_matched_skills / 8))
                  if n_matched_skills else 0)

    composite = round(0.5 * themes_pct + 0.35 * keywords_pct + 0.15 * skills_pct)

    report = {
        'score': composite,
        'themes_pct': themes_pct,
        'keywords_pct': keywords_pct,
        'skills_pct': skills_pct,
        'matched': matched_terms,
        'gaps': gap_terms,
        'jd_required': total,
        'kw_hit': kw_hit,
        'kw_miss': kw_miss[:12],
        'kw_total': len(jd_keys),
        'rating': _rating(composite),
        'reworded': sorted('%s -> %s' % (a, b) for a, b in fired),
    }
    return tailored, report


def master():
    """The complete master CV: every skill, project and bullet, untailored.

    No JD is involved - nothing is re-ordered, re-worded, or held back. This is
    the full record the tailored resume draws from.
    """
    tailored = {
        'name': P.NAME,
        'role': P.DEFAULT_ROLE,
        'summary': P.SUMMARY,
        'skills': [(cat, [(s, False) for s in items]) for cat, items in P.SKILLS],
        'experience': [{'title': j['title'], 'meta': j['meta'],
                        'bullets': list(j['bullets'])} for j in P.EXPERIENCE],
        'projects': list(P.PROJECTS),
        'education': P.EDUCATION,
        'certs': list(P.CERTS),
        'contact': P.CONTACT,
    }
    report = {
        'is_master': True,
        'n_skills': sum(len(i) for _, i in P.SKILLS),
        'n_projects': len(P.PROJECTS),
        'n_bullets': sum(len(j['bullets']) for j in P.EXPERIENCE),
        'n_roles': len(P.EXPERIENCE),
        'matched': [], 'gaps': [], 'reworded': [],
        'score': 0, 'themes_pct': 0, 'keywords_pct': 0, 'skills_pct': 0,
        'jd_required': 0, 'kw_hit': [], 'kw_miss': [], 'kw_total': 0,
        'rating': 'Master CV',
    }
    return tailored, report


def _join_and(items):
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + ' and ' + items[-1]


def _theme_jd_weight(name, jd_lower):
    """How strongly the JD emphasizes a theme (total trigger hits)."""
    trigs = dict(IMPORTANT_TERMS).get(name, [])
    return sum(len(re.findall('(?<![a-z0-9])' + re.escape(t) + 's?(?![a-z0-9])',
                              jd_lower)) for t in trigs)


def build_summary(jd_lower, matched_terms, lex=None, fired=None):
    """Assemble a JD-specific, truthful summary from matched themes.

    Leads with the capabilities the JD emphasizes most, phrased in the JD's own
    words. Only themes the profile genuinely covers appear; gaps are never
    included.
    """
    lex = lex or {}
    order = sorted(matched_terms, key=lambda n: -_theme_jd_weight(n, jd_lower))
    phrases, seen = [], set()
    for n in order:
        p = SUMMARY_PHRASE.get(n)
        if not p:
            continue
        p = speak_jd(p, lex, fired)
        if p.lower() in seen:
            continue
        seen.add(p.lower())
        phrases.append(p)
    phrases = phrases[:4]

    opening = ('Results-driven Business &amp; Digital Transformation professional '
               'with 8+ years across insurance operations, underwriting and '
               'intelligent automation.')
    if phrases:
        mid = (' Proven in %s &mdash; turning manual, fragmented processes into '
               'scalable, Future-Ready, Intelligent Operations.') % _join_and(phrases)
    else:
        mid = (' Skilled at running end-to-end process studies, identifying '
               'automation opportunities, and turning manual processes into '
               'scalable, Future-Ready operations.')
    creds = (' KPMG Lean Six Sigma Green Belt (GenAI / DMAIC) certified, pairing '
             'process rigor with hands-on delivery in Python, RPA and Agentic AI '
             'to drive measurable, audit-ready business outcomes.')
    # `creds` names an actual certification, so it is left exactly as issued.
    return speak_jd(opening, lex, fired) + mid + creds


def _rating(score):
    if score >= 85:
        return 'Excellent match'
    if score >= 70:
        return 'Strong match'
    if score >= 55:
        return 'Moderate match'
    return 'Partial match'
