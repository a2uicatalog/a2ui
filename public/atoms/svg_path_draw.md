# Svg Path Draw

An SVG path that animates drawing itself from start to end using the stroke-dasharray / stroke-dashoffset CSS technique. The agent selects a named shape (arrow, check, circle, zigzag, infinity) or supplies a custom SVG path string.

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
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| shape | "arrow" | "check" | "circle" | "zigzag" | "infinity"  (optional, default "arrow") |
| color | string (optional). Stroke colour. Default "#4f46e5". |
| width | integer (optional). Stroke width in px. Default 3. |
| duration | number (optional). Draw duration in seconds. Default 1.5. |
| label | string (optional). Caption below the SVG. |

## Example payload

```json
{
  "type": "svg_path_draw"
}
```

Live page: https://a2uicatalog.ai/atoms/svg_path_draw/
Full field contract: https://a2uicatalog.ai/spec.json
