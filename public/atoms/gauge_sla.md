# Gauge Sla

Renders a semi-circular radial gauge track with high contrast status quadrants, a glowing needle tick, and a prominent central KPI readout.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'API Response SLA') |
| value | number representing current value (e.g., 99.4) |
| max_value | number representing maximum gauge scale (e.g., 100) |
| unit | string (optional, e.g., '%') |
| label | string (optional, e.g., 'SLA Met') |
| min | number (optional, default 0). Setting min or steps switches to the scale mode (Plotly indicator gauge) with bands, a threshold tick, a needle, a legend and a hidden table. |
| steps | list (optional) of {from, to, color} bands on the scale (up to 8); color is a hex or var(--token), default theme colours; each band is also listed in text. |
| threshold | number (optional). Draws a tick and states whether the value is at or above it (scale mode only). |
| version | integer (optional, default 1). A whole number above 1 draws as version 1 with a muted note (scale mode only). |

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
