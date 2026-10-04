// atoms_motion.gs — design motion as a composable catalogue style (2026-09-30).
//
// THREE LAYERS, each usable alone, each built on the same vocabulary:
//
//   1. TOKENS   _MO_EASE (named cubic-bezier curves, intent-named) and _MO_DUR
//               (instant/quick/base/slow/cinematic). Every motion atom and the
//               generic `enter` prop accept a token name OR four raw numbers.
//   2. ENTER    a generic `enter` prop that works on ANY atom: {effect, ease,
//               duration, delay, on}. _moInstall() wraps every _RENDERERS entry
//               once, so the prop also works on atoms nested inside containers
//               that call _RENDERERS[...] directly. No `enter` => the wrapped
//               function returns the original markup byte for byte.
//   3. TIMELINE motion_timeline drives a stage of child atoms from ONE clock.
//               Everything on screen is a pure function of time t (seek(t)),
//               which is what makes it scrubbable, loopable and exportable
//               frame-by-frame (open the page with #t=3.2 to freeze on a frame).
//               Keys are destinations: {t, x, ease} means "arrive at x at t using
//               ease" (GSAP `.to()` semantics), easing the segment BEFORE the key.
//
// The demo kit (demo_window, demo_kpis, demo_chart, demo_toggle_grid,
// demo_progress, demo_cursor, demo_caption, demo_orb, demo_panel) is plain
// HTML+CSS whose visuals hang off three custom properties the timeline sets:
//   --p  progress 0..1 (chart draw, bar growth, toggles, fills, click ripple)
//   --s  step, a float that crossfades between caption lines
//   [data-mt-num] numbers recount as --p moves
// Standalone (no timeline) every one of them renders its FINAL state.
//
// Security posture (same as flow_field): every option is an enum or a clamped
// number, colours must be #rrggbb, ids match [a-z][a-z0-9_-]{0,31}, the script's
// config object contains only validated numbers and ids, agent text goes only
// through _esc into element content. Python twin: renderers/web_article.py.
// tests/test_motion_atoms.py holds the two together. Edit BOTH.

var _MO_EASE = {
  'linear': [0, 0, 1, 1],
  'ease': [0.25, 0.1, 0.25, 1],
  'ease-in': [0.42, 0, 1, 1],
  'ease-out': [0, 0, 0.58, 1],
  'ease-in-out': [0.42, 0, 0.58, 1],
  'overshoot': [0.34, 1.56, 0.64, 1],
  'anticipate': [0.68, -0.55, 0.27, 1.55],
  'standard': [0.4, 0, 0.2, 1],
  'emphasized': [0.2, 0, 0, 1],
  'decelerate': [0, 0, 0.2, 1],
  'accelerate': [0.4, 0, 1, 1],
  'expo-out': [0.16, 1, 0.3, 1],
  'quint-out': [0.22, 1, 0.36, 1],
  'quart-in-out': [0.76, 0, 0.24, 1],
  'expo-in-out': [0.87, 0, 0.13, 1]
};
// What each curve is FOR, in the order motion_tokens lists them.
var _MO_EASE_ORDER = ['expo-out', 'quint-out', 'decelerate', 'standard', 'emphasized', 'quart-in-out', 'expo-in-out', 'accelerate', 'overshoot', 'anticipate', 'ease', 'ease-in', 'ease-out', 'ease-in-out', 'linear'];
var _MO_EASE_NOTE = {
  'expo-out': 'arrivals: fast launch, long soft landing',
  'quint-out': 'settling UI: a touch gentler than expo-out',
  'decelerate': 'elements entering from off-screen',
  'standard': 'on-screen moves: cursor glides, reflows',
  'emphasized': 'the one hero move on a scene',
  'quart-in-out': 'camera moves and wipes',
  'expo-in-out': 'big symmetric transitions',
  'accelerate': 'exits: leaving the stage',
  'overshoot': 'playful landings (use once, sparingly)',
  'anticipate': 'wind-up before a move (use once)',
  'ease': 'CSS default',
  'ease-in': 'CSS ease-in',
  'ease-out': 'CSS ease-out',
  'ease-in-out': 'CSS ease-in-out',
  'linear': 'progress bars and loops only'
};
var _MO_DUR = {instant: 120, quick: 240, base: 400, slow: 640, cinematic: 1000};
var _MO_FX = {
  'fade': {kf: 'from{opacity:0}', e: 'expo-out', d: 560},
  'rise': {kf: 'from{opacity:0;transform:translateY(24px)}', e: 'expo-out', d: 560},
  'drop': {kf: 'from{opacity:0;transform:translateY(-24px)}', e: 'expo-out', d: 560},
  'slide-left': {kf: 'from{opacity:0;transform:translateX(-32px)}', e: 'expo-out', d: 560},
  'slide-right': {kf: 'from{opacity:0;transform:translateX(32px)}', e: 'expo-out', d: 560},
  'scale': {kf: 'from{opacity:0;transform:scale(0.92)}', e: 'quint-out', d: 560},
  'blur': {kf: 'from{opacity:0;filter:blur(12px);transform:translateY(8px)}', e: 'expo-out', d: 560},
  'wipe': {kf: 'from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}', e: 'quart-in-out', d: 720},
  'pop': {kf: 'from{opacity:0;transform:scale(0.6)}', e: 'overshoot', d: 480}
};
var _MO_FX_ORDER = ['fade', 'rise', 'drop', 'slide-left', 'slide-right', 'scale', 'blur', 'wipe', 'pop'];

function _moId(v) {
  return (typeof v === 'string' && /^[a-z][a-z0-9_-]{0,31}$/.test(v)) ? v : '';
}
// A token name or four numbers -> four fixed-decimal strings (x clamped 0..1, y -1..2).
function _moEaseArr(v, dflt) {
  var a = null;
  if (typeof v === 'string' && Object.prototype.hasOwnProperty.call(_MO_EASE, v)) a = _MO_EASE[v];
  else if (Array.isArray(v) && v.length === 4) a = v;
  if (!a) a = _MO_EASE[dflt];
  return [_ffNum(a[0], 0, 0, 1, 3), _ffNum(a[1], 0, -1, 2, 3), _ffNum(a[2], 0, 0, 1, 3), _ffNum(a[3], 0, -1, 2, 3)];
}
function _moEaseCss(v, dflt) { return 'cubic-bezier(' + _moEaseArr(v, dflt).join(',') + ')'; }
// Config spelling of an ease inside the timeline script: 0 = linear, 1 = hold, else [x1,y1,x2,y2].
function _moEaseJs(v, dflt) {
  if (v === undefined || v === null) v = dflt;
  if (v === 'hold') return '1';
  if (v === 'linear') return '0';
  return '[' + _moEaseArr(v, dflt).join(',') + ']';
}
function _moDur(v, dflt) {
  if (typeof v === 'string' && Object.prototype.hasOwnProperty.call(_MO_DUR, v)) return _MO_DUR[v];
  return _ffInt(v, dflt, 0, 8000);
}

// ─── enter: the generic entrance, any atom ──────────────────────────────────
// enter = "rise" | {effect, ease, duration, delay, on: "load"|"view"}
function _moEnterSpec(e) {
  if (typeof e === 'string') e = {effect: e};
  if (!e || typeof e !== 'object') return null;
  var name = (typeof e.effect === 'string' && Object.prototype.hasOwnProperty.call(_MO_FX, e.effect)) ? e.effect : 'rise';
  var fx = _MO_FX[name];
  return {
    name: name,
    kf: '@keyframes moe-' + name + '{' + fx.kf + '}',
    ease: _moEaseCss(e.ease, fx.e),
    dur: _moDur(e.duration, fx.d),
    delay: _ffInt(e.delay, 0, 0, 20000),
    view: e.on === 'view'
  };
}
var _MO_VIEW_JS =
  '(function(){var e=document.getElementById("mo-%%UID%%");if(!e)return;' +
  'if(!window.IntersectionObserver)return;e.classList.add("mo-arm");' +
  'var o=new IntersectionObserver(function(a){if(a[0].isIntersecting){e.classList.remove("mo-arm");o.disconnect();}},{threshold:0.15});o.observe(e);' +
  '})();';
function _moEnterWrap(s, html, extraDelay) {
  var uid = s.view ? Math.random().toString(36).substr(2, 6) : '';
  return '<style>' + s.kf + '@media (prefers-reduced-motion:reduce){.mo-x{animation:none!important}}@media print{.mo-x{animation:none!important}}.mo-arm{animation-play-state:paused!important}</style>'
    + '<div class="mo-x"' + (uid ? ' id="mo-' + uid + '"' : '') + ' style="animation:moe-' + s.name + ' ' + s.dur + 'ms ' + s.ease + ' ' + (s.delay + (extraDelay || 0)) + 'ms both;">' + html + '</div>'
    + (uid ? '<script>' + _MO_VIEW_JS.replace(/%%UID%%/g, uid) + '<\/script>' : '');
}
function _moEnter(b, html) {
  var s = _moEnterSpec(b.enter);
  return s ? _moEnterWrap(s, html, 0) : html;
}
// Wrap every registered renderer once. Safe to call repeatedly and from any entry
// point: a wrapped function carries _mo and is skipped. Called from renderAtoms
// (and the Worker/bundle entry points share that function).
function _moInstall() {
  for (var k in _RENDERERS) {
    var f = _RENDERERS[k];
    if (typeof f !== 'function' || f._mo) continue;
    _RENDERERS[k] = (function(f) {
      var w = function(b) {
        var h = f(b);
        return (b && typeof b === 'object' && b.enter) ? _moEnter(b, h) : h;
      };
      w._mo = true;
      return w;
    })(f);
  }
}

// One child block of a motion container, rendered through the (wrapped) registry.
function _moRender(blk) {
  if (!blk || typeof blk !== 'object') return '';
  var t = blk.component || blk.type, fn = _RENDERERS[t];
  if (!fn) return '<!-- a2ui: unknown atom "' + _esc(t) + '" -->';
  try { return fn(blk); } catch (err) { return '<!-- a2ui: ' + _esc(t) + ' failed: ' + _esc(err.message) + ' -->'; }
}
// ...and, when it has an `id`, addressable by a timeline track (data-mt-id).
function _moChild(blk) {
  var html = _moRender(blk), id = blk && typeof blk === 'object' ? _moId(blk.id) : '';
  return id ? '<div data-mt-id="' + id + '">' + html + '</div>' : html;
}

// ─── motion_group: staggered entrance for a list of blocks ─────────────────
_RENDERERS['motion_group'] = function(b) {
  var blocks = Array.isArray(b.blocks) ? b.blocks : [];
  var s = _moEnterSpec({effect: b.effect, ease: b.ease, duration: b.duration, delay: b.delay, on: b.on});
  var stagger = _ffInt(b.stagger, 80, 0, 1000), out = [], n = Math.min(blocks.length, 40);
  for (var i = 0; i < n; i++) out.push(_moEnterWrap(s, _moChild(blocks[i]), i * stagger));
  var note = blocks.length > n ? '<!-- a2ui: motion_group showed ' + n + ' of ' + blocks.length + ' blocks (max 40) -->' : '';
  return out.join('') + note;
};

// ─── motion_tokens: the vocabulary, drawn ──────────────────────────────────
_RENDERERS['motion_tokens'] = function(b) {
  var th = _ffTheme(b), acc = _ffHex(b.accent, '#38bdf8');
  var show = (b.show === 'ease' || b.show === 'duration') ? b.show : 'both';
  var mono = _CV_VOICES.mono, rows = '', i, k, a, css;
  if (show !== 'duration') {
    for (i = 0; i < _MO_EASE_ORDER.length; i++) {
      k = _MO_EASE_ORDER[i]; a = _moEaseArr(k, 'standard'); css = 'cubic-bezier(' + a.join(',') + ')';
      rows += '<div style="display:grid;grid-template-columns:minmax(96px,132px) 1fr;gap:6px 14px;align-items:center;padding:9px 0;border-top:1px solid ' + th.line + ';">'
        + '<div style="font-family:' + mono + ';font-size:0.8rem;color:' + th.ink + ';">' + _esc(k) + '</div>'
        + '<div style="position:relative;height:14px;border-radius:7px;background:' + th.soft + ';"><div class="mtk-dot" style="position:absolute;top:1px;left:1px;width:12px;height:12px;border-radius:50%;background:' + acc + ';animation:mtk-run 2200ms ' + css + ' infinite alternate;"></div></div>'
        + '<div></div><div style="font-size:0.72rem;color:' + th.mute + ';"><span style="font-family:' + mono + ';">' + css + '</span> · ' + _esc(_MO_EASE_NOTE[k]) + '</div></div>';
    }
  }
  var dur = '';
  if (show !== 'ease') {
    var names = ['instant', 'quick', 'base', 'slow', 'cinematic'];
    for (i = 0; i < names.length; i++) {
      var ms = _MO_DUR[names[i]];
      dur += '<div style="display:grid;grid-template-columns:minmax(96px,132px) 1fr 64px;gap:14px;align-items:center;padding:7px 0;border-top:1px solid ' + th.line + ';">'
        + '<div style="font-family:' + mono + ';font-size:0.8rem;color:' + th.ink + ';">' + names[i] + '</div>'
        + '<div style="height:8px;border-radius:4px;background:' + th.soft + ';"><div style="height:8px;border-radius:4px;background:' + acc + ';width:' + _ffNum(ms / 10, 0, 0, 100, 1) + '%;"></div></div>'
        + '<div style="font-family:' + mono + ';font-size:0.75rem;color:' + th.mute + ';text-align:right;">' + ms + 'ms</div></div>';
    }
  }
  var fxs = '';
  if (show !== 'duration') {
    fxs = '<div style="margin-top:14px;padding-top:12px;border-top:1px solid ' + th.line + ';font-size:0.72rem;color:' + th.mute + ';">enter effects: <span style="font-family:' + mono + ';">' + _MO_FX_ORDER.join(' · ') + '</span></div>';
  }
  var inner = '<div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:' + th.mute + ';margin-bottom:10px;">motion tokens</div>'
    + '<style>@keyframes mtk-run{from{transform:translateX(0)}to{transform:translateX(calc(min(520px,60vw) - 14px))}}@media (prefers-reduced-motion:reduce){.mtk-dot{animation:none!important}}</style>'
    + rows + dur + fxs;
  return _cvCard(th, inner);
};

// ─── demo kit ───────────────────────────────────────────────────────────────
var _MO_SANS = 'system-ui,-apple-system,Segoe UI,Helvetica Neue,Arial,sans-serif';
// Colours a demo atom reads from its window (or, standalone, the light defaults).
function _moTone(tone) {
  return tone === 'dark'
    ? {bg: '#0f1420', ink: '#e8edf5', mute: '#8a94a7', line: '#222a3a', soft: '#171d2b', card: '#141a27'}
    : {bg: '#ffffff', ink: '#0f172a', mute: '#64748b', line: '#e5e9f0', soft: '#f4f6fa', card: '#ffffff'};
}
function _moV(name, dflt) { return 'var(--dw-' + name + ',' + dflt + ')'; }
function _moAcc(b) { var h = _ffHex(b.accent, ''); return h || _moV('acc', '#2563eb'); }
function _moAccRgb(b) { var h = _ffHex(b.accent, ''); return h ? _ffRgb(h) : _moV('accrgb', '37,99,235'); }
function _moStr(v, max) { return _cvStr(v, max); }
// Final-state number text, integer maths so both renderers agree on the spelling.
function _moFmt(v, dec, pre, suf) {
  var x = typeof v === 'number' ? v : parseFloat(v);
  if (isNaN(x)) x = 0;
  var m = Math.pow(10, dec), n = Math.floor(Math.abs(x) * m + 0.5), ip = '' + Math.floor(n / m), fp = '' + (n % m), g = '';
  while (fp.length < dec) fp = '0' + fp;
  for (var i = ip.length; i > 0; i -= 3) g = ip.slice(Math.max(0, i - 3), i) + (g ? ',' : '') + g;
  return (x < 0 && n > 0 ? '-' : '') + pre + g + (dec > 0 ? '.' + fp : '') + suf;
}
function _moNum(v, dflt) { var x = typeof v === 'number' ? v : parseFloat(v); return isNaN(x) ? dflt : Math.max(-1e9, Math.min(1e9, x)); }
// A recounting number: its text is the final value; the timeline rewrites it from --p.
function _moCount(to, dec, pre, suf, style, from) {
  return '<span data-mt-num="1" data-from="' + _ffNum(from || 0, 0, -1e9, 1e9, dec) + '" data-to="' + _ffNum(to, 0, -1e9, 1e9, dec) + '" data-dec="' + dec + '" data-pre="' + _esc(pre) + '" data-suf="' + _esc(suf) + '"' + (style ? ' style="' + style + '"' : '') + '>' + _esc(_moFmt(to, dec, pre, suf)) + '</span>';
}

_RENDERERS['demo_window'] = function(b) {
  var tn = b.tone === 'dark' ? 'dark' : 'light', c = _moTone(tn), acc = _ffHex(b.accent, '#2563eb');
  var title = _moStr(b.title, 28) || 'App', nav = Array.isArray(b.nav) ? b.nav.slice(0, 8) : [];
  var blocks = Array.isArray(b.blocks) ? b.blocks.slice(0, 10) : [];
  var minh = _ffInt(b.height, 460, 240, 900), heading = _moStr(b.heading, 60), sub = _moStr(b.sub, 90);
  var vars = '--dw-bg:' + c.bg + ';--dw-ink:' + c.ink + ';--dw-mute:' + c.mute + ';--dw-line:' + c.line + ';--dw-soft:' + c.soft + ';--dw-card:' + c.card + ';--dw-acc:' + acc + ';--dw-accrgb:' + _ffRgb(acc) + ';';
  var items = '', act = 0;
  for (var a = 0; a < nav.length; a++) { if (nav[a] && typeof nav[a] === 'object' && nav[a].active === true) { act = a; break; } }
  for (var i = 0; i < nav.length; i++) {
    var n = nav[i] && typeof nav[i] === 'object' ? nav[i] : {label: nav[i]};
    // --k is this item's "how active am I" 0..1, from the window's --s (a timeline step track).
    var k = 'max(0,calc(1 - max(var(--s,' + act + ') - ' + i + ',' + i + ' - var(--s,' + act + '))))';
    items += '<div style="--k:' + k + ';position:relative;display:flex;align-items:center;gap:9px;padding:8px 10px;border-radius:8px;font-size:13px;font-weight:600;color:' + c.mute + ';color:color-mix(in srgb,' + acc + ' calc(var(--k)*100%),' + c.mute + ');">'
      + '<span style="position:absolute;inset:0;border-radius:8px;background:rgba(' + _ffRgb(acc) + ',0.12);opacity:var(--k);"></span>'
      + '<span style="position:relative;width:12px;height:12px;border-radius:4px;border:1.5px solid ' + c.line + ';border-color:color-mix(in srgb,' + acc + ' calc(var(--k)*100%),' + c.line + ');flex:none;"></span><span style="position:relative;">' + _esc(_moStr(n.label, 24)) + '</span></div>';
  }
  var body = '', stack = b.stack === true;
  for (var j = 0; j < blocks.length; j++) {
    if (!stack) { body += _moChild(blocks[j]); continue; }
    // stack: every child overlaps in one grid cell (pages that crossfade); a child
    // without an id is still laid out, it just cannot be animated.
    var sb = blocks[j], sid = sb && typeof sb === 'object' ? _moId(sb.id) : '';
    body += '<div' + (sid ? ' data-mt-id="' + sid + '"' : '') + ' style="grid-area:1/1;min-width:0;">' + _moRender(sb) + '</div>';
  }
  return '<div style="' + vars + 'width:100%;height:100%;min-height:' + minh + 'px;box-sizing:border-box;display:flex;border-radius:14px;overflow:hidden;background:' + c.bg + ';color:' + c.ink + ';font-family:' + _MO_SANS + ';box-shadow:0 30px 80px -24px rgba(2,6,23,0.5),0 0 0 1px ' + c.line + ';">'
    + '<div style="width:176px;flex:none;padding:16px 12px;background:' + c.soft + ';border-right:1px solid ' + c.line + ';box-sizing:border-box;">'
    + '<div style="display:flex;align-items:center;gap:8px;padding:2px 6px 14px;font-weight:700;font-size:15px;"><span style="width:18px;height:18px;border-radius:6px;background:' + acc + ';flex:none;"></span>' + _esc(title) + '</div>'
    + '<div style="display:flex;flex-direction:column;gap:2px;">' + items + '</div></div>'
    + '<div style="flex:1;min-width:0;padding:22px 26px;box-sizing:border-box;' + (stack ? 'display:grid;align-content:start;' : 'display:flex;flex-direction:column;gap:14px;') + '">'
    + (heading ? '<div><div style="font-size:21px;font-weight:700;letter-spacing:-0.01em;">' + _esc(heading) + '</div>' + (sub ? '<div style="font-size:12.5px;color:' + c.mute + ';margin-top:3px;">' + _esc(sub) + '</div>' : '') + '</div>' : '')
    + body + '</div></div>';
};

// A titled column of blocks: one screen of a demo window. Stack several inside a
// demo_window (stack:true) and crossfade them with opacity tracks.
_RENDERERS['demo_page'] = function(b) {
  var blocks = Array.isArray(b.blocks) ? b.blocks.slice(0, 8) : [], body = '', heading = _moStr(b.heading, 60), sub = _moStr(b.sub, 90);
  for (var i = 0; i < blocks.length; i++) body += _moChild(blocks[i]);
  return '<div style="display:flex;flex-direction:column;gap:14px;font-family:' + _MO_SANS + ';color:' + _moV('ink', '#0f172a') + ';">'
    + (heading ? '<div><div style="font-size:21px;font-weight:700;letter-spacing:-0.01em;">' + _esc(heading) + '</div>' + (sub ? '<div style="font-size:12.5px;color:' + _moV('mute', '#64748b') + ';margin-top:3px;">' + _esc(sub) + '</div>' : '') + '</div>' : '')
    + body + '</div>';
};

// Ghost wordmark for behind a camera move.
_RENDERERS['demo_wordmark'] = function(b) {
  var size = _ffInt(b.size, 200, 24, 600), acc = _ffHex(b.accent, '#38bdf8'), tn = b.tone === 'light' ? 'light' : 'dark';
  var ink = tn === 'light' ? '15,23,42' : '241,245,249';
  return '<div style="font-family:' + _MO_SANS + ';font-size:' + size + 'px;font-weight:800;letter-spacing:-0.04em;line-height:1;white-space:nowrap;color:transparent;-webkit-text-stroke:2px rgba(' + (b.outline === 'accent' ? _ffRgb(acc) : ink) + ',0.9);user-select:none;" aria-hidden="true">' + _esc(_moStr(b.text, 24)) + '</div>';
};

_RENDERERS['demo_kpis'] = function(b) {
  var items = Array.isArray(b.items) ? b.items.slice(0, 4) : [], out = '';
  for (var i = 0; i < items.length; i++) {
    var it = items[i] && typeof items[i] === 'object' ? items[i] : {}, dec = _ffInt(it.decimals, 0, 0, 3);
    var pre = _moStr(it.prefix, 4), suf = _moStr(it.suffix, 6), delta = _moStr(it.delta, 14);
    out += '<div style="flex:1 1 0;min-width:0;padding:12px 14px;border-radius:10px;border:1px solid ' + _moV('line', '#e5e9f0') + ';background:' + _moV('card', '#ffffff') + ';">'
      + '<div style="font-size:11.5px;color:' + _moV('mute', '#64748b') + ';font-weight:500;">' + _esc(_moStr(it.label, 24)) + '</div>'
      + '<div style="display:flex;align-items:baseline;gap:8px;margin-top:4px;"><div style="font-size:26px;font-weight:700;letter-spacing:-0.02em;color:' + _moV('ink', '#0f172a') + ';">' + _moCount(_moNum(it.value, 0), dec, pre, suf) + '</div>'
      + (delta ? '<div style="font-size:11.5px;font-weight:600;color:#16a34a;">' + _esc(delta) + '</div>' : '') + '</div></div>';
  }
  return '<div style="display:flex;gap:12px;font-family:' + _MO_SANS + ';">' + out + '</div>';
};

_RENDERERS['demo_chart'] = function(b) {
  var kind = b.kind === 'bars' ? 'bars' : 'line', raw = Array.isArray(b.data) ? b.data.slice(0, 24) : [], data = [], i;
  for (i = 0; i < raw.length; i++) data.push(_moNum(raw[i], 0));
  if (data.length < 2) data = [2, 5, 3, 7, 6, 9];
  var labels = Array.isArray(b.labels) ? b.labels : [], n = data.length, h = _ffInt(b.height, 200, 80, 500), W = 600;
  var acc = _moAcc(b), accRgb = _moAccRgb(b), lo = data[0], hi = data[0];
  for (i = 1; i < n; i++) { if (data[i] < lo) lo = data[i]; if (data[i] > hi) hi = data[i]; }
  if (kind === 'bars') lo = Math.min(0, lo);
  var span = hi - lo || 1, pad = 14, cy = function(v) { return h - pad - (v - lo) / span * (h - 2 * pad); };
  var hl = (typeof b.highlight === 'number' && b.highlight >= 0 && b.highlight < n) ? Math.floor(b.highlight) : n - 1;
  var svg = '', callX = 0, callY = 0;
  if (kind === 'bars') {
    var step = W / n, bw = step * 0.62;
    for (i = 0; i < n; i++) {
      var y = cy(data[i]), x = step * i + (step - bw) / 2, isHl = i === hl;
      svg += '<rect x="' + _ffNum(x, 0, 0, 1000, 1) + '" y="' + _ffNum(y, 0, 0, 1000, 1) + '" width="' + _ffNum(bw, 0, 0, 1000, 1) + '" height="' + _ffNum(h - pad - y, 0, 0, 1000, 1) + '" rx="3" fill="' + (isHl ? acc : 'rgba(' + accRgb + ',0.22)') + '" style="transform-box:fill-box;transform-origin:bottom;transform:scaleY(clamp(0,calc((var(--p,1)*' + (n + 3) + ' - ' + i + ')/3),1));"/>';
      if (isHl) { callX = (x + bw / 2) / W * 100; callY = y / h * 100; }
    }
  } else {
    var d = '', dx = W / (n - 1);
    for (i = 0; i < n; i++) d += (i ? 'L' : 'M') + _ffNum(dx * i, 0, 0, 1000, 1) + ' ' + _ffNum(cy(data[i]), 0, 0, 1000, 1);
    svg += '<path d="' + d + 'L' + W + ' ' + h + 'L0 ' + h + 'Z" fill="rgba(' + accRgb + ',0.10)" style="opacity:var(--p,1);"/>'
      + '<path d="' + d + '" pathLength="1" fill="none" stroke="' + acc + '" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="stroke-dasharray:1;stroke-dashoffset:calc(1 - var(--p,1));"/>';
    callX = dx * hl / W * 100; callY = cy(data[hl]) / h * 100;
  }
  var callout = _moStr(b.callout, 28), tags = '';
  if (callout) {
    tags = '<div style="position:absolute;left:' + _ffNum(callX, 0, 0, 100, 1) + '%;top:' + _ffNum(callY, 0, 0, 100, 1) + '%;transform:translate(-50%,-150%);white-space:nowrap;padding:4px 9px;border-radius:7px;font-size:11.5px;font-weight:600;background:' + _moV('ink', '#0f172a') + ';color:' + _moV('bg', '#ffffff') + ';opacity:clamp(0,calc((var(--p,1) - 0.8)*10),1);">' + _esc(callout) + '</div>';
  }
  var lab = '';
  if (labels.length) {
    lab = '<div style="display:flex;justify-content:space-between;margin-top:6px;font-size:10.5px;color:' + _moV('mute', '#64748b') + ';">';
    for (i = 0; i < n && i < labels.length; i++) lab += '<span>' + _esc(_moStr(labels[i], 8)) + '</span>';
    lab += '</div>';
  }
  return '<div style="font-family:' + _MO_SANS + ';padding:10px 12px 8px;border-radius:10px;border:1px solid ' + _moV('line', '#e5e9f0') + ';background:' + _moV('card', '#ffffff') + ';">'
    + (b.title ? '<div style="font-size:12px;font-weight:600;color:' + _moV('ink', '#0f172a') + ';margin-bottom:6px;">' + _esc(_moStr(b.title, 40)) + '</div>' : '')
    + '<div style="position:relative;height:' + h + 'px;"><svg viewBox="0 0 ' + W + ' ' + h + '" preserveAspectRatio="none" style="width:100%;height:100%;display:block;overflow:visible;" aria-hidden="true">' + svg + '</svg>' + tags + '</div>' + lab + '</div>';
};

_RENDERERS['demo_toggle_grid'] = function(b) {
  var cards = Array.isArray(b.cards) ? b.cards.slice(0, 9) : [], n = cards.length, cols = _ffInt(b.columns, 3, 1, 4), out = '';
  var acc = _moAcc(b), accRgb = _moAccRgb(b);
  for (var i = 0; i < n; i++) {
    var c = cards[i] && typeof cards[i] === 'object' ? cards[i] : {title: cards[i]};
    var on = _ffNum(c.on_at, n > 1 ? 0.12 + 0.7 * i / (n - 1) : 0.4, 0, 1, 2);
    var k = 'clamp(0,calc((var(--p,1) - ' + on + ')*14),1)';
    out += '<div style="position:relative;display:flex;align-items:center;gap:10px;padding:12px 12px;border-radius:10px;border:1px solid ' + _moV('line', '#e5e9f0') + ';background:' + _moV('card', '#ffffff') + ';">'
      + '<span style="width:30px;height:30px;border-radius:8px;flex:none;background:rgba(' + accRgb + ',0.14);"></span>'
      + '<div style="min-width:0;flex:1;"><div style="font-size:13px;font-weight:600;color:' + _moV('ink', '#0f172a') + ';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + _esc(_moStr(c.title, 22)) + '</div>'
      + (c.sub ? '<div style="font-size:11px;color:' + _moV('mute', '#64748b') + ';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + _esc(_moStr(c.sub, 30)) + '</div>' : '') + '</div>'
      + '<span style="position:relative;width:34px;height:20px;border-radius:10px;flex:none;background:' + _moV('line', '#e5e9f0') + ';"><span style="position:absolute;inset:0;border-radius:10px;background:' + acc + ';opacity:' + k + ';"></span>'
      + '<span style="position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:#ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.3);transform:translateX(calc(' + k + '*14px));"></span></span></div>';
  }
  return '<div style="display:grid;grid-template-columns:repeat(' + cols + ',minmax(0,1fr));gap:10px;font-family:' + _MO_SANS + ';">' + out + '</div>';
};

_RENDERERS['demo_progress'] = function(b) {
  var dec = _ffInt(b.decimals, 0, 0, 3), to = _moNum(b.to, 100), pre = _moStr(b.prefix, 4), suf = _moStr(b.suffix, 12), acc = _moAcc(b);
  if (/^[A-Za-z]/.test(suf)) suf = ' ' + suf;
  return '<div style="font-family:' + _MO_SANS + ';padding:10px 12px;border-radius:10px;border:1px solid ' + _moV('line', '#e5e9f0') + ';background:' + _moV('card', '#ffffff') + ';">'
    + '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:8px;"><span style="font-weight:600;color:' + _moV('ink', '#0f172a') + ';">' + _esc(_moStr(b.label, 40)) + '</span>'
    + '<span style="color:' + _moV('mute', '#64748b') + ';font-variant-numeric:tabular-nums;">' + _moCount(to, dec, pre, suf) + '</span></div>'
    + '<div style="height:6px;border-radius:3px;background:' + _moV('soft', '#f4f6fa') + ';overflow:hidden;"><div style="height:6px;border-radius:3px;background:' + acc + ';width:calc(var(--p,1)*100%);"></div></div></div>';
};

_RENDERERS['demo_cursor'] = function(b) {
  var acc = _ffHex(b.accent, '#2563eb'), label = _moStr(b.label, 24);
  return '<div style="position:relative;width:0;height:0;font-family:' + _MO_SANS + ';">'
    + '<span style="position:absolute;left:-14px;top:-14px;width:28px;height:28px;border-radius:50%;border:2px solid ' + acc + ';opacity:calc(var(--p,0)*(1 - var(--p,0))*4);transform:scale(calc(0.5 + var(--p,0)*1.3));"></span>'
    + '<svg width="22" height="26" viewBox="0 0 22 26" style="position:absolute;left:0;top:0;filter:drop-shadow(0 2px 3px rgba(0,0,0,0.35));" aria-hidden="true"><path d="M1 1L1 20L6.2 15.4L9.6 23.4L13 22L9.7 14.2L16.6 14.2Z" fill="#ffffff" stroke="#0f172a" stroke-width="1.6" stroke-linejoin="round"/></svg>'
    + (label ? '<span style="position:absolute;left:16px;top:22px;white-space:nowrap;padding:3px 8px;border-radius:999px;font-size:11px;font-weight:600;color:#ffffff;background:' + acc + ';box-shadow:0 2px 6px rgba(0,0,0,0.25);">' + _esc(label) + '</span>' : '')
    + '</div>';
};

_RENDERERS['demo_caption'] = function(b) {
  var lines = Array.isArray(b.lines) ? b.lines.slice(0, 12) : [], tn = b.tone === 'light' ? 'light' : 'dark', acc = _ffHex(b.accent, '#22c55e');
  var bg = tn === 'light' ? '#ffffff' : '#0b1220', ink = tn === 'light' ? '#0f172a' : '#f1f5f9', pills = '', sr = [];
  for (var i = 0; i < lines.length; i++) {
    var l = lines[i] && typeof lines[i] === 'object' ? lines[i] : {text: lines[i]}, who = _moStr(l.who, 10) || 'agent', text = _moStr(l.text, 120);
    sr.push(who + ': ' + text);
    pills += '<div style="grid-area:1/1;display:flex;align-items:center;gap:10px;padding:8px 16px 8px 8px;border-radius:999px;background:' + bg + ';color:' + ink + ';font-size:15px;font-weight:500;white-space:nowrap;box-shadow:0 10px 30px -10px rgba(2,6,23,0.6);opacity:max(0,calc(1 - max(var(--s,0) - ' + i + ',' + i + ' - var(--s,0))));">'
      + '<span style="padding:3px 9px;border-radius:999px;font-size:10.5px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#05210f;background:' + acc + ';">' + _esc(who) + '</span>' + _esc(text) + '</div>';
  }
  return '<div style="display:grid;justify-items:center;font-family:' + _MO_SANS + ';" role="group" aria-label="Captions">' + pills
    + '<span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;">' + _esc(sr.join(' ')) + '</span></div>';
};

_RENDERERS['demo_orb'] = function(b) {
  var size = _ffInt(b.size, 160, 40, 400), acc = _ffHex(b.accent, '#38bdf8'), rgb = _ffRgb(acc), bars = _ffInt(b.bars, 0, 0, 9), label = _moStr(b.label, 30), wv = '';
  var weights = [0.7, 1, 0.55, 0.9, 0.4, 0.8, 0.6, 1, 0.5];
  for (var i = 0; i < bars; i++) {
    wv += '<span style="width:3px;height:14px;border-radius:2px;background:' + acc + ';transform:scaleY(calc(0.25 + var(--p,0)*' + weights[i] + '*0.75));"></span>';
  }
  return '<div style="display:flex;flex-direction:column;align-items:center;gap:10px;font-family:' + _MO_SANS + ';">'
    + '<div style="position:relative;width:' + size + 'px;height:' + size + 'px;">'
    + '<span style="position:absolute;inset:-40%;border-radius:50%;background:radial-gradient(circle,rgba(' + rgb + ',0.55) 0%,rgba(' + rgb + ',0) 62%);opacity:calc(0.45 + var(--p,0)*0.55);transform:scale(calc(0.9 + var(--p,0)*0.25));"></span>'
    + '<span style="position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle at 35% 30%,#ffffff 0%,rgba(' + rgb + ',0.95) 38%,rgba(' + rgb + ',0.55) 100%);transform:scale(calc(1 + var(--p,0)*0.16));"></span></div>'
    + (bars ? '<div style="display:flex;gap:3px;align-items:center;height:16px;">' + wv + '</div>' : '')
    + (label ? '<div style="font-size:11.5px;color:' + _moV('mute', '#94a3b8') + ';font-weight:600;">' + _esc(label) + '</div>' : '') + '</div>';
};

_RENDERERS['demo_panel'] = function(b) {
  var tn = b.tone === 'dark' ? 'dark' : 'light', c = _moTone(tn), acc = _ffHex(b.accent, ''), rows = Array.isArray(b.rows) ? b.rows.slice(0, 8) : [], out = '';
  var vars = '--dw-bg:' + c.bg + ';--dw-ink:' + c.ink + ';--dw-mute:' + c.mute + ';--dw-line:' + c.line + ';--dw-soft:' + c.soft + ';--dw-card:' + c.card + ';' + (acc ? '--dw-acc:' + acc + ';--dw-accrgb:' + _ffRgb(acc) + ';' : '');
  for (var i = 0; i < rows.length; i++) {
    var r = rows[i] && typeof rows[i] === 'object' ? rows[i] : {label: rows[i]};
    out += '<div style="display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-top:1px solid ' + c.line + ';font-size:12px;"><span style="color:' + c.mute + ';">' + _esc(_moStr(r.label, 28)) + '</span><span style="font-weight:600;color:' + c.ink + ';text-align:right;">' + _esc(_moStr(r.value, 28)) + '</span></div>';
  }
  var av = _moStr(b.avatar, 3), badge = _moStr(b.badge, 14), title = _moStr(b.title, 40), sub = _moStr(b.sub, 50);
  return '<div style="' + vars + 'box-sizing:border-box;width:100%;height:100%;padding:14px 16px;border-radius:12px;background:' + c.card + ';color:' + c.ink + ';border:1px solid ' + c.line + ';font-family:' + _MO_SANS + ';box-shadow:0 18px 40px -22px rgba(2,6,23,0.45);">'
    + '<div style="display:flex;align-items:center;gap:10px;' + (rows.length ? 'margin-bottom:8px;' : '') + '">'
    + (av ? '<span style="width:34px;height:34px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;background:' + c.soft + ';color:' + c.ink + ';">' + _esc(av) + '</span>' : '')
    + '<div style="min-width:0;flex:1;"><div style="font-size:13px;font-weight:700;">' + _esc(title) + '</div>' + (sub ? '<div style="font-size:11px;color:' + c.mute + ';">' + _esc(sub) + '</div>' : '') + '</div>'
    + (badge ? '<span style="padding:3px 8px;border-radius:999px;font-size:10px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;background:' + c.soft + ';color:' + c.mute + ';">' + _esc(badge) + '</span>' : '') + '</div>'
    + out + '</div>';
};

// ─── motion_timeline ─────────────────────────────────────────────────────────
var _MO_ASPECT = {'16:9': [1280, 720], '4:3': [1200, 900], '1:1': [1000, 1000], '9:16': [720, 1280]};
var _MO_PROPS = {x: [-200, 300], y: [-200, 300], opacity: [0, 1], scale: [0, 6], rotate: [-360, 360], rx: [-80, 80], ry: [-80, 80], blur: [0, 40], clip: [0, 1], p: [-0.5, 1.5], step: [0, 40], cs: [0, 9]};
var _MO_PROP_ORDER = ['x', 'y', 'opacity', 'scale', 'rotate', 'rx', 'ry', 'blur', 'clip', 'p', 'step', 'cs'];
var _MO_CAM = {x: [-100, 200], y: [-100, 200], zoom: [0.25, 6], rx: [-80, 80], ry: [-80, 80], rz: [-180, 180], z: [-1500, 1500]};
var _MO_CAM_ORDER = ['x', 'y', 'zoom', 'rx', 'ry', 'rz', 'z'];
var _MO_ORIGIN = {c: '50% 50%', tl: '0 0', t: '50% 0', b: '50% 100%', l: '0 50%', r: '100% 50%'};

var _MO_TIMELINE_JS =
  '(function(){' +
  'var C=%%CFG%%;var root=document.getElementById("mt-%%UID%%");if(!root)return;' +
  'var vp=root.querySelector(".mt-vp"),st=root.querySelector(".mt-st"),cam=root.querySelector(".mt-cam"),btn=root.querySelector(".mt-play"),rng=root.querySelector(".mt-rng"),tm=root.querySelector(".mt-tm");' +
  'var RM=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;' +
  'function bez(a,b,t){var u=1-t;return 3*u*u*t*a+3*u*t*t*b+t*t*t;}' +
  'function ez(e,u){if(u<=0)return 0;if(u>=1)return 1;if(!e)return u;if(e===1)return 0;var lo=0,hi=1,t=u;for(var i=0;i<28;i++){t=(lo+hi)/2;if(bez(e[0],e[2],t)<u)lo=t;else hi=t;}return bez(e[1],e[3],t);}' +
  'function at(ks,t){var n=ks.length;if(t<=ks[0][0])return ks[0][1];if(t>=ks[n-1][0])return ks[n-1][1];for(var i=1;i<n;i++){if(t<=ks[i][0]){var a=ks[i-1],b=ks[i];return a[1]+(b[1]-a[1])*ez(b[2],(t-a[0])/(b[0]-a[0]));}}return ks[n-1][1];}' +
  'function fm(v,d,p,s){var neg=v<0;v=Math.abs(v);var m=Math.pow(10,d),k=Math.floor(v*m+0.5),ip=Math.floor(k/m),fp=""+(k%m);while(fp.length<d)fp="0"+fp;var g="",ds=""+ip;for(var i=ds.length;i>0;i-=3){g=ds.slice(Math.max(0,i-3),i)+(g?",":"")+g;}return (neg&&k>0?"-":"")+p+g+(d>0?"."+fp:"")+s;}' +
  'var els={},nl=root.querySelectorAll("[data-mt-id]");' +
  'for(var i=0;i<nl.length;i++){var el=nl[i],x0=parseFloat(el.getAttribute("data-mt-x")),y0=parseFloat(el.getAttribute("data-mt-y"));els[el.getAttribute("data-mt-id")]={e:el,x0:isNaN(x0)?0:x0,y0:isNaN(y0)?0:y0,nums:el.querySelectorAll("[data-mt-num]")};}' +
  'var LZ={};function lz(id,cl){var c=document.getElementById("mlz%%UID%%-"+id);if(!c)return "";var tx=c.querySelector("text");if(!tx)return "";if(!LZ[id])LZ[id]=lzo(tx);var o=LZ[id],k=0.9*Math.pow(90,cl*cl*cl);tx.setAttribute("transform","translate("+o[0].toFixed(1)+" "+o[1].toFixed(1)+") scale("+k.toFixed(4)+") translate("+(-o[0]).toFixed(1)+" "+(-o[1]).toFixed(1)+")");return "url(#mlz%%UID%%-"+id+")";}function lzo(tx){var q=4,w=Math.ceil(C.W/q),h=Math.ceil(C.H/q),cv=document.createElement("canvas");cv.width=w;cv.height=h;var x=cv.getContext("2d");if(!x)return[C.W/2,C.H/2];x.font=(tx.getAttribute("font-weight")||"900")+" "+(parseFloat(tx.getAttribute("font-size"))/q)+"px "+tx.getAttribute("font-family");x.textAlign="center";x.textBaseline="middle";x.fillText(tx.textContent,w/2,h/2);var d=x.getImageData(0,0,w,h).data,best=null,bd=1e18,yy,xx,a,b2,ok;for(yy=3;yy<h-3;yy++)for(xx=3;xx<w-3;xx++){if(d[(yy*w+xx)*4+3]<200)continue;ok=true;for(a=-3;a<=3&&ok;a++)for(b2=-3;b2<=3;b2++)if(d[((yy+a)*w+xx+b2)*4+3]<200){ok=false;break;}if(!ok)continue;var dd=(xx-w/2)*(xx-w/2)+(yy-h/2)*(yy-h/2);if(dd<bd){bd=dd;best=[xx*q+q/2,yy*q+q/2];}}return best||[C.W/2,C.H/2];}if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){LZ={};});function ap(g,t){var o=els[g.i];if(!o)return;var v={};for(var k in g.p)v[k]=at(g.p[k],t);var e=o.e,tr="";' +
  'if(v.x!==undefined||v.y!==undefined){tr+="translate("+((v.x===undefined?0:v.x-o.x0)*C.W/100).toFixed(2)+"px,"+((v.y===undefined?0:v.y-o.y0)*C.H/100).toFixed(2)+"px) ";}' +
  'if(v.rx!==undefined)tr+="rotateX("+v.rx.toFixed(2)+"deg) ";if(v.ry!==undefined)tr+="rotateY("+v.ry.toFixed(2)+"deg) ";if(v.rotate!==undefined)tr+="rotate("+v.rotate.toFixed(2)+"deg) ";if(v.scale!==undefined)tr+="scale("+Math.max(0,v.scale).toFixed(4)+")";' +
  'if(tr)e.style.transform=tr;' +
  'if(v.opacity!==undefined)e.style.opacity=Math.max(0,Math.min(1,v.opacity)).toFixed(3);' +
  'if(v.blur!==undefined)e.style.filter=v.blur>0.05?"blur("+Math.min(40,v.blur).toFixed(2)+"px)":"";' +
  'if(v.clip!==undefined){var cl=Math.max(0,Math.min(1,v.clip)),cs=v.cs===undefined?0:Math.round(v.cs),cpp="",mk="";if(cl<0.999||cs===5){if(cs===1)cpp="circle("+(cl*75).toFixed(2)+"% at 50% 50%)";else if(cs===2)mk="conic-gradient(#000 "+(cl*360).toFixed(2)+"deg,transparent 0)";else if(cs===3)mk="repeating-linear-gradient(90deg,#000 0,#000 "+(cl*10).toFixed(3)+"%,transparent "+(cl*10).toFixed(3)+"%,transparent 10%)";else if(cs===4)cpp="polygon(0 0,"+(cl*140).toFixed(2)+"% 0,"+(cl*140-40).toFixed(2)+"% 100%,0 100%)";else if(cs===5){var e5=cl*170-15;cpp="polygon("+(e5-14).toFixed(2)+"% 0,"+(e5+8).toFixed(2)+"% 0,"+(e5-32).toFixed(2)+"% 100%,"+(e5-54).toFixed(2)+"% 100%)";}else if(cs===6)cpp="polygon(0 0,"+(cl*170-15).toFixed(2)+"% 0,"+(cl*170-55).toFixed(2)+"% 100%,0 100%)";else if(cs===9)cpp=lz(g.i,cl);else cpp="inset(0 "+((1-cl)*100).toFixed(2)+"% 0 0)";}e.style.clipPath=cpp;e.style.webkitMaskImage=mk;e.style.maskImage=mk;}' +
  'if(v.p!==undefined){e.style.setProperty("--p",v.p.toFixed(4));for(var j=0;j<o.nums.length;j++){var q=o.nums[j],a=parseFloat(q.getAttribute("data-from")),b=parseFloat(q.getAttribute("data-to"));q.textContent=fm(a+(b-a)*v.p,parseInt(q.getAttribute("data-dec"),10)||0,q.getAttribute("data-pre")||"",q.getAttribute("data-suf")||"");}}' +
  'if(v.step!==undefined)e.style.setProperty("--s",v.step.toFixed(4));}' +
  'function cp(t){if(!C.cam||!cam)return;var c=C.cam;function g(k,d){return c[k]?at(c[k],t):d;}' +
  'cam.style.transform="translate("+(C.W/2)+"px,"+(C.H/2)+"px) "+(c.z?"translateZ("+g("z",0).toFixed(2)+"px) ":"")+"scale("+g("zoom",1).toFixed(4)+") rotateX("+g("rx",0).toFixed(2)+"deg) rotateY("+g("ry",0).toFixed(2)+"deg) rotate("+g("rz",0).toFixed(2)+"deg) translate("+(-g("x",50)*C.W/100).toFixed(2)+"px,"+(-g("y",50)*C.H/100).toFixed(2)+"px)";}' +
  'function fit(){var k=vp.clientWidth/C.W;st.style.transform="scale("+k.toFixed(5)+")";st.style.visibility="visible";}' +
  'fit();if(window.ResizeObserver){new ResizeObserver(fit).observe(vp);}else{window.addEventListener("resize",fit);}' +
  'var t=0,pl=false,last=0,raf=0,manual=false;' +
  'function lab(x){var s=Math.floor(x),m=Math.floor(s/60);s=s%60;return m+":"+(s<10?"0":"")+s;}' +
  'function seek(x){t=Math.max(0,Math.min(C.dur,x));for(var i=0;i<C.tg.length;i++)ap(C.tg[i],t);cp(t);if(rng)rng.value=Math.floor(t/C.dur*1000+0.5);if(tm)tm.textContent=lab(t)+" / "+lab(C.dur);}' +
  'function tick(ts){if(!pl)return;var nt=t+(ts-last)/1000;last=ts;if(nt>=C.dur){if(C.loop){nt=nt%C.dur;}else{nt=C.dur;pause();}}seek(nt);if(pl)raf=requestAnimationFrame(tick);}' +
  'function play(){if(pl)return;if(t>=C.dur)t=0;pl=true;last=performance.now();root.setAttribute("data-pl","1");raf=requestAnimationFrame(tick);}' +
  'function pause(){pl=false;cancelAnimationFrame(raf);root.setAttribute("data-pl","0");}' +
  'if(btn)btn.addEventListener("click",function(){if(pl){manual=true;pause();}else{manual=false;play();}});' +
  'if(rng)rng.addEventListener("input",function(){manual=true;pause();seek(parseFloat(rng.value)/1000*C.dur);});' +
  'var hm=/t=([0-9.]+)/.exec(location.hash||""),want=C.auto&&!RM&&!hm;' +
  'seek(hm?parseFloat(hm[1]):(RM||!C.auto)?C.poster:0);' +
  'window.__a2uiMotion=window.__a2uiMotion||{};window.__a2uiMotion["%%UID%%"]={seek:seek,play:play,pause:pause,dur:C.dur};' +
  'if(want){if(window.IntersectionObserver){new IntersectionObserver(function(a){if(a[0].isIntersecting){if(!manual)play();}else if(pl){pause();}},{threshold:0.25}).observe(root);}else{play();}}' +
  '})();';

// Keys -> per-property tracks. Every number goes through _ffNum so both renderers
// spell it identically; anything that does not validate is counted, never silent.
function _moTrackJs(keys, ranges, order, dur, bpm, defEase, st) {
  var list = [], i, p;
  for (i = 0; i < keys.length; i++) {
    var k = keys[i];
    if (!k || typeof k !== 'object') { st.dropped++; continue; }
    var t = null;
    if (typeof k.t === 'number' && isFinite(k.t)) t = k.t;
    else if (typeof k.beat === 'number' && isFinite(k.beat) && bpm) t = k.beat * 60 / bpm;
    if (t === null) { st.dropped++; continue; }
    list.push({t: Math.max(0, Math.min(dur, t)), k: k, i: i});
  }
  list.sort(function(a, c) { return a.t - c.t || a.i - c.i; });
  var parts = [];
  for (p = 0; p < order.length; p++) {
    var prop = order[p], rg = ranges[prop], pts = [];
    for (i = 0; i < list.length; i++) {
      var v = list[i].k[prop];
      if (typeof v !== 'number' || !isFinite(v)) continue;
      pts.push('[' + _ffNum(list[i].t, 0, 0, 100000, 3) + ',' + _ffNum(v, 0, rg[0], rg[1], 3) + ',' + _moEaseJs(list[i].k.ease, defEase) + ']');
    }
    if (pts.length) { parts.push(prop + ':[' + pts.join(',') + ']'); st.keys += pts.length; }
  }
  return parts.join(',');
}

// One child at its `place` (percent of the parent box: a timeline's stage or a motion_layer). null = dropped (counted in st).
function _moPlaced(blk, seen, ids, st) {
  if (!blk || typeof blk !== 'object') { st.dropped++; return null; }
  var type = blk.component || blk.type, fn = _RENDERERS[type];
  if (!fn || type === 'motion_timeline') { st.dropped++; return null; }
  var html;
  try { html = fn(blk); } catch (err) { st.dropped++; return null; }
  var id = _moId(blk.id);
  if (id && seen[id]) { id = ''; st.dropped++; }
  if (id) { seen[id] = 1; ids[id] = 1; }
  var pl = blk.place && typeof blk.place === 'object' ? blk.place : {};
  var px = _ffNum(pl.x, 0, -100, 200, 2), py = _ffNum(pl.y, 0, -100, 200, 2), sz = '';
  // a layer with no size fills its parent: its own children are placed in percent of it
  if (typeof pl.w === 'number') sz += 'width:' + _ffNum(pl.w, 100, 0, 300, 2) + '%;'; else if (type === 'motion_layer') sz += 'width:100%;';
  if (typeof pl.h === 'number') sz += 'height:' + _ffNum(pl.h, 100, 0, 300, 2) + '%;'; else if (type === 'motion_layer') sz += 'height:100%;';
  return '<div class="mt-el"' + (id ? ' data-mt-id="' + id + '" data-mt-x="' + px + '" data-mt-y="' + py + '"' : '') + ' style="position:absolute;left:' + px + '%;top:' + py + '%;' + sz + 'z-index:' + _ffInt(pl.z, 1, 0, 99) + ';transform-origin:' + _ffPick(pl.origin, _MO_ORIGIN, 'c') + ';">' + html + '</div>';
}
// ─── match cut (2026-10-02): an element flies from its box in one scene to its box in another ─────────────────────────────
// `morphs: [{from, to, t|beat, dur?, ease?}]`. Every child is placed in percent, so the server knows both boxes (stage percent,
// through at most one motion_layer) and writes the flight as ordinary tracks on a ghost copy of `from`: the ghost is drawn with its
// origin at its top-left, so translate + scale land it exactly on the `to` box. `from` hides when the flight starts and `to` appears
// when it ends (the morph owns their opacity). Both need a numeric place.w; anything else is dropped and counted.
// place.depth 0-1 pushes a top-level block back in 3D; the compensating scale keeps it identical while the camera is at z 0.
function _moDepth(blk, wrap) {
  var pl = blk.place && typeof blk.place === 'object' ? blk.place : {}, dv = pl.depth;
  if (typeof dv !== 'number' || !isFinite(dv) || !(dv > 0)) return wrap;
  var d = parseFloat(_ffNum(dv, 0, 0, 1, 2)) * 1200;
  if (d <= 0) return wrap;
  return '<div style="position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;transform-style:preserve-3d;transform-origin:50% 50%;transform:translateZ(-' + _ffNum(d, 0, 0, 1200, 1) + 'px) scale(' + _ffNum((1800 + d) / 1800, 1, 1, 2, 4) + ');">'
    + wrap.replace('style="position:absolute;', 'style="pointer-events:auto;position:absolute;') + '</div>';
}
function _moBoxes(blocks) {
  var out = {}, i, j;
  function num(v, d, lo, hi) { return parseFloat(_ffNum(v, d, lo, hi, 2)); }
  for (i = 0; i < blocks.length; i++) {
    var b = blocks[i];
    if (!b || typeof b !== 'object' || b.layer === 'hud') continue;
    var pl = b.place && typeof b.place === 'object' ? b.place : {}, id = _moId(b.id);
    var bx = num(pl.x, 0, -100, 200), by = num(pl.y, 0, -100, 200);
    if (id && typeof pl.w === 'number' && !out[id]) out[id] = {x: bx, y: by, w: num(pl.w, 100, 0, 300), b: b};
    if ((b.component || b.type) === 'motion_layer' && Array.isArray(b.blocks)) {
      var lw = typeof pl.w === 'number' ? num(pl.w, 100, 0, 300) : 100, lh = typeof pl.h === 'number' ? num(pl.h, 100, 0, 300) : 100;
      for (j = 0; j < b.blocks.length && j < 24; j++) {
        var c = b.blocks[j];
        if (!c || typeof c !== 'object') continue;
        var cp = c.place && typeof c.place === 'object' ? c.place : {}, cid = _moId(c.id);
        if (!cid || typeof cp.w !== 'number' || out[cid]) continue;
        out[cid] = {x: bx + num(cp.x, 0, -100, 200) * lw / 100, y: by + num(cp.y, 0, -100, 200) * lh / 100, w: num(cp.w, 100, 0, 300) * lw / 100, b: c};
      }
    }
  }
  return out;
}
function _moMorphs(b, blocks, ids, bpm, dur, st) {
  var src = Array.isArray(b.morphs) ? b.morphs : [], res = {html: '', tg: []}, i, own = Object.prototype.hasOwnProperty;
  if (!src.length) return res;
  if (src.length > 6) { st.dropped += src.length - 6; src = src.slice(0, 6); }
  var box = _moBoxes(blocks);
  for (i = 0; i < src.length; i++) {
    var m = src[i], fid = m && typeof m === 'object' ? _moId(m.from) : '', tid = m && typeof m === 'object' ? _moId(m.to) : '', gid = 'mcut' + i;
    var t = fid && tid && fid !== tid && box[fid] && box[tid] && ids[fid] && ids[tid] && !ids[gid] ? _moAt(m, bpm, dur) : null;
    if (t === null) { st.dropped++; continue; }
    var d = parseFloat(_ffNum(m.dur, 0.8, 0.1, 4, 2)), ez = (typeof m.ease === 'string' && m.ease !== 'hold' && own.call(_MO_EASE, m.ease)) ? m.ease : 'quart-in-out';
    var A = box[fid], Z = box[tid], sc = A.w > 0 ? Z.w / A.w : 1, t1 = Math.min(dur, t + d);
    var fx = _ffNum(A.x, 0, -100, 200, 2), fy = _ffNum(A.y, 0, -100, 200, 2), copy = {}, k;
    for (k in A.b) if (own.call(A.b, k) && k !== 'id' && k !== 'place') copy[k] = A.b[k];
    res.html += '<div class="mt-el" data-mt-id="' + gid + '" data-mt-x="' + fx + '" data-mt-y="' + fy + '" aria-hidden="true" style="position:absolute;left:' + fx + '%;top:' + fy + '%;width:' + _ffNum(A.w, 100, 0, 300, 2) + '%;z-index:60;transform-origin:0 0;opacity:0;pointer-events:none;">' + _moRender(copy) + '</div>';
    var x0 = parseFloat(fx), y0 = parseFloat(fy);
    var gk = [{t: 0, opacity: 0, x: x0, y: y0, scale: 1}, {t: t, opacity: 1, x: x0, y: y0, scale: 1, ease: 'hold'}, {t: t1, opacity: 1, x: Z.x, y: Z.y, scale: sc, ease: ez}, {t: Math.min(dur, t1 + 0.02), opacity: 0, ease: 'hold'}];
    var gj = _moTrackJs(gk, _MO_PROPS, _MO_PROP_ORDER, dur, bpm, 'standard', st), fj = _moTrackJs([{t: 0, opacity: 1}, {t: t, opacity: 0, ease: 'hold'}], _MO_PROPS, _MO_PROP_ORDER, dur, bpm, 'standard', st);
    var tj = _moTrackJs([{t: 0, opacity: 0}, {t: t1, opacity: 1, ease: 'hold'}], _MO_PROPS, _MO_PROP_ORDER, dur, bpm, 'standard', st);
    res.tg.push('{i:"' + gid + '",p:{' + gj + '}}', '{i:"' + fid + '",p:{' + fj + '}}', '{i:"' + tid + '",p:{' + tj + '}}');
  }
  return res;
}
var _moTlDepth = 0;
function _moTimeline(b) {
  var uid = Math.random().toString(36).substr(2, 6), th = _ffTheme(b), acc = _ffHex(b.accent, '#38bdf8');
  var asp = _ffPick(b.aspect, _MO_ASPECT, '16:9'), W = asp[0], H = asp[1];
  var dur = _ffNum(b.duration, 12, 2, 120, 2), durN = parseFloat(dur), bpm = _ffInt(b.bpm, 0, 0, 240);
  var defEase = (typeof b.ease === 'string' && b.ease !== 'hold' && Object.prototype.hasOwnProperty.call(_MO_EASE, b.ease)) ? b.ease : 'standard';
  var loop = b.loop === false ? 'false' : 'true', auto = b.autoplay === false ? 'false' : 'true', ctl = b.controls !== false;
  var poster = _ffNum(b.poster, durN * 0.6, 0, durN, 2);
  var bg = _ffHex(b.background, ''), backdrop = b.backdrop === 'flat' ? 'flat' : (b.backdrop === 'grid' ? 'grid' : 'glow');
  var stBg = bg || th.bg;
  var title = _moStr(b.title, 80) || 'Motion sequence';
  var st = {dropped: 0, keys: 0}, seen = {}, ids = {}, world = '', hud = '', blocks = Array.isArray(b.blocks) ? b.blocks : [];
  if (blocks.length > 24) { st.dropped += blocks.length - 24; blocks = blocks.slice(0, 24); }
  for (var i = 0; i < blocks.length; i++) {
    var blk = blocks[i], wrap = _moPlaced(blk, seen, ids, st);
    if (wrap === null) continue;
    if (blk.layer === 'hud') hud += wrap; else world += _moDepth(blk, wrap);
  }
  // Targets may be nested (a page inside a window): collect every data-mt-id the
  // children actually emitted. Agent text is _esc'd, so it cannot forge one.
  var found = (world + hud).match(/data-mt-id="[a-z][a-z0-9_-]{0,31}"/g) || [];
  for (var f = 0; f < found.length; f++) ids[found[f].slice(12, -1)] = 1;
  var tg = [], tracks = Array.isArray(b.tracks) ? b.tracks : [];
  st.W = W; st.H = H; st.uid = uid;
  tg = tg.concat(_moStitch(b, ids, bpm, durN, st)); // scene hand-overs first, so a track you write on the same layer wins
  if (st.rib) world += st.rib;
  if (st.lz) world += st.lz;
  if (tracks.length > 40) { st.dropped += tracks.length - 40; tracks = tracks.slice(0, 40); }
  for (var j = 0; j < tracks.length; j++) {
    var tr = tracks[j], tid = tr && typeof tr === 'object' ? _moId(tr.target) : '';
    if (!tid || !ids[tid] || !Array.isArray(tr.keys)) { st.dropped++; continue; }
    var keys = tr.keys;
    if (keys.length > 48) { st.dropped += keys.length - 48; keys = keys.slice(0, 48); }
    var pjs = _moTrackJs(keys, _MO_PROPS, _MO_PROP_ORDER, durN, bpm, defEase, st);
    if (pjs) tg.push('{i:"' + tid + '",p:{' + pjs + '}}');
  }
  var mc = _moMorphs(b, blocks, ids, bpm, durN, st); // after your tracks: the morph owns from/to opacity during its flight
  world += mc.html; tg = tg.concat(mc.tg);
  var camJs = 'null', cm = b.camera && typeof b.camera === 'object' && Array.isArray(b.camera.keys) ? b.camera.keys.slice(0, 48) : null;
  if (cm) { var cj = _moTrackJs(cm, _MO_CAM, _MO_CAM_ORDER, durN, bpm, defEase, st); if (cj) camJs = '{' + cj + '}'; }
  var cfg = '{W:' + W + ',H:' + H + ',dur:' + dur + ',poster:' + poster + ',loop:' + loop + ',auto:' + auto + ',tg:[' + tg.join(',') + '],cam:' + camJs + '}';
  var glow = backdrop === 'glow' ? 'background-image:radial-gradient(ellipse at 50% 0%,rgba(' + _ffRgb(acc) + ',0.22) 0%,rgba(' + _ffRgb(acc) + ',0) 62%);'
    : (backdrop === 'grid' ? 'background-image:linear-gradient(rgba(' + _ffRgb(th.ink) + ',0.06) 1px,transparent 1px),linear-gradient(90deg,rgba(' + _ffRgb(th.ink) + ',0.06) 1px,transparent 1px);background-size:48px 48px;' : '');
  var icon = '<svg class="mt-ic-play" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 1.5L12 7L3 12.5Z" fill="currentColor"/></svg><svg class="mt-ic-pause" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><rect x="2.5" y="1.5" width="3.2" height="11" rx="1" fill="currentColor"/><rect x="8.3" y="1.5" width="3.2" height="11" rx="1" fill="currentColor"/></svg>';
  var controls = ctl
    ? '<div style="display:flex;align-items:center;gap:12px;padding:10px 4px 0;color:' + th.ink + ';">'
      + '<button type="button" class="mt-play" aria-label="Play or pause" style="width:32px;height:32px;border-radius:50%;border:1px solid ' + th.line + ';background:' + th.soft + ';color:' + th.ink + ';display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;flex:none;">' + icon + '</button>'
      + '<input type="range" class="mt-rng" min="0" max="1000" value="0" aria-label="Timeline position" style="flex:1;min-width:0;accent-color:' + acc + ';">'
      + '<span class="mt-tm" style="font-family:' + _CV_VOICES.mono + ';font-size:0.72rem;color:' + th.mute + ';min-width:64px;text-align:right;">0:00</span></div>'
    : '';
  var note = st.dropped ? '<!-- a2ui: motion_timeline ignored ' + st.dropped + ' invalid or over-limit item(s) -->' : '';
  return '<div id="mt-' + uid + '" class="mt-root" data-pl="0" role="group" aria-label="' + _esc(title) + '" style="margin:1rem 0;font-family:' + _MO_SANS + ';">'
    + '<style>.mt-root[data-pl="1"] .mt-ic-play{display:none}.mt-root[data-pl="0"] .mt-ic-pause{display:none}.mt-root button:focus-visible{outline:2px solid ' + acc + ';outline-offset:2px}</style>'
    + '<div class="mt-vp" style="position:relative;width:100%;aspect-ratio:' + W + '/' + H + ';overflow:hidden;border-radius:16px;background:' + stBg + ';border:1px solid ' + th.line + ';">'
    + '<div class="mt-st" style="position:absolute;left:0;top:0;width:' + W + 'px;height:' + H + 'px;transform-origin:0 0;visibility:hidden;perspective:1800px;background-color:' + stBg + ';' + glow + '--mt-ink:' + th.ink + ';--mt-mute:' + th.mute + ';--mt-acc:' + acc + ';overflow:hidden;">'
    + '<div class="mt-cam" style="position:absolute;left:0;top:0;width:' + W + 'px;height:' + H + 'px;transform-origin:0 0;transform-style:preserve-3d;">' + world + '</div>'
    + '<div class="mt-hud" style="position:absolute;left:0;top:0;width:' + W + 'px;height:' + H + 'px;pointer-events:none;">' + hud + '</div></div></div>'
    + controls + note
    + '<script>' + _MO_TIMELINE_JS.replace(/%%UID%%/g, uid).replace(/%%CFG%%/g, function() { return cfg; }) + '<\/script></div>';
}
_RENDERERS['motion_timeline'] = function(b) {
  // A timeline inside a timeline would share ids and clocks: refuse, and say so.
  if (_moTlDepth > 0) return '<!-- a2ui: motion_timeline cannot nest inside another motion_timeline -->';
  _moTlDepth++;
  // A cinematic stage is full-bleed, not article text: break out of the host's
  // 860px asw-page reading column (same established pattern as atoms_airspace/atc).
  var out;
  try { out = _moTimeline(b); } finally { _moTlDepth--; }
  // Stage element wrappers sit above nested atoms and would swallow pointer/wheel events meant for
  // an embedded canvas (e.g. brick_build_3d's own drag-orbit and scroll-zoom). Let events pass through
  // the wrappers, and re-enable them on canvases so nested interactive atoms still receive them.
  // Dark stage all the way out: the host page background and any nested brick card otherwise
  // show as a white bleed around the cinematic frame.
  return '<style>html,body{background:#07111f!important}[style*="radial-gradient(120% 90%"]{background:#07111f!important;}'
    + '.asw-page{max-width:none!important;padding:0!important;margin:0!important;background:#07111f!important}'
    + '.mt-el{pointer-events:none}.mt-el canvas{pointer-events:auto}</style>' + out;
};

// ─── topic-free primitives (added after the first composition outside the SaaS demo) ──
// motion_layer groups children into a scene; motion_text, motion_shape and motion_counter draw type, forms and numbers
// from the stage theme (--mt-ink / --mt-acc / --mt-mute, set by motion_timeline) and move with --p like the demo kit.
// Standalone they render their FINAL state.
var _MO_REVEAL = {rise: 1, drop: 1, fade: 1, blur: 1, mask: 1, bar: 1, flap: 1};
var _MO_FLAP = 'ABCDEFGHJKLMNPRSTUVWXYZ0123456789';
var _MO_ALIGN = {start: 'left', middle: 'center', end: 'right'};
function _moInk(b, key, dflt) { var h = _ffHex(b[key], ''); return h || dflt; }

// A scene: children placed in percent of THIS layer, moved as one (opacity/x/scale/blur tracks on the layer id).
_RENDERERS['motion_layer'] = function(b) {
  var blocks = Array.isArray(b.blocks) ? b.blocks : [], st = {dropped: 0}, seen = {}, ids = {}, out = '';
  if (blocks.length > 24) { st.dropped += blocks.length - 24; blocks = blocks.slice(0, 24); }
  for (var i = 0; i < blocks.length; i++) { var w = _moPlaced(blocks[i], seen, ids, st); if (w !== null) out += w; }
  return '<div style="position:absolute;left:0;top:0;width:100%;height:100%;">' + out + '</div>'
    + (st.dropped ? '<!-- a2ui: motion_layer ignored ' + st.dropped + ' invalid or over-limit item(s) -->' : '');
};

// Rich text: *word* takes the accent colour, ** is a literal asterisk. Chars are {c, a} so a unit keeps its colour whatever it reveals by.
function _moChars(s) {
  var out = [], a = false, cs = Array.from(s), i;
  for (i = 0; i < cs.length; i++) {
    if (cs[i] === '*') { if (cs[i + 1] === '*') { out.push({c: '*', a: a}); i++; } else a = !a; continue; }
    out.push({c: cs[i], a: a});
  }
  return out;
}
function _moPlain(s) { var cs = _moChars(s), t = '', i; for (i = 0; i < cs.length; i++) t += cs[i].c; return t; }
function _moWords(chs) {
  var words = [], cur = [], i;
  for (i = 0; i < chs.length; i++) { if (chs[i].c === ' ') { if (cur.length) words.push(cur); cur = []; } else cur.push(chs[i]); }
  if (cur.length) words.push(cur);
  return words;
}
function _moRuns(chs, acc) {
  var html = '', i = 0, j, a, t;
  while (i < chs.length) {
    j = i; a = chs[i].a; t = '';
    while (j < chs.length && chs[j].a === a) { t += chs[j].c; j++; }
    t = _esc(t).replace(/\n/g, '<br>');
    html += a ? '<span style="color:' + acc + ';">' + t + '</span>' : t;
    i = j;
  }
  return html;
}
function _moSr(plain) { return '<span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;">' + _esc(plain) + '</span>'; }

// Kinetic type. Each unit (block, line, word or character) reveals in turn as --p goes 0..1.
_RENDERERS['motion_text'] = function(b) {
  var raw = (typeof b.text === 'string' ? b.text : '').split('\n'), lines = [], total = 0, i, j;
  for (i = 0; i < raw.length && lines.length < 4; i++) {
    var ln = raw[i].trim().slice(0, 60);
    if (!ln) continue;
    ln = ln.slice(0, Math.max(0, 160 - total)); total += ln.length;
    if (ln) lines.push(ln);
  }
  if (!lines.length) lines = ['Text'];
  var size = _ffInt(b.size, 64, 10, 400), weight = _ffPick(b.weight, _FF_WEIGHTS, 'bold'), font = _ffPick(b.font, _FF_FONTS, 'sans');
  var vf = (typeof b.font === 'string' && typeof _MO_VFONTS !== 'undefined' && Object.prototype.hasOwnProperty.call(_MO_VFONTS, b.font)) ? b.font : '', fvs = vf ? _moVfVary(vf, b.vary) : '', von = _moOwn(_MO_VARY_ON, b.vary_on, 'unit');
  if (vf) font = _MO_VFONTS[vf].stack;
  // Style flip (studio pack): every character is a two-faced card; a wave on the second dial turns it over to the matching character
  // of flip_text (default: the same text) in its own face, colour, weight and animated axes. Characters mode only.
  var flipOn = typeof b.flip_text === 'string' || typeof b.flip_font === 'string', flipFace = '', flipStack = '', flipFvs = '', flipChars = [];
  if (flipOn) {
    flipFace = (typeof b.flip_font === 'string' && typeof _MO_VFONTS !== 'undefined' && Object.prototype.hasOwnProperty.call(_MO_VFONTS, b.flip_font)) ? b.flip_font : '';
    flipStack = flipFace ? _MO_VFONTS[flipFace].stack : _ffPick(b.flip_font, _FF_FONTS, 'serif');
    flipFvs = flipFace ? _moVfVary(flipFace, b.flip_vary) : '';
    var flipSrc = typeof b.flip_text === 'string' ? b.flip_text.slice(0, 160) : lines.join(' '), fcs = Array.from(_moPlain(flipSrc)), fi;
    for (fi = 0; fi < fcs.length; fi++) if (fcs[fi] !== ' ' && fcs[fi] !== '\n') flipChars.push(fcs[fi]);
  }
  var flipColor = _moInk(b, 'flip_color', 'var(--mt-acc,#38bdf8)'), flipWeight = _ffPick(b.flip_weight, _FF_WEIGHTS, 'bold');
  var mode = (b.mode === 'block' || b.mode === 'words' || b.mode === 'chars') ? b.mode : 'lines';
  if (flipOn) mode = 'chars';
  var reveal = (typeof b.reveal === 'string' && Object.prototype.hasOwnProperty.call(_MO_REVEAL, b.reveal)) ? b.reveal : 'rise';
  var S = _ffInt(b.overlap, 3, 1, 8), track = _ffNum(b.tracking, -0.02, -0.1, 0.5, 3), lh = _ffNum(b.line_height, 1.05, 0.8, 2, 2);
  var color = _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), align = _ffPick(b.align, _MO_ALIGN, 'start'), upper = b.uppercase === true;
  var accent = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)');
  var bar = _moInk(b, 'bar', 'var(--mt-acc,#38bdf8)'), ext = _ffInt(b.extrude, 0, 0, 30), extc = _moInk(b, 'extrude_color', '#0b0b14'), shadow = '', si;
  var decor = _moOwn(_MO_DECOR, b.decor, ''), decorC = _moInk(b, 'decor_color', accent), kara = _moOwn(_MO_KARA, b.karaoke, ''), spl = _ffInt(b.split, 0, 0, 60), spA = _moInk(b, 'split_a', '#ff2d6f'), spB = _moInk(b, 'split_b', '#19d3ff');
  for (si = 1; si <= ext; si++) shadow += (si > 1 ? ',' : '') + (b.extrude_dir === 'down' ? '0' : si + 'px') + ' ' + si + 'px 0 ' + extc;
  var sd = 'calc(var(--s,0)*' + spl + 'px)', textShadow = [shadow, spl ? 'calc(-1*' + sd + ') 0 ' + spA + ',' + sd + ' 0 ' + spB : ''].filter(function(x) { return x; }).join(',');
  // units: [{c: chars, brk}] ; brk marks a line break BEFORE the unit
  var units = [];
  for (i = 0; i < lines.length; i++) {
    var chs = _moChars(lines[i]);
    if (mode === 'block' || mode === 'lines') { units.push({c: chs, brk: i > 0 && mode === 'block'}); continue; }
    var words = _moWords(chs);
    for (j = 0; j < words.length; j++) {
      if (mode === 'words') units.push({c: words[j], brk: i > 0 && j === 0, sp: j > 0});
      else units.push({c: words[j], brk: i > 0 && j === 0, sp: j > 0, chars: true});
    }
  }
  function joined(sep) {
    var all = [], x, y;
    for (x = 0; x < lines.length; x++) { if (x) all.push({c: sep, a: false}); var cc = _moChars(lines[x]); for (y = 0; y < cc.length; y++) all.push(cc[y]); }
    return all;
  }
  if (mode === 'block') units = [{c: joined('\n'), block: true}];
  var pr = Array.isArray(b.prism) ? b.prism : [], pw = [], prism = '', pk;
  for (pk = 0; pk < pr.length && pw.length < 4; pk++) { var pwd = _moStr(pr[pk], 14); if (pwd) pw.push(pwd); }
  if (pw.length >= 2) { // a turning 3D prism that cycles the words with the second dial (--s)
    var pf = pw.length === 2 ? [pw[0], pw[1], pw[0], pw[1]] : pw, pn = pf.length, pz = pn === 3 ? '0.289' : '0.5', pm = 0, pface = '', pj;
    for (pj = 0; pj < pw.length; pj++) pm = Math.max(pm, Array.from(pw[pj]).length);
    for (pj = 0; pj < pn; pj++) pface += '<span aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:1em;line-height:1;backface-visibility:hidden;-webkit-backface-visibility:hidden;transform:rotateX(' + Math.floor(360 * pj / pn + 0.5) + 'deg) translateZ(' + pz + 'em);">' + _esc(pf[pj]) + '</span>';
    prism = '<span style="display:inline-block;position:relative;vertical-align:bottom;margin-left:0.3em;width:' + _ffNum(pm * 0.62, 1, 1, 12, 2) + 'em;height:1em;line-height:1;perspective:12em;color:' + accent + ';opacity:clamp(0,calc(var(--p,1)*6),1);">'
      + _moSr(pw.join(', ')) + '<span aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:100%;transform-style:preserve-3d;transform:translateZ(-' + pz + 'em) rotateX(calc(var(--s,0)*-360deg));">' + pface + '</span></span>';
  }
  var N = 0, k;
  for (k = 0; k < units.length; k++) N += units[k].chars ? units[k].c.length : 1;
  if (N > 120) { units = [{c: joined(' '), block: true}]; N = 1; mode = 'block'; }
  var idx = 0;
  function uvar(n) { return '--u:clamp(0,calc((var(--p,1)*' + (N + S) + ' - ' + n + ')/' + S + '),1);'; }
  function wrapUnit(inner, n, blockish) {
    var h = wrapUnit0(inner, n, blockish);
    if (fvs) { // studio face axes, driven per unit by its reveal, by the second dial, or by a wave travelling along the second dial
      var vv = von === 'dial' ? 'clamp(0,var(--s,1),1)' : 'clamp(0,calc((var(' + (von === 'wave' ? '--s' : '--p') + ',1)*' + (N + S) + ' - ' + n + ')/' + S + '),1)';
      h = '<span style="--v:' + vv + ';' + (blockish ? 'display:block;' : 'display:inline-block;') + 'font-variation-settings:' + fvs + ';">' + h + '</span>';
    }
    if (flipOn) { // a two-faced card per character: the front turns away as the back turns in, in a wave along the second dial
      var bc = n < flipChars.length ? flipChars[n] : '\u00a0', face = 'grid-area:1/1;justify-self:center;display:inline-block;backface-visibility:hidden;-webkit-backface-visibility:hidden;';
      h = '<span style="--f:clamp(0,calc((var(--s,0)*' + (N + S) + ' - ' + n + ')/' + S + '),1);--v:var(--f);display:inline-grid;perspective:3.5em;vertical-align:bottom;">'
        + '<span style="' + face + 'transform:rotateX(calc(var(--f)*-180deg));">' + h + '</span>'
        + '<span aria-hidden="true" style="' + face + 'transform:rotateX(calc(180deg - var(--f)*180deg));font-family:' + flipStack + ';font-weight:' + flipWeight + ';color:' + flipColor + ';' + (flipFvs ? 'font-variation-settings:' + flipFvs + ';' : '') + '">' + _esc(bc) + '</span></span>';
    }
    if (kara) {
      h = '<span style="--k:clamp(0,calc(1.5 - abs(var(--s,1)*' + N + ' - ' + (n + 0.5) + ')*3),1);display:inline-block;padding:0.04em 0.24em;border-radius:0.3em;color:color-mix(in srgb,' + color + ' calc((1 - var(--k))*100%),' + (kara === 'pill' ? '#0b0712' : accent) + ');'
        + (kara === 'pill' ? 'background:color-mix(in srgb,' + accent + ' calc(var(--k)*100%),transparent);' : '') + '">' + h + '</span>';
    }
    if (decor) {
      var dv = 'clamp(0,calc((var(--s,1)*' + (N + S) + ' - ' + n + ')/' + S + '),1)', bar2;
      if (decor === 'strike') bar2 = 'left:-2%;top:54%;height:0.09em;width:calc(104%*' + dv + ');background:' + decorC + ';';
      else if (decor === 'underline') bar2 = 'left:0;bottom:-0.08em;height:0.1em;width:calc(100%*' + dv + ');background:' + decorC + ';';
      else bar2 = 'left:-0.15em;top:12%;height:78%;width:calc((100% + 0.3em)*' + dv + ');background:color-mix(in srgb,' + decorC + ' 38%,transparent);z-index:-1;';
      h = '<span style="position:relative;isolation:isolate;' + (blockish ? 'display:block;width:fit-content;' : 'display:inline-block;') + '">' + h + '<span aria-hidden="true" style="position:absolute;' + bar2 + '"></span></span>';
    }
    return h;
  }
  function wrapUnit0(inner, n, blockish) {
    var inl = blockish ? 'display:block;' : 'display:inline-block;';
    if (reveal === 'bar') return '<span style="' + uvar(n) + (blockish ? 'display:block;width:fit-content;' : 'display:inline-block;') + 'padding:0.04em 0.3em;margin-bottom:0.08em;background:linear-gradient(' + bar + ',' + bar + ') no-repeat 0 0 / calc(var(--u)*100%) 100%;"><span style="display:inherit;opacity:clamp(0,calc((var(--u) - 0.4)*2),1);">' + inner + '</span></span>';
    if (reveal === 'flap') { // a slot-reel flip: three seeded decoy glyphs scroll past before the real one lands
      var dg = '', dk;
      for (dk = 0; dk < 3; dk++) dg += '<span aria-hidden="true" style="display:block;height:1em;">' + _MO_FLAP.charAt((n * 7 + dk * 11 + 3) % _MO_FLAP.length) + '</span>';
      return '<span style="' + uvar(n) + 'display:inline-block;overflow:hidden;height:1em;line-height:1;vertical-align:bottom;"><span style="display:block;transform:translateY(calc(var(--u)*-3em));">' + dg + '<span style="display:block;height:1em;">' + inner + '</span></span></span>';
    }
    if (reveal === 'mask') return '<span style="' + inl + 'overflow:hidden;padding-bottom:0.12em;margin-bottom:-0.12em;vertical-align:bottom;"><span style="' + uvar(n) + 'display:inherit;transform:translateY(calc((1 - var(--u))*108%));">' + inner + '</span></span>';
    var fx = reveal === 'fade' ? '' : reveal === 'drop' ? 'transform:translateY(calc((1 - var(--u))*-0.6em));' : reveal === 'blur' ? 'filter:blur(calc((1 - var(--u))*0.25em));transform:translateY(calc((1 - var(--u))*0.15em));' : 'transform:translateY(calc((1 - var(--u))*0.6em));';
    return '<span style="' + uvar(n) + inl + 'opacity:var(--u);' + fx + '">' + inner + '</span>';
  }
  var out = '';
  for (k = 0; k < units.length; k++) {
    var u = units[k];
    if (u.block) { out += wrapUnit(_moRuns(u.c, accent), idx++, true); continue; }
    if (u.brk) out += '<br>';
    if (u.sp) out += ' ';
    if (mode === 'lines') { out += wrapUnit(_moRuns(u.c, accent), idx++, true); continue; }
    if (u.chars) {
      var ch = '';
      for (j = 0; j < u.c.length; j++) ch += wrapUnit(_moRuns([u.c[j]], accent), idx++, false);
      out += '<span style="display:inline-block;white-space:nowrap;">' + ch + '</span>';
    } else out += wrapUnit(_moRuns(u.c, accent), idx++, false);
  }
  var srText = _moPlain(lines.join(' ')), flipPlain = flipOn && typeof b.flip_text === 'string' ? _moPlain(b.flip_text.slice(0, 160)).replace(/\n/g, ' ') : '';
  if (flipPlain && flipPlain !== srText) srText += ', then ' + flipPlain;
  return (vf ? _moVfFace(vf) : '') + (flipFace && flipFace !== vf ? _moVfFace(flipFace) : '') + '<div style="font-family:' + font + ';font-size:' + size + 'px;font-weight:' + weight + ';line-height:' + lh + ';letter-spacing:' + track + 'em;color:' + color + ';text-align:' + align + ';' + (upper ? 'text-transform:uppercase;' : '') + (textShadow ? 'text-shadow:' + textShadow + ';' : '') + (mode === 'lines' ? 'white-space:nowrap;' : '') + 'width:100%;">'
    + _moSr(srText)
    + '<span aria-hidden="true" style="display:block;">' + out + prism + '</span></div>';
};

// Forms: bars, rules, discs, sweeping rings, gradients, soft glows. Fills its placed box, or w/h px.
_RENDERERS['motion_shape'] = function(b) {
  var shape = (b.shape === 'circle' || b.shape === 'ring' || b.shape === 'line') ? b.shape : 'rect';
  var fill = _moInk(b, 'fill', 'var(--mt-acc,#38bdf8)'), fill2 = _moInk(b, 'fill2', '');
  var angle = _ffInt(b.angle, 90, 0, 360), thick = _ffInt(b.thickness, 6, 1, 200), radius = _ffInt(b.radius, 0, 0, 500), blur = _ffInt(b.blur, 0, 0, 200);
  var dflt = shape === 'ring' ? 'sweep' : (shape === 'circle' ? 'scale' : 'grow-x');
  var draw = (b.draw === 'grow-x' || b.draw === 'grow-y' || b.draw === 'scale' || b.draw === 'fade' || b.draw === 'none' || (b.draw === 'sweep' && shape === 'ring')) ? b.draw : dflt;
  var w = typeof b.w === 'number' ? _ffInt(b.w, 100, 1, 3000) + 'px' : '100%', h = typeof b.h === 'number' ? _ffInt(b.h, 100, 1, 3000) + 'px' : '100%';
  if (shape === 'line') h = thick + 'px';
  var bg = fill2 ? 'linear-gradient(' + angle + 'deg,' + fill + ',' + fill2 + ')' : fill, extra = '';
  var origin = draw === 'grow-y' ? '50% 100%' : (draw === 'scale' ? '50% 50%' : '0 50%');
  if (shape === 'ring') {
    var mask = 'radial-gradient(farthest-side,transparent calc(100% - ' + thick + 'px),#000 calc(100% - ' + thick + 'px + 1px))';
    bg = draw === 'sweep' ? 'conic-gradient(from -90deg,' + (fill2 ? fill2 : fill) + ' calc(var(--p,1)*360deg),transparent 0)' : bg;
    extra = 'border-radius:50%;-webkit-mask:' + mask + ';mask:' + mask + ';';
  } else if (shape === 'circle') extra = 'border-radius:50%;';
  else extra = 'border-radius:' + (shape === 'line' ? thick : radius) + 'px;';
  var tf = draw === 'grow-x' ? 'transform:scaleX(var(--p,1));' : draw === 'grow-y' ? 'transform:scaleY(var(--p,1));' : draw === 'scale' ? 'transform:scale(var(--p,1));' : '';
  var op = draw === 'fade' ? 'opacity:var(--p,1);' : '';
  return '<div aria-hidden="true" style="width:' + w + ';height:' + h + ';box-sizing:border-box;background:' + bg + ';' + extra + tf + op + 'transform-origin:' + origin + ';' + (blur ? 'filter:blur(' + blur + 'px);' : '') + '"></div>';
};

// A big number that counts from `from` to `to` as --p goes 0..1, with an optional caption.
_RENDERERS['motion_counter'] = function(b) {
  var dec = _ffInt(b.decimals, 0, 0, 3), to = _moNum(b.to, 100), from = _moNum(b.from, 0), pre = _moStr(b.prefix, 4), suf = _moStr(b.suffix, 8);
  var size = _ffInt(b.size, 96, 10, 400), weight = _ffPick(b.weight, _FF_WEIGHTS, 'black'), font = _ffPick(b.font, _FF_FONTS, 'display');
  var color = _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), align = _ffPick(b.align, _MO_ALIGN, 'start'), label = _moStr(b.label, 40);
  var lsize = _ffInt(b.label_size, Math.max(11, Math.floor(size / 5)), 8, 80), shown;
  if (b.roll === true) { // odometer: every digit is a 0-9 strip that scrolls to its value, left to right, as p goes 0 to 1 (counts from zero)
    var txt = _moFmt(to, dec, pre, suf), chs = Array.from(txt), nd = 0, rk, rolled = '';
    for (rk = 0; rk < chs.length; rk++) if (/[0-9]/.test(chs[rk])) nd++;
    var di = 0;
    for (rk = 0; rk < chs.length; rk++) {
      if (/[0-9]/.test(chs[rk])) {
        var strip = '', dd;
        for (dd = 0; dd < 10; dd++) strip += '<span style="display:block;height:1em;">' + dd + '</span>';
        rolled += '<span style="--u:clamp(0,calc(var(--p,1)*' + (nd + 1) + ' - ' + di + '),1);display:inline-block;overflow:hidden;height:1em;vertical-align:bottom;"><span style="display:block;transform:translateY(calc(var(--u)*-' + chs[rk] + 'em));">' + strip + '</span></span>';
        di++;
      } else rolled += '<span style="display:inline-block;height:1em;vertical-align:bottom;white-space:pre;">' + _esc(chs[rk]) + '</span>';
    }
    shown = _moSr(txt) + '<span aria-hidden="true">' + rolled + '</span>';
  } else shown = _moCount(to, dec, pre, suf, '', from);
  return '<div style="width:100%;text-align:' + align + ';">'
    + '<div style="font-family:' + font + ';font-size:' + size + 'px;font-weight:' + weight + ';line-height:1;letter-spacing:-0.02em;color:' + color + ';font-variant-numeric:tabular-nums;' + (b.roll === true ? 'height:1em;overflow:hidden;' : '') + '">' + shown + '</div>'
    + (label ? '<div style="font-family:' + _MO_SANS + ';font-size:' + lsize + 'px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--mt-mute,#94a3b8);margin-top:0.5em;">' + _esc(label) + '</div>' : '')
    + '</div>';
};

// ─── atoms from a studied reference film (2026-10-01) ───────────────────────────────────────────────────────────────
// A published 36 s LinkedIn motion piece (dark, one orange accent) showed what the catalogue lacked: a process map whose rail
// draws and whose chosen cards light up, a ring of app tiles around a product shot, a ticking recipe card, code typing in, a
// persistent call-to-action pill, an accent word inside a headline, and scenes STITCHED together instead of cut. All plain
// HTML+CSS: --p builds the thing, --s is its second dial (spotlight, orbit angle). Standalone each renders its final state.
// Colours come from the stage theme through color-mix, so a light or dark stage both read. Tile glyphs are text, never logos.
var _MO_MIX_LINE = 'color-mix(in srgb,var(--mt-ink,#f1f5f9) 14%,transparent)';
var _MO_MIX_FILL = 'color-mix(in srgb,var(--mt-ink,#f1f5f9) 5%,transparent)';

// A rounded call-to-action chip. *word* inside the text takes the accent colour.
_RENDERERS['motion_pill'] = function(b) {
  var text = _moStr(b.text, 60) || 'Label', size = _ffInt(b.size, 28, 10, 120), icon = _moStr(b.icon, 2);
  var acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), color = _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), fill = _moInk(b, 'fill', '');
  var align = _ffPick(b.align, _MO_ALIGN, 'start'), jc = align === 'right' ? 'flex-end' : (align === 'center' ? 'center' : 'flex-start');
  var href = typeof b.href === 'string' ? b.href.trim() : '', tag = href ? 'a' : 'div';
  return '<div style="display:flex;justify-content:' + jc + ';width:100%;">'
    + '<' + tag + (href ? ' href="' + _esc(href) + '"' : '') + ' style="' + (href ? 'text-decoration:none;cursor:pointer;pointer-events:auto;' : '') + 'display:inline-flex;align-items:center;gap:0.55em;box-sizing:border-box;padding:0.55em 1.3em;border-radius:999px;border:1px solid ' + _MO_MIX_LINE + ';background:' + (fill || _MO_MIX_FILL) + ';color:' + color + ';font-family:' + _MO_SANS + ';font-size:' + size + 'px;font-weight:600;line-height:1.1;white-space:nowrap;opacity:clamp(0,var(--p,1),1);transform:translateY(calc((1 - clamp(0,var(--p,1),1))*0.5em));">'
    + _moSr(_moPlain(text))
    + '<span aria-hidden="true" style="display:inline-flex;align-items:center;gap:0.55em;">' + (icon ? '<span style="color:' + acc + ';">' + _esc(icon) + '</span>' : '') + '<span>' + _moRuns(_moChars(text), acc) + '</span></span></' + tag + '></div>';
};

// A card of items that tick off in turn as p goes 0..1, with optional empty placeholder rows under them.
_RENDERERS['motion_checklist'] = function(b) {
  var title = _moStr(b.title, 40), size = _ffInt(b.size, 26, 10, 80), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)');
  var src = Array.isArray(b.items) ? b.items : [], items = [], i;
  for (i = 0; i < src.length && items.length < 6; i++) {
    var it = src[i], obj = it && typeof it === 'object', t = _moStr(typeof it === 'string' ? it : (obj ? it.text : ''), 40);
    if (t) items.push({t: t, i: obj ? _moStr(it.icon, 2) : ''});
  }
  if (!items.length) items = [{t: 'Item', i: ''}];
  var n = items.length, skel = _ffInt(b.skeleton, 0, 0, 4), rows = '';
  var tick = '<svg viewBox="0 0 16 16" width="62%" height="62%" aria-hidden="true"><path d="M3.8 8.6l2.8 2.8 5.6-5.8" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  for (i = 0; i < n; i++) {
    rows += '<div style="--u:clamp(0,calc(var(--p,1)*' + n + ' - ' + i + '),1);display:flex;align-items:center;gap:0.7em;padding:0.55em 0.8em;border-radius:0.7em;background:' + _MO_MIX_FILL + ';opacity:calc(0.4 + 0.6*var(--u));margin-top:0.55em;">'
      + (items[i].i ? '<span aria-hidden="true">' + _esc(items[i].i) + '</span>' : '')
      + '<span style="flex:1;font-weight:600;transform:translateX(calc((1 - var(--u))*-0.4em));">' + _esc(items[i].t) + '</span>'
      + '<span aria-hidden="true" style="position:relative;width:1.35em;height:1.35em;flex:none;box-sizing:border-box;border-radius:50%;border:2px solid ' + _MO_MIX_LINE + ';">'
      + '<span style="position:absolute;left:-2px;top:-2px;right:-2px;bottom:-2px;border-radius:50%;background:' + acc + ';display:flex;align-items:center;justify-content:center;transform:scale(var(--u));">' + tick + '</span></span></div>';
  }
  for (i = 0; i < skel; i++) rows += '<div aria-hidden="true" style="height:2.3em;border-radius:0.7em;background:' + _MO_MIX_FILL + ';margin-top:0.55em;"></div>';
  return '<div style="box-sizing:border-box;width:100%;padding:0.9em;border-radius:1.1em;border:1px solid ' + _MO_MIX_LINE + ';background:' + _MO_MIX_FILL + ';color:var(--mt-ink,#f1f5f9);font-family:' + _MO_SANS + ';font-size:' + size + 'px;line-height:1.2;">'
    + (title ? '<div style="font-weight:700;font-size:0.9em;">' + _esc(title) + '</div>' : '') + rows + '</div>';
};

// A process map: a rail that draws left to right with a node per column, cards that rise in under each, and (with focus) a
// spotlight on chosen cards while the rest dim. --p builds it, --s drives the spotlight, the metric bars and the scan line.
_RENDERERS['motion_stepper'] = function(b) {
  var size = _ffInt(b.size, 16, 8, 60), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), cap = _moStr(b.title, 40);
  var cols = [], src = Array.isArray(b.columns) ? b.columns : [], i, j;
  for (i = 0; i < src.length && cols.length < 6; i++) {
    var c = src[i];
    if (!c || typeof c !== 'object') continue;
    var its = [], isrc = Array.isArray(c.items) ? c.items : [];
    for (j = 0; j < isrc.length && its.length < 4; j++) {
      var it = isrc[j], obj = it && typeof it === 'object', tx = _moStr(typeof it === 'string' ? it : (obj ? it.text : ''), 40);
      if (!tx) continue;
      its.push({t: tx, m: obj ? _moStr(it.meta, 16) : '', v: obj ? _ffNum(it.value, 0, 0, 1, 2) : '0'});
    }
    cols.push({t: _moStr(c.title, 24) || 'Step', items: its});
  }
  if (!cols.length) cols = [{t: 'Step', items: [{t: 'Item', m: '', v: '0'}]}];
  var C = cols.length, R = 0;
  for (i = 0; i < C; i++) R = Math.max(R, cols[i].items.length);
  var fsrc = Array.isArray(b.focus) ? b.focus : [], bsrc = Array.isArray(b.badges) ? b.badges : [], fmap = {}, nf = 0;
  for (i = 0; i < fsrc.length && i < 6; i++) {
    var f = fsrc[i];
    if (Array.isArray(f) && typeof f[0] === 'number' && typeof f[1] === 'number' && isFinite(f[0]) && isFinite(f[1])) { fmap[Math.floor(f[0]) + ',' + Math.floor(f[1])] = _moStr(bsrc[i], 6); nf++; }
  }
  var dim = nf ? '0.7' : '0';
  var html = '<div style="position:relative;width:100%;font-family:' + _MO_SANS + ';font-size:' + size + 'px;color:var(--mt-ink,#f1f5f9);">';
  if (cap) html += '<div style="font-family:' + _FF_FONTS.mono + ';font-size:0.62em;letter-spacing:0.2em;text-transform:uppercase;color:var(--mt-mute,#94a3b8);margin-bottom:1.4em;opacity:clamp(0,calc(var(--p,1)*6),1);">' + _esc(cap) + '</div>';
  html += '<div style="position:relative;display:grid;grid-template-columns:repeat(' + C + ',minmax(0,1fr));column-gap:0.9em;">'
    + '<div aria-hidden="true" style="position:absolute;left:0.4em;right:0;top:0.4em;height:2px;background:' + acc + ';opacity:0.85;transform-origin:0 0;transform:scaleX(clamp(0,var(--p,1),1));"></div>';
  if (b.scan === true) html += '<div aria-hidden="true" style="position:absolute;top:0;bottom:0;left:calc(var(--s,1)*100%);width:2px;background:linear-gradient(transparent,' + acc + ',transparent);box-shadow:0 0 18px ' + acc + ';opacity:min(calc(var(--s,1)*8),calc((1 - var(--s,1))*8),1);z-index:3;"></div>';
  for (i = 0; i < C; i++) {
    html += '<div style="--u:clamp(0,calc(var(--p,1)*' + (C + 1) + ' - ' + i + '),1);position:relative;">'
      + '<div style="display:flex;align-items:center;gap:0.55em;font-weight:700;font-size:0.95em;margin-bottom:1em;opacity:var(--u);transform:translateY(calc((1 - var(--u))*0.5em));">'
      + '<span aria-hidden="true" style="position:relative;z-index:1;width:0.8em;height:0.8em;flex:none;border-radius:50%;background:' + acc + ';"></span>' + _esc(cols[i].t) + '</div>';
    for (j = 0; j < cols[i].items.length; j++) {
      var cell = cols[i].items[j], key = i + ',' + j, foc = Object.prototype.hasOwnProperty.call(fmap, key);
      html += '<div style="--v:clamp(0,calc(var(--u)*' + (R + 1) + ' - ' + j + '),1);position:relative;margin-bottom:0.6em;padding:0.7em 0.8em;box-sizing:border-box;border-radius:0.6em;border:1px solid ' + _MO_MIX_LINE + ';background:' + _MO_MIX_FILL + ';font-size:0.8em;line-height:1.25;'
        + 'opacity:' + (foc ? 'var(--v)' : 'calc(var(--v)*(1 - ' + dim + '*var(--s,1)))') + ';transform:translateY(calc((1 - var(--v))*0.6em));">' + _esc(cell.t);
      if (cell.m) html += '<div style="display:flex;justify-content:space-between;font-family:' + _FF_FONTS.mono + ';font-size:0.8em;color:var(--mt-mute,#94a3b8);margin-top:0.5em;opacity:var(--s,1);">' + _esc(cell.m) + '</div>'
        + '<div aria-hidden="true" style="height:3px;border-radius:2px;background:' + acc + ';margin-top:0.35em;transform-origin:0 50%;transform:scaleX(calc(var(--s,1)*' + cell.v + '));"></div>';
      if (foc) {
        html += '<span aria-hidden="true" style="position:absolute;left:-1px;top:-1px;right:-1px;bottom:-1px;border-radius:inherit;border:2px solid ' + acc + ';box-shadow:0 0 22px color-mix(in srgb,' + acc + ' 35%,transparent);opacity:var(--s,1);"></span>';
        if (fmap[key]) html += '<span style="position:absolute;top:-0.7em;right:-0.5em;background:' + acc + ';color:#0b0b0b;font-family:' + _FF_FONTS.mono + ';font-weight:700;font-size:0.75em;padding:0.15em 0.55em;border-radius:999px;transform:scale(var(--s,1));">' + _esc(fmap[key]) + '</span>';
      }
      html += '</div>';
    }
    html += '</div>';
  }
  return html + '</div></div>';
};

// Tiles that fly out from the centre onto an ellipse and swing round it as --s goes 0..1. Text tiles only (letters, glyphs, short
// labels): never brand logos. Put the product shot in the same layer, centred.
_RENDERERS['motion_orbit'] = function(b) {
  var size = _ffInt(b.size, 64, 24, 160), src = Array.isArray(b.items) ? b.items : [], items = [], i;
  for (i = 0; i < src.length && items.length < 12; i++) { var t = _moStr(typeof src[i] === 'string' ? src[i] : (src[i] && typeof src[i] === 'object' ? src[i].text : ''), 8); if (t) items.push(t); }
  if (!items.length) items = ['A'];
  var n = items.length, rx = _ffInt(b.rx, 40, 5, 60), ry = _ffInt(b.ry, 36, 5, 60), start = _ffInt(b.start, -90, -360, 360), spin = _ffInt(b.spin, 40, -360, 360);
  var fill = _moInk(b, 'fill', '#ffffff'), ink = _moInk(b, 'ink', '#111827');
  var html = '<div style="position:relative;width:100%;height:100%;">';
  if (b.ring !== false) html += '<div aria-hidden="true" style="position:absolute;left:' + (50 - rx) + '%;top:' + (50 - ry) + '%;width:' + (2 * rx) + '%;height:' + (2 * ry) + '%;box-sizing:border-box;border-radius:50%;border:1px dashed ' + _MO_MIX_LINE + ';opacity:clamp(0,var(--p,1),1);"></div>';
  for (i = 0; i < n; i++) {
    var a = start + Math.floor(i * 360 / n + 0.5), len = Array.from(items[i]).length, fs = len > 2 ? Math.floor(size * 22 / 100) : Math.floor(size * 42 / 100);
    var ang = 'calc(' + a + 'deg + var(--s,0)*' + spin + 'deg)';
    html += '<div style="--u:clamp(0,calc((var(--p,1)*' + (n + 3) + ' - ' + i + ')/3),1);position:absolute;left:calc(50% + ' + rx + '%*var(--u)*cos(' + ang + '));top:calc(50% + ' + ry + '%*var(--u)*sin(' + ang + '));width:' + size + 'px;height:' + size + 'px;margin:-' + Math.floor(size / 2) + 'px 0 0 -' + Math.floor(size / 2) + 'px;display:flex;align-items:center;justify-content:center;border-radius:28%;background:' + fill + ';color:' + ink + ';font-family:' + _MO_SANS + ';font-size:' + fs + 'px;font-weight:800;box-shadow:0 10px 30px rgba(0,0,0,0.35);transform:scale(var(--u));opacity:var(--u);">' + _esc(items[i]) + '</div>';
  }
  return html + '</div>';
};

// Code that types itself in as p goes 0..1. Monospace, so a line's width is its character count in ch: no JS, no per-letter spans.
var _MO_KW = /\b(const|let|var|function|return|export|default|import|from|await|async|if|else|for|new)\b/g;
_RENDERERS['motion_code'] = function(b) {
  var src = Array.isArray(b.lines) ? b.lines : [], lines = [], i, total = 0;
  for (i = 0; i < src.length && lines.length < 14; i++) lines.push(typeof src[i] === 'string' ? src[i].replace(/[ \t\r\n]+$/, '').slice(0, 72) : '');
  if (!lines.length) lines = ['// code'];
  var size = _ffInt(b.size, 18, 8, 60), file = _moStr(b.file, 32), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), starts = [];
  for (i = 0; i < lines.length; i++) { starts.push(total); total += Array.from(lines[i]).length; }
  var T = Math.max(1, total), rows = '';
  for (i = 0; i < lines.length; i++) {
    var len = Array.from(lines[i]).length, esc = _esc(lines[i]), body;
    if (/^[ \t]*\/\//.test(lines[i])) body = '<span style="color:var(--mt-mute,#94a3b8);">' + esc + '</span>';
    else body = esc.replace(_MO_KW, function(m) { return '<span style="color:' + acc + ';">' + m + '</span>'; });
    rows += '<div style="--t:clamp(0,calc(var(--p,1)*' + T + ' - ' + starts[i] + '),' + len + ');display:flex;height:1.6em;align-items:center;">'
      + '<span style="display:block;overflow:hidden;white-space:pre;width:calc(var(--t)*1ch);">' + body + '</span>'
      + '<span aria-hidden="true" style="flex:none;width:0.6ch;height:1.15em;background:' + acc + ';opacity:calc(clamp(0,calc(var(--t)*1000),1)*clamp(0,calc((' + len + ' - var(--t))*1000),1));"></span></div>';
  }
  return '<div style="box-sizing:border-box;width:100%;padding:0.9em 1.2em 1.1em;border-radius:1em;border:1px solid ' + _MO_MIX_LINE + ';background:' + _MO_MIX_FILL + ';color:var(--mt-ink,#f1f5f9);font-family:' + _FF_FONTS.mono + ';font-size:' + size + 'px;">'
    + '<div aria-hidden="true" style="display:flex;align-items:center;gap:0.45em;margin-bottom:0.8em;"><span style="width:0.65em;height:0.65em;border-radius:50%;background:' + _MO_MIX_LINE + ';"></span><span style="width:0.65em;height:0.65em;border-radius:50%;background:' + _MO_MIX_LINE + ';"></span><span style="width:0.65em;height:0.65em;border-radius:50%;background:' + _MO_MIX_LINE + ';"></span>'
    + (file ? '<span style="margin-left:0.6em;font-size:0.72em;color:var(--mt-mute,#94a3b8);">' + _esc(file) + '</span>' : '') + '</div>'
    + _moSr(lines.join(' ')) + '<div aria-hidden="true">' + rows + '</div></div>';
};

// The catalogue's own mark (three tilted ellipses, a nucleus, one electron) that DRAWS itself as p goes 0..1 and whose electron
// circles its orbit as step (--s) goes 0..1. Geometry is the site logo's (atoms/brand-tokens.yaml); colours are fields.
_RENDERERS['motion_mark'] = function(b) {
  var size = _ffInt(b.size, 120, 24, 600), a1 = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), a2 = _moInk(b, 'accent2', '#00b7c3');
  var ew = Math.max(4, Math.floor(size * 5 / 48)), ang = 'calc(197deg + var(--s,0)*360deg)';
  function el(rot, p, w, op, col) {
    return '<ellipse cx="12" cy="12" rx="10" ry="4.4" transform="rotate(' + rot + ' 12 12)" pathLength="1" style="stroke:' + col + ';stroke-width:' + w + ';' + (op ? 'opacity:' + op + ';' : '') + 'stroke-dasharray:1;stroke-dashoffset:calc(1 - clamp(0,' + p + ',1));"/>';
  }
  return '<div role="img" aria-label="A2UI Catalog mark" style="position:relative;width:' + size + 'px;height:' + size + 'px;">'
    + '<svg viewBox="0 0 24 24" width="100%" height="100%" aria-hidden="true" style="display:block;overflow:visible;fill:none;">'
    + el(-32, 'var(--p,1)', 1.5, '', a1) + el(32, 'calc(var(--p,1)*1.5 - 0.25)', 1.5, '', a2) + el(90, 'calc(var(--p,1)*1.5 - 0.5)', 1.1, '0.35', a1)
    + '<circle cx="12" cy="12" r="2.7" style="fill:' + a1 + ';transform-box:fill-box;transform-origin:center;transform:scale(clamp(0,calc(var(--p,1)*4),1));"/></svg>'
    + '<div aria-hidden="true" style="position:absolute;left:calc(50% + 35.335%*cos(' + ang + ') + 9.715%*sin(' + ang + '));top:calc(50% - 22.08%*cos(' + ang + ') + 15.548%*sin(' + ang + '));width:' + ew + 'px;height:' + ew + 'px;border-radius:50%;background:' + a2 + ';transform:translate(-50%,-50%);opacity:clamp(0,calc((var(--p,1) - 0.7)*4),1);"></div></div>';
};

// The catalogue browser: a search box that types its query, filter chips, and a grid of cards that rise in, each holding a LIVE render
// of a real atom (pass the atom block as `preview`). One card can be picked with step (--s): it lifts and takes an accent outline.
// p 0..0.3 types the query, p 0.3..1 brings the cards in. Plain HTML and CSS, no script. Standalone it renders the finished screen.
_RENDERERS['motion_browser'] = function(b) {
  var size = _ffInt(b.size, 16, 8, 40), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), q = Array.from(_moStr(b.query, 16)), ph = _moStr(b.placeholder, 24) || 'Search atoms…';
  var chips = [], cs = Array.isArray(b.chips) ? b.chips : [], cards = [], cr = Array.isArray(b.cards) ? b.cards : [], i;
  for (i = 0; i < cs.length && chips.length < 6; i++) { var ct = _moStr(cs[i], 24); if (ct) chips.push(ct); }
  for (i = 0; i < cr.length && cards.length < 6; i++) {
    var c = cr[i];
    if (!c || typeof c !== 'object') continue;
    cards.push({t: _moStr(c.title, 28) || 'Atom', x: _moStr(c.text, 90), g: _moStr(c.badge, 16), s: _moStr(c.source, 20), p: c.preview && typeof c.preview === 'object' ? _moRender(c.preview) : ''});
  }
  var well = _moInk(b, 'well', ''), N = cards.length, cols = _ffInt(b.columns, 3, 2, 4), pick = N ? Math.min(_ffInt(b.pick, -1, -1, 5), N - 1) : -1, count = _moStr(b.count, 16);
  var typed = '';
  for (i = 0; i < q.length; i++) typed += '<span style="opacity:clamp(0,calc(var(--q)*' + q.length + ' - ' + i + '),1);">' + _esc(q[i]) + '</span>';
  var html = '<div style="width:100%;font-family:' + _MO_SANS + ';font-size:' + size + 'px;color:var(--mt-ink,#f1f5f9);">'
    + '<div style="--q:clamp(0,calc(var(--p,1)*3.334),1);position:relative;display:flex;align-items:center;gap:0.7em;box-sizing:border-box;padding:0.7em 1em;border-radius:0.7em;border:1.5px solid ' + acc + ';background:' + _MO_MIX_FILL + ';">'
    + '<svg viewBox="0 0 16 16" width="1.1em" height="1.1em" aria-hidden="true" style="flex:none;opacity:0.55;"><circle cx="7" cy="7" r="4.6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10.6 10.6L14 14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
    + '<span style="position:relative;flex:1;min-height:1.3em;">' + (q.length ? _moSr(q.join('')) : '')
    + '<span aria-hidden="true" style="position:absolute;left:0;top:0;color:var(--mt-mute,#94a3b8);opacity:calc(1 - clamp(0,calc(var(--p,1)*30),1));white-space:nowrap;">' + _esc(ph) + '</span>'
    + '<span aria-hidden="true" style="white-space:nowrap;">' + typed + '</span></span></div>';
  if (chips.length || count) {
    html += '<div style="display:flex;align-items:center;gap:0.5em;margin:0.9em 0 1.1em;flex-wrap:wrap;opacity:clamp(0,calc(var(--p,1)*10),1);">';
    for (i = 0; i < chips.length; i++) html += '<span style="padding:0.35em 0.9em;border-radius:999px;border:1px solid ' + _MO_MIX_LINE + ';font-size:0.8em;font-weight:600;' + (i === 0 ? 'background:color-mix(in srgb,' + acc + ' 16%,transparent);color:' + acc + ';border-color:transparent;' : 'color:var(--mt-mute,#94a3b8);') + '">' + _esc(chips[i]) + '</span>';
    html += (count ? '<span style="margin-left:auto;font-size:0.8em;color:var(--mt-mute,#94a3b8);opacity:clamp(0,calc((var(--p,1) - 0.3)*10),1);">' + _esc(count) + '</span>' : '') + '</div>';
  }
  html += '<div style="display:grid;grid-template-columns:repeat(' + cols + ',minmax(0,1fr));gap:0.9em;">';
  for (i = 0; i < N; i++) {
    var cd = cards[i], pk = i === pick;
    html += '<div style="--u:clamp(0,calc((clamp(0,calc((var(--p,1) - 0.3)*1.4286),1)*' + (N + 2) + ' - ' + i + ')/2),1);position:relative;border-radius:0.8em;border:1px solid ' + _MO_MIX_LINE + ';background:' + _MO_MIX_FILL + ';overflow:hidden;opacity:var(--u);'
      + 'transform:translateY(calc((1 - var(--u))*0.8em)' + (pk ? ' - var(--s,1)*0.35em' : '') + ');">'
      + '<div aria-hidden="true" style="height:7.2em;display:flex;align-items:center;justify-content:center;overflow:hidden;border-bottom:1px solid ' + _MO_MIX_LINE + ';' + (well ? 'background-color:' + well + ';' : '') + 'background-image:radial-gradient(color-mix(in srgb,var(--mt-ink,#f1f5f9) 16%,transparent) 1px,transparent 1px);background-size:12px 12px;"><div style="transform:scale(0.92);pointer-events:none;">' + cd.p + '</div></div>'
      + '<div style="padding:0.85em 0.95em 0.95em;"><div style="font-weight:700;font-size:1em;">' + _esc(cd.t) + '</div>'
      + '<div style="font-size:0.82em;line-height:1.4;color:var(--mt-mute,#94a3b8);margin-top:0.35em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.8em;">' + _esc(cd.x) + '</div>'
      + '<div style="display:flex;align-items:center;justify-content:space-between;gap:0.5em;margin-top:0.7em;">'
      + (cd.g ? '<span style="padding:0.25em 0.7em;border-radius:0.5em;font-size:0.72em;font-weight:700;white-space:nowrap;background:color-mix(in srgb,' + acc + ' 16%,transparent);color:' + acc + ';">' + _esc(cd.g) + '</span>' : '<span></span>')
      + (cd.s ? '<span style="padding:0.2em 0.6em;border-radius:999px;font-size:0.68em;font-weight:700;white-space:nowrap;background:' + _MO_MIX_FILL + ';color:var(--mt-mute,#94a3b8);">' + _esc(cd.s) + '</span>' : '') + '</div></div>'
      + (pk ? '<span aria-hidden="true" style="position:absolute;left:-1px;top:-1px;right:-1px;bottom:-1px;border-radius:inherit;border:2px solid ' + acc + ';box-shadow:0 14px 34px color-mix(in srgb,' + acc + ' 30%,transparent);opacity:var(--s,1);"></span>' : '') + '</div>';
  }
  return html + '</div></div>';
};

// Strokes that DRAW themselves in turn as p goes 0..1: path data from a strict grammar (path commands, numbers and separators only,
// so nothing but a path can reach the markup), each stroke optionally tinted. A film's "an agent sketches a robot".
var _MO_PATH_OK = /^[MmLlHhVvCcSsQqTtAaZz0-9eE.,+\- \t\n\r]{1,700}$/;
_RENDERERS['motion_sketch'] = function(b) {
  var src = Array.isArray(b.strokes) ? b.strokes : [], st = [], i;
  for (i = 0; i < src.length && st.length < 24; i++) {
    var s = src[i];
    if (!s || typeof s !== 'object' || typeof s.d !== 'string') continue;
    var d = s.d.trim();
    if (!_MO_PATH_OK.test(d)) continue;
    st.push({d: d, c: _moInk(s, 'color', 'var(--mt-ink,#f1f5f9)'), w: _ffInt(s.width, 6, 1, 24), f: _moInk(s, 'fill', ''), fo: _ffNum(s.fill_opacity, 0.2, 0, 1, 2)});
  }
  var vw = _ffInt(b.w, 400, 50, 2000), vh = _ffInt(b.h, 400, 50, 2000), n = st.length, label = _moStr(b.label, 60) || 'Sketch', body = '';
  for (i = 0; i < n; i++) {
    var u = '--u:clamp(0,calc(var(--p,1)*' + n + ' - ' + i + '),1);';
    if (st[i].f) body += '<path d="' + st[i].d + '" style="' + u + 'fill:' + st[i].f + ';stroke:none;opacity:calc(var(--u)*' + st[i].fo + ');"/>';
    body += '<path d="' + st[i].d + '" pathLength="1" style="' + u + 'fill:none;stroke:' + st[i].c + ';stroke-width:' + st[i].w + ';stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:calc(1 - var(--u));"/>';
  }
  return '<svg viewBox="0 0 ' + vw + ' ' + vh + '" width="100%" style="display:block;overflow:visible;" role="img" aria-label="' + _esc(label) + '">' + body + '</svg>';
};

// ─── second reference reel (2026-10-01): callout leader lines, route paths, shape-masked reveals ──────────────────────────────
function _moPt(v, vw, vh, dx, dy) {
  var x = dx * vw, y = dy * vh;
  if (Array.isArray(v) && v.length >= 2) { x = _moNum(v[0], x); y = _moNum(v[1], y); }
  return [Math.max(-4000, Math.min(6000, x)), Math.max(-4000, Math.min(6000, y))];
}
function _moF(x) { return _ffNum(x, 0, -100000, 100000, 1); }

// A line (straight or curved) that draws itself from one point to another, with an arrowhead, a start dot and a label: the
// callout that points at a thing in a diagram. Points are in viewBox units (w by h, default 400 by 300).
_RENDERERS['motion_leader'] = function(b) {
  var vw = _ffInt(b.w, 400, 50, 2000), vh = _ffInt(b.h, 300, 50, 2000), a = _moPt(b.from, vw, vh, 0.12, 0.7), z = _moPt(b.to, vw, vh, 0.88, 0.3);
  var wd = _ffInt(b.width, 4, 1, 24), col = _moInk(b, 'color', 'var(--mt-acc,#38bdf8)'), lc = _moInk(b, 'label_color', 'var(--mt-ink,#f1f5f9)'), fs = _ffInt(b.size, 22, 8, 80);
  var label = _moStr(b.label, 40), at = b.label_at === 'start' ? 'start' : 'end', curve = _ffInt(b.curve, 0, -100, 100), arrow = b.arrow !== false, dot = b.dot !== false;
  var dx = z[0] - a[0], dy = z[1] - a[1], len = Math.sqrt(dx * dx + dy * dy) || 1;
  var cx = (a[0] + z[0]) / 2 - dy * curve / 100, cy = (a[1] + z[1]) / 2 + dx * curve / 100;
  var d = 'M' + _moF(a[0]) + ' ' + _moF(a[1]) + ' Q' + _moF(cx) + ' ' + _moF(cy) + ' ' + _moF(z[0]) + ' ' + _moF(z[1]);
  var tx = z[0] - cx, ty = z[1] - cy, tl = Math.sqrt(tx * tx + ty * ty), sx = cx - a[0], sy = cy - a[1], sl = Math.sqrt(sx * sx + sy * sy);
  if (tl < 0.001) { tx = dx; ty = dy; tl = len; }
  if (sl < 0.001) { sx = dx; sy = dy; sl = len; }
  tx /= tl; ty /= tl; sx /= sl; sy /= sl;
  var hl = wd * 3 + 6, hw = wd * 1.6 + 3, bx = z[0] - tx * hl, by = z[1] - ty * hl, nx = -ty, ny = tx, r0 = wd * 1.5 + 2;
  var head = 'M' + _moF(z[0]) + ' ' + _moF(z[1]) + ' L' + _moF(bx + nx * hw) + ' ' + _moF(by + ny * hw) + ' L' + _moF(bx - nx * hw) + ' ' + _moF(by - ny * hw) + ' Z';
  var lx = at === 'end' ? z[0] + tx * (hl + 10) : a[0] - sx * (r0 + 10), ly = at === 'end' ? z[1] + ty * (hl + 10) : a[1] - sy * (r0 + 10);
  var anchor = at === 'end' ? (tx >= 0 ? 'start' : 'end') : (sx > 0 ? 'end' : 'start');
  return '<svg viewBox="0 0 ' + vw + ' ' + vh + '" width="100%" style="display:block;overflow:visible;" role="img" aria-label="' + _esc(label || 'Leader line') + '">'
    + '<path d="' + d + '" pathLength="1" style="fill:none;stroke:' + col + ';stroke-width:' + wd + ';stroke-linecap:round;stroke-dasharray:1;stroke-dashoffset:calc(1 - clamp(0,calc(var(--p,1)/0.7),1));"/>'
    + (dot ? '<circle cx="' + _moF(a[0]) + '" cy="' + _moF(a[1]) + '" r="' + _moF(r0) + '" style="fill:' + col + ';transform-box:fill-box;transform-origin:center;transform:scale(clamp(0,calc(var(--p,1)*14),1));"/>' : '')
    + (arrow ? '<path d="' + head + '" style="fill:' + col + ';opacity:clamp(0,calc((var(--p,1) - 0.66)*12),1);"/>' : '')
    + (label ? '<text x="' + _moF(lx) + '" y="' + _moF(ly) + '" text-anchor="' + anchor + '" dominant-baseline="central" style="font-family:' + _MO_SANS + ';font-size:' + fs + 'px;font-weight:700;fill:' + lc + ';opacity:clamp(0,calc((var(--p,1) - 0.55)*5),1);">' + _esc(label) + '</text>' : '')
    + '</svg>';
};

// A route that draws itself, with a marker travelling along it and stops that pop as it passes: the metro line, the flight path.
// The marker is a zero-length round dash riding the path, so it needs no script and follows the film clock exactly.
_RENDERERS['motion_path'] = function(b) {
  var d = typeof b.d === 'string' ? b.d.trim() : '';
  if (!_MO_PATH_OK.test(d)) d = 'M 20 200 C 120 40 280 360 380 200';
  var vw = _ffInt(b.w, 400, 50, 2000), vh = _ffInt(b.h, 400, 50, 2000), wd = _ffInt(b.width, 6, 1, 24), col = _moInk(b, 'color', 'var(--mt-acc,#38bdf8)'), lc = _moInk(b, 'label_color', 'var(--mt-ink,#f1f5f9)'), fs = _ffInt(b.size, 20, 8, 80);
  var src = Array.isArray(b.nodes) ? b.nodes : [], nodes = '', i, n = 0, r = wd * 1.7 + 3, label = _moStr(b.label, 60) || 'Route';
  for (i = 0; i < src.length && n < 8; i++) {
    var s = src[i];
    if (!s || typeof s !== 'object') continue;
    var x = Math.max(-4000, Math.min(6000, _moNum(s.x, 0))), y = Math.max(-4000, Math.min(6000, _moNum(s.y, 0))), at = _ffNum(s.at, 0.5, 0, 1, 2), t = _moStr(s.label, 30);
    nodes += '<g style="--k:clamp(0,calc((var(--p,1) - ' + at + ')*14),1);"><circle cx="' + _moF(x) + '" cy="' + _moF(y) + '" r="' + _moF(r) + '" style="fill:' + col + ';transform-box:fill-box;transform-origin:center;transform:scale(var(--k));"/>'
      + '<circle cx="' + _moF(x) + '" cy="' + _moF(y) + '" r="' + _moF(r * 0.42) + '" style="fill:' + lc + ';transform-box:fill-box;transform-origin:center;transform:scale(var(--k));"/>'
      + (t ? '<text x="' + _moF(x + r + 10) + '" y="' + _moF(y) + '" dominant-baseline="central" style="font-family:' + _MO_SANS + ';font-size:' + fs + 'px;font-weight:700;fill:' + lc + ';opacity:var(--k);">' + _esc(t) + '</text>' : '') + '</g>';
    n++;
  }
  return '<svg viewBox="0 0 ' + vw + ' ' + vh + '" width="100%" style="display:block;overflow:visible;" role="img" aria-label="' + _esc(label) + '">'
    + '<path d="' + d + '" pathLength="1" style="fill:none;stroke:' + col + ';stroke-width:' + wd + ';stroke-linecap:round;opacity:0.16;"/>'
    + '<path d="' + d + '" pathLength="1" style="fill:none;stroke:' + col + ';stroke-width:' + wd + ';stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:calc(1 - clamp(0,var(--p,1),1));"/>'
    + (b.marker !== false ? '<path d="' + d + '" pathLength="1" style="fill:none;stroke:' + lc + ';stroke-width:' + _ffNum(wd * 2.6, 1, 0, 100, 1) + ';stroke-linecap:round;stroke-dasharray:0.0001 1;stroke-dashoffset:calc(-1*clamp(0,var(--p,1),1)*0.9999);"/>' : '')
    + nodes + '</svg>';
};

// Reveals its children through a shape that grows with p: a wobbly blob, a circle, a diagonal wipe, a rounded rectangle, or
// venetian bars. The blob and circle are 20-vertex polygons whose coordinates use CSS cos() and sin(), so they need no script.
var _MO_MASK_SHAPES = {blob: 1, circle: 1, diagonal: 1, rounded: 1, bars: 1};
var _MO_MASK_R = [84, 91, 82, 92, 85, 90, 81, 89, 86, 91, 83, 92, 80, 88, 84, 91, 82, 90, 86, 92];
_RENDERERS['motion_mask'] = function(b) {
  var shape = (typeof b.shape === 'string' && Object.prototype.hasOwnProperty.call(_MO_MASK_SHAPES, b.shape)) ? b.shape : 'blob';
  var blocks = Array.isArray(b.blocks) ? b.blocks.slice(0, 6) : [], inner = '', i, clip = '', mask = '';
  for (i = 0; i < blocks.length; i++) inner += _moChild(blocks[i]);
  if (shape === 'blob' || shape === 'circle') {
    var pts = [];
    for (i = 0; i < 20; i++) {
      var rr = shape === 'circle' ? 90 : _MO_MASK_R[i], ang = i * 18;
      pts.push('calc(50% + ' + rr + '% * var(--m) * cos(' + ang + 'deg)) calc(50% + ' + rr + '% * var(--m) * sin(' + ang + 'deg))');
    }
    clip = 'polygon(' + pts.join(',') + ')';
  } else if (shape === 'diagonal') clip = 'polygon(0 0,calc(var(--m)*140%) 0,calc(var(--m)*140% - 40%) 100%,0 100%)';
  else if (shape === 'rounded') clip = 'inset(calc((1 - var(--m))*50%) round calc((1 - var(--m))*80px))';
  else mask = 'repeating-linear-gradient(90deg,#000 0,#000 calc(var(--m)*10%),transparent calc(var(--m)*10%),transparent 10%)';
  return '<div style="--m:clamp(0,var(--p,1),1);position:relative;width:100%;height:100%;' + (clip ? 'clip-path:' + clip + ';-webkit-clip-path:' + clip + ';' : '') + (mask ? '-webkit-mask-image:' + mask + ';mask-image:' + mask + ';' : '') + '">' + inner + '</div>';
};

// ─── stitching: scenes that hand over to each other ─────────────────────────────────────────────────────────────────
// motion_timeline `scenes: [{layer, t|beat, transition?}]` turns a list of scene layers into the tracks that cross them, so a
// film is stitched by declaring where each scene starts instead of hand-writing four tracks per cut. The window between one
// scene's start and `overlap` seconds later is the hand-over: the old scene leaves while the new one arrives. Your own tracks
// on the same layer are applied after, and win.
var _MO_STITCH = {
  'cut': 1, 'dissolve': 1, 'push': 1, 'zoom-through': 1, 'blur': 1, 'rise': 1, 'whip': 1, 'wipe': 1, 'iris': 1, 'clock': 1, 'slice': 1, 'flip': 1, 'spin': 1, 'portal': 1, 'ribbon': 1, 'letter': 1
};
var _MO_STITCH_IN = {
  'letter': {clip: 0, cs: 9}, 'dissolve': {opacity: 0}, 'push': {opacity: 0, x: 8}, 'zoom-through': {opacity: 0, scale: 0.9, blur: 10}, 'blur': {opacity: 0, blur: 16}, 'rise': {opacity: 0, y: 6}, 'whip': {opacity: 0, x: 18, blur: 22}, 'wipe': {clip: 0}, 'iris': {clip: 0, cs: 1}, 'clock': {clip: 0, cs: 2}, 'slice': {clip: 0, cs: 3}, 'ribbon': {clip: 0, cs: 6}, 'flip': {opacity: 0, ry: -90}, 'spin': {opacity: 0, rotate: -14, scale: 0.8, blur: 6}
};
var _MO_STITCH_OUT = {
  'letter': {opacity: 0}, 'dissolve': {opacity: 0}, 'push': {opacity: 0, x: -8}, 'zoom-through': {opacity: 0, scale: 1.12, blur: 10}, 'blur': {opacity: 0, blur: 16}, 'rise': {opacity: 0, y: -6}, 'whip': {opacity: 0, x: -18, blur: 22}, 'wipe': {opacity: 0}, 'iris': {opacity: 0}, 'clock': {opacity: 0}, 'slice': {opacity: 0}, 'ribbon': {opacity: 0}, 'flip': {opacity: 0, ry: 90}, 'spin': {opacity: 0, rotate: 14, scale: 1.2, blur: 6}
};
var _MO_REST = {opacity: 1, x: 0, y: 0, scale: 1, blur: 0, clip: 1};
function _moAt(k, bpm, dur) {
  var t = null;
  if (typeof k.t === 'number' && isFinite(k.t)) t = k.t;
  else if (typeof k.beat === 'number' && isFinite(k.beat) && bpm) t = k.beat * 60 / bpm;
  return t === null ? null : Math.max(0, Math.min(dur, t));
}
function _moStitchKey(list, t, props, ease) {
  var k = {t: t}, p;
  for (p in props) k[p] = props[p];
  if (ease) k.ease = ease;
  list.push(k);
}
// Portal: the box in the old scene (stage percent, uniform scale so it keeps the stage's shape) that becomes the new scene.
function _moPortal(v) {
  if (!v || typeof v !== 'object' || typeof v.x !== 'number' || typeof v.y !== 'number' || typeof v.w !== 'number') return null;
  var w = parseFloat(_ffNum(v.w, 30, 17, 90, 2));
  return {x: parseFloat(_ffNum(v.x, 0, 0, 100, 2)) + w / 2, y: parseFloat(_ffNum(v.y, 0, 0, 100, 2)) + w / 2, w: w};
}
function _moStitch(b, ids, bpm, dur, st) {
  var src = Array.isArray(b.scenes) ? b.scenes : [], sc = [], i, own = Object.prototype.hasOwnProperty;
  if (src.length > 12) { st.dropped += src.length - 12; src = src.slice(0, 12); }
  for (i = 0; i < src.length; i++) {
    var s = src[i], id = s && typeof s === 'object' ? _moId(s.layer) : '', t = id && ids[id] ? _moAt(s, bpm, dur) : null;
    if (t === null) { st.dropped++; continue; }
    sc.push({id: id, t: t, i: i, fx: (typeof s.transition === 'string' && own.call(_MO_STITCH, s.transition)) ? s.transition : '', pb: _moPortal(s.portal), wd: _moStr(s.word, 12), wf: typeof s.word_font === 'string' ? s.word_font : ''});
  }
  sc.sort(function(a, c) { return a.t - c.t || a.i - c.i; });
  var dfx = (typeof b.stitch === 'string' && own.call(_MO_STITCH, b.stitch)) ? b.stitch : 'dissolve', ov = parseFloat(_ffNum(b.overlap, 0.6, 0, 3, 2)), out = [];
  for (i = 0; i < sc.length; i++) {
    var cur = sc[i], nxt = i + 1 < sc.length ? sc[i + 1] : null, keys = [], fin = cur.fx || dfx, fout = nxt ? (nxt.fx || dfx) : '', p, from;
    if (fin === 'portal' && !cur.pb) fin = 'dissolve';
    if (fin === 'ribbon' && cur.t > 0) { // an accent band rides the reveal edge (clip shape 5 straddles shape 6's edge)
      var rid = 'mrib' + i;
      if (ids[rid]) fin = 'wipe';
      else {
        st.rib = (st.rib || '') + '<div class="mt-el" data-mt-id="' + rid + '" data-mt-x="0" data-mt-y="0" aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:100%;z-index:50;opacity:0;pointer-events:none;background:linear-gradient(100deg,var(--mt-acc,#38bdf8),color-mix(in srgb,var(--mt-acc,#38bdf8) 50%,#ffffff));"></div>';
        var rj = _moTrackJs([{t: 0, opacity: 0, clip: 0, cs: 5}, {t: cur.t, opacity: 1, clip: 0, cs: 5, ease: 'hold'}, {t: cur.t + ov, opacity: 1, clip: 1, cs: 5, ease: 'expo-out'}, {t: cur.t + ov + 0.02, opacity: 0, ease: 'hold'}], _MO_PROPS, _MO_PROP_ORDER, dur, bpm, 'standard', st);
        out.push('{i:"' + rid + '",p:{' + rj + '}}');
      }
    }
    if (fin === 'letter' && !cur.wd) fin = 'iris';
    if (fin === 'letter' && cur.t > 0) { // the new scene is seen through a word that grows until a letter fills the frame (clip shape 9)
      var lzv = typeof _MO_VFONTS !== 'undefined' && own.call(_MO_VFONTS, cur.wf) ? cur.wf : '', lzStack = lzv ? _MO_VFONTS[lzv].stack : _ffPick(cur.wf, _FF_FONTS, 'display');
      var lzN = Math.max(1, Array.from(cur.wd).length), lzFs = Math.floor(Math.min(st.H * 0.62, st.W * 0.84 / (lzN * 0.6)));
      st.lz = (st.lz || '') + (lzv ? _moVfFace(lzv) : '') + '<svg aria-hidden="true" width="0" height="0" style="position:absolute;width:0;height:0;overflow:hidden;"><defs><clipPath id="mlz' + st.uid + '-' + cur.id + '" clipPathUnits="userSpaceOnUse"><text x="' + Math.floor(st.W / 2) + '" y="' + Math.floor(st.H / 2) + '" text-anchor="middle" dominant-baseline="central" font-family="' + lzStack + '" font-weight="900" font-size="' + lzFs + '">' + _esc(cur.wd) + '</text></clipPath></defs></svg>';
    }
    if (fout === 'portal' && !nxt.pb) fout = 'dissolve';
    if (cur.t > 0) {
      if (fin === 'cut') { _moStitchKey(keys, 0, {opacity: 0}); _moStitchKey(keys, cur.t, {opacity: 1}, 'hold'); }
      else if (fin === 'portal') { // the new scene starts as the box and grows to fill the frame, glued to the old scene's zoom
        var P = cur.pb, s0 = P.w / 100;
        _moStitchKey(keys, 0, {opacity: 0, x: P.x - 50, y: P.y - 50, scale: s0}); _moStitchKey(keys, cur.t, {opacity: 1, x: P.x - 50, y: P.y - 50, scale: s0}, 'hold');
        _moStitchKey(keys, cur.t + ov, {x: 0, y: 0, scale: 1}, 'quart-in-out');
      }
      else if (fin === 'letter') { // hidden until its start (clip 0 is the word at reading size, not nothing), then dives through the word
        _moStitchKey(keys, 0, {opacity: 0, clip: 0, cs: 9}); _moStitchKey(keys, cur.t, {opacity: 1, clip: 0, cs: 9}, 'hold'); _moStitchKey(keys, cur.t + Math.max(ov, 1.4), _MO_REST, 'linear');
      }
      else { from = _MO_STITCH_IN[fin]; _moStitchKey(keys, 0, from); _moStitchKey(keys, cur.t, from); _moStitchKey(keys, cur.t + ov, _MO_REST, 'expo-out'); }
    }
    if (nxt) {
      if (fout === 'cut') _moStitchKey(keys, nxt.t, {opacity: 0}, 'hold');
      else if (fout === 'portal') { // the old scene zooms so the box fills the frame, then hands over
        var Q = nxt.pb, kq = 100 / Q.w;
        _moStitchKey(keys, nxt.t, {opacity: 1, x: 0, y: 0, scale: 1}); _moStitchKey(keys, nxt.t + ov, {x: -(Q.x - 50) * kq, y: -(Q.y - 50) * kq, scale: kq}, 'quart-in-out');
        _moStitchKey(keys, nxt.t + ov + 0.02, {opacity: 0}, 'hold');
      }
      else if (fout === 'wipe' || fout === 'iris' || fout === 'clock' || fout === 'slice' || fout === 'ribbon' || fout === 'letter') { _moStitchKey(keys, nxt.t, _MO_REST); _moStitchKey(keys, nxt.t + (fout === 'letter' ? Math.max(ov, 1.4) : ov), {opacity: 0}, 'hold'); } // the old scene stays until the new one has covered it
      else { _moStitchKey(keys, nxt.t, _MO_REST); _moStitchKey(keys, nxt.t + ov, _MO_STITCH_OUT[fout], 'accelerate'); }
    }
    if (!keys.length) continue;
    var props = {};
    for (var q = 0; q < keys.length; q++) for (p in keys[q]) if (p !== 't' && p !== 'ease') props[p] = 1;
    // a rest key may carry props this scene never moves: keep only the props some transition really animates
    var live = {};
    for (p in props) { var seenVals = {}, cnt = 0; for (q = 0; q < keys.length; q++) if (own.call(keys[q], p) && !own.call(seenVals, keys[q][p])) { seenVals[keys[q][p]] = 1; cnt++; } if (cnt > 1) live[p] = 1; }
    if (live.clip) live.cs = 1; // the clip shape is constant but must ride with the clip
    var clean = [];
    for (q = 0; q < keys.length; q++) { var kk = {t: keys[q].t}; for (p in live) if (own.call(keys[q], p)) kk[p] = keys[q][p]; if (keys[q].ease) kk.ease = keys[q].ease; clean.push(kk); }
    var pjs = _moTrackJs(clean, _MO_PROPS, _MO_PROP_ORDER, dur, bpm, 'standard', st);
    if (pjs) out.push('{i:"' + cur.id + '",p:{' + pjs + '}}');
  }
  return out;
}

// ─── third reference (2026-10-01, a motion-design screencast): device frames, strike sweeps, rays, HUD, cell grids, 3D stacks, shake, flash ───
// Same contract as the rest: plain HTML+CSS driven by --p (build) and --s (second dial), no per-atom script, standalone it renders finished.
function _moOwn(t, v, d) { return (typeof v === 'string' && Object.prototype.hasOwnProperty.call(t, v)) ? v : d; }
var _MO_DEVICE = {phone: 1, laptop: 1, tablet: 1};
var _MO_DECOR = {strike: 1, highlight: 1, underline: 1};
var _MO_KARA = {pill: 1, color: 1};
var _MO_RAYS = {burst: 1, speed: 1};
var _MO_CELLS = {pop: 1, flip: 1, fill: 1};
var _MO_STACK = {ring: 1, stack: 1};

// A phone, tablet or laptop bezel with children inside its screen; --s scrolls the content up by `scroll` px.
_RENDERERS['motion_device'] = function(b) {
  var kind = _moOwn(_MO_DEVICE, b.kind, 'phone'), w = _ffInt(b.width, kind === 'laptop' ? 520 : (kind === 'tablet' ? 380 : 240), 120, 900);
  var scroll = _ffInt(b.scroll, 0, 0, 2000), fill = _moInk(b, 'fill', '#0b0f19'), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), label = _moStr(b.label, 40) || 'Device screen';
  var blocks = Array.isArray(b.blocks) ? b.blocks.slice(0, 6) : [], inner = '', i;
  for (i = 0; i < blocks.length; i++) inner += _moChild(blocks[i]);
  var bz = Math.max(4, Math.floor(w * (kind === 'laptop' ? 0.022 : 0.032))), rad = Math.floor(w * (kind === 'phone' ? 0.13 : (kind === 'tablet' ? 0.06 : 0.03)));
  var asp = kind === 'phone' ? '9/19' : (kind === 'tablet' ? '3/4' : '16/10');
  var notch = kind === 'phone' ? '<div aria-hidden="true" style="position:absolute;top:' + Math.floor(bz * 0.6) + 'px;left:50%;width:28%;height:' + (bz * 2) + 'px;border-radius:999px;background:' + fill + ';transform:translateX(-50%);z-index:2;"></div>' : '';
  var base = kind === 'laptop' ? '<div aria-hidden="true" style="height:' + Math.max(6, Math.floor(w * 0.03)) + 'px;margin:0 -4%;border-radius:0 0 ' + Math.floor(w * 0.03) + 'px ' + Math.floor(w * 0.03) + 'px;background:linear-gradient(#cfd5de,#9aa3b2);"></div>' : '';
  return '<div role="group" aria-label="' + _esc(label) + '" style="width:' + w + 'px;max-width:100%;opacity:clamp(0,calc(var(--p,1)*4),1);transform:translateY(calc((1 - clamp(0,var(--p,1),1))*8%)) scale(calc(0.94 + 0.06*clamp(0,var(--p,1),1)));">'
    + '<div style="position:relative;box-sizing:border-box;width:100%;aspect-ratio:' + asp + ';border:' + bz + 'px solid ' + fill + ';border-radius:' + rad + 'px;background:' + fill + ';outline:1px solid color-mix(in srgb,' + acc + ' 45%,transparent);box-shadow:0 24px 60px rgba(0,0,0,0.35);">'
    + notch + '<div style="position:relative;width:100%;height:100%;overflow:hidden;border-radius:' + Math.max(2, rad - bz) + 'px;background:var(--mt-bg,#0f1420);color:var(--mt-ink,#f1f5f9);">'
    + '<div style="transform:translateY(calc(var(--s,0)*-' + scroll + 'px));">' + inner + '</div></div></div>' + base + '</div>';
};


// A sunburst that fans out behind a hero (burst), or streaks that sweep across the frame (speed). --s turns or slides it.
_RENDERERS['motion_rays'] = function(b) {
  var kind = _moOwn(_MO_RAYS, b.kind, 'burst'), n = _ffInt(b.count, 24, 4, 64), th = parseFloat(_ffNum(b.thickness, 0.5, 0.1, 0.9, 2)), spin = _ffInt(b.spin, 45, -360, 360);
  var acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), st = _ffNum(b.strength, 0.35, 0.05, 1, 2), seg = _ffNum(360 / n, 15, 0.1, 90, 3), ray = _ffNum(360 / n * th, 7, 0.05, 90, 3);
  var fade = 'clamp(0,calc(var(--p,1)*3),1)';
  if (kind === 'speed') {
    var lines = 'repeating-linear-gradient(0deg,' + acc + ' 0,' + acc + ' ' + _ffNum(100 / n * th, 1, 0.05, 50, 3) + '%,transparent ' + _ffNum(100 / n * th, 1, 0.05, 50, 3) + '%,transparent ' + _ffNum(100 / n, 4, 0.1, 50, 3) + '%)';
    var mk = 'linear-gradient(90deg,transparent 0,#000 30%,#000 60%,transparent 100%)';
    return '<div aria-hidden="true" style="width:100%;aspect-ratio:16/9;background:' + lines + ';-webkit-mask-image:' + mk + ';mask-image:' + mk + ';-webkit-mask-size:50% 100%;mask-size:50% 100%;-webkit-mask-repeat:repeat-x;mask-repeat:repeat-x;-webkit-mask-position:calc(var(--s,0)*-50%) 0;mask-position:calc(var(--s,0)*-50%) 0;opacity:calc(' + fade + '*' + st + ');"></div>';
  }
  var mr = 'radial-gradient(circle,#000 0%,transparent 70%)';
  return '<div aria-hidden="true" style="width:100%;aspect-ratio:1/1;background:repeating-conic-gradient(from calc(var(--s,0)*' + spin + 'deg),' + acc + ' 0deg,' + acc + ' ' + ray + 'deg,transparent ' + ray + 'deg,transparent ' + seg + 'deg);-webkit-mask-image:' + mr + ';mask-image:' + mr
    + ';opacity:calc(' + fade + '*' + st + ');transform:scale(calc(0.6 + 0.4*clamp(0,var(--p,1),1)));"></div>';
};

// A heads-up display: corner brackets, a timecode that counts up, a label and a progress bar. Fills its placed box.
_RENDERERS['motion_hud'] = function(b) {
  var secs = _ffInt(b.seconds, 10, 1, 3600), size = _ffInt(b.size, 14, 8, 60), label = _moStr(b.label, 30), corners = b.corners !== false, bar = b.bar !== false;
  var acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), color = _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), mono = _ffPick('mono', _FF_FONTS, 'mono'), html = '', i;
  var cs = [['top:0.6em;left:0.6em;', 'border-top:2px solid ' + acc + ';border-left:2px solid ' + acc + ';'], ['top:0.6em;right:0.6em;', 'border-top:2px solid ' + acc + ';border-right:2px solid ' + acc + ';'],
            ['bottom:0.6em;left:0.6em;', 'border-bottom:2px solid ' + acc + ';border-left:2px solid ' + acc + ';'], ['bottom:0.6em;right:0.6em;', 'border-bottom:2px solid ' + acc + ';border-right:2px solid ' + acc + ';']];
  if (corners) for (i = 0; i < 4; i++) html += '<span aria-hidden="true" style="position:absolute;' + cs[i][0] + 'width:1.6em;height:1.6em;' + cs[i][1] + '"></span>';
  html += '<span aria-hidden="true" style="position:absolute;top:1.1em;left:2.6em;">' + _moCount(secs, 2, '', 's', '', 0) + '</span>'
    + (label ? '<span style="position:absolute;top:1.1em;right:2.6em;letter-spacing:0.14em;text-transform:uppercase;color:' + acc + ';">' + _esc(label) + '</span>' : '');
  if (bar) html += '<span aria-hidden="true" style="position:absolute;left:2.6em;right:2.6em;bottom:1.1em;height:0.2em;background:' + _MO_MIX_LINE + ';"><span style="display:block;height:100%;width:calc(100%*clamp(0,var(--p,1),1));background:' + acc + ';"></span></span>';
  return '<div style="position:relative;width:100%;height:100%;min-height:5em;box-sizing:border-box;font-family:' + mono + ';font-size:' + size + 'px;font-variant-numeric:tabular-nums;color:' + color + ';opacity:clamp(0,calc(var(--p,1)*6),1);">' + html + '</div>';
};

// A grid of cells that pop, flip or fill in a diagonal wave, optionally a chessboard, optionally numbered 1, 2, 4, 8...
_RENDERERS['motion_cells'] = function(b) {
  var cols = _ffInt(b.columns, 6, 2, 12), rows = _ffInt(b.rows, 4, 1, 8), mode = _moOwn(_MO_CELLS, b.mode, 'pop'), gap = _ffInt(b.gap, 4, 0, 24), rad = _ffInt(b.radius, 6, 0, 40), size = _ffInt(b.size, 18, 8, 80);
  var a1 = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), a2 = _moInk(b, 'accent2', _MO_MIX_FILL), chess = b.chess !== false, nums = b.numbers === true, T = cols + rows + 1, r, c, out = '';
  for (r = 0; r < rows; r++) for (c = 0; c < cols; c++) {
    var idx = r * cols + c, col = (chess && (r + c) % 2) ? a2 : a1, tf = mode === 'flip' ? 'perspective(400px) rotateY(calc((1 - var(--u))*90deg))' : 'scale(var(--u))';
    var bg = mode === 'fill' ? 'color-mix(in srgb,' + col + ' calc(var(--u)*100%),transparent)' : col;
    out += '<div style="--u:clamp(0,calc(var(--p,1)*' + T + ' - ' + (r + c) + '),1);aspect-ratio:1/1;display:flex;align-items:center;justify-content:center;border-radius:' + rad + 'px;background:' + bg + ';' + (mode === 'fill' ? '' : 'transform:' + tf + ';opacity:var(--u);')
      + 'color:var(--mt-ink,#f1f5f9);font-weight:700;">' + (nums && idx < 13 ? _esc('' + Math.pow(2, idx)) : '') + '</div>';
  }
  return '<div aria-hidden="true" style="display:grid;grid-template-columns:repeat(' + cols + ',minmax(0,1fr));gap:' + gap + 'px;width:100%;font-family:' + _MO_SANS + ';font-size:' + size + 'px;">' + out + '</div>';
};

// Cards in 3D: a ring that turns (--s is the turn) or an isometric stack that fans apart (--s is the spread).
_RENDERERS['motion_stack3d'] = function(b) {
  var mode = _moOwn(_MO_STACK, b.mode, 'ring'), w = _ffInt(b.w, 220, 80, 600), h = _ffInt(b.h, 140, 60, 500), size = _ffInt(b.size, 18, 8, 60);
  var acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), fill = _moInk(b, 'fill', 'color-mix(in srgb,var(--mt-bg,#0f1420) 90%,var(--mt-ink,#f1f5f9))');
  var src = Array.isArray(b.items) ? b.items : [], items = [], i;
  for (i = 0; i < src.length && items.length < 6; i++) {
    var it = src[i], obj = it && typeof it === 'object', t = _moStr(typeof it === 'string' ? it : (obj ? it.title : ''), 30);
    if (t) items.push({t: t, x: obj ? _moStr(it.text, 60) : '', i: obj ? _moStr(it.icon, 2) : ''});
  }
  if (!items.length) items = [{t: 'Card', x: '', i: ''}];
  var n = items.length, nn = Math.max(n, 3), rr = Math.max(Math.floor(w * 0.5 / Math.tan(Math.PI / nn) + 0.5), Math.floor(w * 0.6 + 0.5)), cards = '', names = [];
  for (i = 0; i < n; i++) {
    var tf = mode === 'ring' ? 'rotateY(' + Math.floor(360 * i / n + 0.5) + 'deg) translateZ(' + rr + 'px) scale(calc(0.6 + 0.4*var(--u)))' : 'translateZ(calc(' + i + '*(16px + var(--s,0)*60px)))';
    cards += '<div style="--u:clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1);position:absolute;left:0;top:0;width:' + w + 'px;height:' + h + 'px;box-sizing:border-box;padding:0.8em;border-radius:0.8em;background:' + fill + ';border:1px solid ' + _MO_MIX_LINE + ';box-shadow:inset 0 3px 0 ' + acc + ';opacity:var(--u);'
      + (mode === 'ring' ? 'backface-visibility:hidden;-webkit-backface-visibility:hidden;' : '') + 'transform:' + tf + ';color:var(--mt-ink,#f1f5f9);font-family:' + _MO_SANS + ';font-size:' + size + 'px;">'
      + (items[i].i ? '<div aria-hidden="true" style="font-size:1.4em;">' + _esc(items[i].i) + '</div>' : '') + '<div style="font-weight:700;">' + _esc(items[i].t) + '</div>'
      + (items[i].x ? '<div style="font-size:0.8em;color:var(--mt-mute,#94a3b8);margin-top:0.3em;">' + _esc(items[i].x) + '</div>' : '') + '</div>';
    names.push(items[i].t);
  }
  var stage = mode === 'ring' ? 'transform:translateZ(-' + rr + 'px) rotateY(calc(var(--s,0)*-360deg));' : 'transform:rotateX(55deg) rotateZ(-30deg);margin-top:' + Math.floor(h * 0.5) + 'px;';
  return '<div role="group" aria-label="' + _esc(names.join(', ')) + '" style="width:100%;height:' + Math.floor(h * (mode === 'stack' ? 2 : 1.15)) + 'px;perspective:1400px;">'
    + '<div style="position:relative;width:' + w + 'px;height:' + h + 'px;margin-left:auto;margin-right:auto;transform-style:preserve-3d;' + stage + '">' + cards + '</div></div>';
};

// Camera shake: its children jolt and settle as p goes 0 to 1 (set p to 0 at the impact), at rest by p = 1.
_RENDERERS['motion_shake'] = function(b) {
  var amp = _ffInt(b.amount, 12, 1, 80), freq = _ffInt(b.frequency, 9, 1, 40), tilt = _ffNum(b.tilt, 1.5, 0, 10, 1), blocks = Array.isArray(b.blocks) ? b.blocks.slice(0, 12) : [], inner = '', i, st = {dropped: 0}, seen = {}, ids = {};
  for (i = 0; i < blocks.length; i++) { var w = _moPlaced(blocks[i], seen, ids, st); if (w !== null) inner += w; }
  var tf = 'translate(calc(var(--k)*' + amp + 'px*sin(calc(var(--p,1)*' + freq + '*6.2832))),calc(var(--k)*' + Math.floor(amp * 0.6 + 0.5) + 'px*cos(calc(var(--p,1)*' + freq + '*8.1 + 1)))) rotate(calc(var(--k)*' + tilt + 'deg*sin(calc(var(--p,1)*' + freq + '*5.3))))';
  return '<div style="--k:clamp(0,calc(1 - var(--p,1)),1);position:absolute;left:0;top:0;width:100%;height:100%;transform:' + tf + ';">' + inner + '</div>';
};

// A full-frame flash: a hard white (or tinted) pop that fades out, the hit on a beat. Invisible at p = 1.
_RENDERERS['motion_flash'] = function(b) {
  var col = _moInk(b, 'color', '#ffffff'), st = _ffNum(b.strength, 0.8, 0.1, 1, 2);
  return '<div aria-hidden="true" style="width:100%;height:100%;pointer-events:none;background:' + col + ';opacity:calc(clamp(0,calc(var(--p,1)*10),1)*(1 - clamp(0,var(--p,1),1))*' + st + ');"></div>';
};

// ─── fourth reference batch (2026-10-01, five LinkedIn/YouTube motion pieces): marquee rows, glitch type, bounce, scatter, contours, rail ───
var _MO_SCATTER = [[8, 14, -9], [52, 6, 6], [24, 46, 11], [62, 40, -7], [10, 70, 5], [46, 72, -12], [74, 66, 8], [34, 22, -4]];
var _MO_WAVE = [14, -22, 30, -10, 24, -30, 8, -18];

// Rows of big text that slide sideways forever (--s is the travel), alternate rows going opposite ways: the ticker behind a headline.
_RENDERERS['motion_marquee'] = function(b) {
  var src = Array.isArray(b.rows) ? b.rows : [], rows = [], i;
  for (i = 0; i < src.length && rows.length < 5; i++) { var t = _moStr(src[i], 80); if (t) rows.push(t); }
  if (!rows.length) rows = ['MARQUEE'];
  var size = _ffInt(b.size, 40, 10, 200), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), color = _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), gap = 0.8, out = '';
  var weight = _ffPick(b.weight, _FF_WEIGHTS, 'black');
  for (i = 0; i < rows.length; i++) {
    var unit = '<span style="padding-right:1.2em;">' + _esc(rows[i]) + ' &middot; </span>', dir = i % 2 ? 1 : -1, hi = i === 1 ? acc : color;
    out += '<div style="overflow:hidden;white-space:nowrap;opacity:calc(clamp(0,calc(var(--p,1)*' + (rows.length + 1) + ' - ' + i + '),1)*' + (i % 2 ? '0.55' : '1') + ');margin-top:' + gap + 'em;">'
      + '<div style="display:inline-block;color:' + hi + ';transform:translateX(calc(var(--s,0)*' + (dir * 50) + '%' + (dir > 0 ? ' - 50%' : '') + '));">' + unit + unit + unit + unit + '</div></div>';
  }
  return '<div role="img" aria-label="' + _esc(rows.join(', ')) + '" style="width:100%;font-family:' + _MO_SANS + ';font-size:' + size + 'px;font-weight:' + weight + ';letter-spacing:0.04em;line-height:1;text-transform:uppercase;">' + out + '</div>';
};


// A ball that bounces across the box as p goes 0..1, squashing as it lands and stretching in the air, with a dotted trail.
_RENDERERS['motion_bounce'] = function(b) {
  var n = _ffInt(b.bounces, 3, 1, 8), size = _ffInt(b.size, 60, 8, 300), h = _ffInt(b.height, 260, 40, 800), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), trail = b.trail !== false, k, dots = '';
  function ph(d) { return '(clamp(0,calc(var(--p,1) - ' + d + '),1)*' + n + '*3.14159)'; }
  function pos(d) { return 'left:calc(clamp(0,calc(var(--p,1) - ' + d + '),1)*(100% - ' + size + 'px));top:calc(' + h + 'px - ' + size + 'px - abs(sin(' + ph(d) + '))*(' + h + 'px - ' + size + 'px)*(1 - clamp(0,calc(var(--p,1) - ' + d + '),1)*0.6));'; }
  if (trail) for (k = 1; k <= 8; k++) dots += '<div style="position:absolute;width:' + Math.max(3, Math.floor(size / 6)) + 'px;height:' + Math.max(3, Math.floor(size / 6)) + 'px;margin:' + Math.floor(size / 2) + 'px 0 0 ' + Math.floor(size / 2) + 'px;border-radius:50%;background:' + acc + ';opacity:' + _ffNum(0.5 - k * 0.05, 0, 0, 1, 2) + ';' + pos(_ffNum(k * 0.012, 0, 0, 1, 3)) + '"></div>';
  var sq = 'abs(cos(' + ph(0) + '))';
  return '<div role="img" aria-label="A bouncing ball" style="position:relative;width:100%;height:' + h + 'px;">' + dots
    + '<div aria-hidden="true" style="position:absolute;width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:' + acc + ';transform-origin:50% 100%;transform:scale(calc(1 + ' + sq + '*' + sq + '*' + sq + '*0.35),calc(1 - ' + sq + '*' + sq + '*' + sq + '*0.4));' + pos(0) + '"></div>'
    + '<div aria-hidden="true" style="position:absolute;left:0;right:0;bottom:0;height:2px;background:' + _MO_MIX_LINE + ';"></div></div>';
};

// Cards that fly in from outside the frame and settle at scattered, tilted rest positions: the pile of tickets, labels or notes.
_RENDERERS['motion_scatter'] = function(b) {
  var src = Array.isArray(b.items) ? b.items : [], items = [], i;
  for (i = 0; i < src.length && items.length < 8; i++) { var it = src[i], obj = it && typeof it === 'object', t = _moStr(typeof it === 'string' ? it : (obj ? it.title : ''), 30); if (t) items.push({t: t, x: obj ? _moStr(it.text, 50) : ''}); }
  if (!items.length) items = [{t: 'Card', x: ''}];
  var size = _ffInt(b.size, 18, 8, 60), w = _ffInt(b.card_w, 24, 10, 50), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), fill = _moInk(b, 'fill', '#ffffff'), ink = _moInk(b, 'color', '#14161c'), out = '';
  for (i = 0; i < items.length; i++) {
    var P = _MO_SCATTER[i], dx = (i % 2 ? 1 : -1) * (60 + i * 7), dy = -40 - i * 5;
    out += '<div style="--u:clamp(0,calc(var(--p,1)*' + (items.length + 2) + ' - ' + i + '),1);position:absolute;left:' + P[0] + '%;top:' + P[1] + '%;width:' + w + '%;box-sizing:border-box;padding:0.7em 0.9em;border-radius:0.5em;background:' + fill + ';color:' + ink + ';border-top:0.25em solid ' + acc
      + ';box-shadow:0 10px 26px rgba(0,0,0,0.3);opacity:var(--u);transform:translate(calc((1 - var(--u))*' + dx + '%),calc((1 - var(--u))*' + dy + '%)) rotate(calc(' + P[2] + 'deg + (1 - var(--u))*' + (P[2] * 6) + 'deg));">'
      + '<div style="font-weight:800;">' + _esc(items[i].t) + '</div>' + (items[i].x ? '<div style="font-size:0.8em;opacity:0.7;margin-top:0.25em;">' + _esc(items[i].x) + '</div>' : '') + '</div>';
  }
  return '<div style="position:relative;width:100%;height:100%;min-height:12em;font-family:' + _MO_SANS + ';font-size:' + size + 'px;">' + out + '</div>';
};

// Flowing contour lines that draw themselves and drift (--s slides them sideways), like a topographic or wind-map background.
_RENDERERS['motion_contours'] = function(b) {
  var n = _ffInt(b.lines, 12, 3, 30), wd = _ffInt(b.width, 2, 1, 12), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), acc2 = _moInk(b, 'accent2', ''), W = 1000, H = 600, i, out = '';
  for (i = 0; i < n; i++) {
    var y = Math.floor((i + 0.5) * H / n), a = _MO_WAVE[i % 8] * 2, a2 = _MO_WAVE[(i * 3 + 1) % 8] * 2, col = acc2 && i % 3 === 0 ? acc2 : acc;
    var d = 'M-200 ' + y + ' C 0 ' + (y + a) + ' 200 ' + (y - a) + ' 400 ' + y + ' S 800 ' + (y + a2) + ' 1000 ' + y + ' S 1400 ' + (y - a2) + ' 1600 ' + y + ' S 2000 ' + (y + a) + ' 2200 ' + y;
    out += '<path d="' + d + '" pathLength="1" style="--u:clamp(0,calc(var(--p,1)*' + (n + 3) + ' - ' + _ffNum(i * 0.6, 0, 0, 100, 1) + '),1);fill:none;stroke:' + col + ';stroke-width:' + wd + ';stroke-dasharray:1;stroke-dashoffset:calc(1 - var(--u));opacity:' + _ffNum(0.35 + (i % 4) * 0.15, 0, 0, 1, 2) + ';"/>';
  }
  return '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" preserveAspectRatio="xMidYMid slice" aria-hidden="true" style="display:block;overflow:hidden;"><g style="transform:translateX(calc(var(--s,0)*-800px));">' + out + '</g></svg>';
};

// A progress rail with labelled stops: the line fills as p goes 0..1 and each label lights when the fill reaches it.
_RENDERERS['motion_rail'] = function(b) {
  var src = Array.isArray(b.steps) ? b.steps : [], st = [], i;
  for (i = 0; i < src.length && st.length < 6; i++) { var t = _moStr(src[i], 24); if (t) st.push(t); }
  if (st.length < 2) st = ['Start', 'Finish'];
  var n = st.length, size = _ffInt(b.size, 16, 8, 60), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), out = '';
  for (i = 0; i < n; i++) {
    var x = _ffNum(Math.floor(i * 1000 / (n - 1)) / 10, 0, 0, 100, 1);
    out += '<div style="--u:clamp(0,calc(var(--p,1)*' + (n - 1) + ' - ' + _ffNum(i - 0.0001, 0, -1, 10, 4) + ' ),1);position:absolute;left:' + x + '%;top:0;transform:translateX(-50%);text-align:center;">'
      + '<div style="width:0.9em;height:0.9em;margin:0 auto;border-radius:50%;box-sizing:border-box;border:2px solid ' + acc + ';background:color-mix(in srgb,' + acc + ' calc(var(--u)*100%),transparent);"></div>'
      + '<div style="margin-top:0.7em;white-space:nowrap;font-weight:700;opacity:calc(0.4 + 0.6*var(--u));">' + _esc(st[i]) + '</div></div>';
  }
  return '<div style="position:relative;width:100%;padding:0 4em;box-sizing:border-box;font-family:' + _MO_SANS + ';font-size:' + size + 'px;color:var(--mt-ink,#f1f5f9);height:4.4em;">'
    + '<div style="position:absolute;left:4em;right:4em;top:0;height:0;"><div style="position:absolute;left:0;right:0;top:0.4em;height:2px;background:' + _MO_MIX_LINE + ';"></div>'
    + '<div style="position:absolute;left:0;top:0.4em;height:2px;width:calc(100%*clamp(0,var(--p,1),1));background:' + acc + ';"></div>' + out + '</div></div>';
};

// ─── batch 5 (2026-10-02, from the motion-mechanics sweep): image moves, charts that draw, captions, lower third, waveform, repeater ───
// https images, site-relative paths and data:image only; anything else falls back to a gradient placeholder.
var _MO_IMG_OK = /^(https:\/\/[^\s"'<>\\`]{1,500}|\/(?!\/)[^\s"'<>\\`]{0,500}|data:image\/(png|jpe?g|gif|webp|avif);base64,[A-Za-z0-9+\/=]{1,200000})$/;
function _moImg(v) { return (typeof v === 'string' && _MO_IMG_OK.test(v.trim())) ? v.trim() : ''; }
var _MO_RATIO = {'16:9': '16/9', '4:3': '4/3', '1:1': '1/1', '3:4': '3/4', '9:16': '9/16'};
var _MO_IMG_MODE = {kenburns: 1, parallax: 1, polaroid: 1};

// An image that moves: a slow pan and zoom (kenburns), stacked layers that slide at different speeds with --s (parallax), or a
// polaroid that drops in tilted with a caption.
_RENDERERS['motion_image'] = function(b) {
  var mode = _moOwn(_MO_IMG_MODE, b.mode, 'kenburns'), ratio = _ffPick(b.ratio, _MO_RATIO, '16:9'), rad = _ffInt(b.radius, 12, 0, 60), alt = _moStr(b.alt, 80) || 'Image', cap = _moStr(b.caption, 60);
  var zoom = _ffNum(b.zoom, 1.15, 1, 2, 2), px = _ffInt(b.pan_x, -3, -20, 20), py = _ffInt(b.pan_y, -2, -20, 20), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), url = _moImg(b.url);
  function pic(u, extra) {
    return u ? '<img src="' + _esc(u) + '" alt="" loading="lazy" referrerpolicy="no-referrer" style="position:absolute;left:-12%;top:-12%;width:124%;height:124%;object-fit:cover;' + extra + '">'
      : '<div aria-hidden="true" style="position:absolute;left:-12%;top:-12%;width:124%;height:124%;background:linear-gradient(135deg,' + acc + ',color-mix(in srgb,' + acc + ' 25%,#0b0712));' + extra + '"></div>';
  }
  var inner = '';
  if (mode === 'parallax') {
    var src = Array.isArray(b.layers) ? b.layers : [], i, n = 0;
    for (i = 0; i < src.length && n < 4; i++) {
      var l = src[i], u = l && typeof l === 'object' ? _moImg(l.url) : '', d = l && typeof l === 'object' ? _ffNum(l.depth, 0.5, 0, 1, 2) : '0.5';
      if (!u && !(l && typeof l === 'object')) continue;
      inner += pic(u, 'transform:translateX(calc(var(--s,0)*' + _ffNum(parseFloat(d) * 14, 0, 0, 14, 2) + '%));');
      n++;
    }
    if (!n) inner = pic(url, 'transform:translateX(calc(var(--s,0)*7%));');
  } else {
    inner = pic(url, 'transform:translate(calc(var(--p,1)*' + px + '%),calc(var(--p,1)*' + py + '%)) scale(calc(1 + var(--p,1)*' + _ffNum(zoom - 1, 0.15, 0, 1, 2) + '));');
  }
  var frame = '<div style="position:relative;overflow:hidden;aspect-ratio:' + ratio + ';border-radius:' + rad + 'px;width:100%;background:#0b0712;">' + inner + '</div>';
  if (mode === 'polaroid') {
    return '<div role="img" aria-label="' + _esc(alt) + '" style="width:100%;box-sizing:border-box;padding:4% 4% 0;background:#fff;border-radius:4px;box-shadow:0 18px 40px rgba(0,0,0,0.4);opacity:clamp(0,calc(var(--p,1)*5),1);transform:translateY(calc((1 - clamp(0,var(--p,1),1))*-30%)) rotate(calc(-6deg + clamp(0,var(--p,1),1)*3deg));">'
      + '<div style="position:relative;overflow:hidden;aspect-ratio:' + (ratio === '16/9' ? '1/1' : ratio) + ';background:#0b0712;">' + pic(url, '') + '</div>'
      + '<div style="padding:0.9em 0 1.1em;text-align:center;font-family:' + _MO_SANS + ';font-weight:700;color:#14161c;font-size:1.1em;min-height:1.4em;">' + _esc(cap) + '</div></div>';
  }
  return '<div role="img" aria-label="' + _esc(alt) + '" style="width:100%;">' + frame + (cap ? '<div style="margin-top:0.6em;font-family:' + _MO_SANS + ';font-size:0.9em;color:var(--mt-mute,#94a3b8);">' + _esc(cap) + '</div>' : '') + '</div>';
};

// Data that draws itself: bars that grow, a line that draws with its points, or a donut that fills segment by segment.
var _MO_CHART = {bars: 1, line: 1, donut: 1};
_RENDERERS['motion_chart'] = function(b) {
  var kind = _moOwn(_MO_CHART, b.kind, 'bars'), src = Array.isArray(b.data) ? b.data : [], pts = [], i;
  for (i = 0; i < src.length && pts.length < 8; i++) {
    var it = src[i], obj = it && typeof it === 'object', v = obj ? it.value : it;
    if (typeof v !== 'number' || !isFinite(v) || v < 0) continue;
    pts.push({v: Math.min(v, 1e9), l: obj ? _moStr(it.label, 14) : ''});
  }
  if (!pts.length) pts = [{v: 40, l: 'A'}, {v: 70, l: 'B'}, {v: 55, l: 'C'}];
  var n = pts.length, mx = 0, tot = 0, size = _ffInt(b.size, 18, 8, 60), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), acc2 = _moInk(b, 'accent2', ''), unit = _moStr(b.unit, 6), title = _moStr(b.title, 40);
  for (i = 0; i < n; i++) { mx = Math.max(mx, pts[i].v); tot += pts[i].v; }
  if (mx <= 0) mx = 1;
  if (tot <= 0) tot = 1;
  var body = '', lab = _moStr(b.label, 80) || title || 'Chart';
  if (kind === 'bars') {
    for (i = 0; i < n; i++) {
      var h = _ffNum(pts[i].v / mx * 100, 0, 0, 100, 1), col = acc2 && i % 2 ? acc2 : acc;
      body += '<div style="--u:clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1);flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;min-width:0;height:100%;">'
        + '<div style="margin-bottom:0.3em;font-weight:700;opacity:var(--u);">' + _esc(_moFmt(pts[i].v, 0, '', unit)) + '</div>'
        + '<div style="width:70%;height:calc(' + h + '%*var(--u)*0.8);background:' + col + ';border-radius:0.3em 0.3em 0 0;"></div>'
        + '<div style="margin-top:0.5em;font-size:0.8em;color:var(--mt-mute,#94a3b8);white-space:nowrap;">' + _esc(pts[i].l) + '</div></div>';
    }
    body = '<div style="display:flex;align-items:flex-end;gap:2%;height:' + _ffInt(b.height, 260, 80, 800) + 'px;padding-top:1.5em;border-bottom:2px solid ' + _MO_MIX_LINE + ';">' + body + '</div>';
  } else if (kind === 'line') {
    var W = 400, H = 200, d = '', area = '', dots = '';
    for (i = 0; i < n; i++) {
      var x = n > 1 ? Math.floor(i * W * 10 / (n - 1)) / 10 : W / 2, y = _ffNum(H - 10 - pts[i].v / mx * (H - 30), 0, 0, H, 1);
      d += (i ? ' L ' : 'M ') + _ffNum(x, 0, 0, W, 1) + ' ' + y;
      dots += '<circle cx="' + _ffNum(x, 0, 0, W, 1) + '" cy="' + y + '" r="5" style="fill:' + acc + ';transform-box:fill-box;transform-origin:center;transform:scale(clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1));"/>';
    }
    area = d + ' L ' + _ffNum(n > 1 ? W : W / 2, 0, 0, W, 1) + ' ' + H + ' L ' + _ffNum(n > 1 ? 0 : W / 2, 0, 0, W, 1) + ' ' + H + ' Z';
    body = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" aria-hidden="true" style="display:block;overflow:visible;">'
      + '<path d="' + area + '" style="fill:' + acc + ';opacity:calc(0.18*clamp(0,calc(var(--p,1) - 0.5)*2,1));"/>'
      + '<path d="' + d + '" pathLength="1" style="fill:none;stroke:' + acc + ';stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:calc(1 - clamp(0,var(--p,1),1));"/>' + dots + '</svg>';
  } else {
    var cum = 0, segs = '', cols = [acc, acc2 || 'color-mix(in srgb,' + acc + ' 55%,#fff)', 'color-mix(in srgb,' + acc + ' 35%,#0b0712)', 'color-mix(in srgb,' + acc + ' 70%,#ff3d81)'];
    for (i = 0; i < n; i++) {
      var share = pts[i].v / tot, c0 = _ffNum(cum, 0, 0, 1, 4), sh = _ffNum(share, 0, 0, 1, 4);
      segs += '<circle cx="60" cy="60" r="44" pathLength="1" style="fill:none;stroke:' + cols[i % 4] + ';stroke-width:16;stroke-dasharray:calc(clamp(0,calc(var(--p,1) - ' + c0 + '),' + sh + ')) 1;stroke-dashoffset:-' + c0 + ';transform:rotate(-90deg);transform-origin:60px 60px;"/>';
      cum += share;
    }
    body = '<svg viewBox="0 0 120 120" width="' + _ffInt(b.height, 260, 80, 800) + '" aria-hidden="true" style="display:block;margin:0 auto;max-width:100%;">' + segs
      + '<text x="60" y="60" text-anchor="middle" dominant-baseline="central" style="font-family:' + _MO_SANS + ';font-size:16px;font-weight:800;fill:var(--mt-ink,#f1f5f9);">' + _esc(_moFmt(tot, 0, '', unit)) + '</text></svg>';
  }
  return '<div role="img" aria-label="' + _esc(lab) + '" style="width:100%;font-family:' + _MO_SANS + ';font-size:' + size + 'px;color:var(--mt-ink,#f1f5f9);">'
    + (title ? '<div style="font-weight:800;margin-bottom:0.4em;">' + _esc(title) + '</div>' : '') + body + '</div>';
};


// Lower third: an accent bar draws, the name slides out of it, the role fades in under it.
_RENDERERS['motion_lower_third'] = function(b) {
  var name = _moStr(b.name, 40) || 'Name', role = _moStr(b.role, 60), size = _ffInt(b.size, 36, 10, 120), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), color = _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), fill = _moInk(b, 'fill', '#0b0712');
  return '<div style="display:flex;align-items:stretch;font-family:' + _MO_SANS + ';font-size:' + size + 'px;">'
    + '<div aria-hidden="true" style="width:0.18em;background:' + acc + ';transform-origin:50% 100%;transform:scaleY(clamp(0,calc(var(--p,1)*4),1));"></div>'
    + '<div style="overflow:hidden;padding:0.25em 0.8em 0.3em 0.6em;background:color-mix(in srgb,' + fill + ' 82%,transparent);clip-path:inset(0 calc((1 - clamp(0,calc(var(--p,1)*2.2 - 0.2),1))*100%) 0 0);">'
    + '<div style="font-weight:800;line-height:1.1;color:' + color + ';white-space:nowrap;">' + _esc(name) + '</div>'
    + (role ? '<div style="margin-top:0.15em;font-size:0.55em;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:' + acc + ';white-space:nowrap;opacity:clamp(0,calc((var(--p,1) - 0.45)*4),1);">' + _esc(role) + '</div>' : '') + '</div></div>';
};

// An audio-style waveform: bars whose heights move with the second dial (--s), rising in with p. Heights are seeded, so it is deterministic.
var _MO_WAVE_SEED = [5, 9, 3, 8, 6, 10, 4, 7, 9, 2, 8, 5, 10, 3, 7, 6];
_RENDERERS['motion_wave'] = function(b) {
  var n = _ffInt(b.bars, 32, 8, 64), h = _ffInt(b.height, 120, 20, 600), gap = _ffInt(b.gap, 3, 0, 20), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), acc2 = _moInk(b, 'accent2', ''), i, out = '';
  for (i = 0; i < n; i++) {
    var base = _MO_WAVE_SEED[i % 16] / 10, ph = _ffNum(i * 0.7 + _MO_WAVE_SEED[(i * 5) % 16] * 0.3, 0, 0, 100, 2), col = acc2 && i % 2 ? acc2 : acc;
    out += '<div style="flex:1;min-width:1px;height:calc(' + h + 'px*' + _ffNum(base, 0.5, 0, 1, 2) + '*(0.35 + 0.65*abs(sin(calc(var(--s,0)*20 + ' + ph + ')))) *clamp(0,calc(var(--p,1)*3 - ' + _ffNum(i / n * 1.5, 0, 0, 2, 2) + '),1));background:' + col + ';border-radius:999px;"></div>';
  }
  return '<div role="img" aria-label="Audio waveform" style="display:flex;align-items:center;gap:' + gap + 'px;width:100%;height:' + h + 'px;">' + out + '</div>';
};

// Repeater: copies of one child, each stepped by an offset, rotation and scale, appearing one after another as p goes 0 to 1.
_RENDERERS['motion_repeat'] = function(b) {
  var n = _ffInt(b.copies, 6, 2, 16), dx = _ffNum(b.dx, 8, -60, 60, 1), dy = _ffNum(b.dy, 0, -60, 60, 1), rot = _ffNum(b.rotate, 12, -90, 90, 1), sc = _ffNum(b.scale, 0.92, 0.5, 1.5, 3), blk = Array.isArray(b.blocks) && b.blocks.length ? b.blocks[0] : null, i, out = '';
  var inner = blk ? _moRender(blk) : '';
  for (i = 0; i < n; i++) {
    out += '<div style="--u:clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1);position:absolute;left:0;top:0;width:100%;height:100%;opacity:var(--u);transform:translate(calc(' + dx + '%*' + i + '),calc(' + dy + '%*' + i + ')) rotate(calc(' + rot + 'deg*' + i + ')) scale(calc(' + _ffNum(Math.pow(sc, i), 1, 0, 10, 4) + '));">' + inner + '</div>';
  }
  return '<div style="position:relative;width:100%;height:100%;">' + out + '</div>';
};

// ─── batch 6 (2026-10-02): poster-to-player, clock-driven chat, wiggle, text on a path ───────────────────────────────────────
// A poster with a play button that becomes the real player on click (YouTube, Vimeo or Loom). The player loads only after the click:
// a hidden-until-checked iframe with loading=lazy is not fetched, so the film stays deterministic and nothing autoplays on its own.
var _MO_MEDIA_CSS = '<style>.mtm-f{display:none}.mtm-c:checked~.mtm-f{display:block}.mtm-c:checked~.mtm-ui{display:none}.mtm-c:checked{pointer-events:none}</style>';
_RENDERERS['motion_media'] = function(b) {
  var url = typeof b.url === 'string' ? b.url : '', src = '', m;
  if ((m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/))) src = 'https://www.youtube.com/embed/' + m[1] + '?rel=0&autoplay=1&mute=1&playsinline=1';
  else if ((m = url.match(/vimeo\.com\/(\d+)/))) src = 'https://player.vimeo.com/video/' + m[1] + '?autoplay=1&muted=1';
  else if ((m = url.match(/loom\.com\/share\/([a-zA-Z0-9]+)/))) src = 'https://www.loom.com/embed/' + m[1] + '?autoplay=1';
  var ratio = _ffPick(b.ratio, _MO_RATIO, '16:9'), rad = _ffInt(b.radius, 12, 0, 60), title = _moStr(b.title, 60) || 'Video', acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), poster = _moImg(b.poster);
  var bg = poster ? '<img src="' + _esc(poster) + '" alt="" loading="lazy" referrerpolicy="no-referrer" style="position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;transform:scale(calc(1.02 + var(--p,1)*0.06));">'
    : '<div aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:100%;background:linear-gradient(135deg,color-mix(in srgb,' + acc + ' 45%,#0b0712),#0b0712);"></div>';
  var play = '<div aria-hidden="true" style="position:absolute;left:50%;top:50%;width:5.2em;height:5.2em;margin:-2.6em 0 0 -2.6em;border-radius:50%;background:' + acc + ';display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 calc(var(--s,0)*1.4em) color-mix(in srgb,' + acc + ' calc((1 - var(--s,0))*40%),transparent);transform:scale(clamp(0,calc(var(--p,1)*3),1));">'
    + '<svg viewBox="0 0 24 24" width="46%" height="46%" style="margin-left:8%;"><path d="M6 3.5v17l14-8.5z" fill="#fff"/></svg></div>';
  return (src ? _MO_MEDIA_CSS : '') + '<div role="group" aria-label="' + _esc(title) + '" style="position:relative;width:100%;aspect-ratio:' + ratio + ';border-radius:' + rad + 'px;overflow:hidden;background:#000;font-family:' + _MO_SANS + ';font-size:16px;">'
    + (src ? '<input type="checkbox" class="mtm-c" aria-label="Play ' + _esc(title) + '" style="position:absolute;left:0;top:0;width:100%;height:100%;margin:0;opacity:0;z-index:3;cursor:pointer;">' : '')
    + '<div class="mtm-ui" style="position:absolute;left:0;top:0;width:100%;height:100%;">' + bg + play
    + '<div style="position:absolute;left:0;right:0;bottom:0;padding:1.6em 1.2em 0.9em;background:linear-gradient(transparent,rgba(0,0,0,0.65));color:#fff;font-weight:700;opacity:clamp(0,calc(var(--p,1)*4),1);">' + _esc(title) + '</div></div>'
    + (src ? '<iframe class="mtm-f" loading="lazy" src="' + _esc(src) + '" title="' + _esc(title) + '" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen style="position:absolute;left:0;top:0;width:100%;height:100%;border:0;"></iframe>' : '') + '</div>';
};

// A chat that plays on the clock: each message rises in turn, and an agent message shows typing dots first.
_RENDERERS['motion_chat'] = function(b) {
  var src = Array.isArray(b.messages) ? b.messages : [], msgs = [], i;
  for (i = 0; i < src.length && msgs.length < 6; i++) {
    var m = src[i], obj = m && typeof m === 'object', t = _moStr(typeof m === 'string' ? m : (obj ? m.text : ''), 120);
    if (t) msgs.push({t: t, me: obj ? m.from === 'user' : i % 2 === 0});
  }
  if (!msgs.length) msgs = [{t: 'Hello', me: true}, {t: 'Hi, how can I help?', me: false}];
  var n = msgs.length, size = _ffInt(b.size, 22, 8, 60), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), name = _moStr(b.agent, 20), out = '';
  for (i = 0; i < n; i++) {
    var me = msgs[i].me, u = '--u:clamp(0,calc(var(--p,1)*' + (n + 1) + ' - ' + i + '),1);';
    var dots = me ? '' : '<span aria-hidden="true" style="position:absolute;left:0;top:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;gap:0.25em;opacity:calc(clamp(0,calc(var(--u)*8),1)*(1 - clamp(0,calc((var(--u) - 0.3)*8),1)));">'
      + '<i style="width:0.4em;height:0.4em;border-radius:50%;background:currentColor;opacity:0.6;"></i><i style="width:0.4em;height:0.4em;border-radius:50%;background:currentColor;opacity:0.6;"></i><i style="width:0.4em;height:0.4em;border-radius:50%;background:currentColor;opacity:0.6;"></i></span>';
    out += '<div style="' + u + 'display:flex;justify-content:' + (me ? 'flex-end' : 'flex-start') + ';margin-top:0.6em;transform:translateY(calc((1 - var(--u))*0.8em));">'
      + '<div style="position:relative;max-width:78%;padding:0.6em 0.95em;border-radius:1.1em;' + (me ? 'border-bottom-right-radius:0.3em;background:' + acc + ';color:#fff;' : 'border-bottom-left-radius:0.3em;background:' + _MO_MIX_FILL + ';border:1px solid ' + _MO_MIX_LINE + ';color:var(--mt-ink,#f1f5f9);') + 'line-height:1.3;opacity:clamp(0,calc(var(--u)*6),1);">'
      + dots + '<span style="opacity:' + (me ? '1' : 'clamp(0,calc((var(--u) - 0.35)*8),1)') + ';">' + _esc(msgs[i].t) + '</span></div></div>';
  }
  return '<div style="width:100%;font-family:' + _MO_SANS + ';font-size:' + size + 'px;">' + (name ? '<div style="font-size:0.75em;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:var(--mt-mute,#94a3b8);">' + _esc(name) + '</div>' : '') + out + '</div>';
};

// Wiggle: its children drift and tremble continuously as the second dial (--s) runs, at rest at 0. Children are placed in percent of the box.
_RENDERERS['motion_wiggle'] = function(b) {
  var amp = _ffInt(b.amount, 10, 1, 80), freq = _ffInt(b.frequency, 6, 1, 40), rot = _ffNum(b.tilt, 2, 0, 15, 1), blocks = Array.isArray(b.blocks) ? b.blocks.slice(0, 12) : [], inner = '', i, st = {dropped: 0}, seen = {}, ids = {};
  for (i = 0; i < blocks.length; i++) { var w = _moPlaced(blocks[i], seen, ids, st); if (w !== null) inner += w; }
  var tf = 'translate(calc(' + amp + 'px*sin(calc(var(--s,0)*' + freq + '*6.2832))),calc(' + Math.floor(amp * 0.7 + 0.5) + 'px*sin(calc(var(--s,0)*' + freq + '*8.1)))) rotate(calc(' + rot + 'deg*sin(calc(var(--s,0)*' + freq + '*5.3))))';
  return '<div style="position:absolute;left:0;top:0;width:100%;height:100%;transform:' + tf + ';">' + inner + '</div>';
};

// Text that runs along a path and types itself on, one character at a time as p goes 0 to 1.
_RENDERERS['motion_textpath'] = function(b) {
  var text = _moStr(b.text, 40) || 'Text on a path', d = typeof b.d === 'string' ? b.d.trim() : '';
  if (!_MO_PATH_OK.test(d)) d = 'M 20 220 C 120 40 280 40 380 220';
  var vw = _ffInt(b.w, 400, 50, 2000), vh = _ffInt(b.h, 300, 50, 2000), size = _ffInt(b.size, 30, 8, 120), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), color = _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), guide = b.guide === true;
  var h = 7, i, chars = Array.from(text), n = chars.length, spans = '';
  for (i = 0; i < d.length; i++) h = (h * 31 + d.charCodeAt(i)) % 1000003;
  var id = 'mtp' + h;
  for (i = 0; i < n; i++) spans += '<tspan style="fill-opacity:clamp(0,calc(var(--p,1)*' + (n + 2) + ' - ' + i + '),1);">' + _esc(chars[i] === ' ' ? ' ' : chars[i]) + '</tspan>';
  return '<svg viewBox="0 0 ' + vw + ' ' + vh + '" width="100%" role="img" aria-label="' + _esc(text) + '" style="display:block;overflow:visible;">'
    + '<defs><path id="' + id + '" d="' + d + '"/></defs>' + (guide ? '<path d="' + d + '" style="fill:none;stroke:' + acc + ';stroke-width:2;opacity:0.35;"/>' : '')
    + '<text style="font-family:' + _MO_SANS + ';font-size:' + size + 'px;font-weight:800;fill:' + color + ';letter-spacing:0.04em;"><textPath href="#' + id + '" startOffset="4%">' + spans + '</textPath></text></svg>';
};

// ─── batch 7 (2026-10-02, premium spec items 8-11): liquid blobs, finishing layer, page assembly, isometric build ──────────────────
var _MO_GRAIN = {fine: 1.2, medium: 0.8, coarse: 0.45};
var _MO_LEAK = {warm: ['#ff9a3c', '#ff3d81'], cool: ['#38bdf8', '#7c5cff']};
var _MO_POSE = [[-70, -50, -14], [60, -60, 11], [-80, 40, 9], [70, 55, -12], [-30, -90, 7], [40, 85, -9], [-90, -10, 13], [85, 5, -6]];

// Liquid blobs that merge and split (metaballs): circles move between a start and an end point as p goes 0 to 1 and orbit a little
// with --s, inside an SVG whose goo filter is fixed markup (blur then an alpha threshold); nothing from the payload reaches the filter.
_RENDERERS['motion_goo'] = function(b) {
  var src = Array.isArray(b.blobs) ? b.blobs : [], bl = [], i;
  for (i = 0; i < src.length && bl.length < 8; i++) {
    var s = src[i];
    if (!s || typeof s !== 'object') continue;
    function nv(v) { return typeof v === 'number' && isFinite(v) ? v : undefined; } // numbers only: strings parse differently in the two twins
    var x = _ffNum(nv(s.x), 50, 0, 100, 1), y = _ffNum(nv(s.y), 50, 0, 100, 1);
    bl.push({x: x, y: y, x2: _ffNum(nv(s.x2), parseFloat(x), 0, 100, 1), y2: _ffNum(nv(s.y2), parseFloat(y), 0, 100, 1), r: _ffNum(nv(s.r), 10, 2, 40, 1)});
  }
  if (!bl.length) bl = [{x: '30', y: '50', x2: '45', y2: '50', r: '12'}, {x: '70', y: '50', x2: '55', y2: '50', r: '12'}];
  var col = _moInk(b, 'color', 'var(--mt-acc,#38bdf8)'), col2 = _moInk(b, 'accent2', ''), orb = _ffNum(b.orbit, 4, 0, 20, 1), h = 0, cfg = '', out = '', k;
  for (i = 0; i < bl.length; i++) cfg += bl[i].x + ',' + bl[i].y + ',' + bl[i].x2 + ',' + bl[i].y2 + ',' + bl[i].r + ';';
  for (k = 0; k < cfg.length; k++) h = (h * 31 + cfg.charCodeAt(k)) % 1000003;
  var fid = 'mtgoo' + h;
  var glossy = b.style !== 'flat', hl = '';
  for (i = 0; i < bl.length; i++) {
    var B = bl[i], c = glossy ? 'url(#' + fid + 'g)' : (col2 && i % 2 ? col2 : col), ph = _ffNum(i * 1.9, 0, 0, 20, 1);
    var tf = 'transform:translate(calc(' + B.x + 'px + (' + B.x2 + ' - ' + B.x + ')*1px*clamp(0,var(--p,1),1) + ' + orb + 'px*sin(calc(var(--s,0)*6.2832 + ' + ph + '))),calc(' + B.y + 'px + (' + B.y2 + ' - ' + B.y + ')*1px*clamp(0,var(--p,1),1) + ' + orb + 'px*cos(calc(var(--s,0)*6.2832 + ' + ph + '))));';
    out += '<circle r="' + B.r + '" style="fill:' + c + ';' + tf + '"/>';
    if (glossy) { var rf = parseFloat(B.r); hl += '<circle r="' + _ffNum(rf * 0.42, 1, 0, 40, 1) + '" cx="' + _ffNum(-rf * 0.32, 0, -40, 0, 1) + '" cy="' + _ffNum(-rf * 0.38, 0, -40, 0, 1) + '" style="' + tf + '"/>'; }
  }
  var defs = '<filter id="' + fid + '" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur in="SourceGraphic" stdDeviation="3.2" result="b"/><feColorMatrix in="b" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7"/>'
    + (glossy ? '<feDropShadow dx="0" dy="1.6" stdDeviation="1.8" flood-color="#000" flood-opacity="0.35"/>' : '') + '</filter>';
  if (glossy) defs += '<linearGradient id="' + fid + 'g" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="100" y2="100"><stop offset="0" style="stop-color:color-mix(in srgb,' + col + ' 70%,#ffffff)"/><stop offset="0.55" style="stop-color:' + col + '"/><stop offset="1" style="stop-color:' + (col2 || 'color-mix(in srgb,' + col + ' 60%,#000000)') + '"/></linearGradient>'
    + '<filter id="' + fid + 'h" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.4"/></filter>';
  return '<svg viewBox="0 0 100 100" width="100%" role="img" aria-label="Liquid blobs" style="display:block;overflow:visible;"><defs>' + defs + '</defs>'
    + '<g filter="url(#' + fid + ')">' + out + '</g>' + (glossy ? '<g filter="url(#' + fid + 'h)" style="fill:#ffffff;opacity:0.45;mix-blend-mode:screen;">' + hl + '</g>' : '') + '</svg>';
};

// A finishing layer for the whole frame: film grain, a vignette, drifting light leaks and a glass sheen. Place it last, full size;
// it never takes clicks. p fades it in, --s drifts the grain and the leaks.
_RENDERERS['motion_finish'] = function(b) {
  var gr = _ffPick(b.grain_size, _MO_GRAIN, 'medium'), gs = b.grain === false ? 0 : _ffNum(b.grain_amount, 0.12, 0, 0.5, 2), vg = b.vignette === false ? 0 : _ffNum(b.vignette_amount, 0.55, 0, 1, 2);
  var lk = b.leak === false ? '' : _moOwn(_MO_LEAK, b.leak, 'warm'), sh = b.sheen === true, ls = _ffNum(b.leak_amount, 0.35, 0, 1, 2), L = lk ? _MO_LEAK[lk] : null, out = '';
  var fade = 'clamp(0,calc(var(--p,1)*4),1)';
  if (gs > 0) out += '<svg aria-hidden="true" width="100%" height="100%" preserveAspectRatio="none" style="position:absolute;left:0;top:0;width:100%;height:100%;mix-blend-mode:overlay;opacity:calc(' + gs + '*' + fade + '*1.7);transform:translate(calc(var(--s,0)*-60px),calc(var(--s,0)*40px));"><filter id="mtgr"><feTurbulence type="fractalNoise" baseFrequency="' + gr + '" numOctaves="2" seed="7" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect x="-30%" y="-30%" width="170%" height="170%" filter="url(#mtgr)"/></svg>';
  if (L) out += '<div aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:100%;mix-blend-mode:screen;opacity:calc(' + ls + '*' + fade + ');background:radial-gradient(ellipse 45% 70% at calc(10% + var(--s,0)*30%) 20%,' + L[0] + ',transparent 70%),radial-gradient(ellipse 40% 60% at calc(95% - var(--s,0)*25%) 90%,' + L[1] + ',transparent 70%);"></div>';
  if (vg > 0) out += '<div aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:100%;opacity:' + fade + ';background:radial-gradient(ellipse at 50% 50%,transparent 45%,rgba(0,0,0,' + vg + ') 100%);"></div>';
  if (sh) out += '<div aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:100%;overflow:hidden;"><div style="position:absolute;top:-20%;bottom:-20%;width:22%;left:calc(-30% + clamp(0,var(--p,1),1)*150%);background:linear-gradient(100deg,transparent,rgba(255,255,255,0.22),transparent);transform:skewX(-18deg);"></div></div>';
  return '<div aria-hidden="true" style="position:relative;width:100%;height:100%;pointer-events:none;">' + out + '</div>';
};

// Page assembly: child atoms start scattered and tilted and land in a bento grid, one after another as p goes 0 to 1.
_RENDERERS['motion_assemble'] = function(b) {
  var src = Array.isArray(b.blocks) ? b.blocks.slice(0, 8) : [], cols = _ffInt(b.columns, 3, 2, 4), gap = _ffInt(b.gap, 14, 0, 40), i, out = '', n = src.length;
  for (i = 0; i < n; i++) {
    var c = src[i], span = c && typeof c === 'object' ? _ffInt(c.span, 1, 1, 2) : 1, P = _MO_POSE[i % 8];
    out += '<div style="--u:clamp(0,calc(var(--p,1)*' + (n + 2) + ' - ' + i + '),1);grid-column:span ' + Math.min(span, cols) + ';opacity:var(--u);transform:translate(calc((1 - var(--u))*' + P[0] + '%),calc((1 - var(--u))*' + P[1] + '%)) rotate(calc((1 - var(--u))*' + P[2] + 'deg)) scale(calc(0.7 + 0.3*var(--u)));min-width:0;">' + _moRender(c) + '</div>';
  }
  return '<div style="display:grid;grid-template-columns:repeat(' + cols + ',minmax(0,1fr));gap:' + gap + 'px;width:100%;align-items:start;">' + out + '</div>';
};

// Isometric build: a grid of blocks that rise in a diagonal wave as p goes 0 to 1, shaded in three faces from one accent.
_RENDERERS['motion_iso'] = function(b) {
  var cols = _ffInt(b.columns, 6, 2, 12), rows = _ffInt(b.rows, 6, 2, 12), unit = _ffInt(b.height, 14, 4, 40), ku = _ffNum(unit * 0.0086, 0.1, 0, 1, 4), acc = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)'), T = cols + rows + 1;
  var hs = Array.isArray(b.heights) ? b.heights : [], r, c, tiles = '';
  var tw = 200 / (cols + rows + 1), rm = 0.62 * tw, ext = tw * (0.25 * (cols + rows - 2) + 0.5) + rm;
  for (r = 0; r < rows; r++) for (c = 0; c < cols; c++) {
    var idx = r * cols + c, hv = idx < hs.length && typeof hs[idx] === 'number' && isFinite(hs[idx]) ? Math.max(0, Math.min(10, hs[idx])) : ((idx * 7 + r * 3 + c * 5) % 9) + 1;
    var hh = _ffNum(hv, 1, 0, 10, 1), F = hh + '*' + ku + '*var(--u)';
    var left = _ffNum((c - r + rows - 1) * tw / 2, 0, 0, 100, 3), top = _ffNum((rm + (c + r) * 0.25 * tw) / ext * 100, 0, 0, 200, 3), w = _ffNum(tw, 1, 0, 100, 3);
    tiles += '<div style="--u:clamp(0,calc(var(--p,1)*' + T + ' - ' + (r + c) + '),1);position:absolute;left:' + left + '%;top:' + top + '%;width:' + w + '%;aspect-ratio:2/1;opacity:var(--u);">'
      + '<div style="position:absolute;left:0;width:50%;top:calc(50% - 100%*' + F + ');height:calc(100%*' + F + ' + 1px);transform-origin:0 0;transform:skewY(26.565deg);background:color-mix(in srgb,' + acc + ' 62%,#000);"></div>'
      + '<div style="position:absolute;left:50%;width:50%;top:calc(100% - 100%*' + F + ');height:calc(100%*' + F + ' + 1px);transform-origin:0 0;transform:skewY(-26.565deg);background:color-mix(in srgb,' + acc + ' 38%,#000);"></div>'
      + '<div style="position:absolute;left:0;right:0;top:0;height:100%;transform:translateY(calc(-100%*' + F + '));background:' + acc + ';clip-path:polygon(50% 0,100% 50%,50% 100%,0 50%);"></div></div>';
  }
  return '<div role="img" aria-label="Isometric blocks rising" style="position:relative;width:100%;aspect-ratio:100/' + _ffNum(ext, 1, 1, 400, 3) + ';">' + tiles + '</div>';
};

// ─── batch 8 (2026-10-02, premium items 5-6): particles and shape morph. Integer geometry only, so both twins agree exactly ──────────
// Shape outlines: 48 points each, equal-perimeter resampled, starting at the top and running clockwise, as tenths of a 0-100 box.
var _MO_SHAPES = {
  'circle': [500,40,560,44,619,56,676,75,730,102,780,135,825,175,865,220,898,270,925,324,944,381,956,440,960,500,956,560,944,619,925,676,898,730,865,780,825,825,780,865,730,898,676,925,619,944,560,956,500,960,440,956,381,944,324,925,270,898,220,865,175,825,135,780,102,730,75,676,56,619,44,560,40,500,44,440,56,381,75,324,102,270,135,220,175,175,220,135,270,102,324,75,381,56,440,44],
  'square': [500,60,573,60,647,60,720,60,793,60,867,60,940,60,940,133,940,207,940,280,940,353,940,427,940,500,940,573,940,647,940,720,940,793,940,867,940,940,867,940,793,940,720,940,647,940,573,940,500,940,427,940,353,940,280,940,207,940,133,940,60,940,60,867,60,793,60,720,60,647,60,573,60,500,60,427,60,353,60,280,60,207,60,133,60,60,133,60,207,60,280,60,353,60,427,60],
  'triangle': [500,60,527,110,554,161,581,211,608,261,635,312,662,362,689,412,716,463,743,513,770,563,797,614,824,664,851,714,878,764,905,815,932,865,900,880,843,880,786,880,728,880,671,880,614,880,557,880,500,880,443,880,386,880,329,880,272,880,214,880,157,880,100,880,68,865,95,815,122,764,149,714,176,664,203,614,230,563,257,513,284,463,311,412,338,362,365,312,392,261,419,211,446,161,473,110],
  'diamond': [500,40,538,78,577,117,615,155,653,193,692,232,730,270,768,308,807,347,845,385,883,423,922,462,960,500,922,538,883,577,845,615,807,653,768,692,730,730,692,768,653,807,615,845,577,883,538,922,500,960,462,922,423,883,385,845,347,807,308,768,270,730,232,692,193,653,155,615,117,577,78,538,40,500,78,462,117,423,155,385,193,347,232,308,270,270,308,232,347,193,385,155,423,117,462,78],
  'hexagon': [500,30,551,59,602,89,653,118,704,148,754,177,805,206,856,236,907,265,907,324,907,382,907,441,907,500,907,559,907,618,907,676,907,735,856,764,805,794,754,823,704,852,653,882,602,911,551,941,500,970,449,941,398,911,347,882,296,852,246,823,195,794,144,764,93,735,93,676,93,618,93,559,93,500,93,441,93,383,93,324,93,265,144,236,195,206,246,177,296,147,347,118,398,89,449,59],
  'star': [500,40,524,106,549,173,573,239,598,305,632,359,702,362,773,364,844,367,914,370,934,389,879,433,823,477,768,521,712,564,702,623,721,691,740,759,759,827,778,895,735,877,676,838,618,798,559,759,500,720,441,759,382,798,324,838,265,877,222,895,241,827,260,759,279,691,298,623,288,564,232,521,177,477,121,433,66,389,86,370,156,367,227,364,298,362,368,359,402,305,427,239,451,173,476,106],
  'heart': [500,320,516,263,547,212,589,170,641,141,698,127,758,130,814,147,865,179,906,222,934,274,947,332,943,391,925,448,895,499,858,546,817,589,774,630,729,669,683,707,638,747,595,788,555,832,521,881,500,936,479,881,445,832,405,788,362,747,317,707,271,669,226,630,183,589,142,546,105,499,75,448,57,391,53,332,66,274,94,222,135,179,186,147,242,130,302,127,359,141,411,170,453,212,484,263],
  'blob': [500,60,556,70,609,88,660,112,708,143,750,180,789,221,832,257,871,299,903,345,929,395,948,448,959,504,943,558,920,609,890,657,854,701,812,739,767,772,733,817,693,857,647,891,598,918,545,938,490,949,435,937,381,919,331,894,284,863,241,825,203,784,159,748,121,707,89,660,63,610,43,557,30,502,45,448,67,396,95,347,130,302,170,263,216,229,254,188,295,149,341,117,391,91,445,72],
  'plus': [620,60,620,133,620,207,620,280,620,353,667,380,740,380,813,380,887,380,940,400,940,473,940,547,940,620,867,620,793,620,720,620,647,620,620,667,620,740,620,813,620,887,600,940,527,940,453,940,380,940,380,867,380,793,380,720,380,647,333,620,260,620,187,620,113,620,60,600,60,527,60,453,60,380,133,380,207,380,280,380,353,380,380,333,380,260,380,187,380,113,400,60,473,60,547,60],
  'arrow': [560,140,602,180,644,219,686,259,727,299,769,338,811,378,853,418,895,457,937,497,902,536,860,576,818,616,776,655,734,695,692,735,650,774,609,814,567,854,560,812,560,754,560,696,560,639,521,620,463,620,406,620,348,620,291,620,233,620,175,620,118,620,60,620,60,562,60,505,60,447,60,389,108,380,166,380,224,380,281,380,339,380,396,380,454,380,512,380,560,371,560,313,560,255,560,198]
};
// A 5x7 dot font (rows as 5-bit numbers, top row first).
var _MO_FONT = {" ": [0,0,0,0,0,0,0], "!": [4,4,4,4,4,0,4], "'": [4,4,8,0,0,0,0], ",": [0,0,0,0,12,4,8], "-": [0,0,0,31,0,0,0], ".": [0,0,0,0,0,12,12], "0": [14,17,19,21,25,17,14], "1": [4,12,4,4,4,4,14], "2": [14,17,1,2,4,8,31], "3": [31,2,4,2,1,17,14], "4": [2,6,10,18,31,2,2], "5": [31,16,30,1,1,17,14], "6": [6,8,16,30,17,17,14], "7": [31,1,2,4,8,8,8], "8": [14,17,17,14,17,17,14], "9": [14,17,17,15,1,2,12], ":": [0,12,12,0,12,12,0], "?": [14,17,1,2,4,0,4], "A": [14,17,17,31,17,17,17], "B": [30,17,17,30,17,17,30], "C": [14,17,16,16,16,17,14], "D": [30,17,17,17,17,17,30], "E": [31,16,16,30,16,16,31], "F": [31,16,16,30,16,16,16], "G": [14,17,16,23,17,17,15], "H": [17,17,17,31,17,17,17], "I": [14,4,4,4,4,4,14], "J": [7,2,2,2,2,18,12], "K": [17,18,20,24,20,18,17], "L": [16,16,16,16,16,16,31], "M": [17,27,21,21,17,17,17], "N": [17,17,25,21,19,17,17], "O": [14,17,17,17,17,17,14], "P": [30,17,17,30,16,16,16], "Q": [14,17,17,17,21,18,13], "R": [30,17,17,30,20,18,17], "S": [15,16,16,14,1,1,30], "T": [31,4,4,4,4,4,4], "U": [17,17,17,17,17,17,14], "V": [17,17,17,17,17,10,4], "W": [17,17,17,21,21,21,10], "X": [17,17,10,4,10,17,17], "Y": [17,17,10,4,4,4,4], "Z": [31,1,2,4,8,16,31]};
function _moT10(v) { var a = Math.abs(v); return (v < 0 ? '-' : '') + Math.floor(a / 10) + '.' + (a % 10); }

// Particles: up to 400 dots start scattered (a seeded Park-Miller sequence, integer maths) and converge into dot-matrix text or a
// shape outline as p goes 0 to 1; the second dial (--s) scatters them again.
_RENDERERS['motion_particles'] = function(b) {
  var text = typeof b.text === 'string' ? b.text.toUpperCase().slice(0, 12) : '', shape = _moOwn(_MO_SHAPES, b.shape, 'heart'), pts = [], W, H, i, r, c;
  var chs = Array.from(text), useText = false;
  for (i = 0; i < chs.length; i++) if (Object.prototype.hasOwnProperty.call(_MO_FONT, chs[i]) && chs[i] !== ' ') useText = true;
  if (useText) {
    W = chs.length * 60 - 10; H = 70;
    for (i = 0; i < chs.length; i++) {
      var g = Object.prototype.hasOwnProperty.call(_MO_FONT, chs[i]) ? _MO_FONT[chs[i]] : _MO_FONT[' '];
      for (r = 0; r < 7; r++) for (c = 0; c < 5; c++) if (g[r] & (16 >> c)) pts.push([i * 60 + c * 10 + 5, r * 10 + 5]);
    }
  } else {
    W = 1000; H = 1000;
    var sp = _MO_SHAPES[shape];
    for (i = 0; i < sp.length; i += 2) pts.push([sp[i], sp[i + 1]]);
  }
  if (pts.length > 400) pts = pts.slice(0, 400);
  var seed = _ffInt(b.seed, 7, 1, 2147483646), spread = _ffInt(b.scatter, 100, 0, 300), rr = _ffNum(b.dot, useText ? 0.42 : 1.6, 0.1, 10, 2);
  var col = _moInk(b, 'color', 'var(--mt-acc,#38bdf8)'), col2 = _moInk(b, 'accent2', ''), out = '';
  var sw = Math.floor(W * spread / 100), sh = Math.floor(H * spread / 100), vary = b.vary === true, glow = b.glow === true;
  for (i = 0; i < pts.length; i++) {
    seed = (seed * 16807) % 2147483647; var sx = (seed % (W + 2 * sw + 1)) - sw;
    seed = (seed * 16807) % 2147483647; var sy = (seed % (H + 2 * sh + 1)) - sh;
    seed = (seed * 16807) % 2147483647; var jt = seed % 10, ri = rr;
    if (vary) { seed = (seed * 16807) % 2147483647; ri = _ffNum(parseFloat(rr) * (60 + (seed % 9) * 10) / 100, 0.42, 0.05, 20, 2); }
    var tx = pts[i][0], ty = pts[i][1], fill = col2 && i % 3 === 0 ? col2 : col;
    out += '<circle r="' + ri + '" style="--u:clamp(0,calc(var(--p,1)*2 - 0.' + jt + '),1);fill:' + fill + ';transform:translate(calc((' + _moT10(sx) + ' + ' + _moT10(tx - sx) + '*var(--u)*(1 - var(--s,0)))*1px),calc((' + _moT10(sy) + ' + ' + _moT10(ty - sy) + '*var(--u)*(1 - var(--s,0)))*1px));"/>';
  }
  var label = useText ? text : shape;
  var gid = useText ? 'mtpglowt' : 'mtpglows', gf = glow ? '<defs><filter id="' + gid + '" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="' + (useText ? '0.45' : '1.6') + '" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>' : '';
  return '<svg viewBox="0 0 ' + _moT10(W) + ' ' + _moT10(H) + '" width="100%" role="img" aria-label="' + _esc(label) + '" style="display:block;overflow:visible;">' + gf + (glow ? '<g filter="url(#' + gid + ')">' + out + '</g>' : out) + '</svg>';
};

// Shape morph: one shape becomes the next (2 to 4 presets) as p goes 0 to 1. Every vertex of a 48-point clip polygon is a sum of
// clamped steps, so the morph is pure CSS and scrubs exactly. --s turns it by `rotate` degrees.
_RENDERERS['motion_morph'] = function(b) {
  var src = Array.isArray(b.shapes) ? b.shapes : [], sh = [], i, j;
  for (i = 0; i < src.length && sh.length < 4; i++) if (typeof src[i] === 'string' && Object.prototype.hasOwnProperty.call(_MO_SHAPES, src[i])) sh.push(src[i]);
  if (sh.length < 2) sh = ['circle', 'star'];
  var k = sh.length, pts = [], fill = _moInk(b, 'fill', 'var(--mt-acc,#38bdf8)'), fill2 = _moInk(b, 'fill2', ''), rot = _ffInt(b.rotate, 0, -720, 720);
  for (i = 0; i < 96; i += 2) {
    var x = _moT10(_MO_SHAPES[sh[0]][i]) + '%', y = _moT10(_MO_SHAPES[sh[0]][i + 1]) + '%';
    for (j = 1; j < k; j++) {
      var dx = _MO_SHAPES[sh[j]][i] - _MO_SHAPES[sh[j - 1]][i], dy = _MO_SHAPES[sh[j]][i + 1] - _MO_SHAPES[sh[j - 1]][i + 1], st = '*clamp(0,calc(var(--p,1)*' + (k - 1) + ' - ' + (j - 1) + '),1)';
      if (dx) x += ' + ' + _moT10(dx) + '%' + st;
      if (dy) y += ' + ' + _moT10(dy) + '%' + st;
    }
    pts.push('calc(' + x + ') calc(' + y + ')');
  }
  var gl = b.glossy === true, bg = (gl ? 'radial-gradient(circle at 32% 26%,rgba(255,255,255,0.42),rgba(255,255,255,0) 46%),radial-gradient(circle at 70% 85%,rgba(0,0,0,0.28),rgba(0,0,0,0) 55%),' : '') + (fill2 ? 'linear-gradient(135deg,' + fill + ',' + fill2 + ')' : fill), poly = 'polygon(' + pts.join(',') + ')';
  var inner = '<div style="width:100%;aspect-ratio:1/1;background:' + bg + ';clip-path:' + poly + ';-webkit-clip-path:' + poly + ';' + (rot ? 'transform:rotate(calc(var(--s,0)*' + rot + 'deg));' : '') + '"></div>';
  return '<div role="img" aria-label="' + _esc(sh.join(' to ')) + '" style="width:100%;' + (gl ? 'filter:drop-shadow(0 0.9em 1.2em rgba(0,0,0,0.38));' : '') + '">' + inner + '</div>';
};

// ─── WebGL spike (2026-10-02, see a2ui-private/briefs/webgl-spike-design.md): a seekable shader background ─────────────────────
// Fixed shader and driver (no payload text reaches the script; config is numbers only). Time comes from the film: the driver reads the
// inherited --s each frame (span seconds per unit), so seek(t) shows exactly that frame. The element's own CSS gradient is the fallback
// for no WebGL, a failed compile, print, or a host that strips scripts.
var _MO_SHADER_JS = '(function(){var r=document.getElementById("mt-%%UID%%");if(!r)return;var C=%%CFG%%,cv=r.querySelector("canvas"),gl=null;try{gl=cv.getContext("webgl",{antialias:false,preserveDrawingBuffer:true});}catch(e){}if(!gl){cv.style.display="none";return;}var VS="attribute vec2 a;void main(){gl_Position=vec4(a,0.0,1.0);}";var FS="precision mediump float;uniform float t;uniform vec2 R;uniform vec3 c1;uniform vec3 c2;uniform vec3 c3;uniform float sc;uniform float k;float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}float n(vec2 p){vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(h(i),h(i+vec2(1.0,0.0)),f.x),mix(h(i+vec2(0.0,1.0)),h(i+vec2(1.0,1.0)),f.x),f.y);}float fb(vec2 p){float v=0.0;float a=0.5;for(int j=0;j<4;j++){v+=a*n(p);p*=2.02;a*=0.5;}return v;}float sk(vec2 p,float T){return sin(p.x*1.6+sin(p.y*1.1+T)*1.4+T*0.7)+0.6*sin(p.y*2.3+sin(p.x*0.9-T*0.8)*1.8)+0.12*sin((p.x+p.y)*2.6+T*1.3);}void main(){vec2 u=gl_FragCoord.xy/R;vec2 p=u*vec2(R.x/R.y,1.0)*sc;float T=t*0.35;vec2 q=vec2(fb(p+T),fb(p+vec2(5.2,1.3)-T));vec2 w=vec2(fb(p+2.2*q+vec2(1.7,9.2)+T*0.6),fb(p+2.2*q+vec2(8.3,2.8)-T*0.4));float f=fb(p+2.2*w);vec3 col=mix(c1,c2,clamp(f*f*2.2,0.0,1.0));col=mix(col,c3,clamp(length(q)*0.9-0.2,0.0,1.0));if(k>1.5){vec2 s=u*vec2(R.x/R.y,1.0)*sc*vec2(1.5,2.4);float h=sk(s,T);float hx=sk(s+vec2(0.01,0.0),T),hy=sk(s+vec2(0.0,0.01),T);vec3 n=normalize(vec3(-(hx-h)*100.0,-(hy-h)*100.0,2.6));vec3 L=normalize(vec3(-0.45,0.6,0.66));float df=max(dot(n,L),0.0);float sp=pow(max(dot(n,normalize(L+vec3(0.0,0.0,1.0))),0.0),12.0);float rim=pow(1.0-n.z,1.5);vec3 bs=mix(c1,c2,smoothstep(-1.6,1.9,h));col=bs*(0.1+1.0*df)+c3*sp*0.62+mix(c2,c3,0.5)*rim*0.3;}else if(k>0.5){float b=smoothstep(0.25,0.85,fb(vec2(u.x*3.0+T,u.y*1.3-T*0.3)+q*1.5));col=mix(c1*0.18,mix(c2,c3,u.x),b*(1.0-u.y*0.55));}gl_FragColor=vec4(col,1.0);}";function sh(ty,src){var s=gl.createShader(ty);gl.shaderSource(s,src);gl.compileShader(s);return gl.getShaderParameter(s,gl.COMPILE_STATUS)?s:null;}var pg,uT,uR,lost=false,t0=performance.now(),lt=-1,lw=0,lh=0,vis=true,red=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;function init(){var vs=sh(gl.VERTEX_SHADER,VS),fs=sh(gl.FRAGMENT_SHADER,FS);if(!vs||!fs)return false;pg=gl.createProgram();gl.attachShader(pg,vs);gl.attachShader(pg,fs);gl.linkProgram(pg);if(!gl.getProgramParameter(pg,gl.LINK_STATUS))return false;gl.useProgram(pg);var bf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,bf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);var al=gl.getAttribLocation(pg,"a");gl.enableVertexAttribArray(al);gl.vertexAttribPointer(al,2,gl.FLOAT,false,0,0);function U(nm){return gl.getUniformLocation(pg,nm);}uT=U("t");uR=U("R");gl.uniform3fv(U("c1"),C.c1);gl.uniform3fv(U("c2"),C.c2);gl.uniform3fv(U("c3"),C.c3);gl.uniform1f(U("sc"),C.sc);gl.uniform1f(U("k"),C.k);lt=-1;lw=0;lh=0;return true;}if(!init()){cv.style.display="none";return;}cv.addEventListener("webglcontextlost",function(e){e.preventDefault();lost=true;});cv.addEventListener("webglcontextrestored",function(){lost=false;if(!init())cv.style.display="none";});if(window.IntersectionObserver){new IntersectionObserver(function(es){vis=es[0].isIntersecting;}).observe(r);}function fr(){requestAnimationFrame(fr);if(!vis||lost)return;var d=Math.min(window.devicePixelRatio||1,1.5),w=Math.min(960,Math.round(cv.clientWidth*d)),hh=Math.round(w*cv.clientHeight/Math.max(1,cv.clientWidth));if(w<2||hh<2)return;var sv=getComputedStyle(r).getPropertyValue("--s").trim(),tt=sv!==""?parseFloat(sv)*C.span:((C.still||red)?0:(performance.now()-t0)/1000*C.speed);if(isNaN(tt))tt=0;if(tt===lt&&w===lw&&hh===lh)return;if(w!==lw||hh!==lh){cv.width=w;cv.height=hh;gl.viewport(0,0,w,hh);lw=w;lh=hh;}lt=tt;gl.uniform1f(uT,tt);gl.uniform2f(uR,w,hh);gl.drawArrays(gl.TRIANGLES,0,3);}fr();})();';
var _MO_SHADER_KIND = {liquid: 1, aurora: 1, silk: 1};
function _moRgb3(h) { return '[' + _ffNum(parseInt(h.slice(1, 3), 16) / 255, 0, 0, 1, 3) + ',' + _ffNum(parseInt(h.slice(3, 5), 16) / 255, 0, 0, 1, 3) + ',' + _ffNum(parseInt(h.slice(5, 7), 16) / 255, 0, 0, 1, 3) + ']'; }
_RENDERERS['motion_shader'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6), kind = _moOwn(_MO_SHADER_KIND, b.kind, 'liquid');
  var c1 = _ffHex(b.color1, '#0b0712'), c2 = _ffHex(b.color2, '#ff3d81'), c3 = _ffHex(b.color3, '#ffb347');
  var sc = _ffNum(b.scale, 2, 0.5, 12, 2), span = _ffNum(b.span, 20, 0, 600, 2), speed = _ffNum(b.speed, 1, 0, 5, 2), still = b.still === true;
  var ratio = _ffPick(b.ratio, _MO_RATIO, '16:9'), fill = b.fill === true, rad = _ffInt(b.radius, 0, 0, 60), label = _moStr(b.label, 60) || 'Animated gradient background';
  var cfg = '{c1:' + _moRgb3(c1) + ',c2:' + _moRgb3(c2) + ',c3:' + _moRgb3(c3) + ',sc:' + sc + ',k:' + (kind === 'aurora' ? 1 : (kind === 'silk' ? 2 : 0)) + ',span:' + span + ',speed:' + speed + ',still:' + (still ? 'true' : 'false') + '}';
  return '<div id="mt-' + uid + '" role="img" aria-label="' + _esc(label) + '" style="position:relative;width:100%;' + (fill ? 'height:100%;' : 'aspect-ratio:' + ratio + ';') + 'overflow:hidden;border-radius:' + rad + 'px;background:linear-gradient(135deg,' + c1 + ',' + c2 + ' 55%,' + c3 + ');opacity:clamp(0,calc(var(--p,1)*3),1);">'
    + '<style>@media print{#mt-' + uid + ' canvas{display:none}}</style><canvas aria-hidden="true" style="position:absolute;left:0;top:0;width:100%;height:100%;display:block;"></canvas>'
    + '<script>' + _MO_SHADER_JS.replace('%%UID%%', function() { return uid; }).replace('%%CFG%%', function() { return cfg; }) + '<\/script></div>';
};
