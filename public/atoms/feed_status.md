# Feed Status

Live-feed status pill — shows LIVE (n) or SIM based on data published to a named feed

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| name | string (feed name to subscribe to) |
| label | string (optional, text prefix in pill) |
| size | string (optional, CSS font-size, default 0.6rem) |

## Example payload

```json
{
  "type": "feed_status",
  "name": "Feed Status"
}
```

Live page: https://a2uicatalog.ai/atoms/feed_status/
Full field contract: https://a2uicatalog.ai/spec.json
