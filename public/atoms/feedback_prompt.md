# Feedback Prompt

In-context feedback collection widget for rating content or AI response quality. Supports thumbs up/down or 1–5 star ratings with optional follow-up text. Inspired by Vercel Geist Feedback pattern.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
