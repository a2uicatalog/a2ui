// Golden vectors for candlestick_chart's date axis, from the REAL d3-scale 4.0.2 scaleUtc (which uses d3-time 3.1.0 utcTicks and
// d3-time-format 4.1.0 utcFormat). Run from a scratch dir with those packages installed:
//   node candlestick_d3_golden_gen.mjs <scratch>/node_modules > candlestick_d3_golden.json
import { createRequire } from "node:module";
const nm = process.argv[2];
const { scaleUtc } = await import(nm + "/d3-scale/src/index.js");
const R = (s, e, n = 5) => {
  const sc = scaleUtc().domain([s, e]);
  const f = sc.tickFormat();
  const t = sc.ticks(n);
  return { start: s, stop: e, count: n, ticks: t.map(Number), labels: t.map(f) };
};
const D = (s) => Date.parse(s);
const golden = {
  ms: R(D("2024-03-05T10:00:00.000Z"), D("2024-03-05T10:00:00.004Z")),
  seconds: R(D("2024-03-05T10:00:00Z"), D("2024-03-05T10:00:40Z")),
  minutes: R(D("2024-03-05T10:00:00Z"), D("2024-03-05T10:45:00Z")),
  hours: R(D("2024-03-05T09:30:00Z"), D("2024-03-05T16:00:00Z")),
  hours_overnight: R(D("2024-03-05T09:30:00Z"), D("2024-03-06T16:00:00Z")),
  days_two_weeks: R(D("2024-02-26"), D("2024-03-08")),
  days_one_month: R(D("2024-02-01"), D("2024-03-01")),
  months_one_year: R(D("2023-01-02"), D("2023-12-29")),
  months_two_years: R(D("2022-06-01"), D("2024-05-31")),
  years_decade: R(D("2010-01-04"), D("2020-12-30")),
  years_century: R(D("1930-01-01"), D("2024-01-01")),
  leap_day: R(D("2024-02-27"), D("2024-03-02")),
  year_boundary: R(D("2023-12-20"), D("2024-01-12")),
  weekly_span: R(D("2024-01-01"), D("2024-02-15")),
  pre_epoch: R(D("1965-03-01"), D("1965-09-30")),
  same_instant: R(D("2024-05-05"), D("2024-05-05")),
  count3: R(D("2024-01-01"), D("2024-06-30"), 3),
  count8: R(D("2024-01-01"), D("2024-06-30"), 8),
};
let seed = 12345;
const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
const fuzz = [];
for (let i = 0; i < 70; i++) {
  const span = Math.pow(10, 3 + rnd() * 11.2); // 1 s .. ~1.6e14 ms (5000 years is too wide; capped by year range below)
  const s = Date.UTC(1900, 0, 1) + Math.floor(rnd() * 3.8e12);
  const e = s + Math.floor(Math.min(span, 4e12));
  fuzz.push(R(s, e, 3 + Math.floor(rnd() * 6)));
}
console.log(JSON.stringify({ golden, fuzz }));
