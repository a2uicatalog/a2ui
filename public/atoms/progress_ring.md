# Progress Ring

Animated SVG circular progress gauge. Animates from 0 to value on load.

## Surfaces

web, google-apps-script-web, google-apps-script-side-panel, mcp-apps, android

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
| value | numeric value 0-100 (required) |
| size | ring diameter in px (default 100) |
| stroke_width | ring stroke thickness (default 8) |
| color | ring fill colour (default var(--a2ui-accent)) |
| track_color | background ring colour (default var(--border)) |
| label | optional caption below the ring |
| show_value | show numeric value inside ring (default true) |
| unit | unit string (default %) |

## Example payload

```json
{
  "type": "progress_ring",
  "value": "1,234"
}
```

Live page: https://a2uicatalog.ai/atoms/progress_ring/
Full field contract: https://a2uicatalog.ai/spec.json
