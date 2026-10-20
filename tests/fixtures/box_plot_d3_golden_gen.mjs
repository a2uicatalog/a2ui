// usage: node box_plot_d3_golden_gen.mjs /path/to/d3-array-3.2.4/package/src/index.js > box_plot_d3_golden.json
// box_plot: quartiles are d3 quantileSorted (R-7) of each group's numbers sorted by d3.ascending; whiskers follow d3's box plot
// example (Tukey): the furthest numbers inside [q1 - 1.5 iqr, q3 + 1.5 iqr], the rest are outliers. The shared axis is
// d3 nice(min, max, 5) of all the groups' numbers and its ticks(x0, x1, 5).
const {quantileSorted, ascending, nice, ticks} = await import(process.argv[2]);
let s = 777; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const norm = () => { let u = 0; for (let i = 0; i < 12; i++) u += rnd(); return u - 6; };
const rl = (n, f) => Array.from({length: n}, f);
const round = (x, d) => Math.round(x * 10**d) / 10**d;
function stats(v) {
  const a = v.slice().sort(ascending);
  const q1 = quantileSorted(a, 0.25), med = quantileSorted(a, 0.5), q3 = quantileSorted(a, 0.75), r = 1.5 * (q3 - q1);
  const inside = a.filter(x => x >= q1 - r && x <= q3 + r);
  return {n: a.length, min: a[0], q1, median: med, q3, max: a[a.length - 1], lo: inside[0], hi: inside[inside.length - 1], outliers: a.filter(x => x < q1 - r || x > q3 + r)};
}
function box(groups) {
  const all = groups.flat(), dom = nice(Math.min(...all), Math.max(...all), 5);
  return {groups, stats: groups.map(stats), domain: dom, ticks: ticks(dom[0], dom[1], 5)};
}
const cases = {
  three: [rl(40, () => round(40 + norm() * 6, 1)), rl(60, () => round(55 + norm() * 9, 1)), rl(25, () => round(48 + norm() * 3, 1))],
  five_values: [[1, 2, 3, 4, 5]],
  six_values: [[1, 2, 3, 4, 5, 100]],
  all_equal: [[7, 7, 7, 7, 7]],
  outliers_both_sides: [[-50, 1, 2, 3, 3, 4, 4, 5, 6, 60, 61]],
  negatives: [rl(30, () => round(-10 + norm() * 4, 2)), rl(30, () => round(2 + norm() * 4, 2))],
  tiny: [rl(20, () => norm() * 1e-4), rl(20, () => 2e-4 + norm() * 5e-5)],
  big: [rl(50, () => Math.round(1e6 + norm() * 2e5))],
  skewed: [rl(200, () => round(Math.exp(norm() * 0.8 + 2), 2))],
  twelve: rl(12, (_, k) => rl(5 + k * 7, () => round(k * 2 + norm() * 3, 1))),
  zero_iqr: [[5, 5, 5, 5, 5, 5, 9, 1]],
};
const out = {};
for (const [name, g] of Object.entries(cases)) out[name] = box(g);
const fuzz = [];
for (let i = 0; i < 40; i++) {
  const k = 1 + Math.floor(rnd() * 6), scale = Math.pow(10, Math.floor(rnd() * 10) - 4);
  fuzz.push(box(rl(k, () => { const off = (rnd() - 0.5) * scale * 20; return rl(5 + Math.floor(rnd() * 150), () => rnd() < 0.5 ? off + norm() * scale : Math.round(off + rnd() * scale * 10)); })));
}
console.log(JSON.stringify({golden: out, fuzz}));
