# Testimonial Card

Renders a single customer testimonial with text, author details, and

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string |
| author_name | string |
| author_title | string |
| author_avatar_url | string |
| rating | integer |

## Example payload

```json
{
  "type": "testimonial_card",
  "text": "A concise description of the content.",
  "author_name": "Author Name",
  "author_title": "Author title",
  "author_avatar_url": "https://example.com",
  "rating": 75
}
```

Live page: https://a2uicatalog.ai/atoms/testimonial_card/
Full field contract: https://a2uicatalog.ai/spec.json
