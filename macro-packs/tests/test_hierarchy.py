"""Hierarchy group tests (treemap). d3 macro pack tests: independent arithmetic on each layout, the atoms' tolerant-reader rules, guard rails, determinism, and every message validated against the
upstream A2UI 1.0 schemas (with negative controls). No model, no browser, no network. Run: A2UI_UPSTREAM=<upstream checkout> python3 -B tests/test_hierarchy.py"""
import calendar as cal, datetime as dt, glob, json, math, random, re, sys, copy
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
from d3pack import treemap as TM
from d3pack.registry_hierarchy import PACK_HIERARCHY
from d3pack.demos_hierarchy import DEMOS
import ast
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
def raises(fn):
    try: fn(); return False
    except ValueError: return True
def wf(r):
    ET.fromstring(r['svg']); return True

GOLD_SRC = (Path(__file__).resolve().parents[2] / 'tests' / 'test_treemap_squarify.py').read_text()
GOLDEN = next(ast.literal_eval(nd.value) for nd in ast.parse(GOLD_SRC).body if isinstance(nd, ast.Assign) and getattr(nd.targets[0], 'id', '') == 'GOLDEN')
def tile_ok(rects, box, tol=1e-6, otol=None):
    """Independent: areas sum to the box, no pair overlaps (positive-area intersection), every rect inside the box."""
    otol = tol if otol is None else otol; x0, y0, x1, y1 = box; area = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects)
    if abs(area - (x1 - x0) * (y1 - y0)) > tol * (x1 - x0) * (y1 - y0): return False
    for i, a in enumerate(rects):
        if a[0] < x0 - tol or a[1] < y0 - tol or a[2] > x1 + tol or a[3] > y1 + tol: return False
        for b in rects[i + 1:]:
            if min(a[2], b[2]) - max(a[0], b[0]) > otol and min(a[3], b[3]) - max(a[1], b[1]) > otol: return False
    return True
IT = DEMOS['treemap']['items']; BOX = (TM.BX0, TM.BY0, TM.BX1, TM.BY1); TOT = sum(i['value'] for i in IT)
tm = PACK_HIERARCHY['treemap']; R = tm(IT, unit='k USD')
for lay in ('squarified', 'columns'):
    rc = R[lay]['rects']; box_area = (BOX[2] - BOX[0]) * (BOX[3] - BOX[1])
    ok(f'treemap {lay}: every rectangle area is proportional to its value', all(abs((r['x1'] - r['x0']) * (r['y1'] - r['y0']) - box_area * r['value'] / TOT) < 1e-6 for r in rc))
    ok(f'treemap {lay}: rectangles tile the box with no overlap and no gap', tile_ok([(r['x0'], r['y0'], r['x1'], r['y1']) for r in rc], BOX))
    ok(f'treemap {lay}: category rectangles tile the box and are sized by category total', tile_ok(list(R[lay]['cats'].values()), BOX) and all(abs((c[2] - c[0]) * (c[3] - c[1]) - box_area * sum(i['value'] for i in IT if i['category'] == k) / TOT) < 1e-6 for k, c in R[lay]['cats'].items()))
    ok(f'treemap {lay}: each item lies inside its category rectangle', all(R[lay]['cats'][r['category']][0] - 1e-6 <= r['x0'] and r['x1'] <= R[lay]['cats'][r['category']][2] + 1e-6 and R[lay]['cats'][r['category']][1] - 1e-6 <= r['y0'] and r['y1'] <= R[lay]['cats'][r['category']][3] + 1e-6 for r in rc))
    ok(f'treemap {lay}: well-formed SVG', wf(R[lay]))
    ok(f'treemap {lay}: one rect per item drawn', R[lay]['svg'].count('<title>') == len(IT) and len(rc) == len(IT))
ok('treemap: columns variant = one full-height column per category, items stacked', all(abs(c[1] - BOX[1]) < 1e-9 and abs(c[3] - BOX[3]) < 1e-9 for c in R['columns']['cats'].values()))
ok('treemap: default variant is squarified', R['_default'] == 'squarified')
# against real d3-hierarchy 3.1.2 rectangles recorded in the atom repo's golden file (scaled from its 900x300 box to ours)
for name, case in GOLDEN.items():
    its = case['items']; cats = []
    for i in its:
        if i['category'] not in cats: cats.append(i['category'])
    kept = [i for i in its if i['category'] in cats[:4]]; cats = cats[:4]
    vals = [sum(i['value'] for i in kept if i['category'] == c) for c in cats]
    cr = TM.squarify(vals, 0, 0, 900, 300); good = all(abs(a - b) < 1e-6 for r, g in zip(cr, case['cats']) for a, b in zip(r, g))
    for c, g in zip(cats, case['rects']):
        rr = TM.squarify([i['value'] for i in kept if i['category'] == c], *cr[cats.index(c)]); good = good and all(abs(a - b) < 1e-6 * max(1, abs(b)) + 1e-6 for r, gg in zip(rr, g) for a, b in zip(r, gg))
    ok(f'treemap: squarify matches real d3 golden "{name}"', good)
ok('treemap: input order kept inside a category (no sorting)', [r['name'] for r in R['squarified']['rects'] if r['category'] == 'Data'] == ['Warehouse', 'Streams', 'Catalog'])
ok('treemap: table holds item, category, value and share for every item', all(f"{i['category']}/{i['name']} {i['value']}" in R['squarified']['table'] and '%)' in R['squarified']['table'] for i in IT))
shares = [float(x) for x in re.findall(r'\((\d+\.\d)%\)', R['squarified']['table'])]; ok('treemap: shares in the table add up to 100', abs(sum(shares) - 100) < 0.5 and shares[0] == round(100 * 40 / TOT, 1))
ok('treemap: alt text built from the same numbers (total and largest)', 'Total 158' in R['squarified']['alt'] and 'VMs (40, 25%)' in R['squarified']['alt'] and 'k USD' in R['squarified']['alt'])
rn = tm([{'category': 'A', 'name': 'a', 'value': 5}, {'category': 'A', 'name': 'b', 'value': -1}, {'category': 'B', 'name': 'c', 'value': 0}, 'junk', {'category': 'B', 'name': 'd', 'value': float('nan')}, {'category': 'B', 'name': 'e', 'value': True}, {'category': 'B', 'name': 'f', 'value': 3}])
ok('treemap: items with value <= 0, non-numbers and non-objects dropped and counted', any('5 items were left out' in x for x in rn['squarified']['notes']) and len(rn['squarified']['rects']) == 2)
ok('treemap: fewer than 4 usable items drawn with a note', any('4 to 12' in x for x in rn['squarified']['notes']))
r5 = tm([{'category': c, 'name': 'n' + c, 'value': v} for c, v in zip('ABCDE', (1, 2, 3, 4, 5))])
ok('treemap: a fifth category is not drawn and counted', len(r5['squarified']['cats']) == 4 and 'E' not in r5['squarified']['cats'] and any('beyond the 4th' in x for x in r5['squarified']['notes']))
ok('treemap: items beyond the 12th cut and noted', any('beyond the 12th' in x for x in tm([{'category': 'A', 'name': str(i), 'value': 1} for i in range(15)])['squarified']['notes']) and len(tm([{'category': 'A', 'name': str(i), 'value': 1} for i in range(15)])['squarified']['rects']) == 12)
ok('treemap: version 2 drawn as 1 with a note', any('version 1' in x for x in tm(IT, version=2)['squarified']['notes']))
ok('treemap: nothing usable refused', raises(lambda: tm([{'category': 'A', 'name': 'a', 'value': 0}])) and raises(lambda: tm('x')) and raises(lambda: tm([])))
rm = tm([{'name': 'x', 'value': 1}, {'category': 7, 'name': 3.5, 'value': 2}, {'category': 'A' * 50, 'name': 'B' * 50, 'value': 2}, {'category': None, 'name': None, 'value': 1}])
ok('treemap: missing category becomes Other, numbers become text, long text truncated', 'Other/x' in rm['squarified']['table'] and '7/3.5' in rm['squarified']['table'] and 'A' * 20 + '/' + 'B' * 24 + ' ' in rm['squarified']['table'] and 'A' * 21 not in rm['squarified']['table'])
ok('treemap: markup in labels stays well-formed and escaped', wf(tm([{'category': '<c>&"', 'name': '<b>&"', 'value': 1}, {'category': 'x', 'name': "o'k", 'value': 2}])['squarified']) and '<b>' not in tm([{'category': 'c', 'name': '<b>', 'value': 1}, {'category': 'x', 'name': 'k', 'value': 2}])['squarified']['svg'])
ok('treemap: deterministic', tm(IT)['squarified']['svg'] == tm(IT)['squarified']['svg'] and tm(IT)['columns']['svg'] == tm(IT)['columns']['svg'])
ok('treemap: SVG under 60 KB', all(len(R[l]['svg']) < 60_000 for l in ('squarified', 'columns')))
ok('treemap: only palette colours (plus white / ink)', set(re.findall(r'fill="(#[0-9a-f]{6})"', R['squarified']['svg'])) <= {D.common.blend(p, t / 100) for p in D.common.PAL for t in range(0, 51)} | {'#ffffff', '#111111', '#000000', D.common.FACE, D.common.INK})
fs = [int(x) for x in re.findall(r'font-size="(\d+)"', R['squarified']['svg'])]; ok('treemap: text is at least 14 px', fs and min(fs) >= 14)
ok('treemap: two items of equal value in one category split the category in half', abs(((lambda q: (q[0][2] - q[0][0]) * (q[0][3] - q[0][1]) / ((q[1][2] - q[1][0]) * (q[1][3] - q[1][1])))(TM.squarify([3, 3], 0, 0, 100, 50))) - 1) < 1e-9)
ok('treemap: squarify of a single value fills the box', TM.squarify([7], 0, 0, 90, 30) == [(0, 0, 90, 30)])
rnd = random.Random(3); good = True
for _ in range(40):
    vs = [rnd.choice([0.5, 1, 2, 7, 30, 100]) for _ in range(rnd.randint(1, 12))]; good = good and tile_ok(TM.squarify(vs, 5, 7, 305, 207), (5, 7, 305, 207)) and all(abs((r[2] - r[0]) * (r[3] - r[1]) - 300 * 200 * v / sum(vs)) < 1e-6 for r, v in zip(TM.squarify(vs, 5, 7, 305, 207), vs))
ok('treemap: 40 random value lists tile an offset box with areas proportional', good)
ok('treemap: squarified aspect ratios are no worse than a plain slice of the same list', (lambda vs: max(max((r[2] - r[0]) / (r[3] - r[1]), (r[3] - r[1]) / (r[2] - r[0])) for r in TM.squarify(vs, 0, 0, 600, 400)) < max(max((r[2] - r[0]) / (r[3] - r[1]), (r[3] - r[1]) / (r[2] - r[0])) for r in TM.stack(vs, 0, 0, 600, 400)))([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]))
# ---------- nested mode (path)
NI = [{'path': ['Eng', 'Web'], 'name': 'ui', 'value': 30}, {'path': ['Eng', 'Web'], 'name': 'api', 'value': 20}, {'path': ['Eng', 'Data', 'ETL'], 'name': 'jobs', 'value': 25}, {'path': ['Eng', 'Data', 'ETL'], 'name': 'logs', 'value': 5},
      {'path': ['Eng'], 'name': 'misc', 'value': 8}, {'path': ['Ops'], 'name': 'pager', 'value': 12}, {'path': ['Ops', 'Cloud'], 'name': 'vms', 'value': 40}, {'category': 'Legal', 'name': 'review', 'value': 10}, {'name': 'orphan', 'value': 6}]
NR = tm(NI, unit='GB'); NN = NR['squarified']; nodes = NN['nodes']; byid = {r['id']: r for r in nodes}; NT = sum(i['value'] for i in NI)
kids = {}
for r in nodes: kids.setdefault(r['parent'], []).append(r)
rootkids = [r for r in nodes if r['depth'] == 0]
ok('nested: only the squarified variant is produced', set(NR) == {'squarified', '_default'})
ok('nested: top-level nodes tile the whole box', tile_ok([(r['x0'], r['y0'], r['x1'], r['y1']) for r in rootkids], BOX))
ok('nested: top-level areas proportional to totals', all(abs((r['x1'] - r['x0']) * (r['y1'] - r['y0']) - (BOX[2] - BOX[0]) * (BOX[3] - BOX[1]) * r['value'] / NT) < 1e-6 for r in rootkids))
groups = [r for r in nodes if r['group']]
ok('nested: children of every group tile its content box exactly (no overlap, no gap)', all(tile_ok([(c['x0'], c['y0'], c['x1'], c['y1']) for c in kids[g['id']]], (g['cx0'], g['cy0'], g['cx1'], g['cy1'])) for g in groups))
ok('nested: at every level child area is proportional to child value within the parent content box', all(abs((c['x1'] - c['x0']) * (c['y1'] - c['y0']) - (g['cx1'] - g['cx0']) * (g['cy1'] - g['cy0']) * c['value'] / g['value']) < 1e-6 for g in groups for c in kids[g['id']]))
ok('nested: group value is the sum of its children', all(abs(g['value'] - sum(c['value'] for c in kids[g['id']])) < 1e-9 for g in groups))
ok('nested: depth reaches 3 group levels plus the leaves (4 tiers)', NN['depth'] == 4 and max(r['depth'] for r in nodes if r['group']) == 2)
lv = [(r['x0'], r['y0'], r['x1'], r['y1']) for r in nodes if not r['group']]; ok('nested: leaf rectangles are pairwise disjoint and all inside the box', all(not (min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6) for i, a in enumerate(lv) for b in lv[i + 1:]) and all(a[0] >= BOX[0] - 1e-6 and a[3] <= BOX[3] + 1e-6 for a in lv))
ok('nested: group header strip is excluded from the children area', all(abs(g['cy0'] - g['y0'] - g['hdr']) < 1e-9 and g['hdr'] in (0.0, tm.__globals__['HDR']) for g in groups) and any(g['hdr'] > 0 for g in groups))
ok('nested: mixed levels - leaf and group siblings share a parent', {r['name'] for r in nodes if r['depth'] == 1 and r['path'] == ['Eng']} == {'Web', 'Data', 'misc'})
ok('nested: category ignored when a path is given; no path -> category group or Other', {r['name'] for r in rootkids} == {'Eng', 'Ops', 'Legal', 'Other'})
ok('nested: more than four top-level groups are all drawn (no category cap)', len(tm([{'path': [c], 'name': 'n' + c, 'value': 1} for c in 'ABCDEF'])['squarified']['nodes']) == 12)
sv7 = tm([{'path': [c], 'name': 'n' + c, 'value': 5 + i} for i, c in enumerate('ABCDEFG')])['squarified']['svg']; gf = {c: re.search(r'fill="(#[0-9a-f]{6})" stroke="#ffffff" stroke-width="2"><title>' + c + ':', sv7).group(1) for c in 'ABCDE'}
ok('nested: group colours repeat after four top-level groups', gf['A'] == gf['E'] and len({gf[c] for c in 'ABCD'}) == 4)
bad_paths = tm([{'path': ['A', 'B', 'C', 'D'], 'name': 'deep', 'value': 5}, {'path': ['A', ''], 'name': 'blank', 'value': 4, 'category': 'K'}, {'path': [], 'name': 'empty', 'value': 3}, {'path': 'A/B', 'name': 'str', 'value': 2}, {'path': ['G', 'H'], 'name': 'good', 'value': 9}])['squarified']
ok('nested: a 4-level path, blank segment, empty or non-list path is unusable and falls back to category/Other', {r['name'] for r in bad_paths['nodes'] if r['depth'] == 0} == {'Other', 'K', 'G'} and bad_paths['depth'] == 3)
ok('nested: no usable path anywhere keeps the flat mode', 'cats' in tm([{'path': [], 'category': 'A', 'name': 'a', 'value': 1}, {'path': ['', 'x'], 'category': 'B', 'name': 'b', 'value': 2}])['squarified'])
ok('nested: path segment numbers become text and long names truncated to 20', 'x' * 20 + '/' in tm([{'path': ['x' * 30, 5], 'name': 'n', 'value': 1}, {'path': ['y'], 'name': 'm', 'value': 2}])['squarified']['table'] and '/5/n' in tm([{'path': ['x', 5], 'name': 'n', 'value': 1}, {'path': ['y'], 'name': 'm', 'value': 2}])['squarified']['table'])
ok('nested: table lists path, name, value and share for every item', all(('/'.join(i['path']) if i.get('path') else i.get('category', 'Other')) + f"/{i['name']} {i['value']}" in NN['table'] for i in NI) and '%)' in NN['table'])
ok('nested: alt text from the same numbers (total, largest group)', f'Total {NT}' in NN['alt'] and 'Eng (' in NN['alt'] and f"{100 * 88 / NT:.0f}%" in NN['alt'])
ok('nested: well-formed, deterministic, under 60 KB, text >= 14 px', wf(NN) and tm(NI)['squarified']['svg'] == NN['svg'] and len(NN['svg']) < 60_000 and min(int(x) for x in re.findall(r'font-size="(\d+)"', NN['svg'])) >= 14)
ok('nested: group header labels carry name and total', f'>Eng {88}' in NN['svg'] or 'Eng 88' in NN['svg'])
ok('nested: markup in group names escaped', wf(tm([{'path': ['<g>&"'], 'name': 'a', 'value': 1}, {'path': ['q'], 'name': 'b', 'value': 3}])['squarified']))
many = [{'path': ['G' + str(i % 5)], 'name': f'n{i}', 'value': 1 + i % 4} for i in range(50)]
ok('max_items 50 lifts the cap (50 leaves drawn)', len([r for r in tm(many, max_items=50)['squarified']['nodes'] if not r['group']]) == 50)
ok('default cap stays 12 with a note', len([r for r in tm(many)['squarified']['nodes'] if not r['group']]) == 12 and any('38 items beyond the 12th' in x for x in tm(many)['squarified']['notes']))
ok('max_items 30 cuts at 30 and says how many', any('20 items beyond the 30th' in x for x in tm(many, max_items=30)['squarified']['notes']))
ok('max_items outside 12..60 or wrong type keeps 12', all(len([r for r in tm(many, max_items=v)['squarified']['nodes'] if not r['group']]) == 12 for v in (11, 61, 0, -5, '40', 40.0, True, None)))
ok('max_items 60 with 70 items cuts at 60', any('10 items beyond the 60th' in x for x in tm(many + many[:20], max_items=60)['squarified']['notes']))
ok('nested: all-leaf rects in Result have the path as category', all(r['category'] for r in NN['rects'] if r['name'] != 'orphan') and len(NN['rects']) == len(NI))
rnd = random.Random(11); good = True
for _ in range(30):
    its = [{'path': [rnd.choice('ABC'), rnd.choice('xyz'), rnd.choice('pq')][:rnd.randint(1, 3)], 'name': f'i{k}', 'value': rnd.choice([1, 2, 5, 9, 40])} for k in range(rnd.randint(4, 40))]
    rr = tm(its, max_items=60)['squarified']; nd = rr['nodes']; kk = {}
    for r in nd: kk.setdefault(r['parent'], []).append(r)
    good = good and all(tile_ok([(c['x0'], c['y0'], c['x1'], c['y1']) for c in kk[g['id']]], (g['cx0'], g['cy0'], g['cx1'], g['cy1'])) for g in nd if g['group'])
ok('nested: 30 random trees - every group tiled exactly by its children', good)
# ---------- round 2: inverse-read oracle (parse the drawing back), boundary inputs, degradation, pill
import time
SVGNS = '{http://www.w3.org/2000/svg}'
def cells(svgtxt):
    """Drawn cell rectangles (those with a stroke and no corner radius), in drawing order: (x, y, w, h)."""
    return [(float(e.get('x')), float(e.get('y')), float(e.get('width')), float(e.get('height'))) for e in ET.fromstring(svgtxt).iter(SVGNS + 'rect') if e.get('stroke') and e.get('rx') is None]
def texts(svgtxt): return [(float(e.get('x')), float(e.get('y')), int(e.get('font-size')), e.text) for e in ET.fromstring(svgtxt).iter(SVGNS + 'text')]
fmt_ = D.common.fmt; BA = (BOX[2] - BOX[0]) * (BOX[3] - BOX[1])
for lay in ('squarified', 'columns'):
    sv = R[lay]['svg']; cl = cells(sv); rc = R[lay]['rects']; tx = texts(sv)
    ok(f'treemap oracle {lay}: one drawn cell per item', len(cl) == len(rc) == len(IT))
    ok(f'treemap oracle {lay}: DRAWN cell area / box area equals value / total for every item', all(abs(w * h / BA - r['value'] / TOT) < 1e-4 for (x, y, w, h), r in zip(cl, rc)))
    ok(f'treemap oracle {lay}: drawn cells tile the box (areas add up, none overlaps)', tile_ok([(x, y, x + w, y + h) for x, y, w, h in cl], BOX, 1e-3, 0.03))
    ok(f'treemap oracle {lay}: printed cell value is the item value (read from the text nodes, per cell)', all(any(abs(t[0] - (x + 8)) < .01 and x <= t[0] <= x + w and y <= t[1] <= y + h and t[3] == fmt_(r['value']) for t in tx) for (x, y, w, h), r in zip(cl, rc) if w >= 84 and h >= 44 + (26 if r['first'] else 0)) and any(t[3] == '40' for t in tx))
    ok(f'treemap oracle {lay}: category pill shows the category name and total', all(any(t[3].startswith(c + ' ' + fmt_(sum(i['value'] for i in IT if i['category'] == c))) for t in tx) for c in ('Compute', 'Storage', 'Data')))
ok('treemap: pill is text, so colour is not the only carrier; fonts all >= 14', min(t[2] for t in texts(R['squarified']['svg'])) >= 14)
sv = NN['svg']; cl = cells(sv)
ok('treemap oracle nested: drawn rectangles equal the computed ones (x, y, w, h)', len(cl) == len(nodes) and all(abs(x - r['x0']) < .01 and abs(y - r['y0']) < .01 and abs(w - (r['x1'] - r['x0'])) < .01 and abs(h - (r['y1'] - r['y0'])) < .01 for (x, y, w, h), r in zip(cl, nodes)))
ok('treemap oracle nested: drawn leaf area / its parent content area equals value / group value', all(abs(w * h / ((g['cx1'] - g['cx0']) * (g['cy1'] - g['cy0'])) - r['value'] / g['value']) < 1e-3 for (x, y, w, h), r in zip(cl, nodes) if r['depth'] > 0 for g in [next(q for q in nodes if q['id'] == r['parent'])]))
ok('treemap oracle nested: printed leaf values equal the data', all(any(t[3] == fmt_(i['value']) for t in texts(sv)) for i in NI if i['name'] in ('vms', 'ui')))
# boundary inputs
hv = tm([{'category': 'a', 'name': 'x', 'value': 5e-324}, {'category': 'a', 'name': 'y', 'value': 5e-324}])
ok('treemap boundary: two subnormal values draw (no ZeroDivisionError), equal halves', wf(hv['squarified']) and abs((lambda a, b: a / b)(*[(q['x1'] - q['x0']) * (q['y1'] - q['y0']) for q in hv['squarified']['rects']]) - 1) < 1e-9)
hm = tm([{'category': 'a', 'name': 'big', 'value': 1e12}, {'category': 'a', 'name': 'tiny', 'value': 5e-324}, {'category': 'b', 'name': 'sub', 'value': 1e-310}])
ok('treemap boundary: 1e12 next to subnormals tiles the box', wf(hm['squarified']) and tile_ok([(r['x0'], r['y0'], r['x1'], r['y1']) for r in hm['squarified']['rects']], BOX, 1e-6))
hh = tm([{'category': 'a', 'name': 'x', 'value': 1e308}, {'category': 'b', 'name': 'y', 'value': 10 ** 400}, {'category': 'c', 'name': 'z', 'value': 1}])['squarified']
ok('treemap boundary: 1e308 and 10**400 clamped to 1e12 with one note, no nan/inf', any('2 values were above' in x for x in hh['notes']) and not re.search(r'nan|inf', hh['svg'] + hh['alt'] + hh['table'], re.I) and 'Total 2,000,000,000,001' in hh['summary'])
ok('treemap boundary: nan, inf, -inf, bool, text and None values are dropped and counted', len(tm([{'name': 'a', 'value': 1}, {'name': 'n', 'value': float('nan')}, {'name': 'i', 'value': float('inf')}, {'name': 'j', 'value': float('-inf')}, {'name': 'b', 'value': True}, {'name': 't', 'value': '5'}, {'name': 'u', 'value': None}])['squarified']['rects']) == 1)
ok('treemap boundary: dict, list, 10**400 as name, category, path, title, unit, version, max_items do not crash', wf(tm([{'category': {'a': 1}, 'name': ['n'], 'value': 1, 'path': [['x']]}, {'category': 10 ** 400, 'name': 10 ** 400, 'value': 2, 'path': [{'k': 1}, 'y']}, {'category': [1], 'name': {}, 'value': 3}], unit=10 ** 400, title={'t': 1}, version=10 ** 400, max_items=10 ** 400)['squarified']))
ok('treemap boundary: huge string fields are cut cheaply and well-formed', (lambda t0, q: time.time() - t0 < 2 and wf(q))(time.time(), tm([{'category': 'c' * 10 ** 6, 'name': 'n' * 10 ** 6, 'value': 1, 'path': ['p' * 10 ** 6]}, {'name': 'q', 'value': 2}], title='t' * 10 ** 6, unit='u' * 10 ** 6)['squarified']))
ok('treemap boundary: squarify of equal subnormal and a zero-width box does not raise', len(TM.squarify([5e-324, 5e-324, 5e-324], 0, 0, 0, 100)) == 3 and len(TM.squarify([1, 2], 0, 0, 100, 0)) == 2)
ok('treemap boundary: 60 nested items (max_items 60) stay small and valid', (lambda q: wf(q) and len(q['svg']) < 60_000)(tm([{'path': ['G' + str(i % 6), 'S' + str(i % 4)], 'name': f'item {i}', 'value': 1 + i % 7} for i in range(60)], max_items=60)['squarified']))
# degradation: titles go first, refuse only if still too big
def drawer(n, tl, pad):
    return lambda titles: ''.join(f'<rect x="{i % 40}" y="{i // 40}" width="1" height="1" fill="#4b4acf">' + (TM.tip(True, 'x' * tl) if titles else '') + '</rect>' for i in range(n)) + pad
dr = TM.render('treemap', 't', 'Treemap', drawer(700, 190, ''), 's', 'tab', [], '')
ok('degrade: over-budget drawing loses its hover titles first and says so', '<title>' not in dr['svg'] and any('Hover titles were left out' in x for x in dr['notes']) and len(dr['svg']) < 76_000)
dr2 = TM.render('treemap', 't', 'Treemap', drawer(700, 20, ''), 's', 'tab', [], '')
ok('degrade: a drawing within budget keeps its titles and adds no note', '<title>' in dr2['svg'] and not dr2['notes'])
try: TM.render('treemap', 't', 'Treemap', drawer(3900, 20, ''), 's', 'tab', [], ''); refused = False
except D.common.SvgPolicyError: refused = True
ok('degrade: still too big without titles -> refused by the output policy (fail closed)', refused)
# ---------- A2UI messages
res = tm(**DEMOS['treemap']); default = res.pop('_default'); create, updates = D.atom_card('T', res, default)
name = 'treemap'
ok(f'{name}: createSurface validates', not list(A2R.iter_errors(create))); ok(f'{name}: every update validates', all(not list(A2R.iter_errors(u)) for u in updates.values()))
ok(f'{name}: only Basic components', {c['component'] for c in create['createSurface']['components']} <= {'Card', 'Column', 'Row', 'Text', 'Image', 'Button'})
ids = {c['id'] for c in create['createSurface']['components']}; refs = set()
for c in create['createSurface']['components']: refs |= set(c.get('children', [])) | ({c['child']} if 'child' in c else set())
ok(f'{name}: child references resolve', refs <= ids); ok(f'{name}: image description bound', all('description' in c for c in create['createSurface']['components'] if c['component'] == 'Image'))
ok(f'{name}: payload under 200 KB', len(json.dumps(create)) < 200_000)
b1 = copy.deepcopy(create); b1['version'] = 'v1.0'; ok(f'{name}: negative: bad version rejected', bool(list(A2R.iter_errors(b1))))
b2 = copy.deepcopy(create); b2['createSurface']['components'][2]['component'] = 'Chart'; ok(f'{name}: negative: unknown component rejected', bool(list(A2R.iter_errors(b2))))
b3 = copy.deepcopy(updates['columns']); del b3['updateDataModel']['surfaceId']; ok(f'{name}: negative: update without surfaceId rejected', bool(list(A2R.iter_errors(b3))))
ok('registry: PACK_HIERARCHY names the treemap only (dendrogram and radial_tree are org_chart layouts, not atoms)', set(PACK_HIERARCHY) == {'treemap'} and set(DEMOS) == {'treemap'})
print(f'hierarchy tests: {n} checks, {bad} failed'); sys.exit(1 if bad else 0)
