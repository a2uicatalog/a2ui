# Sheet Form Submit

Inline form that appends a timestamped row to a Google Sheet on submit. Calls google.script.run.a2uiSheetAppend server-side. Each field renders as a labelled input or textarea.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| spreadsheet_id | string. Target Google Sheets ID. |
| sheet_name | string (optional). Sheet tab name. Default is "Sheet1". |
| title | string (optional). Form heading. |
| fields | array. Array of {label, name, type, placeholder} objects. type is text, email, number, or textarea. |
| submit_label | string (optional). Submit button text. Default is "Submit". |
| accent | string (optional). Submit button colour. |

## Example payload

```json
{
  "type": "sheet_form_submit",
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
  "fields": 1
}
```

Live page: https://a2uicatalog.ai/atoms/sheet_form_submit/
Full field contract: https://a2uicatalog.ai/spec.json
