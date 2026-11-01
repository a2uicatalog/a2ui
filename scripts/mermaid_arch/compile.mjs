// Canonical graph + layout -> a motion_arch block (and the payload around it).
import { ArchError, LIMITS, validateGraph } from './graph.mjs';
import { layoutGraph } from './layout.mjs';

const r2 = (x) => Math.round(x * 100) / 100;
const r3 = (x) => Math.round(x * 1000) / 1000;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

function clip(str, max) {
  const t = String(str).trim();
  return t.length <= max ? t : t.slice(0, max - 1).trimEnd() + '…';
}

// graph -> {block, layout, warnings}. The graph must already be valid.
export function compileGraph(graph, opts = {}) {
  const warnings = [];
  const lay = layoutGraph(graph, opts);
  if (!lay.fits) throw new ArchError([`the diagram does not fit in the atom's 2000 x 2000 frame even at the smallest text size; shorten the labels or split the diagram`]);
  if (lay.direction !== graph.direction) {
    warnings.push(`drawn ${lay.direction === 'TB' ? 'top-to-bottom' : 'left-to-right'} instead of ${graph.direction}: that keeps the text about ${(lay.size * 343 / lay.W).toFixed(0)} px on a 343 px phone column. Pass --direction ${graph.direction} to force the written direction.`);
  }
  const { W, H, size } = lay;
  const horizontal = lay.direction === 'LR' || lay.direction === 'RL';
  const rev = lay.direction === 'RL' || lay.direction === 'BT';
  const byId = new Map(lay.nodes.map((n) => [n.id, n]));
  const gnodes = new Map(graph.nodes.map((n) => [n.id, n]));

  // --- timing: groups, then nodes in flow order, then edges, then messages
  const main = (n) => (horizontal ? n.x + n.w / 2 : n.y + n.h / 2);
  const mains = lay.nodes.map(main);
  const lo = Math.min(...mains), hi = Math.max(...mains);
  const nodeAt = new Map();
  for (const n of lay.nodes) {
    let t = hi > lo ? (main(n) - lo) / (hi - lo) : 0;
    if (rev) t = 1 - t;
    nodeAt.set(n.id, r3(0.1 + 0.2 * t));
  }
  const NODE_DUR = 0.08;
  const nodeEnd = (id) => nodeAt.get(id) + NODE_DUR;

  const nodes = graph.nodes.map((gn) => {
    const b = byId.get(gn.id);
    const o = { id: gn.id, kind: gn.kind || 'server', label: clip(gn.label, LIMITS.label) };
    if (gn.sub) o.sub = clip(gn.sub, LIMITS.sub);
    o.x = r2(((b.x + b.w / 2) / W) * 100); o.y = r2(((b.y + b.h / 2) / H) * 100);
    o.w = r2(clamp((b.w / W) * 100, 4, 100)); o.h = r2(clamp((b.h / H) * 100, 4, 100));
    o.at = nodeAt.get(gn.id); o.dur = NODE_DUR;
    return o;
  });

  const edgeOrder = graph.edges.map((e, i) => i).sort((a, b) => {
    const ea = Math.max(nodeAt.get(graph.edges[a].from), nodeAt.get(graph.edges[a].to));
    const eb = Math.max(nodeAt.get(graph.edges[b].from), nodeAt.get(graph.edges[b].to));
    return ea - eb || a - b;
  });
  const E = Math.max(1, graph.edges.length);
  const EDGE_DUR = 0.1;
  const edgeAt = [];
  edgeOrder.forEach((ei, k) => {
    const e = graph.edges[ei];
    const base = 0.34 + (k / E) * 0.26;
    edgeAt[ei] = r3(Math.max(base, nodeEnd(e.from), nodeEnd(e.to)));
  });
  const edges = graph.edges.map((e, i) => {
    const o = { from: e.from, to: e.to };
    if (e.label) o.label = clip(e.label, LIMITS.edgeLabel);
    o.style = e.style === 'sync' || e.style === undefined ? 'solid' : 'dashed';
    if (e.both) o.both = true;
    if (lay.curves[i]) o.curve = lay.curves[i];
    o.at = edgeAt[i]; o.dur = EDGE_DUR;
    return o;
  });

  // --- messages: resolve from/to to an edge index (first match), stagger in time
  const M = graph.messages.length;
  const msgDur0 = 0.1;
  const lastOnEdge = new Map();
  const step = M > 1 ? Math.min(0.12, 0.28 / (M - 1)) : 0;
  const messages = graph.messages.map((m, j) => {
    let idx = graph.edges.findIndex((e) => e.from === m.from && e.to === m.to);
    let back = !!m.back;
    if (idx < 0) { idx = graph.edges.findIndex((e) => e.from === m.to && e.to === m.from); back = !back; }
    if (idx < 0) throw new ArchError([`message ${j + 1}: no edge between "${m.from}" and "${m.to}"`]);
    let dur = msgDur0;
    let at = Math.max(0.62 + j * step, edgeAt[idx] + EDGE_DUR);
    if (lastOnEdge.has(idx)) at = Math.max(at, lastOnEdge.get(idx));
    if (at + dur > 1) { at = 1 - dur; }
    lastOnEdge.set(idx, at + dur);
    const o = { edge: idx, text: clip(m.text, LIMITS.msgText) };
    if (back) o.back = true;
    o.at = r3(at); o.dur = dur;
    return o;
  });

  const groups = lay.groups.map((g) => {
    const gg = graph.groups.find((x) => x.id === g.id);
    return { label: clip(gg.label, LIMITS.groupLabel), x: r2((g.x / W) * 100), y: r2((g.y / H) * 100), w: r2((g.w / W) * 100), h: r2((g.h / H) * 100), at: 0, dur: 0.1 };
  });

  const block = { type: 'motion_arch', label: clip(graph.title || 'Architecture diagram', LIMITS.title), w: W, h: H, size, nodes, edges };
  if (groups.length) block.groups = groups;
  if (messages.length) block.messages = messages;
  return { block, layout: lay, warnings };
}

const STAGES = [['16:9', 1280, 720], ['4:3', 1200, 900], ['1:1', 1000, 1000], ['9:16', 720, 1280]];

// Wrap the finished-diagram block in a motion_timeline so it plays (draws itself, chips ride).
export function filmPayload(block, opts = {}) {
  const duration = opts.duration || 9;
  const ratio = block.w / block.h;
  let best = STAGES[0], bd = Infinity;
  for (const st of STAGES) { const d = Math.abs(Math.log(ratio / (st[1] / st[2]))); if (d < bd) { bd = d; best = st; } }
  const [aspect, sw, sh] = best;
  const scale = Math.min(sw / block.w, sh / block.h) * 0.96;
  const pw = (block.w * scale) / sw * 100, ph = (block.h * scale) / sh * 100;
  const arch = { ...block, id: 'arch', place: { x: r2((100 - pw) / 2), y: r2((100 - ph) / 2), w: r2(pw), h: r2(ph) } };
  return {
    theme: 'dark',
    blocks: [{
      type: 'motion_timeline', title: block.label, aspect, duration, loop: true, autoplay: true, controls: true, theme: 'dark',
      blocks: [arch],
      tracks: [{ target: 'arch', keys: [{ t: 0, p: 0 }, { t: 0.5, p: 0 }, { t: duration - 1.5, p: 1, ease: 'linear' }] }],
    }],
  };
}

export function archPayload(block) {
  return { theme: 'dark', blocks: [block] };
}

// Validate the compiled block against the atom's own limits.
export function validateBlock(b) {
  const errs = [];
  if (b.type !== 'motion_arch') errs.push('type must be motion_arch');
  if (!(b.w >= 200 && b.w <= 2000)) errs.push(`w ${b.w} outside 200-2000`);
  if (!(b.h >= 120 && b.h <= 2000)) errs.push(`h ${b.h} outside 120-2000`);
  if (!(b.size >= 8 && b.size <= 40)) errs.push(`size ${b.size} outside 8-40`);
  const nodes = b.nodes || [], edges = b.edges || [], groups = b.groups || [], msgs = b.messages || [];
  if (nodes.length > LIMITS.nodes) errs.push('too many nodes');
  if (edges.length > LIMITS.edges) errs.push('too many edges');
  if (groups.length > LIMITS.groups) errs.push('too many groups');
  if (msgs.length > LIMITS.messages) errs.push('too many messages');
  const ids = new Set();
  for (const n of nodes) {
    if (!/^[a-z][a-z0-9_-]{0,31}$/.test(n.id)) errs.push(`node id ${n.id} invalid`);
    ids.add(n.id);
    if (n.x < 0 || n.x > 100 || n.y < 0 || n.y > 100) errs.push(`node ${n.id} centre outside 0-100`);
    if (n.w < 4 || n.h < 4) errs.push(`node ${n.id} too small`);
    if (n.label.length > 40 || (n.sub && n.sub.length > 40)) errs.push(`node ${n.id} text too long`);
    if (n.at < 0 || n.at > 1 || n.dur < 0.01 || n.dur > 1) errs.push(`node ${n.id} timing outside 0-1`);
  }
  edges.forEach((e, i) => {
    if (!ids.has(e.from) || !ids.has(e.to)) errs.push(`edge ${i} dangling`);
    if (e.curve !== undefined && (e.curve < -100 || e.curve > 100)) errs.push(`edge ${i} curve`);
    if (e.label && e.label.length > 48) errs.push(`edge ${i} label too long`);
  });
  msgs.forEach((m, i) => {
    if (!(m.edge >= 0 && m.edge < edges.length)) errs.push(`message ${i} edge index`);
    if (m.text.length > 40) errs.push(`message ${i} text too long`);
    if (m.at + m.dur > 1.0001) errs.push(`message ${i} runs past the end of the film`);
  });
  groups.forEach((g, i) => {
    if (g.x < 0 || g.y < 0 || g.w < 1 || g.h < 1 || g.x + g.w > 100.01 || g.y + g.h > 100.01) errs.push(`group ${i} outside frame`);
  });
  return errs;
}
