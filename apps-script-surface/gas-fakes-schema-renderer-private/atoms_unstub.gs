// atoms_unstub.gs — renderers for all previously-stub atoms
// All pure CSS / SVG / vanilla JS — no external dependencies.

// ─── trend_indicator ──────────────────────────────────────────────────────────
_RENDERERS['trend_indicator'] = function(b) {
  var dir   = b.trend_direction || b.direction || 'stable';
  var label = _esc(b.label || '');
  var ctx   = b.context ? '<span style="font-size:0.75rem;color:var(--muted,#6b7280);margin-left:6px;">' + _esc(b.context) + '</span>' : '';
  var map   = { up: ['↑', '#10b981', '#d1fae5'], down: ['↓', '#ef4444', '#fee2e2'], stable: ['→', '#6b7280', '#f3f4f6'] };
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
  var dColor  = dtype === 'increase' ? '#10b981' : dtype === 'decrease' ? '#ef4444' : '#6b7280';
  var dBg     = dtype === 'increase' ? '#d1fae5' : dtype === 'decrease' ? '#fee2e2' : '#f3f4f6';
  var arrow   = dtype === 'increase' ? '↑' : dtype === 'decrease' ? '↓' : '→';
  var period  = b.comparison_period ? '<div style="font-size:0.72rem;color:var(--muted,#6b7280);margin-top:2px;">' + _esc(b.comparison_period) + '</div>' : '';
  return '<div style="display:inline-flex;flex-direction:column;padding:16px 20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);min-width:140px;">'
    + '<div style="font-size:0.75rem;font-weight:600;color:var(--muted,#6b7280);text-transform:uppercase;letter-spacing:0.05em;">' + label + '</div>'
    + '<div style="font-size:2rem;font-weight:700;color:var(--text,#111827);line-height:1.2;margin:4px 0;">' + current + '</div>'
    + (delta ? '<span style="display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:12px;background:' + dBg + ';color:' + dColor + ';font-size:0.8rem;font-weight:600;width:fit-content;">' + arrow + ' ' + delta + '</span>' : '')
    + period + '</div>';
};

// ─── action_required_card ─────────────────────────────────────────────────────
_RENDERERS['action_required_card'] = function(b) {
  var urgency = b.urgency || b.level || 'medium';
  var uMap    = { high: ['🔴', '#ef4444', '#fef2f2', '#fecaca'], medium: ['🟡', '#f59e0b', '#fffbeb', '#fde68a'], low: ['🔵', '#3b82f6', '#eff6ff', '#bfdbfe'] };
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
  var accent  = b.accent || 'var(--a2ui-accent,#6366f1)';
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
    boxes += '<input id="' + uid + i + '" maxlength="1" inputmode="numeric" pattern="[0-9]" value="' + _esc(digit) + '" '
      + 'style="width:44px;height:52px;text-align:center;font-size:1.4rem;font-weight:700;border:2px solid var(--border,#e5e7eb);border-radius:8px;background:var(--bg,#fff);color:var(--text,#111827);font-family:inherit;" '
      + 'oninput="var n=this.nextElementSibling;if(this.value&&n&&n.tagName===\'INPUT\')n.focus();" '
      + 'onkeydown="if(event.key===\'Backspace\'&&!this.value){var p=this.previousElementSibling;if(p&&p.tagName===\'INPUT\')p.focus();}">';
  }
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + label
    + '<div style="display:flex;gap:8px;flex-wrap:wrap;">' + boxes + '</div></div>';
};

// ─── combobox ─────────────────────────────────────────────────────────────────
_RENDERERS['combobox'] = function(b) {
  var label   = b.label ? '<label style="display:block;font-size:0.82rem;font-weight:600;color:var(--text,#111827);margin-bottom:4px;">' + _esc(b.label) + '</label>' : '';
  var name    = _esc(b.name || 'combobox');
  var opts    = (b.options || []).map(function(o) {
    var val = typeof o === 'object' ? o.value : o;
    var lbl = typeof o === 'object' ? (o.label || o.value) : o;
    var sel = (b.selected && b.selected == val) ? ' selected' : '';
    return '<option value="' + _esc(String(val)) + '"' + sel + '>' + _esc(String(lbl)) + '</option>';
  }).join('');
  var placeholder = b.placeholder ? '<option value="" disabled' + (b.selected ? '' : ' selected') + '>' + _esc(b.placeholder) + '</option>' : '';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + label
    + '<select name="' + name + '" style="width:100%;padding:8px 12px;border:1px solid var(--border,#e5e7eb);border-radius:8px;font-size:0.875rem;background:var(--bg,#fff);color:var(--text,#111827);font-family:inherit;">'
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
    var accent = b.accent || 'var(--a2ui-accent,#6366f1)';
    return '<label style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;cursor:pointer;font-size:0.82rem;border:1px solid ' + (on ? accent : 'var(--border,#e5e7eb)') + ';background:' + (on ? accent + '15' : 'var(--bg,#fff)') + ';color:' + (on ? accent : 'var(--text,#374151)') + ';">'
      + '<input type="checkbox" name="' + _esc(b.name || 'ms') + '[]" value="' + _esc(val) + '"' + (on ? ' checked' : '') + ' style="display:none;">' + _esc(String(lbl)) + '</label>';
  }).join('');
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">' + label
    + '<div style="display:flex;flex-wrap:wrap;gap:6px;">' + opts + '</div></div>';
};

// ─── avatar_group ─────────────────────────────────────────────────────────────
_RENDERERS['avatar_group'] = function(b) {
  var avatars = (b.avatars || []).slice(0, 6);
  var total   = b.total_count || avatars.length;
  var label   = b.label ? '<span style="font-size:0.82rem;color:var(--muted,#6b7280);margin-left:10px;">' + _esc(b.label) + '</span>' : '';
  var surplus = total > avatars.length ? '<div style="width:36px;height:36px;border-radius:50%;background:#e5e7eb;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;color:#6b7280;margin-left:-10px;">+' + (total - avatars.length) + '</div>' : '';
  var imgs = avatars.map(function(a, i) {
    var initials = (a.name || '?').split(' ').map(function(w){ return w[0]; }).join('').substr(0,2).toUpperCase();
    var colors   = ['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6','#0ea5e9'];
    var bg       = colors[i % colors.length];
    if (a.url || a.avatar_url) {
      return '<img src="' + _esc(a.url || a.avatar_url) + '" alt="' + _esc(a.name || '') + '" title="' + _esc(a.name || '') + '" style="width:36px;height:36px;border-radius:50%;border:2px solid #fff;object-fit:cover;margin-left:' + (i > 0 ? '-10' : '0') + 'px;">';
    }
    return '<div title="' + _esc(a.name || '') + '" style="width:36px;height:36px;border-radius:50%;background:' + bg + ';border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;color:#fff;margin-left:' + (i > 0 ? '-10' : '0') + 'px;">' + initials + '</div>';
  }).join('');
  return '<div style="display:flex;align-items:center;margin:var(--a2ui-block-gap,1.25rem) 0;">' + imgs + surplus + label + '</div>';
};

// ─── contributor_list ─────────────────────────────────────────────────────────
_RENDERERS['contributor_list'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';
  var colors = ['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6','#0ea5e9'];
  var rows = (b.contributors || []).map(function(c, i) {
    var initials = (c.name || '?').split(' ').map(function(w){ return w[0]; }).join('').substr(0,2).toUpperCase();
    var bg = c.color || colors[i % colors.length];
    var avatar = c.avatar_url
      ? '<img src="' + _esc(c.avatar_url) + '" alt="" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">'
      : '<div style="width:36px;height:36px;border-radius:50%;background:' + bg + ';color:#fff;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;">' + initials + '</div>';
    var meta = c.contributions ? '<span style="font-size:0.72rem;color:var(--muted,#9ca3af);margin-left:6px;">' + _esc(String(c.contributions)) + ' contributions</span>' : '';
    return '<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border,#e5e7eb);">'
      + avatar
      + '<div style="flex:1;"><div style="font-weight:600;font-size:0.875rem;color:var(--text,#111827);">' + _esc(c.name || '') + meta + '</div>'
      + (c.role ? '<div style="font-size:0.78rem;color:var(--muted,#6b7280);">' + _esc(c.role) + '</div>' : '')
      + '</div>'
      + (c.url ? '<a href="' + _safeUrl(c.url) + '" target="_top" style="font-size:0.75rem;color:var(--a2ui-accent,#6366f1);">→</a>' : '')
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
    return '<li style="display:flex;align-items:flex-start;gap:8px;padding:4px 0;font-size:0.875rem;' + style + '">'
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
    var label  = typeof item === 'object' ? (item.label || item.name || '') : item;
    var status = typeof item === 'object' ? (item.status || 'available') : 'available';
    var map    = { available: ['✓', '#10b981', '#d1fae5'], unavailable: ['✗', '#ef4444', '#fee2e2'], partial: ['◐', '#f59e0b', '#fef3c7'], planned: ['○', '#6b7280', '#f3f4f6'] };
    var cfg    = map[status] || map.available;
    return '<div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border,#f3f4f6);font-size:0.875rem;">'
      + '<span style="width:20px;height:20px;border-radius:50%;background:' + cfg[2] + ';color:' + cfg[1] + ';display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;flex-shrink:0;">' + cfg[0] + '</span>'
      + '<span style="flex:1;color:var(--text,#374151);">' + _esc(String(label)) + '</span>'
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
    var accent = item.color || b.accent || 'var(--a2ui-accent,#6366f1)';
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
  var score = '<div style="text-align:center;margin-bottom:16px;"><div style="font-size:2.5rem;font-weight:700;color:#10b981;">' + index + '%</div><div style="font-size:0.78rem;color:var(--muted,#6b7280);">Positive sentiment</div></div>';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);">'
    + title + score
    + bar('Positive', index, '#10b981', '#d1fae5')
    + bar('Neutral', neu, '#6b7280', '#f3f4f6')
    + bar('Negative', neg, '#ef4444', '#fee2e2')
    + '</div>';
};

// ─── call_mood_board ──────────────────────────────────────────────────────────
_RENDERERS['call_mood_board'] = function(b) {
  var title = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';
  var moods = (b.moods || []).map(function(m) {
    var pct = Math.min(100, m.intensity || 50);
    var color = m.color || 'var(--a2ui-accent,#6366f1)';
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
  var metric = b.metric_value ? '<div style="font-size:2rem;font-weight:700;color:var(--a2ui-accent,#6366f1);">' + _esc(b.metric_value) + '</div><div style="font-size:0.82rem;color:var(--muted,#6b7280);">' + _esc(b.metric_label || '') + '</div>' : '';
  var logos  = (b.logos || []).map(function(l) {
    return l.url
      ? '<img src="' + _esc(l.url) + '" alt="' + _esc(l.name || '') + '" style="height:32px;object-fit:contain;opacity:0.6;filter:grayscale(1);">'
      : '<span style="font-size:0.8rem;font-weight:700;color:var(--muted,#9ca3af);padding:4px 12px;">' + _esc(l.name || '') + '</span>';
  }).join('');
  var quote  = b.testimonial ? '<blockquote style="font-style:italic;font-size:0.875rem;color:var(--text,#374151);margin:0;">"' + _esc(b.testimonial) + '"</blockquote>' : '';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:24px;border:1px solid var(--border,#e5e7eb);border-radius:10px;background:var(--bg,#fff);text-align:center;">'
    + metric
    + (logos ? '<div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:16px;margin:16px 0;">' + logos + '</div>' : '')
    + quote + '</div>';
};

// ─── expert_endorsement ───────────────────────────────────────────────────────
_RENDERERS['expert_endorsement'] = function(b) {
  var initials = (b.expert_name || '?').split(' ').map(function(w){return w[0];}).join('').substr(0,2).toUpperCase();
  var avatar = b.expert_avatar_url
    ? '<img src="' + _esc(b.expert_avatar_url) + '" alt="' + _esc(b.expert_name||'') + '" style="width:56px;height:56px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
    : '<div style="width:56px;height:56px;border-radius:50%;background:var(--a2ui-accent,#6366f1);color:#fff;display:flex;align-items:center;justify-content:center;font-size:1.1rem;font-weight:700;flex-shrink:0;">' + initials + '</div>';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;padding:20px;border-left:4px solid var(--a2ui-accent,#6366f1);border-radius:0 10px 10px 0;background:var(--surface,#f9fafb);">'
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
_RENDERERS['media_stream_card'] = function(b) {
  var url    = b.url || '';
  var title  = b.title || '';
  var height = b.height || '315px';
  // Auto-detect YouTube and convert to embed URL
  var src = url;
  var ytMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
  if (ytMatch) src = 'https://www.youtube-nocookie.com/embed/' + ytMatch[1];
  var loomMatch = url.match(/loom\.com\/share\/([a-zA-Z0-9]+)/);
  if (loomMatch) src = 'https://www.loom.com/embed/' + loomMatch[1];
  var titleHtml = title ? '<div style="font-size:0.82rem;font-weight:600;color:var(--muted,#6b7280);margin-bottom:6px;">' + _esc(title) + '</div>' : '';
  return '<div style="margin:var(--a2ui-block-gap,1.25rem) 0;">'
    + titleHtml
    + '<div style="position:relative;padding-top:56.25%;border-radius:10px;overflow:hidden;background:#000;">'
    + '<iframe src="' + _esc(src) + '" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen loading="lazy"></iframe>'
    + '</div></div>';
};

// ─── product_thumbnail ────────────────────────────────────────────────────────
_RENDERERS['product_thumbnail'] = function(b) {
  var badge = b.badge ? '<div style="position:absolute;top:8px;left:8px;padding:2px 8px;border-radius:4px;background:var(--a2ui-accent,#6366f1);color:#fff;font-size:0.72rem;font-weight:700;">' + _esc(b.badge) + '</div>' : '';
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
  var logos = (b.logos || []).map(function(l) {
    if (l.url && l.image_url) {
      return '<a href="' + _safeUrl(l.url) + '" target="_top" style="display:flex;align-items:center;justify-content:center;padding:12px;"><img src="' + _esc(l.image_url) + '" alt="' + _esc(l.name||'') + '" style="max-height:36px;max-width:120px;object-fit:contain;opacity:0.5;filter:grayscale(1);transition:opacity 0.2s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.5"></a>';
    }
    if (l.image_url) {
      return '<div style="display:flex;align-items:center;justify-content:center;padding:12px;"><img src="' + _esc(l.image_url) + '" alt="' + _esc(l.name||'') + '" style="max-height:36px;max-width:120px;object-fit:contain;opacity:0.5;filter:grayscale(1);"></div>';
    }
    return '<div style="display:flex;align-items:center;justify-content:center;padding:12px;font-size:0.8rem;font-weight:700;color:var(--muted,#9ca3af);">' + _esc(l.name||'') + '</div>';
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
    + '<a href="' + _safeUrl(repoUrl) + '" target="_top" style="font-weight:700;font-size:0.9rem;color:var(--a2ui-accent,#6366f1);text-decoration:none;">' + _esc(repo) + '</a>'
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
  var svg = '<svg width="144" height="80" viewBox="0 0 144 80" style="overflow:visible;">'
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
  var color  = b.color || 'var(--a2ui-accent,#6366f1)';
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
  return '<svg width="' + w + '" height="' + h + '" style="display:inline-block;vertical-align:middle;">'
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
    var color = p.color || b.color || '#6366f1';
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

// ─── stacked_area ─────────────────────────────────────────────────────────────
// Rendered as stacked horizontal bars (CSS approximation — no canvas/JS charting needed).
_RENDERERS['stacked_area'] = function(b) {
  var title   = b.title ? '<div style="font-weight:700;font-size:0.9rem;color:var(--text,#111827);margin-bottom:12px;">' + _esc(b.title) + '</div>' : '';
  var labels  = b.labels || [];
  var series  = b.series || [];
  var colors  = ['#6366f1','#10b981','#f59e0b','#ef4444','#8b5cf6','#0ea5e9'];
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
};

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
    cells += '<div title="' + iso + ': ' + count + '" style="width:10px;height:10px;border-radius:2px;background:' + bg + ';flex-shrink:0;"></div>';
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
    var cnt = h.content ? '<div class="' + uid + '-tip" style="display:none;position:absolute;left:calc(' + x + '% + 18px);top:calc(' + y + '% - 10px);background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:0.78rem;color:#374151;min-width:120px;max-width:200px;z-index:10;box-shadow:0 4px 12px rgba(0,0,0,0.1);">' + _esc(h.content) + '</div>' : '';
    return '<div style="position:absolute;left:' + x + '%;top:' + y + '%;transform:translate(-50%,-50%);" onmouseenter="var t=this.querySelector(\'.' + uid + '-tip\');if(t)t.style.display=\'block\';" onmouseleave="var t=this.querySelector(\'.' + uid + '-tip\');if(t)t.style.display=\'none\';">'
      + '<div style="width:24px;height:24px;border-radius:50%;background:var(--a2ui-accent,#6366f1);color:#fff;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:700;cursor:pointer;box-shadow:0 0 0 4px rgba(99,102,241,0.2);animation:pulse 2s infinite;">' + lbl + '</div>'
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
    return '<tr style="border-bottom:1px solid var(--border,#f3f4f6);">'
      + '<td style="padding:8px 10px;font-size:0.82rem;color:var(--text,#374151);">' + _esc(item.product || item.sku || '') + '</td>'
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
    return '<th style="padding:8px 12px;text-align:left;font-size:0.75rem;font-weight:600;color:var(--muted,#6b7280);white-space:nowrap;user-select:none;" title="' + _esc(c.header||c.key||'') + '">' + _esc(c.header || c.key || '') + '</th>';
  }).join('');
  var trs = rows.map(function(row, ri) {
    var tds = columns.map(function(c) {
      var val = row[c.key] !== undefined ? row[c.key] : '';
      var cell = '';
      if (c.type === 'status') {
        var smap = { active: ['✓','#10b981','#d1fae5'], inactive: ['✗','#ef4444','#fee2e2'], pending: ['○','#f59e0b','#fef3c7'] };
        var cfg  = smap[String(val).toLowerCase()] || ['?','#6b7280','#f3f4f6'];
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
    return '<tr style="background:' + (ri % 2 ? 'var(--surface,#f9fafb)' : 'var(--bg,#fff)') + ';">' + trs + '</tr>';
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
  var accent = b.accent || 'var(--a2ui-accent,#6366f1)';
  var maxVal = Math.max.apply(null, steps.map(function(s){ return parseFloat(s.value||0); })) || 1;
  var html   = steps.map(function(s, i) {
    var val = parseFloat(s.value || 0);
    var pct = (val / maxVal * 100).toFixed(0);
    var conv = i > 0 ? ((val / parseFloat(steps[i-1].value||1)) * 100).toFixed(0) + '% of prev' : '';
    return '<div style="text-align:center;margin-bottom:4px;">'
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
  var accent  = b.accent || 'var(--a2ui-accent,#6366f1)';
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
