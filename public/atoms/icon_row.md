# Icon Row

Horizontal strip of Material Symbol icon + label pairs. Good for feature/capability lists.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array of {name or icon, label or text, color?} |
| icon_size | px (default 20) |
| color | default icon colour (default var(--a2ui-accent)) |
| filled | filled icon variant (default false) |
| style | outlined (default) or rounded |
| gap | gap between items (default 12px) |

## Example payload

```json
{
  "type": "icon_row",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/icon_row/
Full field contract: https://a2uicatalog.ai/spec.json
