# Weather Now

Current-conditions weather card — a hero temperature reading beside a drawn CSS weather glyph (sun/cloud/storm, not an emoji or external icon font), condition text, hi/lo, and 4 supporting stat tiles (precip, wind, UV, humidity).

## Surfaces

google-chat-chromium-render

## Fields

| Field | Type |
|---|---|
| city_line | string (e.g., 'TOULOUSE — LA VILLE ROSE'). Eyebrow line naming the location. |
| stamp | string (optional, e.g., 'Sat 19 Jul · 17:45') |
| temp | integer. The hero reading. |
| condition | string. Display text in any language, e.g. 'Ensoleillé'. |
| code | string, one of sun|partly|cloud|rain|storm. Selects the drawn glyph. |
| hi | integer |
| lo | integer |
| stats | list of exactly 4 dicts: [{value: string, label: string}, ...] |

## Example payload

```json
{
  "type": "weather_now",
  "city_line": "City line",
  "temp": 1,
  "condition": "Condition",
  "code": "{\"type\": \"example\"}",
  "hi": 1,
  "lo": 1,
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
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/weather_now/
Full field contract: https://a2uicatalog.ai/spec.json
