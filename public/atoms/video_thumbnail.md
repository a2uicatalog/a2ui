# Video Thumbnail

Renders a static image thumbnail for a video, with a play icon overlay

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
