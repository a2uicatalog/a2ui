# Scatter Trend

Renders a coordinate scatter grid representing discrete data points intersected by a prominent glowing linear regression line.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'CSAT vs. Support Response Time') |
| data_points | list of [x, y] coordinates: [[1.2, 95], [2.5, 88], [3.1, 75]] |
| label_x | string (optional, e.g., 'Response Time (Hours)') |
| label_y | string (optional, e.g., 'CSAT Score') |
| series | (optional, preview) array of up to 8 series {label, x, y, mode, color, dash, shape, size, symbol, fill, text}. x is numbers or ISO 8601 date strings (UTC; a missing x is the index 0, 1, 2...), y numbers. mode lines|markers|lines+markers|text or any + combination (default lines+markers up to 20 points, else lines). color a #hex or colour word, else the theme palette. dash solid|dash|dot|dashdot|longdash|longdashdot, symbol circle|square|diamond|triangle-up|cross|x (both cycle per series when unset, so series differ by more than colour). shape linear|spline|hv|vh|hvh|vhv. size a diameter number or an array per point (bubble). fill tozeroy|tonexty. text an array of point labels. Present and non-empty, this replaces the labels/datasets (or data_points) drawing; absent, nothing changes. |
| x_type | (optional, with series) linear or date. Default: date when the first x is a date string, else linear. |
| x_label | string (optional, with series). Axis title under the plot. scatter_trend also reads label_x. |
| y_label | string (optional, with series). Axis title above the plot. scatter_trend also reads label_y. |
| max_points | (optional, with series) integer 50 to 2000, default 2000. A series with more usable points is thinned to evenly spaced points (first and last kept) and a visible note says so; the hidden table lists the drawn points. This is the scattergl case: many points, a cap, never a silent drop. |
| version | integer (optional, default 1). A whole number above 1 draws as version 1 with a note. |

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
