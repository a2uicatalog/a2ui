# Surface Map

Visual diagram showing the A2UI surfaces — schema feeds into each render target

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
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| surfaces | array of {name, icon, desc, color} (optional, defaults to GAS/Meet/Sites/Chat) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "surface_map"
}
```

Live page: https://a2uicatalog.ai/atoms/surface_map/
Full field contract: https://a2uicatalog.ai/spec.json
