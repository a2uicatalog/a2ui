// usage: node box_plot_points_d3_golden_gen.mjs /path/to/d3-force-3.0.0/src/index.js > box_plot_points_d3_golden.json
// box_plot show_points: a beeswarm, as in the d3 beeswarm examples: forceSimulation(nodes).force("x", forceX(x).strength(1))
// .force("y", forceY(0).strength(1)).force("collide", forceCollide(RADIUS)).stop().tick(TICKS), on nodes with no x/y (d3's own
// phyllotaxis start) and the default LCG random source. `xs` are the x targets in pixels, `pos` is [x, y] per node.
const {forceSimulation, forceX, forceY, forceCollide} = await import(process.argv[2]);
const RADIUS = 3, TICKS = 120;
let s = 4242; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const norm = () => { let u = 0; for (let i = 0; i < 12; i++) u += rnd(); return u - 6; };
const rl = (n, f) => Array.from({length: n}, f);
const round = (x, d) => Math.round(x * 10**d) / 10**d;
function swarm(xs) {
  const nodes = xs.map(() => ({}));
  nodes.forEach((d, i) => { d.t = xs[i]; });
  const sim2 = forceSimulation(nodes).force("x", forceX(d => d.t).strength(1)).force("y", forceY(0).strength(1)).force("collide", forceCollide(RADIUS)).stop();
  sim2.tick(TICKS);
  return nodes.map(d => [d.x, d.y]);
}
const cases = {
  single: [90],
  pair_equal: [50, 50],
  five: [10, 40, 90, 120, 170],
  all_equal: rl(40, () => 90),
  normal30: rl(30, () => round(90 + norm() * 22, 2)),
  clustered100: rl(100, () => Math.round(90 + norm() * 6)),
  ties_and_gaps: rl(80, (_, i) => i % 4 === 0 ? 20 : i % 4 === 1 ? 20.5 : 150 + (i % 3)),
  skewed200: rl(200, () => round(Math.min(180, Math.exp(norm() * 0.7 + 3.5)), 2)),
  dense500: rl(500, () => round(90 + norm() * 30, 3)),
};
const golden = {};
for (const [name, xs] of Object.entries(cases)) golden[name] = {xs, pos: swarm(xs)};
const fuzz = [];
for (let i = 0; i < 25; i++) {
  const n = 1 + Math.floor(rnd() * 120), mode = Math.floor(rnd() * 3);
  const xs = rl(n, () => mode === 0 ? rnd() * 180 : mode === 1 ? Math.round(rnd() * 12) * 15 : 90 + norm() * 10);
  fuzz.push({xs, pos: swarm(xs)});
}
console.log(JSON.stringify({radius: RADIUS, ticks: TICKS, golden, fuzz}));
