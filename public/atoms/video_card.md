# Video Card

Renders a card with a video thumbnail, title, and description, linking

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn with differences | 2026-11-13 | overflows at 360 px; pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React |
| a2ui-vue | Drawn with differences | 2026-11-13 | pixels differ from React (dark 360); pixels differ from React (dark 480); pixels differ from React (light 360); pixels differ from React (light 480); visible text differs from React |
| Flutter | Degraded | 2026-11-13 | lowered to Basic components |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| video_url | string |
| thumbnail_url | string |
| title | string |
| description | string |
| alt_text | string |

## Example payload

```json
{
  "type": "video_card",
  "video_url": "https://example.com",
  "thumbnail_url": "https://example.com",
  "title": "Video Card",
  "description": "A concise description of the content.",
  "alt_text": "Descriptive alt text for accessibility"
}
```

Live page: https://a2uicatalog.ai/atoms/video_card/
Full field contract: https://a2uicatalog.ai/spec.json
