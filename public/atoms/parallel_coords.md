# Parallel Coords

Rows of numbers compared across 2 to 8 measures at once: each measure is a vertical axis with its own scale, and each row is one line that crosses every axis at its value, so clusters, trade-offs and outliers across many measures show as bundles of lines. Optionally the lines are coloured by one measure (a light-to-dark ramp from the theme accent, with a legend giving the range). Axis scales come from d3 scaleLinear nice() and ticks() and the lines from d3 line(), computed on the server, so there is no script. The picture is static: the interactive brushing of a Plotly parallel-coordinates chart (dragging on an axis to filter rows) is not available. A hidden table gives every value of every row.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| dimensions | array (required, 2 to 8) of {label (string, max 24, default "Dimension n"), values (array of numbers), min (number, optional), max (number, optional), reverse (boolean, optional)}. Row i takes values[i] of every dimension, so every dimension lists the rows in the same order. Without min and max the axis runs over the d3 nice() of the values; with both (min below max) the axis is exactly that range and a value outside it is drawn on the edge, with a note (the table keeps the real number). reverse true puts the highest value at the bottom and says so under the label. A row with a missing or non-numeric value (finite, up to 1e12 in size) in any dimension is left out with a note; rows beyond the first 200 and dimensions beyond the first 8 are noted and not drawn. Entries that are not a dimension are left out with a note. |
| row_labels | array (optional) of strings (max 30). Names the rows in the hidden table; default "Row n". |
| color_by | string or integer (optional). The label of a dimension, or its number counting from 0, to colour the lines by. A name that matches no dimension is noted and the lines stay one colour. |
| version | integer (optional, default 1). The parallel_coords contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "parallel_coords"
}
```

Live page: https://a2uicatalog.ai/atoms/parallel_coords/
Full field contract: https://a2uicatalog.ai/spec.json
