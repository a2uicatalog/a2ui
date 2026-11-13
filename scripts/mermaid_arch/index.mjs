// Library entry: mermaidToArch(text, opts) -> {payload, graph, warnings}
import { ArchError, validateGraph, foldGroups, PACES, normDirection } from './graph.mjs';
import { parseMermaid, stripTagsDeep } from './mermaid.mjs';
import { parseD2 } from './d2.mjs';
import { compileGraph, archPayload, filmPayload, validateBlock } from './compile.mjs';

export { assignSteps } from './graph.mjs';
export { buildSchedule } from './schedule.mjs';
export { ArchError, validateGraph, parseMermaid, parseD2, compileGraph, archPayload, filmPayload, validateBlock };
export { foldGroups, LIMITS, KINDS, KIND_ALIASES } from './graph.mjs';
export { layoutGraph, commonMetrics } from './layout.mjs';

// Option values are checked, never silently clamped or ignored.
export function checkOptions(opts = {}) {
  const e = [];
  const o = opts || {};
  if (o.size != null && !(typeof o.size === 'number' && Number.isFinite(o.size) && o.size >= 8 && o.size <= 40)) e.push(`size ${JSON.stringify(o.size)} must be a number from 8 to 40 (label text size in px)`);
  if (o.fit != null && !['balanced', 'wide'].includes(o.fit)) e.push(`fit ${JSON.stringify(o.fit)} must be balanced or wide`);
  if (o.aspect != null && !['16:9', '4:3', '1:1', '9:16'].includes(o.aspect)) e.push(`aspect ${JSON.stringify(o.aspect)} must be 16:9, 4:3, 1:1 or 9:16`);
  if (o.routing != null && !['orthogonal', 'curve'].includes(o.routing)) e.push(`routing ${JSON.stringify(o.routing)} must be orthogonal or curve`);
  if (o.pace != null && !(typeof o.pace === 'string' && Object.hasOwn(PACES, o.pace))) e.push(`pace ${JSON.stringify(o.pace)} must be one of ${Object.keys(PACES).join(', ')}`);
  if (o.duration != null && !(typeof o.duration === 'number' && o.duration >= 2 && o.duration <= 120)) e.push(`duration ${JSON.stringify(o.duration)} must be a number of seconds from 2 to 120`);
  if (o.hint != null && !['cli', 'web'].includes(o.hint)) e.push(`hint ${JSON.stringify(o.hint)} must be cli or web`);
  if (o.direction != null && !['LR', 'RL', 'TB', 'BT'].includes(normDirection(o.direction))) e.push(`direction ${JSON.stringify(o.direction)} must be LR, RL, TB (or TD) or BT`);
  if (e.length) throw new ArchError(e);
}

// One gate for every input path (Mermaid, D2, JSON): strings are literal text, so only tags are removed
// (no entity decoding). Returns a copy; the input graph is never changed.
export function sanitizeGraph(graph) {
  let changed = false;
  const clean = (t) => (typeof t === 'string' ? stripTagsDeep(t, () => { changed = true; }) : t);
  const each = (a, keys) => (Array.isArray(a) ? a.map((o) => {
    if (!o || typeof o !== 'object') return o;
    const c = { ...o };
    if (Object.getOwnPropertyDescriptor(o, 'line')) Object.defineProperty(c, 'line', { value: o.line, enumerable: Object.getOwnPropertyDescriptor(o, 'line').enumerable, writable: true, configurable: true });   // keep the hidden source line
    for (const k of keys) if (k in c) c[k] = clean(c[k]);
    return c;
  }) : a);
  if (!graph || typeof graph !== 'object') return { graph, changed };
  const g = { ...graph };
  if ('title' in g) g.title = clean(g.title);
  if ('relationName' in g) g.relationName = clean(g.relationName);
  g.nodes = each(g.nodes, ['label', 'sub']);
  g.groups = each(g.groups, ['label']);
  g.edges = each(g.edges, ['label', 'relation']);
  g.messages = each(g.messages, ['text']);
  for (const k of ['groups', 'messages']) if (g[k] === undefined) g[k] = [];   // a graph without groups or messages used to crash the layout
  return { graph: g, changed };
}

// opts: {hint:'cli'|'web' (wording of the layout warning, default cli), routing:'orthogonal'|'curve' (default orthogonal), direction, title, size, fit:'balanced'|'wide', film:boolean, numbered:boolean, pace:'slow'|'normal'|'fast', duration:seconds, relationColumn:boolean, relationName:string}
export function graphToArch(graph, opts = {}) {
  checkOptions(opts);
  const san = sanitizeGraph(graph);
  const folded = foldGroups(san.graph);
  if (san.changed) folded.warnings.unshift('HTML tags were removed from a label.');
  opts = { ...opts };
  for (const k of ['title', 'relationName']) if (typeof opts[k] === 'string') { const o = sanitizeGraph({ title: opts[k] }); opts[k] = o.graph.title; if (o.changed && !folded.warnings.includes('HTML tags were removed from a label.')) folded.warnings.unshift('HTML tags were removed from a label.'); }
  const g = { ...folded.graph };
  if (opts.direction) g.direction = normDirection(opts.direction);
  if (g.direction) g.direction = normDirection(g.direction);
  if (opts.title) g.title = opts.title;
  if (!g.direction) g.direction = 'LR';
  const v = validateGraph(g);
  const errors = v.errors, warnings = [...folded.warnings, ...v.warnings];
  if (errors.length) throw new ArchError(errors, warnings);
  const lopts = { ...opts, forceDirection: !!opts.direction, direction: normDirection(opts.direction) };
  const c = compileGraph(g, lopts);
  const { block, layout, warnings: w2 } = c;
  const bad = validateBlock(block);
  if (bad.length) throw new ArchError(['internal: compiled block breaks the atom limits: ' + bad.join('; ')], warnings);
  const ctx = { steps: c.steps, textSteps: c.textSteps, textMessages: c.textMessages, schedule: c.schedule, durationSeconds: c.durationSeconds, relationColumn: c.relationColumn, relationName: c.relationName, aspect: opts.aspect };
  const payload = opts.film ? filmPayload(block, ctx) : archPayload(block, ctx);
  return { payload, graph: g, warnings: [...warnings, ...w2], block, layout, steps: c.steps, textSteps: c.textSteps, textMessages: c.textMessages, schedule: c.schedule, durationSeconds: c.durationSeconds, pace: c.pace, minimumSeconds: c.minimumSeconds, numbered: c.numbered, relationColumn: c.relationColumn, relationName: c.relationName };
}

export function mermaidToArch(text, opts = {}) {
  checkOptions(opts);
  const parsed = parseMermaid(text, opts);
  const r = graphToArch(parsed.graph, { ...opts, direction: opts.direction });
  r.warnings = [...new Set([...parsed.warnings, ...r.warnings])];
  return r;
}

export function d2ToArch(text, opts = {}) {
  checkOptions(opts);
  const parsed = parseD2(text, opts);
  const r = graphToArch(parsed.graph, { ...opts, direction: opts.direction });
  r.warnings = [...new Set([...parsed.warnings, ...r.warnings])];
  return r;
}
