# Meteor Shower

Dark panel with CSS-animated diagonal streaks that fall across the surface like a meteor shower. Each meteor is a rotated span with a linear-gradient tail, animated with staggered delays — no JavaScript, no canvas. Optional title and body text render above the effect layer.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

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
| count | integer (optional). Number of meteors. Default 20. Max 40. |
| color | string (optional). Meteor streak colour. Default "#38bdf8". |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| background | string (optional). Panel background colour. Default "#0a0f1d". |
| title | string (optional). Text heading overlaid on the effect. |
| body | string (optional). Body text overlaid on the effect (markdown inline supported). |

## Example payload

```json
{
  "type": "meteor_shower"
}
```

Live page: https://a2uicatalog.ai/atoms/meteor_shower/
Full field contract: https://a2uicatalog.ai/spec.json
