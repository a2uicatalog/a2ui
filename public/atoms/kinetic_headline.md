# Kinetic Headline

Headline where each word flies in with a staggered animation

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
| text | string (alias: title) |
| size | string (optional, CSS font-size) |
| color | string (optional, hex) |
| stagger | number (optional, seconds between words) |
| style | string (optional, up|down|scale|fade) |

## Example payload

```json
{
  "type": "kinetic_headline",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/kinetic_headline/
Full field contract: https://a2uicatalog.ai/spec.json
