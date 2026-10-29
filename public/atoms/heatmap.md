# Heatmap

Renders a graphical representation of data where individual values

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| data | list of lists of numbers (e.g., [[1, 2, 3], [4, 5, 6]]) |
| labels_x | list of strings (labels for the x-axis, e.g., ['Mon', 'Tue', 'Wed']) |
| labels_y | list of strings (labels for the y-axis, e.g., ['AM', 'PM']) |
| color_scale | list of strings (colors for the gradient, e.g., ['#FFFFFF', '#FF0000'] for white to red) |
| unit | string (optional, unit for the data values, e.g., '°C') |
| z_min | number (optional, value drawn with the first colour of the scale; default the smallest value) |
| z_max | number (optional, value drawn with the last colour; default the largest value) |
| z_mid | number (optional, value drawn with the middle of the scale, for diverging data; the colour range becomes symmetric around it; ignored when z_min and z_max are both given) |
| scale | string (optional, a Plotly colour scale name - Viridis, Cividis, Blues, Greens, Reds, Greys, YlGnBu, YlOrRd, RdBu, Bluered, Picnic, Rainbow, Portland, Jet, Hot, Blackbody, Earth or Electric; default Viridis, or color_scale when that is given) |
| show_colorbar | boolean (optional, default true, draws the colour bar with the lowest and highest value) |
| show_values | boolean (optional, default false, prints each value inside its cell) |
| value_format | string (optional, how values print - an optional comma for thousands, optional .N decimals, then f, % or d; for example ',.1f' or '.0%') |
| version | integer (optional, default 1; a higher number draws as version 1 with a muted note) |

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
