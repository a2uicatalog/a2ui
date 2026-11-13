# Progress Reveal

Animated progress bar that counts from 0 to a value when scrolled into view

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
| value | number (0–100, alias: percent) |
| label | string (optional, alias: title) |
| color | string (optional, hex) |
| suffix | string (optional, default %) |
| height | number (optional, bar height px) |

## Example payload

```json
{
  "type": "progress_reveal",
  "value": 75
}
```

Live page: https://a2uicatalog.ai/atoms/progress_reveal/
Full field contract: https://a2uicatalog.ai/spec.json
