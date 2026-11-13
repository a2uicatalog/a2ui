# Image

Single image with caption, hosted at a public URL

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| CopilotKit | Drawn with differences | 2026-11-13 | overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480) |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (light 360); pixels differ from React (light 480) |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| url | string |
| alt | string |
| caption | string (optional) |
| width | string (optional) |

## Example payload

```json
{
  "type": "image",
  "url": "https://example.com",
  "alt": "Descriptive alt text for this image"
}
```

Live page: https://a2uicatalog.ai/atoms/image/
Full field contract: https://a2uicatalog.ai/spec.json
