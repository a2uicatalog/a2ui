# Chip Group

Row of filter/tag chips, optionally scrollable. Chips can link to URLs and have active state.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional, group heading) |
| layout | string (optional, "wrap"|"scroll", default "wrap") |
| chips | array (required). Array of {label, color? (hex), url? (href), active? (bool)} |

## Example payload

```json
{
  "type": "chip_group",
  "chips": true
}
```

Live page: https://a2uicatalog.ai/atoms/chip_group/
Full field contract: https://a2uicatalog.ai/spec.json
