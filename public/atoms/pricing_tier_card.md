# Pricing Tier Card

Renders a single pricing plan with its name, price, key features, and an optional call to action.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| plan_name | string |
| price | string |
| currency | string |
| frequency | string |
| features | array |
| call_to_action_label | string |
| call_to_action_url | string |
| is_highlighted | boolean |

## Example payload

```json
{
  "type": "pricing_tier_card",
  "plan_name": "Plan name",
  "price": "$29/mo",
  "currency": "USD",
  "frequency": "monthly",
  "features": [
    "Core feature",
    "Advanced analytics",
    "API access"
  ],
  "call_to_action_label": "Call to action label",
  "call_to_action_url": "https://example.com",
  "is_highlighted": true
}
```

Live page: https://a2uicatalog.ai/atoms/pricing_tier_card/
Full field contract: https://a2uicatalog.ai/spec.json
