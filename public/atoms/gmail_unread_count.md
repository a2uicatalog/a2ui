# Gmail Unread Count

Unread message count badges for one or more Gmail labels, shown as a pill row. Zero counts are displayed in grey; non-zero in the accent colour.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| labels | array (optional). Gmail label names to count. Default ["INBOX"]. |
| title | string (optional). Card heading. Default is "Gmail". |
| accent | string (optional). Badge colour for non-zero counts. Default red. |
| counts | object (static connector). Label→count map for non-GAS surfaces. |
| auth_token | string (api connector). OAuth2 bearer token for REST API. |

## Example payload

```json
{
  "type": "gmail_unread_count",
  "counts": "42",
  "auth_token": "your-api-token"
}
```

Live page: https://a2uicatalog.ai/atoms/gmail_unread_count/
Full field contract: https://a2uicatalog.ai/spec.json
