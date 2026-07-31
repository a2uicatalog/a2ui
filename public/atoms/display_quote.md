# Display Quote

Large typographic quote with a decorative quotation mark at 5rem, quote body in italic, and optional attribution line. Dark-native, great for Meet Stage title slides.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. Quote body text. |
| attribution | string (optional). Name or source shown below quote. |
| colour | string (optional). Accent colour for mark and attribution. Default |
| size | string (optional). Font-size for quote text. Default clamp(1.4rem,3vw,2.2rem). |
| align | string (optional). center or left. Default center. |

## Example payload

```json
{
  "type": "display_quote",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/display_quote/
Full field contract: https://a2uicatalog.ai/spec.json
