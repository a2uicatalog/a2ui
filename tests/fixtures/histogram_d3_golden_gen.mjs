// usage: node histogram_d3_golden_gen.mjs /path/to/d3-array-3.2.4/package/src/index.js > histogram_d3_golden_raw.json  (the fixture keeps golden + the first 30 fuzz cases)
const {bin, thresholdSturges} = await import(process.argv[2]);
// deterministic PRNG
let s = 12345; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const norm = () => { let u = 0; for (let i = 0; i < 12; i++) u += rnd(); return u - 6; };
const rl = (n, f) => Array.from({length: n}, f);
const round = (x, d) => Math.round(x * 10**d) / 10**d;
const cases = {
  small_ints: [1, 2, 2, 3, 3, 3, 4, 4, 5, 9],
  five_values: [10, 20, 30, 40, 50],
  all_equal: [7, 7, 7, 7, 7, 7],
  two_values: [0, 0, 0, 1, 1, 1],
  negatives: [-5, -3.5, -2, -0.5, 0, 1.5, 2.5, 4, 4.5, 8],
  decimals_small: rl(40, () => round(0.5 + norm() * 0.05, 3)),
  normalish_120: rl(120, () => round(100 + norm() * 15, 1)),
  skewed_300: rl(300, () => round(Math.exp(norm() * 0.6 + 3), 2)),
  bimodal_400: rl(400, () => round(rnd() < 0.55 ? 30 + norm() * 5 : 70 + norm() * 8, 1)),
  max_on_tick: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
  big_numbers: rl(60, () => Math.round(1e6 + norm() * 2.5e5)),
  tiny_numbers: rl(50, () => norm() * 1e-4),
  uniform_2000: rl(2000, () => round(rnd() * 1000, 2)),
  big_range: rl(80, () => round(Math.exp(norm()) * 1e5, 0)),
};
const out = {};
for (const [name, v] of Object.entries(cases)) {
  const variants = {auto: null, 40: 40, 3: 3, 7: 7};
  for (const [k, b] of Object.entries(variants)) {
    if (name.startsWith('uniform') && k !== 'auto' && k !== '40') continue;
    const h = bin().thresholds(b === null ? thresholdSturges : b);
    const bins = h(v);
    out[name + '@' + k] = {values: v, bins: b, edges: bins.map(x => [x.x0, x.x1]), counts: bins.map(x => x.length)};
  }
}
// random fuzz
const fuzz = [];
for (let i = 0; i < 400; i++) {
  const n = 5 + Math.floor(rnd() * 400), scale = Math.pow(10, Math.floor(rnd() * 12) - 5), off = (rnd() - 0.4) * scale * 50 * (rnd() < 0.5 ? 0 : 1);
  const kind = Math.floor(rnd() * 3);
  const v = rl(n, () => kind === 0 ? off + rnd() * scale * 10 : kind === 1 ? off + norm() * scale : Math.round(off + rnd() * scale * 10));
  const b = rnd() < 0.5 ? null : 3 + Math.floor(rnd() * 38);
  const bins = bin().thresholds(b === null ? thresholdSturges : b)(v);
  fuzz.push({values: v, bins: b, edges: bins.map(x => [x.x0, x.x1]), counts: bins.map(x => x.length)});
}
console.log(JSON.stringify({golden: out, fuzz}));
