# Dark Feature Grid

Responsive feature grid on dark background — icon, title, description per cell

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| features | array of {icon, title, description, colour} |
| columns | integer (optional, default 3) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "dark_feature_grid",
  "features": [
    "Core feature",
    "Advanced analytics",
    "API access"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/dark_feature_grid/
Full field contract: https://a2uicatalog.ai/spec.json
