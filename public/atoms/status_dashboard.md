# Status Dashboard

Compact grid showing live operational status of multiple services with color indicators.

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
| title | string (optional). Heading shown in the overall-status banner. |
| items | array of {name, status, description?}. status is one of operational | degraded | outage | maintenance; the banner rolls up to the worst status. |

## Example payload

```json
{
  "type": "status_dashboard",
  "items": 1
}
```

Live page: https://a2uicatalog.ai/atoms/status_dashboard/
Full field contract: https://a2uicatalog.ai/spec.json
