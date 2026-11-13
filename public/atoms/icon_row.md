# Icon Row

Horizontal strip of Material Symbol icon + label pairs. Good for feature/capability lists.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Angular | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
