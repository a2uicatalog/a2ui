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
