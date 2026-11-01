// Canonical graph + layout + schedule -> a motion_arch block (and the payload around it).
import { ArchError, LIMITS, assignSteps } from './graph.mjs';
import { layoutGraph } from './layout.mjs';
import { buildSchedule, words, LEAD_IN, HOLD, CHIP_START, CHIP_GAP, CHIP_TAIL } from './schedule.mjs';

const r2 = (x) => Math.round(x * 100) / 100;
const r4 = (x) => Math.round(x * 10000) / 10000;
// the atom clamps every dur to 0.01-1 of the film, so a very long film cannot have very short windows
const pd = (seconds, D) => r4(Math.max(0.011, seconds / D));
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

function clip(str, max) {
  const t = String(str).trim();
  return t.length <= max ? t : t.slice(0, max - 1).trimEnd() + '…';
}

// graph -> {block, layout, warnings, steps, schedule, durationSeconds}. The graph must already be valid.
export function compileGraph(graph, opts = {}) {
  const warnings = [];
  const numbered = opts.numbered !== undefined ? !!opts.numbered : !!graph.numbered;
  const pace = opts.pace || graph.pace || 'normal';
  const duration = opts.duration !== undefined ? opts.duration : graph.duration;

  // ---- step numbers (shown only when numbered) and the edge labels the atom will draw
  const stepNo = numbered ? assignSteps(graph).steps : null;
  const drawn = graph.edges.map((e, i) => {
    if (!numbered) return e.label;
    const full = String(stepNo[i]) + (e.label ? ' ' + e.label : '');
    if (full.length > LIMITS.edgeLabel) warnings.push(`edge ${i + 1}: the step number pushes the label to ${full.length} characters; the atom shows at most ${LIMITS.edgeLabel}, so it is cut. Shorten the label.`);
    return full;
  });
  const g2 = { ...graph, edges: graph.edges.map((e, i) => ({ ...e, label: drawn[i] })) };

  const lay = layoutGraph(g2, opts);
  if (!lay.fits) throw new ArchError([`the diagram does not fit in the atom's 2000 x 2000 frame even at the smallest text size; shorten the labels or split the diagram`]);
  if (lay.direction !== graph.direction) {
    warnings.push(`drawn ${lay.direction === 'TB' ? 'top-to-bottom' : 'left-to-right'} instead of ${graph.direction}: that keeps the text about ${(lay.size * 343 / lay.W).toFixed(0)} px on a 343 px phone column. Pass --direction ${graph.direction} to force the written direction.`);
  }
  const { W, H, size } = lay;
  const horizontal = lay.direction === 'LR' || lay.direction === 'RL';
  const rev = lay.direction === 'RL' || lay.direction === 'BT';
  const byId = new Map(lay.nodes.map((n) => [n.id, n]));
  const gnode = new Map(graph.nodes.map((n) => [n.id, n]));

  // ---- messages -> edge index
  const msgEdge = graph.messages.map((m, j) => {
    let idx = graph.edges.findIndex((e) => e.from === m.from && e.to === m.to);
    let back = !!m.back;
    if (idx < 0) { idx = graph.edges.findIndex((e) => e.from === m.to && e.to === m.from); back = !back; }
    if (idx < 0) throw new ArchError([`message ${j + 1}: no edge between "${m.from}" and "${m.to}"`]);
    return { idx, back };
  });

  // ---- playing order of the edges: step numbers, else the order the flow reaches them
  const main = (n) => (horizontal ? n.x + n.w / 2 : n.y + n.h / 2);
  const sortedNodes = lay.nodes.map((n, i) => ({ id: n.id, m: main(n) * (rev ? -1 : 1), i })).sort((a, b) => a.m - b.m || a.i - b.i);
  const nodeRank = new Map(sortedNodes.map((n, k) => [n.id, k]));
  const E = graph.edges.length;
  const order = graph.edges.map((e, i) => i).sort((a, b) => {
    if (numbered) return stepNo[a] - stepNo[b];
    const ka = Math.max(nodeRank.get(graph.edges[a].from), nodeRank.get(graph.edges[a].to));
    const kb = Math.max(nodeRank.get(graph.edges[b].from), nodeRank.get(graph.edges[b].to));
    return ka - kb || a - b;
  });
  const lab = (id) => gnode.get(id).label;
  const info = order.map((ei) => {
    const e = graph.edges[ei];
    return {
      labelWords: words(e.label),
      rowWords: words(lab(e.from)) + words(lab(e.to)) + words(e.label) + 1,
      chips: msgEdge.filter((m) => m.idx === ei).length,
    };
  });
  let sched;
  try { sched = buildSchedule(info, { pace, duration }); }
  catch (e) { if (e.archMessage) throw new ArchError([e.message]); throw e; }
  warnings.push(...sched.warnings);
  const D = sched.durationSeconds;
  const stepOf = new Map(order.map((ei, k) => [ei, k]));   // edge index -> position in the schedule

  // ---- nodes: pop in flow order during the lead-in
  const NODE_DUR = 0.4;
  const nodeAt = new Map(sortedNodes.map((n, k) => [n.id, 0.3 + (sortedNodes.length > 1 ? (k * 0.75) / (sortedNodes.length - 1) : 0)]));
  const nodes = graph.nodes.map((gn) => {
    const b = byId.get(gn.id);
    const o = { id: gn.id, kind: gn.kind || 'server', label: clip(gn.label, LIMITS.label) };
    if (gn.sub) o.sub = clip(gn.sub, LIMITS.sub);
    o.x = r2(((b.x + b.w / 2) / W) * 100); o.y = r2(((b.y + b.h / 2) / H) * 100);
    o.w = r2(clamp((b.w / W) * 100, 4, 100)); o.h = r2(clamp((b.h / H) * 100, 4, 100));
    o.at = r4(nodeAt.get(gn.id) / D); o.dur = pd(NODE_DUR, D);
    return o;
  });

  const edgeSec = (st) => Math.max(Math.min(0.5, (st.end - st.start) * 0.4), 0.011 * D);
  // ---- edges draw at their step's start
  const edges = graph.edges.map((e, i) => {
    const st = sched.schedule[stepOf.get(i)];
    const o = { from: e.from, to: e.to };
    if (drawn[i]) o.label = clip(drawn[i], LIMITS.edgeLabel);
    o.style = e.style === 'sync' || e.style === undefined ? 'solid' : 'dashed';
    if (e.both) o.both = true;
    const rt = lay.routes && lay.routes[i];
    if (rt) {
      o.points = rt.points.map((q) => ({ x: r2((q[0] / W) * 100), y: r2((q[1] / H) * 100) }));
      if (rt.label) o.label_at = { x: r2(((rt.label.x + rt.label.w / 2) / W) * 100), y: r2(((rt.label.y + rt.label.h / 2) / H) * 100) };
    } else if (lay.curves[i]) o.curve = lay.curves[i];
    o.at = r4(st.start / D); o.dur = pd(edgeSec(st), D);
    return o;
  });

  // ---- message chips ride inside their step's dwell, one after another
  const seen = new Map();
  const messages = graph.messages.map((m, j) => {
    const { idx, back } = msgEdge[j];
    const st = sched.schedule[stepOf.get(idx)];
    const k = info[stepOf.get(idx)].chips, jn = seen.get(idx) || 0; seen.set(idx, jn + 1);
    const dwell = st.end - st.start;
    const off = Math.max(CHIP_START, edgeSec(st) + 0.05);   // not before the edge is fully drawn
    const c = Math.min(1.2, Math.max(0.3, (dwell - off - CHIP_TAIL - (k - 1) * CHIP_GAP) / k));
    const o = { edge: idx, text: clip(m.text, LIMITS.msgText) };
    if (back) o.back = true;
    o.at = r4((st.start + off + jn * (c + CHIP_GAP)) / D); o.dur = pd(c, D);
    return o;
  });

  const groups = lay.groups.map((g) => {
    const gg = graph.groups.find((x) => x.id === g.id);
    return { label: clip(gg.label, LIMITS.groupLabel), x: r2((g.x / W) * 100), y: r2((g.y / H) * 100), w: r2((g.w / W) * 100), h: r2((g.h / H) * 100), at: 0, dur: pd(0.3, D) };
  });

  const block = { type: 'motion_arch', label: clip(graph.title || 'Architecture diagram', LIMITS.title), w: W, h: H, size, nodes, edges };
  if (lay.routes) { block.radius = clamp(Math.round(size * 0.55), 6, 14); warnings.push(...lay.routeWarnings); }
  if (groups.length) block.groups = groups;
  if (messages.length) block.messages = messages;

  const steps = numbered ? order.map((ei, k) => {
    const e = graph.edges[ei];
    return { step: stepNo[ei], from: lab(e.from), to: lab(e.to), label: e.label || '', style: e.style || 'sync' };
  }) : [];
  const schedule = sched.schedule.map((s, k) => ({ step: numbered ? stepNo[order[k]] : s.step, start: s.start, end: s.end }));
  return { block, layout: lay, warnings, steps, schedule, durationSeconds: D, numbered, pace, minimumSeconds: sched.minimumSeconds };
}

const STAGES = [['16:9', 1280, 720], ['4:3', 1200, 900], ['1:1', 1000, 1000], ['9:16', 720, 1280]];
const TYPE = { sync: 'sync', async: 'async', optional: 'optional' };

export function stepsTable(steps) {
  return {
    type: 'table', caption: 'Steps',
    headers: ['Step', 'From', 'To', 'What', 'Kind'],
    rows: steps.map((s) => [String(s.step), s.from, s.to, s.label || '-', TYPE[s.style] || s.style]),
    col_widths: ['9%', '25%', '25%', '28%', '13%'],
  };
}

// Wrap the diagram (and, when numbered, the steps table) in ONE motion_timeline so both run on one clock.
// The diagram is the motion_arch block, p = t / duration. Each table row is a motion_text that fades in
// when its step's edge starts drawing; a translucent bar steps to the current row.
export function filmPayload(block, ctx = {}) {
  const D = ctx.durationSeconds || 9;
  const steps = ctx.steps || [], sch = ctx.schedule || [];
  const n = steps.length;
  const rowText = (s) => clip(`*${s.step}*  ${s.from} → ${s.to}${s.label ? ': ' + s.label : ''}${s.style === 'async' ? ' (async)' : s.style === 'optional' ? ' (optional)' : ''}`, 60);
  const rows = steps.map(rowText);
  const maxChars = Math.max(20, ...rows.map((r) => r.length));
  let best = null;
  for (const [aspect, sw, sh] of STAGES) {
    const sz = clamp(Math.floor((sw * 0.94) / (maxChars * 0.62)), 12, 24);
    const rowH = Math.round(sz * 1.9), headH = Math.round(sz * 2.1), gap = 24;
    const T = n ? headH + n * rowH : 0;
    const scale = Math.min((sw * 0.96) / block.w, (sh - T - gap * (n ? 3 : 2)) / block.h);
    if (scale > 0 && (!best || scale > best.scale + 1e-9)) best = { aspect, sw, sh, sz, rowH, headH, gap, T, scale };
  }
  if (!best) throw new ArchError(['the diagram and its steps table do not fit on one film stage; reduce the number of steps or the diagram size']);
  const { aspect, sw, sh, sz, rowH, headH, gap, scale } = best;
  const pw = block.w * scale, ph = block.h * scale;
  const px = (sw - pw) / 2, py = gap;
  const arch = { ...block, id: 'arch', place: { x: r2((px / sw) * 100), y: r2((py / sh) * 100), w: r2((pw / sw) * 100), h: r2((ph / sh) * 100), z: 1 } };
  const blocks = [arch];
  const tracks = [{ target: 'arch', keys: [{ t: 0, p: 0 }, { t: D, p: 1, ease: 'linear' }] }];
  if (n) {
    const top = py + ph + gap;
    const xPct = r2((sw * 0.03 / sw) * 100), wPct = 94;
    blocks.push({ type: 'motion_text', id: 'head', text: 'STEP  FROM → TO: WHAT', size: Math.max(11, sz - 3), font: 'mono', weight: 'bold', mode: 'block', reveal: 'fade', color: '#9ca5b1', place: { x: xPct, y: r2((top / sh) * 100), w: wPct, z: 2 } });
    const rowY = (k) => top + headH + k * rowH;
    blocks.push({ type: 'motion_shape', id: 'hl', shape: 'rect', draw: 'none', fill: '#8d98ff', radius: 8, place: { x: r2(xPct - 1.2), y: r2((rowY(0) - 4) / sh * 100), w: r2(wPct + 2.4), h: r2((rowH - 2) / sh * 100), z: 1 } });
    const hlKeys = [{ t: 0, y: r2((rowY(0) - 4) / sh * 100), opacity: 0 }];
    steps.forEach((s, k) => {
      const t0 = sch[k].start;
      blocks.push({ type: 'motion_text', id: 'row' + (k + 1), text: rows[k], size: sz, font: 'mono', weight: 'regular', mode: 'block', reveal: 'fade', place: { x: xPct, y: r2((rowY(k) / sh) * 100), w: wPct, z: 2 } });
      tracks.push({ target: 'row' + (k + 1), keys: [{ t: 0, opacity: 0 }, { t: t0, opacity: 0 }, { t: r2(t0 + 0.3), opacity: 1, ease: 'standard' }] });
      hlKeys.push(k === 0
        ? { t: t0, y: r2((rowY(0) - 4) / sh * 100), opacity: 0, ease: 'hold' }
        : { t: t0, y: r2((rowY(k) - 4) / sh * 100), opacity: 0.22, ease: 'hold' });
      if (k === 0) hlKeys.push({ t: r2(t0 + 0.3), opacity: 0.22, ease: 'standard' });
    });
    tracks.push({ target: 'hl', keys: hlKeys });
  }
  return {
    theme: 'dark',
    blocks: [{
      type: 'motion_timeline', title: block.label, aspect, duration: D, loop: true, autoplay: true, controls: true, theme: 'dark',
      poster: r2(Math.max(0, D - 0.5)), blocks, tracks,
    }],
  };
}

// Standalone payload: the finished diagram (and, when numbered, the steps table under it).
export function archPayload(block, ctx = {}) {
  const blocks = [block];
  if (ctx.steps && ctx.steps.length) blocks.push(stepsTable(ctx.steps));
  return { theme: 'dark', blocks };
}

// Validate the compiled block against the atom's own limits.
export function validateBlock(b) {
  const errs = [];
  if (b.type !== 'motion_arch') errs.push('type must be motion_arch');
  if (!(b.w >= 200 && b.w <= 2000)) errs.push(`w ${b.w} outside 200-2000`);
  if (!(b.h >= 120 && b.h <= 2000)) errs.push(`h ${b.h} outside 120-2000`);
  if (!(b.size >= 8 && b.size <= 40)) errs.push(`size ${b.size} outside 8-40`);
  if (b.radius !== undefined && !(b.radius >= 0 && b.radius <= 60)) errs.push(`radius ${b.radius} outside 0-60`);
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
    if (e.points !== undefined) {
      if (!Array.isArray(e.points) || e.points.length < 2 || e.points.length > 10) errs.push(`edge ${i} points: 2 to 10 needed`);
      else if (e.points.some((q) => !(q.x >= 0 && q.x <= 100 && q.y >= 0 && q.y <= 100))) errs.push(`edge ${i} points outside the frame`);
    }
    if (e.label_at !== undefined && !(e.label_at.x >= 0 && e.label_at.x <= 100 && e.label_at.y >= 0 && e.label_at.y <= 100)) errs.push(`edge ${i} label_at outside the frame`);
    if (e.label && e.label.length > 48) errs.push(`edge ${i} label too long`);
    if (e.at < 0 || e.at > 1 || e.dur < 0.01 || e.dur > 1 || e.at + e.dur > 1.0001) errs.push(`edge ${i} timing outside 0-1`);
  });
  msgs.forEach((m, i) => {
    if (!(m.edge >= 0 && m.edge < edges.length)) errs.push(`message ${i} edge index`);
    if (m.text.length > 40) errs.push(`message ${i} text too long`);
    if (m.at + m.dur > 1.0001 || m.dur < 0.01) errs.push(`message ${i} timing outside the film`);
  });
  groups.forEach((g, i) => {
    if (g.x < 0 || g.y < 0 || g.w < 1 || g.h < 1 || g.x + g.w > 100.01 || g.y + g.h > 100.01) errs.push(`group ${i} outside frame`);
  });
  return errs;
}
