# Live Metric

Animated counter that counts up from start to a target value — alias for animated_counter

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
| value | number (alias: end) |
| start | number (optional) |
| duration | number (optional, seconds) |
| prefix | string (optional) |
| suffix | string (optional) |
| label | string (optional) |
| decimals | integer (optional) |

## Example payload

```json
{
  "type": "live_metric",
  "value": 1
}
```

Live page: https://a2uicatalog.ai/atoms/live_metric/
Full field contract: https://a2uicatalog.ai/spec.json
