# Linkedin Post Image

Renders a styled LinkedIn post image preview (conviction card, stat card, or carousel slide). Screenshot at 1.91:1 ratio for social sharing.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| mode | string (optional, "conviction_card"|"stat_card"|"carousel_slide", default "conviction_card") |
| accent | string (optional, hex, default "#7c3aed") |
| quote | string (conviction_card — main quote text) |
| attribution | string (conviction_card — author/source) |
| value | string (stat_card — big number) |
| label | string (stat_card — metric label) |
| title | string (carousel_slide — slide title) |
| body | string (carousel_slide — slide body) |

## Example payload

```json
{
  "type": "linkedin_post_image",
  "quote": "The vocabulary IS the discovery layer.",
  "attribution": "Source: Example Report, 2026",
  "value": 1,
  "label": "Linkedin Post Image",
  "title": "Linkedin Post Image",
  "body": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/linkedin_post_image/
Full field contract: https://a2uicatalog.ai/spec.json
