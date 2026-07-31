# Glass Card

Frosted-glass card with backdrop-filter blur. Use for dark-theme highlight boxes, callouts, or content wrappers. Content is raw HTML string.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Card heading text. |
| content | string (optional). Inner HTML content of the card. |
| blur | integer (optional). Backdrop blur in px. Default 18. |
| bg | string (optional). Background colour (rgba). Default rgba(255,255,255,0.05). |
| border | string (optional). Border colour (rgba). Default rgba(255,255,255,0.1). |
| padding | string (optional). CSS padding. Default 28px. |
| radius | string (optional). Border radius. Default 16px. |

## Example payload

```json
{
  "type": "glass_card"
}
```

Live page: https://a2uicatalog.ai/atoms/glass_card/
Full field contract: https://a2uicatalog.ai/spec.json
