"""voronoi macro: same contract as the voronoi atom (sites [{x,y,label,group,value}] 3..200, title, x_label, y_label, unit, version).
Each region is the plot box clipped by the perpendicular-bisector half-plane against every other site (O(n^2), pure Python, exact up to float rounding); the regions tile the box.
The diagram is computed in DATA units: coordinates are shifted to the box corner and divided by ONE common scale (the larger of the two spans), so distances keep their ratios and every
region is the set of points nearest to its site in the x and y units of the data, also when the drawing is stretched to fit the plot (the atom: 600 wide, as high as the shape asks, kept
between a third of the width and the full width; then the x and y scales differ and a note says so). Bounds = the sites' extent plus 5% each side, niced to round numbers.
A span below 1e-12 of the coordinates' size counts as zero width (the sites are in a line on that axis); if both do, the sites count as one position. Region polygons come from clipping,
not from d3-delaunay. Fewer than 3 sites at different positions gives a note-only Result (the atom: a note instead of the chart). Returns {'voronoi': Result, '_default': 'voronoi'}."""
import math
from .common import *
from .waterfall import note_result
X0, Y0, PW = 60.0, 72.0, 600.0
TINY = 1e-12
def _nice_step(span):
    raw = span / 5.0; e = math.floor(math.log10(raw)); f = raw / 10 ** e
    return (1 if f <= 1 else 2 if f <= 2 else 5 if f <= 5 else 10) * 10 ** e
def _bounds(lo, hi, other):
    """(lo, hi, step) of the plot on one axis: widened if flat, plus 5% each side, niced. `other` is the other axis' span (used for a flat axis)."""
    if hi - lo <= 0: m = other if other > 0 else 1.0; lo, hi = lo - m / 2, hi + m / 2
    pad = (hi - lo) * 0.05; lo -= pad; hi += pad; st = _nice_step(hi - lo)
    return math.floor(lo / st + 1e-9) * st, math.ceil(hi / st - 1e-9) * st, st
def clip(poly, a, b, c):
    """Keep the part of the polygon with a*x + b*y <= c (Sutherland-Hodgman against one half-plane)."""
    out = []; m = len(poly)
    for i in range(m):
        p, q = poly[i], poly[(i + 1) % m]; fp = a * p[0] + b * p[1] - c; fq = a * q[0] + b * q[1] - c
        if fp <= 0: out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq); out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out
def area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2 if len(poly) >= 3 else 0.0
def cells(pts, box):
    """Voronoi cells of points inside box = (x0, y0, x1, y1), in the points' own (isotropic) units. One polygon per point ([] when the point has no region of its own)."""
    x0, y0, x1, y1 = box; out = []
    for i, s in enumerate(pts):
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for j, t in enumerate(pts):
            if i == j: continue
            if abs(t[0] - s[0]) < 1e-15 and abs(t[1] - s[1]) < 1e-15:
                if j < i: poly = []
                continue
            poly = clip(poly, t[0] - s[0], t[1] - s[1], (t[0] ** 2 + t[1] ** 2 - s[0] ** 2 - s[1] ** 2) / 2)
            if not poly: break
        out.append(poly)
    return out
def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)); return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
def _ticks(lo, hi, st):
    """Tick values lo, lo+st, ... up to hi: the count comes from (hi-lo)/st with a relative tolerance and is capped, so it always ends."""
    cnt = min(20, int(math.floor((hi - lo) / st * (1 + 1e-9) + 1e-9)))
    return [float(f'{lo + i * st:.12g}') for i in range(cnt + 1)]
def voronoi(sites, title='', x_label='', y_label='', unit='', version=1):
    notes = []; ttl = ident(title, 80) or ''; xl = ident(x_label, 30) or ''; yl = ident(y_label, 30) or ''; u = ident(unit, 12) or ''
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10 ** 9)} is drawn as version 1.')
    if not isinstance(sites, list): notes.append('sites must be a list.'); return {'voronoi': note_result('voronoi', ttl, 'The sites were not a list, so there is nothing to draw.', notes), '_default': 'voronoi'}
    if len(sites) > 200: notes.append(f'{len(sites) - 200} sites beyond the 200th were not used.'); sites = sites[:200]
    S = []; bad = 0; merged = 0; at = {}
    for i, d in enumerate(sites):
        x = finite(d.get('x')) if isinstance(d, dict) else None; y = finite(d.get('y')) if isinstance(d, dict) else None
        if x is None or y is None: bad += 1; continue
        if (x, y) in at: merged += 1; continue
        v = finite(d.get('value')); at[(x, y)] = len(S)
        S.append({'x': x, 'y': y, 'label': ident(d.get('label'), 24) or f'Site {i + 1}', 'group': ident(d.get('group'), 20), 'value': v})
    if bad: notes.append(f'{bad} entries were left out (not an object with finite numeric x and y).')
    if merged: notes.append(f'{merged} sites at the same position as an earlier site were merged into it.')
    xs = [s['x'] for s in S]; ys = [s['y'] for s in S]
    flat = lambda v: max(v) - min(v) <= TINY * max(abs(min(v)), abs(max(v)))
    fx, fy = (flat(xs), flat(ys)) if S else (True, True)
    dx, dy = (0.0 if fx else max(xs) - min(xs)), (0.0 if fy else max(ys) - min(ys))
    if len(S) < 3 or max(dx, dy) < 1e-200:
        why = 'A voronoi diagram needs at least 3 sites at different positions.'; notes.append(why)
        return {'voronoi': note_result('voronoi', ttl, why + ' Nothing was drawn.', notes), '_default': 'voronoi'}
    xlo, xhi, xst = _bounds(min(xs), max(xs) if not fx else min(xs), dy); ylo, yhi, yst = _bounds(min(ys), max(ys) if not fy else min(ys), dx)
    D = max(xhi - xlo, yhi - ylo); bw, bh = (xhi - xlo) / D, (yhi - ylo) / D
    ph = PW * (yhi - ylo) / (xhi - xlo)
    if not PW / 3 <= ph <= PW: ph = min(PW, max(PW / 3, ph)); notes.append('The plot height is clamped to between a third and the full width, so the x and y scales differ (the regions are still the nearest-site regions in the data units).')
    uv = [((s['x'] - xlo) / D, (s['y'] - ylo) / D) for s in S]; polys = cells(uv, (0.0, 0.0, bw, bh)); total = bw * bh
    px = lambda u_: X0 + u_ / bw * PW; py = lambda v_: Y0 + ph - v_ / bh * ph
    for s, p, poly in zip(S, uv, polys):
        s['px'], s['py'] = px(p[0]), py(p[1]); s['poly'] = [(px(a), py(b)) for a, b in poly]; s['share'] = area(poly) / total; s['area'] = s['share'] * (xhi - xlo) * (yhi - ylo)
    zero = [s['label'] for s in S if s['share'] * 100 < 0.05]
    if zero: notes.append(f'{len(zero)} sites have no region of their own (shown as 0.0%): ' + ', '.join(zero[:5]) + '.')
    groups = sorted({s['group'] for s in S if s['group']}); gcol = {g: PAL[i % len(PAL)] for i, g in enumerate(groups)}
    box = (X0, Y0, X0 + PW, Y0 + ph); h = int(Y0 + ph + 84); body = label(W / 2, 32, ttl, 20, weight=700) if ttl else ''
    if yl: body += label(X0, Y0 - 12, yl, 14, 'start', MUTED)
    body += f'<g stroke="{INK}" stroke-width="1.5" stroke-linejoin="round">'
    for s in S:
        c = blend(gcol[s['group']], .72) if s['group'] else blend(PAL[0], .88); s['fill'] = c
        if s['poly']:
            d = 'M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in s['poly']) + 'Z'; tip = f'{s["label"]}: {s["share"]*100:.1f}% of the area' + (f', value {fmt(s["value"])}{(" " + u) if u else ""}' if s['value'] is not None else '')
            body += f'<path d="{d}" fill="{c}"><title>{esc(tip)}</title></path>'
    body += '</g>'
    for t in _ticks(xlo, xhi, xst): body += label(X0 + (t - xlo) / (xhi - xlo) * PW, Y0 + ph + 20, fmt(t), 14, fill=MUTED)
    for t in _ticks(ylo, yhi, yst): body += label(X0 - 8, Y0 + ph - (t - ylo) / (yhi - ylo) * ph + 5, fmt(t), 14, 'end', MUTED)
    body += f'<rect x="{X0}" y="{Y0}" width="{PW}" height="{ph:.2f}" fill="none" stroke="{MUTED}" stroke-width="1.5"/>'
    for s in S:
        body += f'<circle cx="{s["px"]:.2f}" cy="{s["py"]:.2f}" r="4.5" fill="{INK}" stroke="{FACE}" stroke-width="1.5"/>'
        if s['poly']:
            m = len(s['poly']); near = min(_seg_dist((s['px'], s['py']), s['poly'][i], s['poly'][(i + 1) % m]) for i in range(m)); s['shown'] = 2 * near >= len(s['label']) * 7.8 + 4 and near >= 12
        else: s['shown'] = False
        if s['shown']: body += label(s['px'], s['py'] + 20, s['label'], 14)
    if xl: body += label(X0 + PW / 2, Y0 + ph + 44, xl, 14, fill=MUTED)
    if groups:
        x = X0
        for g in groups: body += f'<rect x="{x:.0f}" y="{h-30}" width="16" height="16" rx="3" fill="{blend(gcol[g], .72)}" stroke="{INK}"/>' + label(x + 22, h - 17, g, 14, 'start'); x += 40 + len(g) * 8
    tab = '; '.join(f'{s["label"]} at x {fmt(s["x"])}, y {fmt(s["y"])}' + (f', group {s["group"]}' if s['group'] else '') + (f', value {fmt(s["value"])}{(" " + u) if u else ""}' if s['value'] is not None else '') + f', {s["share"]*100:.1f}% of the area' for s in S)
    big = max(S, key=lambda s: s['area']); summary = f'{len(S)} sites, {len(groups)} groups; the largest region is {big["label"]} ({big["share"]*100:.1f}% of the area).'
    res = finish('voronoi', ttl, svg(body, 'Voronoi regions', W, h), summary, tab, notes, u)
    res['sites'] = S; res['box'] = box; res['bounds'] = (xlo, xhi, ylo, yhi); res['size'] = (W, h); res['ticks'] = (xst, yst); res['data_area'] = (xhi - xlo) * (yhi - ylo)
    return {'voronoi': res, '_default': 'voronoi'}
