# Chartjs Bar

Renders an interactive bar chart using Chart.js with configurable datasets.

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
  "type": "chartjs_bar",
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

Live page: https://a2uicatalog.ai/atoms/chartjs_bar/
Full field contract: https://a2uicatalog.ai/spec.json
