"""Stats group of the d3 macro pack (histogram, box_plot, ridgeline, beeswarm): independent arithmetic (bisect-free reference binning, statistics.quantiles, geometric overlap checks), tolerant-reader
rules, determinism, and every emitted message validated against the upstream A2UI 1.0 schemas with negative controls. Run: A2UI_UPSTREAM=<upstream checkout> python3 -B tests/test_stats.py"""
import copy, glob, json, math, random, re, statistics, sys
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
from d3pack import common as C
import math
from d3pack.histogram import histogram, d3_ticks, nice_edges, bin_counts
from d3pack.box_plot import box_plot, quantile
from d3pack.ridgeline import ridgeline
from d3pack.beeswarm import beeswarm, place
from d3pack.registry_stats import PACK_STATS
from d3pack.demos_stats import DEMOS
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
def outl(svg): return [(int(i), float(x), float(y)) for i, blk in re.findall(r'<g fill="none" stroke="[^"]+" stroke-width="2" data-lane="(\d+)">(.*?)</g>', svg, re.S) for x, y in re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)"', blk)]
ALLOWED = {c.lower() for c in C.PAL} | {C.FACE, C.INK, C.MUTED, '#c9cde0', '#e3e6f2'} | {C.blend(p, t).lower() for p in C.PAL for t in (.25, .45)}
def palette_ok(s): return {m.lower() for m in re.findall(r'#[0-9a-fA-F]{6}', s)} <= ALLOWED
def fonts_ok(s): return all(int(m) >= 14 for m in re.findall(r'font-size="(\d+)"', s))
def circles(s):
    out = []
    for lane, blk in re.findall(r'<g [^>]*data-lane="(\d+)">(.*?)</g>', s, re.S): out += [(float(a), float(b), float(c), int(lane)) for a, b, c in re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([\d.]+)"', blk)]
    return out
def ref_counts(vals, edges):
    c = [0] * (len(edges) - 1)
    for v in vals:
        for i in range(len(c)):
            if edges[i] <= v < edges[i + 1] or (i == len(c) - 1 and v == edges[-1]): c[i] += 1; break
    return c
def mant_ok(step): m = step / 10 ** math.floor(math.log10(step) + 1e-9); return any(abs(m - k) < 1e-6 for k in (1, 2, 5, 10))
def generic(tag, r, name_markup=None):
    ok(f'{tag}: well-formed', wf(r)); ok(f'{tag}: svg under 60 KB', len(r['svg']) < 60_000); ok(f'{tag}: only palette colours', palette_ok(r['svg'])); ok(f'{tag}: text at least 14 px', fonts_ok(r['svg']))
rng = random.Random(11)
# =============================== histogram (atom contract)
def H(values=None, **kw): return histogram(values=values, **kw)
ok('histogram: d3.ticks(0,1,10) is 0, 0.1 ... 1', d3_ticks(0, 1, 10) == [round(i / 10, 12) for i in range(11)]); ok('histogram: d3.ticks(0,100,5) is 0,20..100', d3_ticks(0, 100, 5) == [0, 20, 40, 60, 80, 100])
ok('histogram: d3.ticks(1,9,5) is 2,4,6,8', d3_ticks(1, 9, 5) == [2, 4, 6, 8]); ok('histogram: nice_edges widen the extent to whole steps', nice_edges(3.2, 97.5, 5) == [0, 20, 40, 60, 80, 100])
bad_ref = []
for t in range(40):
    k = rng.randint(5, 300); vals = [rng.choice([rng.randint(-50, 200), round(rng.gauss(30, 40), 2)]) for _ in range(k)]
    r = H(vals)['bars']; e = r['edges']; c = r['counts'][0]
    if c != ref_counts(vals, e) or sum(c) != k or e[0] > min(vals) or e[-1] < max(vals) or (len(e) > 2 and not mant_ok(round(e[1] - e[0], 9))) or any(abs((e[i + 1] - e[i]) - (e[1] - e[0])) > 1e-9 for i in range(len(e) - 1)): bad_ref.append((t, k))
ok(f'histogram: 40 random samples: counts match reference, sum to n, equal nice widths, edges cover data {bad_ref[:2]}', not bad_ref)
V5 = [0, 10, 10, 20, 20, 30]; r = H(V5)['bars']; e = r['edges']; ok('histogram: a value on an interior edge goes to the upper bin', r['counts'][0][e.index(10)] >= 2 and ref_counts(V5, e) == r['counts'][0])
ok('histogram: the maximum falls in the last bin (closed)', H([0, 2, 5, 8, 10])['bars']['counts'][0][-1] >= 1 and sum(H([0, 2, 5, 8, 10])['bars']['counts'][0]) == 5)
ok('histogram: bins=5 on 0..100 gives width 20', H([0, 100, 50, 30, 70], bins=5)['bars']['edges'] == [0, 20, 40, 60, 80, 100]); ok('histogram: bins 500 clamped to 40 and 1 clamped to 3, with notes', any('clamped to 40' in x for x in H(list(range(100)), bins=500)['bars']['notes']) and any('clamped to 3' in x for x in H(list(range(100)), bins=1)['bars']['notes']))
ok('histogram: bins asked -> edges, hand arithmetic on 0..99 (span 99): 3 -> width 50, 10 -> width 10, 40 -> width 2; default Sturges for n=100 (8) -> width 10',
   H(list(range(100)), bins=3)['bars']['edges'] == [0, 50, 100] and H(list(range(100)), bins=10)['bars']['edges'] == [float(i) for i in range(0, 101, 10)] and H(list(range(100)), bins=40)['bars']['edges'] == [float(i) for i in range(0, 101, 2)] and H(list(range(100)))['bars']['edges'] == [float(i) for i in range(0, 101, 10)])
ok('histogram: Sturges for n=100 is ceil(log2 100)+1 = 8 bins asked, giving width 10 on 0..99 (7 would give 20)', H(list(range(100)))['bars']['edges'][1] == 10 and H(list(range(100)), bins=7)['bars']['edges'][1] == 20)
dn = H([1, 2, float('nan'), float('inf'), True, 'x', None, 3, 4, 5, 2e12, -3e12]); ok('histogram: non-finite, bool, text and above-1e12 entries skipped and counted', sum(dn['bars']['counts'][0]) == 5 and any('7 values were left out' in x for x in dn['bars']['notes']))
ok('histogram: only the first 2000 entries are read, and a note says so', sum(H(list(range(2500)))['bars']['counts'][0]) == 2000 and any('500 entries beyond the 2,000th' in x for x in H(list(range(2500)))['bars']['notes']))
for bad_in in ([], [1, 2, 3, 4], ['a'] * 9, None, 'text'):
    rr = H(bad_in)['bars']; ok(f'histogram: fewer than 5 usable numbers ({str(bad_in)[:18]}) -> a note replaces the chart', rr.get('note_only') and 'Fewer than 5' in rr['table'] and wf(rr))
ok('histogram: identical values make one bin holding all', H([4, 4, 4, 4, 4])['bars']['counts'] == [[5]])
ok('histogram: x_label and unit form the axis caption and the table edge values', 'Time (min)' in H(list(range(10)), x_label='Time', unit='min')['bars']['svg'] and ' min to ' in H(list(range(10)), unit='min')['bars']['table'])
ok('histogram: x_label cut to 40 and unit to 12', 'x' * 40 in H(list(range(10)), x_label='x' * 60)['bars']['svg'] and 'x' * 41 not in H(list(range(10)), x_label='x' * 60)['bars']['svg'] and 'u' * 13 not in H(list(range(10)), x_label='a', unit='u' * 20)['bars']['svg'] and 'a (' + 'u' * 12 + ')' in H(list(range(10)), x_label='a', unit='u' * 20)['bars']['svg'])
sa, sb = [rng.randint(0, 99) for _ in range(80)], [rng.randint(20, 140) for _ in range(50)]
rs = H(sa)['bars']; hts = {}
for mm in re.finditer(r'<rect x="[\d.]+" y="[\d.]+" width="[\d.]+" height="([\d.]+)" fill="[^"]+"><title>\[([^,]+), ([^\]\)]+)[\]\)]: (\d+)</title>', rs['svg']): hts[(mm.group(2))] = (float(mm.group(1)), int(mm.group(4)))
ok('histogram: bar heights are proportional to counts', len(hts) >= 3 and max(h / c for h, c in hts.values()) - min(h / c for h, c in hts.values()) < .6 and sum(c for _, c in hts.values()) == 80)
tb = [(float(x.replace(',', '')), float(y.replace(',', '')), int(c)) for x, y, c in re.findall(r'([-\d.,]+) to ([-\d.,]+): (\d+)', rs['table'])]
ok('histogram: the table lists every bin as from, to, count, equal to a brute-force count of the input', [(a_, b_) for a_, b_, _ in tb] == list(zip(rs['edges'], rs['edges'][1:])) and [c for _, _, c in tb] == ref_counts(sa, rs['edges']))
ok('histogram: alt text carries the tallest-bin count from the same numbers', f'with {max(rs["counts"][0])}.' in rs['alt'] and '80 values' in rs['alt'])
ok('histogram: unknown layout draws bars with a note', H(sa, layout='pie')['_default'] == 'bars' and any('layout' in x for x in H(sa, layout='pie')['bars']['notes']))
ok('histogram: version 2 drawn as 1 with a note', any('version 1' in x for x in H(sa, version=2)['bars']['notes'])); ok('histogram: deterministic', H(sa)['bars']['svg'] == H(sa)['bars']['svg'])
ok('histogram: options we do not draw are named in the notes', any('norm is not drawn' in x for x in H(sa, norm='percent')['bars']['notes']))
hm = H(sa, title='<t>', x_label='<&>', unit='<u>'); ok('histogram: markup escaped and well-formed', wf(hm['bars']) and '&lt;&amp;&gt;' in hm['bars']['svg'] and '<&>' not in hm['bars']['svg'])
generic('histogram', rs); big = H([rng.random() * 1000 for _ in range(2000)])['bars']; ok('histogram: 2000 values stay a small drawing with every bin in the table', len(big['svg']) < 60_000 and sum(big['counts'][0]) == 2000 and '2,000 values' in big['table'])
# ---- histogram layout 'ridge'
SR = [{'label': 'A', 'values': sa}, {'label': 'B', 'values': sb}, {'label': 'C', 'values': [rng.randint(60, 100) for _ in range(30)]}]
hr = histogram(layout='ridge', series=SR, values=[1, 2, 3, 4, 5]); rr = hr['ridge']; e = rr['edges']
ok('histogram ridge: only the ridge variant, `values` not read', set(hr) == {'ridge', '_default'} and hr['_default'] == 'ridge' and rr['names'] == ['A', 'B', 'C'])
A_ = list(range(100)); B_ = list(range(20, 140)); rp = histogram(layout='ridge', series=[{'label': 'A', 'values': A_}, {'label': 'B', 'values': B_}], bins=4)['ridge']
ok('histogram ridge: shared bins come from BOTH series pooled (0..139, 4 asked -> width 50, edges 0..150) and each series matches a brute-force count', rp['edges'] == [0, 50, 100, 150] and rp['counts'] == [ref_counts(A_, [0, 50, 100, 150]), ref_counts(B_, [0, 50, 100, 150])] and rp['counts'] == [[50, 50, 0], [30, 50, 40]])
allp = sa + sb + SR[2]['values']; ok('histogram ridge: with random series the shared edges cover every series and have one nice width', e[0] <= min(allp) and e[-1] >= max(allp) and mant_ok(round(e[1] - e[0], 9)) and all(rr['counts'][i] == ref_counts(s['values'], e) for i, s in enumerate(SR)))
ok('histogram ridge: each ridge height is its SHARE of its own values (shares sum to 1)', all(abs(sum(sh) - 1) < 1e-9 for sh in rr['shares']) and all(abs(rr['shares'][i][k] - rr['counts'][i][k] / len(SR[i]['values'])) < 1e-12 for i in range(3) for k in range(len(e) - 1)))
ok('histogram ridge: table gives each bin count per series and the drawing has no y-axis tick labels at the left', all(f'{x["label"]} ({len(x["values"])} values)' in rr['table'] for x in SR) and 'text-anchor="end"' in rr['svg'] and rr['svg'].count('text-anchor="end"') == 3)
ok('histogram ridge: series entry with fewer than 5 numbers left out with a note', len(histogram(layout='ridge', series=SR + [{'label': 'short', 'values': [1, 2]}])['ridge']['counts']) == 3 and any('short was left out' in x for x in histogram(layout='ridge', series=SR + [{'label': 'short', 'values': [1, 2]}])['ridge']['notes']))
ok('histogram ridge: series beyond the 8th noted and not drawn', len(histogram(layout='ridge', series=[{'values': list(range(i, i + 6))} for i in range(10)])['ridge']['counts']) == 8 and any('beyond the first 8' in x for x in histogram(layout='ridge', series=[{'values': list(range(i, i + 6))} for i in range(10)])['ridge']['notes']))
ok('histogram ridge: default label is "Series n" by position', histogram(layout='ridge', series=[{'values': list(range(6))}, {'label': 'x', 'values': list(range(6))}, {'values': list(range(6))}])['ridge']['names'] == ['Series 1', 'x', 'Series 3'])
ok('histogram ridge: no usable series -> a note replaces the chart', histogram(layout='ridge', series=[])['ridge'].get('note_only') and histogram(layout='ridge', values=[1, 2, 3, 4, 5, 6])['ridge'].get('note_only'))
ok('histogram ridge: series is ignored in bars layout', histogram(values=sa, series=SR)['_default'] == 'bars' and sum(histogram(values=sa, series=SR)['bars']['counts'][0]) == 80)
ok('histogram ridge: bins=0 is clamped to 3 with a note, and drawn on the 3-bin edges (0..139 -> width 50)', any('clamped to 3' in x for x in histogram(layout='ridge', series=[{'values': A_}, {'values': B_}], bins=0)['ridge']['notes']) and histogram(layout='ridge', series=[{'values': A_}, {'values': B_}], bins=0)['ridge']['edges'] == [0, 50, 100, 150])
ok('histogram ridge: deterministic, well-formed, palette, fonts', histogram(layout='ridge', series=SR)['ridge']['svg'] == histogram(layout='ridge', series=SR)['ridge']['svg'] and wf(rr) and palette_ok(rr['svg']) and fonts_ok(rr['svg']))
# =============================== box_plot (atom contract)
def sq(v): return statistics.quantiles(v, n=4, method='inclusive')
def G(*sets): return [{'label': f'g{i}', 'values': v} for i, v in enumerate(sets)]
bad_q = []
for t in range(60):
    k = rng.randint(5, 120); vals = [round(rng.gauss(10, 8), 2) for _ in range(k)]; st = box_plot(groups=G(vals))['horizontal']['stats'][0]; q = sq(vals)
    if not (abs(st['q1'] - q[0]) < 1e-9 and abs(st['med'] - q[1]) < 1e-9 and abs(st['q3'] - q[2]) < 1e-9 and abs(st['med'] - statistics.median(vals)) < 1e-9): bad_q.append(t)
ok(f'box_plot: quartiles equal statistics.quantiles(inclusive) = R-7 on 60 random samples {bad_q[:3]}', not bad_q)
ok('box_plot: quantile of 1..9 is 3, 5, 7', [quantile(list(range(1, 10)), p) for p in (.25, .5, .75)] == [3, 5, 7]); ok('box_plot: interpolation (1,2,3,4) q1 = 1.75', quantile([1, 2, 3, 4], .25) == 1.75)
O9 = list(range(1, 10)); mq = lambda m, v: box_plot(groups=G(v), quartile_method=m)['horizontal']['stats'][0]
ok('box_plot: exclusive method on 1..9 leaves the middle out of both halves (Q1 2.5, Q3 7.5)', (mq('exclusive', O9)['q1'], mq('exclusive', O9)['q3']) == (2.5, 7.5)); ok('box_plot: inclusive method on 1..9 keeps the middle in both halves (Q1 3, Q3 7)', (mq('inclusive', O9)['q1'], mq('inclusive', O9)['q3']) == (3, 7))
ok('box_plot: even sample 1..10: both halve alike (Q1 3, Q3 8)', all((mq(m, list(range(1, 11)))['q1'], mq(m, list(range(1, 11)))['q3']) == (3, 8) for m in ('exclusive', 'inclusive')))
ok('box_plot: unknown quartile_method falls back to linear with a note', any('quartile_method' in x for x in box_plot(groups=G(O9), quartile_method='zzz')['horizontal']['notes']))
V = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100, -60]; bp = box_plot(groups=G(V)); st = bp['horizontal']['stats'][0]; q1, q3 = sq(V)[0], sq(V)[2]; lf, hf = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
ok('box_plot: outliers are exactly the values beyond the 1.5 x box-length fences', st['out'] == sorted(v for v in V if v < lf or v > hf) and st['out'] == [-60, 100])
ok('box_plot: whiskers are the furthest actual numbers inside the fences', st['wlo'] == min(v for v in V if lf <= v <= hf) and st['whi'] == max(v for v in V if lf <= v <= hf) and st['wlo'] in V and st['whi'] in V)
ok('box_plot: whisker range plus outliers account for every value', sum(1 for v in V if st['wlo'] <= v <= st['whi']) + len(st['out']) == len(V) == st['n'])
ok('box_plot: a group of exactly 5 numbers is accepted, 4 is left out with a note', len(box_plot(groups=G([1, 2, 3, 4, 5], [1, 2, 3, 4]))['horizontal']['stats']) == 1 and any('g1 was left out' in x for x in box_plot(groups=G([1, 2, 3, 4, 5], [1, 2, 3, 4]))['horizontal']['notes']))
ok('box_plot: default label is "Group n" and labels are cut to 30', box_plot(groups=[{'values': O9}, {'label': 'L' * 40, 'values': O9}])['horizontal']['stats'][0]['label'] == 'Group 1' and len(box_plot(groups=[{'label': 'L' * 40, 'values': O9}])['horizontal']['stats'][0]['label']) == 30)
for o in ('horizontal', 'vertical'):
    g2 = box_plot(groups=G([2, 4, 4, 5, 9, 11, 12], [30, 31, 35, 40, 41]), orientation='h' if o == 'horizontal' else 'v')[o]; dlo, dhi = g2['domain']; L_, R_, T_ = (120, 24, 24) if o == 'horizontal' else (64, 24, 24)
    B_ = 46 if o == 'horizontal' else 62; pw, ph = 720 - L_ - R_, 520 - T_ - B_; sc = (lambda v: L_ + (v - dlo) / (dhi - dlo) * pw) if o == 'horizontal' else (lambda v: T_ + ph - (v - dlo) / (dhi - dlo) * ph)
    boxes = {int(i): (float(x), float(y), float(w), float(h)) for x, y, w, h, i in re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" fill="[^"]+" fill-opacity="[^"]+" stroke="[^"]+" stroke-width="2.5" data-box="(\d+)"', g2['svg'])}
    good = True
    for i, s in enumerate(g2['stats']):
        x, y, w, h = boxes[i]; a, b = (x, x + w) if o == 'horizontal' else (y, y + h); lo_, hi_ = sorted((sc(s['q1']), sc(s['q3'])))
        good = good and abs(a - lo_) < .02 and abs(b - hi_) < .02
    ok(f'box_plot: {o} boxes span Q1..Q3 at the axis scale', good and len(boxes) == 2); ok(f'box_plot: {o} domain covers all data and has nice ends', dlo <= 2 and dhi >= 41 and dlo == round(dlo, 9))
ok('box_plot: orientation v makes vertical the default, both variants returned', box_plot(groups=G(O9), orientation='v')['_default'] == 'vertical' and set(box_plot(groups=G(O9))) == {'horizontal', 'vertical', '_default'})
bpd = box_plot(groups=G(V), unit='ms', x_label='Latency')['horizontal']; ok('box_plot: one circle per distinct outlier', len(outl(bpd['svg'])) == 2 and 'outlier 100 ms' in bpd['svg'] and 'outlier -60 ms' in bpd['svg'])
ok('box_plot: table gives n, min, Q1, median, Q3, max with unit, whiskers and outlier count', all(s in bpd['table'] for s in ('n 11', 'min -60 ms', 'Q1 2.5 ms', 'median 5 ms', 'Q3 7.5 ms', 'max 100 ms', 'whiskers 1 to 9 ms', '2 outliers: -60 ms, 100 ms')) and 'Latency (ms)' in bpd['svg'])
ok('box_plot: alt text from the same numbers', '1 groups, 11 values, 2 outliers' in bpd['alt'] and '(2.5 to 7.5 ms' in bpd['alt'])
many = box_plot(groups=[{'label': f'g{i}', 'values': [i, i + 1, i + 5, i + 6, i + 9]} for i in range(15)]); ok('box_plot: groups beyond the 12th noted and not drawn', len(many['horizontal']['stats']) == 12 and any('beyond the first 12' in x for x in many['horizontal']['notes']))
bn = box_plot(groups=G(O9) + [{'values': [float('nan')] * 6}, 'junk']); ok('box_plot: non-group entries and short groups left out with notes', len(bn['horizontal']['stats']) == 1 and any('1 groups were left out' in x for x in bn['horizontal']['notes']) and any('Group 2 was left out' in x for x in bn['horizontal']['notes']))
for bad_in in (None, [], [{'values': [1, 2]}], 'x'): ok(f'box_plot: nothing usable ({str(bad_in)[:12]}) -> a note replaces the chart', box_plot(groups=bad_in)['horizontal'].get('note_only') is True)
ok('box_plot: unknown orientation noted and drawn h', box_plot(groups=G(O9), orientation='diag')['_default'] == 'horizontal' and any('orientation' in x for x in box_plot(groups=G(O9), orientation='diag')['horizontal']['notes']))
ok('box_plot: deterministic', box_plot(groups=G(V))['vertical']['svg'] == box_plot(groups=G(V))['vertical']['svg'])
hb = box_plot(groups=[{'label': '<i>&"', 'values': O9}], unit='<u>'); ok('box_plot: markup escaped', '&lt;i&gt;' in hb['horizontal']['svg'] and '<i>' not in hb['horizontal']['svg'] and wf(hb['vertical']))
ok('box_plot: version 2 noted', any('version 1' in x for x in box_plot(groups=G(O9), version=2)['horizontal']['notes']))
sm_ = box_plot(groups=G(O9), show_mean=True)['horizontal']; ok('box_plot: show_mean draws one diamond at the mean and adds Mean to the table', sm_['svg'].count('data-mean') == 1 and 'Mean 5' in sm_['table'] and 'Mean' not in box_plot(groups=G(O9))['horizontal']['table'])
ok('box_plot: unsupported options named', any('notches is not drawn' in x for x in box_plot(groups=G(O9), notches=True)['horizontal']['notes']))
for o in ('horizontal', 'vertical'): generic('box_plot ' + o, box_plot(groups=G(V), unit='u')[o])
bigp = box_plot(groups=[{'label': 'big', 'values': [rng.gauss(0, 1) for _ in range(5000)]}])['horizontal']; ok('box_plot: only the first 2000 numbers are read, summarised by five numbers and n', 'n 2000' in bigp['table'] and len(bigp['svg']) < 60_000)
# ---- show_points
P1 = [round(rng.gauss(50, 9), 1) for _ in range(40)]; P2 = [round(rng.gauss(70, 5), 1) for _ in range(25)]
sp = box_plot(groups=G(P1, P2), show_points=True)['horizontal']; dl = re.findall(r'<g fill="[^"]+" fill-opacity="\.5" data-dots="(\d)">(.*?)</g>', sp['svg'], re.S)
dots_ = {int(i): [(float(a), float(b)) for a, b in re.findall(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="3.5"', blk)] for i, blk in dl}
dlo, dhi = sp['domain']; scx = lambda v: 120 + (v - dlo) / (dhi - dlo) * 576
ok('box_plot points: every usable number is a dot at exactly its place on the axis', all(sorted(round(x, 2) for x, _ in dots_[i]) == sorted(round(scx(v), 2) for v in vs) for i, vs in enumerate((P1, P2))))
ok('box_plot points: no two dots touch (geometric check within each row)', all(math.hypot(a[0] - b[0], a[1] - b[1]) >= 7 - 1e-6 for i in dots_ for k, a in enumerate(dots_[i]) for b in dots_[i][k + 1:]))
ok('box_plot points: dots are drawn BEHIND the box (earlier in the svg)', sp['svg'].index('data-dots="0"') < sp['svg'].index('data-box="0"'))
ok('box_plot points: only True switches it on', 'data-dots' not in box_plot(groups=G(P1, P2), show_points='yes')['horizontal']['svg'] and 'data-dots' not in box_plot(groups=G(P1, P2))['horizontal']['svg'] and 'data-dots' not in box_plot(groups=G(P1, P2), show_points=1)['horizontal']['svg'])
ok('box_plot points: not drawn with the vertical orientation, show_mean or exclusive quartiles, and a note says so', all('data-dots' not in v and any('show_points' in x for x in box_plot(groups=G(P1, P2), show_points=True, **kw)['horizontal']['notes']) for kw in (dict(orientation='v'), dict(show_mean=True), dict(quartile_method='exclusive')) for v in [box_plot(groups=G(P1, P2), show_points=True, **kw)['horizontal']['svg']]))
big3 = [[round(rng.gauss(50 + 10 * g, 8), 1) for _ in range(400)] for g in range(3)]; b3 = box_plot(groups=G(*big3), show_points=True)['horizontal']; d3_ = b3['dots']
ok('box_plot points: at most 300 dots in all, shared in proportion (equal groups -> 100 each), evenly spaced through the sorted numbers', sum(len(d) for d in d3_) == 300 and [len(d) for d in d3_] == [100] * 3 and d3_[0][0] == min(big3[0]) and d3_[0][-1] == max(big3[0]) and all(d == sorted(d) for d in d3_))
ok('box_plot points: the cap is stated and the table still counts all', any('300 per chart' in x for x in b3['notes']) and 'n 400' in b3['table'])
uneven = box_plot(groups=G(list(range(900)), list(range(100))), show_points=True)['horizontal']['dots']; ok('box_plot points: proportional shares for unequal groups (270 + 30)', [len(d) for d in uneven] == [270, 30])
rem = box_plot(groups=G(list(range(700)), list(range(650)), list(range(650))), show_points=True)['horizontal']['dots']; ok('box_plot points: largest-remainder rounding keeps the total at exactly 300 (700/650/650)', sum(len(d) for d in rem) == 300 and len(rem[0]) == 105 and sorted(len(d) for d in rem[1:]) == [97, 98])
W2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 20]; ok('box_plot: an upper-side value between 1.5 and 3 box lengths out is an outlier (fence not widened)', box_plot(groups=G(W2))['horizontal']['stats'][0]['out'] == [20] and box_plot(groups=G([-v for v in W2]))['horizontal']['stats'][0]['out'] == [-20])
ok('box_plot points: crowded rows keep every dot in place or noted', len(re.findall(r'r="3.5"', box_plot(groups=G([5.0] * 100 + [6.0] * 100), show_points=True)['horizontal']['svg'])) == 200 and any('stay on the edge' in x for x in box_plot(groups=G([5.0] * 100 + [6.0] * 100), show_points=True)['horizontal']['notes']))
many_o = box_plot(groups=G([50.0 + i % 3 for i in range(400)] + [1000.0 + i for i in range(120)]))['horizontal']; ok('box_plot: past 100 distinct outliers only 100 are drawn (the furthest), a note says so and the table counts all', len(outl(many_o['svg'])) == 100 and any('100 of 120 distinct outliers' in x for x in many_o['notes']) and '120 outliers' in many_o['table'] and 'outlier 1,119' in many_o['svg'] and 'outlier 1,000' not in many_o['svg'] and any('100 of 120 distinct outliers' in x for x in box_plot(groups=G([50.0 + i % 3 for i in range(400)] + [1000.0 + i for i in range(120)]))['vertical']['notes']))
# =============================== ridgeline (wrapper over histogram ridge)
G3 = [{'name': 'North', 'values': [rng.gauss(50, 8) for _ in range(90)]}, {'name': 'Mid', 'values': [rng.gauss(65, 12) for _ in range(60)]}, {'name': 'South', 'values': [rng.gauss(30, 6) for _ in range(40)]}]
rl = ridgeline(G3, unit='u')['ridgeline']; e = rl['edges']
ok('ridgeline: every group matches the reference counts on the shared edges', all(rl['counts'][i] == ref_counts(g['values'], e) for i, g in enumerate(G3)) and all(sum(rl['counts'][i]) == len(g['values']) for i, g in enumerate(G3)))
ok('ridgeline: edges are equal-width nice steps covering all data', e[0] <= min(min(g['values']) for g in G3) and e[-1] >= max(max(g['values']) for g in G3) and mant_ok(round(e[1] - e[0], 9)))
paths = [[tuple(map(float, p.split(','))) for p in re.findall(r'[-\d.]+,[-\d.]+', d)] for d in re.findall(r'<path d="([^"]+)"', rl['svg'])]
ok('ridgeline: one filled area per group in input order', len(paths) == 3 and [int(i) for i in re.findall(r'data-group="(\d+)"', rl['svg'])] == [0, 1, 2])
ok('ridgeline: areas never dip below their baseline (non-negative)', all(all(y <= rl['bases'][i] + .006 for _, y in p) for i, p in enumerate(paths)))
ok('ridgeline: baselines strictly increase down the page with equal spacing', all(rl['bases'][i] < rl['bases'][i + 1] for i in range(2)) and abs((rl['bases'][1] - rl['bases'][0]) - (rl['bases'][2] - rl['bases'][1])) < 1e-9)
ok('ridgeline: each area starts and ends on its baseline at the outer edges', all(abs(p[0][1] - rl['bases'][i]) < .01 and abs(p[-1][1] - rl['bases'][i]) < .01 and abs(p[0][0] - 120) < .01 and abs(p[-1][0] - 696) < .01 for i, p in enumerate(paths)))
hh = [[rl['bases'][i] - y for _, y in p[1:-1]] for i, p in enumerate(paths)]
ok('ridgeline: heights are share-of-series x one shared scale', all(abs(hh[i][k] - rl['counts'][i][k] / len(G3[i]['values']) * rl['scale']) < .01 for i in range(3) for k in range(len(e) - 1)))
sp = rl['bases'][1] - rl['bases'][0]; ok('ridgeline: the tallest ridge rises overlap x lane spacing (1.6)', abs(max(max(h) for h in hh) - 1.6 * sp) < .02)
ok('ridgeline: points sit at bin midpoints', all(abs(p[1 + k][0] - (120 + ((e[k] + e[k + 1]) / 2 - e[0]) / (e[-1] - e[0]) * 576)) < .01 for p in paths for k in range(len(e) - 1)))
r3 = ridgeline(G3, overlap=3)['ridgeline']; sp3 = r3['bases'][1] - r3['bases'][0]; ok('ridgeline: overlap=3 lets the tallest ridge rise 3 lane spacings', abs(max(max(c) for c in r3['shares']) * r3['scale'] - 3 * sp3) < 1e-9 and sp3 < sp)
ok('ridgeline: overlap clamped with a note', any('overlap 9' in x for x in ridgeline(G3, overlap=9)['ridgeline']['notes']))
ok('ridgeline: more than 8 groups cut', any('beyond the first 8' in x for x in ridgeline([{'name': str(i), 'values': list(range(i, i + 6))} for i in range(10)])['ridgeline']['notes']))
ok('ridgeline: short or bad groups dropped', len(ridgeline(G3 + [{'name': 'e', 'values': [1]}, 'x'])['ridgeline']['counts']) == 3 and any('1 groups' in x for x in ridgeline(G3 + ['x'])['ridgeline']['notes']))
ok('ridgeline: a single group via values works', len(ridgeline(values=[1, 2, 2, 3, 3, 3, 9])['ridgeline']['counts']) == 1); ok('ridgeline: nothing usable -> a note replaces the chart', ridgeline([])['ridgeline'].get('note_only') and ridgeline([{'name': 'a', 'values': [float('nan')] * 6}])['ridgeline'].get('note_only'))
ok('ridgeline: same drawing as histogram(layout=ridge) for the same series', ridgeline([{'label': g['name'], 'values': g['values']} for g in G3])['ridgeline']['edges'] == histogram(layout='ridge', series=[{'label': g['name'], 'values': g['values']} for g in G3])['ridge']['edges'])
ok('ridgeline: table lists every group count per bin', all(f'{g["name"]} ({len(g["values"])} values)' in rl['table'] for g in G3) and rl['table'].count(' to ') >= 3 * (len(e) - 1))
ok('ridgeline: alt text from the same numbers', '3 series, 190 values' in rl['alt'] and any(f'({c} of its' in rl['alt'] for c in [rl['counts'][i][max(range(len(rl['shares'][i])), key=lambda k: rl['shares'][i][k])] for i in range(3)])); ok('ridgeline: deterministic', ridgeline(G3)['ridgeline']['svg'] == ridgeline(G3)['ridgeline']['svg'])
rh = ridgeline([{'name': '<b>"&', 'values': list(range(6))}], unit='&'); ok('ridgeline: markup escaped', '&lt;b&gt;' in rh['ridgeline']['svg'] and wf(rh['ridgeline'])); generic('ridgeline', rl)
ok('ridgeline: version 2 noted', any('version 1' in x for x in ridgeline(G3, version=2)['ridgeline']['notes']))
# =============================== beeswarm
def overlaps(r):
    k = 0
    for i in range(len(r['radii'])):
        m = [c for c in circles(r['svg']) if c[3] == i]
        k += sum(1 for a, p in enumerate(m) for q in m[a + 1:] if math.hypot(p[0] - q[0], p[1] - q[1]) < 2 * r['radii'][i] - 1e-6)
    return k
def swarm_check(r, groups_vals):
    cs = circles(r['svg']); dlo, dhi = r['domain']; lane = r['lane']; T_ = 24; res_ = {'overlap': 0, 'x': 0, 'lane': 0}
    for i, vals in enumerate(groups_vals):
        mine = [c for c in cs if c[3] == i]; rad = r['radii'][i]; cen = T_ + lane * (i + .5)
        for a, (x1, y1, r1, _) in enumerate(mine):
            if abs(abs(y1 - cen)) > lane / 2: res_['lane'] += 1
            for (x2, y2, r2, _) in mine[a + 1:]:
                if math.hypot(x1 - x2, y1 - y2) < 2 * rad - 1e-6: res_['overlap'] += 1
        xs_ = sorted(c[0] for c in mine); want = sorted(120 + (v - dlo) / (dhi - dlo) * 576 for v in vals)
        if len(xs_) != len(want) or any(abs(a - b) > .011 for a, b in zip(xs_, want)): res_['x'] += 1
    return res_
vs = [[round(rng.gauss(50, 10), 1) for _ in range(50)], [round(rng.gauss(60, 5), 1) for _ in range(40)], [round(rng.uniform(0, 100), 1) for _ in range(30)]]
bw = beeswarm([{'name': 'a', 'values': vs[0]}, {'name': 'b', 'values': vs[1]}, {'name': 'c', 'values': vs[2]}], unit='u')['swarm']; sc_ = swarm_check(bw, vs)
ok('beeswarm: no two circles in a lane overlap (geometric check)', sc_['overlap'] == 0); ok('beeswarm: every circle sits at the x of its value (to 0.01 px)', sc_['x'] == 0); ok('beeswarm: every circle stays inside its lane', sc_['lane'] == 0)
ok('beeswarm: one circle per value', len(circles(bw['svg'])) == 120)
def drawn_x_ok(r, vals_by_lane):
    """Every drawn circle's x is the exact position of one distinct input value of its lane (multiset containment), whatever was or was not drawn."""
    dlo, dhi = r['domain']; cs = circles(r['svg'])
    for i, vals in enumerate(vals_by_lane):
        want = [120 + (v - dlo) / (dhi - dlo) * 576 for v in vals]
        for (x, _, _, ln) in [c for c in cs if c[3] == i]:
            j = next((k for k, w in enumerate(want) if abs(w - x) < .011), None)
            if j is None: return False
            want.pop(j)
    return True
clean_trials = True
for t in range(15):
    v = [round(rng.choice([rng.gauss(0, 1), 0, 0.5]), 1) for _ in range(rng.randint(1, 80))]; rr = beeswarm([{'name': 'g', 'values': v}])['swarm']
    if overlaps(rr) or not drawn_x_ok(rr, [v]): clean_trials = False
ok('beeswarm: 15 random samples with many ties: no overlap, every circle at the exact x of one input value', clean_trials)
ys = place([100.0, 100.0], 6, 50); ok('beeswarm: two points at one x are separated by at least 2r + gap', abs(ys[0] - ys[1]) >= 13 - 1e-9 and ys[0] == 0.0)
ok('beeswarm: a lone point sits on the lane centre', place([55.5], 6, 50) == {0: 0.0}); ok('beeswarm: far-apart points all stay on the centre line', set(place([0, 50, 100, 150], 6, 50).values()) == {0.0})
uv = [[round(i * 1.7 + (g * 0.3), 1) for i in range(35)] for g in range(2)]; sh = [list(v) for v in uv]; [rng.shuffle(q) for q in sh]
key = lambda r_: sorted((c[0], round(c[1], 2), c[3]) for c in circles(r_['svg']))
ok('beeswarm: placement does not depend on the input order of distinct values', key(beeswarm([{'name': 'a', 'values': uv[0]}, {'name': 'b', 'values': uv[1]}])['swarm']) == key(beeswarm([{'name': 'a', 'values': sh[0]}, {'name': 'b', 'values': sh[1]}])['swarm']))
dist = [[1.1 * i for i in range(30)]]; ok('beeswarm: deterministic', beeswarm([{'name': 'g', 'values': dist[0]}])['swarm']['svg'] == beeswarm([{'name': 'g', 'values': dist[0]}])['swarm']['svg'])
tie = beeswarm([{'name': 'g', 'values': [5.0] * 20}])['swarm']; tc = circles(tie['svg']); lane_c = 24 + tie['lane'] / 2
ok('beeswarm: 20 identical values: all drawn at r 6, a column 0, +13, -13, +26 ... (hand arithmetic: 2r + 1 gap = 13)', len(tc) == 20 and tie['radii'] == [6.0] and sorted(round(c[1] - lane_c) for c in tc) == [13 * k for k in range(-9, 11)] and not tie['notes'])
crowd = beeswarm([{'name': 'g', 'values': [10.0] * 200 + [11.0] * 100}])['swarm']; ok('beeswarm: an overcrowded lane shrinks circles or reports unplaced points, never overlaps', overlaps(crowd) == 0 and bool(crowd['notes']) and (crowd['radii'][0] < 6))
nfit = sum(int(m_.group(1)) for x in crowd['notes'] for m_ in [re.match(r'g: (\d+) points did not fit', x)] if m_)
ok('beeswarm: the count of points that did not fit is stated and drawn + stated = 300', nfit > 0 and len(circles(crowd['svg'])) == 300 - nfit and crowd['summary'].count(f'{nfit} points could not be placed') == 1)
lim = beeswarm([{'name': 'g', 'values': [float(i) for i in range(450)]}])['swarm']; ok('beeswarm: 400-per-group limit applied and stated', any('50 of 450 points were not drawn' in x for x in lim['notes']) and len(circles(lim['svg'])) <= 400 and 'n 450' in lim['table'])
ok('beeswarm: 800-point overall limit stated', any('not drawn' in x for x in beeswarm([{'name': str(i), 'values': [float(j) for j in range(300)]} for i in range(4)])['swarm']['notes']))
ok('beeswarm: table gives n/min/median/max and lists small groups in full', all(s in bw['table'] for s in ('a: n 50', 'b: n 40', 'c: n 30')) and 'values 1, 2, 3' in beeswarm(values=[3, 1, 2])['swarm']['table'] and f'median 2' in beeswarm(values=[3, 1, 2])['swarm']['table'])
ok('beeswarm: even-count median is the mean of the middle two', 'median 2.5' in beeswarm(values=[1, 2, 3, 4])['swarm']['table'])
ok('beeswarm: alt text from the same numbers', '3 groups, 120 values' in bw['alt'] and C.fmt(min(min(v) for v in vs)) in bw['alt'])
ok('beeswarm: unusable values and groups dropped and counted', any('2 values were left out' in x for x in beeswarm([{'name': 'a', 'values': [1, 2, None, 'x']}, 'junk'])['swarm']['notes']) and any('1 groups' in x for x in beeswarm([{'name': 'a', 'values': [1, 2]}, 'junk'])['swarm']['notes']))
ok('beeswarm: nothing usable refused', raises(lambda: beeswarm([])) and raises(lambda: beeswarm([{'name': 'a', 'values': [True]}])) and raises(lambda: beeswarm()))
bh = beeswarm([{'name': '<s>&"', 'values': [1, 2]}]); ok('beeswarm: markup escaped', '&lt;s&gt;' in bh['swarm']['svg'] and wf(bh['swarm'])); generic('beeswarm', bw); ok('beeswarm: version 2 noted', any('version 1' in x for x in beeswarm(values=[1, 2], version=2)['swarm']['notes']))
ok('beeswarm: the drawing is sizeable but under 60 KB at 400 points', len(lim['svg']) < 60_000)
# =============================== inverse-read oracles: parse the DRAWING back into data and compare with the input (independent of the code's own numbers)
import time, d3pack as D
TXT = re.compile(r'<text x="([-\d.]+)" y="([-\d.]+)" font-size="(\d+)" font-weight="\d+" fill="(#\w+)" text-anchor="(\w+)" font-family="sans-serif" [^>]*>([^<]*)</text>')
def texts(svg): return [(float(x), float(y), fill, anchor, t) for x, y, _, fill, anchor, t in TXT.findall(svg)]
def lin(p0, v0, p1, v1): return lambda p: v0 + (p - p0) * (v1 - v0) / (p1 - p0)
def num(t): return float(t.replace(',', ''))
def hist_readback(svg):
    tx = texts(svg); xt = sorted((x, num(t)) for x, y, f, a, t in tx if f == C.MUTED and a == 'middle'); yt = sorted((y - 5, num(t)) for x, y, f, a, t in tx if f == C.MUTED and a == 'end')
    X = lin(*xt[0], *xt[-1]); Y = lin(*yt[0], *yt[-1]); bars = []
    for x, y, w, h in re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" fill="#4b4acf">', svg):
        x, y, w, h = map(float, (x, y, w, h)); bars.append((X(x - 1), X(x + w + 1), Y(y) - Y(y + h), Y(y + h)))
    return bars
def ref_bar_counts(vals, a, b): return sum(1 for v in vals if a - 1e-9 <= v < b - 1e-9 or (abs(b - max(vals)) < 1e-9 and abs(v - b) < 1e-9))
for nm, vv in (('skewed', [round(rng.paretovariate(2) * 10, 1) for _ in range(150)]), ('integers with the max on an edge', list(range(0, 101, 5)) * 2 + [100] * 3), ('negative and positive', [round(rng.gauss(0, 30), 1) for _ in range(90)])):
    rr_ = H(vv)['bars']; bars = hist_readback(rr_['svg']); nonempty = [c for c in rr_['counts'][0] if c]
    ok(f'histogram readback ({nm}): every bar, read from pixels, spans a bin and has the count a brute-force tally of the input gives', len(bars) == len(nonempty) and all(abs(c - ref_bar_counts(vv, a, b)) < .02 and c > .5 for a, b, c, _ in bars) and sum(round(c) for _, _, c, _ in bars) == len(vv))
    ok(f'histogram readback ({nm}): the bars sit on the zero line of the y axis', all(abs(z) < 1e-6 for *_, z in bars))
# ridge readback
RS = [{'label': 'A', 'values': [rng.gauss(40, 10) for _ in range(60)]}, {'label': 'B', 'values': [rng.gauss(70, 15) for _ in range(120)]}]
rr_ = histogram(layout='ridge', series=RS)['ridge']; svg_ = rr_['svg']; tx = texts(svg_); xt = sorted((x, num(t)) for x, y, f, a, t in tx if f == C.MUTED and a == 'middle'); X = lin(*xt[0], *xt[-1])
pp = [[tuple(map(float, q.split(','))) for q in re.findall(r'[-\d.]+,[-\d.]+', d)] for d in re.findall(r'<path d="([^"]+)"', svg_)]; ee = rr_['edges']
shares = [[c / len(s['values']) for c in ref_counts(s['values'], ee)] for s in RS]; spacing = pp[1][0][1] - pp[0][0][1]; smax = max(max(x) for x in shares)
ok('ridge readback: each point sits at its bin midpoint (x read through the axis ticks) and its height is the brute-force share of that bin of the series, relative to the tallest ridge (= 1.6 lane spacings)',
   all(abs(X(p[1 + k][0]) - (ee[k] + ee[k + 1]) / 2) < .05 * (ee[1] - ee[0]) and abs((pp[i][0][1] - p[1 + k][1]) / (1.6 * spacing) * smax - shares[i][k]) < .002 for i, p in enumerate(pp) for k in range(len(ee) - 1)))
# box readback
def box_readback(svg, orient):
    tx = texts(svg)
    if orient == 'horizontal': t = sorted((x, num(tt)) for x, y, f, a, tt in tx if f == C.MUTED and a == 'middle')
    else: t = sorted(((y - 5), num(tt)) for x, y, f, a, tt in tx if f == C.MUTED and a == 'end')
    V = lin(*t[0], *t[-1]); out = []
    for blk in re.findall(r'<g>(.*?)</g>', svg, re.S):
        ln = [tuple(map(float, m)) for m in re.findall(r'<line x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)" stroke="#1f2150" stroke-width="2"/>', blk)]
        rect = [float(v) for v in re.search(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([-\d.]+)" height="([-\d.]+)"', blk).groups()]
        med = [float(v) for v in re.search(r'<line x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)" stroke="#1f2150" stroke-width="3.5"/>', blk).groups()]
        k = 0 if orient == 'horizontal' else 1; w, wk = (rect[2], 0) if orient == 'horizontal' else (rect[3], 1)
        wl = sorted((V(ln[0][k]), V(ln[0][k + 2]))); caps = sorted(V(c[k]) for c in ln[1:])
        box = sorted((V(rect[k]), V(rect[k] + w))); out.append(dict(wlo=wl[0], whi=wl[1], caps=caps, q1=box[0], q3=box[1], med=V(med[k])))
    return out, abs(t[-1][1] - t[0][1]) / abs(t[-1][0] - t[0][0])
def ref_tukey(vals, k=1.5):
    q = statistics.quantiles(vals, n=4, method='inclusive'); iqr = q[2] - q[0]; inside = [v for v in vals if q[0] - k * iqr <= v <= q[2] + k * iqr]
    return dict(q1=q[0], med=q[1], q3=q[2], wlo=min(inside), whi=max(inside), out=sorted(v for v in vals if v not in inside))
BS = [[round(rng.gauss(20, 5), 1) for _ in range(40)] + [75.0, 80.5], [1, 2, 3, 4, 5, 6, 7, 8, 9, 15], [round(rng.uniform(0, 100), 1) for _ in range(30)]]
band_q = sq(BS[1]); band = (BS[1][-1] - band_q[2]) / (band_q[2] - band_q[0])
ok(f'box readback test data: the 15 lies between 1.5 and 2.0 box lengths above Q3 ({band:.2f}), so a 2.0 fence would hide the outlier', 1.5 < band < 2.0)
for o in ('horizontal', 'vertical'):
    rbx = box_plot(groups=G(*BS), orientation='h' if o == 'horizontal' else 'v')[o]; got, perpx = box_readback(rbx['svg'], o); tol = .06 * perpx
    for i, vv in enumerate(BS):
        e_ = ref_tukey(vv); g_ = got[i]
        ok(f'box readback {o} group {i}: box = Q1..Q3 and median line read from pixels equal statistics.quantiles', abs(g_['q1'] - e_['q1']) < tol and abs(g_['q3'] - e_['q3']) < tol and abs(g_['med'] - e_['med']) < tol)
        ok(f'box readback {o} group {i}: whiskers (line and both caps) end on the furthest data inside 1.5 box lengths', abs(g_['wlo'] - e_['wlo']) < tol and abs(g_['whi'] - e_['whi']) < tol and all(abs(c - w) < tol for c, w in zip(g_['caps'], (e_['wlo'], e_['whi']))))
    ol = outl(rbx['svg']); tx_ = texts(rbx['svg']); tt = sorted((x, num(t)) for x, y, f, a, t in tx_ if f == C.MUTED and a == 'middle') if o == 'horizontal' else sorted(((y - 5), num(t)) for x, y, f, a, t in tx_ if f == C.MUTED and a == 'end'); Vv = lin(*tt[0], *tt[-1])
    for i, vv in enumerate(BS):
        rd = sorted(Vv(x if o == 'horizontal' else y) for lane, x, y in ol if lane == i); ex = ref_tukey(vv)['out']
        ok(f'box readback {o} group {i}: outlier circles read from pixels are exactly the brute-force outliers', len(rd) == len(ex) and all(abs(a - b) < tol for a, b in zip(rd, ex)))
for m_ in ('exclusive', 'inclusive'):
    rbx = box_plot(groups=G(BS[1], BS[2][:29]), quartile_method=m_)['horizontal']; got, perpx = box_readback(rbx['svg'], 'horizontal')
    def halves(v):
        s_ = sorted(v); h_ = len(s_) // 2; lo_, hi_ = (s_[:h_], s_[h_ + 1:]) if len(s_) % 2 and m_ == 'exclusive' else (s_[:h_ + 1], s_[h_:]) if len(s_) % 2 else (s_[:h_], s_[h_:])
        return statistics.median(lo_), statistics.median(hi_)
    ok(f'box readback {m_}: Q1 and Q3 read from pixels are the medians of the lower and upper half (statistics.median)', all(abs(got[i]['q1'] - halves(v)[0]) < .06 * perpx and abs(got[i]['q3'] - halves(v)[1]) < .06 * perpx for i, v in enumerate((BS[1], BS[2][:29]))))
# ---- vertical layout key, outlier note and unit on both variants
longn = box_plot(groups=[{'label': f'A rather long group name {i}', 'values': O9} for i in range(7)])['vertical']; ok('box_plot vertical: names that cannot fit are replaced by numbers with a key under the axis', all(f'{i + 1} = A rather long group name {i}' in longn['svg'] for i in range(7)) and '>1<' in longn['svg'] and wf(longn))
shortn = box_plot(groups=G(O9, O9))['vertical']; ok('box_plot vertical: names that fit stay as names, no key', '1 = g0' not in shortn['svg'] and '>g0<' in shortn['svg'])
vo = box_plot(groups=G(V), unit='ms')['vertical']; ok('box_plot vertical: outlier tooltips carry the unit and the table counts the outliers', 'outlier 100 ms' in vo['svg'] and '2 outliers: -60 ms, 100 ms' in vo['table'])
# ---- degrade before refusing
heavy = [{'label': f'Group number {i} with a long name', 'values': [rng.paretovariate(1.2) * 10 * (1 if rng.random() < .5 else -1) for _ in range(2000)]} for i in range(12)]
hv = box_plot(groups=heavy, show_points=True, unit='ms')
ok('box_plot: 12 groups x 2000 heavy-tailed numbers with dots are drawn (not refused), under 80 KB, with a note saying what was dropped', all(len(hv[o]['svg'].encode()) < 80_000 and any('keep the drawing small' in x for x in hv[o]['notes']) for o in ('horizontal', 'vertical')) and hv['horizontal']['level'] >= 1)
ok('box_plot: the degraded drawing still has every box and the table still counts every value', all(hv[o]['svg'].count('data-box=') == 12 for o in ('horizontal', 'vertical')) and all(f'n 2000' in hv['horizontal']['table'] for _ in [0]) and hv['horizontal']['table'].count('n 2000') == 12)
mid_ = [{'label': f'G{i}', 'values': [50.0 + (j % 7) for j in range(400)] + [1000.0 + 10 * j + i for j in range(60)]} for i in range(12)]
mb = box_plot(groups=mid_, show_points=True, unit='ms')['horizontal']
ok('box_plot: 12 groups x 60 outliers + 300 dots (under the element limit, over the byte budget with tooltips): tooltips are dropped, size within 72 KB, every outlier circle still drawn', len(mb['svg'].encode()) <= 72_000 and mb['level'] >= 1 and len(outl(mb['svg'])) == 720 and any('Tooltips were left out' in x for x in mb['notes']))
tiny_dot = box_plot(groups=G([5.0] * 100 + [6.0] * 100), show_points=True)['horizontal']; ok('beeswarm/box dots: 200 dots at two x values in one row stay inside the drawing budget', len(tiny_dot['svg']) < 80_000)
# ---- robustness negative controls, through the same entry point a service uses (call(), no isolation so a failure shows its own traceback)
def survives(macro, params):
    try: D.call(macro, params, isolate=False); return True
    except D.MacroError as e: return 'failed on this input' not in str(e) and 'time budget' not in str(e)
NEAR = {'histogram': lambda v: dict(values=v), 'box_plot': lambda v: dict(groups=[{'values': v}], show_points=True), 'ridgeline': lambda v: dict(groups=[{'name': 'a', 'values': v}]), 'beeswarm': lambda v: dict(values=v)}
for m_, mk in NEAR.items():
    ok(f'{m_}: near-constant data [0,0,0,0,1e-13] is drawn, not a crash', survives(m_, mk([0, 0, 0, 0, 1e-13])))
    ok(f'{m_}: a subnormal span [0,0,0,0,1e-310] is drawn, not a crash', survives(m_, mk([0, 0, 0, 0, 1e-310])))
    ok(f'{m_}: 10**400, NaN, inf, True, text and None in the numbers are skipped (counted) without a crash', survives(m_, mk([1, 2, 3, 4, 5, 10 ** 400, float('nan'), float('inf'), True, 'x', None, -10 ** 400])))
    ok(f'{m_}: values at +-1e12 and just beyond are handled', survives(m_, mk([1e12, -1e12, 0, 0, 0, 1e12 + 1e5])))
    ok(f'{m_}: label, title, unit and x_label that are 10**400, NaN, dict or list are tolerated', survives(m_, dict(mk([1, 2, 3, 4, 5, 6]), title=10 ** 400, unit=float('nan'))))
r_ = histogram(values=[0, 0, 0, 0, 1e-13])['bars']; ok('histogram: [0,0,0,0,1e-13] is one bin of width 1 holding all five numbers (span under 1e-9)', r_['counts'] == [[5]] and r_['edges'][1] - r_['edges'][0] == 1)
ok('box_plot: near-constant group is one box at a single value inside a width-1 axis', box_plot(groups=G([3.0, 3.0, 3.0, 3.0, 3.0 + 1e-13]))['horizontal']['domain'][1] - box_plot(groups=G([3.0, 3.0, 3.0, 3.0, 3.0 + 1e-13]))['horizontal']['domain'][0] >= 1)
ok('histogram: 10**400 as a label or number never raises OverflowError', histogram(values=[10 ** 400] * 3 + [1, 2, 3, 4, 5], title=10 ** 400, x_label=10 ** 400, unit=10 ** 400)['bars']['counts'][0] and sum(histogram(values=[10 ** 400] * 3 + [1, 2, 3, 4, 5], title=10 ** 400)['bars']['counts'][0]) == 5)
ok('histogram: a 10**400 entry is skipped and counted, not read as a number', any('1 values were left out' in x for x in histogram(values=[1, 2, 3, 4, 5, 10 ** 400])['bars']['notes']) and histogram(values=[1, 2, 3, 4, 5, 10 ** 400])['bars']['counts'] == histogram(values=[1, 2, 3, 4, 5])['bars']['counts'])
unk = D.call('histogram', dict(values=[1, 2, 3, 4, 5], bogus=1, __class__=2), isolate=False)['bars']; ok('call(): unknown keyword options are dropped and named in the notes (histogram)', any('Unknown option' in x and 'bogus' in x for x in unk['notes']))
for m_, pr in (('box_plot', dict(groups=G(O9))), ('ridgeline', dict(groups=[{'name': 'a', 'values': O9}])), ('beeswarm', dict(values=O9))):
    ru = D.call(m_, dict(pr, nonsense='x'), isolate=False); ok(f'call(): unknown keyword options are named in the notes ({m_})', all(any('nonsense' in x for x in v['notes']) for k_, v in ru.items() if k_ != '_default'))
ctl = 'ab\x00c\x1b[31m‮d\ud800e'
for m_, pr in (('histogram', dict(values=O9, title=ctl, x_label=ctl, unit=ctl)), ('box_plot', dict(groups=[{'label': ctl, 'values': O9}], title=ctl, x_label=ctl, unit=ctl)), ('ridgeline', dict(groups=[{'name': ctl, 'values': O9}], title=ctl, unit=ctl)), ('beeswarm', dict(groups=[{'name': ctl, 'values': O9}], title=ctl, unit=ctl))):
    ru = D.call(m_, pr, isolate=False); allt = ' '.join(v['svg'] + v['alt'] + v['table'] + ' '.join(v['notes']) for k_, v in ru.items() if k_ != '_default')
    ok(f'{m_}: control, bidi and surrogate characters in labels are removed from drawing, alt and table (and the XML is well-formed)', not re.search('[\x00-\x08\x0b\x0c\x0e-\x1f‮\ud800]', allt) and all(wf(v) for k_, v in ru.items() if k_ != '_default') and 'abc[31md' in allt.replace('\x1b', ''))
# ---- caps before reading
class Boom(list):
    def __getitem__(self, k):
        if isinstance(k, slice): return list.__getitem__(self, k)
        raise AssertionError('read past the cap')
    def __iter__(self): raise AssertionError('iterated the whole list')
big_g = Boom([{'label': str(i), 'values': list(range(10))} for i in range(50)])
try: r_ = box_plot(groups=big_g)['horizontal']; capped = len(r_['stats']) == 12
except AssertionError: capped = False
ok('box_plot: a list of 50 groups is cut to 12 BEFORE any of the rest is read', capped)
try: r_ = histogram(layout='ridge', series=Boom([{'label': str(i), 'values': list(range(10))} for i in range(50)]))['ridge']; capped = len(r_['counts']) == 8
except AssertionError: capped = False
ok('histogram ridge: 50 series are cut to 8 before reading', capped)
try: r_ = beeswarm(Boom([{'name': str(i), 'values': [float(i), 1.0]} for i in range(50)]))['swarm']; capped = len(r_['radii']) == 8
except AssertionError: capped = False
ok('beeswarm: 50 groups cut to 8 before reading', capped)
ok('histogram: a 1,000,000-entry values list is cut to the first 2000 without being walked', sum(histogram(values=list(range(1_000_000)))['bars']['counts'][0]) == 2000)
# ---- beeswarm placement against a brute-force reference (the old O(n^2) candidate search) and speed
def place_ref(xs, r, half, gap=1.0):
    d = 2 * r + gap; placed = []; ys = {}
    for i in sorted(range(len(xs)), key=lambda j: (xs[j], j)):
        x = xs[i]; near = [(a, b) for a, b in placed if abs(a - x) < d]; cands = [0.0]
        for a, b in near: dy = math.sqrt(max(0.0, d * d - (a - x) ** 2)); cands += [b - dy, b + dy]
        best = None
        for y in sorted(cands, key=lambda v: (abs(v), -v)):
            if abs(y) > half: continue
            if all(math.hypot(a - x, b - y) >= d - 1e-9 for a, b in near): best = y; break
        ys[i] = best
        if best is not None: placed.append((x, best))
    return ys
same = True
for t in range(25):
    xs_ = [round(rng.choice([rng.uniform(0, 80), rng.randint(0, 6) * 9.0]), 1) for _ in range(rng.randint(1, 70))]; rw = rng.choice([4, 6]); hf = rng.choice([20, 60, 200])
    a_, b_ = place(xs_, rw, hf), place_ref(xs_, rw, hf)
    if set(a_) != set(b_) or any((a_[k] is None) != (b_[k] is None) or (a_[k] is not None and abs(a_[k] - b_[k]) > 1e-6) for k in a_): same = False
ok('beeswarm: bucketed placement gives the same offsets as the brute-force candidate search on 25 random layouts (ties, crowds, tight lanes)', same)
t0 = time.time(); beeswarm([{'name': 'a', 'values': [5.0] * 400}, {'name': 'b', 'values': [5.0] * 400}]); dt = time.time() - t0
ok(f'beeswarm: 2 x 400 identical values take under 1 s ({dt:.2f} s)', dt < 1.0)
# =============================== registry and A2UI messages
from d3pack.registry_stats import DEMO_FN
ok('registry: four macros named like their atoms, every demo maps to one', set(PACK_STATS) == {'histogram', 'box_plot', 'ridgeline', 'beeswarm'} and set(DEMOS) == set(DEMO_FN) and set(DEMO_FN.values()) <= set(PACK_STATS))
for name, params in DEMOS.items():
    fn = PACK_STATS[DEMO_FN[name]]; results = fn(**params); default = results.pop('_default'); create, updates = C.atom_card('T', results, default)
    ok(f'{name}: createSurface validates', not list(A2R.iter_errors(create))); ok(f'{name}: every update validates', all(not list(A2R.iter_errors(u)) for u in updates.values()))
    ok(f'{name}: only Basic components', {c['component'] for c in create['createSurface']['components']} <= {'Card', 'Column', 'Row', 'Text', 'Image', 'Button'})
    ids = {c['id'] for c in create['createSurface']['components']}; refs = set()
    for c in create['createSurface']['components']: refs |= set(c.get('children', [])) | ({c['child']} if 'child' in c else set())
    ok(f'{name}: child references resolve and image description is bound', refs <= ids and all('description' in c for c in create['createSurface']['components'] if c['component'] == 'Image'))
    ok(f'{name}: payload under 200 KB', len(json.dumps(create)) < 200_000)
    for v in results.values(): generic(f'{name} demo', v)
    ok(f'{name}: the data model carries the alt text and the full table', create['createSurface']['dataModel']['table'].startswith(C.ENVELOPE) and C.md_safe(results[default]['table'][:80]) in create['createSurface']['dataModel']['table'] and create['createSurface']['dataModel']['alt'].startswith(results[default]['alt'][:200]))
    b1 = copy.deepcopy(create); b1['version'] = 'v1.0'; ok(f'{name}: negative: bad version rejected', bool(list(A2R.iter_errors(b1))))
    b2 = copy.deepcopy(create); b2['createSurface']['components'][2]['component'] = 'Chart'; ok(f'{name}: negative: unknown component rejected', bool(list(A2R.iter_errors(b2))))
nc = histogram(values=[1, 2]); c2, u2 = C.atom_card('T', {'bars': nc['bars']}, 'bars'); ok('histogram: the note-only card validates as A2UI too', not list(A2R.iter_errors(c2)) and all(not list(A2R.iter_errors(u)) for u in u2.values()))
print(f'stats pack tests: {n} checks, {bad} failed'); sys.exit(1 if bad else 0)
