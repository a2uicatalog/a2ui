# Embed Tweet

Displays a fully rendered standalone publication card containing Twitter status data.

## Surfaces

web, mcp-apps

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
