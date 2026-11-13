# Embed Google Slides

Renders an interactive presentation iframe viewer loading Google Slides resources.

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
| presentation_id | string. Asset identifier for the slide file. |

## Example payload

```json
{
  "type": "embed_google_slides",
  "presentation_id": "Presentation id"
}
```

Live page: https://a2uicatalog.ai/atoms/embed_google_slides/
Full field contract: https://a2uicatalog.ai/spec.json
