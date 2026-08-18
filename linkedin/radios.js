() => {
  const flat = s => (s || '').split(/\s+/).join(' ').trim();
  // Group radios by name; report the question text and whether anything is chosen.
  const groups = {};
  document.querySelectorAll('input[type=radio]').forEach(e => {
    const g = e.name || '(none)';
    groups[g] = groups[g] || { name: g, checked: false, options: [], question: '' };
    if (e.checked) groups[g].checked = true;
    let lab = '';
    if (e.id) { const l = document.querySelector('label[for="' + CSS.escape(e.id) + '"]'); if (l) lab = flat(l.innerText); }
    if (!lab) { const p = e.closest('label'); if (p) lab = flat(p.innerText); }
    groups[g].options.push({ id: e.id, label: lab.slice(0, 60), checked: e.checked });
    if (!groups[g].question) {
      const fs = e.closest('fieldset');
      if (fs) { const lg = fs.querySelector('legend'); if (lg) groups[g].question = flat(lg.innerText).slice(0, 160); }
      // Many LinkedIn question groups have no <legend>: the question sits in the
      // text just above the options, so walk up and strip the option labels out.
      if (!groups[g].question) {
        let n = e, guard = 0;
        while (n && guard++ < 6) {
          let t = flat(n.innerText || '');
          if (t && t.length < 300 && /\?|\*/.test(t)) {
            for (const o of n.querySelectorAll('label')) {
              const ot = flat(o.innerText);
              if (ot && ot.length < 30) t = t.split(ot).join(' ');
            }
            t = flat(t);
            if (t.length > 8) { groups[g].question = t.slice(0, 160); break; }
          }
          n = n.parentElement;
        }
      }
    }
  });
  return Object.values(groups).filter(g => g.options.length > 1 || g.question);
}
