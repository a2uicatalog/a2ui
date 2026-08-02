# Metric Comparison Card

Card comparing a current metric value against a previous period with delta indicator.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string. Metric name. |
| value | number. Current value. |
| previous | number. Previous period value. |
| lower_is_better | boolean (optional, default true). Which direction is GOOD, which decides whether the delta is green or red. Defaults to true because this card was written for response times; set false for traffic, revenue or any metric where a rise is the good outcome. |

## Example payload

```json
{
  "type": "metric_comparison_card",
  "label": "Metric Comparison Card",
  "value": 1,
  "previous": 1
}
```

Live page: https://a2uicatalog.ai/atoms/metric_comparison_card/
Full field contract: https://a2uicatalog.ai/spec.json
