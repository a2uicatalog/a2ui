# Brevet Timeline

Vertical dated timeline of events for study/revision pages.

## Surfaces

google-apps-script-web, mcp-apps

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
