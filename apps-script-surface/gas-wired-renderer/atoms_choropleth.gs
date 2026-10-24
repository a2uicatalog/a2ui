// ─────────────────────────────────────────────────────────────────
// choropleth_map (I41, 2026-10-21, stage: preview; D3 target, owner decision D10). Twin of the _render_choropleth_map block in renderers/web_article.py.
//
// Server-side SVG, one path per region, equal-interval quantized classes coloured from the theme tokens of the shared scale helpers (atoms_d3radial.gs:
// _CR_ACC, _CR_ACC2, _CR_SURF, _CR_TEXT, _CR_MUTED, _CR_SCHEMES, _crMix; atoms_chart_reading.gs: _CR_SR, _CR_BORDER, _CR_CB_CSS, _crCb, _crId, _crTrim, _crNum, _crS). The region outlines are the bundled sets in atoms_choropleth_data.gs (generated from atoms/geo; Natural Earth
// 110m via world-atlas and US Census 10m via us-atlas, both ISC; no custom GeoJSON). Projections are ports of d3-geo 3.1.1 (ISC, Mike Bostock): geoEqualEarth and
// geoAlbersUsa are here, geoMercator is _geoLib().merc (atoms_globe.gs); tests/test_choropleth_map.py checks all three against the real library to 1e-9.
// Vertices are projected only (no adaptive resampling, no clipping): the frame crops what lies outside it. This file is byte-identical in gas-wired-renderer and
// gas-schema-renderer (+ its .js mirror).
// ─────────────────────────────────────────────────────────────────

var _CH_SETS = ['world-countries', 'us-states', 'europe-countries'];
var _CH_PROJ = ['equal-earth', 'mercator', 'albers-usa'];
var _CH_EA = [1.340264, -0.081106, 0.000893, 0.003796];
var _CH_EA_M = Math.sqrt(3) / 2;
var _CH_D2R = Math.PI / 180, _CH_TAU = Math.PI * 2, _CH_EPS = 1e-6;
// Fit window [lon0, lon1, lat0, lat1] per set: only vertices inside it count when the frame is fitted (twin of _CH_WIN).
var _CH_WIN = { 'world-countries': [-180, 180, -58, 84], 'europe-countries': [-25, 45, 34, 72], 'us-states': [-180, -60, 15, 74] };

function _chRound(x) { var f = Math.floor(x); return x - f >= 0.5 ? f + 1 : f; }

// Legend break rounded to three significant digits (display only; class edges stay equal intervals).
function _chNice(x) {
  if (x === 0) return 0;
  var e = 2 - Math.floor(Math.log10(Math.abs(x))), m;
  if (e >= 0) { m = Math.pow(10, e); return Math.floor(x * m + 0.5) / m; }
  m = Math.pow(10, -e);
  return Math.floor(x / m + 0.5) * m;
}

// rings are stored as centi-degree integer deltas (first pair absolute); decode once, in place, to the same floats the old files held
function _chDecode() {
  if (_CH_GEO.__decoded) return;
  ['world-countries', 'us-states'].forEach(function(n) {
    _CH_GEO[n].regions.forEach(function(r) {
      r.p.forEach(function(poly) {
        poly.forEach(function(ring, k) {
          var ax = 0, ay = 0, out = [], i;
          for (i = 0; i < ring.length; i += 2) { ax += ring[i]; ay += ring[i + 1]; out.push(ax / 100, ay / 100); }
          poly[k] = out;
        });
      });
    });
  });
  _CH_GEO.__decoded = true;
}

function _chRegions(rset) {
  var out = [], src, i, ids, r;
  _chDecode();
  if (rset === 'europe-countries') {
    ids = {};
    _CH_GEO['europe-countries'].ids.forEach(function(x) { ids[x] = 1; });
    src = _CH_GEO['world-countries'].regions.filter(function(q) { return ids[q.id] === 1; });
  } else {
    src = _CH_GEO[rset].regions;
  }
  for (i = 0; i < src.length; i++) { r = src[i]; out.push([r.id, r.name, r.p]); }
  return out;
}

// d3.geoEqualEarth().scale(k).translate([tx, ty]) -> f(lon, lat) = [x, y].
function _chEqualEarth(k, tx, ty) {
  return function(lo, la) {
    var l = lo * _CH_D2R;
    if (Math.abs(l) > Math.PI) l -= Math.round(l / _CH_TAU) * _CH_TAU;
    var t = Math.asin(_CH_EA_M * Math.sin(la * _CH_D2R)), t2 = t * t, t6 = t2 * t2 * t2;
    var a1 = _CH_EA[0], a2 = _CH_EA[1], a3 = _CH_EA[2], a4 = _CH_EA[3];
    var x = l * Math.cos(t) / (_CH_EA_M * (a1 + 3 * a2 * t2 + t6 * (7 * a3 + 9 * a4 * t2)));
    var y = t * (a1 + a2 * t2 + t6 * (a3 + a4 * t2));
    return [tx + k * x, ty - k * y];
  };
}

// d3.geoConicEqualArea().parallels([p0, p1]).rotate([rot, 0]).center(cen).scale(k).translate([tx, ty]).
function _chConic(p0, p1, rot, cen, k, tx, ty) {
  var y0 = p0 * _CH_D2R, y1 = p1 * _CH_D2R, sy0 = Math.sin(y0), n = (sy0 + Math.sin(y1)) / 2, c = 1 + sy0 * (2 * n - sy0), r0 = Math.sqrt(c) / n, d = rot * _CH_D2R;
  function raw(lam, phi) {
    var r = Math.sqrt(c - 2 * n * Math.sin(phi)) / n;
    lam = lam * n;
    return [r * Math.sin(lam), r0 - r * Math.cos(lam)];
  }
  var ce = raw(cen[0] * _CH_D2R, cen[1] * _CH_D2R), dx = tx - k * ce[0], dy = ty + k * ce[1];
  return function(lo, la) {
    var l = lo * _CH_D2R + d;
    if (Math.abs(l) > Math.PI) l -= Math.round(l / _CH_TAU) * _CH_TAU;
    var r = raw(l, la * _CH_D2R);
    return [dx + k * r[0], dy - k * r[1]];
  };
}

// The three projections of d3.geoAlbersUsa (lower 48, Alaska, Hawaii) and their clip extents [x0, y0, x1, y1].
function _chAlbersParts(k, tx, ty) {
  var e = _CH_EPS;
  return [[_chConic(29.5, 45.5, 96, [-0.6, 38.7], k, tx, ty), [tx - 0.455 * k, ty - 0.238 * k, tx + 0.455 * k, ty + 0.238 * k]],
          [_chConic(55, 65, 154, [-2, 58.5], k * 0.35, tx - 0.307 * k, ty + 0.201 * k), [tx - 0.425 * k + e, ty + 0.120 * k + e, tx - 0.214 * k - e, ty + 0.234 * k - e]],
          [_chConic(8, 18, 157, [-3, 19.9], k, tx - 0.205 * k, ty + 0.212 * k), [tx - 0.214 * k + e, ty + 0.166 * k + e, tx - 0.115 * k - e, ty + 0.234 * k - e]]];
}

// d3.geoAlbersUsa().scale(k).translate([tx, ty]) -> f(lon, lat) = [x, y], or null where no part of the composite shows the point.
function _chAlbersUsa(k, tx, ty) {
  var parts = _chAlbersParts(k, tx, ty);
  return function(lo, la) {
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i][0](lo, la), c = parts[i][1];
      if (c[0] <= p[0] && p[0] <= c[2] && c[1] <= p[1] && p[1] <= c[3]) return p;
    }
    return null;
  };
}

function _chR1(v) { return Math.floor(v * 10 + 0.5) / 10; }

function _chPath(polys, pr) {
  var d = '', a, b, ring, pts, lx, ly, n, p, x, y, i;
  for (a = 0; a < polys.length; a++) {
    for (b = 0; b < polys[a].length; b++) {
      ring = polys[a][b]; pts = ''; lx = null; ly = null; n = 0;
      for (i = 0; i < ring.length; i += 2) {
        p = pr(ring[i], ring[i + 1]);
        x = _chR1(p[0]); y = _chR1(p[1]);
        if (x !== lx || y !== ly) { pts += (n ? ' ' : '') + x + ' ' + y; n++; lx = x; ly = y; }
      }
      if (n >= 3) d += 'M' + pts + 'Z';
    }
  }
  return d;
}

// [project(regionId, lon, lat), width, height]: albers-usa is d3's default frame; the others are fitted to the set's window.
// the optional travel frame as [lon0, lon1, lat0, lat1] or null (with a note when it was given but is not usable); twin of _ch_frame_read
var _CH_FRAME_KEYS = ['lon_min', 'lon_max', 'lat_min', 'lat_max'];
function _chFrameRead(f, proj, notes) {
  var v = [], i, lo0, lo1, la0, la1, c;
  if (f === undefined || f === null) return null;
  if (proj === 'albers-usa') { notes.push('frame is not used with the albers-usa projection (a fixed composite); the whole map is drawn.'); return null; }
  for (i = 0; i < 4; i++) v.push(_chIsObj(f) ? _crNum(f[_CH_FRAME_KEYS[i]]) : null);
  if (v[0] === null || v[1] === null || v[2] === null || v[3] === null) { notes.push('frame must be {lon_min, lon_max, lat_min, lat_max}, four finite numbers; the whole map is drawn.'); return null; }
  lo0 = Math.max(-180, Math.min(180, v[0])); lo1 = Math.max(-180, Math.min(180, v[1])); la0 = Math.max(-85, Math.min(85, v[2])); la1 = Math.max(-85, Math.min(85, v[3]));
  if (!(lo0 < lo1 && la0 < la1)) { notes.push('frame needs lon_min below lon_max and lat_min below lat_max (after clamping to -180..180 and -85..85); the whole map is drawn.'); return null; }
  if (lo1 - lo0 < 1) { c = (lo0 + lo1) / 2; lo0 = Math.max(-180, c - 0.5); lo1 = Math.min(180, c + 0.5); }
  if (la1 - la0 < 1) { c = (la0 + la1) / 2; la0 = Math.max(-85, c - 0.5); la1 = Math.min(85, c + 0.5); }
  return [lo0, lo1, la0, la1];
}

function _chFrame(rset, proj, regs, fr) {
  if (proj === 'albers-usa') {
    var ps = _chAlbersParts(1070, 480, 250), lo48 = ps[0][0], ak = ps[1][0], hi = ps[2][0];
    return [function(rid, lo, la) { return rid === 'AK' ? ak(lo, la) : rid === 'HI' ? hi(lo, la) : lo48(lo, la); }, 960, 500];
  }
  var u = proj === 'equal-earth' ? _chEqualEarth(1, 0, 0) : _geoLib().merc([0, 0], 1, 0, 0);
  if (fr) {
    var fx0 = Infinity, fy0 = Infinity, fx1 = -Infinity, fy1 = -Infinity, t, fa, fc, fq, fj, fe;
    for (t = 0; t < 33; t++) {
      fa = fr[0] + (fr[1] - fr[0]) * t / 32; fc = fr[2] + (fr[3] - fr[2]) * t / 32;
      fe = [[fa, fr[2]], [fa, fr[3]], [fr[0], fc], [fr[1], fc]];
      for (fj = 0; fj < 4; fj++) {
        fq = u(fe[fj][0], fe[fj][1]);
        fx0 = Math.min(fx0, fq[0]); fx1 = Math.max(fx1, fq[0]); fy0 = Math.min(fy0, fq[1]); fy1 = Math.max(fy1, fq[1]);
      }
    }
    var fpad = 4, fk = Math.min((960 - 2 * fpad) / (fx1 - fx0), (540 - 2 * fpad) / (fy1 - fy0)), ftx = 480 - fk * (fx0 + fx1) / 2, fty = 270 - fk * (fy0 + fy1) / 2;
    return [function(rid, lo, la) { var q = u(lo, la); return [ftx + fk * q[0], fty + fk * q[1]]; }, 960, 540];
  }
  var w = _CH_WIN[rset], x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, a, b, c, ring, p, i;
  for (a = 0; a < regs.length; a++) {
    for (b = 0; b < regs[a][2].length; b++) {
      for (c = 0; c < regs[a][2][b].length; c++) {
        ring = regs[a][2][b][c];
        for (i = 0; i < ring.length; i += 2) {
          if (w[0] <= ring[i] && ring[i] <= w[1] && w[2] <= ring[i + 1] && ring[i + 1] <= w[3]) {
            p = u(ring[i], ring[i + 1]);
            x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]);
          }
        }
      }
    }
  }
  var pad = 4, k = (960 - 2 * pad) / (x1 - x0), h = (y1 - y0) * k + 2 * pad;
  if (h > 640) { k = (640 - 2 * pad) / (y1 - y0); h = 640; }
  h = Math.ceil(h);
  var tx = 480 - k * (x0 + x1) / 2, ty = h / 2 - k * (y0 + y1) / 2;
  return [function(rid, lo, la) { var q = u(lo, la); return [tx + k * q[0], ty + k * q[1]]; }, 960, h];
}

function _chErr(b, msg) {
  var t = _crS(b.title, 80);
  return '<div role="note" style="margin:var(--a2ui-block-gap,1.25rem) 0;border:' + _CR_BORDER + ';border-radius:8px;padding:8px 10px;font-size:0.85rem;color:' + _CR_TEXT + ';">'
    + (t ? '<div style="font-weight:700;margin-bottom:4px;">' + t + '</div>' : '') + 'Choropleth map not drawn: ' + _crS(msg, 200) + '</div>';
}

function _chIds(ids) {
  return ids.slice(0, 8).map(function(i) { return _crS(i, 12); }).join(', ') + (ids.length > 8 ? ' and ' + (ids.length - 8) + ' more' : '');
}

// Class j (0 = lowest) of a quantized scale: the theme-token ramp of the legend, sampled at the class centre.
function _chColor(kind, scheme, j, steps, lo, hi) {
  if (kind === 'sequential') return _crMix(scheme === 'accent2' ? _CR_ACC2 : _CR_ACC, _chRound(12 + 88 * j / (steps - 1)), _CR_SURF);
  var c = lo + (hi - lo) * (j + 0.5) / steps, m = (lo < 0 && 0 < hi) ? 0 : (lo + hi) / 2;
  var den = Math.max(m - lo, hi - m), s = den > 0 ? Math.abs(c - m) / den : 0, p = _chRound(100 * s);
  return p === 0 ? _CR_SURF : _crMix(c < m ? _CR_ACC2 : _CR_ACC, p, _CR_SURF);
}

function _chIsObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }

// ---- category mode (twin of _CH_CATMAX .. _ch_cat_swatch and _render_choropleth_categorical) ----
var _CH_CATMAX = 6;
// only these four names are tokens; read at call time (the _CR_* tokens load later)
function _chCatTok(name) {
  if (name === 'accent') return _CR_ACC;
  if (name === 'accent2') return _CR_ACC2;
  if (name === 'text') return _CR_TEXT;
  if (name === 'muted') return _CR_MUTED;
  return undefined;
}
function _chCatPats() {
  return ['', '<circle cx="4" cy="4" r="1.5"/>', '<line x1="0" y1="4" x2="8" y2="4"/>', '<line x1="4" y1="0" x2="4" y2="8"/>',
    '<line x1="0" y1="4" x2="8" y2="4"/><line x1="4" y1="0" x2="4" y2="8"/>', '<line x1="4" y1="0" x2="4" y2="8" transform="rotate(-45 4 4)"/>'];
}
function _chCatDefault(j) {
  return [_CR_ACC, _CR_ACC2, _crMix(_CR_ACC, 45, _CR_SURF), _crMix(_CR_ACC2, 45, _CR_SURF), _crMix(_CR_TEXT, 45, _CR_SURF), _crMix(_CR_MUTED, 40, _CR_SURF)][j];
}
// [cats, cols, got (region id -> category index), error, unknown ids, repeated ids]
function _chCatRead(cats, cc, entries, field, index, notes, derive) {
  var msg = 'categories must be a list of 1 to ' + _CH_CATMAX + ' category names.', i, j, c, e, t, rid, cc, cols = [], badc = 0, k;
  if (cats !== undefined && cats !== null) {
    if (!Array.isArray(cats) || cats.length < 1) return [null, null, null, msg, null, null];
    for (i = 0; i < cats.length; i++) if (typeof cats[i] !== 'string' || cats[i].trim() === '') return [null, null, null, msg, null, null];
    var c2 = [];
    for (i = 0; i < cats.length; i++) c2.push(typeof cats[i] === 'string' ? cats[i].trim().slice(0, 40) : '');
    cats = [];
    for (i = 0; i < c2.length; i++) if (cats.indexOf(c2[i]) < 0) cats.push(c2[i]);
    if (cats.length > _CH_CATMAX) { notes.push('Only the first ' + _CH_CATMAX + ' categories were used.'); cats = cats.slice(0, _CH_CATMAX); }
  } else if (derive) {
    cats = [];
    for (i = 0; i < entries.length; i++) {
      e = entries[i]; c = _chIsObj(e) ? e[field] : undefined;
      if (typeof c === 'string' && c.trim() !== '' && cats.indexOf(c.trim().slice(0, 40)) < 0 && cats.length < _CH_CATMAX) cats.push(c.trim().slice(0, 40));
    }
  } else {
    return [null, null, null, msg, null, null];
  }
  cc = _chIsObj(cc) ? cc : {};
  for (j = 0; j < cats.length; j++) {
    t = Object.prototype.hasOwnProperty.call(cc, cats[j]) ? cc[cats[j]] : undefined;
    if (t !== undefined && t !== null && !(typeof t === 'string' && _chCatTok(t) !== undefined)) badc++;
    cols.push(typeof t === 'string' && _chCatTok(t) !== undefined ? _chCatTok(t) : _chCatDefault(j));
  }
  if (badc) notes.push(badc + (badc === 1 ? ' category colour is' : ' category colours are') + ' not accent, accent2, text or muted; the default colour was used.');
  var got = Object.create(null), unknown = [], dup = [], skipped = 0, nocat = 0;
  for (i = 0; i < entries.length; i++) {
    e = entries[i]; c = _chIsObj(e) ? e[field] : undefined; rid = _chIsObj(e) ? e.id : undefined;
    if (typeof c !== 'string' || c.trim() === '' || typeof rid !== 'string' || rid.trim() === '') { skipped++; continue; }
    rid = rid.trim().toUpperCase(); c = c.trim().slice(0, 40);
    if (index[rid] === undefined) unknown.push(rid);
    else if (got[rid] !== undefined) dup.push(rid);
    else { k = cats.indexOf(c); if (k < 0) nocat++; else got[rid] = k; }
  }
  if (skipped) notes.push(skipped + (skipped === 1 ? ' entry was' : ' entries were') + ' skipped: each needs an id and a category name.');
  if (nocat) notes.push(nocat + (nocat === 1 ? ' entry names' : ' entries name') + ' a category that is not in categories and was skipped.');
  return [cats, cols, got, null, unknown, dup];
}
function _chCatDefs(pid, cols) {
  var d = '', j, pats = _chCatPats();
  for (j = 0; j < cols.length; j++) {
    if (pats[j]) d += '<pattern id="' + pid + 'c' + j + '" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" style="fill:' + cols[j] + ';"/><g style="fill:' + _CR_TEXT
      + ';stroke:' + _CR_TEXT + ';stroke-width:1.4;stroke-opacity:0.65;fill-opacity:0.65;">' + pats[j] + '</g></pattern>';
  }
  return d;
}
function _chCatFill(pid, cols, j) { return !_chCatPats()[j] ? cols[j] : 'url(#' + pid + 'c' + j + ')'; }
function _chCatSwatch(pid, cols, j) {
  return '<svg aria-hidden="true" focusable="false" width="16" height="16" viewBox="0 0 16 16" style="flex:none;"><rect width="16" height="16" rx="3" style="fill:' + _chCatFill(pid, cols, j)
    + ';stroke:' + _CR_MUTED + ';"/></svg>';
}

function _chRenderCategorical(b, rset, proj, colors) {
  var vals = b.values;
  if (!Array.isArray(vals) || vals.length < 1) return _chErr(b, 'values must be a list of 1 to 250 {id, value}, each value a category name.');
  var notes = [], i, j;
  if (vals.length > 250) { notes.push('Only the first 250 of ' + vals.length + ' values were used.'); vals = vals.slice(0, 250); }
  var regs = _chRegions(rset), index = Object.create(null);
  for (i = 0; i < regs.length; i++) index[regs[i][0]] = i;
  var rd = _chCatRead(b.categories, colors, vals, 'value', index, notes, false);
  if (rd[3]) return _chErr(b, rd[3]);
  var cats = rd[0], cols = rd[1], got = rd[2], unknown = rd[4], dup = rd[5];
  var codes = rset === 'us-states' ? '2-letter USPS codes' : 'ISO 3166-1 alpha-3 codes';
  if (unknown.length) notes.push('Not in the map: ' + _chIds(unknown) + '. Ids are ' + codes + '.');
  if (dup.length) notes.push('Repeated ids, the first category was used: ' + _chIds(dup) + '.');
  var valued = Object.keys(got);
  if (!valued.length) return _chErr(b, 'no value matched a region of ' + rset + ' (ids are ' + codes + ') with a category from categories.');
  valued.sort(function(a, c) { return (got[a] - got[c]) || (index[a] - index[c]); });
  var nodata = regs.filter(function(r) { return got[r[0]] === undefined; });
  var order = valued.map(function(r) { return regs[index[r]]; }).concat(nodata);
  var nTiles = order.length, nAll = nTiles + cats.length;
  var fr = _chFrame(rset, proj, regs, _chFrameRead(b.frame, proj, notes)), pr = fr[0], w = fr[1], h = fr[2];
  var uid = 'ch' + _crId(['choropleth_map', rset, proj, 'categories'].concat(cats, cols, valued.map(function(r) { return r + '=' + got[r]; })));
  var paths = '', fill, tip, reg;
  order.forEach(function(r, n) {
    reg = r;
    if (got[r[0]] !== undefined) { fill = _chCatFill(uid, cols, got[r[0]]); tip = _crS(r[1], 80) + ': ' + _crS(cats[got[r[0]]], 40); }
    else { fill = 'url(#' + uid + ')'; tip = _crS(r[1], 80) + ': no category'; }
    paths += '<path' + _crCb('tile', n, nAll, 'fill:' + fill + ';stroke:' + _CR_MUTED + ';stroke-width:0.4;fill-rule:evenodd;', _crS(r[0], 12)) + ' d="'
      + _chPath(reg[2], function(lo_, la_) { return pr(reg[0], lo_, la_); }) + '"><title>' + tip + '</title></path>';
  });
  var defs = _chCatDefs(uid, cols);
  if (nodata.length) {
    defs += '<pattern id="' + uid + '" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" style="fill:' + _CR_SURF
      + ';"/><line x1="0" y1="0" x2="0" y2="6" style="stroke:' + _CR_MUTED + ';stroke-width:1.5;"/></pattern>';
  }
  defs = defs ? '<defs>' + defs + '</defs>' : '';
  var title = _crS(b.title, 80);
  var label = (title || 'Choropleth map') + ': ' + valued.length + ' of ' + regs.length + ' regions have a category, in ' + cats.length + (cats.length === 1 ? ' category' : ' categories');
  var svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" width="100%" role="img" aria-label="' + label + '" focusable="false" style="display:block;max-width:' + w + 'px;height:auto;">' + defs + paths + '</svg>';
  var lt = _crS(b.legend_title, 60), lis = '';
  for (j = 0; j < cats.length; j++) {
    lis += '<li style="display:inline-flex;align-items:center;gap:6px;">' + _chCatSwatch(uid, cols, j) + '<span' + _crCb('label', nTiles + j, nAll, '', 'class-' + (j + 1)) + '>' + _crS(cats[j], 40) + '</span></li>';
  }
  if (nodata.length) {
    lis += '<li style="display:inline-flex;align-items:center;gap:6px;"><span aria-hidden="true" style="display:inline-block;flex:none;width:14px;height:14px;border-radius:3px;border:' + _CR_BORDER
      + ';background:repeating-linear-gradient(45deg,' + _CR_MUTED + ' 0 1.5px,' + _CR_SURF + ' 1.5px 5px);"></span><span>No category</span></li>';
  }
  var legend = '<div style="margin-top:8px;">' + (lt ? '<div style="font-weight:600;margin-bottom:4px;">' + lt + '</div>' : '')
    + '<ul style="list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 14px;">' + lis + '</ul></div>';
  var nt = notes.map(function(x) { return '<p role="note" style="margin:6px 0 0;font-size:0.8rem;color:' + _CR_MUTED + ';">' + x + '</p>'; }).join('') + _hgVersionNote(b, 'choropleth_map');
  var nd = '';
  if (nodata.length) {
    nd = '<details style="margin-top:6px;"><summary>' + nodata.length + (nodata.length === 1 ? ' region has' : ' regions have') + ' no category (hatched)</summary><p style="margin:4px 0 0;">'
      + nodata.map(function(r) { return _crS(r[1], 80); }).join(', ') + '</p></details>';
  }
  var rows = valued.map(function(r) { return '<tr><th scope="row">' + _crS(regs[index[r]][1], 80) + '</th><td>' + r + '</td><td>' + _crS(cats[got[r]], 40) + '</td></tr>'; }).join('');
  var table = '<table style="' + _CR_SR + '"><caption>' + (title || 'Choropleth map') + ', regions with a category, in category order</caption>'
    + '<thead><tr><th scope="col">Region</th><th scope="col">Code</th><th scope="col">Category</th></tr></thead><tbody>' + rows + '</tbody></table>';
  return '<div role="group" aria-label="' + (title || 'Choropleth map') + '" data-cb-root style="--n:' + nAll + ';margin:var(--a2ui-block-gap,1.25rem) 0;color:' + _CR_TEXT + ';font-size:0.85rem;">'
    + _CR_CB_CSS + (title ? '<div style="font-weight:700;font-size:1.05rem;margin:0 0 8px;">' + title + '</div>' : '') + svg + legend + nt + nd + table + '</div>';
}

_RENDERERS['choropleth_map'] = function(b) {
  b = _chIsObj(b) ? b : {};
  var rset = b.region_set;
  if (_CH_SETS.indexOf(rset) < 0) return _chErr(b, 'region_set must be world-countries, us-states or europe-countries.');
  var proj = b.projection;
  if (proj !== undefined && proj !== null && _CH_PROJ.indexOf(proj) < 0) return _chErr(b, 'projection must be equal-earth, mercator or albers-usa.');
  if (proj === 'albers-usa' && rset !== 'us-states') return _chErr(b, 'albers-usa only works with region_set us-states.');
  proj = proj || (rset === 'us-states' ? 'albers-usa' : 'equal-earth');
  if (b.categories !== undefined && b.categories !== null) return _chRenderCategorical(b, rset, proj, b.category_colors);
  var sc = b.scale;
  if (sc !== undefined && sc !== null && !_chIsObj(sc)) return _chErr(b, 'scale must be an object {kind, scheme}.');
  sc = sc || {};
  var kind = sc.kind === undefined ? 'sequential' : sc.kind;
  if (kind !== 'sequential' && kind !== 'diverging') return _chErr(b, 'scale.kind must be sequential or diverging.');
  var scheme = _CR_SCHEMES[kind].indexOf(sc.scheme) >= 0 ? sc.scheme : _CR_SCHEMES[kind][0];
  var vals = b.values;
  if (!Array.isArray(vals) || vals.length < 1) return _chErr(b, 'values must be a list of 1 to 250 {id, value}.');
  var notes = [];
  if (vals.length > 250) { notes.push('Only the first 250 of ' + vals.length + ' values were used.'); vals = vals.slice(0, 250); }
  var steps = 5, sv;
  if (b.steps !== undefined && b.steps !== null) {
    sv = _crNum(b.steps);
    if (sv === null) notes.push('steps must be a number from 3 to 9; using 5.');
    else {
      steps = Math.max(3, Math.min(9, _chRound(sv)));
      if (steps !== sv) notes.push('steps must be a whole number from 3 to 9; using ' + steps + '.');
    }
  }
  var regs = _chRegions(rset), index = Object.create(null), got = Object.create(null), unknown = [], dup = [], skipped = 0, i, e, v, rid;
  for (i = 0; i < regs.length; i++) index[regs[i][0]] = i;
  for (i = 0; i < vals.length; i++) {
    e = vals[i];
    v = _chIsObj(e) ? _crNum(e.value) : null;
    rid = _chIsObj(e) ? e.id : null;
    if (v === null || typeof rid !== 'string' || rid.trim() === '') { skipped++; continue; }
    rid = rid.trim().toUpperCase();
    if (index[rid] === undefined) unknown.push(rid);
    else if (got[rid] !== undefined) dup.push(rid);
    else got[rid] = v;
  }
  var codes = rset === 'us-states' ? '2-letter USPS codes' : 'ISO 3166-1 alpha-3 codes';
  if (skipped) notes.push(skipped + (skipped === 1 ? ' entry was' : ' entries were') + ' skipped: each needs an id and a finite number value.');
  if (unknown.length) notes.push('Not in the map: ' + _chIds(unknown) + '. Ids are ' + codes + '.');
  if (dup.length) notes.push('Repeated ids, the first value was used: ' + _chIds(dup) + '.');
  var valued = Object.keys(got);
  if (!valued.length) return _chErr(b, 'no value matched a region of ' + rset + ' (ids are ' + codes + ').');
  var lo = Infinity, hi = -Infinity;
  valued.forEach(function(r) { lo = Math.min(lo, got[r]); hi = Math.max(hi, got[r]); });
  var unitRaw = typeof b.unit === 'string' ? b.unit : '', unit = _crS(unitRaw, 12);
  var us = unit ? ((unitRaw.slice(0, 12) === '%' ? '' : ' ') + unit) : '';
  function klass(x) { return hi === lo ? 0 : Math.min(steps - 1, Math.floor((x - lo) / (hi - lo) * steps)); }
  var fills = [], bounds = [], j;
  for (j = 0; j < steps; j++) fills.push(_chColor(kind, scheme, j, steps, lo, hi));
  for (j = 0; j <= steps; j++) bounds.push(j < steps ? lo + (hi - lo) * j / steps : hi);
  valued.sort(function(a, c) { return (got[c] - got[a]) || (index[a] - index[c]); });
  var nodata = regs.filter(function(r) { return got[r[0]] === undefined; });
  var order = valued.map(function(r) { return regs[index[r]]; }).concat(nodata);
  var nTiles = order.length, nAll = nTiles + steps;
  var fr = _chFrame(rset, proj, regs, _chFrameRead(b.frame, proj, notes)), pr = fr[0], w = fr[1], h = fr[2];
  var uid = 'ch' + _crId(['choropleth_map', rset, proj, kind, String(steps)].concat(valued.map(function(r) { return r + '=' + _crTrim(got[r]); })));
  var paths = '', fill, tip, reg;
  order.forEach(function(r, n) {
    reg = r;
    if (got[r[0]] !== undefined) { fill = fills[klass(got[r[0]])]; tip = _crS(r[1], 80) + ': ' + _crTrim(got[r[0]]) + us; }
    else { fill = 'url(#' + uid + ')'; tip = _crS(r[1], 80) + ': no data'; }
    paths += '<path' + _crCb('tile', n, nAll, 'fill:' + fill + ';stroke:' + _CR_MUTED + ';stroke-width:0.4;fill-rule:evenodd;', _crS(r[0], 12)) + ' d="'
      + _chPath(reg[2], function(lo_, la_) { return pr(reg[0], lo_, la_); }) + '"><title>' + tip + '</title></path>';
  });
  var defs = '';
  if (nodata.length) {
    defs = '<defs><pattern id="' + uid + '" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" style="fill:' + _CR_SURF
      + ';"/><line x1="0" y1="0" x2="0" y2="6" style="stroke:' + _CR_MUTED + ';stroke-width:1.5;"/></pattern></defs>';
  }
  var title = _crS(b.title, 80);
  var label = (title || 'Choropleth map') + ': ' + valued.length + ' of ' + regs.length + ' regions have a value, from ' + _crTrim(lo) + us + ' to ' + _crTrim(hi) + us;
  var svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" width="100%" role="img" aria-label="' + label + '" focusable="false" style="display:block;max-width:' + w + 'px;height:auto;">'
    + defs + paths + '</svg>';
  var lt = _crS(b.legend_title, 60), lis = '';
  for (j = 0; j < steps; j++) {
    lis += '<li style="display:inline-flex;align-items:center;gap:6px;"><span aria-hidden="true" style="display:inline-block;flex:none;width:14px;height:14px;border-radius:3px;border:' + _CR_BORDER
      + ';background:' + fills[j] + ';"></span><span' + _crCb('label', nTiles + j, nAll, '', 'class-' + (j + 1)) + '>' + _crTrim(_chNice(bounds[j])) + ' to ' + _crTrim(_chNice(bounds[j + 1])) + us + '</span></li>';
  }
  if (nodata.length) {
    lis += '<li style="display:inline-flex;align-items:center;gap:6px;"><span aria-hidden="true" style="display:inline-block;flex:none;width:14px;height:14px;border-radius:3px;border:' + _CR_BORDER
      + ';background:repeating-linear-gradient(45deg,' + _CR_MUTED + ' 0 1.5px,' + _CR_SURF + ' 1.5px 5px);"></span><span>No data</span></li>';
  }
  var legend = '<div style="margin-top:8px;">' + (lt ? '<div style="font-weight:600;margin-bottom:4px;">' + lt + '</div>' : '')
    + '<ul style="list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 14px;">' + lis + '</ul></div>';
  var nt = notes.map(function(x) { return '<p role="note" style="margin:6px 0 0;font-size:0.8rem;color:' + _CR_MUTED + ';">' + x + '</p>'; }).join('') + _hgVersionNote(b, 'choropleth_map');
  var nd = '';
  if (nodata.length) {
    nd = '<details style="margin-top:6px;"><summary>' + nodata.length + (nodata.length === 1 ? ' region has' : ' regions have') + ' no value (hatched)</summary><p style="margin:4px 0 0;">'
      + nodata.map(function(r) { return _crS(r[1], 80); }).join(', ') + '</p></details>';
  }
  var rows = '';
  valued.forEach(function(r) {
    rows += '<tr><th scope="row">' + _crS(regs[index[r]][1], 80) + '</th><td>' + r + '</td><td>' + _crTrim(got[r]) + us + '</td><td>' + (klass(got[r]) + 1) + ' of ' + steps + '</td></tr>';
  });
  var table = '<table style="' + _CR_SR + '"><caption>' + (title || 'Choropleth map') + (unit ? ' (' + unit + ')' : '') + ', regions with a value, largest first</caption>'
    + '<thead><tr><th scope="col">Region</th><th scope="col">Code</th><th scope="col">Value</th><th scope="col">Class</th></tr></thead><tbody>' + rows + '</tbody></table>';
  return '<div role="group" aria-label="' + (title || 'Choropleth map') + '" data-cb-root style="--n:' + nAll + ';margin:var(--a2ui-block-gap,1.25rem) 0;color:' + _CR_TEXT + ';font-size:0.85rem;">'
    + _CR_CB_CSS + (title ? '<div style="font-weight:700;font-size:1.05rem;margin:0 0 8px;">' + title + '</div>' : '') + svg + legend + nt + nd + table + '</div>';
};
