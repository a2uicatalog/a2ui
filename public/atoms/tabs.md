# Tabs

CSS-only tabbed panels — ideal for multi-language code examples

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| accent | string (optional) |
| tabs | [{'label': 'string', 'language': 'string', 'content': 'string'}] |

## Example payload

```json
{
  "type": "tabs",
  "tabs": [
    {
      "label": "Tab 1",
      "content": "Content one."
    },
    {
      "label": "Tab 2",
      "content": "Content two."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/tabs/
Full field contract: https://a2uicatalog.ai/spec.json
