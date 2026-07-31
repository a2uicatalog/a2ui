# Two Tone Card

Card with a solid colored header section (title, subtitle, icon) and a white body that renders atom blocks. Clean, elegant container for any content.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (required) |
| subtitle | string (optional) |
| icon | string (optional, emoji) |
| accent | string (optional, hex, default "#6366f1") |
| header_theme | string (optional, "light"|"dark", default "light") |
| blocks | array (optional, atom blocks rendered in white body) |

## Example payload

```json
{
  "type": "two_tone_card",
  "title": "Two Tone Card"
}
```

Live page: https://a2uicatalog.ai/atoms/two_tone_card/
Full field contract: https://a2uicatalog.ai/spec.json
