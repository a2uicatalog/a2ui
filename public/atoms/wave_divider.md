# Wave Divider

Animated SVG wave as a decorative section separator.

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
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| color | wave fill colour (default var(--a2ui-accent)) |
| height | wave height in px (default 60) |
| speed | animation cycle in seconds (default 8) |
| opacity | fill opacity (default 0.15) |
| flip | reverse wave direction (default false) |
| animate | animate the wave (default true) |

## Example payload

```json
{
  "type": "wave_divider"
}
```

Live page: https://a2uicatalog.ai/atoms/wave_divider/
Full field contract: https://a2uicatalog.ai/spec.json
