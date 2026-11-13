# Gmail Inbox

Horizontal swipeable carousel of Gmail inbox threads. Each card shows a coloured sender avatar, name, subject (bold if unread), snippet and timestamp. Clicking opens the thread in Gmail. On GAS uses GmailApp for live data; on other surfaces renders from items[] array or Gmail REST API.

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
| title | string (optional). Section label above carousel. Default "Inbox". |
| count | integer (optional). Number of threads, max 20. Default 10. |
| accent | string (optional). Accent colour for unread indicator and nav dot. Default |
| items | array (static connector). Email objects for non-GAS surfaces. |
| auth_token | string (api connector). OAuth2 bearer token for REST API. |

## Example payload

```json
{
  "type": "gmail_inbox",
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

Live page: https://a2uicatalog.ai/atoms/gmail_inbox/
Full field contract: https://a2uicatalog.ai/spec.json
