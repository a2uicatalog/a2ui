// usage: node chord_d3_golden_gen.mjs /path/to/d3-chord-3.0.1/src/index.js /path/to/d3-shape-3.2.0/src/index.js > chord_d3_golden.json
// chord_diagram: chord().padAngle(0.05).sortSubgroups(descending) and chordDirected() likewise, over hand cases and seeded fuzz.
// Per case and mode: the groups [index, startAngle, endAngle, value], the chords (in the order d3 returns them) as
// [source.index, source.startAngle, source.endAngle, source.value, target.index, ..., target.value], the group arcs of d3-shape arc() (innerRadius 175,
// outerRadius 190, no padAngle; 3 digits and full precision) and the ribbon path of ribbon() / ribbonArrow() at radius 174 with padAngle 1/175
// (full precision: d3-chord's ribbon uses a d3-path without a digits setting).
const {chord, chordDirected, ribbon, ribbonArrow} = await import(process.argv[2]);
const {arc} = await import(process.argv[3]);
const desc = (a, b) => a < b ? 1 : a > b ? -1 : a >= b ? 0 : NaN;
let s = 4242; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const cases = {
  two: [[0, 5], [3, 0]],
  two_symmetric: [[1, 4], [4, 1]],
  zero_row: [[0, 4, 0], [2, 0, 0], [0, 0, 0]],
  zero_row_first: [[0, 0, 0], [0, 3, 1], [0, 2, 5]],
  all_zero: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
  all_zero_two: [[0, 0], [0, 0]],
  self_loop: [[7, 2, 0], [2, 0, 1], [0, 1, 3]],
  only_self_loops: [[4, 0], [0, 6]],
  asymmetric: [[0, 10, 1, 0], [2, 0, 8, 3], [0, 6, 0, 9], [12, 0, 1, 0]],
  one_way: [[0, 9, 0], [0, 0, 4], [0, 0, 0]],
  ties: [[0, 3, 3, 3], [3, 0, 3, 3], [3, 3, 0, 3], [3, 3, 3, 0]],
  decimals: [[0, 0.5, 1.25], [0.75, 0, 0.1], [2.5, 0.3, 0]],
  tiny_and_huge: [[0, 1e9, 0.001], [1e-3, 0, 5], [2e8, 0, 0]],
  one_pair_only: [[0, 0, 0, 0], [0, 0, 0, 8], [0, 0, 0, 0], [0, 5, 0, 0]],
};
const mat = (n, density) => Array.from({length: n}, () => Array.from({length: n}, () => rnd() < density ? (rnd() < 0.3 ? Math.round(rnd() * 1000) / 100 : Math.floor(1 + rnd() * 300)) : 0));
cases.twelve = mat(12, 0.3);
cases.twelve_dense = mat(12, 0.65);
for (let i = 0; i < 16; i++) cases['fuzz' + i] = mat(2 + Math.floor(rnd() * 6), [0.2, 0.5, 0.8, 1][i % 4]);
const PAD = 0.05, IN = 175, OUT = 190, RR = IN - 1, RP = 1 / IN;
const mkArc = () => arc().innerRadius(IN).outerRadius(OUT);
const a3 = mkArc(), aN = mkArc().digits(null);
const out = {pad_angle: PAD, inner: IN, outer: OUT, ribbon_radius: RR, ribbon_pad: RP, cases: {}};
for (const [name, m] of Object.entries(cases)) {
  out.cases[name] = {matrix: m};
  for (const directed of [false, true]) {
    const ch = (directed ? chordDirected() : chord()).padAngle(PAD).sortSubgroups(desc)(m);
    const rb = (directed ? ribbonArrow() : ribbon()).radius(RR).padAngle(RP);
    const ends = e => [e.index, e.startAngle, e.endAngle, e.value];
    out.cases[name][directed ? 'directed' : 'undirected'] = {
      groups: ch.groups.map(g => [g.index, g.startAngle, g.endAngle, g.value]),
      chords: ch.map(c => ends(c.source).concat(ends(c.target))),
      arcs: ch.groups.map(g => [a3(g), aN(g)]),
      ribbons: ch.map(c => rb(c)),
    };
  }
}
console.log(JSON.stringify(out));
