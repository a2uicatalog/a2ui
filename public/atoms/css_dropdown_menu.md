# Css Dropdown Menu

Renders a menu that appears when a trigger element is hovered or focused.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
