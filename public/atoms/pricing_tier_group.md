# Pricing Tier Group

Renders a collection of pricing tier cards, typically for comparing

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
