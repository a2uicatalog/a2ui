"""Regression tests for the render-time fixes (venn region count, contour rings / density, SVG output-policy check).
Each fix must leave the drawing byte-identical: (1) the stored hash of the full card of every touched demo, taken BEFORE the fixes (tests/perf_hashes.json); (2) each fast path against a plain reference copy of the original algorithm on
random inputs; (3) a loose time bound (about 5 x the median measured after the fix, one machine, loaded) so a return to the old cost fails and normal noise does not.
Run: python3 tests/test_perf.py   (stdlib only; no network, no model)."""
import sys, json, math, random, hashlib, time, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.dont_write_bytecode = True
import d3pack
from d3pack import venn as V, contour as C, common
fails = []; n = 0
def ok(name, c):
    global n; n += 1
    if not c: fails.append(name); print('FAIL', name)
ns = {}; exec(open(HERE.parent / 'make_payloads.py').read().split('ALL = {')[0], ns)
ALL = {k: (k, p) for k, p in ns['DEMOS'].items()}; ALL.update(d3pack._demos())
# ---- (1) identity against the pre-fix hashes, and (3) time bounds (bound ms = about 5 x the post-fix median of the whole card() call, n=7)
STORED = json.load(open(HERE / 'perf_hashes.json')); BOUND_MS = {'venn': 90, 'venn_two': 90, 'contour_points': 220, 'connect_four_midgame': 130, 'brick_house': 80, 'brick_pyramid': 140}
for k, want in STORED.items():
    macro, p = ALL[k]; ts = []
    for i in range(5):
        t = time.perf_counter(); c, u, r = d3pack.card(macro, k, p); ts.append((time.perf_counter() - t) * 1000)
    got = hashlib.sha256((json.dumps([c, u], sort_keys=True) + repr(r)).encode()).hexdigest()[:16]
    ok(f'{k}: card is identical to the pre-fix output ({got})', got == want)
    if k in BOUND_MS: ok(f'{k}: median {statistics.median(ts):.0f} ms is under {BOUND_MS[k]} ms', statistics.median(ts) < BOUND_MS[k])
# ---- (2a) venn: region counts and centroid sums against the plain 300 x 300 loop
def ref_regions(pos, R, xs0, xs1, ys0, ys1, N=300):
    k = len(pos); cnt = {}; cen = {}; dx = (xs1 - xs0) / N; dy = (ys1 - ys0) / N
    for a in range(N):
        px = xs0 + (a + .5) * dx
        for b in range(N):
            py = ys0 + (b + .5) * dy; m = tuple(i for i in range(k) if (px - pos[i][0]) ** 2 + (py - pos[i][1]) ** 2 <= R[i] * R[i])
            if m: cnt[m] = cnt.get(m, 0) + 1; c = cen.setdefault(m, [0.0, 0.0]); c[0] += px; c[1] += py
    return cnt, cen
rg = random.Random(7); same = True; cases = 0
for _ in range(40):
    k = rg.choice([2, 3]); R = [rg.uniform(.3, 3) for _ in range(k)]; pos = [(0.0, 0.0), (rg.uniform(0, R[0] + R[1] + .5), 0.0)] + ([(rg.uniform(-2, 4), -rg.uniform(0, 4))] if k == 3 else [])
    if rg.random() < .15: R[0] = 0.0                                    # empty set
    xs0 = min(p[0] - r for p, r in zip(pos, R)); xs1 = max(p[0] + r for p, r in zip(pos, R)); ys0 = min(p[1] - r for p, r in zip(pos, R)); ys1 = max(p[1] + r for p, r in zip(pos, R))
    if not (xs1 > xs0 and ys1 > ys0): continue
    cnt, cen = V.grid_regions(pos, R, xs0, xs1, ys0, ys1); rc, rcen = ref_regions(pos, R, xs0, xs1, ys0, ys1); cases += 1
    same &= (cnt == rc and list(cnt) == list(rc))                       # counts and first-seen order
    if k == 2: same &= (cen.get((0, 1)) == rcen.get((0, 1)))            # the one centroid the drawing uses, bit for bit
ok(f'venn grid_regions equals the plain loop on {cases} random 2- and 3-circle cases (counts, order, centroid)', same and cases >= 30)
# ---- (2b) contour: ring_keys (both the plain and the band-rows path) against the original per-cell scan
def ref_ring_keys(P, t):
    R, C_ = len(P), len(P[0]); BIG = R * C_ + 1; ins = [[v >= t for v in row] for row in P]; nxt = {}; offs = ((0, 1), (1, C_ + 1), (C_, C_ + 1), (0, C_))
    for r in range(R - 1):
        ra, rb = ins[r], ins[r + 1]
        for c in range(C_ - 1):
            m = ra[c] | ra[c + 1] << 1 | rb[c + 1] << 2 | rb[c] << 3
            if m == 0 or m == 15: continue
            i = r * C_ + c; segs = C._CASES[m]
            if m == 5 or m == 10:
                vs = [x for x in (P[r][c], P[r][c + 1], P[r + 1][c + 1], P[r + 1][c]) if x != C.NEG]; segs = segs[0] if sum(vs) / len(vs) >= t else segs[1]
            for e1, e2 in segs:
                a1, b1 = offs[e1]; a2, b2 = offs[e2]; nxt[(i + a1) * BIG + i + b1] = (i + a2) * BIG + i + b2
    rings = []; seen = set()
    for start in nxt:
        if start in seen: continue
        ring = []; k = start
        while k not in seen: seen.add(k); ring.append(k); k = nxt[k]
        rings.append(ring)
    return rings, BIG
import bisect
rg = random.Random(11); same = True; tot = 0
for case in range(60):
    h, w = rg.randint(2, 30), rg.randint(2, 30); mode = case % 3
    rows = [[None if rg.random() < .06 else (rg.randint(0, 4) if mode == 0 else rg.random() * 10 if mode == 1 else float(rg.choice([0, 5, 5, 10]))) for _ in range(w)] for _ in range(h)]
    P = C._pad(rows, h, w); good = [q for r in rows for q in r if q is not None]
    if not good: continue
    ths = sorted({float(rg.randint(0, 10)) if mode != 1 else rg.random() * 10 for _ in range(rg.randint(1, 8))})
    band = [bytes([bisect.bisect_right(ths, v) if v == v else 0 for v in row]) for row in P]
    for k, t in enumerate(ths):
        ref = ref_ring_keys(P, t); same &= (C.ring_keys(P, t) == ref and C.ring_keys(P, t, band, k) == ref); tot += 1
ok(f'contour ring_keys (plain and band-rows paths) equals the original scan on {tot} random levels, saddles and ties included', same and tot > 150)
# ---- (2c) contour: kde_grid against the original two-pass convolution
def ref_kde(pts_px, sigma, cell):
    PX, PY, PW, PH = C.PX, C.PY, C.PW, C.PH; gw, gh = PW // cell + 1, PH // cell + 1; M = [[0.0] * gw for _ in range(gh)]
    for x, y in pts_px:
        fx, fy = (x - PX) / cell, (y - PY) / cell; i, j = int(math.floor(fx)), int(math.floor(fy)); ax, ay = fx - i, fy - j
        for jj, wy in ((j, 1 - ay), (j + 1, ay)):
            for ii, wx in ((i, 1 - ax), (i + 1, ax)):
                if 0 <= ii < gw and 0 <= jj < gh: M[jj][ii] += wx * wy
    rad = max(1, int(math.ceil(3 * sigma / cell))); k = [math.exp(-((cell * q) ** 2) / (2 * sigma * sigma)) for q in range(-rad, rad + 1)]; s = sum(k); k = [q / s for q in k]
    def conv(rows, n):
        out = []
        for row in rows:
            o = [0.0] * n
            for i, w in enumerate(row):
                if w > 1e-12:
                    for q in range(max(0, i - rad), min(n, i + rad + 1)): o[q] += w * k[q - i + rad]
            out.append(o)
        return out
    H1 = conv(M, gw); T = [list(col) for col in zip(*H1)]; V_ = conv(T, gh); N = len(pts_px)
    return [[V_[i][j] / (N * cell * cell) for i in range(gw)] for j in range(gh)]
rg = random.Random(5); same = True
for case in range(12):
    pts = [(C.PX + rg.random() * C.PW * (1.1 if case % 4 == 3 else 1) - 20 * (case % 4 == 3), C.PY + rg.random() * C.PH * (.3 if case % 2 else 1)) for _ in range(rg.randint(3, 200))]
    sg = rg.choice([5, 12, 20, 45, 60]); cell = 8 if sg >= 16 else 4; same &= (C.kde_grid(pts, sg, cell) == ref_kde(pts, sg, cell))
ok('contour kde_grid equals the original two-pass convolution on 12 random point sets (every float)', same)
# ---- (2d) the output-policy check still accepts and refuses what it did, and a repeat call is a lookup
good = ALL['venn'] and d3pack.call('venn', ALL['venn'][1], isolate=False)['venn']['svg']
ok('verify_svg returns a good drawing unchanged, twice', common.verify_svg(good) is good or common.verify_svg(good) == good)
bad = [good.replace('<circle', '<circle onclick="x"', 1), good.replace('role="img"', 'role="button"'), good.replace('fill-opacity=".4"', 'fill-opacity="1e9"', 1), good.replace('<circle', '<image', 1), good.replace('</svg>', '<path d="M0,0L99999999,5"/></svg>'),
       good.replace('</svg>', '<path d="M0,0L1e9,5"/></svg>'), good.replace('</svg>', '<path d="M0,0L1,5 x"/></svg>'), good.replace('</svg>', '<path d="M0,0L100000,5"/></svg>')]
res = []
for b in bad + bad:
    try: common.verify_svg(b); res.append(True)
    except common.SvgPolicyError: res.append(False)
ok(f'verify_svg refuses the same bad drawings every time (accepted: {res})', res == [False] * 7 + [True] + [False] * 7 + [True])
print(f'perf tests: {n} checks, {len(fails)} failed'); sys.exit(1 if fails else 0)
