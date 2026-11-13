# Sheet Stats

Aggregate statistics (sum, average, count, min, max) computed from a Google Sheet range and displayed as a row of stat badges. Ideal for dashboards.

## Surfaces

google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| spreadsheet_id | string. The Google Sheets ID. |
| sheet_name | string (optional). Sheet tab name. |
| range | string. A1 notation range (e.g. B2:B50). |
| label | string (optional). Card heading. Default is "Sheet Stats". |
| show | array (optional). Which stats to show — any of sum, average, count, min, max. Default ["sum","average","count"]. |
| accent | string (optional). Accent colour for stat values. |

## Example payload

```json
{
  "type": "sheet_stats",
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
  "range": "A1:D10"
}
```

Live page: https://a2uicatalog.ai/atoms/sheet_stats/
Full field contract: https://a2uicatalog.ai/spec.json
