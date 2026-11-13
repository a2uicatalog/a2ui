# Pros Cons List

Renders a two-column list itemizing advantages and disadvantages for a single subject.

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
| subject | string |
| pros | array |
| cons | array |

## Example payload

```json
{
  "type": "pros_cons_list",
  "subject": "Example subject matter",
  "pros": [
    "Scalable architecture",
    "Clean API design",
    "Excellent documentation"
  ],
  "cons": [
    "Steeper learning curve",
    "Limited third-party plugins"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/pros_cons_list/
Full field contract: https://a2uicatalog.ai/spec.json
