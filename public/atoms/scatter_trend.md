# Scatter Trend

Renders a coordinate scatter grid representing discrete data points intersected by a prominent glowing linear regression line.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'CSAT vs. Support Response Time') |
| data_points | list of [x, y] coordinates: [[1.2, 95], [2.5, 88], [3.1, 75]] |
| label_x | string (optional, e.g., 'Response Time (Hours)') |
| label_y | string (optional, e.g., 'CSAT Score') |

## Example payload

```json
{
  "type": "scatter_trend",
  "data_points": [
    {
      "x": 10,
      "y": 20
    },
    {
      "x": 30,
      "y": 45
    },
    {
      "x": 50,
      "y": 35
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/scatter_trend/
Full field contract: https://a2uicatalog.ai/spec.json
