# Stagger List

List of items that animate in with a staggered delay — supports icons and descriptions

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array of strings or {icon, text, sub} objects |
| direction | string (optional, up|down|left|right) |
| stagger | number (optional, delay between items in seconds, default 0.1) |

## Example payload

```json
{
  "type": "stagger_list",
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

Live page: https://a2uicatalog.ai/atoms/stagger_list/
Full field contract: https://a2uicatalog.ai/spec.json
