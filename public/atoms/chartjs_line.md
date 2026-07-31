# Chartjs Line

Renders an interactive line chart using Chart.js for time-series or trend data.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| labels | array of strings. X-axis labels. |
| datasets | array of {label, data}. Chart datasets. |

## Example payload

```json
{
  "type": "chartjs_line",
  "labels": [
    "Category A",
    "Category B",
    "Category C",
    "Category D"
  ],
  "datasets": [
    {
      "label": "Dataset A",
      "data": [
        65,
        59,
        80,
        72
      ]
    },
    {
      "label": "Dataset B",
      "data": [
        28,
        48,
        40,
        55
      ]
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/chartjs_line/
Full field contract: https://a2uicatalog.ai/spec.json
