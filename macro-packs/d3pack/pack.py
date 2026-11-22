"""circle_pack macro: same contract as the circle_pack atom (items [{path, name, value}], unit, title, version). Own deterministic packing (NOT d3.pack): circles of
radius proportional to sqrt(value), placed one by one (largest first) at the position tangent to two placed circles (or to one) that does not overlap and lies closest to
the group's centroid; each group is the minimal enclosing circle of its children plus padding, packed the same way one level up."""
import math
from .common import *
from .treemap import txt, read_value, usable_path, common_notes, note_result, render, tip, ell
PADDING = 3.0   # the atom's pack() padding
MIN_R = 0.5      # layout units; a circle smaller than this is drawn at this radius (and noted)
def _enclose(cs):
    """Smallest circle containing circles cs = [(x, y, r)] (iterative Badoiu-Clarkson refinement, then exact radius). Deterministic."""
    if len(cs) == 1: return cs[0]
    x = sum(c[0] for c in cs) / len(cs); y = sum(c[1] for c in cs) / len(cs)
    for i in range(1, 400):
        far = max(cs, key=lambda c: math.hypot(c[0] - x, c[1] - y) + c[2]); d = math.hypot(far[0] - x, far[1] - y)
        if d < 1e-12: break
        step = 1 / (i + 1); x += (far[0] - x) * step; y += (far[1] - y) * step
    return (x, y, max(math.hypot(c[0] - x, c[1] - y) + c[2] for c in cs))
def pack_siblings(radii):
    """Positions (x, y) for circles of the given radii, no overlap (gap PADDING). Largest first."""
    order = sorted(range(len(radii)), key=lambda i: -radii[i]); placed = []
    pos = [None] * len(radii)
    for k, i in enumerate(order):
        r = radii[i]
        if k == 0: placed.append((0.0, 0.0, r, i)); continue
        if k == 1:
            a = placed[0]; placed.append((a[2] + r + PADDING, 0.0, r, i)); continue
        cx = sum(p[0] * p[2] ** 2 for p in placed) / sum(p[2] ** 2 for p in placed); cy = sum(p[1] * p[2] ** 2 for p in placed) / sum(p[2] ** 2 for p in placed)
        best = None
        for a in range(len(placed)):
            for b in range(a, len(placed)):
                A, B = placed[a], placed[b]
                cands = []
                if a == b:
                    for ang in range(0, 360, 15): t = math.radians(ang); d = A[2] + r + PADDING; cands.append((A[0] + d * math.cos(t), A[1] + d * math.sin(t)))
                else:
                    d = math.hypot(B[0] - A[0], B[1] - A[1]); ra, rb = A[2] + r + PADDING, B[2] + r + PADDING
                    if d < 1e-9 or d > ra + rb or d < abs(ra - rb): continue
                    a_ = (ra * ra - rb * rb + d * d) / (2 * d); h = math.sqrt(max(ra * ra - a_ * a_, 0)); ux, uy = (B[0] - A[0]) / d, (B[1] - A[1]) / d
                    mx, my = A[0] + a_ * ux, A[1] + a_ * uy; cands += [(mx - h * uy, my + h * ux), (mx + h * uy, my - h * ux)]
                for (x, y) in cands:
                    if all(math.hypot(x - p[0], y - p[1]) >= p[2] + r + PADDING - 1e-6 for p in placed):
                        sc = math.hypot(x - cx, y - cy)
                        if best is None or sc < best[0] - 1e-9: best = (sc, x, y)
        if best is None: far = max(p[0] + p[2] for p in placed); best = (0, far + r + PADDING, 0.0)   # no tangent spot found: put it beyond the right edge (cannot overlap)
        placed.append((best[1], best[2], r, i))
    for x, y, r, i in placed: pos[i] = (x, y)
    return pos
def circle_pack(items, unit='', title='', version=1):
    notes = []; cnt = {'dropped': 0, 'clamped': 0}; u = txt(unit, 12) or ''; ttl = txt(title, 80) or ''
    if not isinstance(items, list): raise ValueError('items must be a list')
    if len(items) > 60: notes.append(f'{len(items) - 60} items beyond the 60th were not drawn.'); items = items[:60]
    its = []
    for n, it in enumerate(items, 1):
        v = read_value(it.get('value'), cnt) if isinstance(it, dict) else None
        if v is None: cnt['dropped'] += 1; continue
        its.append({'path': usable_path(it.get('path')) or [], 'name': txt(it.get('name'), 24) or f'Item {n}', 'value': v})
    common_notes(notes, cnt, version)
    if len(its) < 2: return {'circle_pack': note_result('circle_pack', ttl, 'A circle pack needs at least 2 usable items, so no chart is drawn.', notes), '_default': 'circle_pack'}
    tree = {'name': '', 'kids': {}, 'leaves': []}
    for it in its:
        nd = tree
        for seg in it['path']: nd = nd['kids'].setdefault(seg, {'name': seg, 'kids': {}, 'leaves': []})
        nd['leaves'].append(it)
    vmax = max(i['value'] for i in its); unit_r = 60.0; floored = [0]
    def leaf_r(v):
        r = unit_r * math.sqrt(v / vmax)
        if r < MIN_R: floored[0] += 1; return MIN_R
        return r
    def build(nd, top):
        """returns a node with local children positions and an enclosing radius; children are ordered largest first (d3 order)"""
        kids = []
        for name, c in nd['kids'].items(): kids.append(build(c, top if top is not None else len(kids)))
        for l in nd['leaves']: kids.append({'leaf': True, 'name': l['name'], 'value': l['value'], 'r': leaf_r(l['value']), 'x': 0, 'y': 0, 'kids': [], 'path': l['path']})
        kids.sort(key=lambda k: -k['value'])   # d3 order: largest first (stable)
        pos = pack_siblings([k['r'] for k in kids])
        for k, (x, y) in zip(kids, pos): k['x'], k['y'] = x, y
        ex, ey, er = _enclose([(k['x'], k['y'], k['r']) for k in kids])
        for k in kids: k['x'] -= ex; k['y'] -= ey
        return {'leaf': False, 'name': nd['name'], 'value': sum(k['value'] for k in kids), 'r': er + PADDING, 'x': 0, 'y': 0, 'kids': kids, 'path': []}
    root = build(tree, None); scale = min((W - 40) / (2 * root['r']), (H - 40) / (2 * root['r'])); circles = []
    if floored[0]: notes.append(f'{floored[0]} circles are drawn at a minimum size (their value is under a millionth of the largest); the table has every value.')
    us = (' ' + u) if u else ''
    def walk(nd, ox, oy, depth, top, path):
        for i, k in enumerate(nd['kids']):
            t = i if depth == 0 else top; x, y = ox + k['x'] * scale, oy + k['y'] * scale; r = k['r'] * scale
            circles.append({'name': k['name'], 'value': k['value'], 'x': x, 'y': y, 'r': r, 'leaf': k['leaf'], 'depth': depth, 'parent': id(nd), 'id': id(k), 'top': t, 'path': list(path)})
            walk(k, x, y, depth + 1, t, path + ([] if k['leaf'] else [k['name']]))
    walk(root, W / 2, H / 2, 0, 0, [])
    def draw(titles):
        body = ''
        for c in circles:
            base = PAL[c['top'] % len(PAL)]; tt = tip(titles, '/'.join(c['path'] + ([c['name']] if c['leaf'] else [])) + ': ' + fmt(c['value']) + us)
            if c['leaf']:
                col = blend(base, .15 * min(c['depth'], 3)); body += f'<circle cx="{c["x"]:.2f}" cy="{c["y"]:.2f}" r="{c["r"]:.2f}" fill="{col}" stroke="#ffffff" stroke-width="2">{tt}</circle>'
                cap = int((2 * c['r'] - 8) / (0.6 * 12)); nm = ell(c['name'], cap)
                if nm:
                    big = c['r'] >= 30; body += label(c['x'], c['y'] + (0 if big else 4), nm, 12, fill=text_on(col), weight=600)
                    if big and len(fmt(c['value'])) <= cap: body += label(c['x'], c['y'] + 16, fmt(c['value']), 12, fill=text_on(col))
            else:
                body += f'<circle cx="{c["x"]:.2f}" cy="{c["y"]:.2f}" r="{c["r"]:.2f}" fill="none" stroke="{blend(base, .1 * min(c["depth"], 3))}" stroke-width="2">{tt}</circle>'
                cap = int((c['r'] * 1.2 - 8) / (0.6 * 12)); nm = ell(c['name'], cap)
                if nm and c['r'] >= 36: body += label(c['x'], c['y'] - c['r'] + 16, nm, 12, fill=INK, weight=700)
        return body
    tab = '; '.join(('/'.join(i['path']) + '/' if i['path'] else '') + f"{i['name']} {fmt(i['value'])}{us}" + f" ({100 * i['value'] / sum(j['value'] for j in its):.1f}%)" for i in its)
    big = max(its, key=lambda i: i['value']); tot = sum(i['value'] for i in its); ngroups = sum(1 for c in circles if not c['leaf'])
    summary = f"{len(its)} items in {ngroups} groups, total {fmt(tot)}{us}; circle area is proportional to value; the largest is {big['name']} ({fmt(big['value'])}, {100 * big['value'] / tot:.0f}%)."
    r = render('circle_pack', ttl, 'Circle pack', draw, summary, tab, notes, u); r['circles'] = circles; r['root_r'] = root['r'] * scale; r['scale'] = scale; r['padding'] = PADDING * scale
    return {'circle_pack': r, '_default': 'circle_pack'}
