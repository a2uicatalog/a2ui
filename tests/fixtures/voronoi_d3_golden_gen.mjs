// usage: node voronoi_d3_golden_gen.mjs /path/to/node_modules > voronoi_d3_golden.json
// where /path/to/node_modules holds d3-delaunay 6.0.4, delaunator 5.1.0 and robust-predicates 3.0.3 (d3-delaunay imports delaunator, delaunator imports
// robust-predicates, both by their bare names, so they must resolve from the same node_modules).
// voronoi: Delaunay.from(points).voronoi(bounds).cellPolygon(i). For every case the golden holds the REAL output: the triangles, halfedges and hull of d3-delaunay
// (which, for collinear input, are those of the re-triangulated jittered points, and the jittered points themselves), the raw Delaunator output of the
// original coordinates, and every cellPolygon (null where d3 gives none). Plus orient2d of robust-predicates on hand-made hard triples (the adaptive stages),
// and Math.sin / Math.cos / Math.hypot of this V8 for the jitter that d3-delaunay applies to collinear input.
const root = process.argv[2];
const {Delaunay} = await import(root + '/d3-delaunay/src/index.js');
const {default: Delaunator} = await import(root + '/delaunator/index.js');
const {orient2d} = await import(root + '/robust-predicates/esm/orient2d.js');

function lcg(seed) { let s = seed; return () => (s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296; }
const arr = a => Array.from(a);

function run(points, bounds) {
  const flat = []; for (const p of points) flat.push(p[0], p[1]);
  const raw = new Delaunator(Float64Array.from(flat));
  const d = Delaunay.from(points);
  const v = d.voronoi(bounds);
  const cells = [];
  for (let i = 0; i < points.length; i++) cells.push(v.cellPolygon(i));
  return {points, bounds,
    raw: {triangles: arr(raw.triangles), halfedges: arr(raw.halfedges), hull: arr(raw.hull)},
    triangles: arr(d.triangles), halfedges: arr(d.halfedges), hull: arr(d.hull), jittered: arr(d.points), cells};
}

const cases = {};
const sq = (x0, y0, x1, y1) => [x0, y0, x1, y1];
// ---- hand cases
cases.three_points = run([[2, 2], [8, 3], [5, 8]], sq(0, 0, 10, 10));
cases.three_points_cw = run([[2, 2], [5, 8], [8, 3]], sq(0, 0, 10, 10));
cases.two_points = run([[2, 2], [8, 6]], sq(0, 0, 10, 10));
cases.one_point = run([[3, 4]], sq(0, 0, 10, 10));
cases.same_point_twice = run([[3, 4], [3, 4]], sq(0, 0, 10, 10));
cases.collinear_horizontal = run([[1, 5], [4, 5], [9, 5]], sq(0, 0, 10, 10));
cases.collinear_diagonal = run([[1, 1], [3, 3], [4, 4], [8, 8]], sq(0, 0, 10, 10));
cases.collinear_vertical = run([[5, 1], [5, 3], [5, 4], [5, 9], [5, 6]], sq(0, 0, 10, 10));
cases.collinear_decimals = run([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8], [0.9, 1.0]], sq(0, 0, 1.2, 1.2));
cases.collinear_with_duplicate = run([[1, 5], [4, 5], [4, 5], [9, 5]], sq(0, 0, 10, 10));
cases.near_collinear = run([[0, 0], [5, 1e-9], [10, 0], [15, 2e-9]], sq(-1, -1, 16, 1));
cases.square_grid_4x4 = run(Array.from({length: 16}, (_, i) => [i % 4 * 2 + 1, Math.floor(i / 4) * 2 + 1]), sq(0, 0, 8, 8));
cases.square_grid_5x5 = run(Array.from({length: 25}, (_, i) => [i % 5, Math.floor(i / 5)]), sq(-1, -1, 5, 5));
cases.square_grid_3x3_tight_bounds = run(Array.from({length: 9}, (_, i) => [i % 3, Math.floor(i / 3)]), sq(0, 0, 2, 2));
cases.grid_with_hole = run(Array.from({length: 25}, (_, i) => [i % 5 * 10, Math.floor(i / 5) * 10]).filter((p, i) => i !== 12), sq(-5, -5, 45, 45));
cases.points_on_bounds = run([[0, 0], [10, 0], [0, 10], [10, 10], [5, 0], [5, 10], [0, 5], [10, 5], [5, 5]], sq(0, 0, 10, 10));
cases.points_on_bounds_edges_only = run([[0, 3], [10, 7], [4, 0], [6, 10]], sq(0, 0, 10, 10));
cases.points_outside_bounds = run([[-3, 4], [13, 5], [5, -4], [5, 14], [5, 5]], sq(0, 0, 10, 10));
cases.octagon_and_centre = run([[0, 0], ...Array.from({length: 8}, (_, k) => [Math.cos(k * Math.PI / 4) * 4, Math.sin(k * Math.PI / 4) * 4])], sq(-6, -6, 6, 6));
cases.right_triangle_with_circumcentre = run([[0, 0], [2, 0], [0, 2], [1, 1]], sq(-1, -1, 3, 3));
cases.right_triangle_with_circumcentre_big = run([[0, 0], [20, 0], [0, 20], [10, 10], [3, 4], [17, 2], [5, 15]], sq(-2, -2, 22, 22));
cases.tiny_sliver = run([[0, 0], [1000, 0.001], [500, 0.0004], [250, 3], [750, -2]], sq(-10, -10, 1010, 10));
cases.zero_size_bounds_width = run([[1, 1], [1, 2], [3, 5]], sq(2, 0, 2, 10));

const rnd = lcg(20261021);
cases.random_200 = run(Array.from({length: 200}, () => [rnd() * 1000, rnd() * 1000]), sq(0, 0, 1000, 1000));

// ---- seeded fuzz
const fz = lcg(5551212);
const fuzz = [];
for (let k = 0; k < 44; k++) {
  const n = 3 + Math.floor(fz() * 20), mode = k % 8;
  let pts;
  if (mode === 0) pts = Array.from({length: n}, () => [Math.floor(fz() * 6), Math.floor(fz() * 6)]);                                  // small integer grid: duplicates and cocircular ties
  else if (mode === 1) pts = Array.from({length: n}, () => [fz() * 100, fz() * 100]);
  else if (mode === 2) pts = Array.from({length: n}, () => [Math.round(fz() * 1000) / 10, Math.round(fz() * 1000) / 10]);
  else if (mode === 3) { const a = fz() * 2 - 1, c = fz() * 50; pts = Array.from({length: n}, () => { const x = fz() * 100; return [x, a * x + c + (fz() - 0.5) * 1e-7]; }); }   // near collinear
  else if (mode === 4) pts = Array.from({length: n}, () => [1e6 + fz() * 30, 2e6 + fz() * 30]);                                       // far from the origin
  else if (mode === 5) pts = Array.from({length: n}, () => [fz() * 1e-6, fz() * 1e-6]);                                               // tiny scale
  else if (mode === 6) { const cx = [20, 70, 45], cy = [30, 60, 80]; pts = Array.from({length: n}, (_, i) => [cx[i % 3] + (fz() + fz() - 1) * 6, cy[i % 3] + (fz() + fz() - 1) * 6]); }   // clusters
  else { const m = 2 + Math.floor(fz() * 5); pts = Array.from({length: n}, () => [Math.floor(fz() * m) * 7.5, Math.floor(fz() * 3) * 7.5]); }     // a few rows: many collinear runs and duplicates
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys), mx = (x1 - x0) * 0.1 + 1e-9, my = (y1 - y0) * 0.1 + 1e-9;
  const bounds = mode === 3 && k % 16 === 3 ? sq(x0, y0, x1, y1) : sq(x0 - mx, y0 - my, x1 + mx, y1 + my);                            // sometimes the bounds are the sites' own extent
  fuzz.push(run(pts, bounds));
}

// ---- orient2d: hard triples (the adaptive stages)
const orient = [];
const o = (a, b, c) => orient.push([a[0], a[1], b[0], b[1], c[0], c[1], orient2d(a[0], a[1], b[0], b[1], c[0], c[1])]);
const ulp = x => { const b = new DataView(new ArrayBuffer(8)); b.setFloat64(0, x); b.setBigUint64(0, b.getBigUint64(0) + 1n); return b.getFloat64(0) - x; };
const ro = lcg(77);
for (let k = 0; k < 40; k++) o([ro() * 10, ro() * 10], [ro() * 10, ro() * 10], [ro() * 10, ro() * 10]);                              // generic: the fast filter
for (let k = 0; k < 20; k++) { const a = [Math.floor(ro() * 20), Math.floor(ro() * 20)], t = Math.floor(ro() * 5) + 1, dx = Math.floor(ro() * 7) - 3, dy = Math.floor(ro() * 7) - 3; o(a, [a[0] + dx, a[1] + dy], [a[0] + t * dx, a[1] + t * dy]); }   // exactly collinear
// Kettner et al.: p = (0.5 + i u, 0.5 + j u) against the line through (12, 12) and (24, 24)
for (let i = 0; i < 12; i++) for (let j = 0; j < 12; j++) { const u = Math.pow(2, -53); o([0.5 + i * u, 0.5 + j * u], [12, 12], [24, 24]); }
for (let k = 0; k < 120; k++) {                                                                                                      // near collinear: c on ab, nudged by a few ulps
  const s = [1, 1e-3, 1e5, 1e-8][k % 4], a = [ro() * s, ro() * s], b = [ro() * s, ro() * s], t = ro() * 3 - 1;
  const c = [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])];
  const nx = Math.floor(ro() * 7) - 3, ny = Math.floor(ro() * 7) - 3;
  c[0] += nx * ulp(c[0]); c[1] += ny * ulp(c[1]);
  o(a, b, c);
}
for (let k = 0; k < 40; k++) {                                                                                                       // points with long mantissas on a line through the origin, nudged by ulps
  const a = [ro(), ro()], m = [ro() * 4 + 1, ro() * 4 + 1], b = [a[0] * m[0], a[1] * m[0]], c = [a[0] * m[1], a[1] * m[1]];
  c[1] += (Math.floor(ro() * 5) - 2) * ulp(c[1]);
  o(a, b, c);
}
o([1e150, 1e150], [-1e150, 1e150], [0, -1e150]);
o([5e-324, 0], [0, 5e-324], [5e-324, 5e-324]);
o([0, 0], [0, 0], [0, 0]);

// ---- trig and hypot as this V8 gives them (d3-delaunay's jitter uses sin, cos and hypot)
const rt = lcg(31337), trig = [];
for (let k = 0; k < 400; k++) {
  const x = (rt() - 0.5) * (k % 5 === 0 ? 2e6 : k % 5 === 1 ? 2e3 : k % 5 === 2 ? 20 : k % 5 === 3 ? 4 : 1e-3);
  trig.push([x, Math.sin(x), Math.cos(x)]);
}
for (const x of [0, 0.5, 0.7853981633974483, 0.7853981633974484, 1.5707963267948966, 3.141592653589793, 4.71238898038469, 6.283185307179586, 9.42477796076938, 100, 1e5, 1.5e6, 1.6e6, -1e5, -0.3, 2.356194490192345, 25.132741228718345, 31.41592653589793, 1e-9, 5e-10])
  trig.push([x, Math.sin(x), Math.cos(x)]);
for (let k = 1; k < 32; k++) { const x = k * Math.PI / 2; for (const e of [-1e-9, 0, 1e-9]) trig.push([x + e, Math.sin(x + e), Math.cos(x + e)]); }
const hyp = [], rh = lcg(99);
for (let k = 0; k < 300; k++) { const s = [1, 1e3, 1e-4, 1e8][k % 4]; const dx = (rh() - 0.3) * s, dy = (rh() - 0.5) * s * (k % 7 === 0 ? 0 : 1); hyp.push([dx, dy, Math.hypot(dx, dy)]); }
hyp.push([0, 0, 0], [3, 4, 5], [0, 7, 7], [1e300, 1e300, Math.hypot(1e300, 1e300)]);

process.stdout.write(JSON.stringify({cases, fuzz, orient, trig, hypot: hyp}));
