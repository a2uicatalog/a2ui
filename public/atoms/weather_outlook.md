# Weather Outlook

Multi-day forecast as horizontal range bars on one shared temperature axis with gridlines — lo anchored at the bar's cool end, hi at its warm end, a small drawn weather glyph per row, and a precipitation chip that highlights when precip crosses a wet threshold. The shared axis is what makes a cold/wet day visually collapse relative to its neighbours.

## Surfaces

google-chat-chromium-render

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'NEXT 3 DAYS — OUTLOOK') |
| city | string (optional, e.g., 'Toulouse') |
| scale | dict: {min: integer, max: integer}. Shared axis bounds in the display unit; gridlines drawn at 5-degree steps. |
| days | list of dicts, chronological: [{label: string (e.g. "SUN"), date: string (e.g. "20 Jul"), code: one of sun|partly|cloud|rain|storm, hi: integer, lo: integer, precip: integer 0-100}, ...] |

## Example payload

```json
{
  "type": "weather_outlook",
  "scale": 1,
  "days": 1
}
```

Live page: https://a2uicatalog.ai/atoms/weather_outlook/
Full field contract: https://a2uicatalog.ai/spec.json
