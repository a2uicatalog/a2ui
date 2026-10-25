// ─────────────────────────────────────────────────────────────────
// geo_map (scattergeo parity, 2026-10-21, stage: preview). Twin of the _render_geo_map block in renderers/web_article.py.
//
// Points and great-circle lines on the choropleth_map outlines and projections (atoms_choropleth.gs: _CH_*, _chRegions, _chFrame, _chAlbersUsa, _chPath; no tiles, no network,
// no custom GeoJSON). The great circle is the d3-geo 3.1.1 geoInterpolate (ISC, Mike Bostock) ported by hand; tests/test_geo_map.py checks it against the real library to 1e-9.
// Shape + colour per group and a dash per line, so colour is never the only cue. gas-schema-renderer is frozen and gets no copy.
// ─────────────────────────────────────────────────────────────────

var _GM_SHAPES = ['circle', 'square', 'diamond', 'triangle'];
// read at render time: the _CR_* tokens are defined in files that load after this one
function _gmCol(i) { return [_CR_ACC, _CR_ACC2, _CR_TEXT, _CR_MUTED][i % 4]; }
var _GM_DASH = ['', '7 4', '2 4'];
var _GM_MAXPTS = 500, _GM_MAXLINES = 40, _GM_MAXVERT = 20, _GM_MAXGROUPS = 6;
// slot gi -> [shape, colour]: the colour index moves on by one every fourth slot, so the 7 slots (6 groups and the ungrouped points) are all different pairs
function _gmStyle(gi) { return [_GM_SHAPES[gi % 4], _gmCol(gi + Math.floor(gi / 4))]; }
// key of a point or line: its id (text, max 60), else its label (max 40), else fb ('p3' / 'l0': the position in the list as given)
function _gmKb(e, fb) {
  var i = typeof e.id === 'string' ? _crS(e.id.trim(), 60) : '';
  return i || _crS(e.label, 40) || fb;
}
function _gmUniq(base, seen) {
  var k = base, n = 1;
  while (seen[k] === true) { n++; k = base + '~' + n; }
  seen[k] = true;
  return k;
}

// d3.geoInterpolate(a, b) -> [f(t) = [lon, lat], distance in radians]
function _gmInterp(a, b) {
  var r = Math.PI / 180, x0 = a[0] * r, y0 = a[1] * r, x1 = b[0] * r, y1 = b[1] * r;
  var cy0 = Math.cos(y0), sy0 = Math.sin(y0), cy1 = Math.cos(y1), sy1 = Math.sin(y1);
  var kx0 = cy0 * Math.cos(x0), ky0 = cy0 * Math.sin(x0), kx1 = cy1 * Math.cos(x1), ky1 = cy1 * Math.sin(x1);
  function hv(v) { var s = Math.sin(v / 2); return s * s; }
  var d = 2 * Math.asin(Math.sqrt(Math.min(1, hv(y1 - y0) + cy0 * cy1 * hv(x1 - x0)))), k = Math.sin(d);
  if (!d) return [function() { return [x0 / r, y0 / r]; }, d];
  return [function(t) {
    t = t * d;
    var bb = Math.sin(t) / k, aa = Math.sin(d - t) / k, x = aa * kx0 + bb * kx1, y = aa * ky0 + bb * ky1, z = aa * sy0 + bb * sy1;
    return [Math.atan2(y, x) / r, Math.atan2(z, Math.sqrt(x * x + y * y)) / r];
  }, d];
}

function _gmErr(b, msg) {
  var t = _crS(_chIsObj(b) ? b.title : undefined, 80);
  return '<div role="note" style="margin:var(--a2ui-block-gap,1.25rem) 0;border:' + _CR_BORDER + ';border-radius:8px;padding:8px 10px;font-size:0.85rem;color:' + _CR_TEXT + ';">'
    + (t ? '<div style="font-weight:700;margin-bottom:4px;">' + t + '</div>' : '') + 'Geo map not drawn: ' + _crS(msg, 200) + '</div>';
}

function _gmCoord(e) {
  if (!_chIsObj(e)) return null;
  var la = _crNum(e.lat), lo = _crNum(e.lon);
  return (la !== null && lo !== null && la >= -90 && la <= 90 && lo >= -180 && lo <= 180) ? [la, lo] : null;
}

function _gmMarker(shape, x, y, r, cb, tip) {
  var a = ' data-shape="' + shape + '" data-r="' + _crTrim(r) + '" data-xy="' + x + ',' + y + '"', i, d, pts;
  if (shape === 'circle') return '<circle' + cb + a + ' cx="' + x + '" cy="' + y + '" r="' + _crTrim(r) + '"><title>' + tip + '</title></circle>';
  if (shape === 'square') return '<rect' + cb + a + ' x="' + _chR1(x - r) + '" y="' + _chR1(y - r) + '" width="' + _chR1(2 * r) + '" height="' + _chR1(2 * r) + '"><title>' + tip + '</title></rect>';
  pts = shape === 'diamond' ? [[0, -1.25], [1.25, 0], [0, 1.25], [-1.25, 0]] : [[0, -1.2], [1.1, 0.9], [-1.1, 0.9]];
  d = [];
  for (i = 0; i < pts.length; i++) d.push(_chR1(x + pts[i][0] * r) + ' ' + _chR1(y + pts[i][1] * r));
  return '<path' + cb + a + ' d="M' + d.join('L') + 'Z"><title>' + tip + '</title></path>';
}

function _gmSwatch(shape, col) {
  var m = { circle: '<circle r="5.5"', square: '<rect x="-5" y="-5" width="10" height="10"', diamond: '<path d="M0 -7L7 0L0 7L-7 0Z"', triangle: '<path d="M0 -6.5L6 5L-6 5Z"' };
  return '<svg aria-hidden="true" focusable="false" width="16" height="16" viewBox="-8 -8 16 16" style="flex:none;">' + m[shape] + ' style="fill:' + col + ';stroke:' + _CR_SURF + ';"/></svg>';
}

_RENDERERS['geo_map'] = function(b) {
  b = _chIsObj(b) ? b : {};
  var rset = (b.region_set !== undefined && b.region_set !== null) ? b.region_set : 'world-countries';
  if (_CH_SETS.indexOf(rset) < 0) return _gmErr(b, 'region_set must be world-countries, us-states or europe-countries.');
  var proj = b.projection;
  if (proj !== undefined && proj !== null && _CH_PROJ.indexOf(proj) < 0) return _gmErr(b, 'projection must be equal-earth, mercator or albers-usa.');
  if (proj === 'albers-usa' && rset !== 'us-states') return _gmErr(b, 'albers-usa only works with region_set us-states.');
  proj = proj || (rset === 'us-states' ? 'albers-usa' : 'equal-earth');
  var notes = [], ptsIn = Array.isArray(b.points) ? b.points : [], linesIn = Array.isArray(b.lines) ? b.lines : [], i, k, e, c, bad = 0;
  if (ptsIn.length > _GM_MAXPTS) { notes.push('Only the first ' + _GM_MAXPTS + ' of ' + ptsIn.length + ' points were used.'); ptsIn = ptsIn.slice(0, _GM_MAXPTS); }
  if (linesIn.length > _GM_MAXLINES) { notes.push('Only the first ' + _GM_MAXLINES + ' of ' + linesIn.length + ' lines were used.'); linesIn = linesIn.slice(0, _GM_MAXLINES); }
  var pts = [], lines = [], raw, cs, g;
  for (i = 0; i < ptsIn.length; i++) {
    e = ptsIn[i]; c = _gmCoord(e);
    if (c === null) { bad++; continue; }
    g = (typeof e.group === 'string' && e.group.trim() !== '') ? e.group : '';
    pts.push([c[0], c[1], _crS(e.label, 40), _crNum(e.value), g, _gmKb(e, 'p' + i)]);
  }
  for (i = 0; i < linesIn.length; i++) {
    e = linesIn[i]; raw = _chIsObj(e) ? e.path : null; cs = [];
    if (Array.isArray(raw)) { raw = raw.slice(0, _GM_MAXVERT); for (k = 0; k < raw.length; k++) cs.push(_gmCoord(raw[k])); }
    if (cs.length < 2 || cs.indexOf(null) >= 0) { bad++; continue; }
    lines.push([_crS(e.label, 40), cs, _gmKb(e, 'l' + i)]);
  }
  var seen = {}, lkeys = [], pkeys = [];
  for (i = 0; i < lines.length; i++) lkeys.push(_gmUniq(lines[i][2], seen));
  for (i = 0; i < pts.length; i++) pkeys.push(_gmUniq(pts[i][5], seen));
  if (bad) notes.push(bad + (bad === 1 ? ' entry was' : ' entries were') + ' skipped: a point needs lat (-90 to 90) and lon (-180 to 180) numbers, a line a path of 2 to ' + _GM_MAXVERT + ' of them.');
  if (!pts.length && !lines.length) return _gmErr(b, 'give points (each {lat, lon}) or lines (each {path: [{lat, lon}, ...]}).');
  var groups = [], named = [];
  for (i = 0; i < pts.length; i++) if (groups.indexOf(pts[i][4]) < 0) groups.push(pts[i][4]);
  for (i = 0; i < groups.length; i++) if (groups[i] !== '') named.push(groups[i]);
  if (named.length > _GM_MAXGROUPS) {
    var keep = named.slice(0, _GM_MAXGROUPS - 1);
    notes.push('More than ' + _GM_MAXGROUPS + ' groups: the groups after the first ' + (_GM_MAXGROUPS - 1) + ' are shown as Other.');
    for (i = 0; i < pts.length; i++) if (pts[i][4] !== '' && keep.indexOf(pts[i][4]) < 0) pts[i][4] = 'Other';
    named = keep.concat(['Other']);
  }
  var vals = [], lo, hi;
  for (i = 0; i < pts.length; i++) if (pts[i][3] !== null) vals.push(pts[i][3]);
  lo = vals.length ? Math.min.apply(null, vals) : 0; hi = vals.length ? Math.max.apply(null, vals) : 0;
  var unitRaw = typeof b.unit === 'string' ? b.unit : '', unit = _crS(unitRaw, 12), us = unit ? ((unitRaw.slice(0, 12) === '%' ? '' : ' ') + unit) : '';
  var regs = _chRegions(rset), frm = _chFrameRead(b.frame, proj, notes), fr = (frm ? _chFrameNote(regs, frm, notes) : 0, _chFrame(rset, proj, regs, frm)), pr = fr[0], w = fr[1], h = fr[2], usa = proj === 'albers-usa' ? _chAlbersUsa(1070, 480, 250) : null;
  var shade = Array.isArray(b.regions) ? b.regions.slice(0, 250) : [], cats = null, cols = null, got = Object.create(null), rd, ridxm = Object.create(null), gotN = 0;
  for (i = 0; i < regs.length; i++) ridxm[regs[i][0]] = i;
  if (shade.length) {
    rd = _chCatRead(b.categories, b.category_colors, shade, 'category', ridxm, notes, true);
    if (rd[3]) { notes.push('regions not shaded: ' + rd[3]); }
    else {
      if (rd[4].length) notes.push('Not in the map: ' + _chIds(rd[4]) + '.');
      if (rd[5].length) notes.push('Repeated region ids, the first category was used: ' + _chIds(rd[5]) + '.');
      gotN = Object.keys(rd[2]).length;
      if (gotN) {
        cats = rd[0]; got = rd[2];
        cols = rd[1].map(function(c) { return _crMix(c, 38, _CR_SURF); });   // a tint, so the strong marker and route colours stay readable on a shaded region
      }
    }
  }
  var keyed = !!frm || gotN > 0;
  var pid = '';
  if (gotN) {
    var gks = Object.keys(got);
    gks.sort(function(a, c) { return ridxm[a] - ridxm[c]; });
    var pparts = ['geo_map', 'regions'].concat(cats, cols, frm ? frm.map(_crTrim) : [], gks.map(function(r) { return r + '=' + got[r]; }), pkeys, lkeys);
    for (i = 0; i < pts.length; i++) pparts.push(_crTrim(pts[i][0]), _crTrim(pts[i][1]));
    for (i = 0; i < lines.length; i++) for (k = 0; k < lines[i][1].length; k++) pparts.push(_crTrim(lines[i][1][k][0]), _crTrim(lines[i][1][k][1]));
    pid = 'gc' + _crId(pparts);
  }
  function at(lat, lon) {
    if (usa) return usa(lon, lat);
    var p = pr('', lon, lat);
    return (p[0] >= 0 && p[0] <= w && p[1] >= 0 && p[1] <= h) ? p : null;
  }
  var base = '', ri;
  function mk(rid) { return function(lo_, la_) { return pr(rid, lo_, la_); }; }
  var rfill, rkey, rtip, rid;
  for (ri = 0; ri < regs.length; ri++) {
    rid = regs[ri][0];
    rfill = got[rid] !== undefined ? _chCatFill(pid, cols, got[rid]) : _crMix(_CR_MUTED, 12, _CR_SURF);
    rkey = keyed ? ' data-cb="tile" data-key="' + _crS(rid, 12) + '"' : '';
    rtip = got[rid] !== undefined ? '<title>' + _crS(regs[ri][1], 80) + ': ' + _esc(cats[got[rid]]) + '</title>' : '';
    base += '<path data-base="1"' + rkey + ' style="fill:' + rfill + ';stroke:' + _CR_MUTED + ';stroke-width:' + (frm ? '0.9' : '0.4') + ';fill-rule:evenodd;" d="' + _chPath(regs[ri][2], mk(rid)) + '"' + (rtip ? '>' + rtip + '</path>' : '/>');
  }
  var pq, cut = 0, nAll = lines.length + pts.length, idx = 0, routeSvg = '', masks = '', dsAll = [], li, d, seg, prev, f, dist, n, s, q, p, dash, col, tip, legs, last, ld, lseg, j;
  for (li = 0; li < lines.length; li++) {
    cs = lines[li][1]; d = ''; seg = []; prev = null; pq = null; legs = []; last = null;
    for (k = 0; k < cs.length - 1; k++) {
      f = _gmInterp([cs[k][1], cs[k][0]], [cs[k + 1][1], cs[k + 1][0]]); dist = f[1];
      n = (dist < 1e-9 || Math.sin(dist) < 1e-9) ? 1 : Math.max(1, Math.min(64, Math.ceil(dist / 0.0349)));
      ld = ''; lseg = (k > 0 && prev !== null && last !== null) ? [last] : [];
      for (s = (k === 0 ? 0 : 1); s <= n; s++) {
        q = n > 1 ? f[0](s / n) : (s === 0 ? [cs[k][1], cs[k][0]] : [cs[k + 1][1], cs[k + 1][0]]);
        p = usa ? at(q[1], q[0]) : pr('', q[0], q[1]);
        if (p === null) cut++;
        if (p === null || (prev !== null && (frm ? Math.abs(q[0] - pq) > 180 : Math.abs(p[0] - prev[0]) > w / 2))) {
          if (seg.length >= 2) d += 'M' + seg.join(' ');
          seg = [];
          if (lseg.length >= 2) ld += 'M' + lseg.join(' ');
          lseg = [];
        }
        if (p !== null) { last = _chR1(p[0]) + ' ' + _chR1(p[1]); seg.push(last); lseg.push(last); }
        prev = p; pq = q[0];
      }
      if (lseg.length >= 2) ld += 'M' + lseg.join(' ');
      legs.push(ld);
    }
    if (seg.length >= 2) d += 'M' + seg.join(' ');
    dsAll.push(d);
    dash = _GM_DASH[li % 3]; col = _gmCol(li);
    tip = (lines[li][0] || 'Line ' + (li + 1)) + ': ' + cs.length + ' points';
    // a route has no fade: it is drawn on by the mask below, stop by stop under --p; it carries data-cb/data-key but not cb-fade
    routeSvg += '<path data-cb="link" data-key="' + lkeys[li] + '" mask="url(#@@' + li + ')" style="fill:none;stroke:' + col + ';stroke-width:3;stroke-linecap:round;stroke-linejoin:round;' + (dash ? 'stroke-dasharray:' + dash + ';' : '') + '" d="' + d + '"><title>' + tip + '</title></path>';
    masks += '<mask id="@@' + li + '" maskUnits="userSpaceOnUse" x="0" y="0" width="' + w + '" height="' + h + '">';
    for (j = 0; j < legs.length; j++) {
      if (legs[j]) masks += '<path d="' + legs[j] + '" pathLength="1" style="fill:none;stroke:#fff;stroke-width:8;stroke-dasharray:1;stroke-dashoffset:calc(1px*(1 - clamp(0,calc((var(--p,1)*' + (nAll + 1) + ' - ' + idx + ')*' + legs.length + ' - ' + j + '),1)));"/>';
    }
    masks += '</mask>';
    idx++;
  }
  var mid = 'gm' + _crId(['geo_map', rset, proj].concat(lkeys, dsAll));
  routeSvg = routeSvg.split('url(#@@').join('url(#' + mid);
  masks = masks.split('id="@@').join('id="' + mid);
  var defsM = (masks || gotN) ? '<defs>' + masks + (gotN ? _chCatDefs(pid, cols) : '') + '</defs>' : '';
  var gidx = {}, markSvg = '', outside = [], pi, gi, r, v, st, hasUng = false, ungi = named.length;
  for (i = 0; i < named.length; i++) gidx[named[i]] = i;
  for (i = 0; i < pts.length; i++) if (pts[i][4] === '') hasUng = true;
  for (pi = 0; pi < pts.length; pi++) {
    p = at(pts[pi][0], pts[pi][1]);
    if (p === null) { outside.push(pi); continue; }
    gi = gidx[pts[pi][4]] === undefined ? ungi : gidx[pts[pi][4]]; v = pts[pi][3]; st = _gmStyle(gi);
    r = !vals.length ? 8 : (v === null ? 6 : (hi === lo ? 12 : 7 + 11 * Math.sqrt((v - lo) / (hi - lo))));
    tip = (pts[pi][2] ? pts[pi][2] + ': ' : '') + _crTrim(pts[pi][0]) + ', ' + _crTrim(pts[pi][1]) + (v === null ? '' : ' = ' + _crTrim(v) + us) + (pts[pi][4] ? ' (' + _crS(pts[pi][4], 40) + ')' : '');
    markSvg += _gmMarker(st[0], _chR1(p[0]), _chR1(p[1]), r, _crCb('node', idx, nAll, 'fill:' + st[1] + ';stroke:' + _CR_SURF + ';stroke-width:1.5;', pkeys[pi]), tip);
    idx++;
  }
  if (outside.length) notes.push(outside.length + (outside.length === 1 ? ' point is' : ' points are') + ' outside this map\'s frame and not drawn (still listed in the table).');
  if (cut) notes.push('Lines are cut where they leave the map: the US composite has no place for the path between the lower 48 and Alaska or Hawaii.');
  var title = _crS(b.title, 80);
  var label = (title || 'Geo map') + ': ' + (pts.length - outside.length) + ' of ' + pts.length + ' points drawn' + (lines.length ? ', ' + lines.length + (lines.length === 1 ? ' line' : ' lines') : '')
    + (named.length ? ' in ' + named.length + (named.length === 1 ? ' group' : ' groups') : '')
    + (gotN ? ', ' + gotN + (gotN === 1 ? ' region shaded' : ' regions shaded') + ' in ' + cats.length + (cats.length === 1 ? ' category' : ' categories') : '');
  var svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" width="100%" role="img" aria-label="' + label + '" focusable="false" style="display:block;max-width:' + w + 'px;height:auto;' + (frm ? _CH_SEAS : '') + '">' + (frm ? _chSea(w, h, rset, frm) : '') + defsM + base + routeSvg + markSvg + '</svg>';
  var lt = _crS(b.legend_title, 60), lis = '', noVal = false;
  var gnames = named.concat(named.length && hasUng ? ['Ungrouped'] : []);
  for (i = 0; i < gnames.length; i++) { st = _gmStyle(i); lis += '<li style="display:inline-flex;align-items:center;gap:6px;">' + _gmSwatch(st[0], st[1]) + '<span>' + _crS(gnames[i], 40) + '</span></li>'; }
  for (i = 0; gotN && i < cats.length; i++) lis += '<li style="display:inline-flex;align-items:center;gap:6px;">' + _chCatSwatch(pid, cols, i) + '<span>' + _esc(cats[i]) + '</span></li>';
  for (li = 0; li < lines.length; li++) {
    dash = _GM_DASH[li % 3];
    lis += '<li style="display:inline-flex;align-items:center;gap:6px;"><svg aria-hidden="true" focusable="false" width="28" height="16" viewBox="0 0 28 16" style="flex:none;"><line x1="1" y1="8" x2="27" y2="8" style="stroke:'
      + _gmCol(li) + ';stroke-width:2;' + (dash ? 'stroke-dasharray:' + dash + ';' : '') + '"/></svg><span>' + (lines[li][0] || 'Line ' + (li + 1)) + '</span></li>';
  }
  for (i = 0; i < pts.length; i++) if (pts[i][3] === null) noVal = true;
  var size = vals.length ? ' <p style="margin:4px 0 0;">Marker size: value, from ' + _crTrim(lo) + us + ' (smallest) to ' + _crTrim(hi) + us + ' (largest)' + (noVal ? '; points without a value are smallest' : '') + '.</p>' : '';
  var legend = '<div style="margin-top:8px;">' + (lt ? '<div style="font-weight:600;margin-bottom:4px;">' + lt + '</div>' : '')
    + (lis ? '<ul style="list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 14px;">' + lis + '</ul>' : '') + size + '</div>';
  var nt = '';
  for (i = 0; i < notes.length; i++) nt += '<p role="note" style="margin:6px 0 0;font-size:0.8rem;color:' + _CR_MUTED + ';">' + notes[i] + '</p>';
  nt += _hgVersionNote(b, 'geo_map');
  var prow = '';
  for (pi = 0; pi < pts.length; pi++) {
    prow += '<tr><th scope="row">' + (pts[pi][2] || 'Point ' + (pi + 1)) + '</th><td>' + _crTrim(pts[pi][0]) + '</td><td>' + _crTrim(pts[pi][1]) + '</td><td>' + (pts[pi][3] === null ? '' : _crTrim(pts[pi][3]) + us)
      + '</td><td>' + _crS(pts[pi][4], 40) + '</td><td>' + (outside.indexOf(pi) >= 0 ? 'outside the frame' : 'drawn') + '</td></tr>';
  }
  var ptable = pts.length ? '<table style="' + _CR_SR + '"><caption>' + (title || 'Geo map') + ', points</caption><thead><tr><th scope="col">Point</th><th scope="col">Latitude</th><th scope="col">Longitude</th>'
    + '<th scope="col">Value</th><th scope="col">Group</th><th scope="col">Status</th></tr></thead><tbody>' + prow + '</tbody></table>' : '';
  var lrow = '';
  for (li = 0; li < lines.length; li++) {
    cs = lines[li][1];
    var stops = [];
    for (k = 0; k < cs.length; k++) stops.push(_crTrim(cs[k][0]) + ', ' + _crTrim(cs[k][1]));
    lrow += '<tr><th scope="row">' + (lines[li][0] || 'Line ' + (li + 1)) + '</th><td>' + stops.join(' to ') + '</td><td>' + cs.length + '</td></tr>';
  }
  var ltable = lines.length ? '<table style="' + _CR_SR + '"><caption>' + (title || 'Geo map') + ', lines (great-circle arcs between the listed points)</caption><thead><tr><th scope="col">Line</th>'
    + '<th scope="col">Stops (lat, lon), in order</th><th scope="col">Points</th></tr></thead><tbody>' + lrow + '</tbody></table>' : '';
  var rtable = '';
  if (gotN) {
    var gk = Object.keys(got);
    gk.sort(function(a, c) { return (got[a] - got[c]) || (ridxm[a] - ridxm[c]); });
    rtable = '<table style="' + _CR_SR + '"><caption>' + (title || 'Geo map') + ', shaded regions</caption><thead><tr><th scope="col">Region</th><th scope="col">Code</th><th scope="col">Category</th></tr></thead><tbody>'
      + gk.map(function(r) { return '<tr><th scope="row">' + _crS(regs[ridxm[r]][1], 80) + '</th><td>' + _crS(r, 12) + '</td><td>' + _esc(cats[got[r]]) + '</td></tr>'; }).join('') + '</tbody></table>';
  }
  return '<div role="group" aria-label="' + (title || 'Geo map') + '" data-cb-root' + (keyed ? ' data-mtr-follow' : '') + ' style="--n:' + nAll + ';margin:var(--a2ui-block-gap,1.25rem) 0;color:' + _CR_TEXT + ';font-size:0.85rem;">'
    + _CR_CB_CSS + (title ? '<div style="font-weight:700;font-size:1.05rem;margin:0 0 8px;">' + title + '</div>' : '') + svg + legend + nt + ptable + ltable + rtable + '</div>';
};
