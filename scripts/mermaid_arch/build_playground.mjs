#!/usr/bin/env node
// Builds playground.html: the converter modules inlined into one self-contained page.
// Usage: node scripts/mermaid_arch/build_playground.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const order = ['graph.mjs', 'schedule.mjs', 'mermaid.mjs', 'route.mjs', 'layout.mjs', 'compile.mjs', 'index.mjs'];
const code = order.map((f) => {
  let s = readFileSync(join(HERE, f), 'utf8');
  s = s.replace(/^import[^;]*;\s*$/gm, '');                       // single-statement imports
  s = s.replace(/^export \{[^}]*\}( from '[^']*')?;\s*$/gm, '');  // re-exports
  s = s.replace(/^export (async )?(function|class|const|let) /gm, '$1$2 ');
  return `// ---- ${f}\n${s}`;
}).join('\n');
if (/^\s*(import|export)\s/m.test(code)) throw new Error('unprocessed import/export left in bundle');
const tpl = readFileSync(join(HERE, 'playground.template.html'), 'utf8');
const out = tpl.replace('/*__MODULES__*/', () => code.replace(/<\/script/gi, '<\\/script'));
writeFileSync(join(HERE, 'playground.html'), out);
console.log('wrote playground.html', out.length, 'bytes');
