# Progress Circle

SVG circular progress arc that animates from 0 to the target value on mount using CSS stroke-dashoffset transition. Percentage is displayed in the centre. Replaces the prior placeholder implementation with a proper animated SVG arc. No JavaScript required.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| value | integer. The progress value (0–100). |
| label | string (optional). Caption text below the circle. |
| color | string (optional). Arc stroke colour. Default "#38bdf8". |
| size | "sm" | "md" | "lg"  (optional, default "md"). Circle diameter. |

## Example payload

```json
{
  "type": "progress_circle",
  "value": 75
}
```

Live page: https://a2uicatalog.ai/atoms/progress_circle/
Full field contract: https://a2uicatalog.ai/spec.json
