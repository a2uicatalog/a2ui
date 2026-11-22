"""d3 macro pack tests: independent arithmetic on each layout, the atoms' tolerant-reader rules, guard rails, determinism, and every message validated against the
upstream A2UI 1.0 schemas (with negative controls). No model, no browser, no network. Run: A2UI_UPSTREAM=<upstream checkout> python3 -B tests/test_pack.py"""
import calendar as cal, time, datetime as dt, glob, json, math, random, re, sys, copy
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
from d3pack.common import PAL
fmt_ = D.common.fmt
from d3pack import chord as CH, pack as PK
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
TAU = 2 * math.pi
# ---------- sunburst
IT = [{'path': ['A'], 'name': 'a1', 'value': 30}, {'path': ['A'], 'name': 'a2', 'value': 10}, {'path': ['B', 'x'], 'name': 'b1', 'value': 40}, {'name': 'solo', 'value': 20}]
r = D.sunburst(IT, unit='u'); rec = r['radial']['records']; tot = 100
ok('sunburst: top level arcs span the whole circle', abs(sum(x['f1'] - x['f0'] for x in rec if x['depth'] == 0) - 1) < 1e-9)
ok('sunburst: every arc is proportional to its value', all(abs((x['f1'] - x['f0']) - x['value'] / tot) < 1e-9 for x in rec))
byname = {x['name']: x for x in rec}; ok('sunburst: children sit inside their parent span', byname['a1']['f0'] >= byname['A']['f0'] - 1e-9 and byname['a2']['f1'] <= byname['A']['f1'] + 1e-9)
ok('sunburst: children fill the parent exactly', abs((byname['a1']['f1'] - byname['a1']['f0']) + (byname['a2']['f1'] - byname['a2']['f0']) - (byname['A']['f1'] - byname['A']['f0'])) < 1e-9)
ok('sunburst: item without a path is an innermost-ring arc', byname['solo']['depth'] == 0 and byname['b1']['depth'] == 2)
ok('sunburst: both layouts drawn, well-formed', wf(r['radial']) and wf(r['icicle'])); ok('sunburst: default radial', r['_default'] == 'radial')
ok('sunburst: unknown layout drawn as radial', D.sunburst(IT, layout='spiral')['_default'] == 'radial'); ok('sunburst: icicle accepted', D.sunburst(IT, layout='icicle')['_default'] == 'icicle')
rn = D.sunburst(IT + [{'name': 'bad', 'value': -1}, {'name': 'zero', 'value': 0}, 'junk', {'name': 'nan', 'value': float('nan')}, {'path': ['1', '2', '3', '4'], 'name': 'deep', 'value': 5}])
ok('sunburst: unusable items dropped and counted', [x for x in rn['radial']['notes'] if 'left out' in x] == ['4 items were left out (not an item, or no value above 0 that is a finite number).']); ok('sunburst: a 4-deep path is treated as no path', {x['name']: x for x in rn['radial']['records']}['deep']['depth'] == 0)
ok('sunburst: more than 40 items are cut and noted', any('beyond the 40th' in x for x in D.sunburst([{'name': f'i{i}', 'value': 1} for i in range(45)])['radial']['notes']))
ok('sunburst: version 2 drawn as 1 with a note', any('version 1' in x for x in D.sunburst(IT, version=2)['radial']['notes'])); ok('sunburst: fewer than 2 usable items -> a note replaces the chart', D.sunburst([{'name': 'a', 'value': 1}])['radial'].get('note_only') is True and wf(D.sunburst([{'name': 'a', 'value': 1}])['radial']))
ok('sunburst: text alternative lists every item', all(f"{i['name']} {i['value']}" in r['radial']['table'] for i in IT)); ok('sunburst: deterministic', D.sunburst(IT)['radial']['svg'] == D.sunburst(IT)['radial']['svg'])
ok('sunburst: markup in names stays well-formed', wf(D.sunburst([{'name': '<b>&"', 'value': 1}, {'name': 'x', 'value': 2}])['radial']))
# ---------- chord (d3.chord semantics) + inverse-read oracle on the drawing
NSV = '{http://www.w3.org/2000/svg}'
M = [[0, 12, 6, 20], [4, 0, 8, 3], [2, 5, 0, 1], [18, 2, 0, 0]]; groups, chords = CH.undirected_layout(M); total = sum(map(sum, M)); k = (TAU - CH.PAD * 4) / total
ok('chord: group arc = row sum x scale', all(abs((a1 - a0) - sum(M[i]) * k) < 1e-9 for i, (a0, a1) in enumerate(groups)))
ok('chord: groups plus pads fill the circle', abs(sum(a1 - a0 for a0, a1 in groups) + 4 * CH.PAD - TAU) < 1e-9)
ok('chord: one ribbon per linked pair', len(chords) == sum(1 for i in range(4) for j in range(i, 4) if M[i][j] or M[j][i]))
ok('chord: each ribbon end is the flow from that group (source end = src to tgt, target end = tgt to src)', all(abs((s[1] - s[0]) - M[a][b] * k) < 1e-9 and abs((t[1] - t[0]) - M[b][a] * k) < 1e-9 for a, b, s, t in chords))
def inside(seg, grp): return grp[0] - 1e-9 <= seg[0] and seg[1] <= grp[1] + 1e-9
ok('chord: each ribbon end lies inside its own group (source end in src, target end in tgt)', all(inside(s, groups[a]) and inside(t, groups[b]) for a, b, s, t in chords))
ok('chord: the source of a ribbon is the larger direction', all(M[a][b] >= M[b][a] for a, b, s, t in chords))
def ends_of(i):
    out = []
    for a, b, s, t in chords:
        if a == i: out.append((s[0], s[1] - s[0]))
        if b == i and b != a: out.append((t[0], t[1] - t[0]))
    return sorted(out)
ok('chord: subgroups are sorted largest first inside each group arc (the atom: sortSubgroups descending)', all([w for _, w in ends_of(i)] == sorted([w for _, w in ends_of(i)], reverse=True) for i in range(4)) and ends_of(0)[0][1] > ends_of(0)[-1][1])
g2, arrows = CH.directed_layout(M); ok('directed: one arrow per non-zero off-diagonal flow', len([a for a in arrows if a[0] != a[1]]) == sum(1 for i in range(4) for j in range(4) if i != j and M[i][j] > 0))
ok('directed: arrow width = the flow', all(abs((s[1] - s[0]) - M[i][j] * ((TAU - CH.PAD * 4) / (2 * total))) < 1e-9 for i, j, s, t in arrows if i != j))
cr = D.chord_diagram(['A', 'B', 'C', 'D'], M, unit='TB'); ok('chord: both modes drawn, well-formed', wf(cr['undirected']) and wf(cr['directed']))
def ang(p, c): return math.atan2(p[0] - c[0], -(p[1] - c[1])) % TAU
def seg(p0, p1, c):
    a = ang(p0, c); w = (ang(p1, c) - a) % TAU
    if w > TAU - 2e-3: w = 0.0
    if a > TAU - 2e-3: a -= TAU
    return a, a + w
def read_chord(r):
    """Parse the drawing back into group arcs, ribbons (colour, source end, target end) and legend; angles in radians."""
    rt = ET.fromstring(r['svg']); c = r['center']; arcs = []; ribs = []
    for p in rt.iter(NSV + 'path'):
        v = [float(x) for x in re.findall(r'-?\d+\.?\d*', p.attrib['d'])]
        if 'fill-opacity' in p.attrib:
            if len(v) == 24: ribs.append((p.attrib['fill'], seg(v[0:2], v[7:9], c), seg(v[11:13], v[18:20], c), 'ribbon'))
            else: ribs.append((p.attrib['fill'], seg(v[0:2], v[7:9], c), seg(v[11:13], v[15:17], c), 'arrow'))
        else: arcs.append((p.attrib['fill'], seg(v[0:2], v[7:9], c)))
    els = list(rt.iter()); leg = [(els[i + 1].text, e.attrib['fill']) for i, e in enumerate(els) if e.tag == NSV + 'rect' and e.attrib.get('width') == '16']
    return arcs, ribs, leg
def owner(arcs, e, tol=2e-3):
    h = [i for i, (_, (a0, a1)) in enumerate(arcs) if a0 - tol <= e[0] and e[1] <= a1 + tol]; return h[0] if len(h) == 1 else None
def chord_oracle(r, mm, directed):
    n = len(mm); tot = sum(map(sum, mm)); arcs, ribs, leg = read_chord(r); kk = (TAU - CH.PAD * n) / (tot * (2 if directed else 1)); col = {PAL[i % 8]: i for i in range(n)}
    want_arcs = [((sum(mm[i]) + (sum(mm[a][i] for a in range(n)) if directed else 0)) * kk) for i in range(n)]
    if [round(a1 - a0, 2) for _, (a0, a1) in arcs] != [round(w, 2) for w in want_arcs] or [col[c] for c, _ in arcs] != list(range(n)): return False
    got = set()
    for fill, s, t, kind in ribs:
        i = col[fill]; j = owner(arcs, t); si = owner(arcs, s)
        if si != i or j is None: return False
        if abs((s[1] - s[0]) - mm[i][j] * kk) > 3e-3: return False
        if not directed and abs((t[1] - t[0]) - mm[j][i] * kk) > 3e-3: return False
        got.add((i, j))
    if directed: want = {(i, j) for i in range(n) for j in range(n) if mm[i][j] > 0}
    else: want = {(i, j) if mm[i][j] >= mm[j][i] else (j, i) for i in range(n) for j in range(i, n) if mm[i][j] > 0 or mm[j][i] > 0}
    return got == want and len(ribs) == len(want if directed else want) + 0 and [(t_, c_) for t_, c_ in leg] == [(f'G{i}', PAL[i % 8]) for i in range(n)]
GN = ['G0', 'G1', 'G2', 'G3']; cr = D.chord_diagram(GN, M)
ok('chord INVERSE: every ribbon starts in its source group (colour = source), ends in its target group, with the widths of M[src][tgt] and M[tgt][src]; the pair set is exact', chord_oracle(cr['undirected'], M, False))
ok('chord INVERSE (directed): every arrow starts in the sender\'s arc (its colour), ends in the receiver\'s, width = the flow; group arcs = out + in', chord_oracle(cr['directed'], M, True))
M3 = [[0, 1, 9], [5, 0, 0], [0, 7, 3]]; c3 = D.chord_diagram(['G0', 'G1', 'G2'], M3)
ok('chord INVERSE: an asymmetric matrix with a zero direction and a loop (3 groups) also reads back exactly, both modes', chord_oracle(c3['undirected'], M3, False) and chord_oracle(c3['directed'], M3, True))
ok('chord: ribbon colour is the SOURCE group (the larger direction, here B), not the lower index', [x[0] for x in read_chord(D.chord_diagram(['A', 'B'], [[0, 1], [9, 0]])['undirected'])[1]] == [PAL[1]] and [x[0] for x in read_chord(D.chord_diagram(['A', 'B'], [[0, 9], [1, 0]])['undirected'])[1]] == [PAL[0]])
ok('chord: a visible legend names every group in its colour; hover titles carry "A to B: v (B to A: v)"', 'G1 to G0: 4 (G0 to G1: 12)' in cr['undirected']['svg'] or 'G0 to G1: 12 (G1 to G0: 4)' in cr['undirected']['svg'])
ok('chord: the table has every non-zero flow and each group\'s total out and in', 'G0 to G1 12' in cr['undirected']['table'] and 'G0 out 38, in 24' in cr['undirected']['table'] and 'G3 out 20, in 24' in cr['undirected']['table'])
ok('chord: alt text names the group count, total flow and largest flow with the table\'s numbers', f'4 groups; total flow {total}' in cr['undirected']['alt'] and 'largest flow is G0 to G3 (20)' in cr['undirected']['alt'])
def note_only_(r): v = r[r['_default']]; return bool(v.get('empty')) and 'Nothing was drawn' in v['alt']
ok('chord: a matrix that is not square, mismatching, not a list gives the atom\'s note (note-only Result)', all(note_only_(D.chord_diagram(a, b)) for a, b in ((['A', 'B'], [[0, 1, 2], [1, 0, 3]]), (['A', 'B', 'C'], [[0, 1], [1, 0]]), (['A', 'B'], 'x'), (['A', 'B'], [[0, 1], 5]))) and 'square matrix with one row per group' in D.chord_diagram(['A', 'B'], [[0, 1, 2], [1, 0, 3]])['undirected']['alt'])
ok('chord: fewer than 2 groups, groups not a list, an all-zero matrix: note-only', all(note_only_(D.chord_diagram(a, b)) for a, b in ((['A'], [[1]]), (None, [[1]]), (['A', 'B'], [[0, 0], [0, 0]]))))
cn = D.chord_diagram(['A', None, 3], [[0, 1, 1], [1, 0, -2], [1, 'x', 0]]); ok('chord: non-string name becomes Group n, number kept', 'Group 2' in cn['undirected']['table'] and '; 3 to A 1' in cn['undirected']['table'] and 'A to 3 1' in cn['undirected']['table'])
ok('chord: bad cells treated as 0 and counted in one note', sum(1 for x in cn['undirected']['notes'] if 'treated as 0' in x and '2 cells' in x) == 1)
ok('chord: more than 12 groups: cut and noted', any('beyond the 12th' in x for x in D.chord_diagram([f'g{i}' for i in range(14)], [[1] * 14 for _ in range(14)])['undirected']['notes']))
ch1 = D.chord_diagram(['a', 'b'], [[0, 1e308], [10**400, float('nan')]])['undirected']
ok('chord NEGATIVE: cells of 1e308 and 10**400 are clamped to 1e12 and noted; NaN is 0; no overflow, finite drawing', any('clamped to 1,000,000,000,000' in x for x in ch1['notes']) and any('treated as 0' in x for x in ch1['notes']) and 'nan' not in ch1['svg'].lower() and 'inf' not in ch1['svg'].lower())
ok('chord NEGATIVE: infinite and -10**400 cells count as 0', note_only_(D.chord_diagram(['a', 'b'], [[0, float('inf')], [-10**400, 0]])) and all(isinstance(D.chord_diagram([{'x': 1}, [2]], [[1, 1], [1, 1]]), dict) for _ in [0]))
ok('chord: a hostile unit (markup, entities, CDATA, comment) is escaped everywhere: well-formed, passes the policy, no tag injected', all(wf(D.chord_diagram(GN, M, unit=u_)['undirected']) and '<script' not in D.chord_diagram(GN, M, unit=u_)['undirected']['svg'] for u_ in ('<script>alert(1)</script>', '&amp;&#x3c;&lt;', ']]><![CDATA[x', '--><!--', '<?x?>', '"><g/>')))
ok('arc: a hostile unit is escaped everywhere too', all(wf(D.arc_diagram([{'id': 'a'}, {'id': 'b'}], [{'source': 'a', 'target': 'b'}], unit=u_)['input']) for u_ in ('<script>', '&amp;', ']]>', '--><!--', '<?x?>')))
ok('chord NEGATIVE: 10**400 as title, unit, version, group name does not raise', isinstance(D.chord_diagram(['a', 10**400], [[1, 1], [1, 1]], title=10**400, unit=10**400, version=10**400), dict))
ok('chord: version 2 drawn as 1 with a note; the unit appears in the table and the title text', any('version 1' in x for x in D.chord_diagram(GN, M, version=2)['undirected']['notes']) and 'G0 to G1 12 TB' in D.chord_diagram(GN, M, unit='TB')['undirected']['table'] and 'TB' in D.chord_diagram(GN, M, unit='TB')['undirected']['svg'])
# ---------- arc
ND = [{'id': c, 'label': c.upper(), 'group': g} for c, g in (('a', 'x'), ('b', 'y'), ('c', 'x'), ('d', None))]; LK = [{'source': 'a', 'target': 'b', 'value': 2}, {'source': 'b', 'target': 'c'}, {'source': 'a', 'target': 'a'}, {'source': 'a', 'target': 'zz'}, {'source': 'c', 'target': 'd', 'value': 0}, 'x']
ar = D.arc_diagram(ND, LK); ok('arc: nodes evenly spaced on the line (scalePoint padding 0.5: first at margin + half a step)', len({round(b - a, 6) for a, b in zip(sorted(ar['input']['pos'].values()), sorted(ar['input']['pos'].values())[1:])}) == 1 and abs(ar['input']['pos']['a'] - (40 + 640 / 4 / 2)) < 1e-9)
ok('arc: bad links dropped and counted (self, unknown id, zero value, non-object)', any('4 links were dropped' in x for x in ar['input']['notes'])); ok('arc: two links drawn', ar['input']['svg'].count('<path') == 2)
ok('arc: default value is 1; table links use labels, nodes table has id, label, group, count', 'B to C 1' in ar['input']['table'] and 'a (A, group x, 1 links)' in ar['input']['table'] and 'd (D, 0 links)' in ar['input']['table'])
ok('arc: order=group puts the ungrouped node first then by group', ar['group']['order'] == ['d', 'a', 'c', 'b'])
ok('arc: order=degree puts the most connected first, ties keep input order', ar['degree']['order'][0] == 'b' and ar['degree']['order'][1:] == ['a', 'c', 'd'])
ok('arc: unknown order is input', D.arc_diagram(ND, LK, order='zigzag')['_default'] == 'input'); ok('arc: duplicate id left out and counted', any('left out' in x for x in D.arc_diagram(ND + [{'id': 'a'}], LK)['input']['notes']))
ok('arc: fewer than 2 nodes: note-only Result; more than 40 nodes cut', note_only_(D.arc_diagram([{'id': 'a'}])) and note_only_(D.arc_diagram('x')) and any('beyond the 40th' in x for x in D.arc_diagram([{'id': str(i)} for i in range(45)], [])['input']['notes']))
ok('arc: no links is allowed', 'no links' in D.arc_diagram(ND, [])['input']['table']); ok('arc: well-formed', all(wf(v) for k_, v in ar.items() if k_ != '_default'))
def read_arc(r):
    rt = ET.fromstring(r['svg']); dots = [(float(c.attrib['cx']), c.attrib['fill']) for c in rt.iter(NSV + 'circle')]; arcs = []
    for p in rt.iter(NSV + 'path'):
        m = re.fullmatch(r'M([\d.]+),([\d.]+) A([\d.]+),([\d.]+) 0 0 1 ([\d.]+),([\d.]+)', p.attrib['d']); x0, x1 = float(m.group(1)), float(m.group(5))
        arcs.append((x0, x1, float(m.group(3)), float(p.attrib['stroke-width']), p.attrib['stroke']))
    els = list(rt.iter()); leg = [(els[i + 1].text, e.attrib['fill']) for i, e in enumerate(els) if e.tag == NSV + 'rect' and e.attrib.get('width') == '16']
    names = [(float(tx.attrib['x']), tx.text, tx.attrib.get('transform')) for tx in rt.iter(NSV + 'text') if tx.attrib.get('transform')]
    return dots, arcs, leg, names
def arc_oracle(r, nodes, links, vals):
    """links: [(src_id, tgt_id, value)] the valid links, in any order. Reads widths, ends and colours back and compares them with the input."""
    dots, arcs, leg, names = read_arc(r); xs = {nd['id']: r['pos'][nd['id']] for nd in nodes}; dotcol = {nid: next(c for x, c in dots if abs(x - xs[nid]) < .01) for nid in xs}
    lo, hi = min(vals), max(vals); wid = lambda v: 2.0 if lo == hi else 1 + 5 * (v - lo) / (hi - lo); got = []
    for x0, x1, rad, w, col in arcs:
        a = next((i for i, nd in enumerate(nodes) if abs(xs[nd['id']] - x0) < .01), None); b = next((i for i, nd in enumerate(nodes) if abs(xs[nd['id']] - x1) < .01), None)
        if a is None or b is None or abs(rad - (x1 - x0) / 2) > .01: return False
        got.append((tuple(sorted((nodes[a]['id'], nodes[b]['id']))), round(w, 2), col))
    want = [(tuple(sorted((s, t))), round(wid(v), 2), dotcol[s]) for s, t, v in links]
    return sorted(got) == sorted(want)
vl = [('a', 'b', 2), ('b', 'c', 1)]
ok('arc INVERSE: each arc joins exactly the two dots of its link, as a semicircle, takes the colour of its SOURCE node\'s dot, and its thickness is 1 + 5 (v - min) / (max - min): value 1 -> 1 px, value 2 -> 6 px', arc_oracle(ar['input'], ND, vl, [2, 1]) and arc_oracle(ar['degree'], ND, vl, [2, 1]) and arc_oracle(ar['group'], ND, vl, [2, 1]))
n5 = [{'id': c} for c in 'abcde']; l5 = [('a', 'b', 1), ('b', 'c', 2), ('c', 'd', 4), ('d', 'e', 10), ('a', 'e', 5.5)]; a5 = D.arc_diagram(n5, [{'source': s, 'target': t, 'value': v} for s, t, v in l5])['input']
ok('arc INVERSE: five different values: thickness strictly increasing with value, min 1 px, max 6 px', arc_oracle(a5, n5, l5, [v for *_, v in l5]) and sorted(w for *_, w, _c in read_arc(a5)[1])[0] == 1.0 and sorted(w for *_, w, _c in read_arc(a5)[1])[-1] == 6.0)
ae = D.arc_diagram(n5, [{'source': 'a', 'target': 'b', 'value': 3}, {'source': 'b', 'target': 'c', 'value': 3}, {'source': 'a', 'target': 'd', 'value': 3}])['input']
ok('arc INVERSE: when every explicit value is equal every link is 2 px', [w for *_, w, _c in read_arc(ae)[1]] == [2.0, 2.0, 2.0])
ae2 = D.arc_diagram(n5, [{'source': 'a', 'target': 'b'}, {'source': 'b', 'target': 'c'}])['input']; ok('arc: equal values (the default 1) draw every arc 2 px', [w for *_, w, _c in read_arc(ae2)[1]] == [2.0, 2.0])
dots, arcs, leg, names = read_arc(ar['input'])
ok('arc INVERSE: arcs take the colour of their source node\'s group (x: slate-free palette hue, y another); ungrouped dot is slate', len({d[1] for d in dots}) == 3 and dots[3][1] == '#59607a' and dots[0][1] == dots[2][1] != dots[1][1])
ok('arc INVERSE: the legend has one swatch per group, in the dots\' colours, plus "no group" for ungrouped nodes', [x[0] for x in leg] == ['x', 'y', 'no group'] and leg[0][1] == dots[0][1] and leg[1][1] == dots[1][1] and leg[2][1] == '#59607a')
ok('arc: no legend when no node has a group', read_arc(D.arc_diagram([{'id': 'a'}, {'id': 'b'}], [{'source': 'a', 'target': 'b'}])['input'])[2] == [])
ok('arc: node names are rotated 90 degrees, one per node when they fit', len(names) == 4 and all(re.fullmatch(r'rotate\(90 [\d.]+ [\d.]+\)', tr) for _, _, tr in names) and [t_ for _, t_, _ in names] == ['A', 'B', 'C', 'D'])
a40 = D.arc_diagram([{'id': f'n{i}'} for i in range(40)], [])['input']; nm40 = read_arc(a40)[3]
ok('arc: 40 nodes are 16 px apart (enough for 14 px text): every name is drawn, rotated 90 degrees, none thinned', len(nm40) == 40 and nm40[0][1] == 'n0' and nm40[39][1] == 'n39' and all(nm40[i + 1][0] - nm40[i][0] >= 15.99 for i in range(39)) and not any('every' in x for x in a40['notes']))
ok('arc: markup in labels is escaped and text is at least 12px', wf(D.arc_diagram([{'id': '<a>', 'label': '<b>&"'}, {'id': 'b'}], [{'source': '<a>', 'target': 'b'}])['input']) and all(float(t_.attrib['font-size']) >= 12 for t_ in ET.fromstring(ar['input']['svg']).iter(NSV + 'text')))
ok('arc NEGATIVE: a link whose source or target is a dict, list, bool or None is dropped, not a TypeError', (lambda r: len(r['input']['pos']) == 2 and any('3 links were dropped' in x or '4 links were dropped' in x for x in r['input']['notes']))(D.arc_diagram([{'id': 'a'}, {'id': 'b'}], [{'source': ['a'], 'target': 'b'}, {'source': {'x': 1}, 'target': 'b'}, {'source': True, 'target': 'b'}, {'source': None, 'target': 'a'}])))
ok('arc NEGATIVE: link value 1e308 is drawn (thickest), 10**400 and NaN dropped; ids that are dicts or lists are left out; 10**400 title, unit, version fine', (lambda r: len(read_arc(r['input'])[1]) == 2 and any('2 links were dropped' in x for x in r['input']['notes']))(D.arc_diagram([{'id': 'a'}, {'id': 'b'}, {'id': 'c'}, {'id': {'q': 1}}, {'id': [1]}], [{'source': 'a', 'target': 'b', 'value': 1e308}, {'source': 'b', 'target': 'c', 'value': 1}, {'source': 'a', 'target': 'c', 'value': 10**400}, {'source': 'a', 'target': 'c', 'value': float('nan')}], title=10**400, unit=10**400, version=10**400)))
# ---------- hostile-input sweep (chord, arc) through d3pack.call
HOST = [None, True, 0, -1, 1.5, 1e308, -1e308, float('nan'), float('inf'), 10**400, -10**400, '', 'x' * 300, '<b>&"‮\x00', [], {}, [[]], {'a': [1]}, [1, 'a'], [None] * 3]
def _leaves(o, path=()):
    if isinstance(o, dict):
        for k_, v in o.items(): yield from _leaves(v, path + (k_,))
    elif isinstance(o, list):
        for i, v in enumerate(o[:6]): yield from _leaves(v, path + (i,))
    else: yield path
def _setp(o, path, v):
    o = copy.deepcopy(o); cur = o
    for k_ in path[:-1]: cur = cur[k_]
    cur[path[-1]] = v; return o
def sweep(name, params):
    fails = 0; runs = 0
    for path in _leaves(params):
        for hv in HOST:
            runs += 1
            try: r = D.call(name, _setp(params, path, hv), isolate=False)
            except D.MacroError as e:
                if any(w in str(e) for w in ('failed on this input', 'too deeply', 'time budget', 'memory', 'output policy')): fails += 1; print('   ', name, path, repr(hv)[:30], str(e)[:70])
            except Exception as e: fails += 1; print('   ', name, path, repr(hv)[:30], type(e).__name__)
    return fails, runs
for nm, pr in (('chord_diagram', dict(groups=['A', 'B', 'C'], matrix=[[0, 1, 2], [3, 0, 4], [5, 6, 0]], unit='u', title='t', directed=False, version=1)), ('arc_diagram', dict(nodes=[{'id': 'a', 'label': 'A', 'group': 'g'}, {'id': 'b'}, {'id': 'c'}], links=[{'source': 'a', 'target': 'b', 'value': 2}, {'source': 'b', 'target': 'c'}], order='group', unit='u', title='t'))):
    f_, runs_ = sweep(nm, pr); ok(f'sweep: {nm}: {runs_} hostile single-value substitutions, no crash message', f_ == 0)
# ---------- calendar (checked against Python's calendar module)
data = [{'date': '2028-02-29', 'count': 5}, {'date': '2028-02-01', 'count': 2}, {'date': '2028-03-15', 'count': 9}, {'date': '2028-03-15', 'count': 1}, {'date': '2028-01-01', 'count': 7}, {'date': '2028-02-30', 'count': 1}, {'date': '2028-13-01', 'count': 1}, {'date': 'x', 'count': 1}, {'date': '2028-03-01', 'count': -1}]
cr = D.heatmap_calendar(data, months=2); r = cr['calendar']
ok('calendar: shows the latest month and the one before', r['months'] == [(2028, 2), (2028, 3)]); ok('calendar: counts on the same day are summed', r['shown'][dt.date(2028, 3, 15)] == 10)
ok('calendar: invalid dates and counts dropped and counted', [x for x in r['notes'] if 'left out' in x] == ['4 entries were left out (each needs a real date YYYY-MM-DD and a count from 0 to 1e12).']); ok('calendar: the leap day exists (Feb 2028 has 29 days)', dt.date(2028, 2, 29) in r['shown'])
ok('calendar: dates outside the window are noted', any('outside' in x for x in r['notes'])); svgtxt = r['svg']
ok('calendar: one cell per real day of each month', svgtxt.count('<rect x=') == cal.monthrange(2028, 2)[1] + cal.monthrange(2028, 3)[1])
xs = {}
for mm in re.finditer(r'<rect x="([\d.]+)" y="([\d.]+)"[^>]*><title>(\d{4}-\d{2}-\d{2})', svgtxt): xs[dt.date.fromisoformat(mm.group(3))] = float(mm.group(1))
for (yy, mo) in ((2028, 2), (2028, 3)):
    mine = {d: x for d, x in xs.items() if (d.year, d.month) == (yy, mo)}; base = min(mine.values())
    ok(f'calendar: {yy}-{mo:02d} every day sits in its weekday column (Monday-first), checked against datetime', all(round((x - base) / 26) == d.weekday() for d, x in mine.items()))
ok('calendar: months clamped to 1..12 with a note', any('clamped' in x for x in D.heatmap_calendar(data, months=40)['calendar']['notes'])); ok('calendar: no usable entries refused', raises(lambda: D.heatmap_calendar([{'date': 'x', 'count': 1}])))
cs = D.heatmap_calendar([{'date': '2026-05-01', 'count': 1}, {'date': '2026-05-02', 'count': 4}, {'date': '2026-05-03', 'count': 8}], months=1, color_scale=['#000000', '#ff0000', '#00ff00'])['calendar']['svg']
ok('calendar: well-formed', wf(r))
def cal_read(res_):
    NS_ = '{http://www.w3.org/2000/svg}'; rt = ET.fromstring(res_['svg']); cells = {}; texts = [(float(e.get('x')), float(e.get('y')), e.text) for e in rt.iter(NS_ + 'text') if e.get('font-size') == '12']
    for e in rt.iter(NS_ + 'rect'):
        t = e.find(NS_ + 'title')
        if t is None: continue
        d_, v_ = t.text.split(': ', 1); x_, y_, w_, h_ = (float(e.get(k)) for k in ('x', 'y', 'width', 'height')); inner = [tx for px, py, tx in texts if x_ <= px <= x_ + w_ and y_ <= py <= y_ + h_]
        cells[dt.date.fromisoformat(d_)] = (e.get('fill'), v_, inner[0] if inner else None)
    return cells
SC = ['#000000', '#ff0000', '#00ff00']; cm = cal_read(D.heatmap_calendar([{'date': '2026-05-01', 'count': 1}, {'date': '2026-05-02', 'count': 4}, {'date': '2026-05-03', 'count': 8}, {'date': '2026-05-04', 'count': 0.5}], months=1, color_scale=SC)['calendar'])
ok('calendar read-back: colours are 1->#ff0000, 4->#ff0000, 8->#00ff00 (index 1 + int(2 v / 8), checked by hand) and empty days use the first colour', cm[dt.date(2026, 5, 1)][0] == '#ff0000' and cm[dt.date(2026, 5, 2)][0] == '#ff0000' and cm[dt.date(2026, 5, 3)][0] == '#00ff00' and cm[dt.date(2026, 5, 4)][0] == '#ff0000' and cm[dt.date(2026, 5, 9)][0] == '#000000')
ok("calendar read-back: the number printed in each cell is that day's count", cm[dt.date(2026, 5, 1)][2] == '1' and cm[dt.date(2026, 5, 2)][2] == '4' and cm[dt.date(2026, 5, 3)][2] == '8' and cm[dt.date(2026, 5, 4)][2] == '0.5' and cm[dt.date(2026, 5, 9)][2] is None)
rg = random.Random(4); good = True; good2 = True
for _ in range(15):
    dd = [{'date': f'2026-07-{d_:02d}', 'count': rg.choice([0, 1, 2, 5, 9, 30, 100])} for d_ in range(1, 29)]; cmm = cal_read(D.heatmap_calendar(dd, months=1, color_scale=SC)['calendar']); rank = {c: i for i, c in enumerate(SC)}
    pts = sorted((x['count'], rank[cmm[dt.date.fromisoformat(x['date'])][0]]) for x in dd)
    good = good and all(a[1] <= b[1] for a, b in zip(pts, pts[1:])) and all(rank[cmm[dt.date.fromisoformat(x['date'])][0]] == (0 if x['count'] == 0 else 2 if x['count'] == max(y['count'] for y in dd) else 1) for x in dd)
    good2 = good2 and all((cmm[dt.date.fromisoformat(x['date'])][2] == (str(x['count']) if x['count'] else None)) for x in dd)
ok('calendar read-back: colour rank never falls as the count rises, zero is the first colour, the busiest day the last (15 random months)', good); ok('calendar read-back: every printed number equals its count (15 random months)', good2)
yr = [{'date': f'2026-{m_:02d}-{d_:02d}', 'count': d_ * m_} for m_ in range(1, 13) for d_ in range(1, 29)]; ry = D.heatmap_calendar(yr, months=12, unit='commits')['calendar']
ok('calendar: 12 months of daily data degrades (titles, then numbers) instead of being refused, and says so', len(ry['svg']) < 80_000 and any('left out to keep it small' in x for x in ry['notes']) and wf(ry) and '2026-12-28 336' in ry['table'])
ok('calendar: 5000 entry cap is noted and bad entries make ONE note', any('beyond the 5000th' in x for x in D.heatmap_calendar([{'date': '2026-01-01', 'count': 1}] * 5003)['calendar']['notes']) and len(D.heatmap_calendar([{'date': '2026-01-01', 'count': 1}] + ['x'] * 400)['calendar']['notes']) == 1)
BG_ = 10 ** 400; hr = D.heatmap_calendar([{'date': '2026-01-01', 'count': BG_}, {'date': '2026-01-02', 'count': float('nan')}, {'date': '2026-01-03', 'count': 1e13}, {'date': '2026-01-04', 'count': 3}, {'date': '٢٠٢٦-01-05', 'count': 1}, {'date': {'x': 1}, 'count': 1}], months=BG_, unit=BG_, title=BG_, version='x', color_scale=[{'a': 1}, '#000000'])['calendar']
ok('calendar negative controls: 10**400 count/months/unit/title, NaN, 1e13, non-ASCII digits, dict date, version="x" never raise; only the good day is kept', hr['shown'] == {dt.date(2026, 1, 4): 3} and wf(hr) and any('5 entries' in x for x in hr['notes']))
ok('calendar: version 2 is accepted and noted', any('version 1' in x for x in D.heatmap_calendar(data, months=2, version=2)['calendar']['notes']))
ok('calendar: months that is not a whole number falls back to 3 with a note', any('whole number' in x for x in D.heatmap_calendar(data, months=2.5)['calendar']['notes']) and len(D.heatmap_calendar(data, months='x')['calendar']['months']) == 3)

# ---------- circle pack: independent geometry
rng = random.Random(5)
for trial in range(25):
    items = [{'path': [rng.choice('ABC')] if rng.random() < .8 else [], 'name': f'i{i}', 'value': rng.choice([1, 2, 3, 5, 8, 13, 40])} for i in range(rng.randint(3, 40))]
    cp = D.circle_pack(items)['circle_pack']; C = cp['circles']; sib = {}
    for c in C: sib.setdefault(c['parent'], []).append(c)
    over = [(a['name'], b['name']) for g in sib.values() for i, a in enumerate(g) for b in g[i + 1:] if math.hypot(a['x'] - b['x'], a['y'] - b['y']) < a['r'] + b['r'] - 1e-6]
    if over: ok(f'pack trial {trial}: no sibling overlap {over[:2]}', False); break
else: ok('circle pack: no sibling circles overlap (25 random datasets)', True)
items = [{'name': f'i{i}', 'value': v} for i, v in enumerate((1, 4, 9, 16))]; C = D.circle_pack(items)['circle_pack']['circles']; leaves = {c['name']: c for c in C if c['leaf']}
ok('circle pack: area proportional to value (r^2 ratios)', all(abs(leaves[f'i{i}']['r'] ** 2 / leaves['i0']['r'] ** 2 - v) < 1e-6 for i, v in enumerate((1, 4, 9, 16)))); ok('circle pack: all inside the drawing', all(0 <= c['x'] - c['r'] and c['x'] + c['r'] <= D.common.W and 0 <= c['y'] - c['r'] and c['y'] + c['r'] <= D.common.H for c in C))
nested = D.circle_pack([{'path': ['G'], 'name': 'a', 'value': 5}, {'path': ['G'], 'name': 'b', 'value': 3}, {'name': 'c', 'value': 4}])['circle_pack']['circles']; grp = [c for c in nested if not c['leaf']][0]
ok('circle pack: a group circle contains its children', all(math.hypot(c['x'] - grp['x'], c['y'] - grp['y']) + c['r'] <= grp['r'] + 1e-6 for c in nested if c['leaf'] and c['depth'] == 1))
ok('circle pack: deterministic', D.circle_pack(items)['circle_pack']['svg'] == D.circle_pack(items)['circle_pack']['svg']); ok('circle pack: fewer than 2 -> a note replaces the chart', D.circle_pack([{'name': 'a', 'value': 1}])['circle_pack'].get('note_only') is True); ok('circle pack: 60 cap', any('60th' in x for x in D.circle_pack([{'name': str(i), 'value': 1} for i in range(65)])['circle_pack']['notes']))
# ---------- round 2: inverse-read oracles (the drawing is parsed back to data and compared with the input), boundary inputs, degradation
SVGNS = '{http://www.w3.org/2000/svg}'
def parse_arcs(svgtxt, cx=360, cy=260):
    """For every <path> arc: (start angle, sweep) in radians read back from the path data (0 = 12 o'clock, clockwise)."""
    out = []
    for pth in ET.fromstring(svgtxt).iter(SVGNS + 'path'):
        v = [float(t) for t in re.findall(r'-?\d+\.?\d*', pth.get('d'))]; x0, y0, large, x1, y1 = v[0], v[1], v[5], v[7], v[8]
        a0 = math.atan2(x0 - cx, cy - y0) % TAU; a1 = math.atan2(x1 - cx, cy - y1) % TAU; sw = (a1 - a0) % TAU
        if large == 1 and sw < math.pi: sw += TAU
        out.append((a0, sw))
    return out
def texts(svgtxt): return [(float(e.get('x')), float(e.get('y')), int(e.get('font-size')), e.text) for e in ET.fromstring(svgtxt).iter(SVGNS + 'text')]
SB = [{'path': ['A'], 'name': 'a1', 'value': 30}, {'path': ['A'], 'name': 'a2', 'value': 10}, {'path': ['B', 'x'], 'name': 'b1', 'value': 40}, {'name': 'solo', 'value': 20}, {'path': ['B'], 'name': 'b2', 'value': 5}]
sr = D.sunburst(SB, unit='u'); recs = sr['radial']['records']; arcs = parse_arcs(sr['radial']['svg']); stot = 105
ok('sunburst oracle: one drawn arc per record', len(arcs) == len(recs))
ok('sunburst oracle: every drawn arc angle / 360 equals its share of the total (read back from the path data)', all(abs(sw / TAU - r['value'] / stot) < 5e-4 for (a0, sw), r in zip(arcs, recs)))
ok('sunburst oracle: top-level arcs together span the full circle', abs(sum(sw for (a0, sw), r in zip(arcs, recs) if r['depth'] == 0) - TAU) < 2e-3)
tops = [(a0, sw, r) for (a0, sw), r in zip(arcs, recs) if r['depth'] == 0]
ok('sunburst oracle: top-level arcs are contiguous, starting at 12 o clock', abs(tops[0][0]) < 2e-3 or abs(tops[0][0] - TAU) < 2e-3)
ok('sunburst: groups ordered largest first (drawn sweep decreasing)', all(a[1] >= b[1] - 1e-3 for a, b in zip(tops, tops[1:])) and [t[2]['name'] for t in tops] == ['B', 'A', 'solo'])
ok('sunburst oracle: centre text is the total with the unit label', any(t[3] == '105' and t[2] == 28 for t in texts(sr['radial']['svg'])) and any(t[3] == 'u' for t in texts(sr['radial']['svg'])))
ic = [e for e in ET.fromstring(sr['icicle']['svg']).iter(SVGNS + 'rect') if e.get('fill') != '#ffffff' and e.get('rx') is None]
ok('sunburst oracle: icicle bar heights (+2 px gap) equal share x 440 px', len(ic) == len(recs) and all(abs((float(e.get('height')) + 2) / 440 - r['value'] / stot) < 1e-3 for e, r in zip(ic, recs)))
ok('sunburst: table gives the share of every item', all(f"({100 * v / stot:.1f}%)" in sr['radial']['table'] for v in (30, 10, 40, 20, 5)))
ok('sunburst: summary names the largest GROUP (B = 45)', 'largest group is B (45, 43%)' in sr['radial']['summary'] and '3 top-level groups' in sr['radial']['summary'])
ok('sunburst: dropped items give ONE note with a count', sum(1 for x in D.sunburst(SB + [{'value': -1}] * 7)['radial']['notes'] if 'left out' in x) == 1 and '7 items were left out' in ' '.join(D.sunburst(SB + [{'value': -1}] * 7)['radial']['notes']))
huge = D.sunburst([{'name': 'a', 'value': 1e308}, {'name': 'b', 'value': 1e308}, {'name': 'c', 'value': 10 ** 400}])['radial']
ok('sunburst boundary: values above 1e12 (even 10**400, 1e308 sums) are clamped with a note, no nan/inf anywhere', any('3 values were above' in x for x in huge['notes']) and not re.search(r'nan|inf', huge['svg'] + huge['alt'] + huge['table'], re.I) and 'Total 3,000,000,000,000' in huge['summary'])
ok('sunburst boundary: 10**400 title/unit/name/path/layout, dict and list names and ids do not crash', wf(D.sunburst([{'name': {'x': 1}, 'value': 1, 'path': [['q']]}, {'name': ['l'], 'value': 2, 'path': [10 ** 400]}, {'name': 10 ** 400, 'value': 3, 'path': [None, 'x']}], unit=10 ** 400, title={'a': 1}, layout=[1], version=10 ** 400)['radial']))
ok('sunburst boundary: subnormal and inf and nan and bool values: only the real values drawn', (lambda q: len(q['records']) == 2 and any('3 items were left out' in x for x in q['notes']))(D.sunburst([{'name': 'a', 'value': 5e-324}, {'name': 'b', 'value': 1}, {'name': 'c', 'value': float('inf')}, {'name': 'd', 'value': float('nan')}, {'name': 'e', 'value': True}])['radial']))
ok('sunburst boundary: tiny share arcs stay finite', wf(D.sunburst([{'name': 'a', 'value': 5e-324}, {'name': 'b', 'value': 1e12}])['radial']))
ok('sunburst negative control: a sunburst drawn at 324 degrees would be caught by the oracle', not all(abs(sw * 1.1 / TAU - r['value'] / stot) < 5e-4 for (a0, sw), r in zip(arcs, recs)))
def disks(svgtxt): return [(float(e.get('cx')), float(e.get('cy')), float(e.get('r')), e.get('fill')) for e in ET.fromstring(svgtxt).iter(SVGNS + 'circle')][0:]
CPI = [{'path': ['G1'], 'name': 'a', 'value': 16}, {'path': ['G1'], 'name': 'b', 'value': 9}, {'path': ['G1'], 'name': 'c', 'value': 4}, {'path': ['G2', 'H'], 'name': 'd', 'value': 25}, {'path': ['G2'], 'name': 'e', 'value': 1}, {'name': 'f', 'value': 6}, {'name': 'g', 'value': 12}]
cpr = D.circle_pack(CPI, unit='GB')['circle_pack']; dk = disks(cpr['svg']); recs_c = cpr['circles']
dk = [d for d in dk]; ok('circle pack oracle: one drawn circle per record', len(dk) == len(recs_c))
leafd = [(d, r) for d, r in zip(dk, recs_c) if r['leaf']]; grpd = [(d, r) for d, r in zip(dk, recs_c) if not r['leaf']]
ok('circle pack: leaf circles are filled and group circles are outlined (fill none)', all(d[3] != 'none' for d, r in leafd) and all(d[3] == 'none' for d, r in grpd) and len(grpd) == 3)
sib = {}
for d, r in zip(dk, recs_c): sib.setdefault(r['parent'], []).append(d)
gaps = [min(math.hypot(a[0] - b[0], a[1] - b[1]) - a[2] - b[2] for i, a in enumerate(g) for b in g[i + 1:]) for g in sib.values() if len(g) > 1]
g0 = min(gaps)
ok('circle pack oracle: sibling circles never overlap and the tightest gap is the same padding in every sibling set (read from the SVG)', g0 > 0.01 and all(abs(x - g0) < 0.05 for x in gaps))
vmaxc = 25.0
ok('circle pack oracle: leaf radius = 20 x padding x sqrt(value / largest) (padding 3 in layout units, read back from drawn gaps)', all(abs(d[2] / g0 - 20 * math.sqrt(r['value'] / vmaxc)) < 0.02 * d[2] / g0 + 0.05 for d, r in leafd))
tops_c = [d for d, r in zip(dk, recs_c) if r['depth'] == 0]; ext = max(math.hypot(d[0] - 360, d[1] - 260) + d[2] for d in tops_c)
ok('circle pack oracle: the whole drawing fits the canvas disc of radius 240 minus one padding', abs(ext - (240 - g0)) < 0.6)
byparent = {}
for d, r in zip(dk, recs_c): byparent.setdefault(r['parent'], []).append((d, r))
kidsof = {r['id']: [d for d, q in zip(dk, recs_c) if q['parent'] == r['id']] for d, r in grpd}
ok('circle pack oracle: each group circle = its drawn children enclosed + one padding (tight)', all(abs(d[2] - (max(math.hypot(c[0] - d[0], c[1] - d[1]) + c[2] for c in kidsof[r['id']]) + g0)) < 0.05 for d, r in grpd))
ok('circle pack: every child circle lies inside its group circle in the drawing', all(math.hypot(c[0] - d[0], c[1] - d[1]) + c[2] <= d[2] + 0.02 for d, r in grpd for c in kidsof[r['id']]))
ic_txt = texts(sr['icicle']['svg'])
ok('sunburst oracle: icicle labels carry name and value of the bars tall enough to label', all(any(t_[3] == f"{r['name']} {fmt_(r['value'])}" for t_ in ic_txt) for r in recs if (r['f1'] - r['f0']) * 440 - 2 >= 22) and any(t_[3] == 'a1 30' for t_ in ic_txt))
ok('circle pack: padding is the atom\'s 3 (scale-free: drawn gap / scale)', abs(g0 / cpr['scale'] - 3) < 0.05 and abs(cpr['padding'] - g0) < 0.05)
ok('circle pack: leaf labels and group labels are 12 px', {t[2] for t in texts(cpr['svg'])} == {12})
ok('circle pack: table gives name, path, value and share of every item', all(f"{i['name']} {i['value']} GB (" in cpr['table'] for i in CPI) and 'G2/H/d 25 GB (' in cpr['table'] and f"({100 * 25 / 73:.1f}%)" in cpr['table'])
ok('circle pack: circles are ordered largest first within each group', all([r['value'] for d, r in lst] == sorted([r['value'] for d, r in lst], reverse=True) for lst in byparent.values()))
hc = D.circle_pack([{'name': 'a', 'value': 1e308}, {'name': 'b', 'value': 10 ** 400}, {'name': 'c', 'value': 5e-324}])['circle_pack']
ok('circle pack boundary: huge, 10**400 and subnormal values: clamped / minimum-size circle with notes, no nan/inf', any('2 values were above' in x for x in hc['notes']) and any('minimum size' in x for x in hc['notes']) and not re.search(r'nan|inf', hc['svg'] + hc['alt'], re.I) and wf(hc))
ok('circle pack boundary: dict / list / 10**400 names, paths, title, unit and version do not crash', wf(D.circle_pack([{'name': {'a': 1}, 'value': 1, 'path': [['x']]}, {'name': ['n'], 'value': 2, 'path': [10 ** 400, 'y']}, {'name': 10 ** 400, 'value': 3}], unit=10 ** 400, title=[1], version=10 ** 400)['circle_pack']))
ok('circle pack boundary: 60 tiny-spread items pack without overlap and quickly', (lambda t0, q: time.time() - t0 < 4 and wf(q))(time.time(), D.circle_pack([{'path': [str(i % 5)], 'name': f'n{i}', 'value': 1.5 ** (i % 20)} for i in range(60)])['circle_pack']))
ok('circle pack negative control: leaf radius x0.6 breaks the radius law', not all(abs(d[2] * 0.6 / g0 - 20 * math.sqrt(r['value'] / vmaxc)) < 0.02 * d[2] / g0 + 0.05 for d, r in leafd))
# ---------- every macro: A2UI messages validate; Basic components only; negative controls
demos = {'sunburst': dict(items=IT, unit='u'), 'chord_diagram': dict(groups=['A', 'B', 'C', 'D'], matrix=M), 'arc_diagram': dict(nodes=ND, links=LK), 'heatmap_calendar': dict(data=data, months=2), 'circle_pack': dict(items=IT)}
for name, params in demos.items():
    create, updates, results = D.card(name, 'T', params)
    ok(f'{name}: createSurface validates', not list(A2R.iter_errors(create))); ok(f'{name}: every update validates', all(not list(A2R.iter_errors(u)) for u in updates.values()))
    ok(f'{name}: only Basic components', {c['component'] for c in create['createSurface']['components']} <= {'Card', 'Column', 'Row', 'Text', 'Image', 'Button'})
    ids = {c['id'] for c in create['createSurface']['components']}; refs = set()
    for c in create['createSurface']['components']: refs |= set(c.get('children', [])) | ({c['child']} if 'child' in c else set())
    ok(f'{name}: child references resolve', refs <= ids); ok(f'{name}: image description bound', all('description' in c for c in create['createSurface']['components'] if c['component'] == 'Image'))
    ok(f'{name}: status is a polite live region', next(c for c in create['createSurface']['components'] if c['id'] == 'status')['accessibility'] == {'live': 'polite'})
    ok(f'{name}: payload under 200 KB', len(json.dumps(create)) < 200_000)
    b1 = copy.deepcopy(create); b1['version'] = 'v1.0'; ok(f'{name}: negative: bad version rejected', bool(list(A2R.iter_errors(b1))))
    b2 = copy.deepcopy(create); b2['createSurface']['components'][2]['component'] = 'Chart'; ok(f'{name}: negative: unknown component rejected', bool(list(A2R.iter_errors(b2))))
print(f'd3 pack tests: {n} checks, {bad} failed'); sys.exit(1 if bad else 0)
