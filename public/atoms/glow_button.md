# Glow Button

Button or anchor that uses CSS box-shadow to signal state. Three named states — disabled (grey), ready (brand), fired (success pulse) — each with a distinct glow colour and optional pulse animation. State is set via the state field; no JavaScript required.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string. Button text. |
| state | "disabled" | "ready" | "fired"  (optional, default "ready") |
| href | string (optional). If set renders as an anchor tag. |
| color_ready | string (optional). Glow colour in ready state. Default "#38bdf8". |
| color_fired | string (optional). Glow colour in fired state. Default "#34d399". |
| size | "sm" | "md" | "lg"  (optional, default "md") |
| description | string (optional). Small caption text below the button. |

## Example payload

```json
{
  "type": "glow_button",
  "label": "Glow Button"
}
```

Live page: https://a2uicatalog.ai/atoms/glow_button/
Full field contract: https://a2uicatalog.ai/spec.json
