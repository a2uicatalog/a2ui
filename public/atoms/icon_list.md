# Icon List

List of items each with a colored icon circle, label, and text. More visual than bullet_list. Use for feature lists, how-it-works, benefits.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android, slides, pptx

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
| title | string (optional) |
| accent | string (optional, default hex for all items) |
| size | string (optional, "sm"|"md"|"lg", default "md") |
| items | array (required). Array of {icon (emoji), label (optional), text (optional), color (optional hex)} |

## Example payload

```json
{
  "type": "icon_list"
}
```

Live page: https://a2uicatalog.ai/atoms/icon_list/
Full field contract: https://a2uicatalog.ai/spec.json
