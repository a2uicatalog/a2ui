# Color Swatch Grid

Displays a grid of color swatches with labels and hex values for design system palettes.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| colors | array of {name, hex}. Color entries to display. |

## Example payload

```json
{
  "type": "color_swatch_grid",
  "colors": [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/color_swatch_grid/
Full field contract: https://a2uicatalog.ai/spec.json
