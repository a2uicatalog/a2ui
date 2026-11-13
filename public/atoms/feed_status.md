# Feed Status

Live-feed status pill — shows LIVE (n) or SIM based on data published to a named feed

## Surfaces

google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
