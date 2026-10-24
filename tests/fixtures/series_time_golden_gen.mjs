// Golden vectors for the scatter/line `series[]` date axis (renderers: _ps_* in web_article.py, _ps* in atoms_unstub_series.gs).
// Run from a scratch dir where `npm i d3-scale@4.0.2 d3-time@3.1.0 d3-time-format@4.1.0` was done:
//   cp tests/fixtures/series_time_golden_gen.mjs <scratch>/ && (cd <scratch> && node series_time_golden_gen.mjs) > tests/fixtures/series_time_golden.json
import { scaleUtc } from "d3-scale";
import { utcFormat } from "d3-time-format";
import { utcSecond, utcMinute, utcHour, utcDay, utcWeek, utcMonth, utcYear } from "d3-time";

const SPECS = ["%Y", "%y", "%m", "%d", "%e", "%H", "%I", "%p", "%M", "%S", "%L", "%b", "%B", "%a", "%A", "%j", "%%", "%Y-%m-%d", "%Y-%m-%d %H:%M"];
let s = 12345;
const rnd = () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648;
const tuples = [[1970,1,1,0,0,0,0],[2000,2,29,23,59,59,999],[1999,12,31,12,0,0,0],[2024,2,29,0,0,0,0],[1900,3,1,5,6,7,8],[2100,12,31,23,0,1,2],[1,1,1,0,0,0,0],[9999,12,31,23,59,59,999],[1969,12,31,23,59,59,999],[2026,10,21,9,30,0,0]];
for (let i = 0; i < 60; i++) tuples.push([1600 + Math.floor(rnd() * 800), 1 + Math.floor(rnd() * 12), 1 + Math.floor(rnd() * 28), Math.floor(rnd() * 24), Math.floor(rnd() * 60), Math.floor(rnd() * 60), Math.floor(rnd() * 1000)]);
const p2 = (n, w = 2) => String(n).padStart(w, "0");
const fmt = [];
for (const t of tuples) {
  const d = new Date(0); d.setUTCFullYear(t[0], t[1] - 1, t[2]); d.setUTCHours(t[3], t[4], t[5], t[6]);
  const iso = `${t[0] < 1000 ? p2(t[0], 4) : t[0]}-${p2(t[1])}-${p2(t[2])}T${p2(t[3])}:${p2(t[4])}:${p2(t[5])}.${p2(t[6], 3)}Z`;
  fmt.push({ iso, ms: +d, out: Object.fromEntries(SPECS.map(sp => [sp, utcFormat(sp)(d)])) });
}
const fm = { ms: utcFormat(".%L"), s: utcFormat(":%S"), mi: utcFormat("%I:%M"), h: utcFormat("%I %p"), d: utcFormat("%a %d"), w: utcFormat("%b %d"), mo: utcFormat("%b"), y: utcFormat("%Y") };
// d3's default multi-scale tickFormat, with %B (month) shortened to %b so labels stay narrow
const tickFormat = date => (utcSecond(date) < date ? fm.ms : utcMinute(date) < date ? fm.s : utcHour(date) < date ? fm.mi : utcDay(date) < date ? fm.h : utcMonth(date) < date ? (utcWeek(date) < date ? fm.d : fm.w) : utcYear(date) < date ? fm.mo : fm.y)(date);
const H = 3600e3, D = 24 * H;
const bases = [0, Date.UTC(2020, 0, 1), Date.UTC(2024, 1, 28, 13, 7, 3), Date.UTC(1999, 11, 31, 23, 59, 30), Date.UTC(2026, 9, 21, 9, 30), Date.UTC(1850, 5, 15), Date.UTC(2200, 0, 1)];
const spans = [500, 4e3, 30e3, 2 * 60e3, 20 * 60e3, 3 * H, 14 * H, 3 * D, 20 * D, 90 * D, 300 * D, 900 * D, 5000 * D, 40000 * D, 200000 * D];
const ticks = [];
for (const b of bases) for (const sp of spans) for (const c of [2, 4, 6]) {
  const a = b, z = b + sp;
  const sc = scaleUtc().domain([new Date(a), new Date(z)]);
  const t = sc.ticks(c).map(d => +d);
  ticks.push({ a, z, count: c, ticks: t, labels: t.map(x => tickFormat(new Date(x))) });
}
// reversed and degenerate domains
for (const [a, z] of [[Date.UTC(2020, 0, 1), Date.UTC(2020, 0, 1)], [Date.UTC(2021, 0, 1), Date.UTC(2020, 0, 1)]]) {
  const sc = scaleUtc().domain([new Date(a), new Date(z)]);
  const t = sc.ticks(4).map(d => +d); ticks.push({ a, z, count: 4, ticks: t, labels: t.map(x => tickFormat(new Date(x))) });
}
console.log(JSON.stringify({ specs: SPECS, fmt, ticks }));
