# Stripe Background

Card with animated diagonal stripe background pattern

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
| text | string (optional, alias: content) |
| color1 | string (optional, hex, first stripe colour) |
| color2 | string (optional, hex, second stripe colour) |
| speed | number (optional, animation seconds) |

## Example payload

```json
{
  "type": "stripe_background"
}
```

Live page: https://a2uicatalog.ai/atoms/stripe_background/
Full field contract: https://a2uicatalog.ai/spec.json
