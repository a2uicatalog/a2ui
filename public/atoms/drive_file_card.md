# Drive File Card

Single Drive file card — coloured file-type badge (DOC/XLS/PPT/PDF), file name, optional description, and an "Open →" button. Works on any surface using static name/mime/url fields. On GAS, file_id triggers live lookup via DriveApp to populate name and mime automatically.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| file_id | string (gas-native). Drive file ID for live name/type lookup on GAS. |
| name | string. File display name — required on non-GAS surfaces. |
| mime | string. MIME type for badge colour (e.g. application/vnd.google-apps.spreadsheet). |
| url | string. URL to open — required on non-GAS surfaces. |
| description | string (optional). Short description shown below the file name. |

## Example payload

```json
{
  "type": "drive_file_card",
  "file_id": "File id",
  "name": "Drive File Card",
  "mime": "application/pdf",
  "url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/drive_file_card/
Full field contract: https://a2uicatalog.ai/spec.json
