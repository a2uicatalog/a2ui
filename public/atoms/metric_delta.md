# Metric Delta

Renders a key performance indicator with its current value and a numerical

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (descriptive label for the metric, e.g., 'Sales') |
| current_value | string (the current formatted value, e.g., '$12,345') |
| delta_value | string (the formatted change value, e.g., '+$1,234' or '+10%') |
| delta_type | enum (increase, decrease, no_change) - determines icon/color |
| unit | string (optional, unit for the current value, e.g., 'USD') |
| previous_period_label | string (optional, e.g., 'vs. last month') |

## Example payload

```json
{
  "type": "metric_delta",
  "label": "Metric Delta",
  "current_value": "Current value",
  "delta_value": "Delta value",
  "delta_type": "increase"
}
```

Live page: https://a2uicatalog.ai/atoms/metric_delta/
Full field contract: https://a2uicatalog.ai/spec.json
