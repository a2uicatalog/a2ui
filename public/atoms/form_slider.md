# Form Slider

Numeric range slider with a min, max, and optional step. Supports continuous (smooth) and discrete (stepped) variants. Renders a labelled track with a draggable thumb.

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
| label | string (optional). Visible label above the slider. |
| name | string. Field identifier. |
| min | number. Minimum value. |
| max | number. Maximum value. |
| step | number (optional). Increment size. Omit for continuous. |
| default_value | number (optional). Initial thumb position. |
| variant | string (optional). One of: continuous, discrete. Default: continuous. |
| rules | array of strings (optional). |

## Example payload

```json
{
  "type": "form_slider",
  "name": "Form Slider",
  "min": 1,
  "max": 5
}
```

Live page: https://a2uicatalog.ai/atoms/form_slider/
Full field contract: https://a2uicatalog.ai/spec.json
