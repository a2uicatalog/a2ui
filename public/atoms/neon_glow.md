# Neon Glow

Pulsing neon-glow text on a near-black background

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
| text | string (alias: title, label) |
| color | string (optional, hex, default #22d3ee) |
| size | string (optional, CSS font-size) |

## Example payload

```json
{
  "type": "neon_glow",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/neon_glow/
Full field contract: https://a2uicatalog.ai/spec.json
