() => {
  const flat = s => (s || '').split(/\s+/).join(' ').trim();
  // Walk upward/backward to find the nearest human label for a control.
  const labelFor = (e, root) => {
    if (e.id) { const l = root.querySelector('label[for="' + CSS.escape(e.id) + '"]'); if (l && flat(l.innerText)) return flat(l.innerText); }
    if (e.getAttribute('aria-label')) return flat(e.getAttribute('aria-label'));
    const alb = e.getAttribute('aria-labelledby');
    if (alb) { const t = alb.split(/\s+/).map(i => (document.getElementById(i) || {}).innerText || '').join(' '); if (flat(t)) return flat(t); }
    const fs = e.closest('fieldset'); if (fs) { const lg = fs.querySelector('legend'); if (lg && flat(lg.innerText)) return flat(lg.innerText); }
    // nearest previous element with visible text
    let n = e, guard = 0;
    while (n && guard++ < 6) {
      let s = n.previousElementSibling;
      while (s) { const t = flat(s.innerText); if (t && t.length < 200) return t; s = s.previousElementSibling; }
      n = n.parentElement;
    }
    return '';
  };
  const dlg = document.querySelector('dialog[data-testid="dialog"], dialog[open], [role="dialog"]');
  const root = dlg || document.body;
  const out = { fields: [], buttons: [], step: '' };
  const mt = (root.innerText || '').match(/(\d\/\d) pages/); out.step = mt ? mt[1] : '';
  root.querySelectorAll('input,select,textarea').forEach(e => {
    if (e.type === 'hidden') return;
    const st = getComputedStyle(e);
    out.fields.push({
      type: e.type, id: String(e.id || '').slice(0, 40), name: String(e.name || '').slice(0, 40),
      required: !!e.required || e.getAttribute('aria-required') === 'true',
      value: String(e.value || '').slice(0, 70), checked: !!e.checked,
      visible: !(st.display === 'none' || st.visibility === 'hidden'),
      label: labelFor(e, root).slice(0, 130),
      opts: e.tagName === 'SELECT' ? [...e.options].map(o => o.text).slice(0, 8) : undefined
    });
  });
  const seen = new Set();
  root.querySelectorAll('button').forEach(b => {
    const t = flat(b.innerText || b.getAttribute('aria-label') || '').slice(0, 45);
    if (t && !seen.has(t)) { seen.add(t); out.buttons.push(t); }
  });
  return out;
}
