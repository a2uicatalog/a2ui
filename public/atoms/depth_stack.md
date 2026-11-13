# Depth Stack

Stacked layered cards with parallax depth — alias for card_stack

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
