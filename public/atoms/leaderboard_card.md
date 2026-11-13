# Leaderboard Card

Ranked learner leaderboard by score. On GAS reads live from the course progress Sheet via a2uiCohortRead, extracts scores for score_key, and ranks descending. On web renders from static items[]. Top 3 entries get gold/silver/bronze medal indicators. Per-row score bar visualises relative performance.

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
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| course_id | string (required). Matches progress_store course_id. |
| score_key | string (optional). Which quiz score to rank on. Default "quiz1". |
| limit | integer (optional). Max entries shown. Default 10. |
| title | string (optional). Card heading. Default "Leaderboard". |
| items | array (optional, web/static). Array of {name, score} objects for static rendering. |

## Example payload

```json
{
  "type": "leaderboard_card",
  "course_id": "course-101"
}
```

Live page: https://a2uicatalog.ai/atoms/leaderboard_card/
Full field contract: https://a2uicatalog.ai/spec.json
