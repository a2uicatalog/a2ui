# Time Estimate

Displays the estimated duration required to fully read or complete an article.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| minutes | integer. The estimated reading time in minutes. |

## Example payload

```json
{
  "type": "time_estimate",
  "minutes": 1
}
```

Live page: https://a2uicatalog.ai/atoms/time_estimate/
Full field contract: https://a2uicatalog.ai/spec.json
