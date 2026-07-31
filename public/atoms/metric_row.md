# Metric Row

Horizontal strip of static metrics — value, label, optional prefix/suffix and trend indicator. Cleaner than animated_counter for non-animated use.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps

## Fields

| Field | Type |
|---|---|
| cols | integer (optional, default 4) |
| accent | string (optional, default hex for all metrics) |
| metrics | array (required, alias items). Each item: {value, label, prefix?, suffix?, sub?, accent?, trend? ("up"|"down")} |

## Example payload

```json
{
  "type": "metric_row",
  "metrics": [
    {
      "label": "Revenue",
      "value": "$1.2M",
      "trend": "up"
    },
    {
      "label": "Users",
      "value": "42K",
      "trend": "up"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/metric_row/
Full field contract: https://a2uicatalog.ai/spec.json
