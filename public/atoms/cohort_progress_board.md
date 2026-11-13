# Cohort Progress Board

Instructor-facing table showing all enrolled learners with per-module completion ticks and average quiz scores. On GAS reads live from the course progress Sheet via a2uiCohortRead. On web renders from static items[] array. Shows enrolled and active learner counts at top.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| course_id | string (required). Matches the progress_store course_id. |
| title | string (optional). Board heading. Default "Cohort Progress". |
| modules | array (optional). Array of {id, label} for column headers. Drives per-module completion dots. |
| items | array (optional, web/static). Array of {email, progress{}, updated_at} learner objects. |

## Example payload

```json
{
  "type": "cohort_progress_board",
  "course_id": "course-101"
}
```

Live page: https://a2uicatalog.ai/atoms/cohort_progress_board/
Full field contract: https://a2uicatalog.ai/spec.json
