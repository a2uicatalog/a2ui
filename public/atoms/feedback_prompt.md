# Feedback Prompt

In-context feedback collection widget for rating content or AI response quality. Supports thumbs up/down or 1–5 star ratings with optional follow-up text. Inspired by Vercel Geist Feedback pattern.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| question | string (optional). Label text above the widget. e.g. "Was this helpful?" |
| style | string (optional). One of: thumbs | stars. Default: thumbs. |
| placeholder | string (optional). Follow-up textarea placeholder shown after the rating buttons. |
| action_url | string (optional). Endpoint for form POST on submit. |

## Example payload

```json
{
  "type": "feedback_prompt"
}
```

Live page: https://a2uicatalog.ai/atoms/feedback_prompt/
Full field contract: https://a2uicatalog.ai/spec.json
