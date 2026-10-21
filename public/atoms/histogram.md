# Histogram

The distribution of a list of numbers: bars of counts per bin on a counted y axis, with the bin edges on the x axis. The bins and the rounded axis come from d3-array bin() with the Sturges rule, computed on the server, so there is no script. A hidden table gives each bin from, to and count. Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a per-item --k, so a motion_timeline track on p grows the bars one after another and the standalone render is the finished picture; reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| values | array (required, 5 to 2000) of numbers. Entries that are not finite numbers (text, null, true or false, NaN, Infinity) or whose size is above 1e12 are skipped and counted in a note; with fewer than 5 numbers left a note replaces the chart. Only the first 2000 entries are read. |
| bins | integer (optional, 3 to 40). The number of bins to aim for. Default is the Sturges rule, ceil(log2(n)) + 1. d3 rounds the bin edges to 1, 2 or 5 times a power of ten, so the number drawn can differ a little from the number asked for. |
| x_label | string (optional, max 40). Names the values on the x axis. |
| unit | string (optional, max 12). Appended to the x label and to the edge values in the hidden table. |
| layout | string (optional, "bars" or "ridge", default "bars"). "ridge" draws one ridge per entry of `series` on shared bins, to compare distributions; `values` is then not read. Any other value draws bars. |
| series | array (optional, read only when layout is "ridge", 1 to 8) of {label (string, max 30, default "Series n"), values (array, 5 to 2000, of numbers, filtered like `values`)}. The shared bins come from d3 bin() of all the series pooled (`bins` applies); each ridge's height is its share of that series' values per bin, so series of different sizes compare. A series with fewer than 5 usable numbers is left out with a note; series beyond the first 8 are noted and not drawn. |
| version | integer (optional, default 1). The histogram contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "histogram",
  "values": 1
}
```

Live page: https://a2uicatalog.ai/atoms/histogram/
Full field contract: https://a2uicatalog.ai/spec.json
