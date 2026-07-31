# Comparison Grid

Renders a grid comparing multiple products or services with features,

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

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
