# Icon Checklist

Checklist where each item has a Material Symbol icon (not just a check mark). Good for capability or requirements lists.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | optional heading |
| default_icon | fallback icon for items without one (default check_circle) |
| icon_size | px (default 20) |
| filled | filled icon variant (default true) |
| accent | default icon colour |
| items | array of strings or {text, icon?, sublabel?, color?} |

## Example payload

```json
{
  "type": "icon_checklist",
  "items": [
    {
      "label": "First item"
    },
    {
      "label": "Second item"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/icon_checklist/
Full field contract: https://a2uicatalog.ai/spec.json
