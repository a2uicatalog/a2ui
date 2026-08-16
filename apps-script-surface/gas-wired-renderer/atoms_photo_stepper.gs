// atoms_photo_stepper.gs — one photo full-size at a time, prev/next, a vote
// button per slide, and a live "who's voted" line. Sibling of photo_grid
// (same reasoning: a photo-driven decision needs the thing you're looking
// at and the thing you act on to be the same element), for the case
// photo_grid does not cover — reviewing options ONE AT A TIME rather than
// scanning a grid, both real and complementary, not a replacement for
// each other.
//
// Paging is the SAME pure-CSS radio-input trick `carousel` already uses
// (sibling :checked selectors drive the slide transform) — no JS state to
// go stale, no index to lose. That is also why the live-update counterpart
// (_a2uiUpdatePhotoStepper, A2UIState.html) patches each slide's badge/
// caption text IN PLACE rather than rebuilding the DOM: touching the
// radio/track markup would reset whichever slide the radio's own browser-
// owned :checked state is currently showing, exactly the "vote resets you
// back to photo 1" bug this design avoids by construction.
//
// The vote button on each slide reuses photo_grid's click contract exactly
// (data-row-json + the same generalised [data-row-json] binder in
// A2UIState.html) — not a new mechanism, the third consumer of the same
// one.
_RENDERERS['photo_stepper'] = function(b) {
  var images = b.images || b.rows || [];
  if (!images.length) return '<p style="color:#94a3b8;font-style:italic;">Nothing to show yet.</p>';
  var accent = b.accent || '#0f766e';
  var sid = 'ps' + Math.random().toString(36).substr(2, 6);
  var n = images.length;

  var css = '<style>' +
    '.' + sid + '{position:relative;overflow:hidden;border-radius:12px;background:#111;margin:12px 0;}' +
    '.' + sid + ' input[type=radio]{display:none;}' +
    '.' + sid + '-track{display:flex;transition:transform 0.35s ease;width:' + (n * 100) + '%;}' +
    '.' + sid + '-slide{width:' + (100 / n) + '%;flex:0 0 ' + (100 / n) + '%;position:relative;}' +
    '.' + sid + '-slide img{width:100%;display:block;max-height:70vh;object-fit:contain;background:#000;}' +
    '.' + sid + '-cap{padding:14px 16px;background:#1a1a1a;color:#fff;}' +
    '.' + sid + '-cap .ps-name{font-size:0.95rem;font-weight:600;}' +
    '.' + sid + '-cap .ps-price{color:#9ca3af;font-size:0.82rem;margin-top:2px;}' +
    '.' + sid + '-cap .ps-voters{color:#9ca3af;font-size:0.78rem;margin-top:6px;}' +
    '.' + sid + '-badge{position:absolute;top:10px;right:10px;background:rgba(0,0,0,0.65);color:#fff;font-size:0.78rem;font-weight:700;padding:3px 9px;border-radius:99px;}' +
    '.' + sid + '-badge.ps-badge-active{background:' + accent + ';color:#fff;}' +
    '.' + sid + '-vote{margin-top:10px;display:inline-block;background:' + accent + ';color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:0.85rem;font-weight:600;cursor:pointer;}' +
    '.' + sid + '-source{margin-top:10px;margin-left:10px;display:inline-block;color:#9ca3af;font-size:0.82rem;text-decoration:underline;}' +
    '.' + sid + '-nav{position:absolute;top:0;bottom:64px;width:15%;display:flex;align-items:center;justify-content:center;font-size:2rem;color:rgba(255,255,255,0.55);cursor:pointer;user-select:none;}' +
    '.' + sid + '-nav:hover{color:rgba(255,255,255,0.9);}' +
    '.' + sid + '-prev{left:0;} .' + sid + '-next{right:0;}' +
    '.' + sid + '-count{position:absolute;top:10px;left:10px;background:rgba(0,0,0,0.65);color:#fff;font-size:0.75rem;padding:3px 9px;border-radius:99px;}' +
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
    return '<div class="' + sid + '-navset' + (i + 1) + '" style="display:contents;">' +
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
    return '<div class="' + sid + '-slide" data-ps-slide="' + i + '">' +
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

  return css + perSlide +
    '<div class="' + sid + '" data-photo-stepper="1">' + inputs +
    '<div class="' + sid + '-inner">' + counters + navSets +
    '<div class="' + sid + '-track">' + slidesHtml + '</div>' +
    '</div></div>';
};
