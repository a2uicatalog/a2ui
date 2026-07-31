# Blur Fade In

Container that animates from blurred and transparent to fully visible on mount. Uses CSS @keyframes with filter:blur() and opacity together — no JavaScript. Configurable delay, duration, and direction (up, down, left, right, none).

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| children | array of atom objects to render inside the container (optional). |
| title | string (optional). Heading text. |
| body | string (optional). Body text (markdown inline supported). |
| delay | string (optional). CSS delay before animation starts, e.g. "0.3s". Default "0s". |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| direction | "up" | "down" | "left" | "right" | "none"  (optional, default "up"). Drift direction on reveal. |
| blur | string (optional). Starting blur radius, e.g. "8px". Default "8px". |
| background | string (optional). Panel background. Default transparent. |

## Example payload

```json
{
  "type": "blur_fade_in"
}
```

Live page: https://a2uicatalog.ai/atoms/blur_fade_in/
Full field contract: https://a2uicatalog.ai/spec.json
