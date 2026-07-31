# Mini Sparkline Set

Compact grid of multiple labeled sparklines for at-a-glance multi-metric comparison.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| series | array of {label, data}. Sparkline series. |

## Example payload

```json
{
  "type": "mini_sparkline_set",
  "series": [
    {
      "label": "Series A",
      "data": [
        10,
        20,
        30,
        40
      ]
    },
    {
      "label": "Series B",
      "data": [
        5,
        15,
        25,
        35
      ]
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/mini_sparkline_set/
Full field contract: https://a2uicatalog.ai/spec.json
