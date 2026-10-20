// usage (from a directory whose node_modules holds d3-shape 3.2.0 and d3-path):
//   node stacked_area_d3_golden_gen.mjs /path/to/node_modules/d3-shape/src/index.js > stacked_area_d3_golden.json
// For each dataset (series x points, non-negative finite numbers) and each offset the REAL d3.stack() is run and its [y0, y1]
// pairs are written per ORIGINAL series index, together with the order d3 used.
// none/expand/silhouette use stackOrderNone; wiggle uses stackOrderInsideOut (the d3 streamgraph example); wiggle@none is kept as a reference.
const d3 = await import(process.argv[2]);
let s = 4242; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const rl = (n, f) => Array.from({length: n}, (_, i) => f(i));
const round = (x, d) => Math.round(x * 10**d) / 10**d;
const cases = {
  two_by_two: [[1, 2], [3, 1]],
  three_by_four: [[10, 25, 45, 60], [5, 5, 10, 20], [30, 20, 10, 5]],
  single_series: [[3, 1, 4, 1, 5, 9, 2, 6]],
  with_zero_column: [[0, 4, 0, 2], [0, 1, 0, 3], [0, 2, 0, 1]],
  zero_series: [[0, 0, 0, 0], [1, 2, 3, 4], [4, 3, 2, 1]],
  decimals: [[0.1, 0.25, 0.5, 0.75], [0.3, 0.1, 0.2, 0.05], [0.7, 0.9, 0.2, 0.3], [0.05, 0.05, 0.45, 0.8]],
  peaks_late: [[1, 1, 2, 9, 3], [8, 5, 2, 1, 1], [1, 3, 7, 2, 1], [2, 2, 2, 2, 12]],
  ties_in_peaks: [[5, 5, 5, 5], [5, 5, 5, 5], [1, 5, 1, 5], [5, 1, 5, 1]],
  huge_and_tiny: [[1e9, 2e9, 5e8], [1e-6, 3e-6, 2e-6], [123456.789, 98765.4321, 55555.5]],
  series_twelve_pts_ten: rl(12, i => rl(10, j => round(5 + 4 * Math.sin(j * 0.7 + i) + rnd() * 3, 3))),
  series_four_pts_forty: rl(4, i => rl(40, j => round(20 + 15 * Math.sin(j * 0.15 + i * 1.1) + rnd() * 6, 2))),
  integers_nine: rl(9, i => rl(7, j => Math.floor(rnd() * 100))),
};
const fuzz = [];
for (let k = 0; k < 14; k++) {
  const n = 1 + Math.floor(rnd() * 12), m = 2 + Math.floor(rnd() * 14), sc = Math.pow(10, Math.floor(rnd() * 8) - 3);
  fuzz.push(rl(n, () => rl(m, () => rnd() < 0.15 ? 0 : round(rnd() * sc, 4))));
}
function run(vals, offset) {
  const n = vals.length, m = vals[0].length;
  const data = rl(m, j => rl(n, i => vals[i][j]));
  const keys = rl(n, i => i);
  const st = d3.stack().keys(keys).value((d, key) => d[key]);
  const inside = offset === 'wiggle';
  st.offset({none: d3.stackOffsetNone, expand: d3.stackOffsetExpand, silhouette: d3.stackOffsetSilhouette, wiggle: d3.stackOffsetWiggle, 'wiggle@none': d3.stackOffsetWiggle}[offset]);
  st.order(inside ? d3.stackOrderInsideOut : d3.stackOrderNone);
  const out = st(data);
  const order = rl(n, i => 0); out.forEach((ser, i) => { order[ser.index] = i; });
  return {order, lo: out.map(ser => ser.map(p => p[0])), hi: out.map(ser => ser.map(p => p[1]))};
}
const res = {};
for (const [name, vals] of Object.entries(cases)) {
  res[name] = {values: vals};
  for (const off of ['none', 'expand', 'silhouette', 'wiggle', 'wiggle@none']) res[name][off] = run(vals, off);
}
const fz = fuzz.map(vals => { const o = {values: vals}; for (const off of ['none', 'expand', 'silhouette', 'wiggle']) o[off] = run(vals, off); return o; });
console.log(JSON.stringify({d3_shape: '3.2.0', golden: res, fuzz: fz}));
