# Data Grid

IBM Carbon Design System enterprise data grid with typed columns (string/number/status/tag), optional row-selection checkboxes, sortable column indicators, zebra-stripe rows, and optional pagination footer. More capable than table and data_table_sortable for enterprise data-dense layouts. Adapted from IBM Carbon DataTable patterns.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Dark header bar above the grid. |
| columns | array. List of {header, key, type?, sortable?}. type is one of string | number | status | tag. |
| rows | array. List of row objects where each key matches a column key. |
| selectable | boolean (optional). Show row-selection checkboxes. Default false. |
| pagination | object (optional). '{per_page} splits rows into CSS-tab pages; clicking a page number label switches pages without JavaScript. Omit for single-page display.' |

## Example payload

```json
{
  "type": "data_grid",
  "columns": 1,
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

Live page: https://a2uicatalog.ai/atoms/data_grid/
Full field contract: https://a2uicatalog.ai/spec.json
