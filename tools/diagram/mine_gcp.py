#!/usr/bin/env python3
"""Mine Google Cloud diagram conventions out of draw.io's own GCP sidebars (Apache License 2.0, jgraph/drawio).
Kept: service NAMES and categories (Sidebar-GCPIcons.js palette entries), the 19 core products that draw.io draws from a named STENCIL (Sidebar-GCP3.js:
shape=mxgraph.gcp3.<name>, fill #4285f4), zone fill colours and path colours (Sidebar-GCP2.js). NOT kept: the embedded base64 SVG icons in GCP2 and GCPIcons,
which are Google's artwork; services drawn from those can be recognised by name but are not restyled.

  python mine_gcp.py GCPIcons.js GCP2.js GCP3.js > styles/gcp.catalogue.json"""
import re, sys, json
icons, gcp2, gcp3 = (open(p, encoding='utf8').read() for p in sys.argv[1:4])
# categories + service names: each palette function is addGCPIcons<Category>Palette; entries end "s * w, s * h, '', '<Name>', null, null"
cats = {}
FIX = {'AIandMachineLearning': 'AI and Machine Learning', 'APIManagement': 'API Management', 'InternetofThings': 'Internet of Things'}
parts = re.split(r'Sidebar\.prototype\.addGCPIcons(\w+)Palette = function', icons)
for cat, body in zip(parts[1::2], parts[2::2]):
    if cat in ('Generic', 'ExpandedProductCardIcons', 'OpenSourceIcons'): continue
    names = [n.replace('\\n', ' ').strip() for n in re.findall(r"'', '((?:[^'\\]|\\.)+)', null, null,", body.split('this.addPalette')[0])]
    if names: cats[FIX.get(cat) or re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', cat)] = sorted(set(names))
# core products drawn from named stencils
j = gcp3.index('addGCP3CoreProductsPalette = function')
core = [{'stencil': c[0], 'fill': c[1], 'w': float(c[2]), 'h': float(c[3]), 'name': c[4].replace('\\n', ' ')} for c in
        re.findall(r"createVertexTemplateEntry\(n \+ '([^;]+);fillColor=(#\w+)',\s*s \* ([\d.]+),\s*s \* ([\d.]+),\s*'((?:[^'\\]|\\.)*)'", gcp3[j:])]
# zones: fill colours by name
z = gcp2[gcp2.index('addGCP2ZonesPalette = function'):gcp2.index('addGCP2GeneralIconsPalette = function')]
zones = [{'name': m[1].replace('\\n', ' ').replace('\n', ' '), 'fill': m[0]} for m in re.findall(r"createVertexTemplateEntry\(s \+ 'fillColor=(#\w+);',\s*\n?\s*\d+,\s*\d+,\s*'((?:[^'\\]|\\.)*)'", z)]
paths = [{'name': m[2], 'color': m[1], 'dashed': m[0] == '1'} for m in re.findall(r"dashed=(\d);(?:dashPattern=1 3;)?strokeColor=(#\w+);', 100, 0, '', '([^']+)'", gcp2)]
paths += [{'name': m[1], 'color': m[0], 'dashed': False} for m in re.findall(r"strokeColor=(#\w+);dashed=0;', 100, 0, '', '([^']+)'", gcp2)]
zstyle = re.search(r"var s = '(sketch=0;[^']*)'", z).group(1)
print(json.dumps({'zone_style': zstyle, 'source': 'draw.io Sidebar-GCPIcons/GCP2/GCP3.js (Apache-2.0, jgraph/drawio)', 'categories': cats, 'core_products': core, 'zones': zones, 'paths': paths}, indent=1))
