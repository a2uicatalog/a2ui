# Text Highlight

Inline prose sentence where specific words are highlighted in an accent colour. Mark words with **double asterisks** in the text field — highlighted words are wrapped in a styled span.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string. Body text with **highlighted** words wrapped in double asterisks. |
| size | string (optional). Font-size. Default 1.2rem. |
| colour | string (optional). Highlight colour. Default |
| weight | integer (optional). Base font weight. Default 600. |
| align | string (optional). text-align. Default left. |

## Example payload

```json
{
  "type": "text_highlight",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/text_highlight/
Full field contract: https://a2uicatalog.ai/spec.json
