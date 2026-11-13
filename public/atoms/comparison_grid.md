# Comparison Grid

Renders a grid comparing multiple products or services with features, often using icons or checkmarks to indicate presence.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| products | array |
| features | array |

## Example payload

```json
{
  "type": "comparison_grid",
  "products": [
    {
      "name": "Product A"
    },
    {
      "name": "Product B"
    }
  ],
  "features": [
    "Core feature",
    "Advanced analytics",
    "API access"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/comparison_grid/
Full field contract: https://a2uicatalog.ai/spec.json
