// usage: node org_chart_radial_d3_golden_gen.mjs /path/to/d3-hierarchy-3.1.2/src/index.js /path/to/d3-shape-3.2.0/src/index.js > org_chart_radial_d3_golden.json
// org_chart layout "radial" (I55): d3.tree().size([2 * Math.PI, 1000]).separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth),
// the radial tidy tree of the d3 gallery, on the REAL d3-hierarchy; x is the angle in radians (0 at twelve o'clock, clockwise), y the radius.
// Node 0 is the root (for a forest the undrawn virtual root). Also: each node's point (r cos(x - PI/2), r sin(x - PI/2)) as d3's pointRadial gives it,
// and each link's path from the REAL d3-shape linkRadial() (M, then one cubic Bezier: its three control points are returned parsed).
const {hierarchy, tree} = await import(process.argv[2]);
const {linkRadial, } = await import(process.argv[3]);
let s = 20261022; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
function run(kids) {
  const mk = (i) => ({i, children: kids[i].length ? kids[i].map(mk) : undefined});
  const root = hierarchy(mk(0));
  tree().size([2 * Math.PI, 1000]).separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth)(root);
  const n = kids.length, x = new Array(n), y = new Array(n), depth = new Array(n), pt = new Array(n);
  root.each((d) => { const i = d.data.i; x[i] = d.x; y[i] = d.y; depth[i] = d.depth; pt[i] = [d.y * Math.cos(d.x - Math.PI / 2), d.y * Math.sin(d.x - Math.PI / 2)]; });
  const lk = new Array(n).fill(null), gen = linkRadial().angle((d) => d.x).radius((d) => d.y).digits(null);
  root.links().forEach((l) => {
    const str = gen(l), nums = str.match(/-?[\d.]+(?:e[-+]?\d+)?/g).map(Number);
    lk[l.target.data.i] = nums;                    // [x0, y0, c1x, c1y, c2x, c2y, x1, y1]
  });
  return {x, y, depth, pt, link: lk};
}
function randTree(n) {
  const kids = [[]], depth = [0];
  for (let i = 1; i < n; i++) {
    for (let t = 0; t < 40; t++) {
      const p = Math.floor(rnd() * i);
      if (depth[p] < 4 && kids[p].length < 6) { kids[p].push(i); kids.push([]); depth.push(depth[p] + 1); break; }
    }
  }
  return kids;
}
const cases = {
  single: [[]],
  chain4: [[1], [2], [3], []],
  one_child_fan: [[1], [2, 3, 4], [], [], []],
  six_children: [[1, 2, 3, 4, 5, 6], [], [], [], [], [], []],
  unbalanced: [[1, 2], [3], [4, 5, 6], [7], [], [], [], []],
  forest_virtual_root: [[1, 2, 3], [4, 5], [6], [7], [], [], [], []],
  tree30: (() => { const k = Array.from({length: 30}, () => []); const ch = (p, from, to) => { for (let i = from; i <= to; i++) k[p].push(i); }; ch(0, 1, 6); ch(1, 7, 12); ch(2, 13, 16); ch(3, 17, 19); ch(4, 20, 21); ch(6, 22, 24); ch(7, 25, 27); ch(8, 28, 29); return k; })(),
};
const out = {golden: {}, fuzz: []};
for (const [name, kids] of Object.entries(cases)) out.golden[name] = Object.assign({name, kids, forest: name === 'forest_virtual_root'}, run(kids));
for (let i = 0; i < 70; i++) { const kids = randTree(1 + Math.floor(rnd() * 31)); out.fuzz.push(Object.assign({name: 'fuzz' + i, kids, forest: false}, run(kids))); }
console.log(JSON.stringify(out));
