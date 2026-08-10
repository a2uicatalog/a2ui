// ── layer_stack / stack_layer ────────────────────────────────────────────────
// Declarative labelled layers for a layered architecture — a protocol stack, a
// request path, any "what lives at which level" picture.
//
// Keeps primitive_plate's labelling pairing (`field` = the mono technical fact,
// `note` = the plain-language gloss) and drops its image substrate: a
// primitive_plate pin annotates a REAL capture and must never annotate a
// hand-drawn illustration, and an abstract stack has no capture to pin.
//
// Two things this does that concept_ladder can't. `columns` renders each layer's
// `cells` side by side, so ONE stack carries a per-layer comparison of two
// systems (the case that prompted the atom: MCP declares a session and no
// document model; A2UI declares a document model and no session contract). And
// `status: absent` renders a visibly hollow, dashed band, so a layer a system
// does not define reads as a STATED absence rather than an omission.
//
// Port of renderers/web_article.py's _render_layer_stack/_render_stack_layer
// (the reference implementation). Every helper this needs — _journeyPalette,
// _journeyFontCss, _journeyMdCode, _JOURNEY_MONO/_SERIF, _JOURNEY_PALETTE_LIGHT,
// _esc — already lives in atom.gs; _journeySourceBar comes from atoms_concept.gs
// (one global scope, resolved at render time, so file order doesn't matter).
//
// Why this file exists at all: EVERY render path except the blog pipeline
// compiles from these .gs sources — GAS ?p= URLs, the MCP Apps bundle
// (gen_mcp_apps_bundle.py globs atom.gs + atoms_*.gs) and the Worker's
// /api/render (gen_worker_renderers.py). Python-only would mean a URL that
// renders nothing.

// status -> [strong token, soft token] in the journey palette
var _LAYER_STATUS_TOKENS = {
  present: ['cleared', 'cleared_soft'],
  absent: ['blocked', 'blocked_soft'],
  partial: ['accent', 'accent_soft']
};

function _layerStatus(value) {
  var v = String(value == null ? 'present' : value).trim().toLowerCase();
  return _LAYER_STATUS_TOKENS.hasOwnProperty(v) ? v : 'present';
}

// `cleared_soft` -> `var(--cleared-soft,<light default>)`
function _layerToken(name) {
  return 'var(--' + name.replace(/_/g, '-') + ',' + _JOURNEY_PALETTE_LIGHT[name] + ')';
}

// One field/note pane — the whole band when there are no columns, one column of
// it when there are.
function _layerCellHtml(cell, stretch, label) {
  var status = _layerStatus(cell.status);
  var strong = _LAYER_STATUS_TOKENS[status][0];
  var soft = _LAYER_STATUS_TOKENS[status][1];
  var absent = (status === 'absent');
  var field = String(cell.field == null ? '' : cell.field).trim();
  var note = String(cell.note == null ? '' : cell.note).trim();

  var inner = '';
  // The column header sits once at the top of the stack, which is a long way up
  // by the time you are reading the bottom band — so each pane repeats its
  // column quietly. Colour can't carry this instead: the fill already encodes
  // `status`, and a second colour encoding on the same mark makes both
  // ambiguous. It also keeps a band self-describing when rendered ALONE, which
  // stack_layer's own ComponentId addressability invites.
  // Set as a PILL, not just smaller text: it shares a bubble with `field`, and
  // both are mono uppercase, so weight alone leaves the tag reading as content.
  // Differentiate by form. The recipe is the band's existing `examples` chip
  // (paper fill, line border, full radius) so the tag rhymes with vocabulary
  // already on screen rather than introducing a new one — and staying small
  // keeps it from competing with `field`, which is the actual content.
  if (label) {
    inner += '<div style="margin-bottom:0.45rem;">'
      + '<span style="display:inline-block;font-family:' + _JOURNEY_MONO + ';font-size:0.6rem;'
      + 'font-weight:700;letter-spacing:0.1em;text-transform:uppercase;line-height:1;'
      + 'padding:0.32em 0.65em;border-radius:999px;background:' + _layerToken('paper') + ';'
      + 'border:1px solid ' + _layerToken('line') + ';color:' + _layerToken('ink_soft') + ';">'
      + _esc(label) + '</span></div>';
  }
  if (field) {
    inner += '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.78rem;line-height:1.45;'
      + 'font-weight:600;color:' + _layerToken(strong) + ';word-break:break-word;">'
      + _esc(field) + '</div>';
  }
  if (note) {
    inner += '<div style="font-size:0.88rem;line-height:1.55;max-width:46ch;'
      + 'color:' + _layerToken(absent ? 'ink_soft' : 'ink') + ';'
      + 'margin-top:' + (field ? '0.35rem' : '0') + ';">' + _journeyMdCode(note) + '</div>';
  }
  if (!field && !note) {
    // An absent layer with nothing to say still has to occupy its slot — a blank
    // cell reads as "not filled in", an em-dash as "nothing here".
    inner += '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.9rem;'
      + 'color:' + _layerToken('ink_soft') + ';">&mdash;</div>';
  }

  return '<div style="background:' + (absent ? 'transparent' : _layerToken(soft)) + ';'
    + 'border:1px ' + (absent ? 'dashed' : 'solid') + ' ' + _layerToken(strong) + ';'
    + 'border-radius:8px;padding:0.7rem 0.85rem;min-width:0;'
    + (stretch ? 'grid-column:2 / -1;' : '')
    + '">' + inner + '</div>';
}

// One band of a layer_stack. Renders standalone (no column headers) so it stays
// independently addressable by ComponentId.
_RENDERERS['stack_layer'] = function(b) {
  var status = _layerStatus(b.status);
  var strong = _LAYER_STATUS_TOKENS[status][0];
  var name = String(b.name == null ? '' : b.name).trim();
  var badge = String(b.badge == null ? '' : b.badge).trim();

  var cells = [];
  var raw = b.cells || [];
  for (var i = 0; i < raw.length; i++) {
    if (raw[i] && typeof raw[i] === 'object') cells.push(raw[i]);
  }
  if (!cells.length) {
    // Single-column band — the layer's own field/note IS the one cell.
    cells = [{ field: b.field, note: b.note, status: status }];
  }

  // `_columns` is injected by layer_stack onto its own copy of the layer (never
  // authored, never read off the payload the caller passed in). It carries the
  // stack's column count down so a layer with FEWER cells than there are
  // columns — the "this level applies to everything" band, e.g. one shared
  // observation under a two-system comparison — spans the full width and stays
  // aligned with the column headers, instead of hiding under column one.
  var span = parseInt(b._columns, 10) || cells.length;
  if (span < cells.length) span = cells.length;
  var stretch = (cells.length === 1 && span > 1);
  // Injected alongside `_columns`. Repeats are pointless with one column, and
  // wrong on a stretched band (it spans them all, so it belongs to none).
  var labels = (span > 1 && !stretch) ? (b._column_labels || []) : [];

  var nameCol = '<div style="display:flex;flex-direction:column;gap:0.3rem;'
    + 'padding-top:0.15rem;min-width:0;">'
    + (badge ? '<span style="font-family:' + _JOURNEY_MONO + ';font-size:0.62rem;font-weight:700;'
       + 'letter-spacing:0.09em;color:' + _layerToken('ink_soft') + ';">' + _esc(badge) + '</span>' : '')
    + (name ? '<span style="font-family:' + _JOURNEY_MONO + ';font-weight:600;font-size:0.92rem;'
       + 'line-height:1.3;color:' + _layerToken('ink') + ';word-break:break-word;">'
       + _journeyMdCode(name) + '</span>' : '')
    + '</div>';

  var examplesHtml = '';
  var examples = b.examples || [];
  var chips = '';
  for (var e = 0; e < examples.length; e++) {
    var ex = String(examples[e]);
    if (!ex.trim()) continue;
    chips += '<span style="font-family:' + _JOURNEY_MONO + ';font-size:0.7rem;line-height:1;'
      + 'padding:0.32em 0.6em;border-radius:999px;background:' + _layerToken('paper') + ';'
      + 'border:1px solid ' + _layerToken('line') + ';color:' + _layerToken('ink_soft') + ';'
      + 'white-space:nowrap;">' + _esc(ex) + '</span>';
  }
  if (chips) {
    examplesHtml = '<div style="display:flex;flex-wrap:wrap;gap:0.35rem;margin-top:0.6rem;'
      + 'padding-left:0.15rem;">' + chips + '</div>';
  }

  var cellsHtml = '';
  for (var c = 0; c < cells.length; c++) {
    cellsHtml += _layerCellHtml(cells[c], stretch, (c < labels.length) ? labels[c] : '');
  }

  return '<div style="background:' + _layerToken('paper_raised') + ';'
    + 'border:1px solid ' + _layerToken('line') + ';'
    + 'border-left:3px solid ' + _layerToken(strong) + ';border-radius:10px;'
    + 'padding:0.85rem 1rem;">'
    + '<div style="display:grid;grid-template-columns:minmax(6rem,9rem) repeat(' + span
    + ',minmax(0,1fr));gap:0.75rem;align-items:start;">'
    + nameCol + cellsHtml
    + '</div>'
    + examplesHtml
    + '</div>';
};

_RENDERERS['layer_stack'] = function(b) {
  var pal = _journeyPalette(b);
  var cssVars = '';
  for (var k in pal) {
    if (!pal.hasOwnProperty(k)) continue;
    cssVars += (cssVars ? ';' : '') + '--' + k.replace(/_/g, '-') + ':' + pal[k];
  }

  var layers = [];
  var rawLayers = b.layers || [];
  for (var i = 0; i < rawLayers.length; i++) {
    if (rawLayers[i] && typeof rawLayers[i] === 'object') layers.push(rawLayers[i]);
  }
  var columns = [];
  var rawCols = b.columns || [];
  for (var j = 0; j < rawCols.length; j++) {
    if (rawCols[j] && typeof rawCols[j] === 'object') columns.push(rawCols[j]);
  }

  var order = String(b.order || 'bottom_up').trim().toLowerCase();
  if (order !== 'bottom_up' && order !== 'top_down') order = 'bottom_up';

  var eyebrow = _esc(b.eyebrow || '');
  var title = _esc(b.title || '');
  var dek = _esc(b.dek || '');
  var caption = b.caption ? _journeyMdCode(b.caption) : '';

  // Badge defaults follow the AUTHORED order, so in a bottom_up stack the
  // first-declared (bottom) layer is 1 — which is how you'd say it aloud.
  var prepared = [];
  var ncols = 0;
  for (var p = 0; p < layers.length; p++) {
    var d = {};
    for (var key in layers[p]) {
      if (layers[p].hasOwnProperty(key)) d[key] = layers[p][key];
    }
    if (d.badge === undefined || d.badge === null || d.badge === '') d.badge = String(p + 1);
    prepared.push({ index: p, layer: d });
    var n = (d.cells || []).length;
    if (n > ncols) ncols = n;
  }
  if (columns.length > ncols) ncols = columns.length;
  if (!ncols) ncols = 1;
  var colLabels = [];
  for (var cl = 0; cl < ncols; cl++) {
    var cdef = (cl < columns.length) ? columns[cl] : {};
    colLabels.push(String(cdef.label == null ? '' : cdef.label));
  }
  for (var q = 0; q < prepared.length; q++) {
    // parent-injected; see stack_layer
    prepared[q].layer._columns = ncols;
    prepared[q].layer._column_labels = colLabels;
  }

  var visual = prepared.slice();
  if (order === 'bottom_up') visual.reverse();

  var gridCols = 'minmax(6rem,9rem) repeat(' + ncols + ',minmax(0,1fr))';

  var headerHtml = '';
  if (columns.length) {
    var heads = '';
    for (var h = 0; h < ncols; h++) {
      var col = (h < columns.length) ? columns[h] : {};
      var accent = String(col.accent == null ? '' : col.accent).trim();
      var colour = accent ? _esc(accent) : _layerToken('accent');
      heads += '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.68rem;font-weight:700;'
        + 'letter-spacing:0.09em;text-transform:uppercase;color:' + colour + ';'
        + 'padding:0 0.85rem 0.15rem;border-bottom:2px solid ' + colour + ';">'
        + _esc(col.label || '') + '</div>';
    }
    headerHtml = '<div style="display:grid;grid-template-columns:' + gridCols + ';gap:0.75rem;'
      + 'align-items:end;margin-bottom:0.6rem;"><div></div>' + heads + '</div>';
  }

  function axis(text) {
    return '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.64rem;font-weight:700;'
      + 'letter-spacing:0.1em;text-transform:uppercase;color:' + _layerToken('ink_soft') + ';'
      + 'display:flex;align-items:center;gap:0.6em;margin:0.55rem 0;">'
      + '<span style="height:1.5px;width:1.4em;background:' + _layerToken('line') + ';'
      + 'display:inline-block;"></span>' + _esc(text) + '</div>';
  }

  var bands = '';
  for (var v = 0; v < visual.length; v++) {
    var layer = visual[v].layer;
    var fn = _RENDERERS[layer.component || layer.type] || _RENDERERS['stack_layer'];
    var componentId = _esc(layer.id || ('layer-' + (visual[v].index + 1)));
    bands += '<div data-component-id="' + componentId + '" style="scroll-margin-top:1.5rem;">'
      + fn(layer) + '</div>';
  }

  var stackInner = headerHtml
    + (b.top_label ? axis(b.top_label) : '')
    + '<div style="display:flex;flex-direction:column;gap:0.5rem;">' + bands + '</div>'
    + (b.base_label ? axis(b.base_label) : '');

  // Multi-column bands cannot compress below a readable width — let the stack
  // scroll inside its own box rather than force the page to scroll sideways.
  if (ncols > 1) {
    stackInner = '<div style="overflow-x:auto;"><div style="min-width:' + (9 + ncols * 11) + 'rem;">'
      + stackInner + '</div></div>';
  }

  var fontCss = (b.use_plex_fonts !== false) ? _journeyFontCss() : '';

  return fontCss
    + '<div style="' + cssVars + ';font-family:' + _JOURNEY_SERIF + ';background:var(--paper);'
    + 'color:var(--ink);padding:clamp(1.4rem,4vw,2.2rem);border-radius:14px;'
    + 'border:1px solid var(--line);">'
    // Attribution before everything, headline included — see _journeySourceBar.
    + _journeySourceBar(b)
    + (eyebrow ? '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.72rem;font-weight:600;'
       + 'letter-spacing:0.09em;text-transform:uppercase;color:var(--ink-soft);display:flex;'
       + 'align-items:center;gap:0.6em;margin-bottom:1rem;"><span style="width:1.5em;height:1.5px;'
       + 'background:var(--accent);display:inline-block;"></span>' + eyebrow + '</div>' : '')
    + (title ? '<h2 style="font-family:' + _JOURNEY_MONO + ';font-weight:600;'
       + 'font-size:clamp(1.4rem,3.6vw,1.9rem);line-height:1.2;margin:0 0 0.7rem;'
       + 'color:var(--ink);">' + title + '</h2>' : '')
    + (dek ? '<p style="font-style:italic;color:var(--ink-soft);font-size:1.05rem;max-width:46ch;'
       + 'margin:0 0 1.1rem;">' + dek + '</p>' : '')
    + (caption ? '<p style="margin:0 0 1.3rem;max-width:58ch;line-height:1.6;color:var(--ink);">'
       + caption + '</p>' : '')
    + stackInner
    + '</div>';
};
