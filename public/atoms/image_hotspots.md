# Image Hotspots

Renders an image with interactive points that reveal information when clicked.

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
| hotspots | list of objects with label, x_position, y_position, content |

## Example payload

```json
{
  "type": "image_hotspots",
  "image_url": "https://example.com",
  "alt_text": "Descriptive alt text for accessibility",
  "hotspots": [
    {
      "x": 25,
      "y": 30,
      "label": "Feature A"
    },
    {
      "x": 60,
      "y": 70,
      "label": "Feature B"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/image_hotspots/
Full field contract: https://a2uicatalog.ai/spec.json
