#!/usr/bin/env python3
"""Generate the self-contained MCP Apps renderer bundle — the FULL catalog.

v2 (2026-07-10): concatenation, not extraction. The 2026-07-10 classification
scan (recorded in a2ui-private/spec/mcp-apps-surface-v0.1.md) showed 16 of 22
renderer files are pure string-building with zero server tokens, the guarded
Workspace renderers fall through to their mock path in a browser by design,
and renderAtoms' PropertiesService pack-gate is already try/catch'd (undefined
→ all packs on). So whole .gs files go in VERBATIM, in GAS load order
(PackMap, atom.gs, then atoms_*.gs sorted — matching production last-wins for
the globe_3d double-registration), plus:
  - a prelude shim for _getWebAppUrl (defined in the excluded Code.gs),
  - degraded-card overrides for the 6 class-C atoms (unguarded render-time
    server fetches: no browser path until host-mediated tools/call exists),
  - the client partials (AtomScripts/A2UIState/A2uiUpdates — already
    feature-guarded for non-GAS hosts),
  - the MCP Apps View protocol handshake (spec 2026-01-26, apps.mdx).

Layout note: the bundle is split into marked <script> blocks so tests can
execute the DOM-free core block alone under Node (the client partials touch
window/document at load time; the core never does outside emitted strings).

Output is generated, never hand-edited:
public/surfaces/mcp-apps/renderer-bundle.html
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_DIR = ROOT / "apps-script-surface" / "gas-wired-renderer"
OUT = ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html"
PDFJS_PATH = RENDERER_DIR / "vendor" / "pdfjs" / "pdf.min.mjs"
QRCODEGEN_PATH = RENDERER_DIR / "vendor" / "qrcodegen" / "qrcodegen.js"

# atoms_schema_snapshot.gs: 124 KB of docs, zero _RENDERERS entries.
EXCLUDE_FILES = {"atoms_schema_snapshot.gs"}

# Class C — real, unguarded render-time server calls (UrlFetchApp / Vertex /
# Firestore / CacheService). Everything else in the catalog either has no
# server tokens or guards them with `typeof X !== 'undefined'` mock
# fallbacks. data_source joined the list empirically: the all-atoms sweep
# caught it calling CacheService at render time (it's part of the live-feed
# family with adsb_feed/metar_feed).
# (adsb_feed and metar_feed graduated 2026-07-10: they now ship registry-
# driven browser transports over the DECLARED data proxy — see
# atoms/data-sources.yaml and DATA_FEEDS_JS below.)
CLASS_C = ["doc_ai_summary", "multi_doc_ai_brief", "gemini_handoff",
           "firestore_read", "data_source"]

PARTIALS = ["AtomScripts.html", "A2UIState.html", "A2uiUpdates.html"]

PRELUDE = """
// ---- browser prelude ----
// Code.gs (server routing) is excluded from this bundle; provide the one
// cross-file symbol renderers call from it. Sub-page links degrade to '#'.
// GAS host services (DriveApp, GmailApp, SpreadsheetApp, CalendarApp, ...)
// stay DELIBERATELY undefined: guarded renderers must take their mock path.
function _getWebAppUrl() { return '#'; }
// geo_iso_takeoff calls ScriptApp.getService().getUrl() UNGUARDED to build a
// self-referential radar URL — the one canvas atom that touches a GAS
// service at render time. All other ScriptApp users are class-C (overridden
// below), so this inert shim only affects that link target.
var ScriptApp = { getService: function () { return { getUrl: function () { return '#'; } }; } };
// Utilities.base64EncodeWebSafe(Utilities.newBlob(s).getBytes()) — used by
// geo_iso_takeoff (and conditionally by module_map ?p= sub-links) to encode
// payload URLs. Faithful browser equivalent so those links actually work.
var Utilities = {
  newBlob: function (s) { return { getBytes: function () { return s; } }; },
  base64EncodeWebSafe: function (s) {
    var str = typeof s === 'string' ? s : String(s);
    var b64 = (typeof btoa !== 'undefined')
      ? btoa(unescape(encodeURIComponent(str)))
      : Buffer.from(str, 'utf8').toString('base64');
    return b64.replace(/\\+/g, '-').replace(/\\//g, '_');
  }
};
""".strip()


def class_c_overrides():
    quoted = ",".join("'%s'" % t for t in CLASS_C)
    return """
// ---- class-C overrides ----
// These atoms perform real render-time server fetches with no browser path.
// Until the host-mediated tools/call data path exists (Phase 2 server
// wiring), they render an honest placeholder instead of an error callout.
[%s].forEach(function (t) {
  _RENDERERS[t] = function (b) {
    return '<div class="asw-degraded-card">' +
      '<div class="asw-degraded-title">\\u26a1 ' + _esc(t) + ' needs a live backend</div>' +
      '<div class="asw-degraded-text">This atom fetches live data server-side. ' +
      'It renders fully on the Apps Script surface; in this MCP Apps view it is a placeholder.</div>' +
      '</div>';
  };
});
window.__a2uiAtomCount = Object.keys(_RENDERERS).length;
""" % quoted


DATA_FEEDS_JS = r"""
// ---- declared-data-source feed transports (browser) ----
// adsb_feed / metar_feed over the DECLARED proxy (A2UI_DATA_SOURCES,
// compiled from atoms/data-sources.yaml). Same dispatch contract as the GAS
// originals: window.A2UI_DATA[name] + window.A2UI_CALLBACKS[name](data).
// Reuses the bundle's own pure normalizers (_normaliseAdsbLol, _parseMETAR).
// Until the worker proxy route is deployed, fetches fail silently -> feeds
// stay quiet -> consumers remain in their simulated/fallback mode by design.
// Client polling is clamped to the declared min_client_refresh_s/cache_ttl_s
// (polling faster than the edge cache never reaches the upstream).
_RENDERERS['adsb_feed'] = function (b) {
  var reg = (typeof A2UI_DATA_SOURCES !== 'undefined') && A2UI_DATA_SOURCES.sources.adsb;
  if (!reg) return '<!-- a2ui: adsb data source not declared -->';
  var name = b.name || 'adsb';
  var clat = b.center_lat !== undefined ? b.center_lat : reg.params.lat['default'];
  var clon = b.center_lon !== undefined ? b.center_lon : reg.params.lon['default'];
  var dist = Math.min(b.radius_nm !== undefined ? b.radius_nm : reg.params.dist['default'], reg.params.dist.max);
  var filterGnd = b.filter_ground !== false;
  var refresh = Math.max(b.refresh !== undefined ? b.refresh : reg.min_client_refresh_s,
                         reg.min_client_refresh_s, reg.cache_ttl_s);
  var url = A2UI_DATA_SOURCES.proxy_base + '/adsb?lat=' + encodeURIComponent(clat) +
            '&lon=' + encodeURIComponent(clon) + '&dist=' + encodeURIComponent(dist);
  return '<script>(function(){' +
    'window.A2UI_DATA=window.A2UI_DATA||{};window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
    'function dispatch(flights){window.A2UI_DATA["' + _esc(name) + '"]=flights;' +
      'var cb=window.A2UI_CALLBACKS["' + _esc(name) + '"];if(typeof cb==="function")cb(flights);}' +
    'function pull(){fetch("' + url + '").then(function(r){if(!r.ok)throw 0;return r.json();})' +
      // Only dispatch a NON-EMPTY set. A 200 carrying {"ac":[]} is a
      // successful answer meaning "no traffic right now", not new data --
      // dispatching it overwrites airspace_command_deck's simulated flights
      // with nothing and the scope goes blank. The stated design here is
      // "feeds stay quiet -> consumers remain in their simulated/fallback
      // mode", but only fetch FAILURES were ever quiet; an empty success was
      // not. Observed 2026-08-01: adsb.lol returned ac:[] for the LFBO box
      // (verified upstream, direct, 101 bytes) and the ChatGPT radar showed
      // no aircraft at all rather than the simulated traffic it advertises.
      '.then(function(raw){var _f=_normaliseAdsbLol(raw,' + (filterGnd ? 'true' : 'false') + ');' +
      'if(_f&&_f.length)dispatch(_f);})' +
      '.catch(function(){});}' +
    'setTimeout(pull,120);' +
    'setInterval(pull,' + Math.round(refresh * 1000) + ');' +
  '})();<\/script>';
};

_RENDERERS['metar_feed'] = function (b) {
  var reg = (typeof A2UI_DATA_SOURCES !== 'undefined') && A2UI_DATA_SOURCES.sources.metar;
  if (!reg) return '<!-- a2ui: metar data source not declared -->';
  var name = b.name || 'metar';
  var station = String(b.station || reg.params.station['default']).toUpperCase();
  var refresh = Math.max(b.refresh !== undefined ? b.refresh : reg.min_client_refresh_s,
                         reg.min_client_refresh_s);
  var url = A2UI_DATA_SOURCES.proxy_base + '/metar?station=' + encodeURIComponent(station);
  return '<script>(function(){' +
    'window.A2UI_DATA=window.A2UI_DATA||{};window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
    'function dispatch(d){window.A2UI_DATA["' + _esc(name) + '"]=d;' +
      'var cb=window.A2UI_CALLBACKS["' + _esc(name) + '"];if(typeof cb==="function")cb(d);}' +
    'function pull(){fetch("' + url + '").then(function(r){if(!r.ok)throw 0;return r.text();})' +
      '.then(function(t){var raw=(t||"").trim().split("\\n")[0].trim();' +
      'if(raw)dispatch(_parseMETAR(raw));}).catch(function(){});}' +
    'setTimeout(pull,150);' +
    'setInterval(pull,' + Math.round(refresh * 1000) + ');' +
  '})();<\/script>';
};
""".strip()


HANDSHAKE = """
// ---- MCP Apps View protocol handshake (spec 2026-01-26, apps.mdx) ----
(function() {
  var initId = 'init-' + Math.random().toString(36).slice(2);
  // 2026-07-27 fix: claude.ai keeps the iframe reserved-but-hidden until it
  // receives ui/notifications/initialized. Gating that send on matching
  // THIS view's own init request id (the old `msg.id === initId` check
  // below) deadlocks if the host's result-bearing reply doesn't carry that
  // id back, or arrives in a shape we don't expect: the host waits for
  // `initialized`, we wait for a response we never recognise, nothing ever
  // mounts. Confirmed against a working reference implementation: send
  // `initialized` UNCONDITIONALLY once, via (a) a short timeout fallback
  // and (b) on ANY result-bearing reply, not only one matching initId.
  var _didInit = false;
  function sendInitialized() {
    if (_didInit) return;
    _didInit = true;
    post({ jsonrpc: '2.0', method: 'ui/notifications/initialized' });
  }

  function post(msg) { window.parent.postMessage(msg, '*'); }

  // Host-aware display mode (2026-07-27): hub (subject-tab + multi-slide deck
  // navigation) is EXPLICITLY called out as a poor fit for an inline card in
  // Claude's own MCP Apps design guidelines -- "Deep navigation (no drill-ins,
  // breadcrumbs, or multiple views)" is a listed pattern to AVOID inline;
  // fullscreen is the documented home for exactly this ("tabs or pagination
  // to disclose details"). Rather than let a hub render cramped/clipped
  // inline (inline cards auto-fit height with NO nested scrolling -- the
  // host clips anything taller), request fullscreen proactively the moment
  // one is painted while still inline.
  // playbook (atoms_airspace.gs) joined this list 2026-07-27: it declares
  // itself "always full-page" in its own source (breaks out of the normal
  // asw-page container, forces html/body margin:0, width:100vw) -- the exact
  // same deep-navigation shape as hub, just with nav pill buttons instead of
  // subject tabs. Same reasoning applies identically.
  var _hostContext = {};
  var _fsReqSeq = 0;

  // 2026-08-01: playbook/hub slide containers default to min-height:100vh.
  // That is right on GAS/web and in a GRANTED fullscreen, and wrong in an
  // inline card, where 100vh resolves against the HOST page viewport: short
  // slide content ends up buried below a viewport of empty space. Found in
  // ChatGPT -- clicking a nav pill genuinely worked, but you had to scroll
  // past a blank screen to see the slide, which reads as "it didn't move".
  // ADDITIVE by design: hosts with no handshake (GAS, plain web) never get
  // the class, so their existing full-page behaviour is untouched, and a
  // granted fullscreen doesn't get it either.
  function _syncDisplayModeClass() {
    var el = document.documentElement;
    if (!el || !el.classList) return;
    // Only clamp on an EXPLICIT inline report. Defaulting unknown -> inline
    // (the 2026-08-01 first cut) changes behaviour on every host that simply
    // never sends displayMode, which is how this clamped Claude's deck to a
    // sliver when nothing was wrong there. Absence of information must not
    // change rendering: unknown keeps the pre-existing full-height path.
    el.classList.toggle('a2ui-inline', _hostContext.displayMode === 'inline');
  }
  function _maybeRequestFullscreen(payload) {
    // Classic blocks dialect OR the v1.0 envelope's createSurface.components
    // (paint() decodes the latter internally via _rehydrateV1Surface; this
    // check runs on the raw pre-decode payload, so it inspects both shapes
    // directly rather than duplicating that decode step just to look).
    // Wired surfaces keep their atoms in `layout` under an `atom` key, not in
    // `blocks` under `type` — so this check simply never saw one and every
    // wired surface stayed an inline card regardless of what it contained.
    var blocks = (payload && payload.blocks) ||
      (payload && payload.createSurface && payload.createSurface.components) ||
      (payload && payload.layout) ||
      (Array.isArray(payload) ? payload : []);
    var _type = function (b) { return b && (b.component || b.type || b.atom); };
    // WHICH SURFACES EARN THE VIEWPORT. Not "big" — surfaces you navigate
    // rather than read past: hub and playbook have their own internal nav;
    // concept_ladder is the article playbook's artifact, a rung rail whose
    // whole argument structure is the point and which reads as a keyhole in a
    // chat card; a2ui_wired_surface is an APP with inputs and buttons, and a
    // form squeezed into a card is the worst of both. (2026-08-03, Curtis.)
    var hasDeepNav = (payload && payload.type === 'a2ui_wired_surface') ||
      blocks.some(function (b) {
        var t = _type(b);
        return t === 'hub' || t === 'playbook' || t === 'concept_ladder';
      });
    if (!hasDeepNav) return;
    // gdm_rocket_panel / iso_fireworks_panel are fixed, half-viewport overlay
    // atoms (data-a2ui-overlay in atoms_canvas.gs) authored for the INLINE
    // layout -- position:fixed pinned to one half of the card. Fullscreen
    // hosts don't guarantee a bounded viewport the way an inline card does
    // (Curtis observed live on claude.ai, 2026-07-27: fullscreen mode let the
    // hub's min-height:100vh body balloon into a much taller, scrollable
    // canvas instead of a fixed one-screenful frame), so an overlay built
    // assuming "100% height = one screenful" reads as broken, not just
    // differently sized. If a payload mixes a hub with one of these, don't
    // drag it into fullscreen just because the hub is present.
    var hasFixedOverlay = blocks.some(function (b) {
      var t = _type(b);
      return t === 'gdm_rocket_panel' || t === 'iso_fireworks_panel';
    });
    if (hasFixedOverlay) return;
    var mode = _hostContext.displayMode || 'inline';
    if (mode === 'fullscreen') return;                                    // already there
    var modes = _hostContext.availableDisplayModes;
    if (modes && modes.indexOf('fullscreen') === -1) return;              // host doesn't offer it
    post({ jsonrpc: '2.0', id: 'fsreq-' + (++_fsReqSeq), method: 'ui/request-display-mode', params: { mode: 'fullscreen' } });
  }

  // The SAME shared renderer source backs both GAS surfaces (where GAS wraps
  // pages in its own iframe, so target="_top" correctly escapes to the real
  // browser tab) and this MCP Apps bundle (where "top" is the HOST's own
  // page -- claude.ai -- and browsers correctly refuse to let a sandboxed
  // third-party iframe navigate it: confirmed live, 2026-07-27, "Unsafe
  // attempt to initiate navigation... sandboxed... allow-top-navigation...
  // not set"). Rather than touch 30+ call sites across atom.gs/atoms_*.gs
  // (shared with GAS, where _top is CORRECT), rewrite in ONE place, only
  // here: any link the paint pass produces targeting "_top" opens in a new
  // tab instead, which sandboxed iframes are allowed to do.
  function _detopLinks(root) {
    var links = root.querySelectorAll('a[target="_top"]');
    for (var i = 0; i < links.length; i++) links[i].setAttribute('target', '_blank');
  }

  function paint(payload) {
    // A2UI v1.0 envelope -> legacy dialect via the SAME decoder GAS uses
    // (atoms_v1_decode.gs, concatenated into this bundle). Template variant,
    // dataModel bindings and @index all resolve before renderAtoms sees it.
    if (payload && !Array.isArray(payload) && payload.version === 'v1.0' && payload.createSurface) {
      payload = _rehydrateV1Surface(payload.createSurface);
    }
    var root = document.getElementById('a2ui-root');
    // theme:"terminal" is the brand skin (AtomStyles.html) and is DARK PLUS a
    // token repaint -- it sets both classes, so anything keying off the dark
    // class in JS keeps working and never has to know a third theme exists.
    var _terminal = payload.theme === 'terminal';
    document.body.classList.toggle('asw-dark-theme', payload.theme === 'dark' || _terminal);
    document.body.classList.toggle('asw-terminal-theme', _terminal);
    // Wired dialect (spec/wired-transport-v0.1.md): expand templates, render the
    // layout with the SAME extracted loop GAS uses, then boot the state engine —
    // actions route through _a2uiActionTransport (host tools/call on this surface).
    if (payload.type === 'a2ui_wired_surface') {
      if (payload.variants || payload.wired_templates) {
        payload = _expandWiredSurface(payload, '', '');
      }
      root.innerHTML = _a2uiRenderWiredLayout(payload);
      _reExecuteScripts(root);
      _detopLinks(root);
      if (typeof window._a2uiBootWiredSurface === 'function') {
        window._a2uiBootWiredSurface(payload);
      }
      // The wired branch returns before paint()'s tail, so it has to ask for
      // itself — the tool-result handler's call ran against the raw payload
      // before this decode, and never matched a wired surface anyway.
      _maybeRequestFullscreen(payload);
      reportSize();
      return;
    }
    root.innerHTML = renderAtoms(payload.blocks || [], { theme: payload.theme });
    // Overlay-aware layout: constrain flowing content to the opposite half
    // when an atom DECLARES itself a half-viewport overlay (right by default;
    // left-half overlays push content right instead).
    root.classList.toggle('a2ui-with-overlay', !!root.querySelector('[data-a2ui-overlay]'));
    root.classList.toggle('a2ui-overlay-left', !!root.querySelector('[data-a2ui-overlay="left-half"]'));
    _reExecuteScripts(root);
    _detopLinks(root);
  }

  // innerHTML-injected <script> tags never execute (browsers block it);
  // interactive atoms ship inline <script>, so re-create + re-append each
  // one to actually run it.
  function _reExecuteScripts(root) {
    var scripts = root.querySelectorAll('script');
    for (var i = 0; i < scripts.length; i++) {
      var old = scripts[i];
      var fresh = document.createElement('script');
      fresh.textContent = old.textContent;
      old.parentNode.replaceChild(fresh, old);
    }
  }

  window.addEventListener('message', function(ev) {
    var msg = ev.data;
    if (!msg || msg.jsonrpc !== '2.0') return;

    if (msg.result && !msg.method) {
      // Distinguish the init ack (carries hostContext, id === initId) from a
      // reply to our OWN ui/request-display-mode call (id starts 'fsreq-',
      // carries the resulting mode per spec) -- both are result-bearing
      // replies with no .method, but only one is the initial handshake.
      if (msg.id === initId && msg.result.hostContext) _hostContext = msg.result.hostContext;
      else if (typeof msg.id === 'string' && msg.id.indexOf('fsreq-') === 0 && msg.result.mode) {
        _hostContext.displayMode = msg.result.mode;
      }
      _syncDisplayModeClass();
      sendInitialized();
      return;
    }

    // Host MAY notify display-mode/theme/etc changes at any time -- keep our
    // tracked context current so a later hub paint doesn't re-request a mode
    // change the user already made (e.g. manually closing fullscreen).
    if (msg.method === 'ui/notifications/host-context-changed') {
      var patch = msg.params || {};
      for (var k in patch) { if (patch.hasOwnProperty(k)) _hostContext[k] = patch[k]; }
      _syncDisplayModeClass();
      return;
    }

    if (msg.method === 'ui/notifications/tool-result') {
      var result = msg.params || {};
      paint(result.structuredContent || {});
      reportSize();
      _maybeRequestFullscreen(result.structuredContent || {});
    }
  });

  // ui/notifications/size-changed — REQUIRED for flexible-height hosts: they
  // size the iframe FROM this notification (spec: "hosts MUST listen"), and
  // without it the view mounts at zero height — the claude.ai
  // rendered-but-invisible incident, 2026-07-11. Debounced ResizeObserver
  // where available; explicit reportSize() after every paint regardless.
  var _lastW = 0, _lastH = 0, _sizeT = null;
  function reportSize() {
    var w = Math.ceil(document.documentElement.scrollWidth || 0);
    var h = Math.ceil(document.documentElement.scrollHeight || 0);
    if (!h || (w === _lastW && h === _lastH)) return;
    _lastW = w; _lastH = h;
    post({ jsonrpc: '2.0', method: 'ui/notifications/size-changed',
           params: { width: w, height: h } });
  }
  if (typeof ResizeObserver !== 'undefined') {
    new ResizeObserver(function () {
      clearTimeout(_sizeT);
      _sizeT = setTimeout(reportSize, 80);
    }).observe(document.documentElement);
  }
  setTimeout(reportSize, 150);

  // The wired engine's paint sink (paint_result actions — e.g. distill:
  // the returned surface REPLACES the view). Same paint() the handshake uses.
  window._A2UI_PAINT = paint;

  // View->host tool calls (spec: plain JSON-RPC tools/call over the bridge;
  // the host enforces app-visibility). Powers the wired dialect's host
  // transport (_a2uiActionTransport in the A2UIState partial).
  var _pending = {};
  window._A2UI_HOST_BRIDGE = {
    callTool: function (name, args) {
      return new Promise(function (resolve, reject) {
        var id = 'tc-' + Math.random().toString(36).slice(2);
        _pending[id] = { resolve: resolve, reject: reject };
        setTimeout(function () {
          if (_pending[id]) { delete _pending[id]; reject(new Error('host tools/call timeout: ' + name)); }
        }, 15000);
        post({ jsonrpc: '2.0', id: id, method: 'tools/call',
               params: { name: name, arguments: args || {} } });
      });
    }
  };
  window.addEventListener('message', function (ev) {
    var msg = ev.data;
    if (!msg || msg.jsonrpc !== '2.0' || !_pending[msg.id]) return;
    var pend = _pending[msg.id];
    delete _pending[msg.id];
    if (msg.error) pend.reject(new Error(msg.error.message || 'tools/call failed'));
    else pend.resolve(msg.result);
  });

  post({
    jsonrpc: '2.0',
    id: initId,
    method: 'ui/initialize',
    params: {
      capabilities: {},
      protocolVersion: '2026-01-26',
      clientInfo: { name: 'a2ui-catalog-view', version: '1' },
      appCapabilities: { availableDisplayModes: ['inline', 'fullscreen'] }
    }
  });
  // Fallback: guarantees a visibility-gating host reveals the iframe even if
  // it never sends a recognisable result-bearing reply to ui/initialize.
  setTimeout(sendInitialized, 500);
})();
""".strip()




def data_sources_js():
    """The declared network-access registry, inlined for the View. Single
    source: atoms/data-sources.yaml via gen_data_sources.build()."""
    import json as _json
    sys.path.insert(0, str(ROOT / "scripts"))
    from gen_data_sources import build as _build_registry
    return ("// ---- declared data-source registry (atoms/data-sources.yaml) ----\n"
            "var A2UI_DATA_SOURCES = " +
            _json.dumps(_build_registry(), ensure_ascii=False) + ";")

def renderer_files():
    """GAS load order: PackMap + atom.gs first, then atoms_* sorted — the
    order production runs in (last definition wins, e.g. globe_3d)."""
    atoms = sorted(p for p in RENDERER_DIR.glob("atoms_*.gs")
                   if p.name not in EXCLUDE_FILES)
    return [RENDERER_DIR / "PackMap.gs", RENDERER_DIR / "atom.gs"] + atoms


def partial_body(name):
    text = (RENDERER_DIR / name).read_text().strip()
    assert text.startswith("<script>") and text.endswith("</script>"), \
        f"{name}: expected a single <script> wrapper"
    return text[len("<script>"):-len("</script>")]


def pdfjs_module_block():
    """MCP-Apps-surface-only, main-thread mode (no separate worker file):
    getDocument/getTextContent never touch canvas, so pdf.js's font/render
    machinery is unused — only the fake-worker text-extraction path runs.
    THIRD-PARTY-NOTICES.md carries the vendoring exception for this file.

    The vendored module already assigns a complete, correctly-aliased
    globalThis.pdfjsLib itself (its own export list renames the internal
    `version` binding) — re-declaring `window.pdfjsLib = {..., version:
    version}` here referenced an identifier that doesn't exist as a bare
    name in this module's scope. That ReferenceError aborted the whole
    inline module script, so window._a2uiExtractPdfText was NEVER defined
    either (it's declared after the broken line, same script block) —
    file_upload's PDF branch has been silently broken since this shipped;
    found live 2026-07-14 building a second page that inlines this same
    block. Fixed by just using what the vendored file already set.

    SECOND bug, found live 2026-07-15 testing an actual PDF upload (not just
    checking the bridge function existed): getDocument() itself throws 'No
    "GlobalWorkerOptions.workerSrc" specified.' — this build always needs a
    real, separately-fetchable worker script, even for text-only extraction;
    there is no automatic main-thread fallback. Points at the same vendored
    file served as a static asset (public/vendors/pdfjs/pdf.min.mjs,
    written by generate_atom_pages.py's main()) rather than duplicating
    ~500KB inline a second time."""
    vendored = PDFJS_PATH.read_text()
    bridge = """
window.pdfjsLib.GlobalWorkerOptions.workerSrc = '/vendors/pdfjs/pdf.min.mjs';
// A real, large document can take a long time to extract page-by-page with
// no visible progress (found live 2026-07-15 testing an actual TOGAF PDF).
// Report progress via an optional callback, and stop once enough text has
// accumulated rather than extracting hundreds of pages unconditionally.
window._a2uiExtractPdfText = async function (file, onProgress) {
  var buf = await file.arrayBuffer();
  var doc = await window.pdfjsLib.getDocument({ data: buf, isEvalSupported: false }).promise;
  var parts = [];
  var totalChars = 0;
  var MAX_CHARS = 250000;
  for (var i = 1; i <= doc.numPages; i++) {
    var page = await doc.getPage(i);
    var content = await page.getTextContent();
    var pageText = content.items.map(function (it) { return it.str || ''; }).join(' ');
    parts.push(pageText);
    totalChars += pageText.length;
    if (typeof onProgress === 'function') onProgress(i, doc.numPages);
    if (totalChars >= MAX_CHARS) break;
  }
  return parts.join('\\n\\n').trim();
};
"""
    return escape_script_close(vendored + "\n" + bridge)


def escape_script_close(js):
    """`</script` inside a JS string literal is invisible to Node's parser but
    terminates the WHOLE <script> element for the browser's HTML parser —
    everything after it dumps into the DOM as text (the 2026-07-10 'Video
    placeholder' incident: atom.gs carries 4 unescaped closers that the GAS
    HtmlService pipeline never tripped over). `<\\/script` is byte-identical
    once the string is evaluated, so the wholesale replace is safe — the same
    transform every JS bundler applies."""
    return js.replace("</script", "<\\/script")


def build_bundle():
    atom_styles = (RENDERER_DIR / "AtomStyles.html").read_text().strip()

    core_parts = [PRELUDE]
    # Non-renderer .gs files that legitimately ship in the bundle: PackMap (the
    # atom->catalog gate) and the v1.0 decode shim (pure functions, no DOM).
    NON_RENDERER_GS = {"PackMap.gs", "atoms_v1_decode.gs", "atoms_wired_expand.gs", "atoms_wired_render.gs"}
    for f in renderer_files():
        src = f.read_text()
        if f.name not in NON_RENDERER_GS:
            assert "_RENDERERS[" in src, f"{f.name}: no renderers — wrong include?"
        core_parts.append(f"// ==== {f.name} ====\n{src}")
    core_parts.append(class_c_overrides())
    core_parts.append(data_sources_js())
    core_parts.append(DATA_FEEDS_JS)
    # QR-Code-generator (Project Nayuki, MIT — THIRD-PARTY-NOTICES.md) — unlike
    # PDF.js, this is a plain synchronous algorithm (no Worker/module/async-RPC
    # involved) and schema_qr isn't MCP-Apps-exclusive like file_upload's PDF
    # branch, so it belongs in the shared core block rather than an isolated
    # module script. DOM-free (no window/document references), safe for the
    # Node-testable core block.
    core_parts.append("// ==== vendor/qrcodegen/qrcodegen.js ====\n" + QRCODEGEN_PATH.read_text())
    core = escape_script_close("\n\n".join(core_parts))

    client = escape_script_close("\n\n".join(
        f"// ==== {name} ====\n{partial_body(name)}" for name in PARTIALS
    ))

    for label, block in (("core", core), ("client", client), ("handshake", HANDSHAKE)):
        assert "</script" not in block, \
            f"{label} block still contains a raw </script — would truncate in the browser"

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>A2UI Catalog renderer — MCP Apps View</title>
{atom_styles}
<style>
body {{ padding: 24px; }}
/* Applied by paint() ONLY when the payload contains a declared half-viewport
   overlay atom (data-a2ui-overlay, e.g. gdm_rocket_panel, iso_fireworks_panel)
   -- everything else gets the full viewport. Right-half overlays (default)
   squeeze content left; left-half overlays push it right. */
#a2ui-root.a2ui-with-overlay {{ max-width: 50%; box-sizing: border-box; }}
#a2ui-root.a2ui-with-overlay.a2ui-overlay-left {{ margin-left: 50%; }}
/* hub (atoms_brevet.gs) sets min-height:100vh on its wrapper + content divs --
   correct for the real GAS webapp (a genuine, non-resizing browser window)
   but wrong here: this bundle runs inside a SELF-SIZING iframe (reportSize()
   below drives the host to resize the iframe to match reported content
   height). 100vh is circular in that setup -- the host grows the iframe to
   match the reported height, vh grows to match the new (taller) iframe, the
   100vh min-height grows again on the next layout pass. Curtis observed this
   live in claude.ai's fullscreen mode, 2026-07-27, as a much-taller-than-
   content "infinite canvas" rather than a bounded one-screenful frame.
   Neutralized HERE ONLY (id pattern matches hub's own uid+'body'/uid+
   'content' divs); the shared atoms_brevet.gs source is untouched since the
   real GAS deployment is exactly the case where 100vh is correct. */
[id^="hub"][id$="body"], [id^="hub"][id$="content"] {{ min-height: 0 !important; }}
/* Same fix, same reasoning, for playbook (atoms_airspace.gs) -- its slide
   divs (uid 'pbk' + 6 random chars + 's_' + the caller's own slide id) carry
   the identical min-height:100vh. Slide ids are caller-chosen text, not a
   fixed suffix like hub's, so this matches on the 'pbk' prefix alone; it
   also catches playbook's nav-button/nav-bar ids, which is harmless since
   none of them rely on min-height. */
[id^="pbk"] {{ min-height: 0 !important; }}
/* Follow-up (2026-07-27, same day): the min-height fix above stops the
   RUNAWAY-growth bug, but doesn't address a separate, real host behavior --
   once fullscreen is genuinely granted, the host sizes the iframe to the
   actual screen height regardless of how short our reported content is (we
   don't control that from inside the iframe). A short slide (e.g. a single
   sequence_diagram) confirmed live pinned to the TOP with a large empty
   dark void below it, no indication it was intentional. Vertically center
   each slide's content instead, so any leftover space distributes evenly.
   Scoped to slide CONTENT divs only (id contains "s_", which only ever
   occurs at the uid/slide-id boundary -- the random uid prefix is base36
   [0-9a-z], never "_" -- so this can't accidentally match a nav button/bar
   id). align-items is left at flex's default 'stretch' deliberately: only
   the vertical axis centers, children (e.g. the full-width radar) keep
   their own width instead of shrinking to content size. Content taller
   than the frame is unaffected -- centering only has slack to distribute
   when there IS slack. */
[id^="pbk"][id*="s_"] {{ display: flex !important; flex-direction: column !important; justify-content: center !important; }}
</style>
</head>
<body class="asw-page">
<div id="a2ui-root"></div>
<script>
// ---- a2ui-core (DOM-free at top level; tests execute this block in Node) ----
// Concatenated verbatim from apps-script-surface/gas-wired-renderer/ by
// scripts/gen_mcp_apps_bundle.py — do not hand-edit.
{core}
</script>
<script>
// ---- a2ui-client partials (touch window/document at load) ----
{client}
</script>
<script type="module">
{pdfjs_module_block()}
</script>
<script>
{HANDSHAKE}
</script>
</body>
</html>
"""


def write_qrcodegen_partial():
    """The plain GAS-hosted surface (AtomPage.html, via include()) can't read
    an arbitrary vendor/ path at runtime the way this Python script can —
    GAS only serves project files literally pushed by clasp. Generate a
    checked-in partial from the SAME vendored source so there's one source
    of truth (vendor/qrcodegen/qrcodegen.js) with this file as a compiled
    artifact, never hand-edited — same "generators compile artifacts"
    discipline as renderer-bundle.html itself."""
    out = RENDERER_DIR / "QrCodeGen.html"
    js = QRCODEGEN_PATH.read_text()
    out.write_text(
        "<!-- GENERATED by scripts/gen_mcp_apps_bundle.py from "
        "vendor/qrcodegen/qrcodegen.js — do not hand-edit. -->\n"
        f"<script>\n{escape_script_close(js)}\n</script>\n"
    )
    print("wrote %s (%d bytes)" % (out, out.stat().st_size))


def main():
    bundle = build_bundle()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(bundle)
    print("wrote %s (%d bytes, %d files concatenated)"
          % (OUT, len(bundle), len(renderer_files())))
    write_qrcodegen_partial()


if __name__ == "__main__":
    main()
