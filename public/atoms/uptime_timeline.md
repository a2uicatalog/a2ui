# Uptime Timeline

Visual timeline of service uptime over a rolling window with per-day status blocks.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| uptime | number. Uptime percentage (0–100). |

## Example payload

```json
{
  "type": "uptime_timeline",
  "uptime": 1
}
```

Live page: https://a2uicatalog.ai/atoms/uptime_timeline/
Full field contract: https://a2uicatalog.ai/spec.json
