# Form Slider

Numeric range slider with a min, max, and optional step. Supports continuous (smooth) and discrete (stepped) variants. Renders a labelled track with a draggable thumb.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

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
