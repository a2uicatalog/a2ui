// ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
// Motion candidates from three keynote recordings (2026-10-10, stage: preview). Measured with a2ui-private/motion-probe; the numbers in
// the comments are what the footage showed. All of these are plain HTML and CSS driven by the film's two dials, like the other motion_* atoms:
//   --p  build progress 0..1 (default 1)      --s  step 0..1 (default 1)
// A standalone render is the finished picture; reduced motion needs no code because the end state is simply the end of the clock.
// ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

// ── motion_lit: ghost to lit ─────────────────────────────────────────────────────────────────────────────────
// Cards appear as faint outlines, then their text at low opacity (p builds them one after another), then each lights in turn as the step dial
// runs (s), with a coloured highlight travelling once around the border of the card that is lighting.
var _MLIT_LAYOUT = {row: 'display:flex;gap:GAPpx;align-items:stretch;', column: 'display:flex;flex-direction:column;gap:GAPpx;', grid: 'display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:GAPpx;'};
_RENDERERS['motion_lit'] = function(b) {
  var blocks = Array.isArray(b.blocks) ? b.blocks.slice(0, 8) : [], n = blocks.length || 1;
  var ac = _moInk(b, 'accent', '#5b8cff'), rgb = _ffRgb(ac), G = _ffNum(b.ghost, 0.3, 0, 1, 2), gap = _ffInt(b.gap, 14, 0, 60), edge = b.edge !== false;
  var lay = _ffPick(b.layout, _MLIT_LAYOUT, 'row').replace('GAP', String(gap));
  var css = '<style>.mlit-i{position:relative;box-sizing:border-box;border-radius:14px;padding:12px 14px;min-width:0;flex:1 1 0}' +
    (edge ? '.mlit-i::before{content:"";position:absolute;inset:-1px;border-radius:inherit;padding:2px;pointer-events:none;' +
      'background:conic-gradient(from calc(var(--mlk)*360deg),transparent 0,transparent 55%,rgba(var(--mlc),0.95) 80%,transparent 100%);' +
      '-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask:linear-gradient(#000 0 0) content-box exclude,linear-gradient(#000 0 0);' +
      'opacity:calc(var(--mlk)*(1 - var(--mlk))*4)}' : '') + '</style>';
  var items = blocks.map(function(blk, i) {
    var st = '--mlg:clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1);--mlk:clamp(0,calc(var(--s,1)*' + n + ' - ' + i + '),1);--mlc:' + rgb + ';' +
      'opacity:calc(var(--mlg)*(' + G + ' + (1 - ' + G + ')*var(--mlk)));' +
      'border:1px solid rgba(' + rgb + ',calc(0.25 + 0.75*var(--mlk)));box-shadow:0 0 calc(18px*var(--mlk)) rgba(' + rgb + ',calc(0.5*var(--mlk)))';
    return '<div class="mlit-i" style="' + st + '">' + _moChild(blk) + '</div>';
  }).join('');
  return css + '<div style="' + lay + '">' + items + '</div>';
};

// ── motion_arcs: a mark built from coloured arcs ─────────────────────────────────────────────────────────────
// From the keynote's logo build (measured 0.7 s): a partial ring sweeps in with a blur trail and settles, a second arc of another colour
// follows, and together they close into a mark. One to four arcs, each its own radius, start, sweep and colour (or a two-colour gradient along
// the arc); each enters in turn as p runs, turning in from a rotation and blurred, so the finished picture is simply the arcs at rest.
function _moArcsSvg(b, uid, emSize) {
  var arcs = Array.isArray(b.arcs) ? b.arcs.slice(0, 4) : [], n = arcs.length || 1, defs = '', body = '', i;
  if (!arcs.length) arcs = [{}];
  for (i = 0; i < arcs.length; i++) {
    var a = (arcs[i] && typeof arcs[i] === 'object') ? arcs[i] : {};
    var c1 = _ffHex(a.color, i % 2 ? '#34e0c3' : '#5b8cff'), c2 = _ffHex(a.color2, ''), r = _ffNum(a.r, 34 - i * 8, 8, 48, 1), from = _ffInt(a.from, 200 + i * 140, 0, 359), sweep = _ffInt(a.sweep, 220, 20, 340);
    var w = _ffNum(a.width, 11, 3, 24, 1), dx = _ffNum(a.dx, 0, -30, 30, 1), dy = _ffNum(a.dy, 0, -30, 30, 1), spin = _ffInt(a.spin, -140, -720, 720), blur = _ffInt(a.blur, 6, 0, 24);
    var cx = _ffNum(50 + parseFloat(dx), 50, 5, 95, 1), cy = _ffNum(50 + parseFloat(dy), 50, 5, 95, 1), gid = 'mar' + uid + i;
    if (c2) defs += '<linearGradient id="' + gid + '" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="' + c1 + '"/><stop offset="1" stop-color="' + c2 + '"/></linearGradient>';
    var k = 'clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1)';
    body += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="' + (c2 ? 'url(#' + gid + ')' : c1) + '" stroke-width="' + w + '" stroke-linecap="round" pathLength="360" stroke-dasharray="' + sweep + ' ' + (360 - sweep) + '" ' +
      'style="--ak:' + k + ';transform-box:fill-box;transform-origin:50% 50%;transform:rotate(calc(' + from + 'deg + (1 - var(--ak))*' + spin + 'deg));opacity:var(--ak);filter:blur(calc((1 - var(--ak))*' + blur + 'px))"/>';
  }
  return '<svg viewBox="0 0 100 100" ' + (emSize ? 'width="' + emSize + 'em" height="' + emSize + 'em" style="display:inline-block;vertical-align:-0.18em;overflow:visible;"' : 'width="100%" style="display:block;overflow:visible;"') + ' focusable="false"' + (emSize ? ' aria-hidden="true"' : ' role="img" aria-label="' + _ifLabel(b.label) + '"') + '>' + (defs ? '<defs>' + defs + '</defs>' : '') + body + '</svg>';
}
function _ifLabel(v) { return _esc(String(v === undefined || v === null || v === '' ? 'Mark' : v).slice(0, 60)); }
_RENDERERS['motion_arcs'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  return '<div style="width:100%;">' + _moArcsSvg(b, uid, 0) + '</div>';
};

// ── motion_lockup: type around an inline mark, with the block staying centred ────────────────────────────────
// From the keynote: "The new way to cloud." builds around a small mark that sits inside a word (measured 0.35 to 0.4 s), and "Helping companies"
// gains a third line while the whole block glides up half a line to stay centred. lines is an array of lines; each line is an array of tokens,
// each a word (a string) or {mark: {arcs: [...]}} for an inline mark. The mark appears first and the words arrive in order of distance from it
// (left to right when there is no mark). Every line is laid out in its final place; the block is shifted by half the height of the lines that
// have not arrived yet, so the visible part is always centred, smoothly, with no jump.
_RENDERERS['motion_lockup'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6), rawLines = Array.isArray(b.lines) ? b.lines.slice(0, 4) : [], lines = [], total = 0, mark = null, markLine = -1, markPos = -1, li, ti;
  for (li = 0; li < rawLines.length; li++) {
    var toks = Array.isArray(rawLines[li]) ? rawLines[li].slice(0, 8) : [], row = [];
    for (ti = 0; ti < toks.length && total < 24; ti++) {
      var t = toks[ti];
      if (t && typeof t === 'object' && !Array.isArray(t) && t.mark && typeof t.mark === 'object' && !mark) { mark = t.mark; markLine = lines.length; markPos = row.length; row.push({mark: true}); total++; }
      else if (typeof t === 'string' && t.trim()) { row.push({w: t.trim().slice(0, 24)}); total++; }
    }
    if (row.length) lines.push(row);
  }
  if (!lines.length) lines = [[{w: 'Text'}]];
  // reveal order: the mark first, then by distance from it (a line away costs more than a word away), else reading order
  var flat = [], oi = 0;
  lines.forEach(function(row, l) { row.forEach(function(tk, p) { flat.push({l: l, p: p, tk: tk}); }); });
  flat.forEach(function(f, i) { f.d = markLine >= 0 ? (f.tk.mark ? -1 : Math.abs(f.l - markLine) * 4 + Math.abs(f.p - markPos)) : i; f.i = i; });
  flat.sort(function(a, c) { return a.d - c.d || a.i - c.i; });
  flat.forEach(function(f, i) { f.tk.o = i; });
  var T = flat.length, size = _ffInt(b.size, 72, 14, 300), lh = _ffNum(b.line_height, 1.15, 0.9, 2, 2), weight = _ffPick(b.weight, _FF_WEIGHTS, 'bold'), font = _ffPick(b.font, _FF_FONTS, 'sans');
  var color = _moInk(b, 'color', 'var(--text,#0f172a)'), align = _ffPick(b.align, {start: 'flex-start', center: 'center', end: 'flex-end'}, 'center'), settle = b.settle !== false;
  var LH = size * parseFloat(lh), N = lines.length, qv = '', sum = [];
  lines.forEach(function(row, l) {
    var first = Math.min.apply(null, row.map(function(tk) { return tk.o; }));
    qv += '--q' + l + ':clamp(0,calc(var(--p,1)*' + (T + 2) + ' - ' + first + '),1);'; sum.push('var(--q' + l + ')');
  });
  var shift = settle && N > 1 ? 'transform:translateY(calc((' + N + ' - (' + sum.join(' + ') + '))*' + _ffNum(LH * 0.5, 0, 0, 1000, 2) + 'px));' : '';
  var body = lines.map(function(row) {
    return '<div style="display:flex;justify-content:' + align + ';align-items:baseline;gap:0.28em;white-space:nowrap;">' + row.map(function(tk) {
      var st = '--u:clamp(0,calc(var(--p,1)*' + (T + 2) + ' - ' + tk.o + '),1);opacity:var(--u);filter:blur(calc((1 - var(--u))*8px));transform:translateY(calc((1 - var(--u))*0.18em));display:inline-block;';
      return tk.mark ? '<span style="' + st + '">' + _moArcsSvg(mark, uid, 0.95) + '</span>' : '<span style="' + st + '">' + _esc(tk.w) + '</span>';
    }).join('') + '</div>';
  }).join('');
  var plain = lines.map(function(row) { return row.map(function(tk) { return tk.mark ? (mark.label ? String(mark.label).slice(0, 40) : 'mark') : tk.w; }).join(' '); }).join(' ');
  return '<div role="img" aria-label="' + _esc(plain) + '" style="font-family:' + font + ';font-weight:' + weight + ';font-size:' + size + 'px;line-height:' + lh + ';color:' + color + ';' + qv + shift + '"><div aria-hidden="true">' + body + '</div></div>';
};

// ── motion_collage: a panel whose set of tiles swaps ─────────────────────────────────────────────────────────
// From the keynote's stage screen (measured about 0.9 s a swap: out 0.3 s, a near-blank hold of 0.2 s, in 0.4 s): the tiles do not fly. They blur
// and wash out into the panel colour, faint blurred ghosts of the next layout show through, and the new tiles deblur in, in a different layout, while the
// panel's own silhouette changes (a notch in another corner). The step dial s runs across the sets (u = s x (sets - 1)); within each unit step the
// first third is the way out, the next fifth the hold on ghosts, the rest the way in. p builds the tiles of the first set. Standalone shows the last set.
function _clObj(v) { return (v && typeof v === 'object' && !Array.isArray(v)) ? v : {}; }
var _CL_FILLS = ['#2c3e66', '#7a3b6e', '#2f7d63', '#9a6120', '#3b4a6b', '#5a3d2b', '#1f5f7a', '#6b2d3c'];
var _CL_PANELS = {panel: 1, notch: 1, step: 1, tab: 1};
_RENDERERS['motion_collage'] = function(b) {
  var src = (Array.isArray(b.sets) ? b.sets : []).slice(0, 4), sets = [], si, ti;
  for (si = 0; si < src.length; si++) {
    var s = _clObj(src[si]), tl = (Array.isArray(s.tiles) ? s.tiles : []).slice(0, 8), tiles = [];
    for (ti = 0; ti < tl.length; ti++) {
      var t = _clObj(tl[ti]);
      tiles.push({x: _ffNum(t.x, 10, 0, 100, 1), y: _ffNum(t.y, 10, 0, 100, 1), w: _ffNum(t.w, 30, 2, 100, 1), h: _ffNum(t.h, 30, 2, 100, 1), fill: _ffHex(t.fill, _CL_FILLS[(si * 3 + ti) % 8]), fill2: _ffHex(t.fill2, ''),
        label: _moStr(t.label, 28), block: (t.block && typeof t.block === 'object' && !Array.isArray(t.block)) ? t.block : null});
    }
    sets.push({tiles: tiles, panel: _moOwn(_CL_PANELS, s.panel, 'panel')});
  }
  while (sets.length < 2) sets.push({tiles: [], panel: 'panel'});
  var N = sets.length, blur = _ffInt(b.blur, 10, 0, 30), G = _ffNum(b.ghost, 0.18, 0, 1, 2), radius = _ffInt(b.radius, 10, 0, 40), asp = _ffNum(b.aspect, 1.78, 0.5, 3, 2), pfill = _moInk(b, 'fill', '#f3e8ec');
  var u = 'var(--cu)', layers = '', plain = [], idx = 0;
  sets.forEach(function(st, j) {
    var vars = '--ci:clamp(0,calc((' + u + ' - ' + j + ' + 0.45)/0.45),1);--co:clamp(0,calc((' + u + ' - ' + j + ')/0.33),1);--cg:calc(clamp(0,calc((' + u + ' - ' + j + ' + 0.8)/0.2),1)*(1 - var(--ci)));';
    var show = 'calc(var(--ci)*(1 - var(--co)))';
    var wrap = 'position:absolute;inset:0;pointer-events:none;' + vars + 'opacity:max(' + show + ',calc(var(--cg)*' + G + '));filter:blur(calc((1 - ' + show + ')*' + blur + 'px));';
    var inner = st.tiles.map(function(t) {
      var n = idx++, bg = t.fill2 ? 'linear-gradient(135deg,' + t.fill + ',' + t.fill2 + ')' : t.fill;
      var body = t.block ? _moRender(t.block) : (t.label ? '<span>' + _esc(t.label) + '</span>' : '');
      if (t.label) plain.push(t.label);
      return '<div style="position:absolute;left:' + t.x + '%;top:' + t.y + '%;width:' + t.w + '%;height:' + t.h + '%;box-sizing:border-box;border-radius:' + radius + 'px;background:' + bg + ';color:#fff;font-weight:700;font-size:0.85rem;' +
        'display:flex;align-items:flex-end;padding:8px 10px;overflow:hidden;opacity:clamp(0,calc(var(--p,1)*' + (8 * N + 1) + ' - ' + n + '),1);">' + body + '</div>';
    }).join('');
    layers += '<div style="' + wrap + '">' + inner + '</div>';
  });
  // the panel silhouette: the 48-point outlines of the sets' panel shapes, mixed by the same step dial as the tiles change
  var pts = [], i, j;
  for (i = 0; i < 96; i += 2) {
    var x = _moT10(_MO_SHAPES[sets[0].panel][i]) + '%', y = _moT10(_MO_SHAPES[sets[0].panel][i + 1]) + '%';
    for (j = 1; j < N; j++) {
      var dx = _MO_SHAPES[sets[j].panel][i] - _MO_SHAPES[sets[j - 1].panel][i], dy = _MO_SHAPES[sets[j].panel][i + 1] - _MO_SHAPES[sets[j - 1].panel][i + 1];
      var m = '*clamp(0,calc((' + u + ' - ' + (j - 1) + ' - 0.2)/0.6),1)';
      if (dx) x += ' + ' + _moT10(dx) + '%' + m;
      if (dy) y += ' + ' + _moT10(dy) + '%' + m;
    }
    pts.push('calc(' + x + ') calc(' + y + ')');
  }
  var poly = 'polygon(' + pts.join(',') + ')';
  return '<div role="group" aria-label="' + _esc(typeof b.title === 'string' && b.title ? b.title.slice(0, 80) : 'Collage') + '" style="position:relative;width:100%;aspect-ratio:' + asp + ';--cu:calc(var(--s,1)*' + (N - 1) + ');">' +
    '<div aria-hidden="true" style="position:absolute;inset:0;background:' + pfill + ';clip-path:' + poly + ';-webkit-clip-path:' + poly + ';"></div>' +
    '<div aria-hidden="true" style="position:absolute;inset:0;">' + layers + '</div>' +
    (plain.length ? '<ul style="' + _IF_SR + '">' + plain.map(function(p) { return '<li>' + _esc(p) + '</li>'; }).join('') + '</ul>' : '') + '</div>';
};
