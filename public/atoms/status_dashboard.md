# Status Dashboard

Compact grid showing live operational status of multiple services with color indicators.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| metrics | array of {label, value, color}. Status entries. |

## Example payload

```json
{
  "type": "status_dashboard",
  "metrics": [
    {
      "label": "Revenue",
      "value": "$1.2M",
      "trend": "up"
    },
    {
      "label": "Users",
      "value": "42K",
      "trend": "up"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/status_dashboard/
Full field contract: https://a2uicatalog.ai/spec.json
