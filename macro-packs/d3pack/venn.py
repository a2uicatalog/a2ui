"""venn macro: area-proportional two- and three-set Venn diagram.
CONTRACT. atoms/schema.yaml (the three-set fields are in the current copy) has a `venn_diagram` atom, but it is conceptual (two circles NOT proportional to size, up to four text items per region: set_a_name, set_b_name,
set_a_exclusive, set_b_exclusive, intersection). A proportional Venn needs numbers, so this macro defines its own input (this is NOT the atom's contract):
    sets     = [{name (max 28), size (number above 0)}]   2 or 3 sets (more are cut with a note)
    overlaps = [{sets: [name, name], size}]               size = |A and B| INCLUDING any triple overlap; a missing pair is 0
    triple   = optional |A and B and C| (only used to compare with what the drawing gives)
    unit, title, version
For convenience the atom's own fields (set_a_name, set_b_name, set_a_exclusive, set_b_exclusive, intersection and, for three sets, set_c_name, set_c_exclusive, intersection_ac, intersection_bc, intersection_abc; intersection = A and B only) are also accepted when `sets` is not given: the sizes are then the
item counts (A = exclusive + intersection, ...), each pair overlap is its own region plus the all-three region (triple = intersection_abc count), and the items are listed in the table.
GEOMETRY. Circle areas are proportional to the sizes (r = sqrt(size / pi), in data units, then one common scale to pixels). Two circles: the distance d between centres is found by bisection
so that the lens (intersection) area, from the closed form, equals the overlap. Three circles: the same pairwise solution for each of the three pairs; the centres are then placed by the law of
cosines (C on the upper side of AB). The three pairwise overlaps are exact; the triple overlap is whatever that geometry gives (estimated on a 300 x 300 sample grid) and is reported next to the
request: it is approximate, and a region such as 'A and B only' can be off if the three distances do not make a triangle (then C is placed on the line and the note says so).
Returns {'venn': Result, '_default': 'venn'}. Result carries the numbers used: radii (data units), centres (px), drawn pair areas and the drawn triple estimate."""
import math
from .common import *
def lens_area(r1, r2, d):
    """Area of the intersection of two circles with radii r1, r2 and centre distance d (closed form)."""
    if d >= r1 + r2: return 0.0
    if d <= abs(r1 - r2): return math.pi * min(r1, r2) ** 2
    a = r1 * r1 * math.acos(max(-1, min(1, (d * d + r1 * r1 - r2 * r2) / (2 * d * r1)))) + r2 * r2 * math.acos(max(-1, min(1, (d * d + r2 * r2 - r1 * r1) / (2 * d * r2))))
    return a - .5 * math.sqrt(max(0, (-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2)))
def solve_distance(r1, r2, target, iters=80):
    """Centre distance at which the lens area equals `target` (bisection; the lens area falls as d grows)."""
    lo, hi = abs(r1 - r2), r1 + r2
    if target <= 0: return hi
    if target >= math.pi * min(r1, r2) ** 2 - 1e-12: return lo
    for _ in range(iters):
        mid = (lo + hi) / 2
        if lens_area(r1, r2, mid) > target: lo = mid
        else: hi = mid
    return (lo + hi) / 2
def _text(x, n, default=None):
    """clean_text that cannot overflow: an int too big for a float (10**400) is not text."""
    if isinstance(x, (int, float)) and not isinstance(x, bool) and finite(x, -1e15, 1e15) is None: return default
    return clean_text(x, n, default)
def _rd(x): return x if abs(x - round(x)) > 1e-9 else round(x)
def grid_regions(pos, R, xs0, xs1, ys0, ys1, N=300):
    """Sample-count of every region (tuple of the circles that contain the point) on an N x N grid of cell centres over the bounding box; returns (counts, centroid sums of the 'A and B' region of a two-circle picture)."""
    k = len(pos); cnt = {}; cen = {}; dx = (xs1 - xs0) / N; dy = (ys1 - ys0) / N
    # Same predicate, same float arithmetic and same visiting order (column by column, top to bottom) as testing all 300 x 300 sample points, but per column each circle's run of
    # inside points is found by bisection: dx^2 + (py - cy)^2 is a valley in b, so 'inside' is one unbroken run. Counts, dict order and the float sums of the one centroid that is drawn are bit-identical.
    pys = [ys0 + (b + .5) * dy for b in range(N)]; R2 = [r * r for r in R]; idx = range(k)
    cys = [[(py - pos[i][1]) ** 2 for py in pys] for i in idx]; bmin = [v.index(min(v)) for v in cys]
    for a in range(N):
        px = xs0 + (a + .5) * dx; runs = []
        for i in idx:
            dx2 = (px - pos[i][0]) ** 2; v = cys[i]; r2 = R2[i]; m0 = bmin[i]
            if dx2 + v[m0] > r2: continue
            lo, hi = 0, m0                  # first inside index in [0, m0]
            while lo < hi:
                mid = (lo + hi) // 2
                if dx2 + v[mid] <= r2: hi = mid
                else: lo = mid + 1
            first = lo; lo, hi = m0, N - 1  # last inside index in [m0, N - 1]
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if dx2 + v[mid] <= r2: lo = mid
                else: hi = mid - 1
            runs.append((i, first, lo + 1))
        if not runs: continue
        cuts = sorted({x for _, f, e in runs for x in (f, e)})
        for s0, s1 in zip(cuts, cuts[1:]):
            m = tuple(i for i, f, e in runs if f <= s0 < e)
            if not m: continue
            cnt[m] = cnt.get(m, 0) + (s1 - s0)
            if k == 2 and m == (0, 1):
                c = cen.setdefault(m, [0.0, 0.0])
                for b in range(s0, s1): c[0] += px; c[1] += pys[b]
    return cnt, cen
def venn(sets=None, overlaps=None, triple=None, unit='', title='', version=1, set_a_name=None, set_b_name=None, set_a_exclusive=None, set_b_exclusive=None, intersection=None, set_c_name=None, set_c_exclusive=None, intersection_ac=None, intersection_bc=None, intersection_abc=None):
    notes = []; u = _text(unit, 12, '') or ''; ttl = _text(title, 80, '') or ''; items = None
    ver = finite(version)
    if ver is not None and ver > 1: notes.append(f'Contract version {fmt(ver)} is drawn as version 1.')
    if sets is None and set_a_name is not None:
        def li(x):
            """(first 60 usable items, number of usable items): sizes use the real count, the table shows up to 60 and '+n more'."""
            allv = [t for t in (_text(i, 28) for i in (x if isinstance(x, list) else [])) if t]; return allv[:60], len(allv)
        (ea, nea), (eb, neb), (ix, nix) = li(set_a_exclusive), li(set_b_exclusive), li(intersection); na = _text(set_a_name, 28); nb = _text(set_b_name, 28)
        if not na or not nb: raise ValueError('set_a_name and set_b_name are required')
        nc = _text(set_c_name, 28) if set_c_name is not None else None
        txt = lambda lst, tot: (", ".join(lst) + (f', +{tot - len(lst)} more' if tot > len(lst) else '')) or 'none'
        if nc is None:
            sets = [{'name': na, 'size': nea + nix}, {'name': nb, 'size': neb + nix}]; overlaps = [{'sets': [na, nb], 'size': nix}]
            items = f'Only {na}: {txt(ea, nea)}. Only {nb}: {txt(eb, neb)}. Both: {txt(ix, nix)}.'
        else:
            (ec, nec), (ac, nac), (bc, nbc), (abc, nabc) = li(set_c_exclusive), li(intersection_ac), li(intersection_bc), li(intersection_abc)
            sets = [{'name': na, 'size': nea + nix + nac + nabc}, {'name': nb, 'size': neb + nix + nbc + nabc}, {'name': nc, 'size': nec + nac + nbc + nabc}]
            overlaps = [{'sets': [na, nb], 'size': nix + nabc}, {'sets': [na, nc], 'size': nac + nabc}, {'sets': [nb, nc], 'size': nbc + nabc}]; triple = nabc
            items = f'Only {na}: {txt(ea, nea)}. Only {nb}: {txt(eb, neb)}. Only {nc}: {txt(ec, nec)}. {na} and {nb} only: {txt(ix, nix)}. {na} and {nc} only: {txt(ac, nac)}. {nb} and {nc} only: {txt(bc, nbc)}. All three: {txt(abc, nabc)}.'
        notes.append('Sizes are the item counts of the atom fields; the circles are drawn proportional to them (the atom itself is conceptual).')
    if not isinstance(sets, list): raise ValueError('sets must be a list of {name, size}')
    S = []; dropped = 0
    for s in sets:
        nm = _text(s.get('name'), 28) if isinstance(s, dict) else None
        sz = finite(s.get('size'), 0, 1e12) if isinstance(s, dict) else None
        if nm is None or sz is None or nm in [x['name'] for x in S]: dropped += 1; continue
        S.append({'name': nm, 'size': sz})
    if dropped: notes.append(f'{dropped} sets were left out (no name, a repeated name, or a size that is not a number of 0 or more, up to 1e12).')
    if len(S) > 3: notes.append(f'{len(S) - 3} sets beyond the 3rd were not drawn (two or three sets only).'); S = S[:3]
    if len(S) < 2: raise ValueError('a Venn diagram needs at least 2 usable sets')
    if not any(x['size'] > 0 for x in S): raise ValueError('every set is empty; there is nothing to draw')
    empty = [x['name'] for x in S if x['size'] == 0]
    if empty: notes.append('Empty set' + ('s' if len(empty) > 1 else '') + ' ' + ', '.join(empty) + ' (size 0) drawn as a small marker, not to scale.')
    names = [s['name'] for s in S]; k = len(S); ov = {}; badov = 0
    for o in (overlaps if isinstance(overlaps, list) else []):
        pr = o.get('sets') if isinstance(o, dict) else None
        if not (isinstance(pr, list) and len(pr) == 2 and all(p in names for p in pr) and pr[0] != pr[1]) or finite(o.get('size'), 0, 1e12) is None: badov += 1; continue
        key = tuple(sorted((names.index(pr[0]), names.index(pr[1]))))
        if key in ov: badov += 1; continue
        ov[key] = finite(o['size'], 0, 1e12)
    if badov: notes.append(f'{badov} overlaps were dropped (needs two different set names, a size of 0 or more, and each pair once).')
    for key in sorted(ov):
        m = min(S[key[0]]['size'], S[key[1]]['size'])
        if ov[key] > m: notes.append(f'Overlap {names[key[0]]} and {names[key[1]]} was clamped from {fmt(ov[key])} to {fmt(m)} (it cannot exceed the smaller set).'); ov[key] = m
    pairs = [(i, j) for i in range(k) for j in range(i + 1, k)]
    for p in pairs: ov.setdefault(p, 0.0)
    tri = None
    if triple is not None:
        if k < 3: notes.append('triple was ignored (it needs three sets).')
        elif finite(triple, 0, 1e12) is None: notes.append('triple was ignored (needs a number of 0 or more).')
        else:
            tri = finite(triple, 0, 1e12); cap = min(ov[p] for p in pairs)
            if tri > cap: notes.append(f'triple was clamped from {fmt(tri)} to {fmt(cap)} (it cannot exceed the smallest pair overlap).'); tri = cap
    R = [math.sqrt(s['size'] / math.pi) for s in S]; D = {p: solve_distance(R[p[0]], R[p[1]], ov[p]) for p in pairs}
    pos = [(0.0, 0.0), (D[(0, 1)], 0.0)]
    if k == 3:
        d01, d02, d12 = D[(0, 1)], D[(0, 2)], D[(1, 2)]
        cx = (d01 * d01 + d02 * d02 - d12 * d12) / (2 * d01) if d01 > 1e-12 else d02
        cy2 = d02 * d02 - cx * cx
        if cy2 < -1e-9:
            notes.append('The three pairwise distances do not form a triangle; the third circle is placed on the line, so some pair overlaps are drawn off. Treat the picture as approximate.')
        pos.append((cx, -math.sqrt(max(0, cy2))))   # negative y = up on screen
    xs0 = min(p[0] - r for p, r in zip(pos, R)); xs1 = max(p[0] + r for p, r in zip(pos, R)); ys0 = min(p[1] - r for p, r in zip(pos, R)); ys1 = max(p[1] + r for p, r in zip(pos, R))
    bx, by, bw, bh = 60, 70, 600, 360; f = min(bw / (xs1 - xs0), bh / (ys1 - ys0)); ox = bx + (bw - f * (xs1 - xs0)) / 2 - f * xs0; oy = by + (bh - f * (ys1 - ys0)) / 2 - f * ys0
    C = [(ox + f * p[0], oy + f * p[1]) for p in pos]; Rp = [f * r for r in R]; Rd = [max(x, 5.0) if S[i]['size'] == 0 else x for i, x in enumerate(Rp)]   # empty sets get a 5 px marker
    drawn = {p: lens_area(R[p[0]], R[p[1]], math.hypot(pos[p[0]][0] - pos[p[1]][0], pos[p[0]][1] - pos[p[1]][1])) for p in pairs}
    # region estimate on a fixed 300 x 300 grid over the bounding box (data units)
    N = 300; dx = (xs1 - xs0) / N; dy = (ys1 - ys0) / N; cnt, cen = grid_regions(pos, R, xs0, xs1, ys0, ys1, N)
    reg = {m: n_ * dx * dy for m, n_ in cnt.items()}; drawn_triple = reg.get((0, 1, 2), 0.0) if k == 3 else None
    body = ''
    for i in range(k): body += f'<circle cx="{C[i][0]:.2f}" cy="{C[i][1]:.2f}" r="{Rd[i]:.2f}" fill="{PAL[i]}" fill-opacity=".4" stroke="{PAL[i]}" stroke-width="2"><title>{esc(names[i])}: {fmt(S[i]["size"])}{esc(" " + u) if u else ""}</title></circle>'
    mid = (sum(c[0] for c in C) / k, sum(c[1] for c in C) / k)
    for i in range(k):
        ang = math.atan2(C[i][1] - mid[1], C[i][0] - mid[0]) if (k == 3 or True) else 0
        if k == 2: ang = math.pi if i == 0 else 0.0
        lx = C[i][0] + (Rd[i] + 8) * math.cos(ang); ly = C[i][1] + (Rd[i] + 8) * math.sin(ang); anchor = 'end' if math.cos(ang) < -.3 else 'start' if math.cos(ang) > .3 else 'middle'
        ly += 14 if math.sin(ang) > .5 else -6 if math.sin(ang) < -.5 else 5
        lx = min(W - 12, max(12, lx)); ly = min(H - 60, max(70, ly))
        body += label(lx, ly, f'{names[i]} ({fmt(S[i]["size"])}{(" " + u) if u else ""})', 16, anchor, weight=700)
    if k == 2 and (0, 1) in cen:
        c = cen[(0, 1)]; body += label(ox + f * c[0] / cnt[(0, 1)], oy + f * c[1] / cnt[(0, 1)] + 5, fmt(ov[(0, 1)]), 16, weight=700)
    if ttl: body += label(bx, 36, ttl, 18, 'start', weight=700)
    body += label(W / 2, 500, f'Circle areas are proportional to the sizes{" (triple overlap approximate)" if k == 3 else ""}.', 14, fill=MUTED)
    uu = (' ' + u) if u else ''
    lines = [f'{k} sets, areas in {u or "data units"}: ' + '; '.join(f'{n_} {fmt(s["size"])}{uu}' for n_, s in zip(names, S)) + '.']
    for p in pairs: lines.append(f'Overlap {names[p[0]]} and {names[p[1]]}: requested {fmt(ov[p])}{uu}, drawn {fmt(round(drawn[p], 4))}{uu}.')
    if k == 3:
        lines.append(f'Overlap of all three: drawn about {fmt(round(drawn_triple, 2))}{uu} (estimate, approximate)' + (f', requested {fmt(tri)}{uu}.' if tri is not None else ', none requested.'))
    if items: lines.append(items)
    table = ' '.join(lines)
    summary = f'{k} sets drawn with area proportional to size: ' + ', '.join(f'{n_} {fmt(s["size"])}' for n_, s in zip(names, S)) + '; ' + '; '.join(f'{names[p[0]]} and {names[p[1]]} overlap {fmt(ov[p])}' for p in pairs) + ('; the triple overlap is approximate.' if k == 3 else '.')
    res = finish('venn', ttl, svg(body, 'Venn diagram'), summary, table, notes, u)
    res.update(names=names, sizes=[s['size'] for s in S], radii=R, centres=C, radii_px=Rp, distances=D, overlaps=ov, drawn_overlaps=drawn, drawn_triple=drawn_triple, requested_triple=tri, scale=f, regions=reg)
    return {'venn': res, '_default': 'venn'}
