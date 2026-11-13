# Footnote

Renders a numbered footnote reference and its corresponding text, typically

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
| number | integer (the footnote number) |
| text | string (the footnote content) |
| id | string (unique identifier for linking, e.g., "fn1") |

## Example payload

```json
{
  "type": "footnote",
  "number": 1,
  "text": "A concise description of the content.",
  "id": "example-id"
}
```

Live page: https://a2uicatalog.ai/atoms/footnote/
Full field contract: https://a2uicatalog.ai/spec.json
