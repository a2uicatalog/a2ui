# Drive Recent Files

Horizontal swipeable carousel of recently modified Drive files. Each card shows a coloured file-type badge (DOC/XLS/PPT/PDF), name, relative modified time, and owner. On GAS searches files modified in last 30 days via DriveApp; on other surfaces renders from items[] array or Drive REST API.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional). Section label above carousel. Default "Recent Files". |
| count | integer (optional). Number of files to show, max 20. Default 10. |
| accent | string (optional). Accent colour for active nav dot. Default |
| items | array (static connector). File objects for non-GAS surfaces. |
| auth_token | string (api connector). OAuth2 bearer token for REST API. |

## Example payload

```json
{
  "type": "drive_recent_files",
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

Live page: https://a2uicatalog.ai/atoms/drive_recent_files/
Full field contract: https://a2uicatalog.ai/spec.json
