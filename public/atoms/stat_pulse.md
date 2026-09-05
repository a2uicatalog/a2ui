# Stat Pulse

Three hero stat tiles (value, label, delta with tone) above a small trend bar chart with rounded tops and one emphasized "current" bar. A closing figure for any status or activity digest.

## Surfaces

google-chat-chromium-render

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., '30-DAY PULSE') |
| stamp | string (optional, e.g., '20 Jun – 19 Jul') |
| stats | list of exactly 3 dicts: [{value: string, label: string, delta: string, tone: one of good|bad|flat}, ...] |
| trend | dict: {bars: list of numbers (max 6), labels: list of strings matching bars length, hot_index: integer index of the bar to emphasize} |

## Example payload

```json
{
  "type": "stat_pulse",
  "stats": [
    {
      "label": "Views",
      "value": "1.2M"
    },
    {
      "label": "Clicks",
      "value": "42K"
    },
    {
      "label": "CTR",
      "value": "3.5%"
    }
  ],
  "trend": 1
}
```

Live page: https://a2uicatalog.ai/atoms/stat_pulse/
Full field contract: https://a2uicatalog.ai/spec.json
