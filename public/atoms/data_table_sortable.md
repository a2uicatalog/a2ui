# Data Table Sortable

Renders a data table with client-side column sorting and optional pagination.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| headers | array of strings. Column headers. |
| rows | array of arrays. Table rows. |

## Example payload

```json
{
  "type": "data_table_sortable",
  "headers": [
    "Name",
    "Value",
    "Status"
  ],
  "rows": [
    [
      "Example",
      "42",
      "Active"
    ],
    [
      "Another",
      "17",
      "Pending"
    ]
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/data_table_sortable/
Full field contract: https://a2uicatalog.ai/spec.json
