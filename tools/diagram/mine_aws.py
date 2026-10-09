#!/usr/bin/env python3
"""Mine the AWS service catalogue and group conventions out of draw.io's own AWS sidebar (Apache License 2.0, jgraph/drawio):
a category palette sets the category colour, each entry names a service and the stencil that draws it. We keep the names, categories, colours and the
stencil NAME; we never copy artwork (the editor draws the icon from its own stencil, or app.diagrams.net does).

  python mine_aws.py /path/to/drawio/js/diagramly/sidebar/Sidebar-AWS4.js > styles/aws.catalogue.json"""
import re, sys, json
src = open(sys.argv[1], encoding='utf8').read()
parts = re.split(r'\n\s*Sidebar\.prototype\.addAWS4(\w+)Palette = function', src)
cats = {}
def js_concat(expr, env):
    """Evaluate a JS expression made only of string literals, variables from `env`, mxConstants.STYLE_SHAPE and +."""
    out = ''
    for tok in re.findall(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"|(mxConstants\.STYLE_SHAPE)|\b([A-Za-z_]\w*)\b", expr):
        lit1, lit2, shape, var = tok
        out += lit1 or lit2 or ('shape' if shape else env.get(var, ''))
    return out

split = lambda s: re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s)
for name, body in zip(parts[1::2], parts[2::2]):
    if name in ('Arrows', 'GeneralResources', 'Illustrations', 'Groups'): continue
    n2m = re.search(r"var n2 = (.*?);\s*\n", body); style_base = js_concat(n2m.group(1), {}) if n2m else None
    m = re.search(r"fillColor=(#[0-9A-Fa-f]{6})", style_base or '')
    svc = []
    for e in re.finditer(r"createVertexTemplateEntry\(\s*n2\s*\+\s*'resourceIcon;resIcon='\s*\+\s*gn\s*\+\s*'\.([a-z0-9_]+);'\s*,\s*[^,]+,\s*[^,]+,\s*'([^']*)',\s*'([^']*)',\s*null,\s*null,\s*this\.getTagsForStencil\(gn,\s*'([^']*)'", body):
        nm = e.group(3).strip() or e.group(2).strip(); icon = e.group(1)
        svc.append({'icon': icon, 'name': nm, 'tag': e.group(4).strip(), 'category_icon': icon == re.sub(r'[^a-z0-9]+', '_', nm.lower()).strip('_') and False})
    if svc: cats[split(name)] = {'fill': m.group(1) if m else None, 'style_base': style_base, 'services': svc}
groups = []
gsrc = re.search(r"addAWS4GroupsPalette = function(.*?)\n\t};", src, re.S).group(1)
pts = re.search(r"var pts = '([^']*)'", src).group(1)
n4 = js_concat(re.search(r"var n4 = (.*?);\s*\n", gsrc).group(1), {'pts': pts})
for e in re.finditer(r"createVertexTemplateEntry\((.*?),\s*s \* 130,\s*s \* 130,\s*'([^']*)',\s*'([^']*)'", gsrc, re.S):
    style = js_concat(e.group(1), {'n4': n4, 'gn': 'mxgraph.aws4'}); g = lambda k: (re.search(r'(?:^|;)' + k + r'=([^;]*)', style) or [None, None])[1]
    groups.append({'name': e.group(3), 'style': style, 'strokeColor': g('strokeColor'), 'fillColor': g('fillColor'), 'fontColor': g('fontColor'), 'dashed': g('dashed') == '1'})
print(json.dumps({'source': 'draw.io Sidebar-AWS4.js (Apache-2.0, jgraph/drawio)', 'categories': cats, 'groups': groups}, indent=1))
