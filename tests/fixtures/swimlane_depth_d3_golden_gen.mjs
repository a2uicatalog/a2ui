// usage: node swimlane_depth_d3_golden_gen.mjs /path/to/d3-sankey-0.12.3/src/index.js > swimlane_depth_d3_golden.json
// swimlane `layout: "auto"` puts each task in the column given by the longest path that reaches it from a task with no incoming link
// (the rule of d3-sankey's computeNodeDepths). Golden: node.depth from the REAL d3-sankey 0.12.3 sankey() on acyclic graphs.
// A cycle makes d3-sankey throw, so cycles are covered by hand-computed cases in tests/test_swimlane_links.py instead.
const {sankey} = await import(process.argv[2]);
let s = 20261021; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
function depths(n, edges) {
  const g = sankey().nodeId(d => d.index).nodeWidth(1).nodePadding(1).extent([[0, 0], [10, 10]]);
  const out = g({nodes: Array.from({length: n}, () => ({})), links: edges.map(([a, b]) => ({source: a, target: b, value: 1}))});
  return out.nodes.map(d => d.depth);
}
const hand = {
  chain: [4, [[0, 1], [1, 2], [2, 3]]],
  diamond: [4, [[0, 1], [0, 2], [1, 3], [2, 3]]],
  skip: [4, [[0, 1], [1, 2], [2, 3], [0, 3]]],
  isolated: [3, []],
  two_roots: [5, [[0, 2], [1, 2], [2, 3], [1, 4]]],
  unordered: [5, [[4, 3], [3, 2], [2, 1], [1, 0]]],
};
const cases = {};
for (const [k, [n, e]] of Object.entries(hand)) cases[k] = {n, edges: e, depth: depths(n, e)};
for (let i = 0; i < 60; i++) {
  const n = 1 + Math.floor(rnd() * 12), perm = Array.from({length: n}, (_, j) => j);
  for (let j = n - 1; j > 0; j--) { const r = Math.floor(rnd() * (j + 1)); [perm[j], perm[r]] = [perm[r], perm[j]]; }
  const edges = [], seen = new Set(), m = Math.floor(rnd() * (n * 2));
  for (let k = 0; k < m && n > 1; k++) {
    const a = Math.floor(rnd() * (n - 1)), b = a + 1 + Math.floor(rnd() * (n - 1 - a)), key = a + ',' + b;
    if (seen.has(key)) continue;
    seen.add(key); edges.push([perm[a], perm[b]]);
  }
  cases['fuzz' + i] = {n, edges, depth: depths(n, edges)};
}
console.log(JSON.stringify({source: 'd3-sankey 0.12.3 computeNodeDepths', cases}));
