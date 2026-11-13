# Drive File List

Live list of files in a Google Drive folder rendered with icons and download links. Works on Google Apps Script only.

## Surfaces

google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| folder_id | string. The Google Drive folder ID to list files from. |
| max_results | integer (optional). Maximum number of files to return. Default is 10. |

## Example payload

```json
{
  "type": "drive_file_list",
  "folder_id": [
    {
      "title": "Doc 1",
      "url": "https://example.com"
    },
    {
      "title": "Doc 2",
      "url": "https://example.com"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/drive_file_list/
Full field contract: https://a2uicatalog.ai/spec.json
