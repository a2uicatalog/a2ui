// usage: node org_chart_cluster_d3_golden_gen.mjs /path/to/d3-hierarchy-3.1.2/src/index.js > org_chart_cluster_d3_golden.json
// org_chart layout "cluster" (I53): d3.cluster().nodeSize([1, 1]) with a pixel separation, run on the REAL d3-hierarchy.
// Node 0 is the root (for a forest it is the undrawn virtual root, width 0). kids[i] lists node i's children in order, w[i] is the box
// size along the leaf axis in px (widths for top-down, heights for left-to-right).
// The separation of two consecutive leaves a, b is the largest gap needed in any tier row k between what a's chain and b's chain put in row k:
// a node (its box size) or, where a chain skips the row, the vertical link that passes through it (size 0). Chains that put the same node
// or the same link in row k need nothing. gap = 8 for siblings, 16 otherwise. Row k of node n is root.height - n.height (leaves all
// land on the last row), the row d3 gives with nodeSize [1, 1]: y = root.y - n.y.
const {hierarchy, cluster} = await import(process.argv[2]);
let s = 20261021; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
function run(kids, size) {
  const mk = (i) => ({i, children: kids[i].length ? kids[i].map(mk) : undefined});
  const root = hierarchy(mk(0));
  const H = root.height;
  const row = (n) => H - n.height;
  const occ = (leaf, k) => {
    let q = leaf;                                  // the lowest ancestor-or-self at row >= k that has a node at row k, or the link above the first one below it
    const chain = leaf.ancestors();                // leaf .. root
    for (const n of chain) if (row(n) === k) return {id: 'n' + n.data.i, w: size[n.data.i]};
    let below = null;
    for (const n of chain) if (row(n) > k) below = n; // the shallowest ancestor-or-self deeper than row k
    return {id: 'e' + below.data.i, w: 0};
  };
  const sep = (a, b) => {
    const gap = a.parent === b.parent ? 8 : 16;
    let need = 0;
    for (let k = 0; k <= H; k++) {
      const p = occ(a, k), q = occ(b, k);
      if (p.id !== q.id) need = Math.max(need, (p.w + q.w) / 2 + gap);
    }
    return need;
  };
  const lay = cluster().nodeSize([1, 1]).separation(sep);
  lay(root);
  const x = new Array(kids.length), r = new Array(kids.length);
  root.each((n) => { x[n.data.i] = n.x; r[n.data.i] = row(n); });
  return {x, row: r};
}
function randTree(n, forest) {
  const kids = [[]], depth = [0];
  for (let i = 1; i < n; i++) {
    for (let t = 0; t < 40; t++) {
      const p = Math.floor(rnd() * i);
      if (depth[p] < (forest ? 4 : 3) && kids[p].length < 6) { kids[p].push(i); kids.push([]); depth.push(depth[p] + 1); break; }
    }
  }
  return kids;
}
const wrule = () => [64, 73, 81, 99, 112, 118, 123, 140][Math.floor(rnd() * 8)];
// Box widths from labels by the renderer's documented rule (8.4 px a character, 9.6 bold, plus 22 px; at most 112 unless the longest word needs more, up to 140)
const boxw = (t, bold) => { const c = bold ? 9.6 : 8.4, full = Math.ceil(t.length * c) + 22, word = Math.ceil(Math.max(...t.split(' ').map((x) => x.length)) * c) + 22; return Math.max(64, Math.min(full, Math.max(112, Math.min(140, word)))); };
const boxlines = (t, w, bold) => { const tw = Math.ceil(t.length * (bold ? 9.6 : 8.4)); return tw <= w - 22 ? 1 : Math.min(3, Math.ceil(tw / (w - 30))); };
const cases = {
  single: [[]],
  chain4: [[1], [2], [3], []],
  one_child_then_fan: [[1], [2, 3, 4], [], [], []],
  six_children: [[1, 2, 3, 4, 5, 6], [], [], [], [], [], []],
  unbalanced: [[1, 2], [3], [4, 5, 6], [7], [], [], [], []],
  skip_rows: [[1, 2, 3], [], [4], [5], [], [6, 7], [], []].map((k, i, a) => k),   // 1 is a leaf beside deeper subtrees
  forest_virtual_root: [[1, 2, 3], [4, 5], [6], [7], [], [], [], []],
  tree30: (() => { const k = Array.from({length: 30}, () => []); const ch = (p, from, to) => { for (let i = from; i <= to; i++) k[p].push(i); }; ch(0, 1, 6); ch(1, 7, 12); ch(2, 13, 16); ch(3, 17, 19); ch(4, 20, 21); ch(6, 22, 24); ch(7, 25, 27); ch(8, 28, 29); return k; })(),
};
const out = {golden: {}, fuzz: []};
const add = (name, kids, forest) => {
  const n = kids.length, depth = new Array(n).fill(0), sh = forest ? 1 : 0;
  kids.forEach((ks, i) => ks.forEach((c) => { depth[c] = depth[i] + 1; }));
  const labels = kids.map((_, i) => (forest && i === 0) ? '' : 'L' + i + 'x'.repeat(Math.floor(rnd() * 24)));
  const w = labels.map((t, i) => (forest && i === 0) ? 0 : boxw(t, depth[i] - sh === 0));
  let lines = 1; labels.forEach((t, i) => { if (!(forest && i === 0)) lines = Math.max(lines, boxlines(t, w[i], depth[i] - sh === 0)); });
  const nh = [38, 46, 60][lines - 1], hs = kids.map((_, i) => (forest && i === 0) ? 0 : nh);
  const vw = kids.map((_, i) => (forest && i === 0) ? 0 : wrule()), vh = kids.map((_, i) => (forest && i === 0) ? 0 : [38, 46, 60][Math.floor(rnd() * 3)]);
  const t = run(kids, w), l = run(kids, hs), v = run(kids, vw), vl = run(kids, vh);
  return {name, kids, labels, w, nh, hs, x: t.x, row: t.row, ltr_x: l.x, ltr_row: l.row, vw, vx: v.x, vrow: v.row, vh, vlx: vl.x, forest: !!forest};
};
for (const [name, kids] of Object.entries(cases)) out.golden[name] = add(name, kids, name === 'forest_virtual_root');
for (let i = 0; i < 70; i++) { const forest = i % 5 === 4; out.fuzz.push(add('fuzz' + i, randTree(1 + Math.floor(rnd() * (forest ? 31 : 30)), forest), forest)); }
console.log(JSON.stringify(out));
