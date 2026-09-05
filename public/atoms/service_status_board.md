# Service Status Board

Verdict-first service status board — a lead line naming the single most important thing (all-clear, or the one active disruption), followed by a two-column grid of every tracked service with its state encoded as shape + label + color (never color alone). Designed for any status feed (Google Workspace, an internal fleet, ServiceNow) reduced to name + state.

## Surfaces

google-chat-chromium-render

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'GOOGLE WORKSPACE — SERVICE STATUS') |
| stamp | string (optional, e.g., '19 JUL 2026 · 17:45 CET'). Right-aligned timestamp. |
| verdict | dict: {level: one of ok|warn|crit, text: string headline, detail: string (optional) supporting line} |
| services | list of dicts: [{name: string, state: one of operational|disruption|information|critical}, ...] |

## Example payload

```json
{
  "type": "service_status_board",
  "services": []
}
```

Live page: https://a2uicatalog.ai/atoms/service_status_board/
Full field contract: https://a2uicatalog.ai/spec.json
