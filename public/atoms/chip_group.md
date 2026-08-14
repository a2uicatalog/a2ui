# Chip Group

Row of filter/tag chips, optionally scrollable. Chips can link to URLs and have active state.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional, group heading) |
| layout | string (optional, "wrap"|"scroll", default "wrap") |
| same_tab | bool (optional, default false). Chip links open in a new tab by default, which is right for OUTBOUND links from an embedded surface. Set this when the chips are navigation WITHIN one app — otherwise every tap leaves a tab behind, and four pages on a phone means four tabs. |
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
