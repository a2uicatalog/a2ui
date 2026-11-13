# Post Metadata Bar

Displays article metadata — author, publish date, read time, and optional tags — in a compact bar.

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
| author | string. Author display name. |
| date | string. Publish date (YYYY-MM-DD). |
| readTime | integer. Estimated read time in minutes. |

## Example payload

```json
{
  "type": "post_metadata_bar",
  "author": "Author Name",
  "date": "2026-06-28",
  "readTime": 75
}
```

Live page: https://a2uicatalog.ai/atoms/post_metadata_bar/
Full field contract: https://a2uicatalog.ai/spec.json
