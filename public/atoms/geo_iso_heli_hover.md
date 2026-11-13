# Geo Iso Heli Hover

Full-viewport isometric 3D canvas animation of an H160 helicopter hovering over a helipad. Rotor blur, downwash ripple, and HUD overlay with livery accent colour.

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
| title | string (optional). HUD title. Default "LFBO HELIPAD 2 — AIRBUS H160 HOVER PROFILE". |
| livery | string (optional). ICAO airline code for accent colour — AIB, EZY, AFR, etc. Default AIB. |

## Example payload

```json
{
  "type": "geo_iso_heli_hover"
}
```

Live page: https://a2uicatalog.ai/atoms/geo_iso_heli_hover/
Full field contract: https://a2uicatalog.ai/spec.json
