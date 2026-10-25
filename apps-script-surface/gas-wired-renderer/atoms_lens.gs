// ── article_playbook lenses ───────────────────────────────────────────────────
// spec/article-playbook-v0.1.md (a2ui-private). Renderers for the 8 lens_*
// atoms declared in atoms/schema.yaml. Epistemic TIER (EXTRACTED / INTERPRETED
// / EXTERNAL) is expressed structurally by runbooks/article_playbook.yaml's
// hub composition (one hub subject tab per tier, colored distinctly) — these
// renderers are only responsible for the per-lens content and, for
// interpreted-tier lenses, the evidence verification that is this runbook's
// single highest-value mitigation: every `evidence` span is checked as an
// actual verbatim substring of the lens's own `source_excerpt`, never trusted.

// Verbatim substring check. Returns true only if `span` appears exactly
// (case-sensitive) inside `excerpt` — no fuzzy matching, no normalization.
// A span that "looks close" but isn't an exact substring is exactly the
// distortion this check exists to catch.
function _lensEvidenceVerified(span, excerpt) {
  if (!span || !excerpt) return false;
  return String(excerpt).indexOf(String(span)) !== -1;
}

// Renders one evidence span as a blockquote, tagged verified/unverified
// against source_excerpt. Missing span -> explicit "no supporting quote"
// marker, never silently dropped (spec mitigation 2).
function _lensEvidenceBlock(span, excerpt) {
  if (!span) {
    return '<div style="font-size:0.78rem;font-style:italic;color:#b91c1c;' +
      'border-left:3px solid #b91c1c;padding:4px 10px;margin:6px 0;">' +
      '⚠ no supporting quote</div>';
  }
  var ok = _lensEvidenceVerified(span, excerpt);
  var color = ok ? '#0f766e' : '#b91c1c';
  var label = ok ? '' : '<div style="font-size:0.7rem;font-weight:700;color:' + color + ';margin-bottom:2px;">⚠ UNVERIFIED — not found in source_excerpt</div>';
  return '<div style="border-left:3px solid ' + color + ';padding:4px 10px;margin:6px 0;">' +
    label +
    '<blockquote style="margin:0;font-size:0.85rem;">' + _esc(span) + '</blockquote>' +
    '</div>';
}

_RENDERERS['lens_quotes'] = function(b) {
  var items = Array.isArray(b.items) ? b.items : [];
  if (!items.length) return '<p style="opacity:0.6;font-size:0.85rem;">No quotes supplied.</p>';
  var html = '';
  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    var k = _esc(it.id || it.quote || '');
    html += '<blockquote data-cb="item" data-key="' + k + '" style="margin:0 0 14px 0;">' + _markdownToHtml(it.quote || '') +
      (it.context ? '<div style="font-size:0.78rem;opacity:0.65;margin-top:4px;">' + _esc(it.context) + '</div>' : '') +
      '</blockquote>';
  }
  return html;
};

_RENDERERS['lens_structure'] = function(b) {
  var items = Array.isArray(b.items) ? b.items : [];
  if (!items.length) return '<p style="opacity:0.6;font-size:0.85rem;">No structure supplied.</p>';
  var html = '';
  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    var k = _esc(it.id || it.heading || '');
    html += '<div data-cb="item" data-key="' + k + '" style="margin-bottom:14px;">' +
      '<div data-cb="label" data-key="' + k + '" style="font-weight:700;font-size:0.9rem;margin-bottom:4px;">' + _esc(it.heading || '') + '</div>' +
      '<blockquote style="margin:0;">' + _markdownToHtml(it.quote || '') + '</blockquote>' +
      '</div>';
  }
  return html;
};

_RENDERERS['lens_themes'] = function(b) {
  var items = Array.isArray(b.items) ? b.items : [];
  var excerpt = b.source_excerpt || '';
  // sorted by weight when present, so an unevidenced 0.8 becomes ordering
  // rather than a displayed score (spec Open Q2).
  var sorted = items.slice().sort(function(a, x) {
    return (x.weight || 0) - (a.weight || 0);
  });
  var chipsHtml = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">';
  for (var i = 0; i < sorted.length; i++) {
    var k = _esc(sorted[i].id || sorted[i].theme || sorted[i].label || '');
    chipsHtml += '<span data-cb="tile" data-key="' + k + '" data-lens-theme="' + i + '" style="padding:5px 12px;border-radius:999px;' +
      'background:rgba(124,58,237,0.12);color:#7c3aed;font-size:0.78rem;font-weight:700;">' +
      _esc(sorted[i].label || '') + '</span>';
  }
  chipsHtml += '</div>';
  var evidenceHtml = '';
  for (var j = 0; j < sorted.length; j++) {
    evidenceHtml += '<div style="margin-bottom:8px;"><div style="font-weight:600;font-size:0.82rem;">' +
      _esc(sorted[j].label || '') + '</div>' + _lensEvidenceBlock(sorted[j].evidence, excerpt) + '</div>';
  }
  return chipsHtml + evidenceHtml;
};

_RENDERERS['lens_eli5'] = function(b) {
  var excerpt = b.source_excerpt || '';
  var evidence = Array.isArray(b.evidence) ? b.evidence : [];
  var html = '<div data-cb="node" data-key="' + _ckey(undefined, 'lens_eli5') + '" style="font-size:0.95rem;line-height:1.6;margin-bottom:14px;">' + _markdownToHtml(b.text || '') + '</div>';
  if (evidence.length) {
    html += '<div style="font-size:0.75rem;font-weight:700;opacity:0.6;margin-bottom:4px;">DRAWN FROM</div>';
    for (var i = 0; i < evidence.length; i++) {
      html += _lensEvidenceBlock(evidence[i], excerpt);
    }
  } else {
    html += _lensEvidenceBlock(null, excerpt);
  }
  return html;
};

_RENDERERS['lens_synthesis'] = function(b) {
  var points = Array.isArray(b.points) ? b.points.filter(function(p) { return p && typeof p === 'object' && !Array.isArray(p); }) : [];
  var excerpt = _textLoose(b.source_excerpt);
  if (!points.length) return '<p style="opacity:0.6;font-size:0.85rem;">No synthesis points supplied.</p>';
  var html = '';
  for (var i = 0; i < points.length; i++) {
    var p = points[i];
    html += '<div style="margin-bottom:14px;">' +
      _RENDERERS['take_away_card']({ headline: _textLoose(p.point) }) +
      _lensEvidenceBlock(_textLoose(p.evidence), excerpt) +
      '</div>';
  }
  return html;
};

_RENDERERS['lens_freeform'] = function(b) {
  var tier = b.tier || 'interpreted';
  var excerpt = b.source_excerpt || '';
  var evidence = Array.isArray(b.evidence) ? b.evidence : [];
  var html = '<div data-cb="node" data-key="' + _ckey(b.label, 'lens_freeform') + '" style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.68rem;' +
    'font-weight:700;text-transform:uppercase;background:rgba(0,0,0,0.06);margin-bottom:8px;">' +
    'off-template · ' + _esc(tier) + '</div>' +
    '<div style="font-weight:700;font-size:0.95rem;margin-bottom:6px;">' + _esc(b.label || '') + '</div>' +
    '<div style="font-size:0.9rem;line-height:1.6;margin-bottom:10px;">' + _markdownToHtml(b.text || '') + '</div>';
  if (tier === 'extracted' || tier === 'interpreted') {
    if (evidence.length) {
      for (var i = 0; i < evidence.length; i++) html += _lensEvidenceBlock(evidence[i], excerpt);
    } else {
      html += _lensEvidenceBlock(null, excerpt);
    }
  }
  return html;
};

_RENDERERS['lens_similar'] = function(b) {
  var verified = !!b.verified;
  var items = Array.isArray(b.items) ? b.items : [];
  var noticeHtml = verified ? '' :
    '<div style="font-size:0.78rem;font-weight:700;color:#b91c1c;margin-bottom:10px;">' +
    '⚠ suggestions, unverified — not confirmed retrieved this session</div>';
  var rowsHtml = '';
  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    var retrieved = !!it.retrieved;
    var k = _esc(it.id || it.title || it.label || '');
    var titleHtml = (retrieved && it.url)
      ? '<a href="' + _safeUrl(it.url) + '" target="_blank" rel="noopener" style="color:inherit;">' + _esc(it.title || '') + '</a>'
      : _esc(it.title || '') + ' <span style="font-size:0.7rem;font-weight:700;color:#b91c1c;">· not retrieved</span>';
    rowsHtml += '<div data-cb="item" data-key="' + k + '" style="border-bottom:1px solid rgba(0,0,0,0.06);padding:8px 0;">' +
      '<div data-cb="label" data-key="' + k + '" style="font-weight:700;font-size:0.88rem;">' + titleHtml + '</div>' +
      '<div style="font-size:0.82rem;opacity:0.75;">' + _esc(it.why || '') + '</div>' +
      '</div>';
  }
  return noticeHtml + rowsHtml;
};

_RENDERERS['lens_context'] = function(b) {
  var items = Array.isArray(b.items) ? b.items : [];
  if (!items.length) return '<p style="opacity:0.6;font-size:0.85rem;">No context supplied.</p>';
  var html = '';
  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    var retrieved = !!it.retrieved;
    var k = _esc(it.id || it.label || it.title || '');
    var labelHtml = (retrieved && it.url)
      ? '<a href="' + _safeUrl(it.url) + '" target="_blank" rel="noopener" style="color:inherit;">' + _esc(it.label || '') + '</a>'
      : _esc(it.label || '') + ' <span style="font-size:0.7rem;font-weight:700;color:#b91c1c;">· not retrieved</span>';
    html += '<div data-cb="item" data-key="' + k + '" style="border-bottom:1px solid rgba(0,0,0,0.06);padding:8px 0;">' +
      '<div data-cb="label" data-key="' + k + '" style="font-weight:700;font-size:0.88rem;">' + labelHtml + '</div>' +
      '<div style="font-size:0.82rem;opacity:0.75;">' + _esc(it.note || '') + '</div>' +
      '</div>';
  }
  return html;
};

// ── toulmin_argument ─────────────────────────────────────────────────────────
// One argument laid out Toulmin's way (claim, grounds, warrant, backing,
// qualifier, rebuttals) as an inspectable record: the confidence plumbing
// behind a decision, not a finished reading. Each ground's quote goes through
// the same verbatim check as the lenses above; a missing warrant, backing or
// rebuttal is shown as missing, never left out.
function _tlRow(label, body) {
  return '<div style="display:grid;grid-template-columns:7.5em 1fr;gap:10px;padding:9px 0;border-top:1px solid rgba(0,0,0,0.08);">' +
    '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#4b5563;padding-top:2px;">' + label + '</div>' +
    '<div style="min-width:0;">' + body + '</div></div>';
}

function _tlMissing(text) {
  return '<div style="font-size:0.8rem;font-style:italic;color:#92400e;">⚠ ' + text + '</div>';
}

_RENDERERS['toulmin_argument'] = function(b) {
  var excerpt = b.source_excerpt || '';
  var grounds = (Array.isArray(b.grounds) ? b.grounds : []).slice(0, 8);
  var rebuttals = (Array.isArray(b.rebuttals) ? b.rebuttals : []).slice(0, 6);
  var verified = 0, applies = 0, gh = '', rh = '';
  for (var i = 0; i < grounds.length; i++) {
    var g = grounds[i] || {};
    if (_lensEvidenceVerified(g.quote, excerpt)) verified++;
    gh += '<div style="margin-bottom:8px;">' +
      (g.text ? '<div style="font-size:0.9rem;">' + _esc(g.text) + '</div>' : '') +
      _lensEvidenceBlock(g.quote, excerpt) +
      (g.source ? '<div style="font-size:0.72rem;color:#4b5563;">' + _esc(g.source) + '</div>' : '') +
      '</div>';
  }
  for (var j = 0; j < rebuttals.length; j++) {
    var r = rebuttals[j] || {};
    var on = !!r.applies;
    if (on) applies++;
    rh += '<div style="display:flex;gap:8px;align-items:baseline;margin-bottom:6px;">' +
      '<span style="flex:none;font-size:0.66rem;font-weight:700;padding:2px 7px;border-radius:999px;' +
      (on ? 'background:#fee2e2;color:#b91c1c;">APPLIES' : 'background:rgba(0,0,0,0.06);color:#4b5563;">DOES NOT APPLY') + '</span>' +
      '<span style="font-size:0.88rem;">unless ' + _esc(r.text || '') + '</span></div>';
  }
  var status = 'STANDS', scol = '#0f766e';
  if (applies) { status = 'REBUTTED'; scol = '#b91c1c'; }
  else if (!grounds.length) { status = 'UNGROUNDED'; scol = '#b91c1c'; }
  else if (verified < grounds.length) { status = 'UNVERIFIED GROUNDS'; scol = '#92400e'; }
  var claim = b.claim || '';
  return '<div role="group" aria-label="' + _esc('Argument: ' + claim) + '" style="box-sizing:border-box;border:1px solid rgba(0,0,0,0.12);border-radius:12px;padding:14px 18px 6px;margin:1rem 0;background:#ffffff;color:#111827;font-family:system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif;">' +
    (b.title ? '<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#4b5563;margin-bottom:6px;">' + _esc(b.title) + '</div>' : '') +
    '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px;">' +
    '<span style="font-size:0.7rem;font-weight:800;letter-spacing:0.08em;padding:3px 9px;border-radius:999px;border:1.5px solid ' + scol + ';color:' + scol + ';">' + status + '</span>' +
    '<span style="font-size:0.75rem;color:#4b5563;">' + grounds.length + (grounds.length === 1 ? ' ground · ' : ' grounds · ') + verified + ' verified in source · ' + applies + ' of ' + rebuttals.length + ' rebuttals apply</span></div>' +
    _tlRow('Claim', claim ? (b.qualifier ? '<span style="font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:999px;background:#e0e7ff;color:#3730a3;margin-right:6px;">' + _esc(b.qualifier) + '</span>' : '') + '<span style="font-weight:700;font-size:1rem;">' + _esc(claim) + '</span>' : _tlMissing('no claim stated')) +
    _tlRow('Grounds', gh || _tlMissing('no grounds offered')) +
    _tlRow('Warrant', b.warrant ? '<div style="font-size:0.9rem;">since ' + _esc(b.warrant) + '</div>' : _tlMissing('no warrant stated: the step from grounds to claim is unexamined')) +
    _tlRow('Backing', b.backing ? '<div style="font-size:0.88rem;">' + _esc(b.backing) + '</div>' : _tlMissing('no backing: the warrant is asserted, not supported')) +
    _tlRow('Rebuttals', rh || _tlMissing('no rebuttals considered')) +
    '</div>';
};
