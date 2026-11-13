# Calendar Upcoming

List of upcoming events from the user's primary calendar. Works on Google Apps Script only.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| max_results | integer (optional). Maximum number of upcoming events to show. Default is 5. |

## Example payload

```json
{
  "type": "calendar_upcoming"
}
```

Live page: https://a2uicatalog.ai/atoms/calendar_upcoming/
Full field contract: https://a2uicatalog.ai/spec.json
