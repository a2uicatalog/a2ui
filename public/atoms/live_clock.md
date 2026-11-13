# Live Clock

Live ticking clock on a dark card, updates every second

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
| label | string (optional, alias: title) |
| format | string (optional, 12h|24h, default 24h) |
| timezone | string (optional, IANA tz label for display only) |

## Example payload

```json
{
  "type": "live_clock"
}
```

Live page: https://a2uicatalog.ai/atoms/live_clock/
Full field contract: https://a2uicatalog.ai/spec.json
