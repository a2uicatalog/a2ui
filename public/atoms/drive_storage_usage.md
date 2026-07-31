# Drive Storage Usage

Google Drive storage quota displayed as a labelled progress bar — used GB, total GB, and percentage. Bar colour shifts to amber above 70% and red above 90%. On GAS uses DriveApp; elsewhere pass used_gb and total_gb fields.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional). Card heading. Default is "Drive Storage". |
| accent | string (optional). Bar colour below 70% usage. |
| used_gb | number (static connector). GB used — for non-GAS surfaces. |
| total_gb | number (static connector). Total quota GB — for non-GAS surfaces. |
| auth_token | string (api connector). OAuth2 bearer token for REST API. |

## Example payload

```json
{
  "type": "drive_storage_usage",
  "used_gb": 1,
  "total_gb": 5,
  "auth_token": "your-api-token"
}
```

Live page: https://a2uicatalog.ai/atoms/drive_storage_usage/
Full field contract: https://a2uicatalog.ai/spec.json
