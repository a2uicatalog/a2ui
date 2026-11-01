// D2 subset -> canonical graph. Written from the public D2 syntax documentation; shares no code with D2.
// Supported: shapes (`a`, `a: Label`, `a: { label: X; shape: cylinder }`), containers (`g: Title { a; b }`,
// dotted paths `g.a`), connections (`a -> b`, `<-`, `<->`, `--`, chains, `: label`, attribute blocks),
// `style.stroke-dash` (dashed = async), `shape:` names, `kind:` / `class:` hints, `direction:`, and
// comment directives `# title: ...`, `# msg: a->b "text"`, `# numbered: on`, `# pace: slow`, `# duration: 40`,
// `# step: a->b 2`. Operators must be surrounded by spaces. See docs/mermaid_arch.md.
import { ArchError, resolveKind, didYouMean, PACES, LIMITS } from './graph.mjs';
import { makeIdMapper } from './mermaid.mjs';

export const D2_SHAPE_KIND = Object.freeze({
  cylinder: 'store', stored_data: 'store', queue: 'tool', person: 'user', circle: 'model', oval: 'model',
  hexagon: 'app', rectangle: 'server', square: 'server', page: 'server', document: 'server', step: 'server',
  cloud: 'surface', diamond: 'tool', package: 'server', parallelogram: 'server', callout: 'server',
});
const RESERVED = new Set(['shape', 'label', 'class', 'kind', 'style', 'direction', 'icon', 'tooltip', 'near', 'width', 'height', 'link', 'constraint', 'source-arrowhead', 'target-arrowhead', 'top', 'left', 'grid-rows', 'grid-columns', 'link']);
const UNSUPPORTED = new Set(['classes', 'vars', 'd2-config', 'layers', 'scenarios', 'steps']);
const DIRS = { right: 'LR', left: 'RL', down: 'TB', up: 'BT' };

export function parseD2(text, opts = {}) {
  const errors = [], warnings = [];
  if (typeof text !== 'string') throw new ArchError(['input must be D2 text (a string)']);
  const src = text.replace(/^﻿/, '').replace(/\r\n?/g, '\n');
  let i = 0, line = 1;
  const nodes = new Map();           // path -> {path, leaf, label, sub, shape, hints, parent, order, line, children:0}
  const edges = [];                  // {from(path), to(path), label, style, both, line}
  const msgs = [], stepDirs = [];
  let title, numbered, pace, duration, relationColumn, relationName, direction = 'LR', openWarned = false;
  const relDirs = [];
  const fail = (m, ln = line) => errors.push(`line ${ln}: ${m}`);
  const warn = (m, ln = line) => warnings.push(`line ${ln}: ${m}`);

  const peek = () => src[i];
  const adv = () => { const c = src[i++]; if (c === '\n') line++; return c; };
  function skipSpace(nl) {
    for (;;) {
      const c = peek();
      if (c === ' ' || c === '\t') adv();
      else if (nl && (c === '\n' || c === ';')) adv();
      else if (c === '#') {
        const start = i; let e = src.indexOf('\n', i); if (e < 0) e = src.length;
        directive(src.slice(start + 1, e).trim(), line);
        while (i < e) i++;
      } else break;
    }
  }
  function directive(body, ln) {
    const m = /^(title|msg|numbered|pace|duration|step|relation-column|relation-name|rel)\s*:\s*(.*)$/i.exec(body);
    if (!m) return;
    const k = m[1].toLowerCase(), v = m[2].trim();
    if (k === 'title') { if (v) title = v; }
    else if (k === 'msg') {
      const mm = /^(\S+?)\s*->\s*(\S+?)\s+"([^"]*)"(?:\s+(back))?\s*$/.exec(v);
      if (!mm) fail('bad "# msg:" directive; write it as  # msg: fromId->toId "payload text"', ln); else msgs.push({ line: ln, from: mm[1], to: mm[2], text: mm[3], back: !!mm[4] });
    } else if (k === 'numbered') {
      const b = v.toLowerCase(); if (['on', 'true', 'yes'].includes(b)) numbered = true; else if (['off', 'false', 'no'].includes(b)) numbered = false; else fail('"# numbered:" must be on or off', ln);
    } else if (k === 'pace') { if (v.toLowerCase() in PACES) pace = v.toLowerCase(); else fail(`"# pace:" must be one of ${Object.keys(PACES).join(', ')}`, ln); }
    else if (k === 'duration') { const d = Number(v.replace(/\s*s$/i, '')); if (Number.isFinite(d) && d >= 2 && d <= 120) duration = d; else fail('"# duration:" must be a number of seconds from 2 to 120', ln); }
    else if (k === 'relation-column') { const b = v.toLowerCase(); if (['on', 'true', 'yes'].includes(b)) relationColumn = true; else if (['off', 'false', 'no'].includes(b)) relationColumn = false; else fail('"# relation-column:" must be on or off', ln); }
    else if (k === 'relation-name') { if (v && v.length <= LIMITS.relation) relationName = v; else fail(`"# relation-name:" must be 1 to ${LIMITS.relation} characters`, ln); }
    else if (k === 'rel') {
      const mm = /^(\S+?)\s*->\s*(\S+?)\s+(.+?)\s*$/.exec(v);
      if (!mm) fail('bad "# rel:" directive; write it as  # rel: fromId->toId calls', ln); else if (mm[3].length > LIMITS.relation) fail(`"# rel:" text is ${mm[3].length} characters; the most is ${LIMITS.relation}`, ln); else relDirs.push({ line: ln, from: mm[1], to: mm[2], text: mm[3] });
    }
    else if (k === 'step') {
      const mm = /^(\S+?)\s*->\s*(\S+?)\s+(\d+)\s*$/.exec(v);
      if (!mm) fail('bad "# step:" directive; write it as  # step: fromId->toId 3', ln); else stepDirs.push({ line: ln, from: mm[1], to: mm[2], step: +mm[3] });
    }
  }
  // a reference: dotted path of segments, quoted or bare
  function readRef() {
    const segs = []; let cur = '', quoted = false;
    for (;;) {
      const c = peek();
      if (c === undefined) break;
      if (c === '"') {
        adv(); let t = '';
        while (peek() !== undefined && peek() !== '"') { if (peek() === '\\') adv(); t += adv(); }
        if (peek() !== '"') { fail('a quote is never closed; add a closing "'); break; }
        adv(); cur += t; quoted = true; continue;
      }
      if (c === '.') { adv(); segs.push(cur); cur = ''; continue; }
      if (/[\s:;{}#]/.test(c)) break;
      cur += adv();
    }
    segs.push(cur);
    return segs.filter((s) => s !== '' || quoted);
  }
  function readValue() {       // after ':'
    skipSpace(false);
    let t = '';
    if (peek() === '"') {
      adv();
      while (peek() !== undefined && peek() !== '"') { if (peek() === '\\') { adv(); const n = adv(); t += n === 'n' ? '\n' : n; } else t += adv(); }
      if (peek() !== '"') fail('a quote is never closed; add a closing "'); else adv();
      return t;
    }
    if (peek() === '|') { fail('markdown/code blocks ("|md ... |") are not supported; use a plain label'); while (peek() !== undefined && peek() !== '\n') adv(); return ''; }
    while (peek() !== undefined && !/[\n;{}]/.test(peek()) && !(peek() === '#' && /\s/.test(src[i - 1] || ' '))) t += adv();
    return t.trim();
  }
  const OPS = ['<->', '->', '<-', '--'];
  function readOp() {
    skipSpace(false);
    for (const op of OPS) if (src.startsWith(op, i) && /[\s]/.test(src[i + op.length] || ' ')) { i += op.length; return op; }
    return null;
  }
  const keyOf = (scope, segs) => [...scope.path, ...segs].join('.');
  function ensureNode(path, ln) {
    let n = nodes.get(path);
    if (!n) {
      const segs = path.split('.');
      n = { path, leaf: segs[segs.length - 1], label: undefined, sub: undefined, shape: undefined, hints: [], order: nodes.size, line: ln, children: 0, parent: segs.length > 1 ? segs.slice(0, -1).join('.') : undefined };
      nodes.set(path, n);
      if (n.parent) { const p = ensureNode(n.parent, ln); p.children++; }
    }
    return n;
  }
  function setLabel(n, v) {
    const parts = v.split('\n').map((x) => x.trim()).filter(Boolean);
    n.label = parts[0] || n.leaf; n.sub = parts.length > 1 ? parts.slice(1).join(' ') : undefined;
  }
  function parseBlock(scope, top) {
    for (;;) {
      skipSpace(true);
      const c = peek();
      if (c === undefined) { if (!top) fail('a "{" is never closed; add a closing "}"'); return; }
      if (c === '}') { if (top) { fail('"}" without a matching "{"'); adv(); continue; } adv(); return; }
      const ln = line;
      const segs = readRef();
      if (!segs.length) { fail(`cannot read "${src.slice(i, i + 20).split('\n')[0]}"; expected a shape name or a connection`, ln); while (peek() !== undefined && peek() !== '\n') adv(); continue; }
      const op = readOp();
      if (op) { connection(scope, segs, op, ln); continue; }
      skipSpace(false);
      let val;
      if (peek() === ':') { adv(); val = readValue(); }
      skipSpace(false);
      const first = segs[0].toLowerCase();
      if (UNSUPPORTED.has(first)) { fail(`"${segs[0]}" is not supported in this D2 subset`, ln); skipBlock(); continue; }
      if (scope.stylePrefix) { attribute(scope, segs, val, ln); continue; }
      if (RESERVED.has(first) && (scope.type !== 'root' || ['direction', 'title'].includes(first) || segs.length > 1 || scope.owner)) {
        attribute(scope, segs, val, ln);
        if (peek() === '{') { adv(); parseBlock({ ...scope, stylePrefix: first === 'style' }, false); }
        continue;
      }
      if (scope.type === 'root' && first === 'direction') { attribute(scope, segs, val, ln); continue; }
      const path = keyOf(scope, segs);
      const n = ensureNode(path, ln);
      if (val !== undefined && val !== '') setLabel(n, val);
      if (peek() === '{') { adv(); parseBlock({ type: 'node', path: path.split('.'), owner: n }, false); }
    }
  }
  function skipBlock() { skipSpace(false); if (peek() !== '{') return; let d = 0; do { const c = adv(); if (c === '{') d++; else if (c === '}') d--; } while (d > 0 && peek() !== undefined); }
  function attribute(scope, segs, val, ln) {
    const key = segs.join('.').toLowerCase();
    const owner = scope.owner;
    const isEdge = scope.type === 'edge';
    if (key === 'direction') { const d = DIRS[(val || '').toLowerCase()]; if (d) direction = d; else fail('direction must be right, left, down or up', ln); return; }
    if (!owner) return;
    if (key === 'style' || key === 'style.stroke-dash' || scope.stylePrefix) {
      const k = scope.stylePrefix ? key : key;
      if (k === 'style.stroke-dash' || (scope.stylePrefix && key === 'stroke-dash')) { if (isEdge && val !== '0') owner.style = 'async'; }
      return;
    }
    if (key.startsWith('style.')) return;
    if (isEdge) { if (key === 'label' && val !== undefined) owner.label = val; return; }
    if (key === 'label') { if (val !== undefined) setLabel(owner, val); }
    else if (key === 'shape') { if (val) owner.shape = val.toLowerCase(); }
    else if (key === 'class' || key === 'kind') { if (val) owner.hints.push(val.trim().toLowerCase()); }
  }
  function connection(scope, firstSegs, op0, ln) {
    const refs = [firstSegs], ops = [op0];
    for (;;) {
      skipSpace(false);
      const segs = readRef();
      if (!segs.length) { fail('a connection needs a shape on both sides of the arrow', ln); return; }
      refs.push(segs);
      const op = readOp();
      if (!op) break;
      ops.push(op);
    }
    skipSpace(false);
    let label;
    if (peek() === ':') { adv(); label = readValue(); }
    skipSpace(false);
    const made = [];
    for (let k = 0; k < ops.length; k++) {
      let a = keyOf(scope, refs[k]), b = keyOf(scope, refs[k + 1]);
      let op = ops[k];
      ensureNode(a, ln); ensureNode(b, ln);
      if (op === '<-') { [a, b] = [b, a]; op = '->'; }
      if (op === '--' && !openWarned) { openWarned = true; warn('"--" lines have no arrowhead in D2, but motion_arch always draws one; the edge is drawn as an arrow.', ln); }
      const e = { from: a, to: b, label: label || undefined, style: 'sync', both: op === '<->' || undefined, line: ln };
      edges.push(e); made.push(e);
    }
    if (peek() === '{') {
      adv();
      const sub = { type: 'edge', path: scope.path, owner: { set style(v) { made.forEach((e) => { e.style = v; }); }, get style() { return made[0].style; }, set label(v) { made.forEach((e) => { e.label = v || undefined; }); }, get label() { return made[0].label; } } };
      parseBlock(sub, false);
    }
  }

  parseBlock({ type: 'root', path: [] }, true);
  if (!nodes.size && !errors.length) fail('no shapes found; write for example  a: Alpha  and  a -> b', 1);
  if (errors.length) throw new ArchError(errors.slice(0, 20), warnings);

  // ---- canonical graph
  const leafCount = new Map();
  for (const n of nodes.values()) if (!n.children) leafCount.set(n.leaf, (leafCount.get(n.leaf) || 0) + 1);
  const origOf = (n) => (leafCount.get(n.leaf) > 1 ? n.path : n.leaf);
  const mapNode = makeIdMapper(), mapGroup = makeIdMapper();
  const outer = (n) => { let p = n; while (p.parent) p = nodes.get(p.parent); return p; };
  const groupNodes = [...nodes.values()].filter((n) => n.children && !n.parent);
  groupNodes.forEach((g) => {
    const stack = [...nodes.values()].filter((x) => x.parent && x.parent !== undefined && outer(x) === g && x.children);
    stack.forEach((sg) => warn(`container "${sg.leaf}" is inside "${g.leaf}"; nested groups are flattened, its shapes are drawn in the outer group "${g.leaf}".`, sg.line));
  });
  const groups = groupNodes.map((g) => ({ id: mapGroup(g.leaf), label: g.label || g.leaf, path: g.path }));
  const leaves = [...nodes.values()].filter((n) => !n.children).sort((a, b) => a.order - b.order);
  const byPath = new Map(leaves.map((n) => [n.path, n]));
  const nOut = leaves.map((n) => {
    let kind;
    for (const h of n.hints) { const k = resolveKind(h); if (k) kind = k; else warn(`"${h}" is not a known kind; ignored.`, n.line); }
    if (!kind) {
      if (n.shape && !(n.shape in D2_SHAPE_KIND)) warn(`shape "${n.shape}" is not known; treated as a plain box.`, n.line);
      kind = D2_SHAPE_KIND[n.shape || 'rectangle'] || 'server';
    }
    const o = { id: mapNode(origOf(n)), label: n.label !== undefined ? n.label : n.leaf, kind };
    if (n.sub) o.sub = n.sub;
    if (n.parent) o.group = groups.find((g) => g.path === outer(n).path).id;
    return o;
  });
  const idOf = (path) => {
    const n = byPath.get(path);
    return n ? mapNode(origOf(n)) : undefined;
  };
  const eOut = [];
  for (const e of edges) {
    const f = idOf(e.from), t = idOf(e.to);
    if (!f || !t) { errors.push(`line ${e.line}: "${!f ? e.from : e.to}" is a container, not a shape. Edges to a whole container are not supported; connect to a shape inside it.`); continue; }
    const o = { from: f, to: t, style: e.style };
    if (e.label) o.label = e.label;
    if (e.both) o.both = true;
    eOut.push(o);
  }
  const findId = (ref, ln) => {
    const cand = [...byPath.values()].filter((n) => n.path === ref || n.leaf === ref || origOf(n) === ref || n.leaf.toLowerCase() === ref.toLowerCase());
    if (cand.length) return mapNode(origOf(cand[0]));
    const names = [...byPath.values()].map((n) => n.leaf);
    errors.push(`line ${ln}: "${ref}" is not a shape` + (didYouMean(ref, names) ? ` (did you mean "${didYouMean(ref, names)}"?)` : ''));
    return undefined;
  };
  const mOut = [];
  for (const d of msgs) { const f = findId(d.from, d.line), t = findId(d.to, d.line); if (f && t) mOut.push({ from: f, to: t, text: d.text, ...(d.back ? { back: true } : {}) }); }
  const taken = new Set();
  for (const d of stepDirs) {
    const f = findId(d.from, d.line), t = findId(d.to, d.line);
    if (!f || !t) continue;
    const idx = eOut.findIndex((e, k) => e.from === f && e.to === t && !taken.has(k));
    if (idx < 0) { errors.push(`line ${d.line}: step directive: there is no (further) edge from "${d.from}" to "${d.to}"`); continue; }
    taken.add(idx); eOut[idx].step = d.step;
  }
  const relTaken = new Set();
  for (const d of relDirs) {
    const f = findId(d.from, d.line), t = findId(d.to, d.line);
    if (!f || !t) continue;
    const idx = eOut.findIndex((e, k) => e.from === f && e.to === t && !relTaken.has(k));
    if (idx < 0) { errors.push(`line ${d.line}: rel directive: there is no (further) edge from "${d.from}" to "${d.to}"`); continue; }
    relTaken.add(idx); eOut[idx].relation = d.text;
  }
  if (errors.length) throw new ArchError(errors.slice(0, 20), warnings);
  const graph = { direction: opts.direction || direction, groups: groups.map(({ id, label }) => ({ id, label })), nodes: nOut, edges: eOut, messages: mOut };
  if (relationColumn !== undefined) graph.relationColumn = relationColumn;
  if (relationName) graph.relationName = relationName;
  if (numbered !== undefined) graph.numbered = numbered;
  if (pace) graph.pace = pace;
  if (duration !== undefined) graph.duration = duration;
  const ttl = opts.title || title;
  if (ttl) graph.title = ttl;
  return { graph, warnings };
}
