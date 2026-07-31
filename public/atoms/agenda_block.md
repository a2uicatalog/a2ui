# Agenda Block

Time-slotted schedule view for a day or event. Each slot has a time, title, optional speaker, location, type badge, and description.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| date | string (optional) |
| accent | string (optional, hex, default "#6366f1") |
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
