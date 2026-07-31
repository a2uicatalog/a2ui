# Article Series Nav

Renders an organized multi-part sequence navigation panel mapping serial publication installments.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| series_id | string. Unique identifier of the series cluster. |
| current_part | integer. Ordered index within series limits. |

## Example payload

```json
{
  "type": "article_series_nav",
  "series_id": "Series id",
  "current_part": 2
}
```

Live page: https://a2uicatalog.ai/atoms/article_series_nav/
Full field contract: https://a2uicatalog.ai/spec.json
