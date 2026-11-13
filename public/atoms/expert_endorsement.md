# Expert Endorsement

Renders an endorsement from an industry expert, including their quote, photo, name, and credentials.

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
| quote | string |
| expert_name | string |
| expert_title | string |
| expert_organization | string |
| expert_avatar_url | string |

## Example payload

```json
{
  "type": "expert_endorsement",
  "quote": "The vocabulary IS the discovery layer.",
  "expert_name": "Expert name",
  "expert_title": "Expert title",
  "expert_organization": "Expert organization",
  "expert_avatar_url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/expert_endorsement/
Full field contract: https://a2uicatalog.ai/spec.json
