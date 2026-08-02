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
    html += '<blockquote style="margin:0 0 14px 0;">' + _markdownToHtml(it.quote || '') +
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
    html += '<div style="margin-bottom:14px;">' +
      '<div style="font-weight:700;font-size:0.9rem;margin-bottom:4px;">' + _esc(it.heading || '') + '</div>' +
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
    chipsHtml += '<span data-lens-theme="' + i + '" style="padding:5px 12px;border-radius:999px;' +
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
  var html = '<div style="font-size:0.95rem;line-height:1.6;margin-bottom:14px;">' + _markdownToHtml(b.text || '') + '</div>';
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
  var points = Array.isArray(b.points) ? b.points : [];
  var excerpt = b.source_excerpt || '';
  if (!points.length) return '<p style="opacity:0.6;font-size:0.85rem;">No synthesis points supplied.</p>';
  var html = '';
  for (var i = 0; i < points.length; i++) {
    var p = points[i];
    html += '<div style="margin-bottom:14px;">' +
      _RENDERERS['take_away_card']({ headline: p.point || '' }) +
      _lensEvidenceBlock(p.evidence, excerpt) +
      '</div>';
  }
  return html;
};

_RENDERERS['lens_freeform'] = function(b) {
  var tier = b.tier || 'interpreted';
  var excerpt = b.source_excerpt || '';
  var evidence = Array.isArray(b.evidence) ? b.evidence : [];
  var html = '<div style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.68rem;' +
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
    var titleHtml = (retrieved && it.url)
      ? '<a href="' + _safeUrl(it.url) + '" target="_blank" rel="noopener" style="color:inherit;">' + _esc(it.title || '') + '</a>'
      : _esc(it.title || '') + ' <span style="font-size:0.7rem;font-weight:700;color:#b91c1c;">· not retrieved</span>';
    rowsHtml += '<div style="border-bottom:1px solid rgba(0,0,0,0.06);padding:8px 0;">' +
      '<div style="font-weight:700;font-size:0.88rem;">' + titleHtml + '</div>' +
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
    var labelHtml = (retrieved && it.url)
      ? '<a href="' + _safeUrl(it.url) + '" target="_blank" rel="noopener" style="color:inherit;">' + _esc(it.label || '') + '</a>'
      : _esc(it.label || '') + ' <span style="font-size:0.7rem;font-weight:700;color:#b91c1c;">· not retrieved</span>';
    html += '<div style="border-bottom:1px solid rgba(0,0,0,0.06);padding:8px 0;">' +
      '<div style="font-weight:700;font-size:0.88rem;">' + labelHtml + '</div>' +
      '<div style="font-size:0.82rem;opacity:0.75;">' + _esc(it.note || '') + '</div>' +
      '</div>';
  }
  return html;
};
