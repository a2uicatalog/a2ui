// Orthogonal edge router and edge-label placement for the converter. Pure ES module, deterministic.
//
// The atom stays dumb: it draws each edge's `points` as a polyline with rounded corners and puts the label where
// `label_at` says. Everything clever is here.
//
//   routeEdges(graph, layout, opts) -> {routes, warnings, metrics}
//     routes[i] = {points: [[x, y], ...] (rim to rim, axis-aligned), label: {x, y, w, h} | null, via: 'grid' | 'curve'}
//
// How an edge is routed: a uniform grid (cell = about 0.55 x the text size) is laid over the drawing. Cells close to
// a node box, or on a group title, are blocked. Each edge is an A* search over (cell, heading) with a cost for
// distance, for every bend, for every cell another edge already uses (a heavy cost if it runs along that edge, a
// medium one if it crosses it), for cells inside a group the edge does not belong to, and for running along a group
// border. Edges are routed shortest first in input order, so the result is byte-stable. An edge leaves and enters a
// box at a port: a cell in the band 14 px beyond one of its four sides, so the first and last stretch always run at
// a right angle to the box and are long enough for the arrowhead. Parallel edges take neighbouring lanes because an
// occupied lane is expensive; a request/response pair therefore comes out as two lanes side by side.
//
// Labels go on the longest free straight stretch: candidates sit above or below a horizontal stretch, left or right
// of a vertical one, or on the line, and are checked against every box, group title, other label and other edge.
// A label is never shortened here; if nothing is free it is placed where it collides least and a warning says so.
import { edgeLabelSize, groupLabelWidth } from './layout.mjs';

const E = 0, S = 1, W = 2, N = 3;
const DX = [1, 0, -1, 0], DY = [0, 1, 0, -1];

class Heap {
  constructor() { this.a = []; this.n = 0; }
  push(f, id, term, port) {
    const it = { f, id, term, port, k: this.n++ };
    const a = this.a;
    a.push(it);
    let i = a.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (this.lt(a[i], a[p])) { [a[i], a[p]] = [a[p], a[i]]; i = p; } else break;
    }
  }
  lt(x, y) { return x.f < y.f - 1e-9 || (Math.abs(x.f - y.f) <= 1e-9 && x.k < y.k); }
  pop() {
    const a = this.a;
    const top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < a.length && this.lt(a[l], a[m])) m = l;
        if (r < a.length && this.lt(a[r], a[m])) m = r;
        if (m === i) break;
        [a[i], a[m]] = [a[m], a[i]]; i = m;
      }
    }
    return top;
  }
  get size() { return this.a.length; }
}

const rectsOverlap = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
const inflate = (r, m) => ({ x: r.x - m, y: r.y - m, w: r.w + 2 * m, h: r.h + 2 * m });

export function groupTitleRect(g, gl, s) {
  return { x: g.x + 12, y: g.y + 6, w: groupLabelWidth(gl.label, s) - 20, h: 24 };
}

// does the axis-aligned segment a-b pass through the open interior of rect r (shrunk by `m`)?
function segHitsRect(a, b, r, m = 0) {
  const x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]), y0 = Math.min(a[1], b[1]), y1 = Math.max(a[1], b[1]);
  return x1 > r.x + m && x0 < r.x + r.w - m && y1 > r.y + m && y0 < r.y + r.h - m;
}
// proper crossing of two axis-aligned segments (perpendicular, interiors meet)
function axisCross(a1, a2, b1, b2) {
  const ah = a1[1] === a2[1], bh = b1[1] === b2[1];
  if (ah === bh) return false;
  const [h1, h2, v1, v2] = ah ? [a1, a2, b1, b2] : [b1, b2, a1, a2];
  const hx0 = Math.min(h1[0], h2[0]), hx1 = Math.max(h1[0], h2[0]), vy0 = Math.min(v1[1], v2[1]), vy1 = Math.max(v1[1], v2[1]);
  return v1[0] > hx0 + 0.5 && v1[0] < hx1 - 0.5 && h1[1] > vy0 + 0.5 && h1[1] < vy1 - 0.5;
}

// proper crossing of two general segments (used for sampled curves)
function diagCross(a, b, c, d) {
  if (a[0] === b[0] || a[1] === b[1] || c[0] === d[0] || c[1] === d[1]) return false;
  const o = (p, q, r) => (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
  return o(c, d, a) * o(c, d, b) < 0 && o(a, b, c) * o(a, b, d) < 0;
}

export function routeEdges(graph, layout, opts = {}) {
  const s = layout.s;
  const warnings = [];
  const g = Math.max(8, Math.round(0.55 * s));            // lane pitch
  const clear = Math.max(6, Math.round(0.42 * s));        // keep-out around every box
  const port0 = Math.max(clear + 3, 15);                  // first port ring distance from the rim
  const nodeById = new Map(layout.nodes.map((n) => [n.id, n]));
  const boxes = layout.nodes;
  const glabels = layout.groups.map((gr) => groupTitleRect(gr, graph.groups.find((x) => x.id === gr.id), s));
  // ---- the grid covers all content plus a few lanes of margin on every side
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const r of [...boxes, ...layout.groups]) { x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.w); y1 = Math.max(y1, r.y + r.h); }
  if (!isFinite(x0)) { x0 = y0 = 0; x1 = y1 = 100; }
  const pad = 5 * g;
  const ox = x0 - pad, oy = y0 - pad;
  const cols = Math.ceil((x1 - x0 + 2 * pad) / g), rows = Math.ceil((y1 - y0 + 2 * pad) / g);
  const NC = cols * rows;
  const cx = (i) => ox + (i + 0.5) * g, cy = (j) => oy + (j + 0.5) * g;
  const ci = (x) => Math.floor((x - ox) / g), cj = (y) => Math.floor((y - oy) / g);
  const blocked = new Uint8Array(NC);
  const fillRect = (r, m, arr, val = 1) => {
    const i0 = Math.max(0, ci(r.x - m)), i1 = Math.min(cols - 1, ci(r.x + r.w + m)), j0 = Math.max(0, cj(r.y - m)), j1 = Math.min(rows - 1, cj(r.y + r.h + m));
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
      const px = cx(i), py = cy(j);
      if (px > r.x - m && px < r.x + r.w + m && py > r.y - m && py < r.y + r.h + m) arr[j * cols + i] = val;
    }
  };
  for (const b of boxes) fillRect(b, clear, blocked);
  for (const t of glabels) fillRect(t, 3, blocked);
  // group membership per cell, and cells that lie on a group border
  const cellGroup = new Int8Array(NC).fill(-1);
  layout.groups.forEach((gr, k) => fillRect(gr, 0, cellGroup, k));
  const hBorder = new Uint8Array(NC), vBorder = new Uint8Array(NC);
  layout.groups.forEach((gr) => {
    for (let i = 0; i < cols; i++) for (const yy of [gr.y, gr.y + gr.h]) {
      const j = cj(yy), px = cx(i);
      if (px >= gr.x - g && px <= gr.x + gr.w + g && j >= 0 && j < rows && Math.abs(cy(j) - yy) <= 0.6 * g) hBorder[j * cols + i] = 1;
    }
    for (let j = 0; j < rows; j++) for (const xx of [gr.x, gr.x + gr.w]) {
      const i = ci(xx), py = cy(j);
      if (py >= gr.y - g && py <= gr.y + gr.h + g && i >= 0 && i < cols && Math.abs(cx(i) - xx) <= 0.6 * g) vBorder[j * cols + i] = 1;
    }
  });
  const groupIdx = new Map(layout.groups.map((gr, k) => [gr.id, k]));
  const groupOfNode = new Map(graph.nodes.map((n) => [n.id, n.group && groupIdx.has(n.group) ? groupIdx.get(n.group) : -1]));
  // near a box (not blocked): a small cost keeps lanes in the middle of a channel
  const near = new Uint8Array(NC);
  for (const b of boxes) fillRect(b, clear + 1.5 * g, near);

  const usedH = new Uint8Array(NC), usedV = new Uint8Array(NC);
  const scale = opts.bendScale || 1;
  const BEND = 34 * scale, OVERLAP = 420, CROSS = 70, FOREIGN = 14, OWN_OUT = 7, BORDER = 12, NEAR = 3.5, SIDE = 0.18;

  // ports of a box: cells in the band [port0, port0 + g) beyond a side, away from the rounded corners
  const ports = (b) => {
    const out = [];
    const cm = 14;
    const sides = [
      { dir: E, ok: (px, py) => px >= b.x + b.w + port0 && px < b.x + b.w + port0 + g && py > b.y + cm && py < b.y + b.h - cm, off: (px, py) => Math.abs(py - (b.y + b.h / 2)) },
      { dir: W, ok: (px, py) => px <= b.x - port0 && px > b.x - port0 - g && py > b.y + cm && py < b.y + b.h - cm, off: (px, py) => Math.abs(py - (b.y + b.h / 2)) },
      { dir: S, ok: (px, py) => py >= b.y + b.h + port0 && py < b.y + b.h + port0 + g && px > b.x + cm && px < b.x + b.w - cm, off: (px) => Math.abs(px - (b.x + b.w / 2)) },
      { dir: N, ok: (px, py) => py <= b.y - port0 && py > b.y - port0 - g && px > b.x + cm && px < b.x + b.w - cm, off: (px) => Math.abs(px - (b.x + b.w / 2)) },
    ];
    const i0 = Math.max(0, ci(b.x - port0 - g)), i1 = Math.min(cols - 1, ci(b.x + b.w + port0 + g)), j0 = Math.max(0, cj(b.y - port0 - g)), j1 = Math.min(rows - 1, cj(b.y + b.h + port0 + g));
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
      if (blocked[j * cols + i]) continue;
      const px = cx(i), py = cy(j);
      for (const sd of sides) if (sd.ok(px, py)) out.push({ cell: j * cols + i, i, j, out: sd.dir, side: sd.off(px, py) * SIDE });
    }
    return out;
  };

  const route = (e, k, scl) => {
    const fb = nodeById.get(e.from), tb = nodeById.get(e.to);
    const sg = groupOfNode.get(e.from), tg = groupOfNode.get(e.to);
    const cellCost = (c, axisH) => {
      let k2 = 0;
      if (axisH ? usedH[c] : usedV[c]) k2 += OVERLAP;
      if (axisH ? usedV[c] : usedH[c]) k2 += CROSS;
      const cg = cellGroup[c];
      if (cg >= 0 && cg !== sg && cg !== tg) k2 += FOREIGN;
      else if (cg < 0 && sg >= 0 && sg === tg) k2 += OWN_OUT;
      if (axisH ? hBorder[c] : vBorder[c]) k2 += BORDER;
      if (near[c]) k2 += NEAR;
      return k2;
    };
    const dist = new Float64Array(NC * 4).fill(Infinity);
    const prev = new Int32Array(NC * 4).fill(-1);
    const heap = new Heap();
    const tPorts = ports(tb), tMap = new Map();
    for (const p of tPorts) tMap.set(p.cell, [...(tMap.get(p.cell) || []), p]);
    const hTarget = (i, j) => {
      const px = cx(i), py = cy(j);
      return Math.abs(Math.max(tb.x - px, 0, px - (tb.x + tb.w))) + Math.abs(Math.max(tb.y - py, 0, py - (tb.y + tb.h)));
    };
    for (const p of ports(fb)) {
      const id = p.cell * 4 + p.out;
      const c0 = p.side + cellCost(p.cell, p.out === E || p.out === W);
      if (c0 < dist[id]) { dist[id] = c0; prev[id] = -2 - p.out; heap.push(c0 + hTarget(p.i, p.j), id, false); }
    }
    let end = -1, endCost = Infinity, endPort = null;
    while (heap.size) {
      const it = heap.pop();
      if (it.term) { end = it.id; endCost = it.f; endPort = it.port; break; }
      const id = it.id, cell = id >> 2, dir = id & 3;
      const gcost = dist[id];
      if (it.f > gcost + hTarget(cell % cols, (cell / cols) | 0) + 1e-6) continue;
      const i = cell % cols, j = (cell / cols) | 0;
      const tp = tMap.get(cell);
      if (tp) for (const p of tp) {
        const inward = (p.out + 2) & 3;
        heap.push(gcost + p.side + (dir === inward ? 0 : BEND * scl), id, true, p);
      }
      for (const nd of [dir, (dir + 1) & 3, (dir + 3) & 3]) {
        const ni = i + DX[nd], nj = j + DY[nd];
        if (ni < 0 || nj < 0 || ni >= cols || nj >= rows) continue;
        const nc = nj * cols + ni;
        if (blocked[nc]) continue;
        const cost = gcost + g + (nd === dir ? 0 : BEND * scl) + cellCost(nc, nd === E || nd === W);
        const nid = nc * 4 + nd;
        if (cost < dist[nid] - 1e-9) { dist[nid] = cost; prev[nid] = id; heap.push(cost + hTarget(ni, nj), nid, false); }
      }
    }
    if (end < 0) return null;
    // rebuild the cell path
    const cells = [];
    let id = end;
    while (id >= 0) { cells.push([id >> 2, id & 3]); id = prev[id]; }
    const startDir = -2 - id;
    cells.reverse();
    const pts = [];
    const first = cells[0][0];
    const fi = first % cols, fj = (first / cols) | 0;
    // rim point of the source
    pts.push(startDir === E ? [fb.x + fb.w, cy(fj)] : startDir === W ? [fb.x, cy(fj)] : startDir === S ? [cx(fi), fb.y + fb.h] : [cx(fi), fb.y]);
    for (const [c] of cells) pts.push([cx(c % cols), cy((c / cols) | 0)]);
    const pin = (endPort.out + 2) & 3;
    const lastC = cells[cells.length - 1][0], li = lastC % cols, lj = (lastC / cols) | 0;
    pts.push(endPort.out === E ? [tb.x + tb.w, cy(lj)] : endPort.out === W ? [tb.x, cy(lj)] : endPort.out === S ? [cx(li), tb.y + tb.h] : [cx(li), tb.y]);
    void pin;
    // drop collinear points
    const out = [pts[0]];
    for (let q = 1; q < pts.length - 1; q++) {
      const a = out[out.length - 1], b = pts[q], c = pts[q + 1];
      if ((a[0] === b[0] && b[0] === c[0]) || (a[1] === b[1] && b[1] === c[1])) continue;
      out.push(b);
    }
    out.push(pts[pts.length - 1]);
    return { points: out, cells: cells.map((c) => c[0]), cost: endCost };
  };

  const order = graph.edges.map((e, i) => i).sort((a, b) => {
    const ea = graph.edges[a], eb = graph.edges[b];
    const da = Math.abs(nodeById.get(ea.from).x - nodeById.get(ea.to).x) + Math.abs(nodeById.get(ea.from).y - nodeById.get(ea.to).y);
    const db = Math.abs(nodeById.get(eb.from).x - nodeById.get(eb.to).x) + Math.abs(nodeById.get(eb.from).y - nodeById.get(eb.to).y);
    return da - db || a - b;
  });
  const routes = new Array(graph.edges.length).fill(null);
  for (const k of order) {
    const e = graph.edges[k];
    if (!nodeById.has(e.from) || !nodeById.has(e.to) || e.from === e.to) continue;
    let r = null;
    for (const scl of [1, 3, 8]) {
      r = route(e, k, scl);
      if (r && r.points.length <= 10) break;
      if (r && scl === 8) r = null;
    }
    if (!r) { warnings.push(`edge ${k + 1} (${e.from} -> ${e.to}): no clear orthogonal route was found, so it is drawn as a curve.`); continue; }
    // occupy the lanes this edge uses (a cell is entered along an axis; the corner cell counts for both)
    const cs = r.cells;
    for (let q = 0; q < cs.length; q++) {
      const c = cs[q], pc = q ? cs[q - 1] : c, nc2 = q + 1 < cs.length ? cs[q + 1] : c;
      const horiz = (a, b) => ((a / cols) | 0) === ((b / cols) | 0), vert = (a, b) => a % cols === b % cols;
      if ((q && horiz(c, pc) && c !== pc) || (q + 1 < cs.length && horiz(c, nc2) && c !== nc2)) usedH[c] = 1;
      if ((q && vert(c, pc) && c !== pc) || (q + 1 < cs.length && vert(c, nc2) && c !== nc2)) usedV[c] = 1;
      if (cs.length === 1) { usedH[c] = 1; usedV[c] = 1; }
    }
    // the stub cells (the port cell is the first/last in the list)
    routes[k] = { points: r.points, via: 'grid', label: null };
  }

  placeLabels(graph, layout, routes, glabels, s, warnings);
  return { routes, warnings, metrics: routeMetrics(graph, layout, routes, glabels, s) };
}

// ---------------------------------------------------------------- labels
function segs(points) { const o = []; for (let i = 0; i + 1 < points.length; i++) o.push([points[i], points[i + 1]]); return o; }

function placeLabels(graph, layout, routes, glabels, s, warnings) {
  const boxes = layout.nodes;
  const placed = [];
  const allSegs = routes.map((r) => (r ? segs(r.points) : []));
  // longest labels first: they are the hardest to fit; ties by input order
  const order = graph.edges.map((e, i) => i).filter((i) => graph.edges[i].label && routes[i]).sort((a, b) => edgeLabelSize(graph.edges[b].label, s).w - edgeLabelSize(graph.edges[a].label, s).w || a - b);
  const gap = 3;
  for (const k of order) {
    const e = graph.edges[k], sz = edgeLabelSize(e.label, s), r = routes[k];
    const cands = [];
    segs(r.points).forEach(([a, b], si) => {
      const horiz = a[1] === b[1];
      const len = horiz ? Math.abs(b[0] - a[0]) : Math.abs(b[1] - a[1]);
      const lo = horiz ? Math.min(a[0], b[0]) : Math.min(a[1], b[1]);
      const need = horiz ? sz.w : sz.h;
      // positions along the stretch: the middle first, then both ways in 6 px steps; never within 14 px of an end (corners, arrowheads)
      const margin = 14;
      const span = len - 2 * margin - need;
      const offs = [];
      if (span >= -0.5) { offs.push(0); for (let d = 6; d <= span / 2 + 0.01; d += 6) { offs.push(d, -d); } }
      else if (len - need >= 4) offs.push(0);
      const mid = lo + len / 2;
      for (const d of offs) {
        const c = mid + d;
        if (horiz) {
          const x = c - sz.w / 2, y = a[1];
          cands.push({ x, y: y - gap - sz.h, w: sz.w, h: sz.h, pref: 0, si, d, len });          // above
          cands.push({ x, y: y + gap, w: sz.w, h: sz.h, pref: 1.5, si, d, len });               // below
          cands.push({ x, y: y - sz.h / 2, w: sz.w, h: sz.h, pref: 4, si, d, len, on: true });  // on the line
        } else {
          const y = c - sz.h / 2, xx = a[0];
          cands.push({ x: xx + gap, y, w: sz.w, h: sz.h, pref: 0.5, si, d, len });
          cands.push({ x: xx - gap - sz.w, y, w: sz.w, h: sz.h, pref: 1.5, si, d, len });
          cands.push({ x: xx - sz.w / 2, y, w: sz.w, h: sz.h, pref: 5, si, d, len, on: true });
        }
      }
    });
    let best = null;
    for (const c of cands) {
      let hard = 0, soft = 0;
      for (const b of boxes) if (rectsOverlap(c, inflate(b, 2))) hard++;
      for (const t of glabels) if (rectsOverlap(c, inflate(t, 1))) hard++;
      for (const p of placed) if (rectsOverlap(c, inflate(p, 3))) hard++;
      for (let q = 0; q < allSegs.length; q++) for (const [a, b] of allSegs[q]) {
        if (q === k && !c.on) { if (segHitsRect(a, b, c, 0.5)) soft += 0.2; continue; }
        if (q === k && c.on) continue;
        if (segHitsRect(a, b, inflate(c, 1), 0)) soft += 1;
      }
      // another edge between this label and its own line makes it read as that edge's label
      let between = 0;
      if (!c.on) {
        const own = r.points[c.si], own2 = r.points[c.si + 1], horiz = own[1] === own2[1];
        for (let q = 0; q < allSegs.length; q++) if (q !== k) for (const [a, b] of allSegs[q]) {
          if (horiz && a[1] === b[1]) {
            const lo = Math.min(a[0], b[0]), hi = Math.max(a[0], b[0]);
            if (hi > c.x && lo < c.x + c.w && ((a[1] > own[1] && a[1] < c.y + c.h / 2) || (a[1] < own[1] && a[1] > c.y + c.h / 2))) between = 1;
          } else if (!horiz && a[0] === b[0]) {
            const lo = Math.min(a[1], b[1]), hi = Math.max(a[1], b[1]);
            if (hi > c.y && lo < c.y + c.h && ((a[0] > own[0] && a[0] < c.x + c.w / 2) || (a[0] < own[0] && a[0] > c.x + c.w / 2))) between = 1;
          }
        }
      }
      const cost = hard * 1000 + soft * 60 + between * 25 + c.pref + Math.abs(c.d) * 0.08 - Math.min(c.len, 400) * 0.01;
      if (!best || cost < best.cost - 1e-9) best = { c, cost, hard, soft };
    }
    if (!best) {
      // no stretch is long enough: put it at the middle of the route, on the line, and say so
      const pts = r.points, m = Math.floor(pts.length / 2);
      const mx = (pts[m - 1][0] + pts[m][0]) / 2, my = (pts[m - 1][1] + pts[m][1]) / 2;
      best = { c: { x: mx - sz.w / 2, y: my - sz.h / 2, w: sz.w, h: sz.h }, hard: 1, soft: 0, cost: 1e9 };
      warnings.push(`edge ${k + 1}: its label "${e.label}" does not fit on a straight stretch of the route; it sits on a bend. Shorten the label.`);
    } else if (best.hard) {
      warnings.push(`edge ${k + 1}: the label "${e.label}" overlaps a box or another label (no free place was found). Shorten it or give the diagram more room.`);
    }
    const c = best.c;
    r.label = { x: c.x, y: c.y, w: c.w, h: c.h };
    placed.push(r.label);
  }
}

// ---------------------------------------------------------------- measuring (used for routed and for curved edges)
export function routeMetrics(graph, layout, routes, glabels, s) {
  const boxes = layout.nodes;
  const lines = routes.map((r) => (r ? r.points : null));
  let throughBoxes = 0, titleHits = 0, labelNode = 0, labelLabel = 0, labelTitle = 0, labelOnLine = 0, crossings = 0, bends = 0, length = 0;
  const L = [];
  routes.forEach((r, k) => {
    if (!r) return;
    const e = graph.edges[k];
    const ps = r.points;
    bends += Math.max(0, ps.length - 2);
    if (r.curve) {
      // a sampled curve: count a box or title once if any sample point lies inside it
      for (const bx of boxes) {
        const own = bx.id === e.from || bx.id === e.to, m = own ? 3 : 0;
        if (ps.some((p) => p[0] > bx.x + m && p[0] < bx.x + bx.w - m && p[1] > bx.y + m && p[1] < bx.y + bx.h - m)) throughBoxes++;
      }
      for (const t of glabels) if (ps.some((p) => p[0] > t.x && p[0] < t.x + t.w && p[1] > t.y && p[1] < t.y + t.h)) titleHits++;
    } else segs(ps).forEach(([a, b]) => {
      length += Math.abs(b[0] - a[0]) + Math.abs(b[1] - a[1]);
      for (const bx of boxes) {
        const own = bx.id === e.from || bx.id === e.to;
        if (segHitsRect(a, b, bx, own ? 2 : 0.5)) throughBoxes++;
      }
      for (const t of glabels) if (segHitsRect(a, b, t, 0)) titleHits++;
    });
    if (r.label) {
      L.push({ k, rect: r.label });
      for (const bx of boxes) if (rectsOverlap(r.label, bx)) labelNode++;
      for (const t of glabels) if (rectsOverlap(r.label, t)) labelTitle++;
    }
  });
  for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) if (rectsOverlap(L[i].rect, L[j].rect)) labelLabel++;
  for (const { k, rect } of L) lines.forEach((ps, q) => {
    if (!ps || q === k) return;
    if (routes[q].curve ? ps.some((p) => p[0] > rect.x && p[0] < rect.x + rect.w && p[1] > rect.y && p[1] < rect.y + rect.h) : segs(ps).some(([a, b]) => segHitsRect(a, b, rect, 0))) labelOnLine++;
  });
  for (let i = 0; i < lines.length; i++) for (let j = i + 1; j < lines.length; j++) {
    if (!lines[i] || !lines[j]) continue;
    let hit = false;
    for (const [a, b] of segs(lines[i])) { for (const [c, d] of segs(lines[j])) if (axisCross(a, b, c, d) || diagCross(a, b, c, d)) { hit = true; break; } if (hit) break; }
    if (hit) crossings++;
  }
  return { crossings, throughBoxes, titleHits, labelNode, labelLabel, labelTitle, labelOnLine, bends, length: Math.round(length) };
}

// the same metrics for the atom's quadratic curves (stage 1), so the two modes can be compared like for like
export function curveRoutes(graph, layout, curves, edgeCurve, labelRect) {
  const boxes = new Map(layout.nodes.map((n) => [n.id, { ...n, cx: n.x + n.w / 2, cy: n.y + n.h / 2 }]));
  const quad = (P, t) => [(1 - t) * (1 - t) * P[0][0] + 2 * (1 - t) * t * P[1][0] + t * t * P[2][0], (1 - t) * (1 - t) * P[0][1] + 2 * (1 - t) * t * P[1][1] + t * t * P[2][1]];
  return graph.edges.map((e, i) => {
    const fb = boxes.get(e.from), tb = boxes.get(e.to);
    if (!fb || !tb || fb === tb) return null;
    const P = edgeCurve(fb, tb, curves ? curves[i] : 0);
    const pts = [];
    for (let k = 0; k <= 24; k++) pts.push(quad(P, k / 24));
    return { points: pts, via: 'curve', label: e.label ? (({ x, y, w, h }) => ({ x, y, w, h }))(labelRect(P, e.label, layout.s)) : null, curve: true };
  });
}
// crossing counter for sampled (non axis-aligned) polylines
export function curveCrossings(routes) {
  const cr = (p1, p2, p3, p4) => {
    const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
    return d(p3, p4, p1) * d(p3, p4, p2) < 0 && d(p1, p2, p3) * d(p1, p2, p4) < 0;
  };
  let n = 0;
  for (let i = 0; i < routes.length; i++) for (let j = i + 1; j < routes.length; j++) {
    if (!routes[i] || !routes[j]) continue;
    const A = segs(routes[i].points), B = segs(routes[j].points);
    let hit = false;
    for (const [a, b] of A) { for (const [c, d] of B) if (cr(a, b, c, d)) { hit = true; break; } if (hit) break; }
    if (hit) n++;
  }
  return n;
}
