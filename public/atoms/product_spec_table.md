# Product Spec Table

Renders a table detailing technical specifications or features for

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| product_name | string |
| specs | array |

## Example payload

```json
{
  "type": "product_spec_table",
  "product_name": "Product name",
  "specs": [
    {
      "label": "Weight",
      "value": "1.2 kg"
    },
    {
      "label": "Dimensions",
      "value": "20\u00d715 cm"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/product_spec_table/
Full field contract: https://a2uicatalog.ai/spec.json
