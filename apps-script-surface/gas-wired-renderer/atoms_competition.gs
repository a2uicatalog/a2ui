// atoms_competition.gs — competition & multi-section atoms (a2ui-competition-v1 + base)
//
// Origin: backfill proposal from a real off-catalog build (americano tournament
// night, 2026-07-10) — each atom replaces a documented workaround where a
// generic atom (table, code-oriented tabs) was fighting structured domain data.
// All three are class-A: pure string-building, no server tokens, CSS-only
// interactivity (same radio-input trick as the existing `tabs` atom).

// ── content_tabs ──────────────────────────────────────────────────────────────
// Tabbed panels where each pane holds real nested atom blocks (rendered via
// renderAtoms), unlike `tabs` whose panes are single content strings.
//
// Fields:
//   accent        — active-tab colour (optional, default var(--accent))
//   default_index — tab open on load (optional, default 0)
//   tabs          — required [{label: string, blocks: [atom blocks]}]
_RENDERERS['content_tabs'] = function(b) {
  var tabList = b.tabs || [];
  if (!tabList.length) return '';
  var uid    = 'ct' + Math.random().toString(36).substr(2, 6);
  var accent = b.accent || 'var(--a2ui-accent,#6366f1)';
  var open   = Math.min(Math.max(b.default_index || 0, 0), tabList.length - 1);

  var css = '<style>';
  css += '.' + uid + 'p{display:none;padding:16px 4px;}';
  css += '.' + uid + 'l{padding:10px 18px;cursor:pointer;font-size:0.85rem;font-weight:600;' +
         'color:var(--muted,#5f6368);white-space:nowrap;border-bottom:2px solid transparent;' +
         'margin-bottom:-2px;transition:color 0.15s;display:inline-block;}';
  tabList.forEach(function(t, i) {
    css += '#' + uid + '_' + i + ':checked ~ .' + uid + 'ls .' + uid + 'l:nth-child(' + (i + 1) + ')' +
           '{color:' + accent + ';border-bottom-color:' + accent + ';}';
    css += '#' + uid + '_' + i + ':checked ~ .' + uid + 'ps .' + uid + 'p:nth-child(' + (i + 1) + '){display:block;}';
  });
  css += '</style>';

  var inputs = tabList.map(function(t, i) {
    return '<input type="radio" name="' + uid + '" id="' + uid + '_' + i + '"' +
           (i === open ? ' checked' : '') + ' style="display:none;">';
  }).join('');
  var labels = tabList.map(function(t, i) {
    return '<label class="' + uid + 'l" for="' + uid + '_' + i + '">' + _esc(t.label || 'Tab ' + (i + 1)) + '</label>';
  }).join('');
  var panels = tabList.map(function(t) {
    return '<div class="' + uid + 'p">' + renderAtoms(t.blocks || []) + '</div>';
  }).join('');

  return '<div style="margin:1.2rem 0;">' + css + inputs +
         '<div class="' + uid + 'ls" style="border-bottom:2px solid var(--border,#e8eaed);overflow-x:auto;white-space:nowrap;">' + labels + '</div>' +
         '<div class="' + uid + 'ps">' + panels + '</div>' +
         '</div>';
};

// ── standings_table ───────────────────────────────────────────────────────────
// Ranked competition standings — rank + name + played + primary sort metric +
// extra numeric columns. Sort is the RENDERER's job (descending by `primary`);
// `highlight` is a semantic state name, the renderer owns the styling.
//
// Fields:
//   primary_label — header for the sort column (optional, default "PTS")
//   columns       — extra numeric column headers (optional, e.g. ["Points Won","+/-"])
//   rows          — required [{name, played?, primary, values?[], highlight?}]
_RENDERERS['standings_table'] = function(b) {
  var rows = (b.rows || []).slice().sort(function(x, y) { return (y.primary || 0) - (x.primary || 0); });
  if (!rows.length) return '';
  var extra = b.columns || [];
  var num = 'font-variant-numeric:tabular-nums;text-align:right;';
  var th  = 'padding:8px 12px;font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase;' +
            'color:var(--muted,#5f6368);border-bottom:2px solid var(--border,#e8eaed);';
  var td  = 'padding:9px 12px;font-size:0.88rem;border-bottom:1px solid var(--border,#e8eaed);';

  var head = '<tr>' +
    '<th style="' + th + num + '">#</th>' +
    '<th style="' + th + 'text-align:left;">Player</th>' +
    (rows.some(function(r) { return r.played !== undefined; }) ? '<th style="' + th + num + '">P</th>' : '') +
    '<th style="' + th + num + '">' + _esc(b.primary_label || 'PTS') + '</th>' +
    extra.map(function(c) { return '<th style="' + th + num + '">' + _esc(c) + '</th>'; }).join('') +
    '</tr>';
  var showPlayed = rows.some(function(r) { return r.played !== undefined; });

  var body = rows.map(function(r, i) {
    var lead = r.highlight === 'leader';
    var rowStyle = lead ? 'background:rgba(99,102,241,0.08);font-weight:700;' : '';
    return '<tr style="' + rowStyle + '">' +
      '<td style="' + td + num + (lead ? 'color:var(--a2ui-accent,#6366f1);' : '') + '">' + (i + 1) + '</td>' +
      '<td style="' + td + '">' + _esc(r.name || '') + '</td>' +
      (showPlayed ? '<td style="' + td + num + '">' + (r.played !== undefined ? _esc(r.played) : '') + '</td>' : '') +
      '<td style="' + td + num + 'font-weight:700;">' + _esc(r.primary !== undefined ? r.primary : '') + '</td>' +
      extra.map(function(c, j) {
        var v = (r.values || [])[j];
        return '<td style="' + td + num + '">' + (v !== undefined ? _esc(v) : '') + '</td>';
      }).join('') +
      '</tr>';
  }).join('');

  return '<div style="overflow-x:auto;margin:1.2rem 0;">' +
         '<table style="border-collapse:collapse;width:100%;">' + head + body + '</table></div>';
};

// ── match_schedule ────────────────────────────────────────────────────────────
// Round-by-round matchup schedule across courts. Structured teams (arrays of
// player names), optional scores; layout "table" (reference/printable, one row
// per round) or "cards" (one card per match, courtside/mobile).
//
// Fields:
//   rounds — required [{label?, matches: [{court?, team_a[], team_b[], score_a?, score_b?}]}]
//   layout — "table" (default) | "cards"
_RENDERERS['match_schedule'] = function(b) {
  var rounds = b.rounds || [];
  if (!rounds.length) return '';

  function team(names) { return (names || []).map(_esc).join(' &amp; '); }
  function scored(m) { return m.score_a !== undefined && m.score_b !== undefined; }

  if ((b.layout || 'table') === 'cards') {
    var cards = rounds.map(function(r, ri) {
      var label = _esc(r.label || 'Round ' + (ri + 1));
      var items = (r.matches || []).map(function(m) {
        return '<div style="border:1px solid var(--border,#e8eaed);border-radius:10px;padding:12px 14px;margin:8px 0;">' +
          (m.court ? '<div style="font-size:0.68rem;letter-spacing:0.08em;text-transform:uppercase;color:var(--muted,#5f6368);margin-bottom:6px;">' + _esc(m.court) + '</div>' : '') +
          '<div style="display:flex;align-items:center;gap:10px;font-size:0.92rem;">' +
            '<span style="flex:1;text-align:right;font-weight:600;">' + team(m.team_a) + '</span>' +
            (scored(m)
              ? '<span style="font-variant-numeric:tabular-nums;font-weight:700;padding:2px 10px;border-radius:6px;background:var(--surface2,#f1f3f4);">' + _esc(m.score_a) + ' – ' + _esc(m.score_b) + '</span>'
              : '<span style="font-size:0.72rem;color:var(--muted,#5f6368);font-weight:700;">vs</span>') +
            '<span style="flex:1;font-weight:600;">' + team(m.team_b) + '</span>' +
          '</div></div>';
      }).join('');
      return '<div style="margin:1rem 0;">' +
        '<div style="font-size:0.78rem;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;color:var(--a2ui-accent,#6366f1);">' + label + '</div>' +
        items + '</div>';
    }).join('');
    return '<div style="margin:1.2rem 0;">' + cards + '</div>';
  }

  // table layout — one row per round, one column per court
  var courts = [];
  rounds.forEach(function(r) {
    (r.matches || []).forEach(function(m, i) {
      var c = m.court || 'Court ' + (i + 1);
      if (courts.indexOf(c) === -1) courts.push(c);
    });
  });
  var th = 'padding:8px 12px;font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase;' +
           'color:var(--muted,#5f6368);border-bottom:2px solid var(--border,#e8eaed);text-align:left;';
  var td = 'padding:9px 12px;font-size:0.88rem;border-bottom:1px solid var(--border,#e8eaed);';

  var head = '<tr><th style="' + th + '">Round</th>' +
    courts.map(function(c) { return '<th style="' + th + '">' + _esc(c) + '</th>'; }).join('') + '</tr>';
  var body = rounds.map(function(r, ri) {
    var byCourt = {};
    (r.matches || []).forEach(function(m, i) { byCourt[m.court || 'Court ' + (i + 1)] = m; });
    return '<tr><td style="' + td + 'font-weight:700;">' + _esc(r.label || ri + 1) + '</td>' +
      courts.map(function(c) {
        var m = byCourt[c];
        if (!m) return '<td style="' + td + '"></td>';
        return '<td style="' + td + '">' + team(m.team_a) +
               ' <span style="color:var(--muted,#5f6368);font-size:0.78rem;">vs</span> ' + team(m.team_b) +
               (scored(m) ? ' <b style="font-variant-numeric:tabular-nums;">' + _esc(m.score_a) + '–' + _esc(m.score_b) + '</b>' : '') +
               '</td>';
      }).join('') + '</tr>';
  }).join('');

  return '<div style="overflow-x:auto;margin:1.2rem 0;">' +
         '<table style="border-collapse:collapse;width:100%;">' + head + body + '</table></div>';
};
