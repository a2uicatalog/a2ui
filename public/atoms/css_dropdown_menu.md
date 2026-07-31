# Css Dropdown Menu

Renders a menu that appears when a trigger element is hovered or focused.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| trigger_text | string |
| menu_items | list of objects with label, url |

## Example payload

```json
{
  "type": "css_dropdown_menu",
  "trigger_text": "Click to trigger",
  "menu_items": [
    {
      "label": "Dashboard"
    },
    {
      "label": "Settings"
    },
    {
      "label": "Help"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/css_dropdown_menu/
Full field contract: https://a2uicatalog.ai/spec.json
