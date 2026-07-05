// atoms_data.gs — Data source / feed atoms
//
// PARADIGM:
//   Data atoms are declarative specs — they describe WHAT to fetch and in what shape.
//   The surface provides the HOW:
//     GAS surface  → UrlFetchApp (server-side, no CORS) + google.script.run (client refresh)
//     Web surface  → fetch() / XHR (future)
//     Python       → requests (future)
//
// BINDING:
//   Data atoms publish to window.A2UI_DATA[name] and call window.A2UI_CALLBACKS[name].
//   Visual atoms subscribe by setting window.A2UI_CALLBACKS[name] = function(data){...}
//   Dispatch is deferred 80ms so all atom scripts can register their callbacks first.
//
// SERVER-SIDE CACHING:
//   adsb_feed and metar_feed use CacheService (15s TTL) to avoid hitting external APIs
//   on every page load — OpenSky rate limit is 400 req/day unauthenticated.

// ── firestore_read server-side callable ──────────────────────────────────────
// Called from client via google.script.run.fetchFirestoreDoc(project, collection, docId).
// Returns deserialized plain JS object, or null on error.
// Requires: oauthScopes includes https://www.googleapis.com/auth/datastore

function fetchFirestoreDoc(project, collection, docId) {
  var token = ScriptApp.getOAuthToken();
  var url   = 'https://firestore.googleapis.com/v1/projects/' + project +
              '/databases/(default)/documents/' + collection + '/' + docId;
  try {
    var resp = UrlFetchApp.fetch(url, {
      headers: { Authorization: 'Bearer ' + token },
      muteHttpExceptions: true
    });
    if (resp.getResponseCode() !== 200) return null;
    return _fsDoc(JSON.parse(resp.getContentText()).fields);
  } catch(e) { return null; }
}

function _fsDoc(fields) {
  if (!fields) return null;
  var out = {};
  for (var k in fields) out[k] = _fsVal(fields[k]);
  return out;
}
function _fsVal(v) {
  if (!v) return null;
  if ('stringValue'  in v) return v.stringValue;
  if ('integerValue' in v) return parseInt(v.integerValue);
  if ('doubleValue'  in v) return v.doubleValue;
  if ('booleanValue' in v) return v.booleanValue;
  if ('nullValue'    in v) return null;
  if ('arrayValue'   in v) return (v.arrayValue.values || []).map(_fsVal);
  if ('mapValue'     in v) return _fsDoc(v.mapValue.fields);
  return null;
}

// ── Shared server-side helpers ────────────────────────────────────────────────

function _parseMETAR(raw) {
  if (!raw) return { wind: '—', temp: '—', qnh: '—', raw: '' };
  var wm = raw.match(/(VRB|\d{3})(\d{2})(G\d{2})?KT/);
  var tm = raw.match(/\s(M?\d{2})\/(M?\d{2})\s/);
  var qm = raw.match(/Q(\d{4})/);
  return {
    wind: wm ? (wm[1] === 'VRB' ? 'VRB' : wm[1] + '°') + '/' + wm[2] + 'kt' +
               (wm[3] ? ' gust ' + wm[3].slice(1) + 'kt' : '') : '—',
    temp: tm ? tm[1].replace('M', '-') + '°C' : '—',
    qnh:  qm ? qm[1] + ' hPa' : '—',
    raw:  raw
  };
}

function _normaliseOpenSky(raw, filterGnd) {
  if (!raw || !raw.states) return [];
  return raw.states.map(function(s) {
    return {
      callsign:  (s[1]  || '').trim(),
      lat:        s[6],
      lon:        s[5],
      alt_ft:     s[7]  ? Math.round(s[7]  * 3.281) : 0,
      spd_kt:     s[9]  ? Math.round(s[9]  * 1.944) : 0,
      hdg:        s[10] || 0,
      on_ground:  !!s[8],
      squawk:     s[14] || ''
    };
  }).filter(function(f) {
    return f.callsign && f.lat !== null && f.lon !== null &&
           (!filterGnd || !f.on_ground);
  });
}

// adsb.lol format: { ac: [{flight, lat, lon, alt_baro, gs, track, squawk, ...}] }
function _normaliseAdsbLol(raw, filterGnd) {
  if (!raw || !raw.ac) return [];
  return raw.ac.map(function(a) {
    var altFt = (typeof a.alt_baro === 'number') ? a.alt_baro : 0;
    return {
      callsign:  (a.flight || a.hex || '').trim(),
      lat:        a.lat,
      lon:        a.lon,
      alt_ft:     altFt,
      spd_kt:     a.gs   || 0,
      hdg:        a.track || 0,
      on_ground:  a.alt_baro === 'ground' || altFt < 50,
      squawk:     a.squawk || ''
    };
  }).filter(function(f) {
    return f.callsign && f.lat !== undefined && f.lon !== undefined &&
           (!filterGnd || !f.on_ground);
  });
}

// Generic surface fetch used by all data atoms (caches by URL key)
function _surfaceFetch(url, cacheKey, ttl) {
  var cache = CacheService.getScriptCache();
  var hit   = cache.get(cacheKey);
  if (hit) return hit;
  try {
    var resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    if (resp.getResponseCode() === 200) {
      var body = resp.getContentText();
      cache.put(cacheKey, body, ttl || 15);
      return body;
    }
  } catch(e) {}
  return null;
}

// ── feed_status ───────────────────────────────────────────────────────────────
// Inline pill indicator — green LIVE (N) or red SIM — for any named feed.
// Chains onto existing window.A2UI_CALLBACKS[name] so it doesn't break other subscribers.
// Use anywhere on a page to surface whether a data atom is receiving real data.
//
// Fields:
//   name   — feed name to watch (required)
//   label  — optional text prefix shown before the status (e.g. "ADS-B")
//   size   — font-size (default 0.6rem)
_RENDERERS['feed_status'] = function(b) {
  var uid   = 'fs' + Math.random().toString(36).substr(2, 5);
  var name  = b.name  || '';
  var label = b.label ? _esc(b.label) + ' ' : '';
  var size  = b.size  || '0.6rem';

  var pill =
    '<span id="' + uid + '" style="display:inline-flex;align-items:center;gap:5px;' +
      'font-family:\'Courier New\',monospace;font-size:' + size + ';letter-spacing:0.08em;' +
      'padding:3px 9px;border-radius:100px;vertical-align:middle;' +
      'background:rgba(255,59,48,0.12);border:1px solid rgba(255,59,48,0.3);color:#ff3b30;">' +
      '<span id="' + uid + 'd" style="width:6px;height:6px;border-radius:50%;flex-shrink:0;' +
        'background:#ff3b30;box-shadow:0 0 5px #ff3b30;"></span>' +
      label + '<span id="' + uid + 'l">SIM</span>' +
    '</span>';

  var script =
    '<script>(function(){' +
      'window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
      'window.A2UI_DATA=window.A2UI_DATA||{};' +
      'function update(data){' +
        'var n=Array.isArray(data)?data.length:(data?1:0);' +
        'var live=n>0;' +
        'var c=live?"#34c759":"#ff3b30";' +
        'var el=document.getElementById("' + uid + '");' +
        'var dot=document.getElementById("' + uid + 'd");' +
        'var lbl=document.getElementById("' + uid + 'l");' +
        'if(el){el.style.background=live?"rgba(52,199,89,0.12)":"rgba(255,59,48,0.12)";' +
          'el.style.borderColor=live?"rgba(52,199,89,0.3)":"rgba(255,59,48,0.3)";' +
          'el.style.color=c;}' +
        'if(dot){dot.style.background=c;dot.style.boxShadow="0 0 5px "+c;}' +
        'if(lbl)lbl.textContent=live?"LIVE ("+n+")":"SIM";' +
      '}' +
      // Chain — preserve any existing subscriber
      (name ?
        'var prev=window.A2UI_CALLBACKS["' + _esc(name) + '"];' +
        'window.A2UI_CALLBACKS["' + _esc(name) + '"]=function(d){update(d);if(prev)prev(d);};' +
        // Catch data already dispatched before this atom's script ran
        'if(window.A2UI_DATA["' + _esc(name) + '"])update(window.A2UI_DATA["' + _esc(name) + '"]);' : '') +
    '})();<\/script>';

  return pill + script;
};

// ── data_source ───────────────────────────────────────────────────────────────
// Generic HTTP GET feed. Surface-agnostic descriptor — the transport is the surface's concern.
// On GAS: initial server-side fetch via UrlFetchApp; client refresh via google.script.run.fetchDataSource().
//
// Fields:
//   name    — identifier other atoms subscribe to (required)
//   url     — HTTP GET endpoint
//   format  — 'json' | 'text' (default 'json')
//   path    — dot-notation into parsed response (e.g. 'data.items')
//   refresh — client-side refresh interval seconds (0 = initial load only, default 0)
//   cache   — server-side cache TTL seconds (default 15)
_RENDERERS['data_source'] = function(b) {
  var name    = b.name    || 'feed';
  var url     = b.url     || '';
  var format  = b.format  || 'json';
  var path    = b.path    || '';
  var refresh = b.refresh || 0;
  var ttl     = b.cache   || 15;

  var initial = null;
  if (url) {
    var body = _surfaceFetch(url, 'ds_' + name, ttl);
    if (body) {
      try {
        var data = format === 'json' ? JSON.parse(body) : body;
        if (path) path.split('.').forEach(function(k) { if (data && k) data = data[k]; });
        initial = data;
      } catch(e) {}
    }
  }

  return '<script>(function(){' +
    'window.A2UI_DATA=window.A2UI_DATA||{};' +
    'window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
    'function dispatch(data){' +
      'window.A2UI_DATA["' + _esc(name) + '"]=data;' +
      'var cb=window.A2UI_CALLBACKS["' + _esc(name) + '"];' +
      'if(typeof cb==="function")cb(data);' +
    '}' +
    // Deferred initial dispatch — gives all atom scripts time to register callbacks
    (initial !== null ? 'setTimeout(function(){dispatch(' + JSON.stringify(initial) + ');},80);' : '') +
    // Client-side refresh via GAS surface transport
    (refresh > 0 && url ?
      'setInterval(function(){' +
        'if(typeof google!=="undefined"&&google.script){' +
          'google.script.run' +
            '.withSuccessHandler(dispatch)' +
            '.withFailureHandler(function(){})' +
            '.fetchDataSource("' + _esc(url) + '","' + _esc(format) + '","' + _esc(path) + '");' +
        '}' +
      '},' + Math.round(refresh * 1000) + ');' : '') +
  '})();<\/script>';
};

// ── adsb_feed ─────────────────────────────────────────────────────────────────
// adsb.lol ADS-B live traffic feed (reachable from GAS, free, no auth required).
// Endpoint: https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{nm}
// Publishes normalised flight objects: {callsign, lat, lon, alt_ft, spd_kt, hdg, on_ground, squawk}
//
// Fields:
//   name         — feed name (default 'adsb')
//   center_lat   — centre latitude (default 43.629 = LFBO)
//   center_lon   — centre longitude (default 1.363 = LFBO)
//   radius_nm    — radius in nautical miles (default 40)
//   refresh      — client refresh interval seconds (default 15)
//   filter_ground — exclude on-ground traffic (default true)
//   cache        — server-side cache TTL seconds (default 15)
_RENDERERS['adsb_feed'] = function(b) {
  var name      = b.name         || 'adsb';
  var clat      = b.center_lat   !== undefined ? b.center_lat : 43.629;
  var clon      = b.center_lon   !== undefined ? b.center_lon : 1.363;
  var radius    = b.radius_nm    !== undefined ? b.radius_nm  : 40;
  var refresh   = b.refresh      !== undefined ? b.refresh    : 15;
  var filterGnd = b.filter_ground !== false;
  var ttl       = b.cache        || 15;

  var url = 'https://api.adsb.lol/v2/lat/' + clat + '/lon/' + clon + '/dist/' + radius;

  // Server-side initial fetch (cached)
  var initialFlights = [];
  var body = _surfaceFetch(url, 'adsb_' + name, ttl);
  if (body) {
    try { initialFlights = _normaliseAdsbLol(JSON.parse(body), filterGnd); } catch(e) {}
  }

  // Client-side normalisation — mirrors _normaliseAdsbLol
  var normFn =
    'function norm(raw){' +
      'if(!raw||!raw.ac)return[];' +
      'return raw.ac.map(function(a){' +
        'var alt=typeof a.alt_baro==="number"?a.alt_baro:0;' +
        'return{callsign:(a.flight||a.hex||"").trim(),lat:a.lat,lon:a.lon,' +
          'alt_ft:alt,spd_kt:a.gs||0,hdg:a.track||0,' +
          'on_ground:a.alt_baro==="ground"||alt<50,squawk:a.squawk||""};' +
      '}).filter(function(f){' +
        'return f.callsign&&f.lat!==undefined&&f.lon!==undefined' +
        (filterGnd ? '&&!f.on_ground' : '') + ';' +
      '});' +
    '}';

  return '<script>(function(){' +
    'window.A2UI_DATA=window.A2UI_DATA||{};' +
    'window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
    normFn +
    'function dispatch(raw){' +
      'var flights=Array.isArray(raw)?raw:norm(raw);' +
      'window.A2UI_DATA["' + _esc(name) + '"]=flights;' +
      'var cb=window.A2UI_CALLBACKS["' + _esc(name) + '"];' +
      'if(typeof cb==="function")cb(flights);' +
    '}' +
    'setTimeout(function(){dispatch(' + JSON.stringify(initialFlights) + ');},80);' +
    (refresh > 0 ?
      'setInterval(function(){' +
        'if(typeof google!=="undefined"&&google.script){' +
          'google.script.run' +
            '.withSuccessHandler(dispatch)' +
            '.withFailureHandler(function(){})' +
            '.fetchDataSource("' + _esc(url) + '","json","");' +
        '}' +
      '},' + Math.round(refresh * 1000) + ');' : '') +
  '})();<\/script>';
};

// ── metar_feed ────────────────────────────────────────────────────────────────
// METAR weather for an ICAO station via aviationweather.gov.
// Publishes { wind, temp, qnh, raw } to the named feed.
//
// Fields:
//   name    — feed name (default 'metar')
//   station — ICAO code (default 'LFBO')
//   refresh — client refresh interval seconds (default 60)
//   cache   — server-side cache TTL seconds (default 30)
_RENDERERS['metar_feed'] = function(b) {
  var name    = b.name    || 'metar';
  var station = (b.station || 'LFBO').toUpperCase();
  var refresh = b.refresh !== undefined ? b.refresh : 60;
  var ttl     = b.cache   || 30;

  var url = 'https://aviationweather.gov/api/data/metar?ids=' + station + '&format=raw&hours=1';

  var initial = { wind: '—', temp: '—', qnh: '—', raw: '' };
  var body = _surfaceFetch(url, 'metar_' + station, ttl);
  if (body) {
    var raw = body.trim().split('\n')[0].trim();
    if (raw) initial = _parseMETAR(raw);
  }

  // Client-side METAR parser (mirrors _parseMETAR)
  var parseFn =
    'function parseMETAR(raw){' +
      'if(!raw||typeof raw==="object")return raw||{};' +
      'var wm=raw.match(/(VRB|\\d{3})(\\d{2})(G\\d{2})?KT/);' +
      'var tm=raw.match(/\\s(M?\\d{2})\\/(M?\\d{2})\\s/);' +
      'var qm=raw.match(/Q(\\d{4})/);' +
      'return{' +
        'wind:wm?(wm[1]==="VRB"?"VRB":wm[1]+"°")+"/"+wm[2]+"kt"+(wm[3]?" gust "+wm[3].slice(1)+"kt":""):"—",' +
        'temp:tm?tm[1].replace("M","-")+"°C":"—",' +
        'qnh:qm?qm[1]+" hPa":"—",' +
        'raw:raw};' +
    '}';

  return '<script>(function(){' +
    'window.A2UI_DATA=window.A2UI_DATA||{};' +
    'window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
    parseFn +
    'function dispatch(raw){' +
      'var data=parseMETAR(raw);' +
      'window.A2UI_DATA["' + _esc(name) + '"]=data;' +
      'var cb=window.A2UI_CALLBACKS["' + _esc(name) + '"];' +
      'if(typeof cb==="function")cb(data);' +
    '}' +
    'setTimeout(function(){dispatch(' + JSON.stringify(initial) + ');},80);' +
    (refresh > 0 ?
      'setInterval(function(){' +
        'if(typeof google!=="undefined"&&google.script){' +
          'google.script.run' +
            '.withSuccessHandler(dispatch)' +
            '.withFailureHandler(function(){})' +
            '.fetchDataSource("' + _esc(url) + '","text","");' +
        '}' +
      '},' + Math.round(refresh * 1000) + ');' : '') +
  '})();<\/script>';
};

// ── firestore_read ────────────────────────────────────────────────────────────
// Data connector: reads a named Firestore document (noun) on render (verb: read).
// Publishes deserialized doc to window.A2UI_DATA[name]; visual atoms subscribe
// via window.A2UI_CALLBACKS[name]. Optional client refresh via google.script.run.
//
// Fields:
//   name       — connector name other atoms subscribe to (required)
//   project    — GCP project ID owning the Firestore database (required)
//   collection — Firestore collection name (required)
//   doc_id     — document ID within the collection (required)
//   refresh    — client-side refresh interval seconds (0 = initial load only, default 0)
//
// Note: appsscript.json must declare oauthScopes with datastore scope.
_RENDERERS['firestore_read'] = function(b) {
  var name       = b.name       || 'firestore';
  var project    = b.project    || '';
  var collection = b.collection || '';
  var docId      = b.doc_id     || '';
  var refresh    = b.refresh    || 0;

  var initial = null;
  if (project && collection && docId) {
    initial = fetchFirestoreDoc(project, collection, docId);
  }

  return '<script>(function(){' +
    'window.A2UI_DATA=window.A2UI_DATA||{};' +
    'window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
    'function dispatch(data){' +
      'window.A2UI_DATA["' + _esc(name) + '"]=data;' +
      'var cb=window.A2UI_CALLBACKS["' + _esc(name) + '"];' +
      'if(typeof cb==="function")cb(data);' +
    '}' +
    (initial !== null ? 'setTimeout(function(){dispatch(' + JSON.stringify(initial) + ');},80);' : '') +
    (refresh > 0 && project && collection && docId ?
      'setInterval(function(){' +
        'if(typeof google!=="undefined"&&google.script){' +
          'google.script.run' +
            '.withSuccessHandler(dispatch)' +
            '.withFailureHandler(function(){})' +
            '.fetchFirestoreDoc("' + _esc(project) + '","' + _esc(collection) + '","' + _esc(docId) + '");' +
        '}' +
      '},' + Math.round(refresh * 1000) + ');' : '') +
  '})();<\/script>';
};
