# Renderer Stats

Simple stat grid showing custom key/value pairs — used to show renderer capabilities

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| stats | array of {value, label} |
| sub | string (optional, footer note) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "renderer_stats",
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

Live page: https://a2uicatalog.ai/atoms/renderer_stats/
Full field contract: https://a2uicatalog.ai/spec.json
