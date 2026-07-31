# Series Overview Card

Renders a navigation box indexing all parts within a multi-part article series.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| series_name | string. Name of the series. |
| parts | array. Objects with title, url, and optional current boolean. |

## Example payload

```json
{
  "type": "series_overview_card",
  "series_name": "Series name"
}
```

Live page: https://a2uicatalog.ai/atoms/series_overview_card/
Full field contract: https://a2uicatalog.ai/spec.json
