# Drive Folder Contents

Responsive grid of files and subfolders inside a Drive folder. Subfolders appear first, each item shows a coloured file-type badge and name, clicking opens in Drive. On GAS uses DriveApp with folder_id; on other surfaces renders from items[] array or Drive REST API with folder_id + auth_token.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| folder_id | string (gas-native/api). The Google Drive folder ID to browse. |
| title | string (optional). Override for the folder name shown as header. |
| count | integer (optional). Max items to show. Default 12. |
| items | array (static connector). File objects for non-GAS surfaces. |
| auth_token | string (api connector). OAuth2 bearer token for REST API. |

## Example payload

```json
{
  "type": "drive_folder_contents",
  "folder_id": "Folder id",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ],
  "auth_token": "your-api-token"
}
```

Live page: https://a2uicatalog.ai/atoms/drive_folder_contents/
Full field contract: https://a2uicatalog.ai/spec.json
