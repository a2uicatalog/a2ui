# Card Stack

Two to four cards stacked with CSS transform rotate and translateY, creating a fanned deck effect. The front card shows full title and body; back cards are progressively rotated and faded. No JavaScript — purely presentational. Useful for showcasing multiple items with a premium layered feel.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| cards | array. Each card: {title, body, accent}. Max 4 cards. |
| background | string (optional). Card background colour. Default "#1e293b". |
| border_color | string (optional). Card border colour. Default "rgba(255,255,255,0.08)". |
| height | integer (optional). Card height in px. Default 160. |

## Example payload

```json
{
  "type": "card_stack",
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

Live page: https://a2uicatalog.ai/atoms/card_stack/
Full field contract: https://a2uicatalog.ai/spec.json
