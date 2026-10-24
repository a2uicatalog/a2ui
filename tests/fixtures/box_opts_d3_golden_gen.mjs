// usage: node box_opts_d3_golden_gen.mjs /path/to/d3-array-3.2.4/src/index.js > box_opts_d3_golden.json
// Quartiles for box_plot `quartile_method` from the real d3-array (linear = quantileSorted R-7; exclusive / inclusive = median of the lower / upper half,
// the middle value left out / kept for odd n), the sample deviation and the Gaussian KDE (mean of K((x - v) / h) / h, d3's kernel density example).
const {quantileSorted, median, deviation, mean, ascending} = await import(process.argv[2]);
const cases = {five: [1, 2, 3, 4, 5], six: [1, 2, 3, 4, 5, 100], seven: [2, 4, 4, 5, 7, 9, 12], eight: [3, 5, 6, 8, 9, 10, 15, 21], dup: [5, 5, 5, 5, 5, 9], neg: [-8, -3.5, -2, 0, 1.5, 2, 7, 11, 11.5]};
const K = u => 0.3989422804014327 * Math.exp(-0.5 * u * u);
const out = {};
for (const [name, v] of Object.entries(cases)) {
  const a = [...v].sort(ascending), n = a.length, h = n >> 1;
  const lowE = a.slice(0, h), upE = a.slice(n - h), lowI = a.slice(0, h + (n & 1)), upI = a.slice(n - h - (n & 1));
  const q1 = quantileSorted(a, 0.25), q3 = quantileSorted(a, 0.75), sd = deviation(a);
  const bw = (() => { const b = 0.9 * Math.min(sd, (q3 - q1) / 1.34) * Math.pow(n, -0.2); return b > 0 ? b : (a[n - 1] - a[0]) / 10 || 1; })();
  const grid = Array.from({length: 41}, (_, j) => a[0] + (a[n - 1] - a[0]) * j / 40);
  out[name] = {values: v, linear: [q1, median(a), q3], exclusive: [median(lowE), median(a), median(upE)], inclusive: [median(lowI), median(a), median(upI)],
    sd, bw, density: grid.map(x => mean(a, d => K((x - d) / bw) / bw))};
}
console.log(JSON.stringify(out));
