// ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
// Infographic atoms (2026-10-10, stage: preview). Twelve diagram-style atoms that had no home in the catalogue:
//   quadrant, bullet_graph, swimlane, gantt, change_chart, cycle_diagram, journey_map, maturity_ladder,
//   treemap, venn_diagram, callout_anatomy, org_chart.
//
// Design rules (the same for all twelve):
//  * Plain HTML and CSS (an SVG only where a line has to be drawn), no script, enum-only configuration, counted limits.
//  * MOTION-COMPATIBLE BY CONSTRUCTION: every moving value reads the custom property --p (build progress 0..1, default 1) through
//    --k per item, exactly like the motion_* atoms, so a motion_timeline track on `p` builds the atom and the standalone render is the
//    finished picture. Reduced motion needs no code here: the end state is p = 1.
//  * Text is escaped by _ifS; numbers are clamped by _ifNum; enums are picked from a fixed list. No payload text reaches a style or URL.
//  * Colour: neutrals follow the host (--text, --muted, --surface, --bg); status and category colours are fixed, verified tokens
//    (white text on them is 4.5:1 or better) and are never the only signal: a word, glyph or direct label sits next to every mark.
//  * An SVG is decoration (aria-hidden) and is followed by a visually hidden table with the same numbers.
// The layouts were first proved as static draw.io XML in a2ui-private/diagrams (mxkinds.py); these are the HTML twins.
// ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

var _IF_CAT = ['#19294E', '#810998', '#0F6C4F', '#9A6120'];                 // navy, plum, pine, bronze: white text >= 5.1:1
var _IF_SR = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;';
var _IF_FADE = 'opacity:var(--k,1);transform:translateY(calc((1 - var(--k,1))*8px));';
var _IF_BORDER = '1px solid #64748B';

function _ifS(v, max) { return _esc(String(v === undefined || v === null ? '' : v).slice(0, max || 80)); }
function _ifNum(v, lo, hi, d) { var n = Number(v); return isFinite(n) ? Math.min(hi, Math.max(lo, n)) : d; }
function _ifArr(v, max) { return Array.isArray(v) ? v.slice(0, max) : []; }
function _ifObj(v) { return (v && typeof v === 'object' && !Array.isArray(v)) ? v : {}; }
function _ifPick(v, allowed, d) { return allowed.indexOf(v) >= 0 ? v : d; }
function _ifK(i, n) { return '--k:clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1);'; }
function _ifFmt(n) { return (Math.round(n * 100) / 100).toString(); }
function _ifTitle(b) { return b.title ? '<div style="font-weight:700;font-size:1.05rem;margin:0 0 10px;">' + _ifS(b.title, 80) + '</div>' : ''; }
function _ifWrap(inner) { return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;color:var(--text,#0F172A);font-size:0.9rem;line-height:1.4;">' + inner + '</div>'; }
function _ifCard(extra) { return 'border:' + _IF_BORDER + ';border-radius:8px;background:var(--surface,#F8FAFC);padding:8px 10px;' + (extra || ''); }
function _ifTable(head, rows) {
  return '<table style="' + _IF_SR + '"><thead><tr>' + head.map(function(h) { return '<th scope="col">' + _ifS(h, 40) + '</th>'; }).join('') + '</tr></thead><tbody>' +
    rows.map(function(r) { return '<tr><th scope="row">' + _ifS(r[0], 60) + '</th>' + r.slice(1).map(function(c) { return '<td>' + _ifS(c, 60) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table>';
}

// ── quadrant ──────────────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['quadrant'] = function(b) {
  var xa = _ifObj(b.x_axis), ya = _ifObj(b.y_axis), items = _ifArr(b.items, 12), seen = {};
  var Q = [['top_left', ya.high, xa.low], ['top_right', ya.high, xa.high], ['bottom_left', ya.low, xa.low], ['bottom_right', ya.low, xa.high]];
  var cells = Q.map(function(q, qi) {
    var its = items.filter(function(i) { return i && i.quadrant === q[0]; }).slice(0, 3);
    return '<div style="' + _ifCard(_ifK(qi, 4) + _IF_FADE + 'min-height:96px;') + '"><div style="font-weight:700;font-size:0.78rem;color:var(--muted,#475569);margin-bottom:4px;">' +
      _ifS(q[1], 24) + ', ' + _ifS(q[2], 24) + '</div>' +
      its.map(function(i) {
        return '<div style="border:' + _IF_BORDER + ';border-radius:6px;padding:6px 8px;margin-top:4px;background:var(--bg,#fff);">' + _ifS(i.item, 28) +
          (i.note ? ': <span style="color:var(--muted,#475569);">' + _ifS(i.note, 40) + '</span>' : '') + '</div>';
      }).join('') + '</div>';
  });
  var lab = 'font-size:0.78rem;font-weight:700;color:var(--muted,#475569);';
  return _ifWrap(_ifTitle(b) + '<div style="display:grid;grid-template-columns:auto 1fr 1fr;gap:8px;">' +
    '<div style="' + lab + 'align-self:start;text-align:right;padding-top:8px;">' + _ifS(ya.high, 24) + '</div>' + cells[0] + cells[1] +
    '<div style="' + lab + 'align-self:end;text-align:right;padding-bottom:8px;">' + _ifS(ya.low, 24) + '</div>' + cells[2] + cells[3] +
    '<div></div><div style="' + lab + '">' + _ifS(xa.low, 24) + '</div><div style="' + lab + 'text-align:right;">' + _ifS(xa.high, 24) + '</div></div>');
};

// ── bullet_graph ──────────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['bullet_graph'] = function(b) {
  var rows = _ifArr(b.rows, 6).map(function(r, i, all) {
    r = _ifObj(r);
    var a = _ifNum(r.actual, 0, 1e9, 0), t = _ifNum(r.target, 0, 1e9, 0), rg = _ifArr(r.ranges, 3).map(function(v) { return _ifNum(v, 0, 1e9, 0); }).sort(function(x, y) { return x - y; });
    while (rg.length < 3) rg.push(rg.length ? rg[rg.length - 1] : 1);
    var top = Math.max(rg[2], t, a) || 1, pc = function(v) { return (v / top * 100).toFixed(2) + '%'; }, bands = ['#BFDBFE', '#60A5FA', '#2563EB'], prev = 0;
    var track = rg.map(function(v, bi) { var s = 'position:absolute;top:0;bottom:0;left:' + pc(prev) + ';width:' + ((v - prev) / top * 100).toFixed(2) + '%;background:' + bands[bi] + ';'; prev = v; return '<div style="' + s + '"></div>'; }).join('') +
      '<div style="position:absolute;left:0;top:9px;height:10px;width:calc(var(--k,1)*' + (a / top * 100).toFixed(2) + '%);background:#0F172A;"></div>' +
      '<div style="position:absolute;left:calc(' + pc(t) + ' - 1.5px);top:-3px;width:3px;height:34px;background:#B91C1C;"></div>';
    return '<div style="display:grid;grid-template-columns:minmax(110px,28%) 1fr auto;gap:10px;align-items:center;margin:8px 0;' + _ifK(i, all.length) + '"><div>' + _ifS(r.label, 40) + '</div>' +
      '<div style="position:relative;height:28px;border:' + _IF_BORDER + ';border-radius:4px;overflow:visible;">' + track + '</div>' +
      '<div style="font-weight:700;font-size:0.82rem;white-space:nowrap;">' + _ifFmt(a) + ' / ' + _ifFmt(t) + ' <span style="font-weight:400;color:var(--muted,#475569);">' + (a >= t ? 'target met' : 'below target') + '</span></div></div>';
  }).join('');
  return _ifWrap(_ifTitle(b) + rows + '<div style="font-size:0.75rem;color:var(--muted,#475569);">Dark bar: actual. Red tick: target. Shaded bands: poor, fair, good. The scale starts at 0.</div>');
};

// ── swimlane ──────────────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['swimlane'] = function(b) {
  var roles = _ifArr(b.roles, 4), phases = _ifArr(b.phases, 5), tasks = _ifArr(b.tasks, 12), n = tasks.length;
  var head = '<div></div>' + phases.map(function(p) { return '<div style="text-align:center;font-weight:700;font-size:0.8rem;padding:4px;border-radius:6px;background:#E0E7FF;color:#1E1B4B;">' + _ifS(p, 24) + '</div>'; }).join('');
  var lanes = roles.map(function(r) {
    return '<div style="' + _ifCard('font-weight:700;display:flex;align-items:center;') + '">' + _ifS(r, 24) + '</div>' + phases.map(function(p) {
      var cell = tasks.map(function(t, ti) { return [t, ti]; }).filter(function(x) { return x[0] && x[0].role === r && x[0].phase === p; }).slice(0, 2);
      return '<div style="' + _ifCard('background:var(--surface,#F8FAFC);min-height:64px;display:flex;flex-direction:column;gap:4px;') + '">' + cell.map(function(x) {
        return '<div style="display:flex;gap:6px;align-items:flex-start;border:' + _IF_BORDER + ';border-radius:6px;padding:5px 7px;background:var(--bg,#fff);' + _ifK(x[1], n) + _IF_FADE + '">' +
          '<span style="flex:0 0 auto;min-width:20px;height:20px;border-radius:50%;background:#0369A1;color:#fff;font-size:0.72rem;font-weight:700;text-align:center;line-height:20px;">' + (x[1] + 1) + '</span><span>' + _ifS(x[0].task, 60) + '</span></div>';
      }).join('') + '</div>';
    }).join('');
  }).join('');
  return _ifWrap(_ifTitle(b) + '<div style="display:grid;grid-template-columns:minmax(90px,16%) repeat(' + Math.max(phases.length, 1) + ',1fr);gap:6px;">' + head + lanes + '</div>' +
    '<div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:6px;">Numbers show the order of the tasks.</div>');
};

// ── gantt ─────────────────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['gantt'] = function(b) {
  var iv = _ifArr(b.intervals, 16), tasks = _ifArr(b.tasks, 10), N = Math.max(iv.length, 1), cats = [];
  tasks.forEach(function(t) { t = _ifObj(t); var c = String(t.category === undefined ? '' : t.category).slice(0, 16); if (cats.indexOf(c) < 0 && cats.length < 4) cats.push(c); });
  var head = '<div></div>' + iv.map(function(p) { return '<div style="text-align:center;font-weight:700;font-size:0.78rem;border-left:1px solid #CBD5E1;">' + _ifS(p, 10) + '</div>'; }).join('');
  var rows = tasks.map(function(t, i) {
    t = _ifObj(t);
    var s = Math.round(_ifNum(t.start_slot, 0, N - 1, 0)), d = Math.round(_ifNum(t.duration_slots, 1, N - s, 1)), ci = Math.max(0, cats.indexOf(String(t.category === undefined ? '' : t.category).slice(0, 16)));
    return '<div style="padding:4px 8px 4px 0;align-self:center;grid-row:' + (i + 2) + ';">' + _ifS(t.task, 40) + '</div>' +
      '<div style="grid-row:' + (i + 2) + ';grid-column:' + (s + 2) + ' / span ' + d + ';padding:3px 2px;"><div style="height:22px;border-radius:5px;background:' + _IF_CAT[ci] + ';transform:scaleX(var(--k,1));transform-origin:left;' + _ifK(i, tasks.length) + '"></div></div>';
  }).join('');
  var key = cats.map(function(c, ci) { return '<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px;"><span style="width:12px;height:12px;border-radius:3px;background:' + _IF_CAT[ci] + ';display:inline-block;"></span>' + _ifS(c, 16) + '</span>'; }).join('');
  return _ifWrap(_ifTitle(b) + '<div style="display:grid;grid-template-columns:minmax(120px,26%) repeat(' + N + ',1fr);row-gap:4px;">' + head + rows + '</div>' +
    '<div style="margin-top:8px;font-size:0.78rem;">' + key + '</div>' +
    _ifTable(['Task', 'Start', 'Length', 'Category'], tasks.map(function(t) { t = _ifObj(t); var s = Math.round(_ifNum(t.start_slot, 0, N - 1, 0)); return [t.task, iv[s], Math.round(_ifNum(t.duration_slots, 1, N - s, 1)), t.category]; })));
};

// ── change_chart (dumbbell | slope | bars) ────────────────────────────────────────────────────────────────────
_RENDERERS['change_chart'] = function(b) {
  var mode = _ifPick(b.mode, ['dumbbell', 'slope', 'bars'], 'dumbbell'), rows = _ifArr(b.rows, 12).map(function(r) { r = _ifObj(r); return { l: r.label, a: _ifNum(r.from, 0, 1e12, 0), c: _ifNum(r.to, 0, 1e12, 0) }; });
  var names = _ifArr(b.series, 2).map(function(s) { return String(s).slice(0, 20); }); while (names.length < 2) names.push(names.length ? 'After' : 'Before');
  var top = Math.max.apply(null, rows.map(function(r) { return Math.max(r.a, r.c); }).concat([1])) * 1.05, n = rows.length, body = '', eq = _ifTable(['Item', names[0], names[1], 'Change'], rows.map(function(r) { return [r.l, _ifFmt(r.a), _ifFmt(r.c), r.a ? ((r.c - r.a) / r.a * 100).toFixed(1) + '%' : 'n/a']; }));
  if (mode === 'bars') {
    body = rows.map(function(r, i) {
      return '<div style="display:grid;grid-template-columns:minmax(110px,26%) 1fr;gap:10px;margin:8px 0;' + _ifK(i, n) + '"><div>' + _ifS(r.l, 40) + '</div><div>' +
        [[r.a, _IF_CAT[0], names[0]], [r.c, _IF_CAT[3], names[1]]].map(function(v) {
          return '<div style="display:flex;align-items:center;gap:6px;margin:2px 0;"><div style="height:14px;border-radius:3px;background:' + v[1] + ';width:calc(var(--k,1)*' + (v[0] / top * 78).toFixed(2) + '%);min-width:2px;"></div><span style="font-size:0.78rem;font-weight:700;white-space:nowrap;">' + _ifS(v[2], 20) + ' ' + _ifFmt(v[0]) + '</span></div>';
        }).join('') + '</div></div>';
    }).join('') + '<div style="font-size:0.75rem;color:var(--muted,#475569);">Bars start at 0 and share one scale.</div>';
    return _ifWrap(_ifTitle(b) + body);
  }
  var W = 640, rowH = mode === 'dumbbell' ? 34 : 0, H, svg = '';
  if (mode === 'dumbbell') {
    var lw = 170, tw = W - lw - 150; H = n * rowH + 8;
    svg = rows.map(function(r, i) {
      var xa = lw + r.a / top * tw, xc = lw + r.c / top * tw, y = i * rowH + 17;
      return '<g style="' + _ifK(i, n) + 'opacity:var(--k,1);"><text x="0" y="' + (y + 4) + '" font-size="12" fill="currentColor">' + _ifS(r.l, 28) + '</text><line x1="' + xa.toFixed(1) + '" y1="' + y + '" x2="' + xc.toFixed(1) + '" y2="' + y + '" stroke="#64748B" stroke-width="2"/>' +
        '<circle cx="' + xa.toFixed(1) + '" cy="' + y + '" r="7" fill="#475569"/><circle cx="' + xc.toFixed(1) + '" cy="' + y + '" r="7" fill="#0369A1"/>' +
        '<text x="' + (Math.max(xa, xc) + 14).toFixed(1) + '" y="' + (y + 4) + '" font-size="11" font-weight="700" fill="currentColor">' + _ifFmt(r.a) + ' → ' + _ifFmt(r.c) + '</text></g>';
    }).join('');
  } else {
    var gap = Math.max(26, 30), lx = 200, rx = 440, pad = 28; H = Math.max(220, n * gap) + pad * 2;
    var lo = 0, ys = function(v) { return pad + (H - 2 * pad) * (1 - (v - lo) / (top - lo)); };
    var spread = function(arr) { var o = {}, last = -1e9; arr.map(function(v, i) { return [i, v]; }).sort(function(p, q) { return p[1] - q[1]; }).forEach(function(p) { var y = Math.max(p[1], last + 15); o[p[0]] = y; last = y; }); return o; };
    var L = spread(rows.map(function(r) { return ys(r.a); })), R = spread(rows.map(function(r) { return ys(r.c); }));
    svg = '<text x="' + lx + '" y="14" font-size="12" font-weight="700" text-anchor="middle" fill="currentColor">' + _ifS(names[0], 20) + '</text><text x="' + rx + '" y="14" font-size="12" font-weight="700" text-anchor="middle" fill="currentColor">' + _ifS(names[1], 20) + '</text>' +
      rows.map(function(r, i) {
        return '<g style="' + _ifK(i, n) + '"><path d="M' + lx + ' ' + ys(r.a).toFixed(1) + ' L' + rx + ' ' + ys(r.c).toFixed(1) + '" pathLength="1" fill="none" stroke="#0369A1" stroke-width="2" stroke-dasharray="1" style="stroke-dashoffset:calc(1 - var(--k,1));"/>' +
          '<text x="' + (lx - 10) + '" y="' + (L[i] + 4).toFixed(1) + '" font-size="11" text-anchor="end" fill="currentColor">' + _ifS(r.l, 20) + ' ' + _ifFmt(r.a) + '</text>' +
          '<text x="' + (rx + 10) + '" y="' + (R[i] + 4).toFixed(1) + '" font-size="11" fill="currentColor">' + _ifFmt(r.c) + ' ' + _ifS(r.l, 20) + '</text></g>';
      }).join('');
  }
  return _ifWrap(_ifTitle(b) + '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" style="max-width:' + W + 'px;display:block;" aria-hidden="true" focusable="false">' + svg + '</svg>' +
    '<div style="font-size:0.75rem;color:var(--muted,#475569);">' + (mode === 'dumbbell' ? 'Grey dot: ' + _ifS(names[0], 20) + '. Blue dot: ' + _ifS(names[1], 20) + '. The scale starts at 0.' : 'Each line joins the two values for one item.') + '</div>' + eq);
};

// ── cycle_diagram ─────────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['cycle_diagram'] = function(b) {
  var st = _ifArr(b.stages, 6), n = st.length || 1, VH = n <= 4 ? 340 : 430, boxes = '', lines = '', pos = [];
  for (var i = 0; i < st.length; i++) { var a = -Math.PI / 2 + 2 * Math.PI * i / n; pos.push([50 + 34 * Math.cos(a), 50 + (n <= 4 ? 33 : 38) * Math.sin(a)]); }
  st.forEach(function(s, i) {
    s = _ifObj(s);
    boxes += '<div style="position:absolute;left:' + pos[i][0].toFixed(2) + '%;top:' + pos[i][1].toFixed(2) + '%;width:26%;transform:translate(-50%,-50%);' + _ifCard(_ifK(i, n) + 'opacity:var(--k,1);') + '"><div style="font-weight:700;">' + (i + 1) + '. ' + _ifS(s.name, 24) + '</div><div style="font-size:0.78rem;color:var(--muted,#475569);">' + _ifS(s.description, 60) + '</div></div>';
    var q = pos[(i + 1) % n], p = pos[i], dx = (q[0] - p[0]) * 10, dy = (q[1] - p[1]) * VH / 100, px = p[0] * 10, py = p[1] * VH / 100;
    lines += '<line x1="' + (px + dx * 0.3).toFixed(1) + '" y1="' + (py + dy * 0.3).toFixed(1) + '" x2="' + (px + dx * 0.7).toFixed(1) + '" y2="' + (py + dy * 0.7).toFixed(1) + '" stroke="#64748B" stroke-width="2.5" marker-end="url(#ifarr)" style="opacity:var(--k,1);' + _ifK(i, n) + '"/>';
  });
  return _ifWrap(_ifTitle(b) + '<div style="position:relative;aspect-ratio:1000/' + VH + ';"><svg viewBox="0 0 1000 ' + VH + '" width="100%" height="100%" style="position:absolute;inset:0;" aria-hidden="true" focusable="false">' +
    '<defs><marker id="ifarr" markerWidth="12" markerHeight="12" refX="9" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,1 L12,6 L0,11 z" fill="#64748B"/></marker></defs>' + lines + '</svg>' + boxes + '</div>' +
    '<ol style="' + _IF_SR + '">' + st.map(function(s) { s = _ifObj(s); return '<li>' + _ifS(s.name, 24) + '. ' + _ifS(s.description, 60) + '</li>'; }).join('') + '</ol><div style="' + _IF_SR + '">The last stage loops back to the first.</div>');
};

// ── journey_map ───────────────────────────────────────────────────────────────────────────────────────────────
var _IF_SENT = { positive: ['#15803D', '+ Positive'], neutral: ['#475569', '= Neutral'], negative: ['#B91C1C', '− Negative'] };
_RENDERERS['journey_map'] = function(b) {
  var st = _ifArr(b.stages, 6), n = st.length || 1;
  var cols = st.map(function(s, i) {
    s = _ifObj(s); var se = _IF_SENT[_ifPick(s.sentiment, ['positive', 'neutral', 'negative'], 'neutral')];
    return '<div style="display:flex;flex-direction:column;gap:6px;' + _ifK(i, n) + _IF_FADE + '"><div style="text-align:center;font-weight:700;padding:5px;border-radius:6px;background:#E0E7FF;color:#1E1B4B;">' + _ifS(s.stage, 24) + '</div>' +
      '<div style="' + _ifCard() + '"><div style="font-size:0.72rem;font-weight:700;color:var(--muted,#475569);">Goal</div>' + _ifS(s.user_goal, 60) + '</div>' +
      '<div style="text-align:center;font-weight:700;padding:4px;border-radius:6px;background:' + se[0] + ';color:#fff;">' + se[1] + '</div>' +
      '<div style="' + _ifCard() + '"><div style="font-size:0.72rem;font-weight:700;color:var(--muted,#475569);">Friction</div>' + _ifS(s.friction_point, 80) + '</div></div>';
  }).join('');
  return _ifWrap(_ifTitle(b) + '<div style="display:grid;grid-template-columns:repeat(' + n + ',minmax(0,1fr));gap:8px;">' + cols + '</div>');
};

// ── maturity_ladder ───────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['maturity_ladder'] = function(b) {
  var lv = _ifArr(b.levels, 6), n = lv.length || 1;
  var steps = lv.map(function(l, i) {
    l = _ifObj(l); var cur = l.is_current === true;
    return '<div style="flex:1;min-width:0;min-height:' + (84 + i * 36) + 'px;border:' + _IF_BORDER + ';border-radius:8px;padding:8px 10px;background:' + (cur ? '#0369A1' : 'var(--surface,#F8FAFC)') + ';color:' + (cur ? '#fff' : 'var(--text,#0F172A)') + ';' + _ifK(i, n) + _IF_FADE + '">' +
      '<div style="font-weight:700;">Level ' + _ifS(l.level, 3) + ': ' + _ifS(l.name, 30) + (cur ? ' [CURRENT]' : '') + '</div><div style="font-size:0.78rem;margin-top:4px;' + (cur ? '' : 'color:var(--muted,#475569);') + '">' + _ifS(l.criteria, 120) + '</div></div>';
  }).join('');
  return _ifWrap(_ifTitle(b) + '<div style="display:flex;align-items:flex-end;gap:6px;">' + steps + '</div>');
};

// ── treemap ───────────────────────────────────────────────────────────────────────────────────────────────────
// Squarified treemap layout: a line-for-line port of d3-hierarchy 3.1.2 treemapSquarify (ISC, Mike Bostock); twin of _tm_squarify in renderers/web_article.py.
// Laid out in a nominal 900 x 300 box, no padding, no rounding; the renderer emits the rectangles as percentages and draws the gaps in CSS.
var _TM_PHI = (1 + Math.sqrt(5)) / 2, _TM_W = 900, _TM_H = 300;
function _tmSum(vals) { var s = 0, i = vals.length; while (--i >= 0) s += vals[i]; return s; }
function _tmSquarify(vals, x0, y0, x1, y1, pv) {  // pv: the parent's value as d3 summed it (input order); a sorted layout must pass it
  var n = vals.length, out = new Array(n), value = pv === undefined ? _tmSum(vals) : pv, i0 = 0, i1 = 0, dx, dy, sv, mn, mx, alpha, beta, mr, nr, nv, rx0, ry0, ry1, rx1, k, px, py, j;
  while (i0 < n) {
    dx = x1 - x0; dy = y1 - y0;
    do sv = +vals[i1++]; while (!sv && i1 < n);
    mn = mx = sv;
    alpha = Math.max(dy / dx, dx / dy) / (value * _TM_PHI);
    beta = sv * sv * alpha;
    mr = Math.max(mx / beta, beta / mn);
    for (; i1 < n; ++i1) {
      sv += nv = +vals[i1];
      if (nv < mn) mn = nv;
      if (nv > mx) mx = nv;
      beta = sv * sv * alpha;
      nr = Math.max(mx / beta, beta / mn);
      if (nr > mr) { sv -= nv; break; }
      mr = nr;
    }
    rx0 = x0; ry0 = y0;
    if (dx < dy) {
      if (value) { y0 += dy * sv / value; ry1 = y0; } else ry1 = y1;
      k = sv ? (x1 - rx0) / sv : 0; px = rx0;
      for (j = i0; j < i1; j++) { out[j] = [px, ry0, 0, ry1]; px += vals[j] * k; out[j][2] = px; }
    } else {
      if (value) { x0 += dx * sv / value; rx1 = x0; } else rx1 = x1;
      k = sv ? (y1 - ry0) / sv : 0; py = ry0;
      for (j = i0; j < i1; j++) { out[j] = [rx0, py, rx1, 0]; py += vals[j] * k; out[j][3] = py; }
    }
    value -= sv; i0 = i1;
  }
  return out;
}
function _tmLayout(groups) {
  var cr = _tmSquarify(groups.map(_tmSum), 0, 0, _TM_W, _TM_H);
  return [cr, groups.map(function(g, i) { return _tmSquarify(g, cr[i][0], cr[i][1], cr[i][2], cr[i][3]); })];
}
// A label's width is estimated, identically in both twins, as 0.6em per character of the 0.78rem (12.48px) bold label font, plus padding.
// The chart is drawn at whatever width its container has, so the width a label needs is turned into the narrowest container it fits in
// (_tmWmin). A label needing more than 320px is gated by a container query rule (class tmw<N> hides it below N px); one that cannot fit
// even in 1600px is left out. Heights are exact: the chart is always 300px high, the same as its nominal box.
var _TM_K = 7.488, _TM_HDR = 20, _TM_MAXW = 1600, _TM_MINW = 320;
function _tmWmin(chars, pad, w) { return w > 0 ? Math.ceil((chars * _TM_K + pad) * _TM_W / w) : 1e9; }
function _tmPct(x, d) { return (x / d * 100).toFixed(3) + '%'; }
function _tmBox(r) { return 'position:absolute;left:' + _tmPct(r[0], _TM_W) + ';top:' + _tmPct(r[1], _TM_H) + ';width:' + _tmPct(r[2] - r[0], _TM_W) + ';height:' + _tmPct(r[3] - r[1], _TM_H) + ';'; }
// Nested treemap: a line-for-line port of d3-hierarchy 3.1.2 hierarchy().sum().sort(by value, descending) and treemap().tile(treemapSquarify)
// .size([900, 300]) with paddingInner 2 and, below the root, paddingOuter 3 and a 20 high paddingTop (the group header); no rounding.
// root: {n, c: [children]} for a group, {n, v} for a leaf. Returns every node in pre-order (d3 eachBefore): {depth, x0, y0, x1, y1, value, src, kids}.
// d3 hierarchy(d, c).sum(v).sort(by value, descending): {src, depth, kids (sorted, or null for a leaf), value}; children are added last to first.
function _tmBuild(d, depth) {
  var kids = (d.c instanceof Array && d.c.length) ? d.c : null, node = { src: d, depth: depth, kids: null, value: 0 }, i, s;
  if (!kids) { node.value = typeof d.v === 'number' && d.v === d.v ? d.v : 0; return node; }
  node.kids = kids.map(function(k) { return _tmBuild(k, depth + 1); });
  s = 0; i = node.kids.length; while (--i >= 0) s += node.kids[i].value;
  node.value = s;
  node.kids = node.kids.slice().sort(function(a, b) { return b.value - a.value; });
  return node;
}
function _tmNest(root) {
  var top = _tmBuild(root, 0), pad = { 0: 0 }, out = [], stack = [top], nd, p, x0, y0, x1, y1, outer, rects, i;
  top.x0 = top.y0 = 0; top.x1 = _TM_W; top.y1 = _TM_H;
  while (stack.length) {
    nd = stack.pop(); out.push(nd);
    p = pad[nd.depth];
    x0 = nd.x0 + p; y0 = nd.y0 + p; x1 = nd.x1 - p; y1 = nd.y1 - p;
    if (x1 < x0) x0 = x1 = (x0 + x1) / 2;
    if (y1 < y0) y0 = y1 = (y0 + y1) / 2;
    nd.x0 = x0; nd.y0 = y0; nd.x1 = x1; nd.y1 = y1;
    if (nd.kids) {
      p = pad[nd.depth + 1] = 2 / 2;
      outer = nd.depth ? 3 : 0;
      x0 += outer - p; y0 += (nd.depth ? _TM_HDR : 0) - p; x1 -= outer - p; y1 -= outer - p;
      if (x1 < x0) x0 = x1 = (x0 + x1) / 2;
      if (y1 < y0) y0 = y1 = (y0 + y1) / 2;
      rects = _tmSquarify(nd.kids.map(function(k) { return k.value; }), x0, y0, x1, y1, nd.value);
      for (i = 0; i < rects.length; i++) { nd.kids[i].x0 = rects[i][0]; nd.kids[i].y0 = rects[i][1]; nd.kids[i].x1 = rects[i][2]; nd.kids[i].y1 = rects[i][3]; }
      for (i = nd.kids.length - 1; i >= 0; i--) stack.push(nd.kids[i]);
    }
  }
  return out;
}
function _tmNestLayout(spec) { return _tmNest(spec).map(function(n) { return [n.depth, n.x0, n.y0, n.x1, n.y1, n.value, n.src.n]; }); }
// The usable group names of an item's `path`: strings that are not blank, 20 characters each, at most 3.
function _tmPath(raw) {
  if (!(raw instanceof Array)) return [];
  return raw.slice(0, 12).filter(function(e) { return typeof e === 'string' && e.replace(/[ \t\r\n]/g, '') !== ''; }).map(function(e) { return e.slice(0, 20); }).slice(0, 3);
}
// [class attribute, gate width]: a label needing more than 320px hides itself in a narrower container.
function _tmGate(w) { return w > _TM_MINW ? [' class="tmw' + w + '"', w] : ['', 0]; }
function _tmLabel(show, g, cls, text) { return show ? (g ? '<span' + cls + '>' + text + '</span>' : text) : ''; }
// The group tree of items that carry a chain (their ancestor group names, top down): [root {n, c}, tops] with the top-level entries in first-seen order.
// A group is {n, c, chain, topc}; a leaf is {n, v, item, k, topc}. An item with an empty chain is a leaf of the root and is its own top-level entry.
function _tmTree(items) {
  var root = { n: '', c: [] }, tops = [];
  items.forEach(function(i, k) {
    var node = root, leaf;
    i.chain.forEach(function(g) {
      var nx = null; node.c.forEach(function(x) { if (!nx && x.c && x.n === g) nx = x; });
      if (!nx) { nx = { n: g, c: [], chain: (node.chain || []).concat([g]) }; if (node === root) tops.push(nx); nx.topc = node === root ? tops.length - 1 : node.topc; node.c.push(nx); }
      node = nx;
    });
    leaf = { n: i.n, v: i.v, item: i, k: k };
    if (node === root) { tops.push(leaf); leaf.topc = tops.length - 1; } else leaf.topc = node.topc;
    node.c.push(leaf);
  });
  return [root, tops];
}
_RENDERERS['treemap'] = function(b) {
  // the optional 'version' field is read by _hgVersionNote at the end
  var items = _ifArr(b.items, 12).map(function(i) { i = _ifObj(i); return { c: String(i.category === undefined ? '' : i.category).slice(0, 20), n: i.name, v: _ifNum(i.value, 0, 1e12, 0), p: _tmPath(i.path) }; }).filter(function(i) { return i.v > 0; });
  var nested = items.some(function(i) { return i.p.length > 0; }), cats = [];
  if (!nested) { items.forEach(function(i) { if (cats.indexOf(i.c) < 0 && cats.length < 4) cats.push(i.c); }); items = items.filter(function(i) { return cats.indexOf(i.c) >= 0; }); }
  var tot = items.reduce(function(s, i) { return s + i.v; }, 0) || 1, cells = '', tags = '', boxes = '', gates = [], hid = [], aria = '', table, css = '', ws = [];
  if (nested) {
    items.forEach(function(i) { i.chain = i.p.length ? i.p : [i.c || 'Other']; });
    var tr = _tmTree(items), root = tr[0], tops = tr[1];
    _tmNest(root).slice(1).forEach(function(nd) {
      var sp = nd.src, r = [nd.x0, nd.y0, nd.x1, nd.y1], w = r[2] - r[0], h = r[3] - r[1], col = _IF_CAT[sp.topc % 4], txt, wm, show, gt, cls, g, name;
      if (nd.kids) {
        txt = _ifS(sp.n, 20) + ' ' + _ifFmt(nd.value); wm = _tmWmin(txt.length, 14, w); show = h >= 24 && wm <= _TM_MAXW; gt = _tmGate(wm); cls = gt[0]; g = show ? gt[1] : 0; gates.push(g);
        boxes += '<div' + (show && !g ? '' : ' title="' + txt + '"') + ' style="' + _tmBox(r) + 'box-sizing:border-box;border:1px solid ' + col + ';border-radius:4px;background:var(--surface,#F8FAFC);"></div>';
        if (show) tags += '<div' + cls + ' style="position:absolute;left:' + _tmPct(r[0], _TM_W) + ';top:' + _tmPct(r[1], _TM_H) + ';width:' + _tmPct(w, _TM_W) + ';height:' + _tmPct(_TM_HDR, _TM_H) +
          ';box-sizing:border-box;padding:1px 7px 0;overflow:hidden;white-space:nowrap;font-size:0.78rem;font-weight:700;line-height:18px;color:var(--text,#0F172A);">' + txt + '</div>';
      } else {
        name = _ifS(sp.item.n, 24) + ' ' + _ifFmt(sp.item.v); wm = _tmWmin(name.length, 18, w); show = h >= 30 && wm <= _TM_MAXW; gt = _tmGate(wm); cls = gt[0]; g = show ? gt[1] : 0; gates.push(g); hid.push(!show);
        cells += '<div' + (show && !g ? '' : ' title="' + name + '"') + ' style="' + _tmBox(r) + 'box-sizing:border-box;border:1px solid transparent;background:' + col + ';background-clip:padding-box;color:#fff;border-radius:4px;padding:' + (show ? '6px 8px 6px' : '0') + ';font-size:0.78rem;font-weight:700;overflow:hidden;' + _ifK(sp.k, 12) + 'opacity:var(--k,1);">' + _tmLabel(show, g, cls, name) + '</div>';
      }
    });
    var shown = tops.slice(0, 6).map(function(t) { return t.n + ' ' + _ifFmt(items.reduce(function(s, i) { return i.chain[0] === t.n ? s + i.v : s; }, 0)); }).join(', ');
    aria = ' role="img" aria-label="' + _ifS('Nested treemap of ' + items.length + ' items in ' + tops.length + ' top-level group' + (tops.length === 1 ? '' : 's') + ', area shows share of the total ' + _ifFmt(tot) + ': ' + shown + (tops.length <= 6 ? '' : ', and ' + (tops.length - 6) + ' more') + '.', 400) + '"';
    table = _ifTable(['Item', 'Path', 'Value', 'Share'], items.map(function(i) { return [i.n, i.chain.join(' / '), _ifFmt(i.v), (i.v / tot * 100).toFixed(1) + '%']; }));
  } else {
    var groups = cats.map(function(c) { return items.filter(function(i) { return i.c === c; }); });
    var lay = _tmLayout(groups.map(function(m) { return m.map(function(i) { return i.v; }); })), cr = lay[0], ir = lay[1];
    cats.forEach(function(c, ci) {
      var m = groups[ci], ct = m.reduce(function(s, i) { return s + i.v; }, 0), ptxt = _ifS(c, 20) + ' ' + _ifFmt(ct), pw = _tmWmin(ptxt.length, 12, cr[ci][2] - cr[ci][0]);
      var pill = cr[ci][3] - cr[ci][1] >= 40 && pw <= _TM_MAXW, pg = _tmGate(pw), pcls = pg[0]; gates.push(pill ? pg[1] : 0);
      m.forEach(function(i, k) {
        var lead = pill && k === 0, name = _ifS(i.n, 24) + ' ' + _ifFmt(i.v), r = ir[ci][k], wm = _tmWmin(name.length, 18, r[2] - r[0]), show = r[3] - r[1] >= (lead ? 48 : 30) && wm <= _TM_MAXW, gt = _tmGate(wm), cls = gt[0], g = show ? gt[1] : 0;
        gates.push(g); hid.push(!show);
        cells += '<div' + (show && !g ? '' : ' title="' + name + '"') + ' style="' + _tmBox(r) + 'box-sizing:border-box;border:1px solid transparent;background:' + _IF_CAT[ci] + ';background-clip:padding-box;color:#fff;border-radius:4px;padding:' + (show ? (lead ? '24px' : '6px') + ' 8px 6px' : '0') + ';font-size:0.78rem;font-weight:700;overflow:hidden;' + _ifK(groups.slice(0, ci).reduce(function(s, g_) { return s + g_.length; }, 0) + k, 12) + 'opacity:var(--k,1);">' + _tmLabel(show, g, cls, name) + '</div>';
      });
      if (pill) tags += '<div' + pcls + ' style="position:absolute;left:' + _tmPct(cr[ci][0], _TM_W) + ';top:' + _tmPct(cr[ci][1], _TM_H) + ';max-width:' + _tmPct(cr[ci][2] - cr[ci][0], _TM_W) + ';box-sizing:border-box;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;background:rgba(15,23,42,0.6);color:#fff;border-radius:0 0 4px 0;padding:2px 6px;font-size:0.78rem;font-weight:700;">' + ptxt + '</div>';
    });
    table = _ifTable(['Item', 'Category', 'Value', 'Share'], items.map(function(i) { return [i.n, i.c, _ifFmt(i.v), (i.v / tot * 100).toFixed(1) + '%']; }));
  }
  gates.forEach(function(g) { if (g && ws.indexOf(g) < 0) ws.push(g); });
  ws.sort(function(a, c) { return a - c; });
  if (ws.length) css = '<style>' + ws.map(function(w) { return '@container (width<' + w + 'px){.tmw' + w + '{display:none}}'; }).join('') + '</style>';
  return _ifWrap(_ifTitle(b) + '<div' + aria + ' style="position:relative;height:300px;' + (css ? 'container-type:inline-size;' : '') + (css || hid.some(function(x) { return x; }) ? 'overflow:hidden;' : '') + '">' + css + boxes + cells + tags + '</div><div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">Area shows share of the total.' +
    (nested ? ' Boxes inside boxes are groups.' : '') + '</div>' + _hgVersionNote(b, 'treemap') + table);
};

// ── sunburst (I40) and its icicle layout (I54) ───────────────────────────────────────────────────────────────────────────────────────────────
// d3-hierarchy 3.1.2 partition() on the same hierarchy().sum().sort(by value, descending) as the nested treemap (_tmBuild), and d3-shape 3.2.0 arc()
// (the sector without rounded corners, with padAngle and padRadius) drawn through d3-path 3.1.0 arc() and its 3-digit number rounding (ISC, Mike Bostock);
// twin of _sb_partition / _sb_arc / _render_sunburst in renderers/web_article.py.
var _SB_R = 300, _SB_PAD = 0.005, _SB_PADR = 450, _SB_TAU = 2 * Math.PI, _SB_EPS = 1e-12;
function _sbPartition(root, dx, dy) {
  var top = _tmBuild(root, 0), out = [], stack = [top], nd, n, x0, y0, x1, y1, k, i, c;
  function height(m) { var h = 0, j; if (m.kids) for (j = 0; j < m.kids.length; j++) h = Math.max(h, 1 + height(m.kids[j])); return h; }
  n = height(top) + 1;
  top.x0 = top.y0 = 0; top.x1 = dx; top.y1 = dy / n;
  while (stack.length) {
    nd = stack.pop(); out.push(nd);
    if (nd.kids) {
      x0 = nd.x0; y0 = dy * (nd.depth + 1) / n; x1 = nd.x1; y1 = dy * (nd.depth + 2) / n;
      k = nd.value && (x1 - x0) / nd.value;
      for (i = 0; i < nd.kids.length; i++) { c = nd.kids[i]; c.y0 = y0; c.y1 = y1; c.x0 = x0; c.x1 = x0 += c.value * k; }
    }
    x0 = nd.x0; y0 = nd.y0; x1 = nd.x1; y1 = nd.y1;
    if (x1 < x0) x0 = x1 = (x0 + x1) / 2;
    if (y1 < y0) y0 = y1 = (y0 + y1) / 2;
    nd.x0 = x0; nd.y0 = y0; nd.x1 = x1; nd.y1 = y1;
    if (nd.kids) for (i = nd.kids.length - 1; i >= 0; i--) stack.push(nd.kids[i]);
  }
  return out;
}
function _sbRows(spec, dx, dy) { return _sbPartition(spec, dx, dy).map(function(n) { return [n.depth, n.x0, n.y0, n.x1, n.y1, n.value, n.src.n]; }); }
function _sbAsin(x) { return x >= 1 ? Math.PI / 2 : x <= -1 ? -Math.PI / 2 : Math.asin(x); }
// d3-path 3.1.0 Path: moveTo, lineTo, quadraticCurveTo, arc (the SVG arc commands), closePath; numbers rounded to `digits` (null = not rounded). Shared by
// _sbArc (sunburst) and the chord ribbons (_chRibbon).
function _D3Path(digits) { this.k = digits === null ? null : Math.pow(10, digits); this.d = ''; this.x0 = this.y0 = this.x1 = this.y1 = null; }
_D3Path.prototype.f = function(v) { return String(this.k === null ? v : Math.round(v * this.k) / this.k); };
_D3Path.prototype.moveTo = function(x, y) { this.x0 = this.x1 = x; this.y0 = this.y1 = y; this.d += 'M' + this.f(x) + ',' + this.f(y); };
_D3Path.prototype.lineTo = function(x, y) { this.x1 = x; this.y1 = y; this.d += 'L' + this.f(x) + ',' + this.f(y); };
_D3Path.prototype.quadTo = function(cx, cy, x, y) { this.x1 = x; this.y1 = y; this.d += 'Q' + this.f(cx) + ',' + this.f(cy) + ',' + this.f(x) + ',' + this.f(y); };
_D3Path.prototype.arc = function(x, y, rr, s0, s1, ccw) {
  var f = this.f.bind(this), dx = rr * Math.cos(s0), dy = rr * Math.sin(s0), x0 = x + dx, y0 = y + dy, w = ccw ? 0 : 1, a = ccw ? s0 - s1 : s1 - s0, ex, ey;
  if (this.x1 === null) { this.d += 'M' + f(x0) + ',' + f(y0); this.x0 = this.x1 = x0; this.y0 = this.y1 = y0; }
  else if (Math.abs(this.x1 - x0) > 1e-6 || Math.abs(this.y1 - y0) > 1e-6) { this.d += 'L' + f(x0) + ',' + f(y0); this.x1 = x0; this.y1 = y0; }
  if (!rr) return;
  if (a < 0) a = a % _SB_TAU + _SB_TAU;
  if (a > _SB_TAU - 1e-6) { this.d += 'A' + f(rr) + ',' + f(rr) + ',0,1,' + w + ',' + f(x - dx) + ',' + f(y - dy) + 'A' + f(rr) + ',' + f(rr) + ',0,1,' + w + ',' + f(x0) + ',' + f(y0); this.x1 = x0; this.y1 = y0; }
  else if (a > 1e-6) { ex = x + rr * Math.cos(s1); ey = y + rr * Math.sin(s1); this.d += 'A' + f(rr) + ',' + f(rr) + ',0,' + (a >= Math.PI ? 1 : 0) + ',' + w + ',' + f(ex) + ',' + f(ey); this.x1 = ex; this.y1 = ey; }
};
_D3Path.prototype.close = function() { if (this.x1 !== null) { this.x1 = this.x0; this.y1 = this.y0; this.d += 'Z'; } };
// The path text of d3-shape arc() with cornerRadius 0: startAngle a0, endAngle a1 (radians clockwise from 12 o'clock), inner radius r0, outer radius r1, padAngle,
// padRadius (null = sqrt(r0^2 + r1^2)); numbers rounded to `digits` (null = not rounded) as d3-path does.
function _sbArc(a0, a1, r0, r1, padAngle, padRadius, digits) {
  var pth = new _D3Path(digits), r, da, cw, a01, a11, a00, a10, da0, da1, ap, rp, p0, p1, sa, x01, y01, x10, y10;
  function move(x, y) { pth.moveTo(x, y); }
  function line(x, y) { pth.lineTo(x, y); }
  function arc(x, y, rr, s0, s1, ccw) { pth.arc(x, y, rr, s0, s1, ccw); }
  a0 -= Math.PI / 2; a1 -= Math.PI / 2; da = Math.abs(a1 - a0); cw = a1 > a0;
  if (r1 < r0) { r = r1; r1 = r0; r0 = r; }
  if (!(r1 > _SB_EPS)) move(0, 0);
  else if (da > _SB_TAU - _SB_EPS) {
    move(r1 * Math.cos(a0), r1 * Math.sin(a0)); arc(0, 0, r1, a0, a1, !cw);
    if (r0 > _SB_EPS) { move(r0 * Math.cos(a1), r0 * Math.sin(a1)); arc(0, 0, r0, a1, a0, cw); }
  } else {
    a01 = a0; a11 = a1; a00 = a0; a10 = a1; da0 = da; da1 = da; ap = padAngle / 2;
    rp = (ap > _SB_EPS) && (padRadius !== null ? padRadius : Math.sqrt(r0 * r0 + r1 * r1));
    if (rp > _SB_EPS) {
      sa = Math.sin(ap);
      p0 = _sbAsin(rp / r0 * sa); p1 = _sbAsin(rp / r1 * sa);
      if ((da0 -= p0 * 2) > _SB_EPS) { p0 *= (cw ? 1 : -1); a00 += p0; a10 -= p0; } else { da0 = 0; a00 = a10 = (a0 + a1) / 2; }
      if ((da1 -= p1 * 2) > _SB_EPS) { p1 *= (cw ? 1 : -1); a01 += p1; a11 -= p1; } else { da1 = 0; a01 = a11 = (a0 + a1) / 2; }
    }
    x01 = r1 * Math.cos(a01); y01 = r1 * Math.sin(a01); x10 = r0 * Math.cos(a10); y10 = r0 * Math.sin(a10);
    move(x01, y01);
    if (da1 > _SB_EPS) arc(0, 0, r1, a01, a11, !cw);
    if (!(r0 > _SB_EPS) || !(da0 > _SB_EPS)) line(x10, y10); else arc(0, 0, r0, a10, a00, cw);
  }
  pth.close();
  return pth.d;
}
var _SB_PALETTE = ['#19294E', '#810998', '#0F6C4F', '#9A6120', '#0369A1', '#B4235A', '#4D6B0E', '#5B5F66'], _SB_SHADE = [0, 16, 40, 60];
function _sbFill(base, depth) {
  var pct = _SB_SHADE[Math.min(Math.max(depth, 1), 4) - 1];
  return '#' + [1, 3, 5].map(function(i) { var v = parseInt(base.slice(i, i + 2), 16), m = v + Math.floor(((255 - v) * pct + 50) / 100); return (m < 16 ? '0' : '') + m.toString(16).toUpperCase(); }).join('');
}
function _sbInk(fill) {
  function lin(v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
  var lum = 0.2126 * lin(parseInt(fill.slice(1, 3), 16)) + 0.7152 * lin(parseInt(fill.slice(3, 5), 16)) + 0.0722 * lin(parseInt(fill.slice(5, 7), 16));
  return lum <= 0.179 ? '#FFFFFF' : '#000000';
}
// A label's width is estimated, identically in both twins, as 0.6em per character of the 12px label font; see _SB_K in renderers/web_article.py.
var _SB_K = 7.2, _SB_MINW = 240, _SB_MAXW = 640, _SB_BOX = 604, _SB_LINE = 18, _SB_IW = 900, _SB_IH = 360, _SB_IMAXW = 1600;
function _sbQ(w) { return Math.ceil(w / 10) * 10; }
function _sbCls(wm) { return wm > _SB_MINW ? [' tmw' + wm, wm] : ['', 0]; }
function _sbBox(l, t, w, h) { return 'position:absolute;left:' + _tmPct(l, _SB_IW) + ';top:' + _tmPct(t, _SB_IH) + ';width:' + _tmPct(w, _SB_IW) + ';height:' + _tmPct(h, _SB_IH) + ';'; }
_RENDERERS['sunburst'] = function(b) {
  // the optional 'version' field is read by _hgVersionNote at the end
  var lst = Array.isArray(b.items) ? b.items : [], items = [], leftOut = 0;
  lst.slice(0, 40).forEach(function(it, k) {
    var v = (it && typeof it === 'object' && !Array.isArray(it)) ? _ifNum(it.value, 0, 1e12, 0) : 0;
    if (!(v > 0)) { leftOut++; return; }
    items.push({ n: it.name ? String(it.name).slice(0, 24) : 'Item ' + (k + 1), v: v, chain: _tmPath(it.path) });
  });
  var beyond = lst.length - 40;
  var notes = (leftOut ? _hgNote(leftOut + (leftOut === 1 ? ' entry had no value above 0 or was not an item and was' : ' entries had no value above 0 or were not an item and were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + (beyond === 1 ? ' item beyond the first 40 was' : ' items beyond the first 40 were') + ' not drawn.') : '');
  if (items.length < 2) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A sunburst needs at least 2 items with a value above 0.</div>' + notes + _hgVersionNote(b, 'sunburst'));
  var icicle = _ifPick(b.layout, ['radial', 'icicle'], 'radial') === 'icicle', unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '';
  var f = function(v) { return _bpFmt(v, 2) + us; };
  var tr = _tmTree(items), root = tr[0], tops = tr[1], height = Math.max.apply(null, items.map(function(i) { return i.chain.length; })) + 1, ncol = height + 1;
  var nodes = icicle ? _sbPartition(root, _SB_IH, _SB_IW * ncol / height) : _sbPartition(root, _SB_TAU, _SB_R), tot = nodes[0].value, ws = [], cells = '', labels = '', rings = [], i;
  for (i = 0; i < height; i++) rings.push('');
  nodes.slice(1).forEach(function(nd) {
    var sp = nd.src, dp = nd.depth, fill = _sbFill(_SB_PALETTE[sp.topc % 8], dp), ink = _sbInk(fill), c = Math.min(sp.n.length, 6), kk = _ifK(dp - 1, height), x0 = nd.x0, y0 = nd.y0, x1 = nd.x1, y1 = nd.y1;
    var title = _ifS((nd.kids ? sp.chain : sp.item.chain.concat([sp.n])).join(' / '), 160) + ': ' + _esc(f(nd.value)) + ' (' + (nd.value / tot * 100).toFixed(1) + '%)';
    var ro, t, dth, wm, cl, rm, th, deg, left, w, hh, show, g;
    if (!icicle) {
      ro = Math.max(y0, y1 - 1);
      rings[dp - 1] += '<path d="' + _sbArc(x0, x1, y0, ro, Math.min((x1 - x0) / 2, _SB_PAD), _SB_PADR, 3) + '" fill="' + fill + '"><title>' + title + '</title></path>';
      t = ro - y0; dth = x1 - x0;
      if (t > 0 && dth > 0) {
        wm = _sbQ(Math.max((c * _SB_K + 8) * _SB_BOX / t, _SB_LINE * _SB_BOX / ((y0 + 4) * dth)));
        if (wm <= _SB_MAXW) {
          cl = _sbCls(wm); ws.push(cl[1]);
          rm = (y0 + ro) / 2; th = (x0 + x1) / 2; deg = th * 180 / Math.PI - 90; if (deg > 90) deg -= 180;
          labels += '<div class="sbl' + cl[0] + '" style="position:absolute;left:' + _tmPct(_SB_BOX / 2 + rm * Math.sin(th), _SB_BOX) + ';top:' + _tmPct(_SB_BOX / 2 - rm * Math.cos(th), _SB_BOX) +
            ';transform:translate(-50%,-50%) rotate(' + deg.toFixed(2).replace(/^-0\.00$/, '0.00') + 'deg);width:max-content;max-width:calc(' + _tmPct(t, _SB_BOX).slice(0, -1) + 'cqw - 8px);overflow:hidden;white-space:nowrap;text-overflow:ellipsis;' +
            'text-align:center;font-size:12px;line-height:14px;font-weight:600;color:' + ink + ';pointer-events:none;' + kk + 'opacity:var(--k,1);">' + _ifS(sp.n, 24) + '</div>';
        }
      }
    } else {
      left = y0 - nodes[0].y1; w = y1 - y0; hh = x1 - x0;
      wm = w > 0 ? _sbQ((c * _SB_K + 12) * _SB_IW / w) : 1e9; show = hh >= 20 && wm <= _SB_IMAXW; cl = _sbCls(wm); g = show ? cl[1] : 0; ws.push(g);
      cells += '<div title="' + title + '" style="' + _sbBox(left, x0, w, hh) + 'box-sizing:border-box;border:1px solid transparent;background:' + fill + ';background-clip:padding-box;border-radius:3px;color:' + ink +
        ';padding:1px 5px 0;font-size:12px;line-height:17px;font-weight:600;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;' + kk + 'opacity:var(--k,1);">' +
        (show ? (g ? '<span class="' + cl[0].replace(/^ /, '') + '">' + _ifS(sp.n, 24) + '</span>' : _ifS(sp.n, 24)) : '') + '</div>';
    }
  });
  var top = nodes[0].kids[0];
  var aria = (icicle ? 'Icicle chart' : 'Sunburst') + ' of ' + items.length + ' items in ' + tops.length + ' top-level group' + (tops.length === 1 ? '' : 's') + ', total ' + f(tot) + '. Largest top-level group: ' +
    top.src.n + ', ' + f(top.value) + ', ' + (top.value / tot * 100).toFixed(1) + '% of the total.';
  var body, boxcss, cap;
  if (!icicle) {
    var hole = nodes[0].y1, half = f(tot).length * _SB_K / 2, wmc = _sbQ((Math.sqrt(half * half + 196) + 3) * _SB_BOX / hole), centre = '', cc;
    if (wmc <= _SB_MAXW) {
      cc = _sbCls(wmc); ws.push(cc[1]);
      centre = '<div class="sbc' + cc[0] + '" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center;white-space:nowrap;font-size:12px;line-height:14px;color:var(--text,#0F172A);pointer-events:none;">' +
        '<div style="font-weight:700;">' + _ifS(f(tot), 40) + '</div><div style="color:var(--muted,#475569);">total</div></div>';
    }
    body = '<svg viewBox="-302 -302 604 604" width="100%" height="100%" style="display:block;" aria-hidden="true" focusable="false">' +
      rings.map(function(g, j) { return '<g class="sbr" style="' + _ifK(j, height) + 'opacity:var(--k,1);">' + g + '</g>'; }).join('') + '</svg>' + labels + centre;
    boxcss = 'position:relative;width:100%;max-width:640px;margin:0 auto;aspect-ratio:1/1;';
    cap = 'Angle shows share of the total; each ring out is one level deeper.';
  } else {
    body = cells; boxcss = 'position:relative;height:' + _SB_IH + 'px;';
    cap = 'Height shows share of the total; each column to the right is one level deeper.';
  }
  var uw = [];
  ws.forEach(function(w) { if (w && uw.indexOf(w) < 0) uw.push(w); });
  uw.sort(function(a, c) { return a - c; });
  var css = uw.length ? '<style>' + uw.map(function(w) { return '@container (width<' + w + 'px){.tmw' + w + '{display:none}}'; }).join('') + '</style>' : '';
  return _ifWrap(_ifTitle(b) + '<div role="img" aria-label="' + _ifS(aria, 400) + '" style="' + boxcss + 'container-type:inline-size;overflow:hidden;">' + css + body + '</div>' +
    _hgNote(cap) + notes + _hgVersionNote(b, 'sunburst') +
    _ifTable(['Item', 'Path', 'Value', 'Share of total'], items.map(function(it) { return [it.n, it.chain.join(' / ') || 'Top level', f(it.v), (it.v / tot * 100).toFixed(1) + '%']; })));
};

// ── chord_diagram (I47) and its directed mode (I62) ───────────────────────────────────────────────────────────────────────────────────────────
// d3-chord 3.0.1 chord() / chordDirected() (padAngle 0.05, sortSubgroups descending) and ribbon() / ribbonArrow(), with d3-shape arc() (_sbArc, via _D3Path) for
// the group arcs. Twin of _ch_chord / _ch_ribbon / _render_chord_diagram in renderers/web_article.py.
var _CH_PAD = 0.05, _CH_IN = 175, _CH_OUT = 190, _CH_RR = 174, _CH_RPAD = 1 / 175, _CH_HEAD = 10, _CH_EPS = 1e-12, _CH_BOX = 600, _CH_LAB = 198, _CH_MAXW = 720, _CH_LINE = 14;
function _chSort(idx, key) {   // a stable sort by d3.descending of key(i)
  var d = idx.map(function(v, p) { return [v, p, key(v)]; });
  d.sort(function(a, b) { return (a[2] < b[2] ? 1 : a[2] > b[2] ? -1 : 0) || a[1] - b[1]; });
  return d.map(function(e) { return e[0]; });
}
function _chChord(matrix, directed) {
  var n = matrix.length, m = [], sums = [], k = 0, dx, chords = {}, groups = [], x = 0, i, j, x0, sub, c, v, st, key, keys, out = [];
  for (i = 0; i < n; i++) for (j = 0; j < n; j++) m.push(Number(matrix[i][j]));
  for (i = 0; i < n; i++) { var s = 0; for (j = 0; j < n; j++) s += m[i * n + j] + (directed ? m[j * n + i] : 0); sums[i] = s; k += s; }
  k = Math.max(0, _SB_TAU - _CH_PAD * n) / k;
  dx = k ? _CH_PAD : _SB_TAU / n;
  function slot(idx) { return chords[idx] || (chords[idx] = {}); }
  for (i = 0; i < n; i++) {
    x0 = x;
    if (directed) {
      sub = [];
      for (j = -n; j < n; j++) if (j < 0 ? m[(-j - 1) * n + i] : m[i * n + j]) sub.push(j);
      sub = _chSort(sub, function(a) { return a < 0 ? -m[(-a - 1) * n + i] : m[i * n + a]; });
      sub.forEach(function(jj) {
        if (jj < 0) { c = slot((-jj - 1) * n + i); v = m[(-jj - 1) * n + i]; st = x; x += v * k; c.t = [i, st, x, v]; }
        else { c = slot(i * n + jj); v = m[i * n + jj]; st = x; x += v * k; c.s = [i, st, x, v]; }
      });
    } else {
      sub = [];
      for (j = 0; j < n; j++) if (m[i * n + j] || m[j * n + i]) sub.push(j);
      sub = _chSort(sub, function(a) { return m[i * n + a]; });
      sub.forEach(function(jj) {
        v = m[i * n + jj]; st = x; x += v * k;
        if (i < jj) { c = slot(i * n + jj); c.s = [i, st, x, v]; }
        else { c = slot(jj * n + i); c.t = [i, st, x, v]; if (i === jj) c.s = c.t; }
        if (c.s && c.t && c.s[3] < c.t[3]) { var tmp = c.s; c.s = c.t; c.t = tmp; }
      });
    }
    groups[i] = [i, x0, x, sums[i]];
    x += dx;
  }
  keys = Object.keys(chords).map(Number).sort(function(a, b) { return a - b; });
  keys.forEach(function(q) { out.push(chords[q].s.concat(chords[q].t)); });
  return [groups, out];
}
function _chRibbon(row, radius, padAngle, arrow, digits) {
  var sa0 = row[1] - Math.PI / 2, sa1 = row[2] - Math.PI / 2, ta0 = row[5] - Math.PI / 2, ta1 = row[6] - Math.PI / 2, ap = padAngle / 2, sr = radius, tr = radius, p = new _D3Path(digits), tr2, ta2;
  if (ap > _CH_EPS) {
    if (Math.abs(sa1 - sa0) > ap * 2 + _CH_EPS) { if (sa1 > sa0) { sa0 += ap; sa1 -= ap; } else { sa0 -= ap; sa1 += ap; } } else sa0 = sa1 = (sa0 + sa1) / 2;
    if (Math.abs(ta1 - ta0) > ap * 2 + _CH_EPS) { if (ta1 > ta0) { ta0 += ap; ta1 -= ap; } else { ta0 -= ap; ta1 += ap; } } else ta0 = ta1 = (ta0 + ta1) / 2;
  }
  p.moveTo(sr * Math.cos(sa0), sr * Math.sin(sa0));
  p.arc(0, 0, sr, sa0, sa1, false);
  if (sa0 !== ta0 || sa1 !== ta1) {
    if (arrow) {
      tr2 = tr - _CH_HEAD; ta2 = (ta0 + ta1) / 2;
      p.quadTo(0, 0, tr2 * Math.cos(ta0), tr2 * Math.sin(ta0));
      p.lineTo(tr * Math.cos(ta2), tr * Math.sin(ta2));
      p.lineTo(tr2 * Math.cos(ta1), tr2 * Math.sin(ta1));
    } else {
      p.quadTo(0, 0, tr * Math.cos(ta0), tr * Math.sin(ta0));
      p.arc(0, 0, tr, ta0, ta1, false);
    }
  }
  p.quadTo(0, 0, sr * Math.cos(sa0), sr * Math.sin(sa0));
  p.close();
  return p.d;
}
_RENDERERS['chord_diagram'] = function(b) {
  // the optional 'version' field is read by _hgVersionNote at the end
  var gl = Array.isArray(b.groups) ? b.groups : [], ml = b.matrix, ng = gl.length, why = '', r, i, j, k;
  var wrap = function(inner) { return _ifWrap(_ifTitle(b) + inner + _hgVersionNote(b, 'chord_diagram')); };
  if (ng < 2) return wrap('<div style="' + _ifCard() + '">A chord diagram needs at least 2 groups.</div>');
  if (!Array.isArray(ml)) why = 'The matrix is missing or is not a list of rows.';
  else if (ml.length !== ng) why = 'The matrix has ' + ml.length + (ml.length === 1 ? ' row' : ' rows') + ' but there are ' + ng + ' groups.';
  else for (r = 0; r < ng; r++) {
    if (!Array.isArray(ml[r])) { why = 'Row ' + (r + 1) + ' is not a list.'; break; }
    if (ml[r].length !== ng) { why = 'Row ' + (r + 1) + ' has ' + ml[r].length + (ml[r].length === 1 ? ' cell' : ' cells') + ' but there are ' + ng + ' groups.'; break; }
  }
  if (why) return wrap('<div style="' + _ifCard() + '">' + _esc('A chord diagram needs a square matrix with one row per group. ' + why) + '</div>');
  var n = Math.min(ng, 12), names = [], mat = [], bad = 0, v;
  for (k = 0; k < n; k++) names.push((typeof gl[k] === 'string' && gl[k] !== '') || (typeof gl[k] === 'number' && isFinite(gl[k])) ? String(gl[k]).slice(0, 20) : 'Group ' + (k + 1));
  for (i = 0; i < n; i++) {
    var row = [];
    for (j = 0; j < n; j++) { v = _ifNum(ml[i][j], -1e300, 1e12, null); if (v === null || v < 0) { bad++; v = 0; } row.push(v + 0); }
    mat.push(row);
  }
  var notes = (bad ? _hgNote(bad + (bad === 1 ? ' cell was' : ' cells were') + ' negative or not a number and ' + (bad === 1 ? 'was' : 'were') + ' drawn as 0.') : '') +
    (ng > n ? _hgNote((ng - n) + (ng - n === 1 ? ' group' : ' groups') + ' beyond the first 12 ' + (ng - n === 1 ? 'was' : 'were') + ' not drawn.') : '');
  var directed = b.directed === true, unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '';
  var f = function(x) { return _bpFmt(x, 2) + us; };
  var total = 0, best = null;
  for (i = 0; i < n; i++) for (j = 0; j < n; j++) { total += mat[i][j]; if (mat[i][j] > 0 && (best === null || mat[i][j] > mat[best[0]][best[1]])) best = [i, j]; }
  if (best === null) return wrap('<div style="' + _ifCard() + '">Every flow is 0, so there is nothing to draw.</div>' + notes);
  var cg = _chChord(mat, directed), groups = cg[0], chords = cg[1], outT = [], inT = [];
  for (i = 0; i < n; i++) { outT.push(0); inT.push(0); }
  for (i = 0; i < n; i++) for (j = 0; j < n; j++) { outT[i] += mat[i][j]; inT[j] += mat[i][j]; }
  var col = names.map(function(_, q) { return _SB_PALETTE[q % 8]; }), ribs = names.map(function() { return ''; });
  chords.forEach(function(rw) {
    var s = rw[0], t = rw[4], title = _ifS(names[s], 20) + ' → ' + _ifS(names[t], 20) + ': ' + _esc(f(rw[3])) + (directed ? '' : ' (' + _ifS(names[t], 20) + ' → ' + _ifS(names[s], 20) + ': ' + _esc(f(rw[7])) + ')');
    ribs[s] += '<path class="chd" d="' + _chRibbon(rw, _CH_RR, _CH_RPAD, directed, 3) + '" fill="' + col[s] + '" fill-opacity="0.55" stroke="' + col[s] + '" stroke-width="0.6"><title>' + title + '</title></path>';
  });
  var arcs = '', labels = '', legend = '', ws = [];
  var order = groups.filter(function(g) { return g[2] > g[1]; }).sort(function(a, c) { return a[1] - c[1]; }), need = {};
  order.forEach(function(g, p) {
    var mid = (g[1] + g[2]) / 2, gap = 10;
    [order[(p + order.length - 1) % order.length], order[(p + 1) % order.length]].forEach(function(o) {
      if (o !== g) { var d = Math.abs((o[1] + o[2]) / 2 - mid); gap = Math.min(gap, Math.min(d, _SB_TAU - d)); }
    });
    need[g[0]] = gap > 0 ? _sbQ(_CH_LINE * _CH_BOX / (_CH_LAB * gap)) : 1e9;
  });
  groups.forEach(function(g, q) {
    var nm = _ifS(names[q], 20), kk = _ifK(q, n);
    legend += '<span class="chs" style="white-space:nowrap;"><span aria-hidden="true" style="display:inline-block;width:10px;height:10px;border-radius:2px;background:' + col[q] + ';margin-right:5px;"></span>' + nm + '</span>';
    if (!(g[2] > g[1])) return;
    arcs += '<g class="chg" style="' + kk + 'opacity:var(--k,1);"><path class="cha" d="' + _sbArc(g[1], g[2], _CH_IN, _CH_OUT, 0, null, 3) + '" fill="' + col[q] + '"><title>' + nm + ': sends ' + _esc(f(outT[q])) + ', receives ' + _esc(f(inT[q])) + '</title></path></g>';
    var wm = need[q];
    if (wm > _CH_MAXW) return;
    var cl = _sbCls(wm), th = (g[1] + g[2]) / 2, x = _CH_LAB * Math.sin(th), y = -_CH_LAB * Math.cos(th), right = Math.sin(th) >= 0;
    ws.push(cl[1]);
    var deg = right ? th * 180 / Math.PI - 90 : th * 180 / Math.PI - 270, ty = 'top:' + _tmPct(_CH_BOX / 2 + y, _CH_BOX) + ';';
    var anchor = right ? 'left:' + _tmPct(_CH_BOX / 2 + x, _CH_BOX) + ';' + ty + 'transform-origin:0 7px;' : 'right:' + _tmPct(_CH_BOX / 2 - x, _CH_BOX) + ';' + ty + 'transform-origin:100% 7px;';
    labels += '<div class="chl' + cl[0] + '" style="position:absolute;' + anchor + 'margin-top:-7px;transform:rotate(' + deg.toFixed(2).replace(/^-0\.00$/, '0.00') + 'deg);width:max-content;max-width:calc(' +
      _tmPct(_CH_BOX / 2 - _CH_LAB, _CH_BOX).slice(0, -1) + 'cqw - 4px);overflow:hidden;white-space:nowrap;text-overflow:ellipsis;text-align:' + (right ? 'left' : 'right') +
      ';font-size:12px;line-height:14px;font-weight:600;color:' + col[q] + ';pointer-events:none;' + kk + 'opacity:var(--k,1);">' + nm + '</div>';
  });
  var aria = (directed ? 'Directed chord diagram' : 'Chord diagram') + ' of ' + n + ' groups, total flow ' + f(total) + '. Largest flow: ' + names[best[0]] + ' to ' + names[best[1]] + ', ' + f(mat[best[0]][best[1]]) + '.';
  var svg = '<svg viewBox="-300 -300 600 600" width="100%" height="100%" style="display:block;" aria-hidden="true" focusable="false">' +
    ribs.map(function(rs, q) { return '<g class="chk" style="' + _ifK(q, n) + 'opacity:var(--k,1);">' + rs + '</g>'; }).join('') + arcs + '</svg>';
  var uw = [];
  ws.forEach(function(w) { if (w && uw.indexOf(w) < 0) uw.push(w); });
  uw.sort(function(a, c) { return a - c; });
  var css = uw.length ? '<style>' + uw.map(function(w) { return '@container (width<' + w + 'px){.tmw' + w + '{display:none}}'; }).join('') + '</style>' : '';
  var cap = directed ? 'Each ribbon is an arrow from the group that sends the flow to the group that receives it; its width shows the amount. A group\'s arc covers what it sends and what it receives.' :
    'Each ribbon joins two groups; its width at each end shows the flow from that group to the other.';
  var flows = [];
  for (i = 0; i < n; i++) for (j = 0; j < n; j++) if (mat[i][j] > 0) flows.push([names[i], names[j], f(mat[i][j])]);
  return _ifWrap(_ifTitle(b) + '<div role="img" aria-label="' + _ifS(aria, 400) + '" style="position:relative;width:100%;max-width:' + _CH_MAXW + 'px;margin:0 auto;aspect-ratio:1/1;container-type:inline-size;overflow:hidden;">' +
    css + svg + labels + '</div><div style="display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:0.8rem;">' + legend + '</div>' + _hgNote(cap) + notes + _hgVersionNote(b, 'chord_diagram') +
    _ifTable(['From', 'To', 'Value'], flows) + _ifTable(['Group', 'Total out', 'Total in'], names.map(function(nm, q) { return [nm, f(outT[q]), f(inT[q])]; })));
};

// ── venn_diagram ──────────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['venn_diagram'] = function(b) {
  var list = function(v) { return _ifArr(v, 4).map(function(i) { return '<div>• ' + _ifS(i, 28) + '</div>'; }).join(''); }, c = 'position:absolute;top:34px;width:56%;aspect-ratio:1;border-radius:50%;border:' + _IF_BORDER + ';opacity:calc(0.55 + 0.45*var(--k,1));';
  return _ifWrap(_ifTitle(b) + '<div style="position:relative;max-width:640px;margin:0 auto;aspect-ratio:1.5;font-size:0.82rem;">' +
    '<div style="position:absolute;left:4%;top:0;font-weight:700;">' + _ifS(b.set_a_name, 28) + '</div><div style="position:absolute;right:4%;top:0;font-weight:700;text-align:right;">' + _ifS(b.set_b_name, 28) + '</div>' +
    '<div style="' + c + 'left:4%;background:#BFDBFE;' + _ifK(0, 2) + '"></div><div style="' + c + 'right:4%;background:#FDE68A;mix-blend-mode:multiply;' + _ifK(1, 2) + '"></div>' +
    '<div style="position:absolute;left:10%;top:48%;width:24%;transform:translateY(-50%);">' + list(b.set_a_exclusive) + '</div>' +
    '<div style="position:absolute;left:38%;top:48%;width:24%;transform:translateY(-50%);text-align:center;">' + list(b.intersection) + '</div>' +
    '<div style="position:absolute;right:10%;top:48%;width:24%;transform:translateY(-50%);">' + list(b.set_b_exclusive) + '</div></div>');
};

// ── callout_anatomy ───────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['callout_anatomy'] = function(b) {
  var co = _ifArr(b.callouts, 8).map(function(c) { c = _ifObj(c); return { id: Math.round(_ifNum(c.id, 1, 99, 1)), t: c.title, d: c.description, p: _ifPick(c.pin_position, ['top_left', 'top_right', 'bottom_left', 'bottom_right'], 'top_left') }; });
  var side = function(sfx) { return co.filter(function(c) { return c.p.slice(-sfx.length) === sfx; }).sort(function(x, y) { return (x.p.indexOf('top') === 0 ? 0 : 1) - (y.p.indexOf('top') === 0 ? 0 : 1); }); };
  var card = function(c, i, n) {
    return '<div style="display:flex;gap:8px;align-items:flex-start;' + _ifCard(_ifK(c.id - 1, co.length) + _IF_FADE) + '"><span style="flex:0 0 auto;width:22px;height:22px;border-radius:50%;background:#0369A1;color:#fff;font-size:0.75rem;font-weight:700;text-align:center;line-height:22px;">' + c.id + '</span>' +
      '<div><div style="font-weight:700;">' + _ifS(c.t, 28) + '</div><div style="font-size:0.78rem;color:var(--muted,#475569);">' + _ifS(c.d, 80) + '</div></div></div>';
  };
  var L = side('left'), R = side('right');
  return _ifWrap(_ifTitle(b) + '<div style="display:grid;grid-template-columns:1fr minmax(150px,220px) 1fr;gap:12px;align-items:center;"><div style="display:flex;flex-direction:column;gap:8px;">' + L.map(card).join('') + '</div>' +
    '<div style="border:' + _IF_BORDER + ';border-radius:8px;background:#E0E7FF;color:#1E1B4B;font-weight:700;text-align:center;padding:32px 10px;">' + _ifS(b.central_label, 40) + '</div>' +
    '<div style="display:flex;flex-direction:column;gap:8px;">' + R.map(card).join('') + '</div></div><div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:6px;">Numbered notes on the left and right describe the parts of the subject.</div>');
};

// ── org_chart ─────────────────────────────────────────────────────────────────────────────────────────────────
// Tidy-tree layout: a line-for-line port of d3-hierarchy 3.1.2 tree() (Reingold-Tilford as Buchheim et al. implement it; ISC, Mike Bostock),
// nodeSize [1, 1] and the default separation (1 for siblings, 2 for cousins); twin of _oc_layout in renderers/web_article.py.
function _OcNode(sid, i) { this.sid = sid; this.parent = null; this.children = null; this.A = null; this.a = this; this.z = 0; this.m = 0; this.c = 0; this.s = 0; this.t = null; this.i = i; this.w = 0; this.d = 0; }
// d3's separation hook, in pixels: half of each box plus a gap (8 between siblings, 16 between cousins)
function _ocSep(a, b) { return (a.w + b.w) / 2 + (a.parent === b.parent ? 8 : 16); }
function _ocNextLeft(v) { return v.children ? v.children[0] : v.t; }
function _ocNextRight(v) { return v.children ? v.children[v.children.length - 1] : v.t; }
function _ocMoveSubtree(wm, wp, shift) { var change = shift / (wp.i - wm.i); wp.c -= change; wp.s += shift; wm.c += change; wp.z += shift; wp.m += shift; }
function _ocExecuteShifts(v) {
  var shift = 0, change = 0, i = v.children.length, w;
  while (--i >= 0) { w = v.children[i]; w.z += shift; w.m += shift; shift += w.s + (change += w.c); }
}
function _ocApportion(v, w, ancestor, sep) {
  if (w) {
    var vip = v, vop = v, vim = w, vom = vip.parent.children[0], sip = vip.m, sop = vop.m, sim = vim.m, som = vom.m, shift;
    while (vim = _ocNextRight(vim), vip = _ocNextLeft(vip), vim && vip) {
      vom = _ocNextLeft(vom);
      vop = _ocNextRight(vop);
      vop.a = v;
      shift = vim.z + sim - vip.z - sip + sep(vim, vip);
      if (shift > 0) {
        _ocMoveSubtree(vim.a.parent === v.parent ? vim.a : ancestor, v, shift);
        sip += shift; sop += shift;
      }
      sim += vim.m; sip += vip.m; som += vom.m; sop += vop.m;
    }
    if (vim && !_ocNextRight(vop)) { vop.t = vim; vop.m += sim - sop; }
    if (vip && !_ocNextLeft(vom)) { vom.t = vip; vom.m += sip - som; ancestor = v; }
  }
  return ancestor;
}
// d3 tree() before any scaling: the tree nodes (index = the caller's node index) and their pre-order [index, depth]. sep(a, b) is d3's separation hook.
function _ocWalk(kids, root, widths, sep) {
  var n = kids.length, tn = [], order = [], i, fake = new _OcNode(-1, 0);
  for (i = 0; i < n; i++) { tn.push(new _OcNode(i, 0)); tn[i].w = widths[i]; }
  function link(i, d) {
    order.push([i, d]);
    tn[i].d = d;
    var ks = kids[i];
    if (ks.length) {
      tn[i].children = ks.map(function(c) { return tn[c]; });
      ks.forEach(function(c, j) { tn[c].parent = tn[i]; tn[c].i = j; link(c, d + 1); });
    }
  }
  fake.children = [tn[root]]; tn[root].parent = fake; tn[root].i = 0;
  link(root, 0);
  function firstWalk(v) {
    if (v.children) v.children.forEach(firstWalk);
    var siblings = v.parent.children, w = v.i ? siblings[v.i - 1] : null, midpoint;
    if (v.children) {
      _ocExecuteShifts(v);
      midpoint = (v.children[0].z + v.children[v.children.length - 1].z) / 2;
      if (w) { v.z = w.z + sep(v, w); v.m = v.z - midpoint; } else { v.z = midpoint; }
    } else if (w) { v.z = w.z + sep(v, w); }
    v.parent.A = _ocApportion(v, w, v.parent.A || siblings[0], sep);
  }
  firstWalk(tn[root]);
  fake.m = -tn[root].z;
  order.forEach(function(o) { var v = tn[o[0]]; v.t = v.z + v.parent.m; v.m += v.parent.m; });   // v.t: the real x (the thread slot is free by now)
  return [tn, order];
}
function _ocLayout(kids, root, widths) {
  var w = _ocWalk(kids, root, widths, _ocSep), tn = w[0], x = [], depth = [], i;
  for (i = 0; i < kids.length; i++) { x.push(0); depth.push(0); }
  w[1].forEach(function(o) { x[o[0]] = tn[o[0]].t; depth[o[0]] = o[1]; });
  return [x, depth];
}
// The separation of the d3 radial tidy tree: (a.parent == b.parent ? 1 : 2) / a.depth.
function _ocRadialSep(a, b) { return (a.parent === b.parent ? 1 : 2) / (a.d || 1); }
// d3 tree().size([2 * PI, radius]) with that separation: [angle per node, radius per node, depth per node]; the angle is d3's x (radians from twelve o'clock, clockwise).
function _ocRadial(kids, root, radius) {
  var n = kids.length, z = [], i, w;
  for (i = 0; i < n; i++) z.push(0);
  w = _ocWalk(kids, root, z, _ocRadialSep);
  var tn = w[0], left = tn[root], right = tn[root], bottom = tn[root];
  w[1].forEach(function(o) { var v = tn[o[0]]; if (v.t < left.t) left = v; if (v.t > right.t) right = v; if (o[1] > bottom.d) bottom = v; });
  var s = left === right ? 1 : _ocRadialSep(left, right) / 2, tx = s - left.t, kx = (2 * Math.PI) / (right.t + s + tx), ky = radius / (bottom.d || 1), x = z.slice(), y = z.slice(), depth = z.slice();
  w[1].forEach(function(o) { x[o[0]] = (tn[o[0]].t + tx) * kx; y[o[0]] = o[1] * ky; depth[o[0]] = o[1]; });
  return [x, y, depth];
}
// d3 pointRadial(angle, radius).
function _ocPolar(a, r) { a -= Math.PI / 2; return [r * Math.cos(a), r * Math.sin(a)]; }
// d3-shape linkRadial() (curveBumpRadial): the Bezier from (a0, r0) to (a1, r1), both control points at the mid radius: [x0, y0, c1x, c1y, c2x, c2y, x1, y1].
function _ocLinkRadial(a0, r0, a1, r1) { var rm = (r0 + r1) / 2; return _ocPolar(a0, r0).concat(_ocPolar(a0, rm), _ocPolar(a1, rm), _ocPolar(a1, r1)); }
// d3 cluster().nodeSize([1, 1]) with a pixel separation: [x per node, tier row per node]; size[i] is node i's extent along the leaf axis. See _oc_cluster in renderers/web_article.py.
function _ocCluster(kids, root, size) {
  var n = kids.length, parent = [], post = [], height = [], row = [], x = [], i;
  for (i = 0; i < n; i++) { parent.push(-1); height.push(0); x.push(0); }
  function walk(i) { kids[i].forEach(function(c) { parent[c] = i; walk(c); }); post.push(i); }
  walk(root);
  post.forEach(function(i) { if (kids[i].length) height[i] = 1 + Math.max.apply(null, kids[i].map(function(c) { return height[c]; })); });
  var top = height[root];
  for (i = 0; i < n; i++) row.push(top - height[i]);
  function occupants(leaf) {
    var occ = [], chain = [], v = leaf, k, j;
    while (v !== -1) { chain.push(v); v = parent[v]; }
    for (k = 0; k <= top; k++) {
      var hit = null, below = null;
      for (j = 0; j < chain.length; j++) { if (row[chain[j]] === k) hit = chain[j]; if (row[chain[j]] > k) below = chain[j]; }
      occ.push(hit !== null ? ['n', hit, size[hit]] : ['e', below, 0]);
    }
    return occ;
  }
  var prev = null, run = 0, occs = {};
  post.forEach(function(i) {
    var ks = kids[i];
    if (ks.length) {
      var t = 0;
      ks.forEach(function(c) { t += x[c]; });
      x[i] = t / ks.length;
    } else {
      occs[i] = occupants(i);
      if (prev === null) { x[i] = 0; } else {
        var gap = parent[i] === parent[prev] ? 8 : 16, need = 0, k, p, q;
        for (k = 0; k < occs[i].length; k++) {
          p = occs[i][k]; q = occs[prev][k];
          if (p[0] !== q[0] || p[1] !== q[1]) need = Math.max(need, (p[2] + q[2]) / 2 + gap);
        }
        run += need; x[i] = run;
      }
      prev = i;
    }
  });
  var rx = x[root];
  return [x.map(function(v) { return (v - rx) * 1; }), row];
}
var _OC_W = 640;   // nominal width: a tree wider than this top-down is laid out left to right
var _OC_MAX_NODES = 30, _OC_MAX_KIDS = 6, _OC_MAX_DEPTH = 3;   // 30 nodes, six children per node, four tiers (depth 0..3)
function _ocText(l) { return String(l === undefined || l === null ? '' : l).slice(0, 28); }
// Box width in px from the label, by deterministic character arithmetic (8.4 px a character, 9.6 bold, plus 22 px of padding): the full one-line width,
// but no wider than 112 px unless the longest word needs more (up to 140), so long labels wrap at spaces as the old layout did.
function _ocWidth(t, bold) {
  var c = bold ? 9.6 : 8.4, full = Math.ceil(t.length * c) + 22, word = Math.ceil(Math.max.apply(null, t.split(' ').map(function(x) { return x.length; })) * c) + 22;
  return Math.max(64, Math.min(full, Math.max(112, Math.min(140, word))));
}
function _ocLines(t, w, bold) { var tw = Math.ceil(t.length * (bold ? 9.6 : 8.4)); return tw <= w - 22 ? 1 : Math.min(3, Math.ceil(tw / (w - 30))); }
// ── org_chart radial layout (I55): twin of the radial block above _render_org_chart in renderers/web_article.py (read its comments) ──
var _OC_RAD_MIN = 300, _OC_RAD_BREAK = 520, _OC_RAD_MAX = 640, _OC_RAD_A = [300, 340, 400, 460, 519], _OC_RAD_B = [520, 580, 640], _OC_RAD_R = [0.24, 0.30, 0.34];
var _OC_RAD_PAD = 9, _OC_RAD_TH = 15, _OC_RAD_MINL = 14, _OC_RAD_CAP = 210, _OC_RAD_EDGE = 2, _OC_RAD_GAP = 2;
// Round to 1e-6 so the fitting sees identical doubles in both twins whatever Math.cos / Math.sin and CPython's libm do in the last bit.
function _ocQ(v) { return Math.floor(v * 1e6 + 0.5) / 1e6; }
function _ocRadHit(a, b, m) {
  var dx = b[0] - a[0], dy = b[1] - a[1], ax = [a[2], -a[3], b[2], -b[3]], ay = [a[3], a[2], b[3], b[2]], i, ra, rb;
  for (i = 0; i < 4; i++) {
    ra = a[4] * Math.abs(ax[i] * a[2] + ay[i] * a[3]) + a[5] * Math.abs(-ax[i] * a[3] + ay[i] * a[2]);
    rb = b[4] * Math.abs(ax[i] * b[2] + ay[i] * b[3]) + b[5] * Math.abs(-ax[i] * b[3] + ay[i] * b[2]);
    if (Math.abs(dx * ax[i] + dy * ay[i]) >= ra + rb + m) return false;
  }
  return true;
}
function _ocRadDot(a, px, py, r, m) {
  var lx = (px - a[0]) * a[2] + (py - a[1]) * a[3], ly = -(px - a[0]) * a[3] + (py - a[1]) * a[2], qx = Math.max(Math.abs(lx) - a[4], 0), qy = Math.max(Math.abs(ly) - a[5], 0);
  return qx * qx + qy * qy < (r + m) * (r + m);
}
function _ocRadFit(side, fx, fy, ux, uy, nat, dotR) {
  var n = nat.length, cx = [], cy = [], L = [], h = _OC_RAD_TH / 2, i, j, sg, sx, sy, lim, cs, us, q, pairs = [], dots = [], d2;
  for (i = 0; i < n; i++) { cx.push(side * (0.5 + fx[i])); cy.push(side * (0.5 + fy[i])); }
  for (i = 0; i < n; i++) {
    sx = cx[i] + _OC_RAD_PAD * ux[i]; sy = cy[i] + _OC_RAD_PAD * uy[i]; lim = nat[i];
    for (sg = 1; sg >= -1; sg -= 2) {
      cs = [sx - sg * h * uy[i], sy + sg * h * ux[i]]; us = [ux[i], uy[i]];
      for (q = 0; q < 2; q++) {
        if (us[q] > 1e-9) lim = Math.min(lim, (side - _OC_RAD_EDGE - cs[q]) / us[q]);
        else if (us[q] < -1e-9) lim = Math.min(lim, (_OC_RAD_EDGE - cs[q]) / us[q]);
      }
    }
    L.push(Math.max(_OC_RAD_MINL, Math.floor(lim)));
  }
  function box(i) { var m = _OC_RAD_PAD + L[i] / 2; return [cx[i] + m * ux[i], cy[i] + m * uy[i], ux[i], uy[i], L[i] / 2, h]; }
  for (i = 0; i < n; i++) for (j = 0; j < n; j++) {
    d2 = (cx[j] - cx[i]) * (cx[j] - cx[i]) + (cy[j] - cy[i]) * (cy[j] - cy[i]);
    if (j > i && d2 <= Math.pow(2 * _OC_RAD_PAD + L[i] + L[j] + 2 * _OC_RAD_TH + _OC_RAD_GAP, 2)) pairs.push([i, j]);
    if (j !== i && d2 <= Math.pow(_OC_RAD_PAD + L[i] + _OC_RAD_TH + dotR[j] + _OC_RAD_GAP, 2)) dots.push([i, j]);
  }
  var pass, changed, k, pr;
  for (pass = 0; pass < 400; pass++) {
    changed = false;
    for (q = 0; q < pairs.length; q++) {
      i = pairs[q][0]; j = pairs[q][1];
      if (_ocRadHit(box(i), box(j), _OC_RAD_GAP)) {
        k = L[i] >= L[j] ? i : j;
        if (L[k] <= _OC_RAD_MINL) k = k === i ? j : i;
        if (L[k] > _OC_RAD_MINL) { L[k] = Math.max(_OC_RAD_MINL, L[k] - 4); changed = true; }
      }
    }
    for (q = 0; q < dots.length; q++) {
      i = dots[q][0]; j = dots[q][1];
      if (L[i] > _OC_RAD_MINL && _ocRadDot(box(i), cx[j], cy[j], dotR[j], _OC_RAD_GAP)) { L[i] = Math.max(_OC_RAD_MINL, L[i] - 4); changed = true; }
    }
    if (!changed) break;
  }
  return L;
}
function _ocRenderRadial(b, flat, kids, top, root, virt, note) {
  var total = flat.length, n = kids.length, i, deep = 0, d0 = _ocRadial(kids, root, 1)[2];
  for (i = 0; i < n; i++) deep = Math.max(deep, d0[i]);
  var frac = _OC_RAD_R[Math.min(Math.max(deep, 1), 3) - 1], r = _ocRadial(kids, root, frac), ang = r[0], rad = r[1];
  var labX = ang.slice(), fx = [], fy = [], ux = [], uy = [], nat = [], dotR = [], pt;
  if (!virt) {
    var ch = kids[root].map(function(c) { return ang[c]; }).sort(function(a, c) { return a - c; });
    if (ch.length) {
      var best = -1, at = 0, k, gap;
      for (k = 0; k < ch.length; k++) {
        gap = (k + 1 < ch.length ? ch[k + 1] : ch[0] + 2 * Math.PI) - ch[k];
        if (gap > best) { best = gap; at = ch[k] + gap / 2; }
      }
      labX[root] = at % (2 * Math.PI);
    } else labX[root] = Math.PI / 2;
  }
  for (i = 0; i < n; i++) {
    pt = _ocPolar(ang[i], rad[i]); fx.push(_ocQ(pt[0])); fy.push(_ocQ(pt[1]));
    pt = _ocPolar(labX[i], 1); ux.push(_ocQ(pt[0])); uy.push(_ocQ(pt[1]));
    nat.push(i < total ? Math.min(_OC_RAD_CAP, Math.ceil(flat[i].t.length * 7.2) + 2) : 0);
    dotR.push(i === root && !virt ? 7 : 5);
  }
  var La = [], Lb = [], sel = function(a) { return a.slice(0, total); }, fit = function(sides, tgt) {
    sides.forEach(function(side) {
      var got = _ocRadFit(side, sel(fx), sel(fy), sel(ux), sel(uy), sel(nat), sel(dotR)), j;
      for (j = 0; j < total; j++) tgt[j] = Math.min(tgt[j], got[j]);
    });
  };
  for (i = 0; i < total; i++) { La.push(_OC_RAD_CAP); Lb.push(_OC_RAD_CAP); }
  fit(_OC_RAD_A, La); fit(_OC_RAD_B, Lb);
  var cnt = 0, paths = [];
  var emit = function(idx) {
    return '<ul style="position:static;display:block;list-style:none;margin:0;padding:0;">' + idx.map(function(i) {
      var f = flat[i], kk = _ifK(cnt, total), isroot = i === root && !virt, dr = dotR[i], out, c, p;
      cnt++;
      var left = (50 + 100 * fx[i]).toFixed(3) + '%', tp = (50 + 100 * fy[i]).toFixed(3) + '%', deg = labX[i] * 180 / Math.PI - 90, flip = ux[i] < -1e-9;
      var tf = flip ? 'rotate(' + (deg - 180).toFixed(2) + 'deg) translate(calc(-100% - ' + _OC_RAD_PAD + 'px),-50%)' : 'rotate(' + deg.toFixed(2) + 'deg) translate(' + _OC_RAD_PAD + 'px,-50%)';
      out = '<li style="position:static;padding:0;"><div aria-hidden="true" style="position:absolute;left:' + left + ';top:' + tp + ';width:' + (2 * dr) + 'px;height:' + (2 * dr) + 'px;margin:-' + dr + 'px 0 0 -' + dr + 'px;box-sizing:border-box;border-radius:50%;' +
        (isroot ? 'background:#E0E7FF;border:2px solid #1E1B4B;' : 'background:var(--surface,#F8FAFC);border:2px solid #64748B;') + kk + 'opacity:var(--k,1);"></div>' +
        '<div class="ocr-l"' + (nat[i] > Lb[i] ? ' title="' + _ifS(f.l, 28) + '"' : '') + ' style="position:absolute;left:' + left + ';top:' + tp + ';width:max-content;max-width:var(--la);height:' + _OC_RAD_TH + 'px;--la:' + La[i] + 'px;--lb:' + Lb[i] + 'px;transform-origin:0 0;transform:' + tf +
        ';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px;line-height:' + _OC_RAD_TH + 'px;color:var(--text,#0F172A);' + (isroot ? 'font-weight:700;' : '') +
        'text-shadow:0 0 2px var(--bg,#fff),0 0 2px var(--bg,#fff),0 0 3px var(--bg,#fff);' + kk + 'opacity:var(--k,1);">' + _ifS(f.l, 28) + '</div>';
      if (f.par >= 0) {
        p = f.par; c = _ocLinkRadial(ang[p], rad[p], ang[i], rad[i]);
        paths.push('<path d="M' + (500 + 1000 * c[0]).toFixed(3) + ' ' + (500 + 1000 * c[1]).toFixed(3) + 'C' + c.slice(2).map(function(v) { return (500 + 1000 * v).toFixed(3); }).join(' ') + '" fill="none" stroke="#64748B" stroke-width="2" vector-effect="non-scaling-stroke" style="' + kk + 'opacity:var(--k,1);"/>');
      }
      if (f.kids.length) out += emit(f.kids);
      return out + '</li>';
    }).join('') + '</ul>';
  };
  var lists = emit(top);
  var svg = '<svg aria-hidden="true" viewBox="0 0 1000 1000" preserveAspectRatio="none" style="position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible;">' + paths.join('') + '</svg>';
  var css = '<style>.ocr-l{max-width:var(--la)}@container (min-width:' + _OC_RAD_BREAK + 'px){.ocr-l{max-width:var(--lb)}}</style>';
  var chart = '<div style="position:relative;margin:0 auto;width:100%;min-width:' + _OC_RAD_MIN + 'px;max-width:' + _OC_RAD_MAX + 'px;aspect-ratio:1/1;">' + svg + lists + '</div>';
  return _ifWrap(_ifTitle(b) + css + '<div class="ifoct" data-oc="radial" data-oc-layout="radial" style="overflow-x:auto;contain:inline-size;container-type:inline-size;">' + chart + '</div>' + note);
}
_RENDERERS['org_chart'] = function(b) {
  var nodes = _ifArr(b.nodes, _OC_MAX_NODES).map(function(n) { n = _ifObj(n); return { id: String(n.id === undefined ? '' : n.id).slice(0, 24), l: n.label, p: String(n.parent_id === undefined ? '' : n.parent_id).slice(0, 24) }; });
  // Flatten to a tree in document (pre-order) order: four tiers, six children per node; a duplicated id renders its subtree under each.
  var flat = [];
  var build = function(pid, depth, par) {
    var out = [];
    if (depth > _OC_MAX_DEPTH) return out;
    nodes.forEach(function(n) {
      if (n.p === pid && n.id !== pid && out.length < _OC_MAX_KIDS) {
        var f = { l: n.l, t: _ocText(n.l), depth: depth, par: par, kids: [] };
        flat.push(f); out.push(flat.length - 1);
        f.kids = build(n.id, depth + 1, flat.length - 1);
      }
    });
    return out;
  };
  var top = build('', 0, -1), note = _hgVersionNote(b, 'org_chart'), mode = (b.layout === 'cluster' || b.layout === 'radial') ? b.layout : 'tree';
  if (!flat.length) return _ifWrap(_ifTitle(b) + '<div class="ifoct" style="overflow-x:auto;contain:inline-size;"></div>' + note);
  return _ocRenderFlat(b, flat, top, note, mode, 28);
};
// Everything org_chart does once the tree is flattened (also used by decision_tree layout "tree"): widths, the d3 layout, the nested ul/li boxes and the links. lmax: the longest label a box prints.
function _ocRenderFlat(b, flat, top, note, mode, lmax) {
  var total = flat.length, ws = flat.map(function(f) { return _ocWidth(f.t, f.depth === 0); });
  var kids = flat.map(function(f) { return f.kids; }), virt = top.length !== 1, root;
  if (virt) { kids.push(top); ws.push(0); root = total; } else { root = top[0]; }
  if (mode === 'radial') return _ocRenderRadial(b, flat, kids, top, root, virt, note);
  var lay = mode === 'cluster' ? _ocCluster(kids, root, ws) : _ocLayout(kids, root, ws), xs = lay[0], ds = lay[1], i, lo = Infinity, hi = -Infinity, maxd = 0, lines = 1;
  for (i = 0; i < total; i++) {
    lo = Math.min(lo, xs[i] - ws[i] / 2); hi = Math.max(hi, xs[i] + ws[i] / 2); maxd = Math.max(maxd, ds[i]);
    lines = Math.max(lines, _ocLines(flat[i].t, ws[i], flat[i].depth === 0));
  }
  var tdWid = hi - lo, sh = virt ? 1 : 0, tiers = maxd + 1 - sh, nh = [38, 46, 60][lines - 1], d, row, pa;
  var chart = function(box, link, cw, ch, cls) {
    var cnt = 0, paths = [];
    var emit = function(ids) {
      return '<ul style="position:static;display:block;list-style:none;margin:0;padding:0;">' + ids.map(function(i) {
        var f = flat[i], k = _ifK(cnt, total), out;
        cnt++;
        out = '<li style="position:static;padding:0;"><div style="position:absolute;left:' + _tmPct(Math.max(0, box[i][0]), cw) + ';top:' + _tmPct(Math.max(0, box[i][1]), ch) + ';width:' + _tmPct(ws[i], cw) + ';height:' + nh + 'px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden;overflow-wrap:anywhere;line-height:1.25;'
          + _ifCard('padding:2px 6px;' + (f.depth === 0 ? 'background:#E0E7FF;color:#1E1B4B;font-weight:700;' : '') + k + _IF_FADE) + '">' + _ifS(f.l, lmax) + '</div>';
        if (link[i] !== undefined) paths.push('<path d="' + link[i] + '" fill="none" stroke="#64748B" stroke-width="2" vector-effect="non-scaling-stroke" style="' + k + 'opacity:var(--k,1);"/>');
        if (f.kids.length) out += emit(f.kids);
        return out + '</li>';
      }).join('') + '</ul>';
    };
    var lists = emit(top);
    var svg = '<svg aria-hidden="true" viewBox="0 0 ' + cw.toFixed(3) + ' ' + ch.toFixed(3) + '" preserveAspectRatio="none" style="position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible;">' + paths.join('') + '</svg>';
    return '<div' + (cls ? ' class="' + cls + '"' : '') + ' style="position:relative;margin:0 auto;height:' + ch.toFixed(3) + 'px;width:' + cw.toFixed(3) + 'px;">' + svg + lists + '</div>';
  };
  // top-down geometry
  row = nh + 28;
  var tdHt = tiers * row - 28, tdBox = [], tdLink = [];
  for (i = 0; i < total; i++) {
    d = ds[i] - sh; tdBox[i] = [xs[i] - lo - ws[i] / 2, d * row];
    if (flat[i].par >= 0) {
      var y0 = (ds[flat[i].par] - sh) * row + nh, y1 = d * row;
      tdLink[i] = 'M' + (xs[flat[i].par] - lo).toFixed(3) + ' ' + y0 + 'V' + (y0 + 14).toFixed(1) + 'H' + (xs[i] - lo).toFixed(3) + 'V' + y1;
    }
  }
  var td = chart(tdBox, tdLink, tdWid, tdHt, tdWid > _OC_W ? 'oct' : '');
  var dl = mode === 'cluster' ? ' data-oc-layout="cluster"' : '';
  if (tdWid <= _OC_W) return _ifWrap(_ifTitle(b) + '<div class="ifoct" data-oc="td"' + dl + ' style="overflow-x:auto;contain:inline-size;">' + td + '</div>' + note);
  // wider: also lay it out left to right (the same d3 tree() call with x and y swapped; separation in box heights, tiers as columns) and let CSS pick
  var hs = [], ys, top0 = Infinity, bot = -Infinity, colw = [], col = [0], g, t, sumw, lBox = [], lLink = [];
  for (i = 0; i < total; i++) hs.push(nh);
  if (virt) hs.push(0);
  ys = (mode === 'cluster' ? _ocCluster(kids, root, hs) : _ocLayout(kids, root, hs))[0];
  for (i = 0; i < total; i++) { top0 = Math.min(top0, ys[i] - nh / 2); bot = Math.max(bot, ys[i] + nh / 2); }
  for (t = 0; t < tiers; t++) colw.push(0);
  for (i = 0; i < total; i++) colw[ds[i] - sh] = Math.max(colw[ds[i] - sh], ws[i]);
  sumw = colw.reduce(function(a, c) { return a + c; }, 0);
  g = tiers < 2 ? 28 : Math.min(28, Math.max(12, Math.floor((_OC_W - sumw) / (tiers - 1))));
  for (t = 1; t < tiers; t++) col.push(col[t - 1] + colw[t - 1] + g);
  for (i = 0; i < total; i++) {
    d = ds[i] - sh; lBox[i] = [col[d], ys[i] - nh / 2 - top0]; pa = flat[i].par;
    if (pa >= 0) lLink[i] = 'M' + (col[ds[pa] - sh] + ws[pa]).toFixed(3) + ' ' + (ys[pa] - top0).toFixed(3) + 'H' + (col[ds[pa] - sh] + colw[ds[pa] - sh] + g / 2).toFixed(3) + 'V' + (ys[i] - top0).toFixed(3) + 'H' + col[d].toFixed(3);
  }
  var ltr = chart(lBox, lLink, sumw + g * (tiers - 1), bot - top0, 'ocl');
  var w = String(Math.ceil(tdWid)), cls = 'oc-w' + w;
  var css = '<style>.' + cls + ' .oct{display:none}.' + cls + ' .ocl{display:block}@container (min-width:' + w + 'px){.' + cls + ' .oct{display:block}.' + cls + ' .ocl{display:none}}' +
    '@media print{.' + cls + ' .oct{display:block!important}.' + cls + ' .ocl{display:none!important}}</style>';
  return _ifWrap(_ifTitle(b) + css + '<div class="ifoct ' + cls + '" data-oc="both"' + dl + ' style="overflow-x:auto;contain:inline-size;container-type:inline-size;">' + td + ltr + '</div>' + note);
}

// ── histogram (proposal) ─────────────────────────────────────────────────────────────────────────────────────
// d3-array 3.2.4 bin() with thresholdSturges and the default (niced) domain, ported by hand (ISC, Mike Bostock); twin of _hg_bin in renderers/web_article.py.
function _hgP10(p) { return Number('1e' + p); }   // exact decimal literals, not Math.pow(10, p): V8's pow is an ulp off for some exponents and differs between engine versions
function _hgTickSpec(start, stop, count) {
  var step = (stop - start) / Math.max(0, count), power = Math.floor(Math.log10(step)), error = step / _hgP10(power);
  var factor = error >= Math.sqrt(50) ? 10 : error >= Math.sqrt(10) ? 5 : error >= Math.sqrt(2) ? 2 : 1, i1, i2, inc;
  if (power < 0) {
    inc = _hgP10(-power) / factor; i1 = Math.round(start * inc); i2 = Math.round(stop * inc);
    if (i1 / inc < start) ++i1; if (i2 / inc > stop) --i2; inc = -inc;
  } else {
    inc = _hgP10(power) * factor; i1 = Math.round(start / inc); i2 = Math.round(stop / inc);
    if (i1 * inc < start) ++i1; if (i2 * inc > stop) --i2;
  }
  if (i2 < i1 && 0.5 <= count && count < 2) return _hgTickSpec(start, stop, count * 2);
  return [i1, i2, inc];
}
function _hgTicks(start, stop, count) {
  if (!(count > 0)) return [];
  if (start === stop) return [start];
  var rev = stop < start, sp = rev ? _hgTickSpec(stop, start, count) : _hgTickSpec(start, stop, count), i1 = sp[0], i2 = sp[1], inc = sp[2];
  if (!(i2 >= i1)) return [];
  var n = i2 - i1 + 1, t = new Array(n), i;
  for (i = 0; i < n; ++i) t[i] = rev ? (inc < 0 ? (i2 - i) / -inc : (i2 - i) * inc) : (inc < 0 ? (i1 + i) / -inc : (i1 + i) * inc);
  return t;
}
function _hgTickInc(start, stop, count) { return _hgTickSpec(start, stop, count)[2]; }
function _hgNice(start, stop, count) {
  var pre;
  while (true) {
    var step = _hgTickInc(start, stop, count);
    if (step === pre || step === 0 || !isFinite(step)) return [start, stop];
    if (step > 0) { start = Math.floor(start / step) * step; stop = Math.ceil(stop / step) * step; }
    else if (step < 0) { start = Math.ceil(start * step) / step; stop = Math.floor(stop * step) / step; }
    pre = step;
  }
}
function _hgBin(values, target) {
  var n = values.length, mx = Math.max.apply(null, values), x0 = Math.min.apply(null, values), x1 = mx, i, x;
  var tn = target === null ? Math.max(1, Math.ceil(Math.log(n) / Math.LN2) + 1) : target, nz = _hgNice(x0, x1, tn), step;
  x0 = nz[0]; x1 = nz[1];
  var tz = _hgTicks(x0, x1, tn);
  if (tz.length && tz[0] <= x0) step = _hgTickInc(x0, x1, tn);
  if (tz.length && tz[tz.length - 1] >= x1) {
    if (mx >= x1) {
      var st = _hgTickInc(x0, x1, tn);
      if (isFinite(st)) { if (st > 0) x1 = (Math.floor(x1 / st) + 1) * st; else if (st < 0) x1 = (Math.ceil(x1 * -st) + 1) / -st; }
    } else tz.pop();
  }
  var m = tz.length, a = 0, b = m;
  while (a < tz.length && tz[a] <= x0) ++a;
  while (b - 1 >= 0 && tz[b - 1] > x1) --b;
  if (a || b < m) { tz = tz.slice(a, b); m = b - a; }
  var edges = [], counts = [];
  for (i = 0; i <= m; ++i) { edges.push([i > 0 ? tz[i - 1] : x0, i < m ? tz[i] : x1]); counts.push(0); }
  var fin = isFinite(step);
  for (i = 0; i < n; ++i) {
    x = values[i];
    if (!(x0 <= x && x <= x1)) continue;
    if (fin && step > 0) counts[Math.min(m, Math.floor((x - x0) / step))]++;
    else if (fin && step < 0) { var j = Math.floor((x0 - x) * step); counts[Math.min(m, j + (j >= 0 && j < tz.length && tz[j] <= x ? 1 : 0))]++; }
    else if (!fin) { var lo = 0, hi = m; while (lo < hi) { var mid = (lo + hi) >>> 1; if (tz[mid] <= x) lo = mid + 1; else hi = mid; } counts[lo]++; }
  }
  return [edges, counts];
}
function _hgDecimals(vals) {
  var P = [1, 10, 100, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8];
  for (var d = 0; d < 9; d++) { var k = P[d]; if (vals.every(function(v) { return Math.abs(v * k - Math.round(v * k)) <= Math.max(1e-7, Math.abs(v * k) * 1e-12); })) return d; }
  return 8;
}
function _hgNum(v, d) {
  var s = v.toFixed(d); if (/^-0(\.0+)?$/.test(s)) s = s.slice(1);
  var neg = s.charAt(0) === '-', p = s.replace('-', '').split('.');
  return (neg ? '-' : '') + p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (p.length > 1 ? '.' + p[1] : '');
}
// layout ridge: d3 bin() of all the series pooled gives the shared edges; each series is counted by bin().domain([x0, x1]).thresholds(the inner edges)
function _hgRidge(series, target) {
  var edges = _hgBin([].concat.apply([], series), target)[0], m = edges.length, X0 = edges[0][0], X1 = edges[m - 1][1];
  var inner = edges.slice(1).map(function(e) { return e[0]; });
  var counts = series.map(function(s) {
    var c = [], i;
    for (i = 0; i < m; i++) c.push(0);
    s.forEach(function(x) {
      if (!(X0 <= x && x <= X1)) return;
      var lo = 0, hi = inner.length;
      while (lo < hi) { var mid = (lo + hi) >>> 1; if (inner[mid] <= x) lo = mid + 1; else hi = mid; }
      c[lo]++;
    });
    return c;
  });
  return [edges, counts];
}
function _hgUsable(raw) { return raw.filter(function(v) { return typeof v === 'number' && Math.abs(v) <= 1e12; }); }
function _hgTarget(bv) { return (typeof bv === 'number' && isFinite(bv)) ? Math.round(Math.min(40, Math.max(3, bv))) : null; }
function _hgNote(s) { return '<div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">' + s + '</div>'; }
function _hgSkipNote(skipped) { return skipped ? _hgNote(skipped + (skipped === 1 ? ' entry was' : ' entries were') + ' not a usable number and ' + (skipped === 1 ? 'was' : 'were') + ' skipped.') : ''; }
function _hgVersionNote(b, atom) {
  var v = b.version;
  return (typeof v === 'number' && isFinite(v) && Math.floor(v) === v && v > 1) ? _hgNote('Written for ' + (atom || 'histogram') + ' version ' + v + '; drawn as version 1.') : '';
}
// the x edge labels: few enough to fit, every other one hidden in a narrow container
function _hgAxis(ev, X0, span, lab) {
  var maxlen = Math.max.apply(null, lab.map(function(s) { return s.length; })), want = Math.max(2, Math.min(8, Math.floor(48 / maxlen))), stride = Math.ceil(ev.length / want), xs = '', i;
  for (i = 0; i < ev.length; i++) {
    if (i % stride === 0 && (span > 0 || i === 0)) xs += '<div class="hgx' + (i % (2 * stride) === 0 ? ' hgc' : '') + '" style="position:absolute;top:100%;left:' + (span > 0 ? _tmPct(ev[i] - X0, span) : '50%') + ';"><div style="position:absolute;left:0;top:0;width:1px;height:4px;background:var(--muted,#475569);"></div>' +
      '<div style="position:absolute;left:0;top:10px;transform:translateX(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + lab[i] + '</div></div>';
  }
  return xs;
}
var _HG_LABW = 'clamp(64px,24%,150px)';
function _hgRenderRidge(b) {
  var lst = Array.isArray(b.series) ? b.series : [], used = [], skipped = 0, leftOut = 0;
  lst.slice(0, 8).forEach(function(s, k) {
    if (!(s && typeof s === 'object' && !Array.isArray(s))) { leftOut++; return; }
    var raw = _ifArr(s.values, 2000), vals = _hgUsable(raw);
    skipped += raw.length - vals.length;
    if (vals.length < 5) { leftOut++; return; }
    used.push([s.label ? String(s.label).slice(0, 30) : 'Series ' + (k + 1), vals]);
  });
  var beyond = lst.length - 8;
  var notes = _hgSkipNote(skipped) +
    (leftOut ? _hgNote(leftOut + ' series had fewer than 5 usable numbers or ' + (leftOut === 1 ? 'was not a series and was' : 'were not a series and were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + ' series beyond the first 8 ' + (beyond === 1 ? 'was' : 'were') + ' not drawn.') : '') + _hgVersionNote(b);
  if (!used.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A ridge histogram needs at least one series with 5 numbers.</div>' + notes);
  var rg = _hgRidge(used.map(function(u) { return u[1]; }), _hgTarget(b.bins)), edges = rg[0], counts = rg[1], m = edges.length, n = used.length;
  var X0 = edges[0][0], X1 = edges[m - 1][1], span = X1 - X0;
  var shares = counts.map(function(cs, k) { return cs.map(function(c) { return c / used[k][1].length; }); });
  var top = Math.max.apply(null, shares.map(function(s) { return Math.max.apply(null, s); }));
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '', xl = b.x_label ? String(b.x_label).slice(0, 40) : '', cap = xl ? xl + (unit ? ' (' + unit + ')' : '') : unit;
  var ev = edges.map(function(e) { return e[0]; }); ev.push(edges[m - 1][1]);
  var d = _hgDecimals(ev), lab = ev.map(function(v) { return _hgNum(v, d); });
  var aria = 'Ridgeline histogram of ' + n + ' series in ' + m + (m === 1 ? ' shared bin' : ' shared bins') + ' from ' + lab[0] + ' to ' + lab[lab.length - 1] + us + '. ' +
    used.map(function(u, k) { var p = counts[k].indexOf(Math.max.apply(null, counts[k])); return u[0] + ': ' + u[1].length + ' values, most from ' + lab[p] + ' to ' + lab[p + 1] + us; }).join('; ') + '.';
  var rows = '';
  used.forEach(function(u, k) {
    var path = 'M0.00,1000.00', i;
    for (i = 0; i < m; i++) path += 'H' + (span > 0 ? ((edges[i][0] - X0) / span * 1000).toFixed(2) : '0.00') + 'V' + (1000 - shares[k][i] / top * 1000).toFixed(2);
    path += 'H1000.00L1000.00,1000.00Z';
    rows += '<div style="display:flex;align-items:flex-end;height:44px;">' +
      '<div class="hgrl" style="flex:0 0 ' + _HG_LABW + ';box-sizing:border-box;padding:0 8px 2px 0;text-align:right;font-size:0.75rem;line-height:1.15;color:var(--muted,#475569)' +
      ';overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden;">' + _esc(u[0]) + '</div>' +
      '<div class="hgrp" style="position:relative;flex:1 1 auto;min-width:0;height:100%;border-bottom:1px solid var(--muted,#475569);">' +
      '<svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true" focusable="false" style="position:absolute;left:0;bottom:0;width:100%;height:72px;display:block;overflow:visible;">' +
      '<g class="hgrg" style="' + _ifK(k, n) + 'transform:scaleY(var(--k,1));"><title>' + _esc(u[0] + ': ' + u[1].length + ' values') + '</title>' +
      '<path class="hgrb" d="' + path + '"/><path class="hgr" d="' + path + '"/></g></svg></div></div>';
  });
  var css = '<style>.ifhg .hgrg{transform-box:fill-box;transform-origin:50% 100%}.ifhg .hgrb{fill:var(--bg,#fff)}' +
    '.ifhg .hgr{fill:var(--accent,#0369A1);fill-opacity:0.35;stroke:var(--accent,#0369A1);stroke-width:1.5px;vector-effect:non-scaling-stroke;stroke-linejoin:round}' +
    '@container (max-width:560px){.ifhg .hgx:not(.hgc){display:none}}</style>';
  var chart = '<div class="ifhg" style="container-type:inline-size;max-width:100%;overflow:hidden;">' + css +
    '<div style="font-size:0.75rem;color:var(--muted,#475569);margin:0 0 10px 0;">Share of each series per bin</div>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;padding-top:28px;margin:0 34px 34px 0;">' + rows +
    '<div style="position:relative;margin-left:' + _HG_LABW + ';height:0;">' + _hgAxis(ev, X0, span, lab) + '</div></div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 34px 0 ' + _HG_LABW + ';">' + _esc(cap) + '</div>' : '') + '</div>';
  return _ifWrap(_ifTitle(b) + chart + notes + _ifTable(['Bin from', 'Bin to'].concat(used.map(function(u) { return u[0]; })),
    edges.map(function(e, i) { return [lab[i] + us, lab[i + 1] + us].concat(counts.map(function(cs) { return String(cs[i]); })); })));
}
_RENDERERS['histogram'] = function(b) {
  if (b.layout === 'ridge') return _hgRenderRidge(b);
  var raw = _ifArr(b.values, 2000), vals = _hgUsable(raw), skipped = raw.length - vals.length;
  var skipNote = _hgSkipNote(skipped);
  if (vals.length < 5) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A histogram needs at least 5 numbers; this list has ' + vals.length + '.</div>' + skipNote);
  var target = _hgTarget(b.bins);
  var bn = _hgBin(vals, target), edges = bn[0], counts = bn[1], m = counts.length, X0 = edges[0][0], X1 = edges[m - 1][1], span = X1 - X0;
  var cmax = Math.max.apply(null, counts), top, yt = [], i;
  if (cmax <= 4) { top = cmax; for (i = 0; i <= cmax; i++) yt.push(i); } else { top = _hgNice(0, cmax, 4)[1]; yt = _hgTicks(0, top, 4); }
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', xl = b.x_label ? String(b.x_label).slice(0, 40) : '', cap = xl ? xl + (unit ? ' (' + unit + ')' : '') : unit;
  var ev = edges.map(function(e) { return e[0]; }); ev.push(edges[m - 1][1]);
  var d = _hgDecimals(ev), lab = ev.map(function(v) { return _hgNum(v, d); }), tall = counts.indexOf(cmax), us = unit ? ' ' + unit : '';
  var aria = 'Histogram of ' + vals.length + ' values in ' + m + (m === 1 ? ' bin' : ' bins') + ' from ' + lab[0] + ' to ' + lab[lab.length - 1] + us +
    '. Tallest bin: ' + lab[tall] + ' to ' + lab[tall + 1] + us + ', ' + cmax + (cmax === 1 ? ' value.' : ' values.');
  var rects = '', grid = '', xs = _hgAxis(ev, X0, span, lab);
  for (i = 0; i < m; i++) {
    var x = span > 0 ? (edges[i][0] - X0) / span * 1000 : 0, w = span > 0 ? (edges[i][1] - edges[i][0]) / span * 1000 : 1000, h = top > 0 ? counts[i] / top * 1000 : 0;
    rects += '<rect class="hgb" x="' + x.toFixed(2) + '" y="' + (1000 - h).toFixed(2) + '" width="' + w.toFixed(2) + '" height="' + h.toFixed(2) + '" style="' + _ifK(i, m) +
      'transform:scaleY(var(--k,1));"><title>' + _esc(lab[i] + ' to ' + lab[i + 1] + us + ': ' + counts[i]) + '</title></rect>';
  }
  yt.forEach(function(t) {
    var bt = top > 0 ? (t / top * 100).toFixed(3) + '%' : '0%';
    grid += '<div style="position:absolute;left:0;right:0;bottom:' + bt + ';border-top:1px solid ' + (t === 0 ? 'var(--muted,#475569)' : 'var(--border,#CBD5E1)') + ';"></div>' +
      '<div style="position:absolute;right:100%;margin-right:6px;bottom:' + bt + ';transform:translateY(50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + _hgNum(t, 0) + '</div>';
  });
  var css = '<style>.ifhg .hgb{fill:var(--accent,#0369A1);stroke:var(--bg,#fff);stroke-width:1px;vector-effect:non-scaling-stroke;transform-box:fill-box;transform-origin:50% 100%}' +
    '@container (max-width:560px){.ifhg .hgx:not(.hgc){display:none}}</style>';
  var chart = '<div class="ifhg" style="container-type:inline-size;max-width:100%;overflow:hidden;">' + css +
    '<div style="font-size:0.75rem;color:var(--muted,#475569);margin:0 0 10px 0;">Count of values per bin</div>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;height:220px;margin:0 34px 34px 46px;">' + grid +
    '<svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true" focusable="false" style="position:absolute;left:0;top:0;width:100%;height:100%;display:block;overflow:visible;">' + rects + '</svg>' + xs + '</div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 34px 0 46px;">' + _esc(cap) + '</div>' : '') + '</div>';
  return _ifWrap(_ifTitle(b) + chart + skipNote + _hgVersionNote(b) + _ifTable(['Bin from', 'Bin to', 'Count'], counts.map(function(c, k) { return [lab[k] + us, lab[k + 1] + us, String(c)]; })));
};


// ── box_plot (proposal, I37) ── quartiles are d3-array quantileSorted (R-7); whiskers follow d3's box plot example (Tukey, 1.5 IQR);
// the shared axis is d3 nice(min, max, 5) and its ticks. Twin of _bp_layout / _render_box_plot in renderers/web_article.py.
function _bpQuantile(a, p) {
  var n = a.length;
  if (p <= 0 || n < 2) return a[0];
  if (p >= 1) return a[n - 1];
  var i = (n - 1) * p, i0 = Math.floor(i);
  return a[i0] + (a[i0 + 1] - a[i0]) * (i - i0);
}
function _bpLayout(groups) {
  var loAll = Infinity, hiAll = -Infinity;
  var stats = groups.map(function(g) {
    var a = g.slice().sort(function(x, y) { return x - y; }), q1 = _bpQuantile(a, 0.25), med = _bpQuantile(a, 0.5), q3 = _bpQuantile(a, 0.75), r = 1.5 * (q3 - q1);
    var inside = a.filter(function(x) { return q1 - r <= x && x <= q3 + r; });
    loAll = Math.min(loAll, a[0]); hiAll = Math.max(hiAll, a[a.length - 1]);
    return {n: a.length, min: a[0], q1: q1, median: med, q3: q3, max: a[a.length - 1], lo: inside[0], hi: inside[inside.length - 1],
      outliers: a.filter(function(x) { return x < q1 - r || x > q3 + r; })};
  });
  var d = _hgNice(loAll, hiAll, 5);
  return [stats, [d[0], d[1]], _hgTicks(d[0], d[1], 5)];
}
function _bpFmt(v, cap) { return _hgNum(v, Math.min(_hgDecimals([v]), cap)); }
var _BP_MAX_DOTS = 100;
_RENDERERS['box_plot'] = function(b) {
  var lst = Array.isArray(b.groups) ? b.groups : [], used = [], skipped = 0, leftOut = 0;
  lst.slice(0, 12).forEach(function(g, k) {
    if (!(g && typeof g === 'object' && !Array.isArray(g))) { leftOut++; return; }
    var raw = _ifArr(g.values, 2000), vals = _hgUsable(raw);
    skipped += raw.length - vals.length;
    if (vals.length < 5) { leftOut++; return; }
    used.push([g.label ? String(g.label).slice(0, 30) : 'Group ' + (k + 1), vals]);
  });
  var beyond = lst.length - 12;
  var notes = _hgSkipNote(skipped) +
    (leftOut ? _hgNote(leftOut + (leftOut === 1 ? ' group had fewer than 5 usable numbers or was not a group and was' : ' groups had fewer than 5 usable numbers or were not a group and were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + (beyond === 1 ? ' group beyond the first 12 was' : ' groups beyond the first 12 were') + ' not drawn.') : '');
  if (!used.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A box plot needs at least one group with 5 numbers.</div>' + notes + _hgVersionNote(b, 'box_plot'));
  var L = _bpLayout(used.map(function(u) { return u[1]; })), stats = L[0], X0 = L[1][0], X1 = L[1][1], ticks = L[2], n = used.length, span = X1 - X0;
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '', xl = b.x_label ? String(b.x_label).slice(0, 40) : '', cap = xl ? xl + (unit ? ' (' + unit + ')' : '') : unit;
  var td = _hgDecimals(ticks), tlab = ticks.map(function(t) { return _hgNum(t, td); });
  var fc = Math.min(_hgDecimals([].concat.apply([], used.map(function(u) { return u[1]; }))) + 2, td + 3);
  var pos = function(v) { return span > 0 ? _tmPct(v - X0, span) : '50%'; };
  var wid = function(a, c) { return span > 0 ? _tmPct(c - a, span) : '0%'; };
  var f = function(v) { return _bpFmt(v, fc); };
  var grid = ticks.map(function(t) { return '<div style="position:absolute;top:0;bottom:0;left:' + pos(t) + ';border-left:1px solid var(--border,#CBD5E1);"></div>'; }).join('');
  var rows = '', capped = '';
  used.forEach(function(u, k) {
    var s = stats[k], med = s.median;
    var distinct = s.outliers.filter(function(v, i, a) { return i === 0 || v !== a[i - 1]; }).sort(function(x, y) { return (Math.abs(y - med) - Math.abs(x - med)) || (x - y); });
    if (distinct.length > _BP_MAX_DOTS) capped += _hgNote(_esc(u[0]) + ' has ' + distinct.length + ' distinct outliers; the ' + _BP_MAX_DOTS + ' furthest from the median are drawn. The table counts them all.');
    var dots = distinct.slice(0, _BP_MAX_DOTS).map(function(o) { return '<div class="bpo" style="position:absolute;left:' + pos(o) + ';top:50%;width:7px;height:7px;box-sizing:border-box;border-radius:50%;border:1.5px solid var(--accent,#0369A1);background:var(--bg,#fff);transform:translate(-50%,-50%);"></div>'; }).join('');
    rows += '<div style="display:flex;align-items:center;height:40px;">' +
      '<div class="bpl" style="flex:0 0 ' + _HG_LABW + ';box-sizing:border-box;padding-right:8px;text-align:right;font-size:0.75rem;line-height:1.15;color:var(--muted,#475569)' +
      ';overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;">' + _esc(u[0]) + '</div>' +
      '<div class="bpp" style="position:relative;flex:1 1 auto;min-width:0;height:100%;">' + grid +
      '<div class="bpg" style="position:absolute;inset:0;' + _ifK(k, n) + _IF_FADE + '">' +
      '<div class="bpw" style="position:absolute;left:' + pos(s.lo) + ';width:' + wid(s.lo, s.hi) + ';top:50%;border-top:1.5px solid var(--muted,#475569);"></div>' +
      '<div style="position:absolute;left:' + pos(s.lo) + ';top:32%;height:36%;border-left:1.5px solid var(--muted,#475569);"></div>' +
      '<div style="position:absolute;left:' + pos(s.hi) + ';top:32%;height:36%;border-left:1.5px solid var(--muted,#475569);transform:translateX(-1.5px);"></div>' +
      '<div class="bpb" style="position:absolute;left:' + pos(s.q1) + ';width:' + wid(s.q1, s.q3) + ';top:22%;height:56%;min-width:2px;box-sizing:border-box;border:1.5px solid var(--accent,#0369A1);background:var(--surface,#F8FAFC);border-radius:2px;"></div>' +
      '<div class="bpm" style="position:absolute;left:' + pos(med) + ';top:22%;height:56%;border-left:3px solid var(--accent,#0369A1);transform:translateX(-1.5px);"></div>' +
      dots + '</div></div></div>';
  });
  var no = function(c) { return c + (c === 1 ? ' outlier' : ' outliers'); };
  var aria = 'Box plot of ' + n + (n === 1 ? ' group' : ' groups') + ' on a shared axis from ' + _hgNum(X0, td) + ' to ' + _hgNum(X1, td) + us + '. ' +
    used.map(function(u, k) { var s = stats[k]; return u[0] + ': median ' + f(s.median) + us + ', middle half ' + f(s.q1) + ' to ' + f(s.q3) + us + ', whiskers ' + f(s.lo) + ' to ' + f(s.hi) + us + ', ' + no(s.outliers.length); }).join('; ') + '.';
  var chart = '<div class="ifbp" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>@container (max-width:560px){.ifbp .hgx:not(.hgc){display:none}}</style>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;margin:0 34px 34px 0;">' + rows +
    '<div style="position:relative;margin-left:' + _HG_LABW + ';height:0;border-top:1px solid var(--muted,#475569);">' + _hgAxis(ticks, X0, span, tlab) + '</div></div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 34px 0 ' + _HG_LABW + ';">' + _esc(cap) + '</div>' : '') + '</div>';
  return _ifWrap(_ifTitle(b) + chart + notes + capped + _hgVersionNote(b, 'box_plot') +
    _ifTable(['Group', 'Count', 'Minimum', 'Lower quartile', 'Median', 'Upper quartile', 'Maximum', 'Outliers'],
      used.map(function(u, k) { var s = stats[k]; return [u[0], String(s.n), f(s.min) + us, f(s.q1) + us, f(s.median) + us, f(s.q3) + us, f(s.max) + us, String(s.outliers.length)]; })));
};

// ── waterfall (proposal, I38) ── a delta runs from the running total to the running total plus its value, a total from 0 to the
// running total (a total with its own value sets it); sums are left to right in doubles. The axis is d3 nice(min, max, 5) over 0
// and every bar end, and its ticks. Twin of _wf_layout / _render_waterfall in renderers/web_article.py.
function _wfLayout(steps) {
  var run = 0, lo = 0, hi = 0, checks = [];
  var bars = steps.map(function(st, k) {
    var a, e;
    if (st.kind === 'total') {
      if (typeof st.value === 'number') { checks.push([k, st.value, run]); run = st.value; }
      a = 0; e = run;
    } else { a = run; run = run + st.value; e = run; }
    lo = Math.min(lo, a, e); hi = Math.max(hi, a, e);
    return [a, e];
  });
  var d = _hgNice(lo, hi, 5);
  return [bars, [d[0], d[1]], _hgTicks(d[0], d[1], 5), checks];
}
function _wfNum(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12; }
_RENDERERS['waterfall'] = function(b) {
  var lst = Array.isArray(b.steps) ? b.steps : [], labels = [], steps = [], leftOut = 0;
  lst.slice(0, 24).forEach(function(st, k) {
    if (!(st && typeof st === 'object' && !Array.isArray(st))) { leftOut++; return; }
    var tot = st.kind === 'total', v = st.value;
    if (!tot && !_wfNum(v)) { leftOut++; return; }
    steps.push(tot && _wfNum(v) ? {kind: 'total', value: v} : tot ? {kind: 'total'} : {value: v});
    labels.push(st.label ? String(st.label).slice(0, 30) : 'Step ' + (k + 1));
  });
  var beyond = lst.length - 24;
  var notes = (leftOut ? _hgNote(leftOut + (leftOut === 1 ? ' step had no usable number or was not a step and was' : ' steps had no usable number or were not a step and were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + (beyond === 1 ? ' step beyond the first 24 was' : ' steps beyond the first 24 were') + ' not drawn.') : '');
  if (!steps.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A waterfall needs at least one step with a number.</div>' + notes + _hgVersionNote(b, 'waterfall'));
  var L = _wfLayout(steps), bars = L[0], X0 = L[1][0], X1 = L[1][1], ticks = L[2], n = steps.length, span = X1 - X0;
  var given = steps.filter(function(st) { return 'value' in st; }).map(function(st) { return st.value; });
  var dc = given.length ? Math.min(6, _hgDecimals(given)) : 0, scale = given.reduce(function(m, x) { return Math.max(m, Math.abs(x)); }, 0);
  var f = function(v) { return _bpFmt(v, dc); };
  var sg = function(v) { return (v > 0 ? '+' : '') + f(v); };
  L[3].forEach(function(c) {
    if (c[0] > 0 && Math.abs(c[1] - c[2]) > scale * 1e-9) notes += _hgNote(_esc('The total "' + labels[c[0]] + '" is ' + f(c[1]) + ' but the steps before it add up to ' + f(c[2]) + '; the bar shows ' + f(c[1]) + ' and later steps start there.'));
  });
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '', xl = b.x_label ? String(b.x_label).slice(0, 40) : '', cap = xl ? xl + (unit ? ' (' + unit + ')' : '') : unit;
  var td = _hgDecimals(ticks), tlab = ticks.map(function(t) { return _hgNum(t, td); });
  var vtxt = steps.map(function(st, k) { return st.kind === 'total' ? f(bars[k][1]) : sg(st.value); });
  var vw = 'calc(' + Math.max.apply(null, vtxt.map(function(t) { return t.length; })) + 'ch + 8px)';
  var pos = function(v) { return span > 0 ? _tmPct(v - X0, span) : '50%'; };
  var wid = function(a, c) { return span > 0 ? _tmPct(c - a, span) : '0%'; };
  var grid = ticks.map(function(t) { return '<div style="position:absolute;top:0;bottom:0;left:' + pos(t) + ';border-left:1px solid var(--border,#CBD5E1);"></div>'; }).join('') +
    '<div style="position:absolute;top:0;bottom:0;left:' + pos(0) + ';border-left:1px solid var(--muted,#475569);"></div>';
  var rows = '';
  steps.forEach(function(st, k) {
    var a = bars[k][0], e = bars[k][1], kind = st.kind === 'total' ? 'wft' : e > a ? 'wfu' : e < a ? 'wfd' : 'wfu';
    var col = {wft: 'var(--accent,#0369A1)', wfu: 'var(--positive,#15803D)', wfd: 'var(--negative,#B91C1C)'}[kind];
    rows += '<div style="display:flex;align-items:center;height:40px;">' +
      '<div class="wfl" style="flex:0 0 ' + _HG_LABW + ';box-sizing:border-box;padding-right:8px;text-align:right;font-size:0.75rem;line-height:1.15;color:var(--muted,#475569)' +
      ';overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;">' + _esc(labels[k]) + '</div>' +
      '<div class="wfp" style="position:relative;flex:1 1 auto;min-width:0;height:100%;">' + grid +
      '<div class="wfg" style="position:absolute;inset:0;' + _ifK(k, n) + _IF_FADE + '">' +
      '<div class="wfb ' + kind + '" style="position:absolute;left:' + pos(Math.min(a, e)) + ';width:' + wid(Math.min(a, e), Math.max(a, e)) + ';top:22%;height:56%;min-width:2px;box-sizing:border-box;background:' + col + ';border-radius:2px;"></div>' +
      (k < n - 1 ? '<div class="wfc" style="position:absolute;left:' + pos(e) + ';top:78%;height:44%;border-left:1px dashed var(--muted,#475569);"></div>' : '') +
      '</div></div>' +
      '<div class="wfv" style="flex:0 0 ' + vw + ';box-sizing:border-box;padding-left:8px;font-size:0.75rem;line-height:1;white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--text,#0F172A);">' + vtxt[k] + '</div></div>';
  });
  var up = null, dn = null;
  steps.forEach(function(st, k) {
    if (st.kind === 'total') return;
    if (up === null || st.value > up[1]) up = [k, st.value];
    if (dn === null || st.value < dn[1]) dn = [k, st.value];
  });
  var aria = 'Waterfall of ' + n + (n === 1 ? ' step' : ' steps') + ' ending at ' + f(bars[n - 1][1]) + us + '.' +
    (up && up[1] > 0 ? ' Biggest increase: ' + labels[up[0]] + ', ' + sg(up[1]) + us + '.' : '') +
    (dn && dn[1] < 0 ? ' Biggest decrease: ' + labels[dn[0]] + ', ' + sg(dn[1]) + us + '.' : '');
  var chart = '<div class="ifwf" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>@container (max-width:560px){.ifwf .hgx:not(.hgc){display:none}}</style>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;margin:0 0 34px 0;">' + rows +
    '<div style="position:relative;margin-left:' + _HG_LABW + ';margin-right:' + vw + ';height:0;border-top:1px solid var(--muted,#475569);">' + _hgAxis(ticks, X0, span, tlab) + '</div></div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 ' + vw + ' 0 ' + _HG_LABW + ';">' + _esc(cap) + '</div>' : '') + '</div>';
  return _ifWrap(_ifTitle(b) + chart + notes + _hgVersionNote(b, 'waterfall') + _ifTable(['Step', 'Change', 'Running total'],
    steps.map(function(st, k) { return [labels[k], st.kind === 'total' ? 'Total' : sg(st.value) + us, f(bars[k][1]) + us]; })));
};
