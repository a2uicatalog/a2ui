#!/usr/bin/env node
// Batch runner for tests/test_mermaid_corpus.py: converts every file in tests/mermaid_corpus once (twice for the
// determinism check) in one node process and prints one JSON object per file name.
// usage: node tests/mermaid_corpus_runner.mjs <corpus dir>
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mermaidToArch, d2ToArch, graphToArch, foldGroups, validateGraph, validateBlock, ArchError } from '../scripts/mermaid_arch/index.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const dir = process.argv[2] || join(HERE, 'mermaid_corpus');
const OPTS = { film: true, numbered: true, hint: 'web' };

function convert(name, text) {
  if (name.endsWith('.json')) {
    const raw = JSON.parse(text);
    const f = foldGroups(raw);
    const r = graphToArch(raw, OPTS);
    r.warnings = [...f.warnings.filter((w) => !r.warnings.includes(w)), ...r.warnings];
    return r;
  }
  return name.endsWith('.d2') ? d2ToArch(text, OPTS) : mermaidToArch(text, OPTS);
}

function once(name, text) {
  const t0 = performance.now();
  try {
    const r = convert(name, text);
    return { ms: performance.now() - t0, ok: true, r };
  } catch (e) {
    const known = e instanceof ArchError;
    const syntax = e instanceof SyntaxError;
    return { ms: performance.now() - t0, ok: false, known, errors: known ? e.errors : [String(e && e.message)], warnings: known ? e.warnings : [], syntax, crash: !known && !syntax, stack: !known && !syntax ? String(e && e.stack) : undefined };
  }
}

const out = {};
for (const name of readdirSync(dir).filter((f) => /\.(mmd|d2|json)$/.test(f)).sort()) {
  const text = readFileSync(join(dir, name), 'utf8');
  const a = once(name, text), b = once(name, text);
  if (!a.ok) {
    out[name] = { ok: false, known: a.known, syntax: a.syntax, crash: a.crash, stack: a.stack, errors: a.errors, warnings: a.warnings, ms: Math.max(a.ms, b.ms), deterministic: JSON.stringify(a.errors) === JSON.stringify(b.errors) };
    continue;
  }
  const { r } = a;
  const payload = JSON.stringify(r.payload);
  out[name] = {
    ok: true, ms: Math.max(a.ms, b.ms), warnings: r.warnings,
    counts: { nodes: r.graph.nodes.length, edges: r.graph.edges.length, groups: r.graph.groups.length },
    nodeLabels: r.graph.nodes.map((n) => n.label),
    steps: r.textSteps.length,
    tableRows: (function find(x) { if (Array.isArray(x)) { for (const y of x) { const v = find(y); if (v !== null) return v; } return null; } if (x && typeof x === 'object') { if (x.type === 'table' && Array.isArray(x.rows)) return x.rows.length; for (const k of Object.keys(x)) { const v = find(x[k]); if (v !== null) return v; } } return null; })(r.payload),
    blockErrors: validateBlock(r.block),
    payload,
    deterministic: payload === JSON.stringify(once(name, text).r.payload),
  };
}
console.log(JSON.stringify(out));
