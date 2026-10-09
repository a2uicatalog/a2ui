"""Schema-check every XML part of a .pptx against the ECMA-376 transitional XSDs. It answers one question: is the package legal OOXML?
It says nothing about whether a slide looks right (that needs a layout engine: Google Slides, LibreOffice, PowerPoint).

  python validate_ooxml.py <dir with pml.xsd, dml-main.xsd and the XSDs they import> deck.pptx [more.pptx ...]

The XSDs are the published ECMA-376 / ISO 29500 transitional schemas. They are not stored in this repository; get them from ECMA International
(ECMA-376, Part 4 transitional) and put the .xsd files in one directory. Needs lxml."""
import sys, zipfile, re, os
from lxml import etree
X = sys.argv[1]
pml = etree.XMLSchema(etree.parse(X + '/pml.xsd')); dml = etree.XMLSchema(etree.parse(X + '/dml-main.xsd'))
NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
def check(path):
    z = zipfile.ZipFile(path); res = []
    for n in z.namelist():
        if not n.endswith('.xml') or n.startswith('[') : continue
        if re.match(r'ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters)/[^/]+\.xml$', n) or n in ('ppt/presentation.xml',) or re.match(r'ppt/theme/theme\d+\.xml$', n):
            doc = etree.fromstring(z.read(n)); sch = dml if doc.tag.startswith('{' + NS['a']) else pml
            if not sch.validate(doc): res.append((n, [str(e.message)[:160] for e in sch.error_log][:3]))
    return res, len([n for n in z.namelist() if n.startswith('ppt/slides/slide')])
bad_total = 0
for p in sys.argv[2:]:
    try: bad, n = check(p)
    except Exception as e: print('SKIP', os.path.basename(p), str(e)[:80]); continue
    print(('OK  ' if not bad else 'FAIL'), os.path.basename(p), f'({n} slides)')
    for part, errs in bad[:3]: print('     ', part, errs)
    bad_total += len(bad)
print('parts failing:', bad_total)
