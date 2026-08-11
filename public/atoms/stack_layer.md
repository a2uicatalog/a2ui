# Stack Layer

One band of a layer_stack — a badge, the layer name, and either a single field/note pane or one pane per column via `cells`. Reads its colour tokens from the CSS custom properties an enclosing layer_stack sets and renders with sane fallback colours standalone. Rarely authored outside layer_stack.layers, but is its own atom type so it can be independently addressed by ComponentId in the A2UI v1.0 ChildList wire format.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | string (required). The layer name, e.g. "Transport". |
| badge | string (optional). Small label above the name — defaults to the 1-based position in layer_stack.layers as declared. |
| field | string (optional). The technical/schema fact, rendered monospace. Used when the layer has no `cells`. |
| note | string (optional). The plain-language gloss. Used when the layer has no `cells`. Backtick spans render as inline code. |
| examples | array of strings (optional). Concrete instances at this layer, rendered as a wrapping chip row across the foot of the band, e.g. "stdio", "Streamable HTTP". |
| status | string (optional). 'present' (default), 'absent' or 'partial'. absent renders the pane hollow with a dashed border — the point is that a layer a system does not define stays VISIBLE and reads as a stated absence. Maps onto the palette's cleared / blocked / accent tokens. |
| cells | array (optional). One entry per layer_stack column, index-aligned with it. Each item {field?, note?, status?} — the same three fields, per column. Given cells, the layer's own field/note/status are ignored. |

## Example payload

```json
{
  "type": "stack_layer",
  "name": "Stack Layer"
}
```

Live page: https://a2uicatalog.ai/atoms/stack_layer/
Full field contract: https://a2uicatalog.ai/spec.json
