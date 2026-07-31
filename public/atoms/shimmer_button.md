# Shimmer Button

Inline button or link with a diagonal shimmer sweep animation driven by CSS background-position keyframes. The shimmer accent colour sweeps across the button on a loop. No JavaScript. Use for primary CTAs on dark backgrounds.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string. Button text. |
| href | string (optional). If set, renders as an anchor tag. |
| size | "sm" | "md" | "lg"  (optional, default "md") |
| accent | string (optional). Shimmer highlight colour. Default "#38bdf8". |
| background | string (optional). Button background colour. Default "#1e293b". |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| description | string (optional). Small text below the button. |

## Example payload

```json
{
  "type": "shimmer_button",
  "label": "Shimmer Button"
}
```

Live page: https://a2uicatalog.ai/atoms/shimmer_button/
Full field contract: https://a2uicatalog.ai/spec.json
