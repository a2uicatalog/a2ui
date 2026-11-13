# Particle Burst

On every click anywhere on the page, coloured particles burst outward from the click point with random velocities and simulated gravity, then fade out.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Angular | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Flutter | Not supported | 2026-11-13 | component type unknown to the renderer |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| count | integer (optional). Particles per click. Default 14. |
| colours | array (optional). Array of hex colour strings. |
| size | integer (optional). Particle diameter px. Default 8. |
| duration | integer (optional). Animation duration ms. Default 700. |
| gravity | number (optional). Downward pull factor. Default 1.2. |

## Example payload

```json
{
  "type": "particle_burst"
}
```

Live page: https://a2uicatalog.ai/atoms/particle_burst/
Full field contract: https://a2uicatalog.ai/spec.json
