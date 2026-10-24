// Builds atoms/geo/*.json for the choropleth_map atom from world-atlas countries-110m and us-atlas states-10m (both ISC; the data is Natural Earth, public
// domain, and the US Census Bureau cartographic boundaries, public domain). Not part of any release path; run by hand:
//   mkdir /tmp/geo && cd /tmp/geo && npm i topojson-client world-atlas@2 us-atlas@3 i18n-iso-countries
//   node <repo>/scripts/build_choropleth_geo.mjs <repo>/atoms/geo
// Each region is {id, name, p}: p is a list of polygons, a polygon a list of rings, a ring a flat [lon, lat, lon, lat, ...] list rounded to 2 decimals
// (a 3-decimal-free, 1e-2 degree grid is ~1 km, far below the 110m scale). Rings are Douglas-Peucker simplified (tolerance TOL degrees) and rings that
// collapse below 4 points, or smaller than MINAREA square degrees, are dropped. Names and borders are Natural Earth as shipped, unchanged.
import { createRequire } from 'node:module';
import { writeFileSync } from 'node:fs';
const require = createRequire(process.cwd() + '/');
const topo = require('topojson-client');
const iso = require('i18n-iso-countries');
const world = require('world-atlas/countries-110m.json');
const us = require('us-atlas/states-10m.json');
const out = process.argv[2];
const r2 = (v) => Math.round(v * 100) / 100;

function dp(pts, tol) {
  if (pts.length < 3) return pts;
  const keep = new Uint8Array(pts.length);
  keep[0] = keep[pts.length - 1] = 1;
  const st = [[0, pts.length - 1]];
  while (st.length) {
    const [a, b] = st.pop();
    let md = 0, mi = -1;
    const [ax, ay] = pts[a], [bx, by] = pts[b];
    const dx = bx - ax, dy = by - ay, L = dx * dx + dy * dy;
    for (let i = a + 1; i < b; i++) {
      const [px, py] = pts[i];
      let d;
      if (L === 0) d = Math.hypot(px - ax, py - ay);
      else { const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / L)); d = Math.hypot(px - (ax + t * dx), py - (ay + t * dy)); }
      if (d > md) { md = d; mi = i; }
    }
    if (md > tol) { keep[mi] = 1; st.push([a, mi], [mi, b]); }
  }
  return pts.filter((_, i) => keep[i]);
}
function area(r) { let s = 0; for (let i = 0; i < r.length - 1; i++) s += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]; return Math.abs(s) / 2; }
// A ring that jumps more than 180 degrees of longitude between neighbours crosses the antimeridian: unwrap it, then cut it at +-180 (Sutherland-Hodgman) into pieces
// that each stay inside [-180, 180], so no edge of the drawing runs across the whole map.
function unwrap(r) {
  const o = [r[0].slice()];
  for (let i = 1; i < r.length; i++) {
    let x = r[i][0];
    const px = o[i - 1][0];
    while (x - px > 180) x -= 360;
    while (px - x > 180) x += 360;
    o.push([x, r[i][1]]);
  }
  return o;
}
function clipX(pts, edge, keepLess) {
  const out = [];
  const inside = (p) => (keepLess ? p[0] <= edge : p[0] >= edge);
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length];
    if (inside(a)) out.push(a);
    if (inside(a) !== inside(b)) { const t = (edge - a[0]) / (b[0] - a[0]); out.push([edge, a[1] + t * (b[1] - a[1])]); }
  }
  return out;
}
function split(r) {
  const u = unwrap(r.slice(0, -1));
  const xs = u.map((p) => p[0]);
  const lo = Math.min(...xs), hi = Math.max(...xs);
  if (lo >= -180 && hi <= 180) return [u];
  const res = [];
  const shift = lo < -180 ? 360 : -360;
  const inner = clipX(clipX(u, -180, false), 180, true);
  if (inner.length >= 3) res.push(inner);
  const edge = lo < -180 ? -180 : 180;
  const far = lo < -180 ? clipX(u, edge, true) : clipX(u, edge, false);
  if (far.length >= 3) res.push(far.map((p) => [p[0] + shift, p[1]]));
  return res;
}
function ring(r, tol, minArea) {
  if (area(r) < minArea) return null;
  const s = dp(r.slice(0, -1).concat([r[0]]), tol).map((p) => [r2(p[0]), r2(p[1])]);
  if (s.length < 4) return null;
  return s.flatMap((p) => p);
}
function polys(geom, tol, minArea) {
  const mp = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
  const res = [];
  for (const poly of mp) {
    const outer = split(poly[0]);
    const holes = poly.slice(1).flatMap((h) => split(h));
    outer.forEach((o, oi) => {
      const rings = [];
      const q = ring(o.concat([o[0]]), tol, minArea);
      if (!q) return;
      rings.push(q);
      if (oi === 0 || outer.length === 1) holes.forEach((h) => { const qh = ring(h.concat([h[0]]), tol, minArea * 4); if (qh) rings.push(qh); });
      res.push(rings);
    });
  }
  return res;
}

const NAME_FIX = {};
const wc = topo.feature(world, world.objects.countries).features.filter((f) => f.properties.name !== 'Antarctica');
const USER = { 'Kosovo': 'XKX', 'N. Cyprus': 'CYN', 'Somaliland': 'SOL' };
const countries = [];
for (const f of wc) {
  const id = f.id !== undefined ? iso.numericToAlpha3(String(f.id).padStart(3, '0')) : USER[f.properties.name];
  if (!id) throw new Error('no alpha-3 for ' + f.id + ' ' + f.properties.name);
  const p = polys(f.geometry, 0.06, 0.01);
  if (p.length) countries.push({ id, name: f.properties.name, p });
}
countries.sort((a, b) => (a.id < b.id ? -1 : 1));

const FIPS = { '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL', '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN', '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME', '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS', '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH', '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND', '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI', '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI', '56': 'WY' };
const states = [];
for (const f of topo.feature(us, us.objects.states).features) {
  const id = FIPS[f.id];
  if (!id) continue;
  states.push({ id, name: f.properties.name, p: polys(f.geometry, 0.05, 0.01) });
}
states.sort((a, b) => (a.id < b.id ? -1 : 1));

const EUROPE = 'ALB AND AUT BLR BEL BIH BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ITA XKX LVA LIE LTU LUX MLT MDA MNE NLD MKD NOR POL PRT ROU RUS SRB SVK SVN ESP SWE CHE TUR UKR GBR CYN'.split(' ');
const have = new Set(countries.map((c) => c.id));
const europe = EUROPE.filter((i) => have.has(i));

const meta = (set, src) => ({ set, source: src, regions: undefined });
// rings are written as centi-degree integer deltas (first pair absolute): "enc":"d100"; both loaders (web_article.py _ch_load, atoms_choropleth.gs _chDecode) turn them back into the same floats
const enc = (obj) => obj.regions ? { ...obj, enc: 'd100', regions: obj.regions.map((r) => ({ ...r, p: r.p.map((poly) => poly.map((ring) => { let px = 0, py = 0; const o = []; for (let i = 0; i < ring.length; i += 2) { const x = Math.round(ring[i] * 100), y = Math.round(ring[i + 1] * 100); o.push(x - px, y - py); px = x; py = y; } return o; })) })) } : obj;
const w = (name, obj) => { const s = JSON.stringify(enc(obj)); writeFileSync(out + '/' + name, s); console.log(name, s.length); };
w('world-countries.json', { set: 'world-countries', source: 'Natural Earth 110m via world-atlas@2 (ISC)', regions: countries });
w('us-states.json', { set: 'us-states', source: 'US Census cartographic boundaries 10m via us-atlas@3 (ISC)', regions: states });
w('europe-countries.json', { set: 'europe-countries', of: 'world-countries', ids: europe });
