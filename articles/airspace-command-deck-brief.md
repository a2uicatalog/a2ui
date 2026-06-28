# Airspace Command Deck — Implementation Brief

*A2UI atom-driven playbook running on Google Apps Script. Share with Gemini for review and improvement.*
*Last updated: deployment @98 — playbook atom, adsb.lol feed, aircraft silhouettes, isometric panel, client-side weather interpolation.*

---

## What this is

A full-viewport, animated Toulouse TMA (Terminal Manoeuvring Area) airspace radar display built entirely on the A2UI atom paradigm, running on the Google Apps Script web app surface.

The entire 5-slide deck is encoded in a single shareable `?p=` URL — no server-side state, no hardcoded playbook, no page reloads between slides. Flight positions come from **adsb.lol** live ADS-B API. METAR weather from **aviationweather.gov**. A built-in LIVE/SIM pill shows data status.

**Shareable deck URL (5 slides, client-side nav):**
```
https://script.google.com/macros/s/AKfycbyVKvt_mFlaPgbHLOoi65bfpi8qkDgnt-eC-7XNAqiVVIFl4EViQ-4nBHbY6MDMKLMwDg/exec?p=W3sidHlwZSI6InBsYXlib29rIiwic2hhcmVkX2Jsb2NrcyI6W3sidHlwZSI6ImFkc2JfZmVlZCIsIm5hbWUiOiJhZHNiIiwicmVmcmVzaCI6MTV9LHsidHlwZSI6Im1ldGFyX2ZlZWQiLCJuYW1lIjoibWV0YXJfbGZibyIsInN0YXRpb24iOiJMRkJPIiwicmVmcmVzaCI6NjB9XSwic2xpZGVzIjpbeyJpZCI6ImNhbGlicmF0aW9uIiwibGFiZWwiOiLwn5OhIENhbGlicmF0aW9uIiwiYmxvY2tzIjpbeyJ0eXBlIjoiYWlyc3BhY2VfY29tbWFuZF9kZWNrIiwiaGVpZ2h0IjoiZnVsbHNjcmVlbiIsInNob3dfc2xhdGUiOnRydWUsInNsYXRlX3RpdGxlIjoi8J+ToSBUTFMgU2VjdG9yIDMyTC9SIFN3ZWVwIENhbGlicmF0aW9uIiwic2xhdGVfZGVzY3JpcHRpb24iOiJCb290aW5nIHRyYW5zcG9uZGVyIHRyYWNraW5nIG1hdHJpeCBhbmQgYWxpZ25pbmcgcHJpbWFyeSBTLUJhbmQgcmVjZWl2ZXJzLi4uIn1dfSx7ImlkIjoibGl2ZSIsImxhYmVsIjoi4pyI77iPIExpdmUgVHJhZmZpYyIsImJsb2NrcyI6W3sidHlwZSI6ImFpcnNwYWNlX2NvbW1hbmRfZGVjayIsImhlaWdodCI6ImZ1bGxzY3JlZW4iLCJkYXRhX3NvdXJjZSI6ImFkc2IiLCJ3ZWF0aGVyX3NvdXJjZSI6Im1ldGFyX2xmYm8iLCJ6b29tIjozNSwiY2h5cm9uX3RpdGxlIjoiTEZCTyBUTUEg4oCUIExJVkUgVFJBRkZJQyIsImNoeXJvbl9zdWJ0aXRsZSI6IlJ1bndheSAzMkwvUiBBY3RpdmUg4oCiIHt7d2VhdGhlci53aW5kfX0g4oCiIFFOSCB7e3dlYXRoZXIucHJlc3N1cmV9fSIsInRpY2tlcl90ZXh0Ijoi4pyI77iPIFRPVUxPVVNFIEJMQUdOQUMgQVBQUk9BQ0ggQ09OVFJPTCDigKIgUlVOV0FZIDMyTC9SIEFDVElWRSDigKIgU1VSRkFDRSBXSU5EOiB7e3dlYXRoZXIud2luZH19IOKAoiBURU1QOiB7e3dlYXRoZXIudGVtcH19IOKAoiBRTkg6IHt7d2VhdGhlci5wcmVzc3VyZX19IOKAoiBSQVcgTUVUQVI6IHt7d2VhdGhlci5yYXd9fSDigKIiLCJ0aWNrZXJfc3BlZWQiOjQ1fV19LHsiaWQiOiJzdXBlcnZpc29yIiwibGFiZWwiOiLwn5OhIFNlY3RvciBDb250cm9sIiwiYmxvY2tzIjpbeyJ0eXBlIjoiYWlyc3BhY2VfY29tbWFuZF9kZWNrIiwiaGVpZ2h0IjoiZnVsbHNjcmVlbiIsImRhdGFfc291cmNlIjoiYWRzYiIsIndlYXRoZXJfc291cmNlIjoibWV0YXJfbGZibyIsInpvb20iOjM1LCJwYW5lbF90eXBlIjoic3VwZXJ2aXNvciIsInBhbmVsX3RpdGxlIjoi8J+ToSBUYWN0aWNhbCBTdXBlcnZpc29yIEhVRCIsImNoeXJvbl90aXRsZSI6IkxGQk8gVE1BIEFQUFJPQUNIIENPTlRST0wiLCJjaHlyb25fc3VidGl0bGUiOiJBY3RpdmUgQXBwcm9hY2ggVmVjdG9ycyBSdW53YXkgMzJML1IiLCJ0aWNrZXJfdGV4dCI6IvCfk40gTEZCTyBUZXJtaW5hbCBJbmZvcm1hdGlvbiDigKIgUlVOV0FZIDMyTC9SIEFDVElWRSDigKIgU1VSRkFDRSBXSU5EOiB7e3dlYXRoZXIud2luZH19IOKAoiBURU1QOiB7e3dlYXRoZXIudGVtcH19IOKAoiBRTkg6IHt7d2VhdGhlci5wcmVzc3VyZX19IOKAoiIsInRpY2tlcl9zcGVlZCI6NTB9XX0seyJpZCI6InRhcmdldCIsImxhYmVsIjoi8J+OryBUYXJnZXQgTG9jayIsImJsb2NrcyI6W3sidHlwZSI6ImFpcnNwYWNlX2NvbW1hbmRfZGVjayIsImhlaWdodCI6ImZ1bGxzY3JlZW4iLCJkYXRhX3NvdXJjZSI6ImFkc2IiLCJ3ZWF0aGVyX3NvdXJjZSI6Im1ldGFyX2xmYm8iLCJ6b29tIjoyMiwicGFuZWxfdHlwZSI6InRhcmdldCIsInBhbmVsX3RpdGxlIjoi8J+OryBBY3RpdmUgVGFyZ2V0IFByb2ZpbGVyIiwibG9ja2VkQ2FsbHNpZ24iOiJBRlI2MTI5IiwiY2h5cm9uX3RpdGxlIjoiVEFSR0VUIEFDUVVJUkVEOiBBRlI2MTI5IiwiY2h5cm9uX3N1YnRpdGxlIjoiVHJhY2tpbmcgRGVzY2VudCBQcm9maWxlIOKAlCBJbnN0cnVtZW50IEdsaWRlIFNsb3BlIFJ1bndheSAzMkwiLCJ0aWNrZXJfdGV4dCI6IvCfk40gTEZCTyBUZXJtaW5hbCBJbmZvcm1hdGlvbiDigKIgUlVOV0FZIDMyTC9SIEFDVElWRSDigKIgU1VSRkFDRSBXSU5EOiB7e3dlYXRoZXIud2luZH19IOKAoiBURU1QOiB7e3dlYXRoZXIudGVtcH19IOKAoiBRTkg6IHt7d2VhdGhlci5wcmVzc3VyZX19IOKAoiIsInRpY2tlcl9zcGVlZCI6NTB9XX0seyJpZCI6InBvbGwiLCJsYWJlbCI6IvCfl7PvuI8gUG9sbCIsImJsb2NrcyI6W3sidHlwZSI6ImFpcnNwYWNlX2NvbW1hbmRfZGVjayIsImhlaWdodCI6ImZ1bGxzY3JlZW4iLCJkYXRhX3NvdXJjZSI6ImFkc2IiLCJ3ZWF0aGVyX3NvdXJjZSI6Im1ldGFyX2xmYm8iLCJ6b29tIjozNSwicGFuZWxfdHlwZSI6InN1cGVydmlzb3IiLCJwYW5lbF90aXRsZSI6IvCfk6EgU3VwZXJ2aXNvciBMaXZlIENvbnNvbGUiLCJjaHlyb25fdGl0bGUiOiJUTUEgQ09ORkxJQ1QgUkVTT0xVVElPTiIsImNoeXJvbl9zdWJ0aXRsZSI6IlNlbGVjdCBzZXBhcmF0aW9uIG1hbmV1dmVycyBhbmQgcnVud2F5IHZlY3RvciBhbGxvY2F0aW9uIiwidGlja2VyX3RleHQiOiLwn5ONIExGQk8gVGVybWluYWwgSW5mb3JtYXRpb24g4oCiIFJVTldBWSAzMkwvUiBBQ1RJVkUg4oCiIFNVUkZBQ0UgV0lORDoge3t3ZWF0aGVyLndpbmR9fSDigKIiLCJ0aWNrZXJfc3BlZWQiOjUwLCJwb2xsX3F1ZXN0aW9uIjoiVE1BIERpcmVjdGlvbjogUmVzb2x2ZSBzZXBhcmF0aW9uIGNvbmZsaWN0PyDwn5ez77iPIiwicG9sbF9vcHRpb25zIjpbIkVzdGFibGlzaCBwYXJhbGxlbCBzaW11bHRhbmVvdXMgdmlzdWFsIGFycml2YWxzIFJ1bndheSAzMkwvUiIsIlZlY3RvciBSWVIxMDlCIHRvIGVudGVyIGhvbGRpbmcgcGF0dGVybiBhdCBUT1UgVk9SIiwiSW5zdHJ1Y3QgRVpZNDIxOCB0byByZWR1Y2Ugc3BlZWQgdG8gbWluaW11bSAxODBrdCJdLCJwb2xsX3ZhbHVlcyI6WzEyLDgsNF19XX1dfV0
```

---

## Atom architecture

All slides are driven by three atom types. The payload is a standard A2UI `?p=` base64 array:

```json
[
  {
    "type": "playbook",
    "shared_blocks": [
      { "type": "adsb_feed",  "name": "adsb",       "refresh": 15 },
      { "type": "metar_feed", "name": "metar_lfbo",  "station": "LFBO", "refresh": 60 }
    ],
    "slides": [
      { "id": "calibration", "label": "📡 Calibration",
        "blocks": [{ "type": "airspace_command_deck", "height": "fullscreen", "show_slate": true, "..." }]},
      { "id": "live", "label": "✈️ Live Traffic",
        "blocks": [{ "type": "airspace_command_deck", "height": "fullscreen",
          "data_source": "adsb", "weather_source": "metar_lfbo", "zoom": 35, "..." }]},
      { "id": "supervisor", "label": "📡 Sector Control", "blocks": ["..."] },
      { "id": "target",     "label": "🎯 Target Lock",    "blocks": ["..."] },
      { "id": "poll",       "label": "🗳️ Poll",           "blocks": ["..."] }
    ]
  }
]
```

### `playbook` atom

Renders all slides server-side into hidden `<div>` containers. JS switches visibility on nav click — no page reloads. `location.hash` updates to reflect the active slide.

- `shared_blocks` — atoms rendered once outside slide containers (data feeds, shared styles)
- `slides[]` — each: `{ id, label, blocks[] }`
- `transition` — `'fade'` | `'instant'`

Callbacks are **chained**: each `airspace_command_deck` in each slide registers its callback as:
```javascript
var prev = window.A2UI_CALLBACKS['adsb'];
window.A2UI_CALLBACKS['adsb'] = function(d) { myUpdate(d); if (prev) prev(d); };
```
So all slides receive every data dispatch even though only one feed runs in `shared_blocks`.

### `adsb_feed` atom

Live ADS-B traffic via **adsb.lol** (OpenSky was DNS-blocked from GAS servers).

```json
{ "type": "adsb_feed", "name": "adsb", "refresh": 15 }
```

- URL: `https://api.adsb.lol/v2/lat/43.629/lon/1.363/dist/40` (40nm radius from LFBO)
- Server-side: `UrlFetchApp.fetch()` + `CacheService` (15s TTL) on initial page render
- Client-side: `setInterval` → `google.script.run.fetchDataSource(url, 'json', '')`
- Normalises to: `{ callsign, lat, lon, alt_ft, spd_kt, hdg, on_ground, squawk }`
- Publishes to `window.A2UI_DATA['adsb']` and calls `window.A2UI_CALLBACKS['adsb']`
- Dispatch deferred 80ms so all visual atom scripts register callbacks first

**Connectivity probe** (`?debug=all`): adsb.lol confirmed reachable (200, 38 aircraft). OpenSky, fr24, airplanes.live all blocked from GAS.

### `metar_feed` atom

Live METAR for any ICAO station.

```json
{ "type": "metar_feed", "name": "metar_lfbo", "station": "LFBO", "refresh": 60 }
```

- URL: `https://aviationweather.gov/api/data/metar?ids=LFBO&format=raw&hours=1`
- Parses raw METAR to: `{ wind, temp, qnh, raw }` (e.g. `"120°/12kt"`, `"35°C"`, `"1015 hPa"`)
- Server-side initial fetch cached 30s
- Client refresh every 60s

### `airspace_command_deck` atom

Full-viewport canvas radar with HTML/CSS overlays. All fields are declarative:

| Field | Default | Description |
|---|---|---|
| `height` | `520` | `'fullscreen'` for 100vh |
| `zoom` | `35` | nm radius visible on radar |
| `chyron_title` | `'LFBO TMA'` | top-left headline |
| `chyron_subtitle` | — | top-left subtitle, supports `{{weather.*}}` |
| `ticker_text` | — | scrolling bottom bar, supports `{{weather.*}}` |
| `ticker_speed` | `45` | px/s scroll speed |
| `panel_type` | — | `'supervisor'` or `'target'` |
| `panel_title` | — | HUD panel heading |
| `lockedCallsign` | — | highlight + reticle on this callsign |
| `data_source` | — | name of `adsb_feed` to subscribe to |
| `weather_source` | — | name of `metar_feed` to subscribe to |
| `show_slate` | `false` | calibration boot screen instead of radar |
| `slate_title` | — | slate heading |
| `slate_description` | — | slate body text |
| `poll_question` | — | poll overlay question |
| `poll_options[]` | — | poll answer strings |
| `poll_values[]` | — | current vote counts |

---

## Weather tag interpolation

`{{weather.wind}}`, `{{weather.temp}}`, `{{weather.pressure}}`, `{{weather.raw}}` can appear in any string field. They resolve **client-side** when the `metar_feed` callback fires (~80ms after load):

```javascript
// Stored as JS template variables at render time
var _CSUB = "Runway 32L/R Active • {{weather.wind}} • QNH {{weather.pressure}}";
var _TKRT = "✈️ TOULOUSE BLAGNAC • SURFACE WIND: {{weather.wind}} • ...";

function updateWeather(wx) {
  // Update weather panel spans
  document.getElementById(uid+'wind').textContent = wx.wind;
  // ...
  // Interpolate template tags into chyron subtitle + ticker
  function _wi(s) {
    return s.replace(/\{\{weather\.wind\}\}/g, wx.wind || '—')
            .replace(/\{\{weather\.temp\}\}/g, wx.temp || '—')
            .replace(/\{\{weather\.pressure\}\}/g, wx.qnh || '—')
            .replace(/\{\{weather\.raw\}\}/g, wx.raw || '');
  }
  document.getElementById(uid+'csub').textContent = _wi(_CSUB);
  var t = _wi(_TKRT);
  document.getElementById(uid+'tkr').textContent = t + '     ' + t;
}
```

This means the `?p=` URL can include `{{weather.*}}` tags without any server-side fetch — they resolve after the metar_feed dispatch.

---

## Visual rendering

### Two-layer approach

```
┌─────────────────────────────────────────────────────┐
│  HTML/CSS overlays (position:absolute)              │
│  • Chyron top-left (title + subtitle)               │
│  • Weather panel top-right (WIND/TEMP/QNH)          │
│  • LIVE/SIM status pill (top-right)                 │
│  • Supervisor panel left (flight list grid)         │
│  • Target panel left (iso aircraft + detail card)   │
│  • Poll overlay right (bar chart)                   │
│  • Ticker bar bottom (CSS animation)                │
│  • Slide nav pill fixed bottom-centre               │
├─────────────────────────────────────────────────────┤
│  <canvas> radar (position:absolute, rAF loop)       │
│  • Dark radial gradient background                  │
│  • Rotating radar sweep sector                      │
│  • Concentric range rings (10/20/30nm labels)       │
│  • Crosshair grid lines                             │
│  • VOR beacons: TOU, BGC, CNA (amber squares)       │
│  • Runway 32L/R symbol + dashed approach path       │
│  • Aircraft silhouettes (top-down plan view)        │
│  • Position trails (fading cyan dots)               │
│  • Targeting reticle (rotating dashed ring)         │
└─────────────────────────────────────────────────────┘
```

### Aircraft silhouettes

Each flight is drawn as a proper top-down plan view silhouette oriented by heading, not a dot:

```javascript
function drawPlane(ctx, x, y, hdg, s, col, glow) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(hdg * Math.PI / 180);
  if (glow) { ctx.shadowBlur = 12; ctx.shadowColor = col; }
  ctx.fillStyle = col;
  // fuselage
  ctx.beginPath(); ctx.moveTo(0, -s*3.2); ctx.lineTo(s*0.45, -s*0.2);
  ctx.lineTo(s*0.3, s*2.8); ctx.lineTo(-s*0.3, s*2.8);
  ctx.lineTo(-s*0.45, -s*0.2); ctx.closePath(); ctx.fill();
  // wings (left + right), tail stabilisers (left + right)
  // ...
  ctx.restore();
}
```

Scale: `s=3.2` normal, `s=5.5` for locked callsign (with glow). Heading from `f.hdg` (adsb.lol `track` field for live flights; `(brg+180)%360` for simulated).

### Labels

Three lines per flight:
1. Callsign (bright, bold if locked)
2. `FL{alt}  {spd}kt` (dim white)
3. Airline name (very dim, from ICAO prefix lookup)

### Airline lookup

30+ airlines mapped from 3-letter ICAO prefix to `{ name, color }`. Unknown prefixes show the raw 3-letter code. Color used for the isometric aircraft panel.

```javascript
var AL = {
  AFR: { n: 'Air France',   c: '#002395' },
  EZY: { n: 'easyJet',      c: '#FF6600' },
  RYR: { n: 'Ryanair',      c: '#073590' },
  // ... 27 more
};
function getAL(cs) {
  var p = (cs||'').substr(0,3).toUpperCase();
  return AL[p] || { n: p, c: '#00f2ff' };  // fallback: show ICAO code
}
```

### Isometric 3D aircraft (target panel)

The target panel shows a slowly rotating isometric 3D aircraft drawn on a `<canvas>` element inside the panel. Uses proper 3D → ISO projection with Y-axis rotation for animation:

```javascript
function drawIso(cvs, color, yaw) {
  function p3(x, y, z) {  // rotate around Y then project
    var rx = x*Math.cos(yaw) + z*Math.sin(yaw);
    var rz = -x*Math.sin(yaw) + z*Math.cos(yaw);
    return { sx: ox + (rx-rz)*S*0.866, sy: oy - (rx+rz)*S*0.5 + y*S };
  }
  function face(pts3d, fill) { /* project, fill polygon, stroke */ }
  // fuselage top/side/nose faces
  // wing top/bottom faces
  // horizontal stabilisers
  // vertical fin
  // engines (dark cylinders under wings)
}
```

`isoYaw += 0.008` per rAF frame = full rotation in ~785 frames (~13s at 60fps). Color from airline lookup, so Air France = deep blue, easyJet = orange, etc.

### Supervisor panel

Grid layout: FLIGHT / AIRLINE / FL / STATUS columns, updated from `updateFlightList()` on every rAF frame.

### Data status pill

Built into `airspace_command_deck`. Starts red SIM, flips green LIVE when `adsb_feed` dispatches real data:

```javascript
function setDataStatus(live, count) {
  var c = live ? '#34c759' : '#ff3b30';
  // update pill background, border, dot color, label text
  // label: 'LIVE (N)' or 'SIM'
}
```

---

## `?p=` URL mechanics

The `?p=` parameter carries a **URL-safe base64** encoded JSON array (RFC 4648, `-` and `_` instead of `+` and `/`, no `=` padding). Standard base64 `+` characters get decoded as spaces by URL parsers, corrupting the payload.

Generating a link (Node.js):
```javascript
const b64 = Buffer.from(JSON.stringify(payload)).toString('base64')
  .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
const url = baseUrl + '?p=' + b64;
```

Decoding in GAS:
```javascript
var bytes = Utilities.base64DecodeWebSafe(encoded, Utilities.Charset.UTF_8);
var json  = Utilities.newBlob(bytes).getDataAsString();
return _renderFromPayload(JSON.parse(json));
```

Auto-detection of fullscreen template: `_renderFromPayload` checks if any block is `airspace_command_deck` with `height:'fullscreen'`, OR if any block is a `playbook` containing such a slide. If so, uses `AirspaceFullscreen.html` instead of the standard `AtomPage.html`.

---

## GAS surface specifics

### `doGet` routing

```
?debug=all          → API connectivity probe (adsb.lol, aviationweather.gov, etc.)
?p=BASE64           → decode playbook, auto-detect fullscreen, render
?slide=ID           → legacy hardcoded Toulouse playbook (6 slides, METAR server-interpolated)
?makeDeck           → generate ?p= URL from hardcoded playbook
(no params)         → Index.html schema editor UI
```

### `fetchDataSource` — surface transport

Called by client via `google.script.run`:
```javascript
function fetchDataSource(url, format, path) {
  var resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  var data = format === 'json' ? JSON.parse(resp.getContentText()) : resp.getContentText().trim();
  if (path) path.split('.').forEach(function(k) { if (data && k) data = data[k]; });
  return data;
}
```

This is the only surface-specific code. Other surfaces substitute their own transport (`fetch()`, `requests`, etc.) without changing atom schemas.

### `_surfaceFetch` — cached server fetch

```javascript
function _surfaceFetch(url, cacheKey, ttlSeconds) {
  var cache = CacheService.getScriptCache();
  var hit = cache.get(cacheKey);
  if (hit) return hit;
  var resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  if (resp.getResponseCode() === 200) {
    var body = resp.getContentText();
    cache.put(cacheKey, body, ttlSeconds);
    return body;
  }
  return null;
}
```

### `AirspaceFullscreen.html`

Minimal template — no wrapper div, no padding, body fills viewport:
```html
<!DOCTYPE html><html lang="en"><head>
  <meta charset="UTF-8">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { width: 100%; height: 100%; overflow: hidden; background: #050810; }
  </style>
</head><body>
  <?!= content ?>
  <script>window.__A2UI_SCHEMA__ = {};</script>
</body></html>
```

---

## Constraints

| Constraint | Detail |
|---|---|
| No external JS | CDN scripts blocked by GAS CSP — everything inline |
| No client CORS | External APIs must go via `UrlFetchApp` server-side |
| `google.script.run` async | Client can call server functions for post-load refresh |
| GAS template validation | `tmpl.evaluate()` validates HTML — raw `<body>` without DOCTYPE throws |
| URL-safe base64 only | Standard base64 `+` → space in URL params — use `base64DecodeWebSafe` |
| adsb.lol only | OpenSky, fr24, airplanes.live all DNS-blocked from GAS servers |
| 400 req/day unauth | adsb.lol is generous but cache TTL should be ≥15s per concurrent user |

---

## Potential improvements

1. **Real STAR waypoints** — LORNI, MINDI, OKRIX, EVOLI, VALKU are published LFBO approach waypoints; draw as diamond symbols on radar
2. **3° glideslope altitude profile** — current: linear. Model: `alt = Math.max(0, dist_nm * 318)` (300ft/nm)
3. **Radar return fade** — bright primary hit fades along sweep arc; secondary canvas layer keyed to sweep angle
4. **Squawk 7700/7600 alerts** — flash red border on label, inject into ticker, sound (Web Audio API beep)
5. **Separation conflict detection** — O(N²) distance check; highlight pairs within 3nm lateral + 1000ft vertical in amber
6. **Live poll values** — current values baked into schema; wire to Firestore or Script Properties for live update
7. **Keyboard nav** — `←` `→` arrow keys between playbook slides
8. **Airline logo / livery** — small SVG livery stripe on the isometric aircraft top surface
9. **Wind barb visualisation** — draw standard meteorological wind barb on METAR panel
10. **`feed_status` in schema.yaml** — atom exists in `atoms_data.gs` but not catalogued yet
