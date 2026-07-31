# Achievement Badge

Unlockable achievement or completion badge displayed as a circular icon with a title, description, and optional unlock date. Locked state shows a greyscale padlock overlay. Suitable for course completion, streak milestones, and skill certifications. Renders as a centred card or inline pill depending on size variant.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string. Achievement name. |
| description | string (optional). Short achievement description. |
| icon | string (optional). Emoji or single character used as the badge icon. Default "🏆". |
| locked | boolean (optional, default false). Shows greyscale padlock overlay when true. |
| unlocked_at | string (optional). ISO date string shown beneath the badge when unlocked. |
| color | string (optional). Badge accent colour. Default "#f59e0b". |
| size | "card" | "pill"  (optional, default "card") |

## Example payload

```json
{
  "type": "achievement_badge",
  "title": "Achievement Badge"
}
```

Live page: https://a2uicatalog.ai/atoms/achievement_badge/
Full field contract: https://a2uicatalog.ai/spec.json
