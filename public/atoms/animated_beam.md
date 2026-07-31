# Animated Beam

Inline SVG panel showing two labelled endpoint nodes connected by a path with a pulsing light dot that travels along it, animating via CSS stroke-dashoffset. No JavaScript, no mousemove. Visualises data routing between two named components.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| from_label | string. Left/source node label. |
| to_label | string. Right/target node label. |
| label | string (optional). Small caption above the beam diagram. |
| body | string (optional). Description text below the diagram. |
| active | bool (optional). Whether the beam pulse animates. Default true. |
| color | string (optional). Beam and node accent colour. Default "#38bdf8". |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| curved | bool (optional). Use a curved cubic-bezier path. Default true. |

## Example payload

```json
{
  "type": "animated_beam",
  "from_label": "From label",
  "to_label": "To label"
}
```

Live page: https://a2uicatalog.ai/atoms/animated_beam/
Full field contract: https://a2uicatalog.ai/spec.json
