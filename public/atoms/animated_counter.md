# Animated Counter

CSS @property counter animation that counts up from zero to target values without JavaScript. Uses @keyframes with CSS custom properties typed as integers. Each counter has a value, label, optional prefix/suffix, and color.

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
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| counters | array of objects with — value (integer), label, prefix (optional), suffix (optional), color (optional hex). |
| duration | number (optional). Animation duration in seconds. Default 2. |

## Example payload

```json
{
  "type": "animated_counter"
}
```

Live page: https://a2uicatalog.ai/atoms/animated_counter/
Full field contract: https://a2uicatalog.ai/spec.json
