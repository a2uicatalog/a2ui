# Before After Stack

Animated comparison: old approach items cross out one by one, then new approach slides in

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array of strings (old approach items to cross out, alias: before_items) |
| before_label | string (optional) |
| after_label | string (optional) |
| result | string (the new approach shown after animation, alias: after_text) |
| delay | number (optional, seconds between strikes) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "before_after_stack",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ],
  "result": "Improved"
}
```

Live page: https://a2uicatalog.ai/atoms/before_after_stack/
Full field contract: https://a2uicatalog.ai/spec.json
