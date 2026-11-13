# Conversation Snippet

Renders a prompt-response pair as two chat bubbles — a user bubble on the right and an AI response bubble on the left. Ideal for showing LLM examples, chatbot flows, and agent interaction patterns in documentation.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
