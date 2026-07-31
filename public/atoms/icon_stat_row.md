# Icon Stat Row

Horizontal strip of stats each with a large emoji icon above the number and a label below. More visual than metric_row — use when icons reinforce meaning.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| cols | integer (optional, default 4) |
| accent | string (optional, default hex) |
| stats | array (required, alias items). Each: {icon (emoji), value, label, prefix?, suffix?, sub?, accent?} |

## Example payload

```json
{
  "type": "icon_stat_row",
  "stats": [
    {
      "label": "Views",
      "value": "1.2M"
    },
    {
      "label": "Clicks",
      "value": "42K"
    },
    {
      "label": "CTR",
      "value": "3.5%"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/icon_stat_row/
Full field contract: https://a2uicatalog.ai/spec.json
