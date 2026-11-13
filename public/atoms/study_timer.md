# Study Timer

Pomodoro-style focus/break countdown timer. Configurable focus and break durations. Animated SVG progress ring. Counts completed sessions. Session-scoped only — no persistence to progress_store.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
