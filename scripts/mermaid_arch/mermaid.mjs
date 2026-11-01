// Mermaid flowchart subset -> canonical graph. Pure ES module, no dependencies.
// See docs/mermaid_arch.md for the supported syntax. Unsupported input gives a
// plain error naming the line; the parser never throws anything but ArchError.
import { ArchError, KINDS, resolveKind, didYouMean, LIMITS, PACES } from './graph.mjs';

const OTHER_DIAGRAMS = {
  sequencediagram: 'Draw each participant as a node and each message as an edge in a flowchart.',
  classdiagram: 'Draw each class as a node and each relation as an edge in a flowchart.',
  statediagram: 'Draw each state as a node and each transition as an edge in a flowchart.',
  'statediagram-v2': 'Draw each state as a node and each transition as an edge in a flowchart.',
  erdiagram: 'Draw each entity as a node and each relation as an edge in a flowchart.',
  gantt: 'Gantt charts are timelines, not architecture; use a flowchart of the components instead.',
  pie: 'Pie charts are not architecture diagrams.',
  journey: 'User journeys are not supported; use a flowchart.',
  gitgraph: 'Git graphs are not supported; use a flowchart.',
  mindmap: 'Mind maps are not supported; use a flowchart.',
  timeline: 'Timelines are not supported; use a flowchart.',
  c4context: 'C4 diagrams are not supported; use a flowchart with subgraphs for the boundaries.',
  c4container: 'C4 diagrams are not supported; use a flowchart with subgraphs for the boundaries.',
  c4component: 'C4 diagrams are not supported; use a flowchart with subgraphs for the boundaries.',
  'architecture-beta': 'architecture-beta is not supported; use a flowchart with subgraphs for the groups.',
  'block-beta': 'block-beta is not supported; use a flowchart.',
  'sankey-beta': 'Sankey diagrams are not supported; use a flowchart.',
  'xychart-beta': 'Charts are not supported; use a flowchart.',
  quadrantchart: 'Quadrant charts are not supported; use a flowchart.',
  requirementdiagram: 'Requirement diagrams are not supported; use a flowchart.',
  kanban: 'Kanban boards are not supported; use a flowchart.',
  packet: 'Packet diagrams are not supported; use a flowchart.',
};

// shape delimiters, longest opener first
// A fourth item names a shape the atom cannot draw; it is degraded to the shape in position three
// (a rectangle or a circle) with a warning. A close may be a list (trapezoids close with either slash).
const SHAPES = [
  ['(((', ')))', 'circle', 'double circle'], ['[/', ['/]', '\\]'], 'rect', null], ['[\\', ['\\]', '/]'], 'rect', null],
  ['>', ']', 'rect', 'asymmetric'],
  ['((', '))', 'circle'], ['([', '])', 'stadium'], ['[(', ')]', 'cylinder'], ['[[', ']]', 'subroutine'],
  ['{{', '}}', 'hexagon'], ['(', ')', 'round'], ['[', ']', 'rect'], ['{', '}', 'diamond'],
];
// default kind per shape (documented in docs/mermaid_arch.md)
export const SHAPE_KIND = Object.freeze({
  cylinder: 'store', subroutine: 'tool', stadium: 'device', circle: 'model', hexagon: 'app',
  round: 'app', diamond: 'tool', rect: 'server', plain: 'server',
});
// Mermaid 11 "@{ shape: x }" names -> our shape classes
const AT_SHAPES = {
  cyl: 'cylinder', cylinder: 'cylinder', 'lin-cyl': 'cylinder', 'h-cyl': 'cylinder', 'das': 'cylinder', database: 'cylinder', db: 'cylinder',
  circle: 'circle', circ: 'circle', 'sm-circ': 'circle', 'dbl-circ': 'circle',
  stadium: 'stadium', terminal: 'stadium', pill: 'stadium',
  subproc: 'subroutine', subroutine: 'subroutine', 'fr-rect': 'subroutine',
  hex: 'hexagon', hexagon: 'hexagon', prepare: 'hexagon',
  rounded: 'round', event: 'round',
  rect: 'rect', rectangle: 'rect', proc: 'rect', process: 'rect', square: 'rect',
  diamond: 'diamond', decision: 'diamond', question: 'diamond',
};

const ID_CHAR = /^[\p{L}\p{N}_]$/u;   // Mermaid accepts any letter or digit in an id, not just ASCII
const SLASH_NAME = { '//': 'parallelogram', '\\\\': 'parallelogram (alt)', '/\\': 'trapezoid', '\\/': 'trapezoid (alt)' };

// **bold**, __bold__, *italic*, _italic_ inside a Mermaid markdown string (the text between backquotes)
function stripMarkdown(t) {
  return t.replace(/\*\*(.+?)\*\*/g, '$1').replace(/__(.+?)__/g, '$1')
    .replace(/\*(.+?)\*/g, '$1').replace(/(^|[^\p{L}\p{N}_])_(.+?)_(?![\p{L}\p{N}_])/gu, '$1$2');
}

function stripQuotes(s) {
  let t = s.trim();
  if (t.length >= 2 && t[0] === '"' && t[t.length - 1] === '"') t = t.slice(1, -1).trim();
  if (t.length >= 2 && t[0] === '`' && t[t.length - 1] === '`') t = stripMarkdown(t.slice(1, -1));
  return t;
}

const NAMED = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };
// Named (#amp; or &amp;) and numeric (#35; &#35; &#x23;) entity codes, decoded in one pass so "&amp;lt;" stays "&lt;".
function decodeEntities(s) {
  return s.replace(/(?:#|&)(amp|lt|gt|quot|apos|nbsp);|(?:#|&#)(\d{1,7});|&#x([0-9a-f]{1,6});/gi, (m, name, dec, hex) => {
    if (name) return NAMED[name.toLowerCase()];
    const cp = dec !== undefined ? +dec : parseInt(hex, 16);
    return cp >= 32 && cp <= 0x10ffff && !(cp >= 0xd800 && cp <= 0xdfff) && !(cp >= 0x7f && cp < 0xa0) ? String.fromCodePoint(cp) : '';
  });
}

// The source line rides on each node and edge as a hidden (non-enumerable) property, so graph errors can say
// "line N" while the canonical graph, its JSON and the D2 parity stay unchanged.
function withLine(o, line) { Object.defineProperty(o, 'line', { value: line, enumerable: false }); return o; }

// Set when stripping tags changed a label; parseMermaid reads it once to warn (parsing is synchronous).
let tagsStripped = false;
const TAG = /<\/?[A-Za-z!][^>]*>/g;
function stripTags(t) {
  return t.replace(TAG, () => { tagsStripped = true; return ''; });
}
// one line of label text: drop tags, decode entities, drop any tag the decoding made, tidy spaces
function tidy(p) {
  return stripTags(decodeEntities(stripTags(p))).replace(/\s+/g, ' ').trim();
}

// "Agent runtime<br/>on ADK" -> {label:'Agent runtime', sub:'on ADK'}
function splitLabel(raw) {
  const parts = stripQuotes(raw).split(/<br\s*\/?>/i).map(tidy).filter(Boolean);
  if (!parts.length) return { label: '' };
  return parts.length === 1 ? { label: parts[0] } : { label: parts[0], sub: parts.slice(1).join(' ') };
}

function cleanText(raw) {
  return stripQuotes(raw).split(/<br\s*\/?>/i).map(tidy).filter((x) => x !== '').join(' ');
}

// split a line at ';' outside quotes
function splitStatements(line) {
  const out = []; let cur = ''; let q = false;
  for (const ch of line) {
    if (ch === '"') q = !q;
    if (ch === ';' && !q) { out.push(cur); cur = ''; } else cur += ch;
  }
  out.push(cur);
  return out.map((s) => s.trim()).filter(Boolean);
}

// remove a trailing "%% comment" that sits outside quotes
function stripTrailingComment(s) {
  let q = false;
  for (let i = 0; i < s.length - 1; i++) {
    if (s[i] === '"') q = !q;
    if (!q && s[i] === '%' && s[i + 1] === '%' && (i === 0 || /\s/.test(s[i - 1]))) return s.slice(0, i).trimEnd();
  }
  return s;
}

function slug(s) {
  return s.toLowerCase().replace(/[^a-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '') || 'x';
}

// deterministic, collision-safe map to the atom id rule ^[a-z][a-z0-9_-]{0,31}$
export function makeIdMapper() {
  const used = new Set();
  const byOrig = new Map();
  return (orig) => {
    if (byOrig.has(orig)) return byOrig.get(orig);
    let base = orig.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[^a-z0-9_-]/g, '_');
    if (!/^[a-z]/.test(base)) base = 'n' + base;
    base = base.slice(0, 32);
    let id = base, k = 2;
    while (used.has(id)) { const suf = '_' + k++; id = base.slice(0, 32 - suf.length) + suf; }
    used.add(id); byOrig.set(orig, id);
    return id;
  };
}

export const MAX_INPUT_CHARS = 20000, MAX_LINE_CHARS = 500;   // keeps backtracking in matchLink and the & cross product bounded
export function parseMermaid(text, opts = {}) {
  tagsStripped = false;
  let styleLine = 0, clickLine = 0;
  const errors = [], warnings = [];
  const fail = (line, msg) => errors.push(`line ${line}: ${msg}`);
  const warn = (line, msg) => warnings.push(`line ${line}: ${msg}`);
  if (typeof text !== 'string') throw new ArchError(['input must be Mermaid text (a string)']);
  if (text.length > MAX_INPUT_CHARS) throw new ArchError([`input is ${text.length} characters; the most this converter reads is ${MAX_INPUT_CHARS}. A diagram this atom can show is far smaller.`]);
  const lines = text.replace(/^﻿/, '').replace(/\r\n?/g, '\n').split('\n');
  const longLine = lines.findIndex((l) => l.length > MAX_LINE_CHARS);
  if (longLine >= 0) throw new ArchError([`line ${longLine + 1}: ${lines[longLine].length} characters; the most one line may hold is ${MAX_LINE_CHARS}. Split it over several lines.`]);

  const nodes = new Map();          // orig -> {orig,label,sub,shape,hints:[],group,order,line}
  const edges = [];                 // {from,to,label,style,both,line}
  const groupsByKey = new Map();    // key -> {key,label,order}
  const groupStack = [];            // [{key,label,nested}]
  const classStmts = [];            // {line, ids, cls}
  const msgDirectives = [];         // {line, from, to, text, back}
  const stepDirectives = [];         // {line, from, to, step}
  let title, numbered, pace, duration, relationColumn, relationName, direction = 'TB', headerSeen = false, openLinkWarned = false;
  const relDirectives = [];         // {line, from, to, text}

  function touchNode(orig, line) {
    let n = nodes.get(orig);
    if (!n) { n = { orig, label: undefined, sub: undefined, shape: undefined, hints: [], group: undefined, order: nodes.size, line }; nodes.set(orig, n); }
    if (groupStack.length) {
      const outer = groupStack[0].key;
      if (n.group === undefined) n.group = outer;
      else if (n.group !== outer) warn(line, `node "${orig}" is listed in more than one subgraph; keeping it in "${groupsByKey.get(n.group).label}".`);
    }
    return n;
  }

  // ---- node reference: id [shape text] [@{..}] [:::class]
  function parseNodeRef(s, i0, line) {
    let i = i0;
    while (s[i] === ' ' || s[i] === '\t') i++;
    const start = i;
    while (i < s.length) {
      const cp = String.fromCodePoint(s.codePointAt(i));
      if (ID_CHAR.test(cp)) i += cp.length;
      else if (cp === '-' && i + 1 < s.length && ID_CHAR.test(String.fromCodePoint(s.codePointAt(i + 1))) && i > start) i++;
      else break;
    }
    if (i === start) {
      fail(line, `expected a node id at "${s.slice(i0).trim().slice(0, 20)}"; node ids are letters, digits and underscores (write A[Label] or A --> B)`);
      return null;
    }
    const orig = s.slice(start, i);
    const ref = { orig, hints: [] };
    for (const [open, closes, shape, degraded] of SHAPES) {
      if (!s.startsWith(open, i)) continue;
      const closeList = Array.isArray(closes) ? closes : [closes];
      let close = closeList[0];
      let j = i + open.length;
      while (s[j] === ' ') j++;
      let txt;
      if (s[j] === '"') {
        const e = s.indexOf('"', j + 1);
        if (e < 0) { fail(line, `node "${orig}": the quote opened here is never closed; add a closing "`); return null; }
        txt = s.slice(j + 1, e);
        let k = e + 1;
        while (s[k] === ' ') k++;
        close = closeList.find((c) => s.startsWith(c, k)) ?? close;
        if (!s.startsWith(close, k)) { fail(line, `node "${orig}": expected "${close}" after the quoted text`); return null; }
        i = k + close.length;
      } else {
        let e = -1;
        for (const c of closeList) { const x = s.indexOf(c, j); if (x >= 0 && (e < 0 || x < e)) { e = x; close = c; } }
        if (e < 0 && open[0] === '[' && open.length === 2 && '/\\'.includes(open[1])) continue;   // "[/path]" is a plain box
        if (e < 0) { fail(line, `node "${orig}": missing closing "${close}"; if the text contains brackets or parentheses, wrap it in quotes: ${orig}["text (like this)"]`); return null; }
        txt = s.slice(j, e);
        i = e + close.length;
      }
      ref.shape = shape;
      const name = degraded || (open.length === 2 && open[0] === '[' && '/\\'.includes(open[1]) ? SLASH_NAME[open[1] + close[0]] : null);
      if (name) warn(line, `Node "${orig}" uses a shape the atom cannot draw (${name}); drawn as a ${shape === 'circle' ? 'circle' : 'rectangle'}.`);
      Object.assign(ref, splitLabel(txt));
      break;
    }
    // Mermaid 11: A@{ shape: cyl, label: "x" }
    if (s.startsWith('@{', i)) {
      const e = s.indexOf('}', i);
      if (e < 0) { fail(line, `node "${orig}": "@{" is never closed with "}"`); return null; }
      const body = s.slice(i + 2, e);
      const sm = body.match(/shape\s*:\s*([\w-]+)/);
      const lm = body.match(/label\s*:\s*("([^"]*)"|[^,]+)/);
      if (sm) {
        const shk = sm[1].toLowerCase(), sh = Object.hasOwn(AT_SHAPES, shk) ? AT_SHAPES[shk] : undefined;
        if (sh) ref.shape = sh;
        else { ref.shape = 'rect'; warn(line, `node "${orig}": shape "${sm[1]}" is not known; treated as a plain box.`); }
      }
      if (lm) Object.assign(ref, splitLabel(lm[2] !== undefined ? lm[2] : lm[1]));
      i = e + 1;
    }
    // :::class (also "A:::user" right after the id)
    while (s.startsWith(':::', i)) {
      const m = /^:::([A-Za-z0-9_-]+)/.exec(s.slice(i));
      if (!m) { fail(line, `node "${orig}": ":::" must be followed by a class name, for example ${orig}:::server`); return null; }
      ref.hints.push(m[1]); i += m[0].length;
    }
    ref.end = i;
    return ref;
  }

  function applyRef(ref, line) {
    const n = touchNode(ref.orig, line);
    if (ref.label !== undefined && ref.label !== '') { n.label = ref.label; n.sub = ref.sub; }
    if (ref.shape) n.shape = ref.shape;
    n.hints.push(...ref.hints);
    return n;
  }

  // ---- links
  function matchLink(rest) {
    let m;
    // text inside the line: -- text -->, -. text .->, == text ==>
    if ((m = /^(<?)--\s+(.+?)\s+(-{2,}>|-{3,})(?=\s|$|[A-Za-z0-9_])/.exec(rest)) && !/^(<?)--\s*>/.test(rest)) {
      return { len: m[0].length, both: !!m[1] && m[3].endsWith('>'), style: 'sync', open: !m[3].endsWith('>'), label: m[2] };
    }
    if ((m = /^(<?)-\.\s+(.+?)\s+(\.-+>?)(?=\s|$|[A-Za-z0-9_])/.exec(rest))) {
      return { len: m[0].length, both: !!m[1] && m[3].endsWith('>'), style: 'async', open: !m[3].endsWith('>'), label: m[2] };
    }
    if ((m = /^(<?)==\s+(.+?)\s+(={2,}>|={3,})(?=\s|$|[A-Za-z0-9_])/.exec(rest)) ) {
      return { len: m[0].length, both: !!m[1] && m[3].endsWith('>'), style: 'sync', open: !m[3].endsWith('>'), label: m[2] };
    }
    if ((m = /^(<?)(-\.+-+>?)/.exec(rest))) return { len: m[0].length, both: !!m[1] && m[2].endsWith('>'), style: 'async', open: !m[2].endsWith('>') };
    if ((m = /^(<?)(-{2,}>|-{3,})/.exec(rest))) return { len: m[0].length, both: !!m[1] && m[2].endsWith('>'), style: 'sync', open: !m[2].endsWith('>') };
    if ((m = /^(<?)(={2,}>|={3,})/.exec(rest))) return { len: m[0].length, both: !!m[1] && m[2].endsWith('>'), style: 'sync', open: !m[2].endsWith('>') };
    return null;
  }

  function parseChain(s, line) {
    let i = 0;
    const readGroup = () => {
      const refs = [];
      for (;;) {
        const ref = parseNodeRef(s, i, line);
        if (!ref) return null;
        refs.push(ref); i = ref.end;
        while (s[i] === ' ' || s[i] === '\t') i++;
        if (s[i] === '&' ) { i++; continue; }
        break;
      }
      return refs;
    };
    let prev = readGroup();
    if (!prev) return;
    prev.forEach((r) => applyRef(r, line));
    for (;;) {
      while (s[i] === ' ' || s[i] === '\t') i++;
      if (i >= s.length) return;
      const rest = s.slice(i);
      if (/^[A-Za-z0-9_-]+@(-|=|<)/.test(rest)) { fail(line, 'edge ids ("e1@-->") are not supported; remove the "e1@" part'); return; }
      if (/^~{3,}/.test(rest)) { fail(line, 'invisible links (~~~) are not supported; remove the line or use a normal arrow.'); return; }
      if (/^(<?)(-{2,}|={2,}|-\.+-*)[xo](\s|$)/.test(rest) || /^[xo](-{2,}|={2,}|-\.+-*)[xo]?(\s|$)/.test(rest)) { fail(line, 'arrows with a cross or circle end ("--x", "--o", "x--x", "o--o") are not supported; use --> or <-->.'); return; }
      const lk = matchLink(rest);
      if (!lk) { fail(line, `cannot read "${rest.slice(0, 24)}"; expected an arrow such as -->, -.->, ==> or --- between nodes`); return; }
      i += lk.len;
      let label = lk.label;
      const pm = /^\s*\|([^|]*)\|/.exec(s.slice(i));
      if (pm) { if (label !== undefined) { fail(line, 'an edge has its label written twice (in the line and in |bars|); keep one'); return; } label = pm[1]; i += pm[0].length; }
      if (lk.open && !openLinkWarned) { openLinkWarned = true; warn(line, '"---" lines have no arrowhead in Mermaid, but motion_arch always draws one; the edge is drawn as an arrow.'); }
      const next = readGroup();
      if (!next) return;
      next.forEach((r) => applyRef(r, line));
      const lab = label !== undefined ? cleanText(label) : '';
      for (const a of prev) for (const b of next) {
        edges.push({ from: a.orig, to: b.orig, label: lab || undefined, style: lk.style, both: lk.both || undefined, line });
      }
      prev = next;
    }
  }

  // ---- header
  let li = 0;
  const L = () => li + 1;
  // front matter
  const firstReal = lines.findIndex((l) => l.trim() !== '');
  if (firstReal >= 0 && lines[firstReal].trim() === '---') {
    let e = -1;
    for (let k = firstReal + 1; k < lines.length; k++) if (lines[k].trim() === '---') { e = k; break; }
    if (e < 0) fail(firstReal + 1, 'front matter starts with "---" but is never closed; add a closing "---" line');
    else {
      for (let k = firstReal + 1; k < e; k++) {
        const m = /^\s*title\s*:\s*(.+?)\s*$/.exec(lines[k]);
        if (m) title = stripQuotes(m[1]);
      }
      li = e + 1;
    }
  }

  for (; li < lines.length; li++) {
    let line = lines[li].trim();
    if (!line) continue;
    if (line.startsWith('%%')) {
      const d = /^%%\s*(title|msg|numbered|pace|duration|step|relation-column|relation-name|rel)\s*:\s*(.*)$/i.exec(line);
      const key = d && d[1].toLowerCase();
      if (key === 'title') { if (d[2].trim()) title = d[2].trim(); }
      else if (key === 'msg') {
        const m = /^(\S+?)\s*->\s*(\S+?)\s+"([^"]*)"(?:\s+(back))?\s*$/.exec(d[2].trim());
        if (!m) fail(L(), `bad "%% msg:" directive; write it as  %% msg: fromId->toId "payload text"  (add the word back at the end for a reply)`);
        else msgDirectives.push({ line: L(), from: m[1], to: m[2], text: cleanText(m[3]), back: !!m[4] });
      } else if (key === 'numbered') {
        const v = d[2].trim().toLowerCase();
        if (v === 'on' || v === 'true' || v === 'yes') numbered = true;
        else if (v === 'off' || v === 'false' || v === 'no') numbered = false;
        else fail(L(), '"%% numbered:" must be on or off');
      } else if (key === 'pace') {
        const v = d[2].trim().toLowerCase();
        if (Object.hasOwn(PACES, v)) pace = v; else fail(L(), `"%% pace:" must be one of ${Object.keys(PACES).join(', ')}`);
      } else if (key === 'duration') {
        const v = Number(d[2].trim().replace(/\s*s$/i, ''));
        if (Number.isFinite(v) && v >= 2 && v <= 120) duration = v; else fail(L(), '"%% duration:" must be a number of seconds from 2 to 120, for example %% duration: 40');
      } else if (key === 'relation-column') {
        const v = d[2].trim().toLowerCase();
        if (v === 'on' || v === 'true' || v === 'yes') relationColumn = true;
        else if (v === 'off' || v === 'false' || v === 'no') relationColumn = false;
        else fail(L(), '"%% relation-column:" must be on or off');
      } else if (key === 'relation-name') {
        const v = d[2].trim();
        if (v && v.length <= LIMITS.relation) relationName = v; else fail(L(), `"%% relation-name:" must be 1 to ${LIMITS.relation} characters, for example %% relation-name: Interaction`);
      } else if (key === 'rel') {
        const m = /^(\S+?)\s*->\s*(\S+?)\s+(.+?)\s*$/.exec(d[2].trim());
        if (!m) fail(L(), 'bad "%% rel:" directive; write it as  %% rel: fromId->toId calls  (free text, at most 20 characters)');
        else if (m[3].length > LIMITS.relation) fail(L(), `"%% rel:" text "${m[3]}" is ${m[3].length} characters; the most is ${LIMITS.relation}`);
        else relDirectives.push({ line: L(), from: m[1], to: m[2], text: m[3] });
      } else if (key === 'step') {
        const m = /^(\S+?)\s*->\s*(\S+?)\s+(\d+)\s*$/.exec(d[2].trim());
        if (!m) fail(L(), 'bad "%% step:" directive; write it as  %% step: fromId->toId 3');
        else stepDirectives.push({ line: L(), from: m[1], to: m[2], step: +m[3] });
      }
      continue;
    }
    line = stripTrailingComment(line);
    if (!headerSeen) {
      const hm = /^(flowchart|graph)(?:-elk)?(?:\s+(LR|RL|TB|TD|BT))?\s*;?$/i.exec(line);
      if (hm) {
        headerSeen = true;
        const d = (hm[2] || 'TB').toUpperCase();
        direction = d === 'TD' ? 'TB' : d;
        continue;
      }
      const word = (/^([A-Za-z][\w-]*)/.exec(line) || [])[1] || line.slice(0, 20);
      const k = word.toLowerCase();
      if (/^(flowchart|graph)/i.test(line)) {
        fail(L(), `cannot read the header "${line}"; write "flowchart LR" (or TD, TB, RL, BT)`);
      } else if (Object.hasOwn(OTHER_DIAGRAMS, k)) {
        fail(L(), `"${word}" diagrams are not supported; only flowcharts are. ${OTHER_DIAGRAMS[k]}`);
      } else if (line.startsWith('%%{')) { continue; }
      else {
        fail(L(), `expected "flowchart LR" (or "graph TD") on the first line, found "${line.slice(0, 30)}"`);
      }
      break;
    }
    for (const stmt of splitStatements(line)) {
      let m;
      if (/^%%\{.*\}%%$/.test(stmt)) continue;
      if ((m = /^subgraph\b\s*(.*)$/.exec(stmt))) {
        let rest = m[1].trim(), key, label;
        let mm;
        if ((mm = /^([A-Za-z0-9_-]+)\s*\[\s*(.*?)\s*\]$/.exec(rest))) { key = mm[1]; label = cleanText(mm[2]); }
        else if ((mm = /^"(.*)"$/.exec(rest))) { label = cleanText(mm[1]); key = slug(label); }
        else if (rest) { label = cleanText(rest); key = rest.includes(' ') ? slug(rest) : rest; }
        else { fail(L(), 'a subgraph needs a name; write: subgraph id[Title]'); key = 'sg' + groupsByKey.size; label = key; }
        const nested = groupStack.length > 0;
        if (nested) {
          warn(L(), `subgraph "${label}" is inside "${groupStack[0].label}"; nested groups are flattened, its nodes are drawn in the outer group "${groupStack[0].label}".`);
        } else if (!groupsByKey.has(key)) {
          groupsByKey.set(key, { key, label, order: groupsByKey.size, line: L() });
        } else {
          warn(L(), `subgraph "${key}" is declared twice; the second block adds to the first.`);
        }
        groupStack.push({ key: nested ? groupStack[0].key : key, label: nested ? groupStack[0].label : label, nested });
        continue;
      }
      if (/^end$/i.test(stmt)) {
        if (!groupStack.length) fail(L(), '"end" without a matching "subgraph"; remove it or add the subgraph line above');
        else groupStack.pop();
        continue;
      }
      if (/^direction\b/i.test(stmt)) { warn(L(), `"${stmt}" inside a subgraph is ignored; the whole diagram uses the direction on the first line.`); continue; }
      if (/^(classDef|style|linkStyle)\b/.test(stmt)) { styleLine = styleLine || L(); continue; }
      if (/^(accTitle|accDescr)\b/.test(stmt)) continue;
      if ((m = /^class\s+([^\s]+)\s+([A-Za-z0-9_-]+)$/.exec(stmt))) { if (!resolveKind(m[2])) styleLine = styleLine || L(); classStmts.push({ line: L(), ids: m[1].split(',').filter(Boolean), cls: m[2] }); continue; }
      if (/^class\b/.test(stmt)) { fail(L(), 'write class statements as: class nodeId kind  (for example: class db store)'); continue; }
      if (/^click\b/.test(stmt)) { clickLine = clickLine || L(); continue; }
      parseChain(stmt, L());
    }
  }
  if (!headerSeen && !errors.length) fail(1, 'empty input; start with "flowchart LR" and add nodes and arrows');
  if (groupStack.length) fail(lines.length, `${groupStack.length} "subgraph" block(s) are never closed; add an "end" line for each`);

  if (styleLine) warnings.push('Colours and styles (classDef, style, linkStyle) are not drawn; the diagram uses its own colours by node kind.' + (clickLine ? ' click/link statements are ignored too.' : ''));
  else if (clickLine) warn(clickLine, 'click/link statements are ignored.');
  if (tagsStripped) warnings.push('HTML tags were removed from a label.');

  // class statements -> hints
  for (const cs of classStmts) {
    for (const id of cs.ids) {
      const n = nodes.get(id);
      if (n) n.hints.push(cs.cls);
      else warn(cs.line, `class statement names "${id}", which is not a node` + (didYouMean(id, [...nodes.keys()]) ? ` (did you mean "${didYouMean(id, [...nodes.keys()])}"?)` : '') + '; ignored.');
    }
  }

  if (errors.length) throw new ArchError(errors.slice(0, 20), warnings);

  // ---- build canonical graph
  const mapNode = makeIdMapper();
  const mapGroup = makeIdMapper();
  const groups = [...groupsByKey.values()].sort((a, b) => a.order - b.order);
  const usedGroups = new Set([...nodes.values()].map((n) => n.group).filter((g) => g !== undefined));
  const gOut = [];
  for (const g of groups) {
    if (!usedGroups.has(g.key)) { warn(g.line, `subgraph "${g.label}" has no nodes; it is dropped.`); continue; }
    gOut.push({ id: mapGroup(g.key), label: g.label });
  }
  const nOut = [];
  for (const n of [...nodes.values()].sort((a, b) => a.order - b.order)) {
    let kind;
    for (const h of n.hints) { const k = resolveKind(h); if (k) kind = k; }
    if (!kind) kind = SHAPE_KIND[Object.hasOwn(SHAPE_KIND, n.shape || 'plain') ? (n.shape || 'plain') : 'plain'];
    const label = n.label !== undefined ? n.label : n.orig;
    const o = withLine({ id: mapNode(n.orig), label, kind }, n.line);
    if (n.sub) o.sub = n.sub;
    if (n.group !== undefined && groupsByKey.has(n.group)) o.group = mapGroup(n.group);
    nOut.push(o);
  }
  const lookup = (k) => (nodes.has(k) ? k : [...nodes.keys()].find((x) => x.toLowerCase() === k.toLowerCase()));
  const eOut = edges.map((e) => {
    const o = withLine({ from: mapNode(e.from), to: mapNode(e.to), style: e.style }, e.line);
    if (e.label) o.label = e.label;
    if (e.both) o.both = true;
    return o;
  });
  // subgraph ids used as edge endpoints would have become nodes; catch that clearly
  for (const e of edges) {
    if (groupsByKey.has(e.from) || groupsByKey.has(e.to)) {
      const which = groupsByKey.has(e.from) ? e.from : e.to;
      const n = nodes.get(which);
      if (n && n.group === undefined && n.label === undefined) {
        errors.push(`line ${e.line}: "${which}" is a subgraph, not a node. Edges to a whole subgraph are not supported; connect to a node inside it.`);
      }
    }
  }
  const mOut = [];
  for (const d of msgDirectives) {
    const f = lookup(d.from), t = lookup(d.to);
    const names = [...nodes.keys()];
    if (!f) { errors.push(`line ${d.line}: message endpoint "${d.from}" is not a node` + (didYouMean(d.from, names) ? ` (did you mean "${didYouMean(d.from, names)}"?)` : '')); continue; }
    if (!t) { errors.push(`line ${d.line}: message endpoint "${d.to}" is not a node` + (didYouMean(d.to, names) ? ` (did you mean "${didYouMean(d.to, names)}"?)` : '')); continue; }
    const m = { from: mapNode(f), to: mapNode(t), text: d.text };
    if (d.back) m.back = true;
    mOut.push(m);
  }
  if (errors.length) throw new ArchError(errors.slice(0, 20), warnings);

  const taken = new Set();
  for (const d of stepDirectives) {
    const f = lookup(d.from), t = lookup(d.to);
    const names = [...nodes.keys()];
    if (!f || !t) { errors.push(`line ${d.line}: step directive names "${!f ? d.from : d.to}", which is not a node` + (didYouMean(!f ? d.from : d.to, names) ? ` (did you mean "${didYouMean(!f ? d.from : d.to, names)}"?)` : '')); continue; }
    const idx = eOut.findIndex((e, i) => e.from === mapNode(f) && e.to === mapNode(t) && !taken.has(i));
    if (idx < 0) { errors.push(`line ${d.line}: step directive: there is no (further) edge from "${d.from}" to "${d.to}"`); continue; }
    taken.add(idx); eOut[idx].step = d.step;
  }
  const relTaken = new Set();
  for (const d of relDirectives) {
    const f = lookup(d.from), t = lookup(d.to);
    const names = [...nodes.keys()];
    if (!f || !t) { errors.push(`line ${d.line}: rel directive names "${!f ? d.from : d.to}", which is not a node` + (didYouMean(!f ? d.from : d.to, names) ? ` (did you mean "${didYouMean(!f ? d.from : d.to, names)}"?)` : '')); continue; }
    const idx = eOut.findIndex((e, i) => e.from === mapNode(f) && e.to === mapNode(t) && !relTaken.has(i));
    if (idx < 0) { errors.push(`line ${d.line}: rel directive: there is no (further) edge from "${d.from}" to "${d.to}"`); continue; }
    relTaken.add(idx); eOut[idx].relation = d.text;
  }
  if (errors.length) throw new ArchError(errors.slice(0, 20), warnings);
  const graph = { direction: opts.direction || direction, groups: gOut, nodes: nOut, edges: eOut, messages: mOut };
  if (relationColumn !== undefined) graph.relationColumn = relationColumn;
  if (relationName) graph.relationName = relationName;
  if (numbered !== undefined) graph.numbered = numbered;
  if (pace) graph.pace = pace;
  if (duration !== undefined) graph.duration = duration;
  const ttl = opts.title || title;
  if (ttl) graph.title = ttl;
  return { graph, warnings };
}
