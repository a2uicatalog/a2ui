// atoms_news.gs — News/headline atoms for ranked lists, breaking banners, digests
// All pure CSS/inline — no CDN, GAS CSP-safe

// ── headline_list ─────────────────────────────────────────────────────────────
// Ranked numbered list of news headlines with source, time, tag pill.
// Fields:
//   title   — section label above the list (optional)
//   accent  — colour for rank badges and tag pills (default: #6366f1)
//   items   — array of { rank?, title, source?, time?, tag?, url? }
_RENDERERS['headline_list'] = function(b) {
  var accent = b.accent || '#6366f1';
  var items  = b.items  || [];
  var hdr    = b.title
    ? '<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted,#9ca3af);margin:0 0 14px">' + _esc(b.title) + '</p>'
    : '';

  var rows = items.map(function(item, i) {
    var rank    = item.rank != null ? item.rank : i + 1;
    var tagHtml = item.tag
      ? '<span style="background:' + accent + '22;color:' + accent + ';padding:1px 7px;border-radius:4px;font-size:0.67rem;font-weight:700;letter-spacing:0.04em;margin-right:8px">' + _esc(item.tag) + '</span>'
      : '';
    var meta    = [item.source, item.time].filter(Boolean).map(_esc).join(' · ');
    var titleEl = item.url
      ? '<a href="' + _safeUrl(item.url) + '" target="_top" style="color:var(--text,#f9fafb);text-decoration:none">' + _esc(item.title) + '</a>'
      : _esc(item.title || '');
    return '<div style="display:flex;align-items:flex-start;gap:14px;padding:14px 0;border-bottom:1px solid var(--border,rgba(255,255,255,0.08))">' +
      '<span style="flex:0 0 28px;height:28px;border-radius:50%;background:' + accent + ';color:#fff;font-size:0.78rem;font-weight:800;display:flex;align-items:center;justify-content:center;margin-top:2px">' + rank + '</span>' +
      '<div style="flex:1;min-width:0">' +
      '<p style="margin:0;font-size:1rem;font-weight:700;line-height:1.45;color:var(--text,#f9fafb)">' + titleEl + '</p>' +
      (tagHtml || meta ? '<p style="margin:5px 0 0;font-size:0.75rem;color:var(--muted,#9ca3af)">' + tagHtml + meta + '</p>' : '') +
      '</div></div>';
  }).join('');

  return '<div style="margin:12px 0">' + hdr + rows + '</div>';
};

// ── breaking_banner ───────────────────────────────────────────────────────────
// High-impact left-bordered card for a single featured or breaking story.
// Fields:
//   label   — badge text (default: "BREAKING")
//   title   — headline
//   summary — optional supporting sentence
//   source  — publication name
//   time    — e.g. "Just now", "3h ago"
//   accent  — border/badge colour (default: #ef4444 red)
_RENDERERS['breaking_banner'] = function(b) {
  var accent  = b.accent  || '#ef4444';
  var label   = b.label   || 'BREAKING';
  var summary = b.summary ? '<p style="margin:8px 0 0;font-size:0.875rem;color:var(--muted,#9ca3af);line-height:1.65">' + _esc(b.summary) + '</p>' : '';
  var sourceLine = (b.source || b.time)
    ? '<p style="margin:8px 0 0;font-size:0.75rem;color:var(--muted,#9ca3af)">' + [b.source, b.time].filter(Boolean).map(_esc).join(' · ') + '</p>'
    : '';
  return '<div style="border-left:4px solid ' + accent + ';background:' + accent + '18;border-radius:0 10px 10px 0;padding:18px 20px;margin:12px 0">' +
    '<p style="margin:0 0 7px;font-size:0.63rem;font-weight:800;letter-spacing:0.13em;text-transform:uppercase;color:' + accent + '">' + _esc(label) + '</p>' +
    '<p style="margin:0;font-size:1.15rem;font-weight:800;line-height:1.4;color:var(--text,#f9fafb)">' + _esc(b.title || '') + '</p>' +
    summary + sourceLine +
    '</div>';
};

// ── news_digest ───────────────────────────────────────────────────────────────
// Two-column grid of compact story cards — good for "5 things to know" briefs.
// Fields:
//   title   — section heading
//   accent  — accent colour for numbering (default: #6366f1)
//   items   — array of { title, body?, tag?, source? }
_RENDERERS['news_digest'] = function(b) {
  var accent = b.accent || '#6366f1';
  var items  = b.items  || [];
  var hdr    = b.title
    ? '<p style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted,#9ca3af);margin:0 0 14px">' + _esc(b.title) + '</p>'
    : '';

  var cards = items.map(function(item, i) {
    var tag = item.tag
      ? '<span style="background:' + accent + '22;color:' + accent + ';padding:1px 7px;border-radius:4px;font-size:0.67rem;font-weight:700;margin-right:6px">' + _esc(item.tag) + '</span>'
      : '';
    var body = item.body
      ? '<p style="margin:6px 0 0;font-size:0.82rem;color:var(--muted,#9ca3af);line-height:1.6">' + _esc(item.body) + '</p>'
      : '';
    var source = item.source
      ? '<p style="margin:6px 0 0;font-size:0.72rem;color:var(--muted,#9ca3af)">' + _esc(item.source) + '</p>'
      : '';
    return '<div style="background:var(--surface2,#1a1a2e);border-radius:10px;padding:16px;position:relative">' +
      '<span style="position:absolute;top:14px;right:14px;font-size:1.1rem;font-weight:900;color:' + accent + ';opacity:0.3">' + (i + 1) + '</span>' +
      (tag ? '<p style="margin:0 0 8px">' + tag + '</p>' : '') +
      '<p style="margin:0;font-size:0.92rem;font-weight:700;line-height:1.45;color:var(--text,#f9fafb);padding-right:24px">' + _esc(item.title || '') + '</p>' +
      body + source +
      '</div>';
  }).join('');

  return '<div style="margin:12px 0">' + hdr +
    '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px">' + cards + '</div>' +
    '</div>';
};
