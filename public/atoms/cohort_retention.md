# Cohort Retention

Renders a SaaS subscription or customer cohort retention triangular matrix with color-coded continuous gradients.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| cohorts | list of dictionaries representing cohorts (e.g., [{'cohort_name': 'Jan 2026', 'original_size': 2500, 'retention_rates': [100.0, 93.4]}]) |
| periods | list of strings representing period headers (e.g., ['Month 0', 'Month 1']) |
| color_scale | list of strings representing the continuous color scale (e.g., ['#1e293b', '#10b981']) |
| title | string (optional, chart title, e.g., 'SaaS Retention Cohorts') |

## Example payload

```json
{
  "type": "cohort_retention",
  "cohorts": [
    {
      "label": "Jan 2025",
      "data": [
        100,
        72,
        58,
        45
      ]
    },
    {
      "label": "Feb 2025",
      "data": [
        80,
        65,
        50,
        38
      ]
    }
  ],
  "periods": [
    "Week 1",
    "Week 2",
    "Week 3",
    "Week 4"
  ],
  "color_scale": [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/cohort_retention/
Full field contract: https://a2uicatalog.ai/spec.json
