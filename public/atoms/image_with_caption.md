# Image With Caption

Renders a single image with a descriptive caption below it.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | pixels differ from React (dark 480); pixels differ from React (light 480); content sits 1 px lower than in React (and than 1.85.0), stable between passes; cause not isolated. A real difference, not hidden |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| image_url | string |
| alt_text | string |
| caption | string |
| link_url | string |

## Example payload

```json
{
  "type": "image_with_caption",
  "image_url": "https://example.com",
  "alt_text": "Descriptive alt text for accessibility",
  "caption": "A descriptive caption",
  "link_url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/image_with_caption/
Full field contract: https://a2uicatalog.ai/spec.json
