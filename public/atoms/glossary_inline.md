# Glossary Inline

Renders a specialised inline element displaying technical term definitions on hover.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| term | string. The technical phrase needing definition. |
| definition | string. Explanation displayed when term is activated. |

## Example payload

```json
{
  "type": "glossary_inline",
  "term": "API",
  "definition": "Application Programming Interface"
}
```

Live page: https://a2uicatalog.ai/atoms/glossary_inline/
Full field contract: https://a2uicatalog.ai/spec.json
