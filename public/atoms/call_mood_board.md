# Call Mood Board

Renders a premium, aesthetic call emotion summary and theme board showing detected sentiments, dominant moods with color codings, active themes, and word weightings.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'Call Mood & Themes Summary') |
| moods | list of dictionaries representing call emotions: [{'mood': 'Collaborative', 'intensity': 85, 'color': '#10b981'}, ...] |
| themes | list of dictionaries representing keywords/themes: [{'term': 'Pricing', 'weight': 90, 'sentiment': 'neutral'}, ...] |
| summary | string (optional summary paragraph) |

## Example payload

```json
{
  "type": "call_mood_board",
  "moods": 1,
  "themes": [
    {
      "label": "Positive",
      "count": 42
    },
    {
      "label": "Neutral",
      "count": 18
    },
    {
      "label": "Negative",
      "count": 7
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/call_mood_board/
Full field contract: https://a2uicatalog.ai/spec.json
