# Expandable List

Nested tree list where parent items expand to reveal children on click.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array of {text, children}. Tree nodes. |

## Example payload

```json
{
  "type": "expandable_list",
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

Live page: https://a2uicatalog.ai/atoms/expandable_list/
Full field contract: https://a2uicatalog.ai/spec.json
