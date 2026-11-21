// Reference dump for test_markup.py: runs the JS mermaid_arch compiler over the corpus and writes the results as JSON.
// usage: node ref_dump.mjs <out.json> <js repo root>
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
const { mermaidToArch, d2ToArch, graphToArch, foldGroups, parseMermaid, parseD2, ArchError } = await import('file://' + process.argv[3] + '/scripts/mermaid_arch/index.mjs');
const dir = process.argv[3] + '/tests/mermaid_corpus';
const optsets = { A: { film: true, numbered: true, hint: 'web' }, B: {}, C: { routing: 'curve', hint: 'cli' }, D: { numbered: true, pace: 'slow', duration: 60, direction: 'TD', title: 'T <b>x</b>' },
  E: { size: 14, fit: 'wide', direction: 'RL' }, F: { direction: 'BT', pace: 'fast', numbered: true, relationColumn: true, relationName: 'Rel' }, G: { duration: 5, numbered: true }, H: { duration: 14, size: 22, direction: 'LR', hint: 'web' } };
const withLines = (g) => ({ ...g, nodes: g.nodes.map((n) => ({ ...n, line: n.line })), edges: g.edges.map((e) => ({ ...e, line: e.line })) });
const err = (e) => (e instanceof ArchError ? { known: true, errors: e.errors, warnings: e.warnings } : { known: false, errors: [String(e && e.message)], syntax: e instanceof SyntaxError });
const out = {};
for (const name of readdirSync(dir).filter((f) => /\.(mmd|d2|json)$/.test(f) && f !== 'expected.json').sort()) {
  const text = readFileSync(join(dir, name), 'utf8');
  const o = { parse: null, full: {} };
  try {
    if (name.endsWith('.json')) { const raw = JSON.parse(text); const f = foldGroups(raw); o.parse = { ok: true, graph: raw, fold: { graph: f.graph, warnings: f.warnings } }; }
    else { const p = name.endsWith('.d2') ? parseD2(text, {}) : parseMermaid(text, {}); o.parse = { ok: true, graph: withLines(p.graph), warnings: p.warnings }; }
  } catch (e) { o.parse = { ok: false, ...err(e) }; }
  for (const [k, opts] of Object.entries(optsets)) {
    try {
      let r;
      if (name.endsWith('.json')) { const raw = JSON.parse(text); const f = foldGroups(raw); r = graphToArch(raw, opts); r.warnings = [...f.warnings.filter((w) => !r.warnings.includes(w)), ...r.warnings]; }
      else r = name.endsWith('.d2') ? d2ToArch(text, opts) : mermaidToArch(text, opts);
      o.full[k] = { ok: true, warnings: r.warnings, block: r.block, graph: withLines(r.graph), textSteps: r.textSteps, textMessages: r.textMessages, schedule: r.schedule, durationSeconds: r.durationSeconds, steps: r.steps, relationColumn: r.relationColumn, relationName: r.relationName, direction: r.layout.direction };
    } catch (e) { o.full[k] = { ok: false, ...err(e) }; }
  }
  out[name] = o;
}
writeFileSync(process.argv[2], JSON.stringify(out));
