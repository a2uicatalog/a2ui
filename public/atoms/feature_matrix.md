# Feature Matrix

Renders a table comparing features across multiple products or versions.

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
| product_names | array |
| features | array |

## Example payload

```json
{
  "type": "feature_matrix",
  "product_names": [
    "Starter",
    "Pro",
    "Enterprise"
  ],
  "features": [
    "Core feature",
    "Advanced analytics",
    "API access"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/feature_matrix/
Full field contract: https://a2uicatalog.ai/spec.json
