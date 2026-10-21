// usage: D3_DIR=/path/to/dir-with-node_modules node parallel_coords_d3_golden_gen.mjs > parallel_coords_d3_golden.json
// (D3_DIR/node_modules holds d3-scale 4.0.2, d3-shape 3.2.0 / d3-path 3.1.0, d3-array 3.2.4.)
// parallel_coords: each dimension is a scaleLinear().domain(nice(min, max, 5) or the explicit [min, max]).range([BOT, TOP]) (reversed: [TOP, BOT]);
// the axes sit at scalePoint().domain(0..n-1).range([0, 1000]).padding(0.5); each row is d3.line().digits(2) through (x_i, y_i).
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const imp = (m) => import(pathToFileURL(path.join(process.env.D3_DIR, 'node_modules', m, 'src/index.js')).href);
const {scaleLinear, scalePoint} = await imp('d3-scale');
const {line} = await imp('d3-shape');
const {ticks} = await imp('d3-array');
const VBW = 1000, TOP = 16, BOT = 244;
let s = 7; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const round = (x, d) => Math.round(x * 10**d) / 10**d;

function layout(dims) {
  // dims: [{values: [...], min?, max?, reverse?}], every row complete
  const n = dims.length, rows = dims[0].values.length;
  const xs = scalePoint().domain(dims.map((_, i) => i)).range([0, VBW]).padding(0.5);
  const axes = dims.map(d => {
    const explicit = typeof d.min === 'number' && typeof d.max === 'number' && d.min < d.max;
    const sc = scaleLinear().domain(explicit ? [d.min, d.max] : [Math.min(...d.values), Math.max(...d.values)]).range(d.reverse ? [TOP, BOT] : [BOT, TOP]);
    if (!explicit) sc.nice(5);
    return {domain: sc.domain(), ticks: sc.ticks(5), tickY: sc.ticks(5).map(t => sc(t)), sc};
  });
  const paths = [];
  const ys = [];
  for (let r = 0; r < rows; r++) {
    const pts = dims.map((d, i) => [xs(i), axes[i].sc(d.values[r])]);
    ys.push(pts.map(p => p[1]));
    paths.push(line().digits(2)(pts));
  }
  return {dims, xs: dims.map((_, i) => xs(i)), domains: axes.map(a => a.domain), ticks: axes.map(a => a.ticks), tickY: axes.map(a => a.tickY), ys, paths};
}
const mk = (cols, extra = []) => cols.map((v, i) => Object.assign({values: v}, extra[i] || {}));
const golden = {
  iris_like: layout(mk([[5.1, 4.9, 6.3, 5.8, 7.1], [3.5, 3.0, 3.3, 2.7, 3.0], [1.4, 1.4, 6.0, 5.1, 5.9], [0.2, 0.2, 2.5, 1.9, 2.1]])),
  two_dims: layout(mk([[1, 2, 3], [30, 10, 20]])),
  eight_dims: layout(mk(Array.from({length: 8}, (_, k) => [k, k * 2 + 1, 10 - k, 3.5]))),
  negatives: layout(mk([[-5, 0, 5], [-0.25, 0.5, 0.125]])),
  constant_axis: layout(mk([[4, 4, 4], [1, 2, 3]])),
  one_row: layout(mk([[10], [20], [30]])),
  explicit_range: layout(mk([[1, 2, 3], [0.1, 0.5, 0.9]], [{min: 0, max: 10}, {min: 0, max: 1, reverse: true}])),
  reversed: layout(mk([[1, 2, 3], [100, 250, 175]], [{reverse: true}, {reverse: true}])),
  huge: layout(mk([[1e9, 5e9, 12e9], [0.00001, 0.00005, 0.00009]])),
  noise: layout(mk([[0.1, 0.2, 0.30000000000000004], [1e-3, 2e-3, 3e-3]])),
  rounding_ties: layout(mk([[0, 1, 2, 3, 4, 5, 6, 7], [0.005, 0.015, 0.025, 0.035, 0.045, 0.055, 0.065, 0.075]])),
};
const fuzz = [];
for (let c = 0; c < 24; c++) {
  const n = 2 + Math.floor(rnd() * 7), rows = 1 + Math.floor(rnd() * 12), scale = [1, 0.01, 1000, 37.5][c % 4];
  const dims = Array.from({length: n}, () => {
    const off = (rnd() - 0.5) * 200 * scale, sp = (0.1 + rnd() * 100) * scale;
    return {values: Array.from({length: rows}, () => round(off + rnd() * sp, 3)), reverse: rnd() < 0.25};
  });
  fuzz.push(layout(dims));
}
console.log(JSON.stringify({golden, fuzz}));
