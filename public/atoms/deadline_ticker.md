# Deadline Ticker

Countdown timer showing days/hours/minutes/seconds to a target date — alias for countdown_timer

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
| target_date | string (ISO date, alias: target) |
| label | string (optional, alias: title) |

## Example payload

```json
{
  "type": "deadline_ticker",
  "target_date": "Target date"
}
```

Live page: https://a2uicatalog.ai/atoms/deadline_ticker/
Full field contract: https://a2uicatalog.ai/spec.json
