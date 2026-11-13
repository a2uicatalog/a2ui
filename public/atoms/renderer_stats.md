# Renderer Stats

Simple stat grid showing custom key/value pairs — used to show renderer capabilities

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
| stats | array of {value, label} |
| sub | string (optional, footer note) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "renderer_stats",
  "stats": [
    {
      "label": "Views",
      "value": "1.2M"
    },
    {
      "label": "Clicks",
      "value": "42K"
    },
    {
      "label": "CTR",
      "value": "3.5%"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/renderer_stats/
Full field contract: https://a2uicatalog.ai/spec.json
