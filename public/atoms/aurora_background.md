# Aurora Background

Dark panel with three independently-animating radial gradient blobs that drift and scale using CSS @keyframes — creating an aurora borealis effect with no JavaScript. Supports optional title and body text overlaid on the effect. Ideal for hero sections, cover slides, and atmospheric backgrounds on google-meet-stage.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| colors | array of up to 3 hex colour strings (optional). Default ["#38bdf8","#818cf8","#34d399"]. |
| speed | "slow" | "normal" | "fast"  (optional, default "slow") |
| opacity | float 0–1 (optional, default 0.5). Blob layer opacity. |
| background | string (optional). Panel background colour. Default "#0a0f1d". |
| title | string (optional). Text heading overlaid on the aurora. |
| body | string (optional). Body text overlaid on the aurora (markdown inline supported). |

## Example payload

```json
{
  "type": "aurora_background"
}
```

Live page: https://a2uicatalog.ai/atoms/aurora_background/
Full field contract: https://a2uicatalog.ai/spec.json
