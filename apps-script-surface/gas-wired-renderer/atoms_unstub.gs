// atoms_unstub.gs — renderers for all previously-stub atoms
// All pure CSS / SVG / vanilla JS — no external dependencies.

// ─── trend_indicator ──────────────────────────────────────────────────────────
_RENDERERS['trend_indicator'] = function(b) {
  var dir   = b.trend_direction || b.direction || 'stable';
  var label = _esc(b.label || '');
  var ctx   = b.context ? '<span style="font-size:0.75rem;color:var(--muted,#6b7280);margin-left:6px;">' + _esc(b.context) + '</span>' : '';
  var map   = { up: ['↑', '#0b7a55', '#d1fae5'], down: ['↓', '#ef4444', '#fee2e2'], stable: ['→', '#6b7280', '#f3f4f6'] };
  var cfg   = map[dir] || map.stable;
  var col   = b.color || cfg[1];
  return '<span data-cb="node" data-key="' + _ckey(b.label, 'trend_indicator') + '" style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:20px;background:' + cfg[2] + ';font-size:0.82rem;font-weight:600;color:' + col + ';">'
    + cfg[0] + ' ' + label + ctx + '</span>';
};

// ─── metric_delta ─────────────────────────────────────────────────────────────
_RENDERERS['metric_delta'] = function(b) {
  var label   = _esc(b.label || '');
  var current = _esc(b.current_value || b.value || '');
  var delta   = _esc(b.delta_value || b.delta || '');
  var dtype   = b.delta_type || (delta.charAt(0) === '-' ? 'decrease' : 'increase');
  var dColor  = dtype === 'increase' ? '#0b7a55' : dtype === 'decrease' ? '#ef4444' : '#6b7280';
  var dBg     = dtype === 'increase' ? '#d1fae5' : dtype === 'decrease' ? '#fee2e2' : '#f3f4f6';
  var arrow   = dtype === 'increase' ? '↑' : dtype === 'decrease' ? '↓' : '→';
  var period  = b.comparison_period ? '<div style="font-size:0.72rem;color:var(--a2ui-muted,#666666);margin-top:2px;">' + _esc(b.comparison_period) + '</div>' : '';
  var inner = '<div style="font-size:0.75rem;font-weight:600;color:var(--a2ui-muted,#666666);text-transform:uppercase;letter-spacing:0.05em;">' + label + '</div>'
    + '<div style="font-size:2rem;font-weight:700;color:var(--a2ui-text,#171717);line-height:1.2;margin:4px 0;">' + current + '</div>'
    + (delta ? '<span style="display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:12px;background:' + dBg + ';color:' + dColor + ';font-size:0.8rem;font-weight:600;width:fit-content;">' + arrow + ' ' + delta + '</span>' : '')
    + period;
  var res = _cardChrome(inner, 'card', 'display:inline-flex;flex-direction:column;padding:16px 20px;min-width:140px;');
  return '<div data-cb="node" data-key="' + _ckey(b.label, 'metric_delta') + '"' + res.substring(4);
};

// ─── action_required_card ─────────────────────────────────────────────────────
_RENDERERS['action_required_card'] = function(b) {
  var urgency = b.urgency || b.level || 'medium';
  var uMap    = { high: ['🔴', '#ef4444', '#fef2f2', '#fecaca'], medium: ['🟡', '#a06707', '#fffbeb', '#fde68a'], low: ['🔵', '#3b82f6', '#eff6ff', '#bfdbfe'] };
  var cfg     = uMap[urgency] || uMap.medium;
  var icon    = b.icon || cfg[0];
  var btnHtml = (b.action_label && b.action_url)
    ? '<a href="' + _safeUrl(b.action_url) + '" target="_top" style="display:inline-block;margin-top:14px;padding:8px 20px;background:' + cfg[1] + ';color:#fff;border-radius:8px;font-size:0.85rem;font-weight:600;text-decoration:none;">' + _esc(b.action_label) + '</a>'
    : '';
  var deadline = b.deadline ? '<div style="font-size:0.75rem;color:' + cfg[1] + ';font-weight:600;margin-top:8px;">Due: ' + _esc(b.deadline) + '</div>' : '';
  var k = b.title ? _esc(String(b.title)) : 'action_required_card';
  return '<div data-cb="node" data-key="' + k + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:18px 20px;border-left:4px solid ' + cfg[1] + ';border-radius:0 10px 10px 0;background:' + cfg[2] + ';">'
    + '<div style="display:flex;align-items:flex-start;gap:12px;">'
    + '<span style="font-size:1.4rem;">' + icon + '</span>'
    + '<div style="flex:1;">'
    + '<div style="font-weight:700;font-size:0.95rem;color:var(--text,#111827);">' + _esc(b.title || 'Action Required') + '</div>'
    + (b.description ? '<div style="font-size:0.85rem;color:var(--muted,#6b7280);margin-top:4px;line-height:1.5;">' + _markdownToHtml(b.description) + '</div>' : '')
    + deadline + btnHtml
    + '</div></div></div>';
};

// ─── toggle_switch ────────────────────────────────────────────────────────────
_RENDERERS['toggle_switch'] = function(b) {
  var uid     = 'tog' + Math.random().toString(36).substr(2, 5);
  var label   = _esc(b.label || '');
  var checked = b.is_checked ? ' checked' : '';
  var name    = _esc(b.name || uid);
  var accent  = b.accent || 'var(--a2ui-accent,#4f46e5)';
  return '<style>'
    + '#' + uid + '-inp{display:none;}'
    + '#' + uid + '-trk{display:inline-flex;width:44px;height:24px;border-radius:12px;background:#d1d5db;cursor:pointer;align-items:center;padding:2px;transition:background 0.2s;flex-shrink:0;}'
    + '#' + uid + '-inp:checked ~ label #' + uid + '-trk{background:' + accent + ';}'
    + '#' + uid + '-knob{width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.2);transition:transform 0.2s;}'
    + '#' + uid + '-inp:checked ~ label #' + uid + '-knob{transform:translateX(20px);}'
    + '</style>'
    + '<div style="display:flex;align-items:center;gap:10px;margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + '<input type="checkbox" id="' + uid + '-inp" name="' + name + '"' + checked + '>'
    + '<label for="' + uid + '-inp" style="display:flex;align-items:center;gap:10px;cursor:pointer;font-size:0.875rem;color:var(--text,#111827);">'
    + '<span id="' + uid + '-trk"><span id="' + uid + '-knob"></span></span>'
    + label + '</label></div>';
};

// ─── expandable_text ──────────────────────────────────────────────────────────
_RENDERERS['expandable_text'] = function(b) {
  var summary = _esc(b.summary || 'Read more');
  var details = _markdownToHtml(b.details || b.content || '');
  var open    = b.initial_state_expanded ? ' open' : '';
  return '<details data-cb="node" data-key="' + _ckey(b.summary, 'expandable_text') + '"' + open + ' style="margin:var(--a2ui-block-gap,1.25rem) 0;border:1px solid var(--border,#e5e7eb);border-radius:8px;overflow:hidden;">'
    + '<summary style="padding:10px 14px;font-size:0.875rem;font-weight:600;color:var(--text,#111827);cursor:pointer;background:var(--surface,#f9fafb);list-style:none;">'
    + '▶ ' + summary + '</summary>'
    + '<div style="padding:14px 16px;font-size:0.875rem;line-height:1.6;color:var(--text,#374151);">' + details + '</div></details>';
};

// ─── otp_input ────────────────────────────────────────────────────────────────
_RENDERERS['otp_input'] = function(b) {
  var len   = Math.min(b.length || 6, 8);
  var val   = String(b.value || '').replace(/\D/g, '');
  var label = b.label ? '<div style="font-size:0.82rem;font-weight:600;color:var(--text,#111827);margin-bottom:8px;">' + _esc(b.label) + '</div>' : '';
  var uid   = 'otp' + Math.random().toString(36).substr(2, 5);
  var boxes = '';
  for (var i = 0; i < len; i++) {
    var digit = val.charAt(i) || '';
    boxes += '<input id="' + uid + i + '" aria-label="' + _esc((b.label || 'Verification code') + ', digit ' + (i + 1) + ' of ' + len) + '" maxlength="1" inputmode="numeric" pattern="[0-9]" value="' + _esc(digit) + '" '
      + 'style="width:44px;height:52px;text-align:center;font-size:1.4rem;font-weight:700;border:2px solid var(--border,#e5e7eb);border-radius:8px;background:var(--bg,#fff);color:var(--text,#111827);font-family:inherit;" '
      + 'oninput="var n=this.nextElementSibling;if(this.value&&n&&n.tagName===\'INPUT\')n.focus();" '
      + 'onkeydown="if(event.key===\'Backspace\'&&!this.value){var p=this.previousElementSibling;if(p&&p.tagName===\'INPUT\')p.focus();}">';
  }
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + label
    + '<div style="display:flex;gap:8px;flex-wrap:wrap;">' + boxes + '</div></div>';
};

// ─── combobox ─────────────────────────────────────────────────────────────────
_RENDERERS['combobox'] = function(b) {
  var cbId    = 'cb' + Math.random().toString(36).substr(2, 6);
  var label   = b.label ? '<label for="' + cbId + '" style="display:block;font-size:0.82rem;font-weight:600;color:var(--text,#111827);margin-bottom:4px;">' + _esc(b.label) + '</label>' : '';
  var name    = _esc(b.name || 'combobox');
  var opts    = (b.options || []).map(function(o) {
    var val = typeof o === 'object' ? o.value : o;
    var lbl = typeof o === 'object' ? (o.label || o.value) : o;
    var sel = (b.selected && b.selected == val) ? ' selected' : '';
    return '<option value="' + _esc(String(val)) + '"' + sel + '>' + _esc(String(lbl)) + '</option>';
  }).join('');
  var placeholder = b.placeholder ? '<option value="" disabled' + (b.selected ? '' : ' selected') + '>' + _esc(b.placeholder) + '</option>' : '';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + label
    + '<select id="' + cbId + '"' + (b.label ? '' : ' aria-label="' + _esc(b.placeholder || b.name || 'Choose an option') + '"') + ' name="' + name + '" style="width:100%;padding:8px 12px;border:1px solid var(--border,#e5e7eb);border-radius:8px;font-size:0.875rem;background:var(--bg,#fff);color:var(--text,#111827);font-family:inherit;">'
    + placeholder + opts + '</select></div>';
};

// ─── multi_select_input ───────────────────────────────────────────────────────
_RENDERERS['multi_select_input'] = function(b) {
  var label   = b.label ? '<div style="font-size:0.82rem;font-weight:600;color:var(--text,#111827);margin-bottom:6px;">' + _esc(b.label) + '</div>' : '';
  var selected = b.selected || [];
  var opts = (b.options || []).map(function(o) {
    var val = typeof o === 'object' ? String(o.value) : String(o);
    var lbl = typeof o === 'object' ? (o.label || o.value) : o;
    var on  = selected.indexOf(val) >= 0;
    var accent = b.accent || 'var(--a2ui-accent,#4f46e5)';
    return '<label style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;cursor:pointer;font-size:0.82rem;border:1px solid ' + (on ? accent : 'var(--border,#e5e7eb)') + ';background:' + (on ? accent + '15' : 'var(--bg,#fff)') + ';color:' + (on ? accent : 'var(--text,#374151)') + ';">'
      + '<input type="checkbox" name="' + _esc(b.name || 'ms') + '[]" value="' + _esc(val) + '"' + (on ? ' checked' : '') + ' style="position:absolute;opacity:0;width:1px;height:1px;margin:0;">' + _esc(String(lbl)) + '</label>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + label
    + '<div style="display:flex;flex-wrap:wrap;gap:6px;">' + opts + '</div></div>';
};

// ─── avatar_group ─────────────────────────────────────────────────────────────
_RENDERERS['avatar_group'] = function(b) {
  var rawAvatars = Array.isArray(b.avatars) ? b.avatars : [];
  var avatars = rawAvatars.slice(0, 6);
  var totalRaw = _numLoose(b.total_count);
  var total = totalRaw !== null ? Math.min(Math.floor(totalRaw), 99999) : rawAvatars.length;
  var labelText = _textLoose(b.label);
  var colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9'];

  var imgs = avatars.map(function(a, i) {
    var name = '';
    var url = '';
    var color = '';
    if (typeof a === 'string') {
      name = a;
    } else if (a && typeof a === 'object' && !Array.isArray(a)) {
      name = _textLoose(a.name);
      url = _firstText(a.url, a.avatar_url, a.src);
      color = _textLoose(a.color);
    } else {
      return '';
    }

    var safeUrl = url ? _safe_href(url, ['https', 'http']) : '';
    var marginLeft = i > 0 ? '-10px' : '0';

    if (safeUrl) {
      return '<img data-cb="item" data-key="' + _esc(name) + '" src="' + _esc(safeUrl) + '" alt="' + _esc(name) + '" title="' + _esc(name) + '" ' +
        'style="width:36px;height:36px;border-radius:50%;border:2px solid #fff;object-fit:cover;margin-left:' + marginLeft + ';">';
    } else {
      var words = name ? name.split(/\s+/).filter(Boolean) : [];
      var initials = words.length > 0 ? words.slice(0, 2).map(function(w){ return Array.from(w)[0]; }).join('').toUpperCase() : '?';
      var bg = color ? _safe_css(color, colors[i % colors.length]) : colors[i % colors.length];
      var ariaAttr = name ? ' role="img" aria-label="' + _esc(name) + '"' : ' role="img"';
      return '<div data-cb="item" data-key="' + _esc(name) + '"' + ariaAttr + ' title="' + _esc(name) + '" ' +
        'style="width:36px;height:36px;border-radius:50%;background:' + bg + ';border:2px solid #fff;' +
        'display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;color:#fff;margin-left:' + marginLeft + ';">' +
        _esc(initials) + '</div>';
    }
  }).join('');

  var surplusCount = total - avatars.length;
  var extraHtml = '';
  if (surplusCount > 0) {
    extraHtml = '<div role="img" aria-label="+' + surplusCount + ' more" ' +
      'style="width:36px;height:36px;border-radius:50%;background:#e5e7eb;border:2px solid #fff;' +
      'display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;color:var(--muted,#5f6368);margin-left:-10px;">' +
      '+' + surplusCount + '</div>';
  }

  var labelHtml = labelText ? '<span style="font-size:0.82rem;color:var(--muted,#5f6368);margin-left:10px;">' + _esc(labelText) + '</span>' : '';
  var groupLabel = labelText ? labelText : 'Avatars';

  return '<div role="group" aria-label="' + _esc(groupLabel) + '" ' +
    'style="display:flex;align-items:center;margin:var(--a2ui-block-gap,1.25rem) 0;">' +
    imgs + extraHtml + labelHtml + '</div>';
};

// ─── contributor_list ─────────────────────────────────────────────────────────
_RENDERERS['contributor_list'] = function(b) {
  var rawContributors = Array.isArray(b.contributors) ? b.contributors : [];
  var contributors = rawContributors.slice(0, 100);
  var titleText = b.title !== undefined ? _textLoose(b.title) : 'Contributors';
  if (!titleText) {
    titleText = 'Contributors';
  }

  var items = contributors.map(function(c) {
    var name = '';
    var role = '';
    var avatarUrl = '';
    var url = '';
    var color = '';
    var contribs = null;

    if (typeof c === 'string') {
      name = c;
    } else if (c && typeof c === 'object' && !Array.isArray(c)) {
      name = _textLoose(c.name);
      role = _textLoose(c.role);
      avatarUrl = _firstText(c.avatar_url, c.avatar, c.image);
      url = _firstText(c.url, c.profile_url, c.link);
      color = _textLoose(c.color);
      var cNum = _numLoose(c.contributions);
      if (cNum !== null) {
        contribs = Math.min(Math.floor(cNum), 999999999);
      }
    } else {
      return '';
    }

    var safeAvatar = avatarUrl ? _safe_href(avatarUrl, ['https', 'http']) : '';

    var avHtml = '';
    if (safeAvatar) {
      avHtml = '<img src="' + _esc(safeAvatar) + '" alt="" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">';
    } else {
      var initial = name ? Array.from(name)[0].toUpperCase() : '?';
      var bg = '#e8f0fe';
      var fg = '#1a73e8';
      if (color) {
        bg = _safe_css(color, '#e8f0fe');
        fg = bg !== '#e8f0fe' ? '#ffffff' : '#1a73e8';
      }
      avHtml = '<div style="width:36px;height:36px;border-radius:50%;background:' + bg + ';color:' + fg + ';' +
        'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;">' + _esc(initial) + '</div>';
    }

    var contribHtml = contribs !== null ? '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-left:6px;">' + contribs + ' contributions</span>' : '';
    var roleHtml = role ? '<div style="font-size:0.76rem;color:var(--muted,#5f6368);">' + _esc(role) + '</div>' : '';

    var bodyHtml = avHtml + '<div>' +
      '<div data-cb="label" data-key="' + _esc(name) + '" style="font-weight:600;color:#111827;font-size:0.88rem;">' +
      _esc(name) + contribHtml + '</div>' +
      roleHtml + '</div>';

    var safeUrl = url ? _safe_href(url, ['https', 'mailto']) : '';

    var rowHtml = '';
    if (safeUrl) {
      rowHtml = '<a data-cb="item" data-key="' + _esc(name) + '" href="' + _esc(safeUrl) + '" target="_blank" rel="noopener" ' +
        'style="display:flex;align-items:center;gap:10px;padding:8px;text-decoration:none;border-radius:8px;">' +
        bodyHtml + '</a>';
    } else {
      rowHtml = '<div data-cb="item" data-key="' + _esc(name) + '" ' +
        'style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:8px;">' +
        bodyHtml + '</div>';
    }

    return '<div role="listitem">' + rowHtml + '</div>';
  }).join('');

  return '<div style="border:1px solid #eaeaea;border:1px solid var(--a2ui-border,#eaeaea);' +
    'border-radius:12px;border-radius:var(--a2ui-radius,12px);padding:10px;margin:1.5rem 0;">' +
    '<div style="font-weight:700;padding:4px 8px;margin-bottom:6px;">' + _esc(titleText) + '</div>' +
    '<div role="list" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:4px;">' +
    items + '</div></div>';
};

// ─── prerequisite_checklist ───────────────────────────────────────────────────
_RENDERERS['prerequisite_checklist'] = function(b) {
  var title = (typeof b.title === 'string' && b.title) ? b.title : 'Prerequisites';
  var rawItems = Array.isArray(b.items) ? b.items.slice(0, 200) : [];
  var rows = '';
  for (var i = 0; i < rawItems.length; i++) {
    var item = rawItems[i];
    if (item === null || item === undefined) continue;
    var text = '', done = false;
    if (typeof item === 'string') {
      text = item;
    } else if (typeof item === 'object' && !Array.isArray(item)) {
      text = (typeof item.text === 'string' && item.text) ? item.text : ((typeof item.label === 'string' && item.label) ? item.label : '');
      done = item.done === true;
    } else {
      continue;
    }
    var icon = done ? '✅' : '⬜';
    var textStyle = done ? 'text-decoration:line-through;color:var(--muted,#9ca3af);' : '';
    var textSpan = textStyle ? '<span style="' + textStyle + '">' + _md_inline(text) + '</span>' : '<span>' + _md_inline(text) + '</span>';
    rows += '<li data-cb="item" data-key="' + _ckey(text, 'item') + '" style="display:flex;align-items:flex-start;gap:8px;padding:5px 0;font-size:0.88rem;color:#374151;border-bottom:1px solid #f9fafb;">' +
      '<span style="flex-shrink:0;">' + icon + '</span>' + textSpan + '</li>';
  }
  return '<div style="border:1px solid #dbeafe;border-radius:12px;border-radius:var(--a2ui-radius,12px);padding:14px 18px;margin:1.5rem 0;background:#eff6ff;">' +
    '<div style="font-weight:700;color:#1e40af;margin-bottom:8px;">📋 ' + _esc(title) + '</div>' +
    '<ul style="list-style:none;padding:0;margin:0;">' + rows + '</ul></div>';
};

// ─── capability_checklist ─────────────────────────────────────────────────────
_RENDERERS['capability_checklist'] = function(b) {
  var rawCapNames = Array.isArray(b.capability_names) ? b.capability_names : [];
  var capNames = rawCapNames.slice(0, 100).map(function(c) { return _textLoose(c); });
  var rawItems = Array.isArray(b.items) ? b.items : [];
  var items = rawItems.slice(0, 100);
  var titleText = _textLoose(b.title);

  var titleHtml = titleText ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:10px;">' + _esc(titleText) + '</div>' : '';

  var isMatrix = capNames.length > 0 && items.some(function(it) {
    return it !== null && typeof it === 'object' && Array.isArray(it.capabilities);
  });

  if (isMatrix) {
    var thCells = capNames.map(function(c) {
      return '<th scope="col" style="padding:8px 12px;font-size:0.78rem;font-weight:600;color:var(--muted,#5f6368);border-bottom:1px solid var(--border,#e5e7eb);text-align:center;">' + _esc(c) + '</th>';
    }).join('');
    var thead = '<thead><tr><th scope="col" style="padding:8px 12px;font-size:0.78rem;font-weight:600;color:var(--muted,#5f6368);border-bottom:1px solid var(--border,#e5e7eb);text-align:left;">Item</th>' + thCells + '</tr></thead>';

    var rows = items.map(function(it) {
      var label = '';
      var caps = [];
      if (it && typeof it === 'object' && !Array.isArray(it)) {
        label = _firstText(it.name, it.text, it.label);
        caps = Array.isArray(it.capabilities) ? it.capabilities : [];
      } else {
        label = _textLoose(it);
      }
      var key = _esc(label);
      var tdCells = capNames.map(function(c, i) {
        var val = i < caps.length ? caps[i] : null;
        var cellContent = '';
        if (val === true) {
          cellContent = '<span style="color:#10b981;font-weight:700;"><span aria-hidden="true">✓</span><span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;">yes</span></span>';
        } else if (val === false) {
          cellContent = '<span style="color:#ef4444;font-weight:700;"><span aria-hidden="true">✗</span><span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;">no</span></span>';
        } else {
          cellContent = '<span style="color:var(--muted,#9ca3af);"><span aria-hidden="true">–</span><span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;">unknown</span></span>';
        }
        return '<td style="padding:8px 12px;text-align:center;border-bottom:1px solid var(--border,#f3f4f6);">' + cellContent + '</td>';
      }).join('');

      return '<tr data-cb="item" data-key="' + key + '">' +
        '<th scope="row" data-cb="label" data-key="' + key + '" style="padding:8px 12px;font-size:0.875rem;font-weight:600;color:var(--text,#111827);border-bottom:1px solid var(--border,#f3f4f6);text-align:left;">' + _esc(label) + '</th>' +
        tdCells + '</tr>';
    }).join('');

    return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);overflow-x:auto;">' +
      titleHtml + '<table style="width:100%;border-collapse:collapse;">' + thead + '<tbody>' + rows + '</tbody></table></div>';
  } else {
    var statusMap = {
      available: ['✓', '#10b981', '#d1fae5'],
      unavailable: ['✗', '#ef4444', '#fee2e2'],
      partial: ['◐', '#f59e0b', '#fef3c7'],
      planned: ['○', '#6b7280', '#f3f4f6']
    };
    var listSource = items.length > 0 ? items : capNames;
    var lis = listSource.map(function(it) {
      var label = '';
      var tierText = '';
      var status = 'available';
      if (it && typeof it === 'object' && !Array.isArray(it)) {
        label = _firstText(it.name, it.text, it.label);
        tierText = _textLoose(it.tier);
        var rawStatus = _textLoose(it.status).toLowerCase();
        if (statusMap[rawStatus]) {
          status = rawStatus;
        } else {
          var boolVal = it.has !== undefined ? it.has : (it.capable !== undefined ? it.capable : it.available);
          if (boolVal === true) {
            status = 'available';
          } else if (boolVal === false) {
            status = 'unavailable';
          } else {
            status = 'available';
          }
        }
      } else {
        label = _textLoose(it);
        status = 'available';
      }

      var key = _esc(label);
      var cfg = statusMap[status] || statusMap.available;
      var tierHtml = tierText ? '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);">' + _esc(tierText) + '</span>' : '';

      return '<li data-cb="item" data-key="' + key + '" style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border,#f3f4f6);font-size:0.875rem;">' +
        '<span style="width:20px;height:20px;border-radius:50%;background:' + cfg[2] + ';color:' + cfg[1] + ';display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;flex-shrink:0;"><span aria-hidden="true">' + cfg[0] + '</span><span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;">' + _esc(status) + '</span></span>' +
        '<span data-cb="label" data-key="' + key + '" style="flex:1;color:var(--text,#374151);">' + _esc(label) + '</span>' +
        tierHtml + '</li>';
    }).join('');

    return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">' +
      titleHtml + '<ul style="list-style:none;padding:0;margin:0;">' + lis + '</ul></div>';
  }
};

// ─── review_callout ───────────────────────────────────────────────────────────
_RENDERERS['review_callout'] = function(b) {
  var rating  = Math.round(b.rating || 5);
  var max     = b.max_rating || 5;
  var stars   = '';
  for (var i = 1; i <= max; i++) {
    stars += '<span style="color:' + (i <= rating ? '#fbbf24' : '#e5e7eb') + ';font-size:1rem;">★</span>';
  }
  return '<div data-cb="node" data-key="' + _ckey(b.author_name, 'review_callout') + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + (b.product_name ? '<div style="font-size:0.75rem;font-weight:600;color:var(--muted,#6b7280);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">' + _esc(b.product_name) + '</div>' : '')
    + '<div style="margin-bottom:10px;">' + stars + '</div>'
    + '<blockquote style="margin:0;font-size:0.9rem;line-height:1.6;color:var(--text,#374151);font-style:italic;">"' + _esc(b.review_text || '') + '"</blockquote>'
    + (b.author_name ? '<div style="margin-top:10px;font-size:0.8rem;font-weight:600;color:var(--muted,#6b7280);">— ' + _esc(b.author_name) + '</div>' : '')
    + '</div>';
};

// ─── rating_comparison ────────────────────────────────────────────────────────
_RENDERERS['rating_comparison'] = function(b) {
  var title = _textLoose(b.title);
  var items = Array.isArray(b.items) ? b.items.slice(0, 100).filter(function(i) { return i && typeof i === 'object' && !Array.isArray(i); }) : [];
  var defaultMax = _numLoose(b.max);
  var sr = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;';
  var rows = '';
  for (var k = 0; k < items.length; k++) {
    var item = items[k];
    var label = _firstText(item.label, item.name);
    var rating = _numLoose(item.rating);
    if (rating === null) rating = _numLoose(item.value);
    if (rating === null) rating = 0;
    var m = _numLoose(item.max);
    if (m === null) m = defaultMax;
    var mx = m === null ? 5 : Math.max(1, Math.min(50, Math.floor(m)));
    rating = Math.max(0, Math.min(mx, rating));
    var filled = Math.floor(rating + 0.5);
    var stars = '';
    for (var i = 1; i <= mx; i++) {
      stars += '<span aria-hidden="true" style="color:' + (i <= filled ? '#fbbf24' : '#e5e7eb') + ';font-size:0.85rem;">★</span>';
    }
    rows += '<div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border,#f3f4f6);font-size:0.875rem;">'
      + '<span style="min-width:120px;color:var(--text,#374151);">' + _esc(label) + '</span>'
      + stars
      + '<span style="font-size:0.8rem;color:var(--muted,#6b7280);margin-left:4px;">(' + _textLoose(rating)
      + '<span style="' + sr + '"> out of ' + mx + '</span>)</span></div>';
  }
  var titleHtml = title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:10px;">' + _esc(title) + '</div>' : '';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + titleHtml + rows + '</div>';
};

// ─── sentiment_summary ────────────────────────────────────────────────────────
_RENDERERS['sentiment_summary'] = function(b) {
  var index = b.sentiment_index || b.positive || 0;
  var neg   = b.negative || (100 - index);
  var neu   = Math.max(0, 100 - index - neg);
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:14px;">' + _esc(b.title) + '</div>' : '';
  function bar(label, pct, color, bg) {
    return '<div style="margin-bottom:10px;">'
      + '<div style="display:flex;justify-content:space-between;font-size:0.78rem;color:var(--muted,#6b7280);margin-bottom:3px;"><span>' + label + '</span><span>' + pct + '%</span></div>'
      + '<div style="background:' + bg + ';border-radius:4px;height:8px;"><div style="background:' + color + ';width:' + pct + '%;height:100%;border-radius:4px;"></div></div></div>';
  }
  var score = '<div style="text-align:center;margin-bottom:16px;"><div style="font-size:2.5rem;font-weight:700;color:#0c855d;">' + index + '%</div><div style="font-size:0.78rem;color:var(--muted,#6b7280);">Positive sentiment</div></div>';
  return '<div data-cb="node" data-key="' + _ckey(b.title, 'sentiment_summary') + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + score
    + bar('Positive', index, '#0c855d', '#d1fae5')
    + bar('Neutral', neu, '#6b7280', '#f3f4f6')
    + bar('Negative', neg, '#ef4444', '#fee2e2')
    + '</div>';
};

// ─── call_mood_board ──────────────────────────────────────────────────────────
_RENDERERS['call_mood_board'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';
  var moods = (b.moods || []).map(function(m) {
    var pct = Math.min(100, m.intensity || 50);
    var color = m.color || 'var(--a2ui-accent,#02020c)';
    return '<div style="text-align:center;min-width:80px;">'
      + '<div style="font-size:1.5rem;">' + _esc(m.icon || m.mood.charAt(0)) + '</div>'
      + '<div style="font-size:0.72rem;color:var(--muted,#6b7280);margin:4px 0;">' + _esc(m.mood || '') + '</div>'
      + '<div style="height:40px;background:#f3f4f6;border-radius:4px;display:flex;align-items:flex-end;overflow:hidden;">'
      + '<div style="width:100%;height:' + pct + '%;background:' + color + ';border-radius:4px;transition:height 0.3s;"></div></div>'
      + '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-top:2px;">' + pct + '%</div></div>';
  }).join('');
  var themes = (b.themes || []).map(function(t) {
    var wt = Math.max(0.8, Math.min(1.6, (t.count || 5) / 10 + 0.8));
    return '<span style="padding:3px 10px;border-radius:12px;background:var(--surface,#f3f4f6);font-size:' + (wt * 0.8) + 'rem;color:var(--text,#374151);">' + _esc(t.term || t.label || '') + '</span>';
  }).join('');
  return '<div data-cb="node" data-key="' + _ckey(b.title, 'call_mood_board') + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title
    + (moods ? '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px;">' + moods + '</div>' : '')
    + (themes ? '<div style="display:flex;flex-wrap:wrap;gap:6px;">' + themes + '</div>' : '')
    + '</div>';
};

// ─── social_proof_banner ──────────────────────────────────────────────────────
_RENDERERS['social_proof_banner'] = function(b) {
  var metricVal = _firstText(b.metric_value, b.count, b.number);
  var metricLbl = _firstText(b.metric_label, b.text);
  var safeIcon = _safe_href(_firstText(b.icon_url), ['https', 'http']);
  var safeLink = _safe_href(_firstText(b.link_url), ['https', 'mailto']);
  var testimonial = _firstText(b.testimonial);

  var rawLogos = Array.isArray(b.logos) ? b.logos : [];
  var logosHtml = [];
  var limit = Math.min(rawLogos.length, 20);
  for (var i = 0; i < limit; i++) {
    var l = rawLogos[i];
    var lName = '', lUrl = '';
    if (l !== null && typeof l === 'object' && !Array.isArray(l)) {
      lName = _firstText(l.name, l.title);
      lUrl = _safe_href(_firstText(l.url), ['https', 'http']);
    } else if (typeof l === 'string' || typeof l === 'number') {
      lName = _textLoose(l);
    } else {
      continue;
    }

    if (lUrl) {
      logosHtml.push('<img src="' + _esc(lUrl) + '" alt="' + _esc(lName) + '" style="height:32px;object-fit:contain;opacity:0.6;filter:grayscale(1);">');
    } else if (lName) {
      logosHtml.push('<span style="font-size:0.8rem;font-weight:700;color:var(--muted,#9ca3af);padding:4px 12px;">' + _esc(lName) + '</span>');
    }
  }

  var logosBar = logosHtml.length ? '<div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:16px;margin:16px 0;">' + logosHtml.join('') + '</div>' : '';
  var metricHtml = (metricVal ? '<div style="font-size:2rem;font-weight:700;color:var(--a2ui-accent,#4f46e5);">' + _esc(metricVal) + '</div>' : '') +
    (metricLbl ? '<div style="font-size:0.82rem;color:var(--muted,#6b7280);">' + _esc(metricLbl) + '</div>' : '');
  var quoteHtml = testimonial ? '<blockquote style="font-style:italic;font-size:0.875rem;color:var(--text,#374151);margin:0;">"' + _esc(testimonial) + '"</blockquote>' : '';
  var iconHtml = safeIcon ? '<img src="' + _esc(safeIcon) + '" alt="" style="width:20px;height:20px;object-fit:contain;margin-bottom:8px;">' : '';

  var ckVal = _ckey(b.metric_label, 'social_proof_banner');
  var cardBody = iconHtml + metricHtml + logosBar + quoteHtml;
  var cardStyle = 'margin:var(--a2ui-block-gap,1.25rem) 0;padding:24px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);text-align:center;';

  if (safeLink) {
    return '<a data-cb="node" data-key="' + ckVal + '" href="' + _esc(safeLink) + '" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;display:block;">' +
      '<div style="' + cardStyle + '">' + cardBody + '</div></a>';
  }
  return '<div data-cb="node" data-key="' + ckVal + '" style="' + cardStyle + '">' + cardBody + '</div>';
};

// ─── expert_endorsement ───────────────────────────────────────────────────────
_RENDERERS['expert_endorsement'] = function(b) {
  var initials = (b.expert_name || '?').split(' ').map(function(w){return w[0];}).join('').substr(0,2).toUpperCase();
  var avatar = b.expert_avatar_url
    ? '<img src="' + _esc(b.expert_avatar_url) + '" alt="' + _esc(b.expert_name||'') + '" style="width:56px;height:56px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
    : '<div style="width:56px;height:56px;border-radius:50%;background:var(--a2ui-accent,#4f46e5);color:#fff;display:flex;align-items:center;justify-content:center;font-size:1.1rem;font-weight:700;flex-shrink:0;">' + initials + '</div>';
  return '<div data-cb="node" data-key="' + _ckey(b.expert_name, 'expert_endorsement') + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border-left:4px solid var(--a2ui-accent,#4f46e5);border-radius:0 10px 10px 0;background:var(--surface,#f9fafb);">'
    + '<blockquote style="margin:0 0 16px 0;font-size:0.9rem;line-height:1.7;color:var(--text,#374151);font-style:italic;">"' + _esc(b.quote || '') + '"</blockquote>'
    + '<div style="display:flex;align-items:center;gap:12px;">' + avatar
    + '<div><div style="font-weight:700;font-size:0.875rem;color:var(--text,#111827);">' + _esc(b.expert_name || '') + '</div>'
    + (b.expert_title ? '<div style="font-size:0.78rem;color:var(--muted,#6b7280);">' + _esc(b.expert_title) + '</div>' : '')
    + (b.expert_organization ? '<div style="font-size:0.78rem;color:var(--muted,#9ca3af);">' + _esc(b.expert_organization) + '</div>' : '')
    + '</div></div></div>';
};

// ─── media_mention_card ───────────────────────────────────────────────────────
_RENDERERS['media_mention_card'] = function(b) {
  var publication = _firstText(b.publication_name, b.publication, b.source);
  var safeLogo = _safe_href(_firstText(b.publication_logo_url, b.logo), ['https', 'http']);
  var headline = _firstText(b.headline, b.quote, b.text);
  var safeUrl = _safe_href(_firstText(b.article_url, b.url), ['https', 'mailto']);
  var date = _firstText(b.date);
  var excerpt = _firstText(b.excerpt);

  var ckVal = _ckey(b.publication_name, 'media_mention_card');

  var logoHtml = safeLogo
    ? '<img src="' + _esc(safeLogo) + '" alt="' + _esc(publication) + '" style="height:24px;object-fit:contain;opacity:0.6;">'
    : '<span style="font-size:0.78rem;font-weight:700;color:var(--muted,#6b7280);">' + _esc(publication) + '</span>';
  var dateHtml = date ? '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);">' + _esc(date) + '</span>' : '';

  var headlineStyle = 'font-size:0.9rem;font-weight:600;color:var(--text,#111827);line-height:1.4;';
  var headlineHtml = safeUrl
    ? '<a href="' + _esc(safeUrl) + '" target="_blank" rel="noopener" style="' + headlineStyle + 'text-decoration:none;">' + _esc(headline) + '</a>'
    : '<div style="' + headlineStyle + '">' + _esc(headline) + '</div>';

  var excerptHtml = excerpt ? '<div style="font-size:0.82rem;color:var(--muted,#6b7280);margin-top:6px;line-height:1.5;">' + _esc(excerpt) + '</div>' : '';

  return '<div data-cb="node" data-key="' + ckVal + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px 20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">' +
    '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">' +
    logoHtml + dateHtml + '</div>' +
    headlineHtml + excerptHtml + '</div>';
};

// ─── media_stream_card ────────────────────────────────────────────────────────
// Real inline iframe again (was a click-to-open placeholder, 2026-09-10 -
// 2026-09-10 same day): #mcp-view (generate_atom_pages.py, both templates)
// now serves from play.a2uicatalog.ai, a genuinely separate, deliberately
// stateless origin, and carries allow-same-origin as a result -- see that
// iframe's own comment for the full reasoning. _safeUrl (not just _esc,
// which only blocks attribute breakout, not a dangerous scheme) gates the
// iframe src the same way this bundle's other embeds already do.
// youtube.com, not youtube-nocookie.com: confirmed live, 2026-09-10 --
// with the sandbox fix alone, youtube-nocookie.com's OWN player errored
// "this video isn't available" on a real major-label video (Rick Astley),
// same failure meetstudio's own gdm_stage_video_panel.ts already documents
// ("some videos -- notably music-label uploads -- refuse to play on the
// privacy-enhanced variant even when playableInEmbed:true"). youtube.com
// honours referrer and has looser playback rights; the tradeoff (real
// YouTube cookies reachable inside this now-allow-same-origin iframe) is
// the same one meetstudio already accepted for the identical reason.
//
// Own explicit `sandbox` on the inner iframe (2026-09-10, roast-panel
// follow-up): this atom's Python and live-JS siblings both gate
// allow-same-origin on `matched` -- true only when `src` was REWRITTEN to
// a platform's own canonical embed endpoint below, false for the
// untouched custom-stream fallback (an arbitrary, unvalidated URL with no
// domain allowlist beyond _safeUrl's scheme check). This version never
// had that distinction; #mcp-view's own allow-same-origin meant EVERY
// media_stream_card render here got full privilege inside play.a2uicatalog.ai
// regardless of whether the URL was a recognized platform. Verified live,
// 2026-09-10: a child iframe's own MORE restrictive sandbox attribute
// takes effect even when its parent is non-opaque (has allow-same-origin)
// -- this is ordinary sandbox semantics, unrelated to the inheritance-
// when-the-PARENT-lacks-allow-same-origin cascade found earlier the same
// day. Vimeo/Google Slides detection added here too, matching the other
// two implementations -- previously only this one lacked it.
_RENDERERS['media_stream_card'] = function(b) {
  var url    = b.url || '';
  var title  = b.title || '';
  var height = b.height || '315px';
  var src = url;
  var matched = false;
  var ytMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
  // mute=1 alongside autoplay=1 isn't optional -- browsers block unmuted
  // autoplay outright, so autoplay=1 alone silently does nothing. Same
  // pairing meetstudio's own gdm_stage_video_panel.ts already uses.
  if (ytMatch) {
    src = 'https://www.youtube.com/embed/' + ytMatch[1] + '?rel=0&autoplay=1&mute=1';
    matched = true;
  }
  var loomMatch = url.match(/loom\.com\/share\/([a-zA-Z0-9]+)/);
  if (loomMatch) {
    src = 'https://www.loom.com/embed/' + loomMatch[1] + '?autoplay=1';
    matched = true;
  }
  var slidesMatch = url.match(/docs\.google\.com\/presentation\/d\/([^/?#]+)/);
  if (slidesMatch) {
    src = 'https://docs.google.com/presentation/d/' + slidesMatch[1] + '/embed?start=false&loop=false';
    matched = true;
  }
  var vimeoMatch = url.match(/vimeo\.com\/(\d+)/);
  if (vimeoMatch) {
    src = 'https://player.vimeo.com/video/' + vimeoMatch[1];
    matched = true;
  }
  var titleHtml = title ? '<div style="font-size:0.82rem;font-weight:600;color:var(--muted,#6b7280);margin-bottom:6px;">' + _esc(title) + '</div>' : '';
  var sandbox = matched
    ? 'allow-scripts allow-same-origin allow-popups allow-forms'
    : 'allow-scripts allow-popups allow-forms';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + titleHtml
    + '<div style="position:relative;padding-top:56.25%;border-radius:10px;overflow:hidden;background:#000;">'
    // allow="autoplay" is required, not decorative -- without it in the
    // iframe's own Permissions Policy, the autoplay=1 query param is
    // silently ignored regardless of the mute state.
    + '<iframe src="' + _safeUrl(src) + '" title="' + _esc(title || 'Media stream') + '" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture" allowfullscreen loading="lazy" sandbox="' + sandbox + '"></iframe>'
    + '</div></div>';
};

// ─── product_thumbnail ────────────────────────────────────────────────────────
_RENDERERS['product_thumbnail'] = function(b) {
  var rawImg = _firstText(b.image_url, b.image, b.thumbnail);
  var safeImg = rawImg ? _safe_href(rawImg, ['https', 'http']) : '';

  var badgeText = _firstText(b.badge);
  var badgeHtml = badgeText ? '<div style="position:absolute;top:8px;left:8px;padding:2px 8px;border-radius:4px;background:var(--a2ui-accent,#4f46e5);color:#fff;font-size:0.72rem;font-weight:700;">' + _esc(badgeText) + '</div>' : '';

  var titleText = _firstText(b.title, b.name);
  var imgHtml = '';
  if (safeImg) {
    imgHtml = '<div style="position:relative;"><img src="' + _esc(safeImg) + '" alt="' + _esc(titleText) + '" style="width:100%;aspect-ratio:1;object-fit:cover;border-radius:8px;">' + badgeHtml + '</div>';
  } else if (badgeHtml) {
    imgHtml = '<div style="position:relative;"><div style="background:#f3f4f6;aspect-ratio:1;border-radius:8px;"></div>' + badgeHtml + '</div>';
  }

  var vendorText = _firstText(b.vendor);
  var vendorHtml = vendorText ? '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);">' + _esc(vendorText) + '</div>' : '';

  var titleHtml = '<div style="font-size:0.875rem;font-weight:600;color:var(--text,#111827);margin:2px 0;">' + _esc(titleText) + '</div>';

  var skuText = _firstText(b.sku);
  var skuHtml = skuText ? '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);">SKU: ' + _esc(skuText) + '</div>' : '';

  var priceStr = _textLoose(b.price);
  var priceSpan = '<span style="font-weight:700;color:var(--text,#111827);">' + _esc(priceStr) + '</span>';

  var compareStr = _textLoose(b.compare_at_price);
  var compareHtml = compareStr ? '<span style="text-decoration:line-through;color:var(--muted,#9ca3af);font-size:0.82rem;margin-left:6px;">' + _esc(compareStr) + '</span>' : '';

  var statusRaw = _firstText(b.status);
  var statusHtml = '';
  if (statusRaw) {
    var stNorm = statusRaw.toLowerCase();
    var bgCol = '#fee2e2';
    var txtCol = '#ef4444';
    if (stNorm === 'active' || stNorm === 'in_stock') {
      bgCol = '#d1fae5';
      txtCol = '#10b981';
    } else if (stNorm === 'draft') {
      bgCol = '#fef3c7';
      txtCol = '#b45309';
    } else if (stNorm === 'archived') {
      bgCol = '#f3f4f6';
      txtCol = '#4b5563';
    }
    var statusLabel = statusRaw.replace(/_/g, ' ');
    statusHtml = '<span style="font-size:0.72rem;padding:2px 6px;border-radius:4px;background:' + bgCol + ';color:' + txtCol + ';margin-left:6px;">' + _esc(statusLabel) + '</span>';
  }

  var priceRow = '<div style="margin-top:6px;">' + priceSpan + compareHtml + statusHtml + '</div>';

  var tagsRaw = Array.isArray(b.tags) ? b.tags : [];
  var tagLis = [];
  var tagsLimit = Math.min(tagsRaw.length, 12);
  for (var i = 0; i < tagsLimit; i++) {
    var tStr = _textLoose(tagsRaw[i]);
    if (tStr) {
      tagLis.push('<li style="padding:1px 6px;border-radius:4px;background:#f3f4f6;color:#4b5563;font-size:0.7rem;">' + _esc(tStr) + '</li>');
    }
  }
  var tagsHtml = tagLis.length ? '<ul style="list-style:none;margin:8px 0 0;padding:0;display:flex;flex-wrap:wrap;gap:4px;">' + tagLis.join('') + '</ul>' : '';

  var rawUrl = _firstText(b.url);
  var safeCardUrl = rawUrl ? _safe_href(rawUrl, ['https', 'mailto']) : '';

  var keyAttr = _ckey(b.sku, 'product_thumbnail');
  var tagOpen = '';
  var tagClose = '';
  if (safeCardUrl) {
    tagOpen = '<a data-cb="node" data-key="' + keyAttr + '" href="' + _esc(safeCardUrl) + '" style="display:block;text-decoration:none;color:inherit;margin:var(--a2ui-block-gap,1.25rem) 0;border:1px solid var(--border,#e5e7eb);border-radius:10px;overflow:hidden;background:var(--bg,#fff);max-width:200px;">';
    tagClose = '</a>';
  } else {
    tagOpen = '<div data-cb="node" data-key="' + keyAttr + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;border:1px solid var(--border,#e5e7eb);border-radius:10px;overflow:hidden;background:var(--bg,#fff);display:inline-block;max-width:200px;">';
    tagClose = '</div>';
  }

  return tagOpen + imgHtml
    + '<div style="padding:10px 12px;">'
    + vendorHtml + titleHtml + skuHtml + priceRow + tagsHtml
    + '</div>' + tagClose;
};

// ─── customer_logo_grid ───────────────────────────────────────────────────────
_RENDERERS['customer_logo_grid'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--muted,#6b7280);text-align:center;margin-bottom:16px;">' + _esc(b.title) + '</div>' : '';
  var cols  = b.cols || 4;
  // Schema only documents `logos` as a bare "list" (no item shape); the web renderer
  // accepts either `url`/`src` for the image and `name`/`alt` for the label, but this only
  // checked `image_url`, so a payload shaped the web way (the CURATED/real one) fell through
  // to the text-only branch and the actual logo image never rendered (surface-parity debt).
  // 2026-09-27.
  var logos = (b.logos || []).map(function(l) {
    var img = l.image_url || l.url || l.src || '';
    var name = l.name || l.alt || '';
    var linkUrl = l.link_url || (l.url && l.image_url ? l.url : '');
    var lKey = _esc(String(name || img));
    if (linkUrl && img) {
      return '<a data-cb="tile" data-key="' + lKey + '" href="' + _safeUrl(linkUrl) + '" target="_top" style="display:flex;align-items:center;justify-content:center;padding:12px;"><img src="' + _esc(img) + '" alt="' + _esc(name) + '" style="max-height:36px;max-width:120px;object-fit:contain;opacity:0.5;filter:grayscale(1);transition:opacity 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.5"></a>';
    }
    if (img) {
      return '<div data-cb="tile" data-key="' + lKey + '" style="display:flex;align-items:center;justify-content:center;padding:12px;"><img src="' + _esc(img) + '" alt="' + _esc(name) + '" style="max-height:36px;max-width:120px;object-fit:contain;opacity:0.5;filter:grayscale(1);"></div>';
    }
    return '<div data-cb="tile" data-key="' + lKey + '" style="display:flex;align-items:center;justify-content:center;padding:12px;font-size:0.8rem;font-weight:700;color:var(--muted,#9ca3af);"><span data-cb="label" data-key="' + lKey + '">' + _esc(name) + '</span></div>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + title
    + '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);border:1px solid var(--border,#e5e7eb);border-radius:10px;overflow:hidden;">' + logos + '</div></div>';
};

// ─── github_repo_card ─────────────────────────────────────────────────────────
_RENDERERS['github_repo_card'] = function(b) {
  var repoRaw = _firstText(b.repo, b.name);
  var ownerRaw = _firstText(b.owner);
  var repoPath = '';
  if (repoRaw.indexOf('/') !== -1) {
    repoPath = repoRaw;
  } else if (ownerRaw && repoRaw) {
    repoPath = ownerRaw + '/' + repoRaw;
  } else {
    repoPath = repoRaw;
  }

  var urlVal = _firstText(b.url);
  var safeUrl = '';
  if (urlVal) {
    safeUrl = _safe_href(urlVal, ['https', 'mailto']);
  } else if (repoPath && /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repoPath)) {
    safeUrl = 'https://github.com/' + repoPath;
  }

  var linkHtml = '';
  if (safeUrl) {
    linkHtml = '<a href="' + _esc(safeUrl) + '" target="_top" style="font-weight:700;font-size:0.9rem;color:var(--a2ui-accent,#4f46e5);text-decoration:none;">' + _esc(repoPath) + '</a>';
  } else {
    linkHtml = '<span style="font-weight:700;font-size:0.9rem;color:var(--a2ui-accent,#4f46e5);">' + _esc(repoPath) + '</span>';
  }

  var visText = _firstText(b.visibility);
  var visHtml = visText ? '<span style="font-size:0.7rem;padding:1px 6px;border:1px solid var(--border,#e5e7eb);border-radius:4px;color:var(--muted,#6b7280);">' + _esc(visText) + '</span>' : '';

  var labelText = _firstText(b.label);
  var labelHtml = (labelText && labelText !== repoPath) ? '<div style="font-size:0.85rem;font-weight:700;color:var(--text,#111827);margin-bottom:6px;">' + _esc(labelText) + '</div>' : '';

  var descText = _firstText(b.description);
  var descHtml = descText ? '<div style="font-size:0.82rem;color:var(--muted,#6b7280);line-height:1.5;margin-bottom:10px;">' + _esc(descText) + '</div>' : '';

  var topicsRaw = Array.isArray(b.topics) ? b.topics : [];
  var topicSpans = [];
  var topicsLimit = Math.min(topicsRaw.length, 20);
  for (var i = 0; i < topicsLimit; i++) {
    var tStr = _textLoose(topicsRaw[i]);
    if (tStr) {
      topicSpans.push('<span style="padding:2px 8px;border-radius:12px;background:#dbeafe;color:#1d4ed8;font-size:0.72rem;">' + _esc(tStr) + '</span>');
    }
  }
  var topicsHtml = topicSpans.length ? '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">' + topicSpans.join('') + '</div>' : '';

  var starsStr = _textLoose(b.stars);
  var starsHtml = starsStr ? '<span style="display:flex;align-items:center;gap:3px;font-size:0.78rem;color:var(--muted,#6b7280);">⭐ ' + _esc(starsStr) + '</span>' : '';

  var forksStr = _textLoose(b.forks);
  var forksHtml = forksStr ? '<span style="display:flex;align-items:center;gap:3px;font-size:0.78rem;color:var(--muted,#6b7280);">🍴 ' + _esc(forksStr) + '</span>' : '';

  var langColors = {
    'JavaScript': '#f1e05a', 'TypeScript': '#3178c6', 'Python': '#3572A5',
    'Go': '#00ADD8', 'Rust': '#dea584', 'Java': '#b07219',
    'CSS': '#563d7c', 'HTML': '#e34c26'
  };
  var langStr = _firstText(b.language);
  var langHtml = '';
  if (langStr) {
    var dotColor = Object.prototype.hasOwnProperty.call(langColors, langStr) ? langColors[langStr] : '#6b7280';
    langHtml = '<span style="display:flex;align-items:center;gap:4px;font-size:0.78rem;color:var(--muted,#6b7280);"><span style="width:10px;height:10px;border-radius:50%;background:' + dotColor + ';display:inline-block;"></span>' + _esc(langStr) + '</span>';
  }

  var statsRow = (starsHtml || forksHtml || langHtml) ? '<div style="display:flex;gap:14px;">' + starsHtml + forksHtml + langHtml + '</div>' : '';

  var licText = _firstText(b.license);
  var licHtml = licText ? '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-top:6px;">⚖️ ' + _esc(licText) + '</div>' : '';

  return '<div data-cb="node" data-key="' + _ckey(b.repo, 'github_repo_card') + '" style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px 20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
    + '<span style="font-size:1rem;">📦</span>'
    + linkHtml + visHtml + '</div>'
    + labelHtml + descHtml + topicsHtml + statsRow + licHtml
    + '</div>';
};

// ─── gauge_sla ────────────────────────────────────────────────────────────────
_RENDERERS['gauge_sla'] = function(b) {
  if (!b || typeof b !== 'object') return '';
  var rawVal = b.value;
  var rawMax = b.max_value;
  var val = (typeof rawVal === 'boolean') ? (rawVal ? 1 : 0) : (typeof rawVal === 'number' || typeof rawVal === 'string' ? Number(rawVal) : NaN);
  if (!isFinite(val)) val = 0;
  var maxVal = (typeof rawMax === 'boolean') ? (rawMax ? 1 : 0) : (typeof rawMax === 'number' || typeof rawMax === 'string' ? Number(rawMax) : NaN);
  if (!isFinite(maxVal)) maxVal = 100;
  var unit = _textLoose(b.unit);
  var label = _textLoose(b.label);
  var title = _textLoose(b.title);

  var pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
  pct = Math.min(100.0, Math.max(0.0, pct));

  var pathLen = 314.159;
  var dashOffset = pathLen - (pct / 100.0) * pathLen;

  var angle = 180 + (pct / 100.0) * 180;
  var rad = (angle * Math.PI) / 180.0;
  var nx = 150 + 85 * Math.cos(rad);
  var ny = 140 + 85 * Math.sin(rad);

  var uid = typeof _payloadUid === 'function' ? _payloadUid(b) : '524383943';
  var gradId = 'gauge_sla_' + uid + '_grad';
  var glowId = 'gauge_sla_' + uid + '_glow';

  // status: against the payload's threshold (the value, as the schema says) when it has one, else against 95% / 85% of the scale
  var thr = (typeof b.threshold === 'number' && isFinite(b.threshold) && b.threshold > 0) ? b.threshold : null;
  var healthy = thr !== null ? val >= thr : pct >= 95;
  var warn = thr !== null ? val >= thr * 0.9 : pct >= 85;
  // a status (and the needle colour) only when the payload gave a threshold; without one nothing is judged
  var statusColor = '#ef4444';
  var statusLabel = 'BREACHED';
  if (thr === null) {
    statusColor = '#94a3b8';
    statusLabel = '';
  } else if (healthy) {
    statusColor = '#10b981';
    statusLabel = 'HEALTHY';
  } else if (warn) {
    statusColor = '#38bdf8';
    statusLabel = 'WARNING';
  }

  var headerHtml = '';
  if (title) {
    headerHtml = '\n        <div style="margin-bottom:15px; display:flex; align-items:center; justify-content:space-between;">\n          <div style="font-size:1.15rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px; display:flex; align-items:center; gap:8px;">\n            <span style="color:#00f2ff; font-weight:900;">◵</span> ' + _esc(title) + '\n          </div>\n        </div>\n        ';
  }

  // the schema's value (e.g. 99.4) with its unit, not the filled percentage; two decimals at most, no trailing zeros, clamped so toFixed never goes exponential
  var shown = Math.max(-1e15, Math.min(1e15, val)).toFixed(2);
  if (shown.indexOf('.') >= 0) shown = shown.replace(/0+$/, '').replace(/\.$/, '');
  var valDisplay = shown + unit;
  var ariaText = (title || 'SLA gauge') + ': ' + valDisplay + (statusLabel ? ', ' + statusLabel.toLowerCase() : '') + (label ? ', ' + label : '');
  var fullStatus = [statusLabel, label.toUpperCase()].filter(function(x) { return x; }).join(' · ');

  var svgHtml = '\n    <div style="width:100%; height:200px; display:flex; justify-content:center; align-items:center;">\n      \n      <svg role="img" aria-label="' + _esc(ariaText) + '" viewBox="0 0 300 190" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">\n        <defs>\n          <linearGradient id="' + gradId + '" x1="0" y1="0" x2="1" y2="0">\n            <stop offset="0%" stop-color="#ef4444" />\n            <stop offset="60%" stop-color="#f59e0b" />\n            <stop offset="100%" stop-color="#10b981" />\n          </linearGradient>\n          <filter id="' + glowId + '" x="-20%" y="-20%" width="140%" height="140%">\n            <feGaussianBlur stdDeviation="3" result="blur" />\n            <feMerge>\n              <feMergeNode in="blur" />\n              <feMergeNode in="SourceGraphic" />\n            </feMerge>\n          </filter>\n        </defs>\n\n        <path d="M 50 140 A 100 100 0 0 1 250 140" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="14" stroke-linecap="round" />\n\n        <path d="M 50 140 A 100 100 0 0 1 250 140" fill="none" stroke="url(#' + gradId + ')" stroke-width="14" stroke-linecap="round"\n              stroke-dasharray="314.159" stroke-dashoffset="' + dashOffset + '" filter="url(#' + glowId + ')" />\n\n        <line x1="50" y1="140" x2="60" y2="140" stroke="rgba(255,255,255,0.2)" stroke-width="2" />\n        <line x1="150" y1="40" x2="150" y2="50" stroke="rgba(255,255,255,0.2)" stroke-width="2" />\n        <line x1="240" y1="140" x2="250" y2="140" stroke="rgba(255,255,255,0.2)" stroke-width="2" />\n\n        <line x1="150" y1="140" x2="' + nx.toFixed(1) + '" y2="' + ny.toFixed(1) + '" stroke="' + statusColor + '" stroke-width="3" stroke-linecap="round" filter="url(#' + glowId + ')" />\n        <circle cx="150" cy="140" r="8" fill="#0f172a" stroke="' + statusColor + '" stroke-width="3" />\n\n        <text x="150" y="168" text-anchor="middle" font-size="24" font-weight="900" fill="#f1f5f9" font-family="monospace">' + _esc(valDisplay) + '</text>\n        <text x="150" y="184" text-anchor="middle" font-size="9" font-weight="800" fill="' + statusColor + '" font-family="monospace" letter-spacing="0.1em">' + _esc(fullStatus) + '</text>\n      </svg>\n    \n    </div>\n    ';

  return '\n    <div data-cb="node" data-key="' + _ckey(b.title, 'gauge_sla') + '" style="margin:1.5rem 0;padding:24px;background:rgb(15,23,42);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">' +
    headerHtml +
    svgHtml +
    '\n    </div>\n    ';
};

// ─── sparkline ────────────────────────────────────────────────────────────────
_RENDERERS['sparkline'] = function(b) {
  var data   = b.data || [];
  if (!data.length) return '';
  var color  = b.color || 'var(--a2ui-accent,#4f46e5)';
  var lw     = b.line_width || 2;
  var w      = 120, h = 32;
  var min    = Math.min.apply(null, data), max = Math.max.apply(null, data);
  var range  = max - min || 1;
  var pts    = data.map(function(v, i) {
    var x = (i / (data.length - 1)) * w;
    var y = h - ((v - min) / range) * (h - 4) - 2;
    return x.toFixed(1) + ',' + y.toFixed(1);
  }).join(' ');
  var fill   = data.map(function(v, i) {
    var x = (i / (data.length - 1)) * w;
    var y = h - ((v - min) / range) * (h - 4) - 2;
    return x.toFixed(1) + ',' + y.toFixed(1);
  });
  var area   = '0,' + h + ' ' + fill.join(' ') + ' ' + w + ',' + h;
  return '<svg data-cb="node" data-key="' + _ckey(b.type, 'sparkline') + '" role="img" aria-label="Sparkline" width="' + w + '" height="' + h + '" style="display:inline-block;vertical-align:middle;">'
    + '<polygon points="' + area + '" fill="' + color + '" fill-opacity="0.1"/>'
    + '<polyline points="' + pts + '" fill="none" stroke="' + color + '" stroke-width="' + lw + '" stroke-linejoin="round" stroke-linecap="round"/>'
    + '</svg>';
};

// ─── scatter_trend ────────────────────────────────────────────────────────────
_RENDERERS['scatter_trend'] = function(b) {
  var data  = b.data_points || b.data || [];
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:8px;">' + _esc(b.title) + '</div>' : '';
  var lx    = _esc(b.label_x || '');
  var ly    = _esc(b.label_y || '');
  var w     = 280, h = 160, pad = 30;
  if (!data.length) return title + '<div style="color:var(--muted,#9ca3af);font-size:0.82rem;">No data</div>';
  var xs    = data.map(function(p){ return Array.isArray(p) ? p[0] : p.x; });
  var ys    = data.map(function(p){ return Array.isArray(p) ? p[1] : p.y; });
  var xmin  = Math.min.apply(null, xs), xmax = Math.max.apply(null, xs) || 1;
  var ymin  = Math.min.apply(null, ys), ymax = Math.max.apply(null, ys) || 1;
  var dots  = data.map(function(p, i) {
    var x = pad + ((( Array.isArray(p) ? p[0] : p.x) - xmin) / (xmax - xmin || 1)) * (w - pad * 2);
    var y = (h - pad) - (((Array.isArray(p) ? p[1] : p.y) - ymin) / (ymax - ymin || 1)) * (h - pad * 2);
    var color = p.color || b.color || '#4f46e5';
    return '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="4" fill="' + _esc(color) + '" fill-opacity="0.7"/>';
  }).join('');
  var svg = '<svg width="' + w + '" height="' + h + '" style="overflow:visible;">'
    + '<line x1="' + pad + '" y1="' + (h - pad) + '" x2="' + (w - pad) + '" y2="' + (h - pad) + '" stroke="#e5e7eb" stroke-width="1"/>'
    + '<line x1="' + pad + '" y1="' + pad + '" x2="' + pad + '" y2="' + (h - pad) + '" stroke="#e5e7eb" stroke-width="1"/>'
    + dots
    + (lx ? '<text x="' + (w / 2) + '" y="' + (h + 14) + '" text-anchor="middle" style="font-size:9px;fill:#9ca3af;">' + lx + '</text>' : '')
    + (ly ? '<text x="10" y="' + (h / 2) + '" text-anchor="middle" transform="rotate(-90,10,' + (h/2) + ')" style="font-size:9px;fill:#9ca3af;">' + ly + '</text>' : '')
    + '</svg>';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + svg + '</div>';
};

// ─── calibration_plot ─────────────────────────────────────────────────────────
_RENDERERS['calibration_plot'] = function(b) {
  var series = (b.series || []).filter(function(s) { return s && s.points && s.points.length; });
  var title  = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:8px;">' + _esc(b.title) + '</div>' : '';
  if (!series.length) return title + '<div style="color:var(--muted,#9ca3af);font-size:0.82rem;">No data</div>';
  var palette = ['#8b5cf6', '#dc2626', '#0891b2', '#16a34a', '#d97706', '#db2777'];
  var w = 300, h = 190, padL = 32, padR = 12, padT = 8, padB = 26;
  var chartW = w - padL - padR, chartH = h - padT - padB;
  var px = function(v) { return padL + Math.max(0, Math.min(1, v)) * chartW; };
  var py = function(v) { return padT + (1 - Math.max(0, Math.min(1, v))) * chartH; };

  var grid = '';
  for (var i = 0; i <= 4; i++) {
    var frac = i / 4, gx = padL + frac * chartW, gy = padT + frac * chartH;
    grid += '<line x1="' + padL + '" y1="' + gy.toFixed(1) + '" x2="' + (padL + chartW) + '" y2="' + gy.toFixed(1) + '" stroke="var(--border,#e5e7eb)" stroke-dasharray="2,3"/>'
      + '<text x="' + (padL - 6) + '" y="' + (gy + 3).toFixed(1) + '" text-anchor="end" style="font-size:7.5px;fill:var(--muted,#9ca3af);">' + (1 - frac).toFixed(2) + '</text>'
      + '<line x1="' + gx.toFixed(1) + '" y1="' + padT + '" x2="' + gx.toFixed(1) + '" y2="' + (padT + chartH) + '" stroke="var(--border,#e5e7eb)" stroke-dasharray="2,3"/>'
      + '<text x="' + gx.toFixed(1) + '" y="' + (padT + chartH + 13) + '" text-anchor="middle" style="font-size:7.5px;fill:var(--muted,#9ca3af);">' + frac.toFixed(2) + '</text>';
  }
  var diagonal = '<line x1="' + px(0).toFixed(1) + '" y1="' + py(0).toFixed(1) + '" x2="' + px(1).toFixed(1) + '" y2="' + py(1).toFixed(1)
    + '" stroke="var(--muted,#9ca3af)" stroke-width="1.5" stroke-dasharray="5,4"/>';

  var pointsHtml = '', legendHtml = '';
  series.forEach(function(s, si) {
    var color = s.color || palette[si % palette.length];
    (s.points || []).forEach(function(pt) {
      if (!pt || pt.predicted == null || pt.observed == null) return;
      var cx = px(pt.predicted), cy = py(pt.observed);
      var r = 4.5;
      if (pt.n) r = Math.max(3.5, Math.min(9, 3.5 + Math.sqrt(pt.n) * 0.4));
      if (pt.ci_low != null && pt.ci_high != null) {
        pointsHtml += '<line x1="' + cx.toFixed(1) + '" y1="' + py(pt.ci_low).toFixed(1) + '" x2="' + cx.toFixed(1) + '" y2="' + py(pt.ci_high).toFixed(1)
          + '" stroke="' + _esc(color) + '" stroke-width="1.5" opacity="0.55"/>';
      }
      pointsHtml += '<circle cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="' + r.toFixed(1) + '" fill="' + _esc(color)
        + '" fill-opacity="0.85" stroke="var(--bg,#fff)" stroke-width="1.2"/>';
    });
    legendHtml += '<span style="display:inline-flex;align-items:center;gap:5px;margin-right:12px;font-size:11px;color:var(--muted,#6b7280);">'
      + '<span style="width:8px;height:8px;border-radius:50%;background:' + _esc(color) + ';display:inline-block;"></span>' + _esc(s.label || 'Series ' + (si + 1)) + '</span>';
  });

  var xLabel = _esc(b.x_label || 'Predicted probability'), yLabel = _esc(b.y_label || 'Observed accuracy');
  var svg = '<svg width="' + w + '" height="' + h + '" style="overflow:visible;">'
    + grid + diagonal + pointsHtml
    + '<text x="' + (padL + chartW / 2) + '" y="' + (h - 2) + '" text-anchor="middle" style="font-size:9px;fill:var(--muted,#9ca3af);">' + xLabel + '</text>'
    + '<text x="9" y="' + (padT + chartH / 2) + '" text-anchor="middle" transform="rotate(-90,9,' + (padT + chartH / 2) + ')" style="font-size:9px;fill:var(--muted,#9ca3af);">' + yLabel + '</text>'
    + '</svg>';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + svg + '<div style="margin-top:8px;">' + legendHtml + '</div></div>';
};

// ─── stacked_area `offset` and `layout` (2026-10-21): the default layout is a real SVG area chart (D22); `layout: "bars"` keeps the CSS bar list below; `offset` (I49) "expand" | "silhouette" | "wiggle" reshapes the chart ───
// d3-shape 3.2.0 stackOffsetExpand, stackOffsetSilhouette, stackOffsetWiggle, stackOffsetNone and stackOrderInsideOut / stackOrderAppearance, ported by hand
// (ISC, Mike Bostock); twin of _sa_* in renderers/web_article.py. Self-contained on purpose: this file is also used where the infographic helpers do not exist.
var _SA_COLORS = ['#0369A1', '#B45309', '#15803D', '#7C3AED', '#BE123C', '#0F766E', '#A16207', '#475569'];
var _SA_SR = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;';
function _saNote(s) { return '<div style="font-size:0.75rem;color:var(--muted,#475569);margin-top:4px;">' + s + '</div>'; }
function _saVersionNote(b) {
  var v = b.version;
  return (typeof v === 'number' && isFinite(v) && v === Math.floor(v) && v > 1) ? _saNote('Written for stacked_area version ' + String(v) + '; drawn as version 1.') : '';
}
function _saStack(vals, offset) {
  var n = vals.length, m = vals[0].length, S = [], i, j, k, y, s0, s1, order = [];
  for (i = 0; i < n; i++) { S.push([]); for (j = 0; j < m; j++) S[i].push([0, vals[i][j]]); }
  for (i = 0; i < n; i++) order.push(i);
  if (offset === 'wiggle') {   // stackOrderInsideOut: the series are ordered by where they peak, then dealt to the top or bottom to keep both sides level
    var peaks = [], sums = [], top = 0, bottom = 0, tops = [], bottoms = [];
    for (i = 0; i < n; i++) {
      var pj = 0, vj = -Infinity, s = 0;
      for (j = 0; j < m; j++) { if (S[i][j][1] > vj) { vj = S[i][j][1]; pj = j; } if (S[i][j][1]) s += S[i][j][1]; }
      peaks.push(pj); sums.push(s);
    }
    order.sort(function(a, c) { return (peaks[a] - peaks[c]) || (a - c); });
    var ordered = order.slice();
    for (i = 0; i < n; i++) {
      k = ordered[i];
      if (top < bottom) { top += sums[k]; tops.push(k); } else { bottom += sums[k]; bottoms.push(k); }
    }
    order = bottoms.reverse().concat(tops);
  }
  if (offset === 'expand') {
    for (j = 0; j < m; j++) {
      y = 0;
      for (i = 0; i < n; i++) y += S[i][j][1] || 0;
      if (y) for (i = 0; i < n; i++) S[i][j][1] /= y;
    }
  } else if (offset === 'silhouette') {
    s0 = S[order[0]];
    for (j = 0; j < m; j++) {
      y = 0;
      for (i = 0; i < n; i++) y += S[i][j][1] || 0;
      s0[j][1] += s0[j][0] = -y / 2;
    }
  } else if (offset === 'wiggle') {
    s0 = S[order[0]]; y = 0;
    for (j = 1; j < m; j++) {
      var q1 = 0, q2 = 0;
      for (i = 0; i < n; i++) {
        var si = S[order[i]], sij0 = si[j][1] || 0, sij1 = si[j - 1][1] || 0, s3 = (sij0 - sij1) / 2;
        for (k = 0; k < i; k++) {
          var sk = S[order[k]], skj0 = sk[j][1] || 0, skj1 = sk[j - 1][1] || 0;
          s3 += skj0 - skj1;
        }
        q1 += sij0; q2 += s3 * sij0;
      }
      s0[j - 1][1] += s0[j - 1][0] = y;
      if (q1) y -= q2 / q1;
    }
    s0[j - 1][1] += s0[j - 1][0] = y;
  }
  if (n > 1) {   // stackOffsetNone, which every offset ends with: each series sits on the one before it in `order`
    s1 = S[order[0]];
    for (i = 1; i < n; i++) {
      s0 = s1; s1 = S[order[i]];
      for (j = 0; j < m; j++) s1[j][1] += s1[j][0] = isNaN(s0[j][1]) ? s0[j][0] : s0[j][1];
    }
  }
  return { order: order, lo: S.map(function(r) { return r.map(function(p) { return p[0]; }); }), hi: S.map(function(r) { return r.map(function(p) { return p[1]; }); }) };
}
function _saStr(v) { return typeof v === 'string' ? v : (typeof v === 'number' && isFinite(v)) ? String(v) : ''; }
function _saFx(x) { return x.toFixed(2); }
// every stride-th label, and always the last one: it takes the place of the regular label just before it, which would crowd it
function _saTicks(m, stride) {
  var t = [], i, o = {};
  for (i = 0; i < m; i += stride) t.push(i);
  if (t[t.length - 1] !== m - 1) { if (t[t.length - 1] !== 0) t.pop(); t.push(m - 1); }
  t.forEach(function(k) { o[k] = true; });
  return o;
}
// the zero-based value axis of the default layout: a 1-2-5 step, at most five intervals, k / M / B / T suffix; null when the maximum is not worth an axis
function _saAxis(mx) {
  if (!(mx > 1e-9)) return null;
  var raw = mx / 4, mag = 1, e = 0, d, step, n, unit = 1, suffix = '', ul = 0, k, top, ticks = [], U = [[1e12, 'T', 12], [1e9, 'B', 9], [1e6, 'M', 6], [1e3, 'k', 3]];
  while (mag * 10 <= raw) { mag *= 10; e++; }
  while (mag > raw) { mag /= 10; e--; }
  var r = raw / mag;
  d = r <= 1 ? 1 : r <= 2 ? 2 : r <= 5 ? 5 : 10;
  step = d * mag;
  if (d === 10) e++;
  n = Math.ceil(mx / step); top = n * step;
  for (k = 0; k < U.length; k++) if (top >= U[k][0]) { unit = U[k][0]; suffix = U[k][1]; ul = U[k][2]; break; }
  var dec = Math.max(0, ul - e);
  if (dec > 6) return null;
  for (k = 0; k <= n; k++) ticks.push([k * step, k === 0 ? '0' : (k * step / unit).toFixed(dec) + suffix]);
  return { top: top, ticks: ticks };
}
function _saChart(b, offset) {
  var labels = Array.isArray(b.labels) ? b.labels : [], list = Array.isArray(b.series) ? b.series : [];
  var m = Math.min(labels.length, 60), ser = [], skipped = 0, bad = 0, i, j;
  list.slice(0, 12).forEach(function(s, k) {
    if (!s || typeof s !== 'object' || Array.isArray(s)) { skipped++; return; }
    var d = Array.isArray(s.data) ? s.data : [], raw = [], vals = [];
    for (j = 0; j < m; j++) {
      var v = d[j];
      raw.push(typeof v === 'number' && isFinite(v) ? String(v) : '');
      if (typeof v === 'number' && isFinite(v) && Math.abs(v) <= 1e12 && v >= 0) vals.push(v);
      else { vals.push(0); if (j < d.length) bad++; }
    }
    ser.push({ name: _saStr(s.label) ? _saStr(s.label).slice(0, 40) : 'Series ' + (k + 1), raw: raw, vals: vals,
               col: (typeof s.color === 'string' && /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(s.color)) ? s.color : _SA_COLORS[k % _SA_COLORS.length] });
  });
  if (m < 2 || !ser.length) return null;
  var beyondS = list.length - 12, beyondP = labels.length - 60, ST = _saStack(ser.map(function(s) { return s.vals; }), offset);
  var ymin = 0, ymax = 0, axis = null, allzero = false;
  if (offset === 'expand') { ymax = 1; }
  else {
    ymin = Infinity; ymax = -Infinity;
    ST.lo.forEach(function(r) { r.forEach(function(v) { if (v < ymin) ymin = v; }); });
    ST.hi.forEach(function(r) { r.forEach(function(v) { if (v > ymax) ymax = v; }); });
    if (offset === 'none') {
      axis = _saAxis(ymax);
      if (axis) { ymin = 0; ymax = axis.top; }
      else if (!(ymax > 0)) { ymax = 1; allzero = true; }
    }
  }
  var span = ymax - ymin; if (!(span > 0)) span = 1;
  function X(jj) { return _saFx(jj / (m - 1) * 1000); }
  function Y(v) { var t = (ymax - v) / span * 100; return _saFx(t < 0 ? 0 : t > 100 ? 100 : t); }
  var polys = '';
  for (i = 0; i < ser.length; i++) {
    var pts = [];
    for (j = 0; j < m; j++) pts.push(X(j) + ',' + Y(ST.hi[i][j]));
    for (j = m - 1; j >= 0; j--) pts.push(X(j) + ',' + Y(ST.lo[i][j]));
    polys += '<polygon data-cb="bar" data-key="' + _esc(ser[i].name) + '" points="' + pts.join(' ') + '" fill="' + ser[i].col + '" fill-opacity="0.92" stroke="var(--bg,#fff)" stroke-width="1" vector-effect="non-scaling-stroke" stroke-linejoin="round" style="' + _ifK(i, ser.length) + 'opacity:var(--k,1);"/>';
  }
  var full = labels.slice(0, m).map(function(l) { return _saStr(l); }), lab = full.map(function(t) { return t.length > 14 ? t.slice(0, 13).replace(/\s+$/, '') + '\u2026' : t; });
  var maxlen = Math.max.apply(null, lab.map(function(s) { return s.length; }).concat([1]));
  var want = Math.max(2, Math.min(8, Math.floor(48 / maxlen))), stride = Math.ceil(m / want), xs = ''; var shown = _saTicks(m, stride), coarse = _saTicks(m, 2 * stride);
  for (j = 0; j < m; j++) {
    if (!shown[j]) continue;
    var tr = j === 0 ? '' : (j === m - 1 ? 'transform:translateX(-100%);' : 'transform:translateX(-50%);');
    xs += '<div class="sax' + (coarse[j] ? ' sac' : '') + '" style="position:absolute;top:100%;left:' + _saFx(j / (m - 1) * 100) + '%;">'
      + '<div style="position:absolute;left:0;top:0;width:1px;height:4px;background:var(--muted,#475569);"></div>'
      + '<div style="position:absolute;left:0;top:7px;' + tr + 'font-size:0.75rem;line-height:1;white-space:nowrap;color:var(--muted,#475569);">' + _esc(lab[j]) + '</div></div>';
  }
  var ys = '';
  if (offset === 'expand') {
    for (j = 0; j <= 4; j++) {
      ys += '<div class="say" style="position:absolute;right:100%;top:' + (100 - j * 25) + '%;width:38px;padding-right:6px;box-sizing:border-box;text-align:right;transform:translateY(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--muted,#475569);">' + (j * 25) + '%</div>'
        + '<div style="position:absolute;right:100%;top:' + (100 - j * 25) + '%;width:4px;border-top:1px solid var(--muted,#475569);"></div>';
    }
  }
  var yw = offset === 'expand' ? '44px' : '0';
  if (offset === 'none') {
    var tk = axis ? axis.ticks : [[0, '0']], wd = Math.ceil(Math.max.apply(null, tk.map(function(t) { return t[1].length; })) * 7.5) + 10;
    yw = wd + 'px';
    tk.forEach(function(t) {
      var tp = Y(t[0]);
      ys += '<div class="say" style="position:absolute;right:100%;top:' + tp + '%;width:' + (wd - 6) + 'px;padding-right:6px;box-sizing:border-box;text-align:right;transform:translateY(-50%);font-size:0.75rem;line-height:1;white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--muted,#475569);">' + t[1] + '</div>'
        + '<div style="position:absolute;right:100%;top:' + tp + '%;width:4px;border-top:1px solid var(--muted,#475569);"></div>';
    });
  }
  var mode = offset === 'none' ? 'zero baseline' : offset === 'expand' ? 'each point scaled to 100 percent' : offset === 'silhouette' ? 'centred baseline' : 'streamgraph, baseline chosen to minimise wiggle';
  var names = ser.map(function(s) { return s.name; });
  var aria = 'Stacked area chart, ' + mode + ': ' + ser.length + ' series over ' + m + ' points from ' + full[0] + ' to ' + full[m - 1] + '. Series: ' + names.join(', ') + '.';
  var legend = '<div style="display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:12px;font-size:0.75rem;line-height:1.2;color:var(--text,#0F172A);">'
    + ser.map(function(s) { return '<span style="display:inline-flex;align-items:center;gap:5px;"><span style="width:12px;height:12px;border-radius:2px;background:' + s.col + ';border:1px solid var(--border,#CBD5E1);box-sizing:border-box;display:inline-block;"></span>' + _esc(s.name) + '</span>'; }).join('') + '</div>';
  var notes = '';
  if (offset === 'none') notes += _saNote(allzero ? 'Every value is 0, so there is nothing to draw above the baseline.' : 'The top edge is the total of all layers; each layer’s thickness is its own value, and the exact values are in the table.');
  else if (offset === 'expand') notes += _saNote('Each point is scaled so its layers add up to 100%; the axis shows each series’ share of the total.');
  else notes += _saNote((offset === 'wiggle' ? 'Streamgraph: the baseline moves to keep the layers’ wiggle small and the layers are ordered inside-out, not as listed. ' : 'The layers are centred on a middle line. ')
    + 'There is no value axis because the baseline has no meaning; layer thickness shows the size, and the exact values are in the table.');
  if (bad) notes += _saNote(bad + (bad === 1 ? ' value was' : ' values were') + ' negative or not a usable number and ' + (bad === 1 ? 'is' : 'are') + ' drawn as 0.');
  if (skipped) notes += _saNote(skipped + (skipped === 1 ? ' series was' : ' series were') + ' not an object and ' + (skipped === 1 ? 'was' : 'were') + ' left out.');
  if (beyondS > 0) notes += _saNote(beyondS + (beyondS === 1 ? ' series beyond the first 12 was' : ' series beyond the first 12 were') + ' not drawn.');
  if (beyondP > 0) notes += _saNote(beyondP + (beyondP === 1 ? ' label beyond the first 60 was' : ' labels beyond the first 60 were') + ' not drawn.');
  var table = '<table style="' + _SA_SR + '"><thead><tr><th scope="col">Point</th>' + names.map(function(n) { return '<th scope="col">' + _esc(n.slice(0, 40)) + '</th>'; }).join('') + '</tr></thead><tbody>'
    + lab.map(function(l, jj) { return '<tr><th scope="row">' + _esc(_saStr(labels[jj]).slice(0, 60)) + '</th>' + ser.map(function(s) { return '<td>' + _esc(s.raw[jj]) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table>';
  var title = _saStr(b.title) ? '<div style="font-weight:700;font-size:1.05rem;margin:0 0 10px;">' + _esc(_saStr(b.title).slice(0, 80)) + '</div>' : '';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;color:var(--text,#0F172A);font-size:0.9rem;line-height:1.4;">' + title
    + '<div class="ifsa" style="container-type:inline-size;max-width:100%;overflow:hidden;"><style>@container (max-width:560px){.ifsa .sax:not(.sac){display:none}}</style>'
    + '<div role="img" aria-label="' + _esc(aria) + '" style="position:relative;margin:8px 0 34px 0;">'
    + '<div style="position:relative;margin-left:' + yw + ';height:240px;border-bottom:1px solid var(--muted,#475569);' + (offset === 'expand' || offset === 'none' ? 'border-left:1px solid var(--muted,#475569);' : '') + '">'
    + '<svg aria-hidden="true" focusable="false" viewBox="0 0 1000 100" preserveAspectRatio="none" style="position:absolute;left:0;top:0;width:100%;height:100%;display:block;">' + polys + '</svg>' + ys + xs + '</div></div>'
    + legend + '</div>' + notes + _saVersionNote(b) + table + '</div>';
}
function _saCard(b, msg) {   // what the area chart says when there is nothing to draw
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;color:var(--text,#0F172A);font-size:0.9rem;line-height:1.4;">' + (_saStr(b.title) ? '<div style="font-weight:700;font-size:1.05rem;margin:0 0 10px;">' + _esc(_saStr(b.title).slice(0, 80)) + '</div>' : '')
    + '<div style="border:1px solid #64748B;border-radius:8px;background:var(--surface,#F8FAFC);padding:8px 10px;">' + msg + '</div>' + _saVersionNote(b) + '</div>';
}
function _saGate(b) {   // D22: the default layout is the area chart; html is the chart (or its message), '' for layout "bars"; tail goes after the bar list
  var off = (b.offset === 'expand' || b.offset === 'silhouette' || b.offset === 'wiggle') ? b.offset : null;
  if (b.layout === 'bars') return { html: '', tail: (off ? _saNote('The bar list has no offset; \u201c' + off + '\u201d only applies to the area layout.') : '') + _saVersionNote(b) };
  var h = (Array.isArray(b.labels) && Array.isArray(b.series)) ? _saChart(b, off || 'none') : null;
  return { html: h === null ? _saCard(b, off ? 'A stacked area chart with an offset needs at least two labels and one series with numbers.' : 'A stacked area chart needs at least two labels and one series with numbers. Set layout to bars for a bar list.') : h, tail: '' };
}

// ─── stacked_area ─────────────────────────────────────────────────────────────
// The default layout is the area chart above (_saGate); `layout: "bars"` renders stacked horizontal bars (CSS approximation — no canvas/JS charting needed).
_RENDERERS['stacked_area'] = function(b) {
  var _sa = _saGate(b);   // reads b.layout, b.offset and b.version (and b.labels, b.series, b.title, b.data, b.color) for the area chart
  if (_sa.html) return _cbPass(_sa.html);
  try { return _saBars(b) + _sa.tail; } catch (e) { return _saCard(b, 'The bar list could not be drawn from this data.') + _sa.tail; }
};
function _saBars(b) {
  var title   = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';
  var labels  = b.labels || [];
  var series  = b.series || [];
  var colors  = ['#4f46e5','#10b981','#f59e0b','#ef4444','#8b5cf6','#0ea5e9'];
  // Calculate max per column
  var totals  = labels.map(function(_, i) {
    return series.reduce(function(s, ser){ return s + (ser.data[i] || 0); }, 0);
  });
  var maxTot  = Math.max.apply(null, totals) || 1;
  var rows    = labels.map(function(lbl, i) {
    var segments = series.map(function(ser, si) {
      var v   = ser.data[i] || 0;
      var pct = (v / maxTot * 100).toFixed(1);
      var col = ser.color || colors[si % colors.length];
      return pct > 0 ? '<div style="width:' + pct + '%;height:100%;background:' + col + ';display:inline-block;" title="' + _esc(ser.label || '') + ': ' + v + '"></div>' : '';
    }).join('');
    return '<div style="margin-bottom:8px;">'
      + '<div style="font-size:0.75rem;color:var(--muted,#6b7280);margin-bottom:2px;">' + _esc(String(lbl)) + '</div>'
      + '<div style="height:20px;border-radius:4px;overflow:hidden;background:#f3f4f6;display:flex;">' + segments + '</div>'
      + '</div>';
  }).join('');
  var legend  = series.map(function(ser, si) {
    var col = ser.color || colors[si % colors.length];
    return '<span style="display:inline-flex;align-items:center;gap:4px;font-size:0.75rem;color:var(--text,#374151);margin-right:12px;">'
      + '<span style="width:10px;height:10px;border-radius:2px;background:' + col + ';display:inline-block;"></span>' + _esc(ser.label||'') + '</span>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + rows + '<div style="margin-top:10px;">' + legend + '</div></div>';
}

// ─── heatmap_calendar ─────────────────────────────────────────────────────────
_RENDERERS['heatmap_calendar'] = function(b) {
  var title  = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:10px;">' + _esc(b.title) + '</div>' : '';
  var data   = b.data || [];
  var colors = b.color_scale || ['#f3f4f6','#bfdbfe','#93c5fd','#60a5fa','#2563eb'];
  // Build a lookup: date → count
  var lookup = {};
  var maxVal = 0;
  data.forEach(function(d){ lookup[d.date] = d.count || d.value || 0; if (lookup[d.date] > maxVal) maxVal = lookup[d.date]; });
  maxVal = maxVal || 1;
  // Render weeks: find the date range
  var months = b.months || 3;
  // Generate the last N*28 days
  var days   = months * 28;
  var cells  = '';
  var today  = new Date();
  // align to Monday
  var start  = new Date(today);
  start.setDate(today.getDate() - days);
  var d = new Date(start);
  for (var i = 0; i <= days; i++) {
    var iso   = d.toISOString().split('T')[0];
    var count = lookup[iso] || 0;
    var ci    = Math.min(colors.length - 1, Math.floor((count / maxVal) * (colors.length - 1)));
    var bg    = colors[ci];
    cells += '<div data-cb="item" data-key="' + _esc(iso) + '" title="' + iso + ': ' + count + '" style="width:10px;height:10px;border-radius:2px;background:' + bg + ';flex-shrink:0;"></div>';
    d.setDate(d.getDate() + 1);
  }
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);overflow-x:auto;">'
    + title
    + '<div style="display:flex;flex-wrap:wrap;gap:2px;max-width:' + (Math.ceil((days+1)/7)*12) + 'px;">' + cells + '</div>'
    + '<div style="display:flex;align-items:center;gap:4px;margin-top:8px;">'
    + '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);">Less</span>'
    + colors.map(function(c){ return '<div style="width:10px;height:10px;border-radius:2px;background:' + c + ';"></div>'; }).join('')
    + '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);">More</span></div></div>';
};

// ─── image_hotspots ───────────────────────────────────────────────────────────
_RENDERERS['image_hotspots'] = function(b) {
  var uid      = 'ihs' + Math.random().toString(36).substr(2, 5);
  var imageUrl = b.image_url || '';
  var alt      = _esc(b.alt_text || '');
  var hotspots = (b.hotspots || []).map(function(h, i) {
    var x   = _esc(String(h.x_position || h.x || 50));
    var y   = _esc(String(h.y_position || h.y || 50));
    var lbl = _esc(h.label || String(i + 1));
    var k   = _esc(String(h.id || h.label || h.content || h.description || ''));
    var cnt = h.content ? '<div class="' + uid + '-tip" style="display:none;position:absolute;left:calc(' + x + '% + 18px);top:calc(' + y + '% - 10px);background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:0.78rem;color:#374151;min-width:120px;max-width:200px;z-index:10;box-shadow:0 4px 12px rgba(0,0,0,0.1);">' + _esc(h.content) + '</div>' : '';
    return '<div data-cb="node" data-key="' + k + '" style="position:absolute;left:' + x + '%;top:' + y + '%;transform:translate(-50%,-50%);" onmouseenter="var t=this.querySelector(\'.' + uid + '-tip\');if(t)t.style.display=\'block\';" onmouseleave="var t=this.querySelector(\'.' + uid + '-tip\');if(t)t.style.display=\'none\';">'
      + '<div data-cb="label" data-key="' + k + '" style="width:24px;height:24px;border-radius:50%;background:var(--a2ui-accent,#4f46e5);color:#fff;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;cursor:pointer;box-shadow:0 0 0 4px rgba(99,102,241,0.2);animation:pulse 2s infinite;">' + lbl + '</div>'
      + cnt + '</div>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;position:relative;display:inline-block;width:100%;">'
    + '<style>@keyframes pulse{0%,100%{box-shadow:0 0 0 4px rgba(99,102,241,0.2);}50%{box-shadow:0 0 0 8px rgba(99,102,241,0.1);}}</style>'
    + '<img src="' + _esc(imageUrl) + '" alt="' + alt + '" style="width:100%;border-radius:10px;display:block;">'
    + '<div style="position:absolute;inset:0;">' + hotspots + '</div></div>';
};

// ─── inventory_table ──────────────────────────────────────────────────────────
_RENDERERS['inventory_table'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:10px;">' + _esc(b.title) + '</div>' : '';
  var rows  = (b.items || []).map(function(item) {
    var avail = parseInt(item.available || 0, 10);
    var thresh = parseInt(item.threshold || 0, 10);
    var low   = thresh && avail < thresh;
    var stockColor = avail === 0 ? '#ef4444' : low ? '#f59e0b' : '#10b981';
    var stockBg    = avail === 0 ? '#fee2e2' : low ? '#fef3c7' : '#d1fae5';
    var k = _esc(String(item.sku || item.product || item.name || item.id || ''));
    return '<tr data-cb="item" data-key="' + k + '" style="border-bottom:1px solid var(--border,#f3f4f6);">'
      + '<td data-cb="label" data-key="' + k + '" style="padding:8px 10px;font-size:0.82rem;color:var(--text,#374151);">' + _esc(item.product || item.sku || '') + '</td>'
      + (item.sku && item.product ? '<td style="padding:8px 10px;font-size:0.72rem;color:var(--muted,#9ca3af);">' + _esc(item.sku) + '</td>' : '')
      + '<td style="padding:8px 10px;text-align:right;"><span style="padding:2px 8px;border-radius:12px;font-size:0.78rem;font-weight:600;background:' + stockBg + ';color:' + stockColor + ';">' + avail + '</span></td>'
      + (item.committed !== undefined ? '<td style="padding:8px 10px;text-align:right;font-size:0.78rem;color:var(--muted,#6b7280);">' + _esc(String(item.committed)) + '</td>' : '')
      + (item.location ? '<td style="padding:8px 10px;font-size:0.78rem;color:var(--muted,#6b7280);">' + _esc(item.location) + '</td>' : '')
      + '</tr>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + title
    + '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;border:1px solid var(--border,#e5e7eb);border-radius:10px;overflow:hidden;">'
    + '<thead><tr style="background:var(--surface,#f9fafb);">'
    + '<th style="padding:8px 10px;text-align:left;font-size:0.75rem;font-weight:600;color:var(--muted,#6b7280);">Product</th>'
    + '<th style="padding:8px 10px;text-align:right;font-size:0.75rem;font-weight:600;color:var(--muted,#6b7280);">Available</th>'
    + '<th style="padding:8px 10px;text-align:right;font-size:0.75rem;font-weight:600;color:var(--muted,#6b7280);">Committed</th>'
    + '</tr></thead>'
    + '<tbody>' + rows + '</tbody></table></div></div>';
};

// ─── data_grid ────────────────────────────────────────────────────────────────
_RENDERERS['data_grid'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:.9rem;padding:10px 12px;background:#1e293b;color:#f8fafc;border-radius:8px 8px 0 0;">' + _esc(b.title) + '</div>' : '';
  var cols = b.columns || [];
  var rows_data = b.rows || [];
  var ths = cols.map(function(c) {
    var h = c.header !== undefined ? c.header : (c.key !== undefined ? c.key : '');
    return '<th style="padding:8px 12px;text-align:left;font-size:.75rem;font-weight:600;color:#666d7a;">' + _esc(h) + '</th>';
  }).join('');
  var trs = '';
  for (var ri = 0; ri < rows_data.length; ri++) {
    var row = rows_data[ri];
    var tds = '';
    for (var ci = 0; ci < cols.length; ci++) {
      var c = cols[ci];
      var key = c.key !== undefined ? c.key : '';
      var val = row[key] !== undefined && row[key] !== null ? String(row[key]) : '';
      var cell = '';
      if (c.type === 'status') {
        var smap = {
          'active': ['✓', '#10b981', '#d1fae5'],
          'inactive': ['✗', '#ef4444', '#fee2e2'],
          'pending': ['○', '#f59e0b', '#fef3c7']
        };
        var cfg = smap[val.toLowerCase()] || ['?', '#666d7a', '#f3f4f6'];
        cell = '<span style="padding:2px 8px;border-radius:12px;font-size:.75rem;font-weight:600;background:' + cfg[2] + ';color:' + cfg[1] + ';">' + cfg[0] + ' ' + _esc(val) + '</span>';
      } else if (c.type === 'tag') {
        cell = '<span style="padding:2px 8px;border-radius:12px;font-size:.75rem;background:#dbeafe;color:#1d4ed8;">' + _esc(val) + '</span>';
      } else {
        cell = _esc(val);
      }
      tds += '<td style="padding:8px 12px;font-size:.82rem;color:#374151;border-bottom:1px solid #f3f4f6;">' + cell + '</td>';
    }
    var bg = (ri % 2 !== 0) ? '#f9fafb' : '#fff';
    var raw_key = row.id || row.name || row.label || row.title || (cols.length > 0 && cols[0].key !== undefined ? row[cols[0].key] : '');
    var row_key = _esc(String(raw_key !== undefined && raw_key !== null ? raw_key : ''));
    trs += '<tr data-cb="item" data-key="' + row_key + '" style="background:' + bg + ';">' + tds + '</tr>';
  }
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">' + title + '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#f9fafb;">' + ths + '</tr></thead><tbody>' + trs + '</tbody></table></div></div>';
};

// ─── conversion_funnel ────────────────────────────────────────────────────────
_RENDERERS['conversion_funnel'] = function(b) {
  var title  = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:14px;">' + _esc(b.title) + '</div>' : '';
  var steps  = b.steps || [];
  var accent = b.accent || 'var(--a2ui-accent,#4f46e5)';
  var maxVal = Math.max.apply(null, steps.map(function(s){ return parseFloat(s.value||0); })) || 1;
  var html   = steps.map(function(s, i) {
    var val = parseFloat(s.value || 0);
    var pct = (val / maxVal * 100).toFixed(0);
    var conv = i > 0 ? ((val / parseFloat(steps[i-1].value||1)) * 100).toFixed(0) + '% of prev' : '';
    var sKey = _esc(String(s.stage || s.label || ''));
    return '<div data-cb="bar" data-key="' + sKey + '" style="text-align:center;margin-bottom:4px;">'
      + '<div style="display:inline-block;width:' + pct + '%;background:' + accent + ';opacity:' + (1 - i * 0.12) + ';color:#fff;padding:8px 12px;border-radius:4px;font-size:0.85rem;font-weight:600;min-width:140px;">'
      + _esc(s.stage || s.label || '') + ' — ' + _esc(s.value !== undefined ? String(s.value) : '') + '</div>'
      + (conv ? '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-top:2px;">' + conv + '</div>' : '')
      + '</div>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + html + '</div>';
};

// ─── live_aggregator ──────────────────────────────────────────────────────────
// Static render of bar proportions. For live polling, script tag would need external endpoint.
_RENDERERS['live_aggregator'] = function(b) {
  var title   = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';
  var items   = b.items || [];
  var maxVal  = b.max_value || Math.max.apply(null, items.map(function(i){ return parseFloat(i.value||0); })) || 1;
  var showVal = b.show_values !== false;
  var accent  = b.accent || 'var(--a2ui-accent,#4f46e5)';
  var bars    = items.map(function(item) {
    var val = parseFloat(item.value || 0);
    var pct = (val / maxVal * 100).toFixed(1);
    var col = item.color || accent;
    return '<div style="margin-bottom:10px;">'
      + '<div style="display:flex;justify-content:space-between;font-size:0.82rem;color:var(--text,#374151);margin-bottom:3px;">'
      + '<span>' + _esc(item.label || '') + '</span>'
      + (showVal ? '<span style="font-weight:700;color:' + col + ';">' + val + '</span>' : '')
      + '</div>'
      + '<div style="background:var(--surface,#f3f4f6);border-radius:4px;height:10px;"><div style="width:' + pct + '%;height:100%;background:' + col + ';border-radius:4px;"></div></div>'
      + '</div>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + bars
    + '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-top:8px;font-style:italic;">📊 Static snapshot — live polling requires a server endpoint.</div>'
    + '</div>';
};

// ─── tree_view ────────────────────────────────────────────────────────────────
_RENDERERS['tree_view'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:10px;">' + _esc(b.title) + '</div>' : '';
  function renderNode(node, depth) {
    var indent  = depth * 16;
    var hasKids = node.children && node.children.length;
    var icon    = node.icon || (hasKids ? '📁' : '📄');
    var meta    = node.meta ? '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-left:6px;">' + _esc(node.meta) + '</span>' : '';
    var label   = '<div style="display:flex;align-items:center;gap:6px;padding:4px 8px;border-radius:4px;font-size:0.85rem;color:var(--text,#374151);padding-left:' + indent + 'px;">'
      + '<span>' + _esc(icon) + '</span><span>' + _esc(node.label || '') + '</span>' + meta + '</div>';
    if (!hasKids) return label;
    var kids = node.children.map(function(c){ return renderNode(c, depth + 1); }).join('');
    return '<details' + (node.expanded !== false ? ' open' : '') + '><summary style="display:flex;align-items:center;gap:6px;padding:4px 8px;border-radius:4px;font-size:0.85rem;color:var(--text,#374151);cursor:pointer;list-style:none;padding-left:' + indent + 'px;">'
      + '▶ <span>' + _esc(icon) + '</span><span>' + _esc(node.label || '') + '</span>' + meta + '</summary>'
      + kids + '</details>';
  }
  var nodes = (Array.isArray(b.nodes) ? b.nodes : []).filter(function(n){ return n && typeof n === 'object'; }).map(function(n){ return renderNode(n, 0); }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:12px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);font-family:var(--font,inherit);">'
    + title + nodes + '</div>';
};

// ─── conversion_funnel `shape: "area"` (Plotly funnelarea) and gauge_sla scale mode (Plotly indicator gauge), wave B ───
// Additive: without `shape: "area"` / without `min` or `steps` the renderers above run untouched. Twin of _cf_area / _cf_gauge in
// renderers/web_article.py. Labels live in HTML (not SVG text) so they are never scaled below 12px.
var _CF_COLOR = /^(#[0-9a-fA-F]{3,8}|var\(--[a-z-]+(,#[0-9a-fA-F]{3,8})?\))$/;
var _CF_MAX = 1e15;   // a larger number is refused (twin of _CF_MAX in web_article.py)
var _CF_NUMSTR = /^[ \t]*[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?[ \t]*$/;
function _cfIsnum(v) { return typeof v === 'number' && isFinite(v) && Math.abs(v) <= _CF_MAX; }
function _cfN(v) {   // the usable number in v, or null: a number in range, or a plain decimal string
  if (typeof v === 'string') { if (v.length > 40 || !_CF_NUMSTR.test(v)) return null; v = Number(v); }
  return _cfIsnum(v) ? v : null;
}
function _cfGiven(v) { return !(v === undefined || v === null); }
function _cfUkey(k, used) { var base = k, n = 1; while (used[k] === true) { n++; k = base + ' (' + n + ')'; } used[k] = true; return _esc(k); }
function _cfName(v) { return (v === undefined || v === null) ? '' : String(v).slice(0, 40); }
function _cfPt(cx, cy, r, frac) { var a = Math.PI * (1 + frac); return _ifFmt(cx + r * Math.cos(a)) + ' ' + _ifFmt(cy + r * Math.sin(a)); }

function _cfArea(b) {
  var raw = _ifObj(b).steps, src = Array.isArray(raw) ? raw.slice(0, 500) : [], rows = [], skipped = 0, i, k;
  for (i = 0; i < src.length; i++) {
    var s = src[i], v = _cfN((s && typeof s === 'object') ? s.value : undefined);
    if (v === null || v < 0) { skipped++; continue; }
    var nm = (s && typeof s === 'object') ? (s.stage ? s.stage : s.label) : undefined;
    rows.push([_cfName(nm) || ('Step ' + (rows.length + 1)), v]);
  }
  var capped = rows.length > 12, nAll = rows.length, notes = '';
  rows = rows.slice(0, 12);
  if (skipped) notes += _hgNote(skipped + (skipped === 1 ? ' entry' : ' entries') + ' skipped: not a usable stage (it needs a number value of 0 or more).');
  if (capped) notes += _hgNote('Showing the first 12 of ' + nAll + ' stages.');
  notes += _hgVersionNote(b, 'conversion_funnel');
  var tot = 0;
  for (i = 0; i < rows.length; i++) tot += rows[i][1];
  if (!rows.length || !(tot > 0)) return _ifWrap('<div class="ifcf">' + _ifTitle(b) + _hgNote('Nothing to draw: the funnel has no stage with a value above zero.') + notes + '</div>');
  var H = 240, W0 = 400, polys = '', cum = 0, prevY = 0, pused = Object.create(null), lused = Object.create(null);
  for (k = 0; k < rows.length; k++) {
    cum += rows[k][1];
    var y2 = Math.max(0, H * (1 - Math.sqrt(Math.max(0, 1 - cum / tot))));
    if (rows[k][1] > 0) {
      var w1 = W0 * (1 - prevY / H), w2 = W0 * (1 - y2 / H);
      var pts = [[200 - w1 / 2, prevY], [200 + w1 / 2, prevY], [200 + w2 / 2, y2], [200 - w2 / 2, y2]];
      polys += '<polygon data-cb="bar" data-key="' + _cfUkey(rows[k][0], pused) + '" class="cfb" points="' + pts.map(function(p) { return _ifFmt(p[0]) + ',' + _ifFmt(p[1]); }).join(' ') + '" fill="' + _IF_CAT[k % 4] + '" stroke="var(--bg,#fff)" stroke-width="2"></polygon>';
    }
    prevY = y2;
  }
  var first = rows[0][1];
  var gist = 'Funnel area chart, area proportional to value: ' + rows.map(function(r) { return r[0] + ' ' + String(r[1]); }).join(', ') + '.';
  var svg = '<svg role="img" aria-label="' + _esc(gist.slice(0, 400)) + '" viewBox="0 0 400 240" style="display:block;width:100%;max-width:420px;height:auto;margin:0 auto;">' + polys + '</svg>';
  var sw = 'flex:none;width:12px;height:12px;border:1px solid var(--border,#64748B);border-radius:2px;align-self:center;';
  var legend = '<ol class="cfl" style="list-style:none;margin:10px 0 0;padding:0;font-size:0.9rem;">' + rows.map(function(r, j) {
    return '<li data-cb="label" data-key="' + _cfUkey(r[0], lused) + '" style="display:flex;align-items:baseline;gap:8px;padding:2px 0;"><span aria-hidden="true" style="' + sw + 'background:' + _IF_CAT[j % 4] + ';"></span>' +
      '<span style="flex:1;min-width:0;overflow-wrap:anywhere;">' + (j + 1) + '. ' + _esc(r[0]) + '</span>' +
      '<span style="flex:none;font-weight:600;font-size:0.9rem;">' + _ifS(String(r[1]), 30) + (first > 0 ? ' · ' + _ifFmt(r[1] / first * 100) + '%' : '') + '</span></li>';
  }).join('') + '</ol>';
  var table = _ifTable(['Stage', 'Value', 'Of first', 'Of total area'], rows.map(function(r) {
    return [r[0], String(r[1]), first > 0 ? _ifFmt(r[1] / first * 100) + '%' : 'n/a', _ifFmt(r[1] / tot * 100) + '%'];
  }));
  return _ifWrap('<div class="ifcf">' + _ifTitle(b) + svg + legend + table + notes + '</div>');
}

function _cfGauge(b) {
  var val = _cfN(b.value), mn = _cfN(b.min), mx = _cfN(b.max_value), thr = _cfN(b.threshold), bad = [];
  if (mn === null && _cfGiven(b.min)) bad.push('min');
  if (mx === null && _cfGiven(b.max_value)) bad.push('max_value');
  if (thr === null && _cfGiven(b.threshold)) bad.push('threshold');
  if (mn === null) mn = 0;
  if (mx === null) mx = 100;
  var unit = _cfName(b.unit).slice(0, 12), label = _ifS(b.label, 40);
  var notes = (bad.length ? _hgNote(bad.join(', ') + (bad.length === 1 ? ' was' : ' were') + ' not a usable number (it needs a plain number below 1e15) and ' + (bad.length === 1 ? 'was' : 'were') + ' ignored.') : '') + _hgVersionNote(b, 'gauge_sla');
  var ROOT = '<div class="ifgs" data-cb="node" data-key="' + _ckey(b.title, 'gauge_sla') + '">';
  if (val === null) return _ifWrap(ROOT + _ifTitle(b) + _hgNote('The value is not a number, so there is nothing to draw.') + notes + '</div>');
  if (!(mx > mn)) return _ifWrap(ROOT + _ifTitle(b) + _hgNote('The maximum must be larger than the minimum, so there is nothing to draw.') + notes + '</div>');
  var span = mx - mn;
  function fr(x) { return Math.min(1, Math.max(0, (x - mn) / span)); }
  var raw = b.steps, src = Array.isArray(raw) ? raw.slice(0, 500) : [], bands = [], skipped = 0, i;
  for (i = 0; i < src.length; i++) {
    var s = src[i], o = (s && typeof s === 'object') ? s : {}, f = _cfN(o.from), t = _cfN(o.to), c = o.color;
    if (f === null || t === null || !(f < t)) { skipped++; continue; }
    f = Math.max(mn, f); t = Math.min(mx, t);
    if (!(f < t)) { skipped++; continue; }
    bands.push([f, t, (typeof c === 'string' && _CF_COLOR.test(c)) ? c : null]);
  }
  var capped = bands.length > 8, nAll = bands.length;
  bands = bands.slice(0, 8);
  if (skipped) notes += _hgNote(skipped + ' step' + (skipped === 1 ? '' : 's') + ' skipped: not a usable band (it needs a numeric from below its to).');
  if (capped) notes += _hgNote('Showing the first 8 of ' + nAll + ' bands.');
  var cx = 150, cy = 140, R = 100;
  function arc(a, z) { return 'M ' + _cfPt(cx, cy, R, a) + ' A 100 100 0 0 1 ' + _cfPt(cx, cy, R, z); }
  var g = '<path d="' + arc(0, 1) + '" fill="none" stroke="var(--border,#CBD5E1)" stroke-width="14"></path>';
  bands.forEach(function(q, k) { g += '<path data-cb="arc" data-key="Band ' + (k + 1) + '" class="gsb" d="' + arc(fr(q[0]), fr(q[1])) + '" fill="none" stroke="' + (q[2] || _IF_CAT[k % 4]) + '" stroke-width="14"></path>'; });
  function seg(frac, r1, r2, cls, w) {
    var a = Math.PI * (1 + frac);
    return '<line class="' + cls + '" x1="' + _ifFmt(cx + r1 * Math.cos(a)) + '" y1="' + _ifFmt(cy + r1 * Math.sin(a)) + '" x2="' + _ifFmt(cx + r2 * Math.cos(a)) +
      '" y2="' + _ifFmt(cy + r2 * Math.sin(a)) + '" stroke="var(--text,#0F172A)" stroke-width="' + w + '" stroke-linecap="round"></line>';
  }
  if (thr !== null) g += seg(fr(thr), 88, 114, 'gst', 3);
  g += seg(fr(val), 0, 82, 'gsn', 4) + '<circle cx="150" cy="140" r="7" fill="var(--text,#0F172A)"></circle>';
  var vs = _ifFmt(val);
  var gist = 'Gauge' + (b.title ? ': ' + _cfName(b.title).slice(0, 60) : '') + ', value ' + vs + unit + ' on a scale from ' + _ifFmt(mn) + ' to ' + _ifFmt(mx) +
    (thr !== null ? ', threshold ' + _ifFmt(thr) : '') + (bands.length ? ', ' + bands.length + ' bands' : '') + '.';
  var svg = '<svg role="img" aria-label="' + _esc(gist) + '" viewBox="0 0 300 160" style="display:block;width:100%;max-width:360px;height:auto;margin:0 auto;">' + g + '</svg>';
  var status = '';
  if (thr !== null) status += val >= thr ? 'At or above the threshold of ' + _ifFmt(thr) + '.' : 'Below the threshold of ' + _ifFmt(thr) + '.';
  if (val < mn || val > mx) status += (status ? ' ' : '') + 'The value is off the scale; the needle stops at the end.';
  var sw = 'flex:none;width:12px;height:12px;border:1px solid var(--border,#64748B);border-radius:2px;align-self:center;';
  var items = bands.map(function(q, k) {
    return '<li style="display:flex;gap:8px;padding:2px 0;"><span aria-hidden="true" style="' + sw + 'background:' + (q[2] || _IF_CAT[k % 4]) + ';"></span><span>Band ' + (k + 1) + ': ' + _ifFmt(q[0]) + ' to ' + _ifFmt(q[1]) + '</span></li>';
  }).join('');
  if (thr !== null) items += '<li style="display:flex;gap:8px;padding:2px 0;"><span aria-hidden="true" style="flex:none;font-weight:700;">|</span><span>Threshold: ' + _ifFmt(thr) + '</span></li>';
  var legend = items ? '<ul class="gsl" style="list-style:none;margin:8px 0 0;padding:0;font-size:0.9rem;">' + items + '</ul>' : '';
  var rows = bands.map(function(q, k) { return ['Band ' + (k + 1), _ifFmt(q[0]), _ifFmt(q[1])]; }).concat([['Scale', _ifFmt(mn), _ifFmt(mx)], ['Value', vs, vs]]);
  if (thr !== null) rows.push(['Threshold', _ifFmt(thr), _ifFmt(thr)]);
  return _ifWrap(ROOT + _ifTitle(b) + svg +
    '<div style="display:flex;justify-content:space-between;max-width:360px;margin:0 auto;font-size:0.9rem;color:var(--muted,#475569);"><span>' + _ifFmt(mn) + '</span><span>' + _ifFmt(mx) + '</span></div>' +
    '<div style="text-align:center;font-weight:800;font-size:1.6rem;">' + vs + _esc(unit) + '</div>' +
    (label ? '<div style="text-align:center;font-size:0.9rem;color:var(--muted,#475569);">' + label + '</div>' : '') +
    (status ? '<div style="text-align:center;font-size:0.9rem;">' + status + '</div>' : '') + legend +
    _ifTable(['Band', 'From', 'To'], rows) + notes + '</div>');
}

var _cfPrevFunnel = _RENDERERS['conversion_funnel'], _cfPrevGauge = _RENDERERS['gauge_sla'];
_RENDERERS['conversion_funnel'] = function(b) { return (b && b.shape === 'area') ? _cfArea(b) : _cfPrevFunnel(b); };
_RENDERERS['gauge_sla'] = function(b) { return (b && (_cfIsnum(b.min) || Array.isArray(b.steps))) ? _cfGauge(b) : _cfPrevGauge(b); };
