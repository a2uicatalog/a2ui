# Alert Banner

A prominent banner displaying a message, often with an icon and an

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| message | string The main message to display in the banner. |
| type | string The type of alert (e.g., "info", "warning", "error", "success"). |
| icon | string Optional icon name to display next to the message. |
| action_label | string Optional text for an action button. |
| action_url | string Optional URL for the action button. |

## Example payload

```json
{
  "type": "info",
  "message": "Your action was completed successfully."
}
```

Live page: https://a2uicatalog.ai/atoms/alert_banner/
Full field contract: https://a2uicatalog.ai/spec.json
