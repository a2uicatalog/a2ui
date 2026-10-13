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
  return '<div style="width:100%;">' + _moArcsSvg({arcs: b.arcs, label: b.label}, uid, 0) + '</div>';
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
// Named tile layouts, [x, y, w, h] in percent of the panel: a set that names one needs no coordinates; a tile that gives its own x, y, w or h overrides that part.
var _CL_LAYOUTS = {
  hero: [[5, 6, 44, 52], [52, 6, 43, 24], [52, 34, 43, 24], [5, 62, 90, 30]],
  rail: [[5, 6, 27, 86], [35, 6, 60, 40], [35, 50, 28, 42], [66, 50, 29, 42]],
  grid: [[5, 6, 43, 40], [52, 6, 43, 40], [5, 52, 43, 40], [52, 52, 43, 40]],
  split: [[5, 6, 43, 86], [52, 6, 43, 86]],
  stack: [[5, 6, 90, 26], [5, 37, 90, 26], [5, 68, 90, 26]],
  header: [[5, 6, 90, 22], [5, 32, 43, 60], [52, 32, 43, 60]],
  trio: [[5, 6, 28, 86], [36, 6, 28, 86], [67, 6, 28, 86]],
  mosaic: [[5, 6, 56, 52], [64, 6, 31, 24], [64, 34, 31, 24], [5, 62, 28, 30], [36, 62, 28, 30], [67, 62, 28, 30]]
};
_RENDERERS['motion_collage'] = function(b) {
  var src = (Array.isArray(b.sets) ? b.sets : []).slice(0, 4), sets = [], si, ti;
  for (si = 0; si < src.length; si++) {
    var s = _clObj(src[si]), tl = (Array.isArray(s.tiles) ? s.tiles : []).slice(0, 8), tiles = [];
    for (ti = 0; ti < tl.length; ti++) {
      var t = _clObj(tl[ti]);
      var lay = _moOwn(_CL_LAYOUTS, s.layout, '') ? (_CL_LAYOUTS[s.layout][ti] || [10, 10, 30, 30]) : [10, 10, 30, 30];
      tiles.push({x: _ffNum(t.x, lay[0], 0, 100, 1), y: _ffNum(t.y, lay[1], 0, 100, 1), w: _ffNum(t.w, lay[2], 2, 100, 1), h: _ffNum(t.h, lay[3], 2, 100, 1), fill: _ffHex(t.fill, _CL_FILLS[(si * 3 + ti) % 8]), fill2: _ffHex(t.fill2, ''),
        label: _moStr(t.label, 28), image: _moImg(t.image), block: (t.block && typeof t.block === 'object' && !Array.isArray(t.block)) ? t.block : null});
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
      var pic = t.image ? '<img src="' + _esc(t.image) + '" alt="" loading="lazy" referrerpolicy="no-referrer" style="position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;">' : '';
      var body = pic + (t.block ? _moRender(t.block) : (t.label ? '<span style="position:relative;' + (t.image ? 'background:rgba(8,10,20,0.62);padding:2px 8px;border-radius:6px;' : '') + '">' + _esc(t.label) + '</span>' : ''));
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

// ── second batch from the keynote recordings (2026-10-10): bubbles, beats, pattern, dock, fit ───────────────────────────────────────────────
// Accessibility rules shared by these five: decorative layers are aria-hidden; anything that carries words has one accessible name or is real text; every dial
// defaults to the finished picture; no endless loops (movement is the film's dial, never a CSS animation); colour never carries the only meaning.
function _bxList(v, max) { return Array.isArray(v) ? v.slice(0, max) : []; }
function _bxSeed(seed, i, k) { var x = Math.sin((seed + 1) * 12.9898 + i * 78.233 + k * 37.719) * 43758.5453; return x - Math.floor(x); }

// motion_bubbles: translucent drifting spheres. Position, size and drift come from a seed, so every render is identical.
_RENDERERS['motion_bubbles'] = function(b) {
  var n = _ffInt(b.count, 7, 2, 14), seed = _ffInt(b.seed, 7, 0, 999), size = _ffInt(b.size, 16, 4, 40), drift = _ffInt(b.drift, 14, 0, 60), asp = _ffNum(b.aspect, 1.78, 0.5, 3, 2);
  var c1 = _ffHex(b.color, '#8ad8ff'), c2 = _ffHex(b.color2, '#ff9be8'), out = '', i;
  for (i = 0; i < n; i++) {
    var d = Math.round(size * (0.55 + _bxSeed(seed, i, 3) * 0.9) * 10) / 10, x = Math.round((4 + _bxSeed(seed, i, 1) * (92 - d * 0.56)) * 10) / 10, y = Math.round((6 + _bxSeed(seed, i, 2) * 80) * 10) / 10;
    var dx = Math.round((_bxSeed(seed, i, 4) - 0.5) * 2 * drift * 10) / 10, dy = Math.round((_bxSeed(seed, i, 5) - 0.5) * 2 * drift * 10) / 10, hue = Math.round(_bxSeed(seed, i, 6) * 360);
    out += '<span style="position:absolute;left:' + x + '%;top:' + y + '%;width:' + d + '%;aspect-ratio:1;border-radius:50%;box-sizing:border-box;'
      + 'background:radial-gradient(circle at 30% 26%,rgba(255,255,255,0.9),rgba(255,255,255,0) 34%),conic-gradient(from ' + hue + 'deg,' + c1 + ',' + c2 + ',' + c1 + ');'
      + 'box-shadow:inset 0 0 0 1px rgba(255,255,255,0.55),inset -0.4em -0.5em 1.2em rgba(255,255,255,0.35);'
      + '--bi:clamp(0,calc(var(--p,1)*' + (n + 2) + ' - ' + i + '),1);opacity:calc(var(--bi)*0.72);'
      + 'transform:translate(calc(var(--s,1)*' + dx + 'cqw),calc(var(--s,1)*' + dy + 'cqw)) scale(calc(0.4 + var(--bi)*0.6));"></span>';
  }
  var named = typeof b.label === 'string' && b.label;
  return '<div ' + (named ? 'role="img" aria-label="' + _esc(_moStr(b.label, 60)) + '"' : 'aria-hidden="true"') + ' style="position:relative;width:100%;aspect-ratio:' + asp + ';container-type:inline-size;overflow:hidden;pointer-events:none;">' + out + '</div>';
};

// motion_beats: one element that is restyled on every beat (the keynote countdown: a number, a colour field, a shape, a typeface, per beat).
// Flash caution: a hard cut between very different colour fields is a flashing hazard if beats come faster than about 0.33 s; the engine cannot know the
// film's clock, so transition "fade" is offered and the notes say so.
var _BX_FACES = {sans: 1, serif: 1, mono: 1, display: 1};
_RENDERERS['motion_beats'] = function(b) {
  var src = _bxList(b.items, 12), items = [], i;
  for (i = 0; i < src.length; i++) { var o = _clObj(src[i]); items.push({text: _moStr(o.text, 24), bg: _ffHex(o.bg, _CL_FILLS[i % 8]), color: _ffHex(o.color, '#ffffff'), font: _ffPick(o.font, _FF_FONTS, 'sans'), shape: _moOwn(_MO_SHAPES, o.shape, '')}); }
  while (items.length < 2) items.push({text: items.length ? '' : 'A', bg: '#26346a', color: '#ffffff', font: _FF_FONTS.sans, shape: ''});
  var N = items.length, size = _ffInt(b.size, 160, 24, 400), asp = _ffNum(b.aspect, 1.78, 0.5, 3, 2), fade = b.transition === 'fade', w = fade ? '0.2' : '0.001', weight = _ffPick(b.weight, _FF_WEIGHTS, 'black'), layers = '';
  var u = 'calc(var(--s,1)*' + N + ')', plain = [];
  items.forEach(function(it, j) {
    var inn = j === 0 ? '1' : 'clamp(0,calc((' + u + ' - ' + j + ')/' + w + '),1)', outt = j === N - 1 ? '1' : '(1 - clamp(0,calc((' + u + ' - ' + (j + 1) + ' + ' + w + ')/' + w + '),1))';
    var blob = '';
    if (it.shape) {
      var pts = [], k; for (k = 0; k < 96; k += 2) pts.push(_moT10(_MO_SHAPES[it.shape][k]) + '% ' + _moT10(_MO_SHAPES[it.shape][k + 1]) + '%');
      blob = '<span style="position:absolute;left:50%;top:50%;height:86%;aspect-ratio:1;transform:translate(-50%,-50%);background:' + it.color + ';opacity:0.18;clip-path:polygon(' + pts.join(',') + ');-webkit-clip-path:polygon(' + pts.join(',') + ');"></span>';
    }
    layers += '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:' + it.bg + ';color:' + it.color + ';opacity:calc(' + inn + '*' + outt + ');">' + blob
      + '<span style="position:relative;font-family:' + it.font + ';font-weight:' + weight + ';font-size:' + size + 'px;line-height:1;white-space:nowrap;">' + _esc(it.text) + '</span></div>';
    if (it.text) plain.push(it.text);
  });
  return '<div role="img" aria-label="' + _esc(plain.join(', ') || 'Sequence') + '" style="position:relative;width:100%;aspect-ratio:' + asp + ';overflow:hidden;opacity:clamp(0,calc(var(--p,1)*4),1);"><div aria-hidden="true" style="position:absolute;inset:0;">' + layers + '</div></div>';
};

// motion_pattern: a tilted field of repeated text that slides with the step dial; one row, one repeat gives a single rotated word.
_RENDERERS['motion_pattern'] = function(b) {
  var text = _moStr(b.text, 28) || 'Text', rows = _ffInt(b.rows, 5, 1, 8), rep = _ffInt(b.repeat, 6, 1, 10), ang = _ffInt(b.angle, -20, -90, 90), size = _ffInt(b.size, 56, 14, 200), slide = _ffInt(b.slide, 24, 0, 100);
  var asp = _ffNum(b.aspect, 1.78, 0.5, 3, 2), color = _moInk(b, 'color', 'currentColor'), weight = _ffPick(b.weight, _FF_WEIGHTS, 'bold'), font = _ffPick(b.font, _FF_FONTS, 'sans'), out = '', r, c;
  for (r = 0; r < rows; r++) {
    var row = '';
    for (c = 0; c < rep; c++) row += '<span style="padding-right:0.6em;">' + _esc(text) + '</span>';
    out += '<div style="white-space:nowrap;text-align:center;transform:translateX(calc(var(--s,1)*' + (r % 2 ? slide : -slide) + '%));opacity:clamp(0,calc(var(--p,1)*' + (rows + 1) + ' - ' + r + '),1);">' + row + '</div>';
  }
  var name = typeof b.label === 'string' && b.label ? _moStr(b.label, 80) : text;
  return '<div role="img" aria-label="' + _esc(name) + '" style="position:relative;width:100%;aspect-ratio:' + asp + ';overflow:hidden;"><div aria-hidden="true" style="position:absolute;left:50%;top:50%;width:200%;transform:translate(-50%,-50%) rotate(' + ang + 'deg);'
    + 'font-family:' + font + ';font-weight:' + weight + ';font-size:' + size + 'px;line-height:1.2;color:' + color + ';">' + out + '</div></div>';
};

// motion_dock: icons in a pill with a highlight that travels to the active one. A real list; each glyph is decorative and each item has a text name.
_RENDERERS['motion_dock'] = function(b) {
  var src = _bxList(b.items, 7), items = [], i;
  for (i = 0; i < src.length; i++) { var o = _clObj(src[i]); items.push({glyph: _moStr(o.glyph, 2), label: _moStr(o.label, 28) || ('Item ' + (i + 1)), fill: _ffHex(o.fill, _CL_FILLS[i % 8])}); }
  while (items.length < 2) items.push({glyph: '', label: 'Item ' + (items.length + 1), fill: _CL_FILLS[items.length % 8]});
  var N = items.length, cell = _ffInt(b.size, 56, 24, 120), pad = Math.round(cell * 0.2), bg = _moInk(b, 'fill', '#eef1f7'), ring = _moInk(b, 'accent', '#5b8cff'), lis = '';
  items.forEach(function(it, j) {
    lis += '<li style="position:relative;width:' + cell + 'px;height:' + cell + 'px;display:flex;align-items:center;justify-content:center;--di:clamp(0,calc(var(--p,1)*' + (N + 2) + ' - ' + j + '),1);opacity:var(--di);transform:scale(calc(0.5 + var(--di)*0.5));">'
      + '<span aria-hidden="true" style="width:72%;height:72%;border-radius:50%;background:' + it.fill + ';color:#fff;font-weight:800;font-size:' + Math.round(cell * 0.34) + 'px;display:flex;align-items:center;justify-content:center;">' + _esc(it.glyph) + '</span>'
      + '<span style="' + _IF_SR + '">' + _esc(it.label) + '</span></li>';
  });
  return '<div style="display:inline-block;position:relative;padding:' + pad + 'px;border-radius:' + (cell / 2 + pad) + 'px;background:' + bg + ';">'
    + '<span aria-hidden="true" style="position:absolute;left:' + pad + 'px;top:' + pad + 'px;width:' + cell + 'px;height:' + cell + 'px;border-radius:50%;box-shadow:0 0 0 3px ' + ring + ';background:rgba(255,255,255,0.55);'
    + 'transform:translateX(calc(clamp(0,var(--s,1),1)*' + ((N - 1) * cell) + 'px));opacity:clamp(0,calc(var(--p,1)*3),1);"></span>'
    + '<ul style="position:relative;display:flex;margin:0;padding:0;list-style:none;">' + lis + '</ul></div>';
};

// motion_fit: a display word that fills the width of its box. Real text, not hidden. recede (opt-in) shrinks and fades it with the step dial.
_RENDERERS['motion_fit'] = function(b) {
  var text = _moStr(b.text, 20) || 'Text', fill = _ffNum(b.fill, 0.96, 0.4, 1, 2), color = _moInk(b, 'color', 'var(--text,#0f172a)'), weight = _ffPick(b.weight, _FF_WEIGHTS, 'black'), font = _ffPick(b.font, _FF_FONTS, 'sans');
  var upper = b.upper !== false, n = Math.max(text.length, 2), fs = Math.round(100 * parseFloat(fill) / (n * 0.62) * 100) / 100, rec = b.recede === true;
  var tr = 'scale(calc(0.7 + clamp(0,var(--p,1),1)*0.3' + (rec ? ' - var(--s,0)*0.45' : '') + '))', op = 'clamp(0,calc(var(--p,1)*3),1)' + (rec ? '*(1 - var(--s,0)*0.7)' : '');
  return '<div style="width:100%;container-type:inline-size;overflow:hidden;"><div style="font-family:' + font + ';font-weight:' + weight + ';font-size:' + fs + 'cqw;line-height:1;white-space:nowrap;text-align:center;color:' + color + ';'
    + (upper ? 'text-transform:uppercase;' : '') + 'opacity:calc(' + op + ');transform:' + tr + ';">' + _esc(text) + '</div></div>';
};

// ── third batch from the screen recordings (2026-10-11): theme, dialog, dots, sweep ───────────────────────────────────────────────────────────
// Measured from 88 recordings (motion_probe v2, 80 candidates reviewed by eye). Same accessibility rules as the second batch: decorative layers are aria-hidden,
// words are real text or one accessible name, every dial defaults to the finished picture, no endless loops, no flashing (the sweep is slow and soft).
var _TH_INK = {text: 1, 'text-muted': 1, muted: 1, accent: 1};
var _TH_PAL = {
  dark:  {text: '#e8edf2', 'text-muted': '#9aa7b5', muted: '#9aa7b5', border: '#2a3340', surface: '#151b23', 'surface-2': '#1b2330', surface2: '#1b2330', bg: '#0b0f14', accent: '#8b9bff'},
  light: {text: '#14181f', 'text-muted': '#4b5563', muted: '#4b5563', border: '#d7dce4', surface: '#ffffff', 'surface-2': '#f1f3f7', surface2: '#f1f3f7', bg: '#f7f8fa', accent: '#4338ca'}
};

// motion_theme: child blocks whose colour tokens morph between dark and light with the step dial (0 = from, 1 = to). Seen as the 0.33-0.43 s ease-out
// theme switch in the Wall Builder recordings. One set of tokens is mixed, so every child that reads them moves together and text stays legible at the midpoint.
_RENDERERS['motion_theme'] = function(b) {
  var from = b.from === 'light' ? 'light' : 'dark', to = b.to === 'dark' ? 'dark' : 'light', blocks = _bxList(b.blocks, 6), inner = '', i, k, vars = '';
  if (from === to) to = from === 'dark' ? 'light' : 'dark';
  for (i = 0; i < blocks.length; i++) inner += _moChild(blocks[i]);
  // Surfaces fade smoothly. Ink (text, muted, accent) swaps at the half-way point (a hard flip between 0.49 and 0.491) instead, because a plain mix puts the ink and the
  // surface at the same grey there and the words vanish; swapping keeps the worst contrast about 3:1 (measured in test_theme_ink_never_matches_the_surface).
  for (k in _TH_PAL.dark) vars += '--' + k + ':color-mix(in srgb,' + _TH_PAL[from][k] + ' calc((1 - ' + (_TH_INK[k] ? 'clamp(0,calc((var(--s,1) - 0.49)*1000),1)' : 'clamp(0,var(--s,1),1)') + ')*100%),' + _TH_PAL[to][k] + ');';
  return '<div style="' + vars + 'background:var(--bg);color:var(--text);padding:16px;border-radius:12px;">' + inner + '</div>';
};

// motion_dialog: a scrim and a dialog that enter in turn. The scrim takes the first fifth of p, the dialog the next two fifths (fade, rise or scale).
var _DG_ENTER = {fade: 'fade', rise: 'rise', scale: 'scale'};
_RENDERERS['motion_dialog'] = function(b) {
  var title = _moStr(b.title, 60) || 'Dialog', body = _moStr(b.body, 200), enter = _ffPick(b.enter, _DG_ENTER, 'scale'), dim = _ffNum(b.dim, 0.45, 0.2, 0.8, 2), scrim = _moInk(b, 'scrim', '#000000');
  var src = _bxList(b.actions, 3), acts = '', i, asp = _ffNum(b.aspect, 1.6, 0.8, 3, 2);
  for (i = 0; i < src.length; i++) { var o = _clObj(src[i]), pri = o.primary === true; acts += '<span style="padding:6px 14px;border-radius:8px;font-weight:600;font-size:14px;' + (pri ? 'background:var(--accent,#4338ca);color:#fff;' : 'border:1px solid var(--border,#d7dce4);') + '">' + _esc(_moStr(o.label, 20)) + '</span>'; }
  var t = 'clamp(0,calc((var(--p,1) - 0.2)/0.4),1)', tr = enter === 'rise' ? 'translateY(calc((1 - ' + t + ')*24px))' : enter === 'scale' ? 'scale(calc(0.9 + ' + t + '*0.1))' : '';
  return '<div style="position:relative;width:100%;aspect-ratio:' + asp + ';overflow:hidden;background:var(--bg,#f7f8fa);border-radius:12px;">'
    + '<div aria-hidden="true" style="position:absolute;inset:0;background:' + scrim + ';opacity:calc(clamp(0,calc(var(--p,1)*5),1)*' + dim + ');"></div>'
    + '<div role="dialog" aria-label="' + _esc(title) + '" style="position:absolute;left:50%;top:50%;width:min(80%,420px);box-sizing:border-box;padding:18px;border-radius:14px;background:var(--surface,#fff);color:var(--text,#14181f);'
    + 'box-shadow:0 12px 40px rgba(0,0,0,0.3);opacity:' + t + ';transform:translate(-50%,-50%) ' + tr + ';"><div style="font-weight:700;font-size:17px;">' + _esc(title) + '</div>'
    + (body ? '<div style="margin-top:6px;font-size:14px;color:var(--muted,#4b5563);">' + _esc(body) + '</div>' : '')
    + (acts ? '<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:14px;">' + acts + '</div>' : '') + '</div></div>';
};

// motion_dots: one line of text on a 5x7 dot matrix that resolves into another, left to right, with the step dial. Dots in both words stay lit.
var _DM_FONT = {A:'01110/10001/10001/11111/10001/10001/10001',B:'11110/10001/10001/11110/10001/10001/11110',C:'01110/10001/10000/10000/10000/10001/01110',D:'11110/10001/10001/10001/10001/10001/11110',E:'11111/10000/10000/11110/10000/10000/11111',F:'11111/10000/10000/11110/10000/10000/10000',G:'01110/10001/10000/10111/10001/10001/01111',H:'10001/10001/10001/11111/10001/10001/10001',I:'01110/00100/00100/00100/00100/00100/01110',J:'00111/00010/00010/00010/00010/10010/01100',K:'10001/10010/10100/11000/10100/10010/10001',L:'10000/10000/10000/10000/10000/10000/11111',M:'10001/11011/10101/10101/10001/10001/10001',N:'10001/11001/10101/10011/10001/10001/10001',O:'01110/10001/10001/10001/10001/10001/01110',P:'11110/10001/10001/11110/10000/10000/10000',Q:'01110/10001/10001/10001/10101/10010/01101',R:'11110/10001/10001/11110/10100/10010/10001',S:'01111/10000/10000/01110/00001/00001/11110',T:'11111/00100/00100/00100/00100/00100/00100',U:'10001/10001/10001/10001/10001/10001/01110',V:'10001/10001/10001/10001/10001/01010/00100',W:'10001/10001/10001/10101/10101/10101/01010',X:'10001/10001/01010/00100/01010/10001/10001',Y:'10001/10001/01010/00100/00100/00100/00100',Z:'11111/00001/00010/00100/01000/10000/11111',
  '0':'01110/10001/10011/10101/11001/10001/01110','1':'00100/01100/00100/00100/00100/00100/01110','2':'01110/10001/00001/00010/00100/01000/11111','3':'11110/00001/00001/01110/00001/00001/11110','4':'00010/00110/01010/10010/11111/00010/00010','5':'11111/10000/11110/00001/00001/10001/01110','6':'00110/01000/10000/11110/10001/10001/01110','7':'11111/00001/00010/00100/01000/01000/01000','8':'01110/10001/10001/01110/10001/10001/01110','9':'01110/10001/10001/01111/00001/00010/01100',
  '.':'00000/00000/00000/00000/00000/00000/00100','!':'00100/00100/00100/00100/00100/00000/00100','?':'01110/10001/00001/00010/00100/00000/00100',',':'00000/00000/00000/00000/00000/00100/01000','-':'00000/00000/00000/11111/00000/00000/00000',' ':'00000/00000/00000/00000/00000/00000/00000'};
function _dmGrid(text, cols) {
  var cells = {}, off = Math.floor((cols - (text.length * 6 - 1)) / 2), i, r, c;
  for (i = 0; i < text.length; i++) {
    var rows = (_DM_FONT[text.charAt(i)] || _DM_FONT['?']).split('/');
    for (r = 0; r < 7; r++) for (c = 0; c < 5; c++) if (rows[r].charAt(c) === '1') cells[r + ',' + (off + i * 6 + c)] = 1;
  }
  return cells;
}
_RENDERERS['motion_dots'] = function(b) {
  var clean = function(v, d) { var t = _moStr(v, 14).toUpperCase().replace(/[^A-Z0-9 .,!?\-]/g, ''); return t || d; };
  var a = clean(b.from, 'A'), z = clean(b.to, 'B'), cols = Math.max(a.length, z.length) * 6 - 1, ga = _dmGrid(a, cols), gz = _dmGrid(z, cols), out = '', r, c;
  var col = _moInk(b, 'color', '#e8edf2'), col2 = _moInk(b, 'color2', col), faint = b.grid !== false, dot = 10, asp = Math.round((cols * dot) / (7 * dot) * 100) / 100;
  for (c = 0; c < cols; c++) {
    var u = 'clamp(0,calc(var(--s,1)*1.4 - ' + (Math.round(c / cols * 40) / 100) + '),1)';
    for (r = 0; r < 7; r++) {
      var k = r + ',' + c, ina = ga[k] === 1, inz = gz[k] === 1, cx = c * dot + dot / 2, cy = r * dot + dot / 2;
      if (!ina && !inz) { if (faint) out += '<circle cx="' + cx + '" cy="' + cy + '" r="1.6" fill="' + col + '" opacity="0.14"/>'; continue; }
      var o = ina && inz ? '1' : ina ? '(1 - ' + u + ')' : u;
      out += '<circle cx="' + cx + '" cy="' + cy + '" r="3.4" fill="' + (inz ? col : col2) + '" style="opacity:calc(' + o + ');"/>';
    }
  }
  var name = typeof b.label === 'string' && b.label ? _moStr(b.label, 80) : z;
  return '<svg role="img" aria-label="' + _esc(name) + '" viewBox="0 0 ' + (cols * dot) + ' ' + (7 * dot) + '" style="width:min(100%,' + (cols * 9) + 'px);height:auto;display:block;margin:0 auto;aspect-ratio:' + asp + ';opacity:clamp(0,calc(var(--p,1)*4),1);">' + out + '</svg>';
};

// motion_sweep: a slanted band of light crosses its blocks with the step dial (0 = off the left edge, 1 = off the right edge). Decorative and soft.
_RENDERERS['motion_sweep'] = function(b) {
  var blocks = _bxList(b.blocks, 6), inner = '', i, ang = _ffInt(b.angle, 20, 5, 60), w = _ffInt(b.width, 28, 8, 60), str = _ffNum(b.strength, 0.35, 0.1, 0.8, 2), col = _moInk(b, 'color', '#ffffff');
  for (i = 0; i < blocks.length; i++) inner += _moChild(blocks[i]);
  return '<div style="position:relative;overflow:hidden;border-radius:12px;">' + inner + '<div aria-hidden="true" style="position:absolute;top:-50%;height:200%;width:' + w + '%;left:calc(-' + (w + 20) + '% + clamp(0,var(--s,1),1)*' + (2 * w + 140) + '%);'
    + 'transform:rotate(' + ang + 'deg);pointer-events:none;background:linear-gradient(90deg,transparent,' + col + ',transparent);opacity:' + str + ';"></div></div>';
};

// ── fourth batch from a brand film (2026-10-12): capsule, arrow, swatches, glass, wall, tag ───────────────────────────────────────────
// Same rules as the earlier batches: decorative layers aria-hidden, words are real text, every dial defaults to the finished picture, no endless loops, no flashing.
// Width that follows content ("a pill that grows as words land in it") cannot use calc() with fr units, so a box grows with max-width = progress x an estimated width,
// and is released to its natural width at the end (the max() term), so an estimate that is a little off never clips the finished picture.
var _WS = '[ \\t\\n\\r\\f\\v\\u00a0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000\\ufeff]+';
function _m4Grow(k, chars, pad) { return 'max-width:max(calc(' + k + '*' + _ifFmt(chars * 0.7 + pad) + 'em),calc((' + k + ' - 0.999)*1000000px));'; }

// motion_capsule: a rounded capsule that widens as words land in it, one after another with p; the newest word can resolve out of noise.
var _CP_LOOK = {outline: 'outline', solid: 'solid', glass: 'glass'};
var _CP_RES = {fade: 'fade', blur: 'blur', scramble: 'scramble'};
var _CP_NOISE = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#%&*+=?';
_RENDERERS['motion_capsule'] = function(b) {
  var words = _moStr(b.text, 120).split(new RegExp(_WS)).filter(function(w) { return w; }).slice(0, 12);
  if (!words.length) words = ['Text'];
  var n = words.length, look = _ffPick(b.style, _CP_LOOK, 'outline'), res = _ffPick(b.resolve, _CP_RES, 'blur'), size = _ffInt(b.size, 22, 12, 64), seed = _ffInt(b.seed, 5, 0, 999);
  var ink = _moInk(b, 'color', b.tone === 'dark' ? '#0f172a' : '#ffffff'), box;
  if (look === 'outline') box = 'border:1.5px solid ' + ink + ';';
  else if (look === 'solid') box = 'background:' + ink + '22;border:1.5px solid ' + ink + '55;';
  else box = 'background:' + ink + '1a;border:1px solid ' + ink + '40;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);';
  var inner = '';
  words.forEach(function(w, i) {
    var k = 'clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1)', pad = i ? '0.3em' : '0', noise = '';
    if (res === 'scramble') {
      var j, nz = ''; for (j = 0; j < w.length; j++) nz += _CP_NOISE.charAt(Math.floor(_bxSeed(seed, i, j) * _CP_NOISE.length));
      noise = '<span aria-hidden="true" style="position:absolute;left:' + pad + ';top:0;opacity:calc(1 - var(--ci));">' + _esc(nz) + '</span>';
    }
    inner += '<span style="--ci:' + k + ';position:relative;display:inline-block;vertical-align:bottom;overflow:hidden;white-space:nowrap;padding-left:' + pad + ';' + _m4Grow('var(--ci)', w.length, i ? 0.3 : 0) +
      'opacity:var(--ci);' + (res === 'blur' ? 'filter:blur(calc((1 - var(--ci))*5px));' : '') + '">' + _esc(w) + noise + '</span>';
  });
  return '<span style="display:inline-block;box-sizing:border-box;padding:0.32em 0.95em;border-radius:999px;font-size:' + size + 'px;line-height:1.25;color:' + ink + ';white-space:nowrap;' + box + 'opacity:clamp(0,calc(var(--p,1)*8),1);">' + inner + '</span>';
};

// motion_arrow: an arrow that draws itself with p and turns through a list of directions with the step dial s (0 points right).
_RENDERERS['motion_arrow'] = function(b) {
  var src = _bxList(b.angles, 6), ang = [], i;
  for (i = 0; i < src.length; i++) ang.push(_ffInt(src[i], 0, -720, 720));
  if (!ang.length) ang.push(0);
  var M = ang.length, size = _ffInt(b.size, 64, 12, 400), wt = _ffInt(b.weight, 3, 1, 12), col = _moInk(b, 'color', 'currentColor'), solid = b.style === 'solid', inl = b.inline === true;
  var terms = '', label = _moStr(b.label, 60) || 'Arrow';
  for (i = 0; i < M - 1; i++) terms += ' + ' + (ang[i + 1] - ang[i]) + '*clamp(0,calc(var(--s,1)*' + (M - 1) + ' - ' + i + '),1)';
  var shaft = 'stroke-dasharray:1;stroke-dashoffset:calc(1 - clamp(0,calc(var(--p,1)*1.6),1));', head = 'stroke-dasharray:1;stroke-dashoffset:calc(1 - clamp(0,calc(var(--p,1)*1.6 - 0.6),1));';
  return '<svg role="img" aria-label="' + _esc(label) + '" viewBox="0 0 64 32" width="' + size + '" height="' + Math.round(size / 2) + '" style="display:' + (inl ? 'inline-block;vertical-align:-0.15em' : 'block') + ';overflow:visible;transform:rotate(calc(1deg*(' + ang[0] + terms + ')));transform-origin:50% 50%;" focusable="false">' +
    '<path d="M4 16H58" pathLength="1" fill="none" stroke="' + col + '" stroke-width="' + wt + '" stroke-linecap="round" style="' + shaft + '"/>' +
    (solid ? '<path d="M44 5L60 16L44 27Z" fill="' + col + '" stroke="' + col + '" stroke-width="' + wt + '" stroke-linejoin="round" style="opacity:clamp(0,calc(var(--p,1)*1.6 - 0.6),1);"/>'
           : '<path d="M44 5L59 16L44 27" pathLength="1" fill="none" stroke="' + col + '" stroke-width="' + wt + '" stroke-linecap="round" stroke-linejoin="round" style="' + head + '"/>') + '</svg>';
};

// motion_swatches: a brand palette arriving panel by panel, each from its own edge, each labelled with a real name and hex value.
var _SW_LAYOUT = {grid: 'grid', row: 'row', stack: 'stack'};
function _swInk(hex) {
  var c = [1, 3, 5].map(function(i) { var v = parseInt(hex.slice(i, i + 2), 16) / 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
  var L = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  return (1.05 / (L + 0.05)) >= ((L + 0.05) / 0.05) ? '#ffffff' : '#000000';   // white or black, whichever reads better: at least 4.58:1 on any colour
}
_RENDERERS['motion_swatches'] = function(b) {
  var src = _bxList(b.swatches, 6), sw = [], i;
  for (i = 0; i < src.length; i++) { var o = _clObj(src[i]); sw.push({name: _moStr(o.name, 20) || ('Colour ' + (i + 1)), hex: _ffHex(o.hex, _CL_FILLS[i % 8])}); }
  while (sw.length < 2) sw.push({name: 'Colour ' + (sw.length + 1), hex: _CL_FILLS[sw.length % 8]});
  var n = sw.length, lay = _ffPick(b.layout, _SW_LAYOUT, 'grid'), cols = lay === 'row' ? n : lay === 'stack' ? 1 : (n <= 2 ? n : 2), asp = _ffNum(b.aspect, 1.78, 0.5, 3, 2), gap = _ffInt(b.gap, 0, 0, 24), rad = _ffInt(b.radius, 0, 0, 40);
  var dirs = ['translate(calc((1 - var(--k))*-100%),0)', 'translate(0,calc((1 - var(--k))*-100%))', 'translate(calc((1 - var(--k))*100%),0)', 'translate(0,calc((1 - var(--k))*100%))'], lis = '';
  sw.forEach(function(s, j) {
    var ink = _swInk(s.hex);
    lis += '<li style="--k:clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + j + '),1);position:relative;box-sizing:border-box;padding:6% 7%;display:flex;flex-direction:column;justify-content:space-between;background:' + s.hex + ';color:' + ink + ';border-radius:' + rad + 'px;overflow:hidden;transform:' + dirs[j % 4] + ';opacity:clamp(0,calc(var(--k)*4),1);">' +
      '<span style="font-size:0.85em;font-weight:700;">' + _esc(s.name) + '</span><span style="font-size:0.7em;letter-spacing:0.04em;opacity:0.85;">' + s.hex.toUpperCase() + '</span></li>';
  });
  return '<ul style="list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(' + cols + ',1fr);grid-auto-rows:1fr;gap:' + gap + 'px;width:100%;aspect-ratio:' + asp + ';overflow:hidden;border-radius:' + rad + 'px;font-size:clamp(11px,2.2cqw,22px);container-type:inline-size;">' + lis + '</ul>';
};

// motion_glass: a frosted pane that blurs whatever is behind it; the blur, the tint and the scale come in with p. Its children are ordinary atoms.
_RENDERERS['motion_glass'] = function(b) {
  var blocks = _bxList(b.blocks, 6), inner = '', i, blur = _ffInt(b.blur, 18, 2, 40), tint = _ffHex(b.tint, '#ffffff'), str = _ffNum(b.strength, 0.14, 0.05, 0.6, 2), rad = _ffInt(b.radius, 18, 0, 40), pad = _ffInt(b.padding, 18, 0, 48);
  for (i = 0; i < blocks.length; i++) inner += _moChild(blocks[i]);
  return '<div style="--k:clamp(0,var(--p,1),1);position:relative;box-sizing:border-box;padding:' + pad + 'px;border-radius:' + rad + 'px;background:rgba(' + _ffRgb(tint) + ',calc(' + str + '*var(--k)));' +
    'backdrop-filter:blur(calc(var(--k)*' + blur + 'px)) saturate(1.15);-webkit-backdrop-filter:blur(calc(var(--k)*' + blur + 'px)) saturate(1.15);' +
    (b.edge === false ? '' : 'border:1px solid rgba(255,255,255,calc(0.4*var(--k)));') + 'box-shadow:0 8px 32px rgba(0,0,0,calc(0.18*var(--k)));opacity:var(--k);transform:scale(calc(0.96 + 0.04*var(--k)));">' + inner + '</div>';
};

// motion_wall: a wall of picture tiles. p builds it tile by tile; the step dial s thins it out in a seeded order (s = 1 is the full wall, s = 0 is empty).
_RENDERERS['motion_wall'] = function(b) {
  var cols = _ffInt(b.cols, 6, 2, 10), rows = _ffInt(b.rows, 3, 1, 6), gap = _ffInt(b.gap, 8, 0, 24), rad = _ffInt(b.radius, 8, 0, 24), seed = _ffInt(b.seed, 3, 0, 999), asp = _ffNum(b.aspect, 1.78, 0.5, 3, 2), N = cols * rows;
  var src = _bxList(b.images, 24), imgs = [], i;
  for (i = 0; i < src.length; i++) imgs.push(_moImg(typeof src[i] === 'object' && src[i] ? src[i].url : src[i]));
  var idx = []; for (i = 0; i < N; i++) idx.push(i);
  idx.sort(function(a, c) { return (_bxSeed(seed, a, 9) - _bxSeed(seed, c, 9)) || (a - c); });
  var rank = []; idx.forEach(function(t, r) { rank[t] = r; });
  var out = '';
  for (i = 0; i < N; i++) {
    var pic = imgs.length && imgs[i % imgs.length] ? '<img src="' + _esc(imgs[i % imgs.length]) + '" alt="" loading="lazy" referrerpolicy="no-referrer" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;">' : '';
    out += '<span style="--b:clamp(0,calc(var(--p,1)*' + (N + 3) + ' - ' + i + '),1);--v:clamp(0,calc(1 - (1 - var(--s,1))*' + (N + 3) + ' + ' + rank[i] + '),1);position:relative;display:block;overflow:hidden;border-radius:' + rad + 'px;background:' + _CL_FILLS[(i + seed) % 8] +
      ';opacity:calc(var(--b)*var(--v));transform:scale(calc(0.8 + 0.2*var(--b)*var(--v)));">' + pic + '</span>';
  }
  var named = typeof b.label === 'string' && b.label;
  return '<div ' + (named ? 'role="img" aria-label="' + _esc(_moStr(b.label, 60)) + '"' : 'aria-hidden="true"') + ' style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);grid-auto-rows:1fr;gap:' + gap + 'px;width:100%;aspect-ratio:' + asp + ';overflow:hidden;pointer-events:none;">' + out + '</div>';
};

// motion_tag: a dot that travels across the box and then grows into a label pill, so a caption seems to come out of the thing it names.
var _TG_TONE = {dark: 'dark', light: 'light', accent: 'accent'};
_RENDERERS['motion_tag'] = function(b) {
  var text = _moStr(b.text, 24) || 'Label', f = _clObj(b.from), t = _clObj(b.to), size = _ffInt(b.size, 20, 12, 40), tone = _ffPick(b.tone, _TG_TONE, 'dark'), acc = _moInk(b, 'accent', '#ffd166'), asp = _ffNum(b.aspect, 1.78, 0.5, 3, 2);
  var fx = _ffNum(f.x, 20, 0, 100, 1), fy = _ffNum(f.y, 30, 0, 100, 1), tx = _ffNum(t.x, 55, 0, 100, 1), ty = _ffNum(t.y, 55, 0, 100, 1), mv = 'clamp(0,calc(var(--p,1)*2.2),1)', gr = 'clamp(0,calc((var(--p,1) - 0.45)/0.55),1)';
  var bg = tone === 'light' ? '#ffffff' : tone === 'accent' ? acc : '#111111', ink = tone === 'dark' ? '#ffffff' : '#111111';
  return '<div style="position:relative;width:100%;aspect-ratio:' + asp + ';font-size:' + size + 'px;">' +
    '<div style="--t:' + gr + ';position:absolute;left:calc(' + fx + '% + (' + _ifFmt(parseFloat(tx) - parseFloat(fx)) + '%)*' + mv + ');top:calc(' + fy + '% + (' + _ifFmt(parseFloat(ty) - parseFloat(fy)) + '%)*' + mv + ');transform:translate(0,-50%);display:flex;align-items:center;gap:0.45em;white-space:nowrap;">' +
    '<span aria-hidden="true" style="width:0.7em;height:0.7em;border-radius:50%;background:' + acc + ';flex:none;opacity:clamp(0,calc(var(--p,1)*10),1);"></span>' +
    '<span style="display:inline-block;overflow:hidden;box-sizing:border-box;padding:0.28em calc(var(--t)*0.95em);border-radius:999px;background:' + bg + ';color:' + ink + ';line-height:1.2;' + _m4Grow('var(--t)', text.length, 1.9) + 'opacity:var(--t);">' + _esc(text) + '</span></div></div>';
};

// ── fifth batch from two motion-designer showreels (2026-10-12): ring, highlight, meters, discs ───────────────────────────────────────────────
// motion_ring: text set around a circle that turns with the step dial, around a round picture or colour disc. Each letter is its own element at its own angle, so there is
// no path id to mint and the render is the same every time. The words are the accessible name.
_RENDERERS['motion_ring'] = function(b) {
  var text = _moStr(b.text, 40) || 'Text', base = Array.from(text + ' \u00b7 '), chars = [], i;
  while (chars.length < 36) chars = chars.concat(base);
  chars = chars.slice(0, Math.min(120, chars.length));
  var N = chars.length, size = _ffInt(b.size, 360, 120, 800), turns = _ffInt(b.turns, 1, -4, 4), disc = _ffInt(b.disc, 52, 20, 80), fs = _ffNum(b.font_size, 15, 8, 30, 1);
  var col = _moInk(b, 'color', 'currentColor'), fill = _moInk(b, 'fill', '#7c3aed'), font = _ffPick(b.font, _FF_FONTS, 'sans'), weight = _ffPick(b.weight, _FF_WEIGHTS, 'bold'), img = _moImg(b.image), out = '';
  for (i = 0; i < N; i++) if (chars[i] !== ' ') out += '<text x="100" y="22" text-anchor="middle" transform="rotate(' + _ifFmt(i * 360 / N) + ' 100 100)">' + _esc(chars[i]) + '</text>';
  return '<div role="img" aria-label="' + _esc(text) + '" style="position:relative;width:min(100%,' + size + 'px);aspect-ratio:1;margin:0 auto;">' +
    '<svg aria-hidden="true" focusable="false" viewBox="0 0 200 200" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible;opacity:clamp(0,calc((var(--p,1) - 0.15)*3),1);transform:rotate(calc(var(--s,1)*' + (turns * 360) + 'deg)) scale(calc(0.85 + 0.15*clamp(0,var(--p,1),1)));font-family:' + font + ';font-weight:' + weight + ';font-size:' + fs + 'px;fill:' + col + ';">' + out + '</svg>' +
    '<div aria-hidden="true" style="position:absolute;left:50%;top:50%;width:' + disc + '%;aspect-ratio:1;border-radius:50%;overflow:hidden;background:' + fill + ';transform:translate(-50%,-50%) scale(clamp(0,calc(var(--p,1)*3),1));">' +
    (img ? '<img src="' + _esc(img) + '" alt="" loading="lazy" referrerpolicy="no-referrer" style="width:100%;height:100%;object-fit:cover;display:block;">' : '') + '</div></div>';
};

// motion_highlight: a marker swipe behind words. p draws the swipe from left to right; the words are real text and are always readable.
var _HL_LOOK = {marker: ['0.1em', '0.04em', '-1deg'], underline: ['0.72em', '-0.02em', '0deg'], strike: ['0.46em', '0.4em', '0deg']};
_RENDERERS['motion_highlight'] = function(b) {
  var text = _moStr(b.text, 80) || 'Text', look = _ffPick(b.style, {marker: 'marker', underline: 'underline', strike: 'strike'}, 'marker'), g = _HL_LOOK[look], size = _ffInt(b.size, 40, 12, 160);
  var hl = _moInk(b, 'color', '#ffe94a'), ink = _moInk(b, 'ink', look === 'marker' ? '#111111' : 'currentColor'), weight = _ffPick(b.weight, _FF_WEIGHTS, 'bold'), font = _ffPick(b.font, _FF_FONTS, 'sans');
  return '<span style="position:relative;display:inline-block;font-family:' + font + ';font-weight:' + weight + ';font-size:' + size + 'px;line-height:1.3;color:' + ink + ';white-space:nowrap;">' +
    '<span aria-hidden="true" style="position:absolute;left:-0.12em;right:-0.12em;top:' + g[0] + ';bottom:' + g[1] + ';background:' + hl + ';border-radius:0.12em;transform:rotate(' + g[2] + ') skewX(-6deg);clip-path:inset(0 calc((1 - clamp(0,var(--p,1),1))*100%) 0 0);"></span>' +
    '<span style="position:relative;">' + _esc(text) + '</span></span>';
};

// motion_meters: equaliser columns on either side of a centre (or in one cluster), rising and falling with the step dial in a seeded, seekable pattern. Child atoms sit between them.
var _MT_LAYOUT = {sides: 'sides', row: 'row'};
_RENDERERS['motion_meters'] = function(b) {
  var bars = _ffInt(b.bars, 14, 4, 40), rows = _ffInt(b.rows, 12, 4, 20), seed = _ffInt(b.seed, 3, 0, 999), cyc = _ffInt(b.cycles, 2, 1, 8), lay = _ffPick(b.layout, _MT_LAYOUT, 'sides'), gap = _ffInt(b.gap, 5, 1, 20);
  var src = _bxList(b.colors, 5), cols = [], i; for (i = 0; i < src.length; i++) cols.push(_ffHex(src[i], '#ffffff'));
  if (!cols.length) cols = ['#ff5ea8', '#ffd166', '#34e0c3', '#6d6af7'];
  var cluster = function(flip, base) {
    var o = '', j;
    for (j = 0; j < bars; j++) {
      var d = flip ? bars - 1 - j : j, ph = _ifFmt(_bxSeed(seed, base + j, 2) * 6.2832), c = cols[j % cols.length], k = 'clamp(0,calc(var(--p,1)*' + (bars + 2) + ' - ' + d + '),1)';
      o += '<span style="flex:1 1 0;min-width:2px;align-self:center;height:calc(' + k + '*(0.15 + 0.85*abs(sin(calc(' + ph + '*1rad + var(--s,1)*' + cyc + '*6.2832rad))))*100%);' +
        'background:repeating-linear-gradient(to top,' + c + ' 0,' + c + ' ' + _ifFmt(100 / rows * 0.62) + '%,transparent ' + _ifFmt(100 / rows * 0.62) + '%,transparent ' + _ifFmt(100 / rows) + '%);"></span>';
    }
    return '<span aria-hidden="true" style="display:flex;gap:' + gap + 'px;flex:1 1 0;height:100%;align-items:center;">' + o + '</span>';
  };
  var blocks = _bxList(b.blocks, 3), mid = '', m; for (m = 0; m < blocks.length; m++) mid += _moChild(blocks[m]);
  var named = typeof b.label === 'string' && b.label;
  return '<div ' + (named ? 'role="img" aria-label="' + _esc(_moStr(b.label, 60)) + '" ' : '') + 'style="display:flex;align-items:center;gap:4%;width:100%;height:' + _ffInt(b.height, 180, 60, 600) + 'px;">' +
    (lay === 'sides' ? cluster(false, 0) + '<span style="flex:none;">' + mid + '</span>' + cluster(true, 100) : cluster(false, 0) + (mid ? '<span style="flex:none;">' + mid + '</span>' : '')) + '</div>';
};

// motion_discs: two to four overlapping discs. With the step dial at 0 they sit apart across the box; at 1 they slide together and overlap (colours multiply where they meet).
_RENDERERS['motion_discs'] = function(b) {
  var src = _bxList(b.discs, 4), ds = [], i;
  for (i = 0; i < src.length; i++) { var o = _clObj(src[i]); ds.push({color: _ffHex(o.color, ['#f4d21f', '#2e6fbd', '#e63950', '#16a085'][i % 4]), r: _ffNum(o.r, 24, 8, 50, 1)}); }
  while (ds.length < 2) ds.push({color: ['#f4d21f', '#2e6fbd'][ds.length], r: _ffNum(undefined, 24, 8, 50, 1)});
  var n = ds.length, ov = _ffNum(b.overlap, 12, 2, 30, 1), asp = _ffNum(b.aspect, 1.78, 0.5, 3, 2), blend = b.blend !== false, out = '', named = typeof b.label === 'string' && b.label;
  ds.forEach(function(d, j) {
    var a = _ifFmt(14 + 72 * j / (n - 1)), t = _ifFmt(50 + (j - (n - 1) / 2) * parseFloat(ov)), k = 'clamp(0,calc(var(--p,1)*' + (n + 2) + ' - ' + j + '),1)';
    out += '<span style="position:absolute;top:50%;left:calc((' + a + ' + (' + t + ' - ' + a + ')*clamp(0,var(--s,1),1))*1%);width:' + _ifFmt(parseFloat(d.r) * 2 / parseFloat(asp)) + '%;aspect-ratio:1;border-radius:50%;background:' + d.color + ';' + (blend ? 'mix-blend-mode:multiply;' : '') +
      'transform:translate(-50%,-50%) scale(' + k + ');"></span>';
  });
  return '<div ' + (named ? 'role="img" aria-label="' + _esc(_moStr(b.label, 60)) + '"' : 'aria-hidden="true"') + ' style="position:relative;width:100%;aspect-ratio:' + asp + ';isolation:isolate;overflow:hidden;">' + out + '</div>';
};

// ── sixth batch from a food-brand film (2026-10-12): dotgrid, blade ─────────────────────────────────────────────────────────────────────
// motion_dotgrid: a grid of dots with one token that hops from cell to cell as the step dial runs (a parabola between cells, resting on a cell at s = 1). p scales the dots in from the token's start.
_RENDERERS['motion_dotgrid'] = function(b) {
  var cols = _ffInt(b.cols, 5, 2, 12), rows = _ffInt(b.rows, 4, 2, 10), seed = _ffInt(b.seed, 4, 0, 999), dot = _ffInt(b.dot, 70, 30, 95), asp = _ffNum(b.aspect, 1.25, 0.5, 3, 2);
  var base = _moInk(b, 'color', '#f4ead0'), tok = _moInk(b, 'accent', '#e11d48'), src = _bxList(b.hops, 8), hops = [], i;
  for (i = 0; i < src.length; i++) { var h = _bxList(src[i], 2); hops.push([_ffInt(h[0], 0, 0, cols - 1), _ffInt(h[1], 0, 0, rows - 1)]); }
  if (hops.length < 2) { hops = []; for (i = 0; i < 5; i++) hops.push([Math.floor(_bxSeed(seed, i, 1) * cols), Math.floor(_bxSeed(seed, i, 2) * rows)]); }
  var M = hops.length, cw = _ifFmt(100 / cols), ch = _ifFmt(100 / rows), cells = '', r, c, tx = '', ty = '';
  for (r = 0; r < rows; r++) for (c = 0; c < cols; c++) {
    var d = Math.abs(c - hops[0][0]) + Math.abs(r - hops[0][1]);
    cells += '<span style="display:flex;align-items:center;justify-content:center;"><span style="width:' + dot + '%;aspect-ratio:1;border-radius:50%;background:' + base + ';transform:scale(clamp(0,calc(var(--p,1)*' + (cols + rows + 2) + ' - ' + d + '),1));"></span></span>';
  }
  for (i = 0; i < M - 1; i++) { tx += ' + ' + (hops[i + 1][0] - hops[i][0]) + '*clamp(0,calc(var(--s,1)*' + (M - 1) + ' - ' + i + '),1)'; ty += ' + ' + (hops[i + 1][1] - hops[i][1]) + '*clamp(0,calc(var(--s,1)*' + (M - 1) + ' - ' + i + '),1)'; }
  var tok_el = '<span aria-hidden="true" style="position:absolute;left:0;top:0;width:' + cw + '%;height:' + ch + '%;display:flex;align-items:center;justify-content:center;' +
    'transform:translate(calc((' + hops[0][0] + tx + ')*100%),calc((' + hops[0][1] + ty + ')*100%));"><span style="width:' + dot + '%;aspect-ratio:1;border-radius:50%;background:' + tok + ';' +
    'transform:translateY(calc(-0.9*abs(sin(calc(var(--s,1)*' + (M - 1) + '*3.14159rad)))*100%)) scale(clamp(0,calc(var(--p,1)*6),1));"></span></span>';
  var named = typeof b.label === 'string' && b.label;
  return '<div ' + (named ? 'role="img" aria-label="' + _esc(_moStr(b.label, 60)) + '"' : 'aria-hidden="true"') + ' style="position:relative;width:100%;aspect-ratio:' + asp + ';"><div style="position:absolute;inset:0;display:grid;grid-template-columns:repeat(' + cols + ',1fr);grid-template-rows:repeat(' + rows + ',1fr);">' + cells + '</div>' + tok_el + '</div>';
};

// motion_blade: a shape sweeps along a line of text from left to right with the step dial and the text appears behind it, so the shape seems to write the words. Disc, half-disc or bar.
var _BL_SHAPE = {disc: 'disc', half: 'half', bar: 'bar'};
_RENDERERS['motion_blade'] = function(b) {
  var text = _moStr(b.text, 80) || 'Text', shape = _ffPick(b.shape, _BL_SHAPE, 'half'), size = _ffInt(b.size, 48, 14, 160), sc = _moInk(b, 'color', '#123524'), ink = _moInk(b, 'ink', 'currentColor');
  var font = _ffPick(b.font, _FF_FONTS, 'sans'), weight = _ffPick(b.weight, _FF_WEIGHTS, 'bold'), e = 'clamp(0,var(--s,1),1)', sh;
  if (shape === 'disc') sh = 'width:1.5em;height:1.5em;border-radius:50%;top:-0.2em;';
  else if (shape === 'half') sh = 'width:1.7em;height:0.85em;border-radius:1.7em 1.7em 0 0;top:0.25em;transform:rotate(calc(' + e + '*540deg - 270deg));transform-origin:50% 100%;';
  else sh = 'width:0.18em;height:1.5em;border-radius:0.09em;top:-0.1em;';
  return '<span style="position:relative;display:inline-block;font-family:' + font + ';font-weight:' + weight + ';font-size:' + size + 'px;line-height:1.2;color:' + ink + ';white-space:nowrap;">' +
    '<span style="display:inline-block;clip-path:inset(0 calc((1 - ' + e + ')*100% - 0.1em) 0 0);">' + _esc(text) + '</span>' +
    '<span aria-hidden="true" style="position:absolute;left:calc(' + e + '*100%);margin-left:-0.85em;background:' + sc + ';opacity:clamp(0,calc(var(--p,1)*8),1);' + sh + '"></span></span>';
};

// motion_blueprint: a wordmark built the way a designer draws it: construction guides draw in, the letters appear as an outline, then fill in as the guides step back.
_RENDERERS['motion_blueprint'] = function(b) {
  var text = _moStr(b.text, 24) || 'Text', size = _ffInt(b.size, 120, 24, 300), ink = _moInk(b, 'color', 'currentColor'), gc = _moInk(b, 'guide', '#7c3aed'), lines = b.lines !== false;
  var font = _ffPick(b.font, _FF_FONTS, 'sans'), weight = _ffPick(b.weight, _FF_WEIGHTS, 'black');
  var gp = 'clamp(0,calc(var(--p,1)*2.2),1)', op = 'clamp(0,calc((var(--p,1) - 0.2)*2.2),1)', fp = 'clamp(0,calc((var(--p,1) - 0.6)*2.5),1)', hz = [0.2, 0.42, 0.8], i, g = '';
  if (lines) {
    for (i = 0; i < hz.length; i++) g += '<span style="position:absolute;left:-0.35em;right:-0.35em;top:' + hz[i] + 'em;height:1px;background:' + gc + ';transform:scaleX(' + gp + ');transform-origin:left;opacity:calc(1 - 0.7*' + fp + ');"></span>';
    g += '<span style="position:absolute;left:-0.1em;top:-0.2em;bottom:-0.2em;width:1px;background:' + gc + ';transform:scaleY(' + gp + ');transform-origin:top;opacity:calc(1 - 0.7*' + fp + ');"></span>';
    g += '<span style="position:absolute;right:-0.1em;top:-0.2em;bottom:-0.2em;width:1px;background:' + gc + ';transform:scaleY(' + gp + ');transform-origin:bottom;opacity:calc(1 - 0.7*' + fp + ');"></span>';
  }
  return '<span style="position:relative;display:inline-block;font-family:' + font + ';font-weight:' + weight + ';font-size:' + size + 'px;line-height:1;white-space:nowrap;padding:0.1em 0;">' +
    '<span aria-hidden="true" style="position:absolute;inset:0;pointer-events:none;">' + g + '</span>' +
    '<span style="position:relative;color:' + ink + ';-webkit-text-fill-color:transparent;-webkit-text-stroke:1.5px ' + ink + ';opacity:' + op + ';">' + _esc(text) + '</span>' +
    '<span aria-hidden="true" style="position:absolute;left:0;top:0.1em;color:' + ink + ';opacity:' + fp + ';">' + _esc(text) + '</span></span>';
};

// motion_tracking: a line whose letter-spacing opens (or closes) with the step dial, so the words breathe apart as they appear.
_RENDERERS['motion_tracking'] = function(b) {
  var text = _moStr(b.text, 80) || 'Text', size = _ffInt(b.size, 48, 14, 200), from = _ffNum(b.from, 0, -0.2, 1, 2), to = _ffNum(b.to, 0.35, -0.2, 1, 2), ink = _moInk(b, 'color', 'currentColor');
  var font = _ffPick(b.font, _FF_FONTS, 'sans'), weight = _ffPick(b.weight, _FF_WEIGHTS, 'bold');
  return '<span style="display:inline-block;font-family:' + font + ';font-weight:' + weight + ';font-size:' + size + 'px;line-height:1.2;color:' + ink + ';white-space:nowrap;letter-spacing:calc((' + from + ' + (' + to + ' - ' + from + ')*clamp(0,var(--s,1),1))*1em);opacity:clamp(0,calc(var(--p,1)*4),1);">' + _esc(text) + '</span>';
};

// motion_tabs: a strip of equal tabs with an underline that slides from the first to the last as the step dial runs; the tab under the line is the bright one. The labels are real text.
_RENDERERS['motion_tabs'] = function(b) {
  var src = _bxList(b.items, 6), items = [], i;
  for (i = 0; i < src.length; i++) items.push(_moStr(src[i], 24) || ('Tab ' + (i + 1)));
  while (items.length < 2) items.push('Tab ' + (items.length + 1));
  var n = items.length, size = _ffInt(b.size, 28, 12, 80), ink = _moInk(b, 'color', 'currentColor'), acc = _moInk(b, 'accent', '#2563eb'), pos = 'var(--s,1)*' + (n - 1), cells = '';
  items.forEach(function(t, j) {
    cells += '<span style="text-align:center;padding:0.5em 0.4em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:calc(0.7 + 0.3*clamp(0,calc(1 - abs(' + pos + ' - ' + j + ')),1));">' + _esc(t) + '</span>';
  });
  return '<div style="position:relative;display:grid;grid-template-columns:repeat(' + n + ',1fr);width:100%;font-size:' + size + 'px;font-weight:600;color:' + ink + ';border-bottom:1px solid ' + ink + '33;opacity:clamp(0,calc(var(--p,1)*4),1);">' + cells +
    '<span aria-hidden="true" style="position:absolute;bottom:-1px;height:3px;border-radius:2px;background:' + acc + ';width:calc(70%/' + n + ');left:calc((' + pos + ' + 0.15)*100%/' + n + ');"></span></div>';
};

// ── showpiece pack (2026-10-12): foil, wrap, drop, flag, disperse, reveal, streak ───────────────────────────────────────────────────────────────
// Seven text atoms for the cinematic end of the range, each with many looks behind enums. Same rules as the rest: every value is an enum or a clamped number, the words are
// real text, every dial defaults to the finished picture (so a standalone render is readable), motion is the film's p (builds) and s (steps), nothing loops or flashes.
function _tfBase(b, size0) {
  return {font: _ffPick(b.font, _FF_FONTS, 'sans'), weight: _ffPick(b.weight, _FF_WEIGHTS, 'bold'), size: _ffInt(b.size, size0, 10, 300), color: _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), align: _ffPick(b.align, _MO_ALIGN, 'middle')};
}
function _tfBox(f, inner, extra) {
  return 'font-family:' + f.font + ';font-weight:' + f.weight + ';font-size:' + f.size + 'px;line-height:1.1;white-space:nowrap;color:' + f.color + ';text-align:' + f.align + ';' + (extra || '');
}
function _tfOrder(n, mode, seed) {
  var m = [], i; for (i = 0; i < n; i++) m.push(i);
  if (mode === 'reverse') return m.map(function(x) { return n - 1 - x; });
  var idx = m.slice(), c = (n - 1) / 2;
  if (mode === 'centre') idx.sort(function(a, d) { return (Math.abs(a - c) - Math.abs(d - c)) || (a - d); });
  else if (mode === 'random') idx.sort(function(a, d) { return (_bxSeed(seed, a, 9) - _bxSeed(seed, d, 9)) || (a - d); });
  else return m;
  idx.forEach(function(t, r) { m[t] = r; });
  return m;
}
var _TF_ORDER = {forward: 'forward', reverse: 'reverse', centre: 'centre', random: 'random'};

// motion_foil: a metallic or iridescent gradient fills the letters and a band of light sweeps through them with the step dial.
var _FL_LOOK = {
  chrome: ['linear-gradient(180deg,#f8fafc 0%,#94a3b8 44%,#f1f5f9 50%,#334155 56%,#cbd5e1 100%)', '#ffffff'],
  gold: ['linear-gradient(180deg,#fff3b0 0%,#d4a017 44%,#fff0a0 50%,#8a5a00 58%,#f6d365 100%)', '#fffbe0'],
  silver: ['linear-gradient(180deg,#ffffff 0%,#b8c0cc 48%,#eef2f7 52%,#8a94a3 100%)', '#ffffff'],
  copper: ['linear-gradient(180deg,#ffd9b8 0%,#c8754b 45%,#ffcfa6 50%,#7a3b1d 60%,#e29a6b 100%)', '#fff0e0'],
  holo: ['linear-gradient(110deg,#ff9ad5,#9ad1ff,#b6ff9a,#ffe39a,#ff9ad5)', '#ffffff'],
  rainbow: ['linear-gradient(90deg,#ff4d4d,#ffb84d,#fff94d,#4dff88,#4db8ff,#a64dff)', '#ffffff'],
  aurora: ['linear-gradient(120deg,#34e0c3,#6d6af7,#ff5ea8)', '#e8fffb'],
  ice: ['linear-gradient(180deg,#e0f7ff,#7ac7ff 55%,#d8f0ff)', '#ffffff'],
  oil: ['linear-gradient(135deg,#1b1b2f,#3a1c71,#d76d77,#ffaf7b,#1b1b2f)', '#ffe9d6'],
  mono: ['linear-gradient(180deg,currentColor,currentColor)', '#ffffff']
};
var _FL_DIR = {ltr: [100, 0, 0], rtl: [100, 0, 1], diagonal: [135, 0, 0], down: [180, 1, 0], up: [180, 1, 1]};
_RENDERERS['motion_foil'] = function(b) {
  var text = _moStr(b.text, 60) || 'Text', f = _tfBase(b, 72), lk = _ffPick(b.look, _FL_LOOK, 'chrome'), dr = _ffPick(b.direction, _FL_DIR, 'ltr'), bands = _ffInt(b.bands, 1, 1, 3), hw = _ffInt(b.width, 10, 3, 30) / 2;
  var sh = _moInk(b, 'sheen', lk[1]), cs = bands === 1 ? [50] : bands === 2 ? [40, 60] : [30, 50, 70], g = 'linear-gradient(' + dr[0] + 'deg,transparent 0%', i;
  for (i = 0; i < cs.length; i++) g += ',transparent ' + _ifFmt(cs[i] - hw) + '%,' + sh + ' ' + cs[i] + '%,transparent ' + _ifFmt(cs[i] + hw) + '%';
  g += ',transparent 100%)';
  var pos = dr[2] ? 'clamp(0,var(--s,1),1)' : '(1 - clamp(0,var(--s,1),1))';
  return '<div style="' + _tfBox(f) + '"><span style="display:inline-block;background-image:' + g + ',' + lk[0] + ';background-size:' + (dr[1] ? '100% 300%' : '300% 100%') + ',100% 100%;background-position:' +
    (dr[1] ? '0 calc(' + pos + '*100%)' : 'calc(' + pos + '*100%) 0') + ',0 0;background-repeat:no-repeat;-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;opacity:clamp(0,calc(var(--p,1)*4),1);">' + _esc(text) + '</span></div>';
};

// motion_wrap: letters set on a 3D form that turns with the step dial: a cylinder, a wheel, a helix or a swaying ribbon. Letters at the back dim. The words are the accessible name.
var _WR_FORM = {cylinder: 'cylinder', wheel: 'wheel', helix: 'helix', ribbon: 'ribbon'};
_RENDERERS['motion_wrap'] = function(b) {
  var text = _moStr(b.text, 40) || 'Text', f = _tfBase(b, 56), form = _ffPick(b.form, _WR_FORM, 'cylinder'), arc = _ffInt(b.arc, 360, 60, 360), R = _ffInt(b.radius, 220, 60, 800), turns = _ffInt(b.turns, 1, -3, 3), lean = _ffInt(b.lean, -10, -45, 45);
  var base = Array.from(arc >= 300 ? text + ' · ' : text), chars = [], i; while (chars.length < (arc >= 300 ? 14 : 1)) chars = chars.concat(base);
  chars = chars.slice(0, 48); var N = chars.length, step = arc / N, rot = 'calc(var(--s,1)*' + (turns * 360) + 'deg)', out = '';
  for (i = 0; i < N; i++) {
    var th = _ifFmt((i - (N - 1) / 2) * step), phi = 'calc(' + th + 'deg + ' + rot + ')', front = 'clamp(0,calc((cos(' + phi + ') + 1)*0.7 - 0.2),1)', tf;
    if (form === 'wheel') tf = 'rotateX(' + th + 'deg) translateZ(' + R + 'px)';
    else if (form === 'helix') tf = 'translateY(' + _ifFmt((i - (N - 1) / 2) * f.size * 0.26) + 'px) rotateY(' + th + 'deg) translateZ(' + R + 'px)';
    else if (form === 'ribbon') tf = 'translateY(calc(sin(calc(' + th + 'deg*2 + ' + rot + '))*' + _ifFmt(f.size * 0.4) + 'px)) rotateY(' + th + 'deg) translateZ(' + R + 'px)';
    else tf = 'rotateY(' + th + 'deg) translateZ(' + R + 'px)';
    out += '<span aria-hidden="true" style="position:absolute;left:50%;top:50%;margin:-0.55em 0 0 -0.3em;white-space:pre;transform:' + tf + ';opacity:calc(' + front + '*clamp(0,calc(var(--p,1)*3),1));">' + _esc(chars[i]) + '</span>';
  }
  var spin = form === 'wheel' ? 'rotateX(calc(' + lean + 'deg)) rotateY(0deg) rotateX(' + rot + ')' : 'rotateX(' + lean + 'deg) rotateY(' + rot + ')';
  return '<div role="img" aria-label="' + _esc(text) + '" style="position:relative;width:100%;height:' + Math.round(f.size * 2.6 + (form === 'wheel' ? R * 0.2 : 0)) + 'px;perspective:1100px;overflow:visible;' + _tfBox(f) + '">' +
    '<span aria-hidden="true" style="position:absolute;inset:0;transform-style:preserve-3d;transform:scale(calc(0.7 + 0.3*clamp(0,var(--p,1),1))) ' + spin + ';">' + out + '</span></div>';
};

// motion_drop: letters fall, toss, spring or swing into place, one after another with p; each letter's motion is a pure function of p, so it can be sought.
var _DR_MODE = {bounce: 'bounce', spring: 'spring', rain: 'rain', pile: 'pile', rise: 'rise', swing: 'swing'};
_RENDERERS['motion_drop'] = function(b) {
  var text = _moStr(b.text, 48) || 'Text', f = _tfBase(b, 64), mode = _ffPick(b.mode, _DR_MODE, 'bounce'), H = _ffInt(b.height, 200, 20, 800), B = _ffInt(b.bounces, 3, 1, 8), S = _ffInt(b.overlap, 3, 1, 8), seed = _ffInt(b.seed, 3, 0, 999), ord = _ffPick(b.order, _TF_ORDER, 'forward');
  var chars = Array.from(text), N = chars.length, om = _tfOrder(N, ord, seed), out = '', i;
  for (i = 0; i < N; i++) {
    var u = 'clamp(0,calc((var(--p,1)*' + (N + S) + ' - ' + om[i] + ')/' + S + '),1)', e = 'calc(1 - var(--u))', tf, op = 'clamp(0,calc(var(--u)*6),1)', org = '';
    var rs = _ifFmt((_bxSeed(seed, i, 3) - 0.5) * 80), xs = _ifFmt((_bxSeed(seed, i, 5) - 0.5) * f.size * 4);
    if (mode === 'bounce') tf = 'translateY(calc(-' + H + 'px*' + e + '*' + e + '*abs(cos(calc(var(--u)*' + B + '*3.14159rad))))) scaleY(calc(1 - 0.3*clamp(0,calc(1 - abs(cos(calc(var(--u)*' + B + '*3.14159rad)))*8),1)*' + e + '))';
    else if (mode === 'spring') tf = 'translateY(calc(-' + H + 'px*' + e + '*cos(calc(var(--u)*' + B + '*6.28318rad))))';
    else if (mode === 'rain') tf = 'translateY(calc(-' + H + 'px*' + e + '*' + e + '*' + e + ')) rotate(calc(' + rs + 'deg*' + e + '))';
    else if (mode === 'pile') tf = 'translate(calc(' + xs + 'px*' + e + '*' + e + '),calc(-' + H + 'px*' + e + '*' + e + ')) rotate(calc(' + rs + 'deg*' + e + '))';
    else if (mode === 'rise') tf = 'translate(calc(' + _ifFmt(parseFloat(xs) / 4) + 'px*' + e + '*sin(calc(var(--u)*9.42rad))),calc(' + H + 'px*' + e + '*' + e + '))';
    else { tf = 'rotate(calc(' + _ifFmt(28 + _bxSeed(seed, i, 7) * 20) + 'deg*' + e + '*cos(calc(var(--u)*' + B + '*6.28318rad))))'; org = 'transform-origin:50% -0.15em;'; }
    out += '<span aria-hidden="true" style="--u:' + u + ';display:inline-block;white-space:pre;' + org + 'opacity:' + op + ';transform:' + tf + ';">' + _esc(chars[i]) + '</span>';
  }
  return '<div style="' + _tfBox(f) + '">' + _moSr(text) + '<span aria-hidden="true" style="display:block;">' + out + '</span></div>';
};

// motion_flag: the line ripples like cloth as the step dial runs: a flag pinned at one end, an even ripple or a ribbon. Flat at both ends of s; each letter also catches the light.
var _FG_MODE = {flag: 'flag', ripple: 'ripple', ribbon: 'ribbon', breeze: 'breeze'};
_RENDERERS['motion_flag'] = function(b) {
  var text = _moStr(b.text, 48) || 'Text', f = _tfBase(b, 64), mode = _ffPick(b.mode, _FG_MODE, 'flag'), A = _ffInt(b.amp, 18, 2, 80), W = _ffInt(b.waves, 2, 1, 5), C = _ffInt(b.cycles, 2, 1, 6), shade = b.shade !== false, pin = b.pin === 'right' ? 'right' : 'left';
  var chars = Array.from(text), N = chars.length, out = '', i, env = 'sin(calc(var(--s,0)*3.14159rad))';
  for (i = 0; i < N; i++) {
    var x = N > 1 ? i / (N - 1) : 0, fr = pin === 'right' ? 1 - x : x, ph = 'calc(' + _ifFmt(x * W * 6.28318) + 'rad - var(--s,0)*' + (C * 6.28318) + 'rad)', amp = mode === 'flag' ? A + 'px*' + _ifFmt(fr) : mode === 'breeze' ? A + 'px*' + _ifFmt(0.4 + 0.6 * _bxSeed(7, i, 1)) : A + 'px', tf;
    var ty = 'calc(' + amp + '*' + env + '*sin(' + ph + '))', rt = 'calc(' + _ifFmt(A * 0.5 * (mode === 'flag' ? fr : 1)) + 'deg*' + env + '*cos(' + ph + '))';
    tf = mode === 'ribbon' ? 'translateY(' + ty + ') rotateX(calc(60deg*' + env + '*sin(' + ph + '))) rotate(' + rt + ')' : 'translateY(' + ty + ') rotate(' + rt + ')';
    out += '<span aria-hidden="true" style="display:inline-block;white-space:pre;transform:' + tf + ';' + (shade ? 'filter:brightness(calc(1 + 0.3*' + env + '*cos(' + ph + ')));' : '') + 'opacity:clamp(0,calc(var(--p,1)*' + (N + 2) + ' - ' + i + '),1);">' + _esc(chars[i]) + '</span>';
  }
  return '<div style="' + _tfBox(f, '', 'perspective:700px;') + '">' + _moSr(text) + '<span aria-hidden="true" style="display:block;">' + out + '</span></div>';
};

// motion_disperse: the exit. With the step dial at 0 the line is whole; as it runs to 1 the letters leave in one of eight ways, each from a seeded per-letter path.
var _DP_MODE = {smoke: 'smoke', shatter: 'shatter', rise: 'rise', sink: 'sink', implode: 'implode', explode: 'explode', wind: 'wind', evaporate: 'evaporate'};
_RENDERERS['motion_disperse'] = function(b) {
  var text = _moStr(b.text, 48) || 'Text', f = _tfBase(b, 64), mode = _ffPick(b.mode, _DP_MODE, 'smoke'), S = _ffInt(b.overlap, 3, 1, 8), seed = _ffInt(b.seed, 3, 0, 999), ord = _ffPick(b.order, _TF_ORDER, 'forward'), D = _ffInt(b.distance, 90, 10, 400);
  var chars = Array.from(text), N = chars.length, om = _tfOrder(N, ord, seed), out = '', i;
  for (i = 0; i < N; i++) {
    var dx = (_bxSeed(seed, i, 1) - 0.5) * 2, dy = (_bxSeed(seed, i, 2) - 0.5) * 2, rr = (_bxSeed(seed, i, 3) - 0.5) * 2, c = (i - (N - 1) / 2) / Math.max(N, 1), d = 'var(--d)', tf, op = 'calc(1 - ' + d + ')', fl = '';
    if (mode === 'smoke') { tf = 'translate(calc(' + _ifFmt(dx * D * 0.6) + 'px*' + d + '),calc(-' + D + 'px*' + d + ')) scale(calc(1 + ' + d + '*0.6))'; fl = 'filter:blur(calc(' + d + '*10px));'; }
    else if (mode === 'shatter') { tf = 'translate(calc(' + _ifFmt(dx * D * 1.4) + 'px*' + d + '),calc(' + _ifFmt(dy * D * 1.4) + 'px*' + d + ')) rotate(calc(' + _ifFmt(rr * 200) + 'deg*' + d + '))'; }
    else if (mode === 'rise') { tf = 'translateY(calc(-' + D + 'px*' + d + '))'; }
    else if (mode === 'sink') { tf = 'translateY(calc(' + D + 'px*' + d + '*' + d + ')) rotate(calc(' + _ifFmt(rr * 30) + 'deg*' + d + '))'; }
    else if (mode === 'implode') { tf = 'translateX(calc(' + _ifFmt(-c * 2 * N * f.size * 0.5) + 'px*' + d + ')) scale(calc(1 - ' + d + '))'; op = 'calc(1 - ' + d + '*' + d + ')'; }
    else if (mode === 'explode') { tf = 'translate(calc(' + _ifFmt(dx * D * 2) + 'px*' + d + '),calc(' + _ifFmt(dy * D * 2) + 'px*' + d + ')) scale(calc(1 + ' + d + '*2.5))'; op = 'calc(1 - ' + d + ')'; }
    else if (mode === 'wind') { tf = 'translate(calc(' + _ifFmt(D * 2 + dx * D * 0.5) + 'px*' + d + '),calc(' + _ifFmt(dy * D * 0.3) + 'px*' + d + ')) rotate(calc(' + _ifFmt(rr * 120) + 'deg*' + d + '))'; fl = 'filter:blur(calc(' + d + '*3px));'; }
    else { tf = 'translateY(calc(-' + _ifFmt(D * 0.35) + 'px*' + d + ')) scaleY(calc(1 + ' + d + '*0.8))'; fl = 'filter:blur(calc(' + d + '*8px));'; op = 'calc(1 - ' + d + '*1.2)'; }
    out += '<span aria-hidden="true" style="--d:clamp(0,calc((var(--s,0)*' + (N + S) + ' - ' + om[i] + ')/' + S + '),1);display:inline-block;white-space:pre;transform:' + tf + ';opacity:calc(' + op + '*clamp(0,calc(var(--p,1)*4),1));' + fl + '">' + _esc(chars[i]) + '</span>';
  }
  return '<div style="' + _tfBox(f) + '">' + _moSr(text) + '<span aria-hidden="true" style="display:block;">' + out + '</span></div>';
};

// motion_reveal: the line is uncovered through a moving mask as p goes 0 to 1: ten looks (blinds, iris, diamond, clock, dots, searchlight, a laser line and soft or hard wipes).
var _RV_MODE = {blinds: 'blinds', slats: 'slats', iris: 'iris', diamond: 'diamond', clock: 'clock', halftone: 'halftone', searchlight: 'searchlight', laser: 'laser', soft: 'soft', diagonal: 'diagonal'};
_RENDERERS['motion_reveal'] = function(b) {
  var raw = (typeof b.text === 'string' ? b.text : '').split('\n'), lines = [], i;
  for (i = 0; i < raw.length && lines.length < 4; i++) { var ln = raw[i].trim().slice(0, 60); if (ln) lines.push(ln); }
  if (!lines.length) lines = ['Text'];
  var f = _tfBase(b, 64), mode = _ffPick(b.mode, _RV_MODE, 'blinds'), n = _ffInt(b.slats, 8, 3, 24), fe = _ffInt(b.feather, 18, 0, 40), lc = _moInk(b, 'line', '#34e0c3'), p = 'var(--p,1)', m = '', size = '', extra = '';
  var K = 'clamp(0,' + p + ',1)';
  if (mode === 'blinds') { m = 'linear-gradient(180deg,#000 calc(' + K + '*100%),transparent calc(' + K + '*100%))'; size = '100% ' + _ifFmt(100 / n) + '%'; }
  else if (mode === 'slats') { m = 'linear-gradient(90deg,#000 calc(' + K + '*100%),transparent calc(' + K + '*100%))'; size = _ifFmt(100 / n) + '% 100%'; }
  else if (mode === 'diagonal') { m = 'linear-gradient(135deg,#000 calc(' + K + '*100%),transparent calc(' + K + '*100%))'; size = _ifFmt(100 / n) + '% ' + _ifFmt(100 / n) + '%'; }
  else if (mode === 'halftone') { m = 'radial-gradient(circle,#000 calc(' + K + '*75%),transparent calc(' + K + '*75% + 1px))'; size = _ifFmt(100 / n) + '% ' + _ifFmt(100 / (n / 2)) + '%'; }
  else if (mode === 'iris') m = 'radial-gradient(circle at 50% 50%,#000 calc(' + K + '*75%),transparent calc(' + K + '*75% + ' + fe + '%))';
  else if (mode === 'clock') m = 'conic-gradient(from 0deg,#000 calc(' + K + '*360deg),transparent calc(' + K + '*360deg))';
  else if (mode === 'searchlight') m = 'radial-gradient(circle at calc(' + K + '*100%) 50%,#000 calc(' + K + '*70%),transparent calc(' + K + '*70% + ' + (fe + 12) + '%))';
  else if (mode === 'laser') m = 'linear-gradient(90deg,#000 calc(' + K + '*100%),transparent calc(' + K + '*100%))';
  else m = 'linear-gradient(90deg,#000 calc(' + K + '*(100% + ' + fe + '%) - ' + fe + '%),transparent calc(' + K + '*(100% + ' + fe + '%)))';
  var msk = 'mask-image:' + m + ';-webkit-mask-image:' + m + ';' + (size ? 'mask-size:' + size + ';-webkit-mask-size:' + size + ';' : '');
  if (mode === 'diamond') { msk = 'clip-path:polygon(50% calc(50% - ' + K + '*75%),calc(50% + ' + K + '*75%) 50%,50% calc(50% + ' + K + '*75%),calc(50% - ' + K + '*75%) 50%);'; }
  var body = lines.map(function(l) { return _esc(l); }).join('<br>');
  if (mode === 'laser') extra = '<span aria-hidden="true" style="position:absolute;top:-4%;bottom:-4%;left:calc(' + K + '*100%);width:2px;margin-left:-1px;background:' + lc + ';box-shadow:0 0 14px 4px ' + lc + ';opacity:clamp(0,calc(1 - ' + K + '*1.1),1)"></span>';
  return '<div style="position:relative;' + _tfBox(f) + '"><span style="display:inline-block;' + msk + '">' + body + '</span>' + extra + '</div>';
};

// motion_streak: the line whips in from one side leaving ghost copies behind it, which fade as it settles; the cheap CSS stand-in for a motion blur.
var _SK_DIR = {left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1], diagonal: [-1, -1]};
_RENDERERS['motion_streak'] = function(b) {
  var text = _moStr(b.text, 60) || 'Text', f = _tfBase(b, 72), dr = _ffPick(b.direction, _SK_DIR, 'left'), G = _ffInt(b.ghosts, 5, 2, 10), D = _ffNum(b.distance, 6, 1, 14, 1), tint = _moInk(b, 'tint', ''), k = 'clamp(0,var(--p,1),1)', e = '(1 - ' + k + ')', out = '', i;
  for (i = 1; i <= G; i++) {
    var fr = _ifFmt(i / G);
    out += '<span aria-hidden="true" style="position:absolute;left:0;top:0;white-space:nowrap;' + (tint ? 'color:' + tint + ';' : '') + 'transform:translate(calc(' + dr[0] + '*' + D + 'em*' + e + '*(1 + ' + fr + '*0.7)),calc(' + dr[1] + '*' + D + 'em*' + e + '*(1 + ' + fr + '*0.7)));opacity:calc(' + _ifFmt(0.5 * (1 - i / (G + 1))) + '*' + e + '*clamp(0,calc(' + k + '*6),1));filter:blur(calc(' + _ifFmt(i * 0.6) + 'px*' + e + '));">' + _esc(text) + '</span>';
  }
  return '<div style="' + _tfBox(f) + '">' + _moSr(text) + '<span aria-hidden="true" style="position:relative;display:inline-block;white-space:nowrap;">' + out +
    '<span style="position:relative;display:inline-block;transform:translate(calc(' + dr[0] + '*' + D + 'em*' + e + '),calc(' + dr[1] + '*' + D + 'em*' + e + '));opacity:clamp(0,calc(' + k + '*4),1);">' + _esc(text) + '</span></span></div>';
};
