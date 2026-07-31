# Canvas Plexus

Full-viewport animated particle network — dots connected by proximity lines that fade with distance. Mouse/pointer repulses particles. Zero external dependencies, pure requestAnimationFrame loop.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| count | integer (optional). Number of particles. Default 65. |
| colour | string (optional). Hex colour for particles and lines. Default |
| speed | number (optional). Particle speed multiplier. Default 1.0. |
| max_dist | integer (optional). Max distance px for edge connections. Default 120. |
| bg | string (optional). Background colour. Default |
| height | integer (optional). Canvas height px. Default 400. |
| repulse_radius | integer (optional). Mouse repulsion radius px. Default 90. |

## Example payload

```json
{
  "type": "canvas_plexus"
}
```

Live page: https://a2uicatalog.ai/atoms/canvas_plexus/
Full field contract: https://a2uicatalog.ai/spec.json
