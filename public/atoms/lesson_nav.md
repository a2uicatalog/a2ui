# Lesson Nav

Previous/next lesson navigation bar with the current lesson title centred and module context shown above. Each side shows the adjacent lesson title and a directional arrow. Optionally shows a completion checkbox for the current lesson that persists via localStorage.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| module_label | string (optional). Module or section name shown above the nav bar. |
| current_title | string. Title of the current lesson. |
| prev_title | string (optional). Title of the previous lesson. Omit to hide prev arrow. |
| prev_url | url (optional). Link for the previous lesson. |
| next_title | string (optional). Title of the next lesson. Omit to hide next arrow. |
| next_url | url (optional). Link for the next lesson. |
| show_completion | boolean (optional, default false). Show a "Mark as complete" checkbox persisted in localStorage. |

## Example payload

```json
{
  "type": "lesson_nav",
  "current_title": "Current title"
}
```

Live page: https://a2uicatalog.ai/atoms/lesson_nav/
Full field contract: https://a2uicatalog.ai/spec.json
