# Image With Caption

Renders a single image with a descriptive caption below it.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

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
