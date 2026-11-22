"""beeswarm macro. NO beeswarm atom exists in a2uicatalog's schema.yaml (checked), so this contract is ours:
  groups  [{name, values:[number]}] up to 8 (or `values` alone = one lane), up to 400 points per group and 800 overall
  unit, title, version
One lane per group, the value on a shared horizontal axis. Placement is deterministic, no force simulation: points are taken in ascending value (ties by input order); each sits at its
exact x and takes the offset nearest the lane centre (ties: below the centre) that keeps a gap of 1 px to every placed circle. If a lane would overflow, the radius shrinks
(6 down to 2.5 px); if it still overflows, the points that do not fit are not drawn and are counted in the notes. Returns {'swarm': Result}."""
import math
from .common import *
from .histogram import groups_in, nice_edges, ctext
def _free(iv):
    """Nearest-to-0 y that lies in none of the open intervals iv (ties: the positive one). Merge, then look only at the merged interval holding 0."""
    for a_, b_ in _merge(iv):
        if a_ + 1e-9 < 0 < b_ - 1e-9: return min((a_, b_), key=lambda v: (abs(v), -v))
    return 0.0
def _merge(iv):
    out = []
    for a_, b_ in sorted(iv):
        if out and a_ < out[-1][1] - 1e-9: out[-1][1] = max(out[-1][1], b_)
        else: out.append([a_, b_])
    return out
def place(xs, r, half, gap=1.0):
    """Deterministic swarm. xs = x positions (any order). Returns {index: y offset, or None for a point that does not fit}. Points are bucketed by x (cell width = the collision distance), so
    each point looks only at its neighbours; the blocked y intervals of the neighbours are merged and the free y nearest the lane centre is taken (O(k log k) per point, k neighbours)."""
    d = 2 * r + gap; cells = {}; ys = {}
    for i in sorted(range(len(xs)), key=lambda j: (xs[j], j)):
        x = xs[i]; c = math.floor(x / d); iv = []
        for cc in (c - 1, c, c + 1):
            for px_, py_ in cells.get(cc, ()):
                dx = abs(px_ - x)
                if dx < d: dy = math.sqrt(max(0.0, d * d - dx * dx)); iv.append((py_ - dy, py_ + dy))
        y = _free(iv)
        if abs(y) > half: ys[i] = None
        else: ys[i] = y; cells.setdefault(c, []).append((x, y))
    return ys
def beeswarm(groups=None, values=None, unit='', title='', version=1, **extra):
    notes = []; u = ctext(unit, 12, '') or ''; ttl = ctext(title, 80, '') or ''
    gs = groups_in(groups, values, notes, 8, 'Values')
    if not gs: raise ValueError('a beeswarm needs at least one group with a finite number')
    budget = 800
    for g in gs:
        keep = min(len(g['values']), 400, budget)
        if keep < len(g['values']): notes.append(f'{g["name"]}: {len(g["values"]) - keep} of {len(g["values"])} points were not drawn (limit 400 per group, 800 overall); the table still has the group summary.')
        g['drawn'] = g['values'][:keep]; budget -= keep
    gs = [g for g in gs if g['drawn']]
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {version} is drawn as version 1.')
    allv = [v for g in gs for v in g['values']]; ed = nice_edges(min(allv), max(allv), 6); dlo, dhi = ed[0], ed[-1]
    L, R, T = 120, 24, 24; B = 62 if u else 46; pw, ph = W - L - R, H - T - B; lane = ph / len(gs); half = lane / 2 - 3; sx = lambda v: L + (v - dlo) / (dhi - dlo) * pw
    body = ''
    for e in ed[::max(1, math.ceil(len(ed) / 9))]: body += f'<line x1="{sx(e):.2f}" x2="{sx(e):.2f}" y1="{T}" y2="{T + ph}" stroke="#e3e6f2" stroke-width="1.5"/>' + label(sx(e), T + ph + 22, fmt(e), 14, 'middle', MUTED)
    radii = []; hidden = 0; rows = []; lanes = []
    for i, g in enumerate(gs):
        c = T + lane * (i + .5); xs = [sx(v) for v in g['drawn']]; r = 6.0
        while True:
            ys = place(xs, r, half)
            if all(y is not None for y in ys.values()) or r <= 2.5: break
            r -= .5
        miss = sum(1 for y in ys.values() if y is None); hidden += miss
        if miss: notes.append(f'{g["name"]}: {miss} points did not fit the lane at the smallest circle size and were not drawn (the table has all counts).')
        if r < 6: notes.append(f'{g["name"]}: circles were shrunk to {fmt(r)} px radius to fit.')
        radii.append(r); col = PAL[i % len(PAL)]; body += label(L - 10, c + 5, g['name'][:14], 14, 'end') + f'<line x1="{L}" x2="{W - R}" y1="{c:.2f}" y2="{c:.2f}" stroke="#c9cde0" stroke-width="1"/>'
        lanes.append((i, c, col, r, [(xs[j], ys[j], g['drawn'][j]) for j in sorted(ys, key=lambda j: (g['drawn'][j], j)) if ys[j] is not None]))
        s = sorted(g['values']); n = len(s); med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        rows.append(f'{g["name"]}: n {n}, min {fmt(s[0])}, median {fmt(med)}, max {fmt(s[-1])}' + (', values ' + ', '.join(fmt(v) for v in s) if n <= 15 else '') + '.')
    foot = f'<line x1="{L}" x2="{W - R}" y1="{T + ph}" y2="{T + ph}" stroke="{INK}" stroke-width="2"/>' + (label(L + pw / 2, H - 12, u, 14, 'middle', INK) if u else '')
    def circles_svg(level):
        out = ''
        for i, c, col, r, pts in lanes:
            out += f'<g fill="{col}" fill-opacity=".85" stroke="{INK}" stroke-width="1" data-lane="{i}">'
            for x, y, v in pts: out += f'<circle cx="{x:.2f}" cy="{c + y:.2f}" r="{r}"><title>{fmt(v)}</title></circle>' if level == 0 else f'<circle cx="{x:.1f}" cy="{c + y:.1f}" r="{r}"/>'
            out += '</g>'
        return out
    drawing = svg(body + circles_svg(0) + foot, 'Beeswarm')
    if len(drawing) > 70_000: drawing = svg(body + circles_svg(1) + foot, 'Beeswarm'); notes.append('Tooltips were left out and coordinates rounded to 0.1 px to keep the drawing small; the table has every value.')
    tab = 'One circle per value, placed at its exact position along the axis. ' + ' '.join(rows)
    summary = f'{len(gs)} groups, {len(allv):,} values from {fmt(min(allv))} to {fmt(max(allv))}{(" " + u) if u else ""}.' + (f' {hidden} points could not be placed.' if hidden else '')
    r = finish('beeswarm', ttl, drawing, summary, tab, notes, u); r['domain'] = (dlo, dhi); r['radii'] = radii; r['lane'] = lane; r['names'] = [g['name'] for g in gs]
    return {'swarm': r, '_default': 'swarm'}
