# Encrypted Reveal

Text that appears to scramble through random alphanumeric characters before locking into the final readable string. Implemented entirely in CSS using a steps() @keyframes animation cycling through server-side pre-generated scrambled frames — no JavaScript required.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. The final text to reveal. |
| size | string (optional). Font size e.g. "32px". Default "28px". |
| weight | string (optional). Font weight. Default "700". |
| color | string (optional). Text colour. Default "#f1f5f9". |
| scramble_color | string (optional). Colour of scramble characters. Default "#38bdf8". |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| delay | string (optional). CSS delay before reveal starts. Default "0s". |
| frames | integer (optional). Number of scramble frames before lock. Default 8. |
| background | string (optional). Container background. Default transparent. |

## Example payload

```json
{
  "type": "encrypted_reveal",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/encrypted_reveal/
Full field contract: https://a2uicatalog.ai/spec.json
