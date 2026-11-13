# Uptime Timeline

Visual timeline of service uptime over a rolling window with per-day status blocks.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| uptime | number. Uptime percentage (0–100). |

## Example payload

```json
{
  "type": "uptime_timeline",
  "uptime": 1
}
```

Live page: https://a2uicatalog.ai/atoms/uptime_timeline/
Full field contract: https://a2uicatalog.ai/spec.json
