# Magnetic Element

Wraps content that drifts toward the cursor when it enters the activation radius, then springs back with a cubic-bezier overshoot when the cursor leaves.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional). Text label for the default pill style. |
| content | string (optional). Raw HTML to use instead of the default pill. |
| accent | string (optional). Pill background colour. Default |
| radius | integer (optional). Activation distance px. Default 120. |
| strength | number (optional). Pull factor 0–1. Default 0.4. |

## Example payload

```json
{
  "type": "magnetic_element"
}
```

Live page: https://a2uicatalog.ai/atoms/magnetic_element/
Full field contract: https://a2uicatalog.ai/spec.json
