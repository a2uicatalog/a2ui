# Search Result Card

Styled card displaying a single search result with title, snippet, and URL.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| title | string. Result title. |
| description | string. Snippet text. |
| url | string (optional). Result URL. |

## Example payload

```json
{
  "type": "search_result_card",
  "title": "Search Result Card",
  "description": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/search_result_card/
Full field contract: https://a2uicatalog.ai/spec.json
