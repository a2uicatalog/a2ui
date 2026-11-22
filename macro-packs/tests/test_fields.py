"""Tests for the 'fields' group (contour_plot, venn): independent arithmetic (analytic fields, closed-form lens area, d3's level rule re-derived in exact fractions), INVERSE READS of the
drawn SVG (band polygons tested against the field, legend swatches against band classes, circle radii and labels against the sizes), the tolerant-reader rules, hostile inputs,
timing, determinism, and A2UI 1.0 validation with negative controls. No model, no browser, no network. Run: A2UI_UPSTREAM=<upstream checkout> python3 -B tests/test_fields.py"""
import copy, glob, json, math, random, re, sys, time
from fractions import Fraction
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
from d3pack import common as CM
from d3pack import contour as CT, venn as VN
from d3pack.contour import contour_plot, contour_rings, levels
from d3pack.venn import venn, lens_area, solve_distance
from d3pack.registry_fields import PACK_FIELDS
from d3pack.demos_fields import DEMOS
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
def wf(r): ET.fromstring(r['svg']); return True
PX, PY, PW, PH = CT.PX, CT.PY, CT.PW, CT.PH
ALLOWED = set(CM.PAL) | {CM.FACE, CM.INK, CM.MUTED} | {CM.blend(CM.PAL[0], i / 20000) for i in range(20001)}
def style_ok(svg):
    cols = set(re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{6})"', svg)); sizes = [float(s) for s in re.findall(r'font-size="([\d.]+)"', svg)]
    return cols <= ALLOWED and bool(sizes) and all(s >= 14 for s in sizes)
def C(**k): return contour_plot(**k)['contour']
def shoelace(r): return .5 * sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))
# ---------- an independent re-derivation of d3's level rule, in exact fractions (different code from contour.py: candidate-step search instead of the error-threshold ladder)
def o_step(a, b, count):
    raw = (b - a) / count; p = math.floor(math.log10(float(raw)))
    cands = [Fraction(m) * Fraction(10) ** e for e in (p - 1, p, p + 1) for m in (1, 2, 5)]
    return min(cands, key=lambda c: abs(math.log(float(raw / c))))   # nearest of 1, 2, 5 (x 10^k) by ratio: d3's cut-offs sqrt2, sqrt10, sqrt50 are the geometric midpoints between 1, 2, 5, 10
def o_nice(a, b, count):
    a, b = Fraction(a), Fraction(b); prev = None
    while True:
        s = o_step(a, b, count)
        if s == prev: return a, b
        a, b = math.floor(a / s) * s, math.ceil(b / s) * s; prev = s
def o_levels(lo, hi, count):
    lo_f, hi_f = Fraction(repr(float(lo))), Fraction(repr(float(hi)))
    a, b = o_nice(lo_f, hi_f, count); s = o_step(a, b, count); tz = [i * s for i in range(math.ceil(a / s), math.floor(b / s) + 1)]
    while tz and tz[-1] >= hi_f: tz.pop()
    while len(tz) > 1 and tz[1] < lo_f: tz.pop(0)
    return [float(t) for t in tz]
def near(a, b): return len(a) == len(b) and all(abs(x - y) <= 1e-9 * max(1, abs(y)) for x, y in zip(a, b))
# ---------- inverse read of a contour svg
def parse_contour(svg):
    root = ET.fromstring(svg); ns = '{http://www.w3.org/2000/svg}'; paths = []; swatches = []; texts = []; base = None
    for e in root.iter():
        t = e.tag.replace(ns, '')
        if t == 'path' and e.get('fill-rule') == 'evenodd': paths.append((e.get('fill'), [[tuple(float(v) for v in p.split(',')) for p in seg.split('L')] for seg in re.findall(r'M([^M]*?)Z', e.get('d'))]))
        elif t == 'rect' and e.get('width') == '14' and e.get('height') == '14': swatches.append((e.get('fill'), float(e.get('x')), float(e.get('y'))))
        elif t == 'rect' and e.get('width') == str(PW) and e.get('height') == str(PH) and e.get('fill') != 'none' and base is None: base = e.get('fill')
        elif t == 'text': texts.append((float(e.get('x')), float(e.get('y')), e.text or ''))
    legend_text = [next(tx for xx, yy, tx in texts if abs(xx - (x + 20)) < .01 and abs(yy - (y + 12)) < .01) for _, x, y in swatches]   # a swatch's label: the text 20 px to its right on its row
    return base, paths, swatches, legend_text, texts
def inside_evenodd(px, py, rings):
    c = False
    for ring in rings:
        for i in range(len(ring)):
            (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
            if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1: c = not c
    return c
def painted(px, py, base, paths):
    colour = base
    for fill, rings in paths:
        if inside_evenodd(px, py, rings): colour = fill
    return colour
def cls(v, ths): return sum(1 for t in ths if v >= t)   # independent class rule
# ======================= contour_plot: the level rule (d3.contours thresholds)
rg = random.Random(11); agree = True
for _ in range(60):
    lo = rg.choice([0, -3.7, 0.001, 12.5, -1e4, 7e-7]) + rg.random(); hi = lo + rg.choice([.0004, .9, 3.3, 10, 87, 5000]) * (1 + rg.random()); cnt = rg.randint(3, 20)
    agree &= near(levels(lo, hi, cnt), o_levels(lo, hi, cnt))
ok('levels() equals the independent exact-fraction d3 rule on 60 random ranges and counts', agree)
ok('levels: 0..10 aiming for 5 is 0,2,4,6,8 (tick at 10 dropped, first level at the minimum is kept)', levels(0, 10, 5) == [0, 2, 4, 6, 8])
ok('levels: the first level can sit AT OR BELOW the minimum, as in d3 (0.5..9.5 gives 0 first)', levels(.5, 9.5, 5) == [0, 2, 4, 6, 8] and o_levels(.5, 9.5, 5) == [0, 2, 4, 6, 8])
ok('levels: a level equal to the maximum is dropped; a flat field has none', levels(0, 8, 4)[-1] < 8 and levels(3, 3, 5) == [])
ok('levels: steps are 1, 2 or 5 times a power of ten', all((lambda s: any(abs(s / 10 ** math.floor(math.log10(s)) - q) < 1e-6 for q in (1, 2, 5)))(l[2] - l[1]) for l in (levels(0, 7.3, 6), levels(3, 940, 9), levels(-1, 1, 12), levels(0.002, 0.0031, 4)) if len(l) > 2))
# ---------- linear ramp: vertical iso-lines at the exact x (nodes at cell centres; a cell i spans i to i+1)
w, h = 11, 5; ramp = [c + .3 for r in range(h) for c in range(w)]; R = C(grid=dict(width=w, height=h, values=ramp), thresholds=10)
ths = R['thresholds']; ok('ramp: levels are those of the independent rule (0..10)', near(ths, o_levels(.3, 10.3, 10)) and ths == [float(i) for i in range(11)])
good = True
for t, rgs in zip(ths, R['rings']):
    if t < 1: continue
    xt = PX + (t - .3 + .5) * PW / 11; ring = rgs[0]
    good &= len(rgs) == 1 and abs(min(p[0] for p in ring) - xt) < 1e-6 and sorted(round(p[1], 3) for p in ring if abs(p[0] - xt) < 1e-6) == [round(PY + .5 * PH / 5, 3), round(PY + 4.5 * PH / 5, 3)]   # collinear row crossings are merged: the line is its two end points, first and last row
ok('ramp: every iso-line is straight and vertical at exactly x = PX + (t - 0.3 + 0.5) / 11 * PW (its crossings in all 5 rows are collinear and merged into the two end points), nothing to its left', good)
ok('ramp: the first level (0) is at or below every value, so band 0 is empty and the note says so', R['counts'][0] == 0 and any('band 0 is empty' in x for x in R['notes']))
ok('ramp: counts independent check (v >= t classes)', R['counts'] == [sum(1 for v in ramp if cls(v, ths) == k) for k in range(len(ths) + 1)] and sum(R['counts']) == 55)
# ---------- radial cone
cw = ch = 41; cone = [20 - math.hypot(c - 20, r - 20) for r in range(ch) for c in range(cw)]; RC = C(grid=dict(width=cw, height=ch, values=cone), thresholds=8)
good = True; areas = True; checked = 0
for t, rgs in zip(RC['thresholds'], RC['rings']):
    if not 3 <= t <= 17: continue   # rings with a radius over 17 cells leave the box and are clipped
    rad = 20 - t; ring = rgs[0]; checked += 1
    cell_pts = [((x - PX) / (PW / 41) - .5, (y - PY) / (PH / 41) - .5) for x, y in ring]
    good &= len(rgs) == 1 and all(abs(math.hypot(a - 20, b - 20) - rad) <= 1.0 for a, b in cell_pts) and len(ring) >= 8
    areas &= abs(abs(shoelace(cell_pts)) - math.pi * rad * rad) < .06 * math.pi * rad * rad
ok('cone: every iso-line lies within one cell of the circle of radius 20 - t', good and checked >= 3); ok('cone: the ring encloses ~ pi r^2 (shoelace within 6%)', areas)
ok('cone: levels match the independent rule', near(RC['thresholds'], o_levels(min(cone), 20, 8)))
# ---------- band classes and tables
ok('bands: band count = levels + 1, one evenodd path per level', len(RC['counts']) == len(RC['thresholds']) + 1 and RC['svg'].count('fill-rule="evenodd"') == len(RC['thresholds']))
ok('bands: the cell counts sum to the grid size', sum(RC['counts']) == cw * ch == RC['cells'])
ok('bands: counts match an independent classification', RC['counts'] == [sum(1 for v in cone if cls(v, RC['thresholds']) == k) for k in range(len(RC['thresholds']) + 1)])
g22 = C(grid=dict(width=2, height=2, values=[0, 5, 5, 10]), thresholds=3)
ok('bands: a value equal to a level falls in the upper band (levels 0 and 5: counts 0, 1, 3)', g22['thresholds'] == [0.0, 5.0] and g22['counts'] == [0, 1, 3])
ok('table: every level with its cell count and the share at or above it (100, 100 and 75 percent)', 'Band 0: below 0: 0 cells; 100% of cells' in g22['table'] and 'Band 1: 0 to 5: 1 cells; 100% of cells' in g22['table'] and 'Band 2: 5 and above: 3 cells; 75% of cells' in g22['table'])
ok('table: dimensions, value range and the column/row numbering are stated', all(s in RC['table'] for s in ['41 by 41 = 1681 cells', 'range -8.28 to 20', 'Columns are numbered 0 to 41 and rows 0 to 41']))
ok('alt: carries the levels, dimensions and band count', all(CM.fmt(t) in RC['alt'] for t in RC['thresholds']) and '41 by 41' in RC['alt'] and f'{len(RC["counts"])} bands' in RC['alt'])
# ---------- INVERSE READ of the drawing: painted colour at every cell centre = legend swatch of that cell's class; legend names every band
base, paths, swatches, legend_text, texts = parse_contour(RC['svg']); ths_c = RC['thresholds']; nb = len(ths_c) + 1
ok('legend: one swatch per band, every band named by a range of numbers', len(swatches) == nb and len(legend_text) == nb and legend_text[0] == f'below {CM.fmt(ths_c[0])}' and legend_text[-1] == f'{CM.fmt(ths_c[-1])} and above' and all(legend_text[k] == f'{CM.fmt(ths_c[k - 1])} to {CM.fmt(ths_c[k])}' for k in range(1, nb - 1)))
order = sorted(range(len(swatches)), key=lambda i: (swatches[i][1], swatches[i][2])); sw_col = [swatches[i][0] for i in order]   # reading order: columns left to right, rows top to bottom (lowest band first)
ok('legend: the label order is the band order (each swatch sits next to its own range text)', [legend_text[i] for i in order] == [f'below {CM.fmt(ths_c[0])}'] + [f'{CM.fmt(ths_c[k - 1])} to {CM.fmt(ths_c[k])}' for k in range(1, nb - 1)] + [f'{CM.fmt(ths_c[-1])} and above'])
ok('legend: swatch colours get strictly darker from the lowest band to the highest (the key is not reversed)', all(CM.lum(a) > CM.lum(b) for a, b in zip(sw_col, sw_col[1:])))
ok('legend: swatch 0 is the background colour and swatch k is the fill of the level-k path', sw_col[0] == base and [p[0] for p in paths] == sw_col[1:])
mism = 0; probes = 0
for r in range(ch):
    for c in range(cw):
        v = cone[r * cw + c]
        if any(abs(v - t) < 1e-6 for t in ths_c): continue
        probes += 1; mism += painted(PX + (c + .5) * PW / 41, PY + (r + .5) * PH / 41, base, paths) != sw_col[cls(v, ths_c)]
ok(f'inverse read: the painted colour at all {probes} cell centres equals the legend swatch of the cell class ({mism} mismatches)', probes > 1500 and mism == 0)
mism = 0; probes = 0; b2, p2, s2, lt2, tx2 = parse_contour(R['svg']); sc2 = [s[0] for s in sorted(s2, key=lambda s: (s[1], s[2]))]
for r in range(h):
    for c in range(w):
        v = ramp[r * w + c]; probes += 1; mism += painted(PX + (c + .5) * PW / w, PY + (r + .5) * PH / h, b2, p2) != sc2[cls(v, R['thresholds'])]
ok(f'inverse read (ramp): all {probes} cell centres are painted with their class colour', mism == 0)
cm = 0
for (qx, qy, rr_, cc_) in ((PX + 1, PY + 1, 0, 0), (PX + PW - 1, PY + 1, 0, w - 1), (PX + 1, PY + PH - 1, h - 1, 0), (PX + PW - 1, PY + PH - 1, h - 1, w - 1)): cm += painted(qx, qy, b2, p2) != sc2[cls(ramp[rr_ * w + cc_], R['thresholds'])]
ok('inverse read: the bands reach the four corners of the plot box (no half-cell chips)', cm == 0)
# ---------- saddles, holes, closure
sad = [[1.0, 0.0], [0.0, 1.0]]; xyf = lambda r, c: (c * 10.0, r * 10.0)
ok('marching squares: a saddle with cell mean >= level joins the inside corners (1 ring)', len(contour_rings(sad, 2, 2, .5, xyf)) == 1)
ok('marching squares: a saddle with cell mean < level keeps them apart (2 rings)', len(contour_rings(sad, 2, 2, .6, xyf)) == 2)
dough = [[0, 0, 0, 0, 0], [0, 2, 2, 2, 0], [0, 2, 0, 2, 0], [0, 2, 2, 2, 0], [0, 0, 0, 0, 0]]; dr = contour_rings(dough, 5, 5, 1, xyf); ar = sorted(abs(shoelace(r_)) for r_ in dr)
ok('marching squares: a doughnut gives an outer and a smaller inner ring with no repeated point', len(dr) == 2 and all(len(set(r_)) == len(r_) for r_ in dr) and ar[0] < ar[1])
one = contour_rings([[1.0, None], [1.0, 1.0]], 2, 2, .5, xyf)
ok('marching squares: an empty (None) cell is below every level (one ring: the real nodes are inside it, the empty node is outside)', len(one) == 1 and inside_evenodd(0, 0, one) and inside_evenodd(10, 10, one) and inside_evenodd(0, 10, one) and not inside_evenodd(10, 0, one))
# ---------- tolerant reader
nine = dict(width=4, height=4, values=list(range(16)))
ok('thresholds: below 3 clamped with a note', any('clamped to 3' in x for x in C(grid=nine, thresholds=1)['notes'])); ok('thresholds: above 20 clamped with a note', any('clamped to 20' in x for x in C(grid=nine, thresholds=99)['notes']))
rf = C(grid=nine, thresholds=7.9); ok('thresholds: a fraction is rounded down with a note and gives the independent 7-level set', any('rounded down to 7' in x for x in rf['notes']) and near(rf['thresholds'], o_levels(0, 15, 7)))
ok('thresholds: default for a grid is Sturges (ceil(log2 64) + 1 = 7 levels aimed for)', near(C(grid=dict(width=8, height=8, values=list(range(64))))['thresholds'], o_levels(0, 63, 7)))
bg = [1.0, 2.0, float('nan'), 'x', None, True, 1e13, float('inf'), 4.0, {'a': 1}, [1]] + [3.0] * 5; Rb = C(grid=dict(width=4, height=4, values=bg), thresholds=3)
ok('grid: unusable values (nan, text, None, bool, 1e13, inf, dict, list) counted in a note and left in band 0', any('8 grid values' in x for x in Rb['notes']) and sum(Rb['counts']) == 16 and Rb['counts'][0] >= 8 and Rb['vmax'] == 4.0)
ok('grid: wrong value count refused', raises(lambda: C(grid=dict(width=3, height=3, values=[1] * 8)))); ok('grid: width 1 refused (the contract needs 2 to 100)', raises(lambda: C(grid=dict(width=1, height=3, values=[1] * 3)))); ok('grid: a 1 by N grid (height 1) refused', raises(lambda: C(grid=dict(width=5, height=1, values=[1] * 5))))
ok('grid: width 101 refused', raises(lambda: C(grid=dict(width=101, height=2, values=[1] * 202)))); ok('grid: fractional size refused', raises(lambda: C(grid=dict(width=2.5, height=2, values=[1] * 5)))); ok('grid: no usable value refused', raises(lambda: C(grid=dict(width=2, height=2, values=['a'] * 4))))
ok('neither grid nor points refused', raises(lambda: contour_plot())); ok('grid given as a list (not an object) is refused, not a crash', raises(lambda: contour_plot(grid=[1, 2, 3])))
Rk = C(grid=dict(width=3, height=3, values=[2.0] * 9)); ok('grid: a constant field is one flat band with a note and a one-entry legend', Rk['thresholds'] == [] and Rk['counts'] == [9] and any('flat band' in x for x in Rk['notes']) and len(parse_contour(Rk['svg'])[2]) == 1)
ok('grid: a 2 by 50 grid (the narrowest allowed) draws', sum(C(grid=dict(width=2, height=50, values=list(range(100))))['counts']) == 100)
ok('version 2 is drawn as version 1 with a note', any('version 1' in x for x in C(grid=dict(width=3, height=3, values=list(range(9))), version=2)['notes']))
ok('both grid and points: grid wins with a note', any('points are ignored' in x for x in C(grid=dict(width=3, height=3, values=list(range(9))), points=[{'x': 1, 'y': 2}] * 3)['notes']))
# ---------- hostile numbers: nothing but ValueError may escape, and what is drawn is a valid drawing
BIGINT = 10 ** 400; HOST = [BIGINT, -BIGINT, float('nan'), float('inf'), 1e308, 5e-324, True, 'x', None, {'a': 1}, [1], 10 ** 3999]
def only_valueerror(fn):
    try: r = fn(); CM.verify_svg(r[r['_default']]['svg']); return True
    except ValueError: return True
    except Exception as e: print('   crash:', type(e).__name__, str(e)[:60]); return False
fz = True
for hv in HOST:
    for kw in ('thresholds', 'bandwidth', 'version', 'title', 'unit', 'x_label'):
        fz &= only_valueerror(lambda: contour_plot(grid=dict(width=3, height=3, values=list(range(9))), **{kw: hv}))
        fz &= only_valueerror(lambda: contour_plot(points=[{'x': i, 'y': i * i} for i in range(6)], **{kw: hv}))
    fz &= only_valueerror(lambda: contour_plot(grid=dict(width=hv, height=3, values=list(range(9))))); fz &= only_valueerror(lambda: contour_plot(grid=dict(width=3, height=3, values=[hv] + list(range(8)))))
    fz &= only_valueerror(lambda: contour_plot(points=[{'x': hv, 'y': 1}, {'x': 1, 'y': 2}, {'x': 2, 'y': 3}, {'x': 3, 'y': hv}])); fz &= only_valueerror(lambda: contour_plot(points=[hv, {'x': 1, 'y': 2}, {'x': 2, 'y': 3}, {'x': 3, 'y': 1}]))
ok('hostile values (10**400, nan, inf, 1e308, subnormal, bool, text, None, dict, list) in every parameter: only ValueError, valid SVG', fz)
Rs = C(grid=dict(width=3, height=3, values=[5e-324, 0, 1e-300, 1, 2, 3, 4, 5, 6])); ok('subnormal and tiny values do not crash the level rule', sum(Rs['counts']) == 9)
ok('values of 10**400 are left empty and counted, not an OverflowError', any('1 grid values' in x for x in C(grid=dict(width=3, height=3, values=[BIGINT] + list(range(8))))['notes']))
# ---------- points / kernel density
rg = random.Random(3); P = [{'x': rg.gauss(0, 1), 'y': rg.gauss(0, 1)} for _ in range(300)]
RP = C(points=P, bandwidth=8); mass = sum(sum(r) for r in RP['values']) * RP['cell'] ** 2 / 1e4
ok(f'points: density integrates to ~1 over the plot box ({mass:.4f})', .93 < mass < 1.0001)
xs = [p['x'] for p in P]; ys = [p['y'] for p in P]; xa, xb = o_nice(min(xs), max(xs), 10); ya, yb = o_nice(min(ys), max(ys), 10); xa, xb, ya, yb = map(float, (xa, xb, ya, yb))
ppx = [(PX + (p['x'] - xa) / (xb - xa) * PW, PY + PH - (p['y'] - ya) / (yb - ya) * PH) for p in P]
def direct(px, py, pts, s): return sum(math.exp(-((px - x) ** 2 + (py - y) ** 2) / (2 * s * s)) for x, y in pts) / (2 * math.pi * s * s * len(pts))
RP12 = C(points=P, bandwidth=12); g = RP12['values']; worst = 0; cl = RP12['cell']
for (i, j) in ((75, 50), (60, 40), (90, 60), (40, 30), (100, 70)):
    exact = direct(PX + i * cl, PY + j * cl, ppx, 12) * 1e4; worst = max(worst, abs(g[j][i] - exact) / exact if exact > .02 else 0)
ok(f'points: grid density equals a direct Gaussian sum at sample nodes (worst rel err {worst:.3f}, cell {cl} px)', cl == 4 and worst < .06)
RP20 = C(points=P, bandwidth=20); ok('points: a larger bandwidth lowers the peak; 16 px and over uses the coarser 8 px grid', C(points=P, bandwidth=50)['vmax'] < RP20['vmax'] < RP['vmax'] and RP20['cell'] == 8 and RP['cell'] == 4)
ok('points: the 8 px grid still integrates to ~1 and agrees with the direct sum', .93 < sum(sum(r) for r in RP20['values']) * 64 / 1e4 < 1.0001 and abs(RP20['values'][25][37] - direct(PX + 37 * 8, PY + 25 * 8, ppx, 20) * 1e4) < .04 * RP20['vmax'])
ok('points: bandwidth outside 5..60 is clamped with a note', any('clamped to 60' in x for x in C(points=P, bandwidth=200)['notes']) and any('clamped to 5' in x for x in C(points=P, bandwidth=1)['notes']))
ok('points: default is 20 levels aimed for, by the independent rule on the density range', near(RP20['thresholds'], o_levels(RP20['vmin'], RP20['vmax'], 20)))
ok('points: bad entries skipped and counted; fewer than 3 usable refused', any('2 entries were skipped' in x for x in C(points=P[:5] + [{'x': 1}, 'a'])['notes']) and raises(lambda: C(points=P[:2] + [{'x': 'a', 'y': 1}])))
ok('points: more than 2000 are cut with a note', any('beyond the 2000th' in x for x in C(points=[{'x': i % 7, 'y': i % 11} for i in range(2005)])['notes']))
ok('points: identical x values widen the axis with a note', any('x values are equal' in x for x in C(points=[{'x': 1, 'y': i} for i in range(5)])['notes']))
ok('points: table gives the point count, bandwidth, axes, band counts, shares and the first points', all(s in RP20['table'] for s in ['300 points', 'bandwidth 20 px', 'node grid', 'First points: (', '% of points at or above']) and sum(RP20['counts']) == RP20['cells'] == 76 * 51)
ok('points: share of points at or above band 0 is 100 percent and the shares fall with the band', RP20['shares'][0] == 100 and all(a >= b for a, b in zip(RP20['shares'], RP20['shares'][1:])))
bp, pp, sp, lp, tp = parse_contour(RP20['svg']); ticklab = [t[2] for t in tp if t[0] == PX - 8]; xlab = [t[2] for t in tp if abs(t[1] - (PY + PH + 21)) < .01]
yt = [(t[1] - 5, float(t[2])) for t in tp if t[0] == PX - 8]; xt_ = [(t[0], float(t[2])) for t in tp if abs(t[1] - (PY + PH + 21)) < .01]
ok('points: axis labels sit where the data says (inverse read: every y tick label at PY+PH-(v-ya)/(yb-ya)*PH, every x tick label at PX+(v-xa)/(xb-xa)*PW, niced range, y up)', len(yt) >= 3 and len(xt_) >= 3 and all(abs(py - (PY + PH - (v - ya) / (yb - ya) * PH)) < .6 for py, v in yt) and all(abs(px - (PX + (v - xa) / (xb - xa) * PW)) < .6 for px, v in xt_) and ya <= min(v for _, v in yt) and max(v for _, v in yt) <= yb and yt[0][1] < yt[-1][1] and yt[0][0] > yt[-1][0])
ok('grid: axes carry column and row numbers (0 and the width on x, 0 and the height on y)', {'0', '10'} <= {t[2] for t in tx2 if abs(t[1] - (PY + PH + 21)) < .01} and {'0', '5'} <= {t[2] for t in tx2 if t[0] == PX - 8})
# ---------- speed and size (the worst cases the reviewers found)
def timed(**k): t0 = time.time(); r = C(**k); return time.time() - t0, r
tm, Rc = timed(grid=dict(width=100, height=100, values=[(i % 100 + i // 100) % 2 * 10.0 for i in range(10000)]), thresholds=20)
ok(f'checkerboard 100x100 with 20 levels: under 3 s ({tm:.2f} s), under 80 KB, counts exact, the omitted rings are noted', tm < 3 and len(Rc['svg']) < 80000 and sum(Rc['counts']) == 10000 and any('small contour rings' in x for x in Rc['notes']))
tm, Rn = timed(grid=dict(width=100, height=100, values=[random.Random(2).random() * (i % 7) for i in range(10000)]), thresholds=20)
ok(f'noisy 100x100 grid: under 3 s ({tm:.2f} s), under 80 KB ({len(Rn["svg"])}), exact counts', tm < 3 and len(Rn['svg']) < 80000 and sum(Rn['counts']) == 10000)
big = [{'x': rg.gauss(0, 1), 'y': rg.gauss(0, 1)} for _ in range(2000)]
ok('2000 points at bandwidth 5 and at 60: each under 2 s', all(timed(points=big, bandwidth=b)[0] < 2 for b in (5, 60)))
# ---------- drawing guarantees
ok('svg is well-formed, colours only from PAL/blend, text >= 14 px, passes verify_svg', all(wf(x) and style_ok(x['svg']) and CM.verify_svg(x['svg']) for x in (R, RC, RP20, Rn, Rc)))
Rx = C(grid=dict(width=3, height=3, values=list(range(9))), x_label='<b>&"x', y_label="<i>'y", value_label='<v>', unit='<u>', title='<t>&'); ok('labels are XML-escaped (stays well-formed, no raw <b>)', wf(Rx) and '<b>' not in Rx['svg'] and '&lt;b&gt;' in Rx['svg'])
ok('deterministic', C(points=P)['svg'] == C(points=P)['svg'] and C(grid=dict(width=11, height=5, values=ramp))['svg'] == C(grid=dict(width=11, height=5, values=ramp))['svg'])
ok('the colour ramp is monotonic (darker with the class)', all(CM.lum(a) > CM.lum(b) for a, b in zip(RC['ramp'], RC['ramp'][1:])))
idr = lambda r_: re.search(r'<clipPath id="([^"]+)"', r_['svg']).group(1)
ok('clip id: derived from the content, matches [A-Za-z0-9_-]{1,16}, differs between three contours and is stable for the same one', all(re.fullmatch(r'[A-Za-z0-9_-]{1,16}', idr(x)) for x in (R, RC, RP20)) and len({idr(R), idr(RC), idr(RP20)}) == 3 and idr(R) == idr(C(grid=dict(width=w, height=h, values=ramp), thresholds=10)) and f'url(#{idr(R)})' in R['svg'])
ok('two contour svgs can sit in one page: their ids do not collide', not (set(re.findall(r'id="([^"]+)"', R['svg'])) & set(re.findall(r'id="([^"]+)"', RC['svg']))))
# ======================= venn
def disc_lens(r1, r2, d, N=40000):
    """numeric lens area: integrate the chord overlap over x (independent of the closed form)."""
    x0 = max(-r1, d - r2); x1 = min(r1, d + r2)
    if x1 <= x0: return 0.0
    s = 0.0; dx = (x1 - x0) / N
    for i in range(N):
        x = x0 + (i + .5) * dx; a = math.sqrt(max(0, r1 * r1 - x * x)); b = math.sqrt(max(0, r2 * r2 - (x - d) ** 2)); s += max(0, min(a, b) * 2) * dx
    return s
ok('lens: closed form vs numeric integration (3 cases)', all(abs(lens_area(r1, r2, d) - disc_lens(r1, r2, d)) < 1e-3 * math.pi * min(r1, r2) ** 2 + 1e-6 for r1, r2, d in ((1, 1, 1), (2, 1, 1.7), (3, 1.5, 3.2))))
ok('lens: equal circles at d = r give r^2 (2pi/3 - sqrt3/2)', abs(lens_area(2, 2, 2) - 4 * (2 * math.pi / 3 - math.sqrt(3) / 2)) < 1e-12)
ok('lens: no overlap beyond r1 + r2; full containment inside |r1 - r2|', lens_area(1, 2, 3) == 0 and lens_area(1, 2, 3.5) == 0 and abs(lens_area(1, 2, .5) - math.pi) < 1e-12 and abs(lens_area(1, 2, 0) - math.pi) < 1e-12)
ok('lens: area falls as the circles move apart', all(lens_area(1.5, 1, a) >= lens_area(1.5, 1, b) for a, b in zip([.5 + .1 * i for i in range(20)], [.6 + .1 * i for i in range(20)])))
good = True
for r1, r2 in ((1, 1), (2, .7), (5, 3)):
    for f in (.05, .3, .5, .9, .999):
        tgt = f * math.pi * min(r1, r2) ** 2; d = solve_distance(r1, r2, tgt); good &= abs(lens_area(r1, r2, d) - tgt) < 1e-9 * tgt and abs(r1 - r2) <= d <= r1 + r2
ok('bisection: the solved distance reproduces the requested lens area (15 cases, 1e-9 relative)', good)
ok('bisection: zero overlap = touching circles, overlap = smaller set = containment, and a zero-radius circle sits on the edge', abs(solve_distance(2, 1, 0) - 3) < 1e-12 and abs(solve_distance(2, 1, math.pi) - 1) < 1e-9 and abs(solve_distance(2, 0, 0) - 2) < 1e-12)
def circles(svg): return [tuple(float(v) for v in m) for m in re.findall(r'<circle cx="([\d.\-]+)" cy="([\d.\-]+)" r="([\d.]+)"', svg)]
def circle_titles(svg): return re.findall(r'<circle [^>]*><title>([^<]*)</title>', svg)
def sample_overlap(cs, idx, N=300):
    x0 = min(cs[i][0] - cs[i][2] for i in idx); x1 = max(cs[i][0] + cs[i][2] for i in idx); y0 = min(cs[i][1] - cs[i][2] for i in idx); y1 = max(cs[i][1] + cs[i][2] for i in idx); dx = (x1 - x0) / N; dy = (y1 - y0) / N; cnt = 0
    for a in range(N):
        x = x0 + (a + .5) * dx
        for b in range(N):
            y = y0 + (b + .5) * dy
            if all((x - cs[i][0]) ** 2 + (y - cs[i][1]) ** 2 <= cs[i][2] ** 2 for i in idx): cnt += 1
    return cnt * dx * dy
def read_labels(svg):
    """inverse read: every bold 16 px label 'Name (size unit)' with the circle whose edge is nearest to the label."""
    cs = circles(svg); out = []
    for m in re.finditer(r'<text x="([\d.\-]+)" y="([\d.\-]+)" font-size="16" font-weight="700"[^>]*>([^<]*)</text>', svg):
        x, y, tx = float(m.group(1)), float(m.group(2)), m.group(3); mm = re.fullmatch(r'(.*) \(([\d.,]+)(?: .*)?\)', tx)
        if not mm: continue
        near_i = min(range(len(cs)), key=lambda i: abs(math.hypot(x - cs[i][0], y - cs[i][1]) - cs[i][2])); out.append((near_i, mm.group(1), float(mm.group(2).replace(',', ''))))
    return out
V2 = venn(sets=[{'name': 'A', 'size': 120}, {'name': 'B', 'size': 45}], overlaps=[{'sets': ['A', 'B'], 'size': 30}], unit='u')['venn']; cs = circles(V2['svg'])
ok('venn2: two circles drawn', len(cs) == 2); ratio = [math.pi * c[2] ** 2 / s for c, s in zip(cs, (120, 45))]
ok('venn2: circle areas are proportional to the sizes (pixel area / size is constant)', abs(ratio[0] - ratio[1]) < 1e-3 * ratio[0])
k_ = ratio[0]; ov = sample_overlap(cs, (0, 1)); ok(f'venn2: the drawn overlap (sampled from the svg circles) is 30 within 1.5% ({ov / k_:.3f})', abs(ov / k_ - 30) < .45)
ok('venn2: the overlap label and table repeat the number', '>30<' in V2['svg'] and 'requested 30 u, drawn 30 u' in V2['table'])
V3 = venn(sets=[{'name': 'A', 'size': 40}, {'name': 'B', 'size': 60}, {'name': 'C', 'size': 30}], overlaps=[{'sets': ['A', 'B'], 'size': 15}, {'sets': ['B', 'C'], 'size': 12}, {'sets': ['C', 'A'], 'size': 6}], triple=4)['venn']; c3 = circles(V3['svg']); k3 = math.pi * c3[0][2] ** 2 / 40
# inverse read of the labels and titles: each circle's own title carries its name and size; each label must carry the same name and size as the circle it sits on
for tag, rr, want in (('venn2', V2, [('A', 120.0), ('B', 45.0)]), ('venn3', V3, [('A', 40.0), ('B', 60.0), ('C', 30.0)])):
    tl = circle_titles(rr['svg']); pt = [(m.group(1), float(m.group(2))) for t_ in tl for m in [re.fullmatch(r'(.*): ([\d.,]+)(?: .*)?', t_)]]
    ok(f'{tag}: circle titles carry the names and sizes', pt == want)
    lab = read_labels(rr['svg']); ok(f'{tag}: each set is labelled with ITS OWN name and size (label read back and matched to the circle it sits on)', len(lab) == len(want) and all(pt[i] == (nm, sz) for i, nm, sz in lab))
    cc = circles(rr['svg']); kk = [math.pi * c[2] ** 2 / sz for c, (_, sz) in zip(cc, pt)]
    ok(f'{tag}: radii read from the svg are proportional to the sizes in the titles', max(kk) - min(kk) < 1e-3 * kk[0])
ok('venn3: three circles with areas proportional to 40 : 60 : 30', len(c3) == 3 and all(abs(math.pi * c[2] ** 2 / s - k3) < 1e-3 * k3 for c, s in zip(c3, (40, 60, 30))))
for (i, j), want in (((0, 1), 15), ((1, 2), 12), ((0, 2), 6)): ok(f'venn3: pairwise overlap {i}-{j} drawn equals {want} within 2.5% (sampled from the svg)', abs(sample_overlap(c3, (i, j)) / k3 - want) < .025 * want)
t3 = sample_overlap(c3, (0, 1, 2)) / k3; ok(f'venn3: the reported triple estimate matches sampling the drawn circles ({V3["drawn_triple"]:.2f} vs {t3:.2f})', abs(V3['drawn_triple'] - t3) < .06 * max(t3, 1))
ok('venn3: the triple overlap is flagged approximate in the svg caption, table and alt, with the requested value', 'approximate' in V3['svg'] and 'approximate' in V3['table'] and 'approximate' in V3['alt'] and 'requested 4' in V3['table'])
ok('venn: everything fits the drawing', all(c[0] - c[2] >= 0 and c[0] + c[2] <= CM.W and c[1] - c[2] >= 0 and c[1] + c[2] <= CM.H for c in c3 + cs))
ok('venn2: containment when overlap = smaller set (d = r1 - r2) and a note when it exceeds it', (lambda r: abs(math.hypot(r['centres'][0][0] - r['centres'][1][0], r['centres'][0][1] - r['centres'][1][1]) - (r['radii_px'][0] - r['radii_px'][1])) < 1e-6 and any('clamped' in x for x in r['notes']))(venn(sets=[{'name': 'A', 'size': 50}, {'name': 'B', 'size': 20}], overlaps=[{'sets': ['A', 'B'], 'size': 99}])['venn']))
Vz = venn(sets=[{'name': 'A', 'size': 50}, {'name': 'B', 'size': 20}])['venn']; ok('venn2: no overlap given = circles just touch', abs(math.hypot(Vz['centres'][0][0] - Vz['centres'][1][0], Vz['centres'][0][1] - Vz['centres'][1][1]) - sum(Vz['radii_px'])) < 1e-6)
ok('venn3: triple clamped to the smallest pair with a note; ignored for 2 sets with a note', any('triple was clamped' in x for x in venn(sets=[{'name': n_, 'size': 30} for n_ in 'ABC'], overlaps=[{'sets': ['A', 'B'], 'size': 5}], triple=9)['venn']['notes']) and any('triple was ignored' in x for x in venn(sets=[{'name': 'A', 'size': 3}, {'name': 'B', 'size': 3}], triple=1)['venn']['notes']))
Vn = venn(sets=[{'name': n_, 'size': 10} for n_ in 'ABC'], overlaps=[{'sets': ['A', 'B'], 'size': 9.9}, {'sets': ['B', 'C'], 'size': 9.9}])['venn']; ok('venn3: distances that do not form a triangle are noted, not drawn silently', any('do not form a triangle' in x for x in Vn['notes']))
ok('venn: more than 3 sets cut with a note; fewer than 2 refused', any('beyond the 3rd' in x for x in venn(sets=[{'name': c_, 'size': 1} for c_ in 'ABCD'])['venn']['notes']) and raises(lambda: venn(sets=[{'name': 'A', 'size': 1}])) and raises(lambda: venn()))
Vd = venn(sets=[{'name': 'A', 'size': 5}, {'name': 'A', 'size': 6}, {'name': 'B', 'size': -1}, {'name': 'C', 'size': 7}, 'x', {'size': 2}, {'name': 'D', 'size': float('nan')}], overlaps=[{'sets': ['A', 'C'], 'size': -2}, {'sets': ['A', 'Z'], 'size': 1}, {'sets': ['A', 'A'], 'size': 1}, 'junk'])['venn']
ok('venn: unusable sets and overlaps dropped and counted', any('5 sets were left out' in x for x in Vd['notes']) and any('4 overlaps were dropped' in x for x in Vd['notes']) and Vd['names'] == ['A', 'C'])
# atom fields (rv-i143 venn_diagram)
Va = venn(set_a_name='PM', set_b_name='Tech', set_a_exclusive=['plan', 'roadmap'], set_b_exclusive=['code'], intersection=['specs', 'review', 'demos'])['venn']
ok('venn atom fields: sizes are the item counts (5 and 4), overlap 3, items listed in the table', Va['sizes'] == [5.0, 4.0] and abs(Va['drawn_overlaps'][(0, 1)] - 3) < 1e-6 and 'plan, roadmap' in Va['table'] and 'specs, review, demos' in Va['table'])
V3a = venn(set_a_name='A', set_b_name='B', set_c_name='C', set_a_exclusive=['a1'], set_b_exclusive=['b1', 'b2'], set_c_exclusive=['c1'], intersection=['ab'], intersection_ac=['ac1', 'ac2'], intersection_bc=['bc'], intersection_abc=['x', 'y'])['venn']
ok('venn atom fields, three sets: sizes from the seven regions, pair totals include the all-three region, triple requested = 2', V3a['sizes'] == [6.0, 6.0, 6.0] and V3a['overlaps'] == {(0, 1): 3.0, (0, 2): 4.0, (1, 2): 3.0} and V3a['requested_triple'] == 2.0 and 'All three: x, y' in V3a['table'])
Vm = venn(set_a_name='A', set_b_name='B', set_a_exclusive=[f'a{i}' for i in range(6)], set_b_exclusive=[f'b{i}' for i in range(70)], intersection=['s'])['venn']
ok('venn atom fields: 6 items stay 6 (no silent cut at 4); sizes use the real counts (7 and 71)', Vm['sizes'] == [7.0, 71.0] and 'a0, a1, a2, a3, a4, a5' in Vm['table'])
ok('venn atom fields: the table shows up to 60 per region and "+10 more" for the rest', 'b59' in Vm['table'] and 'b60' not in Vm['table'] and '+10 more' in Vm['table'])
Ve0 = venn(set_a_name='Empty', set_b_name='Full', set_a_exclusive=[], set_b_exclusive=['x', 'y'], intersection=[])['venn']
ok('venn atom fields: a set with no items is drawn as a marker with a note, not refused', Ve0['sizes'] == [0.0, 2.0] and any('Empty set' in x and 'marker' in x for x in Ve0['notes']) and len(circles(Ve0['svg'])) == 2 and circles(Ve0['svg'])[0][2] >= 5)
ok('venn: every set empty is refused', raises(lambda: venn(set_a_name='A', set_b_name='B')))
ok('venn: version 2 noted', any('version 1' in x for x in venn(sets=[{'name': 'A', 'size': 1}, {'name': 'B', 'size': 1}], version=2)['venn']['notes']))
Ve = venn(sets=[{'name': '<b>&"A', 'size': 4}, {'name': "B'<", 'size': 5}], overlaps=[{'sets': ['<b>&"A', "B'<"], 'size': 2}], unit='<u>', title='<t>')['venn']; ok('venn: labels XML-escaped, well-formed', wf(Ve) and '<b>' not in Ve['svg'])
ok('venn: colours only from PAL/blend, text >= 14 px, svg small, passes verify_svg', all(style_ok(x['svg']) and len(x['svg']) < 80000 and CM.verify_svg(x['svg']) for x in (V2, V3, Ve, Va)))
ok('venn: alt and table carry every size and overlap number used for the drawing', all(s in V3['alt'] for s in ('40', '60', '30', '15', '12', '6')) and all(s in V3['table'] for s in ('40', '60', '30', '15', '12', '6')))
ok('venn: deterministic', venn(**DEMOS['venn'])['venn']['svg'] == venn(**DEMOS['venn'])['venn']['svg'])
fz = True
for hv in HOST:
    fz &= only_valueerror(lambda: venn(sets=[{'name': 'a', 'size': hv}, {'name': 'b', 'size': 1}])); fz &= only_valueerror(lambda: venn(sets=[{'name': 'a', 'size': 2}, {'name': 'b', 'size': 1}], overlaps=[{'sets': ['a', 'b'], 'size': hv}]))
    fz &= only_valueerror(lambda: venn(sets=[{'name': 'a', 'size': 2}, {'name': 'b', 'size': 1}, {'name': 'c', 'size': 1}], triple=hv)); fz &= only_valueerror(lambda: venn(sets=[{'name': hv, 'size': 2}, {'name': 'b', 'size': 1}]))
    for kw in ('unit', 'title', 'version'): fz &= only_valueerror(lambda: venn(sets=[{'name': 'a', 'size': 2}, {'name': 'b', 'size': 1}], **{kw: hv}))
    fz &= only_valueerror(lambda: venn(set_a_name='a', set_b_name='b', set_a_exclusive=hv, intersection=[hv, [hv], {'a': hv}]))
ok('venn: hostile values in every parameter: only ValueError, valid SVG', fz)
ok('venn: sizes beyond 1e12 are dropped (so 1e308 cannot overflow the geometry)', raises(lambda: venn(sets=[{'name': 'a', 'size': 1e308}, {'name': 'b', 'size': 1e308}])))
# ======================= registry, demos, A2UI messages
ok('registry: contour_plot, venn and the atom name venn_diagram are all registered (same function for the last two)', set(PACK_FIELDS) == {'contour_plot', 'venn', 'venn_diagram'} and PACK_FIELDS['venn'] is PACK_FIELDS['venn_diagram'])
for dname, params in DEMOS.items():
    fn = PACK_FIELDS['contour_plot' if dname.startswith('contour') else 'venn']; r = fn(**params); default = r.pop('_default'); create, updates = CM.atom_card('T', r, default)
    ok(f'{dname}: createSurface validates', not list(A2R.iter_errors(create))); ok(f'{dname}: every update validates', all(not list(A2R.iter_errors(u)) for u in updates.values()))
    ok(f'{dname}: only Basic components', {c['component'] for c in create['createSurface']['components']} <= {'Card', 'Column', 'Row', 'Text', 'Image', 'Button'})
    ids = {c['id'] for c in create['createSurface']['components']}; refs = set()
    for c in create['createSurface']['components']: refs |= set(c.get('children', [])) | ({c['child']} if 'child' in c else set())
    ok(f'{dname}: references resolve, image described, payload < 200 KB', refs <= ids and all('description' in c for c in create['createSurface']['components'] if c['component'] == 'Image') and len(json.dumps(create)) < 200_000)
    b1 = copy.deepcopy(create); b1['version'] = 'v1.0'; ok(f'{dname}: negative: bad version rejected', bool(list(A2R.iter_errors(b1))))
    b2 = copy.deepcopy(create); b2['createSurface']['components'][2]['component'] = 'Chart'; ok(f'{dname}: negative: unknown component rejected', bool(list(A2R.iter_errors(b2))))
print(f'fields tests: {n} checks, {bad} failed'); sys.exit(1 if bad else 0)
