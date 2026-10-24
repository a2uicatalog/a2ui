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

// ── Build contract v1.1 (owner decision D9; a2ui-private pm/evidence/2026-10-21-build-contract.md) ──
// A moving element carries data-cb="<kind>" (tile|bar|link|branch|arc|ribbon|node|label|ref) and its own --k:clamp(0,calc(var(--p,1)*N - i),1). _cbPass
// runs over a finished chart and adds the rest: --i:<i> beside every --k, opacity:var(--k,1) and transform:scaleY(var(--k,1)) moved out of the inline style into
// the scoped .cb-fade / .cb-grow rules (a wrapper can then replace them without !important), pathLength="1" on a stroked link/branch/ref/arc path, and --n:<N-1>
// plus data-cb-root on the outermost tag, and the two scoped rules in one <style> appended after the chart (so an atom's own first <style> stays first). With no wrapper and --p unset every --k is 1, so the settled picture is the one it always was. Twin: _cb_pass in web_article.py.
var _CB_TAG = /<(\w+)((?:\s+[\w-]+="[^"]*")*)(\s*\/?)>/g;
var _CB_KRE = /--k:clamp\(0,calc\(var\(--p,1\)\*(\d+) - (\d+)\),1\);/;
var _CB_DC = / data-cb="(\w+)"/;
var _CB_STY = / style="([^"]*)"/;
var _CB_CLS = / class="([^"]*)"/;
var _CB_RULES = '<style>:where([data-cb-root]) .cb-fade{opacity:var(--k,1)}:where([data-cb-root]) .cb-grow{transform:scaleY(var(--k,1));transform-box:fill-box;transform-origin:50% 100%}</style>';
// A tree node's contract v1.2 key: its id, or its label where the tree has no ids (decision_tree shares the org_chart drawer).
function _cbKid(f) { return f.id !== undefined ? f.id : f.l; }

function _cbPass(html) {
  if (html.indexOf(' data-cb="') < 0) return html;
  var nmax = 0, m, kg = new RegExp(_CB_KRE.source, 'g'), first = true;
  while ((m = kg.exec(html))) nmax = Math.max(nmax, parseInt(m[1], 10) - 1);
  return html.replace(_CB_TAG, function(all, tag, attrs, end) {
    var km = _CB_DC.exec(attrs), kind, sm, st, mk, add, cm;
    if (km) {
      kind = km[1];
      sm = _CB_STY.exec(attrs);
      st = sm ? sm[1] : '';
      mk = _CB_KRE.exec(st);
      if (mk) st = st.slice(0, mk.index) + '--i:' + mk[2] + ';' + st.slice(mk.index);
      add = '';
      if (st.indexOf('opacity:var(--k,1);') >= 0) { st = st.split('opacity:var(--k,1);').join(''); add += ' cb-fade'; }
      if (st.indexOf('transform:scaleY(var(--k,1));') >= 0) { st = st.split('transform:scaleY(var(--k,1));').join(''); add += ' cb-grow'; }
      if (sm) attrs = attrs.slice(0, sm.index) + (st ? ' style="' + st + '"' : '') + attrs.slice(sm.index + sm[0].length);
      if (add) {
        cm = _CB_CLS.exec(attrs);
        if (cm) attrs = attrs.slice(0, cm.index) + ' class="' + cm[1] + add + '"' + attrs.slice(cm.index + cm[0].length);
        else attrs += ' class="' + add.slice(1) + '"';
      }
      if (tag === 'path' && (kind === 'link' || kind === 'branch' || kind === 'ref' || kind === 'arc') && attrs.indexOf('stroke') >= 0 && attrs.indexOf('pathLength=') < 0) attrs += ' pathLength="1"';
    }
    if (first) {
      first = false;
      sm = _CB_STY.exec(attrs);
      if (sm) attrs = attrs.slice(0, sm.index) + ' style="--n:' + nmax + ';' + sm[1] + '"' + attrs.slice(sm.index + sm[0].length);
      else attrs += ' style="--n:' + nmax + ';"';
      attrs += ' data-cb-root';
    }
    return '<' + tag + attrs + end + '>';
  }) + _CB_RULES;
}
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
    var rKey = _ifS(r.label, 40);
    return '<div data-cb="bar" data-key="' + rKey + '" style="display:grid;grid-template-columns:minmax(110px,28%) 1fr auto;gap:10px;align-items:center;margin:8px 0;' + _ifK(i, all.length) + '"><div data-cb="label" data-key="' + rKey + '">' + rKey + '</div>' +
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
    var tKey = t.id !== undefined ? t.id : (t.task !== undefined ? t.task : '');
    return '<div data-cb="label" data-key="' + _esc(tKey) + '" style="padding:4px 8px 4px 0;align-self:center;grid-row:' + (i + 2) + ';">' + _ifS(t.task, 40) + '</div>' +
      '<div data-cb="bar" data-key="' + _esc(tKey) + '" style="grid-row:' + (i + 2) + ';grid-column:' + (s + 2) + ' / span ' + d + ';padding:3px 2px;"><div style="height:22px;border-radius:5px;background:' + _IF_CAT[ci] + ';transform:scaleX(var(--k,1));transform-origin:left;' + _ifK(i, tasks.length) + '"></div></div>';
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
      var k = _esc(_ifS(r.l, 40));
      return '<div data-cb="bar" data-key="' + k + '" style="display:grid;grid-template-columns:minmax(110px,26%) 1fr;gap:10px;margin:8px 0;' + _ifK(i, n) + '"><div data-cb="label" data-key="' + k + '">' + _ifS(r.l, 40) + '</div><div>' +
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
      var k = _esc(_ifS(r.l, 28));
      var xa = lw + r.a / top * tw, xc = lw + r.c / top * tw, y = i * rowH + 17;
      return '<g data-cb="bar" data-key="' + k + '" style="' + _ifK(i, n) + 'opacity:var(--k,1);"><text data-cb="label" data-key="' + k + '" x="0" y="' + (y + 4) + '" font-size="12" fill="currentColor">' + _ifS(r.l, 28) + '</text><line x1="' + xa.toFixed(1) + '" y1="' + y + '" x2="' + xc.toFixed(1) + '" y2="' + y + '" stroke="#64748B" stroke-width="2"/>' +
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
        var k = _esc(_ifS(r.l, 20));
        return '<g data-cb="bar" data-key="' + k + '" style="' + _ifK(i, n) + '"><path d="M' + lx + ' ' + ys(r.a).toFixed(1) + ' L' + rx + ' ' + ys(r.c).toFixed(1) + '" pathLength="1" fill="none" stroke="#0369A1" stroke-width="2" stroke-dasharray="1" style="stroke-dashoffset:calc(1 - var(--k,1));"/>' +
          '<text data-cb="label" data-key="' + k + '" x="' + (lx - 10) + '" y="' + (L[i] + 4).toFixed(1) + '" font-size="11" text-anchor="end" fill="currentColor">' + _ifS(r.l, 20) + ' ' + _ifFmt(r.a) + '</text>' +
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
    var sKey = _esc(String(s.name || ''));
    boxes += '<div data-cb="item" data-key="' + sKey + '" style="position:absolute;left:' + pos[i][0].toFixed(2) + '%;top:' + pos[i][1].toFixed(2) + '%;width:26%;transform:translate(-50%,-50%);' + _ifCard(_ifK(i, n) + 'opacity:var(--k,1);') + '"><div data-cb="label" data-key="' + sKey + '" style="font-weight:700;">' + (i + 1) + '. ' + _ifS(s.name, 24) + '</div><div style="font-size:0.78rem;color:var(--muted,#475569);">' + _ifS(s.description, 60) + '</div></div>';
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
    var stKey = _esc(s.stage || s.name || String(i));
    return '<div data-cb="item" data-key="' + stKey + '" style="display:flex;flex-direction:column;gap:6px;' + _ifK(i, n) + _IF_FADE + '"><div data-cb="label" data-key="' + stKey + '" style="text-align:center;font-weight:700;padding:5px;border-radius:6px;background:#E0E7FF;color:#1E1B4B;">' + _ifS(s.stage, 24) + '</div>' +
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
    var k = _ifS(l.name, 30);
    return '<div data-cb="item" data-key="' + k + '" style="flex:1;min-width:0;min-height:' + (84 + i * 36) + 'px;border:' + _IF_BORDER + ';border-radius:8px;padding:8px 10px;background:' + (cur ? '#0369A1' : 'var(--surface,#F8FAFC)') + ';color:' + (cur ? '#fff' : 'var(--text,#0F172A)') + ';' + _ifK(i, n) + _IF_FADE + '">' +
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
  var capN = _tmCap(b), items = _ifArr(b.items, capN).map(function(i) { i = _ifObj(i); return { c: String(i.category === undefined ? '' : i.category).slice(0, 20), n: i.name, v: _ifNum(i.value, 0, 1e12, 0), p: _tmPath(i.path) }; }).filter(function(i) { return i.v > 0; });
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
        cells += '<div data-cb="tile" data-key="' + _esc((sp.item.chain || []).concat([sp.item.n]).join('/')) + '"' + (show && !g ? '' : ' title="' + name + '"') + ' style="' + _tmBox(r) + 'box-sizing:border-box;border:1px solid transparent;background:' + col + ';background-clip:padding-box;color:#fff;border-radius:4px;padding:' + (show ? '6px 8px 6px' : '0') + ';font-size:0.78rem;font-weight:700;overflow:hidden;' + _ifK(sp.k, items.length) + 'opacity:var(--k,1);">' + _tmLabel(show, g, cls, name) + '</div>';
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
        cells += '<div data-cb="tile" data-key="' + _esc(c + '/' + i.n) + '"' + (show && !g ? '' : ' title="' + name + '"') + ' style="' + _tmBox(r) + 'box-sizing:border-box;border:1px solid transparent;background:' + _IF_CAT[ci] + ';background-clip:padding-box;color:#fff;border-radius:4px;padding:' + (show ? (lead ? '24px' : '6px') + ' 8px 6px' : '0') + ';font-size:0.78rem;font-weight:700;overflow:hidden;' + _ifK(groups.slice(0, ci).reduce(function(s, g_) { return s + g_.length; }, 0) + k, items.length) + 'opacity:var(--k,1);">' + _tmLabel(show, g, cls, name) + '</div>';
      });
      if (pill) tags += '<div' + pcls + ' style="position:absolute;left:' + _tmPct(cr[ci][0], _TM_W) + ';top:' + _tmPct(cr[ci][1], _TM_H) + ';max-width:' + _tmPct(cr[ci][2] - cr[ci][0], _TM_W) + ';box-sizing:border-box;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;background:rgba(15,23,42,0.6);color:#fff;border-radius:0 0 4px 0;padding:2px 6px;font-size:0.78rem;font-weight:700;">' + ptxt + '</div>';
    });
    table = _ifTable(['Item', 'Category', 'Value', 'Share'], items.map(function(i) { return [i.n, i.c, _ifFmt(i.v), (i.v / tot * 100).toFixed(1) + '%']; }));
  }
  gates.forEach(function(g) { if (g && ws.indexOf(g) < 0) ws.push(g); });
  ws.sort(function(a, c) { return a - c; });
  if (ws.length) css = '<style>' + ws.map(function(w) { return '@container (width<' + w + 'px){.tmw' + w + '{display:none}}'; }).join('') + '</style>';
  return _ifWrap(_ifTitle(b) + '<div' + aria + ' style="position:relative;height:300px;' + (css ? 'container-type:inline-size;' : '') + (css || hid.some(function(x) { return x; }) ? 'overflow:hidden;' : '') + '">' + css + boxes + cells + tags + '</div><div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">Area shows share of the total.' +
    (nested ? ' Boxes inside boxes are groups.' : '') + '</div>' + _tmOver(b, capN) + _hgVersionNote(b, 'treemap') + table);
};

function _tmCap(b) { var m = b.max_items; return typeof m === 'number' && isFinite(m) && m === Math.floor(m) && m >= 12 && m <= 60 ? m : 12; }
function _tmOver(b, capN) {
  var k = Array.isArray(b.items) ? b.items.length - capN : 0;
  return b.max_items === undefined || k <= 0 ? '' : _hgNote(k + (k === 1 ? ' item beyond the first ' : ' items beyond the first ') + capN + (k === 1 ? ' was' : ' were') + ' not drawn.');
}
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
      rings[dp - 1] += '<path data-key="' + _esc((nd.kids ? sp.chain : sp.item.chain.concat([sp.n])).join('/')) + '" d="' + _sbArc(x0, x1, y0, ro, Math.min((x1 - x0) / 2, _SB_PAD), _SB_PADR, 3) + '" fill="' + fill + '"><title>' + title + '</title></path>';
      t = ro - y0; dth = x1 - x0;
      if (t > 0 && dth > 0) {
        wm = _sbQ(Math.max((c * _SB_K + 8) * _SB_BOX / t, _SB_LINE * _SB_BOX / ((y0 + 4) * dth)));
        if (wm <= _SB_MAXW) {
          cl = _sbCls(wm); ws.push(cl[1]);
          rm = (y0 + ro) / 2; th = (x0 + x1) / 2; deg = th * 180 / Math.PI - 90; if (deg > 90) deg -= 180;
          labels += '<div data-cb="label" data-key="' + _esc((nd.kids ? sp.chain : sp.item.chain.concat([sp.n])).join('/')) + '" class="sbl' + cl[0] + '" style="position:absolute;left:' + _tmPct(_SB_BOX / 2 + rm * Math.sin(th), _SB_BOX) + ';top:' + _tmPct(_SB_BOX / 2 - rm * Math.cos(th), _SB_BOX) +
            ';transform:translate(-50%,-50%) rotate(' + deg.toFixed(2).replace(/^-0\.00$/, '0.00') + 'deg);width:max-content;max-width:calc(' + _tmPct(t, _SB_BOX).slice(0, -1) + 'cqw - 8px);overflow:hidden;white-space:nowrap;text-overflow:ellipsis;' +
            'text-align:center;font-size:12px;line-height:14px;font-weight:600;color:' + ink + ';pointer-events:none;' + kk + 'opacity:var(--k,1);">' + _ifS(sp.n, 24) + '</div>';
        }
      }
    } else {
      left = y0 - nodes[0].y1; w = y1 - y0; hh = x1 - x0;
      wm = w > 0 ? _sbQ((c * _SB_K + 12) * _SB_IW / w) : 1e9; show = hh >= 20 && wm <= _SB_IMAXW; cl = _sbCls(wm); g = show ? cl[1] : 0; ws.push(g);
      cells += '<div data-cb="tile" data-key="' + _esc((nd.kids ? sp.chain : sp.item.chain.concat([sp.n])).join('/')) + '" title="' + title + '" style="' + _sbBox(left, x0, w, hh) + 'box-sizing:border-box;border:1px solid transparent;background:' + fill + ';background-clip:padding-box;border-radius:3px;color:' + ink +
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
      rings.map(function(g, j) { return '<g class="sbr" data-cb="arc" data-key="ring-' + (j + 1) + '" style="' + _ifK(j, height) + 'opacity:var(--k,1);">' + g + '</g>'; }).join('') + '</svg>' + labels + centre;
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

// ── circle_pack (I46) ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
// d3-hierarchy 3.1.2 pack() (ISC, Mike Bostock) on the same hierarchy().sum().sort(by value, descending) as the sunburst (_tmBuild): packSiblings (the front
// chain) and packEnclose with d3's fixed LCG (seed 1, one generator per pack() call), ported line by line. Twin of _cp_pack / _render_circle_pack in
// renderers/web_article.py, where the notes on the layout are.
var _CP_SIZE = 600, _CP_PAD = 3, _CP_MAX = 60, _CP_K = 7.2, _CP_MINW = 240;
function _cpLcg() { var s = 1; return function() { s = (1664525 * s + 1013904223) % 4294967296; return s / 4294967296; }; }
function _cpEnclosesNot(a, b) { var dr = a.r - b.r, dx = b.x - a.x, dy = b.y - a.y; return dr < 0 || dr * dr < dx * dx + dy * dy; }
function _cpEnclosesWeak(a, b) { var dr = a.r - b.r + Math.max(a.r, b.r, 1) * 1e-9, dx = b.x - a.x, dy = b.y - a.y; return dr > 0 && dr * dr > dx * dx + dy * dy; }
function _cpEnclosesWeakAll(a, B) { for (var i = 0; i < B.length; ++i) if (!_cpEnclosesWeak(a, B[i])) return false; return true; }
function _cpBasis2(a, b) {
  var x1 = a.x, y1 = a.y, r1 = a.r, x2 = b.x, y2 = b.y, r2 = b.r, x21 = x2 - x1, y21 = y2 - y1, r21 = r2 - r1, l = Math.sqrt(x21 * x21 + y21 * y21);
  return { x: (x1 + x2 + x21 / l * r21) / 2, y: (y1 + y2 + y21 / l * r21) / 2, r: (l + r1 + r2) / 2 };
}
function _cpBasis3(a, b, c) {
  var x1 = a.x, y1 = a.y, r1 = a.r, x2 = b.x, y2 = b.y, r2 = b.r, x3 = c.x, y3 = c.y, r3 = c.r, a2 = x1 - x2, a3 = x1 - x3, b2 = y1 - y2, b3 = y1 - y3, c2 = r2 - r1, c3 = r3 - r1,
    d1 = x1 * x1 + y1 * y1 - r1 * r1, d2 = d1 - x2 * x2 - y2 * y2 + r2 * r2, d3 = d1 - x3 * x3 - y3 * y3 + r3 * r3, ab = a3 * b2 - a2 * b3,
    xa = (b2 * d3 - b3 * d2) / (ab * 2) - x1, xb = (b3 * c2 - b2 * c3) / ab, ya = (a3 * d2 - a2 * d3) / (ab * 2) - y1, yb = (a2 * c3 - a3 * c2) / ab,
    A = xb * xb + yb * yb - 1, B = 2 * (r1 + xa * xb + ya * yb), C = xa * xa + ya * ya - r1 * r1,
    r = -(Math.abs(A) > 1e-6 ? (B + Math.sqrt(B * B - 4 * A * C)) / (2 * A) : C / B);
  return { x: x1 + xa + xb * r, y: y1 + ya + yb * r, r: r };
}
function _cpBasis(B) { return B.length === 1 ? { x: B[0].x, y: B[0].y, r: B[0].r } : B.length === 2 ? _cpBasis2(B[0], B[1]) : _cpBasis3(B[0], B[1], B[2]); }
function _cpExtend(B, p) {
  var i, j;
  if (_cpEnclosesWeakAll(p, B)) return [p];
  for (i = 0; i < B.length; ++i) if (_cpEnclosesNot(p, B[i]) && _cpEnclosesWeakAll(_cpBasis2(B[i], p), B)) return [B[i], p];
  for (i = 0; i < B.length - 1; ++i) for (j = i + 1; j < B.length; ++j) {
    if (_cpEnclosesNot(_cpBasis2(B[i], B[j]), p) && _cpEnclosesNot(_cpBasis2(B[i], p), B[j]) && _cpEnclosesNot(_cpBasis2(B[j], p), B[i]) && _cpEnclosesWeakAll(_cpBasis3(B[i], B[j], p), B)) return [B[i], B[j], p];
  }
  return [p];                                                              // d3 throws here ("something is very wrong"); a renderer must not
}
function _cpEnclose(circles, random) {
  var cs = circles.slice(), m = cs.length, i, t, n, B = [], p, e = null;
  while (m) { i = random() * m-- | 0; t = cs[m]; cs[m] = cs[i]; cs[i] = t; }
  i = 0; n = cs.length;
  while (i < n) {
    p = cs[i];
    if (e && _cpEnclosesWeak(e, p)) ++i;
    else { B = _cpExtend(B, p); e = _cpBasis(B); i = 0; }
  }
  return e;
}
function _cpPlace(b, a, c) {
  var dx = b.x - a.x, x, a2, dy = b.y - a.y, y, b2, d2 = dx * dx + dy * dy;
  if (d2) {
    a2 = a.r + c.r; a2 *= a2; b2 = b.r + c.r; b2 *= b2;
    if (a2 > b2) { x = (d2 + b2 - a2) / (2 * d2); y = Math.sqrt(Math.max(0, b2 / d2 - x * x)); c.x = b.x - x * dx - y * dy; c.y = b.y - x * dy + y * dx; }
    else { x = (d2 + a2 - b2) / (2 * d2); y = Math.sqrt(Math.max(0, a2 / d2 - x * x)); c.x = a.x + x * dx - y * dy; c.y = a.y + x * dy + y * dx; }
  } else { c.x = a.x + c.r; c.y = a.y; }
}
function _cpIntersects(a, b) { var dr = a.r + b.r - 1e-6, dx = b.x - a.x, dy = b.y - a.y; return dr > 0 && dr * dr > dx * dx + dy * dy; }
function _cpScore(nd) { var a = nd.v, b = nd.next.v, ab = a.r + b.r, dx = (a.x * b.r + b.x * a.r) / ab, dy = (a.y * b.r + b.y * a.r) / ab; return dx * dx + dy * dy; }
function _cpSiblings(circles, random) {
  var n = circles.length, a, b, c, aa, ca, i, j, k, sj, sk, again, old, ring, e;
  if (!n) return 0;
  a = circles[0]; a.x = 0; a.y = 0;
  if (!(n > 1)) return a.r;
  b = circles[1]; a.x = -b.r; b.x = a.r; b.y = 0;
  if (!(n > 2)) return a.r + b.r;
  c = circles[2]; _cpPlace(b, a, c);
  a = { v: a, next: null, previous: null }; b = { v: b, next: null, previous: null }; c = { v: c, next: null, previous: null };
  a.next = c.previous = b; b.next = a.previous = c; c.next = b.previous = a;
  i = 3;
  while (i < n) {
    c = circles[i]; _cpPlace(a.v, b.v, c); c = { v: c, next: null, previous: null };
    j = b.next; k = a.previous; sj = b.v.r; sk = a.v.r; again = false;
    for (;;) {
      if (sj <= sk) {
        if (_cpIntersects(j.v, c.v)) { b = j; a.next = b; b.previous = a; again = true; break; }
        sj += j.v.r; j = j.next;
      } else {
        if (_cpIntersects(k.v, c.v)) { a = k; a.next = b; b.previous = a; again = true; break; }
        sk += k.v.r; k = k.previous;
      }
      if (j === k.next) break;
    }
    if (again) continue;
    c.previous = a; c.next = b; old = b; b = c; old.previous = c; a.next = c;
    aa = _cpScore(a);
    while ((c = c.next) !== b) { if ((ca = _cpScore(c)) < aa) { a = c; aa = ca; } }
    b = a.next;
    i++;
  }
  ring = [b.v]; c = b; while ((c = c.next) !== b) ring.push(c.v);
  e = _cpEnclose(ring, random);
  for (i = 0; i < n; ++i) { circles[i].x -= e.x; circles[i].y -= e.y; }
  return e.r;
}
function _cpPack(root, dx, dy, padding) {
  var top = _tmBuild(root, 0), random = _cpLcg(), before = [], stack = [top], after = [], nodes = [top], nd, i, k, r, p;
  top.x = dx / 2; top.y = dy / 2; top.parent = null;
  while (stack.length) {
    nd = stack.pop(); before.push(nd);
    if (nd.kids) for (i = nd.kids.length - 1; i >= 0; i--) { nd.kids[i].parent = nd; stack.push(nd.kids[i]); }
  }
  while (nodes.length) { nd = nodes.pop(); after.push(nd); if (nd.kids) for (i = 0; i < nd.kids.length; i++) nodes.push(nd.kids[i]); }
  after.reverse();
  before.forEach(function(q) { if (!q.kids) { r = Math.sqrt(q.value); q.r = r > 0 ? r : 0; } });
  function group(g, pad, kk) {
    var rr = pad * kk, e, j;
    if (rr !== rr) rr = 0;
    if (rr) for (j = 0; j < g.kids.length; ++j) g.kids[j].r += rr;
    e = _cpSiblings(g.kids, random);
    if (rr) for (j = 0; j < g.kids.length; ++j) g.kids[j].r -= rr;
    g.r = e + rr;
  }
  after.forEach(function(g) { if (g.kids) group(g, 0, 1); });
  k = top.r / Math.min(dx, dy);
  after.forEach(function(g) { if (g.kids) group(g, padding, k); });
  k = Math.min(dx, dy) / (2 * top.r);
  before.forEach(function(q) { p = q.parent; q.r *= k; if (p) { q.x = p.x + k * q.x; q.y = p.y + k * q.y; } });
  return before;
}
function _cpRows(spec, dx, dy, padding) { return _cpPack(spec, dx, dy, padding).map(function(n) { return [n.depth, n.x, n.y, n.r, n.value, n.src.n]; }); }
function _cpQ(w) { return Math.ceil(w / 10) * 10; }
function _cpGate(wm) { return wm > _CP_MINW ? [' tmw' + wm, wm] : ['', 0]; }
function _cpF(x) { return x.toFixed(2).replace(/^-0\.00$/, '0.00'); }
_RENDERERS['circle_pack'] = function(b) {
  // the optional 'version' field is read by _hgVersionNote at the end
  var lst = Array.isArray(b.items) ? b.items : [], items = [], leftOut = 0;
  lst.slice(0, _CP_MAX).forEach(function(it, k) {
    var v = (it && typeof it === 'object' && !Array.isArray(it)) ? _ifNum(it.value, 0, 1e12, 0) : 0;
    if (!(v > 0)) { leftOut++; return; }
    items.push({ n: it.name ? String(it.name).slice(0, 24) : 'Item ' + (k + 1), v: v, chain: _tmPath(it.path) });
  });
  var beyond = lst.length - _CP_MAX;
  var notes = (leftOut ? _hgNote(leftOut + (leftOut === 1 ? ' entry had no value above 0 or was not an item and was' : ' entries had no value above 0 or were not an item and were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + (beyond === 1 ? ' item beyond the first ' + _CP_MAX + ' was' : ' items beyond the first ' + _CP_MAX + ' were') + ' not drawn.') : '');
  if (items.length < 2) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A circle pack needs at least 2 items with a value above 0.</div>' + notes + _hgVersionNote(b, 'circle_pack'));
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '';
  var f = function(v) { return _bpFmt(v, 2) + us; };
  var tr = _tmTree(items), root = tr[0], tops = tr[1], height = Math.max.apply(null, items.map(function(i) { return i.chain.length; })) + 1;
  var nodes = _cpPack(root, _CP_SIZE, _CP_SIZE, _CP_PAD), tot = nodes[0].value, S = _CP_SIZE, M = _CP_SIZE + 4, ws = [], glabs = '', llabs = '', rings = [], big = null, i;
  for (i = 0; i < height; i++) rings.push('');
  nodes.slice(1).forEach(function(nd) {
    var sp = nd.src, dp = nd.depth, x = nd.x, y = nd.y, r = nd.r;
    if (!(isFinite(x) && isFinite(y) && isFinite(r) && r > 0)) return;
    var base = _SB_PALETTE[sp.topc % 8], kk = _ifK(dp - 1, height), c = Math.min(sp.n.length, 6), left = _tmPct(x + 2, M), top = _tmPct(y + 2, M), fill, ink, half, rn, wn, vt, hv, wv, cn, gn, cv, gv, vline, wm, cl;
    var title = _ifS((nd.kids ? sp.chain : sp.item.chain.concat([sp.n])).join(' / '), 160) + ': ' + _esc(f(nd.value)) + ' (' + (nd.value / tot * 100).toFixed(1) + '%)';
    var pos = 'cx="' + _cpF(x) + '" cy="' + _cpF(y) + '" r="' + _cpF(r) + '" ';
    if (nd.kids) {
      rings[dp - 1] += '<circle data-key="' + _esc(sp.chain.join('/')) + '" ' + pos + 'fill="none" stroke="' + _sbFill(base, Math.min(dp, 2)) + '" stroke-width="1.5" vector-effect="non-scaling-stroke"><title>' + title + '</title></circle>';
      wm = _cpQ(Math.max((c * _CP_K + 8) / 0.8, 40) * S / r);
      if (wm <= 640) {
        cl = _cpGate(wm); ws.push(cl[1]);
        glabs += '<div data-cb="label" data-key="' + _esc(sp.chain.join('/')) + '" class="cpg' + cl[0] + '" style="position:absolute;left:' + left + ';top:calc(' + _tmPct(y - r + 2, M) + ' + 18px);transform:translate(-50%,-50%);width:max-content;max-width:min(calc(' + _tmPct(0.8 * r, M).slice(0, -1) +
          'cqw - 4px),100px);overflow:hidden;white-space:nowrap;text-overflow:ellipsis;text-align:center;font-size:12px;line-height:14px;font-weight:700;color:var(--text,#0F172A);' +
          'text-shadow:0 0 3px var(--bg,#fff),0 0 3px var(--bg,#fff),0 0 2px var(--bg,#fff);pointer-events:none;' + kk + 'opacity:var(--k,1);">' + _ifS(sp.n, 24) + '</div>';
      }
    } else {
      fill = _sbFill(base, dp); ink = _sbInk(fill);
      rings[dp - 1] += '<circle data-key="' + _esc(sp.item.chain.concat([sp.n]).join('/')) + '" ' + pos + 'fill="' + fill + '"><title>' + title + '</title></circle>';
      if (big === null || nd.value > big.value) big = nd;
      half = c * _CP_K / 2; rn = Math.max(Math.sqrt(half * half + 49) + 2, (c * _CP_K + 4) / 1.4, 21); wn = _cpQ(rn * S / r);
      if (wn <= 640) {
        vt = f(nd.value); hv = vt.length * _CP_K / 2;
        wv = _cpQ(Math.max(Math.sqrt(Math.pow(Math.max(half, hv), 2) + 196) + 2, (vt.length * _CP_K + 4) / 1.4) * S / r);
        cn = _cpGate(wn); ws.push(cn[1]); vline = '';
        if (wv <= 640) { cv = _cpGate(wv); ws.push(cv[1]); vline = '<div class="cpv' + cv[0] + '" style="opacity:0.85;">' + _ifS(vt, 40) + '</div>'; }
        llabs += '<div data-cb="label" data-key="' + _esc(sp.item.chain.concat([sp.n]).join('/')) + '" class="cpl' + cn[0] + '" style="position:absolute;left:' + left + ';top:' + top + ';transform:translate(-50%,-50%);width:max-content;max-width:calc(' + _tmPct(1.4 * r, M).slice(0, -1) +
          'cqw - 4px);text-align:center;font-size:12px;line-height:14px;font-weight:600;color:' + ink + ';pointer-events:none;' + kk + 'opacity:var(--k,1);">' +
          '<div class="cpn" style="overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">' + _ifS(sp.n, 24) + '</div>' + vline + '</div>';
      }
    }
  });
  var aria = 'Circle packing of ' + items.length + ' items in ' + tops.length + ' top-level group' + (tops.length === 1 ? '' : 's') + ', total ' + f(tot) + '. Largest item: ' +
    big.src.n + ', ' + f(big.value) + ', ' + (big.value / tot * 100).toFixed(1) + '% of the total.';
  var svg = '<svg viewBox="-2 -2 ' + M + ' ' + M + '" width="100%" height="100%" style="display:block;" aria-hidden="true" focusable="false">' +
    rings.map(function(g, j) { return '<g class="cpr" data-cb="arc" data-key="ring-' + (j + 1) + '" style="' + _ifK(j, height) + 'opacity:var(--k,1);">' + g + '</g>'; }).join('') + '</svg>';
  var uw = [];
  ws.forEach(function(w) { if (w && uw.indexOf(w) < 0) uw.push(w); });
  uw.sort(function(a, c) { return a - c; });
  var css = uw.length ? '<style>' + uw.map(function(w) { return '@container (width<' + w + 'px){.tmw' + w + '{display:none}}'; }).join('') + '</style>' : '';
  return _ifWrap(_ifTitle(b) + '<div role="img" aria-label="' + _ifS(aria, 400) + '" style="position:relative;width:100%;max-width:640px;margin:0 auto;aspect-ratio:1/1;container-type:inline-size;overflow:hidden;">' +
    css + svg + glabs + llabs + '</div>' + _hgNote('Circle area shows share of the total; an outlined circle is a group.') + notes + _hgVersionNote(b, 'circle_pack') +
    _ifTable(['Item', 'Path', 'Value', 'Share of total'], items.map(function(it) { return [it.n, it.chain.join(' / ') || 'Top level', f(it.v), (it.v / tot * 100).toFixed(1) + '%']; })));
};

// ── arc_diagram (I61) ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
// Nodes on one horizontal line, each link a semicircle above it; node positions are d3-scale 4.0.2 scalePoint() with padding 0.5 (ISC, Mike Bostock).
// Twin of _ad_point / _render_arc_diagram in renderers/web_article.py, where the notes on the label thinning are.
var _AD_W = 800, _AD_MAXN = 40, _AD_MAXL = 120, _AD_STEP = 16, _AD_MINW = 160, _AD_NONE = '#64748B';
function _adPoint(n, r0, r1) {
  if (n <= 0) return [];
  var step = (r1 - r0) / Math.max(1, n - 1 + 0.5 * 2), start = r0 + (r1 - r0 - step * (n - 1)) * 0.5, out = [], i;
  for (i = 0; i < n; i++) out.push(start + step * i);
  return out;
}
_RENDERERS['arc_diagram'] = function(b) {
  // the optional 'version' field is read by _hgVersionNote at the end
  var lst = Array.isArray(b.nodes) ? b.nodes : [], nodes = [], ids = {}, leftOut = 0, i, k;
  lst.slice(0, _AD_MAXN).forEach(function(it) {
    var o = it && typeof it === 'object' && !Array.isArray(it) ? it : null, id = o ? o.id : null;
    if (!(typeof id === 'string' && id) || Object.prototype.hasOwnProperty.call(ids, id.slice(0, 40))) { leftOut++; return; }
    ids[id.slice(0, 40)] = nodes.length;
    nodes.push({ id: id.slice(0, 40), l: typeof o.label === 'string' && o.label ? o.label.slice(0, 24) : id.slice(0, 24), g: typeof o.group === 'string' && o.group.replace(/[ \t\r\n]/g, '') !== '' ? o.group.slice(0, 20) : '', deg: 0 });
  });
  var nbeyond = lst.length - _AD_MAXN, ll = Array.isArray(b.links) ? b.links : [], links = [], dropped = 0;
  ll.slice(0, _AD_MAXL).forEach(function(it) {
    var o = it && typeof it === 'object' && !Array.isArray(it) ? it : null, s = o ? o.source : null, t = o ? o.target : null, v = o ? o.value : null;
    if (v === undefined || v === null) v = 1;
    if (!(typeof s === 'string' && typeof t === 'string' && Object.prototype.hasOwnProperty.call(ids, s.slice(0, 40)) && Object.prototype.hasOwnProperty.call(ids, t.slice(0, 40)) && s.slice(0, 40) !== t.slice(0, 40) &&
          typeof v === 'number' && isFinite(v) && v > 0)) { dropped++; return; }
    links.push({ s: ids[s.slice(0, 40)], t: ids[t.slice(0, 40)], v: Math.min(v, 1e12), sid: s.slice(0, 40), tid: t.slice(0, 40) });
  });
  var lbeyond = ll.length - _AD_MAXL;
  links.forEach(function(l) { nodes[l.s].deg++; nodes[l.t].deg++; });
  function plural(c, one, many) { return c + ' ' + (c === 1 ? one : many); }
  var notes = (leftOut ? _hgNote(plural(leftOut, 'node entry was', 'node entries were') + ' left out (not a node, no id, or an id already used).') : '') +
    (nbeyond > 0 ? _hgNote(plural(nbeyond, 'node beyond the first 40 was', 'nodes beyond the first 40 were') + ' not drawn.') : '') +
    (dropped ? _hgNote(plural(dropped, 'link was', 'links were') + ' dropped (not a link, a self-link, an unknown node id or a value not above 0).') : '') +
    (lbeyond > 0 ? _hgNote(plural(lbeyond, 'link beyond the first 120 was', 'links beyond the first 120 were') + ' not drawn.') : '');
  if (nodes.length < 2) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">An arc diagram needs at least 2 nodes.</div>' + notes + _hgVersionNote(b, 'arc_diagram'));
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '';
  var f = function(v) { return _bpFmt(v, 2) + us; };
  var groups = [], n = nodes.length;
  nodes.forEach(function(nd) { if (nd.g && groups.indexOf(nd.g) < 0) groups.push(nd.g); });
  nodes.forEach(function(nd) { nd.c = nd.g ? _SB_PALETTE[groups.indexOf(nd.g) % 8] : _AD_NONE; });
  var order = _ifPick(b.order, ['input', 'group', 'degree'], 'input'), idx = [];
  for (i = 0; i < n; i++) idx.push(i);
  if (order === 'group') idx = idx.map(function(v, p) { return [v, p]; }).sort(function(a, c) {
    var x = nodes[a[0]], y = nodes[c[0]];
    return (x.g < y.g ? -1 : x.g > y.g ? 1 : 0) || (x.l < y.l ? -1 : x.l > y.l ? 1 : 0) || a[1] - c[1];
  }).map(function(e) { return e[0]; });
  else if (order === 'degree') idx = idx.map(function(v, p) { return [v, p]; }).sort(function(a, c) { return (nodes[c[0]].deg - nodes[a[0]].deg) || a[1] - c[1]; }).map(function(e) { return e[0]; });
  var xs = [], pts = _adPoint(n, 0, _AD_W), span = 0, base, vals = links.map(function(l) { return l.v; }), vmin = vals.length ? Math.min.apply(null, vals) : 0, vmax = vals.length ? Math.max.apply(null, vals) : 0;
  idx.forEach(function(p, j) { xs[p] = pts[j]; });
  links.forEach(function(l) { span = Math.max(span, Math.abs(xs[l.t] - xs[l.s])); });
  base = span / 2 + 10;
  var dr = _cpF(Math.min(7, _AD_W / n * 0.33)), arcs = '', dots = '';
  links.forEach(function(l) {
    var lo = Math.min(xs[l.s], xs[l.t]), hi = Math.max(xs[l.s], xs[l.t]), w = vmin === vmax ? 2 : 1 + 5 * (l.v - vmin) / (vmax - vmin), rr = _cpF((hi - lo) / 2);
    arcs += '<path class="ada" data-key="' + _esc(l.sid + '→' + l.tid) + '" d="M' + _cpF(lo) + ',' + _cpF(base) + 'A' + rr + ',' + rr + ',0,0,1,' + _cpF(hi) + ',' + _cpF(base) + '" fill="none" stroke="' + nodes[l.s].c + '" stroke-width="' + _cpF(w) +
      '" stroke-opacity="0.6" stroke-linecap="round" vector-effect="non-scaling-stroke"><title>' + _ifS(nodes[l.s].l, 24) + ' to ' + _ifS(nodes[l.t].l, 24) + ': ' + _esc(f(l.v)) + '</title></path>';
  });
  idx.forEach(function(p) {
    var nd = nodes[p];
    dots += '<circle class="adn" data-key="' + _esc(nd.id) + '" cx="' + _cpF(xs[p]) + '" cy="' + _cpF(base) + '" r="' + dr + '" fill="' + nd.c + '"><title>' + _ifS(nd.l, 24) + (nd.g ? ' (' + _ifS(nd.g, 20) + ')' : '') + ': ' + plural(nd.deg, 'link', 'links') + '</title></circle>';
  });
  var maxc = 0;
  nodes.forEach(function(nd) { maxc = Math.max(maxc, nd.l.length); });
  var lh = Math.ceil(maxc * _CP_K) + 8, labs = '', ws = [];
  idx.forEach(function(p, pos) {
    var lvl = pos === 0 ? 99 : Math.min(31 - Math.clz32(pos & -pos), 6), wm = pos === 0 ? 0 : _cpQ(_AD_STEP * n / Math.pow(2, lvl) + 16);
    wm = wm > _AD_MINW ? wm : 0; ws.push(wm);
    labs += '<div data-cb="label" data-key="' + _esc(nodes[p].id) + '" class="adl' + (wm ? ' tmw' + wm : '') + '" style="position:absolute;left:' + _tmPct(xs[p], _AD_W) + ';top:0;transform:translateX(-50%) rotate(180deg);writing-mode:vertical-rl;max-height:' + lh +
      'px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-size:12px;line-height:14px;color:var(--text,#0F172A);pointer-events:none;' + _ifK(1, 2) + 'opacity:var(--k,1);">' + _ifS(nodes[p].l, 24) + '</div>';
  });
  var uw = [];
  ws.forEach(function(w) { if (w && uw.indexOf(w) < 0) uw.push(w); });
  uw.sort(function(a, c) { return a - c; });
  var css = uw.length ? '<style>' + uw.map(function(w) { return '@container (width<' + w + 'px){.tmw' + w + '{display:none}}'; }).join('') + '</style>' : '';
  var top = nodes[idx[0]];
  idx.forEach(function(p) { if (nodes[p].deg > top.deg) top = nodes[p]; });
  var aria = 'Arc diagram of ' + n + ' nodes and ' + plural(links.length, 'link', 'links') + '.' + (links.length ? ' Most connected: ' + top.l + ', ' + plural(top.deg, 'link', 'links') + '.' : '');
  var svg = '<svg viewBox="0 0 ' + _AD_W + ' ' + _cpF(base + 14) + '" width="100%" style="display:block;height:auto;" aria-hidden="true" focusable="false">' +
    '<line x1="0" y1="' + _cpF(base) + '" x2="' + _AD_W + '" y2="' + _cpF(base) + '" style="stroke:var(--border,#CBD5E1);" stroke-width="1" vector-effect="non-scaling-stroke"/>' +
    '<g class="adr" data-cb="link" data-key="links" style="' + _ifK(0, 2) + 'opacity:var(--k,1);">' + arcs + '</g><g class="adr" data-cb="node" data-key="nodes" style="' + _ifK(1, 2) + 'opacity:var(--k,1);">' + dots + '</g></svg>';
  var legend = '';
  if (groups.length) {
    var ent = groups.map(function(g, j) { return [g, _SB_PALETTE[j % 8]]; });
    if (nodes.some(function(nd) { return !nd.g; })) ent.push(['No group', _AD_NONE]);
    legend = '<div class="adleg" style="display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:12px;line-height:16px;color:var(--text,#0F172A);">' +
      ent.map(function(e) { return '<span style="display:inline-flex;align-items:center;gap:5px;"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + e[1] + ';"></span>' + _ifS(e[0], 20) + '</span>'; }).join('') + '</div>';
  }
  var tables = _ifTable(['Node', 'Group', 'Links'], idx.map(function(p) { return [nodes[p].l, nodes[p].g || 'No group', String(nodes[p].deg)]; }));
  if (links.length) tables += _ifTable(['From', 'To', 'Value'], links.map(function(l) { return [nodes[l.s].l, nodes[l.t].l, f(l.v)]; }));
  return _ifWrap(_ifTitle(b) + '<div role="img" aria-label="' + _ifS(aria, 400) + '" style="position:relative;width:100%;max-width:800px;margin:0 auto;padding:0 8px;box-sizing:border-box;container-type:inline-size;">' + css + svg +
    '<div style="position:relative;height:' + lh + 'px;margin-top:2px;">' + labs + '</div></div>' + legend +
    _hgNote('Arc thickness shows the link value. In a narrow container only some node names are drawn; the table lists every node and link.') + notes + _hgVersionNote(b, 'arc_diagram') + tables);
};

// ── contour_plot (I57 contours of a value grid, I51 density contours of points) ──────────────────────────────────────────────────────────────
// d3-contour 4.0.2 (ISC, Mike Bostock): contours() and contourDensity(), with d3-array 3.2.4 blur2, ported by hand in the order of the JavaScript source
// (the density grid is a Float32Array in d3; here every store goes through Math.fround). Twin of the _cn_* functions and _render_contour_plot in
// renderers/web_article.py, where the notes are.
var _CN_CASES = [
  [], [[[1.0, 1.5], [0.5, 1.0]]], [[[1.5, 1.0], [1.0, 1.5]]], [[[1.5, 1.0], [0.5, 1.0]]], [[[1.0, 0.5], [1.5, 1.0]]],
  [[[1.0, 1.5], [0.5, 1.0]], [[1.0, 0.5], [1.5, 1.0]]], [[[1.0, 0.5], [1.0, 1.5]]], [[[1.0, 0.5], [0.5, 1.0]]], [[[0.5, 1.0], [1.0, 0.5]]],
  [[[1.0, 1.5], [1.0, 0.5]]], [[[0.5, 1.0], [1.0, 0.5]], [[1.5, 1.0], [1.0, 1.5]]], [[[1.5, 1.0], [1.0, 0.5]]], [[[0.5, 1.0], [1.5, 1.0]]],
  [[[1.0, 1.5], [1.5, 1.0]]], [[[0.5, 1.0], [1.0, 1.5]]], []];
var _CN_W = 600, _CN_H = 400, _CN_MAXPTS = 2000, _CN_MAXROWS = 200, _CN_BUDGET = 40000, _CN_MIN_VALUE = 5e-324;
var _CN_STOPS = [[0xCF, 0xE3, 0xF5], [0x8F, 0xBB, 0xE0], [0x4E, 0x8F, 0xC9], [0x25, 0x6B, 0xAA], [0x0B, 0x3C, 0x73]];
var _CN_NAMES = ['pale blue', 'light blue', 'mid blue', 'deep blue', 'dark blue'];

function _cnRingArea(ring) {
  var i = 0, n = ring.length, area = ring[n - 1][1] * ring[0][0] - ring[n - 1][0] * ring[0][1];
  while (++i < n) area += ring[i - 1][1] * ring[i][0] - ring[i - 1][0] * ring[i][1];
  return area;
}
function _cnWithin(p, q, r) { return p <= q && q <= r || r <= q && q <= p; }
function _cnRingContains(ring, point) {
  var x = point[0], y = point[1], contains = -1;
  for (var i = 0, n = ring.length, j = n - 1; i < n; j = i++) {
    var pi = ring[i], xi = pi[0], yi = pi[1], pj = ring[j], xj = pj[0], yj = pj[1];
    if ((pj[0] - pi[0]) * (point[1] - pi[1]) === (point[0] - pi[0]) * (pj[1] - pi[1])) {
      var k = +(pi[0] === pj[0]);
      if (_cnWithin(pi[k], point[k], pj[k])) return 0;
    }
    if (((yi > y) !== (yj > y)) && ((x < (xj - xi) * (y - yi) / (yj - yi) + xi))) contains = -contains;
  }
  return contains;
}
function _cnContains(ring, hole) {
  var i = -1, n = hole.length, c;
  while (++i < n) if (c = _cnRingContains(ring, hole[i])) return c;
  return 0;
}
function _cnValid(v) { return v === undefined || v === null || isNaN(v = +v) ? -Infinity : v; }
function _cnSmooth1(x, v0, v1, value) {
  var a = value - v0, b = v1 - v0, d = isFinite(a) || isFinite(b) ? a / b : Math.sign(a) / Math.sign(b);
  return isNaN(d) ? x : x + d - 0.5;
}
function _cnIsorings(values, dx, dy, value, callback) {
  var byStart = {}, byEnd = {}, x, y, t0, t1, t2, t3;
  function above(v) { return v === undefined || v === null ? false : +v >= value; }
  function stitch(line) {
    var start = [line[0][0] + x, line[0][1] + y], end = [line[1][0] + x, line[1][1] + y],
        si = start[0] * 2 + start[1] * (dx + 1) * 4, ei = end[0] * 2 + end[1] * (dx + 1) * 4, f, g;
    if (f = byEnd[si]) {
      if (g = byStart[ei]) {
        delete byEnd[f.end]; delete byStart[g.start];
        if (f === g) { f.ring.push(end); callback(f.ring); }
        else byStart[f.start] = byEnd[g.end] = {start: f.start, end: g.end, ring: f.ring.concat(g.ring)};
      } else { delete byEnd[f.end]; f.ring.push(end); byEnd[f.end = ei] = f; }
    } else if (f = byStart[ei]) {
      if (g = byEnd[si]) {
        delete byStart[f.start]; delete byEnd[g.end];
        if (f === g) { f.ring.push(end); callback(f.ring); }
        else byStart[g.start] = byEnd[f.end] = {start: g.start, end: f.end, ring: g.ring.concat(f.ring)};
      } else { delete byStart[f.start]; f.ring.unshift(start); byStart[f.start = si] = f; }
    } else byStart[si] = byEnd[ei] = {start: si, end: ei, ring: [start, end]};
  }
  function run(c) { _CN_CASES[c].forEach(stitch); }
  x = y = -1;
  t1 = +above(values[0]);
  run(t1 << 1);
  while (++x < dx - 1) { t0 = t1; t1 = +above(values[x + 1]); run(t0 | t1 << 1); }
  run(t1 << 0);
  while (++y < dy - 1) {
    x = -1;
    t1 = +above(values[y * dx + dx]);
    t2 = +above(values[y * dx]);
    run(t1 << 1 | t2 << 2);
    while (++x < dx - 1) {
      t0 = t1; t1 = +above(values[y * dx + dx + x + 1]);
      t3 = t2; t2 = +above(values[y * dx + x + 1]);
      run(t0 | t1 << 1 | t2 << 2 | t3 << 3);
    }
    run(t1 | t2 << 3);
  }
  x = -1;
  t2 = +(values[y * dx] >= value);
  run(t2 << 2);
  while (++x < dx - 1) { t3 = t2; t2 = +above(values[y * dx + x + 1]); run(t2 << 2 | t3 << 3); }
  run(t2 << 3);
}
function _cnContour(values, dx, dy, value) {
  var polygons = [], holes = [];
  _cnIsorings(values, dx, dy, value, function(ring) {
    ring.forEach(function(point) {
      var x = point[0], y = point[1], xt = x | 0, yt = y | 0, v1 = _cnValid(values[yt * dx + xt]);
      if (x > 0 && x < dx && xt === x) point[0] = _cnSmooth1(x, _cnValid(values[yt * dx + xt - 1]), v1, value);
      if (y > 0 && y < dy && yt === y) point[1] = _cnSmooth1(y, _cnValid(values[(yt - 1) * dx + xt]), v1, value);
    });
    if (_cnRingArea(ring) > 0) polygons.push([ring]); else holes.push(ring);
  });
  holes.forEach(function(hole) {
    for (var i = 0, n = polygons.length, polygon; i < n; ++i) {
      if (_cnContains((polygon = polygons[i])[0], hole) !== -1) { polygon.push(hole); return; }
    }
  });
  return polygons;
}
function _cnSturges(count) { return count > 0 ? Math.max(1, Math.ceil(Math.log(count) / Math.LN2) + 1) : 1; }
function _cnContours(values, dx, dy, thresholds) {
  var tz;
  if (Array.isArray(thresholds)) tz = thresholds.slice().sort(function(a, b) { return a - b; });
  else {
    var e0 = Infinity, e1 = -Infinity, cnt = 0, i;
    for (i = 0; i < values.length; i++) {
      var v = values[i];
      if (v === null || v === undefined || v !== v) continue;
      cnt++;
      if (isFinite(v)) { if (v < e0) e0 = v; if (v > e1) e1 = v; }
    }
    if (e0 === Infinity) return [];
    var c = thresholds === null || thresholds === undefined ? _cnSturges(cnt) : thresholds, nn = _hgNice(e0, e1, c);
    tz = _hgTicks(nn[0], nn[1], c);
    while (tz.length && tz[tz.length - 1] >= e1) tz.pop();
    while (tz.length > 1 && tz[1] < e0) tz.shift();
  }
  return tz.map(function(v) { return [v, _cnContour(values, dx, dy, v)]; });
}
function _cnBlurf(radius) {
  var radius0 = Math.floor(radius), w = 2 * radius + 1, t = radius - radius0;
  if (radius0 === radius) return function(T, S, start, stop, step) {
    if (!((stop -= step) >= start)) return;
    var sum = radius * S[start], s = step * radius, i, j;
    for (i = start, j = start + s; i < j; i += step) sum += S[Math.min(stop, i)];
    for (i = start, j = stop; i <= j; i += step) { sum += S[Math.min(stop, i + s)]; T[i] = Math.fround(sum / w); sum -= S[Math.max(start, i - s)]; }
  };
  return function(T, S, start, stop, step) {
    if (!((stop -= step) >= start)) return;
    var sum = radius0 * S[start], s0 = step * radius0, s1 = s0 + step, i, j;
    for (i = start, j = start + s0; i < j; i += step) sum += S[Math.min(stop, i)];
    for (i = start, j = stop; i <= j; i += step) {
      sum += S[Math.min(stop, i + s0)];
      T[i] = Math.fround((sum + t * (S[Math.max(start, i - s1)] + S[Math.min(stop, i + s1)])) / w);
      sum -= S[Math.max(start, i - s0)];
    }
  };
}
// values: an array of numbers that are already float32 values; blurred in place (rx = ry)
function _cnBlur2(values, width, height, rx) {
  if (!width || !height || !rx) return;
  var blur = _cnBlurf(rx), temp = values.slice();
  function blurh(T, S) { for (var y = 0, n = width * height; y < n;) blur(T, S, y, y += width, 1); }
  function blurv(T, S) { for (var x = 0, n = width * height; x < width; ++x) blur(T, S, x, x + n, width); }
  blurh(temp, values); blurh(values, temp); blurh(temp, values);
  blurv(values, temp); blurv(temp, values); blurv(values, temp);
}
function _cnDensityGrid(points, W, H, bandwidth) {
  var r = (Math.sqrt(4 * bandwidth * bandwidth + 1) - 1) / 2, o = r * 3, n = (W + o * 2) >> 2, m = (H + o * 2) >> 2, ln = n * m, values = [], i;
  for (i = 0; i < ln; i++) values.push(0);
  points.forEach(function(p) {
    var xi = (p[0] + o) * 0.25, yi = (p[1] + o) * 0.25;
    if (xi >= 0 && xi < n && yi >= 0 && yi < m) {
      var x0 = Math.floor(xi), y0 = Math.floor(yi), xt = xi - x0 - 0.5, yt = yi - y0 - 0.5, wi = 1;
      var idx = [x0 + y0 * n, x0 + 1 + y0 * n, x0 + 1 + (y0 + 1) * n, x0 + (y0 + 1) * n], wt = [(1 - xt) * (1 - yt) * wi, xt * (1 - yt) * wi, xt * yt * wi, (1 - xt) * yt * wi];
      for (var k = 0; k < 4; k++) if (idx[k] < ln) values[idx[k]] = Math.fround(values[idx[k]] + wt[k]);
    }
  });
  _cnBlur2(values, n, m, r * 0.25);
  return {values: values, n: n, m: m, o: o};
}
function _cnDensityFull(points, W, H, bandwidth, count) {
  var g = _cnDensityGrid(points, W, H, bandwidth), mx = -Infinity, i;
  for (i = 0; i < g.values.length; i++) if (g.values[i] > mx) mx = g.values[i];
  mx = mx / 16;
  var tz = _hgTicks(_CN_MIN_VALUE, mx, count === null || count === undefined ? 20 : count), thr = tz.map(function(d) { return d * 16; });
  var out = _cnContours(g.values, g.n, g.m, thr);
  out.forEach(function(c) { c[1].forEach(function(poly) { poly.forEach(function(ring) { ring.forEach(function(pt) { pt[0] = pt[0] * 4 - g.o; pt[1] = pt[1] * 4 - g.o; }); }); }); });
  return {levels: tz.map(function(v, k) { return [v, out[k][1]]; }), max: mx, grid: g, thr: thr};
}
function _cnDensity(points, W, H, bandwidth, count) { var r = _cnDensityFull(points, W, H, bandwidth, count); return [r.levels, r.max]; }
function _cnRamp(i, m) {
  var t = m === 1 ? 0.5 : i / (m - 1), pos = t * 4, j = Math.min(3, Math.floor(pos)), f = pos - j, a = _CN_STOPS[j], b = _CN_STOPS[j + 1], s = '#';
  for (var c = 0; c < 3; c++) { var h = Math.floor(a[c] + (b[c] - a[c]) * f + 0.5).toString(16).toUpperCase(); s += h.length < 2 ? '0' + h : h; }
  return s;
}
function _cnLine(color) { return 299 * parseInt(color.slice(1, 3), 16) + 587 * parseInt(color.slice(3, 5), 16) + 114 * parseInt(color.slice(5, 7), 16) < 128000 ? '#FFFFFF' : '#04182B'; }
function _cnName(i, m) { return _CN_NAMES[Math.floor((m === 1 ? 0.5 : i / (m - 1)) * 4 + 0.5)]; }
function _cnR(x) { var s = x.toFixed(2); if (s.indexOf('.') >= 0) s = s.replace(/0+$/, '').replace(/\.$/, ''); return s === '-0' ? '0' : s; }
function _cnPath(polys, sx, sy) {
  return polys.map(function(poly) { return poly.map(function(ring) { return 'M' + ring.map(function(p) { return _cnR(p[0] * sx) + ',' + _cnR(p[1] * sy); }).join('L') + 'Z'; }).join(''); }).join('');
}
function _cnNum(v, lo, hi) { return typeof v === 'number' && isFinite(v) ? Math.min(hi, Math.max(lo, v)) : null; }
function _cnUsable(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12; }
_RENDERERS['contour_plot'] = function(b) {
  // the optional 'version' field is read by _hgVersionNote at the end
  var g = b.grid, pts = b.points, notes = '';
  function plural(c, one, many) { return c + ' ' + (c === 1 ? one : many); }
  function fail(msg) { return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">' + msg + '</div>' + notes + _hgVersionNote(b, 'contour_plot')); }
  var isObj = function(o) { return !!o && typeof o === 'object' && !Array.isArray(o); };
  if (!isObj(g) && !Array.isArray(pts)) return fail('A contour plot needs either a grid (width, height and values) or points.');
  var gridMode = isObj(g);
  if (gridMode && Array.isArray(pts)) notes += _hgNote('Both a grid and points were given; the grid is drawn.');
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '';
  var xl = b.x_label ? String(b.x_label).slice(0, 30) : '', yl = b.y_label ? String(b.y_label).slice(0, 30) : '';
  var levels = [], shares, total, vlab, X0, X1, Y0, Y1, flip, dots = '', disp, sx, sy, gw, gh, loV = 0, hiV = 0, xy, bw = 0, i, k;
  if (gridMode) {
    gw = g.width; gh = g.height;
    var okd = function(v) { return typeof v === 'number' && isFinite(v) && v === Math.floor(v) && v >= 2 && v <= 100; };
    if (!(okd(gw) && okd(gh))) return fail('The grid needs a width and a height that are whole numbers from 2 to 100.');
    var raw = Array.isArray(g.values) ? g.values : [];
    if (raw.length !== gw * gh) return fail('The grid needs width times height numbers: ' + (gw * gh) + ' expected, ' + raw.length + ' given.');
    var vals = raw.map(function(v) { return _cnUsable(v) ? v : null; }), bad = 0, usable = [];
    vals.forEach(function(v) { if (v === null) bad++; else usable.push(v); });
    if (bad) notes += _hgNote(plural(bad, 'grid value was', 'grid values were') + ' not a usable number and ' + (bad === 1 ? 'was' : 'were') + ' left empty.');
    var tn = _cnNum(b.thresholds, 3, 20), out = _cnContours(vals, gw, gh, tn === null ? null : Math.floor(tn));
    sx = _CN_W / gw; sy = _CN_H / gh;
    out.forEach(function(c) { if (c[1].length) levels.push(c); });
    total = usable.length;
    shares = levels.map(function(l) { var c = 0; usable.forEach(function(x) { if (x >= l[0]) c++; }); return c; });
    vlab = b.value_label ? String(b.value_label).slice(0, 30) : 'Value';
    xl = xl || 'Column'; yl = yl || 'Row';
    X0 = 0; X1 = gw; Y0 = 0; Y1 = gh; flip = false;
    disp = levels.map(function(l) { return l[0]; });
    if (usable.length) { loV = usable[0]; hiV = usable[0]; usable.forEach(function(x) { if (x < loV) loV = x; if (x > hiV) hiV = x; }); }
  } else {
    var lst = pts.slice(0, _CN_MAXPTS), beyond = pts.length - _CN_MAXPTS;
    xy = lst.filter(function(p) { return isObj(p) && _cnUsable(p.x) && _cnUsable(p.y); }).map(function(p) { return [p.x, p.y]; });
    var bad2 = lst.length - xy.length;
    if (beyond > 0) notes += _hgNote(plural(beyond, 'point', 'points') + ' beyond the first 2000 ' + (beyond === 1 ? 'was' : 'were') + ' not used.');
    if (bad2) notes += _hgNote(plural(bad2, 'point was', 'points were') + ' not an object with a numeric x and y and ' + (bad2 === 1 ? 'was' : 'were') + ' skipped.');
    if (xy.length < 3) return fail('A density contour plot needs at least 3 points with a numeric x and y; this list has ' + xy.length + '.');
    var xs = xy.map(function(p) { return p[0]; }), ys = xy.map(function(p) { return p[1]; });
    var xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
    xs.forEach(function(v) { if (v < xmin) xmin = v; if (v > xmax) xmax = v; });
    ys.forEach(function(v) { if (v < ymin) ymin = v; if (v > ymax) ymax = v; });
    var nx = xmin === xmax ? _hgNice(xmin - 1, xmax + 1, 6) : _hgNice(xmin, xmax, 6), ny = ymin === ymax ? _hgNice(ymin - 1, ymax + 1, 6) : _hgNice(ymin, ymax, 6);
    X0 = nx[0]; X1 = nx[1]; Y0 = ny[0]; Y1 = ny[1];
    var px = xs.map(function(x) { return (x - X0) * _CN_W / (X1 - X0); }), py = ys.map(function(y) { return (Y1 - y) * _CN_H / (Y1 - Y0); });
    var bwn = _cnNum(b.bandwidth, 5, 60);
    bw = bwn === null ? 20 : bwn;
    var tn2 = _cnNum(b.thresholds, 3, 20), res = _cnDensityFull(px.map(function(a, j) { return [a, py[j]]; }), _CN_W, _CN_H, bw, tn2 === null ? null : Math.floor(tn2));
    var gd = res.grid;
    res.levels.forEach(function(l, j) { if (l[1].length) levels.push([l[0], l[1], res.thr[j]]); });
    sx = 1; sy = 1;
    var cells = px.map(function(a, j) {
      var xi = (a + gd.o) * 0.25, yi = (py[j] + gd.o) * 0.25;
      return xi >= 0 && xi < gd.n && yi >= 0 && yi < gd.m ? gd.values[Math.floor(xi) + Math.floor(yi) * gd.n] : null;
    });
    total = xy.length;
    shares = levels.map(function(l) { var c = 0; cells.forEach(function(v) { if (v !== null && v >= l[2]) c++; }); return c; });
    vlab = 'Density (points per 10,000 px² of the drawing)';
    flip = true;
    dots = px.length ? 'M' + px.map(function(a, j) { return _cnR(a) + ',' + _cnR(py[j]) + 'h0'; }).join('M') : '';
    disp = levels.map(function(l) { return l[0] * 10000; });
  }
  if (!levels.length) return fail('No contour level could be drawn from this data.');
  var budget = _CN_BUDGET, keep = 0;
  for (i = 0; i < levels.length; i++) {
    var cnt = 0;
    levels[i][1].forEach(function(poly) { poly.forEach(function(r) { cnt += r.length; }); });
    if (cnt > budget && keep) break;
    budget -= cnt; keep++;
  }
  if (keep < levels.length) {
    notes += _hgNote(plural(levels.length - keep, 'highest level was', 'highest levels were') + ' not drawn to keep the picture small (limit 40,000 outline points).');
    levels = levels.slice(0, keep); shares = shares.slice(0, keep); disp = disp.slice(0, keep);
  }
  var m = levels.length, d = _hgDecimals(disp), lab = disp.map(function(v) { return _hgNum(v, d); }), cols = [], bands = '';
  for (i = 0; i < m; i++) cols.push(_cnRamp(i, m));
  var rng = function(j) { return lab[j] + (j + 1 < m ? ' to ' + lab[j + 1] + us : us + ' and above'); };
  for (i = 0; i < m; i++) {
    bands += '<path class="cnb" data-cb="arc" data-key="' + _esc(rng(i)) + '" d="' + _cnPath(levels[i][1], sx, sy) + '" fill="' + cols[i] + '" stroke="' + _cnLine(cols[i]) + '" stroke-width="1" stroke-linejoin="round" fill-rule="evenodd" ' +
      'vector-effect="non-scaling-stroke" style="' + _ifK(i, m) + 'opacity:var(--k,1);"><title>' + _esc(rng(i)) + '</title></path>';
  }
  if (dots) bands += '<path class="cnp" d="' + dots + '" fill="none" style="stroke:var(--text,#0F172A);" stroke-opacity="0.35" stroke-width="3" stroke-linecap="round" vector-effect="non-scaling-stroke"/>';
  var svg = '<svg viewBox="0 0 ' + _CN_W + ' ' + _CN_H + '" width="100%" style="display:block;height:auto;overflow:hidden;" aria-hidden="true" focusable="false">' +
    '<rect x="0" y="0" width="' + _CN_W + '" height="' + _CN_H + '" style="fill:var(--surface,#F8FAFC);"/>' + bands +
    '<rect x="0" y="0" width="' + _CN_W + '" height="' + _CN_H + '" fill="none" style="stroke:var(--border,#CBD5E1);" stroke-width="1" vector-effect="non-scaling-stroke"/></svg>';
  var ex = _hgTicks(X0, X1, 6), ey = _hgTicks(Y0, Y1, 6), xaxis = '', yaxis = '';
  if (ex.length) { var dxs = _hgDecimals(ex); xaxis = _hgAxis(ex, X0, X1 - X0, ex.map(function(v) { return _hgNum(v, dxs); })); }
  if (ey.length) {
    var dys = _hgDecimals(ey);
    ey.forEach(function(v) {
      yaxis += '<div class="cny" style="position:absolute;right:100%;margin-right:6px;top:' + _tmPct(flip ? Y1 - v : v - Y0, Y1 - Y0) +
        ';transform:translateY(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + _hgNum(v, dys) + '</div>';
    });
  }
  var aria;
  if (gridMode) aria = 'Contour plot of a ' + gw + ' by ' + gh + ' grid, values from ' + _bpFmt(loV, 2) + ' to ' + _bpFmt(hiV, 2) + us + ', ' + m + ' level' + (m === 1 ? '' : 's') + '. Darker bands are higher values.';
  else aria = 'Density contour plot of ' + total + ' points, ' + m + ' level' + (m === 1 ? '' : 's') + ' from ' + lab[0] + ' to ' + lab[m - 1] + ' points per 10,000 px². Darker bands are denser areas.';
  var css = '<style>@container (max-width:560px){.ifcn .hgx:not(.hgc){display:none}}</style>';
  var chart = '<div class="ifcn" style="container-type:inline-size;max-width:100%;overflow:hidden;">' + css +
    (yl ? '<div style="font-size:0.75rem;color:var(--muted,#475569);margin:0 0 2px 0;">' + _esc(yl) + '</div>' : '') +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;margin:8px 30px 34px 54px;">' + svg + yaxis + xaxis + '</div>' +
    (xl ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 30px 0 54px;">' + _esc(xl) + '</div>' : '') + '</div>';
  var ent = [['Below ' + lab[0] + us, 'var(--surface,#F8FAFC)']];
  for (i = 0; i < m; i++) ent.push([rng(i), cols[i]]);
  var legend = '<div class="cnleg" style="margin-top:8px;font-size:12px;line-height:16px;color:var(--text,#0F172A);"><div style="color:var(--muted,#475569);margin-bottom:4px;">' + _esc(vlab) + '</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:4px 14px;">' +
    ent.map(function(e) { return '<span style="display:inline-flex;align-items:center;gap:5px;"><span style="display:inline-block;width:12px;height:12px;border:1px solid #64748B;background:' + e[1] + ';"></span>' + _esc(e[0]) + '</span>'; }).join('') +
    '</div></div>';
  var tables, rows = [];
  if (gridMode) {
    for (i = 0; i < m; i++) rows.push([lab[i] + us, _cnName(i, m), (shares[i] / total * 100).toFixed(1) + '%']);
    tables = _ifTable(['Level from', 'Band colour', 'Cells at or above'], rows);
  } else {
    for (i = 0; i < m; i++) rows.push([lab[i], _cnName(i, m), (shares[i] / total * 100).toFixed(1) + '% (' + shares[i] + ' of ' + total + ')']);
    tables = _ifTable(['Density from (points per 10,000 px²)', 'Band colour', 'Points in cells at or above'], rows);
    var prow = [];
    for (k = 0; k < Math.min(total, _CN_MAXROWS); k++) prow.push([String(k + 1), String(xy[k][0]), String(xy[k][1])]);
    tables += _ifTable(['Point', 'x', 'y'], prow);
    if (total > _CN_MAXROWS) notes += _hgNote('Table of points shows the first ' + _CN_MAXROWS + ' of ' + total + '.');
  }
  return _ifWrap(_ifTitle(b) + chart + legend +
    _hgNote('Each band is the area at or above its level; the outline between two bands is the level.' + (gridMode ? '' : ' Density is smoothed (bandwidth ' + _bpFmt(bw, 2) + ' px).')) +
    notes + _hgVersionNote(b, 'contour_plot') + tables);
};

// ── voronoi (I56 nearest-site regions of a set of points) ───────────────────────────────────────────────────────────────────────────────────
// Three modules ported by hand, each function keeping the name and the order of operations of its source so the output is identical to the real modules:
//   robust-predicates 3.0.3 (Unlicense / public domain, Vladimir Agafonkin): orient2d with its adaptive stages (fast filter, stage B, tails stage C, full expansion D).
//   delaunator 5.1.0 (ISC, Mapbox): Delaunator update() (seed triangle, radial sort by quicksort, advancing hull with its angular hash), _legalize, _link, _addTriangle,
//     pseudoAngle, dist, inCircle, circumradius, circumcenter.
//   d3-delaunay 6.0.4 (ISC, Mike Bostock, Observable): Delaunay _init (inedges, hull index, the collinear check and its jitter) and _step; Voronoi _init (circumcenters
//     and exterior rays), _cell, _clip, _clipFinite, _clipSegment, _clipInfinite, _edge, _project, _edgecode, _regioncode, _simplify, contains, and
//     renderCell (the cellPolygon of Polygon).
// d3-delaunay's collinear fallback jitters the points with Math.sin, Math.cos and Math.hypot, which are not correctly rounded and differ between engines and
// libms: V8's (as in Node) are ported too (fdlibm sin/cos for |x| <= 2^19*pi/2 with the engine's own beyond, and V8's Kahan-summed hypot) so both twins agree to
// the bit. Twin of the _vo_* functions and _render_voronoi in renderers/web_article.py.
var _VO_R_EPS = 1.1102230246251565e-16, _VO_SPLIT = 134217729;
var _VO_RESERR = (3 + 8 * _VO_R_EPS) * _VO_R_EPS;
// fast_expansion_sum_zeroelim routine from original code
function _voSum(elen, e, flen, f, h) {
    var Q, Qnew, hh, bvirt;
    var enow = e[0];
    var fnow = f[0];
    var eindex = 0;
    var findex = 0;
    if ((fnow > enow) === (fnow > -enow)) {
        Q = enow;
        enow = e[++eindex];
    } else {
        Q = fnow;
        fnow = f[++findex];
    }
    var hindex = 0;
    if (eindex < elen && findex < flen) {
        if ((fnow > enow) === (fnow > -enow)) {
            Qnew = enow + Q;
            hh = Q - (Qnew - enow);
            enow = e[++eindex];
        } else {
            Qnew = fnow + Q;
            hh = Q - (Qnew - fnow);
            fnow = f[++findex];
        }
        Q = Qnew;
        if (hh !== 0) {
            h[hindex++] = hh;
        }
        while (eindex < elen && findex < flen) {
            if ((fnow > enow) === (fnow > -enow)) {
                Qnew = Q + enow;
                bvirt = Qnew - Q;
                hh = Q - (Qnew - bvirt) + (enow - bvirt);
                enow = e[++eindex];
            } else {
                Qnew = Q + fnow;
                bvirt = Qnew - Q;
                hh = Q - (Qnew - bvirt) + (fnow - bvirt);
                fnow = f[++findex];
            }
            Q = Qnew;
            if (hh !== 0) {
                h[hindex++] = hh;
            }
        }
    }
    while (eindex < elen) {
        Qnew = Q + enow;
        bvirt = Qnew - Q;
        hh = Q - (Qnew - bvirt) + (enow - bvirt);
        enow = e[++eindex];
        Q = Qnew;
        if (hh !== 0) {
            h[hindex++] = hh;
        }
    }
    while (findex < flen) {
        Qnew = Q + fnow;
        bvirt = Qnew - Q;
        hh = Q - (Qnew - bvirt) + (fnow - bvirt);
        fnow = f[++findex];
        Q = Qnew;
        if (hh !== 0) {
            h[hindex++] = hh;
        }
    }
    if (Q !== 0 || hindex === 0) {
        h[hindex++] = Q;
    }
    return hindex;
}


function _voEstimate(elen, e) {
    var Q = e[0];
    for (var i = 1; i < elen; i++) Q += e[i];
    return Q;
}


var _VO_CCWA = (3 + 16 * _VO_R_EPS) * _VO_R_EPS;
var _VO_CCWB = (2 + 12 * _VO_R_EPS) * _VO_R_EPS;
var _VO_CCWC = (9 + 64 * _VO_R_EPS) * _VO_R_EPS * _VO_R_EPS;

var _VO_O_B = new Float64Array(4);
var _VO_O_C1 = new Float64Array(8);
var _VO_O_C2 = new Float64Array(12);
var _VO_O_D = new Float64Array(16);
var _VO_O_u = new Float64Array(4);

function _voOrient2dAdapt(ax, ay, bx, by, cx, cy, detsum) {
    var acxtail, acytail, bcxtail, bcytail;
    var bvirt, c, ahi, alo, bhi, blo, _i, _j, _0, s1, s0, t1, t0, u3;

    var acx = ax - cx;
    var bcx = bx - cx;
    var acy = ay - cy;
    var bcy = by - cy;

    s1 = acx * bcy;
    c = _VO_SPLIT * acx;
    ahi = c - (c - acx);
    alo = acx - ahi;
    c = _VO_SPLIT * bcy;
    bhi = c - (c - bcy);
    blo = bcy - bhi;
    s0 = alo * blo - (s1 - ahi * bhi - alo * bhi - ahi * blo);
    t1 = acy * bcx;
    c = _VO_SPLIT * acy;
    ahi = c - (c - acy);
    alo = acy - ahi;
    c = _VO_SPLIT * bcx;
    bhi = c - (c - bcx);
    blo = bcx - bhi;
    t0 = alo * blo - (t1 - ahi * bhi - alo * bhi - ahi * blo);
    _i = s0 - t0;
    bvirt = s0 - _i;
    _VO_O_B[0] = s0 - (_i + bvirt) + (bvirt - t0);
    _j = s1 + _i;
    bvirt = _j - s1;
    _0 = s1 - (_j - bvirt) + (_i - bvirt);
    _i = _0 - t1;
    bvirt = _0 - _i;
    _VO_O_B[1] = _0 - (_i + bvirt) + (bvirt - t1);
    u3 = _j + _i;
    bvirt = u3 - _j;
    _VO_O_B[2] = _j - (u3 - bvirt) + (_i - bvirt);
    _VO_O_B[3] = u3;

    var det = _voEstimate(4, _VO_O_B);
    var errbound = _VO_CCWB * detsum;
    if (det >= errbound || -det >= errbound) {
        return det;
    }

    bvirt = ax - acx;
    acxtail = ax - (acx + bvirt) + (bvirt - cx);
    bvirt = bx - bcx;
    bcxtail = bx - (bcx + bvirt) + (bvirt - cx);
    bvirt = ay - acy;
    acytail = ay - (acy + bvirt) + (bvirt - cy);
    bvirt = by - bcy;
    bcytail = by - (bcy + bvirt) + (bvirt - cy);

    if (acxtail === 0 && acytail === 0 && bcxtail === 0 && bcytail === 0) {
        return det;
    }

    errbound = _VO_CCWC * detsum + _VO_RESERR * Math.abs(det);
    det += (acx * bcytail + bcy * acxtail) - (acy * bcxtail + bcx * acytail);
    if (det >= errbound || -det >= errbound) return det;

    s1 = acxtail * bcy;
    c = _VO_SPLIT * acxtail;
    ahi = c - (c - acxtail);
    alo = acxtail - ahi;
    c = _VO_SPLIT * bcy;
    bhi = c - (c - bcy);
    blo = bcy - bhi;
    s0 = alo * blo - (s1 - ahi * bhi - alo * bhi - ahi * blo);
    t1 = acytail * bcx;
    c = _VO_SPLIT * acytail;
    ahi = c - (c - acytail);
    alo = acytail - ahi;
    c = _VO_SPLIT * bcx;
    bhi = c - (c - bcx);
    blo = bcx - bhi;
    t0 = alo * blo - (t1 - ahi * bhi - alo * bhi - ahi * blo);
    _i = s0 - t0;
    bvirt = s0 - _i;
    _VO_O_u[0] = s0 - (_i + bvirt) + (bvirt - t0);
    _j = s1 + _i;
    bvirt = _j - s1;
    _0 = s1 - (_j - bvirt) + (_i - bvirt);
    _i = _0 - t1;
    bvirt = _0 - _i;
    _VO_O_u[1] = _0 - (_i + bvirt) + (bvirt - t1);
    u3 = _j + _i;
    bvirt = u3 - _j;
    _VO_O_u[2] = _j - (u3 - bvirt) + (_i - bvirt);
    _VO_O_u[3] = u3;
    var C1len = _voSum(4, _VO_O_B, 4, _VO_O_u, _VO_O_C1);

    s1 = acx * bcytail;
    c = _VO_SPLIT * acx;
    ahi = c - (c - acx);
    alo = acx - ahi;
    c = _VO_SPLIT * bcytail;
    bhi = c - (c - bcytail);
    blo = bcytail - bhi;
    s0 = alo * blo - (s1 - ahi * bhi - alo * bhi - ahi * blo);
    t1 = acy * bcxtail;
    c = _VO_SPLIT * acy;
    ahi = c - (c - acy);
    alo = acy - ahi;
    c = _VO_SPLIT * bcxtail;
    bhi = c - (c - bcxtail);
    blo = bcxtail - bhi;
    t0 = alo * blo - (t1 - ahi * bhi - alo * bhi - ahi * blo);
    _i = s0 - t0;
    bvirt = s0 - _i;
    _VO_O_u[0] = s0 - (_i + bvirt) + (bvirt - t0);
    _j = s1 + _i;
    bvirt = _j - s1;
    _0 = s1 - (_j - bvirt) + (_i - bvirt);
    _i = _0 - t1;
    bvirt = _0 - _i;
    _VO_O_u[1] = _0 - (_i + bvirt) + (bvirt - t1);
    u3 = _j + _i;
    bvirt = u3 - _j;
    _VO_O_u[2] = _j - (u3 - bvirt) + (_i - bvirt);
    _VO_O_u[3] = u3;
    var C2len = _voSum(C1len, _VO_O_C1, 4, _VO_O_u, _VO_O_C2);

    s1 = acxtail * bcytail;
    c = _VO_SPLIT * acxtail;
    ahi = c - (c - acxtail);
    alo = acxtail - ahi;
    c = _VO_SPLIT * bcytail;
    bhi = c - (c - bcytail);
    blo = bcytail - bhi;
    s0 = alo * blo - (s1 - ahi * bhi - alo * bhi - ahi * blo);
    t1 = acytail * bcxtail;
    c = _VO_SPLIT * acytail;
    ahi = c - (c - acytail);
    alo = acytail - ahi;
    c = _VO_SPLIT * bcxtail;
    bhi = c - (c - bcxtail);
    blo = bcxtail - bhi;
    t0 = alo * blo - (t1 - ahi * bhi - alo * bhi - ahi * blo);
    _i = s0 - t0;
    bvirt = s0 - _i;
    _VO_O_u[0] = s0 - (_i + bvirt) + (bvirt - t0);
    _j = s1 + _i;
    bvirt = _j - s1;
    _0 = s1 - (_j - bvirt) + (_i - bvirt);
    _i = _0 - t1;
    bvirt = _0 - _i;
    _VO_O_u[1] = _0 - (_i + bvirt) + (bvirt - t1);
    u3 = _j + _i;
    bvirt = u3 - _j;
    _VO_O_u[2] = _j - (u3 - bvirt) + (_i - bvirt);
    _VO_O_u[3] = u3;
    var Dlen = _voSum(C2len, _VO_O_C2, 4, _VO_O_u, _VO_O_D);

    return _VO_O_D[Dlen - 1];
}

function _voOrient2d(ax, ay, bx, by, cx, cy) {
    var detleft = (ay - cy) * (bx - cx);
    var detright = (ax - cx) * (by - cy);
    var det = detleft - detright;

    var detsum = Math.abs(detleft + detright);
    if (Math.abs(det) >= _VO_CCWA * detsum) return det;

    return -_voOrient2dAdapt(ax, ay, bx, by, cx, cy, detsum);
}

// ---- V8's Math.sin / Math.cos (fdlibm: __kernel_sin, __kernel_cos, __ieee754_rem_pio2) and Math.hypot
var _VO_NPIO2_HW = [0x3FF921FB, 0x400921FB, 0x4012D97C, 0x401921FB, 0x401F6A7A, 0x4022D97C, 0x4025FDBB, 0x402921FB, 0x402C463A, 0x402F6A7A, 0x4031475C, 0x4032D97C,
  0x40346B9C, 0x4035FDBB, 0x40378FDB, 0x403921FB, 0x403AB41B, 0x403C463A, 0x403DD85A, 0x403F6A7A, 0x40407E4C, 0x4041475C, 0x4042106C, 0x4042D97C,
  0x4043A28C, 0x40446B9C, 0x404534AC, 0x4045FDBB, 0x4046C6CB, 0x40478FDB, 0x404858EB, 0x404921FB];
var _VO_PIO2_1 = 1.57079632673412561417e+00, _VO_PIO2_1T = 6.07710050650619224932e-11;
var _VO_PIO2_2 = 6.07710050630396597660e-11, _VO_PIO2_2T = 2.02226624879595063154e-21;
var _VO_PIO2_3 = 2.02226624871116645580e-21, _VO_PIO2_3T = 8.47842766036889956997e-32;
var _VO_INVPIO2 = 6.36619772367581382433e-01;
var _VO_F64 = new Float64Array(1), _VO_U32 = new Uint32Array(_VO_F64.buffer), _VO_LE = new Uint8Array(new Uint32Array([1]).buffer)[0] === 1;
function _voHi(x) { _VO_F64[0] = x; return _VO_U32[_VO_LE ? 1 : 0] | 0; }
function _voKernelSin(x, y, iy) {
  var S1 = -1.66666666666666324348e-01, S2 = 8.33333333332248946124e-03, S3 = -1.98412698298579493134e-04, S4 = 2.75573137070700676789e-06, S5 = -2.50507602534068634195e-08, S6 = 1.58969099521155010221e-10;
  var ix = _voHi(x) & 0x7fffffff;
  if (ix < 0x3e400000) { if (Math.trunc(x) === 0) return x; }
  var z = x * x, v = z * x, r = S2 + z * (S3 + z * (S4 + z * (S5 + z * S6)));
  if (iy === 0) return x + v * (S1 + z * r);
  return x - ((z * (0.5 * y - v * r) - y) - v * S1);
}
function _voKernelCos(x, y) {
  var C1 = 4.16666666666666019037e-02, C2 = -1.38888888888741095749e-03, C3 = 2.48015872894767294178e-05, C4 = -2.75573143513906633035e-07, C5 = 2.08757232129817482790e-09, C6 = -1.13596475577881948265e-11;
  var ix = _voHi(x) & 0x7fffffff;
  if (ix < 0x3e400000) { if (Math.trunc(x) === 0) return 1; }
  var z = x * x, r = z * (C1 + z * (C2 + z * (C3 + z * (C4 + z * (C5 + z * C6)))));
  if (ix < 0x3FD33333) return 1 - (0.5 * z - (z * r - x * y));
  var qx;
  if (ix > 0x3fe90000) qx = 0.28125;
  else { _VO_U32[_VO_LE ? 1 : 0] = ix - 0x00200000; _VO_U32[_VO_LE ? 0 : 1] = 0; qx = _VO_F64[0]; }
  var hz = 0.5 * z - qx, a = 1 - qx;
  return a - (hz - (z * r - x * y));
}
// __ieee754_rem_pio2 for |x| <= 2^19*pi/2 (the medium sizes): [n, y0, y1], or null beyond.
function _voRemPio2(x) {
  var hx = _voHi(x), ix = hx & 0x7fffffff, z, y0, y1;
  if (ix <= 0x3fe921fb) return [0, x, 0];
  if (ix < 0x4002d97c) {
    if (hx > 0) {
      z = x - _VO_PIO2_1;
      if (ix !== 0x3ff921fb) { y0 = z - _VO_PIO2_1T; y1 = (z - y0) - _VO_PIO2_1T; }
      else { z -= _VO_PIO2_2; y0 = z - _VO_PIO2_2T; y1 = (z - y0) - _VO_PIO2_2T; }
      return [1, y0, y1];
    }
    z = x + _VO_PIO2_1;
    if (ix !== 0x3ff921fb) { y0 = z + _VO_PIO2_1T; y1 = (z - y0) + _VO_PIO2_1T; }
    else { z += _VO_PIO2_2; y0 = z + _VO_PIO2_2T; y1 = (z - y0) + _VO_PIO2_2T; }
    return [-1, y0, y1];
  }
  if (ix <= 0x413921fb) {
    var t = Math.abs(x), n = Math.trunc(t * _VO_INVPIO2 + 0.5), fn = n, r = t - fn * _VO_PIO2_1, w = fn * _VO_PIO2_1T, j, i;
    if (n < 32 && ix !== _VO_NPIO2_HW[n - 1]) { y0 = r - w; }
    else {
      j = ix >> 20;
      y0 = r - w;
      i = j - ((_voHi(y0) >> 20) & 0x7ff);
      if (i > 16) {
        t = r; w = fn * _VO_PIO2_2; r = t - w; w = fn * _VO_PIO2_2T - ((t - r) - w); y0 = r - w;
        i = j - ((_voHi(y0) >> 20) & 0x7ff);
        if (i > 49) { t = r; w = fn * _VO_PIO2_3; r = t - w; w = fn * _VO_PIO2_3T - ((t - r) - w); y0 = r - w; }
      }
    }
    y1 = (r - y0) - w;
    if (hx < 0) return [-n, -y0, -y1];
    return [n, y0, y1];
  }
  return null;
}
function _voSin(x) {
  var ix = _voHi(x) & 0x7fffffff;
  if (ix <= 0x3fe921fb) return _voKernelSin(x, 0, 0);
  if (ix >= 0x7ff00000) return x - x;
  var r = _voRemPio2(x);
  if (r === null) return Math.sin(x);
  var k = r[0] & 3;
  return k === 0 ? _voKernelSin(r[1], r[2], 1) : k === 1 ? _voKernelCos(r[1], r[2]) : k === 2 ? -_voKernelSin(r[1], r[2], 1) : -_voKernelCos(r[1], r[2]);
}
function _voCos(x) {
  var ix = _voHi(x) & 0x7fffffff;
  if (ix <= 0x3fe921fb) return _voKernelCos(x, 0);
  if (ix >= 0x7ff00000) return x - x;
  var r = _voRemPio2(x);
  if (r === null) return Math.cos(x);
  var k = r[0] & 3;
  return k === 0 ? _voKernelCos(r[1], r[2]) : k === 1 ? -_voKernelSin(r[1], r[2], 1) : k === 2 ? -_voKernelCos(r[1], r[2]) : _voKernelSin(r[1], r[2], 1);
}
// V8 Math.hypot(a, b): the largest magnitude scales the terms, which are summed with Kahan compensation.
function _voHypot(a, b) {
  a = Math.abs(a); b = Math.abs(b);
  var mx = a > b ? a : b;
  if (mx === Infinity) return mx;
  if (a !== a || b !== b) return NaN;
  if (mx === 0) return 0;
  var s = 0, comp = 0, v = [a, b], k, n, summand, pre;
  for (k = 0; k < 2; k++) { n = v[k] / mx; summand = n * n - comp; pre = s + summand; comp = (pre - s) - summand; s = pre; }
  return Math.sqrt(s) * mx;
}

// ---- delaunator 5.1.0
var _VO_EPSILON = 2.220446049250313e-16;   // 2^-52
var _VO_EDGE_STACK = new Uint32Array(512);
function _voPseudoAngle(dx, dy) {
  var p = dx / (Math.abs(dx) + Math.abs(dy));
  return (dy > 0 ? 3 - p : 1 + p) / 4;   // [0..1]
}
function _voDist(ax, ay, bx, by) { var dx = ax - bx, dy = ay - by; return dx * dx + dy * dy; }
function _voInCircle(ax, ay, bx, by, cx, cy, px, py) {
  var dx = ax - px, dy = ay - py, ex = bx - px, ey = by - py, fx = cx - px, fy = cy - py;
  var ap = dx * dx + dy * dy, bp = ex * ex + ey * ey, cp = fx * fx + fy * fy;
  return dx * (ey * cp - bp * fy) - dy * (ex * cp - bp * fx) + ap * (ex * fy - ey * fx) < 0;
}
function _voCircumradius(ax, ay, bx, by, cx, cy) {
  var dx = bx - ax, dy = by - ay, ex = cx - ax, ey = cy - ay;
  var bl = dx * dx + dy * dy, cl = ex * ex + ey * ey, d = 0.5 / (dx * ey - dy * ex);
  var x = (ey * bl - dy * cl) * d, y = (dx * cl - ex * bl) * d;
  return x * x + y * y;
}
function _voCircumcenter(ax, ay, bx, by, cx, cy) {
  var dx = bx - ax, dy = by - ay, ex = cx - ax, ey = cy - ay;
  var bl = dx * dx + dy * dy, cl = ex * ex + ey * ey, d = 0.5 / (dx * ey - dy * ex);
  return {x: ax + (ey * bl - dy * cl) * d, y: ay + (dx * cl - ex * bl) * d};
}
function _voSwap(arr, i, j) { var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp; }
function _voQuicksort(ids, dists, left, right) {
  var i, j, temp, tempDist;
  if (right - left <= 20) {
    for (i = left + 1; i <= right; i++) {
      temp = ids[i]; tempDist = dists[temp]; j = i - 1;
      while (j >= left && dists[ids[j]] > tempDist) ids[j + 1] = ids[j--];
      ids[j + 1] = temp;
    }
  } else {
    var median = (left + right) >> 1;
    i = left + 1; j = right;
    _voSwap(ids, median, i);
    if (dists[ids[left]] > dists[ids[right]]) _voSwap(ids, left, right);
    if (dists[ids[i]] > dists[ids[right]]) _voSwap(ids, i, right);
    if (dists[ids[left]] > dists[ids[i]]) _voSwap(ids, left, i);
    temp = ids[i]; tempDist = dists[temp];
    while (true) {
      do i++; while (dists[ids[i]] < tempDist);
      do j--; while (dists[ids[j]] > tempDist);
      if (j < i) break;
      _voSwap(ids, i, j);
    }
    ids[left + 1] = ids[j];
    ids[j] = temp;
    if (right - i + 1 >= j - left) { _voQuicksort(ids, dists, i, right); _voQuicksort(ids, dists, left, j - 1); }
    else { _voQuicksort(ids, dists, left, j - 1); _voQuicksort(ids, dists, i, right); }
  }
}
// Delaunator: coords is a Float64Array [x0, y0, x1, y1, ...]; .triangles, .halfedges and .hull are typed arrays.
function _VoDelaunator(coords) {
  var n = coords.length >> 1;
  this.coords = coords;
  var maxTriangles = Math.max(2 * n - 5, 0);
  this._triangles = new Uint32Array(maxTriangles * 3);
  this._halfedges = new Int32Array(maxTriangles * 3);
  this._hashSize = Math.ceil(Math.sqrt(n));
  this._hullPrev = new Uint32Array(n);
  this._hullNext = new Uint32Array(n);
  this._hullTri = new Uint32Array(n);
  this._hullHash = new Int32Array(this._hashSize);
  this._ids = new Uint32Array(n);
  this._dists = new Float64Array(n);
  this.trianglesLen = 0;
  this._cx = 0; this._cy = 0; this._hullStart = 0;
  this.hull = this._triangles;
  this.triangles = this._triangles;
  this.halfedges = this._halfedges;
  this.update();
}
_VoDelaunator.prototype.update = function() {
  var coords = this.coords, hullPrev = this._hullPrev, hullNext = this._hullNext, hullTri = this._hullTri, hullHash = this._hullHash;
  var n = coords.length >> 1, i, j, k, d, x, y, r;
  var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (i = 0; i < n; i++) {
    x = coords[2 * i]; y = coords[2 * i + 1];
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
    this._ids[i] = i;
  }
  var cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
  var i0 = 0, i1 = 0, i2 = 0, minDist;
  // pick a seed point close to the center
  for (i = 0, minDist = Infinity; i < n; i++) {
    d = _voDist(cx, cy, coords[2 * i], coords[2 * i + 1]);
    if (d < minDist) { i0 = i; minDist = d; }
  }
  var i0x = coords[2 * i0], i0y = coords[2 * i0 + 1];
  // find the point closest to the seed
  for (i = 0, minDist = Infinity; i < n; i++) {
    if (i === i0) continue;
    d = _voDist(i0x, i0y, coords[2 * i], coords[2 * i + 1]);
    if (d < minDist && d > 0) { i1 = i; minDist = d; }
  }
  var i1x = coords[2 * i1], i1y = coords[2 * i1 + 1];
  var minRadius = Infinity;
  // find the third point which forms the smallest circumcircle with the first two
  for (i = 0; i < n; i++) {
    if (i === i0 || i === i1) continue;
    r = _voCircumradius(i0x, i0y, i1x, i1y, coords[2 * i], coords[2 * i + 1]);
    if (r < minRadius) { i2 = i; minRadius = r; }
  }
  var i2x = coords[2 * i2], i2y = coords[2 * i2 + 1];
  if (minRadius === Infinity) {
    // order collinear points by dx (or dy if all x are identical) and return the list as a hull
    for (i = 0; i < n; i++) this._dists[i] = (coords[2 * i] - coords[0]) || (coords[2 * i + 1] - coords[1]);
    _voQuicksort(this._ids, this._dists, 0, n - 1);
    var hull0 = new Uint32Array(n), j0 = 0, d0, id0;
    for (i = 0, d0 = -Infinity; i < n; i++) {
      id0 = this._ids[i]; d = this._dists[id0];
      if (d > d0) { hull0[j0++] = id0; d0 = d; }
    }
    this.hull = hull0.subarray(0, j0);
    this.triangles = new Uint32Array(0);
    this.halfedges = new Int32Array(0);
    return;
  }
  // swap the order of the seed points for counter-clockwise orientation
  if (_voOrient2d(i0x, i0y, i1x, i1y, i2x, i2y) < 0) {
    var sw = i1, swx = i1x, swy = i1y;
    i1 = i2; i1x = i2x; i1y = i2y;
    i2 = sw; i2x = swx; i2y = swy;
  }
  var center = _voCircumcenter(i0x, i0y, i1x, i1y, i2x, i2y);
  this._cx = center.x; this._cy = center.y;
  for (i = 0; i < n; i++) this._dists[i] = _voDist(coords[2 * i], coords[2 * i + 1], center.x, center.y);
  // sort the points by distance from the seed triangle circumcenter
  _voQuicksort(this._ids, this._dists, 0, n - 1);
  // set up the seed triangle as the starting hull
  this._hullStart = i0;
  var hullSize = 3;
  hullNext[i0] = hullPrev[i2] = i1;
  hullNext[i1] = hullPrev[i0] = i2;
  hullNext[i2] = hullPrev[i1] = i0;
  hullTri[i0] = 0; hullTri[i1] = 1; hullTri[i2] = 2;
  hullHash.fill(-1);
  hullHash[this._hashKey(i0x, i0y)] = i0;
  hullHash[this._hashKey(i1x, i1y)] = i1;
  hullHash[this._hashKey(i2x, i2y)] = i2;
  this.trianglesLen = 0;
  this._addTriangle(i0, i1, i2, -1, -1, -1);
  var xp = 0, yp = 0, start, key, e, q, t, nb, id;
  for (k = 0; k < this._ids.length; k++) {
    id = this._ids[k];
    x = coords[2 * id]; y = coords[2 * id + 1];
    // skip near-duplicate points
    if (k > 0 && Math.abs(x - xp) <= _VO_EPSILON && Math.abs(y - yp) <= _VO_EPSILON) continue;
    xp = x; yp = y;
    // skip seed triangle points
    if (id === i0 || id === i1 || id === i2) continue;
    // find a visible edge on the convex hull using edge hash
    start = 0;
    for (j = 0, key = this._hashKey(x, y); j < this._hashSize; j++) {
      start = hullHash[(key + j) % this._hashSize];
      if (start !== -1 && start !== hullNext[start]) break;
    }
    start = hullPrev[start];
    e = start;
    while (q = hullNext[e], _voOrient2d(x, y, coords[2 * e], coords[2 * e + 1], coords[2 * q], coords[2 * q + 1]) >= 0) {
      e = q;
      if (e === start) { e = -1; break; }
    }
    if (e === -1) continue;   // likely a near-duplicate point; skip it
    // add the first triangle from the point
    t = this._addTriangle(e, id, hullNext[e], -1, -1, hullTri[e]);
    // recursively flip triangles from the point until they satisfy the Delaunay condition
    hullTri[id] = this._legalize(t + 2);
    hullTri[e] = t;   // keep track of boundary triangles on the hull
    hullSize++;
    // walk forward through the hull, adding more triangles and flipping recursively
    nb = hullNext[e];
    while (q = hullNext[nb], _voOrient2d(x, y, coords[2 * nb], coords[2 * nb + 1], coords[2 * q], coords[2 * q + 1]) < 0) {
      t = this._addTriangle(nb, id, q, hullTri[id], -1, hullTri[nb]);
      hullTri[id] = this._legalize(t + 2);
      hullNext[nb] = nb;   // mark as removed
      hullSize--;
      nb = q;
    }
    // walk backward from the other side, adding more triangles and flipping
    if (e === start) {
      while (q = hullPrev[e], _voOrient2d(x, y, coords[2 * q], coords[2 * q + 1], coords[2 * e], coords[2 * e + 1]) < 0) {
        t = this._addTriangle(q, id, e, -1, hullTri[e], hullTri[q]);
        this._legalize(t + 2);
        hullTri[q] = t;
        hullNext[e] = e;   // mark as removed
        hullSize--;
        e = q;
      }
    }
    // update the hull indices
    this._hullStart = hullPrev[id] = e;
    hullNext[e] = hullPrev[nb] = id;
    hullNext[id] = nb;
    // save the two new edges in the hash table
    hullHash[this._hashKey(x, y)] = id;
    hullHash[this._hashKey(coords[2 * e], coords[2 * e + 1])] = e;
  }
  this.hull = new Uint32Array(hullSize);
  for (i = 0, e = this._hullStart; i < hullSize; i++) { this.hull[i] = e; e = hullNext[e]; }
  // trim typed triangle mesh arrays
  this.triangles = this._triangles.subarray(0, this.trianglesLen);
  this.halfedges = this._halfedges.subarray(0, this.trianglesLen);
};
_VoDelaunator.prototype._hashKey = function(x, y) { return Math.floor(_voPseudoAngle(x - this._cx, y - this._cy) * this._hashSize) % this._hashSize; };
_VoDelaunator.prototype._legalize = function(a) {
  var triangles = this._triangles, halfedges = this._halfedges, coords = this.coords;
  var i = 0, ar = 0, b, a0, b0, al, bl, p0, pr, pl, p1, illegal, hbl, e, br;
  // recursion eliminated with a fixed-size stack
  while (true) {
    b = halfedges[a];
    // if the pair of triangles doesn't satisfy the Delaunay condition (p1 is inside the circumcircle of [p0, pl, pr]), flip them,
    // then do the same check/flip recursively for the new pair of triangles
    a0 = a - a % 3;
    ar = a0 + (a + 2) % 3;
    if (b === -1) {   // convex hull edge
      if (i === 0) break;
      a = _VO_EDGE_STACK[--i];
      continue;
    }
    b0 = b - b % 3;
    al = a0 + (a + 1) % 3;
    bl = b0 + (b + 2) % 3;
    p0 = triangles[ar]; pr = triangles[a]; pl = triangles[al]; p1 = triangles[bl];
    illegal = _voInCircle(coords[2 * p0], coords[2 * p0 + 1], coords[2 * pr], coords[2 * pr + 1], coords[2 * pl], coords[2 * pl + 1], coords[2 * p1], coords[2 * p1 + 1]);
    if (illegal) {
      triangles[a] = p1;
      triangles[b] = p0;
      hbl = halfedges[bl];
      // edge swapped on the other side of the hull (rare); fix the half-edge reference
      if (hbl === -1) {
        e = this._hullStart;
        do {
          if (this._hullTri[e] === bl) { this._hullTri[e] = a; break; }
          e = this._hullPrev[e];
        } while (e !== this._hullStart);
      }
      this._link(a, hbl);
      this._link(b, halfedges[ar]);
      this._link(ar, bl);
      br = b0 + (b + 1) % 3;
      // don't worry about hitting the cap: it can only happen on extremely degenerate input
      if (i < _VO_EDGE_STACK.length) _VO_EDGE_STACK[i++] = br;
    } else {
      if (i === 0) break;
      a = _VO_EDGE_STACK[--i];
    }
  }
  return ar;
};
_VoDelaunator.prototype._link = function(a, b) {
  this._halfedges[a] = b;
  if (b !== -1) this._halfedges[b] = a;
};
_VoDelaunator.prototype._addTriangle = function(i0, i1, i2, a, b, c) {
  var t = this.trianglesLen;
  this._triangles[t] = i0; this._triangles[t + 1] = i1; this._triangles[t + 2] = i2;
  this._link(t, a); this._link(t + 1, b); this._link(t + 2, c);
  this.trianglesLen += 3;
  return t;
};

// ---- d3-delaunay 6.0.4: Delaunay
// A triangulation is collinear if all its triangles have a non-null area
function _voCollinear(d) {
  var triangles = d.triangles, coords = d.coords, i, a, b, c, cross;
  for (i = 0; i < triangles.length; i += 3) {
    a = 2 * triangles[i]; b = 2 * triangles[i + 1]; c = 2 * triangles[i + 2];
    cross = (coords[c] - coords[a]) * (coords[b + 1] - coords[a + 1]) - (coords[b] - coords[a]) * (coords[c + 1] - coords[a + 1]);
    if (cross > 1e-10) return false;
  }
  return true;
}
function _voJitter(x, y, r) { return [x + _voSin(x + y) * r, y + _voCos(x - y) * r]; }
// Delaunay: points is a Float64Array [x0, y0, ...] (the jitter of collinear input changes it in place, as in d3-delaunay).
function _VoDelaunay(points) {
  this._delaunator = new _VoDelaunator(points);
  this.inedges = new Int32Array(points.length / 2);
  this._hullIndex = new Int32Array(points.length / 2);
  this.points = this._delaunator.coords;
  this.collinear = null;
  this._init();
}
_VoDelaunay.prototype._init = function() {
  var d = this._delaunator, points = this.points, i, e, f, n, p;
  // check for collinear
  if (d.hull && d.hull.length > 2 && _voCollinear(d)) {
    n = points.length / 2;
    this.collinear = Int32Array.from({length: n}, function(_, k) { return k; })
      .sort(function(a, b) { return points[2 * a] - points[2 * b] || points[2 * a + 1] - points[2 * b + 1]; });   // for exact neighbors
    e = this.collinear[0]; f = this.collinear[this.collinear.length - 1];
    var bounds = [points[2 * e], points[2 * e + 1], points[2 * f], points[2 * f + 1]];
    var r = 1e-8 * _voHypot(bounds[3] - bounds[1], bounds[2] - bounds[0]);
    for (i = 0; i < n; ++i) {
      p = _voJitter(points[2 * i], points[2 * i + 1], r);
      points[2 * i] = p[0];
      points[2 * i + 1] = p[1];
    }
    this._delaunator = new _VoDelaunator(points);
  } else {
    this.collinear = null;
  }
  var halfedges = this.halfedges = this._delaunator.halfedges;
  var hull = this.hull = this._delaunator.hull;
  var triangles = this.triangles = this._delaunator.triangles;
  var inedges = this.inedges.fill(-1);
  var hullIndex = this._hullIndex.fill(-1);
  // Compute an index from each point to an (arbitrary) incoming halfedge. Used to give the first neighbor of each point; for this reason,
  // on the hull we give priority to exterior halfedges
  for (e = 0, n = halfedges.length; e < n; ++e) {
    p = triangles[e % 3 === 2 ? e - 2 : e + 1];
    if (halfedges[e] === -1 || inedges[p] === -1) inedges[p] = e;
  }
  for (i = 0, n = hull.length; i < n; ++i) hullIndex[hull[i]] = i;
  // degenerate case: 1 or 2 (distinct) points
  if (hull.length <= 2 && hull.length > 0) {
    this.triangles = new Int32Array(3).fill(-1);
    this.halfedges = new Int32Array(3).fill(-1);
    this.triangles[0] = hull[0];
    inedges[hull[0]] = 1;
    if (hull.length === 2) {
      inedges[hull[1]] = 0;
      this.triangles[1] = hull[1];
      this.triangles[2] = hull[1];
    }
  }
};
_VoDelaunay.prototype._step = function(i, x, y) {
  var inedges = this.inedges, hull = this.hull, hullIndex = this._hullIndex, halfedges = this.halfedges, triangles = this.triangles, points = this.points;
  if (inedges[i] === -1 || !points.length) return (i + 1) % (points.length >> 1);
  var c = i, dc = (x - points[i * 2]) * (x - points[i * 2]) + (y - points[i * 2 + 1]) * (y - points[i * 2 + 1]);
  var e0 = inedges[i], e = e0, t, dt;
  do {
    t = triangles[e];
    dt = (x - points[t * 2]) * (x - points[t * 2]) + (y - points[t * 2 + 1]) * (y - points[t * 2 + 1]);
    if (dt < dc) { dc = dt; c = t; }
    e = e % 3 === 2 ? e - 2 : e + 1;
    if (triangles[e] !== i) break;   // bad triangulation
    e = halfedges[e];
    if (e === -1) {
      e = hull[(hullIndex[i] + 1) % hull.length];
      if (e !== t) {
        if ((x - points[e * 2]) * (x - points[e * 2]) + (y - points[e * 2 + 1]) * (y - points[e * 2 + 1]) < dc) return e;
      }
      break;
    }
  } while (e !== e0);
  return c;
};

// ---- d3-delaunay 6.0.4: Voronoi
function _voAt(a, k) { return a[k]; }   // out of range reads give undefined, which arithmetic turns into NaN, as in the source
function _VoVoronoi(delaunay, b) {
  var xmin = b[0], ymin = b[1], xmax = b[2], ymax = b[3];
  if (!(xmax >= xmin) || !(ymax >= ymin)) throw new Error('invalid bounds');
  this.delaunay = delaunay;
  this.xmax = xmax; this.xmin = xmin;
  this.ymax = ymax; this.ymin = ymin;
  this._init();
}
_VoVoronoi.prototype._init = function() {
  var points = this.delaunay.points, hull = this.delaunay.hull, triangles = this.delaunay.triangles;
  var vectors = this.vectors = new Float64Array(points.length * 2);
  var bx, by;   // lazily computed barycenter of the hull
  // Compute circumcenters.
  var circumcenters = this.circumcenters = new Float64Array(triangles.length / 3 * 2);
  var i, j, n, x, y, t1, t2, t3, x1, y1, x2, y2, x3, y3, dx, dy, ex, ey, ab, a, d, bl, cl, h, k;
  for (i = 0, j = 0, n = triangles.length; i < n; i += 3, j += 2) {
    t1 = triangles[i] * 2; t2 = triangles[i + 1] * 2; t3 = triangles[i + 2] * 2;
    x1 = points[t1]; y1 = points[t1 + 1];
    x2 = points[t2]; y2 = points[t2 + 1];
    x3 = points[t3]; y3 = points[t3 + 1];
    dx = x2 - x1; dy = y2 - y1; ex = x3 - x1; ey = y3 - y1;
    ab = (dx * ey - dy * ex) * 2;
    if (Math.abs(ab) < 1e-9) {
      // For a degenerate triangle, the circumcenter is at the infinity, in a direction orthogonal to the halfedge and away from the "center" of
      // the diagram <bx, by>, defined as the hull's barycenter.
      if (bx === undefined) {
        bx = by = 0;
        for (k = 0; k < hull.length; k++) { bx += points[hull[k] * 2]; by += points[hull[k] * 2 + 1]; }
        bx /= hull.length; by /= hull.length;
      }
      a = 1e9 * Math.sign((bx - x1) * ey - (by - y1) * ex);
      x = (x1 + x3) / 2 - a * ey;
      y = (y1 + y3) / 2 + a * ex;
    } else {
      d = 1 / ab;
      bl = dx * dx + dy * dy;
      cl = ex * ex + ey * ey;
      x = x1 + (ey * bl - dy * cl) * d;
      y = y1 + (dx * cl - ex * bl) * d;
    }
    circumcenters[j] = x;
    circumcenters[j + 1] = y;
  }
  // Compute exterior cell rays.
  h = hull[hull.length - 1];
  var p0, p1 = h * 4, x0, y0;
  x1 = points[2 * h]; y1 = points[2 * h + 1];
  vectors.fill(0);
  for (i = 0; i < hull.length; ++i) {
    h = hull[i];
    p0 = p1; x0 = x1; y0 = y1;
    p1 = h * 4; x1 = points[2 * h]; y1 = points[2 * h + 1];
    vectors[p0 + 2] = vectors[p1] = y0 - y1;
    vectors[p0 + 3] = vectors[p1 + 1] = x1 - x0;
  }
};
_VoVoronoi.prototype.contains = function(i, x, y) {
  if (x !== x || y !== y) return false;
  return this.delaunay._step(i, x, y) === i;
};
// cellPolygon(i): renderCell into a Polygon (moveTo, lineTo without repeats, closePath), as an array of [x, y], or null.
_VoVoronoi.prototype.cellPolygon = function(i) {
  var points = this._clip(i);
  if (points === null || !points.length) return null;
  var polygon = [[points[0], points[1]]], n = points.length, k;
  while (points[0] === points[n - 2] && points[1] === points[n - 1] && n > 1) n -= 2;
  for (k = 2; k < n; k += 2) {
    if (points[k] !== points[k - 2] || points[k + 1] !== points[k - 1]) polygon.push([points[k], points[k + 1]]);
  }
  polygon.push(polygon[0].slice());
  return polygon;
};
_VoVoronoi.prototype._cell = function(i) {
  var circumcenters = this.circumcenters, inedges = this.delaunay.inedges, halfedges = this.delaunay.halfedges, triangles = this.delaunay.triangles;
  var e0 = inedges[i];
  if (e0 === -1) return null;   // coincident point
  var points = [], e = e0, t;
  do {
    t = Math.floor(e / 3);
    points.push(circumcenters[t * 2], circumcenters[t * 2 + 1]);
    e = e % 3 === 2 ? e - 2 : e + 1;
    if (triangles[e] !== i) break;   // bad triangulation
    e = halfedges[e];
  } while (e !== e0 && e !== -1);
  return points;
};
_VoVoronoi.prototype._clip = function(i) {
  // degenerate case (1 valid point: return the box)
  if (i === 0 && this.delaunay.hull.length === 1) return [this.xmax, this.ymin, this.xmax, this.ymax, this.xmin, this.ymax, this.xmin, this.ymin];
  var points = this._cell(i);
  if (points === null) return null;
  var V = this.vectors, v = i * 4;
  return this._simplify(V[v] || V[v + 1] ? this._clipInfinite(i, points, V[v], V[v + 1], V[v + 2], V[v + 3]) : this._clipFinite(i, points));
};
_VoVoronoi.prototype._clipFinite = function(i, points) {
  var n = points.length, P = null, x0, y0, x1 = points[n - 2], y1 = points[n - 1], c0, c1 = this._regioncode(x1, y1), e0, e1 = 0, j, S, sx0, sy0, sx1, sy1;
  for (j = 0; j < n; j += 2) {
    x0 = x1; y0 = y1; x1 = points[j]; y1 = points[j + 1];
    c0 = c1; c1 = this._regioncode(x1, y1);
    if (c0 === 0 && c1 === 0) {
      e0 = e1; e1 = 0;
      if (P) P.push(x1, y1);
      else P = [x1, y1];
    } else {
      if (c0 === 0) {
        if ((S = this._clipSegment(x0, y0, x1, y1, c0, c1)) === null) continue;
        sx0 = S[0]; sy0 = S[1]; sx1 = S[2]; sy1 = S[3];
      } else {
        if ((S = this._clipSegment(x1, y1, x0, y0, c1, c0)) === null) continue;
        sx1 = S[0]; sy1 = S[1]; sx0 = S[2]; sy0 = S[3];
        e0 = e1; e1 = this._edgecode(sx0, sy0);
        if (e0 && e1) this._edge(i, e0, e1, P, P.length);
        if (P) P.push(sx0, sy0);
        else P = [sx0, sy0];
      }
      e0 = e1; e1 = this._edgecode(sx1, sy1);
      if (e0 && e1) this._edge(i, e0, e1, P, P.length);
      if (P) P.push(sx1, sy1);
      else P = [sx1, sy1];
    }
  }
  if (P) {
    e0 = e1; e1 = this._edgecode(P[0], P[1]);
    if (e0 && e1) this._edge(i, e0, e1, P, P.length);
  } else if (this.contains(i, (this.xmin + this.xmax) / 2, (this.ymin + this.ymax) / 2)) {
    return [this.xmax, this.ymin, this.xmax, this.ymax, this.xmin, this.ymax, this.xmin, this.ymin];
  }
  return P;
};
_VoVoronoi.prototype._clipSegment = function(x0, y0, x1, y1, c0, c1) {
  // for more robustness, always consider the segment in the same order
  var flip = c0 < c1, tmp, x, y, c;
  if (flip) { tmp = [x1, y1, x0, y0, c1, c0]; x0 = tmp[0]; y0 = tmp[1]; x1 = tmp[2]; y1 = tmp[3]; c0 = tmp[4]; c1 = tmp[5]; }
  while (true) {
    if (c0 === 0 && c1 === 0) return flip ? [x1, y1, x0, y0] : [x0, y0, x1, y1];
    if (c0 & c1) return null;
    c = c0 || c1;
    if (c & 8) { x = x0 + (x1 - x0) * (this.ymax - y0) / (y1 - y0); y = this.ymax; }
    else if (c & 4) { x = x0 + (x1 - x0) * (this.ymin - y0) / (y1 - y0); y = this.ymin; }
    else if (c & 2) { y = y0 + (y1 - y0) * (this.xmax - x0) / (x1 - x0); x = this.xmax; }
    else { y = y0 + (y1 - y0) * (this.xmin - x0) / (x1 - x0); x = this.xmin; }
    if (c0) { x0 = x; y0 = y; c0 = this._regioncode(x0, y0); }
    else { x1 = x; y1 = y; c1 = this._regioncode(x1, y1); }
  }
};
_VoVoronoi.prototype._clipInfinite = function(i, points, vx0, vy0, vxn, vyn) {
  var P = Array.prototype.slice.call(points), p, j, n, c0, c1;
  if (p = this._project(P[0], P[1], vx0, vy0)) P.unshift(p[0], p[1]);
  if (p = this._project(P[P.length - 2], P[P.length - 1], vxn, vyn)) P.push(p[0], p[1]);
  if (P = this._clipFinite(i, P)) {
    for (j = 0, n = P.length, c1 = this._edgecode(P[n - 2], P[n - 1]); j < n; j += 2) {
      c0 = c1; c1 = this._edgecode(P[j], P[j + 1]);
      if (c0 && c1) { j = this._edge(i, c0, c1, P, j); n = P.length; }
    }
  } else if (this.contains(i, (this.xmin + this.xmax) / 2, (this.ymin + this.ymax) / 2)) {
    P = [this.xmin, this.ymin, this.xmax, this.ymin, this.xmax, this.ymax, this.xmin, this.ymax];
  }
  return P;
};
_VoVoronoi.prototype._edge = function(i, e0, e1, P, j) {
  var x, y;
  while (e0 !== e1) {
    x = undefined; y = undefined;
    switch (e0) {
      case 5: e0 = 4; continue;   // top-left
      case 4: e0 = 6; x = this.xmax; y = this.ymin; break;   // top
      case 6: e0 = 2; continue;   // top-right
      case 2: e0 = 10; x = this.xmax; y = this.ymax; break;   // right
      case 10: e0 = 8; continue;   // bottom-right
      case 8: e0 = 9; x = this.xmin; y = this.ymax; break;   // bottom
      case 9: e0 = 1; continue;   // bottom-left
      case 1: e0 = 5; x = this.xmin; y = this.ymin; break;   // left
    }
    // Note: this implicitly checks for out of bounds: if P[j] or P[j+1] are undefined, the conditional statement will be executed.
    if ((P[j] !== x || P[j + 1] !== y) && this.contains(i, x, y)) {
      P.splice(j, 0, x, y); j += 2;
    }
  }
  return j;
};
_VoVoronoi.prototype._project = function(x0, y0, vx, vy) {
  var t = Infinity, c, x, y;
  if (vy < 0) {   // top
    if (y0 <= this.ymin) return null;
    if ((c = (this.ymin - y0) / vy) < t) { y = this.ymin; t = c; x = x0 + t * vx; }
  } else if (vy > 0) {   // bottom
    if (y0 >= this.ymax) return null;
    if ((c = (this.ymax - y0) / vy) < t) { y = this.ymax; t = c; x = x0 + t * vx; }
  }
  if (vx > 0) {   // right
    if (x0 >= this.xmax) return null;
    if ((c = (this.xmax - x0) / vx) < t) { x = this.xmax; t = c; y = y0 + t * vy; }
  } else if (vx < 0) {   // left
    if (x0 <= this.xmin) return null;
    if ((c = (this.xmin - x0) / vx) < t) { x = this.xmin; t = c; y = y0 + t * vy; }
  }
  return [x, y];
};
_VoVoronoi.prototype._edgecode = function(x, y) {
  return (x === this.xmin ? 1 : x === this.xmax ? 2 : 0) | (y === this.ymin ? 4 : y === this.ymax ? 8 : 0);
};
_VoVoronoi.prototype._regioncode = function(x, y) {
  return (x < this.xmin ? 1 : x > this.xmax ? 2 : 0) | (y < this.ymin ? 4 : y > this.ymax ? 8 : 0);
};
_VoVoronoi.prototype._simplify = function(P) {
  var i, j, k;
  if (P && P.length > 4) {
    for (i = 0; i < P.length; i += 2) {
      j = (i + 2) % P.length; k = (i + 4) % P.length;
      if (P[i] === P[j] && P[j] === P[k] || P[i + 1] === P[j + 1] && P[j + 1] === P[k + 1]) { P.splice(j, 2); i -= 2; }
    }
    if (!P.length) P = null;
  }
  return P;
};
// Delaunator on a flat coordinate array: the raw triangles, halfedges and hull.
function _voDelaunator(coords) {
  var d = new _VoDelaunator(Float64Array.from(coords));
  return {triangles: Array.from(d.triangles), halfedges: Array.from(d.halfedges), hull: Array.from(d.hull)};
}
// Delaunay.from(points).voronoi(bounds) and every cellPolygon: points is [[x, y], ...]. Returns the (jittered) points, triangles, halfedges, hull and cells.
function _voVoronoi(points, bounds) {
  var flat = new Float64Array(points.length * 2), i;
  for (i = 0; i < points.length; i++) { flat[2 * i] = points[i][0]; flat[2 * i + 1] = points[i][1]; }
  var dl = new _VoDelaunay(flat), v = new _VoVoronoi(dl, bounds), cells = [];
  for (i = 0; i < points.length; i++) cells.push(v.cellPolygon(i));
  return {points: Array.from(dl.points), triangles: Array.from(dl.triangles), halfedges: Array.from(dl.halfedges), hull: Array.from(dl.hull), cells: cells};
}


// ---- the voronoi atom (twin of _render_voronoi in renderers/web_article.py; see the comment there for the label rule)
var _VO_W = 600, _VO_MAXN = 200, _VO_MINH = 200, _VO_MAXH = 600, _VO_LY = 21, _VO_MAXWM = 820, _VO_YGAP = 16;
// A label or group: text, or a finite number as JavaScript prints it; anything else (an array, an object, a boolean, null) is no text.
function _voText(v, mx) {
  if (typeof v === 'string') return v.slice(0, mx);
  if (typeof v === 'number' && isFinite(v)) return String(v).slice(0, mx);
  return '';
}
// Shoelace area of a closed polygon (first point repeated at the end), from coordinates relative to (ox, oy).
function _voArea(poly, ox, oy) {
  var s = 0, i;
  for (i = 0; i < poly.length - 1; i++) s += (poly[i][0] - ox) * (poly[i + 1][1] - oy) - (poly[i + 1][0] - ox) * (poly[i][1] - oy);
  return Math.abs(s) / 2;
}
// The distance from (px, py) to the nearest edge of the closed ring [[x, y], ...].
function _voInscribed(px, py, ring) {
  var best = Infinity, k, ax, ay, bx, by, dx, dy, l2, t, ex, ey, d;
  for (k = 0; k < ring.length - 1; k++) {
    ax = ring[k][0]; ay = ring[k][1]; bx = ring[k + 1][0]; by = ring[k + 1][1];
    dx = bx - ax; dy = by - ay; l2 = dx * dx + dy * dy;
    if (l2 === 0) continue;
    t = Math.min(1, Math.max(0, ((px - ax) * dx + (py - ay) * dy) / l2));
    ex = ax + t * dx - px; ey = ay + t * dy - py;
    d = Math.sqrt(ex * ex + ey * ey);
    if (d < best) best = d;
  }
  return best;
}
_RENDERERS['voronoi'] = function(b) {
  // the optional 'version' field is read by _hgVersionNote at the end
  var notes = '';
  function plural(c, one, many) { return c + ' ' + (c === 1 ? one : many); }
  function fail(msg) { return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">' + msg + '</div>' + notes + _hgVersionNote(b, 'voronoi')); }
  var raw = b.sites;
  if (!Array.isArray(raw)) return fail('A Voronoi diagram needs a list of sites, each with a numeric x and y.');
  var lst = raw.slice(0, _VO_MAXN), beyond = raw.length - _VO_MAXN;
  if (beyond > 0) notes += _hgNote(plural(beyond, 'site', 'sites') + ' beyond the first ' + _VO_MAXN + ' ' + (beyond === 1 ? 'was' : 'were') + ' not used.');
  var sites = [], seen = {}, bad = 0, merged = 0, i, e, x, y, key, isObj;
  for (i = 0; i < lst.length; i++) {
    e = lst[i];
    isObj = e !== null && typeof e === 'object' && !Array.isArray(e);
    x = isObj ? e.x : undefined; y = isObj ? e.y : undefined;
    if (!(_cnUsable(x) && _cnUsable(y))) { bad++; continue; }
    key = x + ',' + y;
    if (Object.prototype.hasOwnProperty.call(seen, key)) { merged++; continue; }
    seen[key] = sites.length;
    sites.push({x: x, y: y, l: _voText(e.label, 24), g: _voText(e.group, 20), v: _cnUsable(e.value) ? e.value : null});
  }
  if (bad) notes += _hgNote(plural(bad, 'entry', 'entries') + ' ' + (bad === 1 ? 'was' : 'were') + ' not a site with a finite numeric x and y and ' + (bad === 1 ? 'was' : 'were') + ' left out.');
  if (merged) notes += _hgNote(plural(merged, 'site', 'sites') + ' shared a position with an earlier site and ' + (merged === 1 ? 'was' : 'were') + ' merged into it.');
  var n = sites.length;
  if (n < 3) return fail('A Voronoi diagram needs at least 3 sites at different positions; this list has ' + n + '.');
  var unit = _voText(b.unit, 12), us = unit ? ' ' + unit : '', xl = _voText(b.x_label, 30), yl = _voText(b.y_label, 30);
  function axis(lo, hi) {
    if (lo === hi) { lo = lo - 1; hi = hi + 1; }
    var m = (hi - lo) * 0.05;
    return _hgNice(lo - m, hi + m, 6);
  }
  var xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
  sites.forEach(function(s) { if (s.x < xmin) xmin = s.x; if (s.x > xmax) xmax = s.x; if (s.y < ymin) ymin = s.y; if (s.y > ymax) ymax = s.y; });
  var ax = axis(xmin, xmax), ay = axis(ymin, ymax), X0 = ax[0], X1 = ax[1], Y0 = ay[0], Y1 = ay[1];
  if (!(X1 > X0 && Y1 > Y0)) return fail('These sites are too close together, or too large, to draw.');
  var cells;
  try {
    cells = _voVoronoi(sites.map(function(s) { return [s.x, s.y]; }), [X0, Y0, X1, Y1]).cells;
  } catch (err) {
    return fail('The regions could not be worked out for these sites.');
  }
  var W = _VO_W, hraw = W * (Y1 - Y0) / (X1 - X0), H = Math.floor(Math.min(_VO_MAXH, Math.max(_VO_MINH, hraw)) + 0.5);
  if (Math.abs(H - hraw) > 1) notes += _hgNote('The x and y scales differ in this drawing (its height is kept between a third of its width and its width), so distances look stretched; the regions are worked out from the x and y values.');
  var groups = [];
  sites.forEach(function(s) { if (s.g && groups.indexOf(s.g) < 0) groups.push(s.g); });
  sites.forEach(function(s) { s.c = s.g ? _SB_PALETTE[groups.indexOf(s.g) % 8] : (groups.length ? _AD_NONE : _SB_PALETTE[4]); });
  var total = (X1 - X0) * (Y1 - Y0), areas = cells.map(function(c) { return c ? _voArea(c, X0, Y0) / total : 0; }), best = 0, nocell = 0;
  for (i = 0; i < n; i++) { if (areas[i] > areas[best]) best = i; if (!cells[i]) nocell++; }
  if (nocell) notes += _hgNote(plural(nocell, 'site is', 'sites are') + ' too close to another site to have a region of its own.');
  function name(k) { return sites[k].l || ('Site ' + (k + 1)); }
  function val(s) { return s.v !== null ? _bpFmt(s.v, 2) + us : ''; }
  var ex = _hgTicks(X0, X1, 6), ey = _hgTicks(Y0, Y1, 6);
  var dxs = ex.length ? _hgDecimals(ex) : 0, dys = ey.length ? _hgDecimals(ey) : 0;
  var xlab = ex.map(function(v) { return _hgNum(v, dxs); }), ylab = ey.map(function(v) { return _hgNum(v, dys); });
  var ml = Math.max(54, Math.ceil(Math.max.apply(null, [0].concat(ylab.map(function(t) { return t.length; }))) * 7.2) + 14);
  var mr = Math.max(30, Math.ceil(Math.max.apply(null, [0].concat(xlab.map(function(t) { return t.length; }))) * 7.2 / 2) + 8), padx = ml + mr;
  var cellsvg = '', labs = '', wms = [], s, cx, cy, tip, path, ring, wt, hw, d, wm;
  for (i = 0; i < n; i++) {
    s = sites[i];
    cx = (s.x - X0) * W / (X1 - X0); cy = (Y1 - s.y) * H / (Y1 - Y0);
    tip = name(i) + (s.g ? ' (' + s.g + ')' : '') + ': ';
    path = '';
    if (cells[i]) {
      ring = cells[i].map(function(p) { return [(p[0] - X0) * W / (X1 - X0), (Y1 - p[1]) * H / (Y1 - Y0)]; });
      path = '<path class="voc" d="M' + ring.slice(0, ring.length - 1).map(function(p) { return _cnR(p[0]) + ',' + _cnR(p[1]); }).join('L') + 'Z" fill="' + s.c + '" fill-opacity="0.22" style="stroke:var(--text,#0F172A);" ' +
        'stroke-opacity="0.55" stroke-width="1" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>';
      tip += (s.v !== null ? val(s) + ', ' : '') + (areas[i] * 100).toFixed(1) + '% of the area';
      if (s.l) {
        wt = s.l.length * 7.2 + 8; hw = wt / 2;
        d = _voInscribed(cx, cy, ring);
        wm = d > 0 ? _cpQ(Math.sqrt(hw * hw + _VO_LY * _VO_LY) * W / d + padx) : 1e9;
        if (wm <= _VO_MAXWM) {
          wm = wm > _CP_MINW ? wm : 0;
          wms.push(wm);
          labs += '<div data-cb="label" data-key="' + _esc(name(i)) + '" class="vol' + (wm ? ' tmw' + wm : '') + '" style="position:absolute;left:' + _tmPct(cx, W) + ';top:' + _tmPct(cy, H) +
            ';transform:translate(-50%,7px);white-space:nowrap;font-size:12px;line-height:14px;color:var(--text,#0F172A);pointer-events:none;' + _ifK(i, n) + 'opacity:var(--k,1);">' + _esc(s.l) + '</div>';
        }
      }
    } else {
      tip += 'no region of its own';
    }
    cellsvg += '<g class="vog" data-cb="node" data-key="' + _esc(name(i)) + '" style="' + _ifK(i, n) + 'opacity:var(--k,1);">' + path + '<path class="vod" d="M' + _cnR(cx) + ',' + _cnR(cy) + 'h0" fill="none" stroke-linecap="round" stroke-width="9" vector-effect="non-scaling-stroke" style="stroke:var(--surface,#F8FAFC);"/>' +
      '<path class="vod" d="M' + _cnR(cx) + ',' + _cnR(cy) + 'h0" fill="none" stroke-linecap="round" stroke-width="6" vector-effect="non-scaling-stroke" stroke="' + s.c + '"/><title>' + _esc(tip) + '</title></g>';
  }
  var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" style="display:block;height:auto;overflow:hidden;" aria-hidden="true" focusable="false">' +
    '<rect x="0" y="0" width="' + W + '" height="' + H + '" style="fill:var(--surface,#F8FAFC);"/>' + cellsvg +
    '<rect x="0" y="0" width="' + W + '" height="' + H + '" fill="none" style="stroke:var(--border,#CBD5E1);" stroke-width="1" vector-effect="non-scaling-stroke"/></svg>';
  var xaxis = ex.length ? _hgAxis(ex, X0, X1 - X0, xlab) : '', yaxis = '', k, wy;
  ey.forEach(function(v, i) {
    k = i === 0 ? 0 : Math.min(31 - Math.clz32(i & -i), 3);
    wy = (i === 0 || ey.length < 2) ? 0 : _cpQ(padx + _VO_YGAP * (ey.length - 1) * W / (Math.pow(2, k) * H));
    wy = wy > _CP_MINW ? wy : 0;
    wms.push(wy);
    yaxis += '<div class="voy' + (wy ? ' tmw' + wy : '') + '" style="position:absolute;right:100%;margin-right:6px;top:' + _tmPct(Y1 - v, Y1 - Y0) +
      ';transform:translateY(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + ylab[i] + '</div>';
  });
  var aria = 'Nearest-site regions of ' + plural(n, 'site', 'sites') + (groups.length ? ' in ' + plural(groups.length, 'group', 'groups') : '') + '. Largest region: ' + name(best) + ', ' + (areas[best] * 100).toFixed(1) + '% of the area.';
  var gates = [];
  wms.forEach(function(w) { if (w && gates.indexOf(w) < 0) gates.push(w); });
  gates.sort(function(a, c) { return a - c; });
  var css = '<style>@container (max-width:560px){.ifvo .hgx:not(.hgc){display:none}}' + gates.map(function(w) { return '@container (width<' + w + 'px){.tmw' + w + '{display:none}}'; }).join('') + '</style>';
  var chart = '<div class="ifvo" style="container-type:inline-size;max-width:' + _VO_MAXWM + 'px;overflow:hidden;">' + css +
    (yl ? '<div style="font-size:0.75rem;color:var(--muted,#475569);margin:0 0 2px 0;">' + _esc(yl) + '</div>' : '') +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;margin:8px ' + mr + 'px 34px ' + ml + 'px;">' + svg + yaxis + xaxis + labs + '</div>' +
    (xl ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 ' + mr + 'px 0 ' + ml + 'px;">' + _esc(xl) + '</div>' : '') + '</div>';
  var legend = '';
  if (groups.length) {
    var ent = groups.map(function(g, j) { return [g, _SB_PALETTE[j % 8]]; });
    if (sites.some(function(t) { return !t.g; })) ent.push(['No group', _AD_NONE]);
    legend = '<div class="voleg" style="display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:12px;line-height:16px;color:var(--text,#0F172A);">' +
      ent.map(function(t) { return '<span style="display:inline-flex;align-items:center;gap:5px;"><span style="display:inline-block;width:12px;height:12px;box-sizing:border-box;border:2px solid ' + t[1] + ';background:' + t[1] + '38;"></span>' + _esc(t[0]) + '</span>'; }).join('') + '</div>';
  }
  var rows = sites.map(function(t, k) { return [name(k), String(t.x), String(t.y), t.g || 'No group', t.v !== null ? val(t) : '—', (areas[k] * 100).toFixed(1) + '%']; });
  return _ifWrap(_ifTitle(b) + chart + legend +
    _hgNote('Each region is the part of the area that is nearer to its site than to any other (straight-line distance in the x and y units). In a narrow container some names are hidden; the table lists every site and its share of the area.') +
    notes + _hgVersionNote(b, 'voronoi') + _ifTable(['Site', 'x', 'y', 'Group', 'Value', 'Share of the area'], rows));
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
    ribs[s] += '<path class="chd" data-key="' + _esc(_ifS(names[s], 20) + '→' + _ifS(names[t], 20)) + '" d="' + _chRibbon(rw, _CH_RR, _CH_RPAD, directed, 3) + '" fill="' + col[s] + '" fill-opacity="0.55" stroke="' + col[s] + '" stroke-width="0.6"><title>' + title + '</title></path>';
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
    arcs += '<g class="chg" data-cb="arc" data-key="' + _esc(nm) + '" style="' + kk + 'opacity:var(--k,1);"><path class="cha" d="' + _sbArc(g[1], g[2], _CH_IN, _CH_OUT, 0, null, 3) + '" fill="' + col[q] + '"><title>' + nm + ': sends ' + _esc(f(outT[q])) + ', receives ' + _esc(f(inT[q])) + '</title></path></g>';
    var wm = need[q];
    if (wm > _CH_MAXW) return;
    var cl = _sbCls(wm), th = (g[1] + g[2]) / 2, x = _CH_LAB * Math.sin(th), y = -_CH_LAB * Math.cos(th), right = Math.sin(th) >= 0;
    ws.push(cl[1]);
    var deg = right ? th * 180 / Math.PI - 90 : th * 180 / Math.PI - 270, ty = 'top:' + _tmPct(_CH_BOX / 2 + y, _CH_BOX) + ';';
    var anchor = right ? 'left:' + _tmPct(_CH_BOX / 2 + x, _CH_BOX) + ';' + ty + 'transform-origin:0 7px;' : 'right:' + _tmPct(_CH_BOX / 2 - x, _CH_BOX) + ';' + ty + 'transform-origin:100% 7px;';
    labels += '<div data-cb="label" data-key="' + _esc(nm) + '" class="chl' + cl[0] + '" style="position:absolute;' + anchor + 'margin-top:-7px;transform:rotate(' + deg.toFixed(2).replace(/^-0\.00$/, '0.00') + 'deg);width:max-content;max-width:calc(' +
      _tmPct(_CH_BOX / 2 - _CH_LAB, _CH_BOX).slice(0, -1) + 'cqw - 4px);overflow:hidden;white-space:nowrap;text-overflow:ellipsis;text-align:' + (right ? 'left' : 'right') +
      ';font-size:12px;line-height:14px;font-weight:600;color:' + col[q] + ';pointer-events:none;' + kk + 'opacity:var(--k,1);">' + nm + '</div>';
  });
  var aria = (directed ? 'Directed chord diagram' : 'Chord diagram') + ' of ' + n + ' groups, total flow ' + f(total) + '. Largest flow: ' + names[best[0]] + ' to ' + names[best[1]] + ', ' + f(mat[best[0]][best[1]]) + '.';
  var svg = '<svg viewBox="-300 -300 600 600" width="100%" height="100%" style="display:block;" aria-hidden="true" focusable="false">' +
    ribs.map(function(rs, q) { return '<g class="chk" data-cb="ribbon" data-key="' + _esc(names[q]) + '" style="' + _ifK(q, n) + 'opacity:var(--k,1);">' + rs + '</g>'; }).join('') + arcs + '</svg>';
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
// Three-set venn: a fixed symmetric layout (circles of radius W/3 whose centres are W/3 apart, so the triple overlap is a Reuleaux triangle),
// NOT area-proportional and with no venn.js. Text boxes sit at fixed fractions of the box width, tuned so each lies wholly inside its region
// at 290px and up. Twin of _render_venn_diagram3 in renderers/web_article.py.
var _VD_REGIONS = [  // key, field, max lines (items + the "+n more" line), centre x/y and width in % of the box: narrow tier, then wide tier (container >= 480px)
  ['a', 'set_a_exclusive', 5, [22, 21.5, 19], [18.5, 27, 27.5]], ['b', 'set_b_exclusive', 5, [78, 21.5, 19], [81.5, 27, 27.5]], ['c', 'set_c_exclusive', 5, [50, 83.5, 26], [50, 77.5, 40]],
  ['ab', 'intersection', 3, [50, 22, 16.5], [50, 25, 26]], ['ac', 'intersection_ac', 3, [29, 58.5, 14.5], [29, 61, 21]], ['bc', 'intersection_bc', 3, [71, 58.5, 14.5], [71, 61, 21]],
  ['abc', 'intersection_abc', 4, [50, 43, 19.5], [50, 40, 27.5]]];
var _VD_COL = ['var(--accent,#2563EB)', '#C2410C', '#15803D'], _VD_MAXREAD = 60;
function _vdTrim(x) { return x.length <= 28 ? x : x.slice(0, 27).replace(/\s+$/, '') + '\u2026'; }
function _vdCut(x) { return _esc(_vdTrim(x)); }
function _vdRaw(v, mx) { return String(v === undefined || v === null ? '' : v).slice(0, mx); }
function _vdUsable(v) { return typeof v === 'string' ? /[^ \t\n\r]/.test(v) : (typeof v === 'number' && isFinite(v)); }
function _vdCss() {
  var pos = function(t) { return 'left:' + t[0] + '%;top:' + t[1] + '%;width:' + t[2] + '%;'; };
  return '<style>' + _VD_REGIONS.map(function(r) { return '.v3t.v3' + r[0] + '{' + pos(r[3]) + '}'; }).join('') + '@container (width>=480px){' + _VD_REGIONS.map(function(r) { return '.v3t.v3' + r[0] + '{' + pos(r[4]) + '}'; }).join('') + '}</style>';
}
function _vdRender3(b) {
  var names = [_vdTrim(_vdRaw(b.set_a_name, 60)) || 'Set A', _vdTrim(_vdRaw(b.set_b_name, 60)) || 'Set B', _vdTrim(_vdRaw(b.set_c_name, 60)) || 'Set C'];
  var labels = ['Only ' + names[0], 'Only ' + names[1], 'Only ' + names[2], names[0] + ' and ' + names[1] + ' only', names[0] + ' and ' + names[2] + ' only', names[1] + ' and ' + names[2] + ' only', 'All three sets'];
  var items = [], bad = 0, extra = 0;
  _VD_REGIONS.forEach(function(r) {
    var src = Array.isArray(b[r[1]]) ? b[r[1]] : [], ok = src.filter(_vdUsable);
    bad += src.length - ok.length;
    extra += Math.max(0, ok.length - _VD_MAXREAD);
    items.push(ok.slice(0, _VD_MAXREAD).map(function(x) { return _vdRaw(x, 60); }));
  });
  var swatch = function(i) { return '<span style="flex:0 0 auto;width:10px;height:10px;border-radius:50%;border:2px solid ' + _VD_COL[i] + ';background:' + _VD_COL[i] + ';opacity:0.6;box-sizing:border-box;"></span>'; };
  var nm = function(i, xs) { return '<div style="display:flex;align-items:center;gap:6px;min-width:0;font-weight:700;font-size:13px;line-height:16px;' + xs + '">' + swatch(i) + '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + _ifS(names[i], 28) + '</span></div>'; };
  var circ = [['0', '0'], ['33.333', '0'], ['16.667', '30.218']].map(function(p, i) {
    return '<div class="v3o" data-cb="node" data-key="' + _esc(names[i]) + '" style="position:absolute;left:' + p[0] + '%;top:' + p[1] + '%;width:66.667%;aspect-ratio:1;box-sizing:border-box;border-radius:50%;border:2px solid ' + _VD_COL[i] + ';opacity:var(--k,1);' + _ifK(i, 10) +
      '"><div style="position:absolute;inset:0;border-radius:50%;background:' + _VD_COL[i] + ';opacity:0.16;"></div></div>';
  }).join('');
  var boxes = '';
  _VD_REGIONS.forEach(function(r, i) {
    var its = items[i], lim = r[2], shown = its.length <= lim ? its : its.slice(0, lim - 1);
    var lines = shown.map(function(x) { return '<div class="v3i" style="overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">• ' + _vdCut(x) + '</div>'; }).join('');
    if (its.length > lim) lines += '<div class="v3i" style="overflow:hidden;white-space:nowrap;text-overflow:ellipsis;font-style:italic;color:var(--muted,#475569);">+' + (its.length - shown.length) + ' more</div>';
    if (lines) boxes += '<div class="v3t v3' + r[0] + '" data-cb="label" data-key="' + _esc(labels[i]) + '" data-r="' + r[0] + '" style="position:absolute;transform:translate(-50%,-50%);text-align:center;font-size:12px;line-height:14px;opacity:var(--k,1);' + _ifK(3 + i, 10) + '">' + lines + '</div>';
  });
  var aria = 'Venn diagram of three sets: ' + names[0] + ', ' + names[1] + ' and ' + names[2] + '. ' + labels.map(function(l, i) { return l + ': ' + items[i].length + (items[i].length === 1 ? ' item. ' : ' items. '); }).join('').replace(/\s+$/, '') + ' The circles are not drawn to scale. Every item is in the table.';
  var rows = labels.map(function(l, i) { return '<tr><th scope="row">' + _ifS(l, 90) + '</th><td>' + (items[i].length ? items[i].map(function(x) { return _ifS(x, 60); }).join('; ') : 'none') + '</td></tr>'; }).join('');
  var note = (bad ? _hgNote(bad + (bad === 1 ? ' entry was' : ' entries were') + ' not text or a number and ' + (bad === 1 ? 'was' : 'were') + ' skipped.') : '') +
    (extra ? _hgNote(extra + (extra === 1 ? ' entry' : ' entries') + ' beyond the first ' + _VD_MAXREAD + ' in a region ' + (extra === 1 ? 'was' : 'were') + ' left out.') : '');
  return _ifWrap(_ifTitle(b) + '<div role="img" aria-label="' + _ifS(aria, 900) + '" style="max-width:640px;margin:0 auto;container-type:inline-size;font-size:12px;">' + _vdCss() +
    '<div style="display:flex;justify-content:space-between;gap:12px;margin-bottom:6px;"><div style="flex:1 1 0;min-width:0;display:flex;">' + nm(0, 'min-width:0;max-width:100%;') + '</div><div style="flex:1 1 0;min-width:0;display:flex;justify-content:flex-end;">' + nm(1, 'min-width:0;max-width:100%;') + '</div></div>' +
    '<div style="position:relative;width:100%;aspect-ratio:1/0.955342;">' + circ + boxes + '</div>' +
    '<div style="display:flex;justify-content:center;margin-top:6px;">' + nm(2, 'min-width:0;max-width:100%;') + '</div></div>' +
    _hgNote('Three fixed circles, not drawn to scale: a region\'s size says nothing about how many items it holds. Long item names are cut in the picture; the table has them in full.') +
    note + _hgVersionNote(b, 'venn_diagram') +
    '<table style="' + _IF_SR + '"><thead><tr><th scope="col">Region</th><th scope="col">Items</th></tr></thead><tbody>' + rows + '</tbody></table>');
}
_RENDERERS['venn_diagram'] = function(b) {
  if (b.set_c_name) return _vdRender3(b);
  var list = function(v) { return _ifArr(v, 4).map(function(i) { return '<div>• ' + _ifS(i, 28) + '</div>'; }).join(''); }, c = 'position:absolute;top:34px;width:56%;aspect-ratio:1;border-radius:50%;border:' + _IF_BORDER + ';opacity:calc(0.55 + 0.45*var(--k,1));';
  return _ifWrap(_ifTitle(b) + '<div style="position:relative;max-width:640px;margin:0 auto;aspect-ratio:1.5;font-size:0.82rem;">' +
    '<div style="position:absolute;left:4%;top:0;font-weight:700;">' + _ifS(b.set_a_name, 28) + '</div><div style="position:absolute;right:4%;top:0;font-weight:700;text-align:right;">' + _ifS(b.set_b_name, 28) + '</div>' +
    '<div data-cb="node" data-key="' + _esc(_vdTrim(_vdRaw(b.set_a_name, 60)) || 'Set A') + '" style="' + c + 'left:4%;background:#BFDBFE;' + _ifK(0, 2) + '"></div><div data-cb="node" data-key="' + _esc(_vdTrim(_vdRaw(b.set_b_name, 60)) || 'Set B') + '" style="' + c + 'right:4%;background:#FDE68A;mix-blend-mode:multiply;' + _ifK(1, 2) + '"></div>' +
    '<div style="position:absolute;left:10%;top:48%;width:24%;transform:translateY(-50%);">' + list(b.set_a_exclusive) + '</div>' +
    '<div style="position:absolute;left:38%;top:48%;width:24%;transform:translateY(-50%);text-align:center;">' + list(b.intersection) + '</div>' +
    '<div style="position:absolute;right:10%;top:48%;width:24%;transform:translateY(-50%);">' + list(b.set_b_exclusive) + '</div></div>' + _hgVersionNote(b, 'venn_diagram'));
};

// ── callout_anatomy ───────────────────────────────────────────────────────────────────────────────────────────
_RENDERERS['callout_anatomy'] = function(b) {
  var co = _ifArr(b.callouts, 8).map(function(c) { c = _ifObj(c); return { id: Math.round(_ifNum(c.id, 1, 99, 1)), t: c.title, d: c.description, p: _ifPick(c.pin_position, ['top_left', 'top_right', 'bottom_left', 'bottom_right'], 'top_left') }; });
  var side = function(sfx) { return co.filter(function(c) { return c.p.slice(-sfx.length) === sfx; }).sort(function(x, y) { return (x.p.indexOf('top') === 0 ? 0 : 1) - (y.p.indexOf('top') === 0 ? 0 : 1); }); };
  var card = function(c, i, n) {
    var cKey = _ifS(c.t, 28);
    return '<div data-cb="item" data-key="' + cKey + '" style="display:flex;gap:8px;align-items:flex-start;' + _ifCard(_ifK(c.id - 1, co.length) + _IF_FADE) + '"><span style="flex:0 0 auto;width:22px;height:22px;border-radius:50%;background:#0369A1;color:#fff;font-size:0.75rem;font-weight:700;text-align:center;line-height:22px;">' + c.id + '</span>' +
      '<div><div data-cb="label" data-key="' + cKey + '" style="font-weight:700;">' + cKey + '</div><div style="font-size:0.78rem;color:var(--muted,#475569);">' + _ifS(c.d, 80) + '</div></div></div>';
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
      out = '<li style="position:static;padding:0;"><div aria-hidden="true" data-cb="node" data-key="' + _esc(_cbKid(f)) + '" style="position:absolute;left:' + left + ';top:' + tp + ';width:' + (2 * dr) + 'px;height:' + (2 * dr) + 'px;margin:-' + dr + 'px 0 0 -' + dr + 'px;box-sizing:border-box;border-radius:50%;' +
        (isroot ? 'background:#E0E7FF;border:2px solid #1E1B4B;' : 'background:var(--surface,#F8FAFC);border:2px solid #64748B;') + kk + 'opacity:var(--k,1);"></div>' +
        '<div data-cb="label" data-key="' + _esc(_cbKid(f)) + '" class="ocr-l"' + (nat[i] > Lb[i] ? ' title="' + _ifS(f.l, 28) + '"' : '') + ' style="position:absolute;left:' + left + ';top:' + tp + ';width:max-content;max-width:var(--la);height:' + _OC_RAD_TH + 'px;--la:' + La[i] + 'px;--lb:' + Lb[i] + 'px;transform-origin:0 0;transform:' + tf +
        ';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px;line-height:' + _OC_RAD_TH + 'px;color:var(--text,#0F172A);' + (isroot ? 'font-weight:700;' : '') +
        'text-shadow:0 0 2px var(--bg,#fff),0 0 2px var(--bg,#fff),0 0 3px var(--bg,#fff);' + kk + 'opacity:var(--k,1);">' + _ifS(f.l, 28) + '</div>';
      if (f.par >= 0) {
        p = f.par; c = _ocLinkRadial(ang[p], rad[p], ang[i], rad[i]);
        paths.push('<path data-cb="branch" data-key="' + _esc(_cbKid(flat[p])) + '→' + _esc(_cbKid(f)) + '" d="M' + (500 + 1000 * c[0]).toFixed(3) + ' ' + (500 + 1000 * c[1]).toFixed(3) + 'C' + c.slice(2).map(function(v) { return (500 + 1000 * v).toFixed(3); }).join(' ') + '" fill="none" stroke="#64748B" stroke-width="2" vector-effect="non-scaling-stroke" style="' + kk + 'opacity:var(--k,1);"/>');
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
        var f = { id: n.id || n.l, l: n.l, t: _ocText(n.l), depth: depth, par: par, kids: [] };
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
        out = '<li style="position:static;padding:0;"><div data-cb="node" data-key="' + _esc(_cbKid(f)) + '" style="position:absolute;left:' + _tmPct(Math.max(0, box[i][0]), cw) + ';top:' + _tmPct(Math.max(0, box[i][1]), ch) + ';width:' + _tmPct(ws[i], cw) + ';height:' + nh + 'px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;text-align:center;overflow:hidden;overflow-wrap:anywhere;line-height:1.25;'
          + _ifCard('padding:2px 6px;' + (f.depth === 0 ? 'background:#E0E7FF;color:#1E1B4B;font-weight:700;' : '') + k + _IF_FADE) + '">' + _ifS(f.l, lmax) + '</div>';
        if (link[i] !== undefined) paths.push('<path data-cb="branch" data-key="' + _esc(_cbKid(flat[flat[i].par])) + '→' + _esc(_cbKid(f)) + '" d="' + link[i] + '" fill="none" stroke="#64748B" stroke-width="2" vector-effect="non-scaling-stroke" style="' + k + 'opacity:var(--k,1);"/>');
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
// ── shared chart-axis helper (plotly core-bar) ──
// d3-format 3.1.0 subset (d f e g s % n; fill/align, sign, $, 0, width, comma, precision, ~) and d3-scale 4.0.2 scaleLog ticks / nice (base 10).
// Types b c o p r x X are NOT ported: _axParse returns null for them. Twin of _ax_* in renderers/web_article.py.
var _AX_SPEC = /^(?:(.)?([<>=^]))?([+\-( ])?([$#])?(0)?([0-9]+)?(,)?(\.[0-9]+)?(~)?([a-z%])?$/i;
var _AX_SI = ['y', 'z', 'a', 'f', 'p', 'n', 'µ', 'm', '', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'];
function _axParse(spec) {
  if (typeof spec !== 'string' || spec.length > 24 || spec.indexOf('\n') >= 0 || spec.indexOf('\r') >= 0) return null;
  var m = _AX_SPEC.exec(spec);
  if (!m) return null;
  var typ = m[10] || '';
  if (['d', 'f', 'e', 'g', 's', '%', 'n', ''].indexOf(typ) < 0) return null;
  return {fill: m[1] || ' ', align: m[2] || '>', sign: m[3] || '-', symbol: m[4] || '', zero: !!m[5], width: m[6] === undefined ? null : +m[6],
          comma: !!m[7], precision: m[8] ? +m[8].slice(1) : null, trim: !!m[9], type: typ};
}
function _axDparts(x, p) {
  var s = p ? x.toExponential(p - 1) : x.toExponential(), i = s.indexOf('e'), c = s.slice(0, i);
  return [c.length > 1 ? c.charAt(0) + c.slice(2) : c, +s.slice(i + 1)];
}
function _axPrefixAuto(x, p) {
  var d = _axDparts(x, p), coef = d[0], ex = d[1], pe = Math.max(-8, Math.min(8, Math.floor(ex / 3))) * 3, i = ex - pe + 1, n = coef.length, out;
  if (i === n) out = coef;
  else if (i > n) out = coef + new Array(i - n + 1).join('0');
  else if (i > 0) out = coef.slice(0, i) + '.' + coef.slice(i);
  else out = '0.' + new Array(1 - i).join('0') + _axDparts(x, Math.max(0, p + i - 1))[0];
  return [out, pe];
}
function _axTrim(s) {
  var n = s.length, i, i0 = -1, i1 = 0, c;
  for (i = 1; i < n; ++i) {
    c = s.charAt(i);
    if (c === '.') { i0 = i1 = i; }
    else if (c === '0') { if (i0 === 0) i0 = i; i1 = i; }
    else { if ('123456789'.indexOf(c) < 0) break; if (i0 > 0) i0 = 0; }
  }
  return i0 > 0 ? s.slice(0, i0) + s.slice(i1 + 1) : s;
}
function _axGroup(value, width) {
  var i = value.length, t = [], g = 3, length = 0;
  while (i > 0 && g > 0) {
    if (length + g + 1 > width) g = Math.max(1, width - length);
    t.push(value.substring(i -= g, i + g));
    if ((length += g + 1) > width) break;
  }
  return t.reverse().join(',');
}
function _axFixed(x, d) { return x >= 1e21 ? String(x) : x.toFixed(d); }
function _axDecimal(x) {
  var r = Math.round(x);
  if (r < 1e21) return String(r);
  var p = _axDparts(r, 0), c = p[0];
  return c + new Array(p[1] - c.length + 2).join('0');
}
function _axFormat(spec, v) {
  var s = _axParse(spec);
  v = +v;
  if (s === null || v !== v || v === Infinity || v === -Infinity) return v !== v ? 'NaN' : v > 0 ? 'Infinity' : '−Infinity';
  var typ = s.type, prec = s.precision, trim = s.trim, comma = s.comma, fill = s.fill, align = s.align, sign = s.sign, zero = s.zero, width = s.width;
  if (typ === 'n') { comma = true; typ = 'g'; }
  else if (['d', 'f', 'e', 'g', 's', '%'].indexOf(typ) < 0) { if (prec === null) prec = 12; trim = true; typ = 'g'; }
  if (zero || (fill === '0' && align === '=')) { zero = true; fill = '0'; align = '='; }
  prec = prec === null ? 6 : (typ === 'g' || typ === 's') ? Math.max(1, Math.min(21, prec)) : Math.max(0, Math.min(20, prec));
  var cur = s.symbol === '$', prefix = cur ? '$' : '', suffix = cur ? '' : typ === '%' ? '%' : '';
  var neg = v < 0 || 1 / v < 0, a = Math.abs(v), pe = 0, body;
  if (typ === '%') body = _axFixed(a * 100, prec);
  else if (typ === 'd') body = _axDecimal(a);
  else if (typ === 'e') body = a.toExponential(prec);
  else if (typ === 'f') body = _axFixed(a, prec);
  else if (typ === 'g') body = a.toPrecision(prec);
  else { var pa = _axPrefixAuto(a, prec); body = pa[0]; pe = pa[1]; }
  if (trim) body = _axTrim(body);
  if (neg && +body === 0 && sign !== '+') neg = false;
  var pre = (neg ? (sign === '(' ? '(' : '−') : (sign === '-' || sign === '(' ? '' : sign)) + prefix;
  var suf = (typ === 's' ? _AX_SI[8 + pe / 3] : '') + suffix + (neg && sign === '(' ? ')' : ''), i, c;
  for (i = 0; i < body.length; ++i) {
    c = body.charCodeAt(i);
    if (c < 48 || c > 57) { suf = (c === 46 ? '.' + body.slice(i + 1) : body.slice(i)) + suf; body = body.slice(0, i); break; }
  }
  if (comma && !zero) body = _axGroup(body, Infinity);
  var length = pre.length + body.length + suf.length, pad = width !== null && length < width ? new Array(width - length + 1).join(fill) : '';
  if (comma && zero) { body = _axGroup(pad + body, pad.length ? width - suf.length : Infinity); pad = ''; }
  if (align === '<') return pre + body + suf + pad;
  if (align === '=') return pre + pad + body + suf;
  if (align === '^') { var h = pad.length >> 1; return pad.slice(0, h) + pre + body + suf + pad.slice(h); }
  return pad + pre + body + suf;
}
function _axLogTicks(u, v, n) {
  var rev = v < u, i, j, k, t, z = [];
  if (rev) { t = u; u = v; v = t; }
  i = Math.log10(u); j = Math.log10(v);
  if (j - i < n) {
    i = Math.floor(i); j = Math.ceil(j);
    for (; i <= j; ++i) {
      for (k = 1; k < 10; ++k) {
        t = i < 0 ? k / _hgP10(-i) : k * _hgP10(i);
        if (t < u) continue;
        if (t > v) break;
        z.push(t);
      }
    }
    if (z.length * 2 < n) z = _hgTicks(u, v, n);
  } else {
    z = _hgTicks(i, j, Math.min(j - i, n)).map(function(q) { return _hgP10(q); });
  }
  return rev ? z.reverse() : z;
}
function _axLogNice(u, v) {
  var rev = v < u, a = rev ? v : u, b = rev ? u : v;
  a = _hgP10(Math.floor(Math.log10(a))); b = _hgP10(Math.ceil(Math.log10(b)));
  return rev ? [b, a] : [a, b];
}
function _axScale(lo, hi, log, rng, reverse, count) {
  var nz, ticks, f;
  if (rng) { lo = rng[0]; hi = rng[1]; }
  else if (log) { nz = _axLogNice(lo, hi); lo = nz[0]; hi = nz[1]; if (lo === hi) hi = lo * 10; }
  else {
    if (lo === hi) { if (lo !== 0) { lo = lo - 1; hi = hi + 1; } else { lo = 0; hi = 1; } }
    nz = _hgNice(lo, hi, count); lo = nz[0]; hi = nz[1];
  }
  ticks = log ? _axLogTicks(lo, hi, count) : _hgTicks(lo, hi, count);
  if (log) {
    var major = ticks.filter(function(t) { return t === _hgP10(Math.round(Math.log10(t))); });
    if (major.length >= 2) ticks = major;
  }
  if (log) { var l0 = Math.log10(lo), l1 = Math.log10(hi); f = function(v) { return (Math.log10(v) - l0) / (l1 - l0); }; }
  else f = function(v) { return (v - lo) / (hi - lo); };
  return {lo: lo, hi: hi, ticks: ticks, log: log, pos: reverse ? function(v) { return 1 - f(v); } : f};
}
// ── chartjs_bar (plotly core-bar) ── static HTML bars on the shared axis helper above. Twin of _render_chartjs_bar in renderers/web_article.py;
// this definition replaces the one in atoms_charts.gs (this file loads after it).
var _CB_COL = ['var(--accent,#0369A1)', 'var(--chart-2,#9A6120)', 'var(--chart-3,#0F6C4F)', 'var(--chart-4,#810998)', 'var(--chart-5,#19294E)',
               'var(--chart-6,#B91C1C)', 'var(--chart-7,#0E7490)', 'var(--chart-8,#5B21B6)'];
var _CB_CATS = 40, _CB_SERIES = 8, _CB_PH = 240, _CB_CHIP = 'position:absolute;z-index:1;font-size:0.75rem;line-height:1.25;padding:0 3px;border-radius:3px;white-space:nowrap;background:var(--surface,#F8FAFC);color:var(--text,#0F172A);border:1px solid ';
var _CB_MUTED = 'var(--muted,#475569)';
var _CB_LABW = 'clamp(64px,24cqw,150px)';
function _cbFill(i, col) {
  var k = i % 4;
  if (k === 0) return 'background:' + col + ';';
  if (k === 1) return 'background-color:var(--bg,#fff);background-image:repeating-linear-gradient(45deg,' + col + ' 0 3px,transparent 3px 7px);';
  if (k === 2) return 'background-color:var(--bg,#fff);background-image:radial-gradient(' + col + ' 1.6px,transparent 1.9px);background-size:7px 7px;';
  return 'background-color:var(--bg,#fff);background-image:repeating-linear-gradient(45deg,' + col + ' 0 2px,transparent 2px 6px),repeating-linear-gradient(-45deg,' + col + ' 0 2px,transparent 2px 6px);';
}
function _cbStr(v, mx) { return (v === undefined || v === null || typeof v === 'object') ? '' : String(v).slice(0, mx); }
function _cbNum(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12 ? v : null; }
function _cbPc(f) { var s = (f * 100).toFixed(3); if (/^-0\.0+$/.test(s)) s = s.slice(1); return s + '%'; }
function _cbSpec(v) { return typeof v === 'string' && v !== '' && _axParse(v) !== null ? v : null; }
function _cbObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }
function _cbData(b) {
  var ds = b.datasets, labs = _ifArr(b.labels, 200), skipped = 0, series = [], rows, i, k, givenN = Array.isArray(b.labels) ? b.labels.length : 0, givenS;
  if (!(Array.isArray(ds) && ds.length)) {
    rows = _ifArr(b.data, 200);
    givenN = Array.isArray(b.data) ? b.data.length : 0;
    if (rows.length) {
      labs = rows.map(function(r) { return _cbObj(r) ? _cbStr(r.label, 40) : ''; });
      ds = [{label: _cbStr(b.title, 40) || 'Value', data: rows.map(function(r) { return _cbObj(r) ? r.value : null; })}];
    } else ds = [];
  }
  givenS = Array.isArray(ds) ? ds.length : 0;
  ds = _ifArr(ds, 24);
  for (k = 0; k < ds.length; k++) {
    var d = ds[k];
    if (!_cbObj(d)) { skipped++; continue; }
    var vals = _ifArr(d.data, 200).map(_cbNum), col = d.color;
    if (Array.isArray(d.data) && d.data.length > givenN) givenN = d.data.length;
    vals.forEach(function(x) { if (x === null) skipped++; });
    series.push([_cbStr(d.label, 40) || 'Series ' + (k + 1), typeof col === 'string' && /^#[0-9a-fA-F]{6}$/.test(col) ? col : null, vals]);
  }
  var n = labs.length;
  series.forEach(function(s) { if (s[2].length > n) n = s[2].length; });
  var labels = [];
  for (i = 0; i < n; i++) labels.push((i < labs.length && labs[i] !== null && labs[i] !== undefined ? _cbStr(labs[i], 40) : '') || String(i + 1));
  return [labels, series, skipped, [Math.max(givenN, n), Math.max(givenS, series.length)]];
}
_RENDERERS['chartjs_bar'] = function(b) {
  var dt = _cbData(b), labels = dt[0], series = dt[1], skipped = dt[2], given = dt[3], n = labels.length, S = series.length, i, k, j, q;
  var anyv = false;
  series.forEach(function(s) { s[2].forEach(function(v) { if (v !== null) anyv = true; }); });
  if (n === 0 || !anyv) return _ifWrap(_ifTitle(b) + _hgNote('No numbers to draw as bars.'));
  var notes = skipped ? _hgSkipNote(skipped) : '';
  var nd = Math.min(n, _CB_CATS), sd = Math.min(S, _CB_SERIES);
  if (given[0] > nd) notes += _hgNote('The first ' + nd + ' of ' + given[0] + ' categories are drawn; ' + (given[0] === n ? 'the table has all of them.' : 'the table has the first ' + n + '.'));
  if (given[1] > sd) notes += _hgNote('The first ' + sd + ' of ' + given[1] + ' series are drawn; ' + (given[1] === S ? 'the table has all of them.' : 'the table has the first ' + S + '.'));
  var horiz = b.orientation === 'h' || b.orientation === 'horizontal';
  var mode = _ifPick(b.mode, ['group', 'stack', 'relative', 'overlay'], 'group');
  var log = b.y_scale === 'log';
  var cnt = Math.floor(_ifNum(b.y_ticks, 2, 12, 5));
  var gap = _ifNum(b.gap, 0, 0.8, 0.3);
  var show = !!b.show_values && b.show_values !== 'false';
  var lp = _ifPick(b.legend_position, ['top', 'bottom', 'right', 'none'], S > 1 ? 'top' : 'none');
  var rev = b.y_reverse === true || b.y_reverse === 'true';
  var yf = b.y_format, vf0 = b.value_format;
  [['y_format', yf], ['value_format', vf0]].forEach(function(p) {
    if (p[1] && _cbSpec(p[1]) === null) notes += _hgNote(p[0] + ' "' + _ifS(p[1], 24) + '" is not a number format this chart knows; plain numbers are shown.');
  });
  yf = _cbSpec(yf); vf0 = _cbSpec(vf0);
  var allv = [];
  series.forEach(function(s) { s[2].forEach(function(v) { if (v !== null) allv.push(v); }); });
  if (log && (mode === 'stack' || mode === 'relative')) {
    mode = 'group';
    notes += _hgNote('Stacked bars need a linear axis; the bars are drawn grouped on the log axis.');
  }
  var rng = b.y_range;
  rng = Array.isArray(rng) && rng.length === 2 && _cbNum(rng[0]) !== null && _cbNum(rng[1]) !== null && rng[0] !== rng[1] ? [rng[0], rng[1]] : null;
  if (rng === null && b.y_range) notes += _hgNote('y_range was not two different numbers; it was ignored.');
  if (rng && rng[0] > rng[1]) rng = [rng[1], rng[0]];
  if (rng && log && rng[0] <= 0) { rng = null; notes += _hgNote('y_range must be above zero on a log axis; it was ignored.'); }
  var segs = [], drop = 0, lo = 0, hi = 0;
  for (i = 0; i < nd; i++) {
    var cum = 0, posC = 0, negC = 0;
    for (k = 0; k < sd; k++) {
      var v = i < series[k][2].length ? series[k][2][i] : null, a, e;
      if (v === null) continue;
      if (log && v <= 0) { drop++; continue; }
      if (mode === 'stack') { a = cum; e = cum + v; cum = e; }
      else if (mode === 'relative') {
        if (v >= 0) { a = posC; e = posC + v; posC = e; } else { a = negC; e = negC + v; negC = e; }
      } else { a = null; e = v; }
      segs.push([i, k, a, e, v]);
    }
  }
  if (log) {
    if (drop) notes += _hgNote(drop + (drop === 1 ? ' number is' : ' numbers are') + ' not above zero, so ' + (drop === 1 ? 'it cannot' : 'they cannot') + ' be drawn on a log axis; the table has ' + (drop === 1 ? 'it' : 'them') + '.');
    if (!segs.length) return _ifWrap(_ifTitle(b) + _hgNote('No numbers above zero to draw on a log axis.') + notes);
    lo = segs[0][4]; hi = segs[0][4];
    segs.forEach(function(s) { if (s[4] < lo) lo = s[4]; if (s[4] > hi) hi = s[4]; });
    if (lo === hi) hi = lo * 10;
  } else {
    segs.forEach(function(s) { var x = s[2] === null ? 0 : s[2]; if (x < lo) lo = x; if (x > hi) hi = x; if (s[3] < lo) lo = s[3]; if (s[3] > hi) hi = s[3]; });
  }
  var ax = _axScale(lo, hi, log, rng, rev, cnt), pos = ax.pos, clip = false;
  var base = log ? ax.lo : (ax.lo > 0 ? ax.lo : ax.hi < 0 ? ax.hi : 0);
  function fr(v) { var f = pos(v); if (f < -1e-9 || f > 1 + 1e-9) clip = true; return Math.min(1, Math.max(0, f)); }
  var dec = _hgDecimals(allv);
  var vf = vf0 ? function(v) { return _axFormat(vf0, v); } : yf ? function(v) { return _axFormat(yf, v); } : function(v) { return _hgNum(v, dec); };
  var tdec = _hgDecimals(ax.ticks);
  var tf = yf ? function(t) { return _axFormat(yf, t); } : log ? function(t) { return _axFormat('~s', t); } : function(t) { return _hgNum(t, tdec); };
  var tlab = ax.ticks.map(tf), tw = 1;
  tlab.forEach(function(x) { if (x.length > tw) tw = x.length; });
  var inner = 1 - gap, kk = mode === 'group' ? sd : 1;
  var colr = [];
  for (k = 0; k < sd; k++) colr.push(series[k][1] || _CB_COL[k % 8]);
  var chipW = 1;
  segs.forEach(function(s) { var l = vf(s[4]).length; if (l > chipW) chipW = l; });
  chipW = chipW * 7 + 10;
  var slotPx = Math.max(34, ((mode === 'group' || mode === 'overlay') ? sd : 1) * 24 + 10);
  if (horiz) {
    var ml = 1;
    labels.slice(0, nd).forEach(function(x) { if (x.length > ml) ml = x.length; });
    slotPx = Math.max(slotPx, Math.min(6, Math.ceil(ml * 6.6 / 69)) * 15 + 6);
  }
  var outside = show && (mode === 'group' || mode === 'overlay');
  var padTop = (outside && !horiz) ? (mode === 'overlay' ? 22 + (sd - 1) * 18 : 22) : 8;
  var padRight = horiz ? (outside ? chipW + 6 : 12) : 12;
  var gutPx = Math.ceil(tw * 7.5) + 14;
  var grid = '', f;
  for (j = 0; j < ax.ticks.length; j++) {
    f = pos(ax.ticks[j]);
    if (f < -1e-9 || f > 1 + 1e-9) continue;
    if (horiz) grid += '<div style="position:absolute;top:0;bottom:0;left:' + _cbPc(f) + ';border-left:1px dashed var(--border,#CBD5E1);"></div>';
    else {
      grid += '<div style="position:absolute;left:0;right:0;bottom:' + _cbPc(f) + ';border-top:1px dashed var(--border,#CBD5E1);"></div>';
      grid += '<div style="position:absolute;right:100%;bottom:' + _cbPc(f) + ';transform:translateY(50%);padding-right:6px;font-size:0.75rem;line-height:1;white-space:nowrap;color:' + _CB_MUTED + ';">' + _esc(tlab[j]) + '</div>';
    }
  }
  var zf = (log || !(ax.lo <= 0 && 0 <= ax.hi)) ? null : pos(0);
  if (zf !== null) grid += horiz ? '<div style="position:absolute;top:0;bottom:0;left:' + _cbPc(zf) + ';border-left:1.5px solid var(--muted,#475569);"></div>'
    : '<div style="position:absolute;left:0;right:0;bottom:' + _cbPc(zf) + ';border-top:1.5px solid var(--muted,#475569);"></div>';
  var byc = {};
  segs.forEach(function(s) { (byc[s[0]] = byc[s[0]] || []).push(s); });
  var bars = '', thr = {};
  for (i = 0; i < nd; i++) {
    var ih = '', list = byc[i] || [];
    if (mode === 'overlay') list = list.slice().sort(function(x, y) { return (y[4] - x[4]) || (x[1] - y[1]); });
    for (q = 0; q < list.length; q++) {
      var s = list[q], kx = s[1], f0 = fr(s[2] !== null ? s[2] : base), f1 = fr(s[3]);
      var low = Math.min(f0, f1), size = Math.abs(f1 - f0), gw = mode === 'group' ? inner / kk : inner;
      var off = (1 - inner) / 2 + (mode === 'group' ? kx * gw : 0), col = colr[kx];
      var geo = horiz ? 'top:' + _cbPc((i + off) / nd) + ';height:' + _cbPc(gw / nd) + ';left:' + _cbPc(low) + ';width:' + _cbPc(size) + ';min-width:2px;'
                      : 'left:' + _cbPc((i + off) / nd) + ';width:' + _cbPc(gw / nd) + ';bottom:' + _cbPc(low) + ';height:' + _cbPc(size) + ';min-height:2px;';
      var chip = '';
      if (show) {
        var txt = vf(s[4]), need = txt.length * 7 + 10, inside = mode === 'stack' || mode === 'relative', place, frac, st;
        if (inside && size < (horiz ? 0.1 : 0.075)) chip = '';
        else {
          if (inside) { place = 'left:50%;top:50%;transform:translate(-50%,-50%);'; frac = horiz ? size : gw / nd; }
          else if (horiz) {
            st = mode === 'overlay' ? (kx - (sd - 1) / 2) * 18 : 0;
            place = 'left:calc(100% + 3px);top:calc(50% + ' + st.toFixed(1) + 'px);transform:translateY(-50%);'; frac = 1;
          } else {
            st = mode === 'overlay' ? kx * 18 : 0;
            place = 'left:50%;bottom:calc(100% + 2px + ' + st + 'px);transform:translateX(-50%);'; frac = gw / nd;
          }
          var wk = null;
          if (!(horiz && !inside)) {
            var lead = horiz ? 150 + padRight : gutPx + 12;
            wk = frac <= 0 ? 99999 : Math.ceil((lead + need / frac) / 50) * 50;
            thr[wk] = true;
          }
          chip = '<div class="cbv' + (wk !== null ? ' cbw' + wk : '') + '" style="' + _CB_CHIP + col + ';' + place + '">' + _esc(txt) + '</div>';
        }
      }
      ih += '<div' + (sd > 1 ? ' data-cb="bar" data-key="' + _esc([labels[i], series[kx][0]].join('/')) + '"' : '') + ' style="position:absolute;box-sizing:border-box;border:1.5px solid ' + col + ';' + _cbFill(kx, col) + geo + '">' + chip + '</div>';
    }
    bars += '<div' + (sd === 1 ? ' data-cb="bar" data-key="' + _esc(labels[i]) + '"' : '') + ' style="position:absolute;inset:0;' + _ifK(i, nd) + _IF_FADE + '">' + ih + '</div>';
  }
  var css = '<style>' + Object.keys(thr).map(Number).sort(function(x, y) { return x - y; }).map(function(w) { return '@container (max-width:' + w + 'px){.ifcb .cbw' + w + '{display:none}}'; }).join('') + '@container (max-width:560px){.ifcb .cbx:not(.cbc){display:none}}</style>';
  var gut = horiz ? _CB_LABW : gutPx + 'px', xs = '', plot;
  if (horiz) {
    for (i = 0; i < nd; i++) {
      xs += '<div data-cb="label" data-key="' + _esc(labels[i]) + '" style="position:absolute;right:100%;top:' + _cbPc((i + 0.5) / nd) + ';transform:translateY(-50%);width:' + _CB_LABW
        + ';box-sizing:border-box;padding-right:8px;text-align:right;font-size:0.75rem;line-height:1.15;color:' + _CB_MUTED
        + ';overflow-wrap:anywhere;">' + _esc(labels[i]) + '</div>';
    }
    var axis = '';
    for (j = 0; j < ax.ticks.length; j++) {
      f = pos(ax.ticks[j]);
      if (f < -1e-9 || f > 1 + 1e-9) continue;
      axis += '<div class="cbx' + (j % 2 === 0 ? ' cbc' : '') + '" style="position:absolute;top:6px;left:' + _cbPc(f) + ';transform:translateX(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:' + _CB_MUTED + ';">' + _esc(tlab[j]) + '</div>';
    }
    plot = '<div role="img" aria-label="@ARIA@" style="position:relative;height:' + (nd * slotPx) + 'px;border-left:1px solid var(--muted,#475569);">' + grid + bars + xs + '</div>'
      + '<div style="position:relative;height:26px;margin-top:2px;">' + axis + '</div>';
  } else {
    for (i = 0; i < nd; i++) xs += '<div data-cb="label" data-key="' + _esc(labels[i]) + '" style="flex:0 0 ' + _cbPc(1 / nd) + ';box-sizing:border-box;padding:4px 2px 0;text-align:center;font-size:0.75rem;line-height:1.2;color:' + _CB_MUTED + ';overflow-wrap:anywhere;">' + _esc(labels[i]) + '</div>';
    plot = '<div role="img" aria-label="@ARIA@" style="position:relative;height:' + _CB_PH + 'px;border-bottom:1px solid var(--muted,#475569);">' + grid + bars + '</div>'
      + '<div style="display:flex;">' + xs + '</div>';
  }
  var iHi = 0, iLo = 0;
  for (q = 1; q < segs.length; q++) { if (segs[q][4] > segs[iHi][4]) iHi = q; if (segs[q][4] < segs[iLo][4]) iLo = q; }
  function where(q) { return sd > 1 ? series[segs[q][1]][0] + ', ' + labels[segs[q][0]] : labels[segs[q][0]]; }
  var aria = (mode === 'stack' ? 'Stacked ' : mode === 'relative' ? 'Relative stacked ' : mode === 'overlay' ? 'Overlaid ' : sd > 1 ? 'Grouped ' : '') + (horiz ? 'horizontal ' : '') + 'bar chart of '
    + nd + (nd === 1 ? ' category' : ' categories') + (sd > 1 ? ' and ' + sd + ' series' : '') + '. Highest value ' + vf(segs[iHi][4]) + ' (' + where(iHi)
    + '), lowest ' + vf(segs[iLo][4]) + ' (' + where(iLo) + '). Value axis' + (log ? ' (log)' : '') + ' from ' + tf(ax.lo) + ' to ' + tf(ax.hi) + (rev ? ', reversed' : '') + '.';
  plot = plot.replace('@ARIA@', function() { return _esc(aria); });
  if (clip) notes += _hgNote('Bars that pass the y_range are cut at the axis; the table has the full values.');
  if (show) notes += _hgNote('Value labels hide when the chart is too narrow to fit them; the table has every value.');
  var legend = '';
  if (lp !== 'none' && sd > 0) {
    legend = '<div style="display:flex;flex-wrap:wrap;gap:4px 14px;font-size:0.75rem;line-height:1.2;' + (lp === 'right' ? 'flex-direction:column;' : '') + '">';
    for (k = 0; k < sd; k++) legend += '<div style="display:flex;align-items:center;gap:6px;"><span aria-hidden="true" style="flex:0 0 auto;width:14px;height:14px;box-sizing:border-box;border:1.5px solid ' + colr[k] + ';' + _cbFill(k, colr[k]) + '"></span>'
      + '<span>' + _esc(series[k][0]) + '</span></div>';
    legend += '</div>';
  }
  var box = '<div style="flex:1 1 260px;min-width:0;"><div style="position:relative;margin:' + padTop + 'px ' + padRight + 'px 0 ' + gut + ';">' + plot + '</div></div>';
  var body = lp === 'right' ? '<div style="display:flex;flex-wrap:wrap;gap:8px 16px;align-items:flex-start;">' + box + legend + '</div>' : box;
  var chart = '<div class="ifcb" style="container-type:inline-size;max-width:100%;overflow:hidden;">' + css + (lp === 'top' ? legend : '') + body + (lp === 'bottom' ? legend : '') + '</div>';
  var head = ['Category'].concat(series.map(function(s) { return s[0]; }));
  var rows = [];
  for (i = 0; i < n; i++) {
    var r = [labels[i]];
    for (k = 0; k < S; k++) r.push(i < series[k][2].length && series[k][2][i] !== null ? _hgNum(series[k][2][i], dec) : '');
    rows.push(r);
  }
  return _ifWrap(_ifTitle(b) + chart + notes + _hgVersionNote(b, 'chartjs_bar') + _ifTable(head, rows));
};
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
      '<g class="hgrg" data-cb="bar" data-key="' + _esc(u[0]) + '" style="' + _ifK(k, n) + 'transform:scaleY(var(--k,1));"><title>' + _esc(u[0] + ': ' + u[1].length + ' values') + '</title>' +
      '<path class="hgrb" d="' + path + '"/><path class="hgr" d="' + path + '"/></g></svg></div></div>';
  });
  var css = '<style>.ifhg .hgrb{fill:var(--bg,#fff)}' +
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
  if (_hgOptsGiven(b)) return _hgRenderOpts(b);
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
    rects += '<rect class="hgb" data-cb="bar" data-key="' + _esc(lab[i] + ' to ' + lab[i + 1] + us) + '" x="' + x.toFixed(2) + '" y="' + (1000 - h).toFixed(2) + '" width="' + w.toFixed(2) + '" height="' + h.toFixed(2) + '" style="' + _ifK(i, m) +
      'transform:scaleY(var(--k,1));"><title>' + _esc(lab[i] + ' to ' + lab[i + 1] + us + ': ' + counts[i]) + '</title></rect>';
  }
  yt.forEach(function(t) {
    var bt = top > 0 ? (t / top * 100).toFixed(3) + '%' : '0%';
    grid += '<div style="position:absolute;left:0;right:0;bottom:' + bt + ';border-top:1px solid ' + (t === 0 ? 'var(--muted,#475569)' : 'var(--border,#CBD5E1)') + ';"></div>' +
      '<div style="position:absolute;right:100%;margin-right:6px;bottom:' + bt + ';transform:translateY(50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + _hgNum(t, 0) + '</div>';
  });
  var css = '<style>.ifhg .hgb{fill:var(--accent,#0369A1);stroke:var(--bg,#fff);stroke-width:1px;vector-effect:non-scaling-stroke}' +
    '@container (max-width:560px){.ifhg .hgx:not(.hgc){display:none}}</style>';
  var chart = '<div class="ifhg" style="container-type:inline-size;max-width:100%;overflow:hidden;">' + css +
    '<div style="font-size:0.75rem;color:var(--muted,#475569);margin:0 0 10px 0;">Count of values per bin</div>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;height:220px;margin:0 34px 34px 46px;">' + grid +
    '<svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true" focusable="false" style="position:absolute;left:0;top:0;width:100%;height:100%;display:block;overflow:visible;">' + rects + '</svg>' + xs + '</div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 34px 0 46px;">' + _esc(cap) + '</div>' : '') + '</div>';
  return _ifWrap(_ifTitle(b) + chart + skipNote + _hgVersionNote(b) + _ifTable(['Bin from', 'Bin to', 'Count'], counts.map(function(c, k) { return [lab[k] + us, lab[k + 1] + us, String(c)]; })));
};


// ── histogram options (plotly wave B, d3-variants): explicit bins (bin_size / bin_start / bin_end), norm, cumulative, func + weights ──
// Twin of _hg_fixed / _render_histogram_opts in renderers/web_article.py; edges are start + k * size, binned like d3.bin().domain().thresholds() (bisectRight).
var _HG_OPT_KEYS = ['bin_size', 'bin_start', 'bin_end', 'norm', 'cumulative', 'func', 'weights'], _HG_MAX_BINS = 200, _HG_RATIO_CAP = 1e6;   // range / size is capped before rounding: only 200 bins are drawn
var _HG_FUNCS = { count: 'Count', sum: 'Sum of weights', avg: 'Average weight', min: 'Smallest weight', max: 'Largest weight' };
var _HG_NORMS = { 'percent': 'Percent', 'probability': 'Probability', 'density': 'Density', 'probability density': 'Probability density' };
function _hgIn(v, d) { return typeof v === 'string' && Object.prototype.hasOwnProperty.call(d, v); }
function _hgOptsGiven(b) {   // an option set to something other than its default (absent, null, '' / 'count' for norm, 'count' for func, false for cumulative)
  return ['bin_size', 'bin_start', 'bin_end'].some(function(k) { return b[k] !== undefined && b[k] !== null; }) || (b.norm !== undefined && b.norm !== null && b.norm !== '' && b.norm !== 'count') ||
    (b.func !== undefined && b.func !== null && b.func !== 'count') || b.cumulative === true || Array.isArray(b.weights);
}
function _ifUkey(k, used) { var base = k, n = 1; while (used[k] === true) { n++; k = base + ' (' + n + ')'; } used[k] = true; return _esc(k); }   // a contract data-key unique within one drawing (twin: _cb_ukey)
function _hgFinite(v) { return typeof v === 'number' && Math.abs(v) <= 1e12; }
function _hgFixed(vals, start, size, end) {
  var full = Math.max(1, Math.ceil(Math.min((end - start) / size, _HG_RATIO_CAP))), nb = Math.min(_HG_MAX_BINS, full), t = [], k, edges = [], inner, top;
  for (k = 0; k <= nb; k++) t.push(k === full ? end : start + k * size);
  for (k = 0; k < nb; k++) edges.push([t[k], t[k + 1]]);
  inner = t.slice(1, nb); top = t[nb];
  return [edges, vals.map(function(x) {
    if (!(start <= x && x <= top)) return -1;
    var lo = 0, hi = inner.length, mid;
    while (lo < hi) { mid = (lo + hi) >>> 1; if (inner[mid] <= x) lo = mid + 1; else hi = mid; }
    return lo;
  })];
}
function _hgYFmt(v) { var s = v.toFixed(3); if (s.indexOf('.') >= 0) s = s.replace(/0+$/, '').replace(/\.$/, ''); return (s === '-0' || s === '') ? '0' : s; }
function _hgRenderOpts(b) {
  var raw = _ifArr(b.values, 2000), wraw = b.weights, weighted = Array.isArray(wraw), func = _hgIn(b.func, _HG_FUNCS) ? b.func : 'count', ignored = [], pairs = [], skipped = 0, i, k;
  [['norm', _HG_NORMS], ['func', _HG_FUNCS]].forEach(function(e) { if (b[e[0]] !== undefined && !_hgIn(b[e[0]], e[1]) && !(e[0] === 'norm' && (b.norm === '' || b.norm === 'count'))) ignored.push(e[0]); });
  raw.forEach(function(v, j) { var w = weighted ? (j < wraw.length ? wraw[j] : 1) : 1; if (_hgFinite(v) && _hgFinite(w)) pairs.push([v, w]); else skipped++; });
  var vals = pairs.map(function(p) { return p[0]; }), notes = _hgSkipNote(skipped);
  if (vals.length < 5) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A histogram needs at least 5 numbers; this list has ' + vals.length + '.</div>' + notes);
  if (func !== 'count' && !weighted) { notes += _hgNote('func ' + func + ' needs weights; counting values instead.'); func = 'count'; }
  var size = _hgFinite(b.bin_size) && b.bin_size > 0 ? b.bin_size : null, start = _hgFinite(b.bin_start) ? b.bin_start : null, end = _hgFinite(b.bin_end) ? b.bin_end : null, edges, idx;
  if (b.bin_size !== undefined && size === null) ignored.push('bin_size');
  if (b.bin_start !== undefined && start === null) ignored.push('bin_start');
  if (b.bin_end !== undefined && end === null) ignored.push('bin_end');
  if (start !== null && end !== null && end <= start) { end = null; ignored.push('bin_end'); }
  if (size === null && start === null && end === null) {
    edges = _hgBin(vals, _hgTarget(b.bins))[0];
    idx = vals.map(function(x) { var j = -1; for (var q = 0; q < edges.length; q++) if (edges[q][0] <= x && x < edges[q][1]) { j = q; break; } return j < 0 ? edges.length - 1 : j; });
  } else {
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    if (size === null) { var span0 = (end !== null ? end : hi) - (start !== null ? start : lo); size = span0 > 0 ? span0 / Math.max(1, Math.ceil(Math.log(vals.length) / Math.log(2)) + 1) : 1; if (!(size > 0)) size = 1; }
    if (start === null) { var qs = lo / size; start = (end === null || lo < end) ? (Math.abs(qs) <= 1e15 ? Math.floor(qs) * size : lo) : end - size; }
    var many = false;
    if (end === null) { var nbin = Math.floor(Math.min((hi - start) / size, _HG_RATIO_CAP)) + 1; end = start + nbin * size; many = nbin > _HG_MAX_BINS; }
    if (many || (end - start) / size > _HG_MAX_BINS) notes += _hgNote('The bin size gives more than ' + _HG_MAX_BINS + ' bins; the first ' + _HG_MAX_BINS + ' are drawn.');
    var fx = _hgFixed(vals, start, size, end); edges = fx[0]; idx = fx[1];
  }
  var m = edges.length, inside = idx.filter(function(q) { return q >= 0; }).length, cnt = [], ws = [];
  if (inside < vals.length) notes += _hgNote((vals.length - inside) + (vals.length - inside === 1 ? ' value is' : ' values are') + ' outside the bins and not counted.');
  if (!inside) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">No value falls inside the bins.</div>' + notes);
  for (k = 0; k < m; k++) { cnt.push(0); ws.push([]); }
  pairs.forEach(function(p, j) { if (idx[j] >= 0) { cnt[idx[j]]++; ws[idx[j]].push(p[1]); } });
  var y = ws.map(function(a) {
    if (!a.length) return (func === 'count' || func === 'sum') ? 0 : null;   // an empty bin counts 0 (and sums to 0); only avg / min / max have no value there
    if (func === 'count') return a.length;
    if (func === 'min') return Math.min.apply(null, a);
    if (func === 'max') return Math.max.apply(null, a);
    var t = 0, q; for (q = 0; q < a.length; q++) t += a[q];
    return func === 'avg' ? t / a.length : t;
  });
  var norm = _hgIn(b.norm, _HG_NORMS) ? b.norm : '', cum = b.cumulative === true;
  if (func !== 'count' && func !== 'sum') {
    if (norm || cum) notes += _hgNote('norm and cumulative apply to count and sum only; the ' + _HG_FUNCS[func].toLowerCase() + ' per bin is drawn.');
    norm = ''; cum = false;
  }
  if (norm) {
    var tot = 0; y.forEach(function(v) { tot += v || 0; });
    if (tot === 0) { notes += _hgNote('The bins add up to 0, so norm was not applied.'); norm = ''; }
    else y = y.map(function(v, q) { var w = edges[q][1] - edges[q][0]; return v === null ? null : norm === 'percent' ? v * 100 / tot : norm === 'probability' ? v / tot : norm === 'density' ? v / w : v / (tot * w); });
  }
  if (cum) { var run = 0; y = y.map(function(v) { run += v || 0; return run; }); }
  if (ignored.length) notes += _hgNote('Not understood and ignored: ' + _esc(ignored.join(', ')) + '.');
  var X0 = edges[0][0], X1 = edges[m - 1][1], span = X1 - X0, got = y.filter(function(v) { return v !== null; });
  var ylo = Math.min(0, Math.min.apply(null, got)), yhi = Math.max(0, Math.max.apply(null, got));
  if (yhi === ylo) yhi = ylo + 1;
  var nz = _hgNice(ylo, yhi, 4); ylo = nz[0]; yhi = nz[1];
  var yt = _hgTicks(ylo, yhi, 4), ys = yhi - ylo;
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', xl = b.x_label ? String(b.x_label).slice(0, 40) : '', cap = xl ? xl + (unit ? ' (' + unit + ')' : '') : unit, us = unit ? ' ' + unit : '';
  var ev = edges.map(function(e) { return e[0]; }); ev.push(edges[m - 1][1]);
  var d = _hgDecimals(ev), lab = ev.map(function(v) { return _hgNum(v, d); });
  var ycap = norm ? _HG_NORMS[norm] : _HG_FUNCS[func];
  ycap = (cum ? 'Cumulative ' + ycap.charAt(0).toLowerCase() + ycap.slice(1) : ycap) + ' per bin';
  var top = -1; for (k = 0; k < m; k++) if (y[k] !== null && (top < 0 || y[k] > y[top])) top = k;
  var aria = 'Histogram of ' + inside + ' values in ' + m + (m === 1 ? ' bin' : ' bins') + ' from ' + lab[0] + ' to ' + lab[lab.length - 1] + us + '. ' + ycap + '. Highest bin: ' + lab[top] + ' to ' + lab[top + 1] + us + ', ' + _hgYFmt(y[top]) + '.';
  function yp(v) { return (v - ylo) / ys * 1000; }
  var rects = '', z = yp(0), grid = '', kused = Object.create(null);
  for (i = 0; i < m; i++) {
    if (y[i] === null) continue;
    var x = span > 0 ? (edges[i][0] - X0) / span * 1000 : 0, w = span > 0 ? (edges[i][1] - edges[i][0]) / span * 1000 : 1000, a = Math.min(yp(y[i]), z), c = Math.max(yp(y[i]), z);
    rects += '<rect class="hgb' + (y[i] < 0 ? ' hgn' : '') + '" data-cb="bar" data-key="' + _ifUkey(lab[i] + ' to ' + lab[i + 1] + us, kused) + '" x="' + x.toFixed(2) + '" y="' + (1000 - c).toFixed(2) + '" width="' + w.toFixed(2) + '" height="' + (c - a).toFixed(2) + '" style="' + _ifK(i, m) +
      'transform:scaleY(var(--k,1));"><title>' + _esc(lab[i] + ' to ' + lab[i + 1] + us + ': ' + _hgYFmt(y[i])) + '</title></rect>';
  }
  yt.forEach(function(t) {
    var bt = (yp(t) / 10).toFixed(3) + '%';
    grid += '<div style="position:absolute;left:0;right:0;bottom:' + bt + ';border-top:1px solid ' + (t === 0 ? 'var(--muted,#475569)' : 'var(--border,#CBD5E1)') + ';"></div>' +
      '<div style="position:absolute;right:100%;margin-right:6px;bottom:' + bt + ';transform:translateY(50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + _hgYFmt(t) + '</div>';
  });
  var css = '<style>.ifhg .hgb{fill:var(--accent,#0369A1);stroke:var(--bg,#fff);stroke-width:1px;vector-effect:non-scaling-stroke;transform-box:fill-box;transform-origin:50% 100%}.ifhg .hgn{transform-origin:50% 0}' +
    '@container (max-width:560px){.ifhg .hgx:not(.hgc){display:none}}</style>';
  var chart = '<div class="ifhg" style="container-type:inline-size;max-width:100%;overflow:hidden;">' + css +
    '<div style="font-size:0.75rem;color:var(--muted,#475569);margin:0 0 10px 0;">' + _esc(ycap) + '</div>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;height:220px;margin:0 34px 34px 46px;">' + grid +
    '<svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true" focusable="false" style="position:absolute;left:0;top:0;width:100%;height:100%;display:block;overflow:visible;">' + rects + '</svg>' + _hgAxis(ev, X0, span, lab) + '</div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 34px 0 46px;">' + _esc(cap) + '</div>' : '') + '</div>';
  var plotted = norm || cum || func !== 'count';
  return _ifWrap(_ifTitle(b) + chart + notes + _hgVersionNote(b, 'histogram') + _ifTable(['Bin from', 'Bin to', 'Count'].concat(plotted ? [ycap] : []),
    edges.map(function(e, q) { return [lab[q] + us, lab[q + 1] + us, String(cnt[q])].concat(plotted ? [y[q] !== null ? _hgYFmt(y[q]) : 'none'] : []); })));
}
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
// Dodge beeswarm for box_plot show_points: dots in sorted order, each at its exact x and at the smallest |y| from the row's centre line at which it does not
// touch a dot already placed; ties alternate sides, starting above. Candidates: 0 and, for every placed dot closer than the minimum distance, the two heights
// at which a new dot would just touch it. An independent implementation of the dodge approach (Observable Plot's dodge transform, d3's beeswarm example).
// Pixels of a 180px reference plot; a dot with no room within +/-lim goes to the row's edge, is flagged and is not an obstacle. Twin of _bp_dodge in web_article.py.
var _BP_REFW = 180, _BP_DOT_R = 2.5, _BP_PAD = 0.5, _BP_MAX_POINTS = 300, _BP_MIN_PER_GROUP = 20, _BP_ROW_H = 64;
function _bpDodge(xs, lim) {
  var d = 2 * _BP_DOT_R + _BP_PAD, d2 = d * d - 1e-9, win = [], head = 0, side = -1, edge = -1, ys = [], over = [];
  xs.forEach(function(x) {
    while (head < win.length && win[head][0] <= x - d) head++;
    if (head > 64) { win.splice(0, head); head = 0; }
    var near = win.slice(head), cands = [0], i;
    near.forEach(function(p) { var h = Math.sqrt(d * d - (x - p[0]) * (x - p[0])); cands.push(p[1] + h); cands.push(p[1] - h); });
    cands = cands.filter(function(c) { return Math.abs(c) <= lim; }).sort(function(p, q) { return Math.abs(p) - Math.abs(q); });
    var free = function(y) { for (var k = 0; k < near.length; k++) { if ((x - near[k][0]) * (x - near[k][0]) + (y - near[k][1]) * (y - near[k][1]) < d2) return false; } return true; };
    var y = 0, prev = -1, found = false;
    for (i = 0; i < cands.length; i++) {
      var a = Math.abs(cands[i]);
      if (a === prev) continue;
      prev = a;
      if (a === 0) { if (free(0)) { y = 0; found = true; break; } continue; }
      var first = free(side * a), second = free(-side * a);
      if (first || second) {
        found = true;
        if (first && second) { y = side * a; side = -side; } else y = first ? side * a : -side * a;
        break;
      }
    }
    if (found) { win.push([x, y]); ys.push(y); over.push(false); }
    else { ys.push(edge * lim); over.push(true); edge = -edge; }
  });
  return [ys, over];
}
// toFixed(2) without a negative zero ("-0.00"), which Python's _if_fixed never prints.
function _bpPx(v) { var t = v.toFixed(2); return parseFloat(t) === 0 ? '0.00' : t; }
// How many dots each group may draw: all when the chart has at most _BP_MAX_POINTS numbers, else _BP_MAX_POINTS shared in proportion to the sizes, each group
// keeping at least min(size, _BP_MIN_PER_GROUP). Twin of _bp_alloc.
function _bpAlloc(sizes) {
  var total = sizes.reduce(function(a, c) { return a + c; }, 0);
  if (total <= _BP_MAX_POINTS) return sizes.slice();
  var base = sizes.map(function(s) { return Math.min(s, _BP_MIN_PER_GROUP); }), room = sizes.map(function(s, i) { return s - base[i]; });
  var budget = _BP_MAX_POINTS - base.reduce(function(a, c) { return a + c; }, 0), rsum = room.reduce(function(a, c) { return a + c; }, 0);
  var out = base.map(function(b, i) { return b + Math.floor(budget * room[i] / rsum); });
  var left = _BP_MAX_POINTS - out.reduce(function(a, c) { return a + c; }, 0);
  for (var i = 0; i < out.length && left > 0; i++) if (out[i] < sizes[i]) { out[i]++; left--; }
  return out;
}
// The values drawn as dots, at most `cap`: all of them, or evenly spaced through the sorted values (first and last included).
function _bpPoints(vals, cap) {
  var a = vals.slice().sort(function(x, y) { return x - y; }), m = a.length, c = cap - 1, out = [], i;
  if (m <= cap) return a;
  if (c <= 0) return [a[Math.floor(m / 2)]];
  for (i = 0; i < cap; i++) out.push(a[Math.floor((i * (m - 1) + Math.floor(c / 2)) / c)]);
  return out;
}
_RENDERERS['box_plot'] = function(b) {
  if (_bpOptsGiven(b)) return _bpRenderOpts(b);
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
  var show = b.show_points === true, caps = show ? _bpAlloc(used.map(function(u) { return u[1].length; })) : [], rows = '', capped = '';
  used.forEach(function(u, k) {
    var s = stats[k], med = s.median;
    var distinct = s.outliers.filter(function(v, i, a) { return i === 0 || v !== a[i - 1]; }).sort(function(x, y) { return (Math.abs(y - med) - Math.abs(x - med)) || (x - y); });
    if (distinct.length > _BP_MAX_DOTS) capped += _hgNote(_esc(u[0]) + ' has ' + distinct.length + ' distinct outliers; the ' + _BP_MAX_DOTS + ' furthest from the median are drawn. The table counts them all.');
    var dots = distinct.slice(0, _BP_MAX_DOTS).map(function(o) { return '<div class="bpo" style="position:absolute;left:' + pos(o) + ';top:50%;width:7px;height:7px;box-sizing:border-box;border-radius:50%;border:1.5px solid var(--accent,#0369A1);background:var(--bg,#fff);transform:translate(-50%,-50%);"></div>'; }).join('');
    var strip = '';
    if (show) {
      var drawn = _bpPoints(u[1], caps[k]);
      if (u[1].length > drawn.length) capped += _hgNote(_esc(u[0]) + ' has ' + u[1].length + ' numbers; the ' + drawn.length + ' drawn as dots are evenly spaced through the sorted values. The table counts them all.');
      var dg = _bpDodge(drawn.map(function(v) { return (span > 0 ? (v - X0) / span : 0.5) * _BP_REFW; }), _BP_ROW_H / 2 - 4), cnt = dg[1].filter(function(o) { return o; }).length;
      if (cnt) capped += _hgNote(cnt + (cnt === 1 ? ' dot overlaps in ' : ' dots overlap in ') + _esc(u[0]) + '; the table has every value.');
      strip = drawn.map(function(v, i) {
        return '<div class="bpd" style="position:absolute;left:' + pos(v) + ';top:calc(50% + ' + _bpPx(dg[0][i]) + 'px);width:5px;height:5px;border-radius:50%;background:var(--accent,#0369A1);opacity:0.7;transform:translate(-50%,-50%);"></div>';
      }).join('');
    }
    rows += '<div style="display:flex;align-items:center;height:' + (show ? _BP_ROW_H : 40) + 'px;">' +
      '<div class="bpl" style="flex:0 0 ' + _HG_LABW + ';box-sizing:border-box;padding-right:8px;text-align:right;font-size:0.75rem;line-height:1.15;color:var(--muted,#475569)' +
      ';overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;">' + _esc(u[0]) + '</div>' +
      '<div class="bpp" style="position:relative;flex:1 1 auto;min-width:0;height:100%;">' + grid +
      '<div class="bpg" data-cb="node" data-key="' + _esc(u[0]) + '" style="position:absolute;inset:0;' + _ifK(k, n) + _IF_FADE + '">' + strip +
      '<div class="bpw" style="position:absolute;left:' + pos(s.lo) + ';width:' + wid(s.lo, s.hi) + ';top:50%;border-top:1.5px solid var(--muted,#475569);"></div>' +
      '<div style="position:absolute;left:' + pos(s.lo) + ';top:32%;height:36%;border-left:1.5px solid var(--muted,#475569);"></div>' +
      '<div style="position:absolute;left:' + pos(s.hi) + ';top:32%;height:36%;border-left:1.5px solid var(--muted,#475569);transform:translateX(-1.5px);"></div>' +
      '<div class="bpb" style="position:absolute;left:' + pos(s.q1) + ';width:' + wid(s.q1, s.q3) + ';top:22%;height:56%;min-width:2px;box-sizing:border-box;border:1.5px solid var(--accent,#0369A1);background:' + (show ? 'transparent' : 'var(--surface,#F8FAFC)') + ';border-radius:2px;"></div>' +
      '<div class="bpm" style="position:absolute;left:' + pos(med) + ';top:22%;height:56%;border-left:3px solid var(--accent,#0369A1);transform:translateX(-1.5px);"></div>' +
      dots + '</div></div></div>';
  });
  var no = function(c) { return c + (c === 1 ? ' outlier' : ' outliers'); };
  var aria = 'Box plot of ' + n + (n === 1 ? ' group' : ' groups') + ' on a shared axis from ' + _hgNum(X0, td) + ' to ' + _hgNum(X1, td) + us + '. ' +
    used.map(function(u, k) { var s = stats[k]; return u[0] + ': median ' + f(s.median) + us + ', middle half ' + f(s.q1) + ' to ' + f(s.q3) + us + ', whiskers ' + f(s.lo) + ' to ' + f(s.hi) + us + ', ' + no(s.outliers.length); }).join('; ') + '.' + (show ? ' Dots show every value.' : '');
  var chart = '<div class="ifbp" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>@container (max-width:560px){.ifbp .hgx:not(.hgc){display:none}}</style>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;margin:0 34px 34px 0;">' + rows +
    '<div style="position:relative;margin-left:' + _HG_LABW + ';height:0;border-top:1px solid var(--muted,#475569);">' + _hgAxis(ticks, X0, span, tlab) + '</div></div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 34px 0 ' + _HG_LABW + ';">' + _esc(cap) + '</div>' : '') + '</div>';
  return _ifWrap(_ifTitle(b) + chart + notes + capped + _hgVersionNote(b, 'box_plot') +
    _ifTable(['Group', 'Count', 'Minimum', 'Lower quartile', 'Median', 'Upper quartile', 'Maximum', 'Outliers'],
      used.map(function(u, k) { var s = stats[k]; return [u[0], String(s.n), f(s.min) + us, f(s.q1) + us, f(s.median) + us, f(s.q3) + us, f(s.max) + us, String(s.outliers.length)]; })));
};

// ── ternary_plot and quiver (Plotly wave A, package ternary-quiver) ── the twin of _render_ternary_plot / _render_quiver in renderers/web_article.py.
// Plain trigonometry on top of d3-scale's linear scale: the axis is nice(min, max, 5) and ticks(5), a value is placed by d3's normalize then
// interpolateNumber, a*(1-t) + b*t. A ternary point is normalised to shares that sum to 1 and sits at x = c + a/2, y = 1 - a (fractions of the triangle box).
var _TP_VB_H = 866, _QV_W = 1000, _QV_H = 620, _QV_INSET = 65, _QV_LMAX = 120, _QV_MAX = 200;
var _QV_COS = 0.9063077870366499, _QV_SIN = 0.42261826174069944;     // cos and sin of 25 degrees: the arrowhead's barbs
function _qvAxis(vals) {
  var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), d = _hgNice(lo, hi, 5);
  return [d, _hgTicks(d[0], d[1], 5)];
}
function _qvPlace(v, dom, r0, r1) {
  var span = dom[1] - dom[0], t = span ? (v - dom[0]) / span : 0.5;
  return r0 * (1 - t) + r1 * t;
}
function _qvNum(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12; }
function _qvText(v, mx, d) { var s = typeof v === 'string' ? v : (typeof v === 'number' && isFinite(v) ? String(v) : ''); return s ? s.slice(0, mx) : d; }
function _qvC(f) { return Math.min(1, Math.max(0, f)); }
function _qvF(v) { return _hgNum(v, Math.min(_hgDecimals([v]), 3)); }
function _qv2(x) { var s = x.toFixed(2); return s === '-0.00' ? '0.00' : s; }
function _qvNote(lst, cap, leftOut, noun) {
  var beyond = lst.length - cap;
  return (leftOut ? _hgNote(leftOut + (leftOut === 1 ? ' ' + noun + ' was not a usable ' + noun + ' and was' : ' ' + noun + 's were not a usable ' + noun + ' and were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + (beyond === 1 ? ' ' + noun + ' beyond the first ' + cap + ' was' : ' ' + noun + 's beyond the first ' + cap + ' were') + ' not drawn.') : '');
}
_RENDERERS['ternary_plot'] = function(b) {
  var lst = Array.isArray(b.points) ? b.points : [], used = [], leftOut = 0;
  lst.slice(0, _QV_MAX).forEach(function(p, k) {
    if (!(p && typeof p === 'object' && !Array.isArray(p)) || !(_qvNum(p.a) && p.a >= 0 && _qvNum(p.b) && p.b >= 0 && _qvNum(p.c) && p.c >= 0)) { leftOut++; return; }
    var s = p.a + p.b + p.c;
    if (!(s > 0)) { leftOut++; return; }
    used.push([_qvText(p.label, 30, 'Point ' + (k + 1)), p.a / s, p.b / s, p.c / s]);
  });
  var notes = _qvNote(lst, _QV_MAX, leftOut, 'point'), ver = _hgVersionNote(b, 'ternary_plot');
  if (!used.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A ternary plot needs at least one point with three non-negative numbers.</div>' + notes + ver);
  var names = [_qvText(b.a_label, 20, 'A'), _qvText(b.b_label, 20, 'B'), _qvText(b.c_label, 20, 'C')], n = used.length;
  var pct = [];
  used.forEach(function(u) { pct.push(u[1] * 100, u[2] * 100, u[3] * 100); });
  var d = Math.min(_hgDecimals(pct), 2), mean = [], i;
  for (i = 1; i <= 3; i++) { var tot = 0; used.forEach(function(u) { tot += u[i]; }); mean.push(tot / n * 100); }
  var aria = 'Ternary plot of ' + n + (n === 1 ? ' point' : ' points') + '. ' + names[0] + ', ' + names[1] + ' and ' + names[2] + ' shares sum to 100%. Average: ' +
    [0, 1, 2].map(function(j) { return names[j] + ' ' + _hgNum(mean[j], 1) + '%'; }).join(', ') + '.';
  var ticks = _hgTicks(0, 1, 5).filter(function(t) { return t > 0 && t < 1; });
  var xy = function(fa, fb, fc) { return [_qvC(fc + fa / 2), _qvC(1 - fa)]; };
  var svg = '';
  ticks.forEach(function(t) {
    [[[t, 1 - t, 0], [t, 0, 1 - t]], [[1 - t, t, 0], [0, t, 1 - t]], [[1 - t, 0, t], [0, 1 - t, t]]].forEach(function(pp) {
      var p1 = xy(pp[0][0], pp[0][1], pp[0][2]), p2 = xy(pp[1][0], pp[1][1], pp[1][2]);
      svg += '<line class="tpg" x1="' + _qv2(p1[0] * 1000) + '" y1="' + _qv2(p1[1] * _TP_VB_H) + '" x2="' + _qv2(p2[0] * 1000) + '" y2="' + _qv2(p2[1] * _TP_VB_H) +
        '" stroke="var(--border,#CBD5E1)" stroke-width="1" vector-effect="non-scaling-stroke"/>';
    });
  });
  var line = '';
  if (b.connect === true && n > 1) {
    line = '<polyline class="tpl" fill="none" stroke="var(--accent,#0369A1)" stroke-width="1.5" stroke-dasharray="5 4" vector-effect="non-scaling-stroke" points="' +
      used.map(function(u) { var q = xy(u[1], u[2], u[3]); return _qv2(q[0] * 1000) + ',' + _qv2(q[1] * _TP_VB_H); }).join(' ') + '"/>';
  }
  var tri = '<polygon points="500,0 0,' + _TP_VB_H + ' 1000,' + _TP_VB_H + '" fill="var(--surface,#F8FAFC)" stroke="var(--muted,#475569)" stroke-width="1.5" vector-effect="non-scaling-stroke"/>';
  var dots = used.map(function(u, k) {
    var q = xy(u[1], u[2], u[3]);
    return '<div class="tpd" data-cb="node" data-key="' + _esc(u[0]) + '" style="position:absolute;left:' + _tmPct(q[0], 1) + ';top:' + _tmPct(q[1], 1) + ';width:10px;height:10px;box-sizing:border-box;border-radius:50%;' +
      'border:1.5px solid var(--bg,#fff);background:var(--accent,#0369A1);transform:translate(-50%,-50%);' + _ifK(k, n) + 'opacity:var(--k,1);"></div>';
  }).join('');
  var tl = 'position:absolute;font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);', labs = '';
  ticks.forEach(function(t) {
    var lab = _hgNum(t * 100, 0) + '%', pa = xy(t, 1 - t, 0), pb = xy(0, t, 1 - t), pc = xy(1 - t, 0, t);
    labs += '<div class="tpt" style="' + tl + 'left:' + _tmPct(pa[0], 1) + ';top:' + _tmPct(pa[1], 1) + ';transform:translate(calc(-100% - 6px),-50%);">' + lab + '</div>' +
      '<div class="tpt" style="' + tl + 'left:' + _tmPct(pb[0], 1) + ';top:' + _tmPct(pb[1], 1) + ';transform:translate(-50%,6px);">' + lab + '</div>' +
      '<div class="tpt" style="' + tl + 'left:' + _tmPct(pc[0], 1) + ';top:' + _tmPct(pc[1], 1) + ';transform:translate(6px,-50%);">' + lab + '</div>';
  });
  var vl = 'font-size:0.8rem;font-weight:700;line-height:1.2;overflow-wrap:anywhere;';
  var chart = '<div class="iftp" style="container-type:inline-size;max-width:100%;overflow:hidden;">' +
    '<div role="img" aria-label="' + _esc(aria) + '">' +
    '<div class="tpv" style="' + vl + 'text-align:center;margin:0 0 14px;">' + _esc(names[0]) + '</div>' +
    '<div style="margin:0 52px;"><div class="tpp" style="position:relative;width:100%;aspect-ratio:1000/' + _TP_VB_H + ';">' +
    '<svg aria-hidden="true" viewBox="0 0 1000 ' + _TP_VB_H + '" preserveAspectRatio="none" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible;">' +
    tri + svg + line + '</svg>' + dots + labs + '</div></div>' +
    '<div style="display:flex;justify-content:space-between;gap:8px;margin:30px 0 0;">' +
    '<div class="tpv" style="' + vl + 'max-width:45%;">' + _esc(names[1]) + '</div><div class="tpv" style="' + vl + 'max-width:45%;text-align:right;">' + _esc(names[2]) + '</div></div></div></div>';
  var hint = _hgNote('Gridlines every 20%: ' + _esc(names[0]) + ' counts up the left edge, ' + _esc(names[1]) + ' along the bottom edge towards the left, ' + _esc(names[2]) + ' counts down the right edge towards its corner.');
  return _ifWrap(_ifTitle(b) + chart + hint + notes + ver +
    _ifTable(['Point'].concat(names), used.map(function(u) { return [u[0], _hgNum(u[1] * 100, d) + '%', _hgNum(u[2] * 100, d) + '%', _hgNum(u[3] * 100, d) + '%']; })));
};
_RENDERERS['quiver'] = function(b) {
  var lst = Array.isArray(b.arrows) ? b.arrows : [], used = [], leftOut = 0;
  lst.slice(0, _QV_MAX).forEach(function(p, k) {
    if (!(p && typeof p === 'object' && !Array.isArray(p)) || !(_qvNum(p.x) && _qvNum(p.y) && _qvNum(p.u) && _qvNum(p.v))) { leftOut++; return; }
    used.push([_qvText(p.label, 30, 'Arrow ' + (k + 1)), p.x, p.y, p.u, p.v, Math.sqrt(p.u * p.u + p.v * p.v)]);
  });
  var notes = _qvNote(lst, _QV_MAX, leftOut, 'arrow'), ver = _hgVersionNote(b, 'quiver');
  if (!used.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A quiver plot needs at least one arrow with x, y, u and v numbers.</div>' + notes + ver);
  var n = used.length, unit = _qvText(b.unit, 12, ''), us = unit ? ' ' + unit : '', xn = _qvText(b.x_label, 40, 'x'), yn = _qvText(b.y_label, 40, 'y');
  var ax = _qvAxis(used.map(function(a) { return a[1]; })), ay = _qvAxis(used.map(function(a) { return a[2]; }));
  var X0 = ax[0][0], X1 = ax[0][1], xt = ax[1], Y0 = ay[0][0], Y1 = ay[0][1], yt = ay[1];
  var sc = (typeof b.arrow_scale === 'number' && _qvNum(b.arrow_scale)) ? Math.min(1, Math.max(0.1, b.arrow_scale)) : 1;
  var big = 0;
  used.forEach(function(a) { if (a[5] > big) big = a[5]; });
  var R = _QV_W - _QV_INSET, B = _QV_H - _QV_INSET;
  var px = function(v) { return _qvPlace(v, [X0, X1], _QV_INSET, R); }, py = function(v) { return _qvPlace(v, [Y0, Y1], B, _QV_INSET); };
  var grid = xt.map(function(t) { return '<line class="qvg" x1="' + _qv2(px(t)) + '" y1="0" x2="' + _qv2(px(t)) + '" y2="' + _QV_H + '" stroke="var(--border,#CBD5E1)" stroke-width="1" vector-effect="non-scaling-stroke"/>'; }).join('') +
    yt.map(function(t) { return '<line class="qvg" x1="0" y1="' + _qv2(py(t)) + '" x2="' + _QV_W + '" y2="' + _qv2(py(t)) + '" stroke="var(--border,#CBD5E1)" stroke-width="1" vector-effect="non-scaling-stroke"/>'; }).join('');
  var marks = used.map(function(a, k) {
    var cx = px(a[1]), cy = py(a[2]), mag = a[5], st = _ifK(k, n) + 'opacity:var(--k,1);';
    if (!(mag > 0 && big > 0)) return '<circle class="qvz" data-cb="node" data-key="' + (k + 1) + '" cx="' + _qv2(cx) + '" cy="' + _qv2(cy) + '" r="5" fill="var(--accent,#0369A1)" style="' + st + '"/>';
    var ln = _QV_LMAX * sc * mag / big, dx = a[3] / mag, dy = -a[4] / mag;
    var x0 = cx - 0.5 * ln * dx, y0 = cy - 0.5 * ln * dy, x1 = cx + 0.5 * ln * dx, y1 = cy + 0.5 * ln * dy, hl = Math.min(0.35 * ln, 28);
    var b1x = x1 - hl * (dx * _QV_COS - dy * _QV_SIN), b1y = y1 - hl * (dx * _QV_SIN + dy * _QV_COS);
    var b2x = x1 - hl * (dx * _QV_COS + dy * _QV_SIN), b2y = y1 - hl * (-dx * _QV_SIN + dy * _QV_COS);
    return '<path class="qva" data-cb="node" data-key="' + (k + 1) + '" d="M' + _qv2(x0) + ' ' + _qv2(y0) + 'L' + _qv2(x1) + ' ' + _qv2(y1) + 'M' + _qv2(b1x) + ' ' + _qv2(b1y) + 'L' + _qv2(x1) + ' ' + _qv2(y1) + 'L' + _qv2(b2x) + ' ' + _qv2(b2y) +
      '" fill="none" stroke="var(--accent,#0369A1)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="' + st + '"/>';
  }).join('');
  var tl = 'position:absolute;font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);';
  var xd = _hgDecimals(xt), yd = _hgDecimals(yt), xl = xt.map(function(t) { return _hgNum(t, xd); });
  var stride = Math.ceil(xt.length / Math.max(2, Math.min(8, Math.floor(48 / Math.max.apply(null, xl.map(function(s) { return s.length; })))))), xlabs = '';
  xt.forEach(function(t, i) {
    if (i % stride === 0) xlabs += '<div class="qvx' + (i % (2 * stride) === 0 ? ' qvc' : '') + '" style="' + tl + 'top:100%;margin-top:6px;left:' + _tmPct(px(t), _QV_W) + ';transform:translateX(-50%);">' + xl[i] + '</div>';
  });
  var ylabs = yt.map(function(t) { return '<div class="qvy" style="' + tl + 'left:0;margin-left:-6px;top:' + _tmPct(py(t), _QV_H) + ';transform:translate(-100%,-50%);">' + _hgNum(t, yd) + '</div>'; }).join('');
  var xe = _hgDecimals([X0, X1]), ye = _hgDecimals([Y0, Y1]), lg = used[0];
  used.forEach(function(a) { if (a[5] > lg[5]) lg = a; });
  var aria = 'Quiver plot of ' + n + (n === 1 ? ' arrow' : ' arrows') + ', ' + xn + ' ' + _hgNum(X0, xe) + ' to ' + _hgNum(X1, xe) + ', ' + yn + ' ' + _hgNum(Y0, ye) + ' to ' + _hgNum(Y1, ye) + '. ' +
    (big > 0 ? 'Longest arrow: ' + lg[0] + ' at (' + _qvF(lg[1]) + ', ' + _qvF(lg[2]) + '), across ' + _qvF(lg[3]) + us + ', up ' + _qvF(lg[4]) + us + ', length ' + _qvF(lg[5]) + us + '.' : 'Every arrow has length 0.');
  var cap = _hgNote('Each arrow is centred on its point and points the way its across and up numbers say; lengths are in proportion to the vector length' + (unit ? ' (' + _esc(unit) + ')' : '') + ', the longest drawn at a fixed size.');
  var chart = '<div class="ifqv" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>@container (max-width:560px){.ifqv .qvx:not(.qvc){display:none}}</style>' +
    '<div style="font-size:0.78rem;color:var(--muted,#475569);margin:0 0 6px 4px;">' + _esc(yn) + ' (up)</div>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="margin:0 12px 38px 56px;"><div class="qvp" style="position:relative;width:100%;aspect-ratio:' + _QV_W + '/' + _QV_H + ';">' +
    '<svg aria-hidden="true" viewBox="0 0 ' + _QV_W + ' ' + _QV_H + '" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible;">' +
    '<rect x="0" y="0" width="' + _QV_W + '" height="' + _QV_H + '" fill="var(--surface,#F8FAFC)" stroke="var(--muted,#475569)" stroke-width="1.5" vector-effect="non-scaling-stroke"/>' +
    grid + marks + '</svg>' + xlabs + ylabs + '</div></div>' +
    '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);margin:0 12px 0 56px;">' + _esc(xn) + ' (across)</div></div>';
  return _ifWrap(_ifTitle(b) + chart + cap + notes + ver +
    _ifTable(['Arrow', xn, yn, 'Across', 'Up', 'Length'], used.map(function(a) { return [a[0], _qvF(a[1]), _qvF(a[2]), _qvF(a[3]) + us, _qvF(a[4]) + us, _qvF(a[5]) + us]; })));
};


// ── box_plot options (plotly wave B, d3-variants): quartile_method, show_mean, orientation, notches, stats, shape 'violin' ──
// Twin of _bp_quartiles / _bp_kde / _render_box_plot_opts in renderers/web_article.py (see the comment there for the maths).
var _BPO_KEYS = ['quartile_method', 'show_mean', 'orientation', 'notches', 'shape', 'bandwidth'], _BPO_GRID = 41;
function _bpMedian(a) { var n = a.length; return n % 2 ? a[(n - 1) / 2] : (a[n / 2 - 1] + a[n / 2]) / 2; }
function _bpQuartiles(a, method) {
  var n = a.length, h, odd;
  if (method === 'exclusive' || method === 'inclusive') { h = Math.floor(n / 2); odd = method === 'inclusive' ? n % 2 : 0; return [_bpMedian(a.slice(0, h + odd)), _bpMedian(a), _bpMedian(a.slice(n - h - odd))]; }
  return [_bpQuantile(a, 0.25), _bpQuantile(a, 0.5), _bpQuantile(a, 0.75)];
}
function _bpSd(a) { var cnt = 0, mean = 0, tot = 0, i, d; for (i = 0; i < a.length; i++) { cnt++; d = a[i] - mean; mean += d / cnt; tot += d * (a[i] - mean); } return cnt > 1 ? Math.sqrt(tot / (cnt - 1)) : 0; }  // d3.deviation (Welford)
function _bpKde(a, q1, q3, bw) {
  var n = a.length, out = [], j, i, x, t, u;
  if (!(typeof bw === 'number' && isFinite(bw) && bw > 0 && bw <= 1e12)) { bw = 0.9 * Math.min(_bpSd(a), (q3 - q1) / 1.34) * Math.pow(n, -0.2); if (!(bw > 0)) bw = (a[n - 1] - a[0]) / 10 || 1; }
  var flr = ((a[n - 1] - a[0]) || 1) * 1e-6, clamped = bw < flr;   // below this the kernel is a spike the 41-point grid cannot show (and 1 / bw overflows to NaN)
  if (clamped) bw = flr;
  for (j = 0; j < _BPO_GRID; j++) { x = a[0] + (a[n - 1] - a[0]) * j / (_BPO_GRID - 1); t = 0; for (i = 0; i < n; i++) { u = (x - a[i]) / bw; t += 0.3989422804014327 * Math.exp(-0.5 * u * u) / bw; } out.push([x, t / n]); }
  return [out, bw, clamped];
}
function _bpOptStats(a, method) {
  var qs = _bpQuartiles(a, method), q1 = qs[0], q3 = qs[2], r = 1.5 * (q3 - q1), inside = a.filter(function(x) { return q1 - r <= x && x <= q3 + r; }), t = 0, i;
  for (i = 0; i < a.length; i++) t += a[i];
  return { n: a.length, min: a[0], q1: q1, median: qs[1], q3: q3, max: a[a.length - 1], lo: inside[0], hi: inside[inside.length - 1], mean: t / a.length, outliers: a.filter(function(x) { return x < q1 - r || x > q3 + r; }), vals: a };
}
function _bpOptsGiven(b) {   // an option set to something other than its default, or a group with stats
  var dflt = function(k, d) { return b[k] !== undefined && b[k] !== null && d.indexOf(b[k]) < 0; };
  return dflt('quartile_method', ['linear']) || b.show_mean === true || b.notches === true || dflt('orientation', ['h', 'horizontal']) || dflt('shape', ['box']) || (Array.isArray(b.groups) && b.groups.some(function(g) { return g && typeof g === 'object' && g.stats && typeof g.stats === 'object' && !Array.isArray(g.stats); }));
}
function _bpRenderOpts(b) {
  var method = _hgIn(b.quartile_method, { linear: 1, exclusive: 1, inclusive: 1 }) ? b.quartile_method : 'linear', vert = b.orientation === 'v' || b.orientation === 'vertical', violin = b.shape === 'violin', notch = b.notches === true, meanOn = b.show_mean === true;
  var ignored = [];
  if (b.quartile_method !== undefined && method !== b.quartile_method) ignored.push('quartile_method');
  if (b.orientation !== undefined && ['h', 'horizontal', 'v', 'vertical'].indexOf(b.orientation) < 0) ignored.push('orientation');
  if (b.shape !== undefined && b.shape !== 'box' && b.shape !== 'violin') ignored.push('shape');
  var lst = Array.isArray(b.groups) ? b.groups : [], used = [], skipped = 0, leftOut = 0, nonotch = 0, k, i;
  lst.slice(0, 12).forEach(function(g, kk) {
    if (!g || typeof g !== 'object' || Array.isArray(g)) { leftOut++; return; }
    var nm = g.label ? String(g.label).slice(0, 30) : 'Group ' + (kk + 1), st = g.stats;
    if (st && typeof st === 'object' && !Array.isArray(st)) {
      var q = [st.q1, st.median, st.q3];
      if (!q.every(_hgFinite) || !(q[0] <= q[1] && q[1] <= q[2])) { leftOut++; return; }
      var opt = function(key, d) { return _hgFinite(st[key]) ? st[key] : d; }, mn = opt('min', null), mx = opt('max', null), lo = opt('lo', mn !== null ? mn : q[0]), hi = opt('hi', mx !== null ? mx : q[2]);
      used.push([nm, { n: _hgFinite(st.n) && st.n >= 1 && st.n === Math.floor(st.n) ? st.n : null, min: mn, q1: q[0], median: q[1], q3: q[2], max: mx, lo: Math.min(lo, q[0]), hi: Math.max(hi, q[2]), mean: opt('mean', null), outliers: [], vals: null }]);
      return;
    }
    var raw = _ifArr(g.values, 2000), vals = _hgUsable(raw);
    skipped += raw.length - vals.length;
    if (vals.length < 5) { leftOut++; return; }
    used.push([nm, _bpOptStats(vals.slice().sort(function(x, y) { return x - y; }), method)]);
  });
  var beyond = lst.length - 12;
  var notes = _hgSkipNote(skipped) + (leftOut ? _hgNote(leftOut + (leftOut === 1 ? ' group had fewer than 5 usable numbers, no usable stats or was not a group and was' : ' groups had fewer than 5 usable numbers, no usable stats or were not a group and were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + (beyond === 1 ? ' group beyond the first 12 was' : ' groups beyond the first 12 were') + ' not drawn.') : '');
  if (b.show_points === true) notes += _hgNote('show_points is not drawn together with these options.');
  if (!used.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A box plot needs at least one group with 5 numbers or with q1, median and q3.</div>' + notes + _hgVersionNote(b, 'box_plot'));
  var n = used.length, bwc = false, kdes = used.map(function(u) { if (!(violin && u[1].vals)) return null; var kd = _bpKde(u[1].vals, u[1].q1, u[1].q3, b.bandwidth); bwc = bwc || kd[2]; return kd[0]; });
  if (bwc) notes += _hgNote('The bandwidth was too small to draw a smooth shape and was raised.');
  if (violin && kdes.some(function(x) { return x === null; })) notes += _hgNote('A violin needs the values; groups given as stats are drawn as boxes.');
  var allv = [];
  used.forEach(function(u) { var s = u[1]; allv.push(s.lo, s.hi, s.q1, s.q3); s.outliers.forEach(function(o) { allv.push(o); }); if (s.min !== null) allv.push(s.min); if (s.max !== null) allv.push(s.max); if (meanOn && s.mean !== null) allv.push(s.mean); });
  var nz = _hgNice(Math.min.apply(null, allv), Math.max.apply(null, allv), 5), X0 = nz[0], X1 = nz[1], ticks = _hgTicks(X0, X1, 5), span = X1 - X0, td = _hgDecimals(ticks), tlab = ticks.map(function(t) { return _hgNum(t, td); });
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '', xl = b.x_label ? String(b.x_label).slice(0, 40) : '', cap = xl ? xl + (unit ? ' (' + unit + ')' : '') : unit;
  var fv = []; used.forEach(function(u) { (u[1].vals || [u[1].q1, u[1].median, u[1].q3, u[1].lo, u[1].hi]).forEach(function(x) { fv.push(x); }); });
  var fc = Math.min(_hgDecimals(fv) + 2, td + 3);
  function f(v) { return _bpFmt(v, fc); }
  function al(v) { return span > 0 ? (v - X0) / span * 1000 : 500; }
  function pt(v, c) { return vert ? c.toFixed(2) + ',' + (1000 - al(v)).toFixed(2) : al(v).toFixed(2) + ',' + c.toFixed(2); }
  function at(v, c) { return vert ? 'left:' + (c / 10).toFixed(3) + '%;top:' + (100 - al(v) / 10).toFixed(3) + '%;' : 'left:' + (al(v) / 10).toFixed(3) + '%;top:' + (c / 10).toFixed(3) + '%;'; }
  function line(v0, c0, v1, c1) { var a = pt(v0, c0).split(','), c = pt(v1, c1).split(','); return '<line x1="' + a[0] + '" y1="' + a[1] + '" x2="' + c[0] + '" y2="' + c[1] + '"/>'; }
  var hw = 1000 / n * 0.25, shapes = '', dots = '', gused = Object.create(null);
  used.forEach(function(u, kk) {
    var nm = u[0], s = u[1], kd = kdes[kk], cc = (kk + 0.5) / n * 1000, h2 = kd ? hw * 0.32 : hw, pts = null, dm, side, m, half, nlo, nhi, outl;
    s.notch = null;
    shapes += '<g data-cb="node" data-key="' + _ifUkey(nm, gused) + '">';
    if (kd) {
      dm = Math.max.apply(null, kd.map(function(p) { return p[1]; }));
      side = kd.map(function(p) { return [p[0], cc - p[1] / dm * hw * 1.7]; }).concat(kd.slice().reverse().map(function(p) { return [p[0], cc + p[1] / dm * hw * 1.7]; }));
      shapes += '<polygon class="bpv" points="' + side.map(function(p) { return pt(p[0], p[1]); }).join(' ') + '"/>';
    }
    if (notch && s.n) {
      half = 1.57 * (s.q3 - s.q1) / Math.sqrt(s.n); nlo = Math.max(s.q1, s.median - half); nhi = Math.min(s.q3, s.median + half); m = s.median;
      if (s.median - half < s.q1 || s.median + half > s.q3) notes += _hgNote('The notch of ' + _esc(nm) + ' reaches past the quartiles and is cut at them.');
      s.notch = [nlo, nhi];
      pts = [[s.q1, cc - h2], [nlo, cc - h2], [m, cc - h2 * 0.5], [nhi, cc - h2], [s.q3, cc - h2], [s.q3, cc + h2], [nhi, cc + h2], [m, cc + h2 * 0.5], [nlo, cc + h2], [s.q1, cc + h2]];
    } else if (notch) nonotch++;
    if (!pts) pts = [[s.q1, cc - h2], [s.q3, cc - h2], [s.q3, cc + h2], [s.q1, cc + h2]];
    var m1 = pt(s.median, cc - h2).split(','), m2 = pt(s.median, cc + h2).split(',');
    shapes += line(s.lo, cc, s.q1, cc) + line(s.q3, cc, s.hi, cc) + line(s.lo, cc - h2 / 2, s.lo, cc + h2 / 2) + line(s.hi, cc - h2 / 2, s.hi, cc + h2 / 2) +
      '<polygon class="bpq' + (kd ? ' bpt' : '') + '" points="' + pts.map(function(p) { return pt(p[0], p[1]); }).join(' ') + '"/>' + '<line class="bpm" x1="' + m1[0] + '" y1="' + m1[1] + '" x2="' + m2[0] + '" y2="' + m2[1] + '"/></g>';
    var dist = s.outliers.filter(function(v, j, arr) { return arr.indexOf(v) === j; }).sort(function(p, q) { var da = -Math.abs(p - s.median), db = -Math.abs(q - s.median); return da !== db ? da - db : p - q; });
    dist.slice(0, _BP_MAX_DOTS).forEach(function(o) { dots += '<div class="bpo" style="position:absolute;' + at(o, cc) + 'width:7px;height:7px;box-sizing:border-box;border-radius:50%;border:1.5px solid var(--accent,#0369A1);background:var(--bg,#fff);transform:translate(-50%,-50%);"></div>'; });
    if (dist.length > _BP_MAX_DOTS) notes += _hgNote(_esc(nm) + ' has ' + dist.length + ' distinct outliers; the ' + _BP_MAX_DOTS + ' furthest from the median are drawn. The table counts them all.');
    if (meanOn && s.mean !== null) dots += '<div class="bpa" style="position:absolute;' + at(s.mean, cc) + 'width:9px;height:9px;box-sizing:border-box;background:var(--text,#0F172A);border:1.5px solid var(--bg,#fff);transform:translate(-50%,-50%) rotate(45deg);"></div>';
  });
  if (nonotch) notes += _hgNote('Notches need the group size n; ' + nonotch + (nonotch === 1 ? ' group has' : ' groups have') + ' none and ' + (nonotch === 1 ? 'is' : 'are') + ' drawn without.');
  if (ignored.length) notes += _hgNote('Not understood and ignored: ' + _esc(ignored.join(', ')) + '.');
  var grid = ticks.map(function(t) { return '<div style="position:absolute;' + (vert ? 'left:0;right:0;bottom:' + (al(t) / 10).toFixed(3) + '%;border-top' : 'top:0;bottom:0;left:' + (al(t) / 10).toFixed(3) + '%;border-left') + ':1px solid var(--border,#CBD5E1);"></div>'; }).join('');
  var labS = 'font-size:0.75rem;line-height:1.15;color:var(--muted,#475569);', body;
  var svg = '<svg viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true" focusable="false" class="bps" style="position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible;">' + shapes + '</svg>';
  if (vert) {
    var yax = ticks.map(function(t, j) { return '<div style="position:absolute;right:100%;margin-right:6px;bottom:' + (al(t) / 10).toFixed(3) + '%;transform:translateY(50%);' + labS + 'white-space:nowrap;line-height:1;">' + tlab[j] + '</div>'; }).join('');
    var names = '<div style="display:flex;margin-top:6px;">' + used.map(function(u, j) { return '<div style="flex:1 1 0;min-width:0;text-align:center;' + labS + 'overflow-wrap:anywhere;"><span class="bpf">' + _esc(u[0]) + '</span><span class="bpn">' + (j + 1) + '</span></div>'; }).join('') + '</div>';
    var key = '<div class="bpk" style="' + labS + 'margin-top:6px;">' + _esc(used.map(function(u, j) { return (j + 1) + ' ' + u[0]; }).join('; ')) + '</div>';
    body = '<div style="position:relative;margin:8px 0 0 46px;"><div style="position:relative;height:260px;">' + grid + svg + dots + yax + '</div>' + names + key + '</div>';
  } else {
    var nm2 = used.map(function(u, j) { return '<div style="position:absolute;right:0;top:' + ((j + 0.5) / n * 100).toFixed(3) + '%;transform:translateY(-50%);box-sizing:border-box;padding-right:8px;text-align:right;' + labS + 'overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2;overflow:hidden;max-width:100%;">' + _esc(u[0]) + '</div>'; }).join('');
    var hpx = n * (violin ? 84 : 52);
    body = '<div style="display:flex;"><div style="flex:0 0 ' + _HG_LABW + ';position:relative;height:' + hpx + 'px;">' + nm2 + '</div><div style="position:relative;flex:1 1 auto;min-width:0;height:' + hpx + 'px;margin-right:34px;">' + grid + svg + dots +
      '<div style="position:absolute;left:0;right:0;top:100%;border-top:1px solid var(--muted,#475569);">' + _hgAxis(ticks, X0, span, tlab) + '</div></div></div>';
  }
  var css = '<style>.ifbp .bps *{vector-effect:non-scaling-stroke}.ifbp .bps line,.ifbp .bps polygon{stroke:var(--muted,#475569);stroke-width:1.5px;fill:none}.ifbp .bpq{fill:var(--surface,#F8FAFC);stroke:var(--accent,#0369A1)}' +
    '.ifbp .bpt{fill:none}.ifbp .bpv{fill:var(--surface,#F8FAFC);stroke:var(--accent,#0369A1)}.ifbp .bps .bpm{stroke:var(--accent,#0369A1);stroke-width:3px}.ifbp .bpn,.ifbp .bpk{display:none}' +
    '@container (max-width:560px){.ifbp .hgx:not(.hgc){display:none}.ifbp .bpf{display:none}.ifbp .bpn,.ifbp .bpk{display:inline}.ifbp .bpk{display:block}}</style>';
  var no = function(c) { return c + (c === 1 ? ' outlier' : ' outliers'); };
  var aria = 'Box plot of ' + n + (n === 1 ? ' group' : ' groups') + ' on a shared ' + (vert ? 'vertical' : 'horizontal') + ' axis from ' + _hgNum(X0, td) + ' to ' + _hgNum(X1, td) + us + '. ' +
    used.map(function(u) { var s = u[1]; return u[0] + ': median ' + f(s.median) + us + ', middle half ' + f(s.q1) + ' to ' + f(s.q3) + us + ', whiskers ' + f(s.lo) + ' to ' + f(s.hi) + us + ', ' + no(s.outliers.length) + (meanOn && s.mean !== null ? ', mean ' + f(s.mean) + us : ''); }).join('; ') +
    '.' + (violin ? ' Violin outlines show the estimated density.' : '') + (method !== 'linear' ? ' Quartiles by the ' + method + ' method.' : '');
  var chart = '<div class="ifbp" style="container-type:inline-size;max-width:100%;overflow:hidden;">' + css + '<div role="img" aria-label="' + _esc(aria) + '" style="margin:0 0 34px 0;' + _IF_FADE + '">' + body + '</div>' +
    (cap ? '<div style="text-align:center;font-size:0.78rem;color:var(--muted,#475569);">' + _esc(cap) + '</div>' : '') + '</div>';
  var na = function(v) { return v !== null ? f(v) + us : 'n/a'; };
  return _ifWrap(_ifTitle(b) + chart + notes + _hgVersionNote(b, 'box_plot') + _ifTable(['Group', 'Count', 'Minimum', 'Lower quartile', 'Median', 'Upper quartile', 'Maximum', 'Outliers'].concat(meanOn ? ['Mean'] : []).concat(notch ? ['Notch from', 'Notch to'] : []),
    used.map(function(u) { var s = u[1]; return [u[0], s.n ? String(s.n) : 'n/a', na(s.min), f(s.q1) + us, f(s.median) + us, f(s.q3) + us, na(s.max), String(s.outliers.length)].concat(meanOn ? [na(s.mean)] : []).concat(notch ? [s.notch ? na(s.notch[0]) : 'n/a', s.notch ? na(s.notch[1]) : 'n/a'] : []); })));
}
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
      '<div class="wfg" data-cb="node" data-key="' + _esc(labels[k]) + '" style="position:absolute;inset:0;' + _ifK(k, n) + _IF_FADE + '">' +
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


// ─── heatmap variants (additive; twin of the heatmap block in renderers/web_article.py) ───────────────────────────────────────────────
// Plotly's named colour scales, copied from plotly.js src/components/colorscale/scales.js (tests/fixtures/plotly_scales.json holds the original).
var _HM_SCALES = {
  "Greys": [[0, [0, 0, 0]], [1, [255, 255, 255]]],
  "YlGnBu": [[0, [8, 29, 88]], [0.125, [37, 52, 148]], [0.25, [34, 94, 168]], [0.375, [29, 145, 192]], [0.5, [65, 182, 196]], [0.625, [127, 205, 187]], [0.75, [199, 233, 180]], [0.875, [237, 248, 217]], [1, [255, 255, 217]]],
  "Greens": [[0, [0, 68, 27]], [0.125, [0, 109, 44]], [0.25, [35, 139, 69]], [0.375, [65, 171, 93]], [0.5, [116, 196, 118]], [0.625, [161, 217, 155]], [0.75, [199, 233, 192]], [0.875, [229, 245, 224]], [1, [247, 252, 245]]],
  "YlOrRd": [[0, [128, 0, 38]], [0.125, [189, 0, 38]], [0.25, [227, 26, 28]], [0.375, [252, 78, 42]], [0.5, [253, 141, 60]], [0.625, [254, 178, 76]], [0.75, [254, 217, 118]], [0.875, [255, 237, 160]], [1, [255, 255, 204]]],
  "Bluered": [[0, [0, 0, 255]], [1, [255, 0, 0]]],
  "RdBu": [[0, [5, 10, 172]], [0.35, [106, 137, 247]], [0.5, [190, 190, 190]], [0.6, [220, 170, 132]], [0.7, [230, 145, 90]], [1, [178, 10, 28]]],
  "Reds": [[0, [220, 220, 220]], [0.2, [245, 195, 157]], [0.4, [245, 160, 105]], [1, [178, 10, 28]]],
  "Blues": [[0, [5, 10, 172]], [0.35, [40, 60, 190]], [0.5, [70, 100, 245]], [0.6, [90, 120, 245]], [0.7, [106, 137, 247]], [1, [220, 220, 220]]],
  "Picnic": [[0, [0, 0, 255]], [0.1, [51, 153, 255]], [0.2, [102, 204, 255]], [0.3, [153, 204, 255]], [0.4, [204, 204, 255]], [0.5, [255, 255, 255]], [0.6, [255, 204, 255]], [0.7, [255, 153, 255]], [0.8, [255, 102, 204]], [0.9, [255, 102, 102]], [1, [255, 0, 0]]],
  "Rainbow": [[0, [150, 0, 90]], [0.125, [0, 0, 200]], [0.25, [0, 25, 255]], [0.375, [0, 152, 255]], [0.5, [44, 255, 150]], [0.625, [151, 255, 0]], [0.75, [255, 234, 0]], [0.875, [255, 111, 0]], [1, [255, 0, 0]]],
  "Portland": [[0, [12, 51, 131]], [0.25, [10, 136, 186]], [0.5, [242, 211, 56]], [0.75, [242, 143, 56]], [1, [217, 30, 30]]],
  "Jet": [[0, [0, 0, 131]], [0.125, [0, 60, 170]], [0.375, [5, 255, 255]], [0.625, [255, 255, 0]], [0.875, [250, 0, 0]], [1, [128, 0, 0]]],
  "Hot": [[0, [0, 0, 0]], [0.3, [230, 0, 0]], [0.6, [255, 210, 0]], [1, [255, 255, 255]]],
  "Blackbody": [[0, [0, 0, 0]], [0.2, [230, 0, 0]], [0.4, [230, 210, 0]], [0.7, [255, 255, 255]], [1, [160, 200, 255]]],
  "Earth": [[0, [0, 0, 130]], [0.1, [0, 180, 180]], [0.2, [40, 210, 40]], [0.4, [230, 230, 50]], [0.6, [120, 70, 20]], [1, [255, 255, 255]]],
  "Electric": [[0, [0, 0, 0]], [0.15, [30, 0, 100]], [0.4, [120, 0, 100]], [0.6, [160, 90, 0]], [0.8, [230, 200, 0]], [1, [255, 250, 220]]],
  "Viridis": [[0, [68, 1, 84]], [0.06274509803921569, [72, 24, 106]], [0.12549019607843137, [71, 45, 123]], [0.18823529411764706, [66, 64, 134]], [0.25098039215686274, [59, 82, 139]], [0.3137254901960784, [51, 99, 141]], [0.3764705882352941, [44, 114, 142]], [0.4392156862745098, [38, 130, 142]], [0.5019607843137255, [33, 145, 140]], [0.5647058823529412, [31, 160, 136]], [0.6274509803921569, [40, 174, 128]], [0.6901960784313725, [63, 188, 115]], [0.7529411764705882, [94, 201, 98]], [0.8156862745098039, [132, 212, 75]], [0.8784313725490196, [173, 220, 48]], [0.9411764705882353, [216, 226, 25]], [1, [253, 231, 37]]],
  "Cividis": [[0, [0, 32, 76]], [0.058824, [0, 42, 102]], [0.117647, [0, 52, 110]], [0.176471, [39, 63, 108]], [0.235294, [60, 74, 107]], [0.294118, [76, 85, 107]], [0.352941, [91, 95, 109]], [0.411765, [104, 106, 112]], [0.470588, [117, 117, 117]], [0.529412, [131, 129, 120]], [0.588235, [146, 140, 120]], [0.647059, [161, 152, 118]], [0.705882, [176, 165, 114]], [0.764706, [192, 177, 109]], [0.823529, [209, 191, 102]], [0.882353, [225, 204, 92]], [0.941176, [243, 219, 79]], [1, [255, 233, 69]]],
};
var _HM_KEYS = ['z_min', 'z_max', 'z_mid', 'scale', 'show_colorbar', 'show_values', 'value_format', 'version'];
var _HM_CAP = 40;
var _HM_COMPACT = 8;
var _HM_FMT_RE = /^(,)?(?:\.([0-9]))?([f%d])?$/;
function _hmNum(v) { return (typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12) ? v : null; }
function _hmRound(x) { return Math.floor(x + 0.5); }
function _hmFixed(x, d) { var s = Math.abs(x).toFixed(d); return (x < 0 && parseFloat(s) !== 0 ? '-' : '') + s; }
function _hmRgb(st, t) {
  if (typeof st === 'string') st = _HM_SCALES[st];
  t = Math.min(1, Math.max(0, t));
  for (var i = 1; i < st.length; i++) {
    if (t <= st[i][0] || i === st.length - 1) {
      var p0 = st[i - 1][0], c0 = st[i - 1][1], p1 = st[i][0], c1 = st[i][1];
      var f = p1 === p0 ? 0 : Math.min(1, Math.max(0, (t - p0) / (p1 - p0)));
      return [0, 1, 2].map(function(k) { return _hmRound(c0[k] + (c1[k] - c0[k]) * f); });
    }
  }
  return st[0][1];
}
function _hmDomain(vals, zmin, zmax, zmid) {
  var lo = zmin !== null ? zmin : Math.min.apply(null, vals), hi = zmax !== null ? zmax : Math.max.apply(null, vals);
  if (zmid !== null && !(zmin !== null && zmax !== null)) { var d = Math.max(Math.abs(zmid - lo), Math.abs(hi - zmid)); lo = zmid - d; hi = zmid + d; }
  return [lo, hi > lo ? hi : lo + 1];
}
function _hmTrim(s) { return s.indexOf('.') >= 0 ? s.replace(/0+$/, '').replace(/\.$/, '') : s; }
function _hmFmt(x, spec) {
  var m = (typeof spec === 'string' && spec) ? _HM_FMT_RE.exec(spec) : null, s;
  if (!m) return _hmTrim(_hmFixed(x, 2));
  var typ = m[3], d = m[2] ? parseInt(m[2], 10) : ((typ === '%' || typ === 'd') ? 0 : 2);
  if (!typ && !m[2]) s = _hmTrim(_hmFixed(x, 2)); else s = _hmFixed(typ === '%' ? x * 100 : x, d);
  if (m[1]) {
    var neg = s.charAt(0) === '-', parts = s.replace(/^-/, '').split('.'), ip = parts[0], g = '';
    while (ip.length > 3) { g = ',' + ip.slice(-3) + g; ip = ip.slice(0, -3); }
    s = (neg ? '-' : '') + ip + g + (parts.length > 1 && parts[1] ? '.' + parts[1] : '');
  }
  return s + (typ === '%' ? '%' : '');
}
function _hmHexScale(v) {
  if (!Array.isArray(v) || v.length < 2) return null;
  var out = [];
  for (var i = 0; i < Math.min(v.length, 32); i++) {
    var m = typeof v[i] === 'string' ? /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.exec(v[i]) : null;
    if (!m) return null;
    var h = m[1];
    if (h.length === 3) h = h.charAt(0) + h.charAt(0) + h.charAt(1) + h.charAt(1) + h.charAt(2) + h.charAt(2);
    out.push([parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]);
  }
  return out.map(function(c, k) { return [k / (out.length - 1), c]; });
}
function _hmLab(v) {
  if (typeof v === 'string') return v || null;
  if (typeof v === 'number' && isFinite(v) && v !== 0) return String(v);
  return null;
}
function _hmPivot(raw) {
  if (!(Array.isArray(raw) && raw.length && raw.every(function(x) { return x && typeof x === 'object' && !Array.isArray(x); }) && raw.some(function(x) { return Object.prototype.hasOwnProperty.call(x, 'value'); }))) return null;
  var ry = [], cx = [], cell = {};
  raw.forEach(function(x) {
    var r = _hmLab(x.row), c = _hmLab(x.col);
    if (r === null || c === null) return;
    if (ry.indexOf(r) < 0) ry.push(r);
    if (cx.indexOf(c) < 0) cx.push(c);
    cell[JSON.stringify([r, c])] = x.value;
  });
  return [ry.map(function(r) { return cx.map(function(c) { var k = JSON.stringify([r, c]); return Object.prototype.hasOwnProperty.call(cell, k) ? cell[k] : null; }); }), ry, cx];
}
function _hmExt(b) {
  var raw = b.data, piv = _hmPivot(raw);
  if (piv) raw = piv[0];
  var rowsIn = Array.isArray(raw) ? raw : [];
  var nrAll = rowsIn.length, ncAll = 0;
  rowsIn.forEach(function(r) { if (Array.isArray(r) && r.length > ncAll) ncAll = r.length; });
  var R = Math.min(_HM_CAP, nrAll), C = Math.min(_HM_CAP, ncAll), grid = [], vals = [], i, j;
  for (i = 0; i < R; i++) { grid.push([]); for (j = 0; j < C; j++) { var v0 = (Array.isArray(rowsIn[i]) && j < rowsIn[i].length) ? _hmNum(rowsIn[i][j]) : null; grid[i].push(v0); if (v0 !== null) vals.push(v0); } }
  var capnote = '';
  if (nrAll > R) capnote += _hgNote('Showing the first ' + R + ' of ' + nrAll + ' rows.');
  if (ncAll > C) capnote += _hgNote('Showing the first ' + C + ' of ' + ncAll + ' columns.');
  if (!vals.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A heatmap needs at least one number in data.</div>' + capnote + _hgVersionNote(b, 'heatmap'));
  var ly = Array.isArray(b.labels_y) ? b.labels_y : (Array.isArray(b.rows) ? b.rows : []), lx = Array.isArray(b.labels_x) ? b.labels_x : (Array.isArray(b.cols) ? b.cols : []);
  if (piv) { ly = piv[1]; lx = piv[2]; }
  var rl = [], cl = [];
  for (i = 0; i < R; i++) rl.push(i < ly.length && _hmLab(ly[i]) ? _hmLab(ly[i]).slice(0, 24) : 'Row ' + (i + 1));
  for (j = 0; j < C; j++) cl.push(j < lx.length && _hmLab(lx[j]) ? _hmLab(lx[j]).slice(0, 24) : 'Col ' + (j + 1));
  var notes = capnote, sname = b.scale, stops = null, lname = typeof sname === 'string' ? sname.toLowerCase() : null;
  if (lname !== null) Object.keys(_HM_SCALES).forEach(function(k) { if (stops === null && k.toLowerCase() === lname) stops = _HM_SCALES[k]; });
  if (stops === null && sname) notes += _hgNote('Unknown scale' + (typeof sname === 'string' ? ' "' + _ifS(sname, 30) + '"' : '') + '; drawn with Viridis.');
  if (stops === null) stops = (!sname ? _hmHexScale(b.color_scale) : null) || _HM_SCALES.Viridis;
  var zmin = _hmNum(b.z_min), zmax = _hmNum(b.z_max), zmid = _hmNum(b.z_mid);
  var dom = _hmDomain(vals, zmin, zmax, zmid), lo = dom[0], hi = dom[1];
  var midOn = zmid !== null && !(zmin !== null && zmax !== null), spec = b.value_format;
  if (spec && !(typeof spec === 'string' && _HM_FMT_RE.test(spec))) { notes += _hgNote('value_format "' + _ifS(spec, 20) + '" is not understood (use , .N and f, % or d); values use the default format.'); spec = null; }
  function f(x) { return _hmFmt(x, spec); }
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '', show = b.show_values === true, compact = C > _HM_COMPACT, hdr, mh = compact ? '16' : '32';
  if (compact) {
    if (show) notes += _hgNote('Values are not drawn above ' + _HM_COMPACT + ' columns (the grid is squeezed to fit); hover a cell or read the table.');
    show = false;
    var k = Math.ceil(C / 4);
    hdr = '';
    for (j = 0; j < C; j += k) hdr += '<div style="font-size:12px;line-height:1.25;text-align:left;overflow-wrap:anywhere;color:var(--muted,#475569);padding:0 2px 2px;grid-column:span ' + Math.min(k, C - j) + ';">' + _ifS(cl[j], 24) + '</div>';
  } else {
    hdr = cl.map(function(c) { return '<div style="font-size:12px;line-height:1.25;text-align:center;overflow-wrap:anywhere;color:var(--muted,#475569);padding:0 2px 2px;">' + _ifS(c, 24) + '</div>'; }).join('');
  }
  var cells = '<div></div>' + hdr;
  var nmiss = 0;
  for (i = 0; i < R; i++) {
    cells += '<div style="font-size:12px;line-height:1.25;text-align:right;overflow-wrap:anywhere;max-width:110px;display:flex;align-items:center;justify-content:flex-end;padding-right:6px;color:var(--muted,#475569);">' + _ifS(rl[i], 24) + '</div>';
    for (j = 0; j < C; j++) {
      var v = grid[i][j], tip = _ifS(rl[i] + ', ' + cl[j] + ': ', 60);
      if (v === null) {
        nmiss++;
        cells += '<div class="hmc hmn" title="' + tip + 'no data" style="min-height:' + mh + 'px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;font-size:12px;border:1px dashed var(--muted,#475569);color:var(--muted,#475569);">–</div>';
        continue;
      }
      var c = _hmRgb(stops, (v - lo) / (hi - lo)), fg = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] < 140 ? '#fff' : '#111';
      cells += '<div class="hmc" title="' + tip + _ifS(f(v) + us, 30) + '" style="min-height:' + mh + 'px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;font-size:12px;overflow-wrap:anywhere;background:rgb(' +
        c[0] + ',' + c[1] + ',' + c[2] + ');color:' + fg + ';">' + (show ? _ifS(f(v), 20) : '') + '</div>';
    }
  }
  if (nmiss) notes += _hgNote(nmiss + (nmiss === 1 ? ' cell has' : ' cells have') + ' no usable number and ' + (nmiss === 1 ? 'is' : 'are') + ' marked "no data".');
  var mn = Math.min.apply(null, vals), mx = Math.max.apply(null, vals);
  var aria = 'Heatmap, ' + R + (R === 1 ? ' row' : ' rows') + ' by ' + C + (C === 1 ? ' column' : ' columns') + ', values from ' + f(mn) + ' to ' + f(mx) + us + '.';
  var gridHtml = '<div class="hms" style="max-width:100%;overflow-x:auto;"><div role="img" aria-label="' + _ifS(aria, 200) + '" style="display:grid;grid-template-columns:minmax(72px,auto) repeat(' + C + ',minmax(0,1fr));gap:2px;width:100%;max-width:' + (120 + C * 96) + 'px;">' + cells + '</div></div>';
  var bar = '';
  if (b.show_colorbar !== false) {
    var grad = stops.map(function(s) { return 'rgb(' + s[1][0] + ',' + s[1][1] + ',' + s[1][2] + ') ' + _ifFmt(s[0] * 100) + '%'; }).join(',');
    bar = '<div class="hmb" style="display:flex;align-items:center;gap:8px;margin-top:8px;font-size:12px;color:var(--muted,#475569);"><span style="max-width:35%;overflow-wrap:anywhere;">' + _ifS(f(lo) + us, 30) +
      '</span><div style="flex:1 0 60px;height:12px;border:1px solid var(--border,#CBD5E1);border-radius:3px;background:linear-gradient(to right,' + grad + ');"></div><span style="max-width:35%;overflow-wrap:anywhere;">' + _ifS(f(hi) + us, 30) + '</span></div>';
    if (midOn) bar += _hgNote('Colour midpoint: ' + _ifS(f(zmid) + us, 30) + '.');
  }
  var table = _ifTable(['Row'].concat(cl), rl.map(function(r, ri) { return [r].concat(cl.map(function(_, ci) { return grid[ri][ci] === null ? 'no data' : f(grid[ri][ci]) + us; })); }));
  return _ifWrap('<div class="ifhm" style="max-width:100%;">' + _ifTitle(b) + gridHtml + bar + notes + _hgVersionNote(b, 'heatmap') + table + '</div>');
}
(function() {
  var prev = _RENDERERS['heatmap'];
  _RENDERERS['heatmap'] = function(b) {
    return (b && typeof b === 'object' && _HM_KEYS.some(function(k) { return Object.prototype.hasOwnProperty.call(b, k); })) ? _hmExt(b) : prev(b);
  };
})();

// Build contract v1.1: these atoms emit data-cb on their moving elements; _cbPass completes the markup (see above).
['treemap', 'venn_diagram', 'org_chart', 'histogram', 'box_plot', 'waterfall', 'sunburst', 'chord_diagram', 'circle_pack', 'arc_diagram', 'contour_plot', 'voronoi'].forEach(function(n) {
  var fn = _RENDERERS[n];
  _RENDERERS[n] = function(b) { return _cbPass(fn(b)); };
});

// ── candlestick_chart (Plotly candlestick + ohlc) ── open/high/low/close bars on a time axis, optional volume panel. The date axis is
// d3-scale scaleUtc().ticks(5) (d3-time utcTicks: intervals 1 s .. 1 y, chosen by bisecting the target step) labelled by the scale's
// default multi-scale format (d3-time-format utcFormat), ported by hand for UTC only. The price axis is d3 nice()/ticks() (the histogram
// helpers). Twin of _cs_axis / _cs_parse / _render_candlestick_chart in renderers/web_article.py.
var _CS_STEPS = [['s', 1, 1000], ['s', 5, 5000], ['s', 15, 15000], ['s', 30, 30000], ['m', 1, 60000], ['m', 5, 300000], ['m', 15, 900000], ['m', 30, 1800000],
  ['h', 1, 3600000], ['h', 3, 10800000], ['h', 6, 21600000], ['h', 12, 43200000], ['d', 1, 86400000], ['d', 2, 172800000], ['w', 1, 604800000],
  ['M', 1, 2592000000], ['M', 3, 7776000000], ['y', 1, 31536000000]];
var _CS_DAY = 86400000, _CS_WD = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
var _CS_MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
function _csMod(a, m) { return ((a % m) + m) % m; }
function _csFloor(u, ms) {
  if (u === 's') return ms - _csMod(ms, 1000);
  if (u === 'm') return ms - _csMod(ms, 60000);
  if (u === 'h') return ms - _csMod(ms, 3600000);
  var n = Math.floor(ms / _CS_DAY);
  if (u === 'd') return n * _CS_DAY;
  if (u === 'w') return (n - _csMod(n + 4, 7)) * _CS_DAY;
  var d = new Date(ms);
  return Date.UTC(d.getUTCFullYear(), u === 'M' ? d.getUTCMonth() : 0, 1);
}
function _csOffset(u, ms, k) {
  var f = {s: 1000, m: 60000, h: 3600000, d: _CS_DAY, w: 7 * _CS_DAY};
  if (f[u]) return ms + k * f[u];
  var d = new Date(ms), m = d.getUTCFullYear() * 12 + d.getUTCMonth() + (u === 'M' ? k : 12 * k);
  return Date.UTC(Math.floor(m / 12), _csMod(m, 12), 1);
}
function _csField(u, ms) {
  if (u === 's') return _csMod(Math.floor(ms / 1000), 60);
  if (u === 'm') return _csMod(Math.floor(ms / 60000), 60);
  if (u === 'h') return _csMod(Math.floor(ms / 3600000), 24);
  if (u === 'd') return Math.floor(ms / _CS_DAY);
  var d = new Date(ms);
  return u === 'M' ? d.getUTCMonth() : d.getUTCFullYear();
}
function _csTickStep(a, b, count) {
  if (!(Math.abs(b - a) > 0)) return 0;   // d3 tickSpec gives no step for an empty span; tickStep turns that into 0
  var inc = b < a ? _hgTickInc(b, a, count) : _hgTickInc(a, b, count);
  return (b < a ? -1 : 1) * (inc < 0 ? 1 / -inc : inc);
}
function _csRange(u, k, start, stop) {
  var out = [], t = _csFloor(u, start);
  while (t <= stop) {
    if (t >= start && (k === 1 || _csMod(_csField(u, t), k) === 0)) out.push(t);
    t = _csOffset(u, t, 1);
  }
  return out;
}
function _csPad(v, n) { var s = String(v); while (s.length < n) s = '0' + s; return s; }
function _csLabel(ms) {
  var d = new Date(ms), wd = _csMod(Math.floor(ms / _CS_DAY) + 4, 7), h12 = d.getUTCHours() % 12 || 12;
  if (_csMod(ms, 1000)) return '.' + _csPad(_csMod(ms, 1000), 3);
  if (_csMod(ms, 60000)) return ':' + _csPad(d.getUTCSeconds(), 2);
  if (_csMod(ms, 3600000)) return _csPad(h12, 2) + ':' + _csPad(d.getUTCMinutes(), 2);
  if (_csMod(ms, _CS_DAY)) return _csPad(h12, 2) + ' ' + (d.getUTCHours() < 12 ? 'AM' : 'PM');
  if (d.getUTCDate() !== 1) return (wd ? _CS_WD[wd] : _CS_MON[d.getUTCMonth()].slice(0, 3)) + ' ' + _csPad(d.getUTCDate(), 2);
  if (d.getUTCMonth() !== 0) return _CS_MON[d.getUTCMonth()];
  return _csPad(d.getUTCFullYear(), 4);
}
function _csAxis(start, stop, count) {
  var target = Math.abs(stop - start) / count, i = 0, t, k;
  while (i < _CS_STEPS.length && _CS_STEPS[i][2] <= target) i++;
  if (i === _CS_STEPS.length) {
    k = Math.floor(_csTickStep(start / 31536000000, stop / 31536000000, count));
    t = k > 0 ? _csRange('y', k, start, stop) : [];
  } else if (i === 0) {
    k = Math.floor(Math.max(_csTickStep(start, stop, count), 1)); t = [];
    for (var x = Math.ceil(start); x <= stop; x++) if (_csMod(x, k) === 0) t.push(x);
  } else {
    var j = target / _CS_STEPS[i - 1][2] < _CS_STEPS[i][2] / target ? i - 1 : i;
    t = _csRange(_CS_STEPS[j][0], _CS_STEPS[j][1], start, stop);
  }
  return [t, t.map(_csLabel)];
}
function _csAxisHtml(ev, X0, span, lab) {
  var maxlen = Math.max.apply(null, lab.map(function(s) { return s.length; })), stride = Math.ceil(ev.length / Math.max(2, Math.min(8, Math.floor(48 / maxlen)))), shown = [], i, xs = '';
  for (i = 0; i < ev.length; i++) if (i % stride === 0 && (span > 0 || i === 0)) shown.push(i);
  var mid = shown.filter(function(k) { return _csMod(ev[k], _CS_DAY) === 0; }), pool = mid.length ? mid : shown, keep = {};
  pool.forEach(function(k, j) { if (j % 2 === 0) keep[k] = true; });
  shown.forEach(function(k) {
    xs += '<div class="hgx' + (keep[k] ? ' hgc' : '') + '" style="position:absolute;top:100%;left:' + (span > 0 ? _tmPct(ev[k] - X0, span) : '50%') + ';"><div style="position:absolute;left:0;top:0;width:1px;height:4px;background:var(--muted,#475569);"></div>' +
      '<div style="position:absolute;left:0;top:10px;transform:translateX(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + lab[k] + '</div></div>';
  });
  return xs;
}
function _csParse(s) {
  if (typeof s !== 'string') return null;
  var m = /^[ \t\r\n]*(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,3}))?)?)?Z?[ \t\r\n]*$/.exec(s);
  if (!m) return null;
  var y = +m[1], mo = +m[2], d = +m[3], h = +(m[4] || 0), mi = +(m[5] || 0), sec = +(m[6] || 0), ms = +((m[7] || '0') + '00').slice(0, 3);
  if (!(y >= 1000 && y <= 9000 && mo >= 1 && mo <= 12 && d >= 1 && d <= new Date(Date.UTC(y, mo, 0)).getUTCDate() && h < 24 && mi < 60 && sec < 60)) return null;
  return Date.UTC(y, mo - 1, d, h, mi, sec, ms);
}
var _CS_READ = 10000, _CS_CAP = 250;
function _csBars(b) {
  var col = function(k) { return Array.isArray(b[k]) ? b[k] : []; };
  var dates = col('dates'), o = col('open'), h = col('high'), l = col('low'), c = col('close'), vol = col('volume'), bars = [], leftOut = 0, vmiss = 0;
  for (var i = 0; i < Math.min(dates.length, _CS_READ); i++) {
    var ms = _csParse(dates[i]), q = [o, h, l, c].map(function(x) { return i < x.length ? x[i] : null; });
    if (ms === null || !q.every(_wfNum) || q[2] > Math.min(q[0], q[3]) || q[1] < Math.max(q[0], q[3])) { leftOut++; continue; }
    var v = i < vol.length ? vol[i] : null, vok = _wfNum(v) && v >= 0;
    if (vol.length && !vok) vmiss++;
    bars.push([ms, dates[i].replace(/^[ \t\r\n]+|[ \t\r\n]+$/g, ''), q[0], q[1], q[2], q[3], vok ? v : null, i]);
  }
  bars.sort(function(a, z) { return a[0] - z[0] || a[7] - z[7]; });
  return [bars, leftOut, vmiss, Math.max(0, dates.length - _CS_READ), vol.length > 0];
}
_RENDERERS['candlestick_chart'] = function(b) {
  var R = _csBars(b), bars = R[0], leftOut = R[1], vmiss = R[2], unread = R[3], beyond = bars.length - _CS_CAP;
  bars = bars.slice(0, _CS_CAP);
  var notes = (leftOut ? _hgNote(leftOut + (leftOut === 1 ? ' bar had' : ' bars had') + ' a missing date, a missing number or prices that do not fit together and ' + (leftOut === 1 ? 'was' : 'were') + ' left out.') : '') +
    (vmiss ? _hgNote(vmiss + (vmiss === 1 ? ' volume was' : ' volumes were') + ' missing, negative or not a number and ' + (vmiss === 1 ? 'was' : 'were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + (beyond === 1 ? ' bar beyond the first 250 was' : ' bars beyond the first 250 were') + ' not drawn.') : '') +
    (unread ? _hgNote(unread + (unread === 1 ? ' entry beyond the first 10000 was' : ' entries beyond the first 10000 were') + ' not read.') : '');
  if (!bars.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A candlestick chart needs at least one bar with a date and open, high, low and close numbers.</div>' + notes + _hgVersionNote(b, 'candlestick_chart'));
  var n = bars.length, ohlc = b.style === 'ohlc', unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '';
  var yl = b.y_label ? String(b.y_label).slice(0, 40) : '', cap = yl ? yl + (unit ? ' (' + unit + ')' : '') : unit;
  var allv = []; bars.forEach(function(r) { allv.push(r[2], r[3], r[4], r[5]); });
  var dc = Math.min(6, _hgDecimals(allv)), f = function(v) { return _bpFmt(v, dc); };
  var ms = bars.map(function(r) { return r[0]; }), g = Infinity;
  for (var i = 1; i < n; i++) if (ms[i] > ms[i - 1]) g = Math.min(g, ms[i] - ms[i - 1]);
  if (g === Infinity) g = _CS_DAY;
  var T0 = Math.floor(ms[0] - g / 2), T1 = Math.ceil(ms[n - 1] + g / 2), tspan = T1 - T0;
  var Yd = _hgNice(Math.min.apply(null, bars.map(function(r) { return r[4]; })), Math.max.apply(null, bars.map(function(r) { return r[3]; })), 5), Y0 = Yd[0], Y1 = Yd[1], yspan = Y1 - Y0;
  var yt = _hgTicks(Y0, Y1, 5), ytd = _hgDecimals(yt), ytl = yt.map(function(t) { return _hgNum(t, ytd); });
  var vols = bars.filter(function(r) { return r[6] !== null; }).map(function(r) { return r[6]; }), showVol = vols.length > 0;
  var V1 = showVol ? _hgNice(0, Math.max.apply(null, vols), 3)[1] : 0, vlab = showVol ? [_hgNum(0, 0), _hgNum(V1, _hgDecimals([V1]))] : [];
  var gut = 'calc(' + Math.max.apply(null, ytl.concat(vlab).map(function(t) { return t.length; })) + 'ch + 14px)';
  var yp = function(v) { return yspan > 0 ? _tmPct(Y1 - v, yspan) : '50%'; }, ph = function(a, c) { return yspan > 0 ? _tmPct(c - a, yspan) : '0%'; };
  var w = 0.7 * g, stroke = n <= 60 ? '2px' : '1px', POS = 'var(--positive,#15803D)', NEG = 'var(--negative,#B91C1C)';
  var ax = _csAxis(T0, T1, 5), ticks = ax[0], tlab = ax[1];
  var grid = yt.map(function(t) { return '<div style="position:absolute;left:0;right:0;top:' + yp(t) + ';border-top:1px solid var(--border,#CBD5E1);"></div>'; }).join('');
  var ylab = yt.map(function(t, i) { return '<div class="csyl" style="position:absolute;right:6px;top:' + yp(t) + ';transform:translateY(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--muted,#475569);">' + ytl[i] + '</div>'; }).join('');
  var candles = '', volume = '';
  bars.forEach(function(r, k) {
    var o = r[2], hi = r[3], lo = r[4], c = r[5], v = r[6], up = c >= o, cc = up ? POS : NEG, kind = up ? 'csu' : 'csd';
    var left = _tmPct(r[0] - w / 2 - T0, tspan), wid = _tmPct(w, tspan), thin = up || !ohlc;
    var geo = 'position:absolute;left:calc(50% - ' + (thin ? '1px' : '2px') + ');width:' + (thin ? '2px' : '4px') + ';top:' + yp(hi) + ';height:' + ph(lo, hi) + ';min-height:2px;background:' + cc + ';', inner;
    if (ohlc) {
      var sw = up ? '2px' : '4px';
      inner = '<div class="cso ' + kind + '" style="' + geo + '"></div>' +
        '<div style="position:absolute;right:50%;width:min(50%,14px);top:' + yp(o) + ';height:' + sw + ';margin-top:calc(0px - ' + sw + ' / 2);background:' + cc + ';"></div>' +
        '<div style="position:absolute;left:50%;width:min(50%,14px);top:' + yp(c) + ';height:' + sw + ';margin-top:calc(0px - ' + sw + ' / 2);background:' + cc + ';"></div>';
    } else {
      inner = '<div class="csk" style="' + geo + '"></div>' +
        '<div class="csb ' + kind + '" style="position:absolute;left:0;right:0;margin:0 auto;max-width:28px;top:' + yp(Math.max(o, c)) + ';height:' + ph(Math.min(o, c), Math.max(o, c)) + ';min-height:2px;box-sizing:border-box;border:' + stroke + ' solid ' + cc +
        ';background:' + (up ? 'var(--surface,#FFFFFF)' : cc) + ';"></div>';
    }
    candles += '<div class="csc ' + kind + '" data-cb="bar" data-key="' + _esc(r[1]) + '" style="position:absolute;top:0;bottom:0;left:' + left + ';width:' + wid + ';min-width:1px;' + _ifK(k, n) + _IF_FADE + '">' + inner + '</div>';
    if (v !== null) volume += '<div class="csv ' + kind + '" data-cb="bar" data-key="' + _esc(r[1]) + '/volume" style="position:absolute;bottom:0;left:' + left + ';width:' + wid + ';min-width:1px;height:' + (V1 > 0 ? _tmPct(v, V1) : '0%') + ';min-height:1px;box-sizing:border-box;border:1px solid ' + cc +
      ';background:' + (up ? 'var(--surface,#FFFFFF)' : cc) + ';' + _ifK(k, n) + _IF_FADE + '"></div>';
  });
  var first = bars[0], last = bars[n - 1], hiI = 0, loI = 0, ups = 0;
  bars.forEach(function(r, i) { if (r[3] > bars[hiI][3]) hiI = i; if (r[4] < bars[loI][4]) loI = i; if (r[5] >= r[2]) ups++; });
  var chg = last[5] - first[2], pc = first[2] !== 0 ? Math.round(chg / first[2] * 1000) / 10 : null;
  var aria = (ohlc ? 'OHLC bar chart' : 'Candlestick chart') + ' of ' + n + (n === 1 ? ' bar' : ' bars') + ' from ' + first[1] + ' to ' + last[1] + (unit ? ' in ' + unit : '') + '. First open ' + f(first[2]) +
    ', last close ' + f(last[5]) + ', change ' + (chg > 0 ? '+' : '') + f(chg) + (pc !== null ? ' (' + (pc > 0 ? '+' : '') + _bpFmt(pc, 1) + '%)' : '') + '. Highest high ' + f(bars[hiI][3]) + ' on ' + bars[hiI][1] +
    ', lowest low ' + f(bars[loI][4]) + ' on ' + bars[loI][1] + '. ' + ups + ' up, ' + (n - ups) + ' down.';
  var swUp = ohlc ? '<span style="display:inline-block;width:2px;height:14px;background:var(--positive,#15803D);"></span>'
    : '<span style="display:inline-block;width:12px;height:12px;box-sizing:border-box;border:2px solid var(--positive,#15803D);background:var(--surface,#FFFFFF);"></span>';
  var swDn = ohlc ? '<span style="display:inline-block;width:4px;height:14px;background:var(--negative,#B91C1C);"></span>'
    : '<span style="display:inline-block;width:12px;height:12px;box-sizing:border-box;border:2px solid var(--negative,#B91C1C);background:var(--negative,#B91C1C);"></span>';
  var legend = '<div class="csl" style="display:flex;flex-wrap:wrap;gap:4px 16px;margin:0 0 8px;font-size:0.75rem;line-height:1.2;color:var(--text,#0F172A);">' +
    '<span style="display:inline-flex;align-items:center;gap:6px;">' + swUp + 'Up: close at or above open (' + (ohlc ? 'thin bar' : 'hollow') + ')</span>' +
    '<span style="display:inline-flex;align-items:center;gap:6px;">' + swDn + 'Down: close below open (' + (ohlc ? 'thick bar' : 'filled') + ')</span></div>';
  var vpanel = showVol ? '<div style="display:flex;margin-top:10px;"><div style="flex:0 0 ' + gut + ';position:relative;">' +
    '<div class="csyl" style="position:absolute;right:6px;top:0;font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + vlab[1] + '</div>' +
    '<div class="csyl" style="position:absolute;right:6px;bottom:0;font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + vlab[0] + '</div></div>' +
    '<div class="csq" style="position:relative;flex:1 1 auto;min-width:0;height:64px;border-bottom:1px solid var(--muted,#475569);border-left:1px solid var(--muted,#475569);">' +
    '<div style="position:absolute;left:0;right:0;top:0;border-top:1px solid var(--border,#CBD5E1);"></div>' + volume + '</div></div>' : '';
  var chart = '<div class="ifcs" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>@container (max-width:560px){.ifcs .hgx:not(.hgc){display:none}}</style>' + legend +
    (cap ? '<div class="cscap" style="font-size:0.78rem;color:var(--muted,#475569);margin:0 0 6px;">' + _esc(cap) + '</div>' : '') +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;margin:0 0 34px 0;padding:8px 36px 0 0;">' +
    '<div style="display:flex;"><div style="flex:0 0 ' + gut + ';position:relative;">' + ylab + '</div>' +
    '<div class="csp" style="position:relative;flex:1 1 auto;min-width:0;height:260px;border-left:1px solid var(--muted,#475569);">' + grid + candles + '</div></div>' + vpanel +
    '<div style="position:relative;margin-left:' + gut + ';height:0;border-top:1px solid var(--muted,#475569);">' + _csAxisHtml(ticks, T0, tspan, tlab) + '</div></div></div>';
  var head = ['Date', 'Open', 'High', 'Low', 'Close', 'Direction'].concat(showVol ? ['Volume'] : []);
  return _ifWrap(_ifTitle(b) + chart + notes + _hgVersionNote(b, 'candlestick_chart') + _ifTable(head, bars.map(function(r) {
    return [r[1], f(r[2]) + us, f(r[3]) + us, f(r[4]) + us, f(r[5]) + us, r[5] >= r[2] ? 'Up' : 'Down'].concat(showVol ? [r[6] !== null ? _bpFmt(r[6], 6) : 'none'] : []);
  })));
};

// ── parallel_coords (Plotly parcoords) ── each dimension is a d3 scaleLinear (domain nice(min, max, 5), or the explicit [min, max]) on a vertical
// axis; the axes sit at d3 scalePoint().padding(0.5); each row is d3.line().digits(2) through its value on every axis. Drawn in a 1000 x 260 viewBox
// stretched to the box (preserveAspectRatio none, non-scaling strokes) so every label is real 12px HTML text. Twin of _pc_layout and
// _render_parallel_coords in renderers/web_article.py.
var _PC_W = 1000, _PC_TOP = 16, _PC_BOT = 244, _PC_H = 260;
function _pcLayout(dims) {
  var n = dims.length, step = _PC_W / Math.max(1, n - 1 + 0.5 * 2), start = 0 + (_PC_W - 0 - step * (n - 1)) * 0.5, xs = [], domains = [], ticks = [], tickY = [], scales = [], i;
  for (i = 0; i < n; i++) xs.push(start + step * i);
  dims.forEach(function(d) {
    var v = d.values, d0, d1, r0, r1;
    if (typeof d.min === 'number' && typeof d.max === 'number' && d.min < d.max) { d0 = d.min; d1 = d.max; }
    else { var nn = _hgNice(Math.min.apply(null, v), Math.max.apply(null, v), 5); d0 = nn[0]; d1 = nn[1]; }
    if (d.reverse) { r0 = _PC_TOP; r1 = _PC_BOT; } else { r0 = _PC_BOT; r1 = _PC_TOP; }
    var bw = d1 - d0, sc = function(x) { var t = bw ? (x - d0) / bw : 0.5; return r0 * (1 - t) + r1 * t; }, tk = _hgTicks(d0, d1, 5);
    domains.push([d0, d1]); ticks.push(tk); tickY.push(tk.map(sc)); scales.push(sc);
  });
  var rows = dims[0].values.length, ys = [], paths = [], r, k;
  for (r = 0; r < rows; r++) {
    var ry = [], p = '';
    for (k = 0; k < n; k++) {
      ry.push(scales[k](dims[k].values[r]));
      p += (k === 0 ? 'M' : 'L') + String(Math.round(xs[k] * 100) / 100) + ',' + String(Math.round(ry[k] * 100) / 100);
    }
    ys.push(ry); paths.push(p);
  }
  return {xs: xs, domains: domains, ticks: ticks, tickY: tickY, ys: ys, paths: paths};
}
function _pcNum(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12; }
function _pcText(v) {
  if (typeof v === 'string') return v !== '' ? v : null;
  return typeof v === 'number' && isFinite(v) && v !== 0 ? String(v) : null;
}
function _pcPlural(c, one, many) { return c + ' ' + (c === 1 ? one : many); }
_RENDERERS['parallel_coords'] = function(b) {
  var raw = Array.isArray(b.dimensions) ? b.dimensions : [], dims = [], leftD = 0;
  raw.slice(0, 8).forEach(function(d, k) {
    if (!(d && typeof d === 'object' && !Array.isArray(d)) || !Array.isArray(d.values)) { leftD++; return; }
    var ok = _pcNum(d.min) && _pcNum(d.max) && d.min < d.max;
    var full = _pcText(d.label);
    dims.push({full: full, label: full !== null ? full.slice(0, 24) : 'Dimension ' + (k + 1), raw: d.values, min: ok ? d.min : null, max: ok ? d.max : null, reverse: d.reverse === true});
  });
  var beyondD = raw.length - 8, longest = dims.reduce(function(m, d) { return Math.max(m, d.raw.length); }, 0), nrows = Math.min(200, longest), keep = [], i;
  for (i = 0; i < nrows; i++) if (dims.every(function(d) { return i < d.raw.length && _pcNum(d.raw[i]); })) keep.push(i);
  var leftR = nrows - keep.length, beyondR = longest - 200;
  var notes = (leftD ? _hgNote(_pcPlural(leftD, 'dimension was', 'dimensions were') + ' not a usable dimension and ' + (leftD === 1 ? 'was' : 'were') + ' left out.') : '') +
    (beyondD > 0 ? _hgNote(_pcPlural(beyondD, 'dimension', 'dimensions') + ' beyond the first 8 ' + (beyondD === 1 ? 'was' : 'were') + ' not drawn.') : '') +
    (leftR ? _hgNote(_pcPlural(leftR, 'row had', 'rows had') + ' a missing or non-numeric value and ' + (leftR === 1 ? 'was' : 'were') + ' left out.') : '') +
    (beyondR > 0 ? _hgNote(_pcPlural(beyondR, 'row', 'rows') + ' beyond the first 200 ' + (beyondR === 1 ? 'was' : 'were') + ' not drawn.') : '');
  if (dims.length < 2 || !keep.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">Parallel coordinates need at least 2 dimensions with numbers, and at least 1 complete row.</div>' + notes + _hgVersionNote(b, 'parallel_coords'));
  var n = dims.length, clamped = 0;
  dims.forEach(function(d) {
    d.real = keep.map(function(r) { return d.raw[r]; });
    d.values = d.real.map(function(v) {
      if (d.min !== null && (v < d.min || v > d.max)) { clamped++; v = Math.min(d.max, Math.max(d.min, v)); }
      return v;
    });
    d.lo = Math.min.apply(null, d.real); d.hi = Math.max.apply(null, d.real);
  });
  var L = _pcLayout(dims), cb = b.color_by, cbi = null, cd = null, cols = [];
  if (typeof cb === 'string' && cb !== '') { for (i = 0; i < n; i++) if (dims[i].label === cb || dims[i].full === cb) { cbi = i; break; } }
  else if (typeof cb === 'number' && cb === Math.floor(cb) && cb >= 0 && cb < n) cbi = cb;
  if (cbi === null && cb) notes += _hgNote('color_by "' + _esc(String(cb).slice(0, 40)) + '" matches no dimension; the lines are drawn in one colour.');
  if (clamped) notes += _hgNote(_pcPlural(clamped, 'value was', 'values were') + ' outside ' + (clamped === 1 ? 'its' : 'their') + ' axis range and ' + (clamped === 1 ? 'is' : 'are') + ' drawn on its edge.');
  var rl = Array.isArray(b.row_labels) ? b.row_labels : [];
  var names = keep.map(function(r) { return r < rl.length && _pcText(rl[r]) !== null ? _pcText(rl[r]).slice(0, 30) : 'Row ' + (r + 1); });
  var f = function(v) { return _bpFmt(v, 6); };
  var tl = L.ticks.map(function(tk) { var dc = _hgDecimals(tk); return tk.map(function(t) { return _hgNum(t, dc); }); });
  var lw = Math.max.apply(null, [].concat.apply([], tl).map(function(s) { return s.length; })) * 8 + 6, pitch = Math.max(92, lw + 8), pad = Math.max(0, lw - Math.floor(pitch / 2)), ACC = 'var(--accent,#0369A1)';
  var ramp = function(p) { return 'color-mix(in srgb,' + ACC + ' ' + p + '%,var(--surface,#F8FAFC))'; };
  if (cbi !== null) {
    cd = dims[cbi];
    var span = cd.hi - cd.lo;
    cols = cd.real.map(function(v) { return ramp(40 + Math.floor(60 * (span ? (v - cd.lo) / span : 0.5) + 0.5)); });
  }
  var heads = dims.map(function(d) {
    return '<div class="pch" style="flex:1 1 0;min-width:0;box-sizing:border-box;padding:0 3px;text-align:center;font-size:0.75rem;line-height:1.15;font-weight:600;overflow-wrap:anywhere;">' + _esc(d.label) +
      (d.reverse ? '<span style="display:block;font-weight:400;color:var(--muted,#475569);">reversed</span>' : '') + '</div>';
  }).join('');
  var r2 = function(x) { return String(Math.round(x * 100) / 100); };
  var axes = L.xs.map(function(x) { return '<line class="pca" x1="' + r2(x) + '" x2="' + r2(x) + '" y1="' + _PC_TOP + '" y2="' + _PC_BOT + '" style="stroke:var(--muted,#475569);stroke-width:1.5;"/>'; }).join('');
  var lines = L.paths.map(function(p, r) { return '<path class="pcr" data-cb="link" data-key="' + _esc(names[r]) + '" d="' + p + '"' + (cbi !== null ? ' style="stroke:' + cols[r] + ';"' : '') + '/>'; }).join('');
  var tickl = '';
  L.xs.forEach(function(x, k) {
    L.tickY[k].forEach(function(y, j) {
      tickl += '<div class="pct" style="position:absolute;left:' + _tmPct(x, _PC_W) + ';top:' + _tmPct(y, _PC_H) + ';transform:translate(calc(-100% - 5px),-50%);font-size:0.75rem;line-height:1;white-space:nowrap;' +
        'font-variant-numeric:tabular-nums;color:var(--muted,#475569);text-shadow:0 0 3px var(--bg,#fff),0 0 3px var(--bg,#fff);">' + tl[k][j] + '</div>';
    });
  });
  var legend = cbi === null ? '' : '<div class="pcl" style="display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;margin-top:8px;font-size:0.75rem;line-height:1.15;color:var(--muted,#475569);"><span>Line colour: ' + _esc(cd.label) + '</span>' +
    '<span>' + f(cd.lo) + '</span><span style="display:inline-block;width:96px;height:10px;border:1px solid var(--muted,#475569);background:linear-gradient(to right,' + ramp(40) + ',' + ramp(100) + ');"></span>' +
    '<span>' + f(cd.hi) + '</span></div>';
  var aria = 'Parallel coordinates of ' + _pcPlural(keep.length, 'row', 'rows') + ' across ' + n + ' dimensions.' +
    dims.map(function(d) { return ' ' + d.label + ' from ' + f(d.lo) + ' to ' + f(d.hi) + (d.reverse ? ', drawn upside down' : '') + '.'; }).join('') +
    (cbi !== null ? ' Lines are coloured by ' + cd.label + ', light for low and dark for high.' : '');
  var chart = '<div class="ifpc pcm' + (n * pitch + pad - 1) + '" style="container-type:inline-size;max-width:100%;">' +
    '<style>.ifpc path,.ifpc line{vector-effect:non-scaling-stroke}@container (max-width:' + (n * pitch + pad - 1) + 'px){.pcm' + (n * pitch + pad - 1) + ' .pcs{display:block!important}}</style>' +
    '<div class="pcs" style="display:none;font-size:0.75rem;color:var(--muted,#475569);margin:0 0 4px;">Scroll sideways to see every axis.</div>' +
    '<div role="region" aria-label="Parallel coordinates chart" tabindex="0" style="overflow-x:auto;">' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;box-sizing:content-box;padding-left:' + pad + 'px;min-width:' + (n * pitch) + 'px;">' +
    '<div style="display:flex;">' + heads + '</div>' +
    '<div style="position:relative;height:' + _PC_H + 'px;margin-top:4px;">' +
    '<svg viewBox="0 0 ' + _PC_W + ' ' + _PC_H + '" preserveAspectRatio="none" width="100%" height="' + _PC_H + '" aria-hidden="true" focusable="false" style="position:absolute;left:0;top:0;display:block;">' +
    axes + '<g fill="none" stroke-width="1.5" stroke-linejoin="round" stroke-opacity="0.75" style="stroke:' + ACC + ';' + _ifK(0, 1) + _IF_FADE + '">' + lines + '</g></svg>' + tickl + '</div>' + legend + '</div></div></div>';
  return _ifWrap(_ifTitle(b) + chart + notes + _hgVersionNote(b, 'parallel_coords') +
    _ifTable(['Row'].concat(dims.map(function(d) { return d.label; })), keep.map(function(r, j) { return [names[j]].concat(dims.map(function(d) { return f(d.real[j]); })); })));
};

// ── polar_chart (Plotly scatterpolar / scatterpolargl, package "polar") ── points at (angle, radius) on a circular grid. The radial axis is
// d3 nice(lo, hi, count) over the data (or the given r_range) with ticks(); a radius is scaleLinear().domain([lo, hi]).range([0, 40])(r) in a
// 100 x 100 box, an angle is clockwise from twelve o'clock = 90 - (rotation + direction * theta) degrees (d3 lineRadial's convention); a line is
// lineRadial() with defined() (a point outside the radial range breaks the line) and curveLinearClosed for fill "toself". Paths use d3-path's
// default 3 digits. Twin of _pc_layout / _render_polar_chart in renderers/web_article.py.
var _PL_R = 40, _PL_POINT_CAP = 2000, _PL_READ_CAP = 5000;
var _PL_COLORS = ['var(--accent,#0369A1)', 'var(--chart-2,#B45309)', 'var(--chart-3,#7E22CE)', 'var(--chart-4,#0F766E)', 'var(--chart-5,#BE123C)', 'var(--chart-6,#4D7C0F)'];
var _PL_DASH = ['', '6 3', '2 3', '8 3 2 3', '1 3', '10 4'];
var _PL_SYMBOLS = ['circle', 'square', 'triangle', 'diamond', 'cross', 'plus'];
function _plDec(v, d) {
  var k = Math.pow(10, d), n = Math.floor(v * k + 0.5);
  if (n === 0) return '0';
  var s = String(Math.abs(n)); while (s.length < d + 1) s = '0' + s;
  var fp = d ? s.slice(s.length - d).replace(/0+$/, '') : '';
  return (n < 0 ? '-' : '') + s.slice(0, s.length - d) + (fp ? '.' + fp : '');
}
function _plPath(angs, rads, ok, closed) {
  var out = '', seg = 0;
  for (var i = 0; i <= angs.length; i++) {
    if (i < angs.length && ok[i]) {
      out += (seg === 0 ? 'M' : 'L') + _plDec(rads[i] * Math.sin(angs[i]), 3) + ',' + _plDec(-rads[i] * Math.cos(angs[i]), 3);
      seg++;
    } else {
      if (seg && (closed || seg === 1)) out += 'Z';
      seg = 0;
    }
  }
  return out;
}
function _plLayout(r, theta, rotation, direction, rng, count) {
  var lo, hi;
  if (rng) { lo = rng[0]; hi = rng[1]; }
  else {
    var d = _hgNice(Math.min.apply(null, [0].concat(r)), Math.max.apply(null, [0].concat(r)), count); lo = d[0]; hi = d[1];
    if (lo === hi) { lo = 0; hi = 1; }
  }
  var span = hi - lo;
  return [lo, hi, _hgTicks(lo, hi, count),
    theta.map(function(t) { return (90 - (rotation + direction * t)) * Math.PI / 180; }),
    r.map(function(v) { return 0 * (1 - (v - lo) / span) + _PL_R * ((v - lo) / span); }),
    r.map(function(v) { return lo <= v && v <= hi; })];
}
function _plUniq(base, seen) {
  var k = base, n = 1;
  while (seen[k] === true) { n++; k = base + '~' + n; }
  seen[k] = true;
  return k;
}
function _plNum(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12; }
function _plMarker(sym, x, y, s) {
  var d = _plDec;
  if (sym === 'circle') return '<circle cx="' + d(x, 3) + '" cy="' + d(y, 3) + '" r="' + d(s, 3) + '"/>';
  if (sym === 'square') return '<rect x="' + d(x - s, 3) + '" y="' + d(y - s, 3) + '" width="' + d(2 * s, 3) + '" height="' + d(2 * s, 3) + '"/>';
  if (sym === 'triangle') return '<path d="M' + d(x, 3) + ',' + d(y - 1.2 * s, 3) + 'L' + d(x + 1.1 * s, 3) + ',' + d(y + s, 3) + 'L' + d(x - 1.1 * s, 3) + ',' + d(y + s, 3) + 'Z"/>';
  if (sym === 'diamond') return '<path d="M' + d(x, 3) + ',' + d(y - 1.3 * s, 3) + 'L' + d(x + 1.3 * s, 3) + ',' + d(y, 3) + 'L' + d(x, 3) + ',' + d(y + 1.3 * s, 3) + 'L' + d(x - 1.3 * s, 3) + ',' + d(y, 3) + 'Z"/>';
  if (sym === 'cross') return '<path d="M' + d(x - s, 3) + ',' + d(y - s, 3) + 'L' + d(x + s, 3) + ',' + d(y + s, 3) + 'M' + d(x + s, 3) + ',' + d(y - s, 3) + 'L' + d(x - s, 3) + ',' + d(y + s, 3) + '" fill="none" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"/>';
  return '<path d="M' + d(x - 1.3 * s, 3) + ',' + d(y, 3) + 'L' + d(x + 1.3 * s, 3) + ',' + d(y, 3) + 'M' + d(x, 3) + ',' + d(y - 1.3 * s, 3) + 'L' + d(x, 3) + ',' + d(y + 1.3 * s, 3) + '" fill="none" stroke="currentColor" stroke-width="1.4" vector-effect="non-scaling-stroke"/>';
}
function _plLabel(txt, x, y, cls) {
  var side = x > 56 ? 'r' : x < 44 ? 'l' : 'c';
  var tf = {r: 'translate(0,-50%)', l: 'translate(-100%,-50%)', c: 'translate(-50%,-50%)'}[side];
  var avail = side === 'r' ? 100 - x : side === 'l' ? x : 2 * Math.min(x, 100 - x);
  if (cls.indexOf('pcr') === 0) {
    return '<div class="' + cls + '" style="position:absolute;left:' + _plDec(x, 2) + '%;top:' + _plDec(y, 2) + '%;transform:translate(-50%,-50%)' +
      ';font-size:0.75rem;line-height:1;white-space:nowrap;padding:1px 3px;border-radius:3px;background:var(--bg,#fff);color:var(--muted,#475569);font-variant-numeric:tabular-nums;">' + txt + '</div>';
  }
  return '<div class="pca" style="position:absolute;left:' + _plDec(x, 2) + '%;top:' + _plDec(y, 2) + '%;transform:' + tf + ';max-width:' + _plDec(Math.max(avail - 1, 8), 2) +
    '%;font-size:0.75rem;line-height:1.1;text-align:' + {r: 'left', l: 'right', c: 'center'}[side] +
    ';overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden;color:var(--muted,#475569);">' + txt + '</div>';
}
_RENDERERS['polar_chart'] = function(b) {
  var lst = Array.isArray(b.series) ? b.series : [];
  var catsIn = b.categories;
  var cats = Array.isArray(catsIn) ? catsIn.slice(0, 12).filter(function(c) { return typeof c === 'string' || _plNum(c); }).map(function(c) { return String(c).slice(0, 30); }) : [];
  cats = cats.filter(function(c, i) { return cats.indexOf(c) === i; });
  var raw = [], leftOut = 0, nbad = 0, capped = [];
  lst.slice(0, 6).forEach(function(sr, k) {
    if (!(sr && typeof sr === 'object' && !Array.isArray(sr))) { leftOut++; return; }
    var rr = Array.isArray(sr.r) ? sr.r : [], tt = Array.isArray(sr.theta) ? sr.theta : [];
    var lab = sr.label ? String(sr.label).slice(0, 30) : 'Series ' + (k + 1);
    if (Math.max(rr.length, tt.length) > _PL_READ_CAP) capped.push([lab, Math.max(rr.length, tt.length)]);
    rr = rr.slice(0, _PL_READ_CAP); tt = tt.slice(0, _PL_READ_CAP);
    nbad += Math.abs(rr.length - tt.length);
    raw.push({k: k, label: lab, r: rr, theta: tt, sr: sr});
  });
  var categorical = cats.length > 0 || raw.some(function(s) { return s.theta.some(function(t) { return typeof t === 'string'; }); });
  if (categorical) raw.forEach(function(s) { s.theta.forEach(function(t) {
    if (cats.length < 12 && (typeof t === 'string' || _plNum(t)) && cats.indexOf(String(t).slice(0, 30)) < 0) cats.push(String(t).slice(0, 30));
  }); });
  var series = [], outsideCat = 0;
  raw.forEach(function(s) {
    var pr = [], pt = [], pl = [], m = Math.min(s.r.length, s.theta.length);
    for (var j = 0; j < m; j++) {
      var rv = s.r[j], tv = s.theta[j];
      if (!_plNum(rv)) { nbad++; continue; }
      if (categorical) {
        var ck = (typeof tv === 'string' || _plNum(tv)) ? String(tv).slice(0, 30) : null;
        if (ck === null) { nbad++; continue; }
        if (cats.indexOf(ck) < 0) { outsideCat++; continue; }
        pt.push(cats.indexOf(ck) * 360 / cats.length); pl.push(ck);
      } else {
        if (!_plNum(tv)) { nbad++; continue; }
        pt.push(tv); pl.push(tv);
      }
      pr.push(rv);
    }
    s.r = pr; s.theta = pt; s.tlabel = pl;
    if (pr.length) series.push(s);
  });
  var beyond = lst.length - 6;
  var notes = (leftOut ? _hgNote(leftOut + (leftOut === 1 ? ' series was not a series and was' : ' series were not a series and were') + ' left out.') : '') +
    (beyond > 0 ? _hgNote(beyond + (beyond === 1 ? ' series beyond the first 6 was' : ' series beyond the first 6 were') + ' not drawn.') : '') +
    (nbad ? _hgNote(nbad + (nbad === 1 ? ' entry was' : ' entries were') + ' not a usable number or had no matching partner and ' + (nbad === 1 ? 'was' : 'were') + ' skipped.') : '') +
    (outsideCat ? _hgNote(outsideCat + (outsideCat === 1 ? ' point was' : ' points were') + ' in a category beyond the first 12 and ' + (outsideCat === 1 ? 'was' : 'were') + ' not drawn.') : '') +
    capped.map(function(c) { return _hgNote(_esc('Series "' + c[0] + '": ' + c[1] + ' points were given; only the first ' + _PL_READ_CAP + ' were read and the rest were not drawn.')); }).join('');
  if (!series.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A polar chart needs at least one series with a radius and an angle for each point.</div>' + notes + _hgVersionNote(b, 'polar_chart'));
  var n = series.length, cap = Math.max(1, Math.floor(_PL_POINT_CAP / n));
  series.forEach(function(s) {
    var m = s.r.length;
    if (m > cap) {
      var idx = [];
      if (cap === 1) idx = [0]; else for (var i = 0; i < cap; i++) { var q = Math.floor(i * (m - 1) / (cap - 1)); if (idx.indexOf(q) < 0) idx.push(q); }
      notes += _hgNote(_esc('Series "' + s.label + '": ' + m + ' points were thinned to ' + idx.length + ' evenly spaced points (the first and last of the points read are kept); the limit is ' + _PL_POINT_CAP + ' points in all.'));
      s.r = idx.map(function(i) { return s.r[i]; }); s.theta = idx.map(function(i) { return s.theta[i]; }); s.tlabel = idx.map(function(i) { return s.tlabel[i]; });
    }
  });
  var direction = b.direction === 'clockwise' ? -1 : b.direction === 'counterclockwise' ? 1 : (categorical ? -1 : 1);
  var rotation = (_plNum(b.rotation) && Math.abs(b.rotation) <= 360) ? b.rotation : (direction === -1 ? 90 : 0);
  var count = _plNum(b.r_ticks) ? Math.floor(Math.min(8, Math.max(2, b.r_ticks)) + 0.5) : 4;
  var rg = b.r_range, rng = null;
  if (Array.isArray(rg) && rg.length === 2 && _plNum(rg[0]) && _plNum(rg[1]) && rg[0] < rg[1]) rng = [rg[0], rg[1]];
  else if (rg) notes += _hgNote('r_range needs two numbers, the first below the second; it was ignored.');
  var allr = []; series.forEach(function(s) { allr = allr.concat(s.r); });
  var lo, hi;
  if (rng) { lo = rng[0]; hi = rng[1]; }
  else { var dd = _hgNice(Math.min.apply(null, [0].concat(allr)), Math.max.apply(null, [0].concat(allr)), count); lo = dd[0]; hi = dd[1]; if (lo === hi) { lo = 0; hi = 1; } }
  var ticks = _hgTicks(lo, hi, count), hidden = 0;
  series.forEach(function(s) {
    var L = _plLayout(s.r, s.theta, rotation, direction, [lo, hi], count);
    s.ang = L[3]; s.rad = L[4]; s.ok = L[5];
    hidden += s.ok.filter(function(x) { return !x; }).length;
  });
  if (hidden) notes += _hgNote(hidden + (hidden === 1 ? ' point is' : ' points are') + ' outside the radial range and not drawn.');
  var unit = b.unit ? String(b.unit).slice(0, 12) : '', us = unit ? ' ' + unit : '';
  var dc = Math.min(6, _hgDecimals(allr.concat(ticks))), ff = function(v) { return _bpFmt(v, dc); };
  var ncat = cats.length, tstep = _plNum(b.theta_step) ? Math.floor(Math.min(180, Math.max(30, b.theta_step)) + 0.5) : 30;
  var spokes = [], spokeLab = [];
  if (categorical) { for (var ci = 0; ci < ncat; ci++) spokes.push(ci * 360 / ncat); spokeLab = cats; }
  else for (var tt2 = 0; tt2 < 360; tt2 += tstep) { spokes.push(tt2); spokeLab.push(tt2 + '°'); }
  var half = (categorical ? 360 / ncat : tstep) / 2, boxR = categorical ? 30 : 38, scale = boxR / _PL_R;
  var sx = function(deg, rr) { var a = (rotation + direction * deg) * Math.PI / 180; return [50 + rr * Math.cos(a), 50 - rr * Math.sin(a)]; };
  var grid = ticks.filter(function(t) { return t > lo; }).map(function(t) {
    return '<circle cx="0" cy="0" r="' + _plDec(_PL_R * (t - lo) / (hi - lo), 3) + '" fill="none" stroke="var(--border,#CBD5E1)" stroke-width="1" vector-effect="non-scaling-stroke"/>'; }).join('');
  spokes.forEach(function(t) {
    var a = (90 - (rotation + direction * t)) * Math.PI / 180;
    grid += '<path d="M0,0L' + _plDec(_PL_R * Math.sin(a), 3) + ',' + _plDec(-_PL_R * Math.cos(a), 3) + '" stroke="var(--border,#CBD5E1)" stroke-width="1" fill="none" vector-effect="non-scaling-stroke"/>';
  });
  var body = '', seenK = {};
  series.forEach(function(s, i) {
    var col = _PL_COLORS[i], dash = _PL_DASH[i], sym = _PL_SYMBOLS[i], pts = s.r.length, mode = s.sr.mode;
    mode = (mode === 'lines' || mode === 'markers' || mode === 'lines+markers') ? mode : (pts <= 20 ? 'lines+markers' : 'lines');
    var g = '<g data-cb="node" data-key="' + _esc(_plUniq(s.label, seenK)) + '" style="' + _ifK(i, n) + 'opacity:var(--k,1);color:' + col + ';">';
    if (s.sr.fill === 'toself') g += '<path d="' + _plPath(s.ang, s.rad, s.ok, true) + '" fill="' + col + '" fill-opacity="0.16" stroke="none"/>';
    if (mode.indexOf('lines') >= 0) g += '<path d="' + _plPath(s.ang, s.rad, s.ok, false) + '" fill="none" stroke="' + col + '" stroke-width="2"' + (dash ? ' stroke-dasharray="' + dash + '"' : '') + ' stroke-linejoin="round" vector-effect="non-scaling-stroke"/>';
    if (mode.indexOf('markers') >= 0) {
      g += '<g fill="' + col + '" stroke="var(--bg,#fff)" stroke-width="0.5">' + s.ang.map(function(a, j) { return s.ok[j] ? _plMarker(sym, s.rad[j] * Math.sin(a), -s.rad[j] * Math.cos(a), 1.6) : ''; }).join('') + '</g>';
    }
    body += g + '</g>';
  });
  var svg = '<svg viewBox="0 0 100 100" aria-hidden="true" focusable="false" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible;"><g transform="translate(50 50) scale(' + _plDec(scale, 3) + ')">' + grid + body + '</g></svg>';
  var labels = '';
  spokes.forEach(function(t, i) { var p = sx(t, boxR + 3.5); labels += _plLabel(_esc(spokeLab[i]), p[0], p[1], 'pca'); });
  var tdc = _hgDecimals(ticks);
  ticks.forEach(function(t, ti) { var p = sx(half, boxR * ((t - lo) / (hi - lo))); labels += _plLabel(_hgNum(t, tdc), p[0], p[1], ti % 2 && ticks.length > 3 ? 'pcr pcx' : 'pcr'); });
  var legend = '';
  if (n > 1) legend = '<div style="display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:0.75rem;color:var(--text,#0F172A);">' + series.map(function(s, i) {
    return '<span class="pcl" style="display:inline-flex;align-items:center;gap:6px;"><svg width="30" height="12" viewBox="0 0 30 12" aria-hidden="true" focusable="false" style="flex:0 0 30px;color:' + _PL_COLORS[i] + ';">' +
      '<path d="M1,6L29,6" stroke="' + _PL_COLORS[i] + '" stroke-width="2" fill="none"' + (_PL_DASH[i] ? ' stroke-dasharray="' + _PL_DASH[i] + '"' : '') + '/><g fill="' + _PL_COLORS[i] + '">' +
      _plMarker(_PL_SYMBOLS[i], 15, 6, 3.2) + '</g></svg><span>' + _esc(s.label) + '</span></span>'; }).join('') + '</div>';
  var aria = 'Polar chart of ' + n + ' series with the radius from ' + ff(lo) + ' to ' + ff(hi) + us +
    (categorical ? ', ' + ncat + ' categories: ' + cats.join(', ') : ', angles in degrees') + '. ' +
    series.map(function(s) {
      var dr = s.r.filter(function(v, j) { return s.ok[j]; });
      return s.label + ': ' + s.r.length + (s.r.length === 1 ? ' point' : ' points') +
        (dr.length ? ', radius from ' + ff(Math.min.apply(null, dr)) + ' to ' + ff(Math.max.apply(null, dr)) + us : ', none in the radial range') +
        (dr.length && dr.length !== s.r.length ? ' (' + (s.r.length - dr.length) + ' outside the radial range, not drawn)' : '');
    }).join('; ') + '.';
  var chart = '<div class="ifpc" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>@container (max-width:560px){.ifpc .pcx{display:none}}</style><div role="img" aria-label="' + _esc(aria) + '" style="position:relative;width:100%;max-width:520px;margin:0 auto;aspect-ratio:1/1;">' +
    svg + labels + '</div>' + legend + '</div>';
  var rows = [];
  series.forEach(function(s) { s.r.forEach(function(v, j) { rows.push([s.label, categorical ? s.tlabel[j] : _bpFmt(s.tlabel[j], 6), ff(v) + us, s.ok[j] ? 'drawn' : 'outside the radial range, not drawn']); }); });
  return _ifWrap(_ifTitle(b) + chart + notes + _hgVersionNote(b, 'polar_chart') + _ifTable(['Series', categorical ? 'Category' : 'Angle (degrees)', 'Radius', 'Status'], rows));
};

// ── histogram2d (preview): d3.bin() twice, drawn through the heatmap atom ─────────────────────────────────────────────────────────
// Twin of _h2_* in renderers/web_article.py. Bin edges are d3-array 3.2.4 bin() (ISC, Mike Bostock; see _hgBin), one run per axis; a cell counts the points
// that fall in both bins. The drawing, colour bar and hidden table are the registered heatmap renderer's.
var _H2_PTS = 20000, _H2_BINS = 40;
function _h2Axis(vals, target) {
  var edges = _hgBin(vals, target)[0], inner = edges.slice(1).map(function(e) { return e[0]; });
  return [edges, vals.map(function(v) { var lo = 0, hi = inner.length; while (lo < hi) { var m = (lo + hi) >>> 1; if (v < inner[m]) hi = m; else lo = m + 1; } return lo; })];
}
function _h2AxisCapped(vals, target) {
  var t = target;
  while (true) {
    var r = _h2Axis(vals, t);
    if (r[0].length <= _H2_BINS) return r;
    t = (t !== null ? t : Math.max(1, Math.ceil(Math.log(vals.length) / Math.LN2) + 1)) - 1;
    if (t < 2) return r;
  }
}
function _h2Counts(ex, ix, ey, iy) {
  var counts = ey.map(function() { return ex.map(function() { return 0; }); });
  for (var i = 0; i < ix.length; i++) counts[iy[i]][ix[i]]++;
  return counts;
}
function _h2Bin(xs, ys, nx, ny) {
  var ax = _h2Axis(xs, nx), ay = _h2Axis(ys, ny);
  return [ax[0], ay[0], _h2Counts(ax[0], ax[1], ay[0], ay[1])];
}
function _h2Labels(edges) {
  var all = []; edges.forEach(function(p) { all.push(p[0], p[1]); });
  var d = _hgDecimals(all);
  return edges.map(function(p) { return p[0] === p[1] ? _hgNum(p[0], d) : _hgNum(p[0], d) + '–' + _hgNum(p[1], d); });
}
function _h2Block(b) {
  var rx = Array.isArray(b.x) ? b.x : [], ry = Array.isArray(b.y) ? b.y : [], total = Math.min(rx.length, ry.length), pts = [], i;
  for (i = 0; i < total; i++) if (typeof rx[i] === 'number' && typeof ry[i] === 'number' && Math.abs(rx[i]) <= 1e12 && Math.abs(ry[i]) <= 1e12) pts.push([rx[i], ry[i]]);
  var notes = '', skipped = total - pts.length;
  if (skipped) notes += _hgNote(skipped + (skipped === 1 ? ' pair was' : ' pairs were') + ' not two usable numbers and ' + (skipped === 1 ? 'was' : 'were') + ' skipped.');
  if (pts.length > _H2_PTS) { notes += _hgNote('Using the first ' + _hgNum(_H2_PTS, 0) + ' of ' + _hgNum(pts.length, 0) + ' points.'); pts = pts.slice(0, _H2_PTS); }
  if (pts.length < 2) return [null, notes, pts.length];
  var xs = pts.map(function(p) { return p[0]; }), ys = pts.map(function(p) { return p[1]; });
  var ax = _h2AxisCapped(xs, _hgTarget(b.nbinsx)), ay = _h2AxisCapped(ys, _hgTarget(b.nbinsy)), ex = ax[0], ey = ay[0];
  var counts = _h2Counts(ex, ax[1], ey, ay[1]), hb = {
    type: 'heatmap', data: counts.slice().reverse(), labels_x: _h2Labels(ex), labels_y: _h2Labels(ey.slice().reverse()),
    scale: b.scale ? b.scale : 'YlGnBu', value_format: ',.0f', show_values: b.show_values === undefined || b.show_values === null ? ex.length <= _HM_COMPACT : b.show_values !== false, show_colorbar: b.show_colorbar !== false
  };
  if (b.title) hb.title = b.title;
  var peak = Math.max.apply(null, counts.map(function(r) { return Math.max.apply(null, r); }));
  notes = _hgNote('Columns bin x' + (b.x_label ? ' (' + _ifS(b.x_label, 40) + ')' : '') + ', rows bin y' + (b.y_label ? ' (' + _ifS(b.y_label, 40) + ')' : '') +
    ', highest y at the top. ' + _hgNum(pts.length, 0) + ' points in ' + ey.length + (ey.length === 1 ? ' row' : ' rows') + ' by ' + ex.length +
    (ex.length === 1 ? ' column' : ' columns') + '; the busiest cell holds ' + _hgNum(peak, 0) + '.') + notes;
  return [hb, notes, pts.length];
}
_RENDERERS['histogram2d'] = function(b) {
  var r = _h2Block(b), ver = _hgVersionNote(b, 'histogram2d');
  if (r[0] === null) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A histogram2d needs at least two points with a usable x and y.</div>' + r[1] + ver);
  var hm = _RENDERERS['heatmap'](r[0]);   // already wrapped: put the notes inside its wrapper, not in a second one
  return hm.slice(0, hm.length - 6) + r[1] + ver + '</div>';
};

// ── image_plot (preview): a pixel matrix or a safe image source, with axes ────────────────────────────────────────────────────────
// Twin of _ip_* in renderers/web_article.py. Tick labels are HTML text (12px at any width); the pixels are one SVG of crisp rectangles (equal neighbours in a row
// merged); a src is drawn only when it is an https URL or a base64 PNG/JPEG/GIF/WebP data: URI.
var _IP_CAP = 64;
var _IP_HEX = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
var _IP_HTTPS = /^https:\/\/[A-Za-z0-9.-]+(:[0-9]{1,5})?(\/[A-Za-z0-9\-._~:\/?#\[\]@!$&()*+,;=%]*)?$/;
var _IP_DATA = /^data:image\/(png|jpeg|gif|webp);base64,[A-Za-z0-9+\/]+={0,2}$/;
function _ipNum(v) { return (typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12) ? v : null; }
function _ipColor(c) {
  if (typeof c === 'string') {
    var m = _IP_HEX.exec(c);
    if (!m) return null;
    var h = m[1].toLowerCase();
    return '#' + (h.length === 3 ? h.split('').map(function(ch) { return ch + ch; }).join('') : h);
  }
  if (Array.isArray(c) && c.length === 3) {
    var n = c.map(_ipNum);
    if (n.indexOf(null) >= 0) return null;
    return '#' + n.map(function(v) { return ('0' + Math.min(255, Math.max(0, Math.round(v))).toString(16)).slice(-2); }).join('');
  }
  return null;
}
function _ipSrc(v) {
  if (typeof v !== 'string') return null;
  if (v.length <= 2000 && _IP_HTTPS.test(v)) return v;
  if (v.length <= 300000 && _IP_DATA.test(v)) return v;
  return null;
}
function _ipRange(v) {
  if (Array.isArray(v) && v.length === 2) { var a = _ipNum(v[0]), b = _ipNum(v[1]); if (a !== null && b !== null && a !== b) return [a, b]; }
  return null;
}
function _ipAxis(rng, vertical, room) {
  var a = rng[0], b = rng[1], lo = Math.min(a, b), hi = Math.max(a, b), cnts = [5, 4, 3, 2], ticks, labs, w = 0, html = '', ci;
  for (ci = 0; ci < cnts.length; ci++) {
    ticks = _hgTicks(lo, hi, cnts[ci]).filter(function(t) { return t >= lo && t <= hi; });
    var d = _hgDecimals(ticks);
    labs = ticks.map(function(t) { return _hgNum(t, d); });
    w = 0; labs.forEach(function(x) { w = Math.max(w, x.length); });
    if (ticks.length * (vertical ? 30 : w * 7 + 16) <= room) break;
  }
  ticks.forEach(function(t, k) {
    var pct = (t - a) / (b - a) * 100, pos;
    if (vertical) pos = 'right:0;top:' + _ifFmt(pct) + '%;transform:translateY(-50%);';
    else pos = 'left:' + _ifFmt(pct) + '%;transform:translateX(' + (pct < 6 ? '0' : pct > 94 ? '-100%' : '-50%') + ');';
    html += '<span style="position:absolute;' + pos + 'font-size:12px;line-height:1;white-space:nowrap;">' + _ifS(labs[k], 20) + '</span>';
  });
  return [html, w];
}
function _ipRangeText(r) { var d = _hgDecimals(r); return _hgNum(r[0], d) + ' to ' + _hgNum(r[1], d); }
_RENDERERS['image_plot'] = function(b) {
  b = (b && typeof b === 'object' && !Array.isArray(b)) ? b : {};
  var notes = '', rowsIn = Array.isArray(b.z) ? b.z : [], R = Math.min(_IP_CAP, rowsIn.length), C = 0, i, j, wide = 0;
  rowsIn.forEach(function(r) { if (Array.isArray(r)) wide = Math.max(wide, r.length); });
  C = Math.min(_IP_CAP, wide);
  var grid = [], nvalid = 0;
  for (i = 0; i < R; i++) { grid.push([]); for (j = 0; j < C; j++) { var c0 = (Array.isArray(rowsIn[i]) && j < rowsIn[i].length) ? _ipColor(rowsIn[i][j]) : null; grid[i].push(c0); if (c0) nvalid++; } }
  var src = _ipSrc(b.src), asMatrix = R > 0 && C > 0 && nvalid > 0;
  if (asMatrix && b.src) notes += _hgNote('Both z and src were given; z is drawn.');
  if (!asMatrix && src === null) {
    if (b.src && typeof b.src === 'string') return _ifWrap(_ifTitle(b) + _hgNote('The image source is not allowed (use an https URL or a base64 PNG, JPEG, GIF or WebP data: URI); nothing was drawn.') + _hgVersionNote(b, 'image_plot'));
    return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">An image_plot needs a z matrix or a src.</div>' + _hgVersionNote(b, 'image_plot'));
  }
  if (asMatrix) {
    if (rowsIn.length > R) notes += _hgNote('Showing the first ' + R + ' of ' + rowsIn.length + ' rows.');
    if (wide > C) notes += _hgNote('Showing the first ' + C + ' of ' + wide + ' columns.');
    var nb = R * C - nvalid;
    if (nb) notes += _hgNote(nb + (nb === 1 ? ' cell is' : ' cells are') + ' not a colour and ' + (nb === 1 ? 'was' : 'were') + ' left blank.');
  }
  var xr = _ipRange(b.x_range), yr = _ipRange(b.y_range);
  [['x_range', b.x_range, xr], ['y_range', b.y_range, yr]].forEach(function(t) {
    if (t[1] && t[2] === null) notes += _hgNote(t[0] + ' must be two different numbers; ' + (asMatrix ? 'the cell numbers are used.' : 'no ticks are drawn.'));
  });
  if (asMatrix) { xr = xr || [0, C]; yr = yr || [0, R]; }
  var wmin = asMatrix ? Math.min(250, Math.min(640, Math.max(40, C * 20))) : 250, hmin = asMatrix ? Math.max(36, wmin * R / C) : 100;
  var xa = xr ? _ipAxis(xr, false, wmin) : ['', 0], ya = yr ? _ipAxis(yr, true, hmin) : ['', 0], xt = xa[0], yt = ya[0], yw = ya[1];
  var aria, plot, maxw, table;
  if (asMatrix) {
    aria = 'Image, ' + R + (R === 1 ? ' row' : ' rows') + ' by ' + C + (C === 1 ? ' column' : ' columns') + ' of pixels, x from ' + _ipRangeText(xr) + ', y from ' + _ipRangeText(yr) + '.';
    var rects = '';
    for (i = 0; i < R; i++) {
      j = 0;
      while (j < C) {
        var c = grid[i][j], k = j;
        while (c && k + 1 < C && grid[i][k + 1] === c) k++;
        if (c) rects += '<rect x="' + j + '" y="' + i + '" width="' + (k - j + 1) + '" height="1" fill="' + c + '"/>';
        j = k + 1;
      }
    }
    plot = '<svg viewBox="0 0 ' + C + ' ' + R + '" preserveAspectRatio="none" shape-rendering="crispEdges" aria-hidden="true" focusable="false" style="display:block;width:100%;height:auto;aspect-ratio:' + C + '/' + R + ';min-height:36px;">' + rects + '</svg>';
    maxw = String(Math.min(640, Math.max(40, C * 20)) + 56);
    var head = ['Row']; for (j = 0; j < C; j++) head.push('Col ' + (j + 1));
    var trs = grid.map(function(r, ri) { return ['Row ' + (ri + 1)].concat(r.map(function(cc) { return cc || 'blank'; })); });
    table = _ifTable(head, trs);
  } else {
    aria = 'Picture, no text description given' + (xr && yr ? ', x from ' + _ipRangeText(xr) + ', y from ' + _ipRangeText(yr) : '') + '.';
    plot = '<img src="' + _esc(src) + '" alt="" referrerpolicy="no-referrer" loading="lazy" decoding="async" style="display:block;width:100%;height:auto;">';
    maxw = '640';
    table = _ifTable(['Axis', 'From', 'To'], [xr ? ['x', _ifFmt(xr[0]), _ifFmt(xr[1])] : ['x', 'none', 'none'], yr ? ['y', _ifFmt(yr[0]), _ifFmt(yr[1])] : ['y', 'none', 'none']]);
  }
  if (b.alt && typeof b.alt === 'string') aria = b.alt;
  var muted = 'font-size:12px;line-height:1.3;color:var(--muted,#475569);overflow-wrap:anywhere;';
  var ycol = yt ? String(Math.min(8, Math.max(1.5, Math.round((yw * 0.65 + 0.4) * 10) / 10))) + 'em' : '0';
  var gridHtml = '<div style="display:grid;grid-template-columns:' + ycol + ' minmax(0,1fr);column-gap:6px;width:100%;max-width:' + maxw + 'px;padding-top:6px;box-sizing:border-box;">' +
    '<div style="position:relative;">' + yt + '</div>' +
    '<div role="img" aria-label="' + _ifS(aria, 200) + '" style="min-width:0;' + (asMatrix ? '' : 'min-height:100px;') + 'border:1px solid var(--border,#CBD5E1);">' + plot + '</div>' +
    '<div></div><div style="position:relative;height:' + (xt ? '1.6em' : '0') + ';margin-top:4px;">' + xt + '</div></div>';
  var yl = b.y_label ? '<div style="' + muted + 'margin-bottom:2px;">' + _ifS(b.y_label, 40) + '</div>' : '';
  var xl = b.x_label ? '<div style="' + muted + 'text-align:center;max-width:' + maxw + 'px;">' + _ifS(b.x_label, 40) + '</div>' : '';
  return _ifWrap('<div data-cb="node" data-key="' + _ckey(b.title, 'image_plot') + '" class="ifip" style="max-width:100%;">' + _ifTitle(b) + yl + gridHtml + xl + notes + _hgVersionNote(b, 'image_plot') + table + '</div>');
};


// ── scatter_matrix and parallel_categories (Plotly splom / parcats, wave B) ── Twins of _render_scatter_matrix / _render_parallel_categories in renderers/web_article.py;
// the comment there describes both layouts.
var _WB_COL = ['#19294E', '#810998', '#0F6C4F', '#9A6120', '#B91C1C', '#0369A1', '#4D7C0F', '#BE185D'];
function _wbDims(b) {
  var lst = Array.isArray(b.dimensions) ? b.dimensions : [], dims = [], bad = 0;
  lst.forEach(function(d) {
    var v = d && typeof d === 'object' && !Array.isArray(d) ? d.values : undefined;
    if (!Array.isArray(v)) { bad++; return; }
    dims.push([d.label ? String(d.label).slice(0, 24) : 'Dimension ' + (dims.length + 1), v]);
  });
  return [dims.slice(0, 6), bad, Math.max(0, dims.length - 6)];
}
function _wbKeys(labs) { return labs.map(function(l, j) { return labs.indexOf(l) === labs.lastIndexOf(l) ? l : l + ' #' + (j + 1); }); }
function _wbDimNotes(bad, beyond) {
  return (bad ? _hgNote(bad + (bad === 1 ? ' entry was' : ' entries were') + ' not a dimension with a list of values and ' + (bad === 1 ? 'was' : 'were') + ' left out.') : '') +
    (beyond ? _hgNote(beyond + (beyond === 1 ? ' dimension beyond the first 6 was' : ' dimensions beyond the first 6 were') + ' not drawn.') : '');
}
function _smAxis(vals) {
  var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), d = _hgNice(lo, hi, 4);
  return [d[0], d[1], _hgTicks(d[0], d[1], 4)];
}
function _smExp(v) { return v === 0 ? '0' : v.toExponential(2); }
_RENDERERS['scatter_matrix'] = function(b) {
  var D = _wbDims(b), dims = D[0], notes = _wbDimNotes(D[1], D[2]);
  var m = dims.reduce(function(t, d) { return Math.max(t, d[1].length); }, 0), rows = [], skipped = 0, beyondR = 0;
  for (var r = 0; r < m; r++) {
    if (rows.length === 200) { beyondR = m - r; break; }
    var vals = dims.map(function(d) { return r < d[1].length ? d[1][r] : null; });
    if (vals.every(_wfNum)) rows.push([r, vals]); else skipped++;
  }
  notes += (skipped ? _hgNote(skipped + (skipped === 1 ? ' row had' : ' rows had') + ' a value that was not a usable number and ' + (skipped === 1 ? 'was' : 'were') + ' left out.') : '') +
    (beyondR ? _hgNote(beyondR + (beyondR === 1 ? ' row beyond the first 200 was' : ' rows beyond the first 200 were') + ' not drawn.') : '');
  var vn = _hgVersionNote(b, 'scatter_matrix');
  if (dims.length < 2 || rows.length < 2) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A scatter plot matrix needs at least two dimensions with two complete rows.</div>' + notes + vn);
  var N = dims.length, cols = dims.map(function(d, j) { return rows.map(function(row) { return row[1][j]; }); });
  var ax = cols.map(_smAxis), dc = cols.map(function(c) { return Math.min(6, _hgDecimals(c)); });
  var showUp = b.show_upper === true, labs = dims.map(function(d) { return d[0]; });
  var tiny = cols.map(function(c) { var mx = Math.max.apply(null, c.map(Math.abs)); return mx > 0 && mx < 1e-5; });
  var fm = function(j, v) { return tiny[j] ? _smExp(v) : _bpFmt(v, dc[j]); };
  var rng = cols.map(function(c, j) { return fm(j, Math.min.apply(null, c)) + ' to ' + fm(j, Math.max.apply(null, c)); });
  var erng = ax.map(function(a, j) { var q = _hgDecimals([a[0], a[1]]); return tiny[j] ? _smExp(a[0]) + ' to ' + _smExp(a[1]) : _hgNum(a[0], q) + ' to ' + _hgNum(a[1], q); });
  var pos = function(j, v) { var sp = ax[j][1] - ax[j][0]; return sp > 0 ? 5 + 90 * (v - ax[j][0]) / sp : 50; };
  var cell = 'position:relative;aspect-ratio:1;box-sizing:border-box;min-width:0;', out = '', idx = 0, lk = _wbKeys(labs);
  for (var i = 0; i < N; i++) {
    out += '<div class="sma" style="align-items:center;justify-content:flex-end;text-align:right;padding-right:4px;overflow-wrap:anywhere;font-size:0.75rem;line-height:1.15;color:var(--muted,#475569);">' + _esc(erng[i]) + '</div>';
    for (var j = 0; j < N; j++) {
      var kk = _ifK(idx, N * N) + _IF_FADE; idx++;
      if (i === j) {
        out += '<div data-cb="tile" data-key="' + _esc(lk[i]) + '" class="smc smd" style="' + cell + 'border:1px solid var(--muted,#475569);background:var(--surface,#F8FAFC);display:flex;align-items:center;justify-content:center;padding:4px;text-align:center;overflow:hidden;' +
          kk + '"><span class="smn" style="font-size:0.75rem;font-weight:700;">' + (i + 1) + '</span>' +
          '<span data-cb="label" data-key="' + _esc(lk[i]) + '" class="sml" style="font-size:0.75rem;font-weight:700;line-height:1.15;overflow-wrap:anywhere;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden;">' + _esc(labs[i]) + '</span></div>';
      } else if (i > j || showUp) {
        var dots = rows.map(function(row) {
          return '<circle class="smp" cx="' + pos(j, row[1][j]).toFixed(1) + '" cy="' + (100 - pos(i, row[1][i])).toFixed(1) + '" r="2.2" fill="var(--accent,#0369A1)" fill-opacity="0.7"/>';
        }).join('');
        out += '<div data-cb="tile" data-key="' + _esc(lk[i] + '\u00d7' + lk[j]) + '" class="smc" style="' + cell + 'border:1px solid var(--border,#CBD5E1);' + kk + '"><svg class="smx" viewBox="0 0 100 100" aria-hidden="true" focusable="false" ' +
          'style="position:absolute;inset:0;width:100%;height:100%;display:block;">' + dots + '</svg></div>';
      } else out += '<div class="smc sme" style="' + cell + kk + '"></div>';
    }
  }
  out += '<div class="sma"></div>' + erng.map(function(t) { return '<div class="sma" style="justify-content:center;text-align:center;overflow-wrap:anywhere;padding-top:2px;font-size:0.75rem;line-height:1.15;color:var(--muted,#475569);">' + _esc(t) + '</div>'; }).join('');
  var legend = '<ul style="list-style:none;margin:8px 0 0;padding:0;display:flex;flex-wrap:wrap;gap:2px 14px;font-size:0.75rem;line-height:1.3;color:var(--muted,#475569);">' +
    labs.map(function(l, j) { return '<li><b style="color:var(--text,#0F172A);">' + (j + 1) + '</b> ' + _esc(l) + ' (' + _esc(rng[j]) + ')</li>'; }).join('') + '</ul>';
  var css = '.ifsm .sma{display:none}.ifsm .sml{display:none}.ifsm .smg' + N + '{display:grid;grid-template-columns:repeat(' + N + ',minmax(0,1fr));gap:2px}' +
    '@container (min-width:600px){.ifsm .sma{display:flex}.ifsm .sml{display:-webkit-box}.ifsm .smn{display:none}.ifsm .smg' + N + '{grid-template-columns:52px repeat(' + N + ',minmax(0,1fr))}}';
  var aria = 'Scatter plot matrix of ' + N + ' measures over ' + rows.length + (rows.length === 1 ? ' row: ' : ' rows: ') + labs.map(function(l, j) { return l + ' (' + rng[j] + ')'; }).join(', ') + '.';
  var chart = '<div class="ifsm" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>' + css + '</style>' +
    '<div role="img" aria-label="' + _esc(aria) + '" class="smg' + N + '">' + out + '</div>' + legend + '</div>';
  return _ifWrap(_ifTitle(b) + chart + notes + vn + _ifTable(['Row'].concat(labs), rows.map(function(row) {
    return [String(row[0] + 1)].concat(row[1].map(function(v, j) { return fm(j, v); }));
  })));
};
function _pcRank(col) {
  var cnt = {}, first = {}, names = [];
  col.forEach(function(c, k) { var key = 'k:' + c; if (!(key in cnt)) { cnt[key] = 0; first[key] = k; names.push(c); } cnt[key]++; });
  var rk = names.map(function(c) { return [c, cnt['k:' + c]]; });
  rk.sort(function(a, b) { return (b[1] - a[1]) || (first['k:' + a[0]] - first['k:' + b[0]]); });
  return rk;
}
function _pcModel(cols) {
  var cats = [], idx = [];
  cols.forEach(function(col) {
    var rk = _pcRank(col), keep = rk.slice(0, 8), pos = {};
    cats.push(keep.concat(rk.length > 8 ? [['Other', rk.slice(8).reduce(function(t, x) { return t + x[1]; }, 0)]] : []));
    keep.forEach(function(x, i) { pos['k:' + x[0]] = i; });
    idx.push(col.map(function(c) { return ('k:' + c) in pos ? pos['k:' + c] : keep.length; }));
  });
  var joint = [];
  for (var j = 0; j + 1 < cols.length; j++) {
    var m = cats[j].map(function() { return cats[j + 1].map(function() { return 0; }); });
    idx[j].forEach(function(a, i) { m[a][idx[j + 1][i]]++; });
    joint.push(m);
  }
  return [cats, joint];
}
function _pcPct(jn, n) { var t = (jn / n * 100).toFixed(1); return t === '0.0' ? '<0.1' : t; }
function _pcCat(v) {
  if (typeof v === 'string' && v !== '') { var t = v.slice(0, 20); return (t === '(missing)' || t === 'Other') ? '"' + t + '"' : t; }
  if (typeof v === 'number' || typeof v === 'boolean') return String(v).slice(0, 20);
  return '(missing)';
}
_RENDERERS['parallel_categories'] = function(b) {
  var D = _wbDims(b), dims = D[0], notes = _wbDimNotes(D[1], D[2]);
  var total = dims.reduce(function(t, d) { return Math.max(t, d[1].length); }, 0), n = Math.min(total, 5000);
  if (total > n) notes += _hgNote((total - n) + (total - n === 1 ? ' record beyond the first 5000 was' : ' records beyond the first 5000 were') + ' not drawn.');
  var vn = _hgVersionNote(b, 'parallel_categories');
  if (dims.length < 2 || n < 1) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">Parallel categories needs at least two dimensions with values.</div>' + notes + vn);
  var N = dims.length, labs = dims.map(function(d) { return d[0]; });
  var cols = dims.map(function(d) { var c = []; for (var r = 0; r < n; r++) c.push(_pcCat(r < d[1].length ? d[1][r] : null)); return c; });
  var M = _pcModel(cols), cats = M[0], joint = M[1];
  cols.forEach(function(col, j) {
    var merged = _pcRank(col).length - 8;
    if (merged > 0) notes += _hgNote(_esc('In ' + labs[j] + ', ' + merged + (merged === 1 ? ' less common category was' : ' less common categories were') + ' grouped as Other.'));
  });
  var H = 360, FLOOR = 22, GAP = 10, top = [], hgt = [], lk = _wbKeys(labs);
  for (var j = 0; j < N; j++) {
    var k = cats[j].length, free = H - GAP * (k - 1) - FLOOR * k, ts = [], y = 0;
    var hs = cats[j].map(function(c) { return FLOOR + free * c[1] / n; });
    hs.forEach(function(h) { ts.push(y); y += h + GAP; });
    top.push(ts); hgt.push(hs);
  }
  var colOf = function(j, a) { return a === 8 ? 'var(--muted,#475569)' : 'var(--series-' + (a + 1) + ',' + _WB_COL[a % 8] + ')'; };
  var f = function(v) { return v.toFixed(1); }, paths = '', best = null;
  for (j = 0; j < N - 1; j++) {
    var x0 = 1000 * (j + 0.5) / N, x1 = 1000 * (j + 1.5) / N, xm = (x0 + x1) / 2, ya = top[j].slice();
    var inc = cats[j].map(function() { return cats[j + 1].map(function() { return 0; }); }), off = top[j + 1].slice();
    for (var b2 = 0; b2 < cats[j + 1].length; b2++) for (var a = 0; a < cats[j].length; a++) {
      var jn = joint[j][a][b2];
      if (jn) { inc[a][b2] = off[b2]; off[b2] += jn * hgt[j + 1][b2] / cats[j + 1][b2][1]; }
    }
    var g = '';
    for (a = 0; a < cats[j].length; a++) for (b2 = 0; b2 < cats[j + 1].length; b2++) {
      jn = joint[j][a][b2];
      if (!jn) continue;
      var ha = jn * hgt[j][a] / cats[j][a][1], hb = jn * hgt[j + 1][b2] / cats[j + 1][b2][1], y0 = ya[a], y1 = inc[a][b2];
      ya[a] += ha;
      var c = colOf(j, a);
      g += '<path data-cb="ribbon" data-key="' + _esc(lk[j] + '/' + cats[j][a][0] + '\u2192' + lk[j + 1] + '/' + cats[j + 1][b2][0]) + '" class="pcr" d="M' + f(x0) + ' ' + f(y0) + ' C' + f(xm) + ' ' + f(y0) + ' ' + f(xm) + ' ' + f(y1) + ' ' + f(x1) + ' ' + f(y1) +
        ' L' + f(x1) + ' ' + f(y1 + hb) + ' C' + f(xm) + ' ' + f(y1 + hb) + ' ' + f(xm) + ' ' + f(y0 + ha) + ' ' + f(x0) + ' ' + f(y0 + ha) +
        ' Z" fill="' + c + '" fill-opacity="0.4" stroke="' + c + '" stroke-opacity="0.7" stroke-width="1" vector-effect="non-scaling-stroke"/>';
      if (best === null || jn > best[0]) best = [jn, j, a, b2];
    }
    paths += '<g data-cb="ribbon" data-key="' + _esc(lk[j]) + '" style="' + _ifK(j, N - 1) + 'opacity:var(--k,1);">' + g + '</g>';
  }
  var bars = '';
  for (j = 0; j < N; j++) cats[j].forEach(function(cc, a) {
    bars += '<div data-cb="bar" data-key="' + _esc(lk[j] + '/' + cc[0]) + '" class="pcb" title="' + _esc(labs[j] + ': ' + cc[0] + ', ' + cc[1] + (cc[1] === 1 ? ' record' : ' records')) + '" style="position:absolute;left:calc(' + (100 * (j + 0.5) / N).toFixed(3) + '% - 12px);top:' +
      top[j][a].toFixed(1) + 'px;width:24px;height:' + hgt[j][a].toFixed(1) + 'px;box-sizing:border-box;border-radius:3px;background:' + colOf(j, a) +
      ';color:' + (a === 8 ? 'var(--bg,#fff)' : '#fff') + ';display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;line-height:1;' + _ifK(j, N) + _IF_FADE + '">' + (a + 1) + '</div>';
  });
  var heads = labs.map(function(l, q) { return '<div data-cb="label" data-key="' + _esc(lk[q]) + '" style="flex:1 1 0;min-width:0;text-align:center;font-size:0.75rem;font-weight:700;line-height:1.2;overflow-wrap:anywhere;padding:0 2px;"><span>' + 'ABCDEF'.charAt(q) +
    '</span><span class="pcl"> ' + _esc(l) + '</span></div>'; }).join('');
  var legend = '<ul style="list-style:none;margin:8px 0 0;padding:0;font-size:0.75rem;line-height:1.35;color:var(--muted,#475569);">' + labs.map(function(l, q) {
    return '<li style="margin:2px 0;"><b style="color:var(--text,#0F172A);">' + 'ABCDEF'.charAt(q) + ' ' + _esc(l) + '</b>: ' + cats[q].map(function(cc, a) { return (a + 1) + ' ' + _esc(cc[0]) + ' (' + cc[1] + ')'; }).join('; ') + '</li>';
  }).join('') + '</ul>';
  var big = '';
  if (best) big = ' Biggest flow: ' + labs[best[1]] + ' "' + cats[best[1]][best[2]][0] + '" to ' + labs[best[1] + 1] + ' "' + cats[best[1] + 1][best[3]][0] + '", ' + best[0] + (best[0] === 1 ? ' record' : ' records') +
    ' (' + _pcPct(best[0], n) + '%).';
  var aria = 'Parallel categories of ' + N + ' dimensions (' + labs.join(', ') + ') over ' + n + (n === 1 ? ' record.' : ' records.') + big;
  var chart = '<div class="ifpc" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>.ifpc .pcl{display:none}@container (min-width:600px){.ifpc .pcl{display:inline}}</style>' +
    '<div style="display:flex;margin-bottom:4px;">' + heads + '</div>' +
    '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;height:' + H + 'px;">' +
    '<svg viewBox="0 0 1000 ' + H + '" preserveAspectRatio="none" aria-hidden="true" focusable="false" style="position:absolute;inset:0;width:100%;height:100%;display:block;">' + paths + '</svg>' + bars + '</div>' +
    legend + '</div>';
  var rows = [];
  for (j = 0; j < N - 1; j++) for (a = 0; a < cats[j].length; a++) for (b2 = 0; b2 < cats[j + 1].length; b2++) {
    jn = joint[j][a][b2];
    if (jn) rows.push([labs[j], cats[j][a][0], labs[j + 1], cats[j + 1][b2][0], String(jn), _pcPct(jn, n) + '%']);
  }
  var members = [];
  for (j = 0; j < N; j++) _pcRank(cols[j]).slice(8).forEach(function(x) { members.push([labs[j], x[0], String(x[1])]); });
  var other = '';
  if (members.length) {
    var shown = members.slice(0, 200);
    if (members.length > 200) shown.push(['...', (members.length - 200) + ' more categories not listed', '']);
    other = _ifTable(['Dimension', 'Category grouped as Other', 'Records'], shown);
  }
  return _ifWrap(_ifTitle(b) + chart + notes + vn + _ifTable(['From dimension', 'From category', 'To dimension', 'To category', 'Records', 'Share of records'], rows) + other);
};


// ── scatter3d_static and surface_static (Plotly scatter3d / surface, wave B package 3d, preview) ─────────────────────────────
// A settled 3D view from one fixed camera: data scaled into a [-1, 1] cube, rotated to the camera (azimuth, elevation or a Plotly-style
// camera.eye), projected orthographically (or with a simple perspective) and drawn as SVG far to near (painter's algorithm). No script, no
// rotation. Labels are HTML on top of the SVG so they stay >= 12px at any width. Twin: _render_scatter3d_static in web_article.py.
var _P3_W = 480, _P3_H = 340, _P3_MX = 104, _P3_MY = 46;
var _P3_COL = ['var(--accent,#0369A1)', 'var(--series-2,#810998)', 'var(--series-3,#0F6C4F)', 'var(--series-4,#9A6120)'];
var _P3_GLYPH = ['●', '■', '▲', '◆'];
var _P3_EDGES = [[0, 1], [2, 3], [4, 5], [6, 7], [0, 2], [1, 3], [4, 6], [5, 7], [0, 4], [1, 5], [2, 6], [3, 7]];
function _p3Ok(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12; }
function _p3f(v) { var s = v.toFixed(1); return /^-0\.0$/.test(s) ? '0.0' : s; }
function _p3Round(x) { return Math.floor(x + 0.5); }
function _p3Camera(b) {
  var cam = _ifObj(b.camera), az = _ifNum(cam.azimuth, -360, 360, 45), el = _ifNum(cam.elevation, -80, 80, 30), eye = _ifObj(cam.eye);
  var ex = eye.x, ey = eye.y, ez = eye.z;
  if (_p3Ok(ex) && _p3Ok(ey) && _p3Ok(ez) && (ex !== 0 || ey !== 0 || ez !== 0)) {
    az = Math.atan2(ey, ex) * 180 / Math.PI;
    el = Math.max(-80, Math.min(80, Math.atan2(ez, Math.hypot(ex, ey)) * 180 / Math.PI));
  }
  var persp = _ifPick(cam.projection, ['orthographic', 'perspective'], 'orthographic') === 'perspective';
  var a = az * Math.PI / 180, e = el * Math.PI / 180;
  return [az, el, persp, [[-Math.sin(a), Math.cos(a), 0], [-Math.sin(e) * Math.cos(a), -Math.sin(e) * Math.sin(a), Math.cos(e)], [Math.cos(e) * Math.cos(a), Math.cos(e) * Math.sin(a), Math.sin(e)]]];
}
function _p3Proj(p, basis, persp) {
  var r = basis[0], u = basis[1], v = basis[2];
  var x = p[0] * r[0] + p[1] * r[1] + p[2] * r[2], y = p[0] * u[0] + p[1] * u[1] + p[2] * u[2], d = p[0] * v[0] + p[1] * v[1] + p[2] * v[2];
  if (persp) { var k = 5 / (5 - d); x = x * k; y = y * k; }
  return [x, y, d];
}
function _p3Scene(basis, persp) {
  var corners = [], i;
  for (i = 0; i < 8; i++) corners.push([i & 1 ? 1 : -1, i & 2 ? 1 : -1, i & 4 ? 1 : -1]);
  var pr = corners.map(function(c) { return _p3Proj(c, basis, persp); });
  var xs = pr.map(function(q) { return q[0]; }), ys = pr.map(function(q) { return q[1]; });
  var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
  var s = Math.min((_P3_W - 2 * _P3_MX) / (x1 - x0), (_P3_H - 2 * _P3_MY) / (y1 - y0));
  var ox = _P3_W / 2 - s * (x0 + x1) / 2, oy = _P3_H / 2 + s * (y0 + y1) / 2;
  return [function(p) { var q = _p3Proj(p, basis, persp); return [ox + s * q[0], oy - s * q[1], q[2]]; }, corners];
}
function _p3Norm(v, lo, hi) { return hi > lo ? 2 * (v - lo) / (hi - lo) - 1 : 0; }
function _p3Frame(screen, corners, labels, ranges) {
  var sc = corners.map(function(c) { return screen(c); }), lines = '', flines = '', i;
  var far = 0, fark = null;   // the hidden corner: only the three edges that meet there are behind the cube
  for (i = 0; i < 8; i++) { var kk = _p3Round(sc[i][2] * 1e6); if (fark === null || kk < fark) { fark = kk; far = i; } }
  _P3_EDGES.forEach(function(e) {
    var back = e[0] === far || e[1] === far;
    var ln = '<line x1="' + _p3f(sc[e[0]][0]) + '" y1="' + _p3f(sc[e[0]][1]) + '" x2="' + _p3f(sc[e[1]][0]) + '" y2="' + _p3f(sc[e[1]][1]) +
      '" stroke="var(--muted,#475569)" stroke-width="1"' + (back ? ' stroke-dasharray="3 3" opacity="0.55"' : ' opacity="0.9"') + '/>';
    if (back) lines += ln; else flines += ln;
  });
  var cx = 0, cy = 0;
  sc.forEach(function(q) { cx += q[0]; cy += q[1]; });
  cx /= 8; cy /= 8;
  var front = 0, fk = null;
  for (i = 0; i < 8; i++) { if (i & 4) continue; var k = _p3Round(sc[i][2] * 1e6); if (fk === null || k > fk) { fk = k; front = i; } }
  var cap = function(px, py, text, rng, side) {
    var left, top, tf, inner = '<div>' + _esc(rng) + '</div>';
    if (side) { left = Math.max(2, Math.min(98, (px - 8) / _P3_W * 100)); top = Math.max(6, Math.min(94, py / _P3_H * 100)); tf = 'translate(-100%,-50%);text-align:right'; var parts = rng.split(' to '); inner = '<div>' + _esc(parts[0]) + '</div><div>' + _esc('to ' + parts[1]) + '</div>'; }
    else {
      var dx = px - cx, dy = py - cy, n = Math.hypot(dx, dy) || 1, lx = px + dx / n * 30, ly = py + dy / n * 22;
      left = Math.max(18, Math.min(82, lx / _P3_W * 100)); top = Math.max(6, Math.min(94, ly / _P3_H * 100)); tf = 'translate(-50%,-50%);text-align:center';
    }
    return '<div style="position:absolute;left:' + _p3f(left) + '%;top:' + _p3f(top) + '%;transform:' + tf + ';font-size:0.75rem;line-height:1.15;color:var(--muted,#475569);white-space:nowrap;">' +
      '<div style="font-weight:700;">' + _esc(text) + '</div>' + inner + '</div>';
  };
  var caps = '', others = [front ^ 1, front ^ 2];
  [0, 1].forEach(function(axis) {
    var o = others[axis], mx = (sc[front][0] + sc[o][0]) / 2, my = (sc[front][1] + sc[o][1]) / 2, loFirst = corners[front][axis] < 0;
    caps += cap(mx, my, labels[axis], loFirst ? ranges[axis][0] + ' to ' + ranges[axis][1] : ranges[axis][1] + ' to ' + ranges[axis][0]);
  });
  var vert = 0;
  for (i = 1; i < 4; i++) if (Math.min(sc[i][0], sc[i | 4][0]) < Math.min(sc[vert][0], sc[vert | 4][0])) vert = i;
  caps += cap(Math.min(sc[vert][0], sc[vert | 4][0]), (sc[vert][1] + sc[vert | 4][1]) / 2, labels[2], ranges[2][0] + ' to ' + ranges[2][1], true);
  return [lines, caps, flines];
}
function _p3Label(b, key, name) { return b[key] ? String(b[key]).slice(0, 16) : name; }
function _p3Wrap(b, aria, svg, caps, legend, notes, table) {
  return _ifWrap(_ifTitle(b) + '<div style="max-width:640px;margin:0 auto;"><div role="img" aria-label="' + _esc(aria) + '" style="position:relative;width:100%;">' +
    '<svg viewBox="0 0 ' + _P3_W + ' ' + _P3_H + '" width="100%" style="display:block;width:100%;height:auto;" focusable="false" aria-hidden="true">' + svg + '</svg>' +
    caps + '</div>' + legend + '</div>' + notes + table);
}
function _p3Marker(shape, x, y, r, col, op, key) {
  var st = ' fill="' + col + '" fill-opacity="' + op + '" stroke="var(--bg,#fff)" stroke-width="1"', pts;
  if (shape === 0) return '<circle data-cb="node" data-key="' + key + '" cx="' + _p3f(x) + '" cy="' + _p3f(y) + '" r="' + _p3f(r) + '"' + st + '/>';
  if (shape === 1) return '<rect data-cb="node" data-key="' + key + '" x="' + _p3f(x - r) + '" y="' + _p3f(y - r) + '" width="' + _p3f(2 * r) + '" height="' + _p3f(2 * r) + '"' + st + '/>';
  if (shape === 2) pts = [[x, y - r * 1.2], [x + r * 1.1, y + r * 0.9], [x - r * 1.1, y + r * 0.9]];
  else pts = [[x, y - r * 1.25], [x + r * 1.25, y], [x, y + r * 1.25], [x - r * 1.25, y]];
  return '<polygon data-cb="node" data-key="' + key + '" points="' + pts.map(function(p) { return _p3f(p[0]) + ',' + _p3f(p[1]); }).join(' ') + '"' + st + '/>';
}
_RENDERERS['scatter3d_static'] = function(b) {
  var raw = Array.isArray(b.points) ? b.points : [], pts = [], skipped = 0, names = [], beyondSeries = 0;
  raw.slice(0, 500).forEach(function(p) {
    if (!(p && typeof p === 'object' && !Array.isArray(p) && _p3Ok(p.x) && _p3Ok(p.y) && _p3Ok(p.z))) { skipped++; return; }
    var sn = p.series ? String(p.series).slice(0, 16) : '';
    if (names.indexOf(sn) < 0) { if (names.length >= 4) { beyondSeries++; return; } names.push(sn); }
    pts.push([p.x, p.y, p.z, names.indexOf(sn), p.label ? String(p.label).slice(0, 30) : '']);
  });
  var over = raw.length - 500;
  var notes = (skipped ? _hgNote(skipped + (skipped === 1 ? ' point was' : ' points were') + ' not a usable x, y, z number triple and ' + (skipped === 1 ? 'was' : 'were') + ' left out.') : '') +
    (beyondSeries ? _hgNote(beyondSeries + (beyondSeries === 1 ? ' point' : ' points') + ' in a fifth or later series ' + (beyondSeries === 1 ? 'was' : 'were') + ' not drawn (4 series at most).') : '') +
    (over > 0 ? _hgNote(over + (over === 1 ? ' point beyond the first 500 was' : ' points beyond the first 500 were') + ' not drawn.') : '');
  if (!pts.length) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A 3D scatter needs at least one point with numbers x, y and z.</div>' + notes + _hgVersionNote(b, 'scatter3d_static'));
  var cam = _p3Camera(b), az = cam[0], el = cam[1], persp = cam[2], sceneA = _p3Scene(cam[3], persp), screen = sceneA[0], corners = sceneA[1];
  var lo = [0, 1, 2].map(function(k) { return Math.min.apply(null, pts.map(function(p) { return p[k]; })); });
  var hi = [0, 1, 2].map(function(k) { return Math.max.apply(null, pts.map(function(p) { return p[k]; })); });
  var rng = [0, 1, 2].map(function(k) { return [_bpFmt(lo[k], 3), _bpFmt(hi[k], 3)]; });
  var labels = [_p3Label(b, 'x_label', 'x'), _p3Label(b, 'y_label', 'y'), _p3Label(b, 'z_label', 'z')];
  var fr = _p3Frame(screen, corners, labels, rng), drop = b.drop_lines !== false;
  var drawn = pts.map(function(p, i) {
    var nx = _p3Norm(p[0], lo[0], hi[0]), ny = _p3Norm(p[1], lo[1], hi[1]);
    return [screen([nx, ny, _p3Norm(p[2], lo[2], hi[2])]), drop ? screen([nx, ny, -1]) : null, p[3], i];
  });
  drawn.sort(function(a, c) { return (_p3Round(a[0][2] * 1e6) - _p3Round(c[0][2] * 1e6)) || (a[3] - c[3]); });
  var bases = pts.map(function(p, k) { return p[4] || 'Point ' + (k + 1); });
  var pkeys = bases.map(function(t, k) { return _esc(bases.indexOf(t) === bases.lastIndexOf(t) ? t : t + ' #' + (k + 1)); });
  var body = '';
  drawn.forEach(function(d) {
    var q = d[0], base = d[1], s = d[2], t = Math.max(0, Math.min(1, (q[2] + 1.8) / 3.6));
    if (base) body += '<line x1="' + _p3f(q[0]) + '" y1="' + _p3f(q[1]) + '" x2="' + _p3f(base[0]) + '" y2="' + _p3f(base[1]) + '" stroke="' + _P3_COL[s] + '" stroke-width="1" opacity="0.3"/>';
    body += _p3Marker(s, q[0], q[1], 5 + 3 * t, _P3_COL[s], (0.55 + 0.45 * t).toFixed(2), pkeys[d[3]]);
  });
  var n = pts.length, named = [];
  names.forEach(function(nm, k) { if (nm) named.push(k); });
  var legend = named.length ? '<div style="display:flex;flex-wrap:wrap;gap:4px 14px;justify-content:center;font-size:0.75rem;margin-top:6px;">' +
    named.map(function(k) { return '<span><span aria-hidden="true" style="color:' + _P3_COL[k] + ';">' + _P3_GLYPH[k] + '</span> ' + _esc(names[k]) + '</span>'; }).join('') + '</div>' : '';
  var aria = '3D scatter of ' + n + (n === 1 ? ' point' : ' points') + (names.length > 1 ? ' in ' + names.length + ' series' : '') + '. ' +
    labels[0] + ' from ' + rng[0][0] + ' to ' + rng[0][1] + ', ' + labels[1] + ' from ' + rng[1][0] + ' to ' + rng[1][1] + ', ' + labels[2] + ' from ' + rng[2][0] + ' to ' + rng[2][1] +
    '. Fixed view from azimuth ' + _bpFmt(_p3Round(az), 0) + ' and elevation ' + _bpFmt(_p3Round(el), 0) + ' degrees' + (persp ? ', perspective' : '') + '.';
  var table = _ifTable(['Point', labels[0], labels[1], labels[2], 'Series'],
    pts.map(function(p, k) { return [p[4] || 'Point ' + (k + 1), _bpFmt(p[0], 3), _bpFmt(p[1], 3), _bpFmt(p[2], 3), names[p[3]] || '-']; }));
  return _p3Wrap(b, aria, fr[0] + body + fr[2], fr[1], legend, notes + _hgVersionNote(b, 'scatter3d_static'), table);
};
_RENDERERS['surface_static'] = function(b) {
  var zr = Array.isArray(b.z) ? b.z : [], rowsIn = zr.slice(0, 30).filter(function(r) { return Array.isArray(r); }), overRows = zr.length - 30;
  var maxLen = rowsIn.reduce(function(m, r) { return Math.max(m, r.length); }, 0), ncol = Math.min(30, maxLen), overCols = maxLen - 30;
  var grid = rowsIn.map(function(r) {
    var o = [], j;
    for (j = 0; j < ncol; j++) o.push(_p3Ok(r[j]) ? r[j] : null);
    return o;
  });
  var nrow = grid.length, missing = 0, cells = nrow * ncol, flat = [];
  grid.forEach(function(r) { r.forEach(function(v) { if (v === null) missing++; else flat.push(v); }); });
  var notes = (overRows > 0 ? _hgNote(overRows + (overRows === 1 ? ' row beyond the first 30 was' : ' rows beyond the first 30 were') + ' not drawn.') : '') +
    (overCols > 0 ? _hgNote(overCols + (overCols === 1 ? ' column beyond the first 30 was' : ' columns beyond the first 30 were') + ' not drawn.') : '');
  if (nrow < 2 || ncol < 2 || missing === cells) return _ifWrap(_ifTitle(b) + '<div style="' + _ifCard() + '">A surface needs a grid z of at least 2 rows by 2 columns of numbers.</div>' + notes + _hgVersionNote(b, 'surface_static'));
  if (missing) notes += _hgNote(missing + (missing === 1 ? ' grid value was' : ' grid values were') + ' not a usable number and the faces touching ' + (missing === 1 ? 'it were' : 'them were') + ' left open.');
  var axis = function(key, len) {
    var v = b[key], a = Array.isArray(v) ? v.slice(0, len) : [], k, o = [];
    if (a.length === len && a.every(_p3Ok)) return a;
    for (k = 0; k < len; k++) o.push(k);
    return o;
  };
  var xs = axis('x', ncol), ys = axis('y', nrow);
  var zlo = Math.min.apply(null, flat), zhi = Math.max.apply(null, flat), xlo = Math.min.apply(null, xs), xhi = Math.max.apply(null, xs), ylo = Math.min.apply(null, ys), yhi = Math.max.apply(null, ys);
  var cam = _p3Camera(b), az = cam[0], el = cam[1], persp = cam[2], sceneA = _p3Scene(cam[3], persp), screen = sceneA[0], corners = sceneA[1];
  var rng = [[_bpFmt(xlo, 3), _bpFmt(xhi, 3)], [_bpFmt(ylo, 3), _bpFmt(yhi, 3)], [_bpFmt(zlo, 3), _bpFmt(zhi, 3)]];
  var labels = [_p3Label(b, 'x_label', 'x'), _p3Label(b, 'y_label', 'y'), _p3Label(b, 'z_label', 'z')];
  var fr = _p3Frame(screen, corners, labels, rng), i, j;
  var P = grid.map(function(r, i2) { return r.map(function(v, j2) { return v === null ? null : screen([_p3Norm(xs[j2], xlo, xhi), _p3Norm(ys[i2], ylo, yhi), _p3Norm(v, zlo, zhi)]); }); });
  var faces = [];
  for (i = 0; i < nrow - 1; i++) for (j = 0; j < ncol - 1; j++) {
    var q = [P[i][j], P[i][j + 1], P[i + 1][j + 1], P[i + 1][j]];
    if (q.some(function(c) { return c === null; })) continue;
    var h = (grid[i][j] + grid[i][j + 1] + grid[i + 1][j + 1] + grid[i + 1][j]) / 4;
    faces.push([_p3Round((q[0][2] + q[1][2] + q[2][2] + q[3][2]) / 4 * 1e6), faces.length, q, h, i, j]);
  }
  faces.sort(function(a, c) { return (a[0] - c[0]) || (a[1] - c[1]); });
  var body = '';
  faces.forEach(function(f) {
    var t = zhi > zlo ? (f[3] - zlo) / (zhi - zlo) : 0.5;
    body += '<polygon data-cb="tile" data-key="r' + (f[4] + 1) + 'c' + (f[5] + 1) + '" points="' + f[2].map(function(c) { return _p3f(c[0]) + ',' + _p3f(c[1]); }).join(' ') + '" fill="var(--accent,#0369A1)" fill-opacity="' + (0.25 + 0.7 * t).toFixed(2) +
      '" stroke="var(--bg,#fff)" stroke-width="0.6" stroke-linejoin="round"/>';
  });
  var hiAt = null, loAt = null;
  for (i = 0; i < nrow; i++) for (j = 0; j < ncol; j++) {
    var v = grid[i][j];
    if (v === null) continue;
    if (hiAt === null || v > hiAt[0]) hiAt = [v, i, j];
    if (loAt === null || v < loAt[0]) loAt = [v, i, j];
  }
  var aria = '3D surface of ' + nrow + ' by ' + ncol + ' values. ' + labels[2] + ' from ' + rng[2][0] + ' (at ' + labels[0] + ' ' + _bpFmt(xs[loAt[2]], 3) + ', ' + labels[1] + ' ' + _bpFmt(ys[loAt[1]], 3) +
    ') to ' + rng[2][1] + ' (at ' + labels[0] + ' ' + _bpFmt(xs[hiAt[2]], 3) + ', ' + labels[1] + ' ' + _bpFmt(ys[hiAt[1]], 3) + '). Fixed view from azimuth ' + _bpFmt(_p3Round(az), 0) +
    ' and elevation ' + _bpFmt(_p3Round(el), 0) + ' degrees' + (persp ? ', perspective' : '') + '.';
  var legend = '<div style="text-align:center;font-size:0.75rem;margin-top:6px;color:var(--muted,#475569);">Stronger colour is higher: ' + _esc(labels[2]) + ' ' + rng[2][0] + ' (faint) to ' + rng[2][1] + ' (solid).</div>';
  var table = _ifTable([labels[1] + ' \\ ' + labels[0]].concat(xs.map(function(x) { return _bpFmt(x, 3); })),
    grid.map(function(r, i2) { return [_bpFmt(ys[i2], 3)].concat(r.map(function(v) { return v === null ? '-' : _bpFmt(v, 3); })); }));
  return _p3Wrap(b, aria, fr[0] + body + fr[2], fr[1], legend, notes + _hgVersionNote(b, 'surface_static'), table);
};
