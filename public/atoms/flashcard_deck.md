# Flashcard Deck

Tap-to-flip study cards cycling through question/answer pairs.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| cards | array (required) of {front, back} |
| accent | string (optional, hex, default "#6366f1") |
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
