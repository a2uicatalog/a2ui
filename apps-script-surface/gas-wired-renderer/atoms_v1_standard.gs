/**
 * atoms_v1_standard.gs — renderers for the ~12 A2UI v1.0 "basic catalog" primitive
 * component names (Text/Image/Button/Divider/Video/AudioPlayer/Icon/Column/Row/
 * Card/Tabs/Modal). These are the names renderers/a2ui_v1.py's STANDARD_MAP and
 * _child_blocklists emit for the ~78 common atoms it maps to a standard shape —
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
  var alt = b.alt ? ' alt="' + _esc(b.alt) + '"' : '';
  return '<div style="margin:16px 0;text-align:center;">' +
         '<img src="' + _esc(b.url) + '"' + alt + ' style="max-width:100%;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">' +
         '</div>';
};

_RENDERERS['Button'] = function(b) {
  var url = (b.action && b.action.event && b.action.event.context && b.action.event.context.url) || '#';
  return '<a class="asw-button" href="' + _safeUrl(url) + '" style="display:inline-block;padding:10px 20px;border-radius:8px;background:var(--a2ui-accent,#6366f1);color:#fff;text-decoration:none;margin:8px 0;">' +
         _esc(b.label || 'Button') + '</a>';
};

_RENDERERS['Divider'] = function(b) {
  return '<hr class="asw-divider">';
};

_RENDERERS['Video'] = function(b) {
  return '<div style="margin:16px 0;"><video controls style="max-width:100%;border-radius:6px;" src="' + _esc(b.url) + '"></video></div>';
};

_RENDERERS['AudioPlayer'] = function(b) {
  var title = b.title ? '<div style="font-size:0.85rem;color:var(--muted);margin-bottom:4px;">' + _esc(b.title) + '</div>' : '';
  return '<div style="margin:16px 0;">' + title + '<audio controls style="width:100%;" src="' + _esc(b.url) + '"></audio></div>';
};

_RENDERERS['Icon'] = function(b) {
  return '<span class="asw-icon" data-icon="' + _esc(b.name || '') + '"></span>';
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
  return '<div class="asw-v1-card" style="border:1px solid var(--border,#e5e7eb);border-radius:12px;padding:20px;margin:1rem 0;">' +
         renderAtoms(b.blocks || []) + '</div>';
};

_RENDERERS['Modal'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 8);
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
           _esc(t.label || ('Tab ' + (i + 1))) + '</button>';
  }).join('');
  var panels = tabs.map(function(t, i) {
    return '<div class="asw-v1-tab-panel" id="tab-' + uid + '-' + i + '" style="display:' + (i === 0 ? 'block' : 'none') + ';">' +
           renderAtoms(t.blocks || []) + '</div>';
  }).join('');
  return '<div class="asw-v1-tabs" style="margin:1rem 0;">' +
         '<div class="asw-v1-tab-nav" style="display:flex;gap:4px;border-bottom:1px solid var(--border,#e5e7eb);margin-bottom:16px;">' + nav + '</div>' +
         panels + '</div>';
};
