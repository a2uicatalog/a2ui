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
function _tmSquarify(vals, x0, y0, x1, y1) {
  var n = vals.length, out = new Array(n), value = _tmSum(vals), i0 = 0, i1 = 0, dx, dy, sv, mn, mx, alpha, beta, mr, nr, nv, rx0, ry0, ry1, rx1, k, px, py, j;
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
function _tmFits(r, chars, wpad, hmin) { return r[2] - r[0] >= chars * 7 + wpad && r[3] - r[1] >= hmin; }
function _tmPct(x, d) { return (x / d * 100).toFixed(3) + '%'; }
function _tmBox(r) { return 'position:absolute;left:' + _tmPct(r[0], _TM_W) + ';top:' + _tmPct(r[1], _TM_H) + ';width:' + _tmPct(r[2] - r[0], _TM_W) + ';height:' + _tmPct(r[3] - r[1], _TM_H) + ';'; }
_RENDERERS['treemap'] = function(b) {
  var items = _ifArr(b.items, 12).map(function(i) { i = _ifObj(i); return { c: String(i.category === undefined ? '' : i.category).slice(0, 20), n: i.name, v: _ifNum(i.value, 0, 1e12, 0) }; }).filter(function(i) { return i.v > 0; });
  var cats = []; items.forEach(function(i) { if (cats.indexOf(i.c) < 0 && cats.length < 4) cats.push(i.c); }); items = items.filter(function(i) { return cats.indexOf(i.c) >= 0; });
  var tot = items.reduce(function(s, i) { return s + i.v; }, 0) || 1;
  var groups = cats.map(function(c) { return items.filter(function(i) { return i.c === c; }); });
  var lay = _tmLayout(groups.map(function(m) { return m.map(function(i) { return i.v; }); })), cr = lay[0], ir = lay[1], cells = '', tags = '';
  cats.forEach(function(c, ci) {
    var m = groups[ci], ct = m.reduce(function(s, i) { return s + i.v; }, 0);
    var ptxt = _ifS(c, 20) + ' ' + _ifFmt(ct), pill = _tmFits(cr[ci], _ifS(c, 20).length + 1 + _ifFmt(ct).length, 12, 40);
    m.forEach(function(i, k) {
      var lead = pill && k === 0, show = _tmFits(ir[ci][k], _ifS(i.n, 24).length + 1 + _ifFmt(i.v).length, 18, lead ? 48 : 30);
      cells += '<div' + (show ? '' : ' title="' + _ifS(i.n, 24) + ' ' + _ifFmt(i.v) + '"') + ' style="' + _tmBox(ir[ci][k]) + 'box-sizing:border-box;border:1px solid transparent;background:' + _IF_CAT[ci] + ';background-clip:padding-box;color:#fff;border-radius:4px;padding:' + (show ? (lead ? '24px' : '6px') + ' 8px 6px' : '0') + ';font-size:0.78rem;font-weight:700;overflow:hidden;' + _ifK(groups.slice(0, ci).reduce(function(s, g) { return s + g.length; }, 0) + k, 12) + 'opacity:var(--k,1);">' + (show ? _ifS(i.n, 24) + ' ' + _ifFmt(i.v) : '') + '</div>';
    });
    if (pill) tags += '<div style="position:absolute;left:' + _tmPct(cr[ci][0], _TM_W) + ';top:' + _tmPct(cr[ci][1], _TM_H) + ';max-width:' + _tmPct(cr[ci][2] - cr[ci][0], _TM_W) + ';box-sizing:border-box;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;background:rgba(15,23,42,0.6);color:#fff;border-radius:0 0 4px 0;padding:2px 6px;font-size:0.78rem;font-weight:700;">' + ptxt + '</div>';
  });
  return _ifWrap(_ifTitle(b) + '<div style="position:relative;height:300px;">' + cells + tags + '</div><div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">Area shows share of the total.</div>' +
    _ifTable(['Item', 'Category', 'Value', 'Share'], items.map(function(i) { return [i.n, i.c, _ifFmt(i.v), (i.v / tot * 100).toFixed(1) + '%']; })));
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
function _OcNode(sid, i) { this.sid = sid; this.parent = null; this.children = null; this.A = null; this.a = this; this.z = 0; this.m = 0; this.c = 0; this.s = 0; this.t = null; this.i = i; this.w = 0; }
// d3's separation hook, in pixels: half of each box plus a gap (8 between siblings, 16 between cousins)
function _ocSep(a, b) { return (a.w + b.w) / 2 + (a.parent === b.parent ? 8 : 16); }
function _ocNextLeft(v) { return v.children ? v.children[0] : v.t; }
function _ocNextRight(v) { return v.children ? v.children[v.children.length - 1] : v.t; }
function _ocMoveSubtree(wm, wp, shift) { var change = shift / (wp.i - wm.i); wp.c -= change; wp.s += shift; wm.c += change; wp.z += shift; wp.m += shift; }
function _ocExecuteShifts(v) {
  var shift = 0, change = 0, i = v.children.length, w;
  while (--i >= 0) { w = v.children[i]; w.z += shift; w.m += shift; shift += w.s + (change += w.c); }
}
function _ocApportion(v, w, ancestor) {
  if (w) {
    var vip = v, vop = v, vim = w, vom = vip.parent.children[0], sip = vip.m, sop = vop.m, sim = vim.m, som = vom.m, shift;
    while (vim = _ocNextRight(vim), vip = _ocNextLeft(vip), vim && vip) {
      vom = _ocNextLeft(vom);
      vop = _ocNextRight(vop);
      vop.a = v;
      shift = vim.z + sim - vip.z - sip + _ocSep(vim, vip);
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
function _ocLayout(kids, root, widths) {
  var n = kids.length, tn = [], order = [], i, fake = new _OcNode(-1, 0);
  for (i = 0; i < n; i++) { tn.push(new _OcNode(i, 0)); tn[i].w = widths[i]; }
  function link(i, d) {
    order.push([i, d]);
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
      if (w) { v.z = w.z + _ocSep(v, w); v.m = v.z - midpoint; } else { v.z = midpoint; }
    } else if (w) { v.z = w.z + _ocSep(v, w); }
    v.parent.A = _ocApportion(v, w, v.parent.A || siblings[0]);
  }
  firstWalk(tn[root]);
  fake.m = -tn[root].z;
  var x = [], depth = [];
  for (i = 0; i < n; i++) { x.push(0); depth.push(0); }
  order.forEach(function(o) { var v = tn[o[0]]; x[o[0]] = v.z + v.parent.m; v.m += v.parent.m; depth[o[0]] = o[1]; });
  return [x, depth];
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
  var top = build('', 0, -1);
  if (!flat.length) return _ifWrap(_ifTitle(b) + '<div class="ifoct" style="overflow-x:auto;contain:inline-size;"></div>');
  var total = flat.length, ws = flat.map(function(f) { return _ocWidth(f.t, f.depth === 0); });
  var kids = flat.map(function(f) { return f.kids; }), virt = top.length !== 1, root;
  if (virt) { kids.push(top); ws.push(0); root = total; } else { root = top[0]; }
  var lay = _ocLayout(kids, root, ws), xs = lay[0], ds = lay[1], i, lo = Infinity, hi = -Infinity, maxd = 0, lines = 1;
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
        out = '<li style="position:static;padding:0;"><div style="position:absolute;left:' + _tmPct(box[i][0], cw) + ';top:' + _tmPct(box[i][1], ch) + ';width:' + _tmPct(ws[i], cw) + ';height:' + nh + 'px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden;overflow-wrap:anywhere;line-height:1.25;'
          + _ifCard('padding:2px 6px;' + (f.depth === 0 ? 'background:#E0E7FF;color:#1E1B4B;font-weight:700;' : '') + k + _IF_FADE) + '">' + _ifS(f.l, 28) + '</div>';
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
      var y0 = (d - 1) * row + nh, y1 = d * row;
      tdLink[i] = 'M' + (xs[flat[i].par] - lo).toFixed(3) + ' ' + y0 + 'V' + ((y0 + y1) / 2).toFixed(1) + 'H' + (xs[i] - lo).toFixed(3) + 'V' + y1;
    }
  }
  var td = chart(tdBox, tdLink, tdWid, tdHt, tdWid > _OC_W ? 'oct' : '');
  if (tdWid <= _OC_W) return _ifWrap(_ifTitle(b) + '<div class="ifoct" data-oc="td" style="overflow-x:auto;contain:inline-size;">' + td + '</div>');
  // wider: also lay it out left to right (the same d3 tree() call with x and y swapped; separation in box heights, tiers as columns) and let CSS pick
  var hs = [], ys, top0 = Infinity, bot = -Infinity, colw = [], col = [0], g, t, sumw, lBox = [], lLink = [];
  for (i = 0; i < total; i++) hs.push(nh);
  if (virt) hs.push(0);
  ys = _ocLayout(kids, root, hs)[0];
  for (i = 0; i < total; i++) { top0 = Math.min(top0, ys[i] - nh / 2); bot = Math.max(bot, ys[i] + nh / 2); }
  for (t = 0; t < tiers; t++) colw.push(0);
  for (i = 0; i < total; i++) colw[ds[i] - sh] = Math.max(colw[ds[i] - sh], ws[i]);
  sumw = colw.reduce(function(a, c) { return a + c; }, 0);
  g = tiers < 2 ? 28 : Math.min(28, Math.max(12, Math.floor((_OC_W - sumw) / (tiers - 1))));
  for (t = 1; t < tiers; t++) col.push(col[t - 1] + colw[t - 1] + g);
  for (i = 0; i < total; i++) {
    d = ds[i] - sh; lBox[i] = [col[d], ys[i] - nh / 2 - top0]; pa = flat[i].par;
    if (pa >= 0) lLink[i] = 'M' + (col[d - 1] + ws[pa]).toFixed(3) + ' ' + (ys[pa] - top0).toFixed(3) + 'H' + (col[d] - g / 2).toFixed(3) + 'V' + (ys[i] - top0).toFixed(3) + 'H' + col[d].toFixed(3);
  }
  var ltr = chart(lBox, lLink, sumw + g * (tiers - 1), bot - top0, 'ocl');
  var w = String(Math.ceil(tdWid)), cls = 'oc-w' + w;
  var css = '<style>.' + cls + ' .oct{display:none}.' + cls + ' .ocl{display:block}@container (min-width:' + w + 'px){.' + cls + ' .oct{display:block}.' + cls + ' .ocl{display:none}}' +
    '@media print{.' + cls + ' .oct{display:block!important}.' + cls + ' .ocl{display:none!important}}</style>';
  return _ifWrap(_ifTitle(b) + css + '<div class="ifoct ' + cls + '" data-oc="both" style="overflow-x:auto;contain:inline-size;container-type:inline-size;">' + td + ltr + '</div>');
};

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
_RENDERERS['histogram'] = function(b) {
  var raw = _ifArr(b.values, 2000), vals = raw.filter(function(v) { return typeof v === 'number' && Math.abs(v) <= 1e12; }), skipped = raw.length - vals.length;
  var skipNote = skipped ? '<div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">' + skipped + (skipped === 1 ? ' entry was' : ' entries were') + ' not a usable number and ' + (skipped === 1 ? 'was' : 'were') + ' skipped.</div>' : '';
  if (vals.length < 5) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A histogram needs at least 5 numbers; this list has ' + vals.length + '.</div>' + skipNote);
  var target = (typeof b.bins === 'number' && isFinite(b.bins)) ? Math.round(Math.min(40, Math.max(3, b.bins))) : null;
  var bn = _hgBin(vals, target), edges = bn[0], counts = bn[1], m = counts.length, X0 = edges[0][0], X1 = edges[m - 1][1], span = X1 - X0;
  var cmax = Math.max.apply(null, counts), top, yt = [], i;
  if (cmax <= 4) { top = cmax; for (i = 0; i <= cmax; i++) yt.push(i); } else { top = _hgNice(0, cmax, 4)[1]; yt = _hgTicks(0, top, 4); }
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', xl = b.x_label ? String(b.x_label).slice(0, 40) : '', cap = xl ? xl + (unit ? ' (' + unit + ')' : '') : unit;
  var ev = edges.map(function(e) { return e[0]; }); ev.push(edges[m - 1][1]);
  var d = _hgDecimals(ev), lab = ev.map(function(v) { return _hgNum(v, d); }), tall = counts.indexOf(cmax), us = unit ? ' ' + unit : '';
  var aria = 'Histogram of ' + vals.length + ' values in ' + m + (m === 1 ? ' bin' : ' bins') + ' from ' + lab[0] + ' to ' + lab[lab.length - 1] + us +
    '. Tallest bin: ' + lab[tall] + ' to ' + lab[tall + 1] + us + ', ' + cmax + (cmax === 1 ? ' value.' : ' values.');
  var maxlen = Math.max.apply(null, lab.map(function(s) { return s.length; })), want = Math.max(2, Math.min(8, Math.floor(48 / maxlen))), stride = Math.ceil(ev.length / want);
  var pos = function(e) { return span > 0 ? _tmPct(e - X0, span) : '50%'; };
  var rects = '', grid = '', xs = '';
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
  for (i = 0; i < ev.length; i++) {
    if (i % stride === 0 && (span > 0 || i === 0)) xs += '<div class="hgx' + (i % (2 * stride) === 0 ? ' hgc' : '') + '" style="position:absolute;top:100%;left:' + pos(ev[i]) + ';"><div style="position:absolute;left:0;top:0;width:1px;height:4px;background:var(--muted,#475569);"></div>' +
      '<div style="position:absolute;left:0;top:10px;transform:translateX(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + lab[i] + '</div></div>';
  }
  var css = '<style>.ifhg .hgb{fill:var(--accent,#0369A1);stroke:var(--bg,#fff);stroke-width:1px;vector-effect:non-scaling-stroke;transform-box:fill-box;transform-origin:50% 100%}' +
    '@container (max-width:560px){.ifhg .hgx:not(.hgc){display:none}}</style>';
  var chart = '<div class="ifhg" style="container-type:inline-size;max-width:100%;overflow:hidden;">' + css +
    '<div style="font-size:0.75rem;color:var(--muted,#475569);margin:0 0 10px 0;">Count of values per bin</div>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;height:220px;margin:0 34px 34px 46px;">' + grid +
    '<svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true" focusable="false" style="position:absolute;left:0;top:0;width:100%;height:100%;display:block;overflow:visible;">' + rects + '</svg>' + xs + '</div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 34px 0 46px;">' + _esc(cap) + '</div>' : '') + '</div>';
  return _ifWrap(_ifTitle(b) + chart + skipNote + _ifTable(['Bin from', 'Bin to', 'Count'], counts.map(function(c, k) { return [lab[k] + us, lab[k + 1] + us, String(c)]; })));
};
