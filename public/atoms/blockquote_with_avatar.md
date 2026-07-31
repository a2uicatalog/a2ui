# Blockquote With Avatar

Renders a blockquote with an associated avatar and attribution.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| quote | string (the quoted text) |
| author_name | string (name of the person quoted) |
| author_title | optional string (title or role of the person) |
| avatar_url | optional string (URL to the author's avatar image) |

## Example payload

```json
{
  "type": "blockquote_with_avatar",
  "quote": "The vocabulary IS the discovery layer.",
  "author_name": "Author Name"
}
```

Live page: https://a2uicatalog.ai/atoms/blockquote_with_avatar/
Full field contract: https://a2uicatalog.ai/spec.json
