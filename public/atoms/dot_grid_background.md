# Dot Grid Background

Panel with a CSS repeating dot, grid, or cross background pattern using background-image with radial-gradient or linear-gradient. No SVG, no JavaScript. Useful as a texture layer behind content in dark or light themes.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| variant | "dots" | "grid" | "cross"  (optional, default "dots") |
| title | string (optional). Text heading overlaid on the pattern. |
| body | string (optional). Body text overlaid on the pattern (markdown inline supported). |
| dot_color | string (optional). Dot or line colour. Default "rgba(148,163,184,0.35)". |
| background | string (optional). Panel background fill. Default "#0d1525". |
| spacing | integer (optional). Grid cell size in px. Default 24. |
| dot_size | integer (optional). Dot radius in px (dots variant only). Default 1. |

## Example payload

```json
{
  "type": "dot_grid_background"
}
```

Live page: https://a2uicatalog.ai/atoms/dot_grid_background/
Full field contract: https://a2uicatalog.ai/spec.json
