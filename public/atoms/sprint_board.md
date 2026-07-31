# Sprint Board

Atlassian Design System Jira-style sprint board rendered as kanban columns. Each column has a name, ticket-count badge, and compact issue cards (key, summary, type icon, priority dot). Distinct from prerequisite_checklist which is a linear checklist. Adapted from Atlassian Design System Board patterns.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| sprint_name | string (optional). Sprint label shown above the board. |
| columns | array. List of {name, items[]} where each item is {key, summary, type?, priority?}. |

## Example payload

```json
{
  "type": "sprint_board",
  "columns": [
    {
      "title": "To Do",
      "cards": []
    },
    {
      "title": "In Progress",
      "cards": []
    },
    {
      "title": "Done",
      "cards": []
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/sprint_board/
Full field contract: https://a2uicatalog.ai/spec.json
