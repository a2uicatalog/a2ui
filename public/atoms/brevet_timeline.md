# Brevet Timeline

Vertical dated timeline of events for study/revision pages.

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
| title | string (optional) |
| events | array (required) of {date, title, desc} |
| accent | string (optional, hex, default "#3b82f6") |

## Example payload

```json
{
  "type": "brevet_timeline",
  "events": [
    {
      "date": "2025",
      "title": "Launch",
      "body": "First release."
    },
    {
      "date": "2026",
      "title": "Today",
      "body": "Still growing."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/brevet_timeline/
Full field contract: https://a2uicatalog.ai/spec.json
