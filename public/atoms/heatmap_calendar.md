# Heatmap Calendar

IBM Carbon-inspired calendar heatmap showing activity density by date across one or more calendar months. Data is a list of date-value pairs; cells are coloured by intensity across a configurable colour scale. Distinct from heatmap (arbitrary x/y grid) and github_activity_grid (year-spanning GitHub-specific format). Adapted from IBM Carbon AI Applications data visualisation patterns.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android

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
| title | string (optional). Heading above the calendar grid. |
| data | array. List of {date, count} objects where date is "YYYY-MM-DD". |
| months | integer (optional). Number of calendar months to render. Default 3. |
| color_scale | array of strings (optional). CSS colours from empty to maximum density. Default IBM Carbon blue scale. |
| unit | string (optional). Unit label appended to count in tooltips, e.g. "commits". |

## Example payload

```json
{
  "type": "heatmap_calendar",
  "data": [
    {
      "date": "2026-06-01",
      "value": 5
    },
    {
      "date": "2026-06-15",
      "value": 12
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/heatmap_calendar/
Full field contract: https://a2uicatalog.ai/spec.json
