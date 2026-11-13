# Jira Ticket

Atlassian Design System Jira issue card showing issue key, type icon (bug/story/task/epic/subtask), one-line summary, status lozenge, priority indicator, assignee, optional description, and label chips. Adapted from Atlassian Design System Card + Lozenge patterns.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| key | string. Issue key, e.g. "PROJ-123". |
| issue_type | string (optional). One of bug | story | task | epic | subtask. Default task. |
| summary | string. Issue title or one-line description. |
| status | string (optional). Column name e.g. "To Do", "In Progress", "Done". |
| priority | string (optional). One of highest | high | medium | low | lowest. |
| assignee | string (optional). Assignee display name. |
| description | string (optional). Short description or acceptance criteria. |
| labels | array of strings (optional). Label chips shown below the description. |

## Example payload

```json
{
  "type": "jira_ticket",
  "key": "example-id",
  "summary": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/jira_ticket/
Full field contract: https://a2uicatalog.ai/spec.json
