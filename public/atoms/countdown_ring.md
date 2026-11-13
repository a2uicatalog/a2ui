# Countdown Ring

Circular SVG countdown that depletes as seconds tick down.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
| duration_sec | total countdown in seconds (required, default 60) |
| size | ring diameter in px (default 80) |
| color | ring colour (default var(--a2ui-accent)) |
| label | caption below |

## Example payload

```json
{
  "type": "countdown_ring",
  "label": "Countdown Ring"
}
```

Live page: https://a2uicatalog.ai/atoms/countdown_ring/
Full field contract: https://a2uicatalog.ai/spec.json
