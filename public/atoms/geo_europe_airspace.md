# Geo Europe Airspace

Interactive SVG European airspace map — country outlines, airport pins, simulated flight tracks, click-to-open TMA playbook

## Surfaces

google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| focus | string (optional, country name to highlight, alias: country) |
| sim_flights | array of {callsign, from: [lat,lon], to: [lat,lon]} (optional simulated flight tracks) |
| airports | boolean (optional, show airport pins, default true) |

## Example payload

```json
{
  "type": "geo_europe_airspace"
}
```

Live page: https://a2uicatalog.ai/atoms/geo_europe_airspace/
Full field contract: https://a2uicatalog.ai/spec.json
