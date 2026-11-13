# Gradient Border Card

Card with an animated gradient border stroke on dark background

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
| title | string (optional) |
| content | string (optional) |
| colours | array of hex strings (optional, gradient stops) |
| bg | string (optional, card background) |
| angle | number (optional, gradient angle degrees) |
| padding | string (optional) |
| radius | string (optional) |

## Example payload

```json
{
  "type": "gradient_border_card"
}
```

Live page: https://a2uicatalog.ai/atoms/gradient_border_card/
Full field contract: https://a2uicatalog.ai/spec.json
