// usage: node waterfall_d3_golden_gen.mjs /path/to/d3-array-3.2.4/package/src/index.js > waterfall_d3_golden.json
// waterfall: a delta step runs from the running total to running total + value; a total step runs from 0 to the running total
// (a total with its own value sets the running total to it). The shared axis is d3 nice(min, max, 5) over 0 and every bar end,
// and its ticks(x0, x1, 5). Sums are left to right in double precision, as both renderers do.
const {nice, ticks} = await import(process.argv[2]);
let s = 99; const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
const round = (x, d) => Math.round(x * 10**d) / 10**d;
function layout(steps) {
  let run = 0, lo = 0, hi = 0;
  const bars = steps.map(st => {
    let a, b;
    if (st.kind === 'total') { if (typeof st.value === 'number') run = st.value; a = 0; b = run; }
    else { a = run; run = run + st.value; b = run; }
    lo = Math.min(lo, a, b); hi = Math.max(hi, a, b);
    return [a, b];
  });
  const dom = nice(lo, hi, 5);
  return {steps, bars, domain: dom, ticks: ticks(dom[0], dom[1], 5)};
}
const D = (v) => ({value: v}), T = (v) => (v === undefined ? {kind: 'total'} : {kind: 'total', value: v});
const cases = {
  pnl: [T(120), D(40), D(-25), D(12.5), D(-7.25), T()],
  all_down: [T(100), D(-30), D(-30), D(-30), T()],
  crosses_zero: [D(20), D(-50), D(10), T()],
  only_deltas: [D(1), D(2), D(3)],
  decimals_noise: [D(0.1), D(0.2), T(), D(-0.3), T()],
  zeros: [D(0), D(0), T()],
  big: [T(1.2e6), D(3.4e5), D(-8.9e5), T()],
  tiny: [D(2e-4), D(-5e-5), D(1.25e-4), T()],
  checkpoint_mismatch: [T(100), D(10), T(120), D(-5), T()],
  twenty_four: Array.from({length: 24}, (_, i) => i % 6 === 5 ? T() : D(round((rnd() - 0.4) * 50, 1))),
};
const out = {};
for (const [name, st] of Object.entries(cases)) out[name] = layout(st);
const fuzz = [];
for (let i = 0; i < 40; i++) {
  const n = 1 + Math.floor(rnd() * 24), scale = Math.pow(10, Math.floor(rnd() * 10) - 4);
  fuzz.push(layout(Array.from({length: n}, () => rnd() < 0.15 ? (rnd() < 0.5 ? T() : T(round((rnd() - 0.3) * scale * 10, 3))) : D(rnd() < 0.5 ? (rnd() - 0.45) * scale : Math.round((rnd() - 0.45) * scale * 10)))));
}
console.log(JSON.stringify({golden: out, fuzz}));
