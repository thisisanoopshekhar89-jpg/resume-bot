"""Resume + cover-letter tailoring bot (Flask).

Give it a job description as pasted text OR a screenshot (offline Windows OCR).
It re-tailors the master profile with an offline keyword aligner, regenerates
the two-column resume PDF and a matching cover letter, and shows a match/gap
report. No API key, no network.

Run:  python app.py    then open http://127.0.0.1:5000
"""

import os
import re
import sys
import time

from flask import Flask, request, render_template, send_from_directory, abort

import aligner
import company as company_svc
import coverletter
import ocr
import pdf_render

FROZEN = getattr(sys, 'frozen', False)


def _resource(rel):
    """Path to a bundled read-only resource (works frozen or as a script)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


APP_DIR = (os.path.dirname(sys.executable) if FROZEN
           else os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(APP_DIR, 'output')
UP_DIR = os.path.join(APP_DIR, 'uploads')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(UP_DIR, exist_ok=True)

ALLOWED_IMG = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.tiff', '.webp'}

app = Flask(__name__, template_folder=_resource('templates'))
app.config['MAX_CONTENT_LENGTH'] = 16777216


def _slug(text, default='resume'):
    for line in text.splitlines():
        line = line.strip()
        if not len(line) > 3:
            continue
        s = re.sub('[^A-Za-z0-9]+', '_', line)[:32].strip('_')
        if s:
            return s
    return default


def _render_index(**kw):
    base = dict(report=None, resume_pdf=None, cover_pdf=None, jd='',
                company='', role='', error=None, role_head=None, active=None)
    base.update(kw)
    return render_template('index.html', **base)


@app.route('/', methods=['GET'])
def index():
    return _render_index()


def _read_jd(request):
    """Return (jd_text, company, role, error). OCRs an uploaded image if no text."""
    jd = (request.form.get('jd') or '').strip()
    company = (request.form.get('company') or '').strip()
    role = (request.form.get('role') or '').strip()

    up = request.files.get('jd_image')
    if up and up.filename and not jd:
        ext = os.path.splitext(up.filename)[1].lower()
        if ext not in ALLOWED_IMG:
            return jd, company, role, ('Unsupported image type. Use '
                                       'PNG/JPG/BMP/TIFF/WEBP, or paste text.')
        saved = os.path.join(UP_DIR, 'jd_%d%s' % (int(time.time()), ext))
        up.save(saved)
        try:
            jd = ocr.image_to_text(saved).strip()
        except ocr.OcrError as e:
            return '', company, role, str(e)
        finally:
            try:
                os.remove(saved)
            except OSError:
                pass

    if len(jd) < 20:
        return jd, company, role, ('Please paste a job description or upload a '
                                   'readable screenshot.')
    return jd, company, role, None


@app.route('/generate', methods=['POST'])
def generate():
    action = request.form.get('action', 'resume')

    # The master CV is the whole profile - it needs no JD at all.
    if action == 'master':
        tailored, report = aligner.master()
        master_name = 'Anoop_Shekhar_MasterCV_%d.pdf' % int(time.time())
        pdf_render.render(tailored, os.path.join(OUT_DIR, master_name))
        return _render_index(report=report, resume_pdf=master_name,
                             jd=(request.form.get('jd') or '').strip(),
                             company=(request.form.get('company') or '').strip(),
                             role=(request.form.get('role') or '').strip(),
                             active='master',
                             role_head=tailored['role'].replace('&amp;', '&'))

    jd, company, role, error = _read_jd(request)
    if error:
        return _render_index(jd=jd, company=company, role=role, error=error,
                             active=action)

    tailored, report = aligner.align(jd)
    stamp = int(time.time())
    tag = _slug(company or jd)
    resume_name = cover_name = None

    if action == 'cover':
        cover_name = 'Anoop_Shekhar_CoverLetter_%s_%d.pdf' % (tag, stamp)
        info = company_svc.lookup(company) if company else None
        cl = coverletter.build(report, company=company, role=role,
                               company_info=info)
        pdf_render.render_cover(cl, os.path.join(OUT_DIR, cover_name))
    else:
        action = 'resume'
        resume_name = 'Anoop_Shekhar_Resume_%s_%d.pdf' % (tag, stamp)
        pdf_render.render(tailored, os.path.join(OUT_DIR, resume_name))

    return _render_index(report=report, resume_pdf=resume_name,
                         cover_pdf=cover_name,
                         jd=jd, company=company, role=role, active=action,
                         role_head=tailored['role'].replace('&amp;', '&'))


@app.route('/download/<path:fname>')
def download(fname):
    if '/' in fname or '\\' in fname or '..' in fname:
        abort(404)
    return send_from_directory(OUT_DIR, fname, as_attachment=True)


@app.route('/view/<path:fname>')
def view(fname):
    if '/' in fname or '\\' in fname or '..' in fname:
        abort(404)
    return send_from_directory(OUT_DIR, fname)


if __name__ == '__main__':
    import threading
    import webbrowser

    port = int(os.environ.get('PORT', '5057'))
    url = 'http://127.0.0.1:%d/' % port
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print('\n  Resume & Cover-Letter Bot running at  %s\n'
          '  (Press CTRL+C to stop)\n' % url)
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)
