# Status Dashboard

Compact grid showing live operational status of multiple services with color indicators.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Heading shown in the overall-status banner. |
| items | array of {name, status, description?}. status is one of operational | degraded | outage | maintenance; the banner rolls up to the worst status. |

## Example payload

```json
{
  "type": "status_dashboard",
  "items": 1
}
```

Live page: https://a2uicatalog.ai/atoms/status_dashboard/
Full field contract: https://a2uicatalog.ai/spec.json
