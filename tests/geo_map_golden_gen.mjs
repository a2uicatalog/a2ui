// Golden vectors for tests/test_geo_map.py, from the REAL d3-geo 3.1.1 (ISC): geoInterpolate (great-circle points) and geoDistance. Run outside the repo:
//   mkdir /tmp/geo && cd /tmp/geo && npm i d3-geo@3.1.1 && node <repo>/tests/geo_map_golden_gen.mjs > <repo>/tests/geo_map_golden.json
import { createRequire } from 'node:module';
const require = createRequire(process.cwd() + '/');
const g = require('d3-geo');
const PAIRS = [[[0, 0], [90, 0]], [[-73.9, 40.7], [2.35, 48.85]], [[139.7, 35.7], [-122.4, 37.8]], [[151.2, -33.9], [-70.6, -33.4]], [[10, 20], [10, 20]], [[0, 0], [179, 1]], [[-170, 60], [170, 60]], [[0, 80], [180, 80]]];
const out = PAIRS.map(([a, b]) => { const f = g.geoInterpolate(a, b); return { a, b, d: f.distance, pts: [0, 0.125, 0.25, 0.5, 0.75, 1].map((t) => ({ t, p: f(t) })) }; });
console.log(JSON.stringify(out));
