# Live Demo Embed

Embeds a live interactive demo or sandbox within the article.

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
| url | string. URL of the live demo. |
| title | string (optional). Display title. |

## Example payload

```json
{
  "type": "live_demo_embed",
  "url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/live_demo_embed/
Full field contract: https://a2uicatalog.ai/spec.json
