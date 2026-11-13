# Progress Bar

Progress bar with an animated width transition, an optional percentage and an optional caption

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, claude-code, android

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
| value | integer (0-100) |
| label | string |
| accent | string (optional) |
| show_percent | bool (optional) |
| caption | string (optional) |

## Example payload

```json
{
  "type": "progress_bar",
  "value": 75,
  "label": "Progress Bar"
}
```

Live page: https://a2uicatalog.ai/atoms/progress_bar/
Full field contract: https://a2uicatalog.ai/spec.json
