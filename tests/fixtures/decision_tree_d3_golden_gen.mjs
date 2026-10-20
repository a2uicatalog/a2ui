// usage: node decision_tree_d3_golden_gen.mjs /path/to/d3-hierarchy-3.1.2/src/index.js > decision_tree_d3_golden.json
// decision_tree layout "tree" draws the nested {text, children} payload with the org_chart tidy tree: the REAL d3.tree().nodeSize([1, 1]) with
// separation (w[a] + w[b]) / 2 + (same parent ? 8 : 16), x = the box centre in px, widths from the label by org_chart's rule (_oc_width).
// Nodes are numbered in pre-order; several top-level nodes get an undrawn virtual root (index = node count, width 0), as org_chart does.
const {hierarchy, tree} = await import(process.argv[2]);
let s = 777; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const T = (text, children) => children ? {text, children} : {text};
const width = (t, bold) => { const c = bold ? 9.6 : 8.4, full = Math.ceil(t.length * c) + 22, word = Math.ceil(Math.max(...t.split(' ').map(x => x.length)) * c) + 22; return Math.max(64, Math.min(full, Math.max(112, Math.min(140, word)))); };
const cases = {
  ship: [T('Tests pass?', [T('Yes: ship'), T('No: fix first', [T('Re-run CI')])])],
  single: [T('Only node')],
  chain: [T('Start', [T('Next step here', [T('Then another', [T('Then the end')])])])],
  wide_root: [T('Which plan?', [T('Free'), T('Team'), T('Business'), T('Enterprise'), T('Custom'), T('Other')])],
  forest: [T('First question', [T('a1'), T('a2', [T('a2x')])]), T('Second question', [T('b1')]), T('Lonely leaf')],
  deep_six_levels: [T('L1 root', [T('L2 a', [T('L3 a', [T('L4 a', [T('L5 a', [T('L6 a')])])]), T('L3 b')]), T('L2 b', [T('L3 c', [T('L4 c')])])])],
  long_labels: [T('A fairly long question text?', [T('Yes, and this one is long too', [T('Supercalifragilisticexpiali')]), T('No')])],
};
const rl = (n, f) => Array.from({length: n}, (_, i) => f(i));
function randTree(budget, depth) {
  const n = {text: 'N' + Math.floor(rnd() * 1000) + (rnd() < 0.4 ? ' with some more words' : '')};
  budget.n--; if (depth < 5 && budget.n > 0 && rnd() < 0.7) { const k = 1 + Math.floor(rnd() * 4); n.children = []; for (let i = 0; i < k && budget.n > 0; i++) n.children.push(randTree(budget, depth + 1)); if (!n.children.length) delete n.children; }
  return n;
}
const fuzz = [];
for (let c = 0; c < 14; c++) { const b = {n: 5 + Math.floor(rnd() * 27)}; const top = []; const nt = rnd() < 0.3 ? 2 : 1; for (let i = 0; i < nt && b.n > 0; i++) top.push(randTree(b, 0)); fuzz.push(top); }
function run(nodes) {
  const flat = [];   // {text, depth, par, kids}
  const build = (n, depth, par) => { const f = {text: n.text, depth, par, kids: []}; flat.push(f); const id = flat.length - 1; f.kids = (n.children || []).map(c => build(c, depth + 1, id)); return id; };
  const top = nodes.map(n => build(n, 0, -1));
  const total = flat.length, virt = top.length !== 1;
  const kids = flat.map(f => f.kids), w = flat.map(f => width(f.text, f.depth === 0));
  if (virt) { kids.push(top); w.push(0); }
  const root = virt ? total : top[0];
  const par = new Array(kids.length).fill(-1); kids.forEach((ks, i) => ks.forEach(k => par[k] = i));
  const mk = i => ({i, children: kids[i].map(mk)});
  const h = hierarchy(mk(root), d => d.children);
  const nodeOf = []; h.each(n => { nodeOf[n.data.i] = n; });
  tree().nodeSize([1, 1]).separation((a, b) => (w[a.data.i] + w[b.data.i]) / 2 + (a.parent === b.parent ? 8 : 16))(h);
  const x = [], depth = [];
  for (let i = 0; i < kids.length; i++) { x.push(nodeOf[i].x + 0); depth.push(nodeOf[i].depth); }
  return {nodes, kids, w, x, depth, virt, labels: flat.map(f => f.text)};
}
const out = {d3_hierarchy: '3.1.2', golden: {}, fuzz: []};
for (const [k, v] of Object.entries(cases)) out.golden[k] = run(v);
for (const v of fuzz) out.fuzz.push(run(v));
console.log(JSON.stringify(out));
