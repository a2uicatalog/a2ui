// ─── series[] for chartjs_line and scatter_trend (preview, optional field; absent = the old drawing, byte for byte) ─────────────────
// Twin of _ps_* in renderers/web_article.py: same arithmetic in the same order, so the HTML is identical. Named atoms_unstub_series so it loads
// after atoms_unstub.gs (which defines scatter_trend) and wraps the final renderer.
// Plotly scatter / scattergl: per-series x (numbers or dates), y, mode, colour, dash, line shape, marker size and symbol, fill.
// Dates: a UTC subset of d3-time-format and d3-scale scaleUtc().ticks() (d3-time 3.1.0 tick intervals), checked against the real modules
// by tests/fixtures/series_time_golden.json.

var _PS_W = 320, _PS_H = 200, _PS_M = 6, _PS_MAX_SERIES = 8, _PS_READ_CAP = 20000, _PS_TEXT_CAP = 30;
var _PS_MS_MAX = 253402300799999, _PS_MS_MIN = -62135596800000;
var _PS_PAL = ['#2563EB', '#D97706', '#059669', '#DB2777', '#7C3AED', '#65A30D'];
var _PS_SYMS = ['circle', 'square', 'diamond', 'triangle-up', 'cross', 'x'];
var _PS_DASH_NAMES = ['solid', 'dash', 'dot', 'dashdot', 'longdash', 'longdashdot'];
var _PS_DASH = { solid: '', dash: '6 4', dot: '2 4', dashdot: '8 4 2 4', longdash: '12 5', longdashdot: '12 4 2 4' };
var _PS_SHAPES = ['linear', 'spline', 'hv', 'vh', 'hvh', 'vhv'];
var _PS_MODES = ['lines', 'markers', 'text'];
var _PS_MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
var _PS_MONL = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
var _PS_DAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
var _PS_DAYL = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
var _PS_DATE_RE = /^([0-9]{4})(?:-([0-9]{2})(?:-([0-9]{2})(?:[T ]([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\.([0-9]{1,3})[0-9]*)?)?)?)?)?(Z)?$/;
var _PS_DIM = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
var _PS_TICK_IVL = [['second', 1, 1e3], ['second', 5, 5e3], ['second', 15, 15e3], ['second', 30, 30e3], ['minute', 1, 6e4], ['minute', 5, 3e5],
  ['minute', 15, 9e5], ['minute', 30, 18e5], ['hour', 1, 36e5], ['hour', 3, 108e5], ['hour', 6, 216e5], ['hour', 12, 432e5],
  ['day', 1, 864e5], ['day', 2, 1728e5], ['week', 1, 6048e5], ['month', 1, 2592e6], ['month', 3, 7776e6], ['year', 1, 31536e6]];
var _PS_UNIT_MS = { second: 1000, minute: 60000, hour: 3600000, day: 86400000 };

var _PS_NUM_MAX = 1e15;   // above the largest epoch-ms date (2.5e14); a larger number is refused (twin of _PS_NUM_MAX)
function _psIsnum(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= _PS_NUM_MAX; }
function _psTrim(v) { return v.replace(/^[ \t\n\v\f\r\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+|[ \t\n\v\f\r\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+$/g, ''); }
function _psUkey(k, used) { var base = k, n = 1; while (used[k] === true) { n++; k = base + ' (' + n + ')'; } used[k] = true; return _esc(k); }
function _psIsstr(v) { return typeof v === 'string'; }
function _psMod(a, b) { return ((a % b) + b) % b; }
function _psFd(a, b) { return (a - _psMod(a, b)) / b; }
function _psLeap(y) { return y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0); }
function _psDays(y, m, d) {
  y -= m <= 2 ? 1 : 0;
  var era = _psFd(y, 400), yoe = y - era * 400, doy = _psFd(153 * (m + (m > 2 ? -3 : 9)) + 2, 5) + d - 1, doe = yoe * 365 + _psFd(yoe, 4) - _psFd(yoe, 100) + doy;
  return era * 146097 + doe - 719468;
}
function _psCivil(ms) {
  var r = _psMod(ms, 86400000), z = (ms - r) / 86400000, h = _psFd(r, 3600000), mi, s, milli, wd, era, doe, yoe, y, doy, mp, d, m, yd;
  r = r % 3600000; mi = _psFd(r, 60000); r = r % 60000; s = _psFd(r, 1000); milli = r % 1000;
  wd = _psMod(z + 4, 7);
  z += 719468; era = _psFd(z, 146097); doe = z - era * 146097;
  yoe = _psFd(doe - _psFd(doe, 1460) + _psFd(doe, 36524) - _psFd(doe, 146096), 365); y = yoe + era * 400;
  doy = doe - (365 * yoe + _psFd(yoe, 4) - _psFd(yoe, 100)); mp = _psFd(5 * doy + 2, 153); d = doy - _psFd(153 * mp + 2, 5) + 1; m = mp < 10 ? mp + 3 : mp - 9;
  y += m <= 2 ? 1 : 0;
  yd = _psDays(y, m, d) - _psDays(y, 1, 1) + 1;
  return [y, m, d, h, mi, s, milli, wd, yd];
}
function _psMs(y, m, d, h, mi, s, milli) { return _psDays(y, m, d) * 86400000 + h * 3600000 + mi * 60000 + s * 1000 + milli; }
function _psParseDate(v) {
  if (!_psIsstr(v) || v.length > 40) return null;
  var m = _PS_DATE_RE.exec(_psTrim(v));
  if (!m) return null;
  var y = parseInt(m[1], 10), mo = parseInt(m[2] || '1', 10), d = parseInt(m[3] || '1', 10), h = parseInt(m[4] || '0', 10), mi = parseInt(m[5] || '0', 10), s = parseInt(m[6] || '0', 10);
  var f = (m[7] || '0'); while (f.length < 3) f += '0';
  if (y < 1 || mo < 1 || mo > 12 || d < 1 || d > _PS_DIM[mo - 1] + (mo === 2 && _psLeap(y) ? 1 : 0) || h > 23 || mi > 59 || s > 59) return null;
  return _psMs(y, mo, d, h, mi, s, parseInt(f, 10));
}
function _psP2(n, w) { var s = String(n); while (s.length < (w || 2)) s = '0' + s; return s; }
function _psUtcFormat(ms, spec) {
  var c = _psCivil(ms), y = c[0], m = c[1], d = c[2], h = c[3], mi = c[4], s = c[5], milli = c[6], wd = c[7], yd = c[8], out = '', i, k, sp;
  for (i = 0; i < spec.length; i++) {
    if (spec.charAt(i) === '%' && i + 1 < spec.length) {
      i++; k = spec.charAt(i);
      out += k === 'Y' ? _psP2(y, 4) : k === 'y' ? _psP2(_psMod(y, 100)) : k === 'm' ? _psP2(m) : k === 'd' ? _psP2(d) : k === 'e' ? (d < 10 ? ' ' + d : String(d)) : k === 'H' ? _psP2(h) :
        k === 'I' ? _psP2(h % 12 || 12) : k === 'p' ? (h < 12 ? 'AM' : 'PM') : k === 'M' ? _psP2(mi) : k === 'S' ? _psP2(s) : k === 'L' ? _psP2(milli, 3) : k === 'b' ? _PS_MON[m - 1] :
        k === 'B' ? _PS_MONL[m - 1] : k === 'a' ? _PS_DAY[wd] : k === 'A' ? _PS_DAYL[wd] : k === 'j' ? _psP2(yd, 3) : k === '%' ? '%' : '%' + k;
    } else out += spec.charAt(i);
  }
  return out;
}
function _psFloorUnit(ms, unit) {
  var size = _PS_UNIT_MS[unit];
  if (size) return ms - _psMod(ms, size);
  var c = _psCivil(ms), day0 = _psDays(c[0], c[1], c[2]);
  if (unit === 'week') return (day0 - c[7]) * 86400000;
  if (unit === 'month') return _psDays(c[0], c[1], 1) * 86400000;
  return _psDays(c[0], 1, 1) * 86400000;
}
function _psNextUnit(ms, unit) {
  var size = _PS_UNIT_MS[unit] || (unit === 'week' ? 604800000 : 0);
  if (size) return ms + size;
  var c = _psCivil(ms), y = c[0], m = c[1];
  if (unit === 'month') return _psDays(y + (m === 12 ? 1 : 0), m === 12 ? 1 : m + 1, 1) * 86400000;
  return _psDays(y + 1, 1, 1) * 86400000;
}
function _psCeilUnit(ms, unit) {
  var size = _PS_UNIT_MS[unit], f;
  if (size) return 0 - _psFd(0 - ms, size) * size;
  f = _psFloorUnit(ms, unit);
  return f === ms ? f : _psNextUnit(f, unit);
}
function _psEveryOk(ms, unit, k) {
  if (k <= 1) return true;
  // d3's utc ticker uses unixDay (no field): the day count since the epoch, not the day of the month
  var c = _psCivil(ms), v = unit === 'second' ? c[5] : unit === 'minute' ? c[4] : unit === 'hour' ? c[3] : unit === 'day' ? _psFd(ms, 86400000) : unit === 'month' ? c[1] - 1 : 0;
  return v % k === 0;
}
function _psTimeTicks(start, stop, count) {
  var rev = stop < start, target, i = 0, out = [], lim, inc, k, y, yy, t, iv, unit;
  if (rev) { t = start; start = stop; stop = t; }
  target = Math.abs(stop - start) / count;
  while (i < _PS_TICK_IVL.length && _PS_TICK_IVL[i][2] <= target) i++;
  lim = stop + 1;
  if (i === _PS_TICK_IVL.length) {
    inc = _hgTickSpec(start / 31536e6, stop / 31536e6, count)[2]; k = Math.floor(inc > 0 ? inc : 1 / -inc);
    if (k >= 1) {
      y = _psCivil(start)[0]; yy = _psFd(y, k) * k; t = _psDays(yy, 1, 1) * 86400000;
      while (t < start) { yy += k; t = _psDays(yy, 1, 1) * 86400000; }
      while (t < lim && out.length < 2000) { out.push(t); yy += k; t = _psDays(yy, 1, 1) * 86400000; }
    }
  } else if (i === 0) {
    // a zero-width domain: d3-array's tickIncrement is -Infinity there, so the step is 1 ms
    inc = start === stop ? -Infinity : _hgTickSpec(start, stop, count)[2]; k = Math.floor(Math.max(inc > 0 ? inc : 1 / -inc, 1));
    t = 0 - _psFd(0 - start, k) * k;
    while (t < lim && out.length < 2000) { out.push(t); t += k; }
  } else {
    iv = target / _PS_TICK_IVL[i - 1][2] < _PS_TICK_IVL[i][2] / target ? _PS_TICK_IVL[i - 1] : _PS_TICK_IVL[i]; unit = iv[0]; k = iv[1];
    t = _psCeilUnit(start, unit);
    while (t < lim && out.length < 2000) { if (_psEveryOk(t, unit, k)) out.push(t); t = _psNextUnit(t, unit); }
  }
  return rev ? out.reverse() : out;
}
function _psTickLabel(ms) {
  if (_psFloorUnit(ms, 'second') < ms) return _psUtcFormat(ms, '.%L');
  if (_psFloorUnit(ms, 'minute') < ms) return _psUtcFormat(ms, ':%S');
  if (_psFloorUnit(ms, 'hour') < ms) return _psUtcFormat(ms, '%I:%M');
  if (_psFloorUnit(ms, 'day') < ms) return _psUtcFormat(ms, '%I %p');
  if (_psFloorUnit(ms, 'month') < ms) return _psUtcFormat(ms, _psFloorUnit(ms, 'week') < ms ? '%a %d' : '%b %d');
  return _psUtcFormat(ms, _psFloorUnit(ms, 'year') < ms ? '%b' : '%Y');
}

function _psC(v) { return (Math.round(v * 100) / 100).toString(); }
function _psFixed2(v) { var s = v.toFixed(2); return /^-0\.00$/.test(s) ? '0.00' : s; }
function _psNumstr(v) { var s = v.toFixed(6); if (s.indexOf('.') >= 0) s = s.replace(/0+$/, '').replace(/\.$/, ''); return s === '-0' ? '0' : s; }
function _psXstr(ms) { var c = _psCivil(ms); return _psUtcFormat(ms, !(c[3] || c[4] || c[5]) ? '%Y-%m-%d' : (!c[5] ? '%Y-%m-%d %H:%M' : '%Y-%m-%d %H:%M:%S')); }
function _psColor(v, i) { return _psIsstr(v) && /^(?:#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|[a-zA-Z]{3,20})$/.test(v) ? v : _PS_PAL[i % _PS_PAL.length]; }
function _psThousands(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
function _psAxisLabel(b, ax) { var v = b[ax + '_label']; if (!_psIsstr(v) || !v) v = b['label_' + ax]; return _psIsstr(v) && v ? _ifS(v, 60) : ''; }
function _psExpand(p, shape) {
  var n = p.length, out, i, j, a, b, t, t2, t3, p0, p1, p2, p3, xm, ym;
  if (n < 2 || shape === 'linear') return p.slice();
  out = [p[0]];
  if (shape === 'spline') {
    if (n < 3) return p.slice();
    for (i = 0; i < n - 1; i++) {
      p0 = p[Math.max(i - 1, 0)]; p1 = p[i]; p2 = p[i + 1]; p3 = p[Math.min(i + 2, n - 1)];
      for (j = 1; j < 9; j++) {
        t = j / 8; t2 = t * t; t3 = t * t * t;
        out.push([0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                  0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)]);
      }
    }
    return out;
  }
  for (i = 0; i < n - 1; i++) {
    a = p[i]; b = p[i + 1];
    if (shape === 'hv') out.push([b[0], a[1]]);
    else if (shape === 'vh') out.push([a[0], b[1]]);
    else if (shape === 'hvh') { xm = (a[0] + b[0]) / 2; out.push([xm, a[1]]); out.push([xm, b[1]]); }
    else { ym = (a[1] + b[1]) / 2; out.push([a[0], ym]); out.push([b[0], ym]); }
    out.push(b);
  }
  return out;
}
function _psPath(pts, close) { return pts.map(function(q, i) { return (i === 0 ? 'M' : 'L') + _psC(q[0]) + ' ' + _psC(q[1]); }).join('') + (close ? 'Z' : ''); }
function _psMarker(sym, cx, cy, r) {
  var f = _psC, k;
  if (sym === 'square') return 'M' + f(cx - r) + ' ' + f(cy - r) + 'h' + f(2 * r) + 'v' + f(2 * r) + 'h' + f(-2 * r) + 'z';
  if (sym === 'diamond') { k = r * 1.3; return 'M' + f(cx) + ' ' + f(cy - k) + 'l' + f(k) + ' ' + f(k) + 'l' + f(-k) + ' ' + f(k) + 'l' + f(-k) + ' ' + f(-k) + 'z'; }
  if (sym === 'triangle-up') return 'M' + f(cx) + ' ' + f(cy - r) + 'l' + f(r) + ' ' + f(2 * r) + 'h' + f(-2 * r) + 'z';
  if (sym === 'cross') return 'M' + f(cx - r) + ' ' + f(cy) + 'h' + f(2 * r) + 'M' + f(cx) + ' ' + f(cy - r) + 'v' + f(2 * r);
  if (sym === 'x') return 'M' + f(cx - r) + ' ' + f(cy - r) + 'l' + f(2 * r) + ' ' + f(2 * r) + 'M' + f(cx - r) + ' ' + f(cy + r) + 'l' + f(2 * r) + ' ' + f(-2 * r);
  return 'M' + f(cx - r) + ' ' + f(cy) + 'a' + f(r) + ' ' + f(r) + ' 0 1 0 ' + f(2 * r) + ' 0a' + f(r) + ' ' + f(r) + ' 0 1 0 ' + f(-2 * r) + ' 0';
}
function _psStrokeSym(sym) { return sym === 'cross' || sym === 'x'; }
function _psSwatch(col, dash, sym, lines, markers) {
  var inner = '';
  if (lines) inner += '<path d="M1 7H29" fill="none" stroke="' + col + '" stroke-width="2"' + (_PS_DASH[dash] ? ' stroke-dasharray="' + _PS_DASH[dash] + '"' : '') + '/>';
  if (markers || !lines) inner += '<path d="' + _psMarker(sym, 15, 7, 4) + '" ' + (_psStrokeSym(sym) ? 'fill="none" stroke="' + col + '" stroke-width="1.6"' : 'fill="' + col + '"') + '/>';
  return '<svg width="30" height="14" viewBox="0 0 30 14" aria-hidden="true" focusable="false" style="flex:none;">' + inner + '</svg>';
}

function _psRender(b, atom) {
  var ser = b.series, pre = _psIsstr(b.title) ? _ifS(b.title, 80) : '', cap = 2000, mp = b.max_points, xt = (b.x_type === 'linear' || b.x_type === 'date') ? b.x_type : null;
  var notes = '', skipped = 0, rows = [], items = [], anytext = false, si, i, k, p, s, n, beyond;
  if (_psIsnum(mp)) cap = Math.round(Math.min(2000, Math.max(50, mp)));
  if (xt === null) {
    xt = 'linear';
    for (i = 0; i < ser.length; i++) {
      var xs0 = (ser[i] && typeof ser[i] === 'object' && !Array.isArray(ser[i])) ? ser[i].x : null;
      if (Array.isArray(xs0) && xs0.length && _psIsstr(xs0[0])) { xt = _psParseDate(xs0[0]) !== null ? 'date' : 'linear'; break; }
      if (Array.isArray(xs0) && xs0.length) break;
    }
  }
  beyond = Math.max(0, ser.length - _PS_MAX_SERIES);
  for (si = 0; si < Math.min(ser.length, _PS_MAX_SERIES); si++) {
    s = (ser[si] && typeof ser[si] === 'object' && !Array.isArray(ser[si])) ? ser[si] : {};
    var label = _psIsstr(s.label) && _psTrim(s.label) ? s.label : 'Series ' + (si + 1), xs = s.x, ys = s.y, tx = s.text, ysl = Array.isArray(ys) ? ys : [], pts = [], total, yv, xv, xm;
    n = Math.min(ysl.length, _PS_READ_CAP);
    if (ysl.length > _PS_READ_CAP) notes += _hgNote('Only the first 20,000 points of ' + _ifS(label, 40) + ' were read.');
    for (i = 0; i < n; i++) {
      yv = ysl[i];
      xv = Array.isArray(xs) ? (i < xs.length ? xs[i] : null) : i;
      if (xt === 'date') {
        xm = _psIsstr(xv) ? _psParseDate(xv) : ((_psIsnum(xv) && xv >= _PS_MS_MIN && xv <= _PS_MS_MAX) ? Math.floor(xv) : null);
        xv = xm !== null ? xm : null;
      } else if (!_psIsnum(xv)) xv = null;
      if (xv === null || !_psIsnum(yv)) { skipped++; continue; }
      pts.push([i, xv, yv]);
    }
    total = pts.length;
    if (total > cap) {
      var np = [];
      for (k = 0; k < cap; k++) np.push(pts[_psFd(k * (total - 1), cap - 1)]);
      pts = np;
      notes += _hgNote(_ifS(label, 40) + ' has ' + _psThousands(total) + ' points; ' + _psThousands(cap) + ' evenly spaced points are drawn and listed in the table.');
    }
    var toks = _psIsstr(s.mode) ? s.mode.split('+') : [], bad = !toks.length;
    toks.forEach(function(t) { if (_PS_MODES.indexOf(t) < 0) bad = true; });
    if (bad) toks = total <= 20 ? ['lines', 'markers'] : ['lines'];
    items.push({ label: label, pts: pts, tx: Array.isArray(tx) ? tx : null, lines: toks.indexOf('lines') >= 0, markers: toks.indexOf('markers') >= 0, text: toks.indexOf('text') >= 0,
      sym: _PS_SYMS.indexOf(s.symbol) >= 0 ? s.symbol : _PS_SYMS[si % _PS_SYMS.length], dash: _PS_DASH_NAMES.indexOf(s.dash) >= 0 ? s.dash : _PS_DASH_NAMES[si % _PS_DASH_NAMES.length],
      shape: _PS_SHAPES.indexOf(s.shape) >= 0 ? s.shape : 'linear', fill: (s.fill === 'tozeroy' || s.fill === 'tonexty') ? s.fill : '', col: _psColor(s.color, si), sz: s.size });
    anytext = anytext || Array.isArray(tx);
  }
  if (beyond) notes += _hgNote(beyond + (beyond === 1 ? ' series beyond the first 8 was' : ' series beyond the first 8 were') + ' not drawn.');
  if (skipped) notes += _hgNote(skipped + (skipped === 1 ? ' point was' : ' points were') + ' not a usable number' + (xt === 'date' ? ' or date' : '') + ' and ' + (skipped === 1 ? 'was' : 'were') + ' skipped.');
  notes += _hgVersionNote(b, atom);
  var allp = [];
  items.forEach(function(it) { it.pts.forEach(function(q) { allp.push(q); }); });
  var ttl = pre ? '<div style="font-weight:700;font-size:1.05rem;margin:0 0 10px;">' + pre + '</div>' : '';
  if (!allp.length) return _ifWrap(ttl + _hgNote('There are no points to draw.') + notes);
  var xl = _psAxisLabel(b, 'x'), yl = _psAxisLabel(b, 'y'), xv2 = allp.map(function(q) { return q[1]; }), yv2 = allp.map(function(q) { return q[2]; });
  var seenp = false, need0 = false;   // tozeroy fills down to y = 0; tonexty fills to the previous drawn series, and to y = 0 only where there is none
  items.forEach(function(it) { if (!need0 && (it.fill === 'tozeroy' || (it.fill === 'tonexty' && !seenp && it.pts.length))) need0 = true; seenp = seenp || it.pts.length > 0; });
  if (need0) yv2.push(0);
  var x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  xv2.forEach(function(v) { if (v < x0) x0 = v; if (v > x1) x1 = v; });
  yv2.forEach(function(v) { if (v < y0) y0 = v; if (v > y1) y1 = v; });
  var mnx = x0, mxx = x1;
  if (x0 === x1) { if (xt === 'date') { x0 -= 43200000; x1 += 43200000; } else { x0 -= 1; x1 += 1; } }
  if (y0 === y1) { y0 -= 1; y1 += 1; }
  var nz = _hgNice(y0, y1, 5); y0 = nz[0]; y1 = nz[1];
  var yt = _hgTicks(y0, y1, 5); if (!yt.length) yt = [y0, y1];
  var xtk = xt === 'date' ? _psTimeTicks(x0, x1, 4) : _hgTicks(x0, x1, 4);
  if (!xtk.length) xtk = [x0, x1];
  var iw = _PS_W - 2 * _PS_M, ih = _PS_H - 2 * _PS_M;
  function px(v) { return _PS_M + (v - x0) / (x1 - x0) * iw; }
  function py(v) { return _PS_M + (1 - (v - y0) / (y1 - y0)) * ih; }
  function pct(v, d) { return _psFixed2(v / d * 100) + '%'; }
  var dy = _hgDecimals(yt), dx = xt !== 'date' ? _hgDecimals(xtk) : 0, yz = Math.min(_PS_H - _PS_M, Math.max(_PS_M, py(0))), grid = '', ylab = '', xlab = '', gy, gx;
  yt.forEach(function(t) {
    gy = py(t);
    if (_PS_M - 0.001 <= gy && gy <= _PS_H - _PS_M + 0.001) {
      grid += '<line x1="' + _PS_M + '" y1="' + _psC(gy) + '" x2="' + (_PS_W - _PS_M) + '" y2="' + _psC(gy) + '" stroke="var(--border,#CBD5E1)" stroke-width="1" vector-effect="non-scaling-stroke"/>';
      ylab += '<div style="position:absolute;right:100%;top:' + pct(gy, _PS_H) + ';transform:translateY(-50%);padding-right:6px;font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + _esc(_hgNum(t, dy)) + '</div>';
    }
  });
  var lused = Object.create(null), sused = Object.create(null);
  xtk.forEach(function(t) {
    gx = px(t);
    if (_PS_M - 0.001 <= gx && gx <= _PS_W - _PS_M + 0.001) {
      grid += '<line x1="' + _psC(gx) + '" y1="' + _PS_M + '" x2="' + _psC(gx) + '" y2="' + (_PS_H - _PS_M) + '" stroke="var(--border,#CBD5E1)" stroke-width="1" vector-effect="non-scaling-stroke"/>';
      var tl = xt === 'date' ? _psTickLabel(t) : _hgNum(t, dx);
      xlab += '<div data-cb="label" data-key="' + _psUkey(tl, lused) + '" style="position:absolute;top:100%;left:' + pct(gx, _PS_W) + ';transform:translateX(-50%);margin-top:8px;font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + _esc(tl) + '</div>';
    }
  });
  grid += '<line x1="' + _PS_M + '" y1="' + _PS_M + '" x2="' + _PS_M + '" y2="' + (_PS_H - _PS_M) + '" stroke="var(--muted,#475569)" stroke-width="1" vector-effect="non-scaling-stroke"/>' +
    '<line x1="' + _PS_M + '" y1="' + (_PS_H - _PS_M) + '" x2="' + (_PS_W - _PS_M) + '" y2="' + (_PS_H - _PS_M) + '" stroke="var(--muted,#475569)" stroke-width="1" vector-effect="non-scaling-stroke"/>';
  var fills = '', lines = '', marks = '', labels = '', prev = null, legend = '';
  items.forEach(function(it) {
    var sp = it.pts.map(function(q) { return [px(q[1]), py(q[2])]; }), ex = _psExpand(sp, it.shape), col = it.col, poly, da, fd, sd, z, r, tv, tt, j, sk = _psUkey(it.label, sused), mk;
    if (it.fill && sp.length) {
      poly = (it.fill === 'tonexty' && prev) ? ex.concat(prev.slice().reverse()) : ex.concat([[ex[ex.length - 1][0], yz], [ex[0][0], yz]]);
      fills += '<path d="' + _psPath(poly, true) + '" fill="' + col + '" fill-opacity="0.15" stroke="none"/>';
    }
    if (it.lines && ex.length > 1) {
      da = _PS_DASH[it.dash];
      lines += '<path data-cb="branch" data-key="' + sk + '" d="' + _psPath(ex) + '" fill="none" stroke="' + col + '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"' + (da ? ' stroke-dasharray="' + da + '"' : '') + ' vector-effect="non-scaling-stroke"/>';
    }
    if (it.markers) {
      fd = ''; sd = '';
      for (j = 0; j < it.pts.length; j++) {
        z = Array.isArray(it.sz) ? (it.pts[j][0] < it.sz.length ? it.sz[it.pts[j][0]] : it.sz) : it.sz;
        r = _psIsnum(z) ? Math.min(40, Math.max(2, z)) / 2 : 3.5;
        if (_psStrokeSym(it.sym)) sd += _psMarker(it.sym, sp[j][0], sp[j][1], r); else fd += _psMarker(it.sym, sp[j][0], sp[j][1], r);
      }
      mk = ' data-cb="node" data-key="' + ((it.lines && ex.length > 1) ? _psUkey(it.label + '/markers', sused) : sk) + '"';
      if (fd) marks += '<path' + mk + ' d="' + fd + '" fill="' + col + '" stroke="var(--bg,#fff)" stroke-width="0.8"/>';
      if (sd) marks += '<path' + mk + ' d="' + sd + '" fill="none" stroke="' + col + '" stroke-width="1.6" vector-effect="non-scaling-stroke"/>';
    }
    if (it.text) {
      for (j = 0; j < it.pts.length; j++) {
        if (j >= _PS_TEXT_CAP) { notes += _hgNote('Only the first ' + _PS_TEXT_CAP + ' point labels of ' + _ifS(it.label, 40) + ' are drawn; all values are in the table.'); break; }
        tv = (it.tx !== null && it.pts[j][0] < it.tx.length) ? it.tx[it.pts[j][0]] : null;
        tt = (_psIsstr(tv) || _psIsnum(tv)) ? tv : _psNumstr(it.pts[j][2]);
        labels += '<div style="position:absolute;left:' + pct(sp[j][0], _PS_W) + ';top:' + pct(sp[j][1], _PS_H) + ';transform:translate(-50%,-135%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--text,#0F172A);">' + _ifS(tt, 20) + '</div>';
      }
    }
    if (sp.length) prev = ex;
    legend += '<span style="display:inline-flex;align-items:center;gap:6px;">' + _psSwatch(col, it.dash, it.sym, it.lines, it.markers) + '<span>' + _ifS(it.label, 40) + '</span></span>';
    it.pts.forEach(function(q) {
      tv = (it.tx !== null && q[0] < it.tx.length) ? it.tx[q[0]] : '';
      rows.push([it.label, xt === 'date' ? _psXstr(q[1]) : _psNumstr(q[1]), _psNumstr(q[2])].concat(anytext ? [(_psIsstr(tv) || _psIsnum(tv)) ? tv : ''] : []));
    });
  });
  var gist = (atom === 'scatter_trend' ? 'Scatter chart' : 'Line chart') + (_psIsstr(b.title) && b.title ? ' ' + _ifS(b.title, 60) : '') + ': ' + items.map(function(it) {
    var lo = Infinity, hi = -Infinity; it.pts.forEach(function(q) { if (q[2] < lo) lo = q[2]; if (q[2] > hi) hi = q[2]; });
    return _ifS(it.label, 30) + ' (' + it.pts.length + ' points' + (it.pts.length ? ', y from ' + _psNumstr(lo) + ' to ' + _psNumstr(hi) : '') + ')';
  }).join('; ') + '. x runs from ' + (xt === 'date' ? _psXstr(mnx) : _psNumstr(mnx)) + ' to ' + (xt === 'date' ? _psXstr(mxx) : _psNumstr(mxx)) + '.';
  var mb = 30;
  var plot = '<div role="img" aria-label="' + gist + '" style="position:relative;aspect-ratio:' + _PS_W + '/' + _PS_H + ';margin:6px 18px ' + mb + 'px 48px;">' +
    '<svg viewBox="0 0 ' + _PS_W + ' ' + _PS_H + '" width="100%" height="100%" aria-hidden="true" focusable="false" style="position:absolute;left:0;top:0;display:block;overflow:visible;" xmlns="http://www.w3.org/2000/svg">' +
    grid + fills + lines + marks + '</svg>' + ylab + xlab + labels +
    '</div>' + (xl ? '<div style="margin:0 18px 4px 48px;text-align:center;font-size:0.75rem;line-height:1.2;color:var(--muted,#475569);">' + xl + '</div>' : '');
  var head = yl ? '<div style="font-size:0.75rem;color:var(--muted,#475569);margin:0 0 2px;">' + yl + '</div>' : '';
  var leg = items.length > 1 ? '<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.75rem;line-height:1.2;margin-top:2px;">' + legend + '</div>' : '';
  return _ifWrap(ttl + '<div class="ifps" style="' + _ifCard() + '">' + head + plot + leg + '</div>' + _ifTable(['Series', 'X', 'Y'].concat(anytext ? ['Label'] : []), rows) + notes);
}

(function() {
  ['chartjs_line', 'scatter_trend'].forEach(function(atom) {
    var prev = _RENDERERS[atom];
    _RENDERERS[atom] = function(b) { return (b && Array.isArray(b.series) && b.series.length) ? _psRender(b, atom) : prev(b); };
  });
})();
