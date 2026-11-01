// Deterministic layered layout for the canonical graph. Pure ES module.
//
// Everything is computed in pixels of the SVG viewBox the atom draws in, then
// compile.mjs turns it into the atom's percent coordinates. Same input gives the
// same output (no randomness, no object-key order dependence: all tie-breaks
// use the input order).
//
// Pipeline:  clusterLayout() -> chooseOrientation() -> routeCurves() -> frame()
// routeCurves() is the ONLY place that decides how an edge bends. A better router
// can replace it without touching anything else.
import { LIMITS } from './graph.mjs';
import { routeEdges, routeMetrics, curveRoutes, groupTitleRect } from './route.mjs';

const CHAR_SANS = 0.56;     // bold system-ui, em per character (calibrated, see docs)
const CHAR_MONO = 0.62;    // mono, em per character

// ---------------------------------------------------------------- measuring
export function nodeBox(n, s) {
  const nh = Math.round(3.0 * s);
  const lab = Math.min(String(n.label).length, LIMITS.label);
  const sub = n.sub ? Math.min(String(n.sub).length, LIMITS.sub) : 0;
  const textW = Math.max(lab * CHAR_SANS * s, sub * CHAR_MONO * (s - 5));
  const nw = Math.max(Math.round(0.76 * nh + textW + 0.34 * nh), Math.round(5.2 * s));
  return { w: nw, h: nh };
}
// an edge label is one or two lines (the lines of `text` are separated by a newline); the box is as wide as the longer line
export function edgeLabelLines(text) { return String(text).split('\n').slice(0, 2); }
export function edgeLabelSize(text, s) {
  const ls = edgeLabelLines(text);
  const t = Math.min(Math.max(...ls.map((l) => l.length)), LIMITS.edgeLabel);
  return { w: Math.round(t * (s - 4) * CHAR_MONO + 12), h: Math.round((s - 4) * 1.15 * ls.length + 6) };
}
export function groupLabelWidth(label, s) {
  const t = Math.min(String(label).length, LIMITS.groupLabel);
  return Math.round(t * (s - 5) * (CHAR_MONO + 0.12) + 36);
}

// ---------------------------------------------------------------- isotonic spacing
// Choose centres closest to `desired` while keeping `minDist[i]` between neighbours i,i+1.
function spaceOut(desired, minDist) {
  const n = desired.length;
  const off = [0];
  for (let i = 1; i < n; i++) off[i] = off[i - 1] + minDist[i - 1];
  const blocks = [];
  for (let i = 0; i < n; i++) {
    blocks.push({ sum: desired[i] - off[i], cnt: 1, from: i, to: i });
    while (blocks.length > 1) {
      const b = blocks[blocks.length - 1], a = blocks[blocks.length - 2];
      if (a.sum / a.cnt <= b.sum / b.cnt) break;
      blocks.pop();
      a.sum += b.sum; a.cnt += b.cnt; a.to = b.to;
    }
  }
  const out = new Array(n);
  for (const b of blocks) for (let i = b.from; i <= b.to; i++) out[i] = b.sum / b.cnt + off[i];
  return out;
}

// ---------------------------------------------------------------- layered core
// items: [{key,w,h}]; edges: [{a,b,lw}] directed between item keys; axis 'x'|'y' is the rank axis.
// returns {pos: Map key -> {x,y} top-left, w, h, rank: Map}
export function layered(items, edges, axis, s, samePairs = [], laneGap = 0, extraGap = 0) {
  const n = items.length;
  const idx = new Map(items.map((it, i) => [it.key, i]));
  const E = edges.filter((e) => idx.has(e.a) && idx.has(e.b) && e.a !== e.b).map((e) => ({ a: idx.get(e.a), b: idx.get(e.b), lw: e.lw || 0, lh: e.lh || 0, n: e.n || 1 }));
  // optional same-rank pairs (union-find): used so a labelled request/response pair runs side by side
  const rep = Array.from({ length: n }, (_, i) => i);
  const find = (x) => { while (rep[x] !== x) { rep[x] = rep[rep[x]]; x = rep[x]; } return x; };
  const pairIdx = [];
  for (const [ka, kb] of samePairs) {
    if (!idx.has(ka) || !idx.has(kb)) continue;
    const ra = find(idx.get(ka)), rb = find(idx.get(kb));
    if (ra !== rb) rep[Math.max(ra, rb)] = Math.min(ra, rb);
    pairIdx.push([idx.get(ka), idx.get(kb)]);
  }
  const Eorig = E.map((e) => ({ ...e, oa: e.a, ob: e.b }));
  E.splice(0, E.length, ...Eorig.map((e) => ({ ...e, oa: e.a, ob: e.b, a: find(e.a), b: find(e.b) })).filter((e) => e.a !== e.b));
  // 1. break cycles deterministically: DFS from sources, then the rest, in input order
  const out = Array.from({ length: n }, () => []);
  const inc = Array(n).fill(0);
  E.forEach((e, i) => { out[e.a].push(i); inc[e.b]++; });
  const state = Array(n).fill(0); // 0 new, 1 on stack, 2 done
  const rev = new Set();
  const visit = (v) => {
    state[v] = 1;
    for (const ei of out[v]) {
      const w = E[ei].b;
      if (state[w] === 1) rev.add(ei);
      else if (state[w] === 0) visit(w);
    }
    state[v] = 2;
  };
  for (let v = 0; v < n; v++) if (!inc[v] && state[v] === 0) visit(v);
  for (let v = 0; v < n; v++) if (state[v] === 0) visit(v);
  const D = E.map((e, i) => (rev.has(i) ? { ...e, a: e.b, b: e.a } : e));
  // 2. longest-path ranks
  const dout = Array.from({ length: n }, () => []), din = Array.from({ length: n }, () => []);
  D.forEach((e) => { dout[e.a].push(e.b); din[e.b].push(e.a); });
  const rank = Array(n).fill(0);
  const indeg = din.map((l) => l.length);
  const queue = [];
  for (let v = 0; v < n; v++) if (!indeg[v]) queue.push(v);
  for (let qi = 0; qi < queue.length; qi++) {
    const v = queue[qi];
    for (const w of dout[v]) { rank[w] = Math.max(rank[w], rank[v] + 1); if (--indeg[w] === 0) queue.push(w); }
  }
  // pull sources next to their nearest successor (shorter edges)
  for (let v = 0; v < n; v++) if (!din[v].length && dout[v].length) rank[v] = Math.max(0, Math.min(...dout[v].map((w) => rank[w])) - 1);
  for (let v = 0; v < n; v++) rank[v] = rank[find(v)];
  const R = (rank.length ? Math.max(...rank) : 0) + 1;
  // 2b. long edges (more than one rank) get a dummy vertex in every rank they cross, so the ordering
  //     and the coordinates leave a lane for them instead of running them through boxes
  let N = n;
  const chain = [];
  for (const e of Eorig) {
    let a = e.oa, b = e.ob;
    if (rank[a] > rank[b]) [a, b] = [b, a];
    let prev = a;
    for (let r = rank[a] + 1; r < rank[b]; r++) { const d = N++; rank[d] = r; chain.push([prev, d]); prev = d; }
    chain.push([prev, b]);
  }
  // 3. order within ranks: barycentre sweeps, keep best by crossings
  const layersOf = () => {
    const L = Array.from({ length: R }, () => []);
    for (let v = 0; v < N; v++) L[rank[v]].push(v);
    return L;
  };
  let L = layersOf();
  const nbr = Array.from({ length: N }, () => []);
  chain.forEach(([u, v]) => { nbr[u].push(v); nbr[v].push(u); });
  const keepPairs = (layer) => {
    for (const [a, b] of pairIdx) {
      const ia = layer.indexOf(a), ib = layer.indexOf(b);
      if (ia < 0 || ib < 0) continue;
      const [first, second] = ia < ib ? [a, b] : [b, a];
      layer.splice(layer.indexOf(second), 1);
      layer.splice(layer.indexOf(first) + 1, 0, second);
    }
  };
  const frac = () => {
    const f = Array(N).fill(0);
    L.forEach((layer) => layer.forEach((v, i) => { f[v] = (i + 0.5) / layer.length; }));
    return f;
  };
  const crossings = () => {
    // count crossings of straight rank-fraction lines (long edges included)
    const f = frac();
    const segs = chain.map(([u, v]) => [rank[u], f[u], rank[v], f[v]]).map(([r1, p1, r2, p2]) => (r1 <= r2 ? [r1, p1, r2, p2] : [r2, p2, r1, p1]));
    let c = 0;
    for (let i = 0; i < segs.length; i++) for (let j = i + 1; j < segs.length; j++) {
      const [a1, p1, a2, p2] = segs[i], [b1, q1, b2, q2] = segs[j];
      const lo = Math.max(a1, b1), hi = Math.min(a2, b2);
      if (hi <= lo) continue;
      const at = (r1, v1, r2, v2, r) => (r2 === r1 ? v1 : v1 + (v2 - v1) * (r - r1) / (r2 - r1));
      const d1 = at(a1, p1, a2, p2, lo) - at(b1, q1, b2, q2, lo), d2 = at(a1, p1, a2, p2, hi) - at(b1, q1, b2, q2, hi);
      if (d1 * d2 < 0) c++;
    }
    return c;
  };
  let best = L.map((l) => l.slice()), bestC = crossings();
  for (let it = 0; it < 8; it++) {
    const f = frac();
    const down = it % 2 === 0;
    const order = down ? [...L.keys()] : [...L.keys()].reverse();
    for (const r of order) {
      const key = new Map();
      L[r].forEach((v, i) => {
        const ns = nbr[v].filter((w) => (down ? rank[w] < r : rank[w] > r));
        const use = ns.length ? ns : nbr[v].filter((w) => rank[w] !== r);
        key.set(v, use.length ? use.reduce((a, w) => a + f[w], 0) / use.length : f[v]);
      });
      const before = new Map(L[r].map((v, i) => [v, i]));
      L[r].sort((a, b) => key.get(a) - key.get(b) || before.get(a) - before.get(b));
      keepPairs(L[r]);
      L[r].forEach((v, i) => { f[v] = (i + 0.5) / L[r].length; });
    }
    const c = crossings();
    if (c < bestC) { bestC = c; best = L.map((l) => l.slice()); }
  }
  L = best;
  // 4. coordinates
  const lane = Math.round(0.8 * s);
  const ext = (v) => (v >= n ? { r: 0, c: lane } : axis === 'x' ? { r: items[v].w, c: items[v].h } : { r: items[v].h, c: items[v].w });
  const thick = L.map((layer) => Math.max(0, ...layer.map((v) => ext(v).r)));
  const gaps = [];
  for (let r = 0; r + 1 < R; r++) {
    let g = axis === 'x' ? 2.7 * s : 3.0 * s;
    for (const e of Eorig) {
      const lo = Math.min(rank[e.oa], rank[e.ob]), hi = Math.max(rank[e.oa], rank[e.ob]);
      if (lo === r && hi === r + 1) g = Math.max(g, axis === 'x' ? e.lw + 1.6 * s : e.lh + 1.4 * s);
    }
    if (laneGap) {
      // orthogonal routing: every edge that runs through this channel takes its own lane
      const through = Eorig.filter((e) => Math.min(rank[e.oa], rank[e.ob]) <= r && Math.max(rank[e.oa], rank[e.ob]) >= r + 1).reduce((a, e) => a + e.n, 0);
      g += Math.max(0, through - 1) * laneGap;
      if (axis === 'y') {
        // top-to-bottom: labels sit beside the vertical stretches inside this channel, so give them height to stack in
        const lh = Eorig.filter((e) => Math.min(rank[e.oa], rank[e.ob]) <= r && Math.max(rank[e.oa], rank[e.ob]) >= r + 1 && e.lh).reduce((a, e) => a + e.lh + 4, 0);
        g = Math.max(g, 0.55 * lh + 1.4 * s);
      }
      g += extraGap;
    }
    gaps.push(Math.round(g));
  }
  const rankPos = [];
  let acc = 0;
  for (let r = 0; r < R; r++) { rankPos.push(acc); acc += thick[r] + (gaps[r] || 0); }
  const crossGap = Math.round(1.3 * s) + (laneGap ? Math.round(0.9 * s) : 0);
  const cpos = Array(N).fill(0);
  L.forEach((layer) => {
    let t = 0;
    layer.forEach((v) => { cpos[v] = t + ext(v).c / 2; t += ext(v).c + crossGap; });
    const total = t - crossGap;
    layer.forEach((v) => { cpos[v] -= total / 2; });
  });
  for (let pass = 0; pass < 8; pass++) {
    const down = pass % 2 === 0;
    const order = down ? [...L.keys()] : [...L.keys()].reverse();
    for (const r of order) {
      const layer = L[r];
      const desired = layer.map((v) => {
        const ns = nbr[v];
        return ns.length ? ns.reduce((a, w) => a + cpos[w], 0) / ns.length : cpos[v];
      });
      const md = layer.slice(1).map((v, i) => (ext(layer[i]).c + ext(v).c) / 2 + crossGap);
      const placed = spaceOut(desired, md);
      layer.forEach((v, i) => { cpos[v] = placed[i]; });
    }
  }
  let lo = Infinity, hi = -Infinity;
  for (let v = 0; v < n; v++) { lo = Math.min(lo, cpos[v] - ext(v).c / 2); hi = Math.max(hi, cpos[v] + ext(v).c / 2); }
  if (!n) { lo = 0; hi = 0; }
  const pos = new Map(), rk = new Map();
  for (let v = 0; v < n; v++) {
    const rc = rankPos[rank[v]] + thick[rank[v]] / 2;      // rank-axis centre
    const cc = cpos[v] - lo;                                  // cross-axis centre
    const cx = axis === 'x' ? rc : cc, cy = axis === 'x' ? cc : rc;
    pos.set(items[v].key, { x: cx - items[v].w / 2, y: cy - items[v].h / 2 });
    rk.set(items[v].key, rank[v]);
  }
  const mainLen = acc;
  const crossLen = hi - lo;
  return { pos, rank: rk, w: Math.round(axis === 'x' ? mainLen : crossLen), h: Math.round(axis === 'x' ? crossLen : mainLen) };
}

// ---------------------------------------------------------------- compound layout
function otherAxis(a) { return a === 'x' ? 'y' : 'x'; }

// graph: validated canonical graph; flows: Map groupId -> 'same'|'cross'
// labelled request/response pairs (a->b and b->a, both labelled): returns [[a,b],...] over keys
function labelledPairs(edges, keyOf) {
  const out = [], seen = new Set();
  for (const e of edges) {
    if (!e.label) continue;
    const a = keyOf(e.from), b = keyOf(e.to);
    if (a === b) continue;
    const k = a < b ? a + '|' + b : b + '|' + a;
    if (seen.has(k)) continue;
    if (edges.some((f) => f.label && keyOf(f.from) === b && keyOf(f.to) === a)) { seen.add(k); out.push([a, b]); }
  }
  return out;
}

export function clusterLayout(graph, s, flows, pairMode = false, laneGap = 0, extraGap = 0) {
  const outerAxis = graph.direction === 'LR' || graph.direction === 'RL' ? 'x' : 'y';
  const nodeById = new Map(graph.nodes.map((n) => [n.id, n]));
  const box = new Map(graph.nodes.map((n) => [n.id, nodeBox(n, s)]));
  const edgeOf = (e) => {
    const lab = e.label ? edgeLabelSize(e.label, s) : { w: 0, h: 0 };
    return { a: e.from, b: e.to, lw: lab.w, lh: lab.h };
  };
  const padX = Math.round(1.1 * s), padBottom = Math.round(1.0 * s);
  const padTop = Math.round(24 + 0.3 * (s - 5) + 11);
  const clusters = [];            // top-level items
  const clusterOfNode = new Map();
  const inner = new Map();        // clusterKey -> {layout, items}
  const groupOrder = graph.groups.map((g) => g.id);
  // clusters ordered by first member's input position (stable)
  const firstSeen = new Map();
  graph.nodes.forEach((n, i) => { const k = n.group ? 'g:' + n.group : 'n:' + n.id; if (!firstSeen.has(k)) firstSeen.set(k, i); });
  const keys = [...firstSeen.keys()];
  for (const k of keys) {
    if (k.startsWith('n:')) {
      const id = k.slice(2), b = box.get(id);
      clusters.push({ key: k, w: b.w, h: b.h, members: [id] });
      clusterOfNode.set(id, k);
    } else {
      const gid = k.slice(2);
      const members = graph.nodes.filter((n) => n.group === gid).map((n) => n.id);
      const flow = flows.get(gid) === 'cross' ? otherAxis(outerAxis) : outerAxis;
      const items = members.map((id) => ({ key: id, ...box.get(id) }));
      const innerEdges = graph.edges.filter((e) => members.includes(e.from) && members.includes(e.to)).map(edgeOf);
      const innerPairs = pairMode && flow === 'y' ? labelledPairs(graph.edges.filter((e) => members.includes(e.from) && members.includes(e.to)), (x) => x) : [];
      const lay = layered(items, innerEdges, flow, s, innerPairs, laneGap, extraGap);
      const gl = graph.groups.find((g) => g.id === gid);
      const w = Math.max(lay.w + 2 * padX, groupLabelWidth(gl.label, s));
      const h = lay.h + padTop + padBottom;
      inner.set(k, { lay, w, h, gid, offX: Math.round((w - lay.w) / 2), offY: padTop });
      clusters.push({ key: k, w, h, members });
      members.forEach((m) => clusterOfNode.set(m, k));
    }
  }
  // cluster-level edges (deduplicated, inter-cluster only)
  const ce = new Map();
  for (const e of graph.edges) {
    const a = clusterOfNode.get(e.from), b = clusterOfNode.get(e.to);
    if (a === b) continue;
    const k = a + '>' + b;
    const o = edgeOf(e);
    const prev = ce.get(k);
    if (prev) { prev.lw = Math.max(prev.lw, o.lw); prev.lh = Math.max(prev.lh, o.lh); prev.n++; } else ce.set(k, { a, b, lw: o.lw, lh: o.lh, n: 1 });
  }
  const topPairs = pairMode && outerAxis === 'y' ? labelledPairs(graph.edges, (x) => clusterOfNode.get(x)) : [];
  const top = layered(clusters, [...ce.values()], outerAxis, s, topPairs, laneGap, extraGap);
  const nodes = [], groups = [];
  for (const c of clusters) {
    const p = top.pos.get(c.key);
    const inn = inner.get(c.key);
    if (!inn) { const id = c.members[0]; nodes.push({ id, x: p.x, y: p.y, w: c.w, h: c.h }); continue; }
    groups.push({ id: inn.gid, x: p.x, y: p.y, w: c.w, h: c.h });
    for (const id of c.members) {
      const q = inn.lay.pos.get(id), b = box.get(id);
      nodes.push({ id, x: p.x + inn.offX + q.x, y: p.y + inn.offY + q.y, w: b.w, h: b.h });
    }
  }
  const order = new Map(graph.nodes.map((n, i) => [n.id, i]));
  nodes.sort((a, b) => order.get(a.id) - order.get(b.id));
  groups.sort((a, b) => groupOrder.indexOf(a.id) - groupOrder.indexOf(b.id));
  // mirror for RL / BT
  const W = top.w, H = top.h;
  if (graph.direction === 'RL') { nodes.forEach((n) => { n.x = W - n.x - n.w; }); groups.forEach((g) => { g.x = W - g.x - g.w; }); }
  if (graph.direction === 'BT') { nodes.forEach((n) => { n.y = H - n.y - n.h; }); groups.forEach((g) => { g.y = H - g.y - g.h; }); }
  return { nodes, groups, w: W, h: H, s };
}

// ---------------------------------------------------------------- geometry shared with the renderer
export function rim(b, dx, dy) {
  const hw = b.w / 2, hh = b.h / 2;
  const t = Math.min(dx === 0 ? 1e9 : hw / Math.abs(dx), dy === 0 ? 1e9 : hh / Math.abs(dy));
  return [b.cx + dx * t, b.cy + dy * t];
}
// the atom's quadratic curve for an edge (renderers/web_article.py, _render_motion_arch)
export function edgeCurve(fb, tb, curve) {
  const dx = tb.cx - fb.cx, dy = tb.cy - fb.cy;
  const ln = Math.sqrt(dx * dx + dy * dy) || 1;
  const bend = curve / 100;
  const a = rim(fb, dx, dy), z = rim(tb, -dx, -dy);
  const mx = (a[0] + z[0]) / 2, my = (a[1] + z[1]) / 2;
  const c = [mx - (dy / ln) * bend * ln * 0.5, my + (dx / ln) * bend * ln * 0.5];
  return [a, c, z];
}
const quad = (P, t) => [(1 - t) * (1 - t) * P[0][0] + 2 * (1 - t) * t * P[1][0] + t * t * P[2][0], (1 - t) * (1 - t) * P[0][1] + 2 * (1 - t) * t * P[1][1] + t * t * P[2][1]];
export function labelRect(P, text, s) {
  const sz = edgeLabelSize(text, s);
  const lx = 0.25 * P[0][0] + 0.5 * P[1][0] + 0.25 * P[2][0];
  const ly = 0.25 * P[0][1] + 0.5 * P[1][1] + 0.25 * P[2][1] - 10;
  const fs = s - 4;
  // two lines grow upwards from the baseline of the curve's label (the atom puts the second line where the one line would be)
  return { x: lx - sz.w / 2, y: ly - fs * 0.85 - 2 - (edgeLabelLines(text).length - 1) * fs * 1.15, w: sz.w, h: sz.h };
}
const overlap = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
const inside = (p, b, m = 0) => p[0] > b.x - m && p[0] < b.x + b.w + m && p[1] > b.y - m && p[1] < b.y + b.h + m;

function segCross(p1, p2, p3, p4) {
  const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  const d1 = d(p3, p4, p1), d2 = d(p3, p4, p2), d3 = d(p1, p2, p3), d4 = d(p1, p2, p4);
  return d1 * d2 < 0 && d3 * d4 < 0;
}

function asBoxes(layout) {
  const m = new Map();
  for (const n of layout.nodes) m.set(n.id, { ...n, cx: n.x + n.w / 2, cy: n.y + n.h / 2 });
  return m;
}

// ---------------------------------------------------------------- the curve step (replaceable router)
// Picks an integer `curve` (-100..100) for each edge so that, as far as the atom's
// one-bend curve allows, edges do not cross other boxes, edge labels do not sit on
// boxes or on each other, and two edges between the same pair do not coincide.
export function routeCurves(graph, layout) {
  const s = layout.s;
  const boxes = asBoxes(layout);
  const list = [...boxes.values()];
  const cands = [0, 12, -12, 24, -24, 36, -36, 50, -50, 65, -65, 80, -80, 100, -100];
  const glabels = layout.groups.map((g) => {
    const gl = graph.groups.find((x) => x.id === g.id);
    return { x: g.x + 12, y: g.y + 6, w: groupLabelWidth(gl.label, s) - 20, h: 24 };
  });
  const chosen = [];                 // {P, rect}
  const curves = [];
  graph.edges.forEach((e, i) => {
    const fb = boxes.get(e.from), tb = boxes.get(e.to);
    let bestC = 0, bestCost = Infinity, bestGeo = null;
    for (const c of cands) {
      const P = edgeCurve(fb, tb, c);
      let cost = Math.abs(c) * 0.04;
      // samples against third-party boxes
      for (let k = 1; k < 24; k++) {
        const pt = quad(P, k / 24);
        for (const b of list) {
          if (b === fb || b === tb) continue;
          if (inside(pt, { x: b.x, y: b.y, w: b.w, h: b.h }, 3)) cost += 6;
        }
      }
      // endpoint boxes: a curve that bows back through its own end boxes
      for (let k = 2; k < 22; k++) {
        const pt = quad(P, k / 24);
        if (inside(pt, fb, -1) || inside(pt, tb, -1)) cost += 2;
      }
      let rect = null;
      if (e.label) {
        rect = labelRect(P, e.label, s);
        for (const b of list) if (overlap(rect, { x: b.x - 2, y: b.y - 2, w: b.w + 4, h: b.h + 4 })) cost += 40;
        for (const gl of glabels) if (overlap(rect, gl)) cost += 25;
        for (const o of chosen) if (o.rect && overlap(rect, o.rect)) cost += 30;
        for (const o of chosen) for (let k = 1; k < 8; k++) { const pt = quad(o.P, k / 8); if (inside(pt, rect, 2)) cost += 3; }
      }
      // do not lie on top of an earlier edge
      for (const o of chosen) {
        let close = 0;
        for (let k = 2; k <= 10; k += 2) { const a = quad(P, k / 12), b = quad(o.P, k / 12); if (Math.hypot(a[0] - b[0], a[1] - b[1]) < 18) close++; }
        if (close >= 2) cost += 12 * close;
        if (segCross(P[0], P[2], o.P[0], o.P[2])) cost += 1.5;
      }
      if (cost < bestCost - 1e-9) { bestCost = cost; bestC = c; bestGeo = { P, rect }; }
    }
    curves[i] = bestC;
    chosen.push(bestGeo);
  });
  return curves;
}

// ---------------------------------------------------------------- quality metrics
export function measure(graph, layout, curves) {
  const boxes = asBoxes(layout);
  const list = [...boxes.values()];
  let crossings = 0, throughBoxes = 0, labelsOnBoxes = 0, labelOverlaps = 0, len = 0;
  const rects = [];
  const geo = graph.edges.map((e, i) => edgeCurve(boxes.get(e.from), boxes.get(e.to), curves ? curves[i] : 0));
  geo.forEach((P, i) => {
    len += Math.hypot(P[2][0] - P[0][0], P[2][1] - P[0][1]);
    const e = graph.edges[i];
    for (const b of list) {
      if (b.id === e.from || b.id === e.to) continue;
      let hit = false;
      for (let k = 1; k < 24; k++) if (inside(quad(P, k / 24), b, 0)) hit = true;
      if (hit) throughBoxes++;
    }
    if (e.label) {
      const r = labelRect(P, e.label, layout.s);
      if (list.some((b) => overlap(r, b))) labelsOnBoxes++;
      for (const o of rects) if (overlap(r, o)) labelOverlaps++;
      rects.push(r);
    }
    for (let j = i + 1; j < geo.length; j++) {
      const f = graph.edges[j];
      if (f.from === e.from || f.from === e.to || f.to === e.from || f.to === e.to) continue;
      if (segCross(P[0], P[2], geo[j][0], geo[j][2])) crossings++;
    }
  });
  return { crossings, throughBoxes, labelsOnBoxes, labelOverlaps, edgeLength: Math.round(len) };
}

// ---------------------------------------------------------------- orientation search
function score(graph, layout, curves, fit) {
  const m = measure(graph, layout, curves);
  const s = layout.s;
  const wu = layout.w / s, hu = layout.h / s;
  const wW = fit === 'wide' ? 0.35 : 1.5, hW = 0.35;
  return wu * wW + hu * hW + m.crossings * 7 + m.throughBoxes * 12 + m.labelsOnBoxes * 10 + m.labelOverlaps * 40 + (m.edgeLength / s) * 0.06;
}

// text px on a 343 px column for a drawing of this size: the smallest text is size - 4 (edge labels)
const phonePx = (w, s) => ((s - 4) * 343) / Math.max(w, 1);
// a quick shape score used to pick which layouts are worth routing: legible on a phone, not absurdly tall, short edges
function shapeScore(graph, layout, fit) {
  const s = layout.s, W = layout.w, H = layout.h;
  const byId = new Map(layout.nodes.map((n) => [n.id, n]));
  let len = 0;
  for (const e of graph.edges) { const a = byId.get(e.from), b = byId.get(e.to); if (a && b) len += Math.abs(a.x + a.w / 2 - b.x - b.w / 2) + Math.abs(a.y + a.h / 2 - b.y - b.h / 2); }
  const phone = fit === 'wide' ? 0 : 24 * Math.max(0, 9 - phonePx(W, s)) + 40 * Math.max(0, H / W - 1.3);
  return phone + (W / s) * 0.15 + (H / s) * 0.15 + (len / s) * 0.35;
}

export function chooseLayout(graph, s, fit = 'balanced') {
  return rankLayouts(graph, s, fit, 1, 0)[0];
}

// All candidate layouts (cluster flow directions x request/response pairing), best first by the cheap curve score.
export function rankLayouts(graph, s, fit = 'balanced', keep = 3, laneGap = 0, shapeOnly = false, extraGap = 0) {
  const multi = graph.groups.filter((g) => graph.nodes.filter((n) => n.group === g.id).length >= 2).map((g) => g.id);
  const list = [];
  const total = 1 << multi.length;
  for (let mask = 0; mask < total; mask++) {
    for (const pairMode of [false, true]) {
      const flows = new Map(multi.map((id, i) => [id, mask & (1 << i) ? 'cross' : 'same']));
      const lay = clusterLayout(graph, s, flows, pairMode, laneGap, extraGap);
      if (shapeOnly) { list.push({ layout: lay, curves: null, score: shapeScore(graph, lay, fit), flows, pairMode }); continue; }
      const curves = routeCurves(graph, lay);
      list.push({ layout: lay, curves, score: score(graph, lay, curves, fit), flows, pairMode });
    }
  }
  return list.map((v, i) => ({ v, i })).sort((a, b) => (Math.abs(a.v.score - b.v.score) < 1e-9 ? a.i - b.i : a.v.score - b.v.score)).slice(0, keep).map((x) => x.v);
}

// ---------------------------------------------------------------- framing: size choice and viewBox
export function layoutGraph(graph, opts = {}) {
  if (opts.routing === 'curve') return layoutCurve(graph, opts);
  const outer = routeMemo;
  routeMemo = outer || new Map();
  try { return layoutOrthogonal(graph, opts); } finally { routeMemo = outer; }
}

// ---------------------------------------------------------------- orthogonal routing: size, orientation, framing
export const FLIP_GAIN = 1.25;
function orthoScore(fr, fit) {
  const m = fr.metrics, s = fr.size;
  const phone = fit === 'wide' ? 0 : 24 * Math.max(0, 9 - phonePx(fr.W, s)) + 40 * Math.max(0, fr.H / fr.W - 1.3);
  return phone + (fr.W / s) * 0.15 + (fr.H / s) * 0.15 + m.crossings * 8 + (m.throughBoxes + m.titleHits) * 40 + m.labelNode * 20 + m.labelLabel * 40 + m.labelTitle * 30
    + m.labelOnLine * 14 + (m.labelChip || 0) * 1.5 + m.bends * 0.5 + (m.length / s) * 0.04 + fr.failed * 50;
}

// Routing is a pure function of the drawn geometry, the edges (ends and label text) and the group membership, and the
// orientation/shape candidates often land on the same geometry (and the TB/LR pass repeats sizes), so identical
// requests are answered from a cache that lives for one layoutGraph call. Results are cloned: callers may edit them.
let routeMemo = null;
function routeCached(gr, layout) {
  if (!routeMemo) return routeEdges(gr, layout, {});
  const r1 = (o) => o.id + ',' + o.x + ',' + o.y + ',' + o.w + ',' + o.h;
  const key = layout.s + '|' + layout.nodes.map(r1).join(';') + '|' + layout.groups.map(r1).join(';') + '|' + gr.edges.map((e) => e.from + '>' + e.to + ':' + e.label).join(';')
    + '|' + gr.nodes.map((n) => n.id + '@' + (n.group || '')).join(';') + '|' + gr.groups.map((g) => g.id + ':' + g.label).join(';');
  let hit = routeMemo.get(key);
  if (!hit) { hit = routeEdges(gr, layout, {}); routeMemo.set(key, hit); }
  return { routes: hit.routes.map((r) => (r ? { ...r, points: r.points.map((p) => [p[0], p[1]]), label: r.label ? { ...r.label } : null } : null)), warnings: [...hit.warnings], metrics: { ...hit.metrics } };
}

function orthoAt(gr, s, fit) {
  const laneGap = Math.round(0.55 * s);
  let best = null;
  // if some label has no free place, give every channel more room and route again (twice at most)
  for (const extra of [0, 1.0, 2.0, 3.5]) {
    for (const v of rankLayouts(gr, s, fit, 4, laneGap, true, Math.round(extra * s))) {
      const rt = routeCached(gr, { nodes: v.layout.nodes, groups: v.layout.groups, s });
      const fr = frameRouted(gr, v, rt, s);
      fr.score = orthoScore(fr, fit);
      if (!best || fr.score < best.score - 1e-9) best = fr;
    }
    const m = best.metrics;
    if (best.failed === 0 && m.labelLabel + m.labelNode + m.labelTitle + m.throughBoxes + m.titleHits === 0 && m.labelOnLine === 0) break;
  }
  return best;
}

function layoutOrthogonal(graph, opts = {}) {
  const fit = opts.fit || 'balanced';
  const targetW = opts.targetW || 1000, maxH = opts.maxH || 1100;
  const one = (gr) => {
    let s = opts.size ? Math.max(8, Math.min(40, Math.round(opts.size))) : 18;
    let res = orthoAt(gr, s, fit);
    if (!opts.size) {
      for (let it = 0; it < 3; it++) {
        const k = Math.min(targetW / res.W, maxH / res.H);
        const ns = Math.max(10, Math.min(40, Math.round(s * k)));
        if (ns === s || (k > 0.88 && k < 1.12)) break;
        s = ns; res = orthoAt(gr, s, fit);
      }
    }
    while ((res.W > 2000 || res.H > 2000) && s > 8) { s -= 1; res = orthoAt(gr, s, fit); }
    res.fits = res.W <= 2000 && res.H <= 2000;
    res.direction = gr.direction;
    return res;
  };
  let res = one(graph);
  if (!opts.forceDirection) {
    const horizontal = graph.direction === 'LR' || graph.direction === 'RL';
    const alt = one({ ...graph, direction: horizontal ? 'TB' : 'LR' });
    // the other axis wins only when it scores better (legibility and shape are part of the score, see orthoScore)
    // AND its text is at least 25% bigger on a phone; a small gain is not worth ignoring the written direction
    if (alt.fits && alt.score < res.score - 1 && alt.size / alt.W >= FLIP_GAIN * (res.size / res.W)) res = alt;
  }
  return res;
}

function layoutCurve(graph, opts = {}) {
  const fit = opts.fit || 'balanced';
  const targetW = opts.targetW || 1000, maxH = opts.maxH || 1100;
  const sized = (gr) => {
    const tryS = (s) => frame(gr, chooseLayout(gr, s, fit), s);
    let s = opts.size ? Math.max(8, Math.min(40, Math.round(opts.size))) : 18;
    let res = tryS(s);
    if (!opts.size) {
      // text size scales the whole drawing only roughly (gaps and label widths do not scale linearly),
      // so walk towards the target frame width a few times
      for (let it = 0; it < 4; it++) {
        const k = Math.min(targetW / res.W, maxH / res.H);
        const ns = Math.max(10, Math.min(40, Math.round(s * k)));
        if (ns === s || (k > 0.85 && k < 1.12)) break;
        s = ns; res = tryS(s);
      }
    }
    while ((res.W > 2000 || res.H > 2000) && s > 8) { s -= 1; res = tryS(s); }
    res.fits = res.W <= 2000 && res.H <= 2000;
    res.direction = gr.direction;
    return res;
  };
  const phone = (r) => (r.size * 343) / r.W;
  const bad = (r) => r.metrics.crossings + r.metrics.throughBoxes + r.metrics.labelsOnBoxes + 2 * r.metrics.labelOverlaps;
  let res = sized(graph);
  // Keep the written direction unless its text would be unreadable on a phone (< 7 px in a 343 px column)
  // and the other axis is clearly better without making the drawing messier.
  if (!opts.forceDirection && phone(res) < 7) {
    const horizontal = graph.direction === 'LR' || graph.direction === 'RL';
    const alt = sized({ ...graph, direction: horizontal ? 'TB' : 'LR' });
    if (alt.fits && phone(alt) > phone(res) * 1.3 && bad(alt) <= bad(res) + 3) res = alt;
  }
  return res;
}

function frame(graph, best, s) {
  const { layout, curves } = best;
  const boxes = asBoxes(layout);
  const margin = Math.round(1.3 * s);
  // content bounds: boxes, groups, edge labels, curve points
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const take = (x, y, w = 0, h = 0) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x + w); y1 = Math.max(y1, y + h); };
  layout.nodes.forEach((n) => take(n.x, n.y, n.w, n.h));
  layout.groups.forEach((g) => take(g.x, g.y, g.w, g.h));
  graph.edges.forEach((e, i) => {
    const P = edgeCurve(boxes.get(e.from), boxes.get(e.to), curves[i]);
    for (let k = 0; k <= 8; k++) { const q = quad(P, k / 8); take(q[0] - 2, q[1] - 2, 4, 4); }
    if (e.label) { const r = labelRect(P, e.label, s); take(r.x, r.y, r.w, r.h); }
  });
  if (!isFinite(x0)) { x0 = y0 = 0; x1 = y1 = 100; }
  const dx = margin - x0, dy = margin - y0;
  const W = Math.max(200, Math.ceil(x1 - x0 + 2 * margin)), H = Math.max(120, Math.ceil(y1 - y0 + 2 * margin));
  const shift = (o) => ({ ...o, x: o.x + dx, y: o.y + dy });
  return {
    W, H, size: s,
    nodes: layout.nodes.map(shift), groups: layout.groups.map(shift), curves,
    direction: best.direction || graph.direction, flows: [...best.flows.entries()], metrics: measure(graph, { ...layout, nodes: layout.nodes.map(shift), groups: layout.groups.map(shift) }, curves),
  };
}

function frameRouted(graph, best, rt, s) {
  const { layout } = best;
  const margin = Math.round(1.3 * s);
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const take = (x, y, w = 0, h = 0) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x + w); y1 = Math.max(y1, y + h); };
  layout.nodes.forEach((n) => take(n.x, n.y, n.w, n.h));
  layout.groups.forEach((g) => take(g.x, g.y, g.w, g.h));
  rt.routes.forEach((r) => { if (!r) return; r.points.forEach((p) => take(p[0] - 2, p[1] - 2, 4, 4)); if (r.label) take(r.label.x, r.label.y, r.label.w, r.label.h); });
  if (!isFinite(x0)) { x0 = y0 = 0; x1 = y1 = 100; }
  const dx = margin - x0, dy = margin - y0;
  const W = Math.max(200, Math.ceil(x1 - x0 + 2 * margin)), H = Math.max(120, Math.ceil(y1 - y0 + 2 * margin));
  const shift = (o) => ({ ...o, x: o.x + dx, y: o.y + dy });
  const routes = rt.routes.map((r) => (r ? { ...r, points: r.points.map((p) => [p[0] + dx, p[1] + dy]), label: r.label ? shift(r.label) : null } : null));
  const failed = graph.edges.filter((e, i) => !routes[i] && e.from !== e.to).length;
  return {
    W, H, size: s, routing: 'orthogonal', routes, routeWarnings: rt.warnings, failed,
    nodes: layout.nodes.map(shift), groups: layout.groups.map(shift), curves: graph.edges.map(() => 0),
    direction: graph.direction, flows: [...best.flows.entries()], metrics: rt.metrics,
  };
}

// One yardstick for both drawings (curved or routed) of a finished layout: counts of edges through boxes or group titles,
// edge crossings (pairs of edges that cross), labels on boxes, titles, each other and other edges.
export function commonMetrics(graph, lay, chips = {}) {
  const layout = { nodes: lay.nodes, groups: lay.groups, s: lay.size };
  const glabels = lay.groups.map((g) => groupTitleRect(g, graph.groups.find((x) => x.id === g.id), lay.size));
  const routes = lay.routes || curveRoutes(graph, layout, lay.curves, edgeCurve, labelRect);
  return routeMetrics(graph, layout, routes, glabels, lay.size, chips);
}
