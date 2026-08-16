// atoms_photo_grid.gs — a browsable image grid where each tile is clickable,
// reusing data_table's own click contract: every tile carries data-row-json,
// bound by the SAME _a2uiBindRowClicks A2UIState.html already runs for table
// rows (its selector generalised from `tbody tr[data-row-json]` to plain
// `[data-row-json]` for this atom — see A2UIState.html's own comment at that
// call site). onRowClick's array form (already shipped 2026-08-04 for "select
// a row AND immediately run the action that opens it") is what makes a single
// tile tap both select AND fire a star/vote action in one click — no new
// engine capability, just a new renderer that opts into what already exists.
//
// Live-updating: wired the same way as data_table via `rows` — see this
// file's client-side counterpart, _a2uiUpdatePhotoGrid (A2UIState.html).
//
// Built for Maison's decision-boards feature (star a photo without a
// separate select-then-tap-a-button step), kept generic: any array of
// {id, url, alt, caption, badge, active} objects works, no board/vote
// concept baked into the atom itself.
_RENDERERS['photo_grid'] = function(b) {
  var images = b.images || b.rows || [];
  var cols = b.cols || 3;
  var gid = 'pg' + Math.random().toString(36).substr(2, 6);
  var css = '<style>' +
    '.' + gid + '{display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:12px;margin:12px 0;}' +
    '@media(max-width:600px){.' + gid + '{grid-template-columns:repeat(2,1fr);}}' +
    '.' + gid + ' figure{position:relative;margin:0;overflow:hidden;border-radius:8px;cursor:pointer;aspect-ratio:4/5;background:#f1f3f4;border:2px solid transparent;transition:border-color 0.15s;}' +
    '.' + gid + ' figure.pg-active{border-color:#0f766e;}' +
    '.' + gid + ' figure img{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.2s ease;}' +
    '.' + gid + ' figure:hover img{transform:scale(1.04);}' +
    '.' + gid + ' figcaption{position:absolute;bottom:0;left:0;right:0;padding:6px 8px;background:linear-gradient(transparent,rgba(0,0,0,0.72));color:#fff;font-size:0.72rem;line-height:1.3;}' +
    '.' + gid + ' .pg-badge{position:absolute;top:6px;right:6px;background:rgba(0,0,0,0.65);color:#fff;font-size:0.72rem;font-weight:700;padding:2px 7px;border-radius:99px;}' +
    '.' + gid + ' .pg-badge-active{background:#f59e0b;color:#1c1108;}' +
    '</style>';
  return css + '<div class="' + gid + '" data-photo-grid="1">' + _a2uiPhotoGridItemsHtml(images) + '</div>';
};

// Shared by the GAS-side renderer above only — A2UIState.html's client-side
// live-update path (_a2uiUpdatePhotoGrid) has its own copy using
// _a2uiSanitize rather than _esc, same duplication data_table_sortable and
// _a2uiUpdateTableRows already carry between the two environments.
function _a2uiPhotoGridItemsHtml(images) {
  return images.map(function(img) {
    var rowJson = _esc(JSON.stringify(img));
    var activeCls = img.active ? ' pg-active' : '';
    var badge = img.badge ? '<span class="pg-badge' + (img.active ? ' pg-badge-active' : '') +
      '">' + _esc(img.badge) + '</span>' : '';
    var cap = img.caption ? '<figcaption>' + _esc(img.caption) + '</figcaption>' : '';
    return '<figure class="' + activeCls + '" data-row-json="' + rowJson + '">' +
      '<img src="' + _esc(img.url || '') + '" alt="' + _esc(img.alt || '') + '" loading="lazy">' +
      badge + cap + '</figure>';
  }).join('');
}
