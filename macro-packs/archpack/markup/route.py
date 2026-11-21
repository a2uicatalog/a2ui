"""Orthogonal edge router and edge-label placement (port of mermaid_arch/route.mjs). Deterministic.

routeEdges(graph, layout, opts) -> {routes, warnings, metrics}
  routes[i] = {'points': [[x, y], ...] (rim to rim, axis-aligned), 'label': {x, y, w, h} | None, 'via': 'grid'}

An edge is an A* search over (cell, heading) on a uniform grid laid over the drawing, with a cost for distance, for every
bend, for cells other edges already use, for cells inside a group the edge does not belong to, and for running along a group
border. Edges are routed shortest first in input order, so the result is byte-stable. Labels go on the longest free straight
stretch and are checked against every box, group title, other label and other edge.
"""
from __future__ import annotations

import math
from heapq import heappop as _pop, heappush as _push

from ._js import js_round

E, S, W, N = 0, 1, 2, 3
DX = (1, 0, -1, 0)
DY = (0, 1, 0, -1)
INF = float('inf')


class _Heap:
    """Binary min-heap on (f, insertion order), compared with the same 1e-9 tolerance as the JS version."""
    __slots__ = ('f', 'k', 'id', 'pt', 'n', 'topF', 'topId', 'topPort')

    def __init__(self):
        self.f = []
        self.k = []
        self.id = []
        self.pt = []
        self.n = 0
        self.topF = 0.0
        self.topId = 0
        self.topPort = -1

    def lt(self, i, j):
        f = self.f
        d = f[i] - f[j]
        return f[i] < f[j] - 1e-9 or (abs(d) <= 1e-9 and self.k[i] < self.k[j])

    def swap(self, i, j):
        for a in (self.f, self.k, self.id, self.pt):
            a[i], a[j] = a[j], a[i]

    def push(self, f, id_, port):
        self.f.append(f)
        self.k.append(self.n)
        self.id.append(id_)
        self.pt.append(port)
        self.n += 1
        i = len(self.f) - 1
        while i > 0:
            p = (i - 1) >> 1
            if self.lt(i, p):
                self.swap(i, p)
                i = p
            else:
                break

    def pop(self):
        self.topF = self.f[0]
        self.topId = self.id[0]
        self.topPort = self.pt[0]
        last = len(self.f) - 1
        if last > 0:
            self.f[0] = self.f[last]
            self.k[0] = self.k[last]
            self.id[0] = self.id[last]
            self.pt[0] = self.pt[last]
        for a in (self.f, self.k, self.id, self.pt):
            a.pop()
        if last > 0:
            i = 0
            while True:
                l = 2 * i + 1
                r = l + 1
                m = i
                if l < last and self.lt(l, m):
                    m = l
                if r < last and self.lt(r, m):
                    m = r
                if m == i:
                    break
                self.swap(i, m)
                i = m

    def __len__(self):
        return len(self.f)


def rects_overlap(a, b):
    return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']


def inflate(r, m):
    return {'x': r['x'] - m, 'y': r['y'] - m, 'w': r['w'] + 2 * m, 'h': r['h'] + 2 * m}


def group_title_rect(g, gl, s):
    from .layout import group_label_width
    return {'x': g['x'] + 12, 'y': g['y'] + 6, 'w': group_label_width(gl['label'], s) - 20, 'h': 24}


def seg_hits_rect(a, b, r, m=0):
    x0, x1 = min(a[0], b[0]), max(a[0], b[0])
    y0, y1 = min(a[1], b[1]), max(a[1], b[1])
    return x1 > r['x'] + m and x0 < r['x'] + r['w'] - m and y1 > r['y'] + m and y0 < r['y'] + r['h'] - m


def axis_cross(a1, a2, b1, b2):
    ah = a1[1] == a2[1]
    bh = b1[1] == b2[1]
    if ah == bh:
        return False
    if ah:
        h1, h2, v1, v2 = a1, a2, b1, b2
    else:
        h1, h2, v1, v2 = b1, b2, a1, a2
    hx0, hx1 = min(h1[0], h2[0]), max(h1[0], h2[0])
    vy0, vy1 = min(v1[1], v2[1]), max(v1[1], v2[1])
    return v1[0] > hx0 + 0.5 and v1[0] < hx1 - 0.5 and h1[1] > vy0 + 0.5 and h1[1] < vy1 - 0.5


def diag_cross(a, b, c, d):
    if a[0] == b[0] or a[1] == b[1] or c[0] == d[0] or c[1] == d[1]:
        return False

    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return o(c, d, a) * o(c, d, b) < 0 and o(a, b, c) * o(a, b, d) < 0


def _segs(points):
    return [(points[i], points[i + 1]) for i in range(len(points) - 1)]


_DIRS = ((0, 1, 3), (1, 2, 0), (2, 3, 1), (3, 0, 2))   # straight, then the two turns, for each heading


def route_edges(graph, layout, opts=None):
    opts = opts or {}
    from .layout import edge_label_size
    s = layout['s']
    warnings = []
    g = max(8, js_round(0.55 * s))
    clear = max(6, js_round(0.42 * s))
    port0 = max(clear + 3, 15)
    node_by_id = {n['id']: n for n in layout['nodes']}
    boxes = layout['nodes']
    gl_by_id = {x['id']: x for x in graph['groups']}
    glabels = [group_title_rect(gr, gl_by_id[gr['id']], s) for gr in layout['groups']]
    x0 = y0 = INF
    x1 = y1 = -INF
    for r in [*boxes, *layout['groups']]:
        x0 = min(x0, r['x'])
        y0 = min(y0, r['y'])
        x1 = max(x1, r['x'] + r['w'])
        y1 = max(y1, r['y'] + r['h'])
    if not math.isfinite(x0):
        x0 = y0 = 0
        x1 = y1 = 100
    pad = 5 * g
    ox = x0 - pad
    oy = y0 - pad
    cols = math.ceil((x1 - x0 + 2 * pad) / g)
    rows = math.ceil((y1 - y0 + 2 * pad) / g)
    NC = cols * rows
    CXs = [ox + (i + 0.5) * g for i in range(cols)]
    CYs = [oy + (j + 0.5) * g for j in range(rows)]
    blocked = [0] * NC

    def ci(x):
        return math.floor((x - ox) / g)

    def cj(y):
        return math.floor((y - oy) / g)

    def fill_rect(r, m, arr, val=1):
        i0 = max(0, ci(r['x'] - m))
        i1 = min(cols - 1, ci(r['x'] + r['w'] + m))
        j0 = max(0, cj(r['y'] - m))
        j1 = min(rows - 1, cj(r['y'] + r['h'] + m))
        xa, xb, ya, yb = r['x'] - m, r['x'] + r['w'] + m, r['y'] - m, r['y'] + r['h'] + m
        for j in range(j0, j1 + 1):
            py = CYs[j]
            if not (py > ya and py < yb):
                continue
            base = j * cols
            for i in range(i0, i1 + 1):
                px = CXs[i]
                if px > xa and px < xb:
                    arr[base + i] = val
    for b in boxes:
        fill_rect(b, clear, blocked)
    for t in glabels:
        fill_rect(t, 3, blocked)
    cell_group = [-1] * NC
    for k, gr in enumerate(layout['groups']):
        fill_rect(gr, 0, cell_group, k)
    h_border = [0] * NC
    v_border = [0] * NC
    for gr in layout['groups']:
        for i in range(cols):
            for yy in (gr['y'], gr['y'] + gr['h']):
                j = cj(yy)
                px = CXs[i]
                if px >= gr['x'] - g and px <= gr['x'] + gr['w'] + g and 0 <= j < rows and abs(CYs[j] - yy) <= 0.6 * g:
                    h_border[j * cols + i] = 1
        for j in range(rows):
            for xx in (gr['x'], gr['x'] + gr['w']):
                i = ci(xx)
                py = CYs[j]
                if py >= gr['y'] - g and py <= gr['y'] + gr['h'] + g and 0 <= i < cols and abs(CXs[i] - xx) <= 0.6 * g:
                    v_border[j * cols + i] = 1
    group_idx = {gr['id']: k for k, gr in enumerate(layout['groups'])}
    group_of_node = {n['id']: (group_idx[n['group']] if (n.get('group') and n['group'] in group_idx) else -1) for n in graph['nodes']}
    near = [0] * NC
    for b in boxes:
        fill_rect(b, clear + 1.5 * g, near)

    used_h = [0] * NC
    used_v = [0] * NC
    scale = opts.get('bendScale') or 1
    BEND = 34 * scale
    OVERLAP, CROSS, FOREIGN, OWN_OUT, BORDER, NEAR, SIDE = 420, 70, 14, 7, 12, 3.5, 0.18

    def ports(b):
        out = []
        cm = 14
        bx, by, bw, bh = b['x'], b['y'], b['w'], b['h']
        midy = by + bh / 2
        midx = bx + bw / 2
        i0 = max(0, ci(bx - port0 - g))
        i1 = min(cols - 1, ci(bx + bw + port0 + g))
        j0 = max(0, cj(by - port0 - g))
        j1 = min(rows - 1, cj(by + bh + port0 + g))
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                if blocked[j * cols + i]:
                    continue
                px, py = CXs[i], CYs[j]
                if px >= bx + bw + port0 and px < bx + bw + port0 + g and py > by + cm and py < by + bh - cm:
                    out.append({'cell': j * cols + i, 'i': i, 'j': j, 'out': E, 'side': abs(py - midy) * SIDE})
                if px <= bx - port0 and px > bx - port0 - g and py > by + cm and py < by + bh - cm:
                    out.append({'cell': j * cols + i, 'i': i, 'j': j, 'out': W, 'side': abs(py - midy) * SIDE})
                if py >= by + bh + port0 and py < by + bh + port0 + g and px > bx + cm and px < bx + bw - cm:
                    out.append({'cell': j * cols + i, 'i': i, 'j': j, 'out': S, 'side': abs(px - midx) * SIDE})
                if py <= by - port0 and py > by - port0 - g and px > bx + cm and px < bx + bw - cm:
                    out.append({'cell': j * cols + i, 'i': i, 'j': j, 'out': N, 'side': abs(px - midx) * SIDE})
        return out

    port_memo = {}
    succ = [None] * (NC * 4)   # neighbour table per state (blocked never changes within a route_edges call)

    def ports_of(b):
        l = port_memo.get(b['id'])
        if l is None:
            l = ports(b)
            port_memo[b['id']] = l
        return l

    def route(e, k, scl, fast=True):
        fb = node_by_id[e['from']]
        tb = node_by_id[e['to']]
        sg = group_of_node.get(e['from'])
        tg = group_of_node.get(e['to'])

        # cell_cost is pure for the whole call (used_h/used_v only change between calls), so it is memoised per cell and axis.
        cost2 = [None] * (NC * 2)   # index cell * 2 + (1 if the step runs along x)

        def cell_cost(c, axis_h):
            k2 = cost2[c * 2 + (1 if axis_h else 0)]
            if k2 is not None:
                return k2
            k2 = 0
            if (used_h[c] if axis_h else used_v[c]):
                k2 += OVERLAP
            if (used_v[c] if axis_h else used_h[c]):
                k2 += CROSS
            cg = cell_group[c]
            if cg >= 0 and cg != sg and cg != tg:
                k2 += FOREIGN
            elif cg < 0 and sg >= 0 and sg == tg:
                k2 += OWN_OUT
            if (h_border[c] if axis_h else v_border[c]):
                k2 += BORDER
            if near[c]:
                k2 += NEAR
            cost2[c * 2 + (1 if axis_h else 0)] = k2
            return k2
        dist = [INF] * (NC * 4)
        prev = [-1] * (NC * 4)
        t_port_list = ports_of(tb)
        t_map = {}
        for pi, p in enumerate(t_port_list):
            t_map.setdefault(p['cell'], []).append(pi)
        tx0, tx1, ty0, ty1 = tb['x'], tb['x'] + tb['w'], tb['y'], tb['y'] + tb['h']
        # distance to the target box, per column and per row (the sum dx + dy is formed in the same order as before)
        hdx = [(tx0 - px if tx0 - px > 0 else (px - tx1 if px - tx1 > 0 else 0)) for px in CXs]
        hdy = [(ty0 - py if ty0 - py > 0 else (py - ty1 if py - ty1 > 0 else 0)) for py in CYs]

        if fast:
            # Fast path: C heapq on (key, insertion order, f, ...), where key = int(f * 1e7 + 0.5). The exact heap below treats f values within
            # 1e-9 as equal (the JS does too), so float noise in sums that are mathematically the same falls to insertion order.
            # The key gives the same order when every pushed f belongs to a cluster of width <= 5e-10 that has the same key and
            # lies more than 2e-9 from the next cluster; that is checked after the search, and the route is searched again with the
            # exact heap when it fails.
            heap = []
            fs = []
            hn = 0
            for p in ports_of(fb):
                id_ = p['cell'] * 4 + p['out']
                c0 = p['side'] + cell_cost(p['cell'], p['out'] == E or p['out'] == W)
                if c0 < dist[id_]:
                    dist[id_] = c0
                    prev[id_] = -2 - p['out']
                    f = c0 + (hdx[p['i']] + hdy[p['j']])
                    fs.append(f)
                    _push(heap, (int(f * 1e7 + 0.5), hn, f, id_, -1))
                    hn += 1
            end = -1
            end_cost = INF
            end_port = None
            bend_s = BEND * scl
            dirs = _DIRS
            ub = INF   # f of the cheapest target-port entry pushed so far; anything above it can never be popped before the search ends
            while heap:
                _key, _k, top_f, id_, top_pt = _pop(heap)
                if top_pt >= 0:
                    end = id_
                    end_cost = top_f
                    end_port = t_port_list[top_pt]
                    break
                cell = id_ >> 2
                d = id_ & 3
                gcost = dist[id_]
                j, i = divmod(cell, cols)
                if top_f > gcost + (hdx[i] + hdy[j]) + 1e-6:
                    continue
                tp = t_map.get(cell)
                if tp:
                    for pi in tp:
                        p = t_port_list[pi]
                        inward = (p['out'] + 2) & 3
                        f = gcost + p['side'] + (0 if d == inward else bend_s)
                        if f < ub:
                            ub = f
                        fs.append(f)
                        _push(heap, (int(f * 1e7 + 0.5), hn, f, id_, pi))
                        hn += 1
                sc = succ[id_]
                if sc is None:
                    sc = []
                    for nd in dirs[d]:
                        ni = i + DX[nd]
                        nj = j + DY[nd]
                        if ni < 0 or nj < 0 or ni >= cols or nj >= rows:
                            continue
                        nc = nj * cols + ni
                        if blocked[nc]:
                            continue
                        sc.append((nc * 4 + nd, nc, 1 if (nd == E or nd == W) else 0, nd == d, ni, nj))
                    succ[id_] = sc
                base = gcost + g
                turn = base + bend_s
                for nid, nc, hz, straight, ni, nj in sc:
                    cc = cost2[nc * 2 + hz]
                    if cc is None:
                        cc = cell_cost(nc, hz == 1)
                    cost = (base if straight else turn) + cc
                    if cost < dist[nid] - 1e-9:
                        dist[nid] = cost
                        prev[nid] = id_
                        f = cost + (hdx[ni] + hdy[nj])
                        hn += 1
                        if f > ub + 1e-6:
                            continue
                        fs.append(f)
                        _push(heap, (int(f * 1e7 + 0.5), hn - 1, f, nid, -1))
            fs.sort()
            g0 = fs[0] if fs else 0.0
            kp = int(g0 * 1e7 + 0.5)
            for q in range(1, len(fs)):
                fq = fs[q]
                kq = int(fq * 1e7 + 0.5)
                if kq == kp:
                    if fq - g0 > 5e-10:
                        return route(e, k, scl, False)
                else:
                    if fq - fs[q - 1] <= 2e-9:
                        return route(e, k, scl, False)
                    g0 = fq
                    kp = kq
        else:
            # Binary min-heap of (f, insertion order, state, port). Ordering is f with the 1e-9 tolerance, ties by insertion order.
            # Hole-style sifts make the same comparisons, in the same order, as swap-style sifts, so the layout is the same.
            heap = []
            hn = 0
            for p in ports_of(fb):
                id_ = p['cell'] * 4 + p['out']
                c0 = p['side'] + cell_cost(p['cell'], p['out'] == E or p['out'] == W)
                if c0 < dist[id_]:
                    dist[id_] = c0
                    prev[id_] = -2 - p['out']
                    f = c0 + (hdx[p['i']] + hdy[p['j']])
                    i = len(heap)
                    heap.append(None)
                    while i > 0:
                        pp = (i - 1) >> 1
                        par = heap[pp]
                        pf = par[0]
                        if f < pf - 1e-9 or (abs(f - pf) <= 1e-9 and hn < par[1]):
                            heap[i] = par
                            i = pp
                        else:
                            break
                    heap[i] = (f, hn, id_, -1)
                    hn += 1
            end = -1
            end_cost = INF
            end_port = None
            bend_s = BEND * scl
            dirs = _DIRS
            while heap:
                top = heap[0]
                last_item = heap.pop()
                n = len(heap)
                if n:
                    i = 0
                    lf = last_item[0]
                    lk = last_item[1]
                    while True:
                        l = 2 * i + 1
                        if l >= n:
                            break
                        cf, ck = lf, lk
                        m = -1
                        mi = heap[l]
                        xf = mi[0]
                        if xf < cf - 1e-9 or (abs(xf - cf) <= 1e-9 and mi[1] < ck):
                            m = l
                            cf, ck = xf, mi[1]
                        r = l + 1
                        if r < n:
                            ri = heap[r]
                            xf = ri[0]
                            if xf < cf - 1e-9 or (abs(xf - cf) <= 1e-9 and ri[1] < ck):
                                m = r
                                mi = ri
                        if m < 0:
                            break
                        heap[i] = mi
                        i = m
                    heap[i] = last_item
                top_f, _k, id_, top_pt = top
                if top_pt >= 0:
                    end = id_
                    end_cost = top_f
                    end_port = t_port_list[top_pt]
                    break
                cell = id_ >> 2
                d = id_ & 3
                gcost = dist[id_]
                j, i = divmod(cell, cols)
                if top_f > gcost + (hdx[i] + hdy[j]) + 1e-6:
                    continue
                tp = t_map.get(cell)
                if tp:
                    for pi in tp:
                        p = t_port_list[pi]
                        inward = (p['out'] + 2) & 3
                        f = gcost + p['side'] + (0 if d == inward else bend_s)
                        ii = len(heap)
                        heap.append(None)
                        while ii > 0:
                            pp = (ii - 1) >> 1
                            par = heap[pp]
                            pf = par[0]
                            if f < pf - 1e-9 or (abs(f - pf) <= 1e-9 and hn < par[1]):
                                heap[ii] = par
                                ii = pp
                            else:
                                break
                        heap[ii] = (f, hn, id_, pi)
                        hn += 1
                sc = succ[id_]
                if sc is None:
                    sc = []
                    for nd in dirs[d]:
                        ni = i + DX[nd]
                        nj = j + DY[nd]
                        if ni < 0 or nj < 0 or ni >= cols or nj >= rows:
                            continue
                        nc = nj * cols + ni
                        if blocked[nc]:
                            continue
                        sc.append((nc * 4 + nd, nc, 1 if (nd == E or nd == W) else 0, nd == d, ni, nj))
                    succ[id_] = sc
                base = gcost + g
                turn = base + bend_s
                for nid, nc, hz, straight, ni, nj in sc:
                    cc = cost2[nc * 2 + hz]
                    if cc is None:
                        cc = cell_cost(nc, hz == 1)
                    cost = (base if straight else turn) + cc
                    if cost < dist[nid] - 1e-9:
                        dist[nid] = cost
                        prev[nid] = id_
                        f = cost + (hdx[ni] + hdy[nj])
                        ii = len(heap)
                        heap.append(None)
                        while ii > 0:
                            pp = (ii - 1) >> 1
                            par = heap[pp]
                            pf = par[0]
                            if f < pf - 1e-9 or (abs(f - pf) <= 1e-9 and hn < par[1]):
                                heap[ii] = par
                                ii = pp
                            else:
                                break
                        heap[ii] = (f, hn, nid, -1)
                        hn += 1
        if end < 0:
            return None
        cells = []
        id_ = end
        while id_ >= 0:
            cells.append((id_ >> 2, id_ & 3))
            id_ = prev[id_]
        start_dir = -2 - id_
        cells.reverse()
        first = cells[0][0]
        fi, fj = first % cols, first // cols
        pts = []
        if start_dir == E:
            pts.append([fb['x'] + fb['w'], CYs[fj]])
        elif start_dir == W:
            pts.append([fb['x'], CYs[fj]])
        elif start_dir == S:
            pts.append([CXs[fi], fb['y'] + fb['h']])
        else:
            pts.append([CXs[fi], fb['y']])
        for c, _d in cells:
            pts.append([CXs[c % cols], CYs[c // cols]])
        last_c = cells[-1][0]
        li, lj = last_c % cols, last_c // cols
        eo = end_port['out']
        if eo == E:
            pts.append([tb['x'] + tb['w'], CYs[lj]])
        elif eo == W:
            pts.append([tb['x'], CYs[lj]])
        elif eo == S:
            pts.append([CXs[li], tb['y'] + tb['h']])
        else:
            pts.append([CXs[li], tb['y']])
        out = [pts[0]]
        for q in range(1, len(pts) - 1):
            a, b, c = out[-1], pts[q], pts[q + 1]
            if (a[0] == b[0] and b[0] == c[0]) or (a[1] == b[1] and b[1] == c[1]):
                continue
            out.append(b)
        out.append(pts[-1])
        return {'points': out, 'cells': [c[0] for c in cells], 'cost': end_cost}

    def dist_key(a):
        ea = graph['edges'][a]
        return abs(node_by_id[ea['from']]['x'] - node_by_id[ea['to']]['x']) + abs(node_by_id[ea['from']]['y'] - node_by_id[ea['to']]['y'])
    order = sorted(range(len(graph['edges'])), key=lambda a: (dist_key(a), a))
    routes = [None] * len(graph['edges'])
    for k in order:
        e = graph['edges'][k]
        if e['from'] not in node_by_id or e['to'] not in node_by_id or e['from'] == e['to']:
            continue
        r = None
        for scl in (1, 3, 8):
            r = route(e, k, scl)
            if r and len(r['points']) <= 10:
                break
            if r and scl == 8:
                r = None
        if not r:
            warnings.append('edge %d (%s -> %s): no clear orthogonal route was found, so it is drawn as a curve.' % (k + 1, e['from'], e['to']))
            continue
        cs = r['cells']
        for q in range(len(cs)):
            c = cs[q]
            pc = cs[q - 1] if q else c
            nc2 = cs[q + 1] if q + 1 < len(cs) else c

            def horiz(a, b):
                return a // cols == b // cols

            def vert(a, b):
                return a % cols == b % cols
            if (q and horiz(c, pc) and c != pc) or (q + 1 < len(cs) and horiz(c, nc2) and c != nc2):
                used_h[c] = 1
            if (q and vert(c, pc) and c != pc) or (q + 1 < len(cs) and vert(c, nc2) and c != nc2):
                used_v[c] = 1
            if len(cs) == 1:
                used_h[c] = 1
                used_v[c] = 1
        routes[k] = {'points': r['points'], 'via': 'grid', 'label': None}

    place_labels(graph, layout, routes, glabels, s, warnings, opts.get('chips') or {})
    return {'routes': routes, 'warnings': warnings, 'metrics': route_metrics(graph, layout, routes, glabels, s, opts.get('chips') or {})}


def chip_bands(graph, routes, chips, s):
    out = []
    for k, r in enumerate(routes):
        if not r or not chips.get(k):
            continue
        hw = (chips[k] * (s - 4) * 0.62 + 22) / 2
        hh = 14
        for a, b in _segs(r['points']):
            x0, x1 = min(a[0], b[0]), max(a[0], b[0])
            y0, y1 = min(a[1], b[1]), max(a[1], b[1])
            out.append({'k': k, 'x': x0 - hw, 'y': y0 - hh, 'w': x1 - x0 + 2 * hw, 'h': y1 - y0 + 2 * hh})
    return out


def place_labels(graph, layout, routes, glabels, s, warnings, chips=None):
    from .layout import edge_label_size
    chips = chips or {}
    boxes = layout['nodes']
    placed_i = []
    all_segs = [(_segs(r['points']) if r else []) for r in routes]
    lab_w = {}

    def lw(i):
        if i not in lab_w:
            lab_w[i] = edge_label_size(graph['edges'][i]['label'], s)
        return lab_w[i]
    order = sorted([i for i in range(len(graph['edges'])) if graph['edges'][i].get('label') and routes[i]], key=lambda i: (-lw(i)['w'], i))
    gap = 3
    bands = chip_bands(graph, routes, chips, s)
    boxes_i = [inflate(b, 2) for b in boxes]
    glabels_i = [inflate(t, 1) for t in glabels]

    def _tup(r):
        return (r['x'], r['x'] + r['w'], r['y'], r['y'] + r['h'])
    bands_t = [_tup(bd) for bd in bands]
    boxes_t = [_tup(b) for b in boxes_i]
    glabels_t = [_tup(t) for t in glabels_i]
    placed_t = []
    sx0, sx1, sy0, sy1, sq = [], [], [], [], []
    for q, ss in enumerate(all_segs):
        for a, b in ss:
            sx0.append(min(a[0], b[0]))
            sx1.append(max(a[0], b[0]))
            sy0.append(min(a[1], b[1]))
            sy1.append(max(a[1], b[1]))
            sq.append(q)
    n_seg = len(sq)
    for k in order:
        e = graph['edges'][k]
        sz = lw(k)
        r = routes[k]
        chip_len = chips.get(k) or 0
        chip_half_w = (chip_len * (s - 4) * 0.62 + 22) / 2 if chip_len else 0
        chip_half_h = 14 if chip_len else 0
        gap_h = chip_half_h + 3 if chip_len else gap
        gap_v = chip_half_w + 3 if chip_len else gap
        cands = []
        for si, (a, b) in enumerate(_segs(r['points'])):
            horiz = a[1] == b[1]
            ln = abs(b[0] - a[0]) if horiz else abs(b[1] - a[1])
            lo = min(a[0], b[0]) if horiz else min(a[1], b[1])
            need = sz['w'] if horiz else sz['h']
            margin = 14
            span = ln - 2 * margin - need
            offs = []
            if span >= -0.5:
                offs.append(0)
                d = 6
                while d <= span / 2 + 0.01:
                    offs.append(d)
                    offs.append(-d)
                    d += 6
            elif ln - need >= 4:
                offs.append(0)
            mid = lo + ln / 2
            for d in offs:
                c = mid + d
                if horiz:
                    x = c - sz['w'] / 2
                    y = a[1]
                    cands.append({'x': x, 'y': y - gap_h - sz['h'], 'w': sz['w'], 'h': sz['h'], 'pref': 0, 'si': si, 'd': d, 'len': ln, 'gp': gap_h})
                    cands.append({'x': x, 'y': y + gap_h, 'w': sz['w'], 'h': sz['h'], 'pref': 1.5, 'si': si, 'd': d, 'len': ln, 'gp': gap_h})
                    if not chip_len:
                        cands.append({'x': x, 'y': y - sz['h'] / 2, 'w': sz['w'], 'h': sz['h'], 'pref': 4, 'si': si, 'd': d, 'len': ln, 'on': True})
                else:
                    y = c - sz['h'] / 2
                    xx = a[0]
                    cands.append({'x': xx + gap_v, 'y': y, 'w': sz['w'], 'h': sz['h'], 'pref': 0.5 + (6 if chip_len else 0), 'si': si, 'd': d, 'len': ln, 'gp': gap_v})
                    cands.append({'x': xx - gap_v - sz['w'], 'y': y, 'w': sz['w'], 'h': sz['h'], 'pref': 1.5 + (6 if chip_len else 0), 'si': si, 'd': d, 'len': ln, 'gp': gap_v})
                    if not chip_len:
                        cands.append({'x': xx - sz['w'] / 2, 'y': y, 'w': sz['w'], 'h': sz['h'], 'pref': 5, 'si': si, 'd': d, 'len': ln, 'on': True})
        best = None
        for c in cands:
            hard = 0
            soft = 0
            chip_hit = 0
            cx0, cx1, cy0, cy1 = c['x'], c['x'] + c['w'], c['y'], c['y'] + c['h']
            for bx0, bx1, by0, by1 in bands_t:
                if cx0 < bx1 and bx0 < cx1 and cy0 < by1 and by0 < cy1:
                    chip_hit += 1
            for bx0, bx1, by0, by1 in boxes_t:
                if cx0 < bx1 and bx0 < cx1 and cy0 < by1 and by0 < cy1:
                    hard += 1
            for bx0, bx1, by0, by1 in glabels_t:
                if cx0 < bx1 and bx0 < cx1 and cy0 < by1 and by0 < cy1:
                    hard += 1
            for bx0, bx1, by0, by1 in placed_t:
                if cx0 < bx1 and bx0 < cx1 and cy0 < by1 and by0 < cy1:
                    hard += 1
            tail = c['pref'] + abs(c['d']) * 0.08 - min(c['len'], 400) * 0.01
            if best and not (hard * 1000 + chip_hit * 150 + 0 + 0 + 0 + tail < best['cost'] - 1e-9):
                continue
            ix0, ix1 = c['x'] - 1, (c['x'] - 1) + (c['w'] + 2)
            iy0, iy1 = c['y'] - 1, (c['y'] - 1) + (c['h'] + 2)
            for t in range(n_seg):
                x0, x1, y0, y1 = sx0[t], sx1[t], sy0[t], sy1[t]
                if sq[t] == k:
                    if not c.get('on') and x1 > cx0 + 0.5 and x0 < cx1 - 0.5 and y1 > cy0 + 0.5 and y0 < cy1 - 0.5:
                        soft += 0.2
                elif x1 > ix0 and x0 < ix1 and y1 > iy0 and y0 < iy1:
                    soft += 1
            between = 0
            if not c.get('on'):
                own = r['points'][c['si']]
                own2 = r['points'][c['si'] + 1]
                horiz = own[1] == own2[1]
                for t in range(n_seg):
                    if sq[t] == k:
                        continue
                    x0, x1, y0, y1 = sx0[t], sx1[t], sy0[t], sy1[t]
                    if horiz and y0 == y1:
                        if x1 > c['x'] and x0 < c['x'] + c['w'] and ((y0 > own[1] and y0 < c['y'] + c['h'] / 2) or (y0 < own[1] and y0 > c['y'] + c['h'] / 2)):
                            between = 1
                    elif not horiz and x0 == x1:
                        if y1 > c['y'] and y0 < c['y'] + c['h'] and ((x0 > own[0] and x0 < c['x'] + c['w'] / 2) or (x0 < own[0] and x0 > c['x'] + c['w'] / 2)):
                            between = 1
            own_d = 0 if c.get('on') else (c.get('gp') or gap)
            lim = own_d + 4
            closer = 0
            for t in range(n_seg):
                if sq[t] == k:
                    continue
                dx = max(c['x'] - sx1[t], 0, sx0[t] - (c['x'] + c['w']))
                dy = max(c['y'] - sy1[t], 0, sy0[t] - (c['y'] + c['h']))
                if dx < lim and dy < lim and math.hypot(dx, dy) < lim:
                    closer = 1
                    break
            cost = hard * 1000 + chip_hit * 150 + soft * 200 + closer * 150 + between * 25 + c['pref'] + abs(c['d']) * 0.08 - min(c['len'], 400) * 0.01
            if not best or cost < best['cost'] - 1e-9:
                best = {'c': c, 'cost': cost, 'hard': hard, 'soft': soft}
        if not best:
            pts = r['points']
            m = len(pts) // 2
            mx = (pts[m - 1][0] + pts[m][0]) / 2
            my = (pts[m - 1][1] + pts[m][1]) / 2
            best = {'c': {'x': mx - sz['w'] / 2, 'y': my - sz['h'] / 2, 'w': sz['w'], 'h': sz['h']}, 'hard': 1, 'soft': 0, 'cost': 1e9}
            warnings.append('edge %d: its label "%s" does not fit on a straight stretch of the route; it sits on a bend. Shorten the label.' % (k + 1, e['label'].replace('\n', ' ')))
        elif best['hard']:
            warnings.append('edge %d: the label "%s" overlaps a box or another label (no free place was found). Shorten it or give the diagram more room.' % (k + 1, e['label'].replace('\n', ' ')))
        c = best['c']
        r['label'] = {'x': c['x'], 'y': c['y'], 'w': c['w'], 'h': c['h']}
        placed_i.append(inflate(r['label'], 3))
        placed_t.append(_tup(placed_i[-1]))


def route_metrics(graph, layout, routes, glabels, s, chips=None):
    chips = chips or {}
    boxes = layout['nodes']
    lines = [(r['points'] if r else None) for r in routes]
    through_boxes = title_hits = label_node = label_label = label_title = label_on_line = crossings = bends = 0
    length = 0
    L = []
    for k, r in enumerate(routes):
        if not r:
            continue
        e = graph['edges'][k]
        ps = r['points']
        bends += max(0, len(ps) - 2)
        if r.get('curve'):
            for bx in boxes:
                own = bx['id'] == e['from'] or bx['id'] == e['to']
                m = 3 if own else 0
                if any(p[0] > bx['x'] + m and p[0] < bx['x'] + bx['w'] - m and p[1] > bx['y'] + m and p[1] < bx['y'] + bx['h'] - m for p in ps):
                    through_boxes += 1
            for t in glabels:
                if any(p[0] > t['x'] and p[0] < t['x'] + t['w'] and p[1] > t['y'] and p[1] < t['y'] + t['h'] for p in ps):
                    title_hits += 1
        else:
            for a, b in _segs(ps):
                length += abs(b[0] - a[0]) + abs(b[1] - a[1])
                for bx in boxes:
                    own = bx['id'] == e['from'] or bx['id'] == e['to']
                    if seg_hits_rect(a, b, bx, 2 if own else 0.5):
                        through_boxes += 1
                for t in glabels:
                    if seg_hits_rect(a, b, t, 0):
                        title_hits += 1
        if r.get('label'):
            L.append({'k': k, 'rect': r['label']})
            for bx in boxes:
                if rects_overlap(r['label'], bx):
                    label_node += 1
            for t in glabels:
                if rects_overlap(r['label'], t):
                    label_title += 1
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            if rects_overlap(L[i]['rect'], L[j]['rect']):
                label_label += 1
    for item in L:
        k, rect = item['k'], item['rect']
        for q, ps in enumerate(lines):
            if not ps or q == k:
                continue
            if routes[q].get('curve'):
                hit = any(p[0] > rect['x'] and p[0] < rect['x'] + rect['w'] and p[1] > rect['y'] and p[1] < rect['y'] + rect['h'] for p in ps)
            else:
                hit = any(seg_hits_rect(a, b, rect, 0) for a, b in _segs(ps))
            if hit:
                label_on_line += 1
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            if not lines[i] or not lines[j]:
                continue
            hit = False
            sj = _segs(lines[j])
            for a, b in _segs(lines[i]):
                for c, d in sj:
                    if axis_cross(a, b, c, d) or diag_cross(a, b, c, d):
                        hit = True
                        break
                if hit:
                    break
            if hit:
                crossings += 1
    label_chip = 0
    bands = chip_bands(graph, routes, chips, s)
    for item in L:
        if any(rects_overlap(item['rect'], bd) for bd in bands):
            label_chip += 1
    return {'crossings': crossings, 'throughBoxes': through_boxes, 'titleHits': title_hits, 'labelNode': label_node, 'labelLabel': label_label,
            'labelTitle': label_title, 'labelOnLine': label_on_line, 'labelChip': label_chip, 'bends': bends, 'length': js_round(length)}


def curve_routes(graph, layout, curves, edge_curve, label_rect):
    boxes = {n['id']: {**n, 'cx': n['x'] + n['w'] / 2, 'cy': n['y'] + n['h'] / 2} for n in layout['nodes']}

    def quad(P, t):
        return [(1 - t) * (1 - t) * P[0][0] + 2 * (1 - t) * t * P[1][0] + t * t * P[2][0], (1 - t) * (1 - t) * P[0][1] + 2 * (1 - t) * t * P[1][1] + t * t * P[2][1]]
    out = []
    for i, e in enumerate(graph['edges']):
        fb, tb = boxes.get(e['from']), boxes.get(e['to'])
        if not fb or not tb or fb is tb:
            out.append(None)
            continue
        P = edge_curve(fb, tb, curves[i] if curves else 0)
        pts = [quad(P, k / 24) for k in range(25)]
        lab = None
        if e.get('label'):
            r = label_rect(P, e['label'], layout['s'])
            lab = {'x': r['x'], 'y': r['y'], 'w': r['w'], 'h': r['h']}
        out.append({'points': pts, 'via': 'curve', 'label': lab, 'curve': True})
    return out
