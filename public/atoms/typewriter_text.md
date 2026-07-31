# Typewriter Text

Text that animates itself character by character using a CSS steps() width animation on a monospace element. A blinking cursor is included by default. Useful for hero hooks, slide reveals, and LLM demo showcases. No JavaScript required.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. The text to type out. |
| size | string (optional). Font size e.g. "32px". Default "28px". |
| weight | string (optional). Font weight e.g. "700". Default "700". |
| color | string (optional). Text colour. Default "#1a1a1a". |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| cursor | bool (optional). Show blinking cursor. Default true. |
| delay | string (optional). CSS delay before typing starts. Default "0s". |

## Example payload

```json
{
  "type": "typewriter_text",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/typewriter_text/
Full field contract: https://a2uicatalog.ai/spec.json
