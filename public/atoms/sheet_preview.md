# Sheet Preview

Live read-only preview of a specified range in a Google Sheet. Renders as an HTML table. Works on Google Apps Script only.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| spreadsheet_id | string. The Google Sheets ID. |
| sheet_name | string. The name of the sheet tab. |
| range | string. The A1 notation range (e.g. A1:D10). |

## Example payload

```json
{
  "type": "sheet_preview",
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
  "sheet_name": "Sheet name",
  "range": "A1:D10"
}
```

Live page: https://a2uicatalog.ai/atoms/sheet_preview/
Full field contract: https://a2uicatalog.ai/spec.json
