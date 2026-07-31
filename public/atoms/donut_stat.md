# Donut Stat

Renders a single key metric with a surrounding donut chart indicating

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| value | number (the current value, e.g., 75) |
| max_value | number (the maximum possible value, e.g., 100) |
| label | string (descriptive label for the metric, e.g., 'Completion') |
| unit | string (optional, unit for the value, e.g., '%') |
| color | string (hex or named color for the donut segment, e.g., '#2196F3') |
| size | string (CSS size value, e.g., '100px') |

## Example payload

```json
{
  "type": "donut_stat",
  "value": 75,
  "max_value": 5,
  "label": "Donut Stat",
  "color": "#6366f1",
  "size": "md"
}
```

Live page: https://a2uicatalog.ai/atoms/donut_stat/
Full field contract: https://a2uicatalog.ai/spec.json
