# Take Away Card

Bold single-insight pull-quote card designed to be screenshotted

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| headline | string (alias: text, quote, insight) |
| sub | string (optional, attribution/source, alias: author, source) |
| accent | string (optional, hex) |
| size | string (optional, CSS font-size) |
| gradient | array of 2 hex strings (optional, background gradient colours) |

## Example payload

```json
{
  "type": "take_away_card",
  "headline": "Main headline text here"
}
```

Live page: https://a2uicatalog.ai/atoms/take_away_card/
Full field contract: https://a2uicatalog.ai/spec.json
