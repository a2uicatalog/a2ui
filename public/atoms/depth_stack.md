# Depth Stack

Stacked layered cards with parallax depth — alias for card_stack

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| cards | array of {title, text} (alias: items) |
| count | integer (optional, max cards to show) |

## Example payload

```json
{
  "type": "depth_stack",
  "cards": [
    {
      "title": "Card 1",
      "body": "First card content."
    },
    {
      "title": "Card 2",
      "body": "Second card content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/depth_stack/
Full field contract: https://a2uicatalog.ai/spec.json
