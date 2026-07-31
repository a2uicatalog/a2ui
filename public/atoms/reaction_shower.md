# Reaction Shower

Emoji reaction buttons — tapping rains the emoji down the screen, with optional Sheet-backed totals

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| reactions | array of emoji strings (optional, default 🔥💡🤯👏) |
| write_url | string (optional, GAS doGet URL to record reactions) |
| sheet_url | string (optional, Google Sheet CSV for live counts) |
| poll | number (optional, poll interval ms) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "reaction_shower"
}
```

Live page: https://a2uicatalog.ai/atoms/reaction_shower/
Full field contract: https://a2uicatalog.ai/spec.json
