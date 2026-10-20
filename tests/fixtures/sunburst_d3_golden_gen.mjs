// usage: node sunburst_d3_golden_gen.mjs /path/to/d3-hierarchy-3.1.2/src/index.js /path/to/d3-shape-3.2.0/src/index.js > sunburst_d3_golden.json
// (d3-shape resolves its d3-path 3.1.0 from the node_modules it sits in.)
// sunburst: hierarchy(spec).sum(value).sort(by value descending) laid out by partition().size([dx, dy]), and the sector of every node drawn by
// d3-shape arc() as in d3's "sunburst" example. Each case lists every node in eachBefore (pre-order) order as
// [depth, x0, y0, x1, y1, value, name] after the sort, so the renderers must reproduce d3's sort order as well as its rectangles.
// Radial: size [2*PI, 300]. Icicle: size [360, 1200]. The arc of every node below the root is given twice: with arc()'s default
// 3 digits (the exact string the renderers print) and with digits(null) (full precision, for a 1e-9 comparison of the numbers).
const {hierarchy, partition} = await import(process.argv[2]);
const {arc} = await import(process.argv[3]);
let s = 777; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const L = (n, v) => ({n, v}), G = (n, ...c) => ({n, c});
const cases = {
  depth2: G('root', G('Home', L('a', 120), L('b', 80), L('c', 30)), G('Work', L('d', 90), L('e', 60))),
  depth3: G('root', G('Home', G('Photos', L('2024', 120), L('2023', 70)), L('docs', 30)), G('Work', G('Code', L('x', 90), L('y', 45), L('z', 5)), L('notes', 20))),
  depth4: G('root', G('A', G('B', G('C', L('1', 50), L('2', 30)), L('3', 20)), L('4', 10)), G('D', G('E', G('F', L('5', 40), L('6', 25), L('7', 5)), L('8', 15)), L('9', 12)), L('10', 8)),
  flat_leaves_only: G('root', L('a', 5), L('b', 3), L('c', 9), L('d', 1)),
  ties_keep_input_order: G('root', G('g1', L('a', 4), L('b', 4), L('c', 4)), G('g2', L('d', 4), L('e', 4)), L('f', 4)),
  one_group_full_circle: G('root', G('only', L('a', 7), L('b', 3))),
  one_chain: G('root', G('A', G('B', G('C', L('only', 7))))),
  tiny_and_huge: G('root', G('big', L('a', 1e6), L('b', 1)), G('tiny', L('c', 0.001), L('d', 0.002)), L('e', 250000)),
  unequal_groups: G('root', G('x', L('a', 1000), L('b', 900), L('c', 800)), G('y', L('d', 3)), G('z', L('e', 2), L('f', 1))),
  forty: G('root', ...Array.from({length: 8}, (_, g) => G('g' + g, ...Array.from({length: 5}, (_, k) => L('l' + g + k, 1 + ((g * 7 + k * 3) % 11) + k / 8))))),
};
function rtree() {
  const root = G('root'), leaves = 2 + Math.floor(rnd() * 12);
  for (let i = 0; i < leaves; i++) {
    let node = root; const d = Math.floor(rnd() * 4);
    for (let k = 0; k < d; k++) {
      const name = 'g' + Math.floor(rnd() * 3); let nx = node.c.find(x => x.n === name && x.c);
      if (!nx) { nx = G(name); node.c.push(nx); } node = nx;
    }
    node.c.push(L('l' + i, rnd() < 0.3 ? Math.round(rnd() * 1000) / 100 : Math.floor(1 + rnd() * 500)));
  }
  return root;
}
for (let i = 0; i < 30; i++) cases['fuzz' + i] = rtree();
const R = 300, PAD = 0.005, PADR = R * 1.5;
const mk = () => arc().innerRadius(d => d.y0).outerRadius(d => Math.max(d.y0, d.y1 - 1)).startAngle(d => d.x0).endAngle(d => d.x1)
  .padAngle(d => Math.min((d.x1 - d.x0) / 2, PAD)).padRadius(PADR);
const a3 = mk(), aN = mk().digits(null);
const out = {radial_size: [2 * Math.PI, R], icicle_size: [360, 1200], pad_angle: PAD, pad_radius: PADR, cases: {}, arcs: {}};
for (const [name, spec] of Object.entries(cases)) {
  const run = (size) => {
    const root = hierarchy(spec, d => d.c).sum(d => d.v).sort((a, b) => b.value - a.value);
    partition().size(size)(root);
    const rows = []; root.eachBefore(n => rows.push([n.depth, n.x0, n.y0, n.x1, n.y1, n.value, n.data.n]));
    return {root, rows};
  };
  const rad = run(out.radial_size), ici = run(out.icicle_size);
  const arcs = []; rad.root.eachBefore(n => { if (n.depth) arcs.push([a3(n), aN(n)]); });
  out.cases[name] = {spec, radial: rad.rows, icicle: ici.rows, arcs};
}
// arcs on their own: [startAngle, endAngle, innerRadius, outerRadius, padAngle, padRadius or null]
const T = 2 * Math.PI, H = Math.PI;
const own = [
  [0, 1, 60, 119, 0.005, 450], [0.3, 1.2, 60, 119, 0.005, 450], [0, T, 60, 119, 0.005, 450], [0, T - 1e-13, 60, 119, 0.005, 450], [0, T - 1e-7, 60, 119, 0.005, 450],
  [0, H, 0, 100, 0, null], [0, H, 0, 100, 0.01, 450], [1, 0, 60, 119, 0.005, 450], [5, 6.28, 40, 80, 0.2, 450], [0, 0.004, 60, 119, 0.005, 450],
  [0, 1e-7, 60, 119, 0.005, 450], [2, 2.0001, 100, 160, 0.005, 450], [0, 1, 119, 60, 0.005, 450], [0, 1, 60, 60, 0.005, 450], [0, 1, 0, 0, 0, null],
  [0, 1, 60, 1e-13, 0, null], [0, 3, 50, 100, 0.5, null], [0, 3, 50, 100, 0.5, 450], [0, 0.0002, 200, 260, 0.00019, 450], [4, 4 + H, 30, 90, 0, null],
  [0, T, 0, 100, 0, null], [H, H + 3.5, 10, 20, 0.005, 450], [0, 6.0, 75, 150, 0.005, 450], [0.1, 0.1 + T, 75, 150, 0.005, 450],
];
out.arcs.own = own.map(p => {
  const f = (dig) => { const a = arc().digits(dig).startAngle(p[0]).endAngle(p[1]).innerRadius(p[2]).outerRadius(p[3]).padAngle(p[4]); if (p[5] !== null) a.padRadius(p[5]); return a(); };
  return {p, d: f(3), full: f(null)};
});
console.log(JSON.stringify(out));
