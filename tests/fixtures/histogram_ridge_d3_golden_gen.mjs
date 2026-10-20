// usage: node histogram_ridge_d3_golden_gen.mjs /path/to/d3-array-3.2.4/package/src/index.js > histogram_ridge_d3_golden.json
// layout: ridge. The shared edges are d3's bin() of all the series pooled; each series is then counted by
// bin().domain([x0, x1]).thresholds(the pooled bin's inner edges), which is how d3 bins several series on common bins.
const {bin, thresholdSturges} = await import(process.argv[2]);
let s = 424242; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const norm = () => { let u = 0; for (let i = 0; i < 12; i++) u += rnd(); return u - 6; };
const rl = (n, f) => Array.from({length: n}, f);
const round = (x, d) => Math.round(x * 10**d) / 10**d;
function ridge(series, b) {
  const pooled = series.flat();
  const shared = bin().thresholds(b === null ? thresholdSturges : b)(pooled);
  const x0 = shared[0].x0, x1 = shared[shared.length - 1].x1, inner = shared.slice(1).map(x => x.x0);
  const one = bin().domain([x0, x1]).thresholds(inner);
  return {series, bins: b, edges: shared.map(x => [x.x0, x.x1]), counts: series.map(v => one(v).map(x => x.length))};
}
const cases = {
  three_shifted: [rl(120, () => round(40 + norm() * 6, 1)), rl(200, () => round(55 + norm() * 8, 1)), rl(80, () => round(70 + norm() * 5, 1))],
  one_series: [rl(60, () => round(10 + norm() * 2, 2))],
  unequal_sizes: [rl(12, () => round(rnd() * 100, 0)), rl(600, () => round(rnd() * 100, 2))],
  disjoint: [[1, 2, 3, 4, 5], [101, 102, 103, 104, 105]],
  all_equal: [[7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 7]],
  value_on_max_tick: [[0, 10, 20, 30, 40], [60, 70, 80, 90, 100]],
  negatives_and_tiny: [rl(40, () => norm() * 1e-3), rl(40, () => -0.002 + norm() * 5e-4)],
  eight_series: rl(8, (_, k) => rl(50 + k * 10, () => round(k * 3 + norm() * 4, 1))),
};
const out = {};
for (const [name, ser] of Object.entries(cases)) for (const b of [null, 3, 12, 40]) out[name + '@' + (b === null ? 'auto' : b)] = ridge(ser, b);
const fuzz = [];
for (let i = 0; i < 40; i++) {
  const k = 1 + Math.floor(rnd() * 8), scale = Math.pow(10, Math.floor(rnd() * 10) - 4);
  const ser = rl(k, () => { const off = (rnd() - 0.5) * scale * 20; return rl(5 + Math.floor(rnd() * 200), () => rnd() < 0.5 ? off + norm() * scale : Math.round(off + rnd() * scale * 10)); });
  fuzz.push(ridge(ser, rnd() < 0.5 ? null : 3 + Math.floor(rnd() * 38)));
}
console.log(JSON.stringify({golden: out, fuzz}));
