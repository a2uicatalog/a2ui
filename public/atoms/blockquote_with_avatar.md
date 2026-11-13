# Blockquote With Avatar

Renders a blockquote with an associated avatar and attribution.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
