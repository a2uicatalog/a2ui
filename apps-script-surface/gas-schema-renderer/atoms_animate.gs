// atoms_animate.gs — pure CSS / vanilla JS animation atoms
// All GAS-safe, no external dependencies.

// ─── Shared keyframe block (injected once per atom type via unique class) ─────
// Each atom generates its own uid to avoid CSS collisions across multiple instances.

// ─── reveal ───────────────────────────────────────────────────────────────────
// Wraps child blocks with entrance animations. animation: fade_up | fade_in |
// slide_left | slide_right | scale_in | stagger (stagger = fade_up with per-block delay)
_RENDERERS['reveal'] = function(b) {
  var uid      = 'rv' + Math.random().toString(36).substr(2, 5);
  var anim     = b.animation || 'fade_up';
  var dur      = b.duration  || 500;
  var delay    = b.delay     || 0;
  var staggerMs = b.stagger_delay || 120;
  var blocks   = b.blocks    || [];
  var isStagger = anim === 'stagger';

  var css = '<style>'
    + '@keyframes ' + uid + '-fu{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}'
    + '@keyframes ' + uid + '-fi{from{opacity:0}to{opacity:1}}'
    + '@keyframes ' + uid + '-sl{from{opacity:0;transform:translateX(-28px)}to{opacity:1;transform:none}}'
    + '@keyframes ' + uid + '-sr{from{opacity:0;transform:translateX(28px)}to{opacity:1;transform:none}}'
    + '@keyframes ' + uid + '-sc{from{opacity:0;transform:scale(0.88)}to{opacity:1;transform:scale(1)}}'
    + '.' + uid + '{animation-fill-mode:both;animation-timing-function:cubic-bezier(0.4,0,0.2,1);}'
    + '.' + uid + '-fade_up{animation-name:' + uid + '-fu}'
    + '.' + uid + '-fade_in{animation-name:' + uid + '-fi}'
    + '.' + uid + '-slide_left{animation-name:' + uid + '-sl}'
    + '.' + uid + '-slide_right{animation-name:' + uid + '-sr}'
    + '.' + uid + '-scale_in{animation-name:' + uid + '-sc}'
    + '</style>';

  var content = blocks.map(function(blk, i) {
    var fn = _RENDERERS[blk.component || blk.type];
    if (!fn) return '';
    var effectClass = isStagger ? uid + '-fade_up' : uid + '-' + anim;
    var d = delay + (isStagger ? i * staggerMs : 0);
    return '<div class="' + uid + ' ' + effectClass + '" style="animation-duration:' + dur + 'ms;animation-delay:' + d + 'ms;">' + fn(blk) + '</div>';
  }).join('');

  return css + content;
};

// ─── skeleton ─────────────────────────────────────────────────────────────────
// Shimmer loading placeholder. type: text | card | avatar_row | image | list | table
_RENDERERS['skeleton'] = function(b) {
  var uid   = 'sk' + Math.random().toString(36).substr(2, 5);
  var type  = b.type  || 'text';
  var rows  = b.rows  || 3;
  var accent = b.accent || '#e5e7eb';

  var css = '<style>'
    + '@keyframes ' + uid + '-sh{0%{background-position:200% 0}100%{background-position:-200% 0}}'
    + '.' + uid + '{background:linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%);background-size:200% 100%;animation:' + uid + '-sh 1.4s ease infinite;border-radius:6px;}'
    + '</style>';

  var blocks = '';
  if (type === 'avatar_row') {
    var avatarRows = '';
    for (var i = 0; i < rows; i++) {
      avatarRows += '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">'
        + '<div class="' + uid + '" style="width:40px;height:40px;border-radius:50%;flex-shrink:0;"></div>'
        + '<div style="flex:1;">'
        + '<div class="' + uid + '" style="height:12px;width:60%;margin-bottom:6px;"></div>'
        + '<div class="' + uid + '" style="height:10px;width:40%;"></div>'
        + '</div></div>';
    }
    blocks = avatarRows;
  } else if (type === 'card') {
    blocks = '<div class="' + uid + '" style="height:160px;margin-bottom:12px;border-radius:10px;"></div>'
      + '<div class="' + uid + '" style="height:14px;width:70%;margin-bottom:8px;"></div>'
      + '<div class="' + uid + '" style="height:12px;width:50%;"></div>';
  } else if (type === 'image') {
    var h = b.height || '200px';
    blocks = '<div class="' + uid + '" style="height:' + _esc(String(h)) + ';border-radius:10px;"></div>';
  } else if (type === 'table') {
    var headerRow = '<div style="display:grid;grid-template-columns:repeat(' + (b.cols||3) + ',1fr);gap:8px;margin-bottom:8px;">';
    for (var c = 0; c < (b.cols||3); c++) {
      headerRow += '<div class="' + uid + '" style="height:12px;border-radius:4px;"></div>';
    }
    headerRow += '</div>';
    var tableRows = '';
    for (var r = 0; r < rows; r++) {
      tableRows += '<div style="display:grid;grid-template-columns:repeat(' + (b.cols||3) + ',1fr);gap:8px;margin-bottom:8px;">';
      for (var tc = 0; tc < (b.cols||3); tc++) {
        tableRows += '<div class="' + uid + '" style="height:10px;border-radius:4px;opacity:' + (1 - r * 0.1) + ';"></div>';
      }
      tableRows += '</div>';
    }
    blocks = headerRow + tableRows;
  } else if (type === 'list') {
    for (var li = 0; li < rows; li++) {
      blocks += '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
        + '<div class="' + uid + '" style="width:8px;height:8px;border-radius:50%;flex-shrink:0;"></div>'
        + '<div class="' + uid + '" style="height:11px;width:' + (60 + li * 8 % 30) + '%;"></div></div>';
    }
  } else {
    // text (default)
    for (var ti = 0; ti < rows; ti++) {
      var w = ti === rows - 1 ? '65%' : (85 + ti % 10) + '%';
      blocks += '<div class="' + uid + '" style="height:12px;width:' + w + ';margin-bottom:10px;"></div>';
    }
  }

  return css + '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:' + (type === 'card' ? '16px' : '0') + (type === 'card' ? ';border:1px solid #f3f4f6;border-radius:10px;' : '') + '">' + blocks + '</div>';
};

// ─── marquee ──────────────────────────────────────────────────────────────────
// Infinite horizontal scroll ticker. items: [{text?, icon?, label?, url?, image_url?}]
_RENDERERS['marquee'] = function(b) {
  var uid   = 'mq' + Math.random().toString(36).substr(2, 5);
  var items = b.items || [];
  var speed = b.speed  || 30; // seconds for one full cycle
  var gap   = b.gap    || 48; // px gap between items
  var dir   = b.direction === 'right' ? 'reverse' : 'normal';
  var sep   = b.separator || '';
  var accent = b.accent || 'var(--a2ui-accent,#6366f1)';
  var bg    = b.bg || 'var(--surface,#f9fafb)';
  var pause = b.pause_on_hover !== false;

  function renderItem(item) {
    if (typeof item === 'string') return '<span style="font-size:0.875rem;color:var(--text,#374151);">' + _esc(item) + '</span>';
    var inner = '';
    if (item.image_url) {
      var imgStyle = 'height:32px;object-fit:contain;' + (b.color_icons ? '' : 'opacity:0.7;filter:grayscale(1);');
      inner += '<img src="' + _esc(item.image_url) + '" alt="' + _esc(item.label||'') + '" style="' + imgStyle + '">';
    }
    if (item.icon)      inner += '<span style="font-size:1.1rem;">' + _esc(item.icon) + '</span>';
    if (item.text || item.label) inner += '<span style="font-size:0.875rem;color:var(--text,#374151);white-space:nowrap;">' + _esc(item.text || item.label) + '</span>';
    return item.url
      ? '<a href="' + _safeUrl(item.url) + '" target="_top" style="display:inline-flex;align-items:center;gap:6px;text-decoration:none;">' + inner + '</a>'
      : '<span style="display:inline-flex;align-items:center;gap:6px;">' + inner + '</span>';
  }

  var sepHtml = sep ? '<span style="color:var(--muted,#d1d5db);margin:0 4px;">' + _esc(sep) + '</span>' : '';
  var itemHtml = items.map(function(item) {
    return '<span style="padding:0 ' + gap + 'px;display:inline-flex;align-items:center;">' + renderItem(item) + sepHtml + '</span>';
  }).join('');
  // Duplicate for seamless loop
  var track = itemHtml + itemHtml;

  var css = '<style>'
    + '@keyframes ' + uid + '{from{transform:translateX(0)}to{transform:translateX(-50%)}}'
    + '#' + uid + '-track{display:inline-flex;animation:' + uid + ' ' + speed + 's linear infinite ' + dir + ';white-space:nowrap;}'
    + (pause ? '#' + uid + ':hover #' + uid + '-track{animation-play-state:paused;}' : '')
    + '</style>';

  var title = b.title ? '<div style="font-size:0.75rem;font-weight:700;color:var(--muted,#9ca3af);text-transform:uppercase;letter-spacing:0.06em;padding:8px 16px 0;">' + _esc(b.title) + '</div>' : '';
  return css + title
    + '<div id="' + uid + '" style="overflow:hidden;background:' + bg + ';border-radius:' + (b.rounded !== false ? '10px' : '0') + ';border:1px solid var(--border,#e5e7eb);padding:12px 0;">'
    + '<div id="' + uid + '-track">' + track + '</div></div>';
};

// ─── pulse_dot ────────────────────────────────────────────────────────────────
// Pulsing status/attention indicator. Inline or block. size: sm | md | lg
_RENDERERS['pulse_dot'] = function(b) {
  var uid    = 'pd' + Math.random().toString(36).substr(2, 5);
  var color  = b.color || b.accent || '#10b981';
  var size   = {sm: '8px', md: '12px', lg: '16px'}[b.size] || '12px';
  var label  = b.label ? '<span style="font-size:0.82rem;color:var(--text,#374151);margin-left:8px;">' + _esc(b.label) + '</span>' : '';
  var speed  = b.speed || '1.8';
  var inline = b.inline !== false;

  var css = '<style>'
    + '@keyframes ' + uid + '{0%,100%{box-shadow:0 0 0 0 ' + color + '55}70%{box-shadow:0 0 0 ' + (parseInt(size)*1.5) + 'px transparent}}'
    + '#' + uid + '{width:' + size + ';height:' + size + ';border-radius:50%;background:' + color + ';animation:' + uid + ' ' + speed + 's ease infinite;flex-shrink:0;}'
    + '</style>';

  return css + '<span style="display:' + (inline ? 'inline-flex' : 'flex') + ';align-items:center;margin:' + (inline ? '0 4px' : 'var(--a2ui-block-gap,1.25rem) 0') + ';">'
    + '<span id="' + uid + '"></span>' + label + '</span>';
};

// ─── loading_dots ─────────────────────────────────────────────────────────────
// Three-dot pulsing loader. Use inline or as a standalone block.
_RENDERERS['loading_dots'] = function(b) {
  var uid   = 'ld' + Math.random().toString(36).substr(2, 5);
  var color = b.color || b.accent || 'var(--a2ui-accent,#6366f1)';
  var size  = b.size === 'sm' ? '6px' : b.size === 'lg' ? '12px' : '8px';
  var label = b.label ? '<span style="font-size:0.82rem;color:var(--muted,#6b7280);margin-left:10px;">' + _esc(b.label) + '</span>' : '';

  var css = '<style>'
    + '@keyframes ' + uid + '{0%,80%,100%{transform:scale(0);opacity:0.3}40%{transform:scale(1);opacity:1}}'
    + '.' + uid + '-d{width:' + size + ';height:' + size + ';border-radius:50%;background:' + color + ';animation:' + uid + ' 1.2s ease infinite;display:inline-block;}'
    + '</style>';

  var dots = [0, 0.2, 0.4].map(function(d) {
    return '<span class="' + uid + '-d" style="animation-delay:' + d + 's;margin:0 2px;"></span>';
  }).join('');

  return css + '<div style="display:flex;align-items:center;justify-content:' + (b.align === 'center' ? 'center' : 'flex-start') + ';margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + dots + label + '</div>';
};

// ─── progress_ring ────────────────────────────────────────────────────────────
// Animated SVG circular progress gauge. value 0–100.
_RENDERERS['progress_ring'] = function(b) {
  var uid    = 'pr' + Math.random().toString(36).substr(2, 5);
  var value  = Math.min(100, Math.max(0, parseFloat(b.value || 0)));
  var size   = parseInt(b.size || 100, 10);
  var stroke = parseInt(b.stroke_width || 8, 10);
  var color  = b.color || b.accent || 'var(--a2ui-accent,#6366f1)';
  var track  = b.track_color || 'var(--border,#e5e7eb)';
  var label  = b.label ? '<div style="font-size:0.78rem;color:var(--muted,#6b7280);margin-top:6px;">' + _esc(b.label) + '</div>' : '';
  var showVal = b.show_value !== false;
  var unit   = _esc(b.unit || '%');

  var r     = (size / 2) - stroke;
  var circ  = 2 * Math.PI * r;
  var dash  = (value / 100) * circ;

  var css = '<style>'
    + '@keyframes ' + uid + '{from{stroke-dashoffset:' + circ + '}to{stroke-dashoffset:' + (circ - dash) + '}}'
    + '#' + uid + '-fg{animation:' + uid + ' 1s cubic-bezier(0.4,0,0.2,1) both;stroke-dasharray:' + circ + ';stroke-dashoffset:' + (circ - dash) + ';}'
    + '</style>';

  var svg = '<svg width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size + '">'
    + '<circle cx="' + (size/2) + '" cy="' + (size/2) + '" r="' + r + '" fill="none" stroke="' + track + '" stroke-width="' + stroke + '"/>'
    + '<circle id="' + uid + '-fg" cx="' + (size/2) + '" cy="' + (size/2) + '" r="' + r + '" fill="none" stroke="' + color + '" stroke-width="' + stroke + '" stroke-linecap="round" transform="rotate(-90 ' + (size/2) + ' ' + (size/2) + ')"/>'
    + (showVal ? '<text x="' + (size/2) + '" y="' + (size/2 + 6) + '" text-anchor="middle" style="font-size:' + (size*0.2) + 'px;font-weight:700;fill:var(--text,#111827);">' + value + unit + '</text>' : '')
    + '</svg>';

  return css + '<div style="display:inline-flex;flex-direction:column;align-items:center;margin:var(--a2ui-block-gap,1.25rem) 0;">' + svg + label + '</div>';
};

// ─── confetti_burst ───────────────────────────────────────────────────────────
// JS confetti celebration. Trigger on load or via a button.
// trigger: "load" | "button" (default button)
_RENDERERS['confetti_burst'] = function(b) {
  var uid    = 'cf' + Math.random().toString(36).substr(2, 5);
  var count  = b.count || 80;
  var colors = JSON.stringify(b.colors || ['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6','#0ea5e9','#f472b6']);
  var label  = _esc(b.label || '🎉 Celebrate!');
  var trigger = b.trigger || 'button';
  var dur    = b.duration || 2000;
  var accent = b.accent || 'var(--a2ui-accent,#6366f1)';

  var css = '<style>'
    + '.' + uid + '-p{position:fixed;pointer-events:none;border-radius:2px;z-index:9999;will-change:transform,opacity;}'
    + '@keyframes ' + uid + '-fall{to{transform:var(--tx) translateY(110vh) rotate(var(--r));opacity:0;}}'
    + '</style>';

  var script = '<script>(function(){'
    + 'function burst(){'
    + 'var colors=' + colors + ';'
    + 'for(var i=0;i<' + count + ';i++){(function(i){'
    + 'var el=document.createElement("div");'
    + 'el.className="' + uid + '-p";'
    + 'var c=colors[i%colors.length];'
    + 'var w=6+Math.random()*6,h=8+Math.random()*10;'
    + 'var x=(Math.random()*100)+"vw";'
    + 'var r=(Math.random()*720-360)+"deg";'
    + 'var tx="translateX("+(Math.random()*200-100)+"px)";'
    + 'el.style.cssText="left:"+x+";top:-20px;width:"+w+"px;height:"+h+"px;background:"+c+";--tx:"+tx+";--r:"+r+";animation:' + uid + '-fall "+(1+Math.random())+"s "+(Math.random()*' + (dur/3000) + ')+"s cubic-bezier(0.25,0.46,0.45,0.94) forwards;";'
    + 'document.body.appendChild(el);'
    + 'setTimeout(function(){el.remove();},' + (dur + 2000) + ');'
    + '})(i);}'
    + '}'
    + (trigger === 'load' ? 'burst();' : 'document.getElementById("' + uid + '-btn").addEventListener("click",burst);')
    + '})();<\/script>';

  var btn = trigger === 'button'
    ? '<div style="text-align:center;margin:var(--a2ui-block-gap,1.25rem) 0;">'
      + '<button id="' + uid + '-btn" style="background:' + accent + ';color:#fff;border:none;border-radius:10px;padding:12px 28px;font-size:1rem;font-weight:700;cursor:pointer;font-family:inherit;">' + label + '</button></div>'
    : '';

  return css + btn + script;
};

// ─── ripple_button ────────────────────────────────────────────────────────────
// Button with CSS/JS ripple effect on click.
_RENDERERS['ripple_button'] = function(b) {
  var uid   = 'rb' + Math.random().toString(36).substr(2, 5);
  var label = _esc(b.label || 'Click me');
  var url   = b.url ? _safeUrl(b.url) : '';
  var accent = b.accent || 'var(--a2ui-accent,#6366f1)';
  var size  = b.size === 'sm' ? '0.8rem' : b.size === 'lg' ? '1.1rem' : '0.9rem';
  var full  = b.full_width ? 'width:100%;' : '';
  var align = b.align === 'center' ? 'center' : b.align === 'right' ? 'flex-end' : 'flex-start';

  var css = '<style>'
    + '@keyframes ' + uid + '-rip{to{transform:scale(4);opacity:0;}}'
    + '#' + uid + '{position:relative;overflow:hidden;display:inline-flex;align-items:center;gap:8px;'
    + 'background:' + accent + ';color:#fff;border:none;border-radius:10px;'
    + 'padding:10px 24px;font-size:' + size + ';font-weight:700;cursor:pointer;font-family:inherit;' + full + '}'
    + '.' + uid + '-r{position:absolute;border-radius:50%;background:rgba(255,255,255,0.35);'
    + 'transform:scale(0);animation:' + uid + '-rip 0.5s linear;pointer-events:none;}'
    + '</style>';

  var script = '<script>(function(){'
    + 'document.getElementById("' + uid + '").addEventListener("click",function(e){'
    + 'var btn=this,r=document.createElement("span");'
    + 'var d=Math.max(btn.offsetWidth,btn.offsetHeight);'
    + 'var rect=btn.getBoundingClientRect();'
    + 'r.className="' + uid + '-r";'
    + 'r.style.cssText="width:"+d+"px;height:"+d+"px;left:"+(e.clientX-rect.left-d/2)+"px;top:"+(e.clientY-rect.top-d/2)+"px;";'
    + 'btn.appendChild(r);'
    + 'setTimeout(function(){r.remove();},600);'
    + (url ? 'setTimeout(function(){window.open("' + url + '","_top");},100);' : '')
    + '});'
    + '})();<\/script>';

  var icon = b.icon ? _esc(b.icon) + ' ' : '';
  return css + '<div style="display:flex;justify-content:' + align + ';margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + '<button id="' + uid + '">' + icon + label + '</button></div>' + script;
};

// ─── wave_divider ─────────────────────────────────────────────────────────────
// Animated SVG wave section divider. flip: reverses the wave direction.
_RENDERERS['wave_divider'] = function(b) {
  var uid    = 'wv' + Math.random().toString(36).substr(2, 5);
  var color  = b.color || b.accent || 'var(--a2ui-accent,#6366f1)';
  var h      = parseInt(b.height || 60, 10);
  var speed  = b.speed || '8';
  var flip   = b.flip ? 'scale(-1,1)' : '';
  var opacity = b.opacity || '0.15';
  var animate = b.animate !== false;

  var css = animate
    ? '<style>@keyframes ' + uid + '{0%{d:path("M0,' + (h*0.5) + ' C200,' + (h*0.1) + ' 400,' + (h*0.9) + ' 600,' + (h*0.5) + ' S1000,' + (h*0.2) + ' 1200,' + (h*0.5) + ' V' + h + ' H0Z")} 50%{d:path("M0,' + (h*0.5) + ' C200,' + (h*0.9) + ' 400,' + (h*0.1) + ' 600,' + (h*0.5) + ' S1000,' + (h*0.8) + ' 1200,' + (h*0.5) + ' V' + h + ' H0Z")} 100%{d:path("M0,' + (h*0.5) + ' C200,' + (h*0.1) + ' 400,' + (h*0.9) + ' 600,' + (h*0.5) + ' S1000,' + (h*0.2) + ' 1200,' + (h*0.5) + ' V' + h + ' H0Z")}}'
    + '#' + uid + '-path{animation:' + uid + ' ' + speed + 's ease-in-out infinite;}</style>'
    : '';

  return css + '<div style="margin:0;line-height:0;transform:' + flip + ';overflow:hidden;">'
    + '<svg viewBox="0 0 1200 ' + h + '" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" style="width:100%;height:' + h + 'px;display:block;">'
    + '<path id="' + uid + '-path" d="M0,' + (h*0.5) + ' C200,' + (h*0.1) + ' 400,' + (h*0.9) + ' 600,' + (h*0.5) + ' S1000,' + (h*0.2) + ' 1200,' + (h*0.5) + ' V' + h + ' H0Z" fill="' + color + '" fill-opacity="' + opacity + '"/>'
    + '<path d="M0,' + (h*0.7) + ' C300,' + (h*0.3) + ' 500,' + (h*0.9) + ' 800,' + (h*0.6) + ' S1100,' + (h*0.4) + ' 1200,' + (h*0.7) + ' V' + h + ' H0Z" fill="' + color + '" fill-opacity="' + (parseFloat(opacity)*0.5) + '"/>'
    + '</svg></div>';
};

// ─── floating_badge ───────────────────────────────────────────────────────────
// A badge or icon that bobs up and down continuously. Great for CTAs and achievements.
_RENDERERS['floating_badge'] = function(b) {
  var uid    = 'fb' + Math.random().toString(36).substr(2, 5);
  var icon   = _esc(b.icon || '🏆');
  var label  = b.label ? '<div style="font-size:0.78rem;font-weight:700;color:var(--muted,#6b7280);margin-top:6px;">' + _esc(b.label) + '</div>' : '';
  var size   = b.size === 'sm' ? '2rem' : b.size === 'lg' ? '4rem' : '3rem';
  var speed  = b.speed || '3';
  var bg     = b.bg || 'transparent';
  var shadow = b.shadow !== false;
  var align  = b.align || 'center';

  var css = '<style>'
    + '@keyframes ' + uid + '{0%,100%{transform:translateY(0)' + (shadow ? ';filter:drop-shadow(0 8px 12px rgba(0,0,0,0.15))' : '') + '}50%{transform:translateY(-10px)' + (shadow ? ';filter:drop-shadow(0 16px 20px rgba(0,0,0,0.08))' : '') + '}}'
    + '#' + uid + '{animation:' + uid + ' ' + speed + 's ease-in-out infinite;display:inline-flex;flex-direction:column;align-items:center;}'
    + '</style>';

  return css + '<div style="text-align:' + align + ';margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + '<div id="' + uid + '">'
    + '<span style="font-size:' + size + ';display:block;background:' + bg + ';line-height:1;">' + icon + '</span>'
    + label + '</div></div>';
};

// ─── shimmer_text ─────────────────────────────────────────────────────────────
// Text with a gloss shimmer sweep. Works well for hero taglines.
_RENDERERS['shimmer_text'] = function(b) {
  var uid   = 'st' + Math.random().toString(36).substr(2, 5);
  var text  = _esc(b.text || '');
  var size  = _esc(b.size  || '2rem');
  var from  = b.from  || '#6366f1';
  var to    = b.to    || '#8b5cf6';
  var via   = b.via   || '#ffffff';
  var speed = b.speed || '2.5';
  var weight = b.weight || '800';
  var align = b.align || 'left';

  var css = '<style>'
    + '@keyframes ' + uid + '{0%{background-position:200% center}100%{background-position:-200% center}}'
    + '#' + uid + '{font-size:' + size + ';font-weight:' + weight + ';text-align:' + align + ';'
    + 'background:linear-gradient(90deg,' + from + ',' + via + ',' + to + ',' + from + ');'
    + 'background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'
    + 'animation:' + uid + ' ' + speed + 's linear infinite;line-height:1.2;}'
    + '</style>';

  return css + '<div id="' + uid + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + text + '</div>';
};

// ─── number_flip ──────────────────────────────────────────────────────────────
// Slot-machine style number reveal. Counts from 0 to value with a flip effect.
_RENDERERS['number_flip'] = function(b) {
  var uid   = 'nf' + Math.random().toString(36).substr(2, 5);
  var value = String(b.value || 0);
  var pre   = _esc(b.prefix || '');
  var suf   = _esc(b.suffix || '');
  var label = b.label ? '<div style="font-size:0.82rem;color:var(--muted,#6b7280);margin-top:4px;">' + _esc(b.label) + '</div>' : '';
  var size  = b.size || '3rem';
  var color = b.color || b.accent || 'var(--a2ui-accent,#6366f1)';
  var dur   = b.duration || 1200;
  var align = b.align || 'center';

  var css = '<style>'
    + '@keyframes ' + uid + '-flip{0%{transform:rotateX(90deg);opacity:0}60%{transform:rotateX(-8deg)}100%{transform:rotateX(0);opacity:1}}'
    + '.' + uid + '-d{display:inline-flex;flex-direction:column;align-items:center;perspective:200px;}'
    + '.' + uid + '-v{animation:' + uid + '-flip 0.35s cubic-bezier(0.4,0,0.2,1) both;display:inline-block;transform-origin:50% 50%;}'
    + '</style>';

  // Build digit spans
  var digits = value.split('').map(function(ch, i) {
    return '<span class="' + uid + '-d"><span class="' + uid + '-v" style="animation-delay:' + (i * 80 + 200) + 'ms;">' + _esc(ch) + '</span></span>';
  }).join('');

  return css + '<div style="text-align:' + align + ';margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + '<div style="font-size:' + _esc(size) + ';font-weight:900;color:' + color + ';line-height:1;font-family:inherit;">'
    + (pre ? '<span>' + pre + '</span>' : '')
    + digits
    + (suf ? '<span>' + suf + '</span>' : '')
    + '</div>' + label + '</div>';
};

// ─── spotlight_card ───────────────────────────────────────────────────────────
// Card with a moving gradient spotlight that follows cursor position.
_RENDERERS['spotlight_card'] = function(b) {
  var uid    = 'sp' + Math.random().toString(36).substr(2, 5);
  var accent = b.accent || 'var(--a2ui-accent,#6366f1)';
  var blocks = b.blocks || [];
  var content = '';
  blocks.forEach(function(blk) { var fn = _RENDERERS[blk.component||blk.type]; if(fn) content += fn(blk); });
  if (!content && b.content) content = '<p style="font-size:0.875rem;line-height:1.6;">' + _markdownToHtml(b.content) + '</p>';

  var css = '<style>'
    + '#' + uid + '{position:relative;border:1px solid var(--border,#e5e7eb);border-radius:12px;padding:20px;overflow:hidden;background:var(--bg,#fff);transition:border-color 0.3s;}'
    + '#' + uid + ':hover{border-color:' + accent + '44;}'
    + '#' + uid + '-glow{position:absolute;pointer-events:none;width:320px;height:320px;border-radius:50%;background:radial-gradient(circle,' + accent + '18 0%,transparent 70%);transform:translate(-50%,-50%);opacity:0;transition:opacity 0.3s;top:50%;left:50%;}'
    + '#' + uid + ':hover #' + uid + '-glow{opacity:1;}'
    + '</style>';

  var script = '<script>(function(){'
    + 'var card=document.getElementById("' + uid + '");'
    + 'var glow=document.getElementById("' + uid + '-glow");'
    + 'card.addEventListener("mousemove",function(e){'
    + 'var r=card.getBoundingClientRect();'
    + 'glow.style.left=(e.clientX-r.left)+"px";'
    + 'glow.style.top=(e.clientY-r.top)+"px";'
    + '});'
    + '})();<\/script>';

  return css + '<div id="' + uid + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + '<div id="' + uid + '-glow"></div>'
    + '<div style="position:relative;z-index:1;">' + content + '</div>'
    + '</div>' + script;
};

// ─── animated_border ──────────────────────────────────────────────────────────
// Card or section with an animated gradient border that rotates.
_RENDERERS['animated_border'] = function(b) {
  var uid    = 'ab' + Math.random().toString(36).substr(2, 5);
  var from   = b.from   || b.accent || '#6366f1';
  var to     = b.to     || '#8b5cf6';
  var via    = b.via    || '#0ea5e9';
  var speed  = b.speed  || '3';
  var pad    = b.padding || '20px';
  var radius = b.radius  || '12px';
  var blocks = b.blocks  || [];
  var content = '';
  blocks.forEach(function(blk){ var fn = _RENDERERS[blk.component||blk.type]; if(fn) content += fn(blk); });
  if (!content && b.content) content = '<p style="font-size:0.875rem;line-height:1.6;">' + _markdownToHtml(b.content) + '</p>';

  // @property with syntax:"<angle>" causes GAS HTML sanitizer to treat <angle> as a tag.
  // Use a rotating inner div carrying the conic gradient instead.
  var css = '<style>'
    + '@keyframes ' + uid + '{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}'
    + '#' + uid + '{position:relative;border-radius:' + radius + ';padding:2px;overflow:hidden;margin:var(--a2ui-block-gap,1.25rem) 0;}'
    + '#' + uid + '-spin{position:absolute;inset:-50%;width:200%;height:200%;background:conic-gradient(' + from + ',' + via + ',' + to + ',' + from + ');animation:' + uid + ' ' + speed + 's linear infinite;pointer-events:none;}'
    + '#' + uid + '-inner{position:relative;z-index:1;border-radius:calc(' + radius + ' - 2px);background:var(--bg,#fff);padding:' + pad + ';}'
    + '</style>';

  return css + '<div id="' + uid + '"><div id="' + uid + '-spin"></div><div id="' + uid + '-inner">' + content + '</div></div>';
};

// ─── typing_indicator ─────────────────────────────────────────────────────────
// Chat-style "someone is typing" indicator with three animated dots.
_RENDERERS['typing_indicator'] = function(b) {
  var uid   = 'ti' + Math.random().toString(36).substr(2, 5);
  var label = b.label ? _esc(b.label) : '';
  var color = b.color || b.accent || '#6b7280';
  var bg    = b.bg    || 'var(--surface,#f3f4f6)';

  var css = '<style>'
    + '@keyframes ' + uid + '{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}'
    + '.' + uid + '-d{width:6px;height:6px;border-radius:50%;background:' + color + ';animation:' + uid + ' 1.2s ease infinite;display:inline-block;}'
    + '</style>';

  var dots = [0, 0.2, 0.4].map(function(d, i) {
    return '<span class="' + uid + '-d" style="animation-delay:' + d + 's;' + (i > 0 ? 'margin-left:4px;' : '') + '"></span>';
  }).join('');

  return css + '<div style="display:inline-flex;align-items:center;gap:8px;padding:10px 14px;background:' + bg + ';border-radius:18px 18px 18px 4px;margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + (label ? '<span style="font-size:0.82rem;color:' + color + ';">' + label + '</span>' : '')
    + '<span>' + dots + '</span></div>';
};

// ─── countdown_ring ───────────────────────────────────────────────────────────
// Circular countdown that depletes. duration_sec sets total seconds.
_RENDERERS['countdown_ring'] = function(b) {
  var uid   = 'cr' + Math.random().toString(36).substr(2, 5);
  var dur   = parseInt(b.duration_sec || 60, 10);
  var size  = parseInt(b.size || 80, 10);
  var color = b.color || b.accent || 'var(--a2ui-accent,#6366f1)';
  var label = b.label ? '<div style="font-size:0.72rem;color:var(--muted,#6b7280);margin-top:4px;">' + _esc(b.label) + '</div>' : '';
  var r     = (size / 2) - 6;
  var circ  = 2 * Math.PI * r;

  var css = '<style>'
    + '@keyframes ' + uid + '{from{stroke-dashoffset:0}to{stroke-dashoffset:' + circ + '}}'
    + '#' + uid + '-arc{stroke-dasharray:' + circ + ';stroke-dashoffset:0;animation:' + uid + ' ' + dur + 's linear forwards;}'
    + '</style>';

  var svg = '<svg width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size + '">'
    + '<circle cx="' + (size/2) + '" cy="' + (size/2) + '" r="' + r + '" fill="none" stroke="var(--border,#e5e7eb)" stroke-width="6"/>'
    + '<circle id="' + uid + '-arc" cx="' + (size/2) + '" cy="' + (size/2) + '" r="' + r + '" fill="none" stroke="' + color + '" stroke-width="6" stroke-linecap="round" transform="rotate(-90 ' + (size/2) + ' ' + (size/2) + ')"/>'
    + '<text id="' + uid + '-num" x="' + (size/2) + '" y="' + (size/2+5) + '" text-anchor="middle" style="font-size:' + Math.round(size*0.22) + 'px;font-weight:700;fill:var(--text,#111827);">' + dur + '</text>'
    + '</svg>';

  var script = '<script>(function(){'
    + 'var el=document.getElementById("' + uid + '-num");'
    + 'var t=' + dur + ';'
    + 'var iv=setInterval(function(){t--;el.textContent=t;if(t<=0){clearInterval(iv);el.textContent="✓";}},1000);'
    + '})();<\/script>';

  return css + '<div style="display:inline-flex;flex-direction:column;align-items:center;margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + svg + label + '</div>' + script;
};
