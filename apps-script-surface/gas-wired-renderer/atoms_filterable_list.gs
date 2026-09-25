// atoms_filterable_list.gs — a list whose rows carry a status/category and a chip row that ACTUALLY filters them.
//
// Why this exists (found 2026-09-25 by giving Haiku the article's T4 brief, "a list of eight items ... filterable by status"):
// chip_group is a static row of labels and links, entity_list is a static list, and nothing in the catalogue connected the
// two, so the closest a model could build was a list with decorative "filter" pills. The answer key accepted that as a filter
// control, so the atom-choice score read fine while the surface did not do what the brief asked.
//
// Self-contained on purpose. A chip that filters ANOTHER atom needs shared state between atoms, which chat, email and PDF
// surfaces cannot provide; one atom that owns both its chips and its rows works wherever this renderer's JS runs, and on a
// static surface it degrades to the full list (every row visible, chips inert) instead of a broken filter.
//
// Same inline-script pattern as tab_group, with one deliberate difference: NO user data is ever spliced into the script.
// Row values travel as escaped data-fv attributes and the script only reads them, so a status like `"});alert(1);//` is text.
// Chip colours come from a scoped CSS custom property, so filtering never touches inline colours.
_RENDERERS['filterable_list'] = function(b) {
  var uid = 'fl' + Math.random().toString(36).substr(2, 6);
  var items = Array.isArray(b.items) ? b.items : [];
  var field = (typeof b.filter_field === 'string' && /^[A-Za-z_]{1,32}$/.test(b.filter_field)) ? b.filter_field : 'status';
  var showCounts = b.show_counts !== false;
  var PALETTE = ['#4f46e5', '#059669', '#d97706', '#dc2626', '#0891b2', '#7c3aed', '#db2777', '#65a30d'];
  function hex(c) { return (typeof c === 'string' && /^#[0-9a-fA-F]{3,8}$/.test(c)) ? c : ''; }
  function key(v) { return String(v === undefined || v === null ? '' : v).trim().toLowerCase(); }
  function title(it) { return it.title !== undefined ? it.title : (it.name !== undefined ? it.name : ''); }
  function detail(it) { return it.detail !== undefined ? it.detail : (it.subtitle !== undefined ? it.subtitle : ''); }

  // Filters: explicit [{value, label?, color?}] (or plain strings), else every distinct value in first-seen order.
  var filters = [], seen = {};
  var explicit = Array.isArray(b.filters) ? b.filters : null;
  if (explicit) {
    explicit.forEach(function(f) {
      var v = (f && typeof f === 'object') ? f.value : f;
      var k = key(v);
      if (!k || seen[k]) return;
      seen[k] = true;
      filters.push({ key: k, label: (f && typeof f === 'object' && f.label) ? f.label : String(v), color: (f && typeof f === 'object') ? hex(f.color) : '' });
    });
  } else {
    items.forEach(function(it) {
      var k = key(it[field]);
      if (!k || seen[k]) return;
      seen[k] = true;
      filters.push({ key: k, label: String(it[field]).trim(), color: '' });
    });
  }
  var colours = (b.colors && typeof b.colors === 'object') ? b.colors : {};
  filters.forEach(function(f, i) { f.color = f.color || hex(colours[f.label]) || hex(colours[f.key]) || PALETTE[i % PALETTE.length]; });
  var colourOf = {};
  filters.forEach(function(f) { colourOf[f.key] = f.color; });
  var counts = {};
  items.forEach(function(it) { var k = key(it[field]); counts[k] = (counts[k] || 0) + 1; });

  var chips = '<button type="button" class="fl-chip" data-fv="" aria-pressed="true" style="--c:#374151">All' +
    (showCounts ? ' <span class="fl-n">' + items.length + '</span>' : '') + '</button>' +
    filters.map(function(f) {
      return '<button type="button" class="fl-chip" data-fv="' + _esc(f.key) + '" aria-pressed="false" style="--c:' + _esc(f.color) + '">' +
        _esc(f.label) + (showCounts ? ' <span class="fl-n">' + (counts[f.key] || 0) + '</span>' : '') + '</button>';
    }).join('');

  var rows = items.map(function(it) {
    var k = key(it[field]);
    var c = colourOf[k] || '#9ca3af';
    var value = (it[field] !== undefined && it[field] !== null && String(it[field]).trim()) ? String(it[field]).trim() : '';
    var badge = (field === 'status' || value) && value
      ? '<span class="fl-badge" style="--c:' + _esc(c) + '">' + _esc(value) + '</span>' : '';
    return '<div class="fl-row" data-fv="' + _esc(k) + '">' +
      (it.icon ? '<span class="fl-ic" aria-hidden="true">' + _esc(it.icon) + '</span>' : '') +
      '<div class="fl-main"><div class="fl-t">' + _esc(title(it)) + '</div>' +
      (detail(it) ? '<div class="fl-d">' + _esc(detail(it)) + '</div>' : '') + '</div>' +
      (it.meta ? '<span class="fl-meta">' + _esc(it.meta) + '</span>' : '') + badge + '</div>';
  }).join('');

  var css = '<style>' +
    '#' + uid + ' .fl-bar{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px;}' +
    '#' + uid + ' .fl-chip{font:inherit;font-size:13px;font-weight:600;cursor:pointer;padding:5px 14px;border-radius:999px;' +
      'border:1.5px solid var(--c);background:transparent;color:var(--c);}' +
    '#' + uid + ' .fl-chip[aria-pressed="true"]{background:var(--c);color:#fff;}' +
    '#' + uid + ' .fl-n{opacity:.75;font-weight:500;margin-left:2px;}' +
    '#' + uid + ' .fl-row{display:flex;align-items:center;gap:12px;padding:10px 12px;border:1px solid var(--border,#e0e0e0);' +
      'border-radius:10px;margin-bottom:8px;background:var(--surface,#f8f9fa);color:var(--text,#202124);}' +
    '#' + uid + ' .fl-main{flex:1;min-width:0;}' +
    '#' + uid + ' .fl-t{font-weight:600;}' +
    '#' + uid + ' .fl-d{font-size:13px;color:var(--muted,#5f6368);margin-top:2px;}' +
    '#' + uid + ' .fl-meta{font-size:12px;color:var(--muted,#5f6368);white-space:nowrap;}' +
    '#' + uid + ' .fl-badge{font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;background:var(--c);color:#fff;white-space:nowrap;}' +
    '#' + uid + ' .fl-count,#' + uid + ' .fl-empty{font-size:12px;color:var(--muted,#5f6368);margin:6px 0;}' +
    '#' + uid + ' .fl-empty{display:none;}' +
    '</style>';

  // Only the generated uid is spliced into the script; every value the script reads comes from data-fv attributes.
  var script = '<script>(function(){var root=document.getElementById("' + uid + '");if(!root)return;' +
    'var chips=root.querySelectorAll(".fl-chip"),rows=root.querySelectorAll(".fl-row"),' +
    'count=root.querySelector(".fl-count"),empty=root.querySelector(".fl-empty"),total=rows.length;' +
    'function apply(v){var shown=0;' +
    'for(var i=0;i<rows.length;i++){var on=(v===""||rows[i].getAttribute("data-fv")===v);rows[i].style.display=on?"":"none";if(on)shown++;}' +
    'for(var j=0;j<chips.length;j++){chips[j].setAttribute("aria-pressed",chips[j].getAttribute("data-fv")===v?"true":"false");}' +
    'if(count)count.textContent="Showing "+shown+" of "+total;if(empty)empty.style.display=shown?"none":"block";}' +
    'for(var k=0;k<chips.length;k++){(function(c){c.addEventListener("click",function(){apply(c.getAttribute("data-fv"));});})(chips[k]);}' +
    '})();<\/script>';

  return css + '<div id="' + uid + '" class="fl-wrap" style="margin:0.75rem 0;">' +
    (b.title ? '<div style="font-size:16px;font-weight:700;margin-bottom:10px;color:var(--text,#202124);">' + _esc(b.title) + '</div>' : '') +
    '<div class="fl-bar" role="group" aria-label="Filter">' + chips + '</div>' +
    '<div class="fl-count" aria-live="polite">Showing ' + items.length + ' of ' + items.length + '</div>' +
    '<div class="fl-list">' + rows + '</div>' +
    '<div class="fl-empty">' + _esc(b.empty_text || 'Nothing matches this filter.') + '</div>' +
    '</div>' + script;
};
