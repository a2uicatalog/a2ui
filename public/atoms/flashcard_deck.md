# Flashcard Deck

Tap-to-flip study cards cycling through question/answer pairs.

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
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| cards | array (required) of {front, back} |
| accent | string (optional, hex, default "#4f46e5") |
| label_front | string (optional, default "QUESTION") |
| label_back | string (optional, default "ANSWER") |

## Example payload

```json
{
  "type": "flashcard_deck",
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

Live page: https://a2uicatalog.ai/atoms/flashcard_deck/
Full field contract: https://a2uicatalog.ai/spec.json
