# Entity List

List of named resources — each row shows an avatar or icon, a title, a subtitle, a status badge, and optional trailing metadata. Covers project lists, deployment rosters, and team member panels. Inspired by Vercel Geist Entity component.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | {'type': 'array', 'description': 'List of {name, subtitle?, icon?, status?, meta?} entries.'} |

## Example payload

```json
{
  "type": "entity_list",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/entity_list/
Full field contract: https://a2uicatalog.ai/spec.json
