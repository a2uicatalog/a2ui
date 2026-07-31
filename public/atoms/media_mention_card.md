# Media Mention Card

Renders a card showcasing a mention or feature in a media publication.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| publication_name | string |
| publication_logo_url | string |
| headline | string |
| article_url | string |
| date | string |

## Example payload

```json
{
  "type": "media_mention_card",
  "publication_name": "Publication name",
  "publication_logo_url": "https://example.com",
  "headline": "Main headline text here",
  "article_url": "https://example.com",
  "date": "2026-06-28"
}
```

Live page: https://a2uicatalog.ai/atoms/media_mention_card/
Full field contract: https://a2uicatalog.ai/spec.json
