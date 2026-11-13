# Document Link

Renders a clickable link to a document (e.g., PDF, DOCX), often with a document icon.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android

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
| document_url | string |
| label | string |
| icon_type | string |

## Example payload

```json
{
  "type": "document_link",
  "document_url": "https://example.com",
  "label": "Document Link",
  "icon_type": "star"
}
```

Live page: https://a2uicatalog.ai/atoms/document_link/
Full field contract: https://a2uicatalog.ai/spec.json
