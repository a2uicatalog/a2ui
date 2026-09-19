// atoms_typography.gs — Typography-forward atoms, dark-native, Meet Stage ready
// All animations auto-play (no click required) — designed for passive viewing.
// Surfaces: G M W

// ── gradient_heading ──────────────────────────────────────────────────────────
// Gradient-fill heading. Simpler than dark_hero — just the text, no padding/CTA.
// Use inside content flow between other atoms.
// Fields:
//   text     — heading text
//   gradient — CSS gradient (default indigo→violet→pink)
//   size     — font-size (default clamp(1.8rem,4vw,3rem))
//   weight   — font-weight (default 900)
//   align    — text-align (default left)
//   margin   — CSS margin (default 16px 0 6px)
_RENDERERS['gradient_heading'] = function(b) {
  var text     = b.text     || 'Heading';
  var gradient = b.gradient || 'linear-gradient(135deg,#6366f1 0%,#a78bfa 50%,#ec4899 100%)';
  var size     = b.size     || 'clamp(1.8rem,4vw,3rem)';
  var weight   = b.weight   || 900;
  var align    = b.align    || 'left';
  var margin   = b.margin   || '16px 0 6px';

  return '<div style="margin:' + _esc(margin) + ';text-align:' + _esc(align) + ';">' +
    '<span style="' +
      'font-size:' + _esc(size) + ';' +
      'font-weight:' + weight + ';' +
      'line-height:1.1;' +
      'background:' + gradient + ';' +
      '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;' +
      'display:inline-block;">' +
    _esc(text) + '</span>' +
    '</div>';
};

// ── display_quote ─────────────────────────────────────────────────────────────
// Large typographic quote — decorative quotation mark, text, attribution.
// Designed for dark; works on light. Great for Meet Stage title slides.
// Fields:
//   text        — quote body
//   attribution — name / source (optional)
//   colour      — accent colour for the quote mark and attribution (default #6366f1)
//   size        — font-size for quote text (default clamp(1.4rem,3vw,2.2rem))
//   align       — center or left (default center)
_RENDERERS['display_quote'] = function(b) {
  var text        = b.text        || '"Something worth saying."';
  var attribution = b.attribution || '';
  var colour      = b.colour      || '#6366f1';
  var size        = b.size        || 'clamp(1.4rem,3vw,2.2rem)';
  var align       = b.align       || 'center';

  return '<div style="padding:40px 24px;text-align:' + _esc(align) + ';position:relative;">' +
    '<div style="font-size:5rem;line-height:0.6;color:' + _esc(colour) + ';' +
      'opacity:0.35;font-family:Georgia,serif;margin-bottom:16px;' +
      (align === 'center' ? 'text-align:center;' : '') +
    '">“</div>' +
    '<p style="margin:0;font-size:' + _esc(size) + ';font-weight:700;line-height:1.45;' +
      'color:rgba(255,255,255,0.92);font-style:italic;letter-spacing:-0.01em;">' +
    _esc(text) + '</p>' +
    (attribution
      ? '<div style="margin-top:20px;font-size:0.8rem;color:' + _esc(colour) + ';' +
        'font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">' +
        '— ' + _esc(attribution) + '</div>'
      : '') +
    '</div>';
};

// ── split_stat ────────────────────────────────────────────────────────────────
// Two-column: large glowing stat on the left, heading + body text on the right.
// Classic presentation / keynote layout. Great for Meet Stage.
// Fields:
//   value       — the stat number / short value
//   prefix      — text before value (e.g. "$", "~")
//   suffix      — text after value (e.g. "%", "k", "+")
//   heading     — right-side heading
//   body        — right-side paragraph text
//   colour      — stat glow colour (default #6366f1)
//   flip        — put stat on right (default false)
_RENDERERS['split_stat'] = function(b) {
  var value   = String(b.value !== undefined ? b.value : '—');
  var prefix  = b.prefix  || '';
  var suffix  = b.suffix  || '';
  var heading = b.heading || '';
  var body    = b.body    || '';
  var colour  = b.colour  || '#6366f1';
  var flip    = b.flip    || false;

  var statHtml =
    '<div style="flex:0 0 auto;text-align:center;padding:0 24px;">' +
    '<div style="font-size:clamp(3rem,8vw,5rem);font-weight:900;line-height:1;color:#fff;' +
      'text-shadow:0 0 20px ' + colour + ',0 0 60px ' + colour + '55;">' +
    (prefix ? '<span style="font-size:0.45em;opacity:0.7;vertical-align:0.55em;">' + _esc(prefix) + '</span>' : '') +
    _esc(value) +
    (suffix ? '<span style="font-size:0.4em;opacity:0.7;vertical-align:0.6em;margin-left:2px;">' + _esc(suffix) + '</span>' : '') +
    '</div>' +
    '<div style="width:60px;height:3px;margin:10px auto 0;border-radius:99px;' +
      'background:' + colour + ';box-shadow:0 0 16px ' + colour + ';"></div>' +
    '</div>';

  var textHtml =
    '<div style="flex:1;min-width:0;padding:0 8px;' +
      'border-left:1px solid rgba(255,255,255,0.08);' +
      (flip ? 'border-left:none;border-right:1px solid rgba(255,255,255,0.08);' : '') + '">' +
    (heading ? '<div style="font-size:1.1rem;font-weight:800;color:rgba(255,255,255,0.92);margin-bottom:8px;">' + _esc(heading) + '</div>' : '') +
    (body    ? '<div style="font-size:0.88rem;color:rgba(255,255,255,0.5);line-height:1.65;">' + _esc(body) + '</div>' : '') +
    '</div>';

  var left  = flip ? textHtml : statHtml;
  var right = flip ? statHtml : textHtml;

  return '<div style="display:flex;align-items:center;gap:24px;padding:28px 0;">' +
    left + right +
    '</div>';
};

// ── word_reveal ───────────────────────────────────────────────────────────────
// Words appear one by one with a fade-up animation — auto-plays on load.
// Great for Meet Stage title slides and reveal moments.
// Fields:
//   text     — the text to reveal word by word
//   colour   — text colour (default rgba(255,255,255,0.92))
//   gradient — optional CSS gradient applied to the whole line (overrides colour)
//   size     — font-size (default clamp(2rem,5vw,3.5rem))
//   weight   — font-weight (default 800)
//   delay    — seconds between each word (default 0.12)
//   align    — text-align (default center)
_RENDERERS['word_reveal'] = function(b) {
  var text     = b.text     || 'Your message here';
  var colour   = b.colour   || 'rgba(255,255,255,0.92)';
  var gradient = b.gradient || '';
  var size     = b.size     || 'clamp(2rem,5vw,3.5rem)';
  var weight   = b.weight   || 800;
  var delay    = b.delay    !== undefined ? b.delay : 0.12;
  var align    = b.align    || 'center';
  var uid      = 'wr' + Math.random().toString(36).substr(2, 5);

  var words   = text.split(' ');
  var spans   = '';
  for (var i = 0; i < words.length; i++) {
    var d = (i * delay).toFixed(2);
    spans += '<span style="display:inline-block;opacity:0;transform:translateY(14px);' +
      'animation:' + uid + ' 0.45s cubic-bezier(0.22,1,0.36,1) ' + d + 's forwards;">' +
      _esc(words[i]) + '&nbsp;</span>';
  }

  var textStyle = gradient
    ? 'background:' + gradient + ';-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'
    : 'color:' + colour + ';';

  return '<style>@keyframes ' + uid + '{to{opacity:1;transform:translateY(0);}}</style>' +
    '<div style="padding:32px 0;text-align:' + _esc(align) + ';">' +
    '<div style="font-size:' + _esc(size) + ';font-weight:' + weight + ';line-height:1.25;' +
      textStyle + '">' +
    spans +
    '</div>' +
    '</div>';
};

// ── section_label ─────────────────────────────────────────────────────────────
// Uppercase section marker with a short gradient accent line.
// Use between content sections on dark pages.
// Fields:
//   text   — label text (uppercased automatically)
//   colour — accent colour (default #6366f1)
//   margin — vertical margin (default 24px 0 12px)
_RENDERERS['section_label'] = function(b) {
  var text   = b.text   || 'Section';
  var colour = b.colour || '#6366f1';
  var margin = b.margin || '24px 0 12px';

  return '<div style="margin:' + _esc(margin) + ';display:flex;align-items:center;gap:12px;">' +
    '<div style="width:24px;height:2px;border-radius:99px;' +
      'background:' + _esc(colour) + ';box-shadow:0 0 8px ' + _esc(colour) + ';flex-shrink:0;"></div>' +
    '<span style="font-size:0.7rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;' +
      'color:' + _esc(colour) + ';">' + _esc(text) + '</span>' +
    '</div>';
};

// ── count_up_stat ─────────────────────────────────────────────────────────────
// Stat number that counts up from 0 to target on page load. Auto-plays.
// Fields:
//   value    — target number (integer)
//   label    — descriptor below
//   prefix   — text before number (e.g. "$")
//   suffix   — text after number (e.g. "%", "k")
//   colour   — glow colour (default #6366f1)
//   duration — count-up duration ms (default 1800)
//   size     — font-size (default 4rem)
_RENDERERS['count_up_stat'] = function(b) {
  var target   = parseInt(b.value)   || 0;
  var label    = b.label    || '';
  var prefix   = b.prefix   || '';
  var suffix   = b.suffix   || '';
  var colour   = b.colour   || '#6366f1';
  var duration = b.duration || 1800;
  var size     = b.size     || '4rem';
  var uid      = 'cu' + Math.random().toString(36).substr(2, 5);

  return '<div style="text-align:center;padding:32px 16px;">' +
    '<div style="font-size:' + _esc(size) + ';font-weight:900;line-height:1;color:#fff;' +
      'text-shadow:0 0 20px ' + colour + ',0 0 60px ' + colour + '55;">' +
    (prefix ? '<span style="font-size:0.45em;opacity:0.7;vertical-align:0.55em;">' + _esc(prefix) + '</span>' : '') +
    '<span id="' + uid + '">0</span>' +
    (suffix ? '<span style="font-size:0.4em;opacity:0.7;vertical-align:0.6em;margin-left:2px;">' + _esc(suffix) + '</span>' : '') +
    '</div>' +
    '<div style="width:60px;height:3px;margin:10px auto 0;border-radius:99px;' +
      'background:' + colour + ';box-shadow:0 0 16px ' + colour + ';"></div>' +
    (label ? '<div style="margin-top:12px;font-size:0.78rem;color:rgba(255,255,255,0.4);' +
      'text-transform:uppercase;letter-spacing:0.12em;">' + _esc(label) + '</div>' : '') +
    '</div>' +
    '<script>(function(){' +
      'var el=document.getElementById("' + uid + '");' +
      'if(!el)return;' +
      'var target=' + target + ',dur=' + duration + ',start=null;' +
      'function ease(t){return t<0.5?4*t*t*t:(t-1)*(2*t-2)*(2*t-2)+1;}' +
      'requestAnimationFrame(function tick(ts){' +
        'if(!start)start=ts;' +
        'var prog=Math.min(1,(ts-start)/dur);' +
        'el.textContent=Math.round(ease(prog)*target).toLocaleString();' +
        'if(prog<1)requestAnimationFrame(tick);' +
      '});' +
    '})();<\/script>';
};

// ── text_highlight ────────────────────────────────────────────────────────────
// Inline sentence where specific words are highlighted in gradient colour.
// Mark words with **double asterisks** in the text field.
// Fields:
//   text      — body text with **highlighted** words in asterisks
//   size      — font-size (default 1.2rem)
//   colour    — highlight gradient or solid colour (default #a78bfa)
//   weight    — base font weight (default 600)
//   align     — text-align (default left)
_RENDERERS['text_highlight'] = function(b) {
  var text   = b.text   || 'Build **anything** with just **JSON**.';
  var size   = b.size   || '1.2rem';
  var colour = b.colour || '#a78bfa';
  var weight = b.weight || 600;
  var align  = b.align  || 'left';

  // Split on **...** markers and render highlighted spans
  var parts  = text.split('**');
  var html   = '';
  for (var i = 0; i < parts.length; i++) {
    if (i % 2 === 0) {
      html += _esc(parts[i]);
    } else {
      html += '<span style="color:' + _esc(colour) + ';font-weight:800;">' + _esc(parts[i]) + '</span>';
    }
  }

  return '<p style="font-size:' + _esc(size) + ';font-weight:' + weight + ';' +
    'line-height:1.6;color:rgba(255,255,255,0.75);text-align:' + _esc(align) + ';margin:12px 0;">' +
    html + '</p>';
};

// ── reveal_line ───────────────────────────────────────────────────────────────
// A single line of text that sweeps in from left using a clip-path animation.
// Dramatic, Meet Stage-ready. Auto-plays.
// Fields:
//   text     — text content
//   colour   — text colour or CSS gradient keyword (default: gradient)
//   gradient — optional CSS gradient (default indigo→pink)
//   size     — font-size (default clamp(2.5rem,6vw,4rem))
//   weight   — font-weight (default 900)
//   duration — animation duration ms (default 800)
//   delay    — start delay ms (default 200)
_RENDERERS['reveal_line'] = function(b) {
  var text     = b.text     || 'Reveal';
  var gradient = b.gradient || 'linear-gradient(90deg,#6366f1,#a78bfa,#ec4899)';
  var size     = b.size     || 'clamp(2.5rem,6vw,4rem)';
  var weight   = b.weight   || 900;
  var dur      = (b.duration || 800);
  var del      = (b.delay    || 200);
  var uid      = 'rl' + Math.random().toString(36).substr(2, 5);
  var durS     = (dur / 1000).toFixed(2) + 's';
  var delS     = (del / 1000).toFixed(2) + 's';

  return '<style>' +
    '@keyframes ' + uid + '{' +
      'from{clip-path:inset(0 100% 0 0);}' +
      'to{clip-path:inset(0 0% 0 0);}' +
    '}' +
    '</style>' +
    '<div style="overflow:hidden;padding:4px 0;">' +
    '<div style="' +
      'font-size:' + _esc(size) + ';' +
      'font-weight:' + weight + ';' +
      'line-height:1.1;' +
      'background:' + gradient + ';' +
      '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;' +
      'animation:' + uid + ' ' + durS + ' cubic-bezier(0.77,0,0.18,1) ' + delS + ' both;' +
      'display:inline-block;' +
    '">' + _esc(text) + '</div>' +
    '</div>';
};

// ── math_block ────────────────────────────────────────────────────────────────
// Native MathML equation, typeset with `font-family: math` (STIX / Latin Modern
// Math) — no JS, no external library. The agent emits standard MathML; the
// surface draws it. Baseline browser support since 2023. Mirrors the Python
// renderer in renderers/web_article.py (_render_math_block).
//
// Fields:
//   mathml   required. MathML markup (inner content or a full <math> element).
//   caption  optional. Caption text shown below the equation.
//   number   optional. Equation number, right-aligned (e.g. "(1)").
//   align    optional. 'center' (default) | 'left'.
//   size     optional. Equation font-size (default clamp(1.1rem,2.5vw,1.6rem)).
function _sanitizeMathml(raw) {
  // Defense-in-depth: MathML can embed HTML via <annotation-xml> and carry
  // event handlers. Strip active content before passing markup through raw.
  return String(raw || '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<annotation-xml[\s\S]*?<\/annotation-xml>/gi, '')
    .replace(/\son\w+\s*=\s*"[^"]*"/gi, '')
    .replace(/\son\w+\s*=\s*'[^']*'/gi, '')
    .replace(/\son\w+\s*=\s*[^\s>]+/gi, '')
    .replace(/javascript:/gi, '');
}
_RENDERERS['math_block'] = function(b) {
  var mathml = _sanitizeMathml(b.mathml);
  if (mathml.toLowerCase().indexOf('<math') === -1) {
    mathml = '<math display="block">' + mathml + '</math>';
  }
  var align   = b.align === 'left' ? 'left' : 'center';
  var size    = b.size || 'clamp(1.1rem,2.5vw,1.6rem)';
  var number  = b.number ? _esc(b.number) : '';
  var caption = b.caption ? _esc(b.caption) : '';

  var numHtml = number
    ? '<span style="position:absolute;right:0;top:50%;transform:translateY(-50%);' +
      'font-size:0.9rem;color:rgba(148,163,184,0.9);font-family:ui-monospace,monospace;">' +
      number + '</span>'
    : '';
  var capHtml = caption
    ? '<div style="margin-top:8px;font-size:0.82rem;color:rgba(148,163,184,0.9);' +
      'text-align:' + align + ';line-height:1.5;">' + caption + '</div>'
    : '';

  return '<div class="a2ui-math" style="margin:1.5rem 0;position:relative;">' +
    '<div style="text-align:' + align + ';' +
      'font-family:math,\'Latin Modern Math\',\'STIX Two Math\',serif;' +
      'font-size:' + _esc(size) + ';color:var(--text,#1f2937);overflow-x:auto;">' + mathml + '</div>' +
    numHtml + capHtml +
    '</div>';
};


// ── conviction typography: weighted_words / stance / receipt / changed_mind ──
// Built 2026-09-19 for sharing a point of view (posts, cover slides, chat
// cards) rather than decorating one. Each is a typographic OBJECT an agent can
// fill: the agent chooses per-word emphasis (weighted_words), states a claim
// with calibrated confidence that the type itself encodes (stance), prints
// evidence lines under a claim like a till receipt with the newest line
// printing in (receipt -- same stateless "resend the full list, only the last
// item animates" rule as agent_sketchpad), or records a belief it changed
// (changed_mind). CSS + at most one tiny inline script; no canvas; light or
// dark via the theme enum. All copy is escaped; every option is an enum or a
// clamped number. Python twins in renderers/web_article.py emit identical
// markup modulo uid -- tests/test_conviction_type.py. Edit BOTH.
var _CV_STANCE_JS =
  '(function(){var s=document.getElementById("st-s-%%UID%%"),t=document.getElementById("st-t-%%UID%%"),r=document.getElementById("st-r-%%UID%%"),l=document.getElementById("st-l-%%UID%%");if(!s||!t)return;' +
  'function pad(n){return n<10?"0"+n:""+n;}' +
  'function ap(p){var w=300+Math.floor((p*6+50)/100)*100,sh=140+Math.floor(p*16/10),ls=2-Math.floor(p*5/100),op=60+Math.floor(p*4/10);' +
  't.style.fontWeight=w;t.style.fontSize=Math.floor(sh/100)+"."+pad(sh%100)+"rem";t.style.letterSpacing=(ls<0?"-0."+pad(-ls):"0."+pad(ls))+"em";t.style.opacity=op>=100?"1":"0."+pad(op);' +
  'if(r)r.style.width=p+"%";if(l)l.textContent="confidence "+p+"%";}' +
  's.addEventListener("input",function(){ap(parseInt(s.value,10)||0);});})();';
var _CV_VOICES = {
  display: 'system-ui,-apple-system,Segoe UI,Helvetica Neue,Arial,sans-serif',
  serif: 'Georgia,Times New Roman,serif',
  mono: 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'
};
var _CV_THEMES = {
  dark:  {bg: '#0b0d12', ink: '#f1f5f9', mute: '#94a3b8', line: '#1f2430', soft: '#12151c'},
  light: {bg: '#ffffff', ink: '#0f172a', mute: '#64748b', line: '#e2e8f0', soft: '#f8fafc'}
};
function _cvStr(v, max) { return (typeof v === 'string' ? v : (typeof v === 'number' ? String(v) : '')).trim().slice(0, max); }
function _cvPad(n) { return n < 10 ? '0' + n : '' + n; }
function _cvCard(th, inner, extra) {
  return '<div style="margin:1rem 0;border-radius:16px;padding:32px 36px;background:' + th.bg + ';color:' + th.ink + ';border:1px solid ' + th.line + ';' + (extra || '') + '">' + inner + '</div>';
}
// djb2 over UTF-16 code units, then an LCG -- deterministic on both renderers.
function _cvHash(s) {
  var h = 5381;
  for (var i = 0; i < s.length; i++) h = (Math.imul(h, 33) + s.charCodeAt(i)) >>> 0;
  return h;
}
function _cvNext(h) { return (Math.imul(h, 1103515245) + 12345) >>> 0; }

_RENDERERS['weighted_words'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var th = _ffPick(b.theme, _CV_THEMES, 'dark');
  var font = _ffPick(b.voice, _CV_VOICES, 'display');
  var accent = _ffHex(b.accent, '#38bdf8');
  var align = _ffPick(b.align, {left: 'left', center: 'center'}, 'left');
  var animate = b.animate === false ? false : true;
  var src = Array.isArray(b.words) ? b.words : _cvStr(b.text, 600).split(/\s+/).filter(function(w) { return w; }).map(function(w) { return {text: w, weight: 2}; });
  var words = [];
  for (var i = 0; i < src.length && words.length < 40; i++) {
    var w = src[i], txt = _cvStr(typeof w === 'string' ? w : (w && w.text), 24);
    if (!txt) continue;
    words.push({text: txt, weight: _ffInt(typeof w === 'string' ? 2 : (w && w.weight), 2, 1, 5)});
  }
  if (!words.length) words = [{text: 'A2UI', weight: 5}];
  var scale = {1: '0.75em', 2: '1em', 3: '1.35em', 4: '1.8em', 5: '2.4em'};
  var fw = {1: '400', 2: '500', 3: '700', 4: '800', 5: '900'};
  var op = {1: '0.55', 2: '0.8', 3: '1', 4: '1', 5: '1'};
  var out = '';
  for (var j = 0; j < words.length; j++) {
    var x = words[j];
    out += '<span title="weight ' + x.weight + '/5" style="display:inline-block;vertical-align:baseline;margin:0 0.28em 0.1em 0;font-size:' + scale[x.weight] + ';font-weight:' + fw[x.weight] + ';opacity:' + op[x.weight]
      + (x.weight === 5 ? ';color:' + accent : '')
      + (animate ? ';animation:ww-' + uid + ' 0.6s cubic-bezier(0.2,0.8,0.2,1) ' + (j * 9) + 'ms both;--ww-d:' + (x.weight * 0.35) + 'em' : '')
      + ';">' + _esc(x.text) + '</span>';
  }
  return (animate ? '<style>@keyframes ww-' + uid + '{from{opacity:0;transform:translateY(calc(var(--ww-d) * -1));}to{transform:none;}}</style>' : '')
    + _cvCard(th, '<div style="font-family:' + font + ';font-size:clamp(1.3rem,3.2vw,2.2rem);line-height:1.15;letter-spacing:-0.01em;text-align:' + align + ';">' + out + '</div>');
};

function _cvConfidence(v) {
  var c = typeof v === 'number' ? v : parseFloat(v);
  if (isNaN(c)) c = 0.5;
  if (c > 1) c = c / 100;
  c = Math.max(0, Math.min(1, c));
  return Math.floor(c * 100 + 0.5);
}
_RENDERERS['stance'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var th = _ffPick(b.theme, _CV_THEMES, 'dark');
  var font = _ffPick(b.voice, _CV_VOICES, 'display');
  var accent = _ffHex(b.accent, '#38bdf8');
  var claim = _cvStr(b.claim, 200) || 'A2UI';
  var because = _cvStr(b.because, 300), unless = _cvStr(b.unless, 300);
  var inter = b.interactive === false ? false : true;
  var p = _cvConfidence(b.confidence);
  var w = 300 + Math.floor((p * 6 + 50) / 100) * 100, sh = 140 + Math.floor(p * 16 / 10), ls = 2 - Math.floor(p * 5 / 100), op = 60 + Math.floor(p * 4 / 10);
  var size = Math.floor(sh / 100) + '.' + _cvPad(sh % 100) + 'rem';
  var spacing = (ls < 0 ? '-0.' + _cvPad(-ls) : '0.' + _cvPad(ls)) + 'em';
  var opacity = op >= 100 ? '1' : '0.' + _cvPad(op);
  var inner = '<div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:' + th.mute + ';margin-bottom:14px;">stance</div>'
    + '<div id="st-t-' + uid + '" style="font-family:' + font + ';font-weight:' + w + ';font-size:' + size + ';letter-spacing:' + spacing + ';opacity:' + opacity + ';line-height:1.12;transition:font-size 0.25s,letter-spacing 0.25s,opacity 0.25s,font-weight 0.25s;">' + _esc(claim) + '</div>'
    + '<div style="margin-top:18px;height:3px;background:' + th.line + ';border-radius:2px;overflow:hidden;"><div id="st-r-' + uid + '" style="height:100%;width:' + p + '%;background:' + accent + ';transition:width 0.25s;"></div></div>'
    + '<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:8px;font-family:' + _CV_VOICES.mono + ';font-size:0.72rem;color:' + th.mute + ';">'
    + '<span id="st-l-' + uid + '">confidence ' + p + '%</span>'
    + (inter ? '<label style="display:flex;align-items:center;gap:8px;"><span>try it</span><input id="st-s-' + uid + '" type="range" min="0" max="100" value="' + p + '" aria-label="confidence" style="width:120px;accent-color:' + accent + ';"></label>' : '')
    + '</div>'
    + (because ? '<div style="margin-top:18px;font-size:0.98rem;line-height:1.55;color:' + th.ink + ';"><span style="color:' + th.mute + ';">because</span> ' + _esc(because) + '</div>' : '')
    + (unless ? '<div style="margin-top:10px;font-size:0.9rem;line-height:1.5;font-style:italic;color:' + th.mute + ';">I would change my mind if ' + _esc(unless) + '</div>' : '')
    + (inter ? '<script>' + _CV_STANCE_JS.replace(/%%UID%%/g, uid) + '<\/script>' : '');
  return _cvCard(th, inner);
};

_RENDERERS['receipt'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var accent = _ffHex(b.accent, '#4338ca');
  var claim = _cvStr(b.claim, 200) || 'A2UI';
  var merchant = _cvStr(b.merchant, 40) || 'EVIDENCE RECEIPT';
  var issued = _cvStr(b.issued, 40);
  var footer = _cvStr(b.footer, 120) || 'Sources listed. No unsourced stats.';
  var totalLabel = _cvStr(b.total_label, 30) || 'CONFIDENCE';
  var printLast = b.print_last === false ? false : true;
  var src = Array.isArray(b.items) ? b.items : [];
  var items = [];
  for (var i = 0; i < src.length && items.length < 24; i++) {
    var it = src[i], txt = _cvStr(typeof it === 'string' ? it : (it && it.text), 160);
    if (!txt) continue;
    items.push({text: txt, source: _cvStr(it && it.source, 60), url: (it && typeof it.url === 'string' && /^https?:\/\//.test(it.url)) ? it.url.slice(0, 300) : ''});
  }
  var total = b.total === undefined || b.total === null ? (items.length + (items.length === 1 ? ' ITEM' : ' ITEMS')) : _cvConfidence(b.total) + '%';
  var mono = _CV_VOICES.mono;
  var rows = '';
  for (var j = 0; j < items.length; j++) {
    var x = items[j], last = printLast && j === items.length - 1;
    var srcHtml = x.source ? (x.url ? '<a href="' + _esc(x.url) + '" target="_blank" rel="noopener" style="color:' + accent + ';text-decoration:none;">' + _esc(x.source) + '</a>' : '<span style="color:#475569;">' + _esc(x.source) + '</span>') : '';
    rows += '<div style="display:flex;align-items:baseline;gap:8px;padding:5px 0;' + (last ? 'animation:rc-' + uid + ' 0.7s steps(7) both;' : '') + '">'
      + '<span style="flex:0 0 auto;color:#94a3b8;">' + _cvPad(j + 1) + '</span>'
      + '<span style="flex:1 1 auto;min-width:0;">' + _esc(x.text) + '</span>'
      + (srcHtml ? '<span style="flex:0 0 auto;max-width:38%;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + srcHtml + '</span>' : '')
      + '</div>';
  }
  // barcode: deterministic from the claim, 48 bars
  var h = _cvHash(claim), x0 = 0, bars = '';
  for (var k = 0; k < 48; k++) {
    h = _cvNext(h);
    var bw = 1 + (h >>> 8) % 3, gap = 1 + (h >>> 16) % 2;
    bars += '<rect x="' + x0 + '" y="0" width="' + bw + '" height="30"/>';
    x0 += bw + gap;
  }
  var inner = '<div style="font-size:0.72rem;letter-spacing:0.16em;text-align:center;color:#475569;">' + _esc(merchant) + '</div>'
    + (issued ? '<div style="font-size:0.7rem;text-align:center;color:#94a3b8;margin-top:2px;">' + _esc(issued) + '</div>' : '')
    + '<div style="margin:16px 0 12px;font-family:' + _CV_VOICES.display + ';font-weight:900;font-size:clamp(1.25rem,2.8vw,1.8rem);line-height:1.15;letter-spacing:-0.02em;color:#0f172a;">' + _esc(claim) + '</div>'
    + '<div style="border-top:1px dashed #94a3b8;margin:10px 0;"></div>'
    + (rows || '<div style="color:#94a3b8;padding:5px 0;">(no evidence yet)</div>')
    + '<div style="border-top:1px dashed #94a3b8;margin:10px 0;"></div>'
    + '<div style="display:flex;justify-content:space-between;font-weight:700;font-size:0.95rem;"><span>' + _esc(totalLabel) + '</span><span style="color:' + accent + ';">' + _esc(total) + '</span></div>'
    + '<div style="margin:16px auto 6px;max-width:260px;"><svg viewBox="0 0 ' + x0 + ' 30" width="100%" height="30" preserveAspectRatio="none" fill="#0f172a" aria-hidden="true">' + bars + '</svg></div>'
    + '<div style="font-size:0.68rem;text-align:center;color:#94a3b8;">' + _esc(footer) + '</div>';
  return '<style>@keyframes rc-' + uid + '{from{opacity:0;transform:translateY(-10px);}to{opacity:1;transform:none;}}</style>'
    + '<div style="margin:1rem auto;max-width:420px;background:#fdfdfb;color:#1e293b;font-family:' + mono + ';font-size:0.82rem;line-height:1.45;padding:26px 24px 22px;border-radius:4px;box-shadow:0 10px 30px rgba(0,0,0,0.18);position:relative;">'
    + inner
    + '<div style="position:absolute;left:0;right:0;bottom:-10px;height:10px;background:linear-gradient(-45deg,transparent 7px,#fdfdfb 0) 0 0/14px 10px repeat-x,linear-gradient(45deg,transparent 7px,#fdfdfb 0) 7px 0/14px 10px repeat-x;"></div>'
    + '</div>';
};

_RENDERERS['changed_mind'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var th = _ffPick(b.theme, _CV_THEMES, 'dark');
  var font = _ffPick(b.voice, _CV_VOICES, 'display');
  var accent = _ffHex(b.accent, '#38bdf8');
  var animate = b.animate === false ? false : true;
  var before = _cvStr(b.before, 200) || 'A2UI is a Google thing';
  var after = _cvStr(b.after, 200) || 'A2UI is a document contract';
  var since = _cvStr(b.since, 200);
  var css = animate
    ? '<style>@keyframes cm-s-' + uid + '{from{transform:scaleX(0);}to{transform:scaleX(1);}}@keyframes cm-a-' + uid + '{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:none;}}</style>'
    : '';
  var inner = '<div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:' + th.mute + ';">I used to think</div>'
    + '<div style="position:relative;display:inline-block;margin:8px 0 22px;font-family:' + _CV_VOICES.serif + ';font-style:italic;font-size:clamp(1.1rem,2.4vw,1.5rem);line-height:1.3;color:' + th.mute + ';">' + _esc(before)
    + '<span style="position:absolute;left:0;right:0;top:55%;height:2px;background:' + th.mute + ';transform-origin:left center;' + (animate ? 'animation:cm-s-' + uid + ' 0.5s ease-out 0.5s both;' : '') + '"></span></div>'
    + '<div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:' + accent + ';">Now I think</div>'
    + '<div style="margin-top:8px;font-family:' + font + ';font-weight:900;font-size:clamp(1.5rem,3.6vw,2.5rem);line-height:1.1;letter-spacing:-0.02em;' + (animate ? 'animation:cm-a-' + uid + ' 0.6s cubic-bezier(0.2,0.8,0.2,1) 1.1s both;' : '') + '">' + _esc(after) + '</div>'
    + (since ? '<div style="margin-top:18px;padding-left:12px;border-left:2px solid ' + accent + ';font-family:' + _CV_VOICES.mono + ';font-size:0.78rem;line-height:1.5;color:' + th.mute + ';">' + _esc(since) + '</div>' : '');
  return css + _cvCard(th, inner);
};


// ── agent_narrator ────────────────────────────────────────────────────────────
// Renderer for the schema entry authored alongside streaming-testbench's
// demos/story (the text-domain sibling of agent_sketchpad). Every beat except
// the LAST renders as already-shown; only the last types itself in -- the
// same stateless full-rerender rule as agent_sketchpad. Beat text is escaped
// first, then ONLY the declared markdown subset (**bold**, *italic*, `code`)
// is applied; raw HTML never survives. Over-cap beats (100 beats, 2000 chars
// each) are skipped with an HTML comment and a console warning, not a crash.
// The typing script walks the already-rendered HTML so tags and entities are
// emitted whole; under prefers-reduced-motion the beat shows in full at once.
// Python twin in renderers/web_article.py; tests/test_agent_narrator.py.
var _AGENT_NARRATOR_JS =
  '(function(){var el=document.getElementById("an-%%UID%%");if(!el)return;var full=el.innerHTML;' +
  'if(window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches)return;' +
  'var cur=document.getElementById("anc-%%UID%%"),i=0,out="";el.innerHTML="";' +
  'function tick(){if(i>=full.length){if(cur)cur.style.display="none";return;}' +
  'var ch=full.charAt(i);if(ch==="<"){var j=full.indexOf(">",i);out+=full.slice(i,j+1);i=j+1;}else if(ch==="&"){var k=full.indexOf(";",i);out+=full.slice(i,k+1);i=k+1;}else{out+=ch;i++;}' +
  'el.innerHTML=out;setTimeout(tick,ch===" "?26:18);}' +
  'tick();})();';
function _anMd(text) {
  return _esc(text).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*]+)\*/g, '<em>$1</em>').replace(/`([^`]+)`/g, '<code>$1</code>');
}
_RENDERERS['agent_narrator'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var beats = Array.isArray(b.beats) ? b.beats : [];
  var title = typeof b.title === 'string' ? b.title.trim() : '';
  var kept = [], skipped = 0;
  for (var i = 0; i < beats.length; i++) {
    var t = beats[i] && typeof beats[i].text === 'string' ? beats[i].text.trim() : '';
    if (!t) continue;
    if (kept.length >= 100 || t.length > 2000) { skipped++; continue; }
    kept.push(t);
  }
  var out = '';
  for (var j = 0; j < kept.length; j++) {
    var last = j === kept.length - 1;
    out += '<p style="margin:0 0 0.9em;font-size:1.05rem;line-height:1.7;">'
      + (last ? '<span id="an-' + uid + '">' + _anMd(kept[j]) + '</span><span id="anc-' + uid + '" style="display:inline-block;width:2px;height:1em;background:currentColor;vertical-align:text-bottom;margin-left:2px;animation:an-blink-' + uid + ' 0.8s step-end infinite;"></span>' : _anMd(kept[j]))
      + '</p>';
  }
  return '<div style="margin:1rem 0;">'
    + (title ? '<div style="font-size:1.25rem;font-weight:800;letter-spacing:-0.01em;margin-bottom:12px;">' + _esc(title) + '</div>' : '')
    + (skipped ? '<!-- agent_narrator: ' + skipped + ' beat(s) skipped, over the 100-beat / 2000-char cap -->' : '')
    + (out || '<p style="margin:0;color:#9ca3af;font-style:italic;">(no beats yet)</p>')
    + (kept.length ? '<style>@keyframes an-blink-' + uid + '{0%,100%{opacity:1;}50%{opacity:0;}}</style><script>' + _AGENT_NARRATOR_JS.replace(/%%UID%%/g, uid) + (skipped ? 'console.warn("agent_narrator: ' + skipped + ' beat(s) skipped, over cap");' : '') + '<\/script>' : '')
    + '</div>';
};
