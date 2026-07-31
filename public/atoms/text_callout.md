# Text Callout

Compact tinted note or tip block used inline within cards, forms, or panels. Lighter than callout — no left-border accent, no icon; just a soft colour-tinted background with a small bold title above body text. Adapted from the TextCallout pattern in OpenUI OUI benchmark samples.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| variant | string. Display variant — "info", "success", "warning", "neutral". |
| title | string. Short bold label (e.g. "Tip", "Note", "Good to know"). |
| description | string. Body text. |

## Example payload

```json
{
  "type": "text_callout",
  "variant": "primary",
  "title": "Text Callout",
  "description": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/text_callout/
Full field contract: https://a2uicatalog.ai/spec.json
