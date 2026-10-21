# Box Plot

Compares groups of numbers as box plots on one shared horizontal axis: per group a box from the lower to the upper quartile, a line at the median, whiskers to the furthest numbers within 1.5 times the box length, and dots for the outliers beyond. The quartiles come from d3-array quantileSorted and the axis from d3 nice() and ticks(), computed on the server, so there is no script. A hidden table gives each group's count, minimum, quartiles, median, maximum and outlier count. Motion-ready: each group fades in through --k from --p (build progress 0 to 1, default 1); the standalone render is the finished picture and reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| groups | array (required, 1 to 12) of {label (string, max 30, default "Group n"), values (array, 5 to 2000, of numbers)}. Entries that are not finite numbers or whose size is above 1e12 are skipped and counted in a note; a group with fewer than 5 usable numbers, or an entry that is not a group, is left out with a note. Groups beyond the first 12 are noted and not drawn. |
| x_label | string (optional, max 40). Names the values on the axis. |
| unit | string (optional, max 12). Appended to the axis caption and to every value in the label and hidden table. |
| show_points | boolean (optional, default false). Only true switches it on. Draws every usable number of each group as a small dot along its row, at exactly its place on the axis, stacked vertically only as far as needed so no two dots touch (a deterministic dodge beeswarm, no script), behind the box, whiskers and median. Rows are taller. At most 300 dots per chart, shared across the groups in proportion to their sizes and evenly spaced through each group's sorted numbers; a note says so, and the table counts them all. A dot that cannot be placed without touching another stays on the edge of its row; a note counts these. |
| version | integer (optional, default 1). The box_plot contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "box_plot"
}
```

Live page: https://a2uicatalog.ai/atoms/box_plot/
Full field contract: https://a2uicatalog.ai/spec.json
