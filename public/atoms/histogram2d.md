# Histogram2D

Counts of x,y points in a grid of 2-D bins (the Plotly histogram2d trace), drawn as a heatmap: d3 bin() is run once on x and once on y, the cell count is the number of points that fall in both bins, and the grid is handed to the heatmap atom, so it has the heatmap colour bar, the cell counts printed inside the cells and a hidden data table. The highest y bin is the top row. Use nbinsx and nbinsy for the number of bins (the real count is the nearest round step, as in d3), or leave them out for the Sturges default. At most 20,000 points are used and at most 40 bins per axis, each with a note.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| x | array (required, numbers, at least 2 usable pairs with y; up to 20,000 used). |
| y | array (required, numbers, same length as x). |
| nbinsx | integer (optional, 3 to 40, the bin count asked of d3 for x; default Sturges). |
| nbinsy | integer (optional, 3 to 40, the bin count asked of d3 for y; default Sturges). |
| title | string (optional, max 80). |
| x_label | string (optional, max 40, named in the note under the grid). |
| y_label | string (optional, max 40, named in the note under the grid). |
| scale | string (optional, a heatmap colour scale name such as Blues, Viridis or YlOrRd; default YlGnBu, light for few points and dark for many). |
| show_values | boolean (optional, default true, prints each count in its cell). |
| show_colorbar | boolean (optional, default true). |
| version | integer (optional, default 1; a higher number draws as version 1 with a muted note). |

## Example payload

```json
{
  "type": "histogram2d",
  "x": 1,
  "y": 1
}
```

Live page: https://a2uicatalog.ai/atoms/histogram2d/
Full field contract: https://a2uicatalog.ai/spec.json
