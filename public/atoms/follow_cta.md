# Follow Cta

Renders a banner encouraging readers to connect with official social channels.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| message | string. Promotional copy driving user interactions. |
| platform_links | object. Platform name keys mapped to target URLs. |

## Example payload

```json
{
  "type": "follow_cta",
  "message": 1,
  "platform_links": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/follow_cta/
Full field contract: https://a2uicatalog.ai/spec.json
