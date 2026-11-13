# Gallery

Responsive image grid with CSS-only lightbox on click

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (light 360) |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| cols | 2 | 3 | 4 (optional, default 3) |
| caption | string (optional) |
| images | [{'url': 'string', 'alt': 'string', 'caption': 'string (optional)'}] |

## Example payload

```json
{
  "type": "gallery"
}
```

Live page: https://a2uicatalog.ai/atoms/gallery/
Full field contract: https://a2uicatalog.ai/spec.json
