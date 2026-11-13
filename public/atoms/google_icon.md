# Google Icon

A single Material Symbol icon from Google Fonts CDN. Browse 2500+ icon names at fonts.google.com/icons.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| name | icon ligature name (required, e.g. "home", "check_circle", "rocket_launch") |
| size | font-size CSS value (default 24px) |
| color | icon colour (default currentColor) |
| filled | render the filled variant (default false — outlined) |
| weight | font weight 100-700 (default 400) |
| style | outlined (default) or rounded |
| label | optional text beside the icon |
| inline | render inline-flex (default true) |

## Example payload

```json
{
  "type": "google_icon",
  "name": "Google Icon"
}
```

Live page: https://a2uicatalog.ai/atoms/google_icon/
Full field contract: https://a2uicatalog.ai/spec.json
