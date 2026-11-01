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
  mermaidToArch, graphToArch, parseMermaid, validateGraph, validateBlock, ArchError, LIMITS, layoutGraph,
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
test('style, linkStyle, click are ignored', () => {
  const r = parseMermaid('flowchart LR\na-->b\nstyle a fill:#f00\nlinkStyle 0 stroke:#f00\nclick a href "http://x"');
  assert.equal(r.graph.nodes.length, 2);
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
  ['parallelogram', 'flowchart LR\na[/x/] --> b', /not supported/],
  ['double circle', 'flowchart LR\na(((x))) --> b', /double circles/],
  ['bad msg directive', '%% msg: nonsense\nflowchart LR\na-->b', /bad "%% msg:" directive/],
  ['msg to unknown node (did you mean)', '%% msg: wrker->db "x"\nflowchart LR\nworker --> db', /"wrker" is not a node \(did you mean "worker"\?\)/],
  ['edge to a subgraph', 'flowchart LR\nsubgraph s[S]\n a\nend\nb --> s', /subgraph, not a node/],
  ['self loop', 'flowchart LR\na --> a', /edge 1: "a" points at itself/],
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
test('error: more than 4 groups', () => {
  const lines = ['flowchart LR'];
  for (let i = 0; i < 5; i++) lines.push(`subgraph s${i}[S${i}]`, `n${i}`, 'end');
  lines.push('n0 --> n1');
  assert.match(err(lines.join('\n')), /5 groups; the atom draws at most 4/);
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
test('warnings: orphan node, long label, duplicate edge, long edge label', () => {
  const long = 'x'.repeat(45);
  const r = mermaidToArch(`flowchart LR\na[${long}] -->|${'y'.repeat(50)}| b\na --> b\na --> b\nlonely`, { direction: 'LR' });
  const w = r.warnings.join('\n');
  assert.match(w, /node "lonely" has no edges/);
  assert.match(w, /label is 45 characters; the atom shows at most 40/);
  assert.match(w, /duplicates edge 2/);
  assert.match(w, /label is 50 characters; the atom shows at most 48/);
  const n = r.block.nodes[0];
  assert.ok(n.label.length <= 40 && n.label.endsWith('…'), 'label cut with an ellipsis, not silently');
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
  b.edges.forEach((e, i) => assert.ok(e.at + 1e-9 >= Math.max(at.get(e.from), at.get(e.to)), `${label}: edge ${i} draws before its nodes`));
  (b.messages || []).forEach((m, i) => assert.ok(m.at + 1e-9 >= b.edges[m.edge].at + b.edges[m.edge].dur, `${label}: message ${i} leaves before its edge is drawn`));
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
  assert.equal(r.payload.blocks.length, 1);
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
  assert.ok(Math.min(...b.nodes.map((n) => n.at)) >= b.groups[0].at + b.groups[0].dur - 1e-9);
  assert.ok(Math.min(...b.edges.map((e) => e.at)) >= Math.min(...b.nodes.map((n) => n.at + n.dur)));
  assert.equal(b.messages[0].edge, 0);
});
test('compile: two messages on one edge are staggered, never overlapping', () => {
  const r = mermaidToArch('%% msg: a->b "one"\n%% msg: a->b "two"\nflowchart LR\na --> b');
  const [m1, m2] = r.block.messages;
  assert.ok(m2.at >= m1.at + m1.dur - 1e-9, JSON.stringify([m1, m2]));
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
    for n in b['nodes']:
        if n['label'].replace('&','&amp;') not in html and n['label'] not in html: bad.append(p + ': label missing ' + n['label'])
    if html.count('<path') < len(b['edges']): bad.append(p + ': edges missing')
print(json.dumps(bad))
`;
  const goldens = examples.map((f) => join(EX, f.replace(/\.mmd$/, '.golden.json')));
  const out = JSON.parse(execFileSync('python3', ['-W', 'ignore', '-c', code, ...goldens], { encoding: 'utf8', cwd: root }));
  assert.deepEqual(out, []);
});
