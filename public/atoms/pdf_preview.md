# Pdf Preview

Renders an image thumbnail of a PDF document with a link to the full

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| pdf_url | string |
| thumbnail_url | string |
| title | string |
| alt_text | string |

## Example payload

```json
{
  "type": "pdf_preview",
  "pdf_url": "https://example.com",
  "thumbnail_url": "https://example.com",
  "title": "Pdf Preview",
  "alt_text": "Descriptive alt text for accessibility"
}
```

Live page: https://a2uicatalog.ai/atoms/pdf_preview/
Full field contract: https://a2uicatalog.ai/spec.json
