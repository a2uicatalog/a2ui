"""Tests for the networks group of the d3 macro pack (decision_tree, spring_nodes, voronoi): independent geometry checks (voronoi in DATA units), inverse-read oracles that parse the SVG
back into data and compare it with the input (every connector, every edge, every legend swatch, every tick), the atoms' tolerant-reader rules, hostile-input sweeps through d3pack.call(),
determinism, and every message validated against the upstream A2UI 1.0 schemas (with negative controls). No model, no browser, no network.
Run: A2UI_UPSTREAM=<upstream checkout> python3 -B tests/test_networks.py"""
import copy, functools, glob, json, math, random, re, sys, time
from pathlib import Path
import os
_UP = os.environ.get('A2UI_UPSTREAM')
try:
    import jsonschema  # noqa: F401
except ImportError:
    _UP = None
if not _UP or not (Path(_UP) / 'specification/v1_0/json').is_dir():
    print('SKIPPED: set A2UI_UPSTREAM to a checkout of the upstream A2UI repository (and install jsonschema) to run the schema validation')
    sys.exit(0)
import xml.etree.ElementTree as ET
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.dont_write_bytecode = True
import d3pack as D
from d3pack.common import atom_card, W as CW, H as CH, PAL, verify_svg
from d3pack.decision_tree import decision_tree
from d3pack.spring_nodes import spring_nodes
from d3pack.voronoi import voronoi
from d3pack.registry_networks import PACK_NETWORKS
from d3pack.demos_networks import DEMOS
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
SPEC = (Path(_UP) / 'specification/v1_0/json'); CATF = (Path(_UP) / 'catalogs/basic/v1/catalog.json')
docs = {p: json.loads(Path(p).read_text()) for p in glob.glob(str(SPEC / '*.json'))}; cat = json.loads(CATF.read_text())
res = [(d.get('$id', 'file://' + p), Resource.from_contents(d)) for p, d in docs.items()] + [(cat['$id'], Resource.from_contents(cat)), ('https://a2ui.org/specification/v1_0/catalog.json', Resource.from_contents(cat))]
A2R = Draft202012Validator(docs[str(SPEC / 'agent_to_renderer.json')], registry=Registry().with_resources(res))
n = 0; bad = 0
def ok(name, c):
    global n, bad; n += 1
    if not c: bad += 1; print('FAIL', name)
def T(r): return r[r['_default']]
NS = '{http://www.w3.org/2000/svg}'
def root(r): return ET.fromstring(r['svg'])
def wf(r): ET.fromstring(r['svg']); return True
def num(s): return float(s.replace(',', ''))
SVG_COLOURS = set(PAL) | {'#ffffff', '#1f2150', '#59607a', '#c9cde0', '#000000', '#111111'}
def colours(r):
    out = set()
    for e in root(r).iter():
        for a in ('fill', 'stroke'):
            if a in e.attrib and e.attrib[a] != 'none': out.add(e.attrib[a])
    return out
def blends(): return {f'#{r:02x}{g:02x}{b:02x}' for p in PAL for r, g, b in [tuple(int(p[i:i + 2], 16) for i in (1, 3, 5))] for t in (.72, .88) for r, g, b in [tuple(round(c + (255 - c) * t) for c in (r, g, b))]}
def fonts(r): return [float(e.attrib['font-size']) for e in root(r).iter(NS + 'text')]
def note_only(r): return bool(T(r).get('empty')) and 'Nothing was drawn' in T(r)['alt']
# ================= decision_tree
TREE = [{'text': 'Root', 'children': [{'text': 'A', 'children': [{'text': 'A1'}, {'text': 'A2'}, {'text': 'A3'}]}, {'text': 'B'}, {'text': 'C', 'children': [{'text': 'C1', 'children': [{'text': 'C1a'}, {'text': 'C1b'}]}]}]}]
PARENT = [None, 0, 1, 1, 1, 0, 0, 6, 7, 7]    # preorder parent index of Root, A, A1, A2, A3, B, C, C1, C1a, C1b
NAMES = ['Root', 'A', 'A1', 'A2', 'A3', 'B', 'C', 'C1', 'C1a', 'C1b']
t = T(decision_tree(TREE, title='T')); N = t['nodes']; by = {x['text']: x for x in N}
def tree_geometry(r):
    """Read the drawing back: box rectangles (in preorder) and connectors, as numbers."""
    rt = root(r); boxes = []; conns = []
    for g in rt.iter(NS + 'g'):
        rc = g.find(NS + 'rect')
        if rc is not None: boxes.append({k: float(rc.attrib[k]) for k in ('x', 'y', 'width', 'height')} | {'title': g.find(NS + 'title').text, 'text': g.find(NS + 'text').text})
    for p in rt.iter(NS + 'path'):
        m = re.fullmatch(r'M([\d.]+),([\d.]+) H([\d.]+) V([\d.]+) H([\d.]+)', p.attrib['d'])
        if m: conns.append(tuple(float(v) for v in m.groups()))
    return boxes, conns
boxes, conns = tree_geometry(t)
ok('tree: all 10 nodes drawn', len(N) == 10 and len(boxes) == 10 and '10 nodes' in t['summary'])
ok('tree: box titles are the node texts in preorder (read back from the SVG)', [b['title'] for b in boxes] == NAMES)
mid = lambda b: b['y'] + b['height'] / 2
ok('tree INVERSE: every connector runs from its parent box (right edge, middle) to its own child box (left edge, middle)',
   len(conns) == 9 and all(any(abs(c[0] - (boxes[PARENT[i]]['x'] + boxes[PARENT[i]]['width'])) < .01 and abs(c[1] - mid(boxes[PARENT[i]])) < .01 and abs(c[4] - boxes[i]['x']) < .01 and abs(c[3] - mid(boxes[i])) < .01 for c in conns) for i in range(1, 10)))
ok('tree INVERSE: no connector ends on a row without a child box (none runs to the root row)', all(any(abs(c[3] - mid(b)) < .01 and abs(c[4] - b['x']) < .01 for b in boxes) for c in conns) and len({(c[3], c[4]) for c in conns}) == 9)
kids = {i: [j for j in range(10) if PARENT[j] == i] for i in range(10)}
ok('tree INVERSE: every parent box is centred on its first and last child (read from the SVG)', all(abs(mid(boxes[i]) - (mid(boxes[k[0]]) + mid(boxes[k[-1]])) / 2) < .01 for i, k in kids.items() if k))
depth = [0 if PARENT[i] is None else 1 + 0 for i in range(10)]
for i in range(10): depth[i] = 0 if PARENT[i] is None else depth[PARENT[i]] + 1
ok('tree INVERSE: depth maps to the horizontal axis (same depth, same column; deeper boxes start right of the shallower ones end)', all(abs(boxes[i]['x'] - boxes[j]['x']) < .01 for i in range(10) for j in range(10) if depth[i] == depth[j]) and all(boxes[i]['x'] >= boxes[PARENT[i]]['x'] + boxes[PARENT[i]]['width'] for i in range(1, 10)))
ok('tree INVERSE: boxes of one level never overlap vertically', all(abs(mid(boxes[i]) - mid(boxes[j])) >= boxes[i]['height'] for i in range(10) for j in range(i + 1, 10) if depth[i] == depth[j]))
ok('tree: leaves occupy distinct rows in order', [x['row'] for x in N if not x['kids']] == sorted(set(x['row'] for x in N if not x['kids'])))
ok('tree: text alternative lists every node with its outline number', all(f'{x["path"]} {x["text"]}' in t['table'] for x in N) and '1.3.1.2 C1b (end)' in t['table'])
ok('tree: alt text carries the same counts as the drawing', '10 nodes in 4 levels, 6 end points' in t['alt'] and t['levels'] == 4 and t['leaves'] == 6)
ok('tree: notes say the tree is drawn expanded', any('fully expanded' in x for x in t['notes']))
ok('tree: well-formed, deterministic', wf(t) and decision_tree(TREE)['tree']['svg'] == decision_tree(TREE)['tree']['svg'])
ok('tree: nodes without text dropped and counted', any('2 nodes were left out' in x for x in T(decision_tree(TREE + [{'children': []}, {'text': None}]))['notes']))
ok('tree: a plain string is a leaf node', T(decision_tree(['x', 'y']))['nodes'][1]['text'] == 'y')
ok('tree: several top-level nodes drawn as a forest in column 0', len({x['x'] for x in T(decision_tree(['x', 'y', 'z']))['nodes']}) == 1)
c40 = T(decision_tree([{'text': f'n{i}'} for i in range(40)])); ok('tree: 31 node cap noted, naming the atom outline fallback', len(c40['nodes']) == 31 and any('9 nodes beyond the 31th' in x and 'outline' in x for x in c40['notes']))
deep = {'text': 'L1'}; cur = deep
for i in range(2, 9): cur['children'] = [{'text': f'L{i}'}]; cur = cur['children'][0]
dd = T(decision_tree([deep])); ok('tree: 6 level cap (levels below are not drawn, all counted)', dd['levels'] == 6 and any('2 nodes below level 6' in x and 'outline' in x for x in dd['notes']))
lg = T(decision_tree([{'text': 'x' * 50}, 'y'])); ok('tree: a label over 32 characters is drawn shortened WITH A NOTE; table and hover title keep the full text', any('1 labels longer than 32' in x for x in lg['notes']) and 'x' * 50 in lg['table'] and lg['nodes'][0]['drawn'] == 'x' * 31 + '…' and tree_geometry(lg)[0][0]['title'] == 'x' * 50)
ok('tree: label of exactly 32 characters is not noted', not any('longer than' in x for x in T(decision_tree([{'text': 'x' * 32}, 'y']))['notes']))
ok('tree: empty or all-unusable input gives a note-only Result', note_only(decision_tree([])) and note_only(decision_tree([{'id': 'a', 'next': 'b'}])) and note_only(decision_tree('x')) and note_only(decision_tree(None)))
ok('tree: version 2 drawn as 1 with a note', any('version 1' in x for x in T(decision_tree(TREE, version=2))['notes']) and any('version 1' in x for x in T(decision_tree(TREE, version=10**400))['notes']))
ok('tree: markup in text stays well-formed and is escaped', wf(T(decision_tree([{'text': '<b>&"', 'children': [{'text': "it's <x>"}]}]))) and '<b>&' not in T(decision_tree([{'text': '<b>&"'}]))['svg'])
long = T(decision_tree([{'text': 'q' * 32, 'children': [{'text': 'w' * 32, 'children': [{'text': 'e' * 32, 'children': [{'text': 'r' * 32, 'children': [{'text': 't' * 32, 'children': [{'text': 'y' * 32}]}]}]}]}]}]))
ok('tree: six levels of 32-character labels still fit inside the drawing width', all(x['x'] + x['w'] <= CW - 19 for x in long['nodes']) and all(len(x['shown']) * 7.8 + 16 <= x['w'] + 1 for x in long['nodes']))
wide = T(decision_tree([{'text': 'r', 'children': [{'text': f'c{i}'} for i in range(30)]}]))
ok('tree: a 30-leaf level grows the drawing height and keeps every box inside it', wide['size'][1] > CH and all(x['y'] + x['h'] / 2 <= wide['size'][1] for x in wide['nodes']) and 'height="%d"' % wide['size'][1] in wide['svg'])
ok('tree: text is at least 14px', all(f >= 14 for f in fonts(t)))
ok('tree: only palette, ink and line colours (no colour that is not on the list)', colours(t) <= SVG_COLOURS)
ok('tree: SVG within the 80 KB policy at 31 nodes', len(wide['svg']) < 80000)
t0 = time.time(); d5 = T(decision_tree([functools.reduce(lambda acc, _: {'text': 'x', 'children': [acc]}, range(5000), {'text': 'leaf'})]))
ok('tree NEGATIVE: nesting 5000 deep does not recurse (6 levels drawn, the rest counted) and is fast', d5['levels'] == 6 and any('4995 nodes below level 6' in x for x in d5['notes']) and time.time() - t0 < 2)
t0 = time.time(); dg = T(decision_tree([functools.reduce(lambda acc, _: {'text': 'x', 'children': [acc, acc]}, range(60), {'text': 'leaf'})]))
ok('tree NEGATIVE: a shared-subtree DAG of depth 60 (2^60 paths) finishes at once', time.time() - t0 < 2 and len(dg['nodes']) == 31)
cyc = {'text': 'c'}; cyc['children'] = [cyc]; ok('tree NEGATIVE: a cyclic structure is drawn to the level cap and stops', T(decision_tree([cyc]))['levels'] == 6)
ok('tree NEGATIVE: 10**400 and NaN as text, title, version, layout and children do not raise', isinstance(T(decision_tree([{'text': 10**400, 'children': float('nan')}, {'text': float('nan')}, 'ok'], title=10**400, version=10**400, layout=10**400)), dict))
ok('tree NEGATIVE: dict and list as text are not text', len(T(decision_tree([{'text': {'a': 1}}, {'text': ['x']}, 'ok']))['nodes']) == 1)
ok('tree: layout other than tree is noted', any('layout outline' in x for x in T(decision_tree(TREE, layout='outline'))['notes']))
# ---- decision_tree layout='flow' (top-down, edge words, detail lines, outcome boxes; additive: the default layout is unchanged)
from d3pack.rich import verify_rich
FLOW = [{'text': 'Does an agent need to drive the UI?', 'children': [
    {'edge': 'No', 'text': 'A plain HTML page', 'detail': 'or an MCP App, if it must live in a chat host (not built)'},
    {'edge': 'Yes', 'text': 'Can you change the host?', 'detail': 'Register a catalogue, ship our code', 'children': [
        {'edge': 'Yes', 'text': 'A custom catalogue', 'detail': 'ours or your own', 'outcome': True},
        {'edge': 'No', 'text': 'Does the screen need more than Basic can draw?', 'detail': 'a chart, a board', 'children': [{'edge': 'No', 'text': 'Plain Basic'}, {'edge': 'Yes', 'text': 'Basic with a drawn Image', 'outcome': True}]}]}]}]
fl = T(decision_tree(FLOW, title='Route', layout='flow')); FN = fl['nodes']
def flow_boxes(r):
    rt = root(r); return [{k: float(e.attrib[k]) for k in ('x', 'y', 'width', 'height')} | {'stroke': e.attrib['stroke']} for e in rt.iter(NS + 'rect') if 'rx' in e.attrib and e.attrib.get('class', '') != 'd3-bg']
fb = flow_boxes(fl)
ok('flow: well-formed, 7 boxes, passes the rich policy (the self-contained theme)', wf(fl) and len(fb) == 7 and verify_rich(fl['svg']) == fl['svg'] and fl['policy'] == 'rich' and fl['svg'] == fl['svg_img'])
ok('flow: outcomes (leaves, or outcome true) have the purple 3px outline, questions the border colour', sorted(b['stroke'] for b in fb) == sorted(['#6b5cff' if not x['kids'] or x['outcome'] else '#d8dde6' for x in FN]) and sum(b['stroke'] == '#6b5cff' for b in fb) == 4)
def overlap(a, b): return a['x'] < b['x'] + b['width'] and b['x'] < a['x'] + a['width'] and a['y'] < b['y'] + b['height'] and b['y'] < a['y'] + a['height']
ok('flow: no two boxes overlap and every box is inside the viewBox', not any(overlap(fb[i], fb[j]) for i in range(7) for j in range(i + 1, 7)) and all(b['x'] >= 0 and b['y'] >= 0 and b['x'] + b['width'] <= fl['size'][0] and b['y'] + b['height'] <= fl['size'][1] for b in fb))
ok('flow: children are below their parent (top-down)', all(FN[x['parent']]['y'] + FN[x['parent']]['h'] < x['y'] for x in FN if x['parent'] is not None))
E = fl['edges']
ok('flow: one edge per child; each starts on its parent bottom border and ends on its child top border (inside the box width)', len(E) == 6 and all(abs(e['y1'] - (FN[e['from']]['y'] + FN[e['from']]['h'])) < .01 and abs(e['y2'] - FN[e['to']]['y']) < .01 and FN[e['from']]['x'] <= e['x1'] <= FN[e['from']]['x'] + FN[e['from']]['w'] and FN[e['to']]['x'] <= e['x2'] <= FN[e['to']]['x'] + FN[e['to']]['w'] for e in E))
def arrows(r):
    out = []
    for p in root(r).iter(NS + 'path'):
        m = re.fullmatch(r'M([\d.]+) ([\d.]+)L([\d.]+) ([\d.]+)L([\d.]+) ([\d.]+)Z', p.attrib['d'])
        if m: out.append(tuple(float(v) for v in m.groups())[:2])
    return out
ok('flow INVERSE: the arrowhead tips read back from the SVG are the edge end points', sorted(arrows(fl)) == sorted((round(e['x2'], 1), round(e['y2'], 1)) for e in E))
words = [t.text for t in root(fl).iter(NS + 'text')]
ok('flow: Yes and No words are drawn on the lines (3 each, from the data), and the title lines and detail lines are drawn', words.count('Yes') == 3 and words.count('No') == 3 and 'Does an agent need to' in words and 'drive the UI?' in words and 'a chart, a board' in words)
ok('flow: labels do not sit inside any box', all(not any(b['x'] < e['lx'] < b['x'] + b['width'] and b['y'] < e['ly'] - 5 < b['y'] + b['height'] for b in fb) for e in E))
ok('flow: table, summary, alt, text and text_html are carried; the table has edge words and details', 'If Yes: A custom catalogue - ours or your own' in fl['table'] and '7 nodes in 4 levels, 4 end points' in fl['alt'] and fl['text'].count('\n') == 6 and fl['text_html'].count('<li>') == 7 and '<ol>' in fl['text_html'])
ok('flow: deterministic', decision_tree(FLOW, layout='flow')['tree']['svg'] == decision_tree(FLOW, layout='flow')['tree']['svg'])
cv = T(decision_tree(FLOW, title='Route', layout='flow', theme='css-vars', ids='ab'))
ok('flow css-vars: inline svg with var(--surface-2, ...) etc, aria-labelledby title and desc ids, no style, no background rect; svg_img is the self-contained one; data_uri refuses it', wf(cv) and 'var(--surface-2, #f2f4f8)' in cv['svg'] and 'var(--border, ' in cv['svg'] and 'var(--text, ' in cv['svg'] and 'var(--muted, ' in cv['svg'] and 'aria-labelledby="ab-t ab-d"' in cv['svg'] and '<title id="ab-t">Route</title>' in cv['svg'] and '<style' not in cv['svg'] and 'd3-bg' not in cv['svg'] and cv['svg_img'] == fl['svg_img'] and cv['policy'] == 'css-vars' and not any('var(' in x for x in [cv['svg_img']]))
try: D.common.data_uri(cv['svg'], cv.get('policy')); refused = False
except Exception: refused = True
ok('flow css-vars: the var() text is not admitted by any policy (cannot become an Image)', refused)
ok('flow self-contained: one dark-mode media block inside the svg and a data URI works', '@media (prefers-color-scheme: dark)' in fl['svg'] and D.common.data_uri(fl['svg'], fl['policy']).startswith('data:image/svg+xml;base64,'))
ok('flow: unknown theme noted and drawn light', any('theme zzz' in x for x in T(decision_tree(FLOW, layout='flow', theme='zzz'))['notes']))
ok('flow: markup in text, edge and detail stays well-formed and escaped', wf(T(decision_tree([{'text': '<b>&"', 'detail': '<i>', 'children': [{'text': 'x', 'edge': '<u>'}]}], layout='flow', theme='css-vars', ids='"><x'))) and '<u>' not in T(decision_tree([{'text': 'a', 'children': [{'text': 'x', 'edge': '<u>'}]}], layout='flow'))['svg'])
lng = T(decision_tree([{'text': 'word ' * 30, 'detail': 'w' * 200}], layout='flow'))
ok('flow limits: over-long title and detail are drawn shortened WITH A NOTE; the table keeps the full (120 character) text', any('shortened' in x for x in lng['notes']) and '…' in lng['svg'] and 'word ' * 20 in lng['table'] and 'w' * 120 in lng['table'])
c40 = T(decision_tree([{'text': f'n{i}', 'detail': 'd', 'edge': 'e'} for i in range(40)], layout='flow'))
ok('flow limits: 31 nodes cap and the outline-fallback note as in the default layout; policy still passes', len(c40['nodes']) == 31 and any('9 nodes beyond the 31th' in x for x in c40['notes']) and c40['policy'] == 'rich')
dd6 = T(decision_tree([functools.reduce(lambda acc, _: {'text': 'x', 'edge': 'y', 'children': [acc]}, range(7), {'text': 'leaf'})], layout='flow'))
ok('flow limits: 6 levels', dd6['levels'] == 6 and any('below level 6' in x for x in dd6['notes']))
full31 = T(decision_tree([{'text': 'r' * 50, 'detail': 'd' * 120, 'edge': 'e' * 30, 'children': [{'text': 'c' * 50, 'detail': 'd' * 120, 'edge': 'e', 'children': [{'text': 'g' * 50, 'detail': 'd' * 120, 'edge': 'e'} for _ in range(14)]} for _ in range(2)]}], layout='flow'))
ok('flow: 31 fully loaded nodes stay inside the rich policy budgets (60 KB, 400 elements) and never raise', len(full31['nodes']) == 31 and full31['policy'] == 'rich' and len(full31['svg'].encode()) < 60000)
t0 = time.time(); d5 = T(decision_tree([functools.reduce(lambda acc, _: {'text': 'x', 'children': [acc]}, range(5000), {'text': 'leaf'})], layout='flow')); dg = T(decision_tree([functools.reduce(lambda acc, _: {'text': 'x', 'children': [acc, acc]}, range(60), {'text': 'leaf'})], layout='flow'))
ok('flow NEGATIVE: 5000 deep and a 2^60 shared subtree are bounded (levels, time)', d5['levels'] == 6 and dg['levels'] <= 6 and time.time() - t0 < 5)
# ---- decision_tree layout='flow-v' (indented, about 320 px wide, for phones; additive)
# a synthetic options tree: 11 boxes, 10 labelled edges, one 'No' edge, one detail line
P3 = [{'text': 'Start', 'detail': 'Plain text', 'children': [
    {'text': 'Words', 'edge': 'Text', 'children': [{'text': 'Cards', 'edge': 'Short'}, {'text': 'Pages', 'edge': 'Long'}]},
    {'text': 'Picture', 'edge': 'Image', 'children': [
        {'text': 'Chart', 'edge': 'Numbers', 'children': [{'text': 'Bars', 'edge': 'Yes'}, {'text': 'Lines', 'edge': 'No'}]},
        {'text': 'Photo', 'edge': 'Real'}]},
    {'text': 'More', 'edge': 'Other', 'children': [{'text': 'Table', 'edge': 'Rows'}]}]}]
fv = T(decision_tree(P3, title='Options', layout='flow-v')); FVN = fv['nodes']; fvb = flow_boxes(fv); FVE = fv['edges']
ok('flow-v: well-formed, 11 boxes, passes the rich policy, width under 400 px', wf(fv) and len(fvb) == 11 and verify_rich(fv['svg']) == fv['svg'] and fv['policy'] == 'rich' and fv['size'][0] < 400 and fv['theme'] == 'light')
ok('flow-v: no two boxes overlap and every box is inside the viewBox; no box wider than 300', not any(overlap(fvb[i], fvb[j]) for i in range(11) for j in range(i + 1, 11)) and all(b['x'] >= 0 and b['y'] >= 0 and b['x'] + b['width'] <= fv['size'][0] and b['y'] + b['height'] <= fv['size'][1] and b['width'] <= 300 for b in fvb))
ok('flow-v: indented one step per level, children below their parent in order', all(x['x'] > FVN[x['parent']]['x'] and x['y'] > FVN[x['parent']]['y'] + FVN[x['parent']]['h'] for x in FVN if x['parent'] is not None) and [x['y'] for x in FVN] == sorted(x['y'] for x in FVN))
fvw = [''.join(e.itertext()) for e in root(fv).iter(NS + 'text')]
ok('flow-v: every edge label is drawn once per edge, and every title word and detail word is drawn', len(FVE) == 10 and all(fvw.count(w) >= 1 for w in ('Start', 'Words', 'Cards', 'Pages', 'Picture', 'Chart', 'Bars', 'Lines', 'Photo', 'More', 'Table', 'No', 'Yes')) and 'Plain text' in fvw and len([w for w in fvw if w == 'No']) == 1)
ok('flow-v: elbows start on the parent bottom, end on the child left border at mid height; labels sit in no box', all(abs(e['y1'] - (FVN[e['from']]['y'] + FVN[e['from']]['h'])) < .01 and abs(e['x2'] - FVN[e['to']]['x']) < .01 and abs(e['y2'] - (FVN[e['to']]['y'] + FVN[e['to']]['h'] / 2)) < .01 and e['x1'] < e['x2'] for e in FVE) and all(not any(b['x'] < e['lx'] < b['x'] + b['width'] and b['y'] < e['ly'] - 5 < b['y'] + b['height'] for b in fvb) for e in FVE if e['label']))
ok('flow-v: text, table, alt carried and equal to the flow layout for the same tree', fv['text'] == T(decision_tree(P3, title='Options', layout='flow'))['text'] and fv['table'] == T(decision_tree(P3, title='Options', layout='flow'))['table'] and fv['text_html'].count('<li>') == 11)
ok('flow-v: deterministic', decision_tree(P3, layout='flow-v')['tree']['svg'] == decision_tree(P3, layout='flow-v')['tree']['svg'])
fvc = T(decision_tree(P3, title='Options', layout='flow-v', theme='css-vars', ids='ab'))
ok('flow-v css-vars: inline, var() colours, aria-labelledby ids with the prefix, no style, no background; svg_img self-contained; data_uri refuses it', wf(fvc) and 'var(--surface-2, #f2f4f8)' in fvc['svg'] and 'aria-labelledby="ab-t ab-d"' in fvc['svg'] and '<title id="ab-t">Options</title>' in fvc['svg'] and '<style' not in fvc['svg'] and 'd3-bg' not in fvc['svg'] and fvc['svg_img'] == fv['svg_img'] and fvc['policy'] == 'css-vars' and fvc['size'] == fv['size'])
try: D.common.data_uri(fvc['svg'], fvc['policy']); refused_v = False
except Exception: refused_v = True
ok('flow-v css-vars: not admitted by any policy; self-contained has one dark media block and a data URI works', refused_v and '@media (prefers-color-scheme: dark)' in fv['svg'] and D.common.data_uri(fv['svg'], fv['policy']).startswith('data:image/svg+xml;base64,'))
ok('flow-v: markup in text, edge, detail and ids stays well-formed and escaped', wf(T(decision_tree([{'text': '<b>&"', 'detail': '<i>', 'children': [{'text': 'x', 'edge': '<u>'}]}], layout='flow-v', theme='css-vars', ids='"><x'))) and '<u>' not in T(decision_tree([{'text': 'a', 'children': [{'text': 'x', 'edge': '<u>'}]}], layout='flow-v'))['svg'])
fvd = [{'text': 'q' + str(i), 'detail': 'd', 'children': [{'text': 'k', 'edge': 'e'}]} for i in range(1)]
ok('flow-v: unknown theme noted; layout flow-v adds no unknown-layout note', any('theme zzz' in x for x in T(decision_tree(fvd, layout='flow-v', theme='zzz'))['notes']) and not any('layout' in x for x in fv['notes']))
fvl = T(decision_tree([{'text': 'word ' * 30, 'detail': 'w' * 200}], layout='flow-v'))
ok('flow-v limits: over-long text drawn shortened WITH A NOTE, table keeps full text; 6 levels still under 400 px and inside the viewBox', any('shortened' in x for x in fvl['notes']) and '…' in fvl['svg'] and 'w' * 120 in fvl['table'] and T(decision_tree([functools.reduce(lambda acc, _: {'text': 'x', 'edge': 'y', 'detail': 'dd', 'children': [acc]}, range(7), {'text': 'leaf'})], layout='flow-v'))['size'][0] < 400 and all(b['x'] + b['width'] <= fvl['size'][0] for b in flow_boxes(fvl)))
ok('flow-v: 31 fully loaded nodes stay inside the rich policy budgets and never raise', T(decision_tree([{'text': 'r' * 50, 'detail': 'd' * 120, 'edge': 'e' * 30, 'children': [{'text': 'c' * 50, 'detail': 'd' * 120, 'edge': 'e', 'children': [{'text': 'g' * 50, 'detail': 'd' * 120, 'edge': 'e'} for _ in range(14)]} for _ in range(2)]}], layout='flow-v'))['policy'] == 'rich')
ok('default and flow layouts unchanged by flow-v: same svg as before for the post 022 tree figure input', T(decision_tree(FLOW, title='Route', layout='flow'))['svg'] == fl['svg'] and T(decision_tree(FLOW))['svg'] == T(decision_tree(FLOW, layout='tree'))['svg'])
ok('flow NEGATIVE: cyclic structure draws to the level cap', T(decision_tree([cyc], layout='flow'))['levels'] == 6)
ok('flow NEGATIVE: non-string fields (numbers, NaN, huge ints, dict, list, bool, None) in text, edge, detail, outcome do not raise and are tolerated', isinstance(decision_tree([{'text': 'a', 'edge': float('nan'), 'detail': 10 ** 400, 'outcome': 'yes', 'children': [{'text': 'b', 'edge': {'x': 1}, 'detail': [1], 'outcome': None}, {'text': 'c', 'edge': 5, 'detail': 2.5, 'outcome': False}]}, 'plain', {'text': None}], layout='flow', theme=10 ** 400, ids=None), dict))
ok('flow: empty and non-list input give a note-only result', note_only(decision_tree([], layout='flow')) and note_only(decision_tree('x', layout='flow')))
ok('flow: number edge words are kept as text', 'If 5: ' in T(decision_tree([{'text': 'a', 'children': [{'text': 'b', 'edge': 5}]}], layout='flow'))['table'])
ok('flow: outcome false on a leaf draws a question box; outcome true on a parent draws a purple box', (lambda r: [b['stroke'] for b in flow_boxes(r)] == ['#6b5cff', '#d8dde6'])(T(decision_tree([{'text': 'a', 'outcome': True, 'children': [{'text': 'b', 'outcome': False}]}], layout='flow'))))
# default layout untouched by the new fields and options
base = lambda **k: decision_tree(TREE, **k)['tree']['svg']
withx = decision_tree([{'text': 'Root', 'edge': 'x', 'detail': 'd', 'outcome': True, 'children': [{'text': 'A', 'edge': 'y', 'children': [{'text': 'A1'}, {'text': 'A2'}, {'text': 'A3'}]}, {'text': 'B'}, {'text': 'C', 'children': [{'text': 'C1', 'children': [{'text': 'C1a'}, {'text': 'C1b'}]}]}]}])['tree']
ok('default layout: edge, detail, outcome, theme and ids are ignored (same svg, same nodes keys, no flow keys)', withx['svg'] == base() and base(theme='css-vars', ids='q') == base() and set(withx['nodes'][0]) == {'text', 'depth', 'parent', 'kids', 'i', 'row', 'drawn', 'x', 'w', 'y', 'h', 'shown', 'path'} and 'edges' not in withx and 'svg_img' not in withx)
ok('default layout: result policy is not rich and the base verifier accepts it', 'policy' not in decision_tree(TREE)['tree'] and verify_svg(base()) == base())
# ================= spring_nodes
def chain(k): return dict(nodes=[{'id': f'n{i}', 'label': f'N{i}'} for i in range(k)], edges=[{'a': i, 'b': i + 1} for i in range(k - 1)])
def tree12(): return dict(nodes=[{'id': str(i)} for i in range(12)], edges=[{'a': (i - 1) // 2, 'b': i} for i in range(1, 12)])
g = T(spring_nodes(**tree12())); g2 = T(spring_nodes(**tree12()))
ok('spring: bit-identical positions and svg between runs', g['pos'] == g2['pos'] and g['svg'] == g2['svg'])
rnd = random.Random(3); graphs = []
for trial in range(8):
    k = rnd.randint(3, 40); graphs.append(dict(nodes=[{'id': f'i{i}', 'label': f'L{i}', **({'size': rnd.choice([10, 20, 30])} if rnd.random() < .3 else {})} for i in range(k)], edges=[{'a': rnd.randrange(k), 'b': rnd.randrange(k)} for _ in range(rnd.randint(0, 2 * k))], height=rnd.choice([420, 600])))
R = [T(spring_nodes(**p)) for p in graphs]
def inbox(r): x0, y0, x1, y1 = r['box']; return all(x0 - 1e-6 <= x - rr and x + rr <= x1 + 1e-6 and y0 - 1e-6 <= y - rr and y + rr <= y1 + 1e-6 for (x, y), rr in zip(r['pos'], r['radii']))
ok('spring: no node outside the box (8 random graphs)', all(inbox(r) for r in R))
ok('spring: all discs inside the SVG too', all(all(0 <= x - rr and x + rr <= r['size'][0] and 0 <= y - rr and y + rr <= r['size'][1] for (x, y), rr in zip(r['pos'], r['radii'])) for r in R))
def mind(r): return min(math.hypot(r['pos'][i][0] - r['pos'][j][0], r['pos'][i][1] - r['pos'][j][1]) - r['radii'][i] - r['radii'][j] for i in range(len(r['pos'])) for j in range(i + 1, len(r['pos'])))
ok('spring: no two nodes closer than the minimum gap after settling (8 random graphs)', all(mind(r) >= r['gap'] - 1e-6 for r in R))
def avg(r, linked):
    L = {frozenset(l) for l in r['links']}; d = [math.hypot(r['pos'][i][0] - r['pos'][j][0], r['pos'][i][1] - r['pos'][j][1]) for i in range(len(r['pos'])) for j in range(i + 1, len(r['pos'])) if (frozenset((i, j)) in L) == linked]; return sum(d) / len(d)
ok('spring: linked nodes are closer on average than unlinked (binary tree, 12 nodes)', avg(g, True) < 0.6 * avg(g, False))
ok('spring: linked closer than unlinked on a 9-node chain too', avg(T(spring_nodes(**chain(9))), True) < avg(T(spring_nodes(**chain(9))), False))
ok('spring: a longer rest length spreads linked nodes further', avg(T(spring_nodes(**chain(5), rest_length=40)), True) < avg(T(spring_nodes(**chain(5), rest_length=130)), True))
def drawn(r):
    """Read the drawing back: circle centres in node order, label texts, and each line's endpoints matched to a circle."""
    rt = root(r); circ = [(float(c.attrib['cx']), float(c.attrib['cy']), float(c.attrib['r'])) for c in rt.iter(NS + 'circle')]; key = {f'{x:.1f},{y:.1f}': i for i, (x, y, _) in enumerate(circ)}
    lines = [(key.get(f'{float(l.attrib["x1"]):.1f},{float(l.attrib["y1"]):.1f}'), key.get(f'{float(l.attrib["x2"]):.1f},{float(l.attrib["y2"]):.1f}')) for l in rt.iter(NS + 'line')]
    return circ, lines, [tx.text for tx in rt.iter(NS + 'text')]
ok('spring INVERSE: every edge is drawn between exactly the two nodes it names (demo, 7 nodes)', (lambda r: sorted((frozenset(l) for l in drawn(r)[1]), key=sorted) == sorted((frozenset(l) for l in [(0, 1), (1, 2), (1, 3), (1, 4), (1, 5), (5, 6)]), key=sorted))(T(spring_nodes(**DEMOS['spring_nodes']))))
def edges_ok(p):
    r = T(spring_nodes(**p)); want = sorted({frozenset((e['a'], e['b'])) for e in p['edges'] if e['a'] != e['b']}, key=sorted); circ, lines, texts = drawn(r)
    return sorted((frozenset(l) for l in lines), key=sorted) == want and None not in [x for l in lines for x in l] and all(abs(c[0] - r['pos'][i][0]) < .06 and abs(c[1] - r['pos'][i][1]) < .06 for i, c in enumerate(circ))
ok('spring INVERSE: the same holds for 8 random graphs (duplicates merged, circles at the computed positions)', all(edges_ok(p) for p in graphs))
ok('spring INVERSE: each label is drawn under its own circle', (lambda r: (lambda circ, lines, texts: all(texts[i] == f'N{i}' for i in range(5)))(*drawn(r)))(T(spring_nodes(**chain(5)))))
dflt = T(spring_nodes()); ok('spring: no nodes gives the six default labelled nodes and their edges', len(dflt['pos']) == 6 and len(dflt['links']) == 6 and 'Database' in dflt['table'])
ok('spring: edges by id, by index and by numeric string all resolve', T(spring_nodes(nodes=[{'id': 'a'}, {'id': 'b'}, {'id': 'c'}], edges=[{'a': 'a', 'b': 1}, {'a': '1', 'b': 'c'}, {'from': 0, 'to': 2}]))['links'] == [(0, 1), (1, 2), (0, 2)])
bd = T(spring_nodes(nodes=[{'id': 'a'}, {'id': 'b'}], edges=[{'a': 0, 'b': 0}, {'a': 0, 'b': 9}, 'x', {'a': True, 'b': 1}, {'a': 0, 'b': 1}]))
ok('spring: self, unknown, non-object and boolean edge ends dropped and counted', bd['links'] == [(0, 1)] and any('4 edges were dropped' in x for x in bd['notes']))
dupe = T(spring_nodes(nodes=['a', 'b', 'c'], edges=[{'a': 0, 'b': 1}, {'a': 1, 'b': 0}, {'a': 0, 'b': 1, 'label': 'x'}, {'a': 1, 'b': 2}]))
ok('spring: repeated edges (either direction) merged into the first and counted', dupe['links'] == [(0, 1), (1, 2)] and any('2 repeated edges' in x for x in dupe['notes']))
nn = T(spring_nodes(nodes=[{'id': str(i)} for i in range(70)])); ok('spring: more than 60 nodes cut and noted', len(nn['pos']) == 60 and any('beyond the 60th' in x for x in nn['notes']))
big = [(i, j) for i in range(60) for j in range(i + 1, 60)]; random.Random(1).shuffle(big); t0 = time.time()
b60 = T(spring_nodes(nodes=[{'id': str(i), 'label': f'Node {i}'} for i in range(60)], edges=[{'a': a, 'b': b, 'label': 'e'} for a, b in big[:400]], height=520)); el = time.time() - t0
ok('spring: 60 nodes and 400 distinct edges fit the 80 KB / 4000-element policy by degrading (and say so)', len(b60['svg'].encode()) <= 80000 and len(re.findall(r'<[A-Za-z]', b60['svg'])) <= 4000 and any('left out' in x for x in b60['notes']))
ok('spring: the 60-node case settles in under 4 s and keeps the gap and the box', el < 4 and mind(b60) >= b60['gap'] - 1e-6 and inbox(b60))
ok('spring: height clamped to 160..1200', T(spring_nodes(**chain(3), height=10))['size'][1] == 160 and T(spring_nodes(**chain(3), height=99999))['size'][1] == 1200 and T(spring_nodes(**chain(3), height='abc'))['size'][1] == 420 and T(spring_nodes(**chain(3), height=1e308))['size'][1] == 1200)
ok('spring: colour, bg and interactive are ignored with notes (palette stays fixed)', all(any(k in x for x in T(spring_nodes(**chain(3), colour='#ff0000', bg='#000000', interactive=True))['notes']) for k in ('colour', 'interactive')) and 'ff0000' not in T(spring_nodes(**chain(3), colour='#ff0000'))['svg'])
ok('spring: an unknown option (a title) is ignored WITH a note', any('Unknown option ignored: title' in x for x in T(spring_nodes(**chain(3), title='T'))['notes']))
ok('spring: fewer than 2 nodes gives a note-only Result', note_only(spring_nodes(nodes=[{'id': 'a'}])))
ok('spring: text alternative lists every node with its degree and every link', all(f'N{i} ({2 if 0 < i < 4 else 1} links)' in T(spring_nodes(**chain(5)))['table'] for i in range(5)) and 'N3 to N4' in T(spring_nodes(**chain(5)))['table'])
ok('spring: alt text carries node and link counts', '5 nodes, 4 links' in T(spring_nodes(**chain(5)))['alt'])
ok('spring: node size honoured between 8 and 48, else 16', T(spring_nodes(nodes=[{'id': 'a', 'size': 30}, {'id': 'b', 'size': 99}, {'id': 'c', 'size': 'x'}]))['radii'] == [30.0, 16.0, 16.0])
ok('spring: markup in labels is escaped and well-formed', wf(T(spring_nodes(nodes=[{'id': 'a', 'label': '<i>&"'}, {'id': 'b'}], edges=[{'a': 0, 'b': 1, 'label': '<e>'}]))))
ok('spring: version 2 drawn as 1 with a note', any('version 1' in x for x in T(spring_nodes(version=2))['notes']))
ok('spring: text is at least 14px and every SVG is small', all(f >= 14 for f in fonts(g)) and max(len(r['svg']) for r in R) < 80000)
ok('spring: only palette and ink colours', colours(g) <= SVG_COLOURS)
ok('spring: edge label drawn at the edge middle', 'lbl' in T(spring_nodes(nodes=[{'id': 'a'}, {'id': 'b'}], edges=[{'a': 0, 'b': 1, 'label': 'lbl'}]))['svg'])
fin = lambda r: all(math.isfinite(c) for p in r['pos'] for c in p)
ok('spring NEGATIVE: rest_length 1e308 with 400 duplicate edges: finite positions, clamped, merged', (lambda r: fin(r) and any('clamped to 400' in x for x in r['notes']) and any('399 repeated' in x for x in r['notes']))(T(spring_nodes(nodes=['a', 'b'], edges=[{'a': 0, 'b': 1}] * 400, rest_length=1e308))))
ok('spring NEGATIVE: rest_length NaN / -5 / 0 / 10**400 / True give the default 110', all(T(spring_nodes(**chain(3), rest_length=v))['rest'] == 110.0 for v in (float('nan'), -5, 0, 10**400, True)))
ok('spring NEGATIVE: 10**400 as size, label, id, height, edge end; NaN size; dict and list ids', (lambda r: fin(r) and len(r['pos']) == 4)(T(spring_nodes(nodes=[{'id': {'a': 1}, 'label': [1]}, {'id': 10**400, 'label': 10**400, 'size': 10**400}, {'id': 'x', 'size': float('nan')}, {'id': ['q']}], edges=[{'a': {'x': 1}, 'b': [1]}, {'a': 10**400, 'b': 1}], height=10**400, rest_length=10**400))))
# ================= voronoi
def rsites(seed, k, w=100, h=60):
    r = random.Random(seed); pts = set()
    while len(pts) < k: pts.add((round(r.uniform(0, w), 3), round(r.uniform(0, h), 3)))
    return [{'x': x, 'y': y} for x, y in sorted(pts)]
def inside(p, poly, tol=1e-6):
    s = [(poly[(i + 1) % len(poly)][0] - poly[i][0]) * (p[1] - poly[i][1]) - (poly[(i + 1) % len(poly)][1] - poly[i][1]) * (p[0] - poly[i][0]) for i in range(len(poly))]
    return all(v >= -tol for v in s) or all(v <= tol for v in s)
def to_px(r, x, y):
    """Independent data -> drawing map, from the box and bounds the result reports."""
    X0, Y0, X1, Y1 = r['box']; xlo, xhi, ylo, yhi = r['bounds']; return (X0 + (x - xlo) / (xhi - xlo) * (X1 - X0), Y1 - (y - ylo) / (yhi - ylo) * (Y1 - Y0))
def to_data(r, px, py):
    X0, Y0, X1, Y1 = r['box']; xlo, xhi, ylo, yhi = r['bounds']; return (xlo + (px - X0) / (X1 - X0) * (xhi - xlo), ylo + (Y1 - py) / (Y1 - Y0) * (yhi - ylo))
def data_nearest(r, x, y):
    S = r['sites']; return min(range(len(S)), key=lambda i: math.hypot(S[i]['x'] - x, S[i]['y'] - y))
def reverse_ok(r, seed, k=400):
    """A random DATA point, mapped into the drawing, must lie in the cell of the site that is nearest IN DATA UNITS."""
    rr = random.Random(seed); xlo, xhi, ylo, yhi = r['bounds']
    for _ in range(k):
        x, y = rr.uniform(xlo, xhi), rr.uniform(ylo, yhi); i = data_nearest(r, x, y)
        if not inside(to_px(r, x, y), r['sites'][i]['poly'], 1e-5): return False
    return True
def forward_ok(r, seed):
    """Random points inside each drawn cell, mapped back to data, must be nearest (in data units) to the cell's own site."""
    rr = random.Random(seed); S = r['sites']
    for i, s in enumerate(S):
        pl = s['poly']
        for _ in range(10):
            w = [rr.random() for _ in pl]; z = sum(w); p = (sum(a * q[0] for a, q in zip(w, pl)) / z, sum(a * q[1] for a, q in zip(w, pl)) / z); x, y = to_data(r, *p)
            dm = math.hypot(S[i]['x'] - x, S[i]['y'] - y)
            if any(math.hypot(o['x'] - x, o['y'] - y) < dm * (1 - 1e-9) - 1e-12 for o in S): return False
    return True
sets_ = [rsites(s, k) for s, k in ((1, 3), (2, 8), (3, 25), (4, 60), (5, 150))]; V = [T(voronoi(s)) for s in sets_]
tall = [{'x': round(x / 100, 4), 'y': y} for x, y in ((a['x'], a['y'] * 10) for a in rsites(7, 30))]; VT = T(voronoi(tall))       # x in 0..1, y in 0..600: aspect clamp applies
wideaspect = T(voronoi([{'x': a['x'] * 10, 'y': a['y'] / 10} for a in rsites(8, 30)]))
ok('voronoi: the aspect clamp applies to the tall and the wide sets, and says so', all(any('clamped' in x for x in r['notes']) for r in (VT, wideaspect)) and not any('clamped' in x for x in V[2]['notes']))
ok('voronoi DATA UNITS: cell areas sum to the box area in data units (also when clamped)', all(abs(sum(s['area'] for s in r['sites']) - r['data_area']) < 1e-9 * r['data_area'] for r in V + [VT, wideaspect]))
ok('voronoi: shares add up to 100%', all(abs(sum(s['share'] for s in r['sites']) - 1) < 1e-9 for r in V + [VT, wideaspect]))
ok('voronoi: every cell contains its own site (drawn positions)', all(inside((s['px'], s['py']), s['poly']) for r in V + [VT, wideaspect] for s in r['sites']))
ok('voronoi DATA UNITS: a random data point lies in the cell of its nearest site in data units (5 sets, 400 points each)', all(reverse_ok(r, 4) for r in V))
ok('voronoi DATA UNITS under a CLAMPED aspect: x 0..1 and y 0..600; and x 0..1000, y 0..6 (400 points each)', reverse_ok(VT, 5, 800) and reverse_ok(wideaspect, 6, 800))
ok('voronoi DATA UNITS: points inside each drawn cell, mapped back to data, are nearest to their own site (all 7 sets)', all(forward_ok(r, 9) for r in V + [VT, wideaspect]))
ok('voronoi DATA UNITS: the drawn site position is the data position under the reported bounds', all(abs(s['px'] - to_px(r, s['x'], s['y'])[0]) < 1e-6 and abs(s['py'] - to_px(r, s['x'], s['y'])[1]) < 1e-6 for r in V + [VT] for s in r['sites']))
ok('voronoi: cells are inside the plot box', all(r['box'][0] - 1e-6 <= x <= r['box'][2] + 1e-6 and r['box'][1] - 1e-6 <= y <= r['box'][3] + 1e-6 for r in V + [VT] for s in r['sites'] for x, y in s['poly']))
sq = T(voronoi([{'x': 0, 'y': 0}, {'x': 10, 'y': 0}, {'x': 0, 'y': 10}, {'x': 10, 'y': 10}])); ok('voronoi: four symmetric sites each own 25% (independent arithmetic)', all(abs(s['share'] - .25) < 1e-9 for s in sq['sites']))
two = T(voronoi([{'x': 0, 'y': 0}, {'x': 10, 'y': 10}, {'x': 10, 'y': 0}])); ok('voronoi: plot box at least a third and at most the full width high', all(200 - 1e-6 <= (r['box'][3] - r['box'][1]) <= 600 + 1e-6 for r in V + [VT, wideaspect, two]))
DMO = T(voronoi(**DEMOS['voronoi'])); rt = root(DMO)
def reads(r):
    rt = root(r); frame = next(e for e in rt.iter(NS + 'rect') if e.attrib.get('fill') == 'none'); fx, fy, fw, fh = (float(frame.attrib[k]) for k in ('x', 'y', 'width', 'height'))
    dots = [(float(c.attrib['cx']), float(c.attrib['cy'])) for c in rt.iter(NS + 'circle')]; return fx, fy, fw, fh, dots
def margins_ok(r):
    fx, fy, fw, fh, dots = reads(r); xs = [d[0] for d in dots]; ys = [d[1] for d in dots]; mx, my = 0.05 * (max(xs) - min(xs)), 0.05 * (max(ys) - min(ys))
    return min(xs) - fx >= mx - 1e-6 and fx + fw - max(xs) >= mx - 1e-6 and min(ys) - fy >= my - 1e-6 and fy + fh - max(ys) >= my - 1e-6
EDGE = T(voronoi([{'x': 0, 'y': 0}, {'x': 100, 'y': 60}, {'x': 100, 'y': 0}, {'x': 40, 'y': 30}]))
ok('voronoi INVERSE: the frame leaves at least 5% of the sites\' spread free on every side (read from the circles and the frame)', margins_ok(EDGE) and margins_ok(DMO) and all(margins_ok(r) for r in V))
def tick_texts(r, axis):
    rt = root(r); X0, Y0, X1, Y1 = r['box']; out = []
    for tx in rt.iter(NS + 'text'):
        a = tx.attrib
        if axis == 'x' and a['text-anchor'] == 'middle' and abs(float(a['y']) - (Y1 + 20)) < .01: out.append((float(a['x']), tx.text))
        if axis == 'y' and a['text-anchor'] == 'end' and abs(float(a['x']) - (X0 - 8)) < .01: out.append((float(a['y']) - 5, tx.text))
    return out
def ticks_ok(r):
    xlo, xhi, ylo, yhi = r['bounds']; X0, Y0, X1, Y1 = r['box']; ox, oy = tick_texts(r, 'x'), tick_texts(r, 'y')
    fx = all(abs(num(tx) - (xlo + (p - X0) / (X1 - X0) * (xhi - xlo))) <= 0.006 + 1e-9 * abs(xhi) for p, tx in ox); fy = all(abs(num(tx) - (ylo + (Y1 - p) / (Y1 - Y0) * (yhi - ylo))) <= 0.006 + 1e-9 * abs(yhi) for p, tx in oy)
    return len(ox) >= 3 and len(oy) >= 3 and fx and fy and abs(num(ox[0][1]) - xlo) < 1e-6 and abs(num(oy[0][1]) - ylo) < 1e-6
ok('voronoi INVERSE: every x and y tick label equals the data value at its drawn position, and the first tick is the bound', ticks_ok(DMO) and ticks_ok(EDGE) and ticks_ok(V[2]))
def legend(r):
    rt = root(r); items = []; els = list(rt.iter())
    for i, e in enumerate(els):
        if e.tag == NS + 'rect' and e.attrib.get('width') == '16' and e.attrib.get('height') == '16': items.append((els[i + 1].text, e.attrib['fill']))
    return items
def regions(r):
    rt = root(r); out = {}
    for p in rt.iter(NS + 'path'):
        t = p.find(NS + 'title')
        if t is not None: out[t.text.split(':')[0]] = p.attrib['fill']
    return out
lg = legend(DMO); rg = regions(DMO)
ok('voronoi INVERSE: the legend has one swatch per group, named, in the colour that fills that group\'s regions', [x[0] for x in lg] == ['Depot', 'Hub'] and len({x[1] for x in lg}) == 2 and all(rg[s['label']] == dict(lg)[s['group']] for s in DMO['sites']))
ok('voronoi: ungrouped sites have no legend and share one fill', legend(V[2]) == [] and len(set(regions(V[2]).values())) == 1)
ok('voronoi: legend colours are the palette hues lightened (and different groups differ)', {c for _, c in lg} <= blends())
dup = T(voronoi([{'x': 1, 'y': 1, 'label': 'a'}, {'x': 1, 'y': 1, 'label': 'b'}, {'x': 5, 'y': 1}, {'x': 3, 'y': 9}])); ok('voronoi: a site at an earlier site\'s position is merged, with a note', len(dup['sites']) == 3 and dup['sites'][0]['label'] == 'a' and any('merged' in x for x in dup['notes']))
bad_ = T(voronoi(sets_[0] + [{'x': 'a', 'y': 1}, {'x': float('nan'), 'y': 1}, {'x': 1e13, 'y': 0}, {'x': True, 'y': 1}, 'junk', {'y': 3}]))
ok('voronoi: unusable entries left out and counted', len(bad_['sites']) == 3 and any('6 entries were left out' in x for x in bad_['notes']))
ok('voronoi: fewer than 3 distinct sites gives a note-only Result', note_only(voronoi([{'x': 0, 'y': 0}, {'x': 1, 'y': 1}])) and note_only(voronoi([{'x': 0, 'y': 0}] * 5)) and note_only(voronoi('x')))
bg = T(voronoi(rsites(8, 200) + rsites(9, 20)[:5])); ok('voronoi: sites beyond the 200th are noted and not used', len(bg['sites']) <= 200 and any('beyond the 200th' in x for x in bg['notes']))
ok('voronoi: 200 sites still tile the box (data units), SVG within the policy', abs(sum(s['area'] for s in bg['sites']) - bg['data_area']) < 1e-9 * bg['data_area'] and len(bg['svg'].encode()) < 80000)
lab = T(voronoi([{'x': 0, 'y': 0, 'label': 42, 'group': 7}, {'x': 9, 'y': 1, 'label': ['x'], 'group': {'a': 1}}, {'x': 4, 'y': 8, 'label': 'z' * 40, 'value': 3.5}], unit='km'))
ok('voronoi: numeric label kept, list label becomes "Site n", long label cut to 24', [s['label'] for s in lab['sites']] == ['42', 'Site 2', 'z' * 24] and lab['sites'][0]['group'] == '7' and lab['sites'][1]['group'] is None)
ok('voronoi: table lists every site with x, y, group, value with unit and share', all(f'at x {f}' in lab['table'] for f in ('0', '9', '4')) and 'value 3.5 km' in lab['table'] and 'group 7' in lab['table'] and '% of the area' in lab['table'])
ok('voronoi: alt text names the site count and the largest region with the same share as the table', (lambda b: f'{len(lab["sites"])} sites' in lab['alt'] and b['label'] in lab['alt'] and f'{b["share"]*100:.1f}%' in lab['alt'] and f'{b["share"]*100:.1f}% of the area' in lab['table'])(max(lab['sites'], key=lambda s: s['area'])))
ok('voronoi: the hover title of each region carries its share, its value and its unit', all('value' in tt and 'km' in tt for tt in [p.find(NS + 'title').text for p in root(T(voronoi(**DEMOS['voronoi'], ))).iter(NS + 'path') if p.find(NS + 'title') is not None]) and 'value 120' in ' '.join(p.find(NS + 'title').text for p in rt.iter(NS + 'path') if p.find(NS + 'title') is not None))
ok('voronoi: well-formed, deterministic', wf(DMO) and voronoi(**DEMOS['voronoi'])['voronoi']['svg'] == voronoi(**DEMOS['voronoi'])['voronoi']['svg'])
ok('voronoi: markup in labels, title, units and axis labels stays well-formed and escaped', wf(T(voronoi([{'x': 0, 'y': 0, 'label': '<b>&"'}, {'x': 5, 'y': 0, 'group': '<g>'}, {'x': 2, 'y': 5}], title='<t>&', x_label='<x>', y_label='"y"', unit='<u>'))))
ok('voronoi: collinear sites are drawn (strips tile the box in data units)', (lambda r: abs(sum(s['area'] for s in r['sites']) - r['data_area']) < 1e-9 * r['data_area'] and reverse_ok(r, 3))(T(voronoi([{'x': i, 'y': 2} for i in (0, 3, 4, 9, 12)]))))
ok('voronoi: version 2 drawn as 1 with a note', any('version 1' in x for x in T(voronoi(sets_[0], version=2))['notes']))
ok('voronoi: text at least 14px, only palette colours (lightened hues allowed)', all(f >= 14 for f in fonts(DMO)) and colours(DMO) <= SVG_COLOURS | blends())
ok('voronoi: a site whose label does not fit keeps it out of the picture but in the table', (lambda r: any(not s['shown'] for s in r['sites']) and all(s['label'] in r['table'] for s in r['sites']))(T(voronoi([{'x': i * .01, 'y': (i % 7) * .01, 'label': f'Name{i}'} for i in range(60)]))))
for e in (1e-11, 1e-14, 1e-100):
    t0 = time.time(); tiny = T(voronoi([{'x': 0, 'y': 0}, {'x': e, 'y': 0}, {'x': 0, 'y': e}])); ntx = len(list(root(tiny).iter(NS + 'text')))
    ok(f'voronoi NEGATIVE: span {e:g} finishes at once with a bounded drawing (<= 60 text elements, < 20 KB) and tiles the box', time.time() - t0 < 2 and ntx <= 60 and len(tiny['svg']) < 20000 and abs(sum(s['share'] for s in tiny['sites']) - 1) < 1e-9 and reverse_ok(tiny, 2, 100))
ok('voronoi NEGATIVE: ticks are bounded (<= 24 per axis) for odd bounds', all(len(tick_texts(r, a)) <= 24 for r in V + [VT, wideaspect, tiny] for a in 'xy'))
ok('voronoi NEGATIVE: a span of 1e-300 (all but one position) or all sites within 1e-13 of the coordinates gives a note-only Result, not a hang', note_only(voronoi([{'x': 0, 'y': 0}, {'x': 1e-300, 'y': 0}, {'x': 0, 'y': 1e-300}])) and note_only(voronoi([{'x': 5e11, 'y': 5e11}, {'x': 5e11 + 1e-3, 'y': 5e11}, {'x': 5e11, 'y': 5e11 + 1e-3}])))
ok('voronoi NEGATIVE: large offsets keep the cells exact (x near 1e11)', (lambda r: reverse_ok(r, 8, 200) and abs(sum(s['share'] for s in r['sites']) - 1) < 1e-9)(T(voronoi([{'x': 1e11 + a['x'], 'y': a['y']} for a in rsites(11, 20)]))))
ok('voronoi NEGATIVE: 10**400, NaN, dict and list in coordinates, labels, groups, values, units, title do not raise', isinstance(voronoi([{'x': 10**400, 'y': 1}, {'x': 0, 'y': 0, 'label': 10**400, 'group': {'a': 1}, 'value': 10**400}, {'x': 1, 'y': 1, 'label': [1], 'value': float('nan')}, {'x': 2, 'y': 0}, {'x': 3, 'y': 3}], title=10**400, unit=10**400, x_label=float('nan'), y_label={'a': 1}, version=10**400), dict))
# ================= hostile-input sweep through d3pack.call (the production entry point): only success or a plain MacroError, never a crash message
HOSTILE = [None, True, 0, -1, 1.5, 1e308, -1e308, float('nan'), float('inf'), 10**400, -10**400, '', 'x' * 300, '<b>&"‮\x00', [], {}, [[]], {'a': [1]}, [1, 'a'], [None] * 3]
def leaves(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items(): yield from leaves(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o[:6]): yield from leaves(v, path + (i,))
    else: yield path
def setp(o, path, v):
    o = copy.deepcopy(o); cur = o
    for k in path[:-1]: cur = cur[k]
    cur[path[-1]] = v; return o
def sweep(name, params):
    fails = 0; runs = 0
    for path in leaves(params):
        for hv in HOSTILE:
            p = setp(params, path, hv) if path else params; runs += 1
            try: r = D.call(name, p, isolate=False)
            except D.MacroError as e:
                if any(k in str(e) for k in ('failed on this input', 'too deeply', 'time budget', 'memory', 'output policy')): fails += 1; print('   ', name, path, repr(hv)[:30], str(e)[:80])
                continue
            except Exception as e: fails += 1; print('   ', name, path, repr(hv)[:30], type(e).__name__, str(e)[:60]); continue
            for k, v in r.items():
                if k != '_default':
                    try: verify_svg(v['svg'])
                    except Exception: fails += 1; print('   policy', name, path, repr(hv)[:30])
    return fails, runs
for name in ('decision_tree', 'spring_nodes', 'voronoi'):
    f, runs = sweep(name, DEMOS[name]); ok(f'sweep: {name}: {runs} hostile single-value substitutions, no crash, no policy violation', f == 0)
# ================= A2UI messages for every macro (demos), with negative controls
ok('registry: three macros, named as the atoms', set(PACK_NETWORKS) == {'decision_tree', 'spring_nodes', 'voronoi'} == set(DEMOS))
for name, fn in PACK_NETWORKS.items():
    out = fn(**DEMOS[name]); default = out.pop('_default'); create, updates = atom_card('T', out, default)
    ok(f'{name}: createSurface validates', not list(A2R.iter_errors(create))); ok(f'{name}: every update validates', all(not list(A2R.iter_errors(u)) for u in updates.values()))
    ok(f'{name}: only Basic components', {c['component'] for c in create['createSurface']['components']} <= {'Card', 'Column', 'Row', 'Text', 'Image', 'Button'})
    ids = {c['id'] for c in create['createSurface']['components']}; refs = set()
    for c in create['createSurface']['components']: refs |= set(c.get('children', [])) | ({c['child']} if 'child' in c else set())
    ok(f'{name}: child references resolve', refs <= ids); ok(f'{name}: image description and table bound to the data model', create['createSurface']['dataModel']['alt'] and create['createSurface']['dataModel']['table'])
    ok(f'{name}: payload under 200 KB', len(json.dumps(create)) < 200_000)
    b1 = copy.deepcopy(create); b1['version'] = 'v1.0'; ok(f'{name}: negative: bad version rejected', bool(list(A2R.iter_errors(b1))))
    b2 = copy.deepcopy(create); b2['createSurface']['components'][2]['component'] = 'Chart'; ok(f'{name}: negative: unknown component rejected', bool(list(A2R.iter_errors(b2))))
    b3 = copy.deepcopy(list(updates.values())[0]); del b3['updateDataModel']['surfaceId']; ok(f'{name}: negative: update without surfaceId rejected', bool(list(A2R.iter_errors(b3))))
    c2, u2, r2 = D.card(name, 'T', DEMOS[name]); ok(f'{name}: card() builds a valid surface through the isolated runner', not list(A2R.iter_errors(c2)))
print(f'networks tests: {n} checks, {bad} failed'); sys.exit(1 if bad else 0)
