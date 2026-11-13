# Diagram

SVG architecture diagram hosted at a public URL

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps, android

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
| url | string |
| caption | string (optional) |

## Example payload

```json
{
  "type": "diagram",
  "url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/diagram/
Full field contract: https://a2uicatalog.ai/spec.json
