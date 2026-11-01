// Label wrapping and label hygiene for the converter. Pure ES module.
//
// The atom shows a node label (max 40) with an optional second line (`sub`, max 40), and an edge label (max 48) with an
// optional second line (`label2`, max 48). A longer text is wrapped here at a word boundary near the middle, so words are
// no longer lost; only a text that cannot fit on two lines is cut (with an ellipsis, and one merged warning).
// Lengths are counted in UTF-16 units (JS .length), the strictest count the Python and Apps Script twins can see; a
// split never lands inside a surrogate pair.
import { LIMITS } from './graph.mjs';

const MIN_SIDE = 4;
const squash = (s) => String(s).replace(/\s+/g, ' ').trim();

// text -> {lines: [line1] | [line1, line2], cut: boolean}; every line is at most `max` units
export function wrapLabel(text, max) {
  const raw = String(text).trim();
  if (raw.length <= max) return { lines: [raw], cut: false };     // fits on one line: untouched, so existing output is byte-identical
  const t = squash(raw);
  if (t.length <= max) return { lines: [t], cut: false };
  const cps = Array.from(t);
  const pre = [0];                       // pre[i] = UTF-16 length of the first i code points
  cps.forEach((c, i) => pre.push(pre[i] + c.length));
  const total = pre[cps.length];
  if (total <= 2 * max) {
    // 1. a space that leaves both halves within the limit and closest to the middle
    let best = -1, bestGap = Infinity;
    for (let i = 1; i < cps.length - 1; i++) {
      if (cps[i] !== ' ') continue;
      const l = pre[i], r = total - pre[i + 1];
      if (l < MIN_SIDE || r < MIN_SIDE) continue;       // never strand a step number or a short word on a line of its own
      if (l <= max && r <= max && Math.abs(l - r) < bestGap) { best = i; bestGap = Math.abs(l - r); }
    }
    if (best >= 0) return { lines: [cps.slice(0, best).join(''), cps.slice(best + 1).join('')], cut: false };
    // 2. one long word, or no spaces (CJK): split inside the text, as near the middle as the limits allow
    let at = -1, gap = Infinity;
    for (let i = 1; i < cps.length; i++) {
      const l = pre[i], r = total - pre[i];
      if (l <= max && r <= max && Math.abs(l - r) < gap) { at = i; gap = Math.abs(l - r); }
    }
    if (at > 0) return { lines: [cps.slice(0, at).join('').trimEnd(), cps.slice(at).join('').trimStart()], cut: false };
  }
  // 3. too long for two lines: fill the first line at a word boundary, cut the rest
  let at = -1;
  for (let i = 1; i < cps.length; i++) if (cps[i] === ' ' && pre[i] <= max) at = i;
  if (at < 0) { at = 0; while (at + 1 < cps.length && pre[at + 1] <= max) at++; }
  const l1 = cps.slice(0, at).join('').trimEnd(), rest = cps.slice(at).join('').trimStart();
  return { lines: [l1, clipText(rest, max)], cut: true };
}

export function clipText(str, max) {
  const t = squash(str);
  if (t.length <= max) return t;
  const cps = Array.from(t);
  let n = 0, i = 0;
  while (i < cps.length && n + cps[i].length <= max - 1) { n += cps[i].length; i++; }
  return cps.slice(0, i).join('').trimEnd() + '…';
}

// an edge label the author numbered themselves ("1. Request", "2) Return", "3: Go", "(4) x"): the part after the number, or the label
const OWN_NUMBER = /^\(?\d{1,3}\s*(?:[.):]|-(?=\s))\s+(?=\S)/;
export function stripOwnNumber(label) {
  const s = String(label ?? '');
  return OWN_NUMBER.test(s.trimStart()) ? s.trimStart().replace(OWN_NUMBER, '') : s;
}

// trailing punctuation that is left over when a label was split on <br/> ("Validate Token Signature,")
export const stripDangling = (s) => String(s).replace(/[\s,;:&\-–—]+$/, '');

const nameList = (xs) => (xs.length < 2 ? xs.join('') : xs.slice(0, -1).join(', ') + ' and ' + xs[xs.length - 1]);

// graph (+ whether the edge labels get a step number) -> what the atom will be given
//   nodes: id -> {label, sub}, edges: index -> {text (lines joined by \n), lines}, edgeLabels: the author's labels without their own number,
//   warnings: at most one line each for nodes, sub-labels, edges and group titles
export function planLabels(graph, { numbered = false, stepNo = null } = {}) {
  const nodeCut = [], subCut = [], edgeCut = [], groupCut = [];
  const nodes = new Map();
  for (const n of graph.nodes) {
    let label = squash(n.label), sub = n.sub ? squash(n.sub) : '';
    if (label.length > LIMITS.label) {
      if (!sub) {
        const w = wrapLabel(label, LIMITS.label);
        label = w.lines[0]; sub = w.lines[1] || '';
        if (w.cut) nodeCut.push(n.id);
      } else { label = clipText(label, LIMITS.label); nodeCut.push(n.id); }
    }
    if (sub.length > LIMITS.sub) { sub = clipText(sub, LIMITS.sub); if (!nodeCut.includes(n.id)) subCut.push(n.id); }
    nodes.set(n.id, { label, sub });
  }
  const edgeLabels = graph.edges.map((e) => (numbered && e.label ? stripOwnNumber(e.label) : e.label));
  const edges = graph.edges.map((e, i) => {
    const base = edgeLabels[i];
    const full = numbered ? String(stepNo[i]) + (base ? ' ' + base : '') : base;
    if (!full) return { text: base, lines: [] };
    const w = wrapLabel(full, LIMITS.edgeLabel);
    if (w.cut) edgeCut.push(i + 1);
    return { text: w.lines.join('\n'), lines: w.lines };
  });
  for (const gr of graph.groups || []) if (String(gr.label).length > LIMITS.groupLabel) groupCut.push(gr.id);

  const warnings = [];
  if (nodeCut.length) {
    warnings.push(`${nodeCut.length === 1 ? 'Node' : 'Nodes'} ${nameList(nodeCut.map((x) => `"${x}"`))} ${nodeCut.length === 1 ? 'has a label' : 'have labels'} longer than the atom can show (${LIMITS.label} characters, or ${LIMITS.label * 2} on two lines when there is no sub-label); ${nodeCut.length === 1 ? 'it was' : 'they were'} cut (the Steps table has the full text).`);
  }
  if (subCut.length) {
    warnings.push(`${subCut.length === 1 ? 'Node' : 'Nodes'} ${nameList(subCut.map((x) => `"${x}"`))} ${subCut.length === 1 ? 'has a sub-label' : 'have sub-labels'} longer than ${LIMITS.sub} characters; ${subCut.length === 1 ? 'it was' : 'they were'} cut.`);
  }
  if (edgeCut.length) {
    warnings.push(`${edgeCut.length === 1 ? 'Edge' : 'Edges'} ${nameList(edgeCut.map(String))} ${edgeCut.length === 1 ? 'has a label' : 'have labels'} longer than the atom can show on two lines; ${edgeCut.length === 1 ? 'it was' : 'they were'} cut (the Steps table has the full text).`);
  }
  if (groupCut.length) {
    warnings.push(`${groupCut.length === 1 ? 'Group' : 'Groups'} ${nameList(groupCut.map((x) => `"${x}"`))} ${groupCut.length === 1 ? 'has a title' : 'have titles'} longer than ${LIMITS.groupLabel} characters; ${groupCut.length === 1 ? 'it was' : 'they were'} cut.`);
  }
  return { nodes, edges, edgeLabels, warnings };
}
