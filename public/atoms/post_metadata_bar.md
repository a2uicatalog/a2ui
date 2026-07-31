# Post Metadata Bar

Displays article metadata — author, publish date, read time, and optional tags — in a compact bar.

## Surfaces

web, google-apps-script-web, mcp-apps

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
