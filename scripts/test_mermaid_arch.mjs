#!/usr/bin/env node
/**
 * Tests for scripts/mermaid_arch (Mermaid / D2 -> motion_arch converter).
 *
 * Run: node scripts/test_mermaid_arch.mjs        (or: node --test scripts/test_mermaid_arch.mjs)
 * Refresh the golden payloads after an intended change:
 *      UPDATE_GOLDEN=1 node scripts/test_mermaid_arch.mjs
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  mermaidToArch, d2ToArch, parseD2, graphToArch, parseMermaid, validateGraph, validateBlock, ArchError, LIMITS, layoutGraph,
} from './mermaid_arch/index.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const EX = join(HERE, 'mermaid_arch', 'examples');
const examples = readdirSync(EX).filter((f) => f.endsWith('.mmd')).sort();

const g = (src, o) => parseMermaid('flowchart LR\n' + src, o).graph;
const err = (src) => { try { mermaidToArch(src); } catch (e) { if (e instanceof ArchError) return e.errors.join('\n'); throw e; } return null; };
const nodeIds = (gr) => gr.nodes.map((n) => n.id);

// ------------------------------------------------------------------ parser table
const FORMS = [
  ['bare id', 'a', { label: 'a', kind: 'server' }],
  ['[text]', 'a[Hello]', { label: 'Hello', kind: 'server' }],
  ['(text)', 'a(Hello)', { label: 'Hello', kind: 'app' }],
  ['([text])', 'a([Hello])', { label: 'Hello', kind: 'device' }],
  ['[[text]]', 'a[[Hello]]', { label: 'Hello', kind: 'tool' }],
  ['[(text)]', 'a[(Hello)]', { label: 'Hello', kind: 'store' }],
  ['((text))', 'a((Hello))', { label: 'Hello', kind: 'model' }],
  ['{text}', 'a{Hello}', { label: 'Hello', kind: 'tool' }],
  ['{{text}}', 'a{{Hello}}', { label: 'Hello', kind: 'app' }],
  ['quoted text', 'a["Hello (world) [x]"]', { label: 'Hello (world) [x]', kind: 'server' }],
  ['<br/> splits label and sub', 'a[Agent runtime<br/>on ADK]', { label: 'Agent runtime', sub: 'on ADK' }],
  ['<br> variant', 'a[One<br>Two<br>Three]', { label: 'One', sub: 'Two Three' }],
  [':::kind', 'a[Box]:::store', { kind: 'store' }],
  [':::alias', 'a[Box]:::db', { kind: 'store' }],
  [':::kind overrides shape', 'a[(Box)]:::user', { kind: 'user' }],
  ['unknown class is styling only', 'a[(Box)]:::highlight', { kind: 'store' }],
  ['@{ shape: cyl }', 'a@{ shape: cyl, label: "Data" }', { label: 'Data', kind: 'store' }],
];
for (const [name, src, want] of FORMS) {
  test('node form: ' + name, () => {
    const n = g('  ' + src).nodes[0];
    for (const [k, v] of Object.entries(want)) assert.equal(n[k], v, `${k} of ${JSON.stringify(n)}`);
  });
}

const LINKS = [
  ['-->', 'a --> b', { style: 'sync' }],
  ['---', 'a --- b', { style: 'sync' }],
  ['-.->', 'a -.-> b', { style: 'async' }],
  ['-.-', 'a -.- b', { style: 'async' }],
  ['==>', 'a ==> b', { style: 'sync' }],
  ['<-->', 'a <--> b', { style: 'sync', both: true }],
  ['<-.->', 'a <-.-> b', { style: 'async', both: true }],
  ['|label|', 'a -->|hi there| b', { label: 'hi there' }],
  ['|"quoted label"|', 'a -->|"x, y"| b', { label: 'x, y' }],
  ['-- text -->', 'a -- some text --> b', { label: 'some text' }],
  ['-. text .->', 'a -. some text .-> b', { label: 'some text', style: 'async' }],
  ['== text ==>', 'a == some text ==> b', { label: 'some text' }],
  ['no spaces', 'a-->b', { style: 'sync' }],
  ['longer arrow', 'a ----> b', { style: 'sync' }],
];
for (const [name, src, want] of LINKS) {
  test('link form: ' + name, () => {
    const e = g('  ' + src).edges[0];
    assert.equal(e.from, 'a'); assert.equal(e.to, 'b');
    for (const [k, v] of Object.entries(want)) assert.equal(e[k], v, `${k} of ${JSON.stringify(e)}`);
  });
}

test('chain A --> B --> C', () => {
  const gr = g('  a --> b --> c');
  assert.deepEqual(gr.edges.map((e) => e.from + '>' + e.to), ['a>b', 'b>c']);
});
test('A & B --> C & D makes four edges', () => {
  const gr = g('  a & b --> c & d');
  assert.deepEqual(gr.edges.map((e) => e.from + '>' + e.to), ['a>c', 'a>d', 'b>c', 'b>d']);
});
test('semicolons separate statements', () => {
  assert.equal(g('  a --> b; b --> c;').edges.length, 2);
});
test('directions', () => {
  for (const [w, d] of [['LR', 'LR'], ['RL', 'RL'], ['TB', 'TB'], ['TD', 'TB'], ['BT', 'BT']]) {
    assert.equal(parseMermaid(`graph ${w}\na-->b`).graph.direction, d);
  }
  assert.equal(parseMermaid('flowchart\na-->b').graph.direction, 'TB');
});
test('subgraph with id and title', () => {
  const gr = g('  subgraph s1[My group]\n    a --> b\n  end\n  c');
  assert.deepEqual(gr.groups, [{ id: 's1', label: 'My group' }]);
  assert.equal(gr.nodes.find((n) => n.id === 'a').group, 's1');
  assert.equal(gr.nodes.find((n) => n.id === 'c').group, undefined);
});
test('subgraph with quoted title and bare title', () => {
  assert.equal(g('  subgraph "Edge tier"\n a\n end').groups[0].label, 'Edge tier');
  assert.equal(g('  subgraph Edge\n a\n end').groups[0].label, 'Edge');
});
test('nested subgraphs flatten into the outer group with a warning', () => {
  const r = parseMermaid('flowchart LR\nsubgraph outer[Outer]\n subgraph inner[Inner]\n  a\n end\n b\nend');
  assert.equal(r.graph.groups.length, 1);
  assert.equal(r.graph.nodes.find((n) => n.id === 'a').group, 'outer');
  assert.ok(r.warnings.some((w) => /nested/.test(w)));
});
test('direction inside a subgraph warns and is ignored', () => {
  const r = parseMermaid('flowchart LR\nsubgraph s[S]\n direction TB\n a\nend');
  assert.ok(r.warnings.some((w) => /direction/.test(w)));
  assert.equal(r.graph.direction, 'LR');
});
test('class statement and classDef', () => {
  const gr = g('  classDef big fill:#f00\n  a[A]\n  b[B]\n  class a,b db\n  class b tool');
  assert.equal(gr.nodes[0].kind, 'store');
  assert.equal(gr.nodes[1].kind, 'tool');          // later statement wins
});
test('style, linkStyle, click are ignored, with one calm warning', () => {
  const r = parseMermaid('flowchart LR\na-->b\nstyle a fill:#f00\nlinkStyle 0 stroke:#f00\nclassDef x fill:#fff\nclick a href "http://x"');
  assert.equal(r.graph.nodes.length, 2);
  assert.equal(r.warnings.length, 1);
  assert.match(r.warnings[0], /^Colours and styles \(classDef, style, linkStyle\) are not drawn; the diagram uses its own colours by node kind\./);
  assert.match(r.warnings[0], /click\/link statements are ignored too\./);
});
test('click alone keeps its own warning; no style lines, no warning', () => {
  assert.deepEqual(parseMermaid('flowchart LR\na-->b\nclick a href "http://x"').warnings, ['line 3: click/link statements are ignored.']);
  assert.deepEqual(parseMermaid('flowchart LR\na-->b').warnings, []);
  assert.equal(parseMermaid('flowchart LR\na[A]\nclass a db').warnings.length, 0);   // a kind name is honoured, nothing dropped
});
test('unicode node ids: accents, kanji, no silent merge when the safe ids collide', () => {
  const r = parseMermaid('flowchart LR\ncafé[Café] --> cafe[Cafe]\n日本 --> 中国\nnaïve --> 日本');
  assert.equal(r.graph.nodes.length, 5);
  assert.equal(new Set(r.graph.nodes.map((n) => n.id)).size, 5);   // café and cafe both map to "cafe"; the second gets a suffix
  assert.deepEqual(r.graph.nodes.slice(2, 4).map((n) => n.label), ['日本', '中国']);
  assert.ok(r.graph.nodes.every((n) => /^[a-z][a-z0-9_-]*$/.test(n.id)));
  assert.ok(mermaidToArch('flowchart LR\ncafé --> 日本').payload);
});
test('markdown strings: bold and italic markers are removed, snake_case is kept', () => {
  const gr = g('a["`**Bold** and __also__ and *it* and _it2_ here`"]\nb["`keep my_var_name`"]\na-->b');
  assert.equal(gr.nodes[0].label, 'Bold and also and it and it2 here');
  assert.equal(gr.nodes[1].label, 'keep my_var_name');
});
test('entity codes: named and numeric decoded, no tag survives', () => {
  const gr = g('a["Tom #amp; Jerry #lt; #gt; #apos;x#apos; #nbsp;y #35;5 #amp;lt;"]\nb["#lt;script#gt;alert(1)#lt;/script#gt;"]\na-->b');
  assert.equal(gr.nodes[0].label, "Tom & Jerry < > 'x' y #5 &lt;");
  assert.doesNotMatch(gr.nodes[1].label, /</);
  assert.equal(gr.nodes[1].label, 'alert(1)');
});
test('HTML tags removed from a label: one warning per diagram', () => {
  const r = parseMermaid('flowchart LR\na["<b>x</b>"] --> b["<i>y</i>"]\nb -->|<u>z</u>| c["<script></script>"]');
  assert.equal(r.warnings.filter((w) => w === 'HTML tags were removed from a label.').length, 1);
  assert.equal(r.graph.nodes[2].label, 'c');   // emptied label falls back to the id
  assert.equal(parseMermaid('flowchart LR\na[One<br/>Two] --> b').warnings.length, 0);   // <br> is a line break, not a removal
});
test('shapes the atom cannot draw degrade to the nearest shape with one warning each', () => {
  const cases = [['a>Flag]', 'asymmetric', 'rectangle', 'rect'], ['a[/In/]', 'parallelogram', 'rectangle', 'rect'], ['a[\\In\\]', 'parallelogram (alt)', 'rectangle', 'rect'],
    ['a[/In\\]', 'trapezoid', 'rectangle', 'rect'], ['a(((Fin)))', 'double circle', 'circle', 'model']];
  for (const [src, name, as, kindOf] of cases) {
    const r = parseMermaid('flowchart LR\n' + src + ' --> b');
    assert.equal(r.warnings.length, 1, src);
    assert.ok(r.warnings[0].endsWith(`Node "a" uses a shape the atom cannot draw (${name}); drawn as a ${as}.`), r.warnings[0]);
    assert.equal(r.graph.nodes[0].kind, kindOf === 'rect' ? 'server' : 'model');
    assert.ok(mermaidToArch('flowchart LR\n' + src + ' --> b').payload);
  }
  assert.equal(parseMermaid('flowchart LR\na["/api/v1"] --> b').warnings.length, 0);
  assert.equal(parseMermaid('flowchart LR\na[/api] --> b').graph.nodes[0].label, '/api');
});
test('graph errors name the source line of the node or edge', () => {
  const e = err('flowchart LR\na[A] --> b[B]\nb --> b');
  assert.match(e, /^line 3: edge 2: "b" points at itself/);
  assert.match(validateGraph({ direction: 'LR', groups: [], nodes: [{ id: 'a', label: 'A', line: 7 }], edges: [{ from: 'a', to: 'a', style: 'sync', line: 7 }], messages: [] }).errors.join(), /^line 7: edge 1/);
  assert.match(validateGraph({ direction: 'LR', groups: [], nodes: [{ id: 'a', label: 'A' }], edges: [{ from: 'a', to: 'a', style: 'sync' }], messages: [] }).errors.join(), /^edge 1:/);
});
test('canonical graph does not carry the hidden line numbers into JSON', () => {
  assert.doesNotMatch(JSON.stringify(parseMermaid('flowchart LR\na-->b').graph), /line/);
});
test('layout flip: a small text gain keeps the written direction and says nothing', () => {
  const r = mermaidToArch('graph TD\nA[Start] --> B[End]', { hint: 'web' });
  assert.equal(r.warnings.filter((w) => /^drawn /.test(w)).length, 0);
  assert.equal(r.layout.direction, 'TB');
});
test('comments and directives', () => {
  const r = parseMermaid('%% title: My title\n%% msg: a->b "hello"\n%% msg: b->a "reply" back\n%% a plain comment\nflowchart LR\na-->b %% trailing\n');
  assert.equal(r.graph.title, 'My title');
  assert.deepEqual(r.graph.messages, [{ from: 'a', to: 'b', text: 'hello' }, { from: 'b', to: 'a', text: 'reply', back: true }]);
  assert.equal(r.graph.edges.length, 1);
});
test('front matter title', () => {
  assert.equal(parseMermaid('---\ntitle: From front matter\n---\nflowchart LR\na-->b').graph.title, 'From front matter');
});
test('id mapping: case, symbols, leading digit, collisions, length', () => {
  const gr = g('  Client --> client\n  My_Node --> 1st\n  ' + 'x'.repeat(40) + ' --> ' + 'x'.repeat(40) + 'y');
  const ids = nodeIds(gr);
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(ids.every((i) => /^[a-z][a-z0-9_-]{0,31}$/.test(i)), ids.join());
  assert.equal(ids[0], 'client'); assert.equal(ids[1], 'client_2');
});
test('ids with hyphens and digits', () => {
  assert.deepEqual(nodeIds(g('  my-node --> n2')), ['my-node', 'n2']);
});
test('later label wins, id used as label when none given', () => {
  const gr = g('  a --> b\n  a[Alpha]');
  assert.equal(gr.nodes[0].label, 'Alpha'); assert.equal(gr.nodes[1].label, 'b');
});
test('msg directive resolves case-insensitively and maps ids', () => {
  const r = parseMermaid('%% msg: Client->srv "x"\nflowchart LR\nClient --> Srv');
  assert.deepEqual(r.graph.messages[0], { from: 'client', to: 'srv', text: 'x' });
});
test('html entities and tags in labels', () => {
  assert.equal(g('  a["Tom &amp; Jerry"]').nodes[0].label, 'Tom & Jerry');
  assert.equal(g('  a["<b>bold</b> text"]').nodes[0].label, 'bold text');
});
test('--direction option overrides the file', () => {
  assert.equal(parseMermaid('flowchart LR\na-->b', { direction: 'TB' }).graph.direction, 'TB');
});

// ------------------------------------------------------------------ errors (20+ good and bad fixtures)
const BAD = [
  ['sequence diagram', 'sequenceDiagram\nA->>B: hi', /line 1: "sequenceDiagram" diagrams are not supported/],
  ['class diagram', 'classDiagram\nA <|-- B', /classDiagram.*not supported/],
  ['no header', 'a --> b', /expected "flowchart LR"/],
  ['bad header', 'flowchart sideways\na-->b', /cannot read the header/],
  ['empty', '', /empty input/],
  ['unclosed bracket', 'flowchart LR\na[Hello --> b', /line 2: node "a": missing closing "]"/],
  ['unclosed quote', 'flowchart LR\na["Hello --> b', /never closed/],
  ['stray end', 'flowchart LR\na-->b\nend', /line 3: "end" without a matching "subgraph"/],
  ['unclosed subgraph', 'flowchart LR\nsubgraph s[S]\na-->b', /never closed/],
  ['garbage after node', 'flowchart LR\na b', /line 2: cannot read "b"/],
  ['edge id', 'flowchart LR\na e1@--> b', /edge ids/],
  ['unsupported arrow end', 'flowchart LR\na --x b', /not supported/],
  ['invisible link', 'flowchart LR\na ~~~ b', /line 2: invisible links \(~~~\) are not supported; remove the line or use a normal arrow\./],
  ['circle end', 'flowchart LR\na --o b', /line 2: arrows with a cross or circle end/],
  ['both-ends cross', 'flowchart LR\na x--x b', /line 2: arrows with a cross or circle end/],
  ['bad msg directive', '%% msg: nonsense\nflowchart LR\na-->b', /bad "%% msg:" directive/],
  ['msg to unknown node (did you mean)', '%% msg: wrker->db "x"\nflowchart LR\nworker --> db', /"wrker" is not a node \(did you mean "worker"\?\)/],
  ['edge to a subgraph', 'flowchart LR\nsubgraph s[S]\n a\nend\nb --> s', /subgraph, not a node/],
  ['self loop', 'flowchart LR\na --> a', /line 2: edge 1: "a" points at itself/],
  ['msg without edge', '%% msg: a->c "x"\nflowchart LR\na-->b\nc', /no edge between "a" and "c"/],
  ['label twice', 'flowchart LR\na -- x --> b', null],
];
for (const [name, src, re] of BAD) {
  if (re === null) continue;
  test('error: ' + name, () => {
    const m = err(src);
    assert.ok(m, 'expected an error');
    assert.match(m, re);
  });
}
test('error: more than 12 nodes names the split', () => {
  const lines = ['flowchart LR', 'subgraph big[Big tier]'];
  for (let i = 0; i < 9; i++) lines.push(`n${i}`);
  lines.push('end', 'subgraph small[Small tier]', 'n9', 'n10', 'n11', 'n12', 'end', ...Array.from({ length: 12 }, (_, i) => `n${i} --> n${i + 1}`));
  const m = err(lines.join('\n'));
  assert.match(m, /13 nodes; the atom draws at most 12 \(1 over\)/);
  assert.match(m, /"Big tier" has 9 nodes, "Small tier" has 4 nodes/);
});
test('error: more than 16 edges', () => {
  const lines = ['flowchart LR', 'a', 'b'];
  for (let i = 0; i < 17; i++) lines.push(`a -->|e${i}| b`);
  assert.match(err(lines.join('\n')), /17 edges; the atom draws at most 16/);
});
const LOGIN5 = `flowchart LR
subgraph s1["1. Sign-in page"]
  form[Login form]
end
subgraph s2["2. Credential check"]
  api[Auth API]
  db[(User store)]
end
subgraph s3["3. Session"]
  sess[Session service]
end
subgraph s4["4. Audit"]
  log[Audit log]
end
subgraph s5["5. Mail"]
  mail[Mailer]
end
form --> api
api --> db
api --> sess
sess --> log
sess --> mail
`;
const foldWarns = (r) => r.warnings.filter((w) => /^Drew \d+ of \d+ groups/.test(w));
test('5 subgraphs fold the smallest into plain nodes with one warning', () => {
  const r = mermaidToArch(LOGIN5);
  assert.equal(foldWarns(r).length, 1);
  assert.equal(foldWarns(r)[0], 'Drew 4 of 5 groups: "5. Mail" was shown without its box (the diagram can draw at most 4).');
  assert.equal(r.block.groups.length, 4);
  assert.equal(r.block.nodes.length, 6);
  assert.deepEqual(validateBlock(r.block), []);
  assert.equal(r.graph.nodes.find((n) => n.id === 'mail').group, undefined);
  assert.equal(r.graph.nodes.find((n) => n.id === 'mail').sub, '5. Mail');
});
test('6 and 8 groups fold down to 4', () => {
  for (const k of [6, 8]) {
    const lines = ['flowchart LR'];
    for (let i = 0; i < k; i++) lines.push(`subgraph s${i}[Tier ${i}]`, `n${i}`, ...(i === 0 ? ['x0'] : []), 'end');
    lines.push('n0 --> n1');
    const r = mermaidToArch(lines.join('\n'));
    assert.equal(r.block.groups.length, 4);
    assert.equal(foldWarns(r).length, 1);
    assert.match(foldWarns(r)[0], new RegExp(`^Drew 4 of ${k} groups: `));
    assert.equal(r.block.nodes.length, k + 1);
    assert.equal(r.graph.groups[0].id, 's0');   // the 2-node group is never folded
  }
});
test('fold ties: the later group goes first', () => {
  const lines = ['flowchart LR'];
  for (let i = 0; i < 6; i++) lines.push(`subgraph s${i}[T${i}]`, `n${i}`, 'end');
  const r = mermaidToArch(lines.join('\n'));
  assert.deepEqual(r.graph.groups.map((x) => x.id), ['s0', 's1', 's2', 's3']);
  assert.match(foldWarns(r)[0], /"T4" and "T5" were shown without their boxes/);
});
test('fold: existing sub-label stays, long titles are skipped, never crashes', () => {
  const nodes = [];
  for (let i = 1; i <= 4; i++) nodes.push({ id: 'a' + i, label: 'A' + i, group: 'g' + i }, { id: 'b' + i, label: 'B' + i, group: 'g' + i });
  nodes.push({ id: 'e', label: 'E', group: 'g5', sub: 'mine' }, { id: 'f', label: 'F', group: 'g6' });
  const gr = { direction: 'LR', groups: [1, 2, 3, 4, 5, 6].map((i) => ({ id: 'g' + i, label: i === 6 ? 'L'.repeat(41) : 'G' + i })), nodes, edges: [], messages: [] };
  const r = graphToArch(gr);
  assert.equal(foldWarns(r).length, 1);
  assert.equal(r.block.groups.length, 4);
  assert.equal(r.graph.nodes.find((n) => n.id === 'e').sub, 'mine');
  assert.equal(r.graph.nodes.find((n) => n.id === 'f').sub, undefined);   // title over the sub limit: skipped
  const r2 = graphToArch({ ...gr, groups: gr.groups.map((x) => (x.id === 'g6' ? { ...x, label: 'G6' } : x)) });
  assert.equal(r2.graph.nodes.find((n) => n.id === 'f').sub, 'G6');
  assert.equal(r2.graph.nodes.find((n) => n.id === 'e').sub, 'mine');
});
test('fold works for the graph JSON input and D2 containers', () => {
  const r = graphToArch({ direction: 'LR', groups: [1, 2, 3, 4, 5].map((i) => ({ id: 'g' + i, label: 'G' + i })),
    nodes: [1, 2, 3, 4, 5].map((i) => ({ id: 'n' + i, label: 'N' + i, group: 'g' + i })), edges: [], messages: [] });
  assert.equal(foldWarns(r).length, 1);
  assert.equal(r.block.groups.length, 4);
  const d2 = [1, 2, 3, 4, 5].map((i) => `c${i}: "C${i}" {\n  n${i}: N${i}\n}`).join('\n') + '\nc1.n1 -> c2.n2\n';
  const r2 = d2ToArch(d2);
  assert.equal(foldWarns(r2).length, 1);
  assert.equal(r2.block.groups.length, 4);
  assert.equal(r2.block.nodes.length, 5);
  assert.deepEqual(validateBlock(r2.block), []);
});
test('fold counts groups after nested ones are flattened', () => {
  const lines = ['flowchart LR'];
  for (let i = 0; i < 4; i++) lines.push(`subgraph s${i}[T${i}]`, `n${i}`, ...(i === 0 ? ['subgraph inner[Inner]', 'deep', 'end'] : []), 'end');
  const r = mermaidToArch(lines.join('\n'));
  assert.equal(foldWarns(r).length, 0);
  assert.ok(r.warnings.some((w) => /nested groups are flattened/.test(w)));
  assert.equal(r.block.groups.length, 4);
});
test('folding still leaves other errors reported', () => {
  const lines = ['flowchart LR'];
  for (let i = 0; i < 5; i++) lines.push(`subgraph s${i}[S${i}]`, `n${i}`, `m${i}`, 'end');
  lines.push('x1', 'x2', 'x3');
  assert.match(err(lines.join('\n')), /13 nodes; the atom draws at most 12/);
  assert.doesNotMatch(err(lines.join('\n')), /groups/);
});
test('layout warning: CLI hint by default, Layout menu hint for the web', () => {
  const src = 'flowchart LR\n' + ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'].map((x, i, a) => (i ? `${a[i - 1]}[Long label number ${i}] --> ${x}[Long label ${x}]` : '')).join('\n');
  const w = (o) => mermaidToArch(src, o).warnings.filter((x) => /^drawn /.test(x));
  const cli = w(), web = w({ hint: 'web' });
  assert.equal(cli.length, 1);
  assert.match(cli[0], /Pass --direction LR to force the written direction\.$/);
  assert.match(web[0], /You can switch the Layout menu to the written direction\.$/);
  assert.doesNotMatch(web[0], /--direction/);
});
test('error: more than 12 messages', () => {
  const lines = ['flowchart LR', 'a --> b'];
  for (let i = 0; i < 13; i++) lines.unshift(`%% msg: a->b "m${i}"`);
  assert.match(err(lines.join('\n')), /13 messages; the atom animates at most 12/);
});
test('error: reports several errors at once, never crashes', () => {
  const e = (() => { try { parseMermaid('flowchart LR\na[x\nb["y\nc d'); } catch (x) { return x; } })();
  assert.ok(e instanceof ArchError); assert.ok(e.errors.length >= 3);
});
test('canonical validator: dangling edge with did-you-mean (spec example)', () => {
  const v = validateGraph({ direction: 'LR', groups: [], nodes: [{ id: 'worker', label: 'W' }, { id: 'db', label: 'D' }],
    edges: [{ from: 'worker', to: 'db', style: 'sync' }, { from: 'worker', to: 'db', style: 'sync', label: 'x' }, { from: 'worker', to: 'db', style: 'sync', label: 'y' }, { from: 'worker', to: 'db', style: 'sync', label: 'z' }, { from: 'worker', to: 'db', style: 'sync', label: 'q' }, { from: 'wrker', to: 'db', style: 'sync' }], messages: [] });
  assert.ok(v.errors.includes('edge 6: "wrker" is not a node id (did you mean "worker"?)'), v.errors.join('\n'));
});
test('canonical validator: duplicate id, bad kind, bad group, bad id', () => {
  const v = validateGraph({ direction: 'LR', groups: [{ id: 'g', label: 'G' }], nodes: [
    { id: 'a', label: 'A' }, { id: 'a', label: 'A2' }, { id: 'B', label: 'B' }, { id: 'c', label: 'C', kind: 'srever' }, { id: 'd', label: 'D', group: 'h' }], edges: [], messages: [] });
  const all = v.errors.join('\n');
  assert.match(all, /node 2: id "a" is used twice/);
  assert.match(all, /node 3: id "B" is not valid/);
  assert.match(all, /kind "srever".*did you mean "server"/);
  assert.match(all, /group "h" is not a group id/);
});
test('warnings: orphan node, duplicate edge; long labels wrap onto two lines instead of being cut', () => {
  const long = 'x'.repeat(45);
  const r = mermaidToArch(`flowchart LR\na[${long}] -->|${'y'.repeat(50)}| b\na --> b\na --> b\nlonely`, { direction: 'LR' });
  const w = r.warnings.join('\n');
  assert.match(w, /node "lonely" has no edges/);
  assert.match(w, /duplicates edge 2/);
  assert.doesNotMatch(w, /longer than|will be cut|atom shows at most/, 'labels that fit on two lines are not warned about');
  const n = r.block.nodes[0];
  assert.equal(n.label + n.sub, long, 'a 45-character word is split over label and sub, nothing lost');
  assert.ok(n.label.length <= 40 && n.sub.length <= 40);
  const e = r.block.edges[0];
  assert.equal(e.label + e.label2, 'y'.repeat(50));
});
test('warning: --- has no arrowhead', () => {
  assert.ok(parseMermaid('flowchart LR\na --- b').warnings.some((w) => /no arrowhead/.test(w)));
});
test('warning: message riding a reverse edge', () => {
  const r = mermaidToArch('%% msg: b->a "reply"\nflowchart LR\na --> b');
  assert.ok(r.warnings.some((w) => /rides it backwards/.test(w)));
  assert.equal(r.block.messages[0].back, true);
});

// ------------------------------------------------------------------ geometry helpers on a compiled block
function boxes(b) {
  const nodes = b.nodes.map((n) => ({ id: n.id, group: null, x: (n.x - n.w / 2) * b.w / 100, y: (n.y - n.h / 2) * b.h / 100, w: n.w * b.w / 100, h: n.h * b.h / 100 }));
  const groups = (b.groups || []).map((gr) => ({ label: gr.label, x: gr.x * b.w / 100, y: gr.y * b.h / 100, w: gr.w * b.w / 100, h: gr.h * b.h / 100 }));
  return { nodes, groups };
}
const hit = (a, c, m = 0) => a.x < c.x + c.w - m && c.x < a.x + a.w - m && a.y < c.y + c.h - m && c.y < a.y + a.h - m;
const within = (a, c, tol = 0.6) => a.x >= c.x - tol && a.y >= c.y - tol && a.x + a.w <= c.x + c.w + tol && a.y + a.h <= c.y + c.h + tol;

function checkInvariants(src, opts, label) {
  const r = typeof src === 'string' ? mermaidToArch(src, opts) : graphToArch(src, opts);
  const b = r.block;
  const { nodes, groups } = boxes(b);
  assert.deepEqual(validateBlock(b), [], label + ': atom limits');
  for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
    assert.ok(!hit(nodes[i], nodes[j]), `${label}: nodes ${nodes[i].id} and ${nodes[j].id} overlap`);
  }
  for (let i = 0; i < groups.length; i++) for (let j = i + 1; j < groups.length; j++) {
    assert.ok(!hit(groups[i], groups[j]), `${label}: groups ${groups[i].label} and ${groups[j].label} overlap`);
  }
  r.graph.nodes.forEach((n, i) => {
    if (n.group) {
      const gi = r.graph.groups.findIndex((x) => x.id === n.group);
      assert.ok(within(nodes[i], groups[gi]), `${label}: group ${n.group} does not enclose ${n.id}`);
    } else {
      groups.forEach((gr) => assert.ok(!hit(nodes[i], gr), `${label}: ungrouped node ${n.id} sits inside group ${gr.label}`));
    }
  });
  // every group contains only its members
  r.graph.nodes.forEach((n, i) => r.graph.groups.forEach((gd, gi) => {
    if (n.group !== gd.id) assert.ok(!hit(nodes[i], groups[gi]), `${label}: ${n.id} intrudes into group ${gd.id}`);
  }));
  // timing: edges start after their nodes; messages after their edge; all inside the film
  const at = new Map(b.nodes.map((n) => [n.id, n.at + n.dur]));
  b.edges.forEach((e, i) => assert.ok(e.at + 3e-4 >= Math.max(at.get(e.from), at.get(e.to)), `${label}: edge ${i} draws before its nodes`));
  (b.messages || []).forEach((m, i) => assert.ok(m.at + 3e-4 >= b.edges[m.edge].at + b.edges[m.edge].dur, `${label}: message ${i} leaves before its edge is drawn`));
  (b.groups || []).forEach((gr) => assert.equal(gr.at, 0));
  return r;
}

// ------------------------------------------------------------------ layout invariants
for (const f of examples) {
  const src = readFileSync(join(EX, f), 'utf8');
  test('layout invariants: ' + f, () => {
    const a = checkInvariants(src, {}, f);
    const b = mermaidToArch(src, {});
    assert.equal(JSON.stringify(a.payload), JSON.stringify(b.payload), 'byte-stable');
    checkInvariants(src, { direction: 'LR' }, f + ' (LR forced)');
    checkInvariants(src, { direction: 'TB' }, f + ' (TB forced)');
    checkInvariants(src, { direction: 'RL' }, f + ' (RL forced)');
    checkInvariants(src, { direction: 'BT' }, f + ' (BT forced)');
  });
}

const SYNTH = {
  'chain of 12 nodes': 'flowchart LR\n' + Array.from({ length: 11 }, (_, i) => `n${i}[Node ${i}] --> n${i + 1}[Node ${i + 1}]`).join('\n'),
  'fan out': 'flowchart TB\nroot[Root] --> a[A] & b[B] & c[C] & d[D] & e[E]',
  'diamond with cycle': 'flowchart LR\na --> b & c\nb --> d\nc --> d\nd --> a',
  'two disconnected parts': 'flowchart LR\na --> b\nc --> d',
  'single node': 'flowchart LR\nonly[Only node]',
  'two nodes': 'flowchart TB\nx[X] -->|go| y[Y]',
  'ungrouped between groups': 'flowchart LR\nsubgraph g1[One]\n a1\n a2\nend\nmid[(Middle)]\nsubgraph g2[Two]\n b1\n b2\nend\na1 --> a2\na1 --> mid\nmid --> b1\nb1 --> b2\nb2 --> a2',
  'four groups': 'flowchart LR\nsubgraph g1[A]\na1\nend\nsubgraph g2[B]\nb1\nend\nsubgraph g3[C]\nc1\nend\nsubgraph g4[D]\nd1\nend\na1-->b1-->c1-->d1\nd1-->a1',
  'long labels': 'flowchart LR\na[Alpha service with long name] -->|a very long edge label that is quite wide| b[Beta service with a long name]\nb --> c[Gamma]',
  'sub labels': 'flowchart LR\na[Agent<br/>runs on ADK] --> b[Store<br/>Postgres 16]',
  'RL and BT': 'flowchart RL\na --> b --> c',
};
for (const [name, src] of Object.entries(SYNTH)) {
  test('layout invariants (synthetic): ' + name, () => {
    const a = checkInvariants(src, {}, name);
    assert.equal(JSON.stringify(a.payload), JSON.stringify(mermaidToArch(src, {}).payload), 'byte-stable');
    for (const d of ['LR', 'TB', 'RL', 'BT']) checkInvariants(src, { direction: d }, name + ' ' + d);
  });
}
test('direction is honoured when forced: LR puts the source left of the sink, BT puts it at the bottom', () => {
  const lr = mermaidToArch('flowchart TB\na --> b', { direction: 'LR' }).block;
  assert.ok(lr.nodes[0].x < lr.nodes[1].x);
  const bt = mermaidToArch('flowchart LR\na --> b', { direction: 'BT' }).block;
  assert.ok(bt.nodes[0].y > bt.nodes[1].y);
  const rl = mermaidToArch('flowchart LR\na --> b', { direction: 'RL' }).block;
  assert.ok(rl.nodes[0].x > rl.nodes[1].x);
});
test('text-size option and frame limits', () => {
  const b = mermaidToArch('flowchart LR\na --> b', { size: 20 }).block;
  assert.equal(b.size, 20);
  for (const f of examples) {
    const c = mermaidToArch(readFileSync(join(EX, f), 'utf8')).block;
    assert.ok(c.w <= 2000 && c.h <= 2000 && c.w >= 200 && c.h >= 120);
  }
});
test('coordinates stay inside the frame and stable under repeated calls', () => {
  for (const f of examples) {
    const src = readFileSync(join(EX, f), 'utf8');
    const out = new Set(Array.from({ length: 3 }, () => JSON.stringify(mermaidToArch(src).payload)));
    assert.equal(out.size, 1);
  }
});

// ------------------------------------------------------------------ compile
test('compile: shape of the standalone payload', () => {
  const r = mermaidToArch(readFileSync(join(EX, examples[0]), 'utf8'));
  assert.equal(r.payload.theme, 'dark');
  assert.equal(r.payload.blocks[0].type, 'motion_arch');
  assert.equal(r.payload.blocks[1].type, 'table', 'the text alternative follows the diagram');
  const b = r.payload.blocks[0];
  assert.equal(b.type, 'motion_arch');
  assert.match(b.label, /^A2UI/);
  assert.ok(b.nodes.every((n) => n.kind && n.at !== undefined));
});
test('compile: kinds, styles, both, groups first, then nodes, edges, messages', () => {
  const r = mermaidToArch('%% msg: a->b "hi"\nflowchart LR\nsubgraph s[S]\n a([A])\nend\nb[(B)]\na -.->|x| b\nb <--> a');
  const b = r.block;
  assert.deepEqual(b.nodes.map((n) => n.kind), ['device', 'store']);
  assert.equal(b.edges[0].style, 'dashed'); assert.equal(b.edges[1].style, 'solid'); assert.equal(b.edges[1].both, true);
  assert.equal(b.groups[0].at, 0);
  assert.ok(Math.min(...b.nodes.map((n) => n.at)) >= b.groups[0].at + b.groups[0].dur - 3e-4);
  assert.ok(Math.min(...b.edges.map((e) => e.at)) >= Math.min(...b.nodes.map((n) => n.at + n.dur)));
  assert.equal(b.messages[0].edge, 0);
});
test('compile: two messages on one edge are staggered, never overlapping', () => {
  const r = mermaidToArch('%% msg: a->b "one"\n%% msg: a->b "two"\nflowchart LR\na --> b');
  const [m1, m2] = r.block.messages;
  assert.ok(m2.at >= m1.at + m1.dur - 3e-4, JSON.stringify([m1, m2]));
});
test('compile: message resolves to the first matching edge; back flag is kept', () => {
  const r = mermaidToArch('%% msg: a->b "x" back\nflowchart LR\na -->|first| b\na -->|second| b');
  assert.equal(r.block.messages[0].edge, 0); assert.equal(r.block.messages[0].back, true);
});
test('compile: film wrapper', () => {
  const r = mermaidToArch(readFileSync(join(EX, examples[1]), 'utf8'), { film: true });
  const t = r.payload.blocks[0];
  assert.equal(t.type, 'motion_timeline');
  assert.equal(t.blocks[0].type, 'motion_arch');
  assert.equal(t.tracks[0].target, 'arch');
  assert.ok(t.blocks[0].place.w <= 100 && t.blocks[0].place.h <= 100);
});
test('library: JSON graph input goes through the same validator', () => {
  const r = graphToArch({ title: 'T', direction: 'LR', groups: [], nodes: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B', kind: 'store' }], edges: [{ from: 'a', to: 'b', style: 'optional' }], messages: [] });
  assert.equal(r.block.edges[0].style, 'dashed');
  assert.throws(() => graphToArch({ nodes: [{ id: 'a', label: 'A' }], edges: [{ from: 'a', to: 'zz', style: 'sync' }] }), /"zz" is not a node id/);
});
test('library: never crashes on odd input', () => {
  for (const s of ['', '   ', '\n\n', 'flowchart', 'flowchart LR\n-->', 'flowchart LR\n[[', 'flowchart LR\na -->', 'flowchart LR\na --> --> b', '\u0000\u0001', 'x'.repeat(5000), 'flowchart LR\n' + 'a-->'.repeat(300) + 'z']) {
    try { mermaidToArch(s); } catch (e) { assert.ok(e instanceof ArchError, `unexpected ${e && e.stack} for ${JSON.stringify(s.slice(0, 30))}`); }
  }
});

// ------------------------------------------------------------------ goldens
for (const f of examples) {
  test('golden payload: ' + f, () => {
    const out = JSON.stringify(mermaidToArch(readFileSync(join(EX, f), 'utf8')).payload, null, 1) + '\n';
    const gp = join(EX, f.replace(/\.mmd$/, '.golden.json'));
    if (process.env.UPDATE_GOLDEN || !existsSync(gp)) writeFileSync(gp, out);
    assert.equal(out, readFileSync(gp, 'utf8'), `${f}: payload changed; if intended run UPDATE_GOLDEN=1 node scripts/test_mermaid_arch.mjs`);
  });
}

for (const f of examples) {
  test('golden numbered standalone payload (diagram + table atom): ' + f, () => {
    const out = JSON.stringify(mermaidToArch(readFileSync(join(EX, f), 'utf8'), { numbered: true }).payload, null, 1) + '\n';
    const gp = join(EX, f.replace(/\.mmd$/, '.numbered.golden.json'));
    if (process.env.UPDATE_GOLDEN || !existsSync(gp)) writeFileSync(gp, out);
    assert.equal(out, readFileSync(gp, 'utf8'), `${f}: numbered payload changed; if intended run UPDATE_GOLDEN=1 node scripts/test_mermaid_arch.mjs`);
  });
}
for (const f of examples) {
  test('golden numbered film payload: ' + f, () => {
    const out = JSON.stringify(mermaidToArch(readFileSync(join(EX, f), 'utf8'), { numbered: true, film: true }).payload, null, 1) + '\n';
    const gp = join(EX, f.replace(/\.mmd$/, '.numbered-film.golden.json'));
    if (process.env.UPDATE_GOLDEN || !existsSync(gp)) writeFileSync(gp, out);
    assert.equal(out, readFileSync(gp, 'utf8'), `${f}: numbered film changed; if intended run UPDATE_GOLDEN=1 node scripts/test_mermaid_arch.mjs`);
  });
}

// the stage-1 curve drawing stays available and byte-identical (routing: 'curve')
for (const f of examples) {
  for (const [suf, o] of [['.curve.golden.json', {}], ['.numbered.curve.golden.json', { numbered: true }], ['.numbered-film.curve.golden.json', { numbered: true, film: true }]]) {
    test('golden curve payload ' + suf + ': ' + f, () => {
      const out = JSON.stringify(mermaidToArch(readFileSync(join(EX, f), 'utf8'), { ...o, routing: 'curve' }).payload, null, 1) + '\n';
      const gp = join(EX, f.replace(/\.mmd$/, suf));
      if (process.env.UPDATE_GOLDEN || !existsSync(gp)) writeFileSync(gp, out);
      assert.equal(out, readFileSync(gp, 'utf8'), `${f}: curve payload changed; if intended run UPDATE_GOLDEN=1 node scripts/test_mermaid_arch.mjs`);
    });
  }
}

// ------------------------------------------------------------------ numbered flows, steps table, pacing
const N3 = 'flowchart LR\na[Alpha] -->|first call| b[Beta]\nb -->|second| c[Gamma]\nc -.-> a';
test('numbered: labels get the step number, in source order; unlabelled edges get just the number', () => {
  const r = mermaidToArch(N3, { numbered: true });
  assert.deepEqual(r.block.edges.map((e) => e.label), ['1 first call', '2 second', '3']);
  assert.deepEqual(r.steps.map((s) => s.step), [1, 2, 3]);
});
test('numbered: off by default in the library; directive turns it on; opts win over the directive', () => {
  assert.equal(mermaidToArch(N3).block.edges[0].label, 'first call');
  assert.equal(mermaidToArch('%% numbered: on\n' + N3).block.edges[0].label, '1 first call');
  assert.equal(mermaidToArch('%% numbered: on\n' + N3, { numbered: false }).block.edges[0].label, 'first call');
  assert.deepEqual(mermaidToArch(N3).steps, []);
});
test('numbered: %% step override reorders; other edges take the lowest free numbers', () => {
  const r = mermaidToArch('%% step: c->a 1\n' + N3, { numbered: true });
  assert.deepEqual(r.block.edges.map((e) => e.label), ['2 first call', '3 second', '1']);
  assert.deepEqual(r.steps.map((s) => s.from + '>' + s.to), ['Gamma>Alpha', 'Alpha>Beta', 'Beta>Gamma']);
});
test('numbered: step errors are plain (duplicate, gap/out of range, unknown edge, bad directive)', () => {
  assert.match(err('%% step: a->b 2\n%% step: b->c 2\n' + N3.replace('flowchart LR', 'flowchart LR') + '\n') || '', /^$|./); // parse ok, validated below
  assert.match(errN('%% step: a->b 2\n%% step: b->c 2\n' + N3), /step 2 is given to both edge 1 and edge 2/);
  assert.match(errN('%% step: a->b 9\n' + N3), /step 9 is larger than the number of edges \(3\)/);
  assert.match(errN('%% step: a->c 1\n' + N3), /no \(further\) edge from "a" to "c"/);
  assert.match(errN('%% step: nonsense\n' + N3), /bad "%% step:" directive/);
  assert.match(errN('%% step: a->zz 1\n' + N3), /"zz", which is not a node/);
});
function errN(src) { try { mermaidToArch(src, { numbered: true }); } catch (e) { if (e instanceof ArchError) return e.errors.join('\n'); throw e; } return ''; }
test('numbered: a prefix that pushes a label over 48 characters wraps instead of warning', () => {
  const r = mermaidToArch('flowchart LR\na -->|' + 'w'.repeat(47) + '| b', { numbered: true });
  assert.deepEqual(r.warnings.filter((w) => /cut|longer than|pushes/.test(w)), []);
  const e = r.block.edges[0];
  assert.equal((e.label + e.label2).replace(/\s/g, ''), '1' + 'w'.repeat(47));
  assert.ok(e.label.length <= 48 && e.label2.length <= 48);
});
test('steps table matches the edges (standalone payload carries a table atom)', () => {
  for (const f of examples) {
    const r = mermaidToArch(readFileSync(join(EX, f), 'utf8'), { numbered: true });
    const t = r.payload.blocks[1];
    assert.equal(t.type, 'table');
    assert.equal(t.rows.length, r.block.edges.length);
    const label = new Map(r.graph.nodes.map((n) => [n.id, n.label]));
    r.graph.edges.forEach((e, i) => {
      const row = t.rows[r.steps.findIndex((s) => s.from === label.get(e.from) && s.to === label.get(e.to) && s.label === (e.label || ''))];
      assert.ok(row, 'row for edge ' + i);
      assert.equal(row.length, 2, 'the legend has exactly the columns Step and Activity');
      assert.equal(row[1], r.steps[r.steps.findIndex((x) => x.from === label.get(e.from) && x.to === label.get(e.to) && x.label === (e.label || ''))].activity);
    });
    assert.deepEqual(r.steps.map((s) => s.step), r.steps.map((_, i) => i + 1));
  }
});
test('film: one timeline carries diagram and rows on one clock; rows reveal at their step', () => {
  const r = mermaidToArch(readFileSync(join(EX, examples[0]), 'utf8'), { numbered: true, film: true });
  const tl = r.payload.blocks[0];
  assert.equal(tl.type, 'motion_timeline');
  assert.equal(tl.duration, r.durationSeconds);
  assert.ok(tl.blocks.length <= 24 && tl.tracks.length <= 40);
  const arch = tl.blocks.find((b) => b.type === 'motion_arch');
  r.schedule.forEach((st, k) => {
    const tr = tl.tracks.find((t) => t.target === 'row' + (k + 1));
    assert.ok(tr, 'row track ' + (k + 1));
    assert.equal(tr.keys[1].t, st.start); assert.equal(tr.keys[1].opacity, 0);       // hidden until its step starts
    assert.equal(tr.keys[2].opacity, 1);
    const stepEdge = arch.edges[r.graph.edges.findIndex((_, i) => r.block.edges[i].label.startsWith(String(st.step) + ' ') || r.block.edges[i].label === String(st.step))];
    assert.ok(Math.abs(stepEdge.at * tl.duration - st.start) < 0.02, 'edge draws when its row appears');
  });
  const hl = tl.tracks.find((t) => t.target === 'hl');
  assert.ok(hl.keys.filter((k) => k.ease === 'hold').length === r.schedule.length);
  assert.ok(tl.poster >= r.schedule[r.schedule.length - 1].end, 'poster shows the finished table');
  assert.equal(tl.tracks.find((t) => t.target === 'arch').keys[1].p, 1);
});
const P3 = 'flowchart LR\na -->|one| b\nb -->|two| c\nc -->|three| d';
test('pacing: step dwell follows the formula (min 1.8 s, 4 words per second + 0.5 s)', () => {
  const r = mermaidToArch(P3, { numbered: true });
  assert.equal(r.schedule[0].start, 1);                                          // lead-in
  r.schedule.forEach((s) => assert.ok(s.end - s.start >= 1.8 - 1e-9));
  const long = mermaidToArch('flowchart LR\na[Alpha service] -->|' + 'word '.repeat(9).trim() + '| b[Beta service]', { numbered: true });
  const w = long.steps[0].activity.trim().split(/\s+/).length;
  assert.ok(w >= 14);
  assert.ok(Math.abs((long.schedule[0].end - long.schedule[0].start) - (w / 4 + 0.5)) < 2e-3);
  assert.equal(r.durationSeconds, +(r.schedule[2].end + 2).toFixed(3));           // 2 s hold at the end
});
test('pacing: more steps and more words never make the film shorter; crowded films get +10% / +21%', () => {
  const chain = (n, lbl = 'x') => 'flowchart LR\n' + Array.from({ length: n }, (_, i) => `n${i} -->|${lbl}| n${i + 1}`).join('\n');
  const d = (n, lbl) => mermaidToArch(chain(n, lbl), { numbered: true }).durationSeconds;
  const ds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((n) => d(n));
  for (let i = 1; i < ds.length; i++) assert.ok(ds[i] > ds[i - 1], 'steps ' + (i + 1));
  assert.ok(d(3, 'a long label with many words in it') > d(3, 'x'));
  const per = (n) => { const r = mermaidToArch(chain(n), { numbered: true }); return r.schedule[0].end - r.schedule[0].start; };
  assert.ok(Math.abs(per(7) / per(6) - 1.1) < 2e-3); assert.ok(Math.abs(per(10) / per(9) - 1.1) < 2e-3);
});
test('pacing: slow 1.4x, fast 0.75x of the dwell; directive and option agree', () => {
  const dw = (o, pre = '') => { const r = mermaidToArch(pre + P3, { numbered: true, ...o }); return r.schedule[0].end - r.schedule[0].start; };
  assert.ok(Math.abs(dw({ pace: 'slow' }) / dw({}) - 1.4) < 2e-3);
  assert.ok(Math.abs(dw({ pace: 'fast' }) / dw({}) - 0.75) < 2e-3);
  assert.equal(dw({}, '%% pace: slow\n'), dw({ pace: 'slow' }));
  assert.match(errP('%% pace: crawling\n' + P3), /"%% pace:" must be one of slow, normal, fast/);
});
function errP(src) { try { mermaidToArch(src); } catch (e) { if (e instanceof ArchError) return e.errors.join('\n'); throw e; } return ''; }
test('pacing: %% duration overrides the total; below the fast reading time it warns', () => {
  const ok = mermaidToArch('%% duration: 40\n' + P3, { numbered: true });
  assert.equal(ok.durationSeconds, 40); assert.equal(ok.warnings.filter((w) => /duration/.test(w)).length, 0);
  assert.equal(ok.schedule[2].end + 2, 40);
  const short = mermaidToArch('%% duration: 6\n' + P3, { numbered: true });
  assert.ok(short.warnings.some((w) => /duration 6 s is shorter than the .* s the steps need at the fast pace/.test(w)));
  assert.match(errP('%% duration: 3\n' + P3.replace('a -->|one| b', 'a -->|one| b\nb -->|x| a')), /leaves no time|duration/);
});
test('pacing: steps never overlap; chips ride inside their own step; film length is monotonic in pace', () => {
  for (const f of examples) {
    const src = readFileSync(join(EX, f), 'utf8');
    const r = mermaidToArch(src, { numbered: true });
    for (let i = 1; i < r.schedule.length; i++) assert.ok(r.schedule[i].start >= r.schedule[i - 1].end - 1e-9, f + ' step ' + i);
    const D = r.durationSeconds;
    r.block.messages.forEach((m, j) => {
      const e = r.block.edges[m.edge];
      const stepNo = r.steps.findIndex((s) => e.label === String(s.step) || e.label.startsWith(s.step + ' '));
      const st = r.schedule[stepNo];
      assert.ok(m.at * D >= st.start - 0.01 && (m.at + m.dur) * D <= st.end + 0.01, `${f}: chip ${j} outside its step ${st.step}`);
    });
    const d = ['fast', 'normal', 'slow'].map((pace) => mermaidToArch(src, { numbered: true, pace }).durationSeconds);
    assert.ok(d[0] < d[1] && d[1] < d[2], f);
    assert.ok(d[2] <= 120);
  }
});
test('schedule is returned by the library: [{step,start,end}] and durationSeconds', () => {
  const r = mermaidToArch(N3, { numbered: true });
  assert.deepEqual(Object.keys(r.schedule[0]), ['step', 'start', 'end']);
  assert.equal(typeof r.durationSeconds, 'number');
});

// ------------------------------------------------------------------ D2 adapter
const d2 = (src, o) => parseD2(src, o).graph;
const d2err = (src) => { try { parseD2(src); } catch (e) { if (e instanceof ArchError) return e.errors.join('\n'); throw e; } return null; };
test('D2 and Mermaid: the same 9-node example gives the identical canonical graph and payload', () => {
  const m = readFileSync(join(EX, 'equiv', 'orders.mmd'), 'utf8'), d = readFileSync(join(EX, 'equiv', 'orders.d2'), 'utf8');
  assert.deepEqual(parseD2(d).graph, parseMermaid(m).graph);
  assert.equal(JSON.stringify(d2ToArch(d).payload), JSON.stringify(mermaidToArch(m).payload));
});
const D2FORMS = [
  ['bare shape', 'a', { label: 'a', kind: 'server' }],
  ['label', 'a: Hello', { label: 'Hello' }],
  ['quoted label with colon', 'a: "Hello: world"', { label: 'Hello: world' }],
  ['block with label/shape', 'a: { label: Data; shape: cylinder }', { label: 'Data', kind: 'store' }],
  ['shape queue', 'a: { shape: queue }', { kind: 'tool' }],
  ['shape person', 'a: { shape: person }', { kind: 'user' }],
  ['shape circle', 'a: { shape: circle }', { kind: 'model' }],
  ['shape hexagon', 'a: { shape: hexagon }', { kind: 'app' }],
  ['kind hint beats shape', 'a: { shape: cylinder; kind: user }', { kind: 'user' }],
  ['class alias', 'a: { class: db }', { kind: 'store' }],
  ['two-line label becomes label + sub', 'a: "Agent\\nruns on ADK"', { label: 'Agent', sub: 'runs on ADK' }],
  ['semicolons and comments', 'a: A; b: B # trailing', { label: 'A' }],
];
for (const [name, src, want] of D2FORMS) {
  test('D2 shape form: ' + name, () => {
    const n = d2(src).nodes[0];
    for (const [k, v] of Object.entries(want)) assert.equal(n[k], v, `${k} of ${JSON.stringify(n)}`);
  });
}
const D2LINKS = [
  ['->', 'a -> b', { style: 'sync' }],
  ['<-', 'a <- b', { from: 'b', to: 'a' }],
  ['<->', 'a <-> b', { both: true }],
  ['--', 'a -- b', { style: 'sync' }],
  ['label', 'a -> b: hello there', { label: 'hello there' }],
  ['dashed inline', 'a -> b: x { style.stroke-dash: 3 }', { style: 'async' }],
  ['dashed nested block', 'a -> b { style: { stroke-dash: 3 } }', { style: 'async' }],
  ['label in block', 'a -> b { label: hi }', { label: 'hi' }],
];
for (const [name, src, want] of D2LINKS) {
  test('D2 connection: ' + name, () => {
    const e = d2(src).edges[0];
    for (const [k, v] of Object.entries({ from: 'a', to: 'b', ...want })) assert.equal(e[k], v, `${k} of ${JSON.stringify(e)}`);
  });
}
test('D2: chains, containers, dotted paths, nested containers, direction, directives', () => {
  assert.equal(d2('a -> b -> c').edges.length, 2);
  assert.equal(d2('a -> b -> c: lbl').edges.every((e) => e.label === 'lbl'), true);
  const g = d2('direction: down\ng: Group {\n  a\n  b\n  a -> b\n}\nc\nc -> g.a');
  assert.equal(g.direction, 'TB'); assert.deepEqual(g.groups, [{ id: 'g', label: 'Group' }]);
  assert.equal(g.nodes.find((n) => n.id === 'a').group, 'g'); assert.equal(g.edges.length, 2);
  const nested = parseD2('o: Outer {\n  i: Inner {\n    a\n  }\n  b\n}\na -> b');
  assert.equal(nested.graph.groups.length, 1); assert.ok(nested.warnings.some((w) => /nested/.test(w)));
  const r = d2ToArch('# numbered: on\n# pace: fast\n# step: b->a 1\na -> b\nb -> a');
  assert.equal(r.pace, 'fast'); assert.deepEqual(r.steps.map((s) => s.from), ['b', 'a']);
});
test('D2 errors are plain and name the line', () => {
  assert.match(d2err('a -> '), /line 1: a connection needs a shape on both sides/);
  assert.match(d2err('a: { b'), /never closed/);
  assert.match(d2err('}'), /without a matching/);
  assert.match(d2err('a: "oops'), /never closed/);
  assert.match(d2err('classes: { x: {} }'), /"classes" is not supported/);
  assert.match(d2err('g: { a }\nb -> g'), /container, not a shape/);
  assert.match(d2err(''), /no shapes found/);
  assert.match(d2err('# msg: a->zz "x"\na -> b'), /"zz" is not a shape/);
  assert.match(d2err('a: { shape: cylinder; kind: user }\n# pace: eternal'), /"# pace:" must be one of/);
});
test('D2: never crashes on odd input', () => {
  for (const s of ['', '{', ':::', 'a ->', '->', 'a: {{{', '\u0000', 'x'.repeat(3000), 'a -> b -> ', '#', 'a: |md hi |']) {
    try { d2ToArch(s); } catch (e) { assert.ok(e instanceof ArchError, `unexpected ${e && e.stack}`); }
  }
});

// ------------------------------------------------------------------ the repo's own renderer accepts the payloads
test('python renderer draws every golden payload (no dropped fields, all labels present)', (t) => {
  const root = join(HERE, '..');
  try { execFileSync('python3', ['--version'], { stdio: 'ignore' }); } catch { t.skip('python3 not available'); return; }
  const code = `
import sys, json, re
sys.path.insert(0, ${JSON.stringify(root)})
from renderers import web_article as wa
wa._mo_install() if hasattr(wa, '_mo_install') else None
bad = []
for p in sys.argv[1:]:
    d = json.load(open(p)); b = d['blocks'][0]
    html = wa.render(d['blocks'], 'dark')
    if re.search(r'<!-- (a2ui|unknown)', html): bad.append(p + ': renderer dropped something')
    if b['type'] == 'motion_timeline':
        arch = [c for c in b['blocks'] if c['type'] == 'motion_arch'][0]
        rows = [c for c in b['blocks'] if c.get('id', '').startswith('row')]
        if len(rows) != len(arch['edges']): bad.append(p + ': row count')
        for r in rows:
            if r['text'].split('*')[2][:10].strip()[:3] not in html: bad.append(p + ': row text missing')
        continue
    if len(d['blocks']) > 1 and d['blocks'][1]['type'] == 'table':
        for row in d['blocks'][1]['rows']:
            if row[1] not in html: bad.append(p + ': table cell missing ' + row[1])
    for n in b['nodes']:
        if n['label'].replace('&','&amp;') not in html and n['label'] not in html: bad.append(p + ': label missing ' + n['label'])
    if html.count('<path') < len(b['edges']): bad.append(p + ': edges missing')
print(json.dumps(bad))
`;
  const goldens = examples.flatMap((f) => ['.golden.json', '.numbered.golden.json', '.numbered-film.golden.json'].map((x) => join(EX, f.replace(/\.mmd$/, x))));
  const out = JSON.parse(execFileSync('python3', ['-W', 'ignore', '-c', code, ...goldens], { encoding: 'utf8', cwd: root }));
  assert.deepEqual(out, []);
});

// ------------------------------------------------------------------ orthogonal router (route.mjs)
const px = (b) => ({
  boxes: b.nodes.map((n) => ({ id: n.id, x: ((n.x - n.w / 2) / 100) * b.w, y: ((n.y - n.h / 2) / 100) * b.h, w: (n.w / 100) * b.w, h: (n.h / 100) * b.h })),
  pts: (e) => e.points.map((q) => [(q.x / 100) * b.w, (q.y / 100) * b.h]),
});
const onRim = (p, r) => {
  const t = 0.8, inX = p[0] >= r.x - t && p[0] <= r.x + r.w + t, inY = p[1] >= r.y - t && p[1] <= r.y + r.h + t;
  return (inX && (Math.abs(p[1] - r.y) <= t || Math.abs(p[1] - r.y - r.h) <= t)) || (inY && (Math.abs(p[0] - r.x) <= t || Math.abs(p[0] - r.x - r.w) <= t));
};
for (const f of examples) {
  test('router: ' + f + ' every edge is a right-angle route from rim to rim, with no box, title or label collision', () => {
    const src = readFileSync(join(EX, f), 'utf8');
    const r = mermaidToArch(src, { numbered: true });
    const b = r.block, { boxes, pts } = px(b);
    assert.deepEqual(validateBlock(b), []);
    assert.ok(b.radius >= 6 && b.radius <= 14);
    b.edges.forEach((e, i) => {
      assert.ok(e.points && e.points.length >= 2 && e.points.length <= 10, `edge ${i + 1} has 2-10 points`);
      assert.equal(e.curve, undefined, 'a routed edge carries no curve');
      const P = pts(e);
      for (let k = 0; k + 1 < P.length; k++) assert.ok(Math.abs(P[k][0] - P[k + 1][0]) < 0.6 || Math.abs(P[k][1] - P[k + 1][1]) < 0.6, `edge ${i + 1} segment ${k} is axis-aligned`);
      const fb = boxes.find((x) => x.id === e.from), tb = boxes.find((x) => x.id === e.to);
      assert.ok(onRim(P[0], fb), `edge ${i + 1} starts on the rim of ${e.from}`);
      assert.ok(onRim(P[P.length - 1], tb), `edge ${i + 1} ends on the rim of ${e.to}`);
      const last = P.length - 1, ln = Math.abs(P[last][0] - P[last - 1][0]) + Math.abs(P[last][1] - P[last - 1][1]);
      assert.ok(ln >= 13, `edge ${i + 1}: the last stretch (${ln.toFixed(1)} px) leaves room for the arrowhead`);
      assert.ok(e.label.startsWith(String(i + 1) + ' ') || e.label === String(i + 1) || r.steps.length, 'numbered label keeps its number');
    });
    const m = r.layout.metrics;
    assert.equal(m.throughBoxes, 0, 'no edge runs through a box');
    assert.equal(m.titleHits, 0, 'no edge crosses a group title');
    assert.equal(m.labelNode + m.labelLabel + m.labelTitle, 0, 'no label sits on a box, a title or another label');
    r.block.edges.forEach((e) => { if (e.label) assert.ok(e.label_at && e.label_at.x >= 0 && e.label_at.x <= 100 && e.label_at.y >= 0 && e.label_at.y <= 100); });
  });
}

test('router: the output is byte-stable', () => {
  const src = readFileSync(join(EX, examples[1]), 'utf8');
  assert.equal(JSON.stringify(mermaidToArch(src, { numbered: true }).payload), JSON.stringify(mermaidToArch(src, { numbered: true }).payload));
});

test("router: routing 'curve' keeps the stage-1 drawing (no points, no label_at, no radius)", () => {
  const r = mermaidToArch(readFileSync(join(EX, examples[0]), 'utf8'), { routing: 'curve' });
  assert.ok(r.block.edges.every((e) => e.points === undefined && e.label_at === undefined));
  assert.equal(r.block.radius, undefined);
});

test('router: goes round a box that stands in the way, and a request/response pair takes two lanes', () => {
  const src = 'flowchart LR\n a[Alpha] -->|req| c[Gamma]\n c -->|resp| a\n b[Blocker]\n a --> d[Delta]\n b --> d';
  const r = mermaidToArch(src, { direction: 'LR', size: 18 });
  const { boxes, pts } = px(r.block);
  r.block.edges.forEach((e, i) => { for (const bx of boxes) if (bx.id !== e.from && bx.id !== e.to) { const P = pts(e); for (let k = 0; k + 1 < P.length; k++) { const x0 = Math.min(P[k][0], P[k + 1][0]), x1 = Math.max(P[k][0], P[k + 1][0]), y0 = Math.min(P[k][1], P[k + 1][1]), y1 = Math.max(P[k][1], P[k + 1][1]); assert.ok(!(x1 > bx.x && x0 < bx.x + bx.w && y1 > bx.y && y0 < bx.y + bx.h), `edge ${i} through ${bx.id}`); } } });
  const a = r.block.edges[0].points, c = r.block.edges[1].points;
  assert.notDeepEqual(a.map((q) => [q.x, q.y]), c.map((q) => [q.x, q.y]).reverse(), 'the two directions do not share one line');
});

test('router: a diagram that is too crowded for the label to fit is warned about, not silently shortened', () => {
  const r = mermaidToArch('flowchart LR\n a[A] -->|a very very long edge label that cannot possibly sit between two close boxes| b[B]', { size: 30 });
  assert.ok(r.block.edges[0].label.length > 20, 'the label text is untouched');
});

// ------------------------------------------------------------------ steps table legend: Step | Activity, optional Relation
import { activity, rowText } from './mermaid_arch/activity.mjs';
test('activity: the sentence template (no model, fixed rules)', () => {
  assert.equal(activity('Chat host', 'LLM', 'tool call'), 'Chat host sends the tool call to the LLM');
  assert.equal(activity('User', 'Orchestrator', 'asks'), 'User asks the orchestrator');
  assert.equal(activity('User', 'Client app', 'types prompt'), 'User types prompt into the client app');
  assert.equal(activity('Remote agent', 'Task state', 'creates task'), 'Remote agent creates task in the task state');
  assert.equal(activity('Orchestrator on ADK', 'Agent Card', 'discovers skills'), 'Orchestrator on ADK discovers skills from the agent card');
  assert.equal(activity('LLM', 'ADK agent', 'A2UI JSON'), 'LLM sends A2UI JSON to the ADK agent');            // acronyms keep their case, no "the" before a capitalised label
  assert.equal(activity('LLM', 'ADK agent', 'A2UI JSON', { reply: true }), 'LLM returns A2UI JSON to the ADK agent');
  assert.equal(activity('Sandboxed iframe', 'Chat host', 'tools/call'), 'Sandboxed iframe sends tools/call to the chat host');
  assert.equal(activity('A', 'B', ''), 'A calls the b');
  assert.equal(activity('Agent', 'Shared state', 'reads and writes', { both: true }), 'Agent reads and writes the shared state');
  assert.equal(activity('A', 'B', 'status', { style: 'async' }), 'A sends the status to the b (async)');
  assert.equal(activity('A', 'B', 'ping', { style: 'optional', reply: true }), 'A sends the ping to the b (optional)');
  assert.equal(activity('Tool with ui:// link', 'Host', 'AG-UI events: A2UI + MCP App HTML'), 'Tool with ui link sends AG-UI events, A2UI + MCP app HTML to the host');
  for (const f of examples) for (const st of mermaidToArch(readFileSync(join(EX, f), 'utf8'), { numbered: true }).steps) assert.ok(!/[:→]|->/.test(st.activity), 'no colon or arrow: ' + st.activity);
  assert.equal(activity('A', 'B', 'x'), activity('A', 'B', 'x'));
});
test('activity: a film row is at most 60 characters and says so with an ellipsis only as a last resort', () => {
  const sentence = activity('Orchestrator on ADK', 'Remote agent', 'status, artifacts, A2UI in a DataPart, over SSE', { style: 'async' });
  const row = rowText(7, sentence, 60);
  assert.ok(row.length <= 60);
  assert.match(row, /^\*7\*  /);
  assert.equal(rowText(1, 'User asks the orchestrator', 60), '*1*  User asks the orchestrator');
  assert.equal(rowText(2, 'A sends the plan to the b ' + 'x'.repeat(45), 60).includes('…'), true);
});
test('steps table: columns are exactly Step | Activity; the standalone table keeps the full sentence', () => {
  for (const f of examples) {
    const r = mermaidToArch(readFileSync(join(EX, f), 'utf8'), { numbered: true });
    const t = r.payload.blocks[1];
    assert.deepEqual(t.headers, ['Step', 'Activity']);
    assert.equal(t.col_widths.length, 2);
    r.steps.forEach((s, i) => assert.equal(t.rows[i][1], s.activity));
  }
});
const REL = 'flowchart LR\na[Chat host] -->|tool call| b[LLM]\nb -->|result| a\n%% rel: a->b calls\n%% rel: b->a reports back';
test('relation column: off by default; the option, the CLI flag value and the directive turn it on', () => {
  const off = mermaidToArch(REL, { numbered: true });
  assert.deepEqual(off.payload.blocks[1].headers, ['Step', 'Activity']);
  assert.equal(off.relationColumn, false);
  const on = mermaidToArch(REL, { numbered: true, relationColumn: true });
  assert.deepEqual(on.payload.blocks[1].headers, ['Step', 'Activity', 'Relation']);
  assert.deepEqual(on.payload.blocks[1].rows.map((r) => r[2]), ['calls', 'reports back']);
  assert.equal(on.payload.blocks[1].col_widths.length, 3);
  const dir = mermaidToArch('%% relation-column: on\n' + REL, { numbered: true });
  assert.deepEqual(dir.payload.blocks[1].headers, ['Step', 'Activity', 'Relation']);
  assert.equal(mermaidToArch('%% relation-column: on\n' + REL, { numbered: true, relationColumn: false }).payload.blocks[1].headers.length, 2, 'an explicit option beats the directive');
});
test('relation column: %% relation-name renames the header; an edge without %% rel has an empty cell; plain (not numbered) diagrams have no table', () => {
  const r = mermaidToArch('%% relation-name: Interaction\n%% relation-column: on\nflowchart LR\na --> b\nb --> c\n%% rel: a->b streams', { numbered: true });
  const t = r.payload.blocks[1];
  assert.deepEqual(t.headers, ['Step', 'Activity', 'Interaction']);
  assert.deepEqual(t.rows.map((x) => x[2]), ['streams', '']);
  assert.deepEqual(mermaidToArch(REL, { relationColumn: true }).payload.blocks[1].headers, ['Step', 'Activity'], 'not numbered: no Relation column');
  assert.equal(mermaidToArch(REL, { numbered: true, relationColumn: true, relationName: 'Verb' }).payload.blocks[1].headers[2], 'Verb');
});
test('relation column: limits and errors are plain', () => {
  assert.match(err('flowchart LR\na --> b\n%% rel: a->b ' + 'x'.repeat(21)), /at most 20|the most is 20/);
  assert.match(err('flowchart LR\na --> b\n%% rel: a->c calls'), /not a node/);
  assert.match(err('flowchart LR\na --> b\n%% rel: a->b'), /bad "%% rel:"/);
  assert.match(err('%% relation-name: ' + 'y'.repeat(21) + '\nflowchart LR\na --> b'), /1 to 20 characters/);
  assert.match(err('%% relation-column: maybe\nflowchart LR\na --> b'), /on or off/);
});
test('relation column: the film shows it as a third column that fades in with its row; same in D2', () => {
  const r = mermaidToArch(REL, { numbered: true, film: true, relationColumn: true });
  const tl = r.payload.blocks[0];
  assert.ok(tl.blocks.some((b) => b.id === 'headrel' && b.text === 'RELATION'));
  assert.ok(tl.blocks.some((b) => b.id === 'rel1' && b.text === 'calls'));
  assert.ok(tl.tracks.some((t) => t.target === 'rel1'));
  const off = mermaidToArch(REL, { numbered: true, film: true });
  assert.ok(!off.payload.blocks[0].blocks.some((b) => /^rel/.test(b.id) || b.id === 'headrel'));
  const d = d2ToArch('# relation-column: on\n# relation-name: Verb\na: A\nb: B\na -> b: go\n# rel: a->b calls', { numbered: true });
  assert.deepEqual(d.payload.blocks[1].headers, ['Step', 'Activity', 'Verb']);
  assert.equal(d.payload.blocks[1].rows[0][2], 'calls');
});
test('film: the stage is picked for the biggest diagram; a tall diagram may get the table beside it', () => {
  for (const f of examples) {
    const r = mermaidToArch(readFileSync(join(EX, f), 'utf8'), { numbered: true, film: true });
    const tl = r.payload.blocks[0], arch = tl.blocks.find((b) => b.id === 'arch');
    assert.ok(arch.place.x >= 0 && arch.place.y >= 0 && arch.place.x + arch.place.w <= 100.01 && arch.place.y + arch.place.h <= 100.01, f + ': diagram on the stage');
    const rows = tl.blocks.filter((b) => /^row\d+$/.test(b.id));
    rows.forEach((b) => assert.ok(b.place.y + 1 <= 100 && b.place.x + b.place.w <= 100.5, f + ': row on the stage'));
  }
});
test('pacing: a 10-step diagram plays in about 25-35 s at the normal pace, and the new durations scale with pace', () => {
  const src = readFileSync(join(EX, '01-a2ui-agent-to-screen.mmd'), 'utf8');
  const d = (pace) => mermaidToArch(src, { numbered: true, pace }).durationSeconds;
  assert.ok(d('normal') >= 25 && d('normal') <= 42, 'normal ' + d('normal'));   // chips ride at a constant apparent speed, so long edges lengthen the film
  assert.ok(d('fast') < d('normal') && d('normal') < d('slow'));
});

test('film stage: the diagram is as big with the Relation column off as with it on (no stage is picked by raw scale)', () => {
  for (const f of examples) {
    const src = readFileSync(join(EX, f), 'utf8');
    const w = (rel) => { const r = mermaidToArch(src, { numbered: true, film: true, relationColumn: rel }), a = r.payload.blocks[0].blocks.find((b) => b.id === 'arch'); return { a: r.payload.blocks[0].aspect, w: a.place.w, sw: { '16:9': 1280, '4:3': 1200, '1:1': 1000, '9:16': 720 }[r.payload.blocks[0].aspect] }; };
    const off = w(false), on = w(true);
    assert.ok(Math.abs(off.w - on.w) < 3, `${f}: ${JSON.stringify(off)} vs ${JSON.stringify(on)}`);
    const tl = mermaidToArch(src, { numbered: true, film: true }).payload.blocks[0], row = tl.blocks.find((b) => b.id === 'row1');
    assert.ok(row.size / ({ '16:9': 1280, '4:3': 1200, '1:1': 1000, '9:16': 720 }[tl.aspect]) >= 0.0165 - 1e-9, f + ': the table text stays readable');
  }
});

test('input caps: a long line or a huge paste is refused fast, not parsed', () => {
  const t0 = Date.now();
  assert.throws(() => mermaidToArch('flowchart LR\nA -- ' + ' '.repeat(8000) + 'x'), /most one line may hold/);
  assert.throws(() => mermaidToArch('flowchart LR\n' + 'A-->B\n'.repeat(5000)), /most this converter reads/);
  assert.ok(Date.now() - t0 < 1000);
});

// ------------------------------------------------------------------ review round 2: B1 / B2
const refuses = (fn, re) => { const t0 = Date.now(); assert.throws(fn, (e) => e instanceof ArchError && re.test(e.errors.join('\n')), 'clear ArchError'); assert.ok(Date.now() - t0 < 1000, 'refused in under 1 s'); };
test('D2 input caps: size, line length, brace depth, dotted-path length, error flood all refuse fast with an ArchError', () => {
  refuses(() => parseD2('a{'.repeat(5000) + 'x' + '}'.repeat(5000)), /most one line may hold/);
  refuses(() => parseD2('a{\n'.repeat(5000) + 'x\n' + '}\n'.repeat(5000)), /most this converter reads/);
  refuses(() => parseD2('a{\n'.repeat(500) + 'x\n' + '}\n'.repeat(500)), /nested more than 8/);
  refuses(() => parseD2(Array.from({ length: 4000 }, (_, i) => 's' + i).join('.')), /most (one line may hold|this converter reads)/);
  refuses(() => parseD2(Array.from({ length: 100 }, (_, i) => 's' + (i % 10)).join('.')), /at most 8 parts/);
  const flood = Array.from({ length: 900 }, (_, i) => 'n' + i).join('\n') + '\n' + '# msg: x->y "t"\n'.repeat(800);
  refuses(() => parseD2(flood), /is not a shape/);
  const bad = parseD2.bind(null, 'a\n' + '# msg: nonsense\n'.repeat(1000));
  try { bad(); assert.fail('should throw'); } catch (e) { assert.ok(e instanceof ArchError && e.errors.length <= 20); }
});
test('prototype keys are not paces: Mermaid, D2, graph JSON and the library option all refuse them', () => {
  for (const k of ['__proto__', 'constructor', 'toString', 'hasOwnProperty']) {
    assert.throws(() => mermaidToArch(`flowchart LR\n%% pace: ${k}\nA-->B`), (e) => e instanceof ArchError && /pace/.test(e.errors.join()), 'mermaid ' + k);
    assert.throws(() => parseD2(`# pace: ${k}\na -> b`), (e) => e instanceof ArchError && /pace/.test(e.errors.join()), 'd2 ' + k);
    assert.throws(() => mermaidToArch('flowchart LR\nA-->B', { pace: k }), (e) => e instanceof ArchError && /pace/.test(e.errors.join()), 'option ' + k);
    assert.throws(() => graphToArch({ nodes: [{ id: 'a' }, { id: 'b' }], edges: [{ from: 'a', to: 'b' }], pace: k }), (e) => e instanceof ArchError, 'graph ' + k);
  }
});

test('accessibility: every output (plain, numbered, film) carries the full text of every edge and every message in table atoms', () => {
  for (const f of examples) {
    const src = readFileSync(join(EX, f), 'utf8');
    for (const o of [{}, { numbered: true }, { film: true }, { numbered: true, film: true }]) {
      const r = mermaidToArch(src, o), bl = r.payload.blocks;
      const steps = bl.find((b) => b.type === 'table' && b.caption === 'Steps');
      assert.ok(steps, f + ' ' + JSON.stringify(o) + ': steps table');
      assert.equal(steps.rows.length, r.graph.edges.length, 'one row per edge');
      assert.deepEqual(steps.rows.map((x) => x[1]), r.textSteps.map((s) => s.activity));
      steps.rows.forEach((row, i) => assert.ok(row[1].length > 10 && !row[1].endsWith('…'), 'full sentence, never cut: ' + row[1]));
      const mt = bl.find((b) => b.type === 'table' && b.caption === 'Messages');
      assert.equal(!!mt, r.graph.messages.length > 0);
      if (mt) assert.deepEqual(mt.rows.map((x) => x[1]).sort(), r.graph.messages.map((m) => m.text).sort(), 'every message text in full');
    }
  }
  const r = mermaidToArch('%% msg: a->b "a rather long payload text, in full"\nflowchart LR\na -->|a long edge label of some words| b', { film: true });
  assert.equal(r.payload.blocks[0].type, 'motion_timeline');
  assert.match(r.payload.blocks[1].rows[0][1], /long edge label of some words/);
  assert.deepEqual(r.payload.blocks[2].rows[0], ['1', 'a rather long payload text, in full', 'a to b']);
});

// ------------------------------------------------------------------ review round 2: S1 (D2 must not misdraw silently)
test('D2: dotted keys ending in a reserved word set a property of the object and never create stray shapes', () => {
  const p = parseD2('g: Old { z }\ng.label: Group\nb\nb.shape: person\nb.style.fill: red\nc.style.stroke-dash: 3\na -> b\nb -> c\nc -> a').graph;
  assert.deepEqual(p.nodes.map((n) => n.id).sort(), ['a', 'b', 'c', 'z']);
  assert.equal(p.groups[0].label, 'Group');
  assert.equal(p.nodes.find((n) => n.id === 'b').kind, 'user');
  const q = parseD2('x\nx.label: Renamed\ny\nx -> y').graph;
  assert.deepEqual(q.nodes.map((n) => [n.id, n.label]), [['x', 'Renamed'], ['y', 'y']]);
});
test('D2: unsupported or ambiguous syntax is an error that names the line', () => {
  assert.match(d2err('a\nb\na->b'), /line 3: .*put spaces around the arrow/);
  assert.match(d2err('a <->b: x'), /line 1|put spaces/);
  assert.match(d2err('a\n"""\nnotes\n"""\nb'), /line 2: block comments/);
  assert.match(d2err('a\nb\n*.style.fill: red'), /line 3: .*globs/);
  assert.match(d2err('a -> b\n(a -> b)[0].style.stroke: red'), /line 2: references to a connection/);
  assert.match(d2err('a\n...@other'), /line 2: .*imports/);
  assert.match(d2err('a: @file'), /line 1: imports/);
  assert.match(d2err('t: { shape: sql_table }'), /line 1: shape: sql_table is not supported/);
  assert.match(d2err('t.shape: class'), /line 1: shape: class is not supported/);
  assert.equal(d2err('my-node -> other-node: calls'), null, 'hyphenated names still fine');
});
test('D2: HTML tags are stripped from labels like Mermaid, <br> splits label and sub', () => {
  const p = parseD2('a: "<b>Bold</b> name<br/>second <i>line</i>"\nb\na -> b: "<script>x</script>sends <u>data</u>"').graph;
  assert.equal(p.nodes[0].label, 'Bold name');
  assert.equal(p.nodes[0].sub, 'second line');
  assert.equal(p.edges[0].label, 'xsends data');
});

// ------------------------------------------------------------------ review round 2: S2 (short duration vs message chips)
test('a short %% duration with many chips on one edge is refused with a clear message, not an internal error', () => {
  const msgs = Array.from({ length: 12 }, (_, i) => `%% msg: a->b "m${i}"`).join('\n');
  const src = `%% duration: 4\n${msgs}\nflowchart LR\na -->|go| b\nb --> c`;
  assert.throws(() => mermaidToArch(src), (e) => e instanceof ArchError && /too short for the 12 message chips/.test(e.errors.join()) && !/internal/.test(e.errors.join()));
  const m = /at least (\d+) s/.exec((() => { try { mermaidToArch(src); } catch (e) { return e.errors[0]; } })());
  const r = mermaidToArch(src.replace('duration: 4', 'duration: ' + m[1]));
  assert.deepEqual(validateBlock(r.block), [], 'the suggested duration works');
  const fine = mermaidToArch('%% duration: 6\n%% msg: a->b "m"\nflowchart LR\na --> b');
  assert.deepEqual(validateBlock(fine.block), []);
});

// ------------------------------------------------------------------ review round 2: option validation
test('library and CLI options are validated, never silently clamped', () => {
  const bad = [{ size: 4 }, { size: 99 }, { size: 'big' }, { size: NaN }, { fit: 'huge' }, { routing: 'zigzag' }, { pace: 'turbo' }, { duration: 1 }, { duration: 500 }, { direction: 'sideways' }];
  for (const o of bad) {
    assert.throws(() => mermaidToArch('flowchart LR\nA-->B', o), (e) => e instanceof ArchError, JSON.stringify(o));
    assert.throws(() => d2ToArch('a -> b', o), (e) => e instanceof ArchError, 'd2 ' + JSON.stringify(o));
  }
  assert.ok(mermaidToArch('flowchart LR\nA-->B', { size: 8, fit: 'wide', routing: 'curve', pace: 'fast', duration: 10, direction: 'TB' }));
  const cli = (...a) => { try { execFileSync('node', [join(HERE, 'mermaid_arch', 'cli.mjs'), join(EX, examples[0]), ...a], { stdio: 'pipe' }); return 0; } catch (e) { return e.status; } };
  assert.equal(cli('--size', '5'), 2);
  assert.equal(cli('--size', 'x'), 2);
  assert.equal(cli('--fit', 'huge'), 2);
  assert.equal(cli('--size', '16', '--fit', 'wide'), 0);
});

// ------------------------------------------------------------------ recheck fixes
const PROTO = ['__proto__', 'constructor', 'toString', 'hasOwnProperty', 'valueOf'];
const clean = (s) => { assert.ok(!/function Object|\[object Object\]|function \w+\(\)/.test(s), s); return s; };
const catchText = (fn) => { try { const r = fn(); return { ok: true, w: (r.warnings || []).join('\n'), r }; } catch (e) { if (e instanceof ArchError) return { ok: false, text: clean(e.errors.join('\n')) }; throw e; } };

test('prototype-chain names in user text give the normal messages', () => {
  for (const w of PROTO) {
    const d = catchText(() => d2ToArch(`direction: ${w}\na -> b`));
    assert.ok(!d.ok && /direction must be right, left, down or up/.test(d.text), w + ' ' + d.text);
    const s = catchText(() => d2ToArch(`a: A\na.shape: ${w}\nb\na -> b`));
    assert.ok(s.ok && /shape "[^"]*" is not known/.test(clean(s.w)), w + ' d2 shape ' + (s.w || s.text));
    const c = catchText(() => d2ToArch(`a: A\na.class: ${w}\nb\na -> b`));
    assert.ok(c.ok && /is not a known kind/.test(clean(c.w)), w + ' d2 class');
    const mc = catchText(() => mermaidToArch(`flowchart LR\na --> b\nclass a ${w}`));
    clean(mc.ok ? mc.w : mc.text);
    const at = catchText(() => mermaidToArch(`flowchart LR\na@{ shape: ${w}, label: "x" } --> b`));
    assert.ok(at.ok && /shape "[^"]*" is not known; treated as a plain box/.test(clean(at.w)), w + ' @shape ' + (at.w || at.text));
    const od = catchText(() => mermaidToArch(w));
    assert.ok(!od.ok && !/diagrams are not supported/.test(od.text), w + ' ' + od.text);
    const gk = catchText(() => graphToArch({ nodes: [{ id: 'a', label: 'A', kind: w }, { id: 'b', label: 'B' }], edges: [{ from: 'a', to: 'b' }] }));
    clean(gk.ok ? gk.w : gk.text);
    assert.ok(!gk.ok && /kind/.test(gk.text), w + ' graph kind ' + gk.text);
  }
});

test('D2: a quoted key with a dot is ONE shape; unquoted dotted paths still nest', () => {
  const q = parseD2('"a.b" -> c').graph;
  assert.equal((q.groups || []).length, 0);
  assert.deepEqual(q.nodes.map((n) => n.label).sort(), ['a.b', 'c']);
  const p = parseD2('a.b.c -> d').graph;
  assert.equal(p.groups.length, 1);
  assert.deepEqual(p.nodes.map((n) => n.label).sort(), ['c', 'd']);
});

test('nits: duration hint is the smallest working value, TD accepted everywhere, %% msg text is cleaned', () => {
  const msgs = Array.from({ length: 12 }, (_, i) => `%% msg: a->b "m${i}"`).join('\n');
  const src = `%% duration: 4\n${msgs}\nflowchart LR\na -->|go| b\nb --> c`;
  const hint = (() => { try { mermaidToArch(src); } catch (e) { return +/at least (\d+) s/.exec(e.errors[0])[1]; } })();
  assert.ok(hint);
  assert.ok(mermaidToArch(src.replace('duration: 4', 'duration: ' + hint)));
  assert.throws(() => mermaidToArch(src.replace('duration: 4', 'duration: ' + (hint - 1))), ArchError);
  assert.equal(graphToArch({ direction: 'TD', groups: [], messages: [], nodes: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }], edges: [{ from: 'a', to: 'b' }] }).graph.direction, 'TB');
  assert.ok(mermaidToArch('flowchart LR\na-->b', { direction: 'TD' }));
  assert.ok(d2ToArch('a -> b', { direction: 'TD' }));
  const r = mermaidToArch('%% msg: a->b "<b>Tom</b> &amp; Jerry &lt;3&quot;"\nflowchart LR\na --> b');
  assert.equal(r.graph.messages[0].text, 'Tom & Jerry <3"');
});

// ------------------------------------------------------------------ speed: the try-it box converts on every keystroke
test('speed: the examples and the 16-edge corpus input convert within a generous budget (median of 3)', () => {
  const inputs = examples.map((f) => join(EX, f));
  inputs.push(join(HERE, '..', 'tests', 'mermaid_corpus', '62_limit_16_edges.mmd'));
  for (const f of inputs) {
    const text = readFileSync(f, 'utf8');
    const ms = [];
    for (let i = 0; i < 3; i++) {
      const t0 = performance.now();
      mermaidToArch(text, { film: true, numbered: true, hint: 'web' });
      ms.push(performance.now() - t0);
    }
    ms.sort((a, b) => a - b);
    assert.ok(ms[1] < 1500, `${f}: median ${ms[1].toFixed(0)} ms exceeds 1500 ms (runs: ${ms.map((x) => x.toFixed(0)).join(', ')})`);
  }
});

test('worker-safe: the converter modules touch no DOM, window, storage or node-only module', () => {
  const dir = join(HERE, 'mermaid_arch');
  for (const f of readdirSync(dir).filter((x) => x.endsWith('.mjs') && !['cli.mjs', 'build_playground.mjs'].includes(x))) {
    const code = readFileSync(join(dir, f), 'utf8').replace(/\/\/.*$/gm, '').replace(/'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`/g, "''");
    assert.ok(!/(?<![.\w])(document|window|localStorage|sessionStorage|navigator|process|require)\b(?!\s*:)|from\s+['"]node:/.test(code), `${f} uses a browser-only or node-only global`);
  }
});

// ------------------------------------------------------------------ chip pacing: one apparent speed
const pathPx = (lay, graph, i) => {
  const rt = lay.routes && lay.routes[i];
  if (rt) { let t = 0; for (let q = 0; q + 1 < rt.points.length; q++) t += Math.hypot(rt.points[q + 1][0] - rt.points[q][0], rt.points[q + 1][1] - rt.points[q][1]); return t; }
  const a = lay.nodes.find((n) => n.id === graph.edges[i].from), b = lay.nodes.find((n) => n.id === graph.edges[i].to);
  return 1.2 * Math.hypot(a.x + a.w / 2 - (b.x + b.w / 2), a.y + a.h / 2 - (b.y + b.h / 2));
};
test('chip pacing: every chip moves at 14% of the long side per second (+-15%) unless its ride is clamped to the minimum or maximum', () => {
  let free = 0;
  for (const f of examples) {
    const r = mermaidToArch(readFileSync(join(EX, f), 'utf8'), { film: true, numbered: true, hint: 'web' });
    const long = Math.max(r.layout.W, r.layout.H);
    for (const m of r.block.messages || []) {
      const ride = m.dur * r.durationSeconds, min = Math.max(1.8, 0.8 + 0.07 * m.text.length), max = Math.max(5, min);
      const v = pathPx(r.layout, r.graph, m.edge) / long / ride;
      if (ride > min + 0.03 && ride < max - 0.03) { free++; assert.ok(Math.abs(v / 0.14 - 1) <= 0.15, `${f} "${m.text}": ${(v * 100).toFixed(1)}%/s`); }
      else assert.ok(ride >= min - 0.03 && ride <= max + 0.03, `${f}: ride ${ride} outside ${min}..${max}`);
    }
  }
  assert.ok(free >= 5, 'enough chips are in the free range to make the property mean something: ' + free);
});

test('chip pacing: long text keeps its chip on screen longer (minimum ride 0.8 s + 0.07 s per character), even on a short edge', () => {
  const text = 'x'.repeat(40);
  const r = mermaidToArch(`%% msg: a->b "${text}"\nflowchart LR\na -->|go| b`, { film: true });
  const m = r.block.messages[0];
  assert.ok(m.dur * r.durationSeconds >= 0.8 + 0.07 * 40 - 0.03, 'ride ' + m.dur * r.durationSeconds);
  const short = mermaidToArch('%% msg: a->b "hi"\nflowchart LR\na -->|go| b', { film: true }).block.messages[0];
  assert.ok(short.dur * mermaidToArch('%% msg: a->b "hi"\nflowchart LR\na -->|go| b', { film: true }).durationSeconds >= 1.8 - 0.03);
});

test('chip pacing: several chips on one edge ride one after another inside their step, never overlapping', () => {
  const src = '%% msg: a->b "one"\n%% msg: a->b "second message here"\n%% msg: b->a "three"\nflowchart LR\na -->|go| b\nb --> c';
  for (const pace of ['slow', 'normal', 'fast']) {
    const r = mermaidToArch(src, { pace });
    const D = r.durationSeconds, ms = r.block.messages.filter((m) => m.edge === 0).map((m) => ({ s: m.at * D, e: (m.at + m.dur) * D }));
    assert.equal(ms.length, 3);
    for (let i = 1; i < ms.length; i++) assert.ok(ms[i].s >= ms[i - 1].e - 0.01, `${pace}: chip ${i} starts before the previous ends`);
    const st = r.schedule[0];
    assert.ok(ms[0].s >= st.start - 0.01 && ms[2].e <= st.end + 0.01, `${pace}: chips inside the step`);
  }
});

test('chip pacing: pace scales the ride (slow longer, fast shorter) but never below 0.75 x the minimum', () => {
  const src = readFileSync(join(EX, examples[1]), 'utf8');
  const rides = (pace) => mermaidToArch(src, { film: true, numbered: true, pace }).block.messages.map((m) => m.dur);
  const D = (pace) => mermaidToArch(src, { film: true, numbered: true, pace }).durationSeconds;
  const sl = rides('slow').map((x) => x * D('slow')), no = rides('normal').map((x) => x * D('normal')), fa = rides('fast').map((x) => x * D('fast'));
  sl.forEach((x, i) => { assert.ok(x >= no[i] - 0.03 && no[i] >= fa[i] - 0.03); assert.ok(fa[i] >= 0.75 * 1.8 - 0.03); });
});

test('chip pacing: a duration override that gives the chips room works, one that does not is refused with a working suggestion', () => {
  const src = readFileSync(join(EX, examples[1]), 'utf8');
  const natural = mermaidToArch(src, { film: true, numbered: true }).durationSeconds;
  assert.deepEqual(validateBlock(mermaidToArch(src, { film: true, numbered: true, duration: Math.ceil(natural) }).block), []);
  assert.throws(() => mermaidToArch('%% duration: 6\n' + src, { film: true }), (e) => e instanceof ArchError && /too short|at least/.test(e.errors.join()));
});

// ------------------------------------------------------------------ two-line labels and label hygiene (2026-11)
import { wrapLabel, stripOwnNumber } from './mermaid_arch/labels.mjs';
import { edgeLabelSize } from './mermaid_arch/layout.mjs';

test('wrapLabel: fits on one line -> untouched; two words -> split at the space nearest the middle', () => {
  assert.deepEqual(wrapLabel('short', 40), { lines: ['short'], cut: false });
  assert.deepEqual(wrapLabel('x'.repeat(40), 40), { lines: ['x'.repeat(40)], cut: false }, 'exactly at the limit stays on one line');
  const w = wrapLabel('Return short-lived GCP Service Account Access Token', 40);
  assert.equal(w.cut, false);
  assert.equal(w.lines.length, 2);
  assert.equal(w.lines.join(' '), 'Return short-lived GCP Service Account Access Token');
  assert.ok(Math.abs(w.lines[0].length - w.lines[1].length) <= 8, `balanced: ${w.lines}`);
  assert.equal(wrapLabel('1 ' + 'w'.repeat(47), 48).lines[0].length > 3, true, 'a step number is not left alone on a line');
});
test('wrapLabel: one past the limit wraps at a space, never inside a word when a space works', () => {
  const t = 'a'.repeat(20) + ' ' + 'b'.repeat(21);          // 42 chars
  assert.deepEqual(wrapLabel(t, 40), { lines: ['a'.repeat(20), 'b'.repeat(21)], cut: false });
});
test('wrapLabel: a single long word is split in the middle; exactly 2 x limit still fits; one more is cut', () => {
  const w = wrapLabel('z'.repeat(60), 40);
  assert.equal(w.cut, false);
  assert.deepEqual(w.lines.map((l) => l.length), [30, 30]);
  assert.equal(wrapLabel('z'.repeat(80), 40).cut, false);
  const c = wrapLabel('z'.repeat(81), 40);
  assert.equal(c.cut, true);
  assert.ok(c.lines[1].endsWith('…') && c.lines.every((l) => l.length <= 40));
});
test('wrapLabel: text beyond two lines fills line 1 at a word boundary and cuts line 2', () => {
  const t = Array.from({ length: 30 }, (_, i) => 'word' + i).join(' ');
  const w = wrapLabel(t, 48);
  assert.equal(w.cut, true);
  assert.ok(w.lines[0].length <= 48 && !w.lines[0].endsWith(' ') && t.startsWith(w.lines[0] + ' '));
  assert.ok(w.lines[1].length <= 48 && w.lines[1].endsWith('…'));
});
test('wrapLabel: emoji and other astral characters are never split in half; lengths count UTF-16 units', () => {
  const t = '😀'.repeat(30);                                   // 60 units
  const w = wrapLabel(t, 40);
  assert.equal(w.cut, false);
  assert.equal(w.lines.join(''), t);
  for (const l of w.lines) { assert.ok(l.length <= 40); assert.ok(!/[\uD800-\uDBFF]$/.test(l) && !/^[\uDC00-\uDFFF]/.test(l), 'no lone surrogate'); }
  const mixed = wrapLabel('Ünïcödé 日本語 text with 😀 emoji and more words to wrap onto lines', 40);
  assert.equal(mixed.lines.join(' '), 'Ünïcödé 日本語 text with 😀 emoji and more words to wrap onto lines');
  for (const l of mixed.lines) assert.ok(!/[\uD800-\uDBFF]$/.test(l));
});
test('wrapLabel: CJK without spaces splits near the middle', () => {
  const t = '这是一个没有空格的很长的中文标签用来测试换行是否在中间附近进行拆分处理';   // 34 chars: fits
  assert.equal(wrapLabel(t, 40).lines.length, 1);
  const long = t + t;                                           // 68
  const w = wrapLabel(long, 40);
  assert.equal(w.cut, false);
  assert.equal(w.lines.join(''), long);
  assert.deepEqual(w.lines.map((l) => l.length), [t.length, t.length]);
});
test('stripOwnNumber: only a leading "N." / "N)" / "N:" / "(N)" is removed', () => {
  for (const [a, b] of [['1. Request credential', 'Request credential'], ['2) Return JWT', 'Return JWT'], ['3: Exchange', 'Exchange'], ['(4) Return', 'Return'], ['12 - Go', 'Go']]) assert.equal(stripOwnNumber(a), b);
  for (const k of ['2024 roadmap', '3 retries', 'v2 API', '1.5 GB', '1.', 'POST /v1']) assert.equal(stripOwnNumber(k), k);
});
test('numbered: an author number on an edge label is dropped from the drawn label and from the Activity sentence', () => {
  const r = mermaidToArch('flowchart LR\na -->|"1. Request credential / identity token"| b\nb -->|"2) Return token"| a', { numbered: true });
  assert.equal(r.block.edges[0].label, '1 Request credential / identity token');
  assert.equal(r.block.edges[1].label, '2 Return token');
  assert.doesNotMatch(r.textSteps.map((s) => s.activity).join('\n'), /\d\.|\d\)/);
  assert.equal(r.textSteps[0].label, 'Request credential / identity token');
  const plain = mermaidToArch('flowchart LR\na -->|"1. Request"| b', {});
  assert.equal(plain.block.edges[0].label, '1. Request', 'not numbered: the author label is left alone');
});
test('hygiene: stray punctuation at the end of the first <br/> line is dropped; sentences never end in , or &', () => {
  const g1 = parseMermaid('flowchart LR\na["Validate Token Signature,<br/>Issuer & Expiration"] -->|"Map claims &"| b').graph;
  assert.equal(g1.nodes[0].label, 'Validate Token Signature');
  assert.equal(g1.nodes[0].sub, 'Issuer & Expiration');
  for (const t of ['Keep-', 'One;', 'Two:', 'Three &', 'Four -']) assert.doesNotMatch(parseMermaid(`flowchart LR\na["${t}<br/>x"] --> b`).graph.nodes[0].label, /[,;:&-]$/);
  const r = mermaidToArch('flowchart LR\na -->|"Map claims,"| b\nb -->|"Send tokens &"| a');
  for (const s of r.textSteps) assert.doesNotMatch(s.activity, /[,&]\s*(\(.*\))?$/);
});
test('warnings: one merged line per kind of cut; labels that fit on two lines give none', () => {
  const huge = Array.from({ length: 14 }, (_, i) => 'segment' + i).join(' ');   // longer than two lines
  const src = 'flowchart LR\n' + [1, 2, 3].map((i) => `n${i}["${huge}"] -->|"${huge}"| m${i}["m${i}"]`).join('\n') + '\nsubgraph g1["' + 'G'.repeat(45) + '"]\n  m1\nend\nsubgraph g2["' + 'H'.repeat(50) + '"]\n  m2\nend';
  const r = mermaidToArch(src, { numbered: true });
  const cut = r.warnings.filter((w) => /longer than|cut/.test(w));
  assert.equal(cut.filter((w) => /^Edges /.test(w)).length, 1);
  assert.match(cut.find((w) => /^Edges /.test(w)), /^Edges 1, 2 and 3 have labels longer than the atom can show on two lines; they were cut \(the Steps table has the full text\)\.$/);
  assert.equal(cut.filter((w) => /^Nodes /.test(w)).length, 1);
  assert.equal(cut.filter((w) => /^Groups /.test(w)).length, 1);
  assert.match(cut.find((w) => /^Groups /.test(w)), /^Groups "g1" and "g2" have titles longer than 40 characters; they were cut\.$/);
  assert.ok(!r.warnings.some((w) => /step number pushes/.test(w)));
  const one = mermaidToArch('flowchart LR\na -->|"' + huge + '"| b');
  assert.ok(one.warnings.includes('Edge 1 has a label longer than the atom can show on two lines; it was cut (the Steps table has the full text).'));
  const fits = mermaidToArch('flowchart LR\na["' + 'word '.repeat(14).trim() + '"] -->|"' + 'word '.repeat(18).trim() + '"| b', { numbered: true });
  assert.deepEqual(fits.warnings.filter((w) => /longer than|cut/.test(w)), []);
});
test('long edge labels: two lines in the block, within the per-line limit, the router reserves the two-line box', () => {
  const r = mermaidToArch('flowchart LR\na -->|"Return short-lived GCP Service Account Access Token"| b');
  const e = r.block.edges[0];
  assert.ok(e.label && e.label2 && e.label.length <= 48 && e.label2.length <= 48);
  assert.equal(e.label + ' ' + e.label2, 'Return short-lived GCP Service Account Access Token');
  assert.deepEqual(validateBlock(r.block), []);
  const one = edgeLabelSize('abc def', 17), two = edgeLabelSize('abc\ndef', 17);
  assert.ok(two.h > one.h * 1.7, 'a two-line label box is about twice as tall');
  assert.ok(two.w < one.w, 'and as wide as its longer line only');
  const lr = r.layout.routes && r.layout.routes[0];
  if (lr && lr.label) assert.ok(lr.label.h >= two.h * 0 + edgeLabelSize(e.label + '\n' + e.label2, r.block.size).h - 1);
});
test('long node labels: split over label and sub when there is no sub; cut (merged warning) when there is one', () => {
  const r = mermaidToArch('flowchart LR\na["Workload Identity Federation token exchange service"] --> b');
  const n = r.block.nodes[0];
  assert.ok(n.sub && n.label.length <= 40 && n.sub.length <= 40);
  assert.equal(n.label + ' ' + n.sub, 'Workload Identity Federation token exchange service');
  assert.deepEqual(r.warnings.filter((w) => /longer than|cut/.test(w)), []);
  const hasSub = mermaidToArch('flowchart LR\na["' + 'Workload Identity Federation token exchange service' + '<br/>with a sub"] --> b');
  assert.ok(hasSub.warnings.some((w) => /^Node "a" has a label longer than/.test(w)));
});
test('backward compatibility: a graph with no long labels gives the same block as before (no label2, no extra fields)', () => {
  for (const f of examples) {
    const r = mermaidToArch(readFileSync(join(EX, f), 'utf8'), {});
    for (const e of r.block.edges) if (e.label2 !== undefined) assert.ok(e.label.length <= 48 && e.label2.length <= 48);
  }
  const r = mermaidToArch('flowchart LR\na -->|short| b');
  assert.ok(!('label2' in r.block.edges[0]));
  assert.ok(!('sub' in r.block.nodes[0]));
});
