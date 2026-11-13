# Glass Card

Frosted-glass card with backdrop-filter blur. Use for dark-theme highlight boxes, callouts, or content wrappers. Content is raw HTML string.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | contrast worse than React (dark 360); contrast worse than React (dark 480); overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional). Card heading text. |
| content | string (optional). Inner HTML content of the card. |
| blur | integer (optional). Backdrop blur in px. Default 18. |
| bg | string (optional). Background colour (rgba). Default rgba(255,255,255,0.05). |
| border | string (optional). Border colour (rgba). Default rgba(255,255,255,0.1). |
| padding | string (optional). CSS padding. Default 28px. |
| radius | string (optional). Border radius. Default 16px. |

## Example payload

```json
{
  "type": "glass_card"
}
```

Live page: https://a2uicatalog.ai/atoms/glass_card/
Full field contract: https://a2uicatalog.ai/spec.json
