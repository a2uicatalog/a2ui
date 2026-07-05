// atoms_icons.gs — Google icon CDN atoms
// Material Symbols: fonts.googleapis.com (variable font, 2500+ icons)
// Workspace product logos: workspacelogos.com (2026Q2 refresh) + fonts.gstatic.com fallback

// ─── CDN constants ────────────────────────────────────────────────────────────
// No &display=block — avoids unescaped & inside CSS @import inside <style>
var _MATERIAL_SYMBOLS_CSS_URL = 'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200';
var _MATERIAL_SYMBOLS_ROUNDED_URL = 'https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200';
var _LOGO_BASE = 'https://fonts.gstatic.com/s/i/productlogos/';

// 2026Q2 icon refresh — sourced from workspacelogos.com (verified 2026-06-27)
// Format: workspacelogos.com/logos/google-workspace-logos/{Product}/{filename}
var _WL_BASE = 'https://workspacelogos.com/logos/google-workspace-logos/';
var _WORKSPACE_LOGOS_2026 = {
  gmail:      'Gmail/logo_gmail_2026q2_color_2x_web_96dp.png',
  drive:      'Drive/logo_drive_2026q2_color_2x_web_96dp.png',
  docs:       'Docs/logo_docs_2026q2_color_2x_web_96dp.png',
  sheets:     'Sheets/logo_sheets_2026q2_color_2x_web_96dp.png',
  slides:     'Slides/logo_slides_2026q2_color_2x_web_96dp.png',
  calendar:   'Calendar/logo_calendar_2026q2_color_2x_web_96dp.png',
  meet:       'Meet/logo_meet_2026q2_color_2x_web_96dp.png',
  forms:      'Forms/logo_forms_2026q2_color_2x_web_96dp.png',
  chat:       'Chat/logo_chat_2026q2_color_2x_web_96dp.png',
  keep:       'Keep/logo_keep_2026q2_color_2x_web_96dp.png',
  sites:      'Sites/logo_sites_2026q2_color_2x_web_96dp.png',
  voice:      'Voice/logo_voice_2026q2_color_2x_web_96dp.png',
  apps_script:'Apps%20Script/logo_apps_script_192px.png',
  gemini:     'Gemini/logo_gemini_2026q2_color_1x_web_560dp.png',
};

// fonts.gstatic.com fallback paths (2026-06-27 verified) for apps not yet in 2026Q2
var _WORKSPACE_LOGOS = {
  gmail:      'gmail/v9',
  drive:      'drive/v4',
  docs:       'docs_2020q4/v12',
  sheets:     'sheets_2020q4/v10',
  slides:     'slides_2020q4/v10',
  calendar:   'calendar_2020q4/v10',
  meet:       'meet_2020q4/v8',
  forms:      'forms_2020q4/v6',
  chat:       'chat_2020q4/v8',
  classroom:  'classroom/v6',
  keep:       'keep/v7',
  sites:      'sites/v8',
  vault:      'vault/v6',
  groups:     'groups/v9',
  tasks:      'tasks/v9',
  contacts:   'contacts/v9',
  jamboard:   'jamboard/v4',
  admin:      'admin/v8',
  appsheet:   'appsheet/v5',
  currents:   'currents/v14'
};

// Brand colours — used for letter-badge fallback when app is unknown
var _WORKSPACE_COLORS = {
  gmail: '#EA4335', drive: '#4285F4', docs: '#4285F4', sheets: '#34A853',
  slides: '#FBBC04', calendar: '#4285F4', meet: '#00832D', forms: '#7248B9',
  chat: '#00AC47', classroom: '#0F9D58', keep: '#FBBC04', sites: '#4285F4',
  vault: '#4285F4', groups: '#EA4335', tasks: '#4285F4', contacts: '#34A853',
  jamboard: '#FF7043', admin: '#4285F4', appsheet: '#4285F4', currents: '#4285F4'
};

// ─── Helper: inject Material Symbols font once per page ──────────────────────
// font-variation-settings axis names MUST use single quotes inside <style> blocks
// to avoid broken HTML when the same values appear in inline style attributes.
var _MS_INJECTED = {};
function _materialSymbolsFont(style) {
  var key = style || 'outlined';
  if (_MS_INJECTED[key]) return '';
  _MS_INJECTED[key] = true;
  var href = key === 'rounded' ? _MATERIAL_SYMBOLS_ROUNDED_URL : _MATERIAL_SYMBOLS_CSS_URL;
  var family = key === 'rounded' ? 'Material Symbols Rounded' : 'Material Symbols Outlined';
  // Single-quoted font-variation-settings inside the <style> block — safe in CSS.
  // The .ms-icon class uses CSS vars so per-instance overrides go via --ms-* vars, not inline style.
  return '<style>'
    + '@import url("' + href + '");'
    + '.ms-icon{'
    +   'font-family:"' + family + '";'
    +   'font-weight:normal;font-style:normal;font-size:inherit;line-height:1;'
    +   'display:inline-block;text-transform:none;letter-spacing:normal;'
    +   'word-wrap:normal;white-space:nowrap;direction:ltr;'
    +   '-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;'
    +   "font-variation-settings:'FILL' var(--ms-fill,0),'wght' var(--ms-w,400),'GRAD' var(--ms-g,0),'opsz' var(--ms-o,24);"
    + '}'
    + '</style>';
}

// ─── google_icon ──────────────────────────────────────────────────────────────
// A single Material Symbol. name = icon ligature (e.g. "home", "check_circle").
// Browse all names: fonts.google.com/icons
_RENDERERS['google_icon'] = function(b) {
  var name   = _esc(b.name || b.icon || 'star');
  var size   = _esc(String(b.size || '24px'));
  var color  = b.color  || b.accent || 'currentColor';
  var fill   = b.filled ? 1 : 0;
  var weight = b.weight || 400;
  var grade  = b.grade  || 0;
  var opsz   = parseInt(b.size) || 24;
  var style  = b.style  || 'outlined';
  var inline = b.inline !== false;
  var label  = b.label ? '<span style="font-size:0.82rem;color:var(--muted,#6b7280);margin-left:6px;">' + _esc(b.label) + '</span>' : '';

  // CSS vars drive font-variation-settings — no quotes needed in inline style attribute
  var cssVars = '--ms-fill:' + fill + ';--ms-w:' + weight + ';--ms-g:' + grade + ';--ms-o:' + opsz;
  var iconSpan = '<span class="ms-icon" style="' + cssVars + ';font-size:' + size + ';color:' + color + ';" aria-hidden="true">' + name + '</span>';

  return _materialSymbolsFont(style)
    + '<span style="display:' + (inline ? 'inline-flex' : 'flex') + ';align-items:center;' + (inline ? '' : 'margin:var(--a2ui-block-gap,1.25rem) 0;') + '">'
    + iconSpan + label + '</span>';
};

// ─── icon_badge ───────────────────────────────────────────────────────────────
// Material Symbol inside a coloured badge (circle or rounded square).
_RENDERERS['icon_badge'] = function(b) {
  var name   = _esc(b.name || b.icon || 'star');
  var size   = parseInt(b.icon_size || 24, 10);
  var bg     = b.bg || b.accent || 'var(--a2ui-accent,#6366f1)';
  var color  = b.color || '#fff';
  var pad    = _esc(b.padding || '12px');
  var radius = _esc(b.radius  || '50%');
  var fill   = b.filled ? 1 : 0;
  var weight = b.weight || 400;
  var style  = b.style  || 'outlined';
  var label  = b.label  ? '<div style="font-size:0.78rem;color:var(--muted,#6b7280);margin-top:4px;text-align:center;">' + _esc(b.label) + '</div>' : '';
  var cssVars = '--ms-fill:' + fill + ';--ms-w:' + weight + ';--ms-g:0;--ms-o:' + size;

  return _materialSymbolsFont(style)
    + '<div style="display:inline-flex;flex-direction:column;align-items:center;text-align:center;margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + '<div style="display:flex;align-items:center;justify-content:center;background:' + bg + ';padding:' + pad + ';border-radius:' + radius + ';">'
    + '<span class="ms-icon" style="' + cssVars + ';font-size:' + size + 'px;color:' + color + ';" aria-hidden="true">' + name + '</span>'
    + '</div>' + label + '</div>';
};

// ─── icon_row ─────────────────────────────────────────────────────────────────
// Horizontal strip of Material Symbol icon+label pairs.
_RENDERERS['icon_row'] = function(b) {
  var items  = b.items  || [];
  var size   = parseInt(b.icon_size || 20, 10);
  var color  = b.color  || b.accent || 'var(--a2ui-accent,#6366f1)';
  var fill   = b.filled ? 1 : 0;
  var style  = b.style  || 'outlined';
  var gap    = _esc(b.gap || '12px');
  var cssVarsBase = '--ms-fill:' + fill + ';--ms-w:400;--ms-g:0;--ms-o:' + size;

  var html = items.map(function(item) {
    var ic  = _esc(item.name || item.icon || 'check');
    var lbl = item.label || item.text || '';
    var c   = item.color || item.accent || color;
    return '<div style="display:flex;align-items:center;gap:8px;">'
      + '<span class="ms-icon" style="' + cssVarsBase + ';font-size:' + size + 'px;color:' + c + ';flex-shrink:0;" aria-hidden="true">' + ic + '</span>'
      + (lbl ? '<span style="font-size:0.875rem;color:var(--text,#374151);">' + _esc(lbl) + '</span>' : '')
      + '</div>';
  }).join('');

  return _materialSymbolsFont(style)
    + '<div style="display:flex;flex-wrap:wrap;gap:' + gap + ';margin:var(--a2ui-block-gap,1.25rem) 0;">' + html + '</div>';
};

// ─── workspace_logo ───────────────────────────────────────────────────────────
// Single Google Workspace product logo from official CDN.
// Unknown app names get a coloured letter badge (no onerror JS needed — GAS strips event handlers).
_RENDERERS['workspace_logo'] = function(b) {
  var app    = (b.app || b.name || 'drive').toLowerCase();
  var size   = parseInt(b.size || 48, 10);
  var path   = _WORKSPACE_LOGOS[app];
  var labelVal = b.label !== undefined ? b.label : _wsCapitalise(app);
  var label  = String(labelVal);
  var inline = b.inline !== false;
  var wrapStyle = 'display:inline-flex;flex-direction:column;align-items:center;' + (inline ? '' : 'margin:var(--a2ui-block-gap,1.25rem) 0;');
  var lblHtml = label ? '<span style="font-size:0.72rem;color:var(--muted,#6b7280);margin-top:4px;text-align:center;">' + _esc(label) + '</span>' : '';

  if (!path) {
    // Unknown app — render coloured letter badge
    var fbBg  = _WORKSPACE_COLORS[app] || '#4285F4';
    var fbCh  = _esc((app[0] || 'G').toUpperCase());
    return '<span style="' + wrapStyle + '">'
      + '<span style="width:' + size + 'px;height:' + size + 'px;border-radius:8px;background:' + fbBg + ';display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:' + Math.round(size * 0.5) + 'px;color:#fff;">' + fbCh + '</span>'
      + lblHtml + '</span>';
  }

  // Prefer 2026Q2 PNG from workspacelogos.com, fall back to fonts.gstatic SVG
  var path2026 = _WORKSPACE_LOGOS_2026[app];
  var src = path2026 ? (_WL_BASE + path2026) : (_LOGO_BASE + path + '/192px.svg');
  return '<span style="' + wrapStyle + '">'
    + '<img src="' + src + '" width="' + size + '" height="' + size + '" alt="' + _esc(app) + '" style="display:block;object-fit:contain;">'
    + lblHtml + '</span>';
};

function _wsCapitalise(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}

// ─── workspace_logo_strip ─────────────────────────────────────────────────────
// Horizontal strip of Workspace logos. greyscale by default, colour on hover.
// No JS/onerror — all apps are validated against _WORKSPACE_LOGOS map.
_RENDERERS['workspace_logo_strip'] = function(b) {
  var uid    = 'ws' + Math.random().toString(36).substr(2, 5);
  var apps   = b.apps || ['gmail','drive','docs','sheets','slides','meet'];
  var size   = parseInt(b.size || 40, 10);
  var gap    = _esc(b.gap || '24px');
  var label  = b.title || b.label || '';
  var grey   = b.greyscale !== false;
  var bg     = b.bg    || 'transparent';
  var align  = b.align === 'center' ? 'center' : b.align === 'right' ? 'flex-end' : 'flex-start';

  var css = grey
    ? '<style>.' + uid + '{filter:grayscale(1);opacity:0.55;transition:filter 0.25s,opacity 0.25s;display:block;object-fit:contain;}.' + uid + ':hover{filter:none;opacity:1;}</style>'
    : '';

  var logos = apps.map(function(app) {
    var key  = app.toLowerCase();
    var path = _WORKSPACE_LOGOS[key];
    var fbBg = _WORKSPACE_COLORS[key] || '#4285F4';
    var fbCh = _esc((key[0] || 'G').toUpperCase());
    if (!path) {
      return '<span style="width:' + size + 'px;height:' + size + 'px;background:' + fbBg + ';border-radius:6px;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:' + Math.round(size*0.5) + 'px;color:#fff;" title="' + _esc(key) + '">' + fbCh + '</span>';
    }
    var path2026 = _WORKSPACE_LOGOS_2026[key];
    var src2026 = path2026 ? (_WL_BASE + path2026) : (_LOGO_BASE + path + '/192px.svg');
    return '<img src="' + src2026 + '" width="' + size + '" height="' + size
      + '" alt="' + _esc(key) + '" title="' + _wsCapitalise(key) + '" class="' + uid + '">';
  }).join('');

  var title = label ? '<div style="font-size:0.75rem;font-weight:600;color:var(--muted,#9ca3af);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px;">' + _esc(label) + '</div>' : '';

  return css + '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;background:' + bg + ';border-radius:10px;">'
    + title
    + '<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:' + align + ';gap:' + gap + ';">'
    + logos + '</div></div>';
};

// ─── workspace_logo_grid ──────────────────────────────────────────────────────
// Grid of all Workspace product logos with labels and hover highlight.
_RENDERERS['workspace_logo_grid'] = function(b) {
  var uid    = 'wg' + Math.random().toString(36).substr(2, 5);
  var apps   = b.apps || Object.keys(_WORKSPACE_LOGOS);
  var size   = parseInt(b.size || 48, 10);
  var cols   = b.cols || 5;
  var grey   = b.greyscale || false;

  var css = '<style>.' + uid + '-c{display:flex;flex-direction:column;align-items:center;gap:6px;padding:12px 8px;border-radius:10px;transition:background 0.2s;}'
    + '.' + uid + '-c:hover{background:var(--surface,#f9fafb);}'
    + '.' + uid + '-i{' + (grey ? 'filter:grayscale(1);opacity:0.6;' : '') + 'transition:filter 0.25s,opacity 0.25s;object-fit:contain;}'
    + '.' + uid + '-c:hover .' + uid + '-i{filter:none;opacity:1;}'
    + '</style>';

  var cells = apps.map(function(app) {
    var key   = typeof app === 'string' ? app.toLowerCase() : app;
    var path  = _WORKSPACE_LOGOS[key];
    var lbl   = b.show_labels !== false ? _wsCapitalise(key) : '';
    var fbBg  = _WORKSPACE_COLORS[key] || '#4285F4';
    var fbCh  = _esc((key[0] || 'G').toUpperCase());
    var inner = path
      ? '<img src="' + _LOGO_BASE + path + '/192px.svg" width="' + size + '" height="' + size + '" class="' + uid + '-i" alt="' + _esc(key) + '">'
      : '<span style="width:' + size + 'px;height:' + size + 'px;background:' + fbBg + ';border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:' + Math.round(size*0.5) + 'px;color:#fff;">' + fbCh + '</span>';
    return '<div class="' + uid + '-c">'
      + inner
      + (lbl ? '<span style="font-size:0.7rem;color:var(--muted,#6b7280);font-weight:500;text-align:center;">' + _esc(lbl) + '</span>' : '')
      + '</div>';
  }).join('');

  var title = b.title ? '<div style="font-size:1rem;font-weight:700;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';

  return css + '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + title
    + '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:4px;">' + cells + '</div>'
    + '</div>';
};

// ─── icon_feature_grid ────────────────────────────────────────────────────────
// Feature grid using Material Symbol icons.
_RENDERERS['icon_feature_grid'] = function(b) {
  var items  = b.items  || [];
  var cols   = b.cols   || 3;
  var size   = parseInt(b.icon_size || 28, 10);
  var fill   = b.filled ? 1 : 0;
  var style  = b.style  || 'outlined';
  var accent = b.accent || 'var(--a2ui-accent,#6366f1)';
  var cssVarsBase = '--ms-fill:' + fill + ';--ms-w:400;--ms-g:0;--ms-o:' + size;

  var cells = items.map(function(item) {
    var icon  = _esc(item.icon || item.name || 'star');
    var c     = item.color || item.accent || accent;
    var ttl   = item.title || item.label || '';
    var txt   = item.text  || item.description || '';
    return '<div style="padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);transition:box-shadow 0.2s;" onmouseover="this.style.boxShadow=\'0 4px 12px rgba(0,0,0,0.08)\'" onmouseout="this.style.boxShadow=\'none\'">'
      + '<span class="ms-icon" style="' + cssVarsBase + ';font-size:' + size + 'px;color:' + c + ';display:block;margin-bottom:10px;" aria-hidden="true">' + icon + '</span>'
      + (ttl ? '<div style="font-size:0.875rem;font-weight:700;color:var(--text,#111827);margin-bottom:4px;">' + _esc(ttl) + '</div>' : '')
      + (txt ? '<div style="font-size:0.8rem;color:var(--muted,#6b7280);line-height:1.5;">' + _esc(txt) + '</div>' : '')
      + '</div>';
  }).join('');

  var title = b.title ? '<div style="font-size:1rem;font-weight:700;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';

  return _materialSymbolsFont(style)
    + '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + title
    + '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:12px;">' + cells + '</div>'
    + '</div>';
};

// ─── icon_checklist ───────────────────────────────────────────────────────────
// Checklist with Material Symbol icons per item.
_RENDERERS['icon_checklist'] = function(b) {
  var items   = b.items  || [];
  var size    = parseInt(b.icon_size || 20, 10);
  var accent  = b.accent || 'var(--a2ui-accent,#6366f1)';
  var fill    = b.filled !== false ? 1 : 0;
  var style   = b.style  || 'outlined';
  var defIcon = b.default_icon || 'check_circle';
  var cssVarsBase = '--ms-fill:' + fill + ';--ms-w:400;--ms-g:0;--ms-o:' + size;

  var rows = items.map(function(item) {
    var text  = typeof item === 'string' ? item : (item.text || item.label || '');
    var icon  = typeof item === 'string' ? defIcon : (item.icon || defIcon);
    var c     = typeof item === 'string' ? accent : (item.color || item.accent || accent);
    var sub   = typeof item === 'object' && item.sublabel ? '<div style="font-size:0.75rem;color:var(--muted,#9ca3af);margin-top:2px;">' + _esc(item.sublabel) + '</div>' : '';
    return '<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid var(--border,#f3f4f6);">'
      + '<span class="ms-icon" style="' + cssVarsBase + ';font-size:' + size + 'px;color:' + c + ';flex-shrink:0;margin-top:1px;" aria-hidden="true">' + _esc(icon) + '</span>'
      + '<div><div style="font-size:0.875rem;color:var(--text,#374151);">' + _esc(text) + '</div>' + sub + '</div>'
      + '</div>';
  }).join('');

  var title = b.title ? '<div style="font-size:0.9rem;font-weight:700;color:var(--text,#111827);margin-bottom:8px;">' + _esc(b.title) + '</div>' : '';

  return _materialSymbolsFont(style)
    + '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + title + rows + '</div>';
};
