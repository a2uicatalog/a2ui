# Quiver

A field of arrows on linear axes: each arrow sits on its x, y point and points the way its u (across) and v (up) numbers say, with a length in proportion to the size of the vector. Use it for wind, flow, forces or any vector field. The axes come from d3 nice() and ticks() (d3-scale's linear scale), computed on the server, so there is no script. Arrows are centred on their point, drawn at a fixed size scale so the longest is a set length, and an arrow of length 0 is a dot. A hidden table gives every arrow's x, y, across, up and length. Static, settled picture; each arrow fades in through --k from --p (build progress 0 to 1, default 1).

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| x_label | string (optional, max 40, default "x"). Names the horizontal axis. |
| y_label | string (optional, max 40, default "y"). Names the vertical axis. |
| unit | string (optional, max 12). The unit of u, v and the length; appended to those values in the table and the label. |
| arrows | array (required, 1 to 200) of {x, y, u, v (finite numbers up to 1e12 in size), label (string or number, max 30, default "Arrow n")}. An entry with a missing or unusable number, or that is not an arrow, is left out and counted in a note. Arrows beyond the first 200 are noted and not drawn. |
| arrow_scale | number (optional, 0.1 to 1, default 1). Shrinks every arrow by this factor; the longest is 120 units of a 1000 unit wide drawing at scale 1. A value that is not a number is ignored. |
| version | integer (optional, default 1). The quiver contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "quiver"
}
```

Live page: https://a2uicatalog.ai/atoms/quiver/
Full field contract: https://a2uicatalog.ai/spec.json
