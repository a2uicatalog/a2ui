# Star Rating Display

Renders a visual representation of a star rating, optionally with a total review count.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| rating | number |
| max_rating | integer |
| review_count | integer |

## Example payload

```json
{
  "type": "star_rating_display",
  "rating": 75,
  "max_rating": 75,
  "review_count": 1
}
```

Live page: https://a2uicatalog.ai/atoms/star_rating_display/
Full field contract: https://a2uicatalog.ai/spec.json
