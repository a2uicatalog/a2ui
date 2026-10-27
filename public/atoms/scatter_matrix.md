# Scatter Matrix

A scatter plot matrix (Plotly splom): 2 to 6 numeric dimensions on one grid, every dimension on a shared axis across its row and column, so each cell plots one dimension against another and a pattern between any two shows at a glance. Below the diagonal each cell is a small scatter plot of every complete row (the upper half too with show_upper); the diagonal names the dimension; wide pages also show each dimension's range on the outer edges. Each axis comes from d3 nice() and ticks() on the server, so there is no script. A legend lists every dimension with its range and a hidden table gives every value of every row. Static: no hover or brushing. Motion-ready: each cell fades in through --k from --p (default 1).

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| dimensions | array (required, 2 to 6) of {label (string, max 24, default "Dimension n"), values (array of numbers)}. Row r is the r-th value of every dimension. A row where any dimension has no finite number up to 1e12 in size is left out and counted in a note; an entry that is not a dimension with a list of values is left out with a note; dimensions beyond the first 6 are noted and not drawn. At most 200 complete rows are read; later rows are noted and not drawn. With fewer than 2 dimensions or 2 complete rows a note replaces the chart. |
| show_upper | boolean (optional, default false). Only true also draws the upper half (the same plots with the axes swapped). |
| version | integer (optional, default 1). The scatter_matrix contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "scatter_matrix"
}
```

Live page: https://a2uicatalog.ai/atoms/scatter_matrix/
Full field contract: https://a2uicatalog.ai/spec.json
