# Cta Button

Full-width call-to-action button linking to a URL

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | contrast worse than React (dark 360); contrast worse than React (dark 480); pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| url | string |
| label | string |
| color | string (optional, hex) |
| same_tab | boolean (optional). Default false (opens in a NEW tab) — see link_button's same_tab for the full reasoning; same field, same default, same atom family. |

## Example payload

```json
{
  "type": "cta_button",
  "url": "https://example.com",
  "label": "Cta Button"
}
```

Live page: https://a2uicatalog.ai/atoms/cta_button/
Full field contract: https://a2uicatalog.ai/spec.json
