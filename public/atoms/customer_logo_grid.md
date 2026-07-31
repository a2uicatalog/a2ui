# Customer Logo Grid

Renders a grid or row of logos from featured customers or partners.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| logos | list |
| title | string |

## Example payload

```json
{
  "type": "customer_logo_grid",
  "logos": [
    {
      "src": "https://example.com/image.png",
      "alt": "Company A"
    },
    {
      "src": "https://example.com/image.png",
      "alt": "Company B"
    }
  ],
  "title": "Customer Logo Grid"
}
```

Live page: https://a2uicatalog.ai/atoms/customer_logo_grid/
Full field contract: https://a2uicatalog.ai/spec.json
