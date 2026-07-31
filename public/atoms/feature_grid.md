# Feature Grid

A responsive CSS grid of feature tiles, each with an icon, title, and description paragraph. Supports 2 or 3 columns and optional per-tile badges. The canonical Tailwind UI marketing feature section pattern.

## Surfaces

web, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| heading | string (optional). Section heading above the grid. |
| description | string (optional). Section sub-heading or intro paragraph. |
| columns | integer (optional). 2 or 3. Default 3. |
| features | array of objects with fields — icon (emoji or text), title, description, badge (optional short label), color (optional hex accent). |

## Example payload

```json
{
  "type": "feature_grid"
}
```

Live page: https://a2uicatalog.ai/atoms/feature_grid/
Full field contract: https://a2uicatalog.ai/spec.json
