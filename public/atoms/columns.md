# Columns

Generic multi-column layout container. Each column holds an array of atom blocks rendered inline. 2–6 columns; collapses to single column on mobile.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| cols | integer (optional, 2–6, default 2) |
| gap | string (optional, css gap value, default "1.5rem") |
| align | string (optional, "top"|"center"|"stretch", default "top") |
| items | array (required). Each item is {blocks: [atom blocks]} — one entry per column. |

## Example payload

```json
{
  "type": "columns",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/columns/
Full field contract: https://a2uicatalog.ai/spec.json
