/**
 * atoms_v1_standard.gs — renderers for ALL 18 A2UI v1.0 Basic Catalog components (display,
 * layout and the five inputs). Until 2026-10-05 this covered only the ~12 names
 * renderers/a2ui_v1.py itself emits; a plain-spec agent's TextField/CheckBox/ChoicePicker/
 * Slider/DateTimeInput/List drew nothing. tests/test_basic_catalog_coverage.py now checks
 * every component in the vendored spec catalog has a renderer here. The emitter's own names are
 * the ~78 common atoms it maps to a standard shape —
 * distinct from "extension" atoms (e.g. brevet_timeline), which keep their OWN
 * catalogue type name as `component` and dispatch straight into their EXISTING
 * _RENDERERS entry unchanged; nothing here is needed for those.
 *
 * Only reachable via the v1.0 decode path (_rehydrateV1Surface in Code.gs) — the
 * legacy `blocks` dialect never produces these component names. See
 * spec/childlist-migration-v0.1.md (a2ui-private) for the migration this is Phase 1 of.
 */

_RENDERERS['Text'] = function(b) {
  return '<p class="asw-body">' + _markdownToHtml(b.text || '') + '</p>';
};

_RENDERERS['Image'] = function(b) {
  // 2026-08-24: real basic-catalog Image field is `description`, not
  // `alt` -- renderers/a2ui_v1.py's own fix, same date. `b.alt` kept as
  // fallback for a stale-bundle rollout window, same reasoning as
  // atoms_v1_decode.gs's surfaceProperties fallback.
  var altText = b.description || b.alt || '';
  var alt = altText ? ' alt="' + _esc(altText) + '"' : '';
  return '<div style="margin:16px 0;text-align:center;">' +
         '<img src="' + _esc(b.url) + '"' + alt + ' style="max-width:100%;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">' +
         '</div>';
};

_RENDERERS['Button'] = function(b) {
  // 2026-08-24: real basic-catalog Button has no `label` field -- it
  // takes a `child` id (renderers/a2ui_v1.py now synthesizes a Text
  // component and points `child` at it). The generic componentId
  // resolution in atoms_v1_decode.gs already resolves `child` into a
  // full node object (see that file's own resolveNode loop) -- b.child
  // is that resolved node, .text is its rendered string. b.label kept
  // as fallback for a stale-bundle rollout window.
  var label = (b.child && b.child.text) || b.label || 'Button';
  var ev = b.action && b.action.event;
  var url = ev && ev.context && ev.context.url;
  var variant = b.variant === 'borderless' ? 'borderless' : (b.variant === 'primary' ? 'primary' : 'default');
  var look = variant === 'primary'
    ? 'background:var(--a2ui-accent,#6366f1);color:#fff;border:1px solid var(--a2ui-accent,#6366f1);'
    : (variant === 'borderless' ? 'background:none;color:var(--a2ui-accent,#6366f1);border:1px solid transparent;'
                                : 'background:none;color:var(--a2ui-accent,#6366f1);border:1px solid var(--a2ui-accent,#6366f1);');
  var css = 'display:inline-block;padding:10px 20px;border-radius:8px;' + look + 'text-decoration:none;margin:8px 0;font:inherit;font-weight:600;cursor:pointer;';
  // openUrl (the emitter's link-button convention) and the legacy no-name shape stay plain links
  if (url && (!ev.name || ev.name === 'openUrl')) {
    return '<a class="asw-button" href="' + _safeUrl(url) + '" style="' + css + '">' + _esc(label) + '</a>';
  }
  if (b._a2uiAction) {
    // A2UI v1.0 event: the surface runtime resolves context against the LIVE data model at click
    // time and sends the spec's renderer_to_agent `action` message (see _A2UI_V1_RUNTIME).
    return '<button type="button" class="asw-button" data-a2ui-action="' + _esc(String(b._a2uiAction)) +
           '" data-a2ui-src="' + _esc(b._a2uiId || '') + '" style="' + css + '">' + _esc(label) + '</button>';
  }
  return '<a class="asw-button" href="#" style="' + css + '">' + _esc(label) + '</a>';
};

_RENDERERS['Divider'] = function(b) {
  return '<hr class="asw-divider">';
};

_RENDERERS['Video'] = function(b) {
  var poster = b.posterUrl ? ' poster="' + _safeUrl(b.posterUrl) + '"' : '';
  return '<div style="margin:16px 0;"><video controls' + poster + ' style="max-width:100%;border-radius:6px;" src="' + _safeUrl(b.url) + '"></video></div>';
};

_RENDERERS['AudioPlayer'] = function(b) {
  // spec field is `description`; `title` kept for payloads from an older emitter
  var caption = b.description || b.title;
  var title = caption ? '<div style="font-size:0.85rem;color:var(--muted);margin-bottom:4px;">' + _esc(caption) + '</div>' : '';
  return '<div style="margin:16px 0;">' + title + '<audio controls style="width:100%;" src="' + _safeUrl(b.url) + '"></audio></div>';
};

_RENDERERS['Icon'] = function(b) {
  // name: one of the 59 built-in names (atoms_v1_icons.gs, Material Symbols) or {svgPath} on a 24px grid
  var n = b.name, d = '', vb = _A2UI_ICON_VIEWBOX, label = '';
  if (typeof n === 'string' && Object.prototype.hasOwnProperty.call(_A2UI_ICON_PATHS, n)) { d = _A2UI_ICON_PATHS[n]; label = n; }
  else if (n && typeof n === 'object' && typeof n.svgPath === 'string') { d = n.svgPath; vb = '0 0 24 24'; }
  if (!d) return '<span class="asw-icon" title="' + _esc(typeof n === 'string' ? n : 'icon') + '"></span>';
  return '<svg class="asw-icon" viewBox="' + _esc(vb) + '" width="24" height="24" fill="currentColor" role="img" aria-label="' +
         _esc(label || 'icon') + '" style="vertical-align:middle;"><path d="' + _esc(d) + '"/></svg>';
};

// ── Inputs (Basic Catalog) — the decoder records each {path} binding's absolute pointer on
// node._a2uiBind; the surface runtime (A2uiSurfaceRuntime, appended by the decoder when a surface
// has inputs or event buttons) writes edits back into the data model.

var _A2UI_FIELD_CSS = 'width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--border,#d1d5db);border-radius:8px;font:inherit;background:var(--surface,#fff);color:inherit;';
function _a2uiFieldId() { return 'a2f-' + Math.random().toString(36).substr(2, 8); }
function _a2uiBindAttr(b, kind) {
  var p = b._a2uiBind && b._a2uiBind.value;
  return p ? ' data-a2ui-bind="' + _esc(p) + '" data-a2ui-kind="' + kind + '"' : '';
}
function _a2uiLabel(id, text) {
  return text ? '<label for="' + id + '" style="display:block;font-size:.88rem;font-weight:600;margin-bottom:4px;">' + _esc(text) + '</label>' : '';
}

_RENDERERS['TextField'] = function(b) {
  var id = _a2uiFieldId(), v = b.value == null ? '' : String(b.value);
  var variant = ({shortText: 1, longText: 1, number: 1, obscured: 1})[b.variant] ? b.variant : 'shortText';
  var attrs = ' id="' + id + '"' + _a2uiBindAttr(b, variant === 'number' ? 'number' : 'text') +
              (b.placeholder ? ' placeholder="' + _esc(b.placeholder) + '"' : '') + ' style="' + _A2UI_FIELD_CSS + '"';
  var field = variant === 'longText'
    ? '<textarea rows="4"' + attrs + '>' + _esc(v) + '</textarea>'
    : '<input type="' + (variant === 'number' ? 'number' : (variant === 'obscured' ? 'password' : 'text')) + '"' + attrs + ' value="' + _esc(v) + '">';
  return '<div class="asw-v1-field" style="margin:10px 0;">' + _a2uiLabel(id, b.label) + field + '</div>';
};

_RENDERERS['CheckBox'] = function(b) {
  var on = b.value === true || b.value === 'true';
  return '<label class="asw-v1-check" style="display:flex;align-items:center;gap:8px;margin:8px 0;cursor:pointer;">' +
         '<input type="checkbox"' + _a2uiBindAttr(b, 'check') + (on ? ' checked' : '') + '>' + _esc(b.label || '') + '</label>';
};

_RENDERERS['ChoicePicker'] = function(b) {
  var multi = b.variant === 'multipleSelection', group = _a2uiFieldId();
  var sel = Array.isArray(b.value) ? b.value.map(String) : (b.value ? [String(b.value)] : []);
  var chips = b.displayStyle === 'chips';
  var opts = (Array.isArray(b.options) ? b.options : []).map(function(o) {
    var val = String(o && o.value != null ? o.value : ''), on = sel.indexOf(val) >= 0;
    var box = '<input type="' + (multi ? 'checkbox' : 'radio') + '" name="' + group + '" value="' + _esc(val) + '" data-a2ui-kind="choice"' + (on ? ' checked' : '') +
              (chips ? ' style="position:absolute;opacity:0;"' : '') + '>';
    var look = chips ? 'position:relative;padding:6px 12px;border:1px solid var(--border,#d1d5db);border-radius:999px;' : '';
    return '<label style="display:' + (chips ? 'inline-flex' : 'flex') + ';align-items:center;gap:8px;margin:4px 6px 4px 0;cursor:pointer;' + look + '">' + box + _esc(o && o.label != null ? o.label : val) + '</label>';
  }).join('');
  var p = b._a2uiBind && b._a2uiBind.value;
  return '<fieldset class="asw-v1-choice" data-a2ui-group="1"' + (p ? ' data-a2ui-bind="' + _esc(p) + '"' : '') +
         ' style="border:0;padding:0;margin:10px 0;">' + (b.label ? '<legend style="font-size:.88rem;font-weight:600;margin-bottom:4px;">' + _esc(b.label) + '</legend>' : '') +
         '<div style="display:flex;flex-wrap:wrap;flex-direction:' + (chips ? 'row' : 'column') + ';">' + opts + '</div></fieldset>';
};

_RENDERERS['Slider'] = function(b) {
  var id = _a2uiFieldId();
  var lo = isFinite(+b.min) ? +b.min : 0, hi = isFinite(+b.max) ? +b.max : 100;
  var v = isFinite(+b.value) && b.value !== '' ? +b.value : lo;
  var step = (b.steps && +b.steps >= 1) ? (hi - lo) / Math.floor(+b.steps) : 'any';
  return '<div class="asw-v1-field" style="margin:10px 0;"><div style="display:flex;justify-content:space-between;font-size:.88rem;font-weight:600;margin-bottom:4px;">' +
         '<label for="' + id + '">' + _esc(b.label || '') + '</label><output data-a2ui-out="' + id + '">' + _esc(String(v)) + '</output></div>' +
         '<input type="range" id="' + id + '" min="' + lo + '" max="' + hi + '" step="' + step + '" value="' + v + '"' + _a2uiBindAttr(b, 'slider') + ' style="width:100%;"></div>';
};

_RENDERERS['DateTimeInput'] = function(b) {
  var id = _a2uiFieldId(), date = b.enableDate === true, time = b.enableTime === true;
  if (!date && !time) date = true;                       // neither flag: a date picker, the common intent
  var type = date && time ? 'datetime-local' : (time ? 'time' : 'date');
  var v = b.value == null ? '' : String(b.value);
  if (type === 'date') v = v.slice(0, 10); else if (type === 'datetime-local') v = v.replace(/:\d\d(\.\d+)?(Z|[+-]\d\d:\d\d)?$/, '').slice(0, 16);
  var lim = function(k) { return b[k] ? ' ' + k + '="' + _esc(String(b[k])) + '"' : ''; };
  return '<div class="asw-v1-field" style="margin:10px 0;">' + _a2uiLabel(id, b.label) +
         '<input type="' + type + '" id="' + id + '" value="' + _esc(v) + '"' + lim('min') + lim('max') + _a2uiBindAttr(b, 'text') + ' style="' + _A2UI_FIELD_CSS + '"></div>';
};

// The runtime for a v1.0 surface with inputs or event buttons. Serialised with toString() into each
// such surface (one per surface), so GAS pages and the MCP Apps bundle run the identical code.
var _A2UI_V1_RUNTIME = function(root, model, sid) {
  function keys(p) { return String(p).split('/').slice(1).map(function(s) { return s.replace(/~1/g, '/').replace(/~0/g, '~'); }); }
  // On a streamed surface the live data model is the surface store's (atoms_v1_decode.gs), so what
  // the user has typed survives the agent sending more components; otherwise the embedded copy.
  function live() { var st = window._A2UI_SURFACES && window._A2UI_SURFACES[sid]; return st && st.dataModel ? st.dataModel : model; }
  function get(p) { var o = live(), k = keys(p); for (var i = 0; i < k.length; i++) { if (o == null) return undefined; o = o[k[i]]; } return o; }
  function set(p, v) {
    var k = keys(p), o = live();
    for (var i = 0; i < k.length - 1; i++) { if (o[k[i]] == null || typeof o[k[i]] !== 'object') o[k[i]] = {}; o = o[k[i]]; }
    if (k.length) o[k[k.length - 1]] = v;
  }
  function onEdit(e) {
    var el = e.target; if (!el || !el.getAttribute) return;
    var group = el.closest ? el.closest('[data-a2ui-group]') : null;
    var holder = group || el, p = holder.getAttribute('data-a2ui-bind');
    if (el.type === 'range') { var out = root.querySelector('[data-a2ui-out="' + el.id + '"]'); if (out) out.textContent = el.value; }
    if (!p) return;
    var kind = el.getAttribute('data-a2ui-kind'), v;
    if (group) { v = []; group.querySelectorAll('input').forEach(function(x) { if (x.checked) v.push(x.value); }); }
    else if (kind === 'check') v = el.checked;
    else if (kind === 'slider') v = Number(el.value);
    else if (kind === 'number') v = el.value === '' ? null : Number(el.value);
    else v = el.value;
    set(p, v);
  }
  function resolve(v) {
    if (Array.isArray(v)) return v.map(resolve);
    if (v && typeof v === 'object') {
      var ks = Object.keys(v);
      if (ks.length === 1 && typeof v.path === 'string') { var r = get(v.path); return r === undefined ? null : r; }
      var o = {}; for (var k in v) o[k] = resolve(v[k]); return o;
    }
    return v;
  }
  root.addEventListener('input', onEdit);
  root.addEventListener('change', onEdit);
  root.addEventListener('click', function(e) {
    var btn = e.target && e.target.closest ? e.target.closest('[data-a2ui-action]') : null;
    if (!btn || !root.contains(btn)) return;
    e.preventDefault();
    var a; try { a = JSON.parse(btn.getAttribute('data-a2ui-action')); } catch (x) { return; }
    var msg = {version: 'v1.0', action: {name: a.name, surfaceId: sid, sourceComponentId: btn.getAttribute('data-a2ui-src') || '',
               timestamp: new Date().toISOString(), context: resolve(a.context || {})}};
    if (a.userMessage !== undefined) msg.action.userMessage = String(resolve(a.userMessage));
    root.dispatchEvent(new CustomEvent('a2ui:action', {bubbles: true, detail: msg}));
    try { if (window.parent && window.parent !== window) window.parent.postMessage({a2uiClientMessage: msg}, '*'); } catch (x) {}
    // In an MCP Apps host the agent that drew the form is in the conversation: hand the action back as a
    // user message (ui/message via the bundle's host bridge), so the model sees the answer and carries on.
    var bridge = window._A2UI_HOST_BRIDGE;
    if (bridge && typeof bridge.sendMessage === 'function' && btn.getAttribute('data-a2ui-sent') !== '1') {
      btn.setAttribute('data-a2ui-sent', '1'); btn.disabled = true;
      bridge.sendMessage(chatText(msg.action)).then(function() { status(btn, 'Sent', false); },
        function(err) { btn.removeAttribute('data-a2ui-sent'); btn.disabled = false; status(btn, (err && err.message) || 'Not sent', true); });
    }
  });
  // The spec's userMessage when the agent gave one; otherwise "Book: name Grace · agree yes · ..."
  function chatText(act) {
    if (act.userMessage) return act.userMessage;
    function show(v) {
      if (v === true) return 'yes'; if (v === false) return 'no';
      if (v == null || v === '') return '(blank)';
      if (Array.isArray(v)) return v.length ? v.map(show).join(', ') : '(none)';
      return typeof v === 'object' ? JSON.stringify(v) : String(v);
    }
    var parts = Object.keys(act.context || {}).map(function(k) { return k + ' ' + show(act.context[k]); });
    var name = String(act.name || 'action');
    return name.charAt(0).toUpperCase() + name.slice(1) + (parts.length ? ': ' + parts.join(' \u00b7 ') : '');
  }
  function status(btn, text, bad) {
    var s = btn.nextElementSibling && btn.nextElementSibling.className === 'a2ui-status' ? btn.nextElementSibling : null;
    if (!s) { s = document.createElement('span'); s.className = 'a2ui-status'; btn.parentNode.insertBefore(s, btn.nextSibling); }
    s.textContent = text; s.style.cssText = 'margin-left:10px;font-size:.85rem;color:' + (bad ? '#b00020' : 'var(--muted,#6b7280)') + ';';
  }
};

_RENDERERS['A2uiSurfaceRuntime'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 8);
  var js = function(v) { return JSON.stringify(v).replace(/</g, '\\u003c'); };
  return '<span id="a2rt-' + uid + '" hidden></span><script>(function(){var m=document.getElementById("a2rt-' + uid +
         '");if(!m)return;(' + _A2UI_V1_RUNTIME.toString() + ')(m.parentNode,' + js(b.model || {}) + ',' + js(String(b.surfaceId || '')) + ');})();<\/script>';
};

// ── Containers — recurse via renderAtoms(b.blocks), matching the existing
// color_section/two_tone_card/split_pane recursion pattern (atom.gs) ──────────

_RENDERERS['Column'] = function(b) {
  return '<div class="asw-v1-column" style="display:flex;flex-direction:column;gap:8px;">' +
         renderAtoms(b.blocks || []) + '</div>';
};

_RENDERERS['Row'] = function(b) {
  var gap = b.gap || '16px';
  return '<div class="asw-v1-row" style="display:flex;flex-direction:row;gap:' + _esc(String(gap)) + ';flex-wrap:wrap;">' +
         renderAtoms(b.blocks || []) + '</div>';
};

_RENDERERS['Card'] = function(b) {
  return '<div class="asw-v1-card" style="border:1px solid var(--border,#e5e7eb);border-radius:12px;border-radius:var(--a2ui-radius,12px);padding:20px;margin:1rem 0;">' +
         renderAtoms(b.blocks || []) + '</div>';
};

_RENDERERS['List'] = function(b) {
  var row = b.direction === 'horizontal';
  var align = ({start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch'})[b.align] || 'stretch';
  return '<div class="asw-v1-list" style="display:flex;flex-direction:' + (row ? 'row' : 'column') + ';align-items:' + align + ';gap:8px;' +
         (row ? 'overflow-x:auto;' : '') + '">' + renderAtoms(b.blocks || []) + '</div>';
};

_RENDERERS['Modal'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 8);
  if (b.trigger && typeof b.trigger === 'object' && b.content && typeof b.content === 'object') {
    // spec v1.0: `trigger` opens a dialog showing `content` (both resolved to nodes by the decoder)
    return '<span class="asw-v1-modal"><span role="button" tabindex="0" style="display:inline-block;cursor:pointer;" ' +
           'onclick="var d=this.nextElementSibling;if(d&&d.showModal)d.showModal();">' + renderAtoms([b.trigger]) + '</span>' +
           '<dialog id="modal-' + uid + '" style="border:1px solid var(--border,#e5e7eb);border-radius:12px;padding:20px;max-width:min(560px,92vw);">' +
           renderAtoms([b.content]) +
           '<form method="dialog" style="text-align:right;margin:12px 0 0;"><button style="font:inherit;padding:6px 14px;border-radius:8px;border:1px solid var(--border,#d1d5db);background:none;cursor:pointer;">Close</button></form>' +
           '</dialog></span>';
  }
  var title = b.title ? '<h3 style="margin-top:0;">' + _esc(b.title) + '</h3>' : '';
  return '<div class="asw-v1-modal" id="modal-' + uid + '">' + title +
         renderAtoms(b.blocks || []) + '</div>';
};

_RENDERERS['Tabs'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 8);
  var tabs = b.tabs || [];
  var nav = tabs.map(function(t, i) {
    return '<button class="asw-v1-tab-btn' + (i === 0 ? ' active' : '') + '" ' +
           'onclick="var p=this.closest(\'.asw-v1-tabs\');p.querySelectorAll(\'.asw-v1-tab-btn\').forEach(function(x){x.classList.remove(\'active\')});' +
           'p.querySelectorAll(\'.asw-v1-tab-panel\').forEach(function(x){x.style.display=\'none\'});' +
           'this.classList.add(\'active\');p.querySelector(\'#tab-' + uid + '-' + i + '\').style.display=\'block\';">' +
           // 2026-08-24: real Tabs entries key on `title`, not `label`
           // (renderers/a2ui_v1.py's own fix, same date). t.label kept
           // as fallback for a stale-bundle rollout window.
           _esc(t.title || t.label || ('Tab ' + (i + 1))) + '</button>';
  }).join('');
  var panels = tabs.map(function(t, i) {
    return '<div class="asw-v1-tab-panel" id="tab-' + uid + '-' + i + '" style="display:' + (i === 0 ? 'block' : 'none') + ';">' +
           renderAtoms(t.blocks || []) + '</div>';
  }).join('');
  return '<div class="asw-v1-tabs" style="margin:1rem 0;">' +
         '<div class="asw-v1-tab-nav" style="display:flex;gap:4px;border-bottom:1px solid var(--border,#e5e7eb);margin-bottom:16px;">' + nav + '</div>' +
         panels + '</div>';
};
