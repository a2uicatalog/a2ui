# Neon Text

Neon-coloured glowing text, ideal for dark technical pages

## Surfaces

google-apps-script-web, mcp-apps, android

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
| text | string |
| colour | string (optional, hex, default #22d3ee) |
| size | string (optional, CSS font-size) |
| weight | string or number (optional) |
| align | string (optional, left|center|right) |
| flicker | boolean (optional) |

## Example payload

```json
{
  "type": "neon_text",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/neon_text/
Full field contract: https://a2uicatalog.ai/spec.json
