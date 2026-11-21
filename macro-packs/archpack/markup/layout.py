"""Deterministic layered layout for the canonical graph (port of mermaid_arch/layout.mjs).

Everything is computed in pixels of the SVG viewBox the atom draws in; compile.py turns it into percent coordinates. The same
input gives the same output (no randomness; every tie-break uses the input order).

Pipeline: cluster_layout() -> orientation/size search -> route_edges() (route.py) -> frame_routed()
"""
from __future__ import annotations

import functools
import math

from ._js import js_round, ulen
from .graph import LIMITS
from .route import curve_routes, group_title_rect, route_edges, route_metrics

CHAR_SANS = 0.56   # bold system-ui, em per character
CHAR_MONO = 0.62   # mono, em per character
INF = float('inf')


def _fsum(xs):
    t = 0
    for x in xs:
        t = t + x
    return t


# ---------------------------------------------------------------- measuring
def node_box(n, s):
    nh = js_round(3.0 * s)
    lab = min(ulen(str(n['label'])), LIMITS['label'])
    sub = min(ulen(str(n['sub'])), LIMITS['sub']) if n.get('sub') else 0
    text_w = max(lab * CHAR_SANS * s, sub * CHAR_MONO * (s - 5))
    nw = max(js_round(0.76 * nh + text_w + 0.34 * nh), js_round(5.2 * s))
    return {'w': nw, 'h': nh}


def edge_label_lines(text):
    return str(text).split('\n')[:2]


def edge_label_size(text, s):
    ls = edge_label_lines(text)
    t = min(max(ulen(l) for l in ls), LIMITS['edgeLabel'])
    return {'w': js_round(t * (s - 4) * CHAR_MONO + 12), 'h': js_round((s - 4) * 1.15 * len(ls) + 6)}


def group_label_width(label, s):
    t = min(ulen(str(label)), LIMITS['groupLabel'])
    return js_round(t * (s - 5) * (CHAR_MONO + 0.12) + 36)


# ---------------------------------------------------------------- isotonic spacing
def space_out(desired, min_dist):
    n = len(desired)
    off = [0]
    for i in range(1, n):
        off.append(off[i - 1] + min_dist[i - 1])
    blocks = []
    for i in range(n):
        blocks.append({'sum': desired[i] - off[i], 'cnt': 1, 'from': i, 'to': i})
        while len(blocks) > 1:
            b, a = blocks[-1], blocks[-2]
            if a['sum'] / a['cnt'] <= b['sum'] / b['cnt']:
                break
            blocks.pop()
            a['sum'] += b['sum']
            a['cnt'] += b['cnt']
            a['to'] = b['to']
    out = [0] * n
    for b in blocks:
        for i in range(b['from'], b['to'] + 1):
            out[i] = b['sum'] / b['cnt'] + off[i]
    return out


# ---------------------------------------------------------------- layered core
def layered(items, edges, axis, s, same_pairs=(), lane_gap=0, extra_gap=0):
    """items: [{key,w,h}]; edges: [{a,b,lw,lh,n}] between item keys; axis 'x'|'y' is the rank axis.
    -> {'pos': {key: {x,y}}, 'rank': {key: rank}, 'w', 'h'}"""
    n = len(items)
    idx = {it['key']: i for i, it in enumerate(items)}
    E = [{'a': idx[e['a']], 'b': idx[e['b']], 'lw': e.get('lw') or 0, 'lh': e.get('lh') or 0, 'n': e.get('n') or 1}
         for e in edges if e['a'] in idx and e['b'] in idx and e['a'] != e['b']]
    rep = list(range(n))

    def find(x):
        while rep[x] != x:
            rep[x] = rep[rep[x]]
            x = rep[x]
        return x
    pair_idx = []
    for ka, kb in same_pairs:
        if ka not in idx or kb not in idx:
            continue
        ra, rb = find(idx[ka]), find(idx[kb])
        if ra != rb:
            rep[max(ra, rb)] = min(ra, rb)
        pair_idx.append((idx[ka], idx[kb]))
    Eorig = [{**e, 'oa': e['a'], 'ob': e['b']} for e in E]
    E = [{**e, 'a': find(e['a']), 'b': find(e['b'])} for e in Eorig]
    E = [e for e in E if e['a'] != e['b']]
    # 1. break cycles deterministically: DFS from sources, then the rest, in input order
    out = [[] for _ in range(n)]
    inc = [0] * n
    for i, e in enumerate(E):
        out[e['a']].append(i)
        inc[e['b']] += 1
    state = [0] * n
    rev = set()

    def visit(v):
        state[v] = 1
        for ei in out[v]:
            w = E[ei]['b']
            if state[w] == 1:
                rev.add(ei)
            elif state[w] == 0:
                visit(w)
        state[v] = 2
    for v in range(n):
        if not inc[v] and state[v] == 0:
            visit(v)
    for v in range(n):
        if state[v] == 0:
            visit(v)
    D = [({**e, 'a': e['b'], 'b': e['a']} if i in rev else e) for i, e in enumerate(E)]
    # 2. longest-path ranks
    dout = [[] for _ in range(n)]
    din = [[] for _ in range(n)]
    for e in D:
        dout[e['a']].append(e['b'])
        din[e['b']].append(e['a'])
    rank = [0] * n
    indeg = [len(l) for l in din]
    queue = [v for v in range(n) if not indeg[v]]
    qi = 0
    while qi < len(queue):
        v = queue[qi]
        qi += 1
        for w in dout[v]:
            rank[w] = max(rank[w], rank[v] + 1)
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    for v in range(n):
        if not din[v] and dout[v]:
            rank[v] = max(0, min(rank[w] for w in dout[v]) - 1)
    for v in range(n):
        rank[v] = rank[find(v)]
    R = (max(rank) if rank else 0) + 1
    # 2b. long edges get a dummy vertex in every rank they cross
    N = n
    chain = []
    for e in Eorig:
        a, b = e['oa'], e['ob']
        if rank[a] > rank[b]:
            a, b = b, a
        prev = a
        for r in range(rank[a] + 1, rank[b]):
            d = N
            N += 1
            if d == len(rank):
                rank.append(r)
            else:
                rank[d] = r
            chain.append((prev, d))
            prev = d
        chain.append((prev, b))
    # 3. order within ranks: barycentre sweeps, keep best by crossings

    def layers_of():
        L = [[] for _ in range(R)]
        for v in range(N):
            L[rank[v]].append(v)
        return L
    L = layers_of()
    nbr = [[] for _ in range(N)]
    for u, v in chain:
        nbr[u].append(v)
        nbr[v].append(u)

    def keep_pairs(layer):
        for a, b in pair_idx:
            ia = layer.index(a) if a in layer else -1
            ib = layer.index(b) if b in layer else -1
            if ia < 0 or ib < 0:
                continue
            first, second = (a, b) if ia < ib else (b, a)
            layer.pop(layer.index(second))
            layer.insert(layer.index(first) + 1, second)

    def frac():
        f = [0] * N
        for layer in L:
            for i, v in enumerate(layer):
                f[v] = (i + 0.5) / len(layer)
        return f

    def crossings():
        f = frac()
        segs = []
        for u, v in chain:
            r1, p1, r2, p2 = rank[u], f[u], rank[v], f[v]
            segs.append((r1, p1, r2, p2) if r1 <= r2 else (r2, p2, r1, p1))
        c = 0

        def at(r1, v1, r2, v2, r):
            return v1 if r2 == r1 else v1 + (v2 - v1) * (r - r1) / (r2 - r1)
        for i in range(len(segs)):
            for j in range(i + 1, len(segs)):
                a1, p1, a2, p2 = segs[i]
                b1, q1, b2, q2 = segs[j]
                lo = max(a1, b1)
                hi = min(a2, b2)
                if hi <= lo:
                    continue
                d1 = at(a1, p1, a2, p2, lo) - at(b1, q1, b2, q2, lo)
                d2 = at(a1, p1, a2, p2, hi) - at(b1, q1, b2, q2, hi)
                if d1 * d2 < 0:
                    c += 1
        return c
    best = [l[:] for l in L]
    best_c = crossings()
    for it in range(8):
        f = frac()
        down = it % 2 == 0
        order = list(range(len(L))) if down else list(reversed(range(len(L))))
        for r in order:
            key = {}
            for i, v in enumerate(L[r]):
                ns = [w for w in nbr[v] if (rank[w] < r if down else rank[w] > r)]
                use = ns if ns else [w for w in nbr[v] if rank[w] != r]
                key[v] = _fsum(f[w] for w in use) / len(use) if use else f[v]
            before = {v: i for i, v in enumerate(L[r])}
            L[r].sort(key=lambda v: (key[v], before[v]))
            keep_pairs(L[r])
            for i, v in enumerate(L[r]):
                f[v] = (i + 0.5) / len(L[r])
        c = crossings()
        if c < best_c:
            best_c = c
            best = [l[:] for l in L]
    L = best
    # 4. coordinates
    lane = js_round(0.8 * s)

    def ext(v):
        if v >= n:
            return (0, lane)          # (r, c)
        return (items[v]['w'], items[v]['h']) if axis == 'x' else (items[v]['h'], items[v]['w'])
    thick = [max([0] + [ext(v)[0] for v in layer]) for layer in L]
    gaps = []
    for r in range(R - 1):
        g = 2.7 * s if axis == 'x' else 3.0 * s
        for e in Eorig:
            lo = min(rank[e['oa']], rank[e['ob']])
            hi = max(rank[e['oa']], rank[e['ob']])
            if lo == r and hi == r + 1:
                g = max(g, e['lw'] + 1.6 * s if axis == 'x' else e['lh'] + 1.4 * s)
        if lane_gap:
            through = _fsum(e['n'] for e in Eorig if min(rank[e['oa']], rank[e['ob']]) <= r and max(rank[e['oa']], rank[e['ob']]) >= r + 1)
            g += max(0, through - 1) * lane_gap
            if axis == 'y':
                lh = _fsum(e['lh'] + 4 for e in Eorig if min(rank[e['oa']], rank[e['ob']]) <= r and max(rank[e['oa']], rank[e['ob']]) >= r + 1 and e['lh'])
                g = max(g, 0.55 * lh + 1.4 * s)
            g += extra_gap
        gaps.append(js_round(g))
    rank_pos = []
    acc = 0
    for r in range(R):
        rank_pos.append(acc)
        acc += thick[r] + (gaps[r] if r < len(gaps) else 0)
    cross_gap = js_round(1.3 * s) + (js_round(0.9 * s) if lane_gap else 0)
    cpos = [0] * N
    for layer in L:
        t = 0
        for v in layer:
            cpos[v] = t + ext(v)[1] / 2
            t += ext(v)[1] + cross_gap
        total = t - cross_gap
        for v in layer:
            cpos[v] -= total / 2
    for p in range(8):
        down = p % 2 == 0
        order = list(range(len(L))) if down else list(reversed(range(len(L))))
        for r in order:
            layer = L[r]
            desired = []
            for v in layer:
                ns = nbr[v]
                desired.append(_fsum(cpos[w] for w in ns) / len(ns) if ns else cpos[v])
            md = [(ext(layer[i])[1] + ext(v)[1]) / 2 + cross_gap for i, v in enumerate(layer[1:])]
            placed = space_out(desired, md)
            for i, v in enumerate(layer):
                cpos[v] = placed[i]
    lo, hi = INF, -INF
    for v in range(n):
        lo = min(lo, cpos[v] - ext(v)[1] / 2)
        hi = max(hi, cpos[v] + ext(v)[1] / 2)
    if not n:
        lo = hi = 0
    pos = {}
    rk = {}
    for v in range(n):
        rc = rank_pos[rank[v]] + thick[rank[v]] / 2
        cc = cpos[v] - lo
        cx = rc if axis == 'x' else cc
        cy = cc if axis == 'x' else rc
        pos[items[v]['key']] = {'x': cx - items[v]['w'] / 2, 'y': cy - items[v]['h'] / 2}
        rk[items[v]['key']] = rank[v]
    main_len = acc
    cross_len = hi - lo
    return {'pos': pos, 'rank': rk, 'w': js_round(main_len if axis == 'x' else cross_len), 'h': js_round(cross_len if axis == 'x' else main_len)}


# ---------------------------------------------------------------- compound layout
def _other_axis(a):
    return 'y' if a == 'x' else 'x'


def labelled_pairs(edges, key_of):
    """labelled request/response pairs (a->b and b->a, both labelled): [[a,b],...] over keys"""
    out = []
    seen = set()
    for e in edges:
        if not e.get('label'):
            continue
        a, b = key_of(e['from']), key_of(e['to'])
        if a == b:
            continue
        k = a + '|' + b if a < b else b + '|' + a
        if k in seen:
            continue
        if any(f.get('label') and key_of(f['from']) == b and key_of(f['to']) == a for f in edges):
            seen.add(k)
            out.append((a, b))
    return out


def _js_lt(a, b):
    """JS string comparison `a < b` (UTF-16 code units)."""
    if a.isascii() and b.isascii():
        return a < b
    return a.encode('utf-16-be', 'surrogatepass') < b.encode('utf-16-be', 'surrogatepass')


def cluster_layout(graph, s, flows, pair_mode=False, lane_gap=0, extra_gap=0):
    outer_axis = 'x' if graph['direction'] in ('LR', 'RL') else 'y'
    box = {n['id']: node_box(n, s) for n in graph['nodes']}

    def edge_of(e):
        lab = edge_label_size(e['label'], s) if e.get('label') else {'w': 0, 'h': 0}
        return {'a': e['from'], 'b': e['to'], 'lw': lab['w'], 'lh': lab['h']}
    pad_x = js_round(1.1 * s)
    pad_bottom = js_round(1.0 * s)
    pad_top = js_round(24 + 0.3 * (s - 5) + 11)
    clusters = []
    cluster_of_node = {}
    inner = {}
    group_order = [g['id'] for g in graph['groups']]
    first_seen = {}
    for i, n in enumerate(graph['nodes']):
        k = 'g:' + n['group'] if n.get('group') else 'n:' + n['id']
        if k not in first_seen:
            first_seen[k] = i
    for k in first_seen:
        if k.startswith('n:'):
            id_ = k[2:]
            b = box[id_]
            clusters.append({'key': k, 'w': b['w'], 'h': b['h'], 'members': [id_]})
            cluster_of_node[id_] = k
        else:
            gid = k[2:]
            members = [n['id'] for n in graph['nodes'] if n.get('group') == gid]
            flow = _other_axis(outer_axis) if flows.get(gid) == 'cross' else outer_axis
            items = [{'key': i_, **box[i_]} for i_ in members]
            inner_edge_list = [e for e in graph['edges'] if e['from'] in members and e['to'] in members]
            inner_edges = [edge_of(e) for e in inner_edge_list]
            inner_pairs = labelled_pairs(inner_edge_list, lambda x: x) if (pair_mode and flow == 'y') else []
            lay = layered(items, inner_edges, flow, s, inner_pairs, lane_gap, extra_gap)
            gl = next(g for g in graph['groups'] if g['id'] == gid)
            w = max(lay['w'] + 2 * pad_x, group_label_width(gl['label'], s))
            h = lay['h'] + pad_top + pad_bottom
            inner[k] = {'lay': lay, 'w': w, 'h': h, 'gid': gid, 'offX': js_round((w - lay['w']) / 2), 'offY': pad_top}
            clusters.append({'key': k, 'w': w, 'h': h, 'members': members})
            for m in members:
                cluster_of_node[m] = k
    ce = {}
    for e in graph['edges']:
        a, b = cluster_of_node[e['from']], cluster_of_node[e['to']]
        if a == b:
            continue
        k = a + '>' + b
        o = edge_of(e)
        prev = ce.get(k)
        if prev:
            prev['lw'] = max(prev['lw'], o['lw'])
            prev['lh'] = max(prev['lh'], o['lh'])
            prev['n'] += 1
        else:
            ce[k] = {'a': a, 'b': b, 'lw': o['lw'], 'lh': o['lh'], 'n': 1}
    top_pairs = labelled_pairs(graph['edges'], lambda x: cluster_of_node[x]) if (pair_mode and outer_axis == 'y') else []
    top = layered(clusters, list(ce.values()), outer_axis, s, top_pairs, lane_gap, extra_gap)
    nodes = []
    groups = []
    for c in clusters:
        p = top['pos'][c['key']]
        inn = inner.get(c['key'])
        if not inn:
            id_ = c['members'][0]
            nodes.append({'id': id_, 'x': p['x'], 'y': p['y'], 'w': c['w'], 'h': c['h']})
            continue
        groups.append({'id': inn['gid'], 'x': p['x'], 'y': p['y'], 'w': c['w'], 'h': c['h']})
        for id_ in c['members']:
            q = inn['lay']['pos'][id_]
            b = box[id_]
            nodes.append({'id': id_, 'x': p['x'] + inn['offX'] + q['x'], 'y': p['y'] + inn['offY'] + q['y'], 'w': b['w'], 'h': b['h']})
    order = {n['id']: i for i, n in enumerate(graph['nodes'])}
    nodes.sort(key=lambda n: order[n['id']])
    groups.sort(key=lambda g: group_order.index(g['id']))
    W, H = top['w'], top['h']
    if graph['direction'] == 'RL':
        for n in nodes:
            n['x'] = W - n['x'] - n['w']
        for g in groups:
            g['x'] = W - g['x'] - g['w']
    if graph['direction'] == 'BT':
        for n in nodes:
            n['y'] = H - n['y'] - n['h']
        for g in groups:
            g['y'] = H - g['y'] - g['h']
    return {'nodes': nodes, 'groups': groups, 'w': W, 'h': H, 's': s}


# ---------------------------------------------------------------- geometry shared with the renderer
def rim(b, dx, dy):
    hw, hh = b['w'] / 2, b['h'] / 2
    t = min(1e9 if dx == 0 else hw / abs(dx), 1e9 if dy == 0 else hh / abs(dy))
    return [b['cx'] + dx * t, b['cy'] + dy * t]


def edge_curve(fb, tb, curve):
    """the atom's quadratic curve for an edge"""
    dx, dy = tb['cx'] - fb['cx'], tb['cy'] - fb['cy']
    ln = math.sqrt(dx * dx + dy * dy) or 1
    bend = curve / 100
    a = rim(fb, dx, dy)
    z = rim(tb, -dx, -dy)
    mx, my = (a[0] + z[0]) / 2, (a[1] + z[1]) / 2
    c = [mx - (dy / ln) * bend * ln * 0.5, my + (dx / ln) * bend * ln * 0.5]
    return [a, c, z]


def quad(P, t):
    return [(1 - t) * (1 - t) * P[0][0] + 2 * (1 - t) * t * P[1][0] + t * t * P[2][0],
            (1 - t) * (1 - t) * P[0][1] + 2 * (1 - t) * t * P[1][1] + t * t * P[2][1]]


def label_rect(P, text, s):
    sz = edge_label_size(text, s)
    lx = 0.25 * P[0][0] + 0.5 * P[1][0] + 0.25 * P[2][0]
    ly = 0.25 * P[0][1] + 0.5 * P[1][1] + 0.25 * P[2][1] - 10
    fs = s - 4
    return {'x': lx - sz['w'] / 2, 'y': ly - fs * 0.85 - 2 - (len(edge_label_lines(text)) - 1) * fs * 1.15, 'w': sz['w'], 'h': sz['h']}


def _overlap(a, b):
    return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']


def _inside(p, b, m=0):
    return p[0] > b['x'] - m and p[0] < b['x'] + b['w'] + m and p[1] > b['y'] - m and p[1] < b['y'] + b['h'] + m


def _seg_cross(p1, p2, p3, p4):
    def d(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = d(p3, p4, p1), d(p3, p4, p2), d(p1, p2, p3), d(p1, p2, p4)
    return d1 * d2 < 0 and d3 * d4 < 0


def _as_boxes(layout):
    return {n['id']: {**n, 'cx': n['x'] + n['w'] / 2, 'cy': n['y'] + n['h'] / 2} for n in layout['nodes']}


# ---------------------------------------------------------------- the curve step
def route_curves(graph, layout):
    """Pick an integer `curve` (-100..100) for each edge (the atom's one-bend curve)."""
    s = layout['s']
    boxes = _as_boxes(layout)
    lst = list(boxes.values())
    cands = [0, 12, -12, 24, -24, 36, -36, 50, -50, 65, -65, 80, -80, 100, -100]
    glabels = []
    for g in layout['groups']:
        gl = next(x for x in graph['groups'] if x['id'] == g['id'])
        glabels.append({'x': g['x'] + 12, 'y': g['y'] + 6, 'w': group_label_width(gl['label'], s) - 20, 'h': 24})
    chosen = []
    curves = []
    for i, e in enumerate(graph['edges']):
        fb, tb = boxes[e['from']], boxes[e['to']]
        best_c, best_cost, best_geo = 0, INF, None
        for c in cands:
            P = edge_curve(fb, tb, c)
            cost = abs(c) * 0.04
            for k in range(1, 24):
                pt = quad(P, k / 24)
                for b in lst:
                    if b is fb or b is tb:
                        continue
                    if _inside(pt, {'x': b['x'], 'y': b['y'], 'w': b['w'], 'h': b['h']}, 3):
                        cost += 6
            for k in range(2, 22):
                pt = quad(P, k / 24)
                if _inside(pt, fb, -1) or _inside(pt, tb, -1):
                    cost += 2
            rect = None
            if e.get('label'):
                rect = label_rect(P, e['label'], s)
                for b in lst:
                    if _overlap(rect, {'x': b['x'] - 2, 'y': b['y'] - 2, 'w': b['w'] + 4, 'h': b['h'] + 4}):
                        cost += 40
                for gl in glabels:
                    if _overlap(rect, gl):
                        cost += 25
                for o in chosen:
                    if o['rect'] and _overlap(rect, o['rect']):
                        cost += 30
                for o in chosen:
                    for k in range(1, 8):
                        pt = quad(o['P'], k / 8)
                        if _inside(pt, rect, 2):
                            cost += 3
            for o in chosen:
                close = 0
                for k in range(2, 11, 2):
                    a, b = quad(P, k / 12), quad(o['P'], k / 12)
                    if math.hypot(a[0] - b[0], a[1] - b[1]) < 18:
                        close += 1
                if close >= 2:
                    cost += 12 * close
                if _seg_cross(P[0], P[2], o['P'][0], o['P'][2]):
                    cost += 1.5
            if cost < best_cost - 1e-9:
                best_cost, best_c, best_geo = cost, c, {'P': P, 'rect': rect}
        curves.append(best_c)
        chosen.append(best_geo)
    return curves


# ---------------------------------------------------------------- quality metrics
def measure(graph, layout, curves):
    boxes = _as_boxes(layout)
    lst = list(boxes.values())
    crossings = through_boxes = labels_on_boxes = label_overlaps = 0
    length = 0
    rects = []
    geo = [edge_curve(boxes[e['from']], boxes[e['to']], curves[i] if curves else 0) for i, e in enumerate(graph['edges'])]
    for i, P in enumerate(geo):
        length += math.hypot(P[2][0] - P[0][0], P[2][1] - P[0][1])
        e = graph['edges'][i]
        for b in lst:
            if b['id'] == e['from'] or b['id'] == e['to']:
                continue
            hit = False
            for k in range(1, 24):
                if _inside(quad(P, k / 24), b, 0):
                    hit = True
            if hit:
                through_boxes += 1
        if e.get('label'):
            r = label_rect(P, e['label'], layout['s'])
            if any(_overlap(r, b) for b in lst):
                labels_on_boxes += 1
            for o in rects:
                if _overlap(r, o):
                    label_overlaps += 1
            rects.append(r)
        for j in range(i + 1, len(geo)):
            f = graph['edges'][j]
            if f['from'] == e['from'] or f['from'] == e['to'] or f['to'] == e['from'] or f['to'] == e['to']:
                continue
            if _seg_cross(P[0], P[2], geo[j][0], geo[j][2]):
                crossings += 1
    return {'crossings': crossings, 'throughBoxes': through_boxes, 'labelsOnBoxes': labels_on_boxes, 'labelOverlaps': label_overlaps, 'edgeLength': js_round(length)}


# ---------------------------------------------------------------- orientation search
def _score(graph, layout, curves, fit):
    m = measure(graph, layout, curves)
    s = layout['s']
    wu, hu = layout['w'] / s, layout['h'] / s
    w_w = 0.35 if fit == 'wide' else 1.5
    h_w = 0.35
    return wu * w_w + hu * h_w + m['crossings'] * 7 + m['throughBoxes'] * 12 + m['labelsOnBoxes'] * 10 + m['labelOverlaps'] * 40 + (m['edgeLength'] / s) * 0.06


def _phone_px(w, s):
    return ((s - 4) * 343) / max(w, 1)


def _shape_score(graph, layout, fit):
    s, W, H = layout['s'], layout['w'], layout['h']
    by_id = {n['id']: n for n in layout['nodes']}
    ln = 0
    for e in graph['edges']:
        a, b = by_id.get(e['from']), by_id.get(e['to'])
        if a and b:
            ln += abs(a['x'] + a['w'] / 2 - b['x'] - b['w'] / 2) + abs(a['y'] + a['h'] / 2 - b['y'] - b['h'] / 2)
    phone = 0 if fit == 'wide' else 24 * max(0, 9 - _phone_px(W, s)) + 40 * max(0, H / W - 1.3)
    return phone + (W / s) * 0.15 + (H / s) * 0.15 + (ln / s) * 0.35


def choose_layout(graph, s, fit='balanced'):
    return rank_layouts(graph, s, fit, 1, 0)[0]


def rank_layouts(graph, s, fit='balanced', keep=3, lane_gap=0, shape_only=False, extra_gap=0):
    """All candidate layouts (cluster flow directions x request/response pairing), best first by the cheap score."""
    multi = [g['id'] for g in graph['groups'] if sum(1 for n in graph['nodes'] if n.get('group') == g['id']) >= 2]
    lst = []
    for mask in range(1 << len(multi)):
        for pair_mode in (False, True):
            flows = {id_: ('cross' if mask & (1 << i) else 'same') for i, id_ in enumerate(multi)}
            lay = cluster_layout(graph, s, flows, pair_mode, lane_gap, extra_gap)
            if shape_only:
                lst.append({'layout': lay, 'curves': None, 'score': _shape_score(graph, lay, fit), 'flows': flows, 'pairMode': pair_mode})
                continue
            curves = route_curves(graph, lay)
            lst.append({'layout': lay, 'curves': curves, 'score': _score(graph, lay, curves, fit), 'flows': flows, 'pairMode': pair_mode})
    idx = list(enumerate(lst))

    def cmp(a, b):
        if abs(a[1]['score'] - b[1]['score']) < 1e-9:
            return a[0] - b[0]
        d = a[1]['score'] - b[1]['score']
        return -1 if d < 0 else (1 if d > 0 else 0)
    idx.sort(key=functools.cmp_to_key(cmp))
    return [x[1] for x in idx[:keep]]


# ---------------------------------------------------------------- framing: size choice and viewBox
_route_memo = None


def layout_graph(graph, opts=None):
    global _route_memo
    opts = opts or {}
    if opts.get('routing') == 'curve':
        return _layout_curve(graph, opts)
    outer = _route_memo
    _route_memo = outer if outer is not None else {}
    try:
        return _layout_orthogonal(graph, opts)
    finally:
        _route_memo = outer


FLIP_GAIN = 1.25


def _ortho_score(fr, fit):
    m, s = fr['metrics'], fr['size']
    phone = 0 if fit == 'wide' else 24 * max(0, 9 - _phone_px(fr['W'], s)) + 40 * max(0, fr['H'] / fr['W'] - 1.3)
    return (phone + (fr['W'] / s) * 0.15 + (fr['H'] / s) * 0.15 + m['crossings'] * 8 + (m['throughBoxes'] + m['titleHits']) * 40 + m['labelNode'] * 20
            + m['labelLabel'] * 40 + m['labelTitle'] * 30 + m['labelOnLine'] * 14 + (m.get('labelChip') or 0) * 1.5 + m['bends'] * 0.5 + (m['length'] / s) * 0.04 + fr['failed'] * 50)


def _route_cached(gr, layout):
    if _route_memo is None:
        return route_edges(gr, layout, {})

    def r1(o):
        return '%s,%s,%s,%s,%s' % (o['id'], _jn(o['x']), _jn(o['y']), _jn(o['w']), _jn(o['h']))
    key = (str(layout['s']) + '|' + ';'.join(r1(o) for o in layout['nodes']) + '|' + ';'.join(r1(o) for o in layout['groups']) + '|'
           + ';'.join('%s>%s:%s' % (e['from'], e['to'], e.get('label')) for e in gr['edges'])
           + '|' + ';'.join('%s@%s' % (n['id'], n.get('group') or '') for n in gr['nodes']) + '|' + ';'.join('%s:%s' % (g['id'], g['label']) for g in gr['groups']))
    hit = _route_memo.get(key)
    if hit is None:
        hit = route_edges(gr, layout, {})
        _route_memo[key] = hit
    return {'routes': [({**r, 'points': [[p[0], p[1]] for p in r['points']], 'label': dict(r['label']) if r['label'] else None} if r else None) for r in hit['routes']],
            'warnings': list(hit['warnings']), 'metrics': dict(hit['metrics'])}


def _jn(x):
    from ._js import num_str
    return num_str(x)


def _ortho_at(gr, s, fit):
    lane_gap = js_round(0.55 * s)
    best = None
    for extra in (0, 1.0, 2.0, 3.5):
        for v in rank_layouts(gr, s, fit, 4, lane_gap, True, js_round(extra * s)):
            rt = _route_cached(gr, {'nodes': v['layout']['nodes'], 'groups': v['layout']['groups'], 's': s})
            fr = _frame_routed(gr, v, rt, s)
            fr['score'] = _ortho_score(fr, fit)
            if not best or fr['score'] < best['score'] - 1e-9:
                best = fr
        m = best['metrics']
        if best['failed'] == 0 and m['labelLabel'] + m['labelNode'] + m['labelTitle'] + m['throughBoxes'] + m['titleHits'] == 0 and m['labelOnLine'] == 0:
            break
    return best


def _clamp_size(size):
    return max(8, min(40, js_round(size)))


def _layout_orthogonal(graph, opts):
    fit = opts.get('fit') or 'balanced'
    target_w = opts.get('targetW') or 1000
    max_h = opts.get('maxH') or 1100

    def one(gr):
        s = _clamp_size(opts['size']) if opts.get('size') else 18
        res = _ortho_at(gr, s, fit)
        if not opts.get('size'):
            for _ in range(3):
                k = min(target_w / res['W'], max_h / res['H'])
                ns = max(10, min(40, js_round(s * k)))
                if ns == s or (k > 0.88 and k < 1.12):
                    break
                s = ns
                res = _ortho_at(gr, s, fit)
        while (res['W'] > 2000 or res['H'] > 2000) and s > 8:
            s -= 1
            res = _ortho_at(gr, s, fit)
        res['fits'] = res['W'] <= 2000 and res['H'] <= 2000
        res['direction'] = gr['direction']
        return res
    res = one(graph)
    if not opts.get('forceDirection'):
        horizontal = graph['direction'] in ('LR', 'RL')
        alt = one({**graph, 'direction': 'TB' if horizontal else 'LR'})
        if alt['fits'] and alt['score'] < res['score'] - 1 and alt['size'] / alt['W'] >= FLIP_GAIN * (res['size'] / res['W']):
            res = alt
    return res


def _layout_curve(graph, opts):
    fit = opts.get('fit') or 'balanced'
    target_w = opts.get('targetW') or 1000
    max_h = opts.get('maxH') or 1100

    def sized(gr):
        def try_s(s):
            return _frame(gr, choose_layout(gr, s, fit), s)
        s = _clamp_size(opts['size']) if opts.get('size') else 18
        res = try_s(s)
        if not opts.get('size'):
            for _ in range(4):
                k = min(target_w / res['W'], max_h / res['H'])
                ns = max(10, min(40, js_round(s * k)))
                if ns == s or (k > 0.85 and k < 1.12):
                    break
                s = ns
                res = try_s(s)
        while (res['W'] > 2000 or res['H'] > 2000) and s > 8:
            s -= 1
            res = try_s(s)
        res['fits'] = res['W'] <= 2000 and res['H'] <= 2000
        res['direction'] = gr['direction']
        return res

    def phone(r):
        return (r['size'] * 343) / r['W']

    def bad(r):
        return r['metrics']['crossings'] + r['metrics']['throughBoxes'] + r['metrics']['labelsOnBoxes'] + 2 * r['metrics']['labelOverlaps']
    res = sized(graph)
    if not opts.get('forceDirection') and phone(res) < 7:
        horizontal = graph['direction'] in ('LR', 'RL')
        alt = sized({**graph, 'direction': 'TB' if horizontal else 'LR'})
        if alt['fits'] and phone(alt) > phone(res) * 1.3 and bad(alt) <= bad(res) + 3:
            res = alt
    return res


def _frame(graph, best, s):
    layout, curves = best['layout'], best['curves']
    boxes = _as_boxes(layout)
    margin = js_round(1.3 * s)
    b = {'x0': INF, 'y0': INF, 'x1': -INF, 'y1': -INF}

    def take(x, y, w=0, h=0):
        b['x0'] = min(b['x0'], x)
        b['y0'] = min(b['y0'], y)
        b['x1'] = max(b['x1'], x + w)
        b['y1'] = max(b['y1'], y + h)
    for n in layout['nodes']:
        take(n['x'], n['y'], n['w'], n['h'])
    for g in layout['groups']:
        take(g['x'], g['y'], g['w'], g['h'])
    for i, e in enumerate(graph['edges']):
        P = edge_curve(boxes[e['from']], boxes[e['to']], curves[i])
        for k in range(9):
            q = quad(P, k / 8)
            take(q[0] - 2, q[1] - 2, 4, 4)
        if e.get('label'):
            r = label_rect(P, e['label'], s)
            take(r['x'], r['y'], r['w'], r['h'])
    x0, y0, x1, y1 = b['x0'], b['y0'], b['x1'], b['y1']
    if not math.isfinite(x0):
        x0 = y0 = 0
        x1 = y1 = 100
    dx, dy = margin - x0, margin - y0
    W = max(200, math.ceil(x1 - x0 + 2 * margin))
    H = max(120, math.ceil(y1 - y0 + 2 * margin))

    def shift(o):
        return {**o, 'x': o['x'] + dx, 'y': o['y'] + dy}
    nodes = [shift(n) for n in layout['nodes']]
    groups = [shift(g) for g in layout['groups']]
    return {'W': W, 'H': H, 'size': s, 'nodes': nodes, 'groups': groups, 'curves': curves,
            'direction': best.get('direction') or graph['direction'], 'flows': list(best['flows'].items()),
            'metrics': measure(graph, {**layout, 'nodes': nodes, 'groups': groups}, curves)}


def _frame_routed(graph, best, rt, s):
    layout = best['layout']
    margin = js_round(1.3 * s)
    b = {'x0': INF, 'y0': INF, 'x1': -INF, 'y1': -INF}

    def take(x, y, w=0, h=0):
        b['x0'] = min(b['x0'], x)
        b['y0'] = min(b['y0'], y)
        b['x1'] = max(b['x1'], x + w)
        b['y1'] = max(b['y1'], y + h)
    for n in layout['nodes']:
        take(n['x'], n['y'], n['w'], n['h'])
    for g in layout['groups']:
        take(g['x'], g['y'], g['w'], g['h'])
    for r in rt['routes']:
        if not r:
            continue
        for p in r['points']:
            take(p[0] - 2, p[1] - 2, 4, 4)
        if r['label']:
            take(r['label']['x'], r['label']['y'], r['label']['w'], r['label']['h'])
    x0, y0, x1, y1 = b['x0'], b['y0'], b['x1'], b['y1']
    if not math.isfinite(x0):
        x0 = y0 = 0
        x1 = y1 = 100
    dx, dy = margin - x0, margin - y0
    W = max(200, math.ceil(x1 - x0 + 2 * margin))
    H = max(120, math.ceil(y1 - y0 + 2 * margin))

    def shift(o):
        return {**o, 'x': o['x'] + dx, 'y': o['y'] + dy}
    routes = [({**r, 'points': [[p[0] + dx, p[1] + dy] for p in r['points']], 'label': shift(r['label']) if r['label'] else None} if r else None) for r in rt['routes']]
    failed = sum(1 for i, e in enumerate(graph['edges']) if not routes[i] and e['from'] != e['to'])
    return {'W': W, 'H': H, 'size': s, 'routing': 'orthogonal', 'routes': routes, 'routeWarnings': rt['warnings'], 'failed': failed,
            'nodes': [shift(n) for n in layout['nodes']], 'groups': [shift(g) for g in layout['groups']], 'curves': [0 for _ in graph['edges']],
            'direction': graph['direction'], 'flows': list(best['flows'].items()), 'metrics': rt['metrics']}


def common_metrics(graph, lay, chips=None):
    layout = {'nodes': lay['nodes'], 'groups': lay['groups'], 's': lay['size']}
    glabels = [group_title_rect(g, next(x for x in graph['groups'] if x['id'] == g['id']), lay['size']) for g in lay['groups']]
    routes = lay.get('routes') or curve_routes(graph, layout, lay['curves'], edge_curve, label_rect)
    return route_metrics(graph, layout, routes, glabels, lay['size'], chips or {})
