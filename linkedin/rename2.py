"""Company-named PDFs; role suffix added where one company has several roles."""
import json, os, re, shutil
from collections import Counter

man = json.load(open("manifest.json", encoding="utf-8"))
def clean(s, n=34):
    s = re.sub(r"[^A-Za-z0-9]+", "_", s or "")
    return re.sub(r"_+", "_", s).strip("_")[:n].strip("_")

dupes = {c for c, n in Counter(clean(m["company"]) for m in man).items() if n > 1}

for m in man:
    comp = clean(m["company"])
    tag = comp if comp not in dupes else "%s_%s" % (comp, clean(m["title"], 30))
    for key, stem in (("resume", "Resume"), ("cover", "CoverLetter")):
        old = m[key]
        if not os.path.exists(old):
            print("  ! missing", old); continue
        new = os.path.join(os.path.dirname(old), "Anoop_Shekhar_%s_%s.pdf" % (stem, tag))
        if os.path.abspath(old) != os.path.abspath(new):
            shutil.move(old, new)
        m[key] = new
    print("  %s" % os.path.basename(m["resume"]))

json.dump(man, open("manifest.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
names = [os.path.basename(m["resume"]) for m in man]
print("\n%d packs | unique filenames: %d" % (len(man), len(set(names))))
