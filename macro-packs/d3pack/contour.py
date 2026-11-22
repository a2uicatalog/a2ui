"""contour_plot macro: same contract as the contour_plot atom (grid {width,height,values} OR points [{x,y}], thresholds 3..20, bandwidth 5..60 px of the 600x400 box,
x_label, y_label, value_label, unit, title, version). Contract source: atoms/schema.yaml (`- type: contour_plot`); the older a2ui-catalogue
schema.yaml has no contour_plot. Returns {'contour': Result, '_default': 'contour'}.

Follows the atom: thresholds by d3's own rule (d3.contours with a count: nice the value extent, take d3.ticks of it, drop ticks at or above the maximum, drop leading ticks while the
second tick is below the minimum, so the FIRST level can sit at or below the minimum and then band 0 is empty; implemented in d3_nice / d3_ticks); default count for a grid is Sturges
(ceil(log2 cells) + 1), for points 20; a cell's class is the number of levels <= its value; a grid cell i spans i to i+1 on the axes (the value is for the whole cell, nodes sit at cell
centres, the grid is stretched to the 600x400 box); points use their own x and y with the data range niced by d3 (a flat range widened by 1 each side), y up; every band is named in a
legend as a range of numbers; the table gives every level with its cell count and the share of cells (or points) at or above it, then the first 200 points.
Differences from the atom, all stated: no faint point dots (2000 circles would break the 4000 element / 80 KB budget), one outline colour for every band (no per-band contrast choice),
and the outline budget is ring-based (below) rather than the atom's 40,000-point cap.

How the bands are built (pure Python, no d3):
 * Marching squares per level on the value grid padded with one ring of "outside" nodes (-infinity). Walking the four corners of a 2x2 block clockwise, an edge that goes inside ->
   outside is an EXIT and outside -> inside an ENTRY; each segment runs entry -> exit, so the region is always on the same side and neighbouring cells meet head to tail. Saddles are
   resolved by the cell mean (mean >= level joins the inside corners). Segments are joined by the identity of the crossed edge (integers, never float comparison), so every ring closes.
   A crossing between two real nodes is interpolated linearly; one towards a pad node sits ON the pad node, half a cell beyond the plot box (one towards an empty interior cell sits halfway),
   and the drawing is clipped to the box, so bands reach the corners.
 * Bands are cumulative: each level's rings go into ONE evenodd path (holes are rings in rings), painted from the lowest level up over a class-0 base.
 * Points mode: data -> niced axes -> linear-binned onto a node grid (4 px spacing; 8 px when the bandwidth is 16 px or more, which is accurate and keeps it fast), smoothed by a separable
   Gaussian with sigma = bandwidth px (cut at 3 sigma, normalised), in share of the points per 10,000 px2, then contoured like a grid.
 * Time and size: ring points are budgeted (RING_BUDGET). Over budget, the smallest rings (by point count) are left out, the note says how many, and a single ring bigger than the budget is
   thinned evenly. The band cell counts are always exact. A checkerboard 100 by 100 grid with 20 levels is the worst case."""
# Port of d3-array 3.2.4 tickIncrement/ticks/nice (ISC), Copyright 2010-2023 Mike Bostock. See THIRD-PARTY-NOTICES.md.
import math, bisect, hashlib
from .common import *
PX, PY, PW, PH = 60, 50, 600, 400
RING_BUDGET = 9000
NEG = float('-inf')
SQ2, SQ10, SQ50 = math.sqrt(2), math.sqrt(10), math.sqrt(50)
def _incr(a, b, count):
    """d3.tickIncrement: positive = step; negative = minus the reciprocal of the step (for steps below 1)."""
    if not count > 0: return 0
    step = (b - a) / count
    if not (step > 1e-290 and math.isfinite(step)): return 0
    power = math.floor(math.log10(step)); err = step / 10.0 ** power
    factor = 10 if err >= SQ50 else 5 if err >= SQ10 else 2 if err >= SQ2 else 1
    return factor * 10.0 ** power if power >= 0 else -(10.0 ** -power) / factor
def d3_ticks(a, b, count):
    """d3.ticks(a, b, count): multiples of 1, 2 or 5 times a power of ten inside [a, b], aiming for `count`."""
    if not count > 0: return []
    if a == b: return [a]
    i = _incr(a, b, count)
    if i == 0 or not math.isfinite(i): return []
    rnd = lambda x: math.floor(x + .5)
    if i > 0:
        r0, r1 = rnd(a / i), rnd(b / i)
        if r0 * i < a: r0 += 1
        if r1 * i > b: r1 -= 1
        return [(r0 + j) * i for j in range(min(max(r1 - r0 + 1, 0), 2000))]
    s = -i; r0, r1 = rnd(a * s), rnd(b * s)
    if r0 / s < a: r0 += 1
    if r1 / s > b: r1 -= 1
    return [(r0 + j) / s for j in range(min(max(r1 - r0 + 1, 0), 2000))]
def d3_nice(a, b, count):
    """d3.nice: widen [a, b] to multiples of the tick step (repeated until it settles)."""
    pre = None
    for _ in range(10):
        step = _incr(a, b, count)
        if step == pre or step == 0 or not math.isfinite(step): return a, b
        if step > 0: a = math.floor(a / step) * step; b = math.ceil(b / step) * step
        else: a = math.ceil(a * step) / step; b = math.floor(b * step) / step
        pre = step
    return a, b
def levels(lo, hi, count):
    """The thresholds d3.contours would use for values spanning lo..hi (see the module docstring)."""
    a, b = d3_nice(lo, hi, count); tz = [float(f'{t:.12g}') for t in d3_ticks(a, b, count)]
    while tz and tz[-1] >= hi: tz.pop()
    while len(tz) > 1 and tz[1] < lo: tz.pop(0)
    return tz
_EDGE = ((0, 1), (1, 2), (2, 3), (3, 0))
def _case_table():
    """For each 4-bit inside pattern (TL, TR, BR, BL = bits 0..3): list of (entry edge, exit edge) segments; saddle patterns 5 and 10 hold two variants (joined, separated)."""
    T = {}
    for m in range(1, 15):
        b = [bool(m >> i & 1) for i in range(4)]
        ex = [k for k in range(4) if b[_EDGE[k][0]] and not b[_EDGE[k][1]]]; en = [k for k in range(4) if not b[_EDGE[k][0]] and b[_EDGE[k][1]]]
        if len(ex) == 1: T[m] = [(en[0], ex[0])]
        else: T[m] = ([(k, (k - 1) % 4) for k in range(4) if not b[k]], [((k - 1) % 4, k) for k in range(4) if b[k]])   # joined: cut off each outside corner; separated: cut off each inside corner
    return T
_CASES = _case_table()
def ring_keys(P, t, band_rows=None, level=None):
    """Closed rings of {value >= t} on the padded grid P (rows of floats, NEG = outside). Each ring is a list of edge keys (a * BIG + b, node ids a < b); returns (rings, BIG)."""
    R, C = len(P), len(P[0]); BIG = R * C + 1; nxt = {}; offs = ((0, 1), (1, C + 1), (C, C + 1), (0, C))
    if band_rows is None: ins = [[v >= t for v in row] for row in P]
    else: tbl = bytes(1 if x > level else 0 for x in range(256)); ins = [row.translate(tbl) for row in band_rows]   # node inside <=> v >= ths[level] <=> its band number (levels at or below it) is above `level`; offs = ((0, 1), (1, C + 1), (C, C + 1), (0, C))
    # Each row becomes one integer (byte c = 1 if node c is inside); the cells that are neither fully inside nor fully outside are the set bits of a few shifts and xors, and only those are visited, in the same
    # row-major order as before, so the dict order and the rings are unchanged.
    segd = {m: [(offs[e1], offs[e2]) for e1, e2 in segs] for m, segs in _CASES.items() if m not in (5, 10)}
    nb = C - 1; full = (1 << 8 * nb) - 1
    rm = [int.from_bytes(bytes(row), 'little') for row in ins]
    for r in range(R - 1):
        ra, rb = ins[r], ins[r + 1]; ma, mb = rm[r], rm[r + 1]
        act = ((ma ^ mb) | (ma ^ ma >> 8) | (mb ^ mb >> 8)) & full
        while act:
            low = act & -act; act ^= low; c = (low.bit_length() - 1) >> 3
            m = ra[c] | ra[c + 1] << 1 | rb[c + 1] << 2 | rb[c] << 3; i = r * C + c
            if m == 5 or m == 10:
                segs = _CASES[m]; vs = [x for x in (P[r][c], P[r][c + 1], P[r + 1][c + 1], P[r + 1][c]) if x != NEG]; segs = segs[0] if sum(vs) / len(vs) >= t else segs[1]
                for e1, e2 in segs:
                    a1, b1 = offs[e1]; a2, b2 = offs[e2]; nxt[(i + a1) * BIG + i + b1] = (i + a2) * BIG + i + b2
            else:
                for (a1, b1), (a2, b2) in segd[m]: nxt[(i + a1) * BIG + i + b1] = (i + a2) * BIG + i + b2
    rings = []; seen = set()
    for start in nxt:
        if start in seen: continue
        ring = []; k = start
        while k not in seen: seen.add(k); ring.append(k); k = nxt[k]
        rings.append(ring)
    return rings, BIG
def _pad(rows, nr, nc):
    P = [[NEG] * (nc + 2)]
    for row in rows: P.append([NEG] + [NEG if v is None else v for v in row] + [NEG])
    P.append([NEG] * (nc + 2)); return P
def key_points(keys, P, BIG, t, xy):
    """Coordinates of edge keys: interpolated between two real nodes; towards the outside ring ON the pad node; towards an empty interior cell halfway."""
    R, C = len(P), len(P[0]); out = []
    for k in keys:
        a, b = divmod(k, BIG); ra, ca = divmod(a, C); rb, cb = divmod(b, C); va, vb = P[ra][ca], P[rb][cb]
        pa, pb = xy(ra - 1, ca - 1), xy(rb - 1, cb - 1)
        if va == NEG or vb == NEG:
            # real = the node with a value; the other is outside (pad ring: crossing on it) or empty (halfway)
            (rr, cr, pr), (ro, co, po) = ((rb, cb, pb), (ra, ca, pa)) if va == NEG else ((ra, ca, pa), (rb, cb, pb))
            f = 1.0 if ro in (0, R - 1) or co in (0, C - 1) else .5
            out.append((pr[0] + (po[0] - pr[0]) * f, pr[1] + (po[1] - pr[1]) * f))
        else:
            f = (t - va) / (vb - va); out.append((pa[0] + (pb[0] - pa[0]) * f, pa[1] + (pb[1] - pa[1]) * f))
    return out
def contour_rings(vals, nr, nc, t, xy):
    """Rings (lists of (x, y)) of the region {value >= t} on an nr x nc node grid (vals[r][c], None = empty). xy(r, c) gives node positions, also for the pad ring r = -1 / nr, c = -1 / nc."""
    P = _pad(vals, nr, nc); rings, BIG = ring_keys(P, t); return [key_points(r, P, BIG, t, xy) for r in rings]
def _drop_collinear(ring):
    n = len(ring); out = []
    for i in range(n):
        a, b, c = ring[i - 1], ring[i], ring[(i + 1) % n]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9: out.append(b)
    return out if len(out) >= 3 else ring
def _path(rings, dec=1):
    return ''.join('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in (r[::dec] if dec > 1 and len(r) > 3 * dec else r)) + 'Z' for r in rings if len(r) >= 3)
def kde_grid(pts_px, sigma, cell):
    """Binned Gaussian density on the node grid (PW/cell + 1 by PH/cell + 1, nodes at PX + i*cell, PY + j*cell); returns share of points per px2 (list of rows)."""
    gw, gh = PW // cell + 1, PH // cell + 1; M = [[0.0] * gw for _ in range(gh)]
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
            if not any(row): out.append(o); continue      # an all-zero row adds nothing
            for i, w in enumerate(row):
                if w > 1e-12:
                    lo_, hi_ = max(0, i - rad), min(n, i + rad + 1)      # o[q] += w * k[q - i + rad] for q in [lo_, hi_), as one slice (same additions, same order per element)
                    o[lo_:hi_] = [x + w * kk for x, kk in zip(o[lo_:hi_], k[lo_ - i + rad:hi_ - i + rad])]
            out.append(o)
        return out
    H1 = conv(M, gw); N = len(pts_px)
    # Vertical pass done row-wise on H1 (no transpose): output row jj gets H1[j][x] * k[jj - j + rad] added, j ascending, only where H1[j][x] > 1e-12 -- the same additions in the same order per cell as the
    # column-wise conv of the transpose, so the floats are identical; each pass handles a whole row at once.
    V = [[0.0] * gw for _ in range(gh)]; thr = 1e-12
    for j, hr in enumerate(H1):
        hr = [w if w > thr else 0.0 for w in hr]       # a weight that is skipped adds 0.0 * kk = 0.0, which leaves the (never negative) running sum unchanged
        if not any(hr): continue
        for jj in range(max(0, j - rad), min(gh, j + rad + 1)):
            kk = k[jj - j + rad]; V[jj] = [o + w * kk for o, w in zip(V[jj], hr)]
    d = N * cell * cell
    return [[q / d for q in row] for row in V]
def _text(x, n, default=None):
    """clean_text that cannot overflow: an int too big for a float (10**400) is not text."""
    if isinstance(x, (int, float)) and not isinstance(x, bool) and finite(x, -1e15, 1e15) is None: return default
    return clean_text(x, n, default)
def _lab(v):
    s = fmt(v); return s if len(s) <= 9 else f'{v:.3g}'
def _whole(v, lo, hi):
    f = finite(v)
    if f is None or f != int(f): return None
    return int(f) if lo <= f <= hi else None
def contour_plot(grid=None, points=None, thresholds=None, bandwidth=20, x_label=None, y_label=None, value_label=None, unit='', title='', version=1):
    notes = []; u = _text(unit, 12, '') or ''; ttl = _text(title, 80, '') or ''
    ver = finite(version)
    if ver is not None and ver > 1: notes.append(f'Contract version {fmt(ver)} is drawn as version 1.')
    gmode = isinstance(grid, dict)
    if gmode and points is not None: notes.append('Both grid and points were given; the grid is drawn and the points are ignored.')
    if gmode:
        w = _whole(grid.get('width'), 2, 100); h = _whole(grid.get('height'), 2, 100); vals = grid.get('values')
        if w is None or h is None: raise ValueError('grid width and height must be whole numbers from 2 to 100')
        if not isinstance(vals, list) or len(vals) != w * h: raise ValueError(f'grid values must be a list of width x height = {w * h} numbers')
        flat = [finite(q) for q in vals]; bad = sum(1 for q in flat if q is None); good = [q for q in flat if q is not None]
        if not good: raise ValueError('the grid has no usable value')
        if bad: notes.append(f'{bad} grid values were not finite numbers (or beyond 1e12); they are left empty and treated as below every level.')
        rows = [flat[r * w:(r + 1) * w] for r in range(h)]; nr, nc = h, w; cw, ch = PW / w, PH / h
        xy = lambda r, c: (PX + (c + .5) * cw, PY + (r + .5) * ch)
        default_count = math.ceil(math.log2(w * h)) + 1; xl = _text(x_label, 30, 'Column'); yl = _text(y_label, 30, 'Row'); vl = _text(value_label, 30, 'Value')
        cell = None; extra = ''
        xticks = [(PX + v * cw, v) for v in d3_ticks(0, w, 8)]; yticks = [(PY + v * ch, v) for v in d3_ticks(0, h, 6)]
    else:
        if not isinstance(points, list): raise ValueError('give either grid {width, height, values} or points [{x, y}]')
        if len(points) > 2000: notes.append(f'{len(points) - 2000} points beyond the 2000th were not used.'); points = points[:2000]
        pts = []; bad = 0
        for p in points:
            x_, y_ = (finite(p.get('x')), finite(p.get('y'))) if isinstance(p, dict) else (None, None)
            if x_ is None or y_ is None: bad += 1
            else: pts.append((x_, y_))
        if bad: notes.append(f'{bad} entries were skipped (needs an object with finite numeric x and y).')
        if len(pts) < 3: raise ValueError('a density needs at least 3 usable points')
        bw = finite(bandwidth)
        if bw is None:
            bw = 20.0
            if bandwidth is not None: notes.append('bandwidth was not a usable number; 20 is used.')
        if bw < 5 or bw > 60: bw2 = min(60.0, max(5.0, bw)); notes.append(f'bandwidth {fmt(bw)} was clamped to {fmt(bw2)}.'); bw = bw2
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; xlo, xhi, ylo, yhi = min(xs), max(xs), min(ys), max(ys)
        if xhi == xlo: xlo -= 1; xhi += 1; notes.append('All x values are equal; the x axis is widened by 1 each side.')
        if yhi == ylo: ylo -= 1; yhi += 1; notes.append('All y values are equal; the y axis is widened by 1 each side.')
        xa, xb = d3_nice(xlo, xhi, 10); ya, yb = d3_nice(ylo, yhi, 10)
        if not xb > xa: xa, xb = xlo, xhi
        if not yb > ya: ya, yb = ylo, yhi
        ppx = [(PX + (x - xa) / (xb - xa) * PW, PY + PH - (y - ya) / (yb - ya) * PH) for x, y in pts]
        cell = 8 if bw >= 16 else 4; dens = kde_grid(ppx, bw, cell); rows = [[q * 1e4 for q in r] for r in dens]; nr, nc = len(rows), len(rows[0]); xy = lambda r, c: (PX + c * cell, PY + r * cell)
        good = [q for r in rows for q in r]; default_count = 20; w, h = nc, nr
        xl = _text(x_label, 30, 'x'); yl = _text(y_label, 30, 'y'); vl = 'Density'; u = ''
        xticks = [(PX + (v - xa) / (xb - xa) * PW, v) for v in d3_ticks(xa, xb, 8)]; yticks = [(PY + PH - (v - ya) / (yb - ya) * PH, v) for v in d3_ticks(ya, yb, 6)]
        extra = f'{len(pts)} points, bandwidth {fmt(bw)} px, x axis {fmt(xa)} to {fmt(xb)}, y axis {fmt(ya)} to {fmt(yb)}; density in share of points per 10,000 px2, on a {nc} by {nr} node grid ({cell} px spacing).'
    lo, hi = min(good), max(good)
    tc = default_count
    if thresholds is not None:
        tf = finite(thresholds)
        if tf is None: notes.append(f'thresholds was not a usable number; {default_count} is used.')
        else:
            t0 = math.floor(tf)
            if t0 != tf: notes.append(f'thresholds {fmt(tf)} was rounded down to {t0}.')
            tc = t0
    if tc < 3 or tc > 20: notes.append(f'thresholds {tc} was clamped to {min(20, max(3, tc))}.'); tc = min(20, max(3, tc))
    ths = levels(lo, hi, tc); n = len(ths)
    if not n: notes.append('The values are all equal (or no level falls below the maximum); one flat band is drawn.')
    elif ths[0] <= lo: notes.append(f'The first level ({fmt(ths[0])}) is at or below the lowest value, as d3 draws it, so band 0 is empty.')
    P = _pad(rows, nr, nc); counts = [0] * (n + 1)
    for r in rows:
        for q in r: counts[0 if q is None else bisect.bisect_right(ths, q)] += 1
    ramp = [blend(PAL[0], .93)] + [blend(PAL[0], .85 * (1 - k / max(1, n))) for k in range(1, n + 1)]
    allrings = []; BIG = 1   # (point count, level index, ring keys)
    # band number of every padded node once (0 for outside nodes, which are -inf, and for anything that is not a number), so that each level only has to translate bytes
    band_rows = [bytes([bisect.bisect_right(ths, v) if v == v else 0 for v in row]) for row in P] if len(ths) < 255 else None
    for k, t in enumerate(ths):
        rk, BIG = ring_keys(P, t, band_rows, k); allrings += [(len(r_), k, r_) for r_ in rk]
    total = sum(a for a, _, _ in allrings); keep = list(range(len(allrings)))
    if total > RING_BUDGET:
        order = sorted(range(len(allrings)), key=lambda i: -allrings[i][0]); keep = []; used = 0
        for i in order:
            sz = allrings[i][0]
            if used + sz > RING_BUDGET and keep: continue
            keep.append(i); used += sz
        keep.sort(); gone = len(allrings) - len(keep)
        if gone: notes.append(f'{gone} small contour rings (of {len(allrings)}) were left out of the drawing to keep it fast and small; the band cell counts and shares are exact.')
    rings = [[] for _ in ths]
    for i in keep:
        sz, k, keys = allrings[i]
        if sz > RING_BUDGET: dec = math.ceil(sz / RING_BUDGET); keys = keys[::dec]; notes.append(f'One ring of {sz} points was thinned to every {dec}th point.')
        rings[k].append(_drop_collinear(key_points(keys, P, BIG, ths[k], xy)))
    def build(dec):
        paths = ''.join(f'<path d="{_path(rg, dec)}" fill="{ramp[k]}" fill-rule="evenodd" stroke="{PAL[0]}" stroke-opacity=".35" stroke-width=".6"><title>Band {k}: {esc(fmt(ths[k - 1]))} and above</title></path>' for k, rg in enumerate(rings, 1))
        cid = 'c' + hashlib.sha1((paths + ''.join(ramp)).encode()).hexdigest()[:9]
        return (f'<defs><clipPath id="{cid}"><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}"/></clipPath></defs><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="{ramp[0]}"/>'
                f'<g clip-path="url(#{cid})">{paths}</g><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="none" stroke="{MUTED}" stroke-width="1"/>'), cid
    dec = 1; body, cid = build(1)
    while len(body) > 46000 and dec < 8: dec += 1; body, cid = build(dec)
    if dec > 1: notes.append(f'Rings were thinned to every {dec}th point to keep the drawing small.')
    ul = f' {u}' if u else ''
    if ttl: body += label(PX, 24, ttl, 18, 'start', weight=700)
    body += label(PX, 42, yl, 14, 'start')
    for x, v in xticks: body += f'<line x1="{x:.1f}" y1="{PY + PH}" x2="{x:.1f}" y2="{PY + PH + 5}" stroke="{MUTED}" stroke-width="1"/>' + label(x, PY + PH + 21, _lab(v), 14)
    for y, v in yticks: body += f'<line x1="{PX - 5}" y1="{y:.1f}" x2="{PX}" y2="{y:.1f}" stroke="{MUTED}" stroke-width="1"/>' + label(PX - 8, y + 5, _lab(v), 14, 'end')
    body += label(PX + PW / 2, PY + PH + 44, xl, 14)
    bname = lambda k: (f'below {fmt(ths[0])}' if k == 0 else f'{fmt(ths[k - 1])} to {fmt(ths[k])}' if k < n else f'{fmt(ths[-1])} and above') if n else 'all values'
    names = [f'{bname(k)}{ul}' for k in range(n + 1)]; cols = 3 if max(len(s) for s in names) <= 28 else 2; per = -(-(n + 1) // cols); cwid = PW / cols; ly0 = PY + PH + 62
    body += label(PX, ly0 - 2, f'{vl} bands (lowest first):', 14, 'start', weight=700)
    for k in range(n + 1):
        cx, ry = PX + (k // per) * cwid, ly0 + 8 + (k % per) * 22
        body += f'<rect x="{cx:.1f}" y="{ry}" width="14" height="14" fill="{ramp[k]}" stroke="{MUTED}" stroke-width=".5"/>' + label(cx + 20, ry + 12, names[k], 14, 'start')
    Hh = int(ly0 + 8 + per * 22 + 12)
    ncell = w * h; above = [sum(counts[k:]) for k in range(n + 1)]
    if gmode: share = [100.0 * a / ncell for a in above]; shname = 'cells'
    else:
        near = []
        for x, y in ppx:
            i = min(w - 1, max(0, int(round((x - PX) / cell)))); j = min(h - 1, max(0, int(round((y - PY) / cell)))); near.append(rows[j][i])
        share = [100.0 * sum(1 for q in near if k == 0 or q >= ths[k - 1]) / len(near) for k in range(n + 1)]; shname = 'points'
    lines = [f'{"Grid" if gmode else "Density grid"} {w} by {h} = {ncell} cells; {vl} range {fmt(lo)} to {fmt(hi)}{ul}.']
    if gmode: lines.insert(1, f'Columns are numbered 0 to {w} and rows 0 to {h}; cell i spans i to i+1.')
    if extra: lines.insert(0, extra)
    lines.append(f'{n} levels: {", ".join(fmt(t) for t in ths) if n else "none"}; {n + 1} bands.')
    lines += [f'Band {k}: {names[k]}: {counts[k]} cells; {fmt(round(share[k], 1))}% of {shname} at or above its lower level.' for k in range(n + 1)]
    if not gmode: lines.append('First points: ' + '; '.join(f'({fmt(x_)}, {fmt(y_)})' for x_, y_ in pts[:200]) + ('' if len(pts) <= 200 else f'; and {len(pts) - 200} more') + '.')
    table = ' '.join(lines)
    summary = f'{"Grid" if gmode else "Kernel density"} of {ncell} cells ({w} by {h}), {vl} {fmt(lo)} to {fmt(hi)}{ul}, drawn in {n + 1} bands at {n} levels ({", ".join(fmt(t) for t in ths) if n else "none"}); the most populated band is band {counts.index(max(counts))} with {max(counts)} cells.'
    res = finish('contour_plot', ttl, svg(body, 'Contour plot', W, Hh), summary, table, notes, u)
    res.update(thresholds=ths, counts=counts, rings=rings, cells=ncell, vmin=lo, vmax=hi, mode='grid' if gmode else 'points', box=(PX, PY, PW, PH), values=rows, ramp=ramp, clip_id=cid, shares=share, cell=cell, band_names=names)
    return {'contour': res, '_default': 'contour'}
