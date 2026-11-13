# Punch Card

Renders a Day-of-Week vs. Hour-of-Day bubble grid (punch card) of repository or commit activity, where bubble size is proportional to activity.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| data | list of lists of numbers (7 rows representing days of week, each containing 24 numbers representing commit frequency for each hour) |
| labels_days | list of strings (optional, e.g., ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']) |
| color | string (optional, hex or named color for active bubbles, e.g., '#00f2ff') |
| title | string (optional, title of the repository or chart, e.g., 'Commit Activity') |
| subtitle | string (optional, subtitle, e.g., 'curtiskrygier/meetstudio') |

## Example payload

```json
{
  "type": "punch_card",
  "data": 1
}
```

Live page: https://a2uicatalog.ai/atoms/punch_card/
Full field contract: https://a2uicatalog.ai/spec.json
