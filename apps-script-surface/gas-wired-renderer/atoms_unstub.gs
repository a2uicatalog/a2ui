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
  return '<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:20px;background:' + cfg[2] + ';font-size:0.82rem;font-weight:600;color:' + col + ';">'
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
  return _cardChrome(inner, 'card', 'display:inline-flex;flex-direction:column;padding:16px 20px;min-width:140px;');
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
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:18px 20px;border-left:4px solid ' + cfg[1] + ';border-radius:0 10px 10px 0;background:' + cfg[2] + ';">'
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
  return '<details' + open + ' style="margin:var(--a2ui-block-gap,1.25rem) 0;border:1px solid var(--border,#e5e7eb);border-radius:8px;overflow:hidden;">'
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
  var avatars = (b.avatars || []).slice(0, 6);
  var total   = b.total_count || avatars.length;
  var label   = b.label ? '<span style="font-size:0.82rem;color:var(--muted,#6b7280);margin-left:10px;">' + _esc(b.label) + '</span>' : '';
  var surplus = total > avatars.length ? '<div style="width:36px;height:36px;border-radius:50%;background:#e5e7eb;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;color:var(--muted,#5f6368);margin-left:-10px;">+' + (total - avatars.length) + '</div>' : '';
  var imgs = avatars.map(function(a, i) {
    var initials = (a.name || '?').split(' ').map(function(w){ return w[0]; }).join('').substr(0,2).toUpperCase();
    var colors   = ['#4f46e5','#10b981','#f59e0b','#ef4444','#8b5cf6','#0ea5e9'];
    var bg       = colors[i % colors.length];
    if (a.url || a.avatar_url) {
      return '<img data-cb="item" data-key="' + _esc(a.name || '') + '" src="' + _esc(a.url || a.avatar_url) + '" alt="' + _esc(a.name || '') + '" title="' + _esc(a.name || '') + '" style="width:36px;height:36px;border-radius:50%;border:2px solid #fff;object-fit:cover;margin-left:' + (i > 0 ? '-10' : '0') + 'px;">';
    }
    return '<div data-cb="item" data-key="' + _esc(a.name || '') + '" title="' + _esc(a.name || '') + '" style="width:36px;height:36px;border-radius:50%;background:' + bg + ';border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;color:#fff;margin-left:' + (i > 0 ? '-10' : '0') + 'px;">' + initials + '</div>';
  }).join('');
  return '<div style="display:flex;align-items:center;margin:var(--a2ui-block-gap,1.25rem) 0;">' + imgs + surplus + label + '</div>';
};

// ─── contributor_list ─────────────────────────────────────────────────────────
_RENDERERS['contributor_list'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';
  var colors = ['#4f46e5','#10b981','#f59e0b','#ef4444','#8b5cf6','#0ea5e9'];
  var rows = (b.contributors || []).map(function(c, i) {
    var initials = (c.name || '?').split(' ').map(function(w){ return w[0]; }).join('').substr(0,2).toUpperCase();
    var bg = c.color || colors[i % colors.length];
    var avatar = c.avatar_url
      ? '<img src="' + _esc(c.avatar_url) + '" alt="" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">'
      : '<div style="width:36px;height:36px;border-radius:50%;background:' + bg + ';color:#fff;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;">' + initials + '</div>';
    var meta = c.contributions ? '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-left:6px;">' + _esc(String(c.contributions)) + ' contributions</span>' : '';
    return '<div data-cb="item" data-key="' + _esc(c.name || '') + '" style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border,#e5e7eb);">'
      + avatar
      + '<div style="flex:1;"><div data-cb="label" data-key="' + _esc(c.name || '') + '" style="font-weight:600;font-size:0.875rem;color:var(--text,#111827);">' + _esc(c.name || '') + meta + '</div>'
      + (c.role ? '<div style="font-size:0.78rem;color:var(--muted,#6b7280);">' + _esc(c.role) + '</div>' : '')
      + '</div>'
      + (c.url ? '<a href="' + _safeUrl(c.url) + '" target="_top" style="font-size:0.75rem;color:var(--a2ui-accent,#4f46e5);">→</a>' : '')
      + '</div>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + title + rows + '</div>';
};

// ─── prerequisite_checklist ───────────────────────────────────────────────────
_RENDERERS['prerequisite_checklist'] = function(b) {
  var title = _esc(b.title || 'Prerequisites');
  var items = (b.items || []).map(function(item) {
    var text  = typeof item === 'object' ? (item.text || item.label || '') : item;
    var done  = typeof item === 'object' ? item.done : false;
    var icon  = done ? '✅' : '⬜';
    var style = done ? 'text-decoration:line-through;color:var(--muted,#9ca3af);' : 'color:var(--text,#374151);';
    return '<li data-cb="item" data-key="' + _esc(String(text)) + '" style="display:flex;align-items:flex-start;gap:8px;padding:4px 0;font-size:0.875rem;' + style + '">'
      + '<span style="flex-shrink:0;">' + icon + '</span>'
      + '<span>' + _markdownToHtml(String(text)) + '</span></li>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px 20px;background:#fffbeb;border:1px solid #fde68a;border-radius:10px;">'
    + '<div style="font-weight:700;font-size:0.9rem;color:#92400e;margin-bottom:10px;">⚠️ ' + title + '</div>'
    + '<ul style="list-style:none;padding:0;margin:0;">' + items + '</ul></div>';
};

// ─── capability_checklist ─────────────────────────────────────────────────────
_RENDERERS['capability_checklist'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:10px;">' + _esc(b.title) + '</div>' : '';
  var names = b.capability_names || [];
  var items = (b.items || names).map(function(item) {
    var label  = typeof item === 'object' ? (item.name || item.text || item.label || '') : item;
    var key    = _esc(String(label));
    var status = typeof item === 'object' ? (item.status || 'available') : 'available';
    var map    = { available: ['✓', '#10b981', '#d1fae5'], unavailable: ['✗', '#ef4444', '#fee2e2'], partial: ['◐', '#f59e0b', '#fef3c7'], planned: ['○', '#6b7280', '#f3f4f6'] };
    var cfg    = map[status] || map.available;
    return '<div data-cb="item" data-key="' + key + '" style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border,#f3f4f6);font-size:0.875rem;">'
      + '<span style="width:20px;height:20px;border-radius:50%;background:' + cfg[2] + ';color:' + cfg[1] + ';display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;flex-shrink:0;">' + cfg[0] + '</span>'
      + '<span data-cb="label" data-key="' + key + '" style="flex:1;color:var(--text,#374151);">' + _esc(String(label)) + '</span>'
      + (typeof item === 'object' && item.tier ? '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);">' + _esc(item.tier) + '</span>' : '')
      + '</div>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + items + '</div>';
};

// ─── review_callout ───────────────────────────────────────────────────────────
_RENDERERS['review_callout'] = function(b) {
  var rating  = Math.round(b.rating || 5);
  var max     = b.max_rating || 5;
  var stars   = '';
  for (var i = 1; i <= max; i++) {
    stars += '<span style="color:' + (i <= rating ? '#fbbf24' : '#e5e7eb') + ';font-size:1rem;">★</span>';
  }
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + (b.product_name ? '<div style="font-size:0.75rem;font-weight:600;color:var(--muted,#6b7280);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">' + _esc(b.product_name) + '</div>' : '')
    + '<div style="margin-bottom:10px;">' + stars + '</div>'
    + '<blockquote style="margin:0;font-size:0.9rem;line-height:1.6;color:var(--text,#374151);font-style:italic;">"' + _esc(b.review_text || '') + '"</blockquote>'
    + (b.author_name ? '<div style="margin-top:10px;font-size:0.8rem;font-weight:600;color:var(--muted,#6b7280);">— ' + _esc(b.author_name) + '</div>' : '')
    + '</div>';
};

// ─── rating_comparison ────────────────────────────────────────────────────────
_RENDERERS['rating_comparison'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:10px;">' + _esc(b.title) + '</div>' : '';
  var rows = (b.items || []).map(function(item) {
    var label  = _esc(item.label || item.name || '');
    var rating = parseFloat(item.rating || item.value || 0);
    var max    = parseFloat(item.max || b.max || 5);
    var pct    = Math.round((rating / max) * 100);
    var accent = item.color || b.accent || 'var(--a2ui-accent,#4f46e5)';
    var stars  = '';
    for (var i = 1; i <= max; i++) {
      stars += '<span style="color:' + (i <= Math.round(rating) ? '#fbbf24' : '#e5e7eb') + ';font-size:0.85rem;">★</span>';
    }
    return '<div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border,#f3f4f6);font-size:0.875rem;">'
      + '<span style="min-width:120px;color:var(--text,#374151);">' + label + '</span>'
      + stars
      + '<span style="font-size:0.8rem;color:var(--muted,#6b7280);margin-left:4px;">(' + rating + ')</span>'
      + '</div>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + rows + '</div>';
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
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
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
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title
    + (moods ? '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px;">' + moods + '</div>' : '')
    + (themes ? '<div style="display:flex;flex-wrap:wrap;gap:6px;">' + themes + '</div>' : '')
    + '</div>';
};

// ─── social_proof_banner ──────────────────────────────────────────────────────
_RENDERERS['social_proof_banner'] = function(b) {
  var metric = b.metric_value ? '<div style="font-size:2rem;font-weight:700;color:var(--a2ui-accent,#4f46e5);">' + _esc(b.metric_value) + '</div><div style="font-size:0.82rem;color:var(--muted,#6b7280);">' + _esc(b.metric_label || '') + '</div>' : '';
  var logos  = (b.logos || []).map(function(l) {
    return l.url
      ? '<img src="' + _esc(l.url) + '" alt="' + _esc(l.name || '') + '" style="height:32px;object-fit:contain;opacity:0.6;filter:grayscale(1);">'
      : '<span style="font-size:0.8rem;font-weight:700;color:var(--muted,#9ca3af);padding:4px 12px;">' + _esc(l.name || '') + '</span>';
  }).join('');
  var quote  = b.testimonial ? '<blockquote style="font-style:italic;font-size:0.875rem;color:var(--text,#374151);margin:0;">"' + _esc(b.testimonial) + '"</blockquote>' : '';
  // Schema also declares `icon_url` and `link_url`; neither was ever used at all
  // (surface-parity debt). 2026-09-27.
  var iconHtml = b.icon_url ? '<img src="' + _esc(b.icon_url) + '" alt="" style="width:20px;height:20px;object-fit:contain;margin-bottom:8px;">' : '';
  var body = iconHtml
    + '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:24px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);text-align:center;">'
    + metric
    + (logos ? '<div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:16px;margin:16px 0;">' + logos + '</div>' : '')
    + quote + '</div>';
  return b.link_url ? '<a href="' + _safeUrl(b.link_url) + '" target="_top" style="text-decoration:none;color:inherit;display:block;">' + body + '</a>' : body;
};

// ─── expert_endorsement ───────────────────────────────────────────────────────
_RENDERERS['expert_endorsement'] = function(b) {
  var initials = (b.expert_name || '?').split(' ').map(function(w){return w[0];}).join('').substr(0,2).toUpperCase();
  var avatar = b.expert_avatar_url
    ? '<img src="' + _esc(b.expert_avatar_url) + '" alt="' + _esc(b.expert_name||'') + '" style="width:56px;height:56px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
    : '<div style="width:56px;height:56px;border-radius:50%;background:var(--a2ui-accent,#4f46e5);color:#fff;display:flex;align-items:center;justify-content:center;font-size:1.1rem;font-weight:700;flex-shrink:0;">' + initials + '</div>';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border-left:4px solid var(--a2ui-accent,#4f46e5);border-radius:0 10px 10px 0;background:var(--surface,#f9fafb);">'
    + '<blockquote style="margin:0 0 16px 0;font-size:0.9rem;line-height:1.7;color:var(--text,#374151);font-style:italic;">"' + _esc(b.quote || '') + '"</blockquote>'
    + '<div style="display:flex;align-items:center;gap:12px;">' + avatar
    + '<div><div style="font-weight:700;font-size:0.875rem;color:var(--text,#111827);">' + _esc(b.expert_name || '') + '</div>'
    + (b.expert_title ? '<div style="font-size:0.78rem;color:var(--muted,#6b7280);">' + _esc(b.expert_title) + '</div>' : '')
    + (b.expert_organization ? '<div style="font-size:0.78rem;color:var(--muted,#9ca3af);">' + _esc(b.expert_organization) + '</div>' : '')
    + '</div></div></div>';
};

// ─── media_mention_card ───────────────────────────────────────────────────────
_RENDERERS['media_mention_card'] = function(b) {
  var logo = b.publication_logo_url
    ? '<img src="' + _esc(b.publication_logo_url) + '" alt="' + _esc(b.publication_name||'') + '" style="height:24px;object-fit:contain;opacity:0.6;">'
    : '<span style="font-size:0.78rem;font-weight:700;color:var(--muted,#6b7280);">' + _esc(b.publication_name || '') + '</span>';
  var headline = b.article_url
    ? '<a href="' + _safeUrl(b.article_url) + '" target="_top" style="font-size:0.9rem;font-weight:600;color:var(--text,#111827);text-decoration:none;line-height:1.4;">' + _esc(b.headline || '') + '</a>'
    : '<div style="font-size:0.9rem;font-weight:600;color:var(--text,#111827);line-height:1.4;">' + _esc(b.headline || '') + '</div>';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px 20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">'
    + logo
    + (b.date ? '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);">' + _esc(b.date) + '</span>' : '')
    + '</div>'
    + headline
    + (b.excerpt ? '<div style="font-size:0.82rem;color:var(--muted,#6b7280);margin-top:6px;line-height:1.5;">' + _esc(b.excerpt) + '</div>' : '')
    + '</div>';
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
  var badge = b.badge ? '<div style="position:absolute;top:8px;left:8px;padding:2px 8px;border-radius:4px;background:var(--a2ui-accent,#4f46e5);color:#fff;font-size:0.72rem;font-weight:700;">' + _esc(b.badge) + '</div>' : '';
  var img   = b.image_url ? '<div style="position:relative;"><img src="' + _esc(b.image_url) + '" alt="' + _esc(b.title||'') + '" style="width:100%;aspect-ratio:1;object-fit:cover;border-radius:8px;">' + badge + '</div>' : '';
  var compare = b.compare_at_price ? '<span style="text-decoration:line-through;color:var(--muted,#9ca3af);font-size:0.82rem;margin-left:6px;">' + _esc(b.compare_at_price) + '</span>' : '';
  var status = b.status ? '<span style="font-size:0.72rem;padding:2px 6px;border-radius:4px;background:' + (b.status === 'in_stock' ? '#d1fae5' : '#fee2e2') + ';color:' + (b.status === 'in_stock' ? '#10b981' : '#ef4444') + ';margin-left:6px;">' + _esc(b.status.replace(/_/g,' ')) + '</span>' : '';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;border:1px solid var(--border,#e5e7eb);border-radius:10px;overflow:hidden;background:var(--bg,#fff);display:inline-block;max-width:200px;">'
    + img
    + '<div style="padding:10px 12px;">'
    + (b.vendor ? '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);">' + _esc(b.vendor) + '</div>' : '')
    + '<div style="font-size:0.875rem;font-weight:600;color:var(--text,#111827);margin:2px 0;">' + _esc(b.title || '') + '</div>'
    + (b.sku ? '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);">SKU: ' + _esc(b.sku) + '</div>' : '')
    + '<div style="margin-top:6px;"><span style="font-weight:700;color:var(--text,#111827);">' + _esc(b.price || '') + '</span>' + compare + status + '</div>'
    + '</div></div>';
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
  var repo = b.repo || b.label || '';
  var langColors = { JavaScript:'#f1e05a', TypeScript:'#3178c6', Python:'#3572A5', Go:'#00ADD8', Rust:'#dea584', Java:'#b07219', CSS:'#563d7c', HTML:'#e34c26' };
  var langColor  = langColors[b.language] || '#6b7280';
  var starsHtml  = b.stars !== undefined ? '<span style="display:flex;align-items:center;gap:3px;font-size:0.78rem;color:var(--muted,#6b7280);">⭐ ' + _esc(String(b.stars)) + '</span>' : '';
  var forksHtml  = b.forks !== undefined ? '<span style="display:flex;align-items:center;gap:3px;font-size:0.78rem;color:var(--muted,#6b7280);">🍴 ' + _esc(String(b.forks)) + '</span>' : '';
  var langHtml   = b.language ? '<span style="display:flex;align-items:center;gap:4px;font-size:0.78rem;color:var(--muted,#6b7280);"><span style="width:10px;height:10px;border-radius:50%;background:' + langColor + ';display:inline-block;"></span>' + _esc(b.language) + '</span>' : '';
  var repoUrl    = b.url || (repo ? 'https://github.com/' + repo : '#');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px 20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
    + '<span style="font-size:1rem;">📦</span>'
    + '<a href="' + _safeUrl(repoUrl) + '" target="_top" style="font-weight:700;font-size:0.9rem;color:var(--a2ui-accent,#4f46e5);text-decoration:none;">' + _esc(repo) + '</a>'
    + (b.visibility ? '<span style="font-size:0.7rem;padding:1px 6px;border:1px solid var(--border,#e5e7eb);border-radius:4px;color:var(--muted,#6b7280);">' + _esc(b.visibility) + '</span>' : '')
    + '</div>'
    + (b.description ? '<div style="font-size:0.82rem;color:var(--muted,#6b7280);line-height:1.5;margin-bottom:10px;">' + _esc(b.description) + '</div>' : '')
    + (b.topics ? '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px;">' + b.topics.map(function(t){ return '<span style="padding:2px 8px;border-radius:12px;background:#dbeafe;color:#1d4ed8;font-size:0.72rem;">' + _esc(t) + '</span>'; }).join('') + '</div>' : '')
    + '<div style="display:flex;gap:14px;">' + starsHtml + forksHtml + langHtml + '</div>'
    + (b.license ? '<div style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-top:6px;">⚖️ ' + _esc(b.license) + '</div>' : '')
    + '</div>';
};

// ─── gauge_sla ────────────────────────────────────────────────────────────────
_RENDERERS['gauge_sla'] = function(b) {
  var value   = parseFloat(b.value || 0);
  var max     = parseFloat(b.max_value || 100);
  var pct     = Math.min(1, value / max);
  var unit    = _esc(b.unit || '');
  var label   = _esc(b.label || '');
  var title   = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:8px;">' + _esc(b.title) + '</div>' : '';
  var thresh  = b.threshold || 90;
  var color   = value >= thresh ? '#10b981' : value >= thresh * 0.9 ? '#f59e0b' : '#ef4444';
  // SVG semicircle gauge
  var r = 56, cx = 72, cy = 72;
  var circ = Math.PI * r;
  var dash = pct * circ;
  var svgStyle = 'transform:rotate(-180deg)';
  var svg = '<svg role="img" aria-label="SLA gauge" width="144" height="80" viewBox="0 0 144 80" style="overflow:visible;">'
    + '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="#f3f4f6" stroke-width="12" stroke-dasharray="' + circ + '" stroke-dashoffset="' + (circ / 2) + '" style="' + svgStyle + '" stroke-linecap="round"/>'
    + '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="' + color + '" stroke-width="12" stroke-dasharray="' + dash + ' ' + circ + '" stroke-dashoffset="' + (circ / 2) + '" style="' + svgStyle + ';transition:stroke-dasharray 0.5s;" stroke-linecap="round"/>'
    + '<text x="' + cx + '" y="' + (cy - 8) + '" text-anchor="middle" style="font-size:20px;font-weight:700;fill:' + color + ';">' + value + unit + '</text>'
    + (label ? '<text x="' + cx + '" y="' + (cy + 12) + '" text-anchor="middle" style="font-size:10px;fill:#9ca3af;">' + label + '</text>' : '')
    + '</svg>';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:16px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);text-align:center;">'
    + title + svg + '</div>';
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
  return '<svg role="img" aria-label="Sparkline" width="' + w + '" height="' + h + '" style="display:inline-block;vertical-align:middle;">'
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
  var title   = b.title ? '<div style="font-weight:700;font-size:0.9rem;padding:10px 12px;background:#1e293b;color:#f8fafc;border-radius:8px 8px 0 0;">' + _esc(b.title) + '</div>' : '';
  var columns = b.columns || [];
  var rows    = b.rows    || [];
  var uid     = 'dg' + Math.random().toString(36).substr(2, 5);
  var ths     = columns.map(function(c) {
    return '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;font-weight:600;color:var(--muted,#666d7a);white-space:nowrap;user-select:none;" title="' + _esc(c.header||c.key||'') + '">' + _esc(c.header || c.key || '') + '</th>';
  }).join('');
  var trs = rows.map(function(row, ri) {
    var tds = columns.map(function(c) {
      var val = row[c.key] !== undefined ? row[c.key] : '';
      var cell = '';
      if (c.type === 'status') {
        var smap = { active: ['✓','#10b981','#d1fae5'], inactive: ['✗','#ef4444','#fee2e2'], pending: ['○','#f59e0b','#fef3c7'] };
        var cfg  = smap[String(val).toLowerCase()] || ['?','#666d7a','#f3f4f6'];
        cell = '<span style="padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;background:' + cfg[2] + ';color:' + cfg[1] + ';">' + cfg[0] + ' ' + _esc(String(val)) + '</span>';
      } else if (c.type === 'tag') {
        cell = '<span style="padding:2px 8px;border-radius:12px;font-size:0.75rem;background:#dbeafe;color:#1d4ed8;">' + _esc(String(val)) + '</span>';
      } else if (c.type === 'number') {
        cell = '<span style="font-variant-numeric:tabular-nums;">' + _esc(String(val)) + '</span>';
      } else {
        cell = _esc(String(val));
      }
      return '<td style="padding:8px 12px;font-size:0.82rem;color:var(--text,#374151);border-bottom:1px solid var(--border,#f3f4f6);">' + cell + '</td>';
    }).join('');
    var rKey = _esc(String(row.id !== undefined ? row.id : (row.name || row.label || row.title || (columns.length > 0 && row[columns[0].key] !== undefined ? row[columns[0].key] : ''))));
    return '<tr data-cb="item" data-key="' + rKey + '" style="background:' + (ri % 2 ? 'var(--surface,#f9fafb)' : 'var(--bg,#fff)') + ';">' + trs + '</tr>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;border:1px solid var(--border,#e5e7eb);border-radius:10px;overflow:hidden;">'
    + title + '<div style="overflow-x:auto;">'
    + '<table id="' + uid + '" style="width:100%;border-collapse:collapse;">'
    + '<thead><tr style="background:var(--surface,#f9fafb);">' + ths + '</tr></thead>'
    + '<tbody>' + trs + '</tbody></table></div></div>';
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
      + '<span>' + icon + '</span><span>' + _esc(node.label || '') + '</span>' + meta + '</div>';
    if (!hasKids) return label;
    var kids = node.children.map(function(c){ return renderNode(c, depth + 1); }).join('');
    return '<details' + (node.expanded !== false ? ' open' : '') + '><summary style="display:flex;align-items:center;gap:6px;padding:4px 8px;border-radius:4px;font-size:0.85rem;color:var(--text,#374151);cursor:pointer;list-style:none;padding-left:' + indent + 'px;">'
      + '▶ <span>' + icon + '</span><span>' + _esc(node.label || '') + '</span>' + meta + '</summary>'
      + kids + '</details>';
  }
  var nodes = (b.nodes || []).map(function(n){ return renderNode(n, 0); }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:12px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);font-family:var(--font,inherit);">'
    + title + nodes + '</div>';
};
