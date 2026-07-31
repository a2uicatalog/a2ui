# Word Scramble

Text that begins as a stream of random alphanumeric characters and progressively resolves left-to-right into the final string using CSS @keyframes content with steps(). Pure CSS — no JavaScript. Each frame pre-generates a partially-revealed scramble via Python at render time.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. The final text to reveal. |
| duration | number (optional). Total animation duration in seconds. Default 2.0. |
| color | string (optional). Final text colour. Default "#0f172a". |
| scramble_color | string (optional). Scramble character colour. Default "#4f46e5". |
| size | string (optional). Font size. Default "2.5rem". |
| weight | string (optional). Font weight. Default "800". |

## Example payload

```json
{
  "type": "word_scramble",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/word_scramble/
Full field contract: https://a2uicatalog.ai/spec.json
