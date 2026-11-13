# Related Posts Grid

Displays a curated grid of preview cards for complementary reading material.

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
| posts | array. Objects containing title, url, and optional topic. |

## Example payload

```json
{
  "type": "related_posts_grid"
}
```

Live page: https://a2uicatalog.ai/atoms/related_posts_grid/
Full field contract: https://a2uicatalog.ai/spec.json
