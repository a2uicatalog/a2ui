"""spring_nodes macro: same input contract as the spring_nodes atom (nodes [{id,label,size}], edges [{a,b}] by index or id, rest_length, height, interactive, colour, bg),
settled STATIC layout only. The layout is a deterministic force simulation in pure Python: golden-angle initial placement, Hooke springs on edges, Coulomb repulsion between
all pairs, a weak centring pull, cooling over a fixed number of iterations, then a fixed-point separation pass so no two discs are closer than their radii plus a gap.
No randomness, so the same input always gives bit-identical output. colour and bg are ignored (the pack palette is fixed); interactive is ignored (static only).
Inputs are read with finite(); rest_length is clamped to 10..400 and node size to 8..48, so no input can make a position NaN. Duplicate edges (same pair, either way round) are merged and
counted; the work is bounded (iterations shrink as the node count grows) and the drawing degrades before it is refused (hover titles, then edge labels, are left out with a note).
Fewer than 2 nodes gives a note-only Result. Unknown keyword options (a title, say) are ignored with a note. Returns {'graph': Result, '_default': 'graph'}."""
import math
from .common import *
from .waterfall import note_result, fit_svg
MAX_NODES, ITER, CHARGE, K_SPRING, DAMP, GAP_PX = 60, 400, 4000.0, 0.04, 0.85, 10.0
WORK = 200_000   # pair-iterations allowed in the force loop and in the separation loop
PADX, PADT, PADB = 40.0, 16.0, 30.0
DEFAULT_NODES = ['Web', 'API', 'Database', 'Auth', 'Cache', 'Queue']; DEFAULT_EDGES = [(0, 1), (1, 2), (1, 3), (1, 4), (0, 3), (1, 5)]
def layout(n, links, rest, radii, box, iters=None):
    """Deterministic settled positions inside box = (x0, y0, x1, y1) (centres; radii respected). Returns a list of (x, y)."""
    pairs = max(1, n * (n - 1) // 2); iters = max(60, min(ITER, WORK // pairs)) if iters is None else iters
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; ga = math.pi * (3 - math.sqrt(5)); P = []
    for i in range(n):
        r = 12 * math.sqrt(0.5 + i) * 1.0; P.append([cx + r * math.cos(i * ga), cy + r * math.sin(i * ga)])
    V = [[0.0, 0.0] for _ in range(n)]
    def clamp(i):
        P[i][0] = min(max(P[i][0], x0 + radii[i]), x1 - radii[i]); P[i][1] = min(max(P[i][1], y0 + radii[i]), y1 - radii[i])
    for it in range(iters):
        cool = 1.0 - it / iters; a = 0.05 + 0.95 * cool; F = [[0.0, 0.0] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                dx = P[j][0] - P[i][0]; dy = P[j][1] - P[i][1]; d2 = dx * dx + dy * dy
                if d2 < 1e-9: dx, dy, d2 = math.cos(i + 7 * j) * 1e-3, math.sin(i + 7 * j) * 1e-3, 1e-6
                d = math.sqrt(d2); f = CHARGE / max(d2, 100.0)
                F[i][0] -= dx / d * f; F[i][1] -= dy / d * f; F[j][0] += dx / d * f; F[j][1] += dy / d * f
        for s, t in links:
            dx = P[t][0] - P[s][0]; dy = P[t][1] - P[s][1]; d = math.sqrt(dx * dx + dy * dy) or 1e-3; f = (d - rest) * K_SPRING
            F[s][0] += dx / d * f; F[s][1] += dy / d * f; F[t][0] -= dx / d * f; F[t][1] -= dy / d * f
        for i in range(n):
            F[i][0] += (cx - P[i][0]) * 0.001; F[i][1] += (cy - P[i][1]) * 0.001
            V[i][0] = (V[i][0] + F[i][0] * a) * DAMP; V[i][1] = (V[i][1] + F[i][1] * a) * DAMP
            sp = math.hypot(V[i][0], V[i][1])
            if sp > 20: V[i][0] *= 20 / sp; V[i][1] *= 20 / sp
            P[i][0] += V[i][0]; P[i][1] += V[i][1]; clamp(i)
    for _ in range(max(40, min(600, 3 * WORK // pairs))):  # separation: push overlapping pairs apart, keep inside the box
        moved = False
        for i in range(n):
            for j in range(i + 1, n):
                need = radii[i] + radii[j] + GAP_PX; dx = P[j][0] - P[i][0]; dy = P[j][1] - P[i][1]; d = math.hypot(dx, dy)
                if d < need - 1e-9:
                    if d < 1e-9: dx, dy, d = 1.0, 0.0, 1.0
                    push = (need - d) / 2 + 1e-6; ux, uy = dx / d, dy / d
                    P[i][0] -= ux * push; P[i][1] -= uy * push; P[j][0] += ux * push; P[j][1] += uy * push; clamp(i); clamp(j); moved = True
        if not moved: break
    return [(p[0], p[1]) for p in P]
def spring_nodes(nodes=None, edges=None, colour=None, bg=None, height=420, rest_length=110, interactive=False, version=1, **ignored):
    notes = []; raw = nodes if isinstance(nodes, list) and nodes else None; src = raw or list(DEFAULT_NODES)
    if len(src) > MAX_NODES: notes.append(f'{len(src) - MAX_NODES} nodes beyond the {MAX_NODES}th were not drawn.'); src = src[:MAX_NODES]
    ns = []; ids = {}
    for i, d in enumerate(src):
        if not isinstance(d, dict): d = {'id': d, 'label': d}
        nid = ident(d.get('id'), 40) or str(i); lab = ident(d.get('label'), 24) or nid[:24]; sz = finite(d.get('size'))
        ns.append({'id': nid, 'label': lab, 'r': sz if sz is not None and 8 <= sz <= 48 else 16.0}); ids.setdefault(nid, i)
    if len(ns) < 2:
        why = 'A graph needs at least 2 nodes.'; notes.append(why); return {'graph': note_result('spring_nodes', '', why + ' Nothing was drawn.', notes), '_default': 'graph'}
    def ref(v):
        if isinstance(v, bool): return -1
        if isinstance(v, (int, float)): f = finite(v, 0, 1e6); return int(f) if f is not None and f == math.floor(f) and f < len(ns) else -1
        if isinstance(v, str):
            if v in ids: return ids[v]
            if v.isdigit() and len(v) <= 4 and int(v) < len(ns): return int(v)
        return -1
    esrc = edges if isinstance(edges, list) else (None if raw else DEFAULT_EDGES)
    esrc = esrc or []; links = []; bad = 0; seen = {}; dup = 0
    if len(esrc) > 400: notes.append(f'{len(esrc) - 400} edges beyond the 400th were not drawn.'); esrc = esrc[:400]
    for e in esrc:
        if isinstance(e, tuple): e = {'a': e[0], 'b': e[1]}
        if not isinstance(e, dict): bad += 1; continue
        a, b = (e.get('a'), e.get('b')) if (e.get('a') is not None or e.get('b') is not None) else ((e.get('from'), e.get('to')) if (e.get('from') is not None or e.get('to') is not None) else (e.get('source'), e.get('target')))
        s, t = ref(a), ref(b)
        if s < 0 or t < 0 or s == t: bad += 1; continue
        key = (min(s, t), max(s, t))
        if key in seen:
            dup += 1
            if not links[seen[key]][2]: lb = ident(e.get('label'), 24) or ''; links[seen[key]] = (links[seen[key]][0], links[seen[key]][1], lb)
            continue
        seen[key] = len(links); links.append((s, t, ident(e.get('label'), 24) or ''))
    if bad: notes.append(f'{bad} edges were dropped (not an object, an endpoint that is not a node, or a self edge).')
    if dup: notes.append(f'{dup} repeated edges (the same two nodes) were merged into the first.')
    h = finite(height, -1.8e308, 1.8e308); h = 420 if h is None else int(max(160, min(1200, h)))
    rl = finite(rest_length, -1.8e308, 1.8e308); rl0 = rl
    if rl is None or rl <= 0: rl = 110.0
    elif not 10 <= rl <= 400: rl = min(400.0, max(10.0, rl)); notes.append(f'rest_length {fmt(rl0)} was clamped to {fmt(rl)}.')
    if colour is not None or bg is not None: notes.append('colour and bg are not used: the pack palette is fixed.')
    if interactive is True: notes.append('interactive is not available here: this is the settled static layout.')
    if ignored: notes.append('Unknown option' + ('s' if len(ignored) > 1 else '') + ' ignored: ' + ', '.join(plain(str(k))[:30] for k in sorted(ignored)) + '.')
    if isinstance(version, int) and not isinstance(version, bool) and version > 1: notes.append(f'Contract version {min(version, 10 ** 9)} is drawn as version 1.')
    n = len(ns); radii = [d['r'] for d in ns]; box = (PADX, PADT, W - PADX, h - PADB)
    pos = layout(n, [(s, t) for s, t, _ in links], rl, radii, box); tight = False
    for i in range(n):
        for j in range(i + 1, n):
            if math.hypot(pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]) < radii[i] + radii[j] + GAP_PX - 1e-6: tight = True
    if tight: notes.append('The nodes do not all fit with the minimum spacing at this height; some are closer than the gap.')
    deg = [0] * n
    for s, t, _ in links: deg[s] += 1; deg[t] += 1
    def draw(level):
        body = f'<g stroke="{MUTED}" stroke-width="2">' if level == 0 else f'<g stroke="{MUTED}" stroke-width="1.5">'
        for s, t, lb in links:
            tip = f'<title>{esc(ns[s]["label"])} to {esc(ns[t]["label"])}</title>' if level == 0 else ''
            body += f'<line x1="{pos[s][0]:.1f}" y1="{pos[s][1]:.1f}" x2="{pos[t][0]:.1f}" y2="{pos[t][1]:.1f}"' + (f'>{tip}</line>' if tip else '/>')
        body += '</g>'
        if level < 2:
            for s, t, lb in links:
                if lb: body += label((pos[s][0] + pos[t][0]) / 2, (pos[s][1] + pos[t][1]) / 2 - 4, lb, 14, fill=MUTED)
        for i, d in enumerate(ns):
            c = PAL[i % len(PAL)]
            body += (f'<circle cx="{pos[i][0]:.1f}" cy="{pos[i][1]:.1f}" r="{d["r"]:.1f}" fill="{c}" stroke="{FACE}" stroke-width="2">' + (f'<title>{esc(d["label"])}: {deg[i]} links</title>' if level == 0 else '') + '</circle>'
                     + label(pos[i][0], pos[i][1] + d['r'] + 16, d['label'], 14))
        return svg(body, 'Spring-layout graph', W, h)
    drawing = fit_svg(draw, notes)
    tab = '; '.join(f'{d["label"]} ({deg[i]} links)' for i, d in enumerate(ns)) + '. Links: ' + ('; '.join(f'{ns[s]["label"]} to {ns[t]["label"]}' + (f' ({lb})' if lb else '') for s, t, lb in links) or 'none')
    top = max(range(n), key=lambda i: (deg[i], -i)); summary = f'{n} nodes, {len(links)} links; the most connected node is {ns[top]["label"]} ({deg[top]} links).'
    res = finish('spring_nodes', '', drawing, summary, tab, notes)
    res['pos'] = pos; res['radii'] = radii; res['links'] = [(s, t) for s, t, _ in links]; res['box'] = box; res['gap'] = GAP_PX; res['size'] = (W, h); res['rest'] = rl; res['degree'] = deg
    return {'graph': res, '_default': 'graph'}
