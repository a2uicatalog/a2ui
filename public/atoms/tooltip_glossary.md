# Tooltip Glossary

Glossary list where hovering a term shows its definition as a tooltip

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
| terms | array of {term, definition} |
| text | string (optional, introductory prose, alias: intro) |

## Example payload

```json
{
  "type": "tooltip_glossary",
  "terms": [
    {
      "term": "API",
      "definition": "Application Programming Interface"
    },
    {
      "term": "A2UI",
      "definition": "Adaptive Atom-based UI"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/tooltip_glossary/
Full field contract: https://a2uicatalog.ai/spec.json
