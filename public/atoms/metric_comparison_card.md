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
