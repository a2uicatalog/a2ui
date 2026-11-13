# Multi Surface

One data pool rendered simultaneously across three surface engines: spatial map (desktop), phone frame card list (mobile), circular focus face (IoT/watch)

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
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| nodes | array of {id, type, label, temp (optional), value (optional), intensity (0–100, optional), coords: {x, y}} |

## Example payload

```json
{
  "type": "multi_surface"
}
```

Live page: https://a2uicatalog.ai/atoms/multi_surface/
Full field contract: https://a2uicatalog.ai/spec.json
