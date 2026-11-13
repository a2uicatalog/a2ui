# Glowing Stat

Single large stat with neon glow effect on dark background

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| value | string or number |
| label | string (optional) |
| colour | string (optional, hex, default #22d3ee) |
| size | string (optional, CSS font-size) |
| prefix | string (optional) |
| suffix | string (optional) |
| glow | boolean (optional) |

## Example payload

```json
{
  "type": "glowing_stat",
  "value": 1
}
```

Live page: https://a2uicatalog.ai/atoms/glowing_stat/
Full field contract: https://a2uicatalog.ai/spec.json
