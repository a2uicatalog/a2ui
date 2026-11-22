"""brick_build: an isometric picture of a toy-brick model, on the Basic Catalog path. Input contract follows the atom brick_build_3d: bricks = objects {x, y, z, w, d, h, c} (x and z are stud positions, y the layer, w and d the footprint in studs,
h the height in bricks, default 1, c a '#rrggbb' colour or an index into palette) or compact arrays [x, y, z, w, d, c] / [x, y, z, w, d, h, c]. Also title, palette, base ('none' or '#rrggbb', default the classic green plate), studs (bool).
Draws one fixed isometric view (flat shading, dark outlines, round studs), back to front by a separating-plane order, and returns the complete model plus up to 3 cumulative build stages. Python also counts the parts, groups them into a parts list and checks the build
(overlaps, bricks with nothing under them, pieces not connected to the plate). No prices: the atom's indicative cost has no sourced price list here, so none is computed. Static: no orbit, no animation, no real LDraw parts.
Tolerant reader: unusable bricks are dropped and noted; more than 400 bricks are not drawn (the SVG size budget) and that is noted."""
import math, re, heapq
from .common import *
BH, PLATE = 1.2, 0.4                      # brick height and plate thickness, in stud pitches
MAX_DRAW, MAX_READ, BUDGET = 190, 3000, 68000      # BUDGET: estimated SVG bytes we allow ourselves (the output policy refuses 80,000)
POLY_B, STUD_B = 125, 270                           # measured: one polygon 117 to 125 bytes, one stud (two arc paths) about 264
INK_EDGE = '#1c1f2b'
DEFAULT_PALETTE = ['#c2182b', '#2f6fd8', '#f5c518', '#2e9e57', '#ee7b30', '#8a4fd0', '#e8e8ee', '#3b3f4a']
def _hex(c):
    c = c.strip().lower()
    if len(c) == 4: c = '#' + ''.join(ch * 2 for ch in c[1:])
    return c
def _rgb(c): c = _hex(c); return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
def _tone(c, f, mix=0.0):
    r, g, b = _rgb(c); out = []
    for v in (r, g, b): v = v * f; v = v + (255 - v) * mix; out.append(max(0, min(255, int(round(v)))))
    return '#%02x%02x%02x' % tuple(out)
def _colour(c, palette):
    if isinstance(c, bool): return None
    if isinstance(c, int) or (isinstance(c, float) and c == int(c)): return palette[int(c) % len(palette)] if palette else DEFAULT_PALETTE[int(c) % len(DEFAULT_PALETTE)]
    if isinstance(c, str) and re.fullmatch(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})', c.strip()): return _hex(c)
    return None
def _read(bricks, palette, notes):
    if not isinstance(bricks, list) or not bricks: raise ValueError('bricks must be a non-empty list')
    pal = []
    for p in (palette or [])[:256]:
        if isinstance(p, str) and re.fullmatch(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})', p.strip()): pal.append(_hex(p))
    out = []; bad = 0
    for i, b in enumerate(bricks[:MAX_READ]):
        try:
            if isinstance(b, dict): x, y, z, w, d, h, c = b.get('x'), b.get('y', 0), b.get('z'), b.get('w', 1), b.get('d', 1), b.get('h', 1), b.get('c')
            elif isinstance(b, (list, tuple)) and len(b) == 6: x, y, z, w, d, c = b; h = 1
            elif isinstance(b, (list, tuple)) and len(b) == 7: x, y, z, w, d, h, c = b
            else: raise ValueError
            vals = []
            for v in (x, y, z, w, d, h):
                f = finite(v)
                if f is None or f != int(f): raise ValueError
                vals.append(int(f))
            x, y, z, w, d, h = vals; col = _colour(c, pal)
            if col is None or not (-200 <= x <= 200 and -200 <= z <= 200 and 0 <= y <= 200 and 1 <= w <= 16 and 1 <= d <= 16 and 1 <= h <= 12): raise ValueError
            out.append((x, y, z, w, d, h, col))
        except Exception: bad += 1
    if bad: notes.append(f'{bad} brick{"s were" if bad != 1 else " was"} unusable (not whole numbers, out of range or no colour) and left out.')
    if len(bricks) > MAX_READ: notes.append(f'{len(bricks) - MAX_READ} bricks beyond the {MAX_READ}th were not read.')
    if not out: raise ValueError('no usable bricks')
    return out
def _check(B):
    """overlaps, bricks with nothing under them, pieces not connected to the plate. Cells are (x, layer, z) with studs and bricks as unit cells."""
    cell = {}; over = 0
    for i, (x, y, z, w, d, h, c) in enumerate(B):
        for xx in range(x, x + w):
            for zz in range(z, z + d):
                for yy in range(y, y + h):
                    if (xx, yy, zz) in cell: over += 1
                    else: cell[(xx, yy, zz)] = i
    sup = [set() for _ in B]; tops = [set() for _ in B]    # sup[i]: bricks directly under i; the plate counts as support at layer 0
    on_plate = [b[1] == 0 for b in B]
    for i, (x, y, z, w, d, h, c) in enumerate(B):
        if y == 0: continue
        for xx in range(x, x + w):
            for zz in range(z, z + d):
                j = cell.get((xx, y - 1, zz))
                if j is not None and j != i: sup[i].add(j); tops[j].add(i)
    floating = sum(1 for i in range(len(B)) if not on_plate[i] and not sup[i])
    seen = set(i for i in range(len(B)) if on_plate[i]); stack = list(seen)
    while stack:
        j = stack.pop()
        for i in tops[j]:
            if i not in seen: seen.add(i); stack.append(i)
        for i in sup[j]:
            if i not in seen: seen.add(i); stack.append(i)
    disconnected = len(B) - len(seen)
    return over, floating, disconnected
def _order(B):
    """Back to front. The viewer looks from +x, +z, above; box A is behind box B when a plane separates them with A on the lower side of x, z or y. Kahn's algorithm over those relations, ties by (x+z+y)."""
    n = len(B); box = [(x, x + w, y * BH, (y + h) * BH, z, z + d) for x, y, z, w, d, h, c in B]; after = [[] for _ in range(n)]; indeg = [0] * n
    for i in range(n):
        a = box[i]
        for j in range(i + 1, n):
            b = box[j]; ab = a[1] <= b[0] or a[5] <= b[4] or a[3] <= b[2]; ba = b[1] <= a[0] or b[5] <= a[4] or b[3] <= a[2]
            if ab and not ba: after[i].append(j); indeg[j] += 1
            elif ba and not ab: after[j].append(i); indeg[i] += 1
    key = lambda i: (box[i][0] + box[i][4] + box[i][2], i); order = []
    h = [(key(i), i) for i in range(n) if indeg[i] == 0]; heapq.heapify(h)
    while h:
        _, i = heapq.heappop(h); order.append(i)
        for j in after[i]:
            indeg[j] -= 1
            if indeg[j] == 0: heapq.heappush(h, (key(j), j))
    if len(order) < n: order += sorted((i for i in range(n) if i not in set(order)), key=key)
    return order
def _proj(x, y, z, s, ox, oy): return ox + (x - z) * 0.8660254 * s, oy + (x + z) * 0.5 * s - y * s
def _poly(pts, fill): return '<polygon points="' + ' '.join(f'{px:.1f},{py:.1f}' for px, py in pts) + f'" fill="{fill}" stroke="{INK_EDGE}" stroke-width="1.2"/>'
def _stud(cx, cy, s, top, side):
    rx = 0.3 * 0.866 * s * 1.15; ry = rx * 0.58; h = 0.16 * s
    e = lambda y, f: f'<path d="M{cx - rx:.1f} {y:.1f} A{rx:.1f} {ry:.1f} 0 1 0 {cx + rx:.1f} {y:.1f} A{rx:.1f} {ry:.1f} 0 1 0 {cx - rx:.1f} {y:.1f}Z" fill="{f}" stroke="{INK_EDGE}" stroke-width="0.8"/>'
    return e(cy, side) + e(cy - h, top)
def _drawn(B, base, studs, notes):
    """Full picture for these bricks as an SVG string. Base plate first (with its own studs), then the bricks in back-to-front order."""
    xs = [b[0] for b in B] + [b[0] + b[3] for b in B]; zs = [b[2] for b in B] + [b[2] + b[4] for b in B]; ys = [b[1] + b[5] for b in B]
    bx0, bx1, bz0, bz1 = min(xs) - 1, max(xs) + 1, min(zs) - 1, max(zs) + 1; top = max(ys) * BH
    pts = [_proj(x, y, z, 1, 0, 0) for x in (bx0, bx1) for z in (bz0, bz1) for y in (-PLATE, top + 0.2)]
    minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts); miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
    s = min(680 / max(maxx - minx, 1e-6), 400 / max(maxy - miny, 1e-6), 46.0); ox = 360 - (minx + maxx) / 2 * s; oy = 40 - miny * s
    P = lambda x, y, z: _proj(x, y, z, s, ox, oy); out = []; n = 0
    covered = {(xx, yy, zz) for x, y, z, w, d, h, c in B for xx in range(x, x + w) for zz in range(z, z + d) for yy in range(y, y + h)}
    brick_studs = sum(1 for x, y, z, w, d, h, c in B for xx in range(x, x + w) for zz in range(z, z + d) if (xx, y + h, zz) not in covered)
    plate_studs = sum(1 for xx in range(bx0, bx1) for zz in range(bz0, bz1) if (xx, 0, zz) not in covered) if base != 'none' else 0
    solid_b = POLY_B * 3 * (len(B) + (1 if base != 'none' else 0)); brick_on = studs; plate_on = studs
    if studs and solid_b + STUD_B * (brick_studs + plate_studs) > BUDGET: plate_on = False; notes.append('The studs on the base plate were left off to stay within the picture size limit.')
    if studs and solid_b + STUD_B * brick_studs > BUDGET: brick_on = False; notes.append('Studs were left off the bricks to stay within the picture size limit.')
    def solid(x0, x1, y0, y1, z0, z1, col, top_studs, plate=False):
        nonlocal n
        t, l, r = _tone(col, 1.0, 0.22), _tone(col, 0.86), _tone(col, 0.66)
        out.append(_poly([P(x1, y0, z0), P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0)], r)); out.append(_poly([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], l)); out.append(_poly([P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], t)); n += 3
        if top_studs:
            for xx in range(x0, x1):
                for zz in range(z0, z1):
                    if (xx, 0 if plate else int(round(y1 / BH)), zz) in covered: continue
                    cx, cy = P(xx + 0.5, y1, zz + 0.5); out.append(_stud(cx, cy, s, t, l)); n += 2
    if base != 'none': solid(bx0, bx1, -PLATE, 0, bz0, bz1, base, plate_on, True)
    for i in _order(B):
        x, y, z, w, d, h, c = B[i]; solid(x, x + w, y * BH, (y + h) * BH, z, z + d, c, brick_on)
    return ''.join(out), n
def _stages(B):
    layers = sorted({b[1] + b[5] - 1 for b in B}); top = max(b[1] + b[5] for b in B)
    k = min(3, max(top - 1, 0)); out = []
    for i in range(1, k + 1):
        cut = math.ceil(top * i / (k + 1)); sub = [b for b in B if b[1] < cut]
        if sub and len(sub) < len(B) and (not out or len(sub) != len(out[-1][1])): out.append((f'stage_{i}_of_{k + 1}', sub))
    return out
def brick_build(bricks, title='', palette=None, base='#2e9e57', studs=True, version=1):
    notes = []; B = _read(bricks, palette, notes)
    if version != 1: notes.append('Only version 1 exists; drawn as version 1.')
    if base != 'none' and not (isinstance(base, str) and re.fullmatch(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})', base.strip())): notes.append('base was not none or a colour; the green plate was used.'); base = '#2e9e57'
    base = base if base == 'none' else _hex(base); over, floating, disc = _check(B)
    if len(B) > MAX_DRAW: notes.append(f'{len(B) - MAX_DRAW} bricks beyond the {MAX_DRAW}th (lowest layers first) were not drawn: the picture would exceed its size limit.'); B = sorted(B, key=lambda b: (b[1], b[0], b[2]))[:MAX_DRAW]
    groups = {}
    for x, y, z, w, d, h, c in B: groups[(w, d, h, c)] = groups.get((w, d, h, c), 0) + 1
    parts = '; '.join(f'{n} x {w}x{d}' + (f'x{h}' if h != 1 else '') + f' brick {c}' for (w, d, h, c), n in sorted(groups.items(), key=lambda kv: (-kv[1], kv[0])))
    verdicts = [f'{over} overlapping cell{"s" if over != 1 else ""}' if over else 'no overlaps', f'{floating} brick{"s" if floating != 1 else ""} with nothing under {"them" if floating != 1 else "it"}' if floating else 'every upper brick has support', f'{disc} brick{"s" if disc != 1 else ""} not connected to the plate' if disc else 'everything is connected to the plate']
    layers = max(b[1] + b[5] for b in B); ttl = clean_text(title, 60, 'Brick model')
    summary = f'{len(B)} bricks in {layers} layer{"s" if layers != 1 else ""}, {len(groups)} different part{"s" if len(groups) != 1 else ""}. Build check: ' + ', '.join(verdicts) + '.'
    table = 'Parts list (count x width x depth [x height] brick colour): ' + parts + '.'
    res = {}
    def one(name, bs, extra=''):
        n2 = list(notes); body, _ = _drawn(bs, base, studs, n2)
        while len(body) > 76000 and len(bs) > 1:      # estimate too low for this model: drop studs first, then the highest bricks, until it fits
            if studs: studs_now = False
            n2.append('The picture was reduced to fit the size limit.') if 'The picture was reduced to fit the size limit.' not in n2 else None
            bs = sorted(bs, key=lambda b: (b[1], b[0], b[2]))[:max(1, int(len(bs) * 0.85))]; body, _ = _drawn(bs, base, False, n2)
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="480" viewBox="0 0 720 480" role="img" aria-label="Isometric brick model">{body}</svg>'
        res[name] = finish('brick_build', ttl, svg, (extra + ' ' if extra else '') + summary, table, n2)
    one('complete', B)
    for name, sub in _stages(B): one(name, sub, f'{name.replace("_", " ").capitalize()}: the first {len(sub)} bricks, up to layer {max(b[1] + b[5] for b in sub)}.')
    res['_default'] = 'complete'; return res
