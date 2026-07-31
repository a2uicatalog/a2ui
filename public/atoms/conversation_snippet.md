# Conversation Snippet

Renders a prompt-response pair as two chat bubbles — a user bubble on the right and an AI response bubble on the left. Ideal for showing LLM examples, chatbot flows, and agent interaction patterns in documentation.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| user_label | string (optional, default "You"). Label above the user bubble. |
| user | string. The user prompt text. |
| ai_label | string (optional, default "Assistant"). Label above the AI bubble. |
| response | string. The AI response text. |
| accent | string (optional, default |

## Example payload

```json
{
  "type": "conversation_snippet",
  "user": "How does this work?",
  "response": "Here's a clear explanation of how it works."
}
```

Live page: https://a2uicatalog.ai/atoms/conversation_snippet/
Full field contract: https://a2uicatalog.ai/spec.json
