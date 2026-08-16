// atoms_photo_stepper.gs — a full-viewport, one-photo-at-a-time lightbox:
// prev/next, a vote button per slide, a live "who's voted" line, and the
// source listing link. Sibling of photo_grid (same reasoning: a photo-
// driven decision needs the thing you're looking at and the thing you act
// on to be the same element), for the case photo_grid does not cover —
// reviewing options ONE AT A TIME, immersively, rather than scanning a
// grid. Both real and complementary, not a replacement for each other.
//
// Fullscreen takeover, not an inline card (2026-08-16, redesigned after
// live feedback: the inline card read as cramped next to an older
// standalone gallery tool this replaced). Opened by a checkbox, exactly
// the same pure-CSS pattern `css_modal` (atom.gs) already uses for its own
// overlay: `#trigger-checkbox:checked ~ .overlay{display:...}` — no new
// mechanism, the second consumer of the same one. Chosen over a JS-driven
// open/close so the same "no JS state to lose sync with" property that
// protects slide position also protects open/closed state.
//
// Paging is the SAME pure-CSS radio-input trick `carousel` already uses
// (sibling :checked selectors drive the slide transform) — no JS state to
// go stale, no index to lose. That is also why the live-update counterpart
// (_a2uiUpdatePhotoStepper, A2UIState.html) patches each slide's badge/
// caption text IN PLACE rather than rebuilding the DOM: touching the
// radio/track markup would reset whichever slide the radio's own browser-
// owned :checked state is currently showing, exactly the "vote resets you
// back to photo 1" bug this design avoids by construction. It also patches
// by candidate id rather than array position — board:get re-sorts by star
// count while voting is open, so a candidate's position in the incoming
// array can move the instant any vote lands, including the one just cast.
//
// The vote button on each slide reuses photo_grid's click contract exactly
// (data-row-json + the same generalised [data-row-json] binder in
// A2UIState.html) — not a new mechanism, the third consumer of that one.
_RENDERERS['photo_stepper'] = function(b) {
  var images = b.images || b.rows || [];
  if (!images.length) return '<p style="color:#94a3b8;font-style:italic;">Nothing to show yet.</p>';
  var accent = b.accent || '#0f766e';
  var sid = 'ps' + Math.random().toString(36).substr(2, 6);
  var n = images.length;
  var mid = sid + '_open';

  var first = images[0] || {};
  var triggerLabel = b.trigger_label || 'Browse full screen';

  var css = '<style>' +
    '#' + mid + '{display:none;}' +
    // Trigger card: a compact preview shown while the overlay is closed.
    // Hidden the moment the checkbox is checked (sibling selector, same
    // mechanism as everything else in this atom).
    '.' + sid + '-trigger{position:relative;display:block;cursor:pointer;border-radius:12px;overflow:hidden;margin:12px 0;background:#111;text-decoration:none;}' +
    '.' + sid + '-trigger img{width:100%;max-height:50vh;object-fit:cover;display:block;opacity:0.85;}' +
    '.' + sid + '-trigger-label{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:10px;background:rgba(0,0,0,0.25);color:#fff;font-size:1.05rem;font-weight:700;text-shadow:0 1px 4px rgba(0,0,0,0.6);}' +
    '#' + mid + ':checked ~ .' + sid + '-trigger{display:none;}' +
    // Overlay: hidden by default, full viewport takeover once checked —
    // same position:fixed;inset:0;z-index pattern as css_modal (atom.gs).
    '.' + sid + '{display:none;position:fixed;inset:0;z-index:9000;background:#111;overflow:hidden;}' +
    '#' + mid + ':checked ~ .' + sid + '{display:block;}' +
    '.' + sid + ' input[type=radio]{display:none;}' +
    '.' + sid + '-inner{position:relative;height:100%;width:100%;}' +
    '.' + sid + '-track{display:flex;height:100%;transition:transform 0.35s ease;width:' + (n * 100) + '%;}' +
    '.' + sid + '-slide{width:' + (100 / n) + '%;flex:0 0 ' + (100 / n) + '%;position:relative;height:100%;}' +
    '.' + sid + '-slide img{width:100%;height:100%;display:block;object-fit:contain;background:#000;}' +
    // Caption is a gradient overlay ON the photo, not a bar below it —
    // matches the immersive reference this redesign targets.
    '.' + sid + '-cap{position:absolute;left:0;right:0;bottom:0;padding:36px 24px 22px;background:linear-gradient(to top, rgba(0,0,0,0.85), rgba(0,0,0,0));color:#fff;pointer-events:none;}' +
    '.' + sid + '-cap > *{pointer-events:auto;}' +
    '.' + sid + '-cap .ps-name{font-size:1.05rem;font-weight:600;}' +
    '.' + sid + '-cap .ps-price{color:#d1d5db;font-size:0.85rem;margin-top:2px;}' +
    '.' + sid + '-cap .ps-voters{color:#d1d5db;font-size:0.78rem;margin-top:8px;}' +
    '.' + sid + '-badge{position:absolute;top:16px;right:16px;background:rgba(0,0,0,0.65);color:#fff;font-size:0.78rem;font-weight:700;padding:3px 9px;border-radius:99px;}' +
    '.' + sid + '-badge.ps-badge-active{background:' + accent + ';color:#fff;}' +
    '.' + sid + '-vote{margin-top:12px;display:inline-block;background:' + accent + ';color:#fff;border:none;border-radius:6px;padding:9px 18px;font-size:0.88rem;font-weight:600;cursor:pointer;}' +
    '.' + sid + '-source{margin-top:12px;margin-left:10px;display:inline-block;color:#d1d5db;font-size:0.82rem;text-decoration:underline;}' +
    // z-index matters here: .sid-slide (each slide) is ALSO position:relative,
    // and the slide track sits AFTER these nav labels in DOM order — with no
    // z-index, default stacking paints later positioned siblings on top,
    // so the slide's own image would otherwise sit above the arrows and eat
    // every click (confirmed live: Playwright's own "intercepts pointer
    // events" error on the image, even though the arrow's bounding box and
    // computed display were both already correct).
    '.' + sid + '-nav{position:absolute;top:0;bottom:0;width:15%;z-index:5;display:flex;align-items:center;justify-content:center;font-size:2.5rem;color:rgba(255,255,255,0.5);cursor:pointer;user-select:none;transition:background 0.15s;}' +
    '.' + sid + '-nav:hover{background:rgba(0,0,0,0.25);color:rgba(255,255,255,0.9);}' +
    '.' + sid + '-prev{left:0;} .' + sid + '-next{right:0;}' +
    '.' + sid + '-topbar{position:absolute;top:0;left:0;right:0;z-index:6;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;background:linear-gradient(to bottom, rgba(0,0,0,0.6), rgba(0,0,0,0));pointer-events:none;}' +
    '.' + sid + '-topbar > *{pointer-events:auto;}' +
    '.' + sid + '-close{color:#fff;font-size:0.85rem;font-weight:600;text-decoration:none;cursor:pointer;background:rgba(0,0,0,0.4);border-radius:99px;padding:6px 14px;}' +
    '.' + sid + '-count{color:#d1d5db;font-size:0.8rem;background:rgba(0,0,0,0.4);padding:4px 11px;border-radius:99px;}' +
    '</style>';

  var perSlide = '';
  for (var i = 1; i <= n; i++) {
    var offset = (i - 1) * (100 / n);
    perSlide += '<style>#' + sid + '_s' + i + ':checked ~ .' + sid + '-inner .' + sid + '-track{transform:translateX(-' + offset + '%);}</style>';
    // Count label swap: N separate absolutely-positioned counters, one per
    // slide, shown only while that slide's radio is checked — same sibling-
    // selector trick as the transform above, no JS.
    perSlide += '<style>.' + sid + '-count' + i + '{display:none;} #' + sid + '_s' + i + ':checked ~ .' + sid + '-inner .' + sid + '-count' + i + '{display:block;}</style>';
  }

  var inputs = images.map(function(img, i) {
    return '<input type="radio" id="' + sid + '_s' + (i + 1) + '" name="' + sid + '"' + (i === 0 ? ' checked' : '') + '>';
  }).join('');

  // Nav arrows: a single prev/next pair whose `for` target is recomputed
  // per slide would need JS; instead every slide gets its OWN pair, shown
  // only while checked, same sibling-selector mechanism as the counter
  // above.
  for (var j = 1; j <= n; j++) {
    perSlide += '<style>.' + sid + '-navset' + j + '{display:none;} #' + sid + '_s' + j + ':checked ~ .' + sid + '-inner .' + sid + '-navset' + j + '{display:flex;}</style>';
  }
  var navSets = images.map(function(img, i) {
    var prevIdx = i === 0 ? n : i;
    var nextIdx = i === n - 1 ? 1 : i + 2;
    // No inline style here: an inline `style` attribute always beats a class
    // selector in the cascade, so `style="display:contents"` would have
    // permanently overridden the :checked toggle above and left every
    // slide's nav arrows stacked at once (or effectively invisible) instead
    // of only the current slide's pair showing.
    return '<div class="' + sid + '-navset' + (i + 1) + '">' +
      '<label for="' + sid + '_s' + prevIdx + '" class="' + sid + '-nav ' + sid + '-prev">&#10094;</label>' +
      '<label for="' + sid + '_s' + nextIdx + '" class="' + sid + '-nav ' + sid + '-next">&#10095;</label>' +
      '</div>';
  }).join('');

  var slidesHtml = images.map(function(img, i) {
    var rowJson = _esc(JSON.stringify(img));
    var badgeCls = sid + '-badge' + (img.active ? ' ps-badge-active' : '');
    var badge = img.badge ? '<span class="' + badgeCls + '">' + _esc(img.badge) + '</span>' : '';
    var voters = img.starred_by_display ? '<div class="ps-voters">' + _esc(img.starred_by_display) + '</div>' : '';
    var price = img.price_display ? '<div class="ps-price">' + _esc(img.price_display) + '</div>' : '';
    var source = img.source_url ? '<a class="' + sid + '-source" href="' + _esc(img.source_url) +
      '" target="_blank" rel="noopener">Open source listing &#8599;</a>' : '';
    // data-ps-id, not just data-ps-slide's positional index: board:get
    // re-sorts candidates by star count on every call while voting is open
    // (surfaces this atom's own consumer), so array position for a given
    // candidate can shift the moment ANY vote lands — including the one you
    // just cast. The live-update counterpart (_a2uiUpdatePhotoStepper,
    // A2UIState.html) matches incoming rows to slides by THIS id, not by
    // index, so a re-sorted refresh still lands on the correct slide rather
    // than silently swapping in a different candidate's data underneath
    // whichever photo the radio's :checked state is currently showing.
    return '<div class="' + sid + '-slide" data-ps-slide="' + i + '" data-ps-id="' + _esc(String(img.id || '')) + '">' +
      '<img src="' + _esc(img.url || '') + '" alt="' + _esc(img.alt || '') + '" loading="lazy">' +
      badge +
      '<div class="' + sid + '-cap"><div class="ps-name">' + _esc(img.name || img.alt || '') + '</div>' +
      price + voters +
      '<button type="button" class="' + sid + '-vote" data-row-json="' + rowJson + '">' +
      (img.active ? '★ Starred — tap to unstar' : '☆ Star this one') + '</button>' +
      source +
      '</div></div>';
  }).join('');

  var counters = images.map(function(img, i) {
    return '<span class="' + sid + '-count ' + sid + '-count' + (i + 1) + '">' + (i + 1) + ' / ' + n + '</span>';
  }).join('');

  return css +
    '<label for="' + mid + '" class="' + sid + '-trigger">' +
    '<img src="' + _esc(first.url || '') + '" alt="" loading="lazy">' +
    '<span class="' + sid + '-trigger-label">' + _esc(triggerLabel) + ' &middot; ' + n + ' photos</span>' +
    '</label>' +
    '<input type="checkbox" id="' + mid + '">' +
    perSlide +
    '<div class="' + sid + '" data-photo-stepper="1">' + inputs +
    '<div class="' + sid + '-inner">' +
    '<div class="' + sid + '-topbar"><label for="' + mid + '" class="' + sid + '-close">&larr; Back</label>' + counters + '</div>' +
    navSets +
    '<div class="' + sid + '-track">' + slidesHtml + '</div>' +
    '</div></div>';
};
