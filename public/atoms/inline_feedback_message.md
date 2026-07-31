# Inline Feedback Message

A small, contextual message displayed inline with content, often used

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| message | string The feedback message text. |
| type | string The type of feedback (e.g., "success", "error", "warning", "info"). |
| icon | string Optional icon to display next to the message. |

## Example payload

```json
{
  "type": "info",
  "message": "Your action was completed successfully."
}
```

Live page: https://a2uicatalog.ai/atoms/inline_feedback_message/
Full field contract: https://a2uicatalog.ai/spec.json
