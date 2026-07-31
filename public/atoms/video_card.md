# Video Card

Renders a card with a video thumbnail, title, and description, linking

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
