# Pricing Tier Group

Renders a collection of pricing tier cards, typically for comparing

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| tiers | array |

## Example payload

```json
{
  "type": "pricing_tier_group",
  "tiers": [
    {
      "name": "Starter",
      "price": "$9/mo",
      "features": []
    },
    {
      "name": "Pro",
      "price": "$29/mo",
      "features": []
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/pricing_tier_group/
Full field contract: https://a2uicatalog.ai/spec.json
