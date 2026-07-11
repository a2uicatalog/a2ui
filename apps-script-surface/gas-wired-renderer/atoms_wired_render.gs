// atoms_wired_render.gs — the wired dialect's layout->HTML loop, extracted from
// Code.gs as a PURE function (spec/wired-transport-v0.1.md, a2ui-private —
// same move as atoms_v1_decode.gs): GAS keeps behavior by delegation, the MCP
// Apps bundle gets the SAME renderer by concatenation. No HtmlService, no GAS
// services — Node-testable. Returns the content HTML only; the caller owns
// the page shell (GAS: AtomPage template + A2UIState include; view: paint()).

var _WIRED_ATOM_ALIASES = {
  'text_input': 'form_input',
  'number_input': 'form_input',   // numeric variant travels via block.input_type (G3)
  'data_table': 'data_table_sortable'
};

function _resolveInitialRows(wireExpr, statePrimitives) {
  if (!wireExpr || !wireExpr.startsWith('#')) return null;
  var dot    = wireExpr.indexOf('.');
  var nodeId = wireExpr.slice(1, dot);
  for (var i = 0; i < statePrimitives.length; i++) {
    var p = statePrimitives[i];
    if (p.id !== nodeId) continue;
    if (p.primitive === 'ArrayFilter' && p.props && Array.isArray(p.props.source)) return p.props.source;
    if (p.primitive === 'ValueStore'  && p.props && Array.isArray(p.props.initialValue)) return p.props.initialValue;
  }
  return null;
}

var _A2UI_VARIANT = '';


function _a2uiRenderWiredLayout(payload) {
  var theme      = payload.theme || 'light';
  var layout     = payload.layout || [];
  var primitives = payload.state_primitives || [];
  var content    = '';

  layout.forEach(function(el) {
    var rawType = el.atom || el.type;
    // Layout structure primitives — not atoms, just HTML wrappers
    if (rawType === 'row_open') {
      var p = el.props || {};
      content += '<div style="display:flex;gap:' + (p.gap || '24px') + ';align-items:' + (p.align || 'stretch') + ';' + (p.style || '') + '">';
      return;
    }
    if (rawType === 'row_close') { content += '</div>'; return; }
    // group_open/group_close: styled container that RESPECTS step visibility —
    // section cards / per-round panels spanning several layout elements
    // (row_open ignores step by design; added 2026-07-10 for the americano app).
    if (rawType === 'group_open') {
      var gp = el.props || {};
      var gStep = (el.step !== undefined) ? ' data-a2ui-step="' + el.step + '"' : '';
      var gHide = (el.step !== undefined && el.step !== 0) ? 'display:none;' : '';
      content += '<div' + gStep + ' style="' + gHide + (gp.style || '') + '">';
      return;
    }
    if (rawType === 'group_close') { content += '</div>'; return; }

    var props = el.props || {};
    var block = {};
    Object.keys(props).forEach(function(k) { block[k] = props[k]; });
    block.type      = _WIRED_ATOM_ALIASES[rawType] || rawType;
    block.component = el.component;
    if (rawType === 'number_input' && !block.input_type) block.input_type = 'number';

    if (Array.isArray(block.columns)) {
      block.columns = block.columns.map(function(c) {
        if (typeof c === 'string') {
          return { key: c, label: c.charAt(0).toUpperCase() + c.slice(1).replace(/_/g, ' ') };
        }
        return c;
      });
    }

    if (el.wire && el.wire.rows && !block.rows) {
      var initRows = _resolveInitialRows(el.wire.rows, primitives);
      if (initRows) block.rows = initRows;
    }

    var atomHtml = renderAtoms([block], { theme: theme });

    if (el.id) {
      var stepAttr  = (el.step !== undefined) ? ' data-a2ui-step="' + el.step + '"' : '';
      var stepStyle = (el.step !== undefined && el.step !== 0) ? 'display:none;' : '';
      var csStyle   = el.container_style ? el.container_style : '';
      var combinedStyle = (stepStyle + csStyle) ? ' style="' + (stepStyle + csStyle).replace(/"/g, "'") + '"' : '';
      var colsAttr  = block.columns
        ? ' data-a2ui-columns="' + JSON.stringify(block.columns).replace(/"/g, '&quot;') + '"'
        : '';
      var emptyAttr = block.emptyMessage
        ? ' data-a2ui-empty="' + String(block.emptyMessage).replace(/"/g, '&quot;') + '"'
        : '';
      content += '<div id="a2ui-' + el.id + '"' + stepAttr + combinedStyle + colsAttr + emptyAttr + '>' + atomHtml + '</div>';
    } else {
      content += atomHtml;
    }
  });

  return content;
}
