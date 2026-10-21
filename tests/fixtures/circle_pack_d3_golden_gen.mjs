// usage: node circle_pack_d3_golden_gen.mjs /path/to/d3-hierarchy-3.1.2/src/index.js > circle_pack_d3_golden.json
// circle_pack: hierarchy(spec).sum(value).sort(by value descending) laid out by pack().size([w, h]).padding(3) (d3's "circle packing" example).
// Each case lists every node in eachBefore (pre-order) order as [depth, x, y, r, value, name]. Two sizes: square [600, 600] and [900, 500].
// pack() uses d3's fixed LCG (seed 1) for the randomised enclose, one generator per pack() call shared by every group in eachAfter order,
// so the renderers must also reproduce that order.
const {hierarchy, pack} = await import(process.argv[2]);
let s = 4242; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const L = (n, v) => ({n, v}), G = (n, ...c) => ({n, c});
const cases = {
  flat_two: G('root', L('a', 3), L('b', 1)),
  flat_three: G('root', L('a', 5), L('b', 3), L('c', 9)),
  flat_equal_six: G('root', ...[1, 2, 3, 4, 5, 6].map(i => L('e' + i, 4))),
  flat_ties: G('root', L('a', 4), L('b', 4), L('c', 4), L('d', 4), L('e', 4)),
  depth2: G('root', G('Home', L('a', 120), L('b', 80), L('c', 30)), G('Work', L('d', 90), L('e', 60))),
  depth3: G('root', G('Home', G('Photos', L('2024', 120), L('2023', 70)), L('docs', 30)), G('Work', G('Code', L('x', 90), L('y', 45), L('z', 5)), L('notes', 20))),
  depth4: G('root', G('A', G('B', G('C', L('1', 50), L('2', 30)), L('3', 20)), L('4', 10)), G('D', G('E', G('F', L('5', 40), L('6', 25), L('7', 5)), L('8', 15)), L('9', 12)), L('10', 8)),
  one_group: G('root', G('only', L('a', 7), L('b', 3))),
  one_chain: G('root', G('A', G('B', G('C', L('only', 7))))),
  single_leaf_groups: G('root', G('A', L('a', 4)), G('B', L('b', 9)), G('C', L('c', 1))),
  tiny_and_huge: G('root', G('big', L('a', 1e6), L('b', 1)), G('tiny', L('c', 0.001), L('d', 0.002)), L('e', 250000)),
  extreme_ratio: G('root', L('a', 1e12), L('b', 1e-9), L('c', 1)),
  many_equal_20: G('root', ...Array.from({length: 20}, (_, i) => L('q' + i, 10))),
  sixty: G('root', ...Array.from({length: 10}, (_, g) => G('g' + g, ...Array.from({length: 6}, (_, k) => L('l' + g + k, 1 + ((g * 7 + k * 3) % 11) + k / 8))))),
  sixty_flat: G('root', ...Array.from({length: 60}, (_, k) => L('f' + k, 1 + ((k * 13) % 17) + k / 8))),
};
function rtree(max) {
  const root = G('root'), leaves = 2 + Math.floor(rnd() * max);
  for (let i = 0; i < leaves; i++) {
    let node = root; const d = Math.floor(rnd() * 4);
    for (let k = 0; k < d; k++) {
      const name = 'g' + Math.floor(rnd() * 3); let nx = node.c.find(x => x.n === name && x.c);
      if (!nx) { nx = G(name); node.c.push(nx); } node = nx;
    }
    node.c.push(L('l' + i, rnd() < 0.3 ? Math.round(rnd() * 1000) / 100 + 0.01 : Math.floor(1 + rnd() * 500)));
  }
  return root;
}
for (let i = 0; i < 40; i++) cases['fuzz' + i] = rtree(i < 30 ? 12 : 58);
const out = {sizes: [[600, 600], [900, 500]], padding: 3, cases: {}};
for (const [name, spec] of Object.entries(cases)) {
  const c = {spec, packs: []};
  for (const size of out.sizes) {
    const root = hierarchy(spec, d => d.c).sum(d => d.v).sort((a, b) => b.value - a.value);
    pack().size(size).padding(out.padding)(root);
    const rows = []; root.eachBefore(n => rows.push([n.depth, n.x, n.y, n.r, n.value, n.data.n]));
    c.packs.push(rows);
  }
  out.cases[name] = c;
}
console.log(JSON.stringify(out));
