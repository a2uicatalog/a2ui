// usage: node treemap_d3_golden_gen.mjs /path/to/d3-hierarchy-3.1.2/src/index.js > treemap_d3_golden.json
// Nested treemap (treemap `path` field): hierarchy(spec).sum(value).sort(by value descending) laid out by treemap().tile(treemapSquarify)
// .size([900, 300]) with nested padding: paddingInner 2; below the root, paddingOuter 3 on three sides and a 20 high header (paddingTop);
// the root has no outer padding. No rounding. Each case lists every node in eachBefore (pre-order) order as
// [depth, x0, y0, x1, y1, value] after the sort, so the renderers must reproduce d3's sort order as well as its rectangles.
const {hierarchy, treemap, treemapSquarify} = await import(process.argv[2]);
let s = 4242; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const L = (n, v) => ({n, v}), G = (n, ...c) => ({n, c});
const cases = {
  depth2: G('root', G('Home', L('a', 120), L('b', 80), L('c', 30)), G('Work', L('d', 90), L('e', 60))),
  depth3: G('root', G('Home', G('Photos', L('2024', 120), L('2023', 70)), L('docs', 30)), G('Work', G('Code', L('x', 90), L('y', 45), L('z', 5)), L('notes', 20))),
  depth4: G('root', G('A', G('B', G('C', L('1', 50), L('2', 30)), L('3', 20)), L('4', 10)), G('D', G('E', G('F', L('5', 40), L('6', 25), L('7', 5)), L('8', 15)), L('9', 12)), L('10', 8)),
  flat_leaves_only: G('root', L('a', 5), L('b', 3), L('c', 9), L('d', 1)),
  ties_keep_input_order: G('root', G('g1', L('a', 4), L('b', 4), L('c', 4)), G('g2', L('d', 4), L('e', 4)), L('f', 4)),
  one_chain: G('root', G('A', G('B', G('C', L('only', 7))))),
  tiny_and_huge: G('root', G('big', L('a', 1e6), L('b', 1)), G('tiny', L('c', 0.001), L('d', 0.002)), L('e', 250000)),
  unequal_groups: G('root', G('x', L('a', 1000), L('b', 900), L('c', 800)), G('y', L('d', 3)), G('z', L('e', 2), L('f', 1))),
  twelve_nested: G('root', G('A', G('A1', L('a', 9), L('b', 8)), G('A2', L('c', 7), L('d', 6))), G('B', G('B1', L('e', 5), L('f', 4)), L('g', 3)), G('C', L('h', 2.5), L('i', 2), L('j', 1.5), L('k', 1), L('l', 0.5))),
};
// seeded random trees, 1 to 12 leaves, depth up to 4
function rtree() {
  const root = G('root'), leaves = 1 + Math.floor(rnd() * 12);
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
const lay = treemap().tile(treemapSquarify).size([900, 300])
  .paddingInner(2).paddingLeft(n => n.depth ? 3 : 0).paddingRight(n => n.depth ? 3 : 0).paddingBottom(n => n.depth ? 3 : 0).paddingTop(n => n.depth ? 20 : 0);
const out = {};
for (const [name, spec] of Object.entries(cases)) {
  const root = hierarchy(spec, d => d.c).sum(d => d.v).sort((a, b) => b.value - a.value);
  lay(root);
  const rows = []; root.eachBefore(n => rows.push([n.depth, n.x0, n.y0, n.x1, n.y1, n.value, n.data.n]));
  out[name] = {spec, rows};
}
console.log(JSON.stringify(out));
