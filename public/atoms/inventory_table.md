# Inventory Table

Shopify Polaris-style inventory management table showing SKU, product name, available quantity, committed quantity, and warehouse location per row. Rows with available stock below the optional threshold are highlighted amber as a low-stock warning. Adapted from Polaris DataTable patterns.

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
| title | string (optional). Table heading. |
| items | array. List of {sku?, product, available, committed?, location?, threshold?}. threshold triggers amber low-stock highlight when available < threshold. |

## Example payload

```json
{
  "type": "inventory_table",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/inventory_table/
Full field contract: https://a2uicatalog.ai/spec.json
