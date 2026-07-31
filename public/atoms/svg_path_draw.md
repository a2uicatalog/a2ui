# Svg Path Draw

An SVG path that animates drawing itself from start to end using the stroke-dasharray / stroke-dashoffset CSS technique. The agent selects a named shape (arrow, check, circle, zigzag, infinity) or supplies a custom SVG path string.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| shape | "arrow" | "check" | "circle" | "zigzag" | "infinity"  (optional, default "arrow") |
| color | string (optional). Stroke colour. Default "#4f46e5". |
| width | integer (optional). Stroke width in px. Default 3. |
| duration | number (optional). Draw duration in seconds. Default 1.5. |
| label | string (optional). Caption below the SVG. |

## Example payload

```json
{
  "type": "svg_path_draw"
}
```

Live page: https://a2uicatalog.ai/atoms/svg_path_draw/
Full field contract: https://a2uicatalog.ai/spec.json
