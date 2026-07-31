# Social Feed Embed

Renders an embedded snippet of a social media post, such as a tweet

## Surfaces

web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| embed_code | string |
| platform | string |
| post_url | string |

## Example payload

```json
{
  "type": "social_feed_embed",
  "embed_code": "Embed code",
  "platform": "twitter",
  "post_url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/social_feed_embed/
Full field contract: https://a2uicatalog.ai/spec.json
