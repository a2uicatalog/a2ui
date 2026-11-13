# Glossary Term

Renders a term with its definition, often with an optional link for more details.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| term | string (the term itself) |
| definition | string (the explanation) |
| link_text | optional string (e.g., "Learn more") |
| link_url | optional string (URL for more details) |

## Example payload

```json
{
  "type": "glossary_term",
  "term": "API",
  "definition": "Application Programming Interface"
}
```

Live page: https://a2uicatalog.ai/atoms/glossary_term/
Full field contract: https://a2uicatalog.ai/spec.json
