// usage: node histogram2d_d3_golden_gen.mjs /path/to/d3-array-3.2.4/src/index.js > tests/fixtures/histogram2d_d3_golden.json
// d3.bin() run twice (once on x, once on y); the 2-D count of a cell is the number of points that landed in both bins.
const {bin, thresholdSturges} = await import(process.argv[2]);
let s = 777; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const norm = () => { let u = 0; for (let i = 0; i < 12; i++) u += rnd(); return u - 6; };
const rl = (n, f) => Array.from({length: n}, f);
const round = (x, d) => Math.round(x * 10**d) / 10**d;
function h2(x, y, nx, ny) {
  const idx = x.map((_, i) => i);
  const mk = (v, n) => bin().value(i => v[i]).thresholds(n === null ? thresholdSturges : n)(idx);
  const bx = mk(x, nx), by = mk(y, ny);
  const cx = new Map(), cy = new Map();
  bx.forEach((b, j) => b.forEach(i => cx.set(i, j)));
  by.forEach((b, j) => b.forEach(i => cy.set(i, j)));
  const counts = by.map(() => bx.map(() => 0));
  for (const i of idx) counts[cy.get(i)][cx.get(i)]++;
  return {x, y, nbinsx: nx, nbinsy: ny, xedges: bx.map(b => [b.x0, b.x1]), yedges: by.map(b => [b.x0, b.x1]), counts};
}
const cases = {
  tiny: [[1, 2, 2, 3, 4, 5], [5, 4, 4, 2, 1, 1]],
  all_equal: [[3, 3, 3, 3], [8, 8, 8, 8]],
  one_axis_flat: [[1, 2, 3, 4, 5, 6], [2, 2, 2, 2, 2, 2]],
  negatives: [[-5, -3.5, -2, -0.5, 0, 1.5, 2.5, 4], [4, 3, -1, -2, 0, 1, -4, -5]],
  max_on_tick: [[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0]],
  blob_200: [rl(200, () => round(50 + norm() * 8, 1)), rl(200, () => round(20 + norm() * 3, 2))],
  corr_500: (() => { const x = rl(500, () => round(norm() * 10, 2)); return [x, x.map(v => round(v * 0.7 + norm() * 4, 2))]; })(),
  big_scale: [rl(120, () => Math.round(1e6 + norm() * 2e5)), rl(120, () => round(norm() * 1e-4, 8))],
};
const out = {};
for (const [name, [x, y]] of Object.entries(cases))
  for (const [k, n] of Object.entries({auto: [null, null], '5x8': [5, 8], '20x20': [20, 20], '3x40': [3, 40]}))
    out[name + '@' + k] = h2(x, y, n[0], n[1]);
const fuzz = [];
for (let i = 0; i < 120; i++) {
  const n = 5 + Math.floor(rnd() * 200), sc = Math.pow(10, Math.floor(rnd() * 8) - 3);
  const x = rl(n, () => rnd() < 0.5 ? round(norm() * sc, 3) : Math.round(rnd() * 10) * sc);
  const y = rl(n, () => rnd() < 0.5 ? round(norm() * sc * 3, 3) : Math.round(rnd() * 7) * sc);
  fuzz.push(h2(x, y, rnd() < 0.5 ? null : 3 + Math.floor(rnd() * 30), rnd() < 0.5 ? null : 3 + Math.floor(rnd() * 30)));
}
console.log(JSON.stringify({golden: out, fuzz}));
