# Task List

Renders a premium, glassmorphic checklist and action item tracker with status checkboxes, priorities, assignees, and due dates.

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
| title | string (optional, e.g., 'Google Tasks & Action Items') |
| tasks | list of dictionaries representing tasks, where each dictionary contains: {'id': string, 'text': string, 'completed': boolean, 'priority': string (high|medium|low), 'due_date': string (optional), 'assignee': string (optional, initials e.g. 'CK')} |

## Example payload

```json
{
  "type": "task_list"
}
```

Live page: https://a2uicatalog.ai/atoms/task_list/
Full field contract: https://a2uicatalog.ai/spec.json
