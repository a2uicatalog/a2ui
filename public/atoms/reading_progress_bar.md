# Reading Progress Bar

Renders a horizontal visual bar tracking the reader's scroll completion depth within the article.

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
| color | string. Hexadecimal or design utility color token for the bar. |

## Example payload

```json
{
  "type": "reading_progress_bar",
  "color": "#6366f1"
}
```

Live page: https://a2uicatalog.ai/atoms/reading_progress_bar/
Full field contract: https://a2uicatalog.ai/spec.json
