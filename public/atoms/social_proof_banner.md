# Social Proof Banner

Renders a prominent banner highlighting a key social proof metric or achievement.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| metric_value | string |
| metric_label | string |
| icon_url | string |
| link_url | string |

## Example payload

```json
{
  "type": "social_proof_banner",
  "metric_value": "Metric value",
  "metric_label": "Metric label",
  "icon_url": "https://example.com",
  "link_url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/social_proof_banner/
Full field contract: https://a2uicatalog.ai/spec.json
