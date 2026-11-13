# Icon Checklist

Checklist where each item has a Material Symbol icon (not just a check mark). Good for capability or requirements lists.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
