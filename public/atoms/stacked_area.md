# Stacked Area

Renders cumulative layered area chart trends utilizing overlapping translucent gradient fills and glowing series borders.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'SaaS Cumulative Workloads') |
| labels | list of strings representing X-axis ticks (e.g., ['Q1', 'Q2', 'Q3', 'Q4']) |
| series | list of dictionaries representing stacked layers: [{'label': 'Enterprise', 'data': [10, 25, 45, 60], 'color': '#00f2ff'}, ...] |

## Example payload

```json
{
  "type": "stacked_area",
  "labels": [
    "Category A",
    "Category B",
    "Category C",
    "Category D"
  ],
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

Live page: https://a2uicatalog.ai/atoms/stacked_area/
Full field contract: https://a2uicatalog.ai/spec.json
