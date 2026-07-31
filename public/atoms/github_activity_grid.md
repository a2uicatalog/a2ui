# Github Activity Grid

Renders a high-fidelity SVG representation of a GitHub-style contribution activity calendar with colored commitment density blocks, total contributions, and streak statistics.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'GitHub Repository Activity') |
| username | string (optional, e.g., 'curtiskrygier') |
| total_contributions | integer (optional, e.g., 342) |
| streak_days | integer (optional, e.g., 18) |
| activity | list of integers (0-4) or dictionary of weeks/days for rendering grid squares |

## Example payload

```json
{
  "type": "github_activity_grid",
  "activity": 1
}
```

Live page: https://a2uicatalog.ai/atoms/github_activity_grid/
Full field contract: https://a2uicatalog.ai/spec.json
