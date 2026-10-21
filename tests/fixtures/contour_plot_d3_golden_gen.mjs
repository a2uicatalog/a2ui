// usage: node contour_plot_d3_golden_gen.mjs /path/to/d3-contour-4.0.2/src/index.js /path/to/d3-array-3.2.4/src/index.js > contour_plot_d3_golden.json
// (both resolve from the same node_modules; d3-contour imports d3-array by its bare name)
// contour_plot: contours() marching squares of a value grid, and contourDensity() (a float32 grid of the points, blurred with d3-array blur2, then the same
// contours). The golden holds, for each case, the MultiPolygon coordinates per threshold, so both twins can be compared coordinate for coordinate.
const {contours, contourDensity} = await import(process.argv[2]);
const {blur2} = await import(process.argv[3]);

function lcg(seed) { let s = seed; return () => (s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296; }
const field = (w, h, f) => Array.from({length: w * h}, (_, i) => f(i % w, Math.floor(i / w)));
const g2 = (x, y, cx, cy, s, a) => a * Math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * s * s));

const grids = {};
grids.hill_6x5 = {w: 6, h: 5, values: field(6, 5, (x, y) => g2(x, y, 2.5, 2, 1.4, 10)), thresholds: null};
grids.two_peaks_with_crater = {w: 14, h: 10, values: field(14, 10, (x, y) => g2(x, y, 3.5, 4, 2, 9) + g2(x, y, 10, 5, 2.2, 7) - g2(x, y, 10, 5, 0.9, 6)), thresholds: null};
grids.saddle_9x9 = {w: 9, h: 9, values: field(9, 9, (x, y) => (x - 4) * (y - 4)), thresholds: 6};
grids.all_equal = {w: 4, h: 3, values: Array(12).fill(5), thresholds: null};
grids.integer_levels_8x8 = {w: 8, h: 8, values: field(8, 8, (x, y) => (x + y) % 5 + (x * y) % 3), thresholds: 5};
grids.minimal_2x2 = {w: 2, h: 2, values: [0, 1, 2, 3], thresholds: 3};
grids.smooth_30x20 = {w: 30, h: 20, values: field(30, 20, (x, y) => 20 + 12 * Math.sin(x / 5) * Math.cos(y / 4) + x * 0.2), thresholds: null};
grids.negatives_and_nulls = {w: 7, h: 6, values: field(7, 6, (x, y) => ((x * 7 + y * 3) % 11) - 5).map((v, i) => (i === 35 || i === 8 ? null : v)), thresholds: 7};
grids.null_first_of_last_row = {w: 5, h: 4, values: field(5, 4, (x, y) => x - 2 + y * 0.5).map((v, i) => (i === 15 ? null : v)), thresholds: 6};
grids.ring_with_hole_and_island = {w: 12, h: 12, values: field(12, 12, (x, y) => { const r = Math.hypot(x - 5.5, y - 5.5); return r < 1.2 ? 9 : r < 3.5 ? 1 : r < 5 ? 5 : 0; }), thresholds: 4};
grids.one_row_high = {w: 10, h: 2, values: [1, 5, 2, 8, 3, 9, 4, 7, 6, 0], thresholds: 5};
grids.sturges_default_100 = {w: 10, h: 10, values: field(10, 10, (x, y) => x * x + y), thresholds: null};
const r = lcg(4242);
for (let k = 0; k < 14; k++) {
  const w = 2 + Math.floor(r() * 8), h = 2 + Math.floor(r() * 8);
  const values = field(w, h, () => Math.round(r() * 1000) / 100 - 3).map(v => (r() < 0.06 ? null : v));
  grids['fuzz' + k] = {w, h, values, thresholds: r() < 0.3 ? null : 3 + Math.floor(r() * 8)};
}

const out = {grids: {}, density: {}, blur: []};
for (const [name, c] of Object.entries(grids)) {
  const cs = contours().size([c.w, c.h]);
  if (c.thresholds !== null) cs.thresholds(c.thresholds);
  const res = cs(c.values);
  out.grids[name] = {w: c.w, h: c.h, values: c.values, thresholds: c.thresholds, out: res.map(m => ({value: m.value, coordinates: m.coordinates}))};
}

function density(name, pts, W, H, bw, count) {
  const d = contourDensity().x(p => p[0]).y(p => p[1]).size([W, H]).bandwidth(bw);
  if (count !== null) d.thresholds(count);
  const res = d(pts);
  const peek = d.contours(pts);
  out.density[name] = {points: pts, W, H, bandwidth: bw, thresholds: count, max: peek.max, out: res.map(m => ({value: m.value, coordinates: m.coordinates}))};
}
const rr = lcg(99);
const cluster = (n, cx, cy, s) => Array.from({length: n}, () => [cx + (rr() + rr() + rr() - 1.5) * s, cy + (rr() + rr() + rr() - 1.5) * s]);
density('three_points_bw40_default', cluster(3, 300, 200, 80), 600, 400, 40, null);
density('one_cluster_bw30_8', cluster(30, 300, 200, 200), 600, 400, 30, 4);
density('small_bw5_5', cluster(8, 300, 200, 300), 600, 400, 5, 3);
density('wide_bw60_4', [...cluster(10, 150, 120, 200), ...cluster(10, 460, 300, 200)], 600, 400, 60, 2);
density('edges_and_duplicates', [[0, 0], [600, 400], [0, 400], [600, 0], [300, 200], [300, 200], [300, 200], [299.5, 200.25]], 600, 400, 12.5, 6);
density('single_point', [[300, 200]], 600, 400, 20, 3);
density('line_of_points', Array.from({length: 12}, (_, i) => [60 + i * 40, 200]), 600, 400, 15, 2);

// blur2 alone: integer and fractional radius, on a float32 array
const rb = lcg(7);
for (const [w, h, rad] of [[9, 7, 1], [9, 7, 2], [9, 7, 1.25], [20, 11, 0.6], [5, 5, 3.5], [13, 4, 8]]) {
  const a = new Float32Array(w * h).map(() => Math.round(rb() * 1000) / 7);
  const before = Array.from(a);
  blur2({data: a, width: w, height: h}, rad);
  out.blur.push({w, h, radius: rad, before, after: Array.from(a)});
}
console.log(JSON.stringify(out));
