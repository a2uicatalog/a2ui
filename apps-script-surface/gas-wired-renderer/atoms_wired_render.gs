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

  // DECLARED fullscreen, same contract the canvas atoms use (height:
  // 'fullscreen' on airspace_command_deck — the payload shape Curtis confirmed
  // working in BOTH Claude and ChatGPT on 2026-08-01). Requesting the display
  // mode from the host only changes the FRAME; without this the content stays
  // inside .asw-page's 860px max-width and padding, which is why asking alone
  // looked like nothing happened.
  //
  // DELIBERATELY NOT 100vh, and deliberately not overflow:hidden — that pair is
  // the documented trap (atoms_airspace.gs): a display-mode grant is a REQUEST,
  // and when a host refuses it (ChatGPT renders in a fixed embedded panel) a
  // 100vh canvas sizes to the HOST viewport instead of the panel and paints its
  // content off-screen. That presented as "no plane data" and cost a day. A
  // document or a form needs the WIDTH escape, not a viewport-height canvas, so
  // taking only the half that cannot misfire is the whole point: if the grant
  // never comes, this degrades to a slightly wider column and nothing is lost.
  var fsBreakout = (payload.fullscreen === true || payload.height === 'fullscreen')
    ? '<style>.asw-page{max-width:none!important;padding:24px 32px!important;'
      + 'margin:0!important;}</style>'
    : '';

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
    // gate_open/gate_close: the pause before an irreversible action — a frame
    // and a question, wrapped around the ordinary buttons that answer it.
    //
    // FLAT, and here that is the whole design rather than a convention. The
    // buttons inside carry the wires that do the work, and each one binds
    // through the SAME `onClick` every other button uses because each is its
    // own top-level layout element. Putting them inside a single atom instead
    // was tried and rejected on 2026-08-14: one element holding two buttons
    // makes `querySelector('button')` ambiguous, which needs new wire props to
    // disambiguate — a permanent addition to the engine's vocabulary, solving
    // a problem that only exists because the buttons were grouped. Same reason
    // row_open above is flat.
    //
    // What the wrapper still buys, and composition alone does not: the pairing
    // is checkable. A gate_open whose span contains fewer than two wired
    // buttons is a gate the reader cannot decline, and that is decidable from
    // the payload (see wirecheck in consuming apps).
    if (rawType === 'gate_open') {
      var kp = el.props || {};
      var kTone = kp.tone === 'danger' ? '#b91c1c' : 'var(--accent,#0f766e)';
      // decision_id names what is being decided. In the durable tier it is a
      // record parked server-side; see spec/durable-pause-v0.1.md.
      var kId = kp.decision_id
        ? ' data-decision-id="' + _esc(String(kp.decision_id)) + '"' : '';
      content += '<div class="a2ui-gate"' + kId + ' style="border:1px solid ' + kTone +
        ';border-radius:10px;padding:14px;margin-bottom:12px;' + (kp.style || '') + '">' +
        (kp.prompt ? '<div style="font-size:15px;font-weight:600;color:var(--text,#374151);' +
          'margin-bottom:' + (kp.detail ? '4px' : '10px') + ';">' + _esc(kp.prompt) + '</div>' : '') +
        (kp.detail ? '<div style="font-size:13px;color:var(--muted,#6b7280);' +
          'margin-bottom:10px;">' + _esc(kp.detail) + '</div>' : '') +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;">';
      return;
    }
    if (rawType === 'gate_close') { content += '</div></div>'; return; }

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

  return fsBreakout + content;
}
