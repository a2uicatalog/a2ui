# Social Feed Embed

Renders an embedded snippet of a social media post, such as a tweet

## Surfaces

web, google-meet-stage, mcp-apps, android

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
