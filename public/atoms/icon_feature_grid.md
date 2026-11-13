# Icon Feature Grid

Feature grid using Material Symbol icons — better than emoji for Workspace UI contexts.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | optional section heading |
| cols | grid columns (default 3) |
| icon_size | icon size in px (default 28) |
| filled | filled icon variant (default false) |
| accent | default icon colour |
| style | outlined (default) or rounded |
| items | array of {icon (ligature name), title, text, color?} |

## Example payload

```json
{
  "type": "icon_feature_grid",
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

Live page: https://a2uicatalog.ai/atoms/icon_feature_grid/
Full field contract: https://a2uicatalog.ai/spec.json
