# Word Cloud

Interactive word cloud — static words or live Google Sheets feed with submit input

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| words | array of {text, weight} (optional static words) |
| palette | array of hex strings (optional, word colours) |
| placeholder | string (optional, input placeholder) |
| accent | string (optional, hex accent for input bar) |
| sheet_url | string (optional, Google Sheet CSV URL for live words) |
| write_url | string (optional, GAS doGet URL to write submissions) |
| poll | number (optional, poll interval seconds) |

## Example payload

```json
{
  "type": "word_cloud"
}
```

Live page: https://a2uicatalog.ai/atoms/word_cloud/
Full field contract: https://a2uicatalog.ai/spec.json
