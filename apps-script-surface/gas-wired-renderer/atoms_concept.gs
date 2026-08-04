// ── concept_ladder / concept_rung ─────────────────────────────────────────────
// Layered-depth concept explainer: an attribution bar (when the ladder reads
// SOMEONE ELSE'S work), an opening hook, a hero mental-model card, then depth
// rungs down the same connected rail article_journey uses — each rung one level
// deeper, terminating in worked-example rungs (kind:'example', mono styling).
//
// Port of renderers/web_article.py's _render_concept_ladder/_render_concept_rung
// (the reference implementation). Every helper this needs — _journeyPalette,
// _journeyFontCss, _journeyMdCode, _JOURNEY_MONO/_SERIF, _JOURNEY_PALETTE_LIGHT
// — already lives in atom.gs, put there by the article_journey port; the two
// article atoms deliberately share one design system.
//
// Why this file exists at all: EVERY render path except the blog pipeline
// compiles from these .gs sources — GAS ?p= URLs, the MCP Apps bundle
// (gen_mcp_apps_bundle.py globs atom.gs + atoms_*.gs) and the Worker's
// /api/render (gen_worker_renderers.py). Python-only meant emit_runbook_surface
// could return a URL that rendered nothing.

// Attribution bar for a ladder that analyses someone else's work. Renders above
// the eyebrow and headline so the first glance reads "a piece ABOUT that piece",
// never a standalone article that could stand in for the original. `steered_by`
// records what the reader asked the reading to look for — a steered reading is a
// different object from a neutral one, and hiding what shaped it is the same
// class of omission as hiding the source. Absent `source` renders nothing.
function _journeySourceBar(b) {
  var src = b.source || null;
  if (!src) return '';
  var pal = _JOURNEY_PALETTE_LIGHT;
  var label = _esc(src.label || 'Analysis of');
  var title = _esc(src.title || '');
  var url = String(src.url || '').replace(/^\s+|\s+$/g, '');
  var linked = title && /^https?:\/\//.test(url);
  var titleHtml = linked
    ? '<a href="' + _safeUrl(url) + '" style="color:var(--ink,' + pal.ink + ');text-decoration:underline;'
      + 'text-underline-offset:2px;text-decoration-thickness:1px;">' + title + '</a>'
    : title;

  var bits = [];
  if (src.author) bits.push(_esc(src.author));
  if (src.publication) bits.push(_esc(src.publication));
  if (src.published) bits.push(_esc(src.published));
  if (src.read_minutes) bits.push(_esc(src.read_minutes) + ' min read');
  var meta = bits.join(' · ');

  var steered = src.steered_by;
  var steeredHtml = '';
  if (steered) {
    var lines = Object.prototype.toString.call(steered) === '[object Array]' ? steered : [steered];
    var items = '';
    for (var i = 0; i < lines.length; i++) {
      if (!lines[i]) continue;
      items += '<div style="font-style:italic;font-size:0.86rem;line-height:1.45;color:var(--ink,'
        + pal.ink + ');max-width:56ch;">' + _journeyMdCode(String(lines[i])) + '</div>';
    }
    if (items) {
      steeredHtml =
        '<div style="margin-top:0.7rem;padding-top:0.6rem;border-top:1px solid var(--line,' + pal.line + ');">'
        + '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.62rem;font-weight:700;'
        + 'letter-spacing:0.1em;text-transform:uppercase;color:var(--ink-soft,' + pal.ink_soft + ');'
        + 'margin-bottom:0.3rem;">Reading steered by</div>' + items + '</div>';
    }
  }

  // WHO READ IT. Once more than one model can write into a reader's history,
  // this is what makes the history interpretable — two readings of one article
  // are only comparable if you know which model produced each.
  //
  // A SELF-REPORT AND A FACT ARE DIFFERENT CLAIMS, and the rendering says which
  // it is. When we called the model ourselves (a server-side reading) we
  // observed it; when a model told us its own name we were merely told, and it
  // can be wrong or silent about that. Overstating the second is the unearned
  // confidence this runbook's parsing_guide forbids everywhere else. Absent
  // entirely, the bar SAYS SO rather than quietly omitting the line — an
  // unattributed reading should look unattributed.
  // Read from EITHER place: the stamper copies contract fields onto the ladder
  // (b.*) while source-shaped data arrives under source (src.*). Checking one
  // only would render "not recorded" for a payload that plainly recorded it.
  var analysed = src.analysed_by || b.analysed_by;
  var analysedOk = src.analysed_verified || b.analysed_verified;
  var analysedHtml =
    '<div style="margin-top:0.55rem;font-family:' + _JOURNEY_MONO + ';font-size:0.62rem;'
    + 'letter-spacing:0.06em;color:var(--ink-soft,' + pal.ink_soft + ');">'
    + (analysed
        ? 'Analysed by ' + _esc(String(analysed))
          + (analysedOk ? '' : ' <span style="opacity:0.75;">(self-reported)</span>')
        : 'Analysing model not recorded')
    + '</div>';

  return '<div style="background:var(--paper-raised,' + pal.paper_raised + ');'
    + 'border:1px solid var(--line,' + pal.line + ');'
    + 'border-left:3px solid var(--accent,' + pal.accent + ');border-radius:8px;'
    + 'padding:0.75rem 1rem;margin-bottom:1.5rem;">'
    + '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.66rem;font-weight:700;'
    + 'letter-spacing:0.1em;text-transform:uppercase;color:var(--accent,' + pal.accent + ');'
    + 'margin-bottom:0.35rem;">' + label + '</div>'
    + (title ? '<div style="font-size:1.02rem;line-height:1.35;color:var(--ink,' + pal.ink + ');'
       + 'max-width:54ch;">' + titleHtml + '</div>' : '')
    + analysedHtml
    + (meta ? '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.74rem;'
       + 'color:var(--ink-soft,' + pal.ink_soft + ');margin-top:0.3rem;">' + meta + '</div>' : '')
    + steeredHtml
    + '</div>';
}

_RENDERERS['concept_rung'] = function(b) {
  var pal = _JOURNEY_PALETTE_LIGHT;
  var kind = b.kind === 'example' ? 'example' : 'depth';
  var chipBg, chipFg, defaultLabel;
  if (kind === 'example') {
    chipBg = 'var(--mono-bg,' + pal.mono_bg + ')';
    chipFg = 'var(--mono-accent,' + pal.mono_accent + ')';
    defaultLabel = 'WORKED EXAMPLE';
  } else {
    chipBg = 'var(--accent-soft,' + pal.accent_soft + ')';
    chipFg = 'var(--accent,' + pal.accent + ')';
    defaultLabel = ('DEPTH ' + (b.badge === undefined || b.badge === null ? '' : b.badge))
      .replace(/^\s+|\s+$/g, '');
  }
  var label = _esc(b.label || defaultLabel);
  var title = _journeyMdCode(b.title || '');

  var bodyHtml = '';
  var paras = String(b.body || '').split('\n\n');
  for (var i = 0; i < paras.length; i++) {
    var p = paras[i].replace(/^\s+|\s+$/g, '');
    if (!p) continue;
    bodyHtml += '<p style="margin:0 0 0.9rem;max-width:60ch;line-height:1.6;'
      + 'color:var(--ink,' + pal.ink + ');">' + _journeyMdCode(p) + '</p>';
  }

  var codeHtml = '';
  if (b.code) {
    codeHtml = '<pre style="margin:0 0 0.9rem;background:var(--mono-bg,' + pal.mono_bg + ');'
      + 'color:var(--mono-fg,' + pal.mono_fg + ');font-family:' + _JOURNEY_MONO + ';'
      + 'font-size:0.82rem;line-height:1.55;padding:0.95rem 1.1rem;border-radius:8px;'
      + 'overflow-x:auto;max-width:100%;">' + _esc(b.code) + '</pre>';
    if (b.code_caption) {
      codeHtml += '<p style="font-style:italic;font-size:0.85rem;color:var(--ink-soft,' + pal.ink_soft + ');'
        + 'margin:-0.4rem 0 0.9rem;">' + _journeyMdCode(b.code_caption) + '</p>';
    }
  }

  var takeawayHtml = '';
  if (b.takeaway) {
    takeawayHtml = '<blockquote style="margin:0;background:var(--mono-bg,' + pal.mono_bg + ');'
      + 'color:var(--mono-fg,' + pal.mono_fg + ');font-family:' + _JOURNEY_MONO + ';'
      + 'font-size:0.86rem;line-height:1.6;padding:0.9rem 1.05rem;border-radius:8px;max-width:58ch;">'
      + '<span style="color:var(--mono-accent,' + pal.mono_accent + ');font-weight:600;'
      + 'margin-right:0.5em;">&gt;</span>' + _journeyMdCode(b.takeaway) + '</blockquote>';
  }

  return '<div style="padding-bottom:1.6rem;">'
    + '<div style="margin-bottom:0.5rem;"><span style="font-family:' + _JOURNEY_MONO + ';font-weight:700;'
    + 'font-size:0.72rem;letter-spacing:0.07em;padding:0.18em 0.6em;border-radius:4px;'
    + 'background:' + chipBg + ';color:' + chipFg + ';">' + label + '</span></div>'
    + (title ? '<h3 style="font-family:' + _JOURNEY_MONO + ';font-weight:600;font-size:1.08rem;'
       + 'line-height:1.32;margin:0 0 0.55rem;color:var(--ink,' + pal.ink + ');">' + title + '</h3>' : '')
    + bodyHtml + codeHtml + takeawayHtml
    + '</div>';
};

_RENDERERS['concept_ladder'] = function(b) {
  var pal = _journeyPalette(b);
  var cssVars = '';
  for (var k in pal) {
    if (!pal.hasOwnProperty(k)) continue;
    cssVars += (cssVars ? ';' : '') + '--' + k.replace(/_/g, '-') + ':' + pal[k];
  }
  var rungs = b.rungs || [];
  var eyebrow = _esc(b.eyebrow || '');
  var title = _esc(b.title || '');
  var dek = _esc(b.dek || '');
  var hook = _journeyMdCode(b.hook || '');
  var model = _journeyMdCode(b.model || '');
  var modelNote = b.model_note ? _journeyMdCode(b.model_note) : '';
  var closing = b.closing_note ? _journeyMdCode(b.closing_note) : '';

  var hookHtml = hook
    ? '<p style="font-size:1.15rem;line-height:1.55;max-width:56ch;margin:0 0 1.4rem;'
      + 'color:var(--ink);border-left:3px solid var(--accent);padding-left:1rem;">' + hook + '</p>'
    : '';

  var modelHtml = '';
  if (model) {
    modelHtml = '<div style="background:var(--paper-raised);border:1px solid var(--line);'
      + 'border-radius:10px;padding:1.1rem 1.3rem;margin-bottom:1.8rem;">'
      + '<div style="font-family:' + _JOURNEY_MONO + ';font-size:0.7rem;font-weight:700;'
      + 'letter-spacing:0.09em;text-transform:uppercase;color:var(--accent);'
      + 'margin-bottom:0.5rem;">The model</div>'
      + '<p style="font-style:italic;font-size:1.12rem;line-height:1.5;margin:0;max-width:52ch;'
      + 'color:var(--ink);">' + model + '</p>'
      + (modelNote ? '<p style="font-size:0.92rem;color:var(--ink-soft);margin:0.6rem 0 0;'
         + 'max-width:56ch;">' + modelNote + '</p>' : '')
      + '</div>';
  }

  var rows = '';
  for (var i = 0; i < rungs.length; i++) {
    var rung = rungs[i];
    var nodeBg, nodeFg;
    if (rung.kind === 'example') {
      nodeBg = 'var(--mono-bg)';
      nodeFg = 'var(--mono-accent)';
    } else {
      nodeBg = 'var(--accent-soft)';
      nodeFg = 'var(--accent)';
    }
    var connector = (i === rungs.length - 1) ? ''
      : '<div style="width:1.5px;flex:1;background:var(--line);margin:0.35rem 0;min-height:1.6rem;"></div>';
    var fn = _RENDERERS[rung.component || rung.type] || _RENDERERS['concept_rung'];
    var cardHtml = fn(rung);
    var componentId = _esc(rung.id || ('rung-' + (i + 1)));
    var badge = _esc(rung.badge === undefined || rung.badge === null ? String(i + 1) : rung.badge);
    rows += '<div data-component-id="' + componentId + '" style="display:grid;'
      + 'grid-template-columns:2.4rem 1fr;gap:1rem;scroll-margin-top:1.5rem;">'
      + '<div style="display:flex;flex-direction:column;align-items:center;">'
      + '<div style="width:2.4rem;height:2.4rem;border-radius:50%;display:flex;align-items:center;'
      + 'justify-content:center;font-family:' + _JOURNEY_MONO + ';font-weight:600;font-size:0.85rem;'
      + 'flex-shrink:0;background:' + nodeBg + ';color:' + nodeFg + ';">' + badge + '</div>'
      + connector
      + '</div>'
      + '<div>' + cardHtml + '</div>'
      + '</div>';
  }

  var fontCss = (b.use_plex_fonts !== false) ? _journeyFontCss() : '';

  // DECLARED fullscreen, same contract airspace_command_deck uses and the wired
  // renderer honours: the artifact escapes .asw-page's 860px column when the
  // payload asks for it. A reading is a rung rail whose argument structure IS
  // the point, and it reads as a keyhole in a chat card.
  //
  // DELIBERATELY NOT 100vh, and NOT overflow:hidden. That pair is the documented
  // trap (atoms_airspace.gs): a display-mode grant is a REQUEST, and a host that
  // refuses it sizes a 100vh canvas to the HOST viewport rather than the panel,
  // painting content off-screen — which presented as "no plane data" and cost a
  // day. Prose wants the WIDTH escape, not a viewport-height canvas, so taking
  // only the half that cannot misfire is the whole point: if the grant never
  // comes, this degrades to a wider column and nothing breaks.
  var fsCss = (b.fullscreen === true || b.height === 'fullscreen')
    ? '<style>.asw-page{max-width:none!important;padding:24px 32px!important;'
      + 'margin:0!important;}</style>'
    : '';

  return fsCss + fontCss
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
       + 'margin:0 0 1.4rem;">' + dek + '</p>' : '')
    + hookHtml
    + modelHtml
    + '<div style="display:flex;flex-direction:column;gap:0;">' + rows + '</div>'
    + (closing ? '<p style="font-style:italic;color:var(--ink-soft);max-width:58ch;'
       + 'margin:1.6rem 0 0;">' + closing + '</p>' : '')
    + '</div>';
};
