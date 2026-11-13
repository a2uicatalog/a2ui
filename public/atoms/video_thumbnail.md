# Video Thumbnail

Renders a static image thumbnail for a video, with a play icon overlay

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| video_url | string |
| thumbnail_url | string |
| alt_text | string |
| title | string |

## Example payload

```json
{
  "type": "video_thumbnail",
  "video_url": "https://example.com",
  "thumbnail_url": "https://example.com",
  "alt_text": "Descriptive alt text for accessibility",
  "title": "Video Thumbnail"
}
```

Live page: https://a2uicatalog.ai/atoms/video_thumbnail/
Full field contract: https://a2uicatalog.ai/spec.json
