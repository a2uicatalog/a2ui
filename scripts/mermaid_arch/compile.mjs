// Canonical graph + layout + schedule -> a motion_arch block (and the payload around it).
import { ArchError, LIMITS, assignSteps } from './graph.mjs';
import { layoutGraph } from './layout.mjs';
import { buildSchedule, words, LEAD_IN, HOLD, CHIP_SECONDS, CHIP_START, CHIP_GAP, CHIP_TAIL } from './schedule.mjs';
import { activity, rowText } from './activity.mjs';

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
    warnings.push(`drawn ${lay.direction === 'TB' ? 'top-to-bottom' : 'left-to-right'} instead of ${graph.direction}: that keeps the text about ${(lay.size * 343 / lay.W).toFixed(0)} px on a 343 px phone column. ${opts.hint === 'web' ? 'You can switch the Layout menu to the written direction.' : `Pass --direction ${graph.direction} to force the written direction.`}`);
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
  const sentence = graph.edges.map((e, i) => activity(lab(e.from), lab(e.to), e.label, { style: e.style, both: e.both, reply: graph.edges.some((o, j) => j !== i && o.from === e.to && o.to === e.from) && graph.edges.findIndex((o) => o.from === e.to && o.to === e.from) < i }));
  const info = order.map((ei) => ({ words: words(sentence[ei]), chips: msgEdge.filter((m) => m.idx === ei).length }));
  let sched;
  try { sched = buildSchedule(info, { pace, duration }); }
  catch (e) { if (e.archMessage) throw new ArchError([e.message]); throw e; }
  warnings.push(...sched.warnings);
  const D = sched.durationSeconds;
  const stepOf = new Map(order.map((ei, k) => [ei, k]));   // edge index -> position in the schedule

  // ---- nodes: pop in flow order during the lead-in
  const NODE_DUR = 0.3;
  const nodeAt = new Map(sortedNodes.map((n, k) => [n.id, 0.3 + (sortedNodes.length > 1 ? (k * 0.4) / (sortedNodes.length - 1) : 0)]));
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

  // ---- message chips ride inside their step's dwell, one after another. A chip needs at least 0.3 s; when a short
  // `duration` squeezes the step below that, refuse up front instead of producing chips that run past the step.
  if (duration !== undefined) {
    let worst = 1, at = -1;
    info.forEach((st, k) => {
      if (!st.chips) return;
      const dw = sched.schedule[k].end - sched.schedule[k].start;
      const need = Math.max(CHIP_START, edgeSec(sched.schedule[k]) + 0.05) + st.chips * 0.3 + (st.chips - 1) * CHIP_GAP;
      if (need / dw > worst) { worst = need / dw; at = k; }
    });
    if (at >= 0) {
      const total = sched.schedule.reduce((a, x) => a + (x.end - x.start), 0);
      throw new ArchError([`duration ${duration} s is too short for the ${info[at].chips} message chips on step ${sched.schedule[at].step}: each chip needs at least 0.3 s inside its step. Raise the duration to at least ${Math.ceil(LEAD_IN + HOLD + total * worst)} s, or remove messages.`]);
    }
  }
  const seen = new Map();
  const messages = graph.messages.map((m, j) => {
    const { idx, back } = msgEdge[j];
    const st = sched.schedule[stepOf.get(idx)];
    const k = info[stepOf.get(idx)].chips, jn = seen.get(idx) || 0; seen.set(idx, jn + 1);
    const dwell = st.end - st.start;
    const off = Math.max(CHIP_START, edgeSec(st) + 0.05);   // not before the edge is fully drawn
    const c = Math.min(CHIP_SECONDS, Math.max(0.3, (dwell - off - CHIP_TAIL - (k - 1) * CHIP_GAP) / k));
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
    const o = { step: stepNo[ei], from: lab(e.from), to: lab(e.to), label: e.label || '', style: e.style || 'sync', activity: sentence[ei] };
    if (e.relation) o.relation = e.relation;
    return o;
  }) : [];
  // text alternative: every edge (full sentence) in playing order, and every message, always present, numbered or not
  const textSteps = order.map((ei, k) => {
    const e = graph.edges[ei];
    const o = { step: numbered ? stepNo[ei] : k + 1, from: lab(e.from), to: lab(e.to), label: e.label || '', style: e.style || 'sync', activity: sentence[ei] };
    if (e.relation) o.relation = e.relation;
    return o;
  });
  const textMessages = graph.messages.map((m, j) => {
    const { idx, back } = msgEdge[j], e = graph.edges[idx];
    return { step: textSteps[stepOf.get(idx)].step, text: m.text, from: lab(back ? e.to : e.from), to: lab(back ? e.from : e.to) };
  }).sort((a, b) => a.step - b.step);
  const relationColumn = numbered && (opts.relationColumn !== undefined ? !!opts.relationColumn : !!graph.relationColumn);
  const relationName = opts.relationName || graph.relationName || 'Relation';
  const schedule = sched.schedule.map((s, k) => ({ step: numbered ? stepNo[order[k]] : s.step, start: s.start, end: s.end }));
  return { block, layout: lay, warnings, steps, textSteps, textMessages, schedule, durationSeconds: D, numbered, pace, minimumSeconds: sched.minimumSeconds, relationColumn, relationName };
}

const STAGES = [['16:9', 1280, 720], ['4:3', 1200, 900], ['1:1', 1000, 1000], ['9:16', 720, 1280]];

// The steps table: a legend with the columns Step | Activity (and Relation when asked for). Full text, no cutting.
export function stepsTable(steps, ctx = {}) {
  const rel = !!ctx.relationColumn;
  return {
    type: 'table', caption: 'Steps',
    headers: rel ? ['Step', 'Activity', ctx.relationName || 'Relation'] : ['Step', 'Activity'],
    rows: steps.map((s) => (rel ? [String(s.step), s.activity, s.relation || ''] : [String(s.step), s.activity])),
    col_widths: rel ? ['9%', '67%', '24%'] : ['9%', '91%'],
  };
}

// The messages table: Step | Message | Direction, full text. Only built when the diagram has messages.
export function messagesTable(messages) {
  return {
    type: 'table', caption: 'Messages',
    headers: ['Step', 'Message', 'Direction'],
    rows: messages.map((m) => [String(m.step), m.text, `${m.from} to ${m.to}`]),
    col_widths: ['9%', '45%', '46%'],
  };
}

// The text alternative that goes after the diagram in every payload: the steps table (every edge as a full sentence)
// and the messages table. Uses the existing public `table` atom; the motion_arch atom itself is unchanged.
export function textAlternative(ctx = {}) {
  const out = [];
  if (ctx.textSteps && ctx.textSteps.length) out.push(stepsTable(ctx.textSteps, ctx));
  if (ctx.textMessages && ctx.textMessages.length) out.push(messagesTable(ctx.textMessages));
  return out;
}

// Wrap the diagram (and, when numbered, the steps table) in ONE motion_timeline so both run on one clock.
// The diagram is the motion_arch block, p = t / duration. Each table row is a motion_text that fades in
// when its step's edge starts drawing; a translucent bar steps to the current row. The stage is the one of
// four shapes (or, for a tall diagram, a wide stage with the table beside it) that draws the diagram biggest.
export function filmPayload(block, ctx = {}) {
  const D = ctx.durationSeconds || 9;
  const steps = ctx.steps || [], sch = ctx.schedule || [];
  const n = steps.length;
  const rel = !!ctx.relationColumn && n > 0, relName = ctx.relationName || 'Relation';
  const rows = steps.map((s) => rowText(s.step, s.activity, 60));
  const maxChars = Math.max(20, ...rows.map((r) => r.length));
  const relChars = rel ? Math.max(relName.length, ...steps.map((s) => (s.relation || '').length)) : 0;
  const gap = 24;
  const cands = [];
  // the text is one line per row: its size is what the table width allows
  const textSize = (tw, lo, hi) => clamp(Math.floor((tw * 0.94) / ((maxChars + (rel ? relChars + 3 : 0)) * 0.62)), lo, hi);
  for (const [aspect, sw, sh] of STAGES) {
    // the table text may shrink to about 1.95% of the stage width (6.7 px in a 343 px column) when that lets a tall diagram be bigger
    const cap = textSize(sw, 12, 24);
    for (const sz of new Set([cap, Math.min(cap, 16), Math.min(cap, Math.max(12, Math.ceil(sw * 0.0195)))])) {
      const rowH = Math.round(sz * 1.9), headH = Math.round(sz * 2.1);
      const T = n ? headH + n * rowH : 0;
      const scale = Math.min((sw * 0.96) / block.w, (sh - T - gap * (n ? 3 : 2)) / block.h);
      if (scale > 0) cands.push({ kind: 'stack', aspect, sw, sh, sz, rowH, headH, scale });
    }
  }
  if (n) for (const [aspect, sw, sh] of STAGES.slice(0, 2)) for (const f of [0.34, 0.4, 0.46]) {
    const tw = sw * f - gap, sz = textSize(tw, 11, 22);
    const rowH = Math.round(sz * 1.9), headH = Math.round(sz * 2.1);
    if (headH + n * rowH > sh - 2 * gap) continue;
    if (maxChars * sz * 0.62 > tw * 0.97) continue;           // the longest row must fit its line
    const scale = Math.min((sw * (1 - f) - 2 * gap) / block.w, (sh - 2 * gap) / block.h);
    if (scale > 0) cands.push({ kind: 'side', aspect, sw, sh, sz, rowH, headH, scale, f });
  }
  // Stages differ in width, and the player is shown at the width of its column, so what the viewer gets is the diagram's size
  // relative to the stage WIDTH (scale / sw), not the raw scale. The table's text must stay readable too (>= 1.65% of the width,
  // about 5.7 px in a 343 px column); a stage where it would be smaller is not considered unless nothing else is left.
  const shown = (c) => c.scale / c.sw;
  const legible = cands.filter((c) => !n || c.sz / c.sw >= 0.0165);
  let best = null;
  // biggest diagram wins; within 1% the larger table text wins
  for (const c of legible.length ? legible : cands) if (!best || shown(c) > shown(best) * 1.01 || (shown(c) > shown(best) * 0.99 && c.sz / c.sw > best.sz / best.sw)) best = c;
  if (!best) throw new ArchError(['the diagram and its steps table do not fit on one film stage; reduce the number of steps or the diagram size']);
  const { aspect, sw, sh, sz, rowH, headH, scale } = best;
  const pw = block.w * scale, ph = block.h * scale;
  let px, py, tx, tw, top;
  if (best.kind === 'side') {
    const reg = sw * (1 - best.f);
    px = (reg - pw) / 2; py = (sh - ph) / 2;
    tx = reg + gap / 2; tw = sw * best.f - gap * 1.5; top = gap;
  } else {
    px = (sw - pw) / 2; py = gap;
    tx = sw * 0.03; tw = sw * 0.94; top = py + ph + gap;
  }
  const arch = { ...block, id: 'arch', place: { x: r2((px / sw) * 100), y: r2((py / sh) * 100), w: r2((pw / sw) * 100), h: r2((ph / sh) * 100), z: 1 } };
  const blocks = [arch];
  const tracks = [{ target: 'arch', keys: [{ t: 0, p: 0 }, { t: D, p: 1, ease: 'linear' }] }];
  if (n) {
    const xPct = r2((tx / sw) * 100), wPct = r2((tw / sw) * 100);
    const aw = rel ? r2(wPct * 0.68) : wPct, rx = r2(xPct + wPct * 0.7), rw = r2(wPct * 0.3);
    blocks.push({ type: 'motion_text', id: 'head', text: 'STEP  ACTIVITY', size: Math.max(11, sz - 3), font: 'mono', weight: 'bold', mode: 'block', reveal: 'fade', color: '#9ca5b1', place: { x: xPct, y: r2((top / sh) * 100), w: aw, z: 2 } });
    if (rel) blocks.push({ type: 'motion_text', id: 'headrel', text: relName.toUpperCase(), size: Math.max(11, sz - 3), font: 'mono', weight: 'bold', mode: 'block', reveal: 'fade', color: '#9ca5b1', place: { x: rx, y: r2((top / sh) * 100), w: rw, z: 2 } });
    const rowY = (k) => top + headH + k * rowH;
    blocks.push({ type: 'motion_shape', id: 'hl', shape: 'rect', draw: 'none', fill: '#8d98ff', radius: 8, place: { x: r2(xPct - 1.2), y: r2((rowY(0) - 4) / sh * 100), w: r2(wPct + 2.4), h: r2((rowH - 2) / sh * 100), z: 1 } });
    const hlKeys = [{ t: 0, y: r2((rowY(0) - 4) / sh * 100), opacity: 0 }];
    steps.forEach((s, k) => {
      const t0 = sch[k].start;
      const fade = [{ t: 0, opacity: 0 }, { t: t0, opacity: 0 }, { t: r2(t0 + 0.3), opacity: 1, ease: 'standard' }];
      blocks.push({ type: 'motion_text', id: 'row' + (k + 1), text: rows[k], size: sz, font: 'mono', weight: 'regular', mode: 'block', reveal: 'fade', place: { x: xPct, y: r2((rowY(k) / sh) * 100), w: aw, z: 2 } });
      tracks.push({ target: 'row' + (k + 1), keys: fade });
      if (rel && s.relation) {
        blocks.push({ type: 'motion_text', id: 'rel' + (k + 1), text: s.relation, size: sz, font: 'mono', weight: 'regular', mode: 'block', reveal: 'fade', color: '#9ca5b1', place: { x: rx, y: r2((rowY(k) / sh) * 100), w: rw, z: 2 } });
        tracks.push({ target: 'rel' + (k + 1), keys: fade });
      }
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
    }, ...textAlternative(ctx)],
  };
}

// Standalone payload: the finished diagram, then the steps table and (when there are messages) the messages table.
export function archPayload(block, ctx = {}) {
  return { theme: 'dark', blocks: [block, ...textAlternative(ctx)] };
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
