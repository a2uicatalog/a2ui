# Product Thumbnail

Shopify Polaris-style product card showing optional image, title, vendor, SKU, price with optional compare-at strike-through, status badge, and tag chips. Adapted from Polaris ResourceItem + Thumbnail patterns.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string. Product display name. |
| vendor | string (optional). Brand or supplier name. |
| sku | string (optional). Stock-keeping unit code. |
| price | string. Formatted price, e.g. "$49.00". |
| compare_at_price | string (optional). Strike-through original price. |
| status | string (optional). One of active | draft | archived. Default active. |
| image_url | string (optional). Product image URL. |
| tags | array of strings (optional). Flat tag list rendered as chips. |

## Example payload

```json
{
  "type": "product_thumbnail",
  "title": "Product Thumbnail",
  "price": "$29/mo"
}
```

Live page: https://a2uicatalog.ai/atoms/product_thumbnail/
Full field contract: https://a2uicatalog.ai/spec.json
