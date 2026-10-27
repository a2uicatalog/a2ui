# Ternary Plot

Shows what share each of three parts makes up of a whole, one dot per observation, on an equilateral triangle: a point's distance from a corner is how little of that part it has, and the corners are pure A, pure B and pure C. Values are normalised to shares that sum to 100%, gridlines run every 20% on all three axes with their percentages printed on the edges, and an optional dashed line joins the points in the order given. The axis ticks come from d3-scale's linear ticks and the placing is plain trigonometry, computed on the server, so there is no script. A hidden table gives every point's three shares. Static, settled picture; each point fades in through --k from --p (build progress 0 to 1, default 1).

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| a_label | string (optional, max 20, default "A"). Names the part at the top corner. |
| b_label | string (optional, max 20, default "B"). Names the part at the bottom left corner. |
| c_label | string (optional, max 20, default "C"). Names the part at the bottom right corner. |
| points | array (required, 1 to 200) of {label (string or number, max 30, default "Point n"), a, b, c (non-negative numbers up to 1e12 in size, not all zero)}. A point whose a, b or c is missing, not a finite number, negative or too large, or that sums to 0, and an entry that is not a point, is left out and counted in a note. Points beyond the first 200 are noted and not drawn. |
| connect | boolean (optional, default false). Only true switches it on. Draws a dashed line through the points in the given order. |
| version | integer (optional, default 1). The ternary_plot contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "ternary_plot"
}
```

Live page: https://a2uicatalog.ai/atoms/ternary_plot/
Full field contract: https://a2uicatalog.ai/spec.json
