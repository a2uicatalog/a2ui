# Data Table Sortable

Renders a data table with client-side column sorting and optional pagination.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| headers | array of strings. Column headers. |
| rows | array of arrays. Table rows. |
| select_state | (wired dialect only) ValueStore id holding the array of selected row ids. Combine with a column whose key is _select to get a per-row checkbox; each row needs a real id field to be selectable. |
| select_count_state | (wired dialect only) companion ValueStore id holding the selected array's length — wire a NumericThreshold to it to show/hide a bulk action bar. |
| delete_action_id | (wired dialect only) action id to run for row deletion. A column whose key is _delete renders a per-row delete button that sets select_state to just that row's id and runs this action directly; the same action id can be targeted by an external Delete-N-selected button via the standard collect wiring, ids from select_state's value. |

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
  ],
  "select_state": [],
  "select_count_state": [],
  "delete_action_id": "Delete action id"
}
```

Live page: https://a2uicatalog.ai/atoms/data_table_sortable/
Full field contract: https://a2uicatalog.ai/spec.json
