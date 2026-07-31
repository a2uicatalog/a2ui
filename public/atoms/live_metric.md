# Live Metric

Animated counter that counts up from start to a target value — alias for animated_counter

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| value | number (alias: end) |
| start | number (optional) |
| duration | number (optional, seconds) |
| prefix | string (optional) |
| suffix | string (optional) |
| label | string (optional) |
| decimals | integer (optional) |

## Example payload

```json
{
  "type": "live_metric",
  "value": 1
}
```

Live page: https://a2uicatalog.ai/atoms/live_metric/
Full field contract: https://a2uicatalog.ai/spec.json
