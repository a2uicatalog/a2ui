# Sentiment Summary

Renders an emotional summary and sentiment tracker for a call or meeting, showing positive/negative/neutral mix, sentiment index progress arc, and emotional journey area timeline.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'Call Sentiment & Mood Analysis') |
| sentiment_index | number representing overall positive sentiment percentage (0-100, e.g., 78) |
| emotional_journey | list of numbers representing call sentiment score over time intervals (values -1.0 to 1.0, e.g., [0.1, -0.2, 0.4, 0.8, 0.6]) |
| themes | list of dictionaries representing key themes with weights or moods: [{'theme': 'Technical Alignment', 'mood': 'Analytical', 'score': 85}, ...] |

## Example payload

```json
{
  "type": "sentiment_summary",
  "sentiment_index": 1,
  "emotional_journey": 1,
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

Live page: https://a2uicatalog.ai/atoms/sentiment_summary/
Full field contract: https://a2uicatalog.ai/spec.json
