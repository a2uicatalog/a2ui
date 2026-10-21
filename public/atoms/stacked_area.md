# Stacked Area

Renders cumulative layered area chart trends utilizing overlapping translucent gradient fills and glowing series borders.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'SaaS Cumulative Workloads') |
| labels | list of strings representing X-axis ticks (e.g., ['Q1', 'Q2', 'Q3', 'Q4']) |
| series | list of dictionaries representing stacked layers: [{'label': 'Enterprise', 'data': [10, 25, 45, 60], 'color': '#00f2ff'}, ...] |
| offset | string (optional): how the layers sit on the baseline. Absent, 'none' or anything else keeps today's stacked bars. 'expand' draws a real area chart with every point scaled to 100% (a 0-100% axis), 'silhouette' centres the layers on a middle line, 'wiggle' is a streamgraph (d3's wiggle baseline, layers ordered inside-out). silhouette and wiggle have no value axis (the baseline means nothing); the hidden table lists the raw values. Up to 12 series and 60 labels; negative or non-numeric cells draw as 0 and are counted in a note. |
| version | integer (optional, default 1). The stacked_area contract the payload was written for. Only version 1 exists; a higher whole number draws as version 1 with a note. |

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
