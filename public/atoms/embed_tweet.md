# Embed Tweet

Displays a fully rendered standalone publication card containing Twitter status data.

## Surfaces

web, mcp-apps, android

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
| tweet_id | string. Unique snowflake identifier for the post. |

## Example payload

```json
{
  "type": "embed_tweet",
  "tweet_id": "Tweet id"
}
```

Live page: https://a2uicatalog.ai/atoms/embed_tweet/
Full field contract: https://a2uicatalog.ai/spec.json
