# Gmail Summary

Summary list of recent emails in the user's Gmail matching a search query. Works on Google Apps Script only.

## Surfaces

google-apps-script-web, mcp-apps

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
