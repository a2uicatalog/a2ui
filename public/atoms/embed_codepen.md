# Embed Codepen

Renders an embedded interactive CodePen sandbox workspace within the document.

## Surfaces

web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| pen_id | string. Alphanumeric identity of the target snippet. |
| user_handle | string. Profile handle owning the snippet. |

## Example payload

```json
{
  "type": "embed_codepen",
  "pen_id": "Pen id",
  "user_handle": "User handle"
}
```

Live page: https://a2uicatalog.ai/atoms/embed_codepen/
Full field contract: https://a2uicatalog.ai/spec.json
