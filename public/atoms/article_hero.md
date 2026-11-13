# Article Hero

Renders a prominent visual header displaying title, metadata, and background cover imagery.

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string. Main showcase headline text. |
| subtitle | string. Optional accompanying summary text. |
| image_url | string. URL to header background media. |

## Example payload

```json
{
  "type": "article_hero",
  "title": "Article Hero",
  "image_url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/article_hero/
Full field contract: https://a2uicatalog.ai/spec.json
