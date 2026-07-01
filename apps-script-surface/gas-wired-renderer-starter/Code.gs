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
  try {
    var clientId = Utilities.getUuid();
    var pageTitle = nav || (p ? 'payload' : 'home');
    var payload = JSON.stringify({
      client_id: clientId,
      events: [{
        name: 'page_view',
        params: {
          page_title: pageTitle,
          page_location: ScriptApp.getService().getUrl() + (nav ? '?nav=' + nav : ''),
          engagement_time_msec: '1'
        }
      }]
    });
    var props = PropertiesService.getScriptProperties();
    var mid   = props.getProperty('GA4_MEASUREMENT_ID') || '';
    var sec   = props.getProperty('GA4_API_SECRET')     || '';
    if (!mid || !sec) return;
    UrlFetchApp.fetch(
      'https://www.google-analytics.com/mp/collect?measurement_id=' + mid + '&api_secret=' + sec,
      { method: 'post', contentType: 'application/json', payload: payload, muteHttpExceptions: true }
    );
  } catch(e) {}
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
  if (e && e.parameter && e.parameter.settings === 'chat') {
    return HtmlService.createHtmlOutputFromFile('ChatSettings')
      .setTitle('Chat Integration Settings')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }
  if (e && e.parameter && e.parameter.gallery === 'transfo') {
    return HtmlService.createHtmlOutputFromFile('TransfoGallery')
      .setTitle('Transfo Gallery — A2UI Atom Catalogue')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }
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
    // Normalise to web-safe base64 in case client sent standard base64 (+ and /)
    encoded = encoded.replace(/\+/g, '-').replace(/\//g, '_');
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
    var payload;
    try {
      payload = JSON.parse(json);
    } catch(e) {
      // Repair common truncation: outer array missing closing ]
      if (json.charAt(0) === '[') {
        payload = JSON.parse(json + ']');
      } else {
        throw e;
      }
    }
    payload._p = encoded; // preserve raw param so wired surface can reconstruct its full URL
    return _renderFromPayload(payload, from || '');
  } catch (err) {
    return _errorPage(err.message);
  }
}

// ─── A2UI Actions dispatcher ──────────────────────────────────────────────────

// ─── Identity resolution ──────────────────────────────────────────────────────
// USER_DEPLOYING: script runs as deployer; Session.getActiveUser() = real accessor.
//   ScriptApp.getOAuthToken() gives the DEPLOYER's token, so tokeninfo is wrong.
// USER_ACCESSING: script runs as accessor; tokeninfo on their token = correct.
// Detection: if effectiveUser ≠ activeUser, we're in USER_DEPLOYING.
var _cachedIdentity = null;
function _resolveIdentity() {
  if (_cachedIdentity) return _cachedIdentity;
  var effectiveEmail = '';
  var activeEmail    = '';
  try { effectiveEmail = Session.getEffectiveUser().getEmail() || ''; } catch(e) {}
  try { activeEmail    = Session.getActiveUser().getEmail()    || ''; } catch(e) {}

  if (activeEmail && effectiveEmail && activeEmail !== effectiveEmail) {
    // USER_DEPLOYING: active user is the real visitor, not the deployer
    var nameParts = activeEmail.split('@')[0].replace(/[._-]/g, ' ')
      .replace(/\b\w/g, function(c) { return c.toUpperCase(); });
    _cachedIdentity = { email: activeEmail, name: nameParts, photoUrl: '' };
    return _cachedIdentity;
  }

  // USER_ACCESSING (or same person): tokeninfo on their own OAuth token
  try {
    var tok  = ScriptApp.getOAuthToken();
    var resp = UrlFetchApp.fetch('https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=' + encodeURIComponent(tok), { muteHttpExceptions: true });
    if (resp.getResponseCode() === 200) {
      var info = JSON.parse(resp.getContentText());
      var email    = info.email    || '';
      var name     = info.name     || info.given_name || '';
      var photoUrl = info.picture  || '';
      if (email) {
        if (!name) name = email.split('@')[0].replace(/[._-]/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
        _cachedIdentity = { email: email, name: name, photoUrl: photoUrl };
        return _cachedIdentity;
      }
    }
  } catch(e) {}

  // Final fallback
  var fb = activeEmail || '';
  var fbName = fb ? fb.split('@')[0].replace(/[._-]/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); }) : '';
  _cachedIdentity = { email: fb, name: fbName, photoUrl: '' };
  return _cachedIdentity;
}

function a2uiGetMe() {
  try {
    var id = _resolveIdentity();
    if (!id.email) return { ok: true, email: '', name: '' };
    return { ok: true, email: id.email, name: id.name, photoUrl: id.photoUrl };
  } catch(e) {
    return { ok: true, email: '', name: '' };
  }
}

// ─── Surface presence molecule ────────────────────────────────────────────────
// Sessions stored in PropertiesService.getScriptProperties() — shared across ALL
// users regardless of executeAs mode, no Drive dependency per user.
// Key: 'psurf_<surfaceId>'  Value: JSON array of {email,name,photoUrl,lastSeen}
function a2uiSurfacePresence(action, payload) {
  try {
    payload = payload || {};
    var surfaceId = String(payload.surface_id || 'default');
    var propKey   = 'psurf_' + surfaceId;

    if (action === 'ping') {
      // Client passes identity from a2uiGetMe(); fall back to server-side resolution
      var email    = String(payload.email    || '');
      var name     = String(payload.name     || '');
      var photoUrl = String(payload.photoUrl || '');
      if (!email) {
        var id = _resolveIdentity();
        email = id.email; name = id.name; photoUrl = id.photoUrl;
      }
      if (!email) return { ok: true };
      if (!name)  name = email.split('@')[0].replace(/[._-]/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });

      // Ping is dumb — just record presence. Access check happens in query (runs as file owner).
      var now  = new Date().toISOString();
      var lock = LockService.getScriptLock();
      try {
        lock.waitLock(4000);
        var props    = PropertiesService.getScriptProperties();
        var raw      = props.getProperty(propKey);
        var sessions = raw ? JSON.parse(raw) : [];
        var stale    = new Date(Date.now() - 10 * 60 * 1000).toISOString();
        sessions = sessions.filter(function(s) { return s.lastSeen > stale && s.email !== email; });
        sessions.push({ email: email, name: name, photoUrl: photoUrl, lastSeen: now });
        props.setProperty(propKey, JSON.stringify(sessions));
      } finally {
        try { lock.releaseLock(); } catch(e) {}
      }
      return { ok: true };
    }

    if (action === 'grant') {
      // Grant Drive edit access to a specific user for the guard sheet
      var targetEmail = String(payload.email || '');
      var sheetName   = String(payload.sheet || '');
      if (!targetEmail || !sheetName) return { ok: false, error: 'Missing email or sheet' };
      var fileId = PropertiesService.getScriptProperties().getProperty(_sheetIdKey_(sheetName));
      if (!fileId) return { ok: false, error: 'Sheet not found' };
      try {
        DriveApp.getFileById(fileId).addEditor(targetEmail);
      } catch(e) {
        return { ok: false, error: e.message || String(e) };
      }
      // Update session: mark hasAccess true for this user
      var lock2 = LockService.getScriptLock();
      try {
        lock2.waitLock(4000);
        var props2   = PropertiesService.getScriptProperties();
        var raw2     = props2.getProperty(propKey);
        var sessions2 = raw2 ? JSON.parse(raw2) : [];
        sessions2.forEach(function(s) { if (s.email === targetEmail) s.hasAccess = true; });
        props2.setProperty(propKey, JSON.stringify(sessions2));
      } finally {
        try { lock2.releaseLock(); } catch(e) {}
      }
      return { ok: true };
    }

    if (action === 'query') {
      var threshold  = parseInt(payload.threshold || 90, 10);
      var guardSheet = String(payload.guard_sheet || '');
      var props      = PropertiesService.getScriptProperties();
      var raw        = props.getProperty(propKey);
      if (!raw) return { ok: true, data: [] };
      var sessions = JSON.parse(raw);
      var cutoff   = new Date(Date.now() - threshold * 1000).toISOString();
      var users    = sessions.filter(function(s) { return s.lastSeen >= cutoff; });

      // If querying user can access the guard sheet, annotate each session with hasAccess.
      // Runs as the file owner (USER_ACCESSING) so getEditors() works for them only.
      if (guardSheet) {
        try {
          var sheetFileId = props.getProperty(_sheetIdKey_(guardSheet));
          if (sheetFileId) {
            var file = DriveApp.getFileById(sheetFileId);
            var editorMap = {};
            try { editorMap[file.getOwner().getEmail()] = true; } catch(e) {}
            file.getEditors().forEach(function(e) { editorMap[e.getEmail()] = true; });
            users.forEach(function(u) { u.hasAccess = editorMap[u.email] === true; });
          }
        } catch(e) {
          // Querying user can't access the file — skip access annotation (default: show all as normal)
        }
      }

      users.sort(function(a, b) { return b.lastSeen.localeCompare(a.lastSeen); });
      return { ok: true, data: users };
    }

    return { ok: false, error: 'Unknown action: ' + action };
  } catch(e) {
    return { ok: false, error: e.message || String(e) };
  }
}

function a2uiAction(type, payload) {
  var result;
  try {
    switch (type) {
      case 'gas:sheet_append':       result = _actionSheetAppend(payload);       break;
      case 'gas:sheet_batch_append': result = _actionSheetBatchAppend(payload);  break;
      case 'gas:sheet_query':        result = _actionSheetQuery(payload);        break;
      case 'gas:sheet_upsert':       result = _actionSheetUpsert(payload);       break;
      case 'gas:sheet_delete_row':   result = _actionSheetDeleteRow(payload);    break;
      case 'gas:sheet_create':       result = _actionSheetCreate(payload);       break;
      case 'gas:sheet_aggregate':    result = _actionSheetAggregate(payload);    break;
      case 'gas:firestore_query':    result = _actionFirestoreQuery(payload);    break;
      case 'gas:firestore_set':      result = _actionFirestoreSet(payload);      break;
      case 'gas:firestore_delete':   result = _actionFirestoreDelete(payload);   break;
      case 'gas:adsb_query':         result = _actionAdsbQuery(payload);         break;
      case 'gas:email_send':         result = _actionEmailSend(payload);         break;
      case 'gas:calendar_event':     result = _actionCalendarEvent(payload);     break;
      case 'gas:api_post':           result = _actionApiPost(payload);           break;
      case 'gas:script_run':         result = _actionScriptRun(payload);         break;
      case 'gas:sheet_info':         result = _actionSheetInfo(payload);         break;
      case 'gas:sheet_presence':     result = _actionSheetPresence(payload);     break;
      case 'gas:calendar_meet':      result = _actionCalendarMeet(payload);      break;
      case 'gas:sheet_import_csv':   result = _actionSheetImportCsv(payload);   break;
      case 'gas:chat_space_create':  result = _actionChatSpaceCreate(payload);  break;
      case 'gas:chat_message_send':  result = _actionChatMessageSend(payload);  break;
      case 'gas:directory_search':   result = _actionDirectorySearch(payload);  break;
      case 'gas:save_property':      result = _actionSaveProperty(payload);     break;
      default: result = { ok: false, error: 'Unknown action type: ' + type };
    }
  } catch (e) {
    result = { ok: false, error: e.message || String(e) };
  }
  return result || { ok: false, error: 'Action returned no response: ' + type };
}

// ─── Identity ─────────────────────────────────────────────────────────────────
// Cached per request — Session calls are slow in GAS.

function _getActiveUserEmail() {
  return _resolveIdentity().email;
}

// ─── Template resolution ──────────────────────────────────────────────────────
// Tokens: {{now}}, {{today}}, {{datetime}}, {{app.*}}, {{app.user.email}}

function _resolveTemplateTokens(value, appConfig) {
  if (typeof value !== 'string') return value;
  var app     = appConfig || {};
  var storage = app.storage || {};
  var now     = new Date();
  var isoDate     = now.toISOString().slice(0, 10);
  var isoDateTime = now.toISOString().slice(0, 19).replace('T', ' ');
  var result  = value
    .replace(/\{\{now\}\}/g,      isoDate)
    .replace(/\{\{today\}\}/g,    isoDate)
    .replace(/\{\{datetime\}\}/g, isoDateTime)
    .replace(/\{\{app\.id\}\}/g,                 String(app.id              || ''))
    .replace(/\{\{app\.storage\.sheet\}\}/g,      String(storage.sheet      || ''))
    .replace(/\{\{app\.storage\.folder_id\}\}/g,  String(storage.folder_id  || ''))
    .replace(/\{\{app\.storage\.type\}\}/g,       String(storage.type       || ''));
  // Resolve user tokens lazily — Session/People API call only when needed
  if (result.indexOf('{{app.user') !== -1) {
    result = result.replace(/\{\{app\.user\.email\}\}/g, _getActiveUserEmail());
    if (result.indexOf('{{app.user.name}}') !== -1) {
      result = result.replace(/\{\{app\.user\.name\}\}/g, _getActiveUserName());
    }
  }
  return result;
}

function _resolveCollect(collect, appConfig) {
  var out  = {};
  var keys = Object.keys(collect || {});
  for (var i = 0; i < keys.length; i++) {
    out[keys[i]] = _resolveTemplateTokens(collect[keys[i]], appConfig);
  }
  return out;
}

// ─── Where filter ─────────────────────────────────────────────────────────────
// Supports equality: { col: "value" }
// Operator: { col: { gt|lt|gte|lte|eq|ne|contains: value } }

function _applyWhere(rows, where) {
  if (!where) return rows;
  var keys = Object.keys(where);
  return rows.filter(function(r) {
    return keys.every(function(k) {
      var col  = k.toLowerCase().replace(/\s+/g, '_');
      var cell = r[col] !== undefined ? r[col] : '';
      var cond = where[k];
      if (cond !== null && typeof cond === 'object') {
        var num  = Number(cell);
        var condKeys = Object.keys(cond);
        return condKeys.every(function(op) {
          var v = cond[op];
          switch (op) {
            case 'gt':       return num > Number(v);
            case 'lt':       return num < Number(v);
            case 'gte':      return num >= Number(v);
            case 'lte':      return num <= Number(v);
            case 'ne':       return String(cell) !== String(v);
            case 'eq':       return String(cell) === String(v);
            case 'contains': return String(cell).toLowerCase().indexOf(String(v).toLowerCase()) !== -1;
            default:         return true;
          }
        });
      }
      return String(cell) === String(cond);
    });
  });
}

// ─── Isolation ────────────────────────────────────────────────────────────────
// When app.data.isolation === 'by_user', auto-scope reads and writes to the
// active user's email via a hidden 'a2ui_owner' column.

var ISOLATION_COL      = 'a2ui_owner';
var ISOLATION_TEAM_COL = 'a2ui_team';

function _getIsolationEmail(appConfig) {
  var isolation = (appConfig && appConfig.data && appConfig.data.isolation) || 'none';
  if (isolation !== 'by_user') return null;
  return _getActiveUserEmail();
}

function _getIsolationTeam(appConfig) {
  var isolation = (appConfig && appConfig.data && appConfig.data.isolation) || 'none';
  if (isolation !== 'by_team') return null;
  var email = _getActiveUserEmail();
  var at = email.indexOf('@');
  return at >= 0 ? email.slice(at + 1) : email;
}

// ─── User display name ────────────────────────────────────────────────────────
// Returns display name from People API if available; falls back to email prefix.

function _getActiveUserName() {
  var email = _getActiveUserEmail();
  if (!email) return '';
  try {
    var resp = UrlFetchApp.fetch(
      'https://people.googleapis.com/v1/people/me?personFields=names',
      { headers: { 'Authorization': 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true }
    );
    if (resp.getResponseCode() === 200) {
      var data = JSON.parse(resp.getContentText());
      var names = (data.names || []);
      if (names.length) return names[0].displayName || email.split('@')[0];
    }
  } catch(e) {}
  return email.split('@')[0];
}

// ─── Renderer config ──────────────────────────────────────────────────────────
// Script Properties set once by the renderer owner (not per-payload):
//   FIRESTORE_PROJECT_ID — GCP project ID for Firestore backend

function _getRendererConfig() {
  try {
    var props = PropertiesService.getScriptProperties().getProperties();
    return {
      firestoreProjectId: props['FIRESTORE_PROJECT_ID'] || null
    };
  } catch(e) { return { firestoreProjectId: null }; }
}

// ─── Firestore helpers ────────────────────────────────────────────────────────

function _firestoreRequest(method, path, body) {
  var cfg = _getRendererConfig();
  if (!cfg.firestoreProjectId) throw new Error(
    'Firestore not configured. Set FIRESTORE_PROJECT_ID in Script Properties.'
  );
  var url = 'https://firestore.googleapis.com/v1/projects/' + cfg.firestoreProjectId +
            '/databases/(default)/documents' + path;
  var opts = {
    method: method,
    headers: { 'Authorization': 'Bearer ' + ScriptApp.getOAuthToken() },
    contentType: 'application/json',
    muteHttpExceptions: true
  };
  if (body) opts.payload = JSON.stringify(body);
  return UrlFetchApp.fetch(url, opts);
}

function _toFirestoreValue(val) {
  if (val === null || val === undefined) return { nullValue: null };
  if (typeof val === 'boolean')          return { booleanValue: val };
  if (typeof val === 'number') {
    return Number.isInteger(val) ? { integerValue: String(val) } : { doubleValue: val };
  }
  if (val instanceof Date)               return { timestampValue: val.toISOString() };
  if (typeof val === 'object' && !Array.isArray(val)) {
    return { mapValue: { fields: _toFirestoreFields(val) } };
  }
  if (Array.isArray(val)) {
    return { arrayValue: { values: val.map(_toFirestoreValue) } };
  }
  return { stringValue: String(val) };
}

function _toFirestoreFields(obj) {
  var fields = {};
  Object.keys(obj).forEach(function(k) { fields[k] = _toFirestoreValue(obj[k]); });
  return fields;
}

function _fromFirestoreValue(v) {
  if (!v) return null;
  if ('nullValue'      in v) return null;
  if ('booleanValue'   in v) return v.booleanValue;
  if ('integerValue'   in v) return parseInt(v.integerValue, 10);
  if ('doubleValue'    in v) return v.doubleValue;
  if ('timestampValue' in v) return v.timestampValue;
  if ('stringValue'    in v) return v.stringValue;
  if ('arrayValue'     in v) return (v.arrayValue.values || []).map(_fromFirestoreValue);
  if ('mapValue'       in v) return _fromFirestoreDoc({ fields: v.mapValue.fields });
  return null;
}

function _fromFirestoreDoc(doc) {
  var out = { _id: (doc.name || '').split('/').pop() };
  Object.keys(doc.fields || {}).forEach(function(k) { out[k] = _fromFirestoreValue(doc.fields[k]); });
  return out;
}

function _firestoreWhereFilter(where) {
  // Converts A2UI where spec to Firestore structuredQuery filter
  var keys = Object.keys(where || {});
  if (!keys.length) return null;

  var opMap = { gt: 'GREATER_THAN', lt: 'LESS_THAN', gte: 'GREATER_THAN_OR_EQUAL',
                lte: 'LESS_THAN_OR_EQUAL', eq: 'EQUAL', ne: 'NOT_EQUAL' };

  var filters = [];
  keys.forEach(function(field) {
    var cond = where[field];
    if (typeof cond === 'object' && cond !== null) {
      Object.keys(cond).forEach(function(op) {
        if (op === 'contains') {
          // Firestore doesn't support LIKE — skip (warn only)
          console.warn('[A2UI] Firestore does not support contains filter on field: ' + field);
          return;
        }
        filters.push({ fieldFilter: {
          field: { fieldPath: field },
          op: opMap[op] || 'EQUAL',
          value: _toFirestoreValue(cond[op])
        }});
      });
    } else {
      filters.push({ fieldFilter: {
        field: { fieldPath: field }, op: 'EQUAL', value: _toFirestoreValue(cond)
      }});
    }
  });

  if (!filters.length) return null;
  return filters.length === 1
    ? filters[0]
    : { compositeFilter: { op: 'AND', filters: filters } };
}

// ─── Firestore actions ────────────────────────────────────────────────────────

function _actionFirestoreQuery(payload) {
  var cfg        = payload.config || {};
  var collection = cfg.collection || (payload.appConfig && payload.appConfig.storage && payload.appConfig.storage.collection) || 'a2ui_data';
  var where      = cfg.where      ? JSON.parse(JSON.stringify(cfg.where)) : {};
  var orderBy    = cfg.order_by   || null;
  var limit      = cfg.limit      ? parseInt(cfg.limit)  : null;
  var offset     = cfg.offset     ? parseInt(cfg.offset) : null;
  var select     = cfg.select     || null; // array of field names to return

  // Isolation
  var ownerEmail = _getIsolationEmail(payload.appConfig);
  if (ownerEmail !== null) where[ISOLATION_COL] = ownerEmail;
  var teamDomain = _getIsolationTeam(payload.appConfig);
  if (teamDomain !== null) where[ISOLATION_TEAM_COL] = teamDomain;

  var query = { from: [{ collectionId: collection }] };
  var filter = _firestoreWhereFilter(where);
  if (filter) query.where = filter;

  // order_by: string "col" or [{column:"col",dir:"desc"}, ...]
  if (orderBy) {
    var orders = Array.isArray(orderBy)
      ? orderBy
      : [{ column: orderBy, dir: 'asc' }];
    query.orderBy = orders.map(function(o) {
      var col = typeof o === 'string' ? o : (o.column || o);
      var dir = (typeof o === 'object' && o.dir === 'desc') ? 'DESCENDING' : 'ASCENDING';
      return { field: { fieldPath: col }, direction: dir };
    });
  }

  if (limit  !== null) query.limit  = limit;
  if (offset !== null) query.offset = offset;

  var resp = _firestoreRequest('post', '/' + collection + ':runQuery', { structuredQuery: query });
  var code = resp.getResponseCode();
  if (code !== 200) return { ok: false, error: 'Firestore query failed: HTTP ' + code + ' ' + resp.getContentText() };

  var results = JSON.parse(resp.getContentText());
  var rows = results
    .filter(function(r) { return r.document; })
    .map(function(r) { return _fromFirestoreDoc(r.document); });

  // Client-side select projection
  if (select && Array.isArray(select) && select.length) {
    rows = rows.map(function(row) {
      var out = {};
      select.forEach(function(f) { if (f in row) out[f] = row[f]; });
      return out;
    });
  }

  return { ok: true, data: rows };
}

function _actionFirestoreSet(payload) {
  var cfg        = payload.config || {};
  var collection = cfg.collection || (payload.appConfig && payload.appConfig.storage && payload.appConfig.storage.collection) || 'a2ui_data';
  var docId      = _resolveTemplateTokens(cfg.doc_id || '', payload.appConfig) || null;
  var data       = _resolveCollect(payload.data, payload.appConfig);

  // Stamp identity
  var ownerEmail = _getIsolationEmail(payload.appConfig);
  if (ownerEmail !== null) data[ISOLATION_COL] = ownerEmail;
  var teamDomain = _getIsolationTeam(payload.appConfig);
  if (teamDomain !== null) data[ISOLATION_TEAM_COL] = teamDomain;

  var fields = _toFirestoreFields(data);
  var path   = docId ? '/' + collection + '/' + docId : '/' + collection;
  var method = docId ? 'patch' : 'post';
  var resp   = _firestoreRequest(method, path, { fields: fields });
  var code   = resp.getResponseCode();
  if (code !== 200) return { ok: false, error: 'Firestore set failed: HTTP ' + code };

  var doc = JSON.parse(resp.getContentText());
  return { ok: true, data: { doc_id: (doc.name || '').split('/').pop() } };
}

function _actionFirestoreDelete(payload) {
  var cfg        = payload.config || {};
  var collection = cfg.collection || (payload.appConfig && payload.appConfig.storage && payload.appConfig.storage.collection) || 'a2ui_data';
  var docId      = _resolveTemplateTokens(cfg.doc_id || '', payload.appConfig);
  if (!docId) return { ok: false, error: 'firestore_delete: doc_id is required' };

  var resp = _firestoreRequest('delete', '/' + collection + '/' + docId, null);
  var code = resp.getResponseCode();
  return code === 200 ? { ok: true, data: {} } : { ok: false, error: 'Firestore delete failed: HTTP ' + code };
}

// ─── Batch sheet append ───────────────────────────────────────────────────────

function _actionSheetBatchAppend(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet  || 'A2UI_Data';
  var rows      = payload.data || [];  // array of collect objects
  if (!Array.isArray(rows) || !rows.length) return { ok: true, data: { inserted_rows: 0 } };

  var ownerEmail = _getIsolationEmail(payload.appConfig);
  var teamDomain = _getIsolationTeam(payload.appConfig);

  var resolved = rows.map(function(r) {
    var d = _resolveCollect(r, payload.appConfig);
    if (ownerEmail !== null) d[ISOLATION_COL]      = ownerEmail;
    if (teamDomain !== null) d[ISOLATION_TEAM_COL] = teamDomain;
    return d;
  });

  var sheet = _getOrCreateSheet_(sheetName);
  if (sheet.getLastRow() === 0) { sheet.appendRow(Object.keys(resolved[0])); }
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

  var matrix = resolved.map(function(d) {
    return headers.map(function(h) { return d[h] !== undefined ? d[h] : ''; });
  });
  sheet.getRange(sheet.getLastRow() + 1, 1, matrix.length, headers.length).setValues(matrix);
  return { ok: true, data: { inserted_rows: matrix.length } };
}

// ─── Sheet helpers ────────────────────────────────────────────────────────────

function _sheetIdKey_(name) {
  return 'a2ui_sid_' + name.replace(/[^a-zA-Z0-9]/g, '_');
}

function _getOrCreateSheet_(name) {
  var props  = PropertiesService.getScriptProperties();
  var key    = _sheetIdKey_(name);
  var fileId = props.getProperty(key);
  if (fileId) {
    try { return SpreadsheetApp.openById(fileId).getSheets()[0]; } catch(e) { props.deleteProperty(key); }
  }
  var files = DriveApp.getFilesByName(name);
  while (files.hasNext()) {
    var f = files.next();
    if (f.getMimeType() === MimeType.GOOGLE_SHEETS) {
      props.setProperty(key, f.getId());
      return SpreadsheetApp.open(f).getSheets()[0];
    }
  }
  var ss = SpreadsheetApp.create(name);
  // Share so any authenticated Google user can access this sheet by file ID,
  // enabling cross-account access in USER_ACCESSING deployments.
  try { DriveApp.getFileById(ss.getId()).setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.EDIT); } catch(e) {}
  props.setProperty(key, ss.getId());
  return ss.getSheets()[0];
}

function _findSheet_(name) {
  if (!name) return null;
  var props  = PropertiesService.getScriptProperties();
  var key    = _sheetIdKey_(name);
  var fileId = props.getProperty(key);
  if (fileId) {
    try { return SpreadsheetApp.openById(fileId).getSheets()[0]; } catch(e) { props.deleteProperty(key); }
  }
  var files = DriveApp.getFilesByName(name);
  while (files.hasNext()) {
    var f = files.next();
    if (f.getMimeType() === MimeType.GOOGLE_SHEETS) {
      props.setProperty(key, f.getId());
      return SpreadsheetApp.open(f).getSheets()[0];
    }
  }
  return null;
}

// ─── Action implementations ───────────────────────────────────────────────────

function _actionSheetAppend(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet || 'A2UI_Data';
  var data      = _resolveCollect(payload.data, payload.appConfig);

  var ownerEmail = _getIsolationEmail(payload.appConfig);
  if (ownerEmail !== null) data[ISOLATION_COL] = ownerEmail;
  var teamDomain = _getIsolationTeam(payload.appConfig);
  if (teamDomain !== null) data[ISOLATION_TEAM_COL] = teamDomain;

  var sheet = _getOrCreateSheet_(sheetName);
  if (sheet.getLastRow() === 0) { sheet.appendRow(Object.keys(data)); }
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = headers.map(function(h) { return data[h] !== undefined ? data[h] : ''; });
  sheet.appendRow(row);
  return { ok: true, data: { insertedRow: sheet.getLastRow() } };
}

function _actionSheetQuery(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet    || 'A2UI_Data';
  var where     = cfg.where    ? JSON.parse(JSON.stringify(cfg.where)) : {};
  var orderBy   = cfg.order_by || null;
  var limit     = cfg.limit    ? parseInt(cfg.limit)  : null;
  var offset    = cfg.offset   ? parseInt(cfg.offset) : 0;
  var select    = cfg.select   || null;

  // Resolve template tokens in where values (e.g. {{today}}, {{app.user.email}})
  Object.keys(where).forEach(function(k) {
    var v = where[k];
    if (typeof v === 'string') {
      where[k] = _resolveTemplateTokens(v, payload.appConfig);
    } else if (v !== null && typeof v === 'object') {
      Object.keys(v).forEach(function(op) {
        if (typeof v[op] === 'string') v[op] = _resolveTemplateTokens(v[op], payload.appConfig);
      });
    }
  });

  // Isolation
  var ownerEmail = _getIsolationEmail(payload.appConfig);
  if (ownerEmail !== null) where[ISOLATION_COL] = ownerEmail;
  var teamDomain = _getIsolationTeam(payload.appConfig);
  if (teamDomain !== null) where[ISOLATION_TEAM_COL] = teamDomain;

  var sheet = _findSheet_(sheetName);
  if (!sheet || sheet.getLastRow() < 2) return { ok: true, data: [], total: 0 };

  var values  = sheet.getDataRange().getValues();
  var headers = values[0].map(function(h) { return String(h).toLowerCase().replace(/\s+/g, '_'); });

  var rows = [];
  for (var i = 1; i < values.length; i++) {
    var row = {};
    for (var j = 0; j < headers.length; j++) { row[headers[j]] = values[i][j]; }
    rows.push(row);
  }

  rows = _applyWhere(rows, Object.keys(where).length ? where : null);

  // order_by: "col" (asc) | [{column:"col",dir:"desc"}, ...]
  if (orderBy) {
    var orders = Array.isArray(orderBy)
      ? orderBy
      : [{ column: orderBy, dir: 'asc' }];
    rows.sort(function(a, b) {
      for (var oi = 0; oi < orders.length; oi++) {
        var o   = orders[oi];
        var key = (typeof o === 'string' ? o : (o.column || o)).toLowerCase().replace(/\s+/g, '_');
        var dir = (typeof o === 'object' && o.dir === 'desc') ? -1 : 1;
        var av  = a[key], bv = b[key];
        if (av < bv) return -1 * dir;
        if (av > bv) return  1 * dir;
      }
      return 0;
    });
  }

  var total = rows.length;
  if (offset) rows = rows.slice(offset);
  if (limit !== null) rows = rows.slice(0, limit);

  // select projection — strip internal isolation columns from output
  var hiddenCols = [ISOLATION_COL, ISOLATION_TEAM_COL];
  var tz = Session.getScriptTimeZone();
  rows = rows.map(function(row) {
    var out = {};
    var cols = (select && select.length) ? select : Object.keys(row);
    cols.forEach(function(c) {
      if (hiddenCols.indexOf(c) === -1 && c in row) {
        var v = row[c];
        out[c] = (v instanceof Date) ? Utilities.formatDate(v, tz, 'yyyy-MM-dd HH:mm:ss') : v;
      }
    });
    return out;
  });

  return { ok: true, data: rows, total: total };
}

function _actionSheetUpsert(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet      || 'A2UI_Data';
  var keyCol    = cfg.key_column || '';
  var keyVal    = (payload.data && payload.data.key_value !== undefined)
    ? String(payload.data.key_value)
    : String(_resolveTemplateTokens(cfg.key_value || '', payload.appConfig));
  var data      = _resolveCollect(payload.data, payload.appConfig);

  var ownerEmail = _getIsolationEmail(payload.appConfig);
  if (ownerEmail !== null) data[ISOLATION_COL] = ownerEmail;

  var sheet = _getOrCreateSheet_(sheetName);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(Object.keys(data));
    sheet.appendRow(Object.keys(data).map(function(k) { return data[k] !== undefined ? data[k] : ''; }));
    return { ok: true, data: { upserted_row: 2, was_insert: true } };
  }

  var headers    = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var keyColNorm = keyCol.toLowerCase().replace(/\s+/g, '_');
  var keyColIdx  = -1;
  for (var c = 0; c < headers.length; c++) {
    if (String(headers[c]).toLowerCase().replace(/\s+/g, '_') === keyColNorm) { keyColIdx = c; break; }
  }

  var matchRow = -1;
  if (keyColIdx >= 0 && keyVal) {
    var allData = sheet.getDataRange().getValues();
    for (var r = 1; r < allData.length; r++) {
      if (String(allData[r][keyColIdx]) === keyVal) { matchRow = r + 1; break; }
    }
  }

  if (matchRow >= 0) {
    var rowValues = headers.map(function(h) {
      var k = String(h);
      return data[k] !== undefined ? data[k] : sheet.getRange(matchRow, headers.indexOf(h) + 1).getValue();
    });
    sheet.getRange(matchRow, 1, 1, headers.length).setValues([rowValues]);
    return { ok: true, data: { upserted_row: matchRow, was_insert: false } };
  } else {
    sheet.appendRow(headers.map(function(h) { return data[String(h)] !== undefined ? data[String(h)] : ''; }));
    return { ok: true, data: { upserted_row: sheet.getLastRow(), was_insert: true } };
  }
}

function _actionSheetDeleteRow(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet       || 'A2UI_Data';
  var keyCol    = cfg.key_column  || '';
  // key_value can come from collect (payload.data) or from static config
  var keyVal    = (payload.data && payload.data.key_value !== undefined)
    ? String(payload.data.key_value)
    : String(_resolveTemplateTokens(cfg.key_value || '', payload.appConfig));

  var sheet = _findSheet_(sheetName);
  if (!sheet) return { ok: false, error: 'Sheet not found: ' + sheetName };

  var headers    = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var keyColNorm = keyCol.toLowerCase().replace(/\s+/g, '_');
  var keyColIdx  = -1;
  for (var c = 0; c < headers.length; c++) {
    if (String(headers[c]).toLowerCase().replace(/\s+/g, '_') === keyColNorm) { keyColIdx = c; break; }
  }
  if (keyColIdx < 0) return { ok: false, error: 'key_column not found: ' + keyCol };

  var tz = Session.getScriptTimeZone();
  var allData = sheet.getDataRange().getValues();
  var deleted = 0;
  // Walk backwards so row indices stay valid as rows are deleted
  for (var r = allData.length - 1; r >= 1; r--) {
    var cellVal = allData[r][keyColIdx];
    var cellStr = (cellVal instanceof Date)
      ? Utilities.formatDate(cellVal, tz, 'yyyy-MM-dd HH:mm:ss')
      : String(cellVal);
    if (cellStr === keyVal) {
      // by_user isolation: only delete own rows
      var ownerEmail = _getIsolationEmail(payload.appConfig);
      if (ownerEmail !== null) {
        var ownerIdx = headers.map(function(h) { return String(h); }).indexOf(ISOLATION_COL);
        if (ownerIdx >= 0 && String(allData[r][ownerIdx]) !== ownerEmail) continue;
      }
      sheet.deleteRow(r + 1);
      deleted++;
      if (!cfg.delete_all) break; // default: delete first match only
    }
  }
  return { ok: true, data: { deleted_rows: deleted } };
}

function _actionSheetInfo(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet || (payload.appConfig && payload.appConfig.storage && payload.appConfig.storage.sheet) || 'A2UI_Data';
  var props     = PropertiesService.getScriptProperties();
  var key       = _sheetIdKey_(sheetName);
  var fileId    = props.getProperty(key);
  if (!fileId) {
    // Try to find it via Drive so we can cache the ID
    var files = DriveApp.getFilesByName(sheetName);
    while (files.hasNext()) {
      var f = files.next();
      if (f.getMimeType() === MimeType.GOOGLE_SHEETS) { fileId = f.getId(); props.setProperty(key, fileId); break; }
    }
  }
  if (!fileId) return { ok: false, error: 'Sheet not found: ' + sheetName };
  return { ok: true, data: {
    name:    sheetName,
    file_id: fileId,
    url:     'https://docs.google.com/spreadsheets/d/' + fileId + '/edit'
  }};
}

function _actionSheetPresence(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet || (payload.appConfig && payload.appConfig.storage && payload.appConfig.storage.sheet) || 'A2UI_Data';
  var windowMin = parseInt(cfg.window_minutes !== undefined ? cfg.window_minutes : 30, 10);

  var sheet = _findSheet_(sheetName);
  if (!sheet) return { ok: true, data: [] };
  var fileId = sheet.getParent().getId();

  var cutoff = windowMin > 0 ? new Date(Date.now() - windowMin * 60 * 1000).toISOString() : null;
  var token  = ScriptApp.getOAuthToken();

  // Revisions come back oldest-first — paginate to collect all, then reverse
  var allRevisions = [], pageToken = null, attempts = 0;
  do {
    var url = 'https://www.googleapis.com/drive/v3/files/' + fileId
      + '/revisions?fields=nextPageToken,revisions(lastModifyingUser,modifiedTime)&pageSize=1000';
    if (pageToken) url += '&pageToken=' + encodeURIComponent(pageToken);
    var resp = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + token }, muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) break;
    var body = JSON.parse(resp.getContentText());
    allRevisions = allRevisions.concat(body.revisions || []);
    pageToken = body.nextPageToken;
  } while (pageToken && ++attempts < 10);

  var seen = {}, users = [];
  allRevisions.slice().reverse().forEach(function(rev) {
    if (cutoff && (!rev.modifiedTime || rev.modifiedTime < cutoff)) return;
    var u     = rev.lastModifyingUser || {};
    var email = u.emailAddress || '';
    var name  = u.displayName  || '';
    // Google omits emailAddress for cross-domain users — fall back to displayName for dedup
    var key   = email || name;
    if (!key || seen[key]) return;
    seen[key] = true;
    users.push({ name: name || email, email: email, photoUrl: u.photoLink || '', lastActive: rev.modifiedTime || '' });
  });

  return { ok: true, data: users };
}

function _actionSheetCreate(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet    || 'A2UI_Data';
  var headers   = cfg.headers  || [];
  var seedRows  = cfg.seed_rows || [];

  var sheet = _getOrCreateSheet_(sheetName);
  var ss    = sheet.getParent();
  // Ensure shared so cross-account access works in USER_ACCESSING mode
  try { DriveApp.getFileById(ss.getId()).setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.EDIT); } catch(e) {}

  // Use the named tab if the file has one, else the first sheet
  var tab = ss.getSheetByName(sheetName) || sheet;

  // If row 1 col 1 is already populated, treat as already set up
  if (tab.getLastRow() > 0 && headers.length > 0 &&
      String(tab.getRange(1, 1).getValue()).toLowerCase() === String(headers[0]).toLowerCase()) {
    return { ok: true, created: false, message: 'Sheet already set up' };
  }

  // Write headers
  if (headers.length > 0) {
    tab.getRange(1, 1, 1, headers.length).setValues([headers]);
    tab.getRange(1, 1, 1, headers.length).setFontWeight('bold');
  }

  // Write seed rows
  if (seedRows.length > 0) {
    var tz = Session.getScriptTimeZone();
    var now = new Date();
    var seedResolved = seedRows.map(function(row) {
      return row.map(function(cell) {
        if (typeof cell !== 'string') return cell;
        return cell
          .replace(/\{\{datetime\}\}/g, Utilities.formatDate(now, tz, 'yyyy-MM-dd HH:mm:ss'))
          .replace(/\{\{today\}\}/g,    Utilities.formatDate(now, tz, 'yyyy-MM-dd'));
      });
    });
    tab.getRange(2, 1, seedResolved.length, seedResolved[0].length).setValues(seedResolved);
  }

  return { ok: true, created: true, total: seedRows.length };
}

function _actionSheetAggregate(payload) {
  var cfg       = payload.config || {};
  var sheetName = cfg.sheet         || 'A2UI_Data';
  var groupBy   = cfg.group_by      || null;
  var aggs      = cfg.aggregations  || [];
  var where     = cfg.where         || null;

  var sheet = _findSheet_(sheetName);
  if (!sheet || sheet.getLastRow() < 2) return { ok: true, data: [] };

  var values  = sheet.getDataRange().getValues();
  var headers = values[0].map(function(h) { return String(h).toLowerCase().replace(/\s+/g, '_'); });

  var rows = [];
  for (var i = 1; i < values.length; i++) {
    var row = {};
    for (var j = 0; j < headers.length; j++) { row[headers[j]] = values[i][j]; }
    rows.push(row);
  }

  // by_user isolation
  var ownerEmail = _getIsolationEmail(payload.appConfig);
  if (ownerEmail !== null) {
    var isoWhere = {}; isoWhere[ISOLATION_COL] = ownerEmail;
    rows = _applyWhere(rows, isoWhere);
  }

  rows = _applyWhere(rows, where);

  // Group
  var groups = {};
  var groupKeys = [];
  rows.forEach(function(r) {
    var key = groupBy ? String(r[groupBy.toLowerCase().replace(/\s+/g, '_')] || '') : '__all__';
    if (!groups[key]) { groups[key] = []; groupKeys.push(key); }
    groups[key].push(r);
  });

  var result = groupKeys.map(function(key) {
    var grpRows = groups[key];
    var out = {};
    if (groupBy) out[groupBy.toLowerCase().replace(/\s+/g, '_')] = key;
    aggs.forEach(function(agg) {
      var col  = agg.column ? agg.column.toLowerCase().replace(/\s+/g, '_') : null;
      var alias = agg.as || (agg.fn + (col ? '_' + col : ''));
      switch (agg.fn) {
        case 'count': out[alias] = grpRows.length; break;
        case 'sum':   out[alias] = grpRows.reduce(function(s, r) { return s + (Number(r[col]) || 0); }, 0); break;
        case 'avg':   out[alias] = grpRows.length ? grpRows.reduce(function(s,r){return s+(Number(r[col])||0);},0) / grpRows.length : 0; break;
        case 'min':   out[alias] = grpRows.reduce(function(m, r) { var v=Number(r[col])||0; return v<m?v:m; }, Infinity); break;
        case 'max':   out[alias] = grpRows.reduce(function(m, r) { var v=Number(r[col])||0; return v>m?v:m; }, -Infinity); break;
      }
    });
    return out;
  });

  return { ok: true, data: result };
}

function _actionEmailSend(payload) {
  var cfg  = payload.config || {};
  var data = payload.data   || {};

  // Resolve template tokens from config then overlay collected data fields as {{key}} tokens
  function resolve(tpl) {
    var v = _resolveTemplateTokens(tpl || '', payload.appConfig);
    Object.keys(data).forEach(function(k) {
      v = v.replace(new RegExp('\\{\\{' + k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\}\\}', 'g'), String(data[k] || ''));
    });
    return v;
  }

  var to      = String(data.to      || resolve(cfg.to      || ''));
  var subject = resolve(cfg.subject || '');
  var body    = resolve(cfg.body    || '');
  var isHtml  = !!cfg.is_html;
  var cc      = String(data.cc || (cfg.cc ? resolve(cfg.cc) : ''));
  if (!to) return { ok: false, error: 'email_send: to is required' };
  var opts = {};
  if (cc) opts.cc = cc;
  if (isHtml) opts.htmlBody = body;
  GmailApp.sendEmail(to, subject, isHtml ? '' : body, opts);
  return { ok: true, data: {} };
}

function _actionSaveProperty(payload) {
  var key   = String((payload.key   || payload.data && payload.data.key)   || '').trim();
  var value = String((payload.value !== undefined ? payload.value : (payload.data && payload.data.value !== undefined ? payload.data.value : '')) || '').trim();
  if (!key) return { ok: false, error: 'No key specified' };
  var props = PropertiesService.getScriptProperties();
  if (value) props.setProperty(key, value);
  else        props.deleteProperty(key);
  return { ok: true };
}

function _actionDirectorySearch(payload) {
  try {
    var query = String((payload.data && payload.data.query) || '').trim();
    if (query.length < 2) return { ok: true, data: { results: [] } };
    var tok  = ScriptApp.getOAuthToken();
    var url  = 'https://people.googleapis.com/v1/people:searchDirectoryPeople'
             + '?query=' + encodeURIComponent(query)
             + '&readMask=names,emailAddresses,photos'
             + '&sources=DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE'
             + '&pageSize=6';
    var resp = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + tok }, muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) return { ok: false, error: 'Directory search failed (' + resp.getResponseCode() + '): ' + resp.getContentText().slice(0, 200) };
    var people = JSON.parse(resp.getContentText()).people || [];
    var results = people.map(function(p) {
      return {
        name:     (p.names         && p.names[0]         && p.names[0].displayName)       || '',
        email:    (p.emailAddresses && p.emailAddresses[0] && p.emailAddresses[0].value)  || '',
        photoUrl: (p.photos         && p.photos[0]         && p.photos[0].url)             || ''
      };
    }).filter(function(r) { return r.email; });
    return { ok: true, data: { results: results } };
  } catch(e) {
    return { ok: false, error: e.message || String(e) };
  }
}

function loadChatSettings() {
  var props = PropertiesService.getScriptProperties();
  var keyJson = props.getProperty('CHAT_SA_KEY') || '';
  var saEmail = '', saProject = '';
  try { var k = JSON.parse(keyJson); saEmail = k.client_email||''; saProject = k.project_id||''; } catch(e) {}
  return {
    hasKey:       !!keyJson,
    saEmail:      saEmail,
    saProject:    saProject,
    webhookUrl:   props.getProperty('CHAT_WEBHOOK_URL') || '',
    spaceId:      props.getProperty('CHAT_SPACE_DEFAULT') || '',
    spaceName:    props.getProperty('CHAT_SPACE_NAME')    || 'MIM War Room',
    members:      props.getProperty('CHAT_MEMBERS_DEFAULT') || '',
    externalUsers: props.getProperty('CHAT_EXTERNAL_USERS') !== 'false'
  };
}

function saveChatSettings(data) {
  try {
    var props = PropertiesService.getScriptProperties();
    if (data.saKey) props.setProperty('CHAT_SA_KEY', data.saKey.trim());
    if (data.webhookUrl !== undefined) {
      if (data.webhookUrl) props.setProperty('CHAT_WEBHOOK_URL', data.webhookUrl.trim());
      else                 props.deleteProperty('CHAT_WEBHOOK_URL');
    }
    if (data.spaceName !== undefined) props.setProperty('CHAT_SPACE_NAME', data.spaceName || 'MIM War Room');
    if (data.spaceId  !== undefined) {
      if (data.spaceId) props.setProperty('CHAT_SPACE_DEFAULT', data.spaceId);
      else              props.deleteProperty('CHAT_SPACE_DEFAULT');
    }
    if (data.members  !== undefined) props.setProperty('CHAT_MEMBERS_DEFAULT', data.members || '');
    if (data.externalUsers !== undefined) props.setProperty('CHAT_EXTERNAL_USERS', data.externalUsers ? 'true' : 'false');
    return { ok: true };
  } catch(e) { return { ok: false, error: e.message || String(e) }; }
}

function testWebhook() {
  var url = PropertiesService.getScriptProperties().getProperty('CHAT_WEBHOOK_URL') || '';
  if (!url) return { ok: false, error: 'No webhook URL saved yet.' };
  var resp = UrlFetchApp.fetch(url, {
    method: 'post', contentType: 'application/json',
    payload: JSON.stringify({ text: '✅ MIM War Room webhook test — connection confirmed.' }),
    muteHttpExceptions: true
  });
  if (resp.getResponseCode() !== 200) return { ok: false, error: 'HTTP ' + resp.getResponseCode() + ': ' + resp.getContentText().slice(0, 200) };
  return { ok: true };
}

function testChatConnection() {
  var tok = _chatBotToken_();
  if (!tok) return { ok: false, error: 'No SA key stored or token mint failed. Check the key JSON is valid and the service account exists in GCP.' };
  var props    = PropertiesService.getScriptProperties();
  var keyJson  = props.getProperty('CHAT_SA_KEY') || '';
  var saEmail  = '';
  try { saEmail = JSON.parse(keyJson).client_email || ''; } catch(e) {}

  // List spaces the bot is a member of
  var resp = UrlFetchApp.fetch('https://chat.googleapis.com/v1/spaces?pageSize=20', {
    headers: { Authorization: 'Bearer ' + tok }, muteHttpExceptions: true
  });
  if (resp.getResponseCode() !== 200) return { ok: false, error: 'API call failed (' + resp.getResponseCode() + '): ' + resp.getContentText().slice(0, 300) };
  var spaces = JSON.parse(resp.getContentText()).spaces || [];

  // If a default space is set, try sending a test ping to it
  var defaultSpace = props.getProperty('CHAT_SPACE_DEFAULT') || '';
  var pingResult = null;
  if (defaultSpace) {
    var pingResp = UrlFetchApp.fetch('https://chat.googleapis.com/v1/' + defaultSpace + '/messages', {
      method: 'post',
      headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
      payload: JSON.stringify({ text: '✅ MIM War Room bot connection test — token valid and space reachable.' }),
      muteHttpExceptions: true
    });
    pingResult = { code: pingResp.getResponseCode(), body: pingResp.getContentText().slice(0, 200) };
  }

  return {
    ok: true, saEmail: saEmail,
    spaces: spaces.map(function(s) { return { name: s.name, displayName: s.displayName || '(unnamed)' }; }),
    pingResult: pingResult
  };
}

function _chatBotToken_() {
  var keyJson = PropertiesService.getScriptProperties().getProperty('CHAT_SA_KEY');
  if (!keyJson) return null;
  try {
    var key  = JSON.parse(keyJson);
    var now  = Math.floor(new Date().getTime() / 1000);
    var hdr  = Utilities.base64EncodeWebSafe(JSON.stringify({ alg: 'RS256', typ: 'JWT' })).replace(/=+$/, '');
    var clm  = Utilities.base64EncodeWebSafe(JSON.stringify({
      iss: key.client_email,
      scope: 'https://www.googleapis.com/auth/chat.bot',
      aud: 'https://oauth2.googleapis.com/token',
      iat: now, exp: now + 3600
    })).replace(/=+$/, '');
    var sig  = Utilities.base64EncodeWebSafe(
      Utilities.computeRsaSha256Signature(hdr + '.' + clm, key.private_key)
    ).replace(/=+$/, '');
    var resp = UrlFetchApp.fetch('https://oauth2.googleapis.com/token', {
      method: 'post',
      payload: { grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion: hdr + '.' + clm + '.' + sig },
      muteHttpExceptions: true
    });
    if (resp.getResponseCode() !== 200) return null;
    return JSON.parse(resp.getContentText()).access_token;
  } catch(e) { return null; }
}

function _actionChatMessageSend(payload) {
  try {
    var cfg       = payload.config || {};
    var data      = payload.data   || {};
    var surfaceId = String((payload.appConfig && payload.appConfig.id) || 'default');
    var sheetNm   = String(cfg.sheet || (payload.appConfig && payload.appConfig.storage && payload.appConfig.storage.sheet) || 'MajorIncidents');
    var context   = String(data.context || '').trim();

    var props2      = PropertiesService.getScriptProperties();
    var webhookUrl  = String(cfg.webhook_url || props2.getProperty('CHAT_WEBHOOK_URL') || '');

    // Use service account bot token (Card v2) falling back to user token (plain text only)
    var botTok2 = _chatBotToken_();
    var tok     = botTok2 || ScriptApp.getOAuthToken();
    var hdrs2   = { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' };

    var spaceName = String(
      cfg.space_name ||
      props2.getProperty('CHAT_SPACE_DEFAULT') ||
      props2.getProperty('CHAT_SPACE_' + surfaceId) ||
      ''
    );

    // Last-resort: search by display name
    if (!spaceName) {
      var targetName = String(cfg.name || props2.getProperty('CHAT_SPACE_NAME') || 'MIM War Room');
      try {
        var listResp = UrlFetchApp.fetch('https://chat.googleapis.com/v1/spaces?pageSize=50', {
          headers: hdrs2, muteHttpExceptions: true
        });
        if (listResp.getResponseCode() === 200) {
          var spaces = JSON.parse(listResp.getContentText()).spaces || [];
          spaces.forEach(function(s) {
            if (!spaceName && s.displayName === targetName) spaceName = s.name;
          });
          if (spaceName) {
            props2.setProperty('CHAT_SPACE_DEFAULT', spaceName);
            props2.setProperty('CHAT_SPACE_' + surfaceId, spaceName);
          }
        }
      } catch(e) {}
    }

    if (!spaceName) return { ok: false, error: 'No Chat space configured. Open Settings (⚙) to paste an existing space ID, or create a new space first.' };

    // Read incidents from sheet
    var sheet = _findSheet_(sheetNm);
    if (!sheet || sheet.getLastRow() < 2) return { ok: false, error: 'Sheet "' + sheetNm + '" not found or empty.' };

    var values  = sheet.getDataRange().getValues();
    var headers = values[0].map(function(h) { return String(h).toLowerCase().replace(/\s+/g, '_'); });
    var rows = [];
    for (var ri = 1; ri < values.length; ri++) {
      var row = {};
      for (var ci = 0; ci < headers.length; ci++) { row[headers[ci]] = values[ri][ci]; }
      rows.push(row);
    }
    var active   = rows.filter(function(r) { return r.status !== 'Resolved'; });
    var resolved = rows.filter(function(r) { return r.status === 'Resolved'; });

    var sender = Session.getActiveUser().getEmail();
    var name   = (payload.appConfig && payload.appConfig.user && payload.appConfig.user.name) || sender;
    var now    = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd MMM yyyy HH:mm z');

    function stIcn(s) { return s==='P1'?'STAR':s==='P2'?'DESCRIPTION':'BOOKMARK'; }
    function stLbl(s) { return s==='Claimed'?'[claimed]':s==='Resolved'?'[resolved]':'[new]'; }

    // Build Card v2 widgets for each active incident
    var activeWidgets = active.length === 0
      ? [{ textParagraph: { text: '<b>All incidents resolved.</b>' } }]
      : active.map(function(r) {
          return {
            decoratedText: {
              topLabel: (r.severity||'') + '  ·  ' + (r.id||''),
              text: '<b>' + (r.title||'') + '</b>',
              bottomLabel: stLbl(r.status) + '  ' + (r.status||'') + (r.owner_name ? '  ·  ' + r.owner_name : '  ·  Unassigned'),
              startIcon: { knownIcon: stIcn(r.severity) }
            }
          };
        });

    var resolvedWidgets = resolved.map(function(r) {
      return {
        decoratedText: {
          topLabel: (r.id||''),
          text: r.title||'',
          startIcon: { knownIcon: 'CONFIRMATION_NUMBER_ICON' }
        }
      };
    });

    var sections = [];

    if (context) {
      sections.push({
        header: 'Context',
        widgets: [{ textParagraph: { text: context } }]
      });
    }

    sections.push({
      header: 'Active Incidents (' + active.length + ')',
      widgets: activeWidgets
    });

    if (resolved.length > 0) {
      sections.push({
        header: 'Resolved (' + resolved.length + ')',
        widgets: resolvedWidgets
      });
    }

    sections.push({
      widgets: [{
        textParagraph: {
          text: 'Active: <b>' + active.length + '</b>  ·  Resolved: <b>' + resolved.length + '</b>  ·  Total: <b>' + rows.length + '</b>'
        }
      }]
    });

    // Build plain-text fallback (works for webhook + user-token paths)
    var lines = ['*MIM War Room — Status Update*', '_' + now + ' · ' + name + '_'];
    if (context) lines.push('\n*Context:* ' + context);
    if (active.length === 0) {
      lines.push('\n✅ All incidents resolved.');
    } else {
      lines.push('\n*Active Incidents (' + active.length + ')*');
      active.forEach(function(r) {
        var sIco = r.severity==='P1'?'🔴':r.severity==='P2'?'🟠':r.severity==='P3'?'🟡':'⚪';
        lines.push(sIco + ' *' + (r.severity||'') + '* — ' + (r.id||'') + '\n   ' + (r.title||'') + '\n   ' + (r.status||'') + (r.owner_name ? ' · ' + r.owner_name : ' · Unassigned'));
      });
    }
    lines.push('\n─────────────────────────\n📊 Active: *' + active.length + '* · Resolved: *' + resolved.length + '*');
    var plainText = lines.join('\n');

    // Priority: webhook > SA bot (Card v2) > user token (plain text)
    if (webhookUrl) {
      var cardBody = {
        cardsV2: [{
          cardId: 'mim-status',
          card: {
            header: {
              title: 'MIM War Room — Status Update',
              subtitle: now + '  ·  ' + name,
              imageUrl: 'https://www.gstatic.com/images/icons/material/system/2x/warning_red_24dp.png',
              imageType: 'CIRCLE'
            },
            sections: sections
          }
        }]
      };
      var whResp = UrlFetchApp.fetch(webhookUrl, {
        method: 'post', contentType: 'application/json',
        payload: JSON.stringify(cardBody),
        muteHttpExceptions: true
      });
      var whCode = whResp.getResponseCode();
      // Fall back to plain text if cardsV2 rejected (some older webhook endpoints)
      if (whCode !== 200) {
        var whResp2 = UrlFetchApp.fetch(webhookUrl, {
          method: 'post', contentType: 'application/json',
          payload: JSON.stringify({ text: plainText }),
          muteHttpExceptions: true
        });
        var whCode2 = whResp2.getResponseCode();
        if (whCode2 !== 200) return { ok: false, error: 'Webhook post failed (' + whCode2 + '): ' + whResp2.getContentText().slice(0, 200) };
        return { ok: true, data: { usedCard: false, via: 'webhook-text' } };
      }
      return { ok: true, data: { usedCard: true, via: 'webhook-card' } };
    }

    if (!spaceName) return { ok: false, error: 'No webhook or space configured. Open Settings (⚙) to add a webhook URL.' };

    var messagePayload, sendHeaders;
    if (botTok2) {
      sendHeaders = { Authorization: 'Bearer ' + botTok2, 'Content-Type': 'application/json' };
      messagePayload = {
        text: 'MIM War Room Status Update — ' + now + ' · Active: ' + active.length + ' · Resolved: ' + resolved.length,
        cardsV2: [{ cardId: 'mim-status', card: { header: { title: 'MIM War Room — Status Update', subtitle: now + '  ·  ' + name, imageUrl: 'https://www.gstatic.com/images/icons/material/system/2x/warning_red_24dp.png', imageType: 'CIRCLE' }, sections: sections } }]
      };
    } else {
      sendHeaders = hdrs2;
      messagePayload = { text: plainText };
    }

    var resp = UrlFetchApp.fetch('https://chat.googleapis.com/v1/' + spaceName + '/messages', {
      method: 'post', headers: sendHeaders,
      payload: JSON.stringify(messagePayload),
      muteHttpExceptions: true
    });
    var code = resp.getResponseCode();
    if (code !== 200) return { ok: false, error: 'Chat post failed (' + code + '): ' + resp.getContentText().slice(0, 200) };

    return { ok: true, data: { usedCard: !!botTok2, via: 'space' } };
  } catch(e) {
    return { ok: false, error: e.message || String(e) };
  }
}

function _actionChatSpaceCreate(payload) {
  try {
    var cfg       = payload.config || {};
    var data      = payload.data   || {};
    var props     = PropertiesService.getScriptProperties();
    var surfaceId = String((payload.appConfig && payload.appConfig.id) || 'default');
    var tok       = ScriptApp.getOAuthToken();
    var botTok    = _chatBotToken_();
    var base      = 'https://chat.googleapis.com/v1';
    var hdrs      = { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' };

    // If a default space is already configured, reuse it — skip creation
    var existingSpaceId = props.getProperty('CHAT_SPACE_DEFAULT') || '';
    if (existingSpaceId) {
      props.setProperty('CHAT_SPACE_' + surfaceId, existingSpaceId);
      var spaceUrl = 'https://chat.google.com/room/' + existingSpaceId.split('/')[1];
      return { ok: true, data: { spaceUrl: spaceUrl, spaceName: existingSpaceId, reused: true } };
    }

    // Build member list: settings defaults + payload members
    var defaultMembers = (props.getProperty('CHAT_MEMBERS_DEFAULT') || '').split(/[\s,\n]+/).map(function(e){return e.trim();}).filter(Boolean);
    var payloadMembers = String(data.members || _resolveTemplateTokens(cfg.members || '', payload.appConfig)).split(/[\s,]+/).map(function(e){return e.trim();}).filter(Boolean);
    var allMembers = defaultMembers.concat(payloadMembers.filter(function(e){return defaultMembers.indexOf(e)<0;}));

    var name   = String(_resolveTemplateTokens(props.getProperty('CHAT_SPACE_NAME') || cfg.name || 'War Room', payload.appConfig));
    var msg    = String(data.message || _resolveTemplateTokens(cfg.initial_message || '', payload.appConfig));
    var extOk  = props.getProperty('CHAT_EXTERNAL_USERS') !== 'false';

    // 1. Create the space
    var spaceResp = UrlFetchApp.fetch(base + '/spaces', {
      method: 'post', headers: hdrs,
      payload: JSON.stringify({ displayName: name, spaceType: 'SPACE', externalUserAllowed: extOk }),
      muteHttpExceptions: true
    });
    if (spaceResp.getResponseCode() !== 200) return { ok: false, error: 'Space create failed: ' + spaceResp.getContentText() };
    var space     = JSON.parse(spaceResp.getContentText());
    var spaceName = space.name;
    var spaceUrl  = 'https://chat.google.com/room/' + spaceName.split('/')[1];

    // 2. Bot adds itself using its own token + special 'users/app' identifier
    if (botTok) {
      try {
        var botSelfHdrs = { Authorization: 'Bearer ' + botTok, 'Content-Type': 'application/json' };
        UrlFetchApp.fetch(base + '/' + spaceName + '/members', {
          method: 'post', headers: botSelfHdrs,
          payload: JSON.stringify({ member: { name: 'users/app', type: 'BOT' } }),
          muteHttpExceptions: true
        });
      } catch(e) {}
    }

    // 3. Add human members
    allMembers.forEach(function(email) {
      try {
        UrlFetchApp.fetch(base + '/' + spaceName + '/members', {
          method: 'post', headers: hdrs,
          payload: JSON.stringify({ member: { name: 'users/' + email, type: 'HUMAN' } }),
          muteHttpExceptions: true
        });
      } catch(e) {}
    });

    // 4. Initial message
    if (msg) {
      try {
        var botHdrs = { Authorization: 'Bearer ' + (botTok || tok), 'Content-Type': 'application/json' };
        UrlFetchApp.fetch(base + '/' + spaceName + '/messages', {
          method: 'post', headers: botHdrs,
          payload: JSON.stringify({ text: msg }), muteHttpExceptions: true
        });
      } catch(e) {}
    }

    // Persist for this surface and as global default
    props.setProperty('CHAT_SPACE_' + surfaceId, spaceName);
    props.setProperty('CHAT_SPACE_DEFAULT', spaceName);
    props.setProperty('CHAT_SPACE_NAME', name);

    return { ok: true, data: { spaceUrl: spaceUrl, spaceName: spaceName, displayName: name } };
  } catch(e) {
    return { ok: false, error: e.message || String(e) };
  }
}

function _actionSheetImportCsv(payload) {
  try {
    var cfg     = payload.config || {};
    var csv     = String((payload.data || {}).csv || '');
    var sheetNm = String(cfg.sheet || (payload.appConfig && payload.appConfig.storage && payload.appConfig.storage.sheet) || '');
    var mapping = String(cfg.mapping || 'servicenow');
    if (!csv)     return { ok: false, error: 'No CSV data received' };
    if (!sheetNm) return { ok: false, error: 'No sheet name configured' };

    var lines = csv.split(/\r?\n/).filter(function(l) { return l.trim(); });
    if (lines.length < 2) return { ok: false, error: 'CSV has no data rows' };

    var srcHeaders = _parseCsvLine(lines[0]);

    // ServiceNow export column names → MIM sheet column names
    var snMap = {
      'Number':            'id',
      'Short description': 'title',
      'Priority':          'severity',
      'State':             'status',
      'Assigned to':       'owner_name',
      'Opened by':         'owner_email',
      'Opened':            'opened_at',
      'Updated':           'updated_at'
    };
    var colMap = mapping === 'servicenow' ? snMap : {};

    var sheet    = _getOrCreateSheet_(sheetNm);
    var lastCol  = sheet.getLastColumn();
    if (lastCol < 1) return { ok: false, error: 'Sheet has no headers — create it first' };
    var sheetHdr     = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
    var idColIdx     = sheetHdr.indexOf('id');
    var statusColIdx = sheetHdr.indexOf('status');
    if (idColIdx < 0) return { ok: false, error: 'Sheet missing id column' };

    var lastRow = sheet.getLastRow();
    var allData = lastRow > 1 ? sheet.getRange(2, 1, lastRow - 1, lastCol).getValues() : [];
    var existing = {};
    allData.forEach(function(row, i) {
      if (row[idColIdx]) existing[String(row[idColIdx])] = i + 2;
    });

    var statusNorm = { 'New': 'New', 'In Progress': 'Claimed', 'On Hold': 'New',
                       'Resolved': 'Resolved', 'Closed': 'Resolved', 'Cancelled': 'Resolved' };
    var imported = 0, updated = 0, skipped = 0;

    for (var r = 1; r < lines.length; r++) {
      var cells = _parseCsvLine(lines[r]);
      var rec   = {};
      srcHeaders.forEach(function(h, i) {
        var mimCol = colMap[h.trim()] || h.trim().toLowerCase().replace(/[\s/]+/g, '_');
        rec[mimCol] = (cells[i] || '').trim();
      });

      // Normalise priority "1 - Critical" → "P1"
      if (rec.severity) { var m = rec.severity.match(/^(\d)/); if (m) rec.severity = 'P' + m[1]; }
      if (rec.status && statusNorm[rec.status]) rec.status = statusNorm[rec.status];
      if (!rec.id) continue;

      var rowNum = existing[rec.id];
      if (rowNum) {
        var curStatus = allData[rowNum - 2][statusColIdx];
        if (curStatus === 'Resolved') { skipped++; continue; }
        var rowVals = sheet.getRange(rowNum, 1, 1, lastCol).getValues()[0];
        sheetHdr.forEach(function(col, ci) {
          if (rec[col] !== undefined && col !== 'id' && col !== 'opened_at') rowVals[ci] = rec[col];
        });
        sheet.getRange(rowNum, 1, 1, lastCol).setValues([rowVals]);
        updated++;
      } else {
        sheet.appendRow(sheetHdr.map(function(col) { return rec[col] !== undefined ? rec[col] : ''; }));
        existing[rec.id] = sheet.getLastRow();
        imported++;
      }
    }
    return { ok: true, data: { imported: imported, updated: updated, skipped: skipped } };
  } catch(e) {
    return { ok: false, error: e.message || String(e) };
  }
}

function _parseCsvLine(line) {
  var result = [], cur = '', inQ = false;
  for (var i = 0; i < line.length; i++) {
    var c = line[i];
    if (c === '"') {
      if (inQ && line[i + 1] === '"') { cur += '"'; i++; } else inQ = !inQ;
    } else if (c === ',' && !inQ) {
      result.push(cur); cur = '';
    } else { cur += c; }
  }
  result.push(cur);
  return result;
}

function _actionCalendarEvent(payload) {
  var cfg   = payload.config || {};
  var title = String(_resolveTemplateTokens(cfg.title || 'Event', payload.appConfig));
  var start = new Date(_resolveTemplateTokens(cfg.start || '', payload.appConfig));
  var end   = new Date(_resolveTemplateTokens(cfg.end   || '', payload.appConfig));
  var calId = cfg.calendar_id || 'primary';
  var cal   = calId === 'primary' ? CalendarApp.getDefaultCalendar() : CalendarApp.getCalendarById(calId);
  if (!cal) return { ok: false, error: 'calendar_event: calendar not found: ' + calId };
  var opts = {};
  if (cfg.description) opts.description = String(_resolveTemplateTokens(cfg.description, payload.appConfig));
  if (cfg.attendees)   opts.guests      = String(_resolveTemplateTokens(cfg.attendees,   payload.appConfig));
  var event = cal.createEvent(title, start, end, opts);
  return { ok: true, data: { event_id: event.getId() } };
}

function _actionCalendarMeet(payload) {
  try {
    var cfg   = payload.config || {};
    var title = String(_resolveTemplateTokens(cfg.title || 'War Room', payload.appConfig));
    var dur   = parseInt(cfg.duration_minutes || 60, 10);
    var desc  = cfg.description ? String(_resolveTemplateTokens(cfg.description, payload.appConfig)) : '';
    var now   = new Date();
    var end   = new Date(now.getTime() + dur * 60 * 1000);
    var tz    = Session.getScriptTimeZone();

    var event = {
      summary:     title,
      description: desc,
      start: { dateTime: now.toISOString(), timeZone: tz },
      end:   { dateTime: end.toISOString(),  timeZone: tz },
      conferenceData: {
        createRequest: {
          requestId: Utilities.getUuid(),
          conferenceSolutionKey: { type: 'hangoutsMeet' }
        }
      }
    };
    var created = Calendar.Events.insert(event, 'primary', { conferenceDataVersion: 1 });

    var meetLink = '';
    if (created.conferenceData && created.conferenceData.entryPoints) {
      created.conferenceData.entryPoints.forEach(function(ep) {
        if (ep.entryPointType === 'video' && !meetLink) meetLink = ep.uri;
      });
    }
    return { ok: true, data: { meetLink: meetLink, calLink: created.htmlLink || '', eventId: created.id || '' } };
  } catch(e) {
    return { ok: false, error: e.message || String(e) };
  }
}

function _actionApiPost(payload) {
  var cfg  = payload.config || {};
  var url  = String(_resolveTemplateTokens(cfg.url || '', payload.appConfig));
  if (!url) return { ok: false, error: 'api_post: url is required' };
  var body    = _resolveCollect(cfg.collect || {}, payload.appConfig);
  var headers = cfg.headers || {};
  var ct      = cfg.content_type || 'application/json';
  headers['Content-Type'] = ct;
  var resp = UrlFetchApp.fetch(url, {
    method: 'post', headers: headers,
    payload: ct === 'application/json' ? JSON.stringify(body) : body,
    muteHttpExceptions: true
  });
  var code = resp.getResponseCode();
  var data = {};
  try { data = JSON.parse(resp.getContentText()); } catch(e) { data = { raw: resp.getContentText() }; }
  return { ok: code >= 200 && code < 300, data: { result: data, status_code: code } };
}

function _actionScriptRun(payload) {
  var cfg = payload.config || {};
  var fn  = cfg.fn;
  if (!fn || typeof this[fn] !== 'function') {
    return { ok: false, error: 'script_run: function not found: ' + fn };
  }
  var args = (cfg.args || []).map(function(a) { return _resolveTemplateTokens(a, payload.appConfig); });
  var result = this[fn].apply(null, args);
  return { ok: true, data: { result: result } };
}

function _actionAdsbQuery(payload) {
  var config = payload.config || {};
  var lamin = config.lamin !== undefined ? config.lamin : 43.0;
  var lomin = config.lomin !== undefined ? config.lomin : 1.0;
  var lamax = config.lamax !== undefined ? config.lamax : 44.5;
  var lomax = config.lomax !== undefined ? config.lomax : 2.5;
  try {
    var url = 'https://opensky-network.org/api/states/all' +
      '?lamin=' + lamin + '&lomin=' + lomin + '&lamax=' + lamax + '&lomax=' + lomax;
    var resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    if (resp.getResponseCode() !== 200) return { ok: false, error: 'OpenSky HTTP ' + resp.getResponseCode() };
    var json  = JSON.parse(resp.getContentText());
    var flights = (json.states || [])
      .filter(function(s) { return s[5] !== null && s[6] !== null && !s[8]; })
      .map(function(s) {
        return {
          callsign: ((s[1] || s[0] || 'UNKN').trim()) || s[0],
          lat:    s[6],
          lon:    s[5],
          alt_ft: s[7]  ? Math.round(s[7]  * 3.28084) : 0,
          spd_kt: s[9]  ? Math.round(s[9]  * 1.944)   : 0,
          hdg:    s[10] || 0,
          squawk: s[14] || '0000'
        };
      });
    return { ok: true, data: flights };
  } catch(e) {
    return { ok: false, error: e.message };
  }
}

// ─── Wired surface ────────────────────────────────────────────────────────────

var _WIRED_ATOM_ALIASES = {
  'text_input': 'form_input',
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

function _renderWiredSurface(payload) {
  var title      = payload.title || 'A2UI Wired Surface';
  var theme      = payload.theme || 'light';
  var layout     = payload.layout || [];
  var primitives = payload.state_primitives || [];
  var content    = '';

  layout.forEach(function(el) {
    var rawType = el.atom || el.type;
    // Layout structure primitives — not atoms, just HTML wrappers
    if (rawType === 'row_open') {
      var p = el.props || {};
      content += '<div style="display:flex;gap:' + (p.gap || '24px') + ';align-items:' + (p.align || 'stretch') + ';' + (p.style || '') + '">';
      return;
    }
    if (rawType === 'row_close') { content += '</div>'; return; }

    var props = el.props || {};
    var block = {};
    Object.keys(props).forEach(function(k) { block[k] = props[k]; });
    block.type      = _WIRED_ATOM_ALIASES[rawType] || rawType;
    block.component = el.component;

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

  content += include('A2UIState');

  var tmpl        = HtmlService.createTemplateFromFile('AtomPage');
  tmpl.title      = title;
  tmpl.content    = content;
  tmpl.theme      = theme;
  tmpl.sidebar    = false;
  var webAppUrl   = _getWebAppUrl();
  var pRaw        = payload._p || '';
  var clientSchema = JSON.parse(JSON.stringify(payload));
  delete clientSchema._p;
  clientSchema._fullUrl = pRaw ? (webAppUrl + '?p=' + pRaw) : webAppUrl;
  tmpl.schemaJson  = JSON.stringify(clientSchema).replace(/<\//g, '<\\/');
  tmpl.navSlug     = '';
  tmpl.fromSlug    = '';
  tmpl.webAppUrl   = webAppUrl;
  // Show settings gear on surfaces that use chat actions
  var hasChatAction = (payload.actions || []).some(function(a) { return String(a.type||'').indexOf('chat')!==-1; });
  tmpl.settingsUrl  = hasChatAction ? (webAppUrl + '?settings=chat') : '';
  return tmpl.evaluate()
    .setTitle(title)
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ─────────────────────────────────────────────────────────────────────────────

function _renderFromPayload(payload, from) {
  try {
    if (!Array.isArray(payload) && payload.type === 'a2ui_wired_surface') {
      return _renderWiredSurface(payload);
    }
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
      return _renderFullscreenHtml(title, content);
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

/**
 * Render the AirspaceFullscreen HTML template without spawning a nested worker.
 * In gas-fakes, HtmlTemplate.evaluate() spawns a second Worker thread inside the
 * already-running page Worker (each loads all .gs files fresh). Replacing with direct
 * string injection eliminates the nested spawn and is safe because AirspaceFullscreen.html
 * only has two scriptlets: <?= title ?> (escaped) and <?!= content ?> (raw).
 */
function _renderFullscreenHtml(title, content) {
  var html = HtmlService.createHtmlOutputFromFile('AirspaceFullscreen').getContent();
  var safe = (title || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  html = html.replace('<?= title ?>', safe).replace('<?!= content ?>', content || '');
  return HtmlService.createHtmlOutput(html)
    .setTitle(title || '')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
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
  var slideTitle = slide.chyron_title || 'Toulouse Airspace';
  var content    = renderAtoms(blocks, { theme: 'dark' }) + nav;
  return _renderFullscreenHtml(slideTitle, content);
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
  var content    = renderAtoms(blocks, { theme: 'dark' }) + nav;
  var deckTitle  = slide.chyron_title || slide.label || 'Airspace';
  return _renderFullscreenHtml(deckTitle, content);
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

// Run this once in the GAS editor to authorize Drive + Sheets scopes
function authorizeScopes() {
  DriveApp.getRootFolder();
  SpreadsheetApp.getActiveSpreadsheet();
}

