# Review Callout

Renders a short, impactful quote from a customer review, often accompanied

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
