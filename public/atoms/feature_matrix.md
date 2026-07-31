# Feature Matrix

Renders a table comparing features across multiple products or versions.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

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
