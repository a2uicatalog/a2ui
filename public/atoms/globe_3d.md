# Globe 3D

Spinning interactive 3-D wireframe or earth globe rendered on HTML5 canvas — draggable with inertia

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| size | number (optional, diameter px, default 300) |
| color | string (optional, hex accent, default #4f46e5) |
| speed | number (optional, auto-spin speed, default 0.006) |
| lines | number (optional, latitude line count, default 10) |
| theme | string (optional, wire|earth, default wire) |
| dots | array of {lat, lon, label (optional), color (optional)} (optional, pins on globe) |
| arcs | array of {from: [lat,lon], to: [lat,lon], color (optional)} (optional, great-circle arcs) |

## Example payload

```json
{
  "type": "globe_3d"
}
```

Live page: https://a2uicatalog.ai/atoms/globe_3d/
Full field contract: https://a2uicatalog.ai/spec.json
