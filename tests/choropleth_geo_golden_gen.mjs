// Golden vectors for tests/test_choropleth_map.py, from the REAL d3-geo 3.1.1 (ISC). Run outside the repo:
//   mkdir /tmp/geo && cd /tmp/geo && npm i d3-geo@3.1.1 && node <repo>/tests/choropleth_geo_golden_gen.mjs > <repo>/tests/choropleth_geo_golden.json
import { createRequire } from 'node:module';
const require = createRequire(process.cwd() + '/');
const g = require('d3-geo');
const PTS = [[0, 0], [10, 20], [-73.9, 40.7], [139.7, 35.7], [-122.4, 37.8], [151.2, -33.9], [-179.5, 60], [179.5, -60], [2.35, 48.85], [30, 80], [-60, -50], [100, -80]];
const US = [[-98, 39], [-122.4, 37.8], [-74, 40.7], [-149.9, 61.2], [-157.8, 21.3], [-81.7, 27.8], [-68.9, 47.3], [-166, 65], [-170, 53], [-155.5, 19.6], [-87.6, 41.9], [10, 20], [-180, 60], [2.35, 48.85], [-100, 30], [-110, 25]];
const out = { equalEarth: [], mercator: [], albersUsa: [] };
const ee = g.geoEqualEarth().scale(177).translate([480, 240]);
for (const p of PTS) out.equalEarth.push({ in: p, out: ee(p) });
const mc = g.geoMercator().scale(300).translate([400, 300]).rotate([-10, 0]);
for (const p of PTS) out.mercator.push({ in: p, out: p[1] > 84 || p[1] < -84 ? null : mc(p) });
const au = g.geoAlbersUsa();
for (const p of US) out.albersUsa.push({ in: p, out: au(p) });
const au2 = g.geoAlbersUsa().scale(700).translate([300, 200]);
out.albersUsa2 = US.map((p) => ({ in: p, out: au2(p) }));
console.log(JSON.stringify(out));
