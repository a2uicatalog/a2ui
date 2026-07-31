# Live Aggregator

Comparative progress-bar display for real-time vote/response data. Accepts an items array of label+value pairs and renders normalised horizontal bars with optional value labels. Designed for stage-first delivery where items update incrementally via fiber.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array of objects — label (string), value (number), color (optional hex). |
| title | string (optional). Section heading above the bars. |
| max_value | number (optional). Denominator for bar widths; auto-computed from max item value if omitted. |
| show_values | boolean (optional). Show numeric value next to each bar. Default true. |

## Example payload

```json
{
  "type": "live_aggregator"
}
```

Live page: https://a2uicatalog.ai/atoms/live_aggregator/
Full field contract: https://a2uicatalog.ai/spec.json
