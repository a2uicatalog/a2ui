// usage: node polar_chart_d3_golden_gen.mjs /path/to/node_modules > polar_chart_d3_golden.json
// polar_chart: the radial axis is d3 nice(lo, hi, 4) over the data (or the given range) with ticks(); a point's radius is
// scaleLinear().domain([lo, hi]).range([0, R])(r), its angle is clockwise from twelve o'clock (d3 lineRadial's convention)
// = 90 - (rotation + direction * theta) degrees; a line is lineRadial() with defined() (points outside the range break the
// line) and curveLinearClosed for fill "toself". Paths use d3-path's default 3 digits; they are drawn inside translate(50 50).
const root = process.argv[2];
const {nice, ticks} = await import(root + '/d3-array/src/index.js');
const {scaleLinear} = await import(root + '/d3-scale/src/index.js');
const {lineRadial, curveLinearClosed} = await import(root + '/d3-shape/src/index.js');
let s = 7; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const R = 40;
function build(c) {
  const pts = c.r.map((r, i) => ({r, t: c.theta[i]}));
  const fin = pts.map(p => p.r);
  let lo, hi;
  if (c.range) { [lo, hi] = c.range; }
  else { lo = Math.min(0, ...fin); hi = Math.max(0, ...fin); [lo, hi] = nice(lo, hi, 4); }
  const tk = ticks(lo, hi, 4);
  const sc = scaleLinear().domain([lo, hi]).range([0, R]);
  const rot = c.rotation, dir = c.direction;
  const ang = pts.map(p => (90 - (rot + dir * p.t)) * Math.PI / 180);
  const rad = pts.map(p => sc(p.r));
  const inr = pts.map(p => p.r >= lo && p.r <= hi);
  const mk = (closed) => lineRadial().angle((d, i) => ang[i]).radius((d, i) => rad[i]).defined((d, i) => inr[i]);
  const open = mk(false)(pts.map((_, i) => i));
  const cl = lineRadial().curve(curveLinearClosed).angle((d, i) => ang[i]).radius((d, i) => rad[i]).defined((d, i) => inr[i])(pts.map((_, i) => i));
  return {...c, lo, hi, ticks: tk, angles: ang, radii: rad, open, closed: cl};
}
const cases = {
  radar6: {r: [4, 3, 5, 2, 4.5, 3.5], theta: [0, 60, 120, 180, 240, 300], rotation: 90, direction: -1},
  numeric_ccw: {r: [1, 2, 3, 4, 5], theta: [0, 45, 90, 135, 180], rotation: 0, direction: 1},
  negative_r: {r: [-3, 2, 5, -1], theta: [10, 100, 200, 300], rotation: 0, direction: 1},
  explicit_range: {r: [0.2, 0.9, 0.5, 1.4, 0.7], theta: [0, 72, 144, 216, 288], rotation: 90, direction: -1, range: [0, 1]},
  rotated: {r: [10, 20, 30], theta: [0, 120, 240], rotation: 45, direction: -1},
  decimals: {r: [0.1, 0.2, 0.30000000000000004, 0.4], theta: [0, 90, 180, 270], rotation: 0, direction: 1},
  big: {r: [1.2e6, 3.4e5, 8.9e5], theta: [15, 135, 255], rotation: 90, direction: -1},
  single: {r: [7], theta: [33], rotation: 0, direction: 1},
  gaps: {r: [1, 9, 2, 3, 9, 4], theta: [0, 50, 100, 150, 200, 250], rotation: 0, direction: 1, range: [0, 5]},
};
const fuzz = [];
for (let k = 0; k < 40; k++) {
  const n = 1 + Math.floor(rnd() * 12), sign = rnd() < 0.3;
  const r = [], theta = [];
  for (let i = 0; i < n; i++) { r.push(Math.round((rnd() * 100 - (sign ? 40 : 0)) * 100) / 100); theta.push(Math.round(rnd() * 72000) / 100 - 90); }
  const c = {r, theta, rotation: [0, 90, 45, -30][k % 4], direction: k % 2 ? -1 : 1};
  if (k % 5 === 0) c.range = [0, 50];
  fuzz.push(build(c));
}
console.log(JSON.stringify({golden: Object.fromEntries(Object.entries(cases).map(([k, v]) => [k, build(v)])), fuzz, R}));
