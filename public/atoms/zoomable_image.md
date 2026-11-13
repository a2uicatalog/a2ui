# Zoomable Image

Renders an image that magnifies when hovered over.

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
| image_url | string |
| alt_text | string |
| zoom_factor | float |

## Example payload

```json
{
  "type": "zoomable_image",
  "image_url": "https://example.com",
  "alt_text": "Descriptive alt text for accessibility",
  "zoom_factor": "Zoom factor"
}
```

Live page: https://a2uicatalog.ai/atoms/zoomable_image/
Full field contract: https://a2uicatalog.ai/spec.json
