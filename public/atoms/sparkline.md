# Sparkline

Renders a small, simple line chart without axes or coordinates, showing

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| data | list of numbers (e.g., [10, 12, 8, 15, 13]) |
| color | string (hex or named color, e.g., '#4CAF50' or 'green') |
| line_width | number (e.g., 2) |
| height | string (CSS height value, e.g., '20px') |
| width | string (CSS width value, e.g., '80px') |

## Example payload

```json
{
  "type": "sparkline",
  "data": 1,
  "color": "#6366f1",
  "line_width": 1,
  "height": "80px",
  "width": "100%"
}
```

Live page: https://a2uicatalog.ai/atoms/sparkline/
Full field contract: https://a2uicatalog.ai/spec.json
