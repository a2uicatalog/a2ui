# Pagination

A control for navigating through a series of pages or results.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
