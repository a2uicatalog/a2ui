# Xp Bar

Experience points or gamification progress bar showing current XP, level label, and XP needed to reach the next level. The fill animates from the previous value to the current value on render via CSS transition. A level-up flash overlay triggers when xp_current equals or exceeds xp_next.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| level_label | string. Current level name e.g. "Level 3 — Intermediate". |
| xp_current | integer. Current XP within the current level. |
| xp_next | integer. XP required to reach the next level. |
| accent | string (optional). Bar fill colour. Default "#6366f1". |
| show_flash | boolean (optional, default true). Trigger level-up flash when xp_current >= xp_next. |

## Example payload

```json
{
  "type": "xp_bar",
  "level_label": 75,
  "xp_current": 2,
  "xp_next": 75
}
```

Live page: https://a2uicatalog.ai/atoms/xp_bar/
Full field contract: https://a2uicatalog.ai/spec.json
