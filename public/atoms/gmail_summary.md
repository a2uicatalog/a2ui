# Gmail Summary

Summary list of recent emails in the user's Gmail matching a search query. Works on Google Apps Script only.

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
| query | string. The search query (e.g. "is:unread label:work"). |
| max_results | integer (optional). Maximum number of emails to display. Default is 5. |

## Example payload

```json
{
  "type": "gmail_summary",
  "query": "inbox is:unread"
}
```

Live page: https://a2uicatalog.ai/atoms/gmail_summary/
Full field contract: https://a2uicatalog.ai/spec.json
