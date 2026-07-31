# Gauge Sla

Renders a semi-circular radial gauge track with high contrast status quadrants, a glowing needle tick, and a prominent central KPI readout.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'API Response SLA') |
| value | number representing current value (e.g., 99.4) |
| max_value | number representing maximum gauge scale (e.g., 100) |
| unit | string (optional, e.g., '%') |
| label | string (optional, e.g., 'SLA Met') |

## Example payload

```json
{
  "type": "gauge_sla",
  "value": 75,
  "max_value": 5
}
```

Live page: https://a2uicatalog.ai/atoms/gauge_sla/
Full field contract: https://a2uicatalog.ai/spec.json
