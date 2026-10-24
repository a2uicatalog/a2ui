// usage: node splom_parcats_d3_golden_gen.mjs /path/to/d3-array-3.2.4/src/index.js > splom_parcats_d3_golden.json
// scatter_matrix: each dimension's shared axis is d3 nice(min, max, 4) and ticks(x0, x1, 4) over that dimension's values.
// parallel_categories: category counts per dimension and joint counts between adjacent dimensions come from d3.rollup();
// categories rank by count descending then first appearance; past 8 the rest are grouped as "Other" (last).
const {nice, ticks, rollup, extent} = await import(process.argv[2]);
let s = 7; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const round = (x, d) => Math.round(x * 10**d) / 10**d;
const axis = (vals) => { const [lo, hi] = extent(vals); const d = nice(lo, hi, 4); return {values: vals, domain: d, ticks: ticks(d[0], d[1], 4)}; };
const axes = {
  small: [3, 1, 4, 1, 5, 9, 2, 6],
  negatives: [-12.5, 3, 7.25, -0.5, 18],
  equal: [5, 5, 5],
  tiny: [2e-4, -5e-5, 1.25e-4, 9e-5],
  big: [1.2e6, 3.4e5, -8.9e5, 2e6],
  fuzz: Array.from({length: 60}, () => round((rnd() - 0.4) * Math.pow(10, Math.floor(rnd() * 8) - 3), 4)),
};
const axisOut = {};
for (const [k, v] of Object.entries(axes)) axisOut[k] = axis(v);
const MAXC = 8;
function model(cols) {
  const n = cols[0].length;
  const cats = cols.map(col => {
    const m = rollup(col, v => v.length, d => d);            // insertion order = first appearance
    const first = new Map(); col.forEach((c, i) => { if (!first.has(c)) first.set(c, i); });
    const ranked = [...m.entries()].sort((a, b) => b[1] - a[1] || first.get(a[0]) - first.get(b[0]));
    const keep = ranked.slice(0, MAXC), rest = ranked.slice(MAXC);
    const out = keep.map(([name, count]) => ({name, count}));
    if (rest.length) out.push({name: 'Other', count: rest.reduce((t, [, c]) => t + c, 0), merged: rest.length});
    return out;
  });
  const idx = cols.map((col, j) => { const pos = new Map(cats[j].map((c, i) => [c.name, i])); return col.map(c => pos.has(c) ? pos.get(c) : cats[j].length - 1); });
  const joint = [];
  for (let j = 0; j + 1 < cols.length; j++) {
    const m = rollup(idx[j].map((a, i) => [a, idx[j + 1][i]]), v => v.length, d => d[0], d => d[1]);
    joint.push(cats[j].map((_, a) => cats[j + 1].map((_, b) => (m.get(a) && m.get(a).get(b)) || 0)));
  }
  return {cols, n, cats, joint};
}
const pick = (a, p) => a[Math.min(a.length - 1, Math.floor(p * a.length))];
const mk = (n, f) => Array.from({length: n}, (_, i) => f(i));
const cat = {
  tiny: [['a', 'b', 'a', 'a'], ['x', 'x', 'y', 'x']],
  three: [['red', 'blue', 'red', 'green', 'blue', 'red'], ['s', 'm', 'l', 's', 'm', 's'], ['yes', 'no', 'yes', 'no', 'no', 'yes']],
  ties: [['b', 'a', 'b', 'a', 'c'], ['q', 'q', 'r', 'r', 'q']],
  numeric_like: [['10', '2', '10', '1', '2', '10'], ['1', '1', '2', '2', '1', '1']],
  other: [mk(40, i => 'c' + (i % 12 + (i % 5 === 0 ? 0 : 0))), mk(40, i => 'd' + (i % 3))],
  fuzz: [mk(300, () => pick(['a','b','c','d','e','f','g','h','i','j','k'], rnd() ** 2)), mk(300, () => pick(['u','v','w','x'], rnd())), mk(300, () => pick(['p','q','r'], rnd() ** 0.5)), mk(300, () => pick(['m1','m2','m3','m4','m5','m6','m7','m8','m9'], rnd()))],
};
const catOut = {};
for (const [k, v] of Object.entries(cat)) catOut[k] = model(v);
console.log(JSON.stringify({axes: axisOut, cats: catOut}));
