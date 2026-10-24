// usage (from a dir where d3-scale 4.0.2 and d3-array 3.2.4 are installed): node quiver_d3_golden_gen.mjs > quiver_d3_golden.json
// quiver axis: scaleLinear().domain([min, max]).nice(5) gives the axis domain, .ticks(5) its ticks, and scaleLinear().domain(dom)
// .range([r0, r1]) places each value. ternary_plot ticks: scaleLinear().domain([0, 1]).ticks(5).
import {scaleLinear} from 'd3-scale';
let s = 4242; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const rl = (n, f) => Array.from({length: n}, f);
const round = (x, d) => Math.round(x * 10**d) / 10**d;
const cases = {
  grid: [0, 1, 2, 3, 4, 5, 6, 7, 8],
  negative: [-3.5, -1, 0, 2.25, 4],
  fractional: rl(20, () => round(rnd() * 0.9, 3)),
  big: [1.5e6, 2.2e6, 9.9e6, 4.1e6],
  tiny: rl(10, () => round(rnd() * 1e-4, 7)),
  one_value: [7],
  two_equal: [3, 3],
  wide: [-1e9, 1e9, 5],
  random: rl(40, () => round(rnd() * 200 - 50, 2)),
};
const R0 = 65, R1 = 935, Y0 = 555, Y1 = 65, out = {};
for (const [k, v] of Object.entries(cases)) {
  const lo = Math.min(...v), hi = Math.max(...v);
  const sc = scaleLinear().domain([lo, hi]).nice(5), dom = sc.domain();
  const m = scaleLinear().domain(dom).range([R0, R1]);
  out[k] = {values: v, domain: dom, ticks: scaleLinear().domain(dom).ticks(5), mapped: v.map(x => m(x)), r0: R0, r1: R1, mapped_y: v.map(x => scaleLinear().domain(dom).range([Y0, Y1])(x)), y0: Y0, y1: Y1};
}
out.ternary_ticks = scaleLinear().domain([0, 1]).ticks(5);
console.log(JSON.stringify(out));
