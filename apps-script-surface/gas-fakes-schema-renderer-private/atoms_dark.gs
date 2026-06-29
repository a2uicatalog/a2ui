// atoms_dark.gs — Dark-native atoms: designed for dark theme first
// All pure CSS/inline — no CDN, GAS CSP-safe, surfaces: G M W

// ── dark_hero ─────────────────────────────────────────────────────────────────
// Full-width hero section with gradient headline, subtext, optional badge + CTA.
// Fields:
//   heading   — main headline text
//   subtext   — supporting paragraph
//   badge     — small pill label above heading (e.g. "New · v2.0")
//   gradient  — CSS gradient for headline text (default indigo→violet→pink)
//   cta_label — call-to-action button text
//   cta_url   — CTA link href
//   align     — text alignment: center (default) or left
_RENDERERS['dark_hero'] = function(b) {
  var heading  = b.heading   || 'Build something beautiful';
  var subtext  = b.subtext   || '';
  var badge    = b.badge     || '';
  var gradient = b.gradient  || 'linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#ec4899 100%)';
  var ctaLabel = b.cta_label || '';
  var ctaUrl   = b.cta_url   || '#';
  var align    = b.align     || 'center';
  var isCenter = align === 'center';

  return '<div style="padding:56px 24px 48px;text-align:' + align + ';background:#0f172a;border-radius:12px;">' +
    (badge
      ? '<div style="display:inline-block;margin-bottom:18px;padding:5px 14px;' +
        'border:1px solid rgba(255,255,255,0.18);border-radius:99px;' +
        'font-size:0.72rem;color:rgba(255,255,255,0.55);letter-spacing:0.1em;text-transform:uppercase;">' +
        _esc(badge) + '</div><br>'
      : '') +
    '<h1 style="margin:0 0 18px;font-size:clamp(2rem,5vw,3.5rem);font-weight:900;line-height:1.1;' +
    'background:' + gradient + ';-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">' +
    _esc(heading) + '</h1>' +
    (subtext
      ? '<p style="margin:0 0 28px;font-size:1rem;color:rgba(255,255,255,0.5);' +
        'line-height:1.7;max-width:560px;' + (isCenter ? 'margin-left:auto;margin-right:auto;' : '') + '">' +
        _esc(subtext) + '</p>'
      : '') +
    (ctaLabel
      ? '<a href="' + _esc(ctaUrl) + '" target="_top" style="display:inline-block;padding:13px 30px;' +
        'border-radius:100px;background:' + gradient + ';color:#fff;font-weight:700;font-size:0.9rem;' +
        'text-decoration:none;box-shadow:0 0 40px rgba(99,102,241,0.35),0 2px 8px rgba(0,0,0,0.3);">' +
        _esc(ctaLabel) + '</a>'
      : '') +
    '</div>';
};

// ── glowing_stat ──────────────────────────────────────────────────────────────
// A dramatic metric display — large number with a radial colour glow beneath it.
// Designed to work as a standalone or inside a glass_card / gradient_border_card.
// Fields:
//   value   — the stat value (string or number)
//   label   — descriptor below the number
//   colour  — glow colour (default #6366f1)
//   size    — font size (default 4.5rem)
//   prefix  — text before value (e.g. "$", "~")
//   suffix  — text after value (e.g. "%", "k", "x")
//   glow    — enable glow effect (default true)
_RENDERERS['glowing_stat'] = function(b) {
  var value  = String(b.value !== undefined ? b.value : '—');
  var label  = b.label  || '';
  var colour = b.colour || '#6366f1';
  var size   = b.size   || '4.5rem';
  var prefix = b.prefix || '';
  var suffix = b.suffix || '';
  var glow   = b.glow   !== false;

  var glowStyle = glow
    ? 'text-shadow:0 0 20px ' + colour + ',0 0 60px ' + colour + '66,0 0 100px ' + colour + '33;'
    : '';

  return '<div style="text-align:center;padding:36px 20px;">' +
    '<div style="' + glowStyle +
    'font-size:' + _esc(size) + ';font-weight:900;line-height:1;color:#fff;letter-spacing:-0.02em;">' +
    (prefix ? '<span style="font-size:0.45em;opacity:0.7;vertical-align:0.55em;">' + _esc(prefix) + '</span>' : '') +
    _esc(value) +
    (suffix ? '<span style="font-size:0.4em;opacity:0.7;vertical-align:0.6em;margin-left:3px;">' + _esc(suffix) + '</span>' : '') +
    '</div>' +
    (glow
      ? '<div style="width:80px;height:4px;margin:12px auto 0;border-radius:99px;' +
        'background:' + colour + ';box-shadow:0 0 20px ' + colour + ',0 0 40px ' + colour + '66;"></div>'
      : '') +
    (label
      ? '<div style="margin-top:12px;font-size:0.78rem;color:rgba(255,255,255,0.4);' +
        'text-transform:uppercase;letter-spacing:0.12em;">' + _esc(label) + '</div>'
      : '') +
    '</div>';
};

// ── glass_card ────────────────────────────────────────────────────────────────
// Frosted glass card — backdrop-filter blur + semi-transparent background.
// Looks best over floating_orbs or any gradient/image background.
// Fields:
//   content — inner HTML
//   title   — optional heading
//   blur    — backdrop blur px (default 18)
//   bg      — background colour (default rgba(255,255,255,0.05))
//   border  — border colour (default rgba(255,255,255,0.1))
//   padding — inner padding (default 28px)
//   radius  — border radius (default 16px)
_RENDERERS['glass_card'] = function(b) {
  var content = b.content || '';
  var title   = b.title   || '';
  var blur    = b.blur    !== undefined ? b.blur : 18;
  var bg      = b.bg      || 'rgba(255,255,255,0.05)';
  var border  = b.border  || 'rgba(255,255,255,0.1)';
  var padding = b.padding || '28px';
  var radius  = b.radius  || '16px';

  return '<div style="' +
    'background:' + bg + ';' +
    'backdrop-filter:blur(' + blur + 'px);' +
    '-webkit-backdrop-filter:blur(' + blur + 'px);' +
    'border:1px solid ' + border + ';' +
    'border-radius:' + radius + ';' +
    'padding:' + padding + ';' +
    'position:relative;overflow:hidden;">' +
    (title
      ? '<div style="font-size:1rem;font-weight:700;color:rgba(255,255,255,0.9);margin-bottom:14px;">' +
        _esc(title) + '</div>'
      : '') +
    content +
    '</div>';
};

// ── gradient_border_card ──────────────────────────────────────────────────────
// Card with a gradient border — achieved via double-layer background-clip.
// Static by default; pairs well with dark_hero content inside.
// Fields:
//   content  — inner HTML
//   title    — optional heading
//   colours  — array of gradient stop colours (default indigo→violet→pink→amber)
//   bg       — inner background colour (default #0c0e1a)
//   angle    — gradient angle degrees (default 135)
//   padding  — inner padding (default 24px)
//   radius   — border radius (default 14px)
_RENDERERS['gradient_border_card'] = function(b) {
  var content = b.content || '';
  var title   = b.title   || '';
  var colours = b.colours || ['#6366f1','#8b5cf6','#ec4899','#f59e0b'];
  var bg      = b.bg      || '#0c0e1a';
  var angle   = b.angle   !== undefined ? b.angle : 135;
  var padding = b.padding || '24px';
  var radius  = b.radius  || '14px';
  var gradStr = 'linear-gradient(' + angle + 'deg,' + colours.join(',') + ')';

  return '<div style="padding:1.5px;border-radius:' + radius + ';background:' + gradStr + ';">' +
    '<div style="background:' + bg + ';border-radius:calc(' + radius + ' - 1.5px);padding:' + padding + ';">' +
    (title
      ? '<div style="font-size:1rem;font-weight:700;color:rgba(255,255,255,0.92);margin-bottom:12px;">' +
        _esc(title) + '</div>'
      : '') +
    content +
    '</div>' +
    '</div>';
};

// ── floating_orbs ─────────────────────────────────────────────────────────────
// Decorative animated gradient orbs — page-level atmospheric background layer.
// Place before content atoms on a dark page for depth.
// Fields:
//   orbs    — array of { colour, size, x, y } (x/y as % of container)
//   blur    — filter blur px (default 80)
//   opacity — orb opacity (default 0.22)
//   animate — enable float animation (default true)
_RENDERERS['floating_orbs'] = function(b) {
  var orbs    = b.orbs || [
    { colour: '#6366f1', size: 500, x: 10,  y: 15  },
    { colour: '#8b5cf6', size: 350, x: 75,  y: 55  },
    { colour: '#ec4899', size: 280, x: 45,  y: 85  }
  ];
  var blur    = b.blur    !== undefined ? b.blur    : 80;
  var opacity = b.opacity !== undefined ? b.opacity : 0.22;
  var animate = b.animate !== false;
  var uid     = 'orb' + Math.random().toString(36).substr(2, 5);

  var keyframes = animate
    ? '<style>@keyframes ' + uid + '{' +
      '0%,100%{transform:translate(-50%,-50%) scale(1);}' +
      '33%{transform:translate(calc(-50% + 30px),calc(-50% - 24px)) scale(1.06);}' +
      '66%{transform:translate(calc(-50% - 20px),calc(-50% + 28px)) scale(0.94);}' +
      '}</style>'
    : '';

  var orbDivs = '';
  for (var i = 0; i < orbs.length; i++) {
    var o = orbs[i];
    var sz  = o.size   || 300;
    var dur = (7 + i * 2.3).toFixed(1) + 's';
    var del = (i * 1.8).toFixed(1) + 's';
    orbDivs += '<div style="position:absolute;pointer-events:none;' +
      'width:' + sz + 'px;height:' + sz + 'px;' +
      'left:' + (o.x || 50) + '%;top:' + (o.y || 50) + '%;' +
      'transform:translate(-50%,-50%);' +
      'background:radial-gradient(circle at 40% 40%,' + _esc(o.colour) + ' 0%,transparent 68%);' +
      'filter:blur(' + blur + 'px);' +
      'opacity:' + opacity + ';' +
      (animate ? 'animation:' + uid + ' ' + dur + ' ease-in-out ' + del + ' infinite;' : '') +
      '"></div>';
  }

  return keyframes +
    '<div style="position:relative;height:0;overflow:visible;pointer-events:none;z-index:0;">' +
    orbDivs +
    '</div>';
};

// ── neon_text ─────────────────────────────────────────────────────────────────
// Text with CSS neon glow effect via layered text-shadow.
// Fields:
//   text    — the text to display
//   colour  — neon colour (default #6366f1)
//   size    — font size (default 2rem)
//   weight  — font weight (default 800)
//   align   — text-align (default center)
//   flicker — add flicker animation (default false)
_RENDERERS['neon_text'] = function(b) {
  var text    = b.text    || 'Neon';
  var colour  = b.colour  || '#a78bfa';
  var size    = b.size    || '2rem';
  var weight  = b.weight  || 800;
  var align   = b.align   || 'center';
  var flicker = b.flicker || false;
  var uid     = 'nx' + Math.random().toString(36).substr(2, 5);

  var keyframes = flicker
    ? '<style>@keyframes ' + uid + 'flk{' +
      '0%,19%,21%,23%,25%,54%,56%,100%{' +
        'text-shadow:0 0 4px #fff,0 0 10px ' + colour + ',0 0 20px ' + colour + ',0 0 50px ' + colour + ';}' +
      '20%,24%,55%{text-shadow:none;}' +
      '}</style>'
    : '';

  var glowStyle = flicker
    ? 'animation:' + uid + 'flk 3s infinite alternate;'
    : 'text-shadow:0 0 4px #fff,0 0 10px ' + colour + ',0 0 24px ' + colour + ',0 0 50px ' + colour + '66,0 0 80px ' + colour + '33;';

  return keyframes +
    '<div style="text-align:' + align + ';padding:20px 0;">' +
    '<span style="' +
    'font-size:' + _esc(size) + ';' +
    'font-weight:' + weight + ';' +
    'color:#fff;' +
    'letter-spacing:0.04em;' +
    glowStyle +
    '">' + _esc(text) + '</span>' +
    '</div>';
};

// ── dark_feature_grid ─────────────────────────────────────────────────────────
// Grid of feature cards designed for dark theme — icon, title, description,
// with a gradient icon container and subtle gradient border.
// Fields:
//   features — array of { icon, title, description, colour? }
//   columns  — grid columns: 2 or 3 (default 3, collapses to 1 on narrow)
//   accent   — default icon bg gradient colour (default #6366f1)
_RENDERERS['dark_feature_grid'] = function(b) {
  var features = b.features || [
    { icon: '⚡', title: 'Fast',     description: 'Renders in under 100ms from a base64 URL.' },
    { icon: '🔒', title: 'Secure',   description: 'No external dependencies. CSP-safe inline JS only.' },
    { icon: '🎨', title: 'Flexible', description: 'Dark and light themes, any accent colour, 290+ atoms.' }
  ];
  var cols   = b.columns || 3;
  var accent = b.accent  || '#6366f1';

  var cards = '';
  for (var i = 0; i < features.length; i++) {
    var f      = features[i];
    var colour = f.colour || accent;
    cards += '<div style="' +
      'background:#0f1117;' +
      'border:1px solid rgba(255,255,255,0.07);' +
      'border-radius:14px;padding:22px;' +
      'display:flex;flex-direction:column;gap:10px;">' +
      '<div style="width:40px;height:40px;border-radius:10px;' +
      'background:linear-gradient(135deg,' + _esc(colour) + '33,' + _esc(colour) + '11);' +
      'border:1px solid ' + _esc(colour) + '33;' +
      'display:flex;align-items:center;justify-content:center;font-size:1.2rem;">' +
      (f.icon ? _esc(f.icon) : '◆') +
      '</div>' +
      '<div style="font-size:0.92rem;font-weight:700;color:rgba(255,255,255,0.9);">' + _esc(f.title || '') + '</div>' +
      '<div style="font-size:0.8rem;color:rgba(255,255,255,0.45);line-height:1.6;">' + _esc(f.description || '') + '</div>' +
      '</div>';
  }

  return '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:14px;' +
    '@media(max-width:480px){grid-template-columns:1fr;}">' +
    cards +
    '</div>';
};

// ── dark_divider ──────────────────────────────────────────────────────────────
// Gradient divider line — more dramatic than a plain hr on dark backgrounds.
// Fields:
//   colour  — centre colour of the gradient (default #6366f1)
//   margin  — vertical margin (default 32px)
//   height  — line height px (default 1)
_RENDERERS['dark_divider'] = function(b) {
  var colour = b.colour || '#6366f1';
  var margin = b.margin || '32px';
  var height = b.height || 1;

  return '<div style="' +
    'height:' + height + 'px;' +
    'margin:' + _esc(margin) + ' 0;' +
    'background:linear-gradient(90deg,transparent 0%,' + colour + ' 30%,' + colour + ' 70%,transparent 100%);' +
    'opacity:0.4;' +
    'border-radius:99px;"></div>';
};
