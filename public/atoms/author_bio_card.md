# Author Bio Card

Renders a profile section containing the creator's avatar, bio, and links.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | string. Full name of the content creator. |
| avatar_url | string. URL to the profile image. |
| bio | string. Short narrative profiling the writer. |
| links | object. Optional key-value pairs of platform names and URLs. |

## Example payload

```json
{
  "type": "author_bio_card",
  "name": "Author Bio Card",
  "avatar_url": "https://example.com",
  "bio": "Short author biography goes here."
}
```

Live page: https://a2uicatalog.ai/atoms/author_bio_card/
Full field contract: https://a2uicatalog.ai/spec.json
