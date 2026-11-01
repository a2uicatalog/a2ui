// Library entry: mermaidToArch(text, opts) -> {payload, graph, warnings}
import { ArchError, validateGraph } from './graph.mjs';
import { parseMermaid } from './mermaid.mjs';
import { compileGraph, archPayload, filmPayload, validateBlock } from './compile.mjs';

export { ArchError, validateGraph, parseMermaid, compileGraph, archPayload, filmPayload, validateBlock };
export { LIMITS, KINDS, KIND_ALIASES } from './graph.mjs';
export { layoutGraph } from './layout.mjs';

// opts: {direction, title, size, fit:'balanced'|'wide', film:boolean, duration}
export function graphToArch(graph, opts = {}) {
  const g = { ...graph };
  if (opts.direction) g.direction = opts.direction;
  if (opts.title) g.title = opts.title;
  if (!g.direction) g.direction = 'LR';
  const { errors, warnings } = validateGraph(g);
  if (errors.length) throw new ArchError(errors, warnings);
  const lopts = { ...opts, forceDirection: !!opts.direction };
  const { block, layout, warnings: w2 } = compileGraph(g, lopts);
  const bad = validateBlock(block);
  if (bad.length) throw new ArchError(['internal: compiled block breaks the atom limits: ' + bad.join('; ')], warnings);
  const payload = opts.film ? filmPayload(block, opts) : archPayload(block);
  return { payload, graph: g, warnings: [...warnings, ...w2], block, layout };
}

export function mermaidToArch(text, opts = {}) {
  const parsed = parseMermaid(text, opts);
  const r = graphToArch(parsed.graph, { ...opts, direction: opts.direction });
  r.warnings = [...parsed.warnings, ...r.warnings];
  return r;
}
