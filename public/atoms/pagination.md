# Pagination

A control for navigating through a series of pages or results.

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
| current_page | integer |
| total_pages | integer |
| base_url | string (the URL prefix for all page links) |
| page_param | string (e.g., 'page', the query parameter name for the page number) |

## Example payload

```json
{
  "type": "pagination",
  "current_page": 2,
  "total_pages": 5,
  "base_url": "https://example.com",
  "page_param": 1
}
```

Live page: https://a2uicatalog.ai/atoms/pagination/
Full field contract: https://a2uicatalog.ai/spec.json
