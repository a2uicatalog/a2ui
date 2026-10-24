// usage: node histogram_opts_d3_golden_gen.mjs /path/to/d3-array-3.2.4/src/index.js > histogram_opts_d3_golden.json
// Real d3-array bin().domain([start, end]).thresholds([interior edges]) for explicit bins (bin_size / bin_start / bin_end), plus
// the per-bin reductions the twins implement for `func` (d3.sum, d3.min, d3.max, d3.mean over the weights of the values in the bin).
const {bin, sum, min, max, mean} = await import(process.argv[2]);
const cases = {
  ints_size2: {values: [0, 1, 2, 2, 3, 4, 4, 4, 5, 9, 10], weights: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], start: 0, size: 2, end: 10},
  edge_right_closed: {values: [0, 5, 10, 10, 10, 2.5, 7.5], weights: [1, 1, 1, 1, 1, 1, 1], start: 0, size: 5, end: 10},
  outside_dropped: {values: [-3, -1, 0, 4, 8, 12, 99], weights: [1, 2, 3, 4, 5, 6, 7], start: 0, size: 4, end: 12},
  decimals: {values: [0.1, 0.2, 0.25, 0.3, 0.35, 0.5, 0.55, 0.9], weights: [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5], start: 0, size: 0.1, end: 1},
  negatives: {values: [-9, -7.5, -5, -5, -2.5, 0, 1, 2.2], weights: [-1, 2, -3, 4, -5, 6, -7, 8], start: -10, size: 2.5, end: 2.5},
  empty_bins: {values: [1, 1, 1, 9, 9, 9], weights: [3, 3, 3, 4, 4, 4], start: 0, size: 2, end: 10},
};
const out = {};
for (const [name, c] of Object.entries(cases)) {
  const nb = Math.ceil((c.end - c.start) / c.size);
  const t = []; for (let k = 0; k <= nb; k++) t.push(k === nb ? c.end : c.start + k * c.size);
  const idx = c.values.map((v, i) => i);
  const h = bin().domain([c.start, c.end]).thresholds(t.slice(1, nb)).value(i => c.values[i]);
  const bins = h(idx);
  out[name] = {...c, edges: bins.map(b => [b.x0, b.x1]), counts: bins.map(b => b.length),
    sum: bins.map(b => b.length ? sum(b, i => c.weights[i]) : null), min: bins.map(b => b.length ? min(b, i => c.weights[i]) : null),
    max: bins.map(b => b.length ? max(b, i => c.weights[i]) : null), avg: bins.map(b => b.length ? mean(b, i => c.weights[i]) : null)};
}
console.log(JSON.stringify(out));
