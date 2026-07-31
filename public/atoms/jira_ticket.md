# Jira Ticket

Atlassian Design System Jira issue card showing issue key, type icon (bug/story/task/epic/subtask), one-line summary, status lozenge, priority indicator, assignee, optional description, and label chips. Adapted from Atlassian Design System Card + Lozenge patterns.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

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
