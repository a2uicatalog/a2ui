# Typewriter

Text that reveals itself character-by-character using a CSS steps() width animation on an overflow-hidden monospace container, with an optional blinking cursor. No JavaScript required.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. The text to type out. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| cursor | bool (optional). Show blinking cursor after typing. Default true. |
| color | string (optional). Text colour. Default "#0f172a". |
| size | string (optional). Font size e.g. "1.4rem". Default "1.4rem". |
| weight | string (optional). Font weight. Default "600". |
| background | string (optional). Container background. Default "#f8fafc". |

## Example payload

```json
{
  "type": "typewriter",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/typewriter/
Full field contract: https://a2uicatalog.ai/spec.json
