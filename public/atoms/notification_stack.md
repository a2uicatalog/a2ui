# Notification Stack

Persistent notification inbox showing a list of notification items, each with an icon or emoji, a title, a body snippet, a timestamp, and an optional unread indicator dot. Distinct from toast_notification which is a transient single pop-up — the stack is a persistent grouped list.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Heading above the list, e.g. "Notifications". |
| items | {'type': 'array', 'description': 'List of {icon?, title, body?, time?, unread?} entries. unread is boolean, default false.'} |

## Example payload

```json
{
  "type": "notification_stack"
}
```

Live page: https://a2uicatalog.ai/atoms/notification_stack/
Full field contract: https://a2uicatalog.ai/spec.json
