// Library entry: mermaidToArch(text, opts) -> {payload, graph, warnings}
import { ArchError, validateGraph } from './graph.mjs';
import { parseMermaid } from './mermaid.mjs';
import { parseD2 } from './d2.mjs';
import { compileGraph, archPayload, filmPayload, validateBlock } from './compile.mjs';

export { assignSteps } from './graph.mjs';
export { buildSchedule } from './schedule.mjs';
export { ArchError, validateGraph, parseMermaid, parseD2, compileGraph, archPayload, filmPayload, validateBlock };
export { LIMITS, KINDS, KIND_ALIASES } from './graph.mjs';
export { layoutGraph, commonMetrics } from './layout.mjs';

// opts: {routing:'orthogonal'|'curve' (default orthogonal), direction, title, size, fit:'balanced'|'wide', film:boolean, numbered:boolean, pace:'slow'|'normal'|'fast', duration:seconds, relationColumn:boolean, relationName:string}
export function graphToArch(graph, opts = {}) {
  const g = { ...graph };
  if (opts.direction) g.direction = opts.direction;
  if (opts.title) g.title = opts.title;
  if (!g.direction) g.direction = 'LR';
  const { errors, warnings } = validateGraph(g);
  if (errors.length) throw new ArchError(errors, warnings);
  const lopts = { ...opts, forceDirection: !!opts.direction };
  const c = compileGraph(g, lopts);
  const { block, layout, warnings: w2 } = c;
  const bad = validateBlock(block);
  if (bad.length) throw new ArchError(['internal: compiled block breaks the atom limits: ' + bad.join('; ')], warnings);
  const ctx = { steps: c.steps, textSteps: c.textSteps, textMessages: c.textMessages, schedule: c.schedule, durationSeconds: c.durationSeconds, relationColumn: c.relationColumn, relationName: c.relationName };
  const payload = opts.film ? filmPayload(block, ctx) : archPayload(block, ctx);
  return { payload, graph: g, warnings: [...warnings, ...w2], block, layout, steps: c.steps, textSteps: c.textSteps, textMessages: c.textMessages, schedule: c.schedule, durationSeconds: c.durationSeconds, pace: c.pace, minimumSeconds: c.minimumSeconds, numbered: c.numbered, relationColumn: c.relationColumn, relationName: c.relationName };
}

export function mermaidToArch(text, opts = {}) {
  const parsed = parseMermaid(text, opts);
  const r = graphToArch(parsed.graph, { ...opts, direction: opts.direction });
  r.warnings = [...parsed.warnings, ...r.warnings];
  return r;
}

export function d2ToArch(text, opts = {}) {
  const parsed = parseD2(text, opts);
  const r = graphToArch(parsed.graph, { ...opts, direction: opts.direction });
  r.warnings = [...parsed.warnings, ...r.warnings];
  return r;
}
