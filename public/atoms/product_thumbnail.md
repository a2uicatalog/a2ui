# Product Thumbnail

Shopify Polaris-style product card showing optional image, title, vendor, SKU, price with optional compare-at strike-through, status badge, and tag chips. Adapted from Polaris ResourceItem + Thumbnail patterns.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
