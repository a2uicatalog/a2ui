# Calendar Today

Today's events from the user's default Google Calendar, displayed as a compact timeline with time and location. Automatically shows today's date in the header.

## Surfaces

google-apps-script-web, mcp-apps, android

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
| title | string (optional). Card heading. Default is "Today's Schedule". |
| max_results | integer (optional). Maximum events to show. Default 8. |

## Example payload

```json
{
  "type": "calendar_today"
}
```

Live page: https://a2uicatalog.ai/atoms/calendar_today/
Full field contract: https://a2uicatalog.ai/spec.json
