// node --test tests/try_mermaid_worker.test.mjs : the converter worker behind the Mermaid paste window (public/try-mermaid/convert.worker.js).
// The limits must hold inside the worker, whatever the page does.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const CODE = readFileSync(join(HERE, '..', 'public', 'try-mermaid', 'convert.worker.js'), 'utf8');
function run(msg) {
  let out;
  const self = { postMessage: (m) => { out = m; } };
  vm.runInContext(CODE, vm.createContext({ self }));
  self.onmessage({ data: msg });
  return JSON.parse(JSON.stringify(out));   // the worker's objects belong to another realm: compare them as plain data
}
const FLOW = 'flowchart LR\n a[User]-->|asks|b[Agent]\n b-->|calls|c[(Catalogue)]\n c-->|returns|b\n b-->|draws|d[Screen]';
const nodes = (n) => 'flowchart LR\n' + Array.from({ length: n }, (_, i) => ` n${i}[N${i}]`).join('\n') + '\n n0-->n1';
const edges = (n) => 'flowchart LR\n' + Array.from({ length: n }, (_, i) => ` a${i % 2 ? 'a' : 'b'}[A${i}]-->|e${i}|b${i % 2 ? 'b' : 'a'}[B${i}]`).join('\n');

test('a small flowchart becomes a numbered film with a text alternative', () => {
  const r = run({ id: 1, mode: 'mermaid', text: FLOW });
  assert.equal(r.ok, true); assert.equal(r.id, 1);
  assert.deepEqual(r.payload.blocks.map((b) => b.type), ['motion_timeline', 'table']);
  assert.equal(r.steps.length, 4); assert.deepEqual(r.counts, { nodes: 4, edges: 4 });
  assert.ok(r.durationSeconds > 2 && r.durationSeconds <= 120);
});
test('D2 works too', () => {
  const r = run({ id: 2, mode: 'd2', text: 'a: A\nb: B\na -> b: go' });
  assert.equal(r.ok, true); assert.deepEqual(r.counts, { nodes: 2, edges: 1 });
});
test('13 nodes are refused with a plain sentence and the counts', () => {
  const r = run({ id: 3, mode: 'mermaid', text: nodes(13) });
  assert.equal(r.ok, false); assert.equal(r.counts.nodes, 13); assert.match(r.errors[0], /13 nodes; the limit is 12/);
  assert.equal(run({ id: 4, mode: 'mermaid', text: nodes(12) }).ok, true);
});
test('more than 16 edges are refused', () => {
  const t = 'flowchart LR\n' + Array.from({ length: 17 }, (_, i) => ` a-->|e${i}|b`).join('\n');
  const r = run({ id: 5, mode: 'mermaid', text: t });
  assert.equal(r.ok, false); assert.match(r.errors.join(' '), /edges|limit/);
});
test('20,001 characters and a 501-character line are refused before parsing', () => {
  let r = run({ id: 6, mode: 'mermaid', text: 'x'.repeat(20001) });
  assert.equal(r.ok, false); assert.match(r.errors[0], /20,001 characters; the limit is 20,000/);
  r = run({ id: 7, mode: 'mermaid', text: 'flowchart LR\n a[' + 'y'.repeat(600) + ']-->b' });
  assert.equal(r.ok, false); assert.match(r.errors[0], /line 2 is .* the limit is 500 per line/);
});
test('a sequence diagram gets the converter\'s own sentence, with the line', () => {
  const r = run({ id: 8, mode: 'mermaid', text: 'sequenceDiagram\n A->>B: hi' });
  assert.equal(r.ok, false); assert.match(r.errors[0], /^line 1: "sequenceDiagram" diagrams are not supported/);
});
test('hostile text never reaches the payload as markup, and built-in names are only names', () => {
  const t = 'flowchart LR\n constructor["<script>alert(1)</script>x"] -->|"<img src=x onerror=alert(1)>"| __proto__["&lt;b&gt;<svg onload=alert(1)>y"]\n __proto__ --> toString["<iframe src=javascript:alert(1)>z"]';
  const r = run({ id: 9, mode: 'mermaid', text: t });
  assert.equal(r.ok, true, JSON.stringify(r.errors));
  const s = JSON.stringify(r.payload);
  assert.doesNotMatch(s, /<\s*(script|img|svg|iframe|b)\b/i);
  assert.ok(r.warnings.some((w) => /HTML tags were removed/.test(w)));
  assert.equal(Object.getPrototypeOf({}), Object.prototype);
});
test('odd options and odd messages do not crash the worker', () => {
  assert.equal(run({ id: 10, mode: 'mermaid', text: FLOW, pace: '__proto__', direction: 'constructor', relation: 'yes' }).ok, true);
  const r = run(null); assert.equal(r.ok, false); assert.ok(r.errors.length);
  assert.equal(run({ id: 11, text: 12345 }).ok, false);
});
test('the relation column is off unless asked for', () => {
  const off = JSON.stringify(run({ id: 12, mode: 'mermaid', text: FLOW }).payload), on = JSON.stringify(run({ id: 13, mode: 'mermaid', text: FLOW, relation: true }).payload);
  assert.ok(on.length > off.length);
});
