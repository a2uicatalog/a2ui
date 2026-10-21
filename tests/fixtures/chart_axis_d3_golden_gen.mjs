// usage: node chart_axis_d3_golden_gen.mjs <scratch>/node_modules > chart_axis_d3_golden.json
// scratch: `npm i d3-format@3.1.0 d3-scale@4.0.2 d3-array@3.2.4` OUTSIDE the repo.
const nm = process.argv[2];
const {format} = await import(nm + '/d3-format/src/index.js');
const {scaleLog, scaleLinear} = await import(nm + '/d3-scale/src/index.js');
const SPECS = ['.20f', '.16f', '.20%', '.18%', ',.0f', '.1f', '.2f', 'f', ',.2f', '.0f', 'd', ',d', '+d', '.0%', '.1%', '%', '+.1%', 's', '.2s', '.3s', '.1s', '~s', '.3~s', '.2~f', '~f', ',.3~f', '$,.2f', '$.0f', '+.1f', '(.1f', ' .1f', '08.2f', '010,.1f', '10.1f', '<10.1f', '^10.1f', '>10,.1f', '=+10.1f', '*^12,.2f', 'e', '.2e', '.3~e', '~%', '.1~%', '$.2s', '$~s', '.4g', '.3g', '~g', ',.0d', '.2f%', 'x', '.0s'];
const VALS = [0, -0, 1, -1, 0.5, -0.5, 1.5, 2.5, 0.005, 0.015, 0.045, 1234.5678, -1234.5678, 999.5, 999999, 1e6, 1.5e6, 12345678, 1e9, 2.5e12, 0.00012, -0.00012, 1e-7, 123, 99.995, 0.1, 0.2 + 0.1, 1e21, 7, 1000, 0.999, 4.35, 1.005, 2e-9, 123456789012];
const fmt = {};
for (const s of SPECS) { fmt[s] = []; for (const v of VALS) { try { fmt[s].push(format(s)(v)); } catch (e) { fmt[s].push(null); } } }
const DOMS = [[1, 1000], [1, 10], [0.01, 500], [3, 3000], [1, 1e9], [2, 7], [1, 50], [0.001, 0.1], [5, 6], [10, 100], [0.5, 2e4], [1, 1e15], [250, 98000], [1, 3]];
const COUNTS = [2, 3, 5, 8, 10];
const logTicks = [];
for (const d of DOMS) for (const c of COUNTS) for (const rev of [false, true]) {
  const dom = rev ? [d[1], d[0]] : d;
  logTicks.push({domain: dom, count: c, ticks: scaleLog().domain(dom).ticks(c), nice: scaleLog().domain(dom).nice().domain()});
}
const LD = [[0, 100], [0, 1], [0, 7], [0, 1234], [-5, 40], [-1000, 250], [0, 0.0042], [3, 3.2], [0, 1e6], [-0.5, 0.5], [12, 987], [0, 1e-9], [100, 100]];
const linear = [];
for (const d of LD) for (const c of [2, 3, 5, 8, 10]) {
  const s = scaleLinear().domain(d);
  const t = s.ticks(c);
  const n = scaleLinear().domain(d).nice(c);
  linear.push({domain: d, count: c, ticks: t, nice: n.domain(), niceTicks: n.ticks(c)});
}
console.log(JSON.stringify({vals: VALS.map(v => Object.is(v, -0) ? '-0' : v), formats: fmt, logTicks, linear}));
