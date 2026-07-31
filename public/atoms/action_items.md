# Action Items

Action items table with owner, due date, and status. For retros, meeting notes, sprint planning, incident reports.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional) |
| items | array (required). Array of {action, owner?, due?, status? ("open"|"in_progress"|"done")} |

## Example payload

```json
{
  "type": "action_items",
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

Live page: https://a2uicatalog.ai/atoms/action_items/
Full field contract: https://a2uicatalog.ai/spec.json
