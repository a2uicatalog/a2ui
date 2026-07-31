# Study Timer

Pomodoro-style focus/break countdown timer. Configurable focus and break durations. Animated SVG progress ring. Counts completed sessions. Session-scoped only — no persistence to progress_store.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional). Timer heading. Default "Study Timer". |
| focus_mins | integer (optional). Focus period in minutes. Default 25. |
| break_mins | integer (optional). Break period in minutes. Default 5. |
| accent | string (optional). Ring and mode label colour. Default |

## Example payload

```json
{
  "type": "study_timer"
}
```

Live page: https://a2uicatalog.ai/atoms/study_timer/
Full field contract: https://a2uicatalog.ai/spec.json
