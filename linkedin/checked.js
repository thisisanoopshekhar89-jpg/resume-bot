() => {
  const flat = s => (s || '').split(/\s+/).join(' ').trim();
  const out = [];
  document.querySelectorAll('input[type=radio]').forEach(e => {
    if (!e.checked) return;
    let n = e, lab = '', guard = 0;
    while (n && guard++ < 5) {
      const t = flat(n.innerText || '');
      if (t && t.length < 200) { lab = t; break; }
      n = n.parentElement;
    }
    out.push(lab.slice(0, 120));
  });
  return out;
}
