/**
 * A2UI Gem Renderer
 *
 * Four modes:
 *   GET  ?p=BASE64       — decode base64 payload, render atoms (small schemas, shareable URL)
 *   POST ?p=JSON         — read raw JSON from form field (large schemas, no URL limit)
 *   GET  ?slide=<id>     — render Toulouse Airspace Command Deck slide with live METAR
 *   GET  (no params)     — serve the helper UI for pasting / encoding JSON
 */

// Current named-page slug being rendered — used by module_map to stamp &from= on ?p= child URLs
var _CURRENT_NAV_SLUG = '';

function _ga4PageView(nav, p) {
  // Wire up your own GA4 property: set measurement_id and api_secret below,
  // then uncomment the UrlFetchApp.fetch call.
  // var GA4_MEASUREMENT_ID = 'G-XXXXXXXXXX';
  // var GA4_API_SECRET     = 'YOUR_API_SECRET';
}

function doGet(e) {
  var p        = e && e.parameter && e.parameter.p;
  var slide    = e && e.parameter && e.parameter.slide;
  var deck     = e && e.parameter && e.parameter.deck;
  var debug    = e && e.parameter && e.parameter.debug;
  var makeDeck = e && e.parameter && e.parameter.makeDeck;
  var nav      = e && e.parameter && e.parameter.nav;
  var from     = e && e.parameter && e.parameter.from;
  _ga4PageView(nav, p);
  if (debug)   return _debugPage(debug);
  if (makeDeck !== undefined) return _makeDeckPage();
  if (deck)    return _renderDeckSlide(deck, slide || '');
  if (slide !== undefined) return _renderAirspaceSlide(slide);
  if (e && e.parameter && e.parameter.mode === 'builder') {
    return HtmlService.createHtmlOutputFromFile('PageBuilder')
      .setTitle('A2UI Page Builder')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }
  if (e && e.parameter && e.parameter.mode === 'screenshot' && p) {
    return _renderScreenshotPage(p);
  }
  if (nav === 'brevet-2026') return _renderBrevetPage();
  if (nav === 'nist-ai-rmf') return _renderNistAirmfPage();
  if (nav) return _renderNamedPage(nav, from || '');
  if (p) return _renderFromParam(p, from || '');
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('A2UI — Page Generator')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doPost(e) {
  var raw = e.parameter && e.parameter.p;
  if (!raw && e.postData) raw = e.postData.contents;
  if (!raw) return doGet(e);
  try {
    var payload = JSON.parse(raw);
    return _renderFromPayload(payload);
  } catch (err) {
    // Fallback: treat as base64
    return _renderFromParam(raw);
  }
}

function _renderFromParam(encoded, from) {
  try {
    // Restore stripped padding
    var padded = encoded;
    while (padded.length % 4 !== 0) padded += '=';
    var bytes = Utilities.base64DecodeWebSafe(padded);
    var json;
    // Detect gzip magic bytes (0x1f 0x8b) — new compressed URLs
    if (bytes.length >= 2 && bytes[0] === 31 && (bytes[1] & 0xFF) === 139) {
      json = Utilities.ungzip(Utilities.newBlob(bytes, 'application/x-gzip')).getDataAsString();
    } else {
      json = Utilities.newBlob(bytes).getDataAsString();
    }
    return _renderFromPayload(JSON.parse(json), from || '');
  } catch (err) {
    return _errorPage(err.message);
  }
}

function _renderFromPayload(payload, from) {
  try {
    var blocks  = Array.isArray(payload) ? payload : (payload.blocks || []);
    var title   = (Array.isArray(payload) ? '' : payload.title) || 'A2UI Page';
    var theme   = (Array.isArray(payload) ? 'light' : payload.theme) || 'light';

    // Register hub + cascade-save module pages into ScriptProperties.
    // hub_slug (explicit field) takes precedence over title-derived slug for stable back-nav.
    var hasModuleMap = blocks.some(function(b) { return b.type === 'module_map'; });
    if (hasModuleMap && !from) {
      var autoSlug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/, '');
      var hubSlug  = (!Array.isArray(payload) && payload.hub_slug)
        ? payload.hub_slug.toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
        : autoSlug;
      if (hubSlug) {
        try {
          var props   = PropertiesService.getScriptProperties();
          var hubEnc  = Utilities.base64EncodeWebSafe(
            Utilities.gzip(Utilities.newBlob(JSON.stringify(payload), 'application/json')).getBytes()
          ).replace(/=+$/, '');
          var hubMeta = JSON.stringify({ title: title, encoded: hubEnc, saved: new Date().toISOString() });
          // Always overwrite when hub_slug is explicit; first-visit-only for title-derived slugs
          if (hubMeta.length <= 9000 && (payload.hub_slug || !props.getProperty('nav:' + hubSlug))) {
            props.setProperty('nav:' + hubSlug, hubMeta);
          }
          _CURRENT_NAV_SLUG = hubSlug;
          // Cascade-save module pages so ?nav=<module.id> resolves even when modules used url fields
          blocks.forEach(function(b) {
            if (b.type !== 'module_map') return;
            (b.modules || []).forEach(function(m) {
              if (!m.page || !m.page.length || !m.id) return;
              try {
                var modPayload = { title: m.title || m.id, theme: theme, hub_slug: hubSlug, blocks: m.page };
                var modEnc     = Utilities.base64EncodeWebSafe(
                  Utilities.gzip(Utilities.newBlob(JSON.stringify(modPayload), 'application/json')).getBytes()
                ).replace(/=+$/, '');
                var modMeta    = JSON.stringify({ title: m.title || m.id, encoded: modEnc, saved: new Date().toISOString() });
                if (modMeta.length <= 9000) props.setProperty('nav:' + m.id, modMeta);
              } catch(me) {}
            });
          });
        } catch(e) {}
      }
    }

    var content = renderAtoms(blocks, { theme: theme });

    // Use fullscreen template for fullscreen airspace atoms, multi_surface, or any playbook containing one
    var needsFullscreen = blocks.some(function(b) {
      if (b.type === 'airspace_command_deck' && b.height === 'fullscreen') return true;
      if (b.type === 'multi_surface') return true;
      if (b.type === 'geo_europe_airspace') return true;
      if (b.type === 'geo_iso_takeoff') return true;
      if (b.type === 'geo_iso_rocket_launch') return true;
      if (b.type === 'geo_iso_heli_hover') return true;
      if (b.type === 'geo_iso_fleet') return true;
      if (b.type === 'playbook') {
        var allSlides = (b.slides || []);
        return allSlides.some(function(s) {
          return (s.blocks || []).some(function(sb) {
            return sb.type === 'airspace_command_deck' && sb.height === 'fullscreen';
          });
        });
      }
      return false;
    });

    if (needsFullscreen) {
      var fTmpl     = HtmlService.createTemplateFromFile('AirspaceFullscreen');
      fTmpl.title   = title;
      fTmpl.content = content;
      return fTmpl.evaluate()
        .setTitle(title)
        .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
    }

    var tmpl        = HtmlService.createTemplateFromFile('AtomPage');
    tmpl.title      = title;
    tmpl.content    = content;
    tmpl.theme      = theme;
    tmpl.sidebar    = false;
    tmpl.schemaJson = JSON.stringify(payload).replace(/<\//g, '<\\/');
    tmpl.navSlug    = '';
    tmpl.fromSlug   = from || '';
    tmpl.webAppUrl  = _getWebAppUrl();
    return tmpl.evaluate()
      .setTitle(title)
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  } catch (err) {
    return _errorPage(err.message);
  }
}

function _debugPage(target) {
  var lines = [];

  function probe(label, url, parse) {
    var t = Date.now();
    try {
      var r = UrlFetchApp.fetch(url, { muteHttpExceptions: true, followRedirects: true });
      var ms = Date.now() - t;
      var code = r.getResponseCode();
      var body = r.getContentText().trim();
      var ok = code >= 200 && code < 300;
      var preview = body.slice(0, 120).replace(/\n/g, ' ');
      lines.push((ok ? '✓' : '✗') + ' ' + label + ' — HTTP ' + code + ' (' + ms + 'ms)');
      if (ok && parse) {
        try { lines.push('  → ' + parse(body)); } catch(e) { lines.push('  parse err: ' + e.message); }
      } else if (!ok) {
        lines.push('  ' + preview);
      }
    } catch(e) {
      lines.push('✗ ' + label + ' — FAILED: ' + e.message.slice(0, 100));
    }
  }

  // ── ADS-B candidates ──────────────────────────────────────────────────────
  lines.push('=== ADS-B SOURCES ===');
  probe('adsb.lol (radius)',
    'https://api.adsb.lol/v2/lat/43.629/lon/1.363/dist/40',
    function(b) { var d=JSON.parse(b); return (d.ac||[]).length + ' aircraft'; });
  probe('airplanes.live (radius)',
    'https://api.airplanes.live/v2/lat/43.629/lon/1.363/dist/40',
    function(b) { var d=JSON.parse(b); return (d.ac||[]).length + ' aircraft'; });
  probe('opensky-network.org (bbox)',
    'https://opensky-network.org/api/states/all?lamin=43.1&lomin=0.7&lamax=44.2&lomax=2.0',
    function(b) { var d=JSON.parse(b); return (d.states||[]).length + ' states'; });
  probe('fr24 (via public feed)',
    'https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds=44.2,43.1,0.7,2.0&faa=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0',
    function(b) { var d=JSON.parse(b); return Object.keys(d).filter(function(k){return Array.isArray(d[k]);}).length + ' flights'; });

  lines.push('');

  // ── METAR candidates ──────────────────────────────────────────────────────
  lines.push('=== METAR SOURCES ===');
  probe('aviationweather.gov (api)',
    'https://aviationweather.gov/api/data/metar?ids=LFBO&format=raw&hours=1',
    function(b) { return b.split('\n')[0].trim().slice(0,80); });
  probe('aviationweather.gov (cgi)',
    'https://aviationweather.gov/cgi-bin/data/metar.php?ids=LFBO&hours=1&order=id,-obs&sep=true',
    function(b) { return b.trim().slice(0,80); });
  probe('NOAA tgftp (text file)',
    'https://tgftp.nws.noaa.gov/data/observations/metar/stations/LFBO.TXT',
    function(b) { return b.trim().split('\n').pop().trim().slice(0,80); });
  probe('vatsim metar',
    'https://metar.vatsim.net/metar.php?id=LFBO',
    function(b) { return b.trim().slice(0,80); });

  var escaped = lines.join('\n')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  var html = '<!DOCTYPE html><html><head><meta charset="UTF-8">' +
    '<style>body{background:#050810;color:#00f2ff;font-family:"Courier New",monospace;' +
    'padding:40px;font-size:0.8rem;line-height:1.9;margin:0;}' +
    'h2{color:#00ff41;margin-bottom:20px;font-size:1rem;letter-spacing:0.1em;}' +
    'pre{white-space:pre-wrap;word-break:break-all;}' +
    'footer{opacity:0.35;font-size:0.65rem;margin-top:24px;display:block;}</style>' +
    '</head><body><h2>A2UI — API CONNECTIVITY PROBE</h2>' +
    '<pre>' + escaped + '</pre>' +
    '<footer>checkmark = reachable from GAS   x = blocked/failed</footer>' +
    '</body></html>';
  return HtmlService.createHtmlOutput(html).setTitle('A2UI Debug');
}

function _errorPage(msg) {
  return HtmlService.createHtmlOutput(
    '<body style="font-family:monospace;padding:40px;background:#0a0f1e;color:#ef4444">' +
    '<h2>Render error</h2><pre>' + msg + '</pre>' +
    '<p><a href="' + ScriptApp.getService().getUrl() + '" style="color:#60a5fa">← Back to generator</a></p>' +
    '</body>'
  ).setTitle('Render error');
}

// ── Screenshot / LinkedIn card page ──────────────────────────────────────────

function _renderScreenshotPage(encoded) {
  try {
    var padded = encoded;
    while (padded.length % 4 !== 0) padded += '=';
    var bytes = Utilities.base64DecodeWebSafe(padded);
    var json;
    if (bytes.length >= 2 && bytes[0] === 31 && (bytes[1] & 0xFF) === 139) {
      json = Utilities.ungzip(Utilities.newBlob(bytes, 'application/x-gzip')).getDataAsString();
    } else {
      json = Utilities.newBlob(bytes).getDataAsString();
    }
    var payload = JSON.parse(json);
    var blocks  = Array.isArray(payload) ? payload : (payload.blocks || []);
    var content = renderAtoms(blocks, { theme: 'light' });
    var tmpl = HtmlService.createTemplateFromFile('LinkedInPage');
    tmpl.content = content;
    return tmpl.evaluate()
      .setTitle('LinkedIn Card')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  } catch (err) {
    return _errorPage(err.message);
  }
}

// ── Named page nav system ─────────────────────────────────────────────────────

function _getWebAppUrl() {
  try { return ScriptApp.getService().getUrl(); } catch(e) { return ''; }
}

// Save a page under a slug. Accepts the same gzip+base64 encoded string
// that callGemini() returns as `encoded`. Callable from PageBuilder via google.script.run.
function a2uiNavSave(slug, title, encoded) {
  if (!slug || !encoded) return { error: 'slug and encoded are required' };
  slug = slug.toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/-+/g, '-');
  var props = PropertiesService.getScriptProperties();
  var meta  = JSON.stringify({ title: title || slug, encoded: encoded, saved: new Date().toISOString() });
  if (meta.length > 9000) return { error: 'Page payload too large to store (' + meta.length + ' chars). Try fewer atoms.' };
  props.setProperty('nav:' + slug, meta);
  return { url: _getWebAppUrl() + '?nav=' + slug, slug: slug };
}

// List all saved named pages. Callable from PageBuilder.
function a2uiNavList() {
  var props = PropertiesService.getScriptProperties();
  var all   = props.getProperties();
  return Object.keys(all)
    .filter(function(k) { return k.indexOf('nav:') === 0; })
    .map(function(k) {
      try {
        var m = JSON.parse(all[k]);
        return { slug: k.slice(4), title: m.title, saved: m.saved };
      } catch(e) { return { slug: k.slice(4), title: k.slice(4), saved: '' }; }
    })
    .sort(function(a, b) { return b.saved.localeCompare(a.saved); });
}

// Delete a named page.
function a2uiNavDelete(slug) {
  PropertiesService.getScriptProperties().deleteProperty('nav:' + slug);
  return true;
}

// Serve a named page, with optional from-slug for the back button.
function _renderNamedPage(slug, from) {
  _CURRENT_NAV_SLUG = slug; // allows module_map to stamp &from=<slug> on child ?p= URLs
  var props = PropertiesService.getScriptProperties();
  var raw   = props.getProperty('nav:' + slug);
  if (!raw) return _errorPage('Page not found: "' + slug + '". Save it first via the Page Builder.');
  try {
    var meta    = JSON.parse(raw);
    var decoded = _renderFromParam(meta.encoded);
    // _renderFromParam returns an HtmlOutput — we need to re-render with nav context
    // Re-decode to get the payload JSON and render properly with nav vars
    var enc     = meta.encoded;
    var padded  = enc;
    while (padded.length % 4 !== 0) padded += '=';
    var bytes   = Utilities.base64DecodeWebSafe(padded);
    var json    = (bytes.length >= 2 && bytes[0] === 31 && (bytes[1] & 0xFF) === 139)
      ? Utilities.ungzip(Utilities.newBlob(bytes, 'application/x-gzip')).getDataAsString()
      : Utilities.newBlob(bytes).getDataAsString();
    var payload = JSON.parse(json);
    var blocks  = Array.isArray(payload) ? payload : (payload.blocks || []);
    var title   = meta.title || payload.title || slug;
    var theme   = (Array.isArray(payload) ? 'light' : payload.theme) || 'light';
    var content = renderAtoms(blocks, { theme: theme });
    var webAppUrl = _getWebAppUrl();

    var tmpl        = HtmlService.createTemplateFromFile('AtomPage');
    tmpl.title      = title;
    tmpl.content    = content;
    tmpl.theme      = theme;
    tmpl.sidebar    = false;
    tmpl.schemaJson = JSON.stringify(payload).replace(/<\//g, '<\\/');
    tmpl.navSlug    = slug;
    tmpl.fromSlug   = from || '';
    tmpl.webAppUrl  = webAppUrl;
    return tmpl.evaluate()
      .setTitle(title)
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  } catch(err) {
    return _errorPage('Failed to render "' + slug + '": ' + err.message);
  }
}

/** Called by AtomPage.html to include partial files. */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * Export the renderer script to the deployer's Drive under "a2ui apps script exports",
 * shared with anyone-with-link so users can open it and File > Make a copy.
 * Returns { url, name } on success or { error } on failure.
 */
function exportScript() {
  try {
    var folderName = 'a2ui apps script exports';
    var copyName   = 'A2UI Schema Renderer';

    // Get or create the exports folder
    var fi = DriveApp.getFoldersByName(folderName);
    var folder = fi.hasNext() ? fi.next() : DriveApp.createFolder(folderName);

    // Reuse existing copy if already exported (avoid duplicates)
    var existing = folder.getFilesByName(copyName);
    var copy = existing.hasNext() ? existing.next() : DriveApp.getFileById(ScriptApp.getScriptId()).makeCopy(copyName, folder);

    // Share with anyone who has the link (view only — they can File > Make a copy)
    copy.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

    return { url: copy.getUrl(), name: copyName };
  } catch (e) {
    return { error: e.toString() };
  }
}

// ── Toulouse Airspace Command Deck ────────────────────────────────────────────

/**
 * Generic surface fetch callable from the client via google.script.run.fetchDataSource().
 * This is the GAS surface transport layer for all data_source / adsb_feed / metar_feed atoms.
 * On other surfaces (browser fetch, Python requests) this function would not exist —
 * the atom's client-side JS would call the appropriate transport directly.
 */
function fetchDataSource(url, format, path) {
  try {
    var resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) return null;
    var text = resp.getContentText();
    var data = format === 'json' ? JSON.parse(text) : text.trim();
    if (path) path.split('.').forEach(function(k) { if (data && k) data = data[k]; });
    return data;
  } catch (err) { return null; }
}

/** Kept for backward compatibility — thin wrapper around _parseMETAR + fetchDataSource. */
function fetchMETAR() {
  var raw = fetchDataSource(
    'https://aviationweather.gov/api/data/metar?ids=LFBO&format=raw&hours=1',
    'text', ''
  );
  return raw ? _parseMETAR(raw.split('\n')[0]) : { wind: '—', temp: '—', qnh: '—', raw: '' };
}

/** Renders one slide from the Toulouse Airspace playbook with live METAR interpolation. */
function _renderAirspaceSlide(slideId) {
  var playbook = _getToulousePlaybook();
  var slide    = null;
  for (var i = 0; i < playbook.length; i++) {
    if (!slideId || playbook[i].id === slideId) { slide = playbook[i]; break; }
  }
  if (!slide) slide = playbook[0];

  var wx   = fetchMETAR();
  var tags = {
    '{{weather.wind}}':     wx.wind,
    '{{weather.temp}}':     wx.temp,
    '{{weather.pressure}}': wx.qnh,
    '{{weather.raw}}':      wx.raw
  };

  function interp(val) {
    if (typeof val !== 'string') return val;
    for (var tag in tags) val = val.split(tag).join(tags[tag]);
    return val;
  }

  var block = { type: 'airspace_command_deck' };
  var skip  = { id: 1, label: 1, template: 1, data: 1 };
  for (var key in slide) {
    if (skip[key]) continue;
    var v = slide[key];
    if (typeof v === 'string') v = interp(v);
    else if (Array.isArray(v)) v = v.map(function(x) { return interp(x); });
    block[key] = v;
  }

  var baseUrl = ScriptApp.getService().getUrl();
  var nav = '<div style="position:fixed;bottom:20px;left:50%;transform:translateX(-50%);' +
    'display:flex;gap:8px;z-index:999;flex-wrap:wrap;justify-content:center;' +
    'background:rgba(0,0,0,0.8);border:1px solid rgba(0,242,255,0.18);' +
    'border-radius:10px;padding:8px 14px;backdrop-filter:blur(12px);">';
  for (var si = 0; si < playbook.length; si++) {
    var s   = playbook[si];
    var act = s.id === slide.id;
    nav += '<a href="' + baseUrl + '?slide=' + s.id + '" ' +
      'style="font-family:\'Courier New\',monospace;font-size:0.75rem;' +
      'padding:6px 14px;border-radius:6px;text-decoration:none;white-space:nowrap;' +
      'background:' + (act ? 'rgba(0,242,255,0.18)' : 'transparent') + ';' +
      'border:1px solid ' + (act ? 'rgba(0,242,255,0.5)' : 'rgba(255,255,255,0.1)') + ';' +
      'color:' + (act ? '#00f2ff' : 'rgba(255,255,255,0.5)') + ';' +
      'transition:all 0.15s;">' +
      _esc(s.label || s.id) + '</a>';
  }
  nav += '</div>';

  block.height         = 'fullscreen';
  block.data_source    = 'adsb';
  block.weather_source = 'metar_lfbo';

  // Data atoms first — they run server-side fetches and set up client refresh.
  // Visual atom subscribes to the named feeds via window.A2UI_CALLBACKS.
  var blocks = [
    { type: 'adsb_feed',   name: 'adsb',      refresh: 15 },
    { type: 'metar_feed',  name: 'metar_lfbo', station: 'LFBO', refresh: 60 },
    block
  ];
  var content  = renderAtoms(blocks, { theme: 'dark' }) + nav;
  var tmpl     = HtmlService.createTemplateFromFile('AirspaceFullscreen');
  tmpl.title   = slide.chyron_title || 'Toulouse Airspace';
  tmpl.content = content;
  return tmpl.evaluate()
    .setTitle(tmpl.title)
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Renders a slide from a base64-encoded playbook passed in the URL.
 * URL format: ?deck=BASE64&slide=SLIDE_ID
 * Nav links embed the same BASE64 so the deck is fully self-contained.
 */
function _renderDeckSlide(deckEncoded, slideId) {
  var playbook;
  try {
    var bytes = Utilities.base64Decode(deckEncoded, Utilities.Charset.UTF_8);
    playbook  = JSON.parse(Utilities.newBlob(bytes).getDataAsString());
  } catch(e) { return _errorPage('Invalid deck encoding: ' + e.message); }

  var slide = null;
  for (var i = 0; i < playbook.length; i++) {
    if (!slideId || playbook[i].id === slideId) { slide = playbook[i]; break; }
  }
  if (!slide) slide = playbook[0];

  var wx   = fetchMETAR();
  var tags = {
    '{{weather.wind}}':     wx.wind,
    '{{weather.temp}}':     wx.temp,
    '{{weather.pressure}}': wx.qnh,
    '{{weather.raw}}':      wx.raw
  };
  function interp(val) {
    if (typeof val !== 'string') return val;
    for (var tag in tags) val = val.split(tag).join(tags[tag]);
    return val;
  }

  var block = { type: 'airspace_command_deck', height: 'fullscreen',
                data_source: 'adsb', weather_source: 'metar_lfbo' };
  var skip  = { id: 1, label: 1, template: 1 };
  for (var key in slide) {
    if (skip[key]) continue;
    var v = slide[key];
    if (typeof v === 'string') v = interp(v);
    else if (Array.isArray(v)) v = v.map(function(x) { return interp(x); });
    block[key] = v;
  }

  var baseUrl = ScriptApp.getService().getUrl();
  var nav = '<div style="position:fixed;bottom:20px;left:50%;transform:translateX(-50%);' +
    'display:flex;gap:8px;z-index:999;flex-wrap:wrap;justify-content:center;' +
    'background:rgba(0,0,0,0.8);border:1px solid rgba(0,242,255,0.18);' +
    'border-radius:10px;padding:8px 14px;backdrop-filter:blur(12px);">';
  for (var si = 0; si < playbook.length; si++) {
    var s   = playbook[si];
    var act = s.id === slide.id;
    nav += '<a href="' + baseUrl + '?deck=' + deckEncoded + '&slide=' + s.id + '" ' +
      'style="font-family:\'Courier New\',monospace;font-size:0.75rem;' +
      'padding:6px 14px;border-radius:6px;text-decoration:none;white-space:nowrap;' +
      'background:' + (act ? 'rgba(0,242,255,0.18)' : 'transparent') + ';' +
      'border:1px solid ' + (act ? 'rgba(0,242,255,0.5)' : 'rgba(255,255,255,0.1)') + ';' +
      'color:' + (act ? '#00f2ff' : 'rgba(255,255,255,0.5)') + ';' +
      'transition:all 0.15s;">' + _esc(s.label || s.id) + '</a>';
  }
  nav += '</div>';

  var blocks  = [
    { type: 'adsb_feed',  name: 'adsb',       refresh: 15 },
    { type: 'metar_feed', name: 'metar_lfbo',  station: 'LFBO', refresh: 60 },
    block
  ];
  var content = renderAtoms(blocks, { theme: 'dark' }) + nav;
  var tmpl    = HtmlService.createTemplateFromFile('AirspaceFullscreen');
  tmpl.title  = slide.chyron_title || slide.label || 'Airspace';
  tmpl.content = content;
  return tmpl.evaluate()
    .setTitle(tmpl.title)
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/** ?makeDeck — encodes the Toulouse playbook and returns the shareable ?deck= URL. */
function _makeDeckPage() {
  var playbook = _getToulousePlaybook();
  var encoded  = Utilities.base64EncodeWebSafe(
    Utilities.newBlob(JSON.stringify(playbook)).getBytes()
  );
  var base     = ScriptApp.getService().getUrl();
  var url      = base + '?deck=' + encoded;
  var lines    = ['Shareable deck URL (open any slide by appending &slide=ID):', '', url, ''];
  playbook.forEach(function(s) {
    lines.push(s.id + ':');
    lines.push('  ' + url + '&slide=' + s.id);
    lines.push('');
  });
  var escaped = lines.join('\n').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  var html = '<!DOCTYPE html><html><head><meta charset="UTF-8">' +
    '<style>body{background:#050810;color:#00f2ff;font-family:"Courier New",monospace;' +
    'padding:40px;font-size:0.8rem;line-height:1.8;margin:0;}' +
    'h2{color:#00ff41;margin-bottom:20px;}pre{white-space:pre-wrap;word-break:break-all;}</style>' +
    '</head><body><h2>A2UI — DECK ENCODER</h2><pre>' + escaped + '</pre></body></html>';
  return HtmlService.createHtmlOutput(html).setTitle('Deck URL');
}

/** Inline compiled playbook — source of truth is toulouse_airspace.yaml */
function _getToulousePlaybook() {
  return [
    {
      id: 'calibration', label: '📡 Sweep Calibration', template: 'airspace_command_deck',
      show_slate: true,
      slate_title: '📡 TLS Sector 32L/R Sweep Calibration',
      slate_description: 'Booting transponder tracking matrix and aligning primary S-Band receivers...'
    },
    {
      id: 'clean_deck', label: '✈️ Live Traffic', template: 'airspace_command_deck',
      zoom: 35, chyron_title: 'LFBO TMA — LIVE TRAFFIC',
      chyron_subtitle: 'Runway 32L/R Active • {{weather.wind}} • QNH {{weather.pressure}}',
      ticker_text: '✈️ TOULOUSE BLAGNAC APPROACH CONTROL • RUNWAY 32L/R ACTIVE • SURFACE WIND: {{weather.wind}} • TEMP: {{weather.temp}} • QNH: {{weather.pressure}} • RAW METAR: {{weather.raw}} •',
      ticker_speed: 45
    },
    {
      id: 'supervisor_deck', label: '📡 Sector Control', template: 'airspace_command_deck',
      zoom: 35, panel_type: 'supervisor', panel_title: '📡 Tactical Supervisor HUD',
      chyron_title: 'LFBO TMA APPROACH CONTROL',
      chyron_subtitle: 'Active Approach Vectors Runway 32L/R',
      ticker_text: '📍 LFBO Terminal Information • RUNWAY 32L/R ACTIVE • SURFACE WIND: {{weather.wind}} • TEMP: {{weather.temp}} • QNH: {{weather.pressure}} • RAW METAR: {{weather.raw}} •',
      ticker_speed: 50
    },
    {
      id: 'locked_target', label: '🎯 Target Lock AFR6129', template: 'airspace_command_deck',
      zoom: 22, panel_type: 'target', panel_title: '🎯 Active Target Profiler',
      lockedCallsign: 'AFR6129',
      chyron_title: 'TARGET ACQUIRED: AFR6129',
      chyron_subtitle: 'Tracking Descent Profile and Instrument Glide Slope Runway 32L',
      ticker_text: '📍 LFBO Terminal Information • RUNWAY 32L/R ACTIVE • SURFACE WIND: {{weather.wind}} • TEMP: {{weather.temp}} • QNH: {{weather.pressure}} • RAW METAR: {{weather.raw}} •',
      ticker_speed: 50
    },
    {
      id: 'corridor_map', label: '🗺️ Airway Map', template: 'airspace_command_deck',
      zoom: 35, panel_type: 'supervisor', panel_title: '📡 Supervisor Live Console',
      chyron_title: 'LFBO TMA AIRWAY NETWORKS',
      chyron_subtitle: 'Standard Terminal Arrival Paths & Intercept Vectors Map',
      ticker_text: '📍 LFBO Terminal Information • RUNWAY 32L/R ACTIVE • SURFACE WIND: {{weather.wind}} • TEMP: {{weather.temp}} • QNH: {{weather.pressure}} • RAW METAR: {{weather.raw}} •',
      ticker_speed: 50
    },
    {
      id: 'separation_poll', label: '🗳️ Separation Poll', template: 'airspace_command_deck',
      zoom: 35, panel_type: 'supervisor', panel_title: '📡 Supervisor Live Console',
      chyron_title: 'TMA CONFLICT RESOLUTION',
      chyron_subtitle: 'Select separation maneuvers and runway vector allocation',
      ticker_text: '📍 LFBO Terminal Information • RUNWAY 32L/R ACTIVE • SURFACE WIND: {{weather.wind}} • TEMP: {{weather.temp}} • QNH: {{weather.pressure}} • RAW METAR: {{weather.raw}} •',
      ticker_speed: 50,
      poll_question: 'TMA Direction: Resolve separation conflict? 🗳️',
      poll_options: [
        'Establish parallel simultaneous visual arrivals Runway 32L/R',
        'Vector RYR109B to enter holding pattern at TOU VOR',
        'Instruct EZY4218 to reduce speed to minimum 180kt'
      ],
      poll_values: [12, 8, 4]
    }
  ];
}

// ── Workspace context ─────────────────────────────────────────────────────────

function getWorkspaceContext() {
  var ctx = { userEmail: '', userName: '', calendar: [], gmailUnread: 0 };
  try { ctx.userEmail = Session.getActiveUser().getEmail(); } catch(e) {}
  try { ctx.userName  = ctx.userEmail.split('@')[0]; } catch(e) {}
  try {
    var now     = new Date();
    var weekEnd = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    var events  = CalendarApp.getDefaultCalendar().getEvents(now, weekEnd);
    ctx.calendar = events.slice(0, 8).map(function(ev) {
      return {
        title:    ev.getTitle(),
        start:    ev.getStartTime().toISOString(),
        end:      ev.getEndTime().toISOString(),
        location: ev.getLocation() || ''
      };
    });
  } catch(e) {}
  try { ctx.gmailUnread = GmailApp.getInboxUnreadCount(); } catch(e) {}
  return ctx;
}

// ── URL inspector / decoder ───────────────────────────────────────────────────

function encodePayload(jsonStr) {
  try {
    var obj = JSON.parse(jsonStr);
    var clean = JSON.stringify(obj);
    var enc = Utilities.base64EncodeWebSafe(
      Utilities.gzip(Utilities.newBlob(clean, 'application/json')).getBytes()
    ).replace(/=+$/, '');
    var url = _getWebAppUrl() + '?p=' + enc;
    return { url: url, encoded: enc };
  } catch(e) {
    return { error: e.message };
  }
}

function a2uiNavInspect(slug) {
  try {
    var props = PropertiesService.getScriptProperties();
    var raw   = props.getProperty('nav:' + slug);
    if (!raw) return { error: 'Not found: ' + slug };
    var payload = decodePageUrl(raw);
    return payload;
  } catch(e) {
    return { error: e.message };
  }
}

function a2uiNavRename(oldSlug, newSlug) {
  try {
    newSlug = newSlug.trim().toLowerCase().replace(/[^a-z0-9-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
    if (!newSlug) return { error: 'Invalid slug' };
    var props = PropertiesService.getScriptProperties();
    var raw   = props.getProperty('nav:' + oldSlug);
    if (!raw) return { error: 'Not found: ' + oldSlug };
    if (props.getProperty('nav:' + newSlug)) return { error: 'Slug already exists: ' + newSlug };
    props.setProperty('nav:' + newSlug, raw);
    props.deleteProperty('nav:' + oldSlug);
    var url = _getWebAppUrl() + '?nav=' + newSlug;
    return { ok: true, slug: newSlug, url: url };
  } catch(e) {
    return { error: e.message };
  }
}

function decodePageUrl(encoded) {
  try {
    // Accept full URL or just the p= value
    var val = encoded.trim();
    var m   = val.match(/[?&]p=([^&]+)/);
    if (m) val = m[1];
    var padded = val;
    while (padded.length % 4 !== 0) padded += '=';
    var bytes = Utilities.base64DecodeWebSafe(padded);
    var json;
    if (bytes.length >= 2 && bytes[0] === 31 && (bytes[1] & 0xFF) === 139) {
      json = Utilities.ungzip(Utilities.newBlob(bytes, 'application/x-gzip')).getDataAsString();
    } else {
      json = Utilities.newBlob(bytes).getDataAsString();
    }
    var obj = JSON.parse(json);
    return { json: obj, raw: json };
  } catch(e) {
    return { error: e.message };
  }
}

// ── LMS Progress Store ────────────────────────────────────────────────────────
// Server-side read/write for progress_store atom.
// Each course gets its own Sheet named "A2UI Progress: <courseId>".
// Rows: [email, progress_json, updated_at]

function a2uiProgressRead(courseId) {
  try {
    var email = Session.getActiveUser().getEmail();
    var sheet = _lmsGetSheet_(courseId);
    var data  = sheet.getDataRange().getValues();
    for (var i = 1; i < data.length; i++) {
      if (data[i][0] === email) {
        return JSON.parse(data[i][1] || '{}');
      }
    }
    return {};
  } catch(e) { return {}; }
}

function a2uiProgressWrite(courseId, progressData) {
  try {
    var email = Session.getActiveUser().getEmail();
    var sheet = _lmsGetSheet_(courseId);
    var data  = sheet.getDataRange().getValues();
    var json  = JSON.stringify(progressData);
    var now   = new Date().toISOString();
    for (var i = 1; i < data.length; i++) {
      if (data[i][0] === email) {
        sheet.getRange(i + 1, 2, 1, 2).setValues([[json, now]]);
        return true;
      }
    }
    sheet.appendRow([email, json, now]);
    return true;
  } catch(e) { return false; }
}

function _lmsGetSheet_(courseId) {
  var name  = 'A2UI Progress: ' + courseId;
  var files = DriveApp.searchFiles(
    'title = "' + name.replace(/"/g, '\\"') + '" and ' +
    'mimeType = "application/vnd.google-apps.spreadsheet" and trashed = false'
  );
  if (files.hasNext()) {
    return SpreadsheetApp.open(files.next()).getActiveSheet();
  }
  var ss    = SpreadsheetApp.create(name);
  var sheet = ss.getActiveSheet();
  sheet.appendRow(['email', 'progress_json', 'updated_at']);
  sheet.setFrozenRows(1);
  return sheet;
}

// Read the full cohort progress for a course (instructor view).
// Returns array of {email, progress, updated_at}.
function a2uiCohortRead(courseId) {
  try {
    var sheet = _lmsGetSheet_(courseId);
    var data  = sheet.getDataRange().getValues();
    var rows  = [];
    for (var i = 1; i < data.length; i++) {
      if (!data[i][0]) continue;
      var prog = {};
      try { prog = JSON.parse(data[i][1] || '{}'); } catch(e) {}
      rows.push({ email: data[i][0], progress: prog, updated_at: data[i][2] });
    }
    return rows;
  } catch(e) { return []; }
}
