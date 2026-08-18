"""Offline, JD-tailored cover letter builder.

Weaves the strongest matched themes and real achievements from the master
profile into a standard 4-paragraph letter. No LLM; nothing invented.
build(...) returns a dict consumed by pdf_render.render_cover().
"""

import datetime

import profile as P

_PROOF = {'Value Stream Mapping': 'running end-to-end process studies and value stream mapping to surface '
                         'automation opportunities',
 'Customer Journey Mapping': 'mapping customer journeys to redesign operations around the client',
 'End-to-End Process Transformation': 'delivering end-to-end process transformation across '
                                      'insurance operations',
 'Transformation Roadmap': 'building automation and transformation roadmaps toward Future-Ready '
                           'operations',
 'RPA': 'deploying RPA and workflow automation (n8n, Python, Playwright) across insurer portals',
 'Cognition (AI/ML)': 'applying Cognition (AI/ML), Agentic AI and LLM/RAG to operational '
                      'workflows',
 'BPM': 'enabling integration across BPM, platforms and point solutions',
 'RACI Matrix': 'standardizing delivery with RACI-based processes and reusable frameworks',
 'Balanced Scorecard': 'driving Balanced-Scorecard KPI metrics and reducing process variability '
                       'and defects',
 'Underwriting (UW)': 'working hands-on across upstream and downstream underwriting processes',
 'Claims Management': 'structuring insurance documentation and compliance workflows',
 'Insurance Domain': 'eight-plus years inside insurance operations and underwriting',
 'Analytics': 'standing up analytics and Power BI reporting for operational visibility',
 'Automation / AI': 'architecting scalable automation and AI platforms',
 'Lean Six Sigma': 'applying Lean Six Sigma (DMAIC) as a KPMG-certified Green Belt',
 'Stakeholder / CXO': 'partnering with cross-functional teams and CXO stakeholders',
 'Process Study / Redesign': 'conducting process studies and redesign to remove inefficiencies'}

def _join(items):
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    return ', '.join(items[:-1]) + ' and ' + items[-1]


def build(report, company='', role='', company_info=None):
    company = (company or '').strip()
    role = (role or '').strip()
    company_disp = company if company else 'your organization'
    role_disp = role if role else 'this Business Transformation role'

    import company as company_mod
    descriptor = company_mod.short_descriptor(company_info) if company_info else ''

    matched = report.get('matched', [])
    proofs = [_PROOF[m] for m in matched if m in _PROOF][:4]

    try:
        today = datetime.date.today().strftime('%d %B %Y')
    except Exception:
        today = ''

    greeting = 'Dear Hiring Manager,'

    p1 = (f'I am writing to express my strong interest in {role_disp} at '
          f'{company_disp}. As a Business &amp; Digital Transformation professional '
          'with 8+ years across insurance operations, underwriting and intelligent '
          'automation, I was excited to see how closely the role aligns with my '
          'track record of turning manual, fragmented processes into scalable, '
          'Future-Ready operations.')
    if descriptor:
        article = 'an' if descriptor[:1].lower() in 'aeiou' else 'a'
        p1 += (f' I am especially drawn to {company_disp}, {article} {descriptor}'
               ', and to the opportunity to translate deep process expertise and '
               'automation into measurable business outcomes.')

    if proofs:
        p2 = ('Your requirements map directly to my experience &mdash; %s. At '
              'InsuranceMarket.ae I built and now manage a multi-insurer automation '
              'platform integrating five leading UAE insurers, and led sales-reporting '
              'automation for 100+ employees that eliminated roughly 333 hours of '
              'manual effort while improving accuracy and audit-readiness.') % _join(proofs)
    else:
        p2 = ('At InsuranceMarket.ae I built and now manage a multi-insurer automation '
              'platform integrating five leading UAE insurers, and led sales-reporting '
              'automation for 100+ employees that eliminated roughly 333 hours of '
              'manual effort while improving accuracy and audit-readiness.')

    p3 = ('I pair deep insurance-domain knowledge with hands-on delivery in Python, '
          'Flask, REST APIs, Playwright, n8n, RPA and Agentic AI/LLM &mdash; and, as a '
          'KPMG Lean Six Sigma Green Belt (GenAI/DMAIC), I bring the process rigor to '
          'identify opportunities, design transformation roadmaps, and govern delivery '
          'end to end with clear metrics.')
    gaps = report.get('gaps', [])
    if gaps:
        p3 += (' I am equally comfortable ramping quickly on adjacent areas such as '
               '%s, and I thrive in ambiguous, self-directed environments.') % _join(gaps[:3])

    p4 = ('I would welcome the chance to discuss how I can help %s accelerate its '
          'Intelligent Operations journey. Thank you for your time and '
          'consideration.') % company_disp

    return {
        'date': today,
        'company': company_disp,
        'role': role_disp,
        'greeting': greeting,
        'paragraphs': [p1, p2, p3, p4],
        'signoff': 'Sincerely,',
        'name': P.NAME,
        'contact': P.CONTACT,
    }
