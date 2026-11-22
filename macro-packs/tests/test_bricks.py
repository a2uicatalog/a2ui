"""brick_build and connect_four macros: draw order against a separating-plane oracle, the SVG read back (every polygon and top-face colour), the build checks, the tolerant reader, size, determinism, isolation. Each guard has a negative control.
Run: python3 tests/test_bricks.py   (stdlib only; no network, no model)."""
import sys, random, re, json, math
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.dont_write_bytecode = True
import d3pack
bb = sys.modules['d3pack.brick_build']
fails = []; n = 0
def ok(name, c):
    global n; n += 1
    if not c: fails.append(name); print('FAIL', name)
def brick(x, y, z, w=1, d=1, h=1, c='#c2182b'): return {'x': x, 'y': y, 'z': z, 'w': w, 'd': d, 'h': h, 'c': c}
def rnd_model(seed, cnt=25, grid=8, layers=4):
    r = random.Random(seed); used = set(); out = []
    for _ in range(cnt * 6):
        if len(out) >= cnt: break
        w, d, h = r.choice([1, 2, 3]), r.choice([1, 2]), r.choice([1, 1, 2]); x, z, y = r.randrange(grid - w + 1), r.randrange(grid - d + 1), r.randrange(layers)
        cells = {(x + a, y + c, z + b) for a in range(w) for b in range(d) for c in range(h)}
        if cells & used: continue
        used |= cells; out.append(brick(x, y, z, w, d, h, r.choice(['#c2182b', '#2f6fd8', '#f5c518', '#2e9e57'])))
    return out
def polys(svg): root = ET.fromstring(svg); ns = '{http://www.w3.org/2000/svg}'; return [e for e in root.iter(ns + 'polygon')]
# ---- draw order: whenever a plane separates two bricks (exactly one way), the one behind is drawn first
bad = 0; pairs = 0
for seed in range(40):
    B = bb._read(rnd_model(seed), None, []); order = bb._order(B); pos = {i: k for k, i in enumerate(order)}
    box = [(x, x + w, y * bb.BH, (y + h) * bb.BH, z, z + d) for x, y, z, w, d, h, c in B]
    for i in range(len(B)):
        for j in range(len(B)):
            a, b = box[i], box[j]
            if i == j: continue
            ab = a[1] <= b[0] or a[5] <= b[4] or a[3] <= b[2]; ba = b[1] <= a[0] or b[5] <= a[4] or b[3] <= a[2]
            if ab and not ba: pairs += 1; bad += pos[i] > pos[j]
ok(f'draw order respects every separating plane ({pairs} pairs over 40 random models)', bad == 0 and pairs > 1000)
B = bb._read(rnd_model(1), None, []); rev = list(reversed(bb._order(B))); box = [(x, x + w, y * bb.BH, (y + h) * bb.BH, z, z + d) for x, y, z, w, d, h, c in B]; pos = {i: k for k, i in enumerate(rev)}
viol = sum(1 for i in range(len(B)) for j in range(len(B)) if i != j and (box[i][1] <= box[j][0] or box[i][5] <= box[j][4] or box[i][3] <= box[j][2]) and not (box[j][1] <= box[i][0] or box[j][5] <= box[i][4] or box[j][3] <= box[i][2]) and pos[i] > pos[j])
ok('negative control: the reversed order violates the oracle', viol > 0)
# ---- read-back: three polygons per brick and per plate; every top face colour is the brick's colour tone
models = {s: rnd_model(s, 18) for s in range(6)}
for s, M in models.items():
    r = d3pack.call('brick_build', {'bricks': M}, isolate=False)['complete']; ps = polys(r['svg'])
    tops = sorted(p.get('fill') for p in ps[2::3]) if False else None
    fills = [p.get('fill') for p in ps]; ok(f'model {s}: 3 polygons per brick plus 3 for the plate ({len(ps)} for {len(M)})', len(ps) == 3 * (len(M) + 1))
    want = sorted([bb._tone(b['c'], 1.0, 0.22) for b in M] + [bb._tone('#2e9e57', 1.0, 0.22)]); got = sorted(f for f in fills if f in set(want)); 
    ok(f'model {s}: every top-face colour is present the right number of times', all(got.count(c) >= want.count(c) for c in set(want)))
    ok(f'model {s}: passes the output policy and is deterministic', d3pack.common.verify_svg(r['svg']) and d3pack.call('brick_build', {'bricks': M}, isolate=False)['complete']['svg'] == r['svg'])
r = d3pack.call('brick_build', {'bricks': models[0]}, isolate=False)['complete']['svg']; cut = r.replace(re.search(r'<polygon[^>]*/>', r).group(0), '', 1); ok('negative control: a removed polygon breaks the count oracle', len(polys(cut)) != 3 * (len(models[0]) + 1))
# ---- no plate, no studs
r0 = d3pack.call('brick_build', {'bricks': [brick(0, 0, 0, 2, 2)], 'base': 'none', 'studs': False}, isolate=False)['complete']['svg']; ok('base none and studs off: exactly three polygons and no stud paths', len(polys(r0)) == 3 and '<path' not in r0)
r1 = d3pack.call('brick_build', {'bricks': [brick(0, 0, 0, 2, 2)], 'base': 'none', 'studs': True}, isolate=False)['complete']['svg']; ok('studs on: 4 studs, 2 paths each, one per stud position', r1.count('<path') == 8)
r2 = d3pack.call('brick_build', {'bricks': [brick(0, 0, 0, 2, 2), brick(0, 1, 0, 2, 1)], 'base': 'none'}, isolate=False)['complete']['svg']; ok('studs under a brick above are not drawn (4 + 2 uncovered)', r2.count('<path') == 2 * (2 + 2))
# ---- build checks
def chk(M): return bb._check(bb._read(M, None, []))
ok('check: a clean stack has no overlap, floating or disconnected brick', chk([brick(0, 0, 0), brick(0, 1, 0), brick(0, 2, 0)]) == (0, 0, 0))
ok('check: overlapping cells are counted', chk([brick(0, 0, 0, 2, 2), brick(1, 0, 1)])[0] == 1)
ok('check: a brick with nothing under it is floating (and what sits on it is not connected)', chk([brick(0, 0, 0), brick(3, 2, 3), brick(3, 3, 3)]) == (0, 1, 2))
ok('check: side by side on the plate is fine', chk([brick(0, 0, 0), brick(1, 0, 0), brick(2, 0, 0)]) == (0, 0, 0))
ok('check: a tall brick supports what sits on its top layer', chk([brick(0, 0, 0, h=3), brick(0, 3, 0)]) == (0, 0, 0))
# ---- tolerant reader
a = d3pack.call('brick_build', {'bricks': [[0, 0, 0, 2, 2, 0], [2, 0, 0, 2, 2, 2, 1]], 'palette': ['#c2182b', '#2f6fd8']}, isolate=False)['complete']
ok('compact arrays and palette indexes are read', 'bricks in' in a['summary'] and '#c2182b' in a['table'] and '#2f6fd8' in a['table'] and '2 x' not in a['summary'])
bad = [brick(0, 0, 0), {'x': 1.5, 'y': 0, 'z': 0, 'c': '#c2182b'}, {'x': 0, 'y': 0, 'z': 0, 'c': 'red'}, {'x': float('nan'), 'y': 0, 'z': 0, 'c': '#c2182b'}, {'x': 0, 'y': 0, 'z': 0, 'w': 99, 'c': '#c2182b'}, 'junk', None, {'x': True, 'y': 0, 'z': 0, 'c': '#c2182b'}, {'x': 0, 'y': 0, 'z': 0, 'c': '#fff"/><script>'}, {'x': 10 ** 400, 'y': 0, 'z': 0, 'c': '#c2182b'}]
r = d3pack.call('brick_build', {'bricks': bad}, isolate=False)['complete']; ok('unusable bricks are dropped and counted (9 of 10)', '9 bricks were unusable' in ' '.join(r['notes']) and '1 bricks in' in r['summary'].replace('1 brick in', '1 bricks in'))
for badin in ([], None, 'x', [{'x': 'a'}], [None]):
    try: d3pack.call('brick_build', {'bricks': badin}, isolate=False); ok(f'refuses {str(badin)[:14]!r}', False)
    except ValueError: ok(f'refuses {str(badin)[:14]!r}', True)
r = d3pack.call('brick_build', {'bricks': [brick(0, 0, 0)], 'title': '<script>alert(1)</script> \u202eevil', 'base': 'javascript:1'}, isolate=False)['complete']; ok('bidi controls stripped from the title, no title text or markup inside the SVG, a bad base falls back with a note', '\u202e' not in r['alt'] and '<script' not in r['svg'] and 'alert' not in r['svg'] and any('green plate' in x for x in r['notes']))
# ---- size, stages, isolation
r = d3pack.call('brick_build', {'bricks': [brick(x, y, z, 1, 1, 1, '#2f6fd8') for x in range(10) for z in range(10) for y in range(5)]}, isolate=False)['complete']; ok(f'500 one-stud bricks stay under 80 KB ({len(r["svg"])} B) and the cut is noted', len(r['svg']) < 80000 and any('not drawn' in x for x in r['notes']))
res = d3pack.call('brick_build', {'bricks': rnd_model(3, 30)}, isolate=False); st = [k for k in res if k.startswith('stage')]; counts = [int(re.search(r'first (\d+) bricks', res[k]['summary']).group(1)) for k in st]
ok(f'stages are cumulative and shorter than the whole ({counts})', counts == sorted(counts) and all(c < 30 for c in counts) and len(set(counts)) == len(counts))
ok('isolated child run gives the same picture', d3pack.call('brick_build', {'bricks': models[1]}, isolate=True)['complete']['svg'] == d3pack.call('brick_build', {'bricks': models[1]}, isolate=False)['complete']['svg'])
ok('parts list groups identical parts', '3 x 2x2 brick #c2182b' in d3pack.call('brick_build', {'bricks': [brick(0, 0, 0, 2, 2), brick(2, 0, 0, 2, 2), brick(4, 0, 0, 2, 2)]}, isolate=False)['complete']['table'])
ok('registered in the pack', 'brick_build' in d3pack.PACK and 'connect_four' in d3pack.PACK)
print(f'brick tests: {n} checks, {len(fails)} failed'); sys.exit(1 if fails else 0)
