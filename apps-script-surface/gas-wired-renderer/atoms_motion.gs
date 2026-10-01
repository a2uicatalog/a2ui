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
var _MO_PROPS = {x: [-200, 300], y: [-200, 300], opacity: [0, 1], scale: [0, 6], rotate: [-360, 360], rx: [-80, 80], ry: [-80, 80], blur: [0, 40], clip: [0, 1], p: [-0.5, 1.5], step: [0, 40]};
var _MO_PROP_ORDER = ['x', 'y', 'opacity', 'scale', 'rotate', 'rx', 'ry', 'blur', 'clip', 'p', 'step'];
var _MO_CAM = {x: [-100, 200], y: [-100, 200], zoom: [0.25, 6], rx: [-80, 80], ry: [-80, 80], rz: [-180, 180]};
var _MO_CAM_ORDER = ['x', 'y', 'zoom', 'rx', 'ry', 'rz'];
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
  'function ap(g,t){var o=els[g.i];if(!o)return;var v={};for(var k in g.p)v[k]=at(g.p[k],t);var e=o.e,tr="";' +
  'if(v.x!==undefined||v.y!==undefined){tr+="translate("+((v.x===undefined?0:v.x-o.x0)*C.W/100).toFixed(2)+"px,"+((v.y===undefined?0:v.y-o.y0)*C.H/100).toFixed(2)+"px) ";}' +
  'if(v.rx!==undefined)tr+="rotateX("+v.rx.toFixed(2)+"deg) ";if(v.ry!==undefined)tr+="rotateY("+v.ry.toFixed(2)+"deg) ";if(v.rotate!==undefined)tr+="rotate("+v.rotate.toFixed(2)+"deg) ";if(v.scale!==undefined)tr+="scale("+Math.max(0,v.scale).toFixed(4)+")";' +
  'if(tr)e.style.transform=tr;' +
  'if(v.opacity!==undefined)e.style.opacity=Math.max(0,Math.min(1,v.opacity)).toFixed(3);' +
  'if(v.blur!==undefined)e.style.filter=v.blur>0.05?"blur("+Math.min(40,v.blur).toFixed(2)+"px)":"";' +
  'if(v.clip!==undefined){var cl=Math.max(0,Math.min(1,v.clip));e.style.clipPath=cl<0.999?"inset(0 "+((1-cl)*100).toFixed(2)+"% 0 0)":"";}' +
  'if(v.p!==undefined){e.style.setProperty("--p",v.p.toFixed(4));for(var j=0;j<o.nums.length;j++){var q=o.nums[j],a=parseFloat(q.getAttribute("data-from")),b=parseFloat(q.getAttribute("data-to"));q.textContent=fm(a+(b-a)*v.p,parseInt(q.getAttribute("data-dec"),10)||0,q.getAttribute("data-pre")||"",q.getAttribute("data-suf")||"");}}' +
  'if(v.step!==undefined)e.style.setProperty("--s",v.step.toFixed(4));}' +
  'function cp(t){if(!C.cam||!cam)return;var c=C.cam;function g(k,d){return c[k]?at(c[k],t):d;}' +
  'cam.style.transform="translate("+(C.W/2)+"px,"+(C.H/2)+"px) scale("+g("zoom",1).toFixed(4)+") rotateX("+g("rx",0).toFixed(2)+"deg) rotateY("+g("ry",0).toFixed(2)+"deg) rotate("+g("rz",0).toFixed(2)+"deg) translate("+(-g("x",50)*C.W/100).toFixed(2)+"px,"+(-g("y",50)*C.H/100).toFixed(2)+"px)";}' +
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
    if (blk.layer === 'hud') hud += wrap; else world += wrap;
  }
  // Targets may be nested (a page inside a window): collect every data-mt-id the
  // children actually emitted. Agent text is _esc'd, so it cannot forge one.
  var found = (world + hud).match(/data-mt-id="[a-z][a-z0-9_-]{0,31}"/g) || [];
  for (var f = 0; f < found.length; f++) ids[found[f].slice(12, -1)] = 1;
  var tg = [], tracks = Array.isArray(b.tracks) ? b.tracks : [];
  tg = tg.concat(_moStitch(b, ids, bpm, durN, st)); // scene hand-overs first, so a track you write on the same layer wins
  if (tracks.length > 40) { st.dropped += tracks.length - 40; tracks = tracks.slice(0, 40); }
  for (var j = 0; j < tracks.length; j++) {
    var tr = tracks[j], tid = tr && typeof tr === 'object' ? _moId(tr.target) : '';
    if (!tid || !ids[tid] || !Array.isArray(tr.keys)) { st.dropped++; continue; }
    var keys = tr.keys;
    if (keys.length > 48) { st.dropped += keys.length - 48; keys = keys.slice(0, 48); }
    var pjs = _moTrackJs(keys, _MO_PROPS, _MO_PROP_ORDER, durN, bpm, defEase, st);
    if (pjs) tg.push('{i:"' + tid + '",p:{' + pjs + '}}');
  }
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
  try { return _moTimeline(b); } finally { _moTlDepth--; }
};

// ─── topic-free primitives (added after the first composition outside the SaaS demo) ──
// motion_layer groups children into a scene; motion_text, motion_shape and motion_counter draw type, forms and numbers
// from the stage theme (--mt-ink / --mt-acc / --mt-mute, set by motion_timeline) and move with --p like the demo kit.
// Standalone they render their FINAL state.
var _MO_REVEAL = {rise: 1, drop: 1, fade: 1, blur: 1, mask: 1};
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
  var mode = (b.mode === 'block' || b.mode === 'words' || b.mode === 'chars') ? b.mode : 'lines';
  var reveal = (typeof b.reveal === 'string' && Object.prototype.hasOwnProperty.call(_MO_REVEAL, b.reveal)) ? b.reveal : 'rise';
  var S = _ffInt(b.overlap, 3, 1, 8), track = _ffNum(b.tracking, -0.02, -0.1, 0.5, 3), lh = _ffNum(b.line_height, 1.05, 0.8, 2, 2);
  var color = _moInk(b, 'color', 'var(--mt-ink,#f1f5f9)'), align = _ffPick(b.align, _MO_ALIGN, 'start'), upper = b.uppercase === true;
  var accent = _moInk(b, 'accent', 'var(--mt-acc,#38bdf8)');
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
  var N = 0, k;
  for (k = 0; k < units.length; k++) N += units[k].chars ? units[k].c.length : 1;
  if (N > 120) { units = [{c: joined(' '), block: true}]; N = 1; mode = 'block'; }
  var idx = 0;
  function uvar(n) { return '--u:clamp(0,calc((var(--p,1)*' + (N + S) + ' - ' + n + ')/' + S + '),1);'; }
  function wrapUnit(inner, n, blockish) {
    var inl = blockish ? 'display:block;' : 'display:inline-block;';
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
  return '<div style="font-family:' + font + ';font-size:' + size + 'px;font-weight:' + weight + ';line-height:' + lh + ';letter-spacing:' + track + 'em;color:' + color + ';text-align:' + align + ';' + (upper ? 'text-transform:uppercase;' : '') + (mode === 'lines' ? 'white-space:nowrap;' : '') + 'width:100%;">'
    + _moSr(_moPlain(lines.join(' ')))
    + '<span aria-hidden="true" style="display:block;">' + out + '</span></div>';
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
  var lsize = _ffInt(b.label_size, Math.max(11, Math.floor(size / 5)), 8, 80);
  return '<div style="width:100%;text-align:' + align + ';">'
    + '<div style="font-family:' + font + ';font-size:' + size + 'px;font-weight:' + weight + ';line-height:1;letter-spacing:-0.02em;color:' + color + ';font-variant-numeric:tabular-nums;">' + _moCount(to, dec, pre, suf, '', from) + '</div>'
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
  return '<div style="display:flex;justify-content:' + jc + ';width:100%;">'
    + '<div style="display:inline-flex;align-items:center;gap:0.55em;box-sizing:border-box;padding:0.55em 1.3em;border-radius:999px;border:1px solid ' + _MO_MIX_LINE + ';background:' + (fill || _MO_MIX_FILL) + ';color:' + color + ';font-family:' + _MO_SANS + ';font-size:' + size + 'px;font-weight:600;line-height:1.1;white-space:nowrap;opacity:clamp(0,var(--p,1),1);transform:translateY(calc((1 - clamp(0,var(--p,1),1))*0.5em));">'
    + _moSr(_moPlain(text))
    + '<span aria-hidden="true" style="display:inline-flex;align-items:center;gap:0.55em;">' + (icon ? '<span style="color:' + acc + ';">' + _esc(icon) + '</span>' : '') + '<span>' + _moRuns(_moChars(text), acc) + '</span></span></div></div>';
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

// ─── stitching: scenes that hand over to each other ─────────────────────────────────────────────────────────────────
// motion_timeline `scenes: [{layer, t|beat, transition?}]` turns a list of scene layers into the tracks that cross them, so a
// film is stitched by declaring where each scene starts instead of hand-writing four tracks per cut. The window between one
// scene's start and `overlap` seconds later is the hand-over: the old scene leaves while the new one arrives. Your own tracks
// on the same layer are applied after, and win.
var _MO_STITCH = {
  'cut': 1, 'dissolve': 1, 'push': 1, 'zoom-through': 1, 'blur': 1, 'rise': 1
};
var _MO_STITCH_IN = {
  'dissolve': {opacity: 0}, 'push': {opacity: 0, x: 8}, 'zoom-through': {opacity: 0, scale: 0.9, blur: 10}, 'blur': {opacity: 0, blur: 16}, 'rise': {opacity: 0, y: 6}
};
var _MO_STITCH_OUT = {
  'dissolve': {opacity: 0}, 'push': {opacity: 0, x: -8}, 'zoom-through': {opacity: 0, scale: 1.12, blur: 10}, 'blur': {opacity: 0, blur: 16}, 'rise': {opacity: 0, y: -6}
};
var _MO_REST = {opacity: 1, x: 0, y: 0, scale: 1, blur: 0};
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
function _moStitch(b, ids, bpm, dur, st) {
  var src = Array.isArray(b.scenes) ? b.scenes : [], sc = [], i, own = Object.prototype.hasOwnProperty;
  if (src.length > 12) { st.dropped += src.length - 12; src = src.slice(0, 12); }
  for (i = 0; i < src.length; i++) {
    var s = src[i], id = s && typeof s === 'object' ? _moId(s.layer) : '', t = id && ids[id] ? _moAt(s, bpm, dur) : null;
    if (t === null) { st.dropped++; continue; }
    sc.push({id: id, t: t, i: i, fx: (typeof s.transition === 'string' && own.call(_MO_STITCH, s.transition)) ? s.transition : ''});
  }
  sc.sort(function(a, c) { return a.t - c.t || a.i - c.i; });
  var dfx = (typeof b.stitch === 'string' && own.call(_MO_STITCH, b.stitch)) ? b.stitch : 'dissolve', ov = parseFloat(_ffNum(b.overlap, 0.6, 0, 3, 2)), out = [];
  for (i = 0; i < sc.length; i++) {
    var cur = sc[i], nxt = i + 1 < sc.length ? sc[i + 1] : null, keys = [], fin = cur.fx || dfx, fout = nxt ? (nxt.fx || dfx) : '', p, from;
    if (cur.t > 0) {
      if (fin === 'cut') { _moStitchKey(keys, 0, {opacity: 0}); _moStitchKey(keys, cur.t, {opacity: 1}, 'hold'); }
      else { from = _MO_STITCH_IN[fin]; _moStitchKey(keys, 0, from); _moStitchKey(keys, cur.t, from); _moStitchKey(keys, cur.t + ov, _MO_REST, 'expo-out'); }
    }
    if (nxt) {
      if (fout === 'cut') _moStitchKey(keys, nxt.t, {opacity: 0}, 'hold');
      else { _moStitchKey(keys, nxt.t, _MO_REST); _moStitchKey(keys, nxt.t + ov, _MO_STITCH_OUT[fout], 'accelerate'); }
    }
    if (!keys.length) continue;
    var props = {};
    for (var q = 0; q < keys.length; q++) for (p in keys[q]) if (p !== 't' && p !== 'ease') props[p] = 1;
    // a rest key may carry props this scene never moves: keep only the props some transition really animates
    var live = {};
    for (p in props) { var seenVals = {}, cnt = 0; for (q = 0; q < keys.length; q++) if (own.call(keys[q], p) && !own.call(seenVals, keys[q][p])) { seenVals[keys[q][p]] = 1; cnt++; } if (cnt > 1) live[p] = 1; }
    var clean = [];
    for (q = 0; q < keys.length; q++) { var kk = {t: keys[q].t}; for (p in live) if (own.call(keys[q], p)) kk[p] = keys[q][p]; if (keys[q].ease) kk.ease = keys[q].ease; clean.push(kk); }
    var pjs = _moTrackJs(clean, _MO_PROPS, _MO_PROP_ORDER, dur, bpm, 'standard', st);
    if (pjs) out.push('{i:"' + cur.id + '",p:{' + pjs + '}}');
  }
  return out;
}
