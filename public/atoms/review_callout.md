# Review Callout

Renders a short, impactful quote from a customer review, often accompanied

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| review_text | string |
| author_name | string |
| rating | number |
| max_rating | integer |
| product_name | string |

## Example payload

```json
{
  "type": "review_callout",
  "review_text": "Review text",
  "author_name": "Author Name",
  "rating": 75,
  "max_rating": 75,
  "product_name": "Product name"
}
```

Live page: https://a2uicatalog.ai/atoms/review_callout/
Full field contract: https://a2uicatalog.ai/spec.json
