# Particle Burst

On every click anywhere on the page, coloured particles burst outward from the click point with random velocities and simulated gravity, then fade out.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

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
