# Take Away Card

Bold single-insight pull-quote card designed to be screenshotted

## Surfaces

web, google-apps-script-web, mcp-apps

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
