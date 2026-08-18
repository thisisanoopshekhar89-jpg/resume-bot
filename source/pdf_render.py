"""ReportLab renderer: two-column navy resume, driven by a tailored profile dict.

render(data, out_path) where data has keys:
  name, role, summary, contact[], certs[],
  education[(title, school, year)],
  skills[(category, [(skill_text, matched_bool), ...])],
  experience[{title, meta, bullets[]}],
  projects[(title, desc)]
"""

import os

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as canvasmod
from reportlab.platypus import Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable

NAVY = HexColor('#1B3A5B')
NAVY_DEEP = HexColor('#12283F')
STEEL = HexColor('#35618E')
INK = HexColor('#24303A')
SLATE = HexColor('#5C6773')
HAIRLINE = HexColor('#C9D3DE')

_WIN = 'C:\\Windows\\Fonts'


def _reg(name, filename):
    try:
        pdfmetrics.registerFont(TTFont(name, os.path.join(_WIN, filename)))
        return True
    except Exception:
        return False


HEAD = 'Georgia' if _reg('Georgia', 'georgia.ttf') else 'Times-Roman'
BODY = 'Calibri' if _reg('Calibri', 'calibri.ttf') else 'Helvetica'
BODYB = 'CalibriB' if _reg('CalibriB', 'calibrib.ttf') else 'Helvetica-Bold'
BODYI = 'CalibriI' if _reg('CalibriI', 'calibrii.ttf') else 'Helvetica-Oblique'

# Inline <b>/<i> only resolve if the family is registered. Without this the
# <b> tags in bullets, project titles and the cover letter render flat.
try:
    pdfmetrics.registerFontFamily(BODY, normal=BODY, bold=BODYB, italic=BODYI,
                                  boldItalic=BODYB)
    pdfmetrics.registerFontFamily(HEAD, normal=HEAD, bold=HEAD, italic=HEAD,
                                  boldItalic=HEAD)
except Exception:
    pass

PW, PH = A4
BORDER = 16
LX, LW = 38, 168
DIV = 220
RX, RW = 236, 322
TOP_Y = 792
BOT_Y = 44


def _ps(name, **kw):
    base = dict(fontName=BODY, fontSize=8.6, leading=11.6, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)


ST = {
    'name': _ps('name', fontName=HEAD, fontSize=27, leading=29, textColor=NAVY_DEEP),
    'role': _ps('role', fontName=BODY, fontSize=9.5, leading=12, textColor=STEEL,
                spaceBefore=3),
    'secR': _ps('secR', fontName=HEAD, fontSize=12.5, leading=14, textColor=NAVY_DEEP),
    'secL': _ps('secL', fontName=HEAD, fontSize=11, leading=13, textColor=NAVY_DEEP),
    'body': _ps('body', alignment=TA_JUSTIFY, fontSize=8.7, leading=12),
    'bullet': _ps('bul', fontSize=8.6, leading=11.8, leftIndent=9, bulletIndent=0,
                  spaceAfter=1.5),
    'lbul': _ps('lbul', fontSize=8.2, leading=10.8, leftIndent=8, bulletIndent=0,
                spaceAfter=1.2),
    'lbulM': _ps('lbulM', fontName=BODYB, fontSize=8.2, leading=10.8, leftIndent=8,
                 bulletIndent=0, spaceAfter=1.2, textColor=NAVY_DEEP),
    'jobt': _ps('jobt', fontName=BODYB, fontSize=9.6, leading=11.8, textColor=NAVY_DEEP),
    'meta': _ps('meta', fontName=BODYI, fontSize=8.0, leading=10, textColor=SLATE),
    'contact': _ps('contact', fontSize=8.4, leading=12, textColor=INK),
    'lcat': _ps('lcat', fontName=BODYB, fontSize=8.6, leading=11, textColor=STEEL,
                spaceBefore=2),
    'edt': _ps('edt', fontName=BODYB, fontSize=8.6, leading=10.6, textColor=NAVY_DEEP),
    'eds': _ps('eds', fontName=BODY, fontSize=8.0, leading=10.2, textColor=INK),
    'edd': _ps('edd', fontName=BODYI, fontSize=7.6, leading=9.6, textColor=SLATE),
}


def _rule(color=STEEL, w=1.1, space=3):
    return HRFlowable(width='100%', thickness=w, color=color,
                      spaceBefore=space, spaceAfter=space, lineCap='round')


def _sec_R(t):
    return [Paragraph(t, ST['secR']), _rule(STEEL, 1.2, 2)]


def _sec_L(t):
    return [Paragraph(t, ST['secL']), _rule(HAIRLINE, 0.9, 2)]


def _bul(items, style):
    return [Paragraph(t, style, bulletText='\u2022') for t in items]


def _build_left(data):
    blocks = [[Paragraph(c, ST['contact']) for c in data['contact']] + [Spacer(1, 6)]]
    blocks.append(_sec_L('Skills'))
    for cat, items in data['skills']:
        blk = [Paragraph(cat, ST['lcat'])]
        for text, matched in items:
            blk.append(Paragraph(text, ST['lbulM'] if matched else ST['lbul'],
                                 bulletText='\u2022'))
        blk.append(Spacer(1, 3))
        blocks.append(blk)
    blocks.append([Spacer(1, 4)])
    blocks.append(_sec_L('Education'))
    for t, s, d in data['education']:
        blocks.append([Paragraph(t, ST['edt']), Paragraph(s, ST['eds']),
                       Paragraph(d, ST['edd']), Spacer(1, 5)])
    blocks.append([Spacer(1, 2)])
    blocks.append(_sec_L('Certifications'))
    blocks.append(_bul(data['certs'], ST['lbul']))
    return blocks


def _build_right(data):
    blocks = [[Paragraph(data['name'], ST['name']),
               Paragraph(data['role'], ST['role']), Spacer(1, 9)]]
    blocks.append(_sec_R('Summary') +
                  [Paragraph(data['summary'], ST['body']), Spacer(1, 7)])
    blocks.append(_sec_R('Professional Experience'))
    for job in data['experience']:
        blk = [Paragraph(job['title'], ST['jobt']),
               Paragraph(job['meta'], ST['meta']), Spacer(1, 2)]
        blk += _bul(job['bullets'], ST['bullet'])
        blk += [Spacer(1, 7)]
        blocks.append(blk)
    blocks.append(_sec_R('Selected Transformation Projects'))
    for t, d in data['projects']:
        blocks.append([Paragraph('<b>' + t + '</b> &mdash; ' + d, ST['bullet']),
                       Spacer(1, 4)])
    return blocks


def _measure(f, w):
    _, h = f.wrap(w, 100000)
    return h


def _paginate(blocks, w, top_y, bot_y):
    pages = [[]]
    y = top_y
    avail = top_y - bot_y
    for block in blocks:
        bh = sum(_measure(f, w) for f in block)
        if bh <= y - bot_y:
            for f in block:
                h = _measure(f, w)
                pages[-1].append((f, y, h))
                y -= h
            continue
        if bh <= avail:
            pages.append([])
            y = top_y
            for f in block:
                h = _measure(f, w)
                pages[-1].append((f, y, h))
                y -= h
            continue
        for f in block:
            h = _measure(f, w)
            if h > y - bot_y:
                pages.append([])
                y = top_y
            pages[-1].append((f, y, h))
            y -= h
    return pages


def _frame(c, divider=True):
    c.setLineWidth(1.2)
    c.setStrokeColor(NAVY)
    c.rect(BORDER, BORDER, PW - 2 * BORDER, PH - 2 * BORDER, stroke=1, fill=0)
    s = 30
    c.setFillColor(NAVY_DEEP)
    corners = [
        [(BORDER, PH - BORDER), (BORDER + s, PH - BORDER), (BORDER, PH - BORDER - s)],
        [(PW - BORDER, PH - BORDER), (PW - BORDER - s, PH - BORDER),
         (PW - BORDER, PH - BORDER - s)],
        [(BORDER, BORDER), (BORDER + s, BORDER), (BORDER, BORDER + s)],
        [(PW - BORDER, BORDER), (PW - BORDER - s, BORDER), (PW - BORDER, BORDER + s)],
    ]
    for tri in corners:
        p = c.beginPath()
        p.moveTo(*tri[0])
        p.lineTo(*tri[1])
        p.lineTo(*tri[2])
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    if divider:
        c.setStrokeColor(HAIRLINE)
        c.setLineWidth(0.8)
        c.line(DIV, BOT_Y, DIV, TOP_Y + 4)


def render_cover(cl, out_path):
    c = canvasmod.Canvas(out_path, pagesize=A4)
    _frame(c, divider=False)
    mL, mR = 62, 62
    w = PW - mL - mR
    y = TOP_Y - 6

    def draw(flow, gap_after=0, x=mL, width=w):
        nonlocal y
        h = _measure(flow, width)
        flow.drawOn(c, x, y - h)
        y -= h + gap_after

    st_h = ParagraphStyle('clh', fontName=HEAD, fontSize=22, leading=24,
                          textColor=NAVY_DEEP)
    st_role = ParagraphStyle('clrole', fontName=BODY, fontSize=9.5, leading=12,
                             textColor=STEEL)
    st_ci = ParagraphStyle('clci', fontName=BODY, fontSize=8.6, leading=11,
                           textColor=SLATE)
    st_dt = ParagraphStyle('cldt', fontName=BODY, fontSize=9, leading=12,
                           textColor=SLATE)
    st_p = ParagraphStyle('clp', fontName=BODY, fontSize=10, leading=14.5,
                          textColor=INK, alignment=TA_JUSTIFY, spaceAfter=9)
    st_sign = ParagraphStyle('clsign', fontName=BODY, fontSize=10, leading=14,
                             textColor=INK)
    st_nm = ParagraphStyle('clnm', fontName=BODYB, fontSize=10.5, leading=13,
                           textColor=NAVY_DEEP)

    draw(Paragraph(cl['name'], st_h), 1)
    draw(Paragraph('Insurance Operations &amp; Transformation  |  '
                   'Intelligent Operations', st_role), 3)
    draw(Paragraph('  \u00b7  '.join(cl['contact']), st_ci), 10)

    c.setStrokeColor(STEEL)
    c.setLineWidth(1)
    c.line(mL, y, mL + w, y)
    y -= 14

    if cl['date']:
        draw(Paragraph(cl['date'], st_dt), 12)
    draw(Paragraph(cl['greeting'], st_p), 4)
    for para in cl['paragraphs']:
        draw(Paragraph(para, st_p), 0)
    y -= 6
    draw(Paragraph(cl['signoff'], st_sign), 2)
    draw(Paragraph(cl['name'], st_nm), 0)
    c.showPage()
    c.save()
    return out_path


def render(data, out_path):
    c = canvasmod.Canvas(out_path, pagesize=A4)
    left_pages = _paginate(_build_left(data), LW, TOP_Y, BOT_Y)
    right_pages = _paginate(_build_right(data), RW, TOP_Y, BOT_Y)
    n = max(len(left_pages), len(right_pages))
    for i in range(n):
        _frame(c)
        if i < len(left_pages):
            for f, y, h in left_pages[i]:
                f.drawOn(c, LX, y - h)
        if i < len(right_pages):
            for f, y, h in right_pages[i]:
                f.drawOn(c, RX, y - h)
        c.showPage()
    c.save()
    return out_path
