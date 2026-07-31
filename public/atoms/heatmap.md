# Heatmap

Renders a graphical representation of data where individual values

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| data | list of lists of numbers (e.g., [[1, 2, 3], [4, 5, 6]]) |
| labels_x | list of strings (labels for the x-axis, e.g., ['Mon', 'Tue', 'Wed']) |
| labels_y | list of strings (labels for the y-axis, e.g., ['AM', 'PM']) |
| color_scale | list of strings (colors for the gradient, e.g., ['#FFFFFF', '#FF0000'] for white to red) |
| unit | string (optional, unit for the data values, e.g., '°C') |

## Example payload

```json
{
  "type": "heatmap",
  "data": 1,
  "labels_x": [
    "Category A",
    "Category B",
    "Category C",
    "Category D"
  ],
  "labels_y": [
    "Low",
    "Medium",
    "High"
  ],
  "color_scale": [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/heatmap/
Full field contract: https://a2uicatalog.ai/spec.json
