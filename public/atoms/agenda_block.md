# Agenda Block

Time-slotted schedule view for a day or event. Each slot has a time, title, optional speaker, location, type badge, and description.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| date | string (optional) |
| accent | string (optional, hex, default "#4f46e5") |
| slots | array (required). Array of {time, title, speaker?, location?, type? ("break"|"keynote"|"workshop"|"panel"|"social"), description?} |

## Example payload

```json
{
  "type": "agenda_block",
  "slots": [
    {
      "time": "09:00",
      "title": "Opening keynote"
    },
    {
      "time": "10:00",
      "title": "Workshop A"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/agenda_block/
Full field contract: https://a2uicatalog.ai/spec.json
