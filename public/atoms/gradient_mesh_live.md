# Gradient Mesh Live

Full-bleed animated hero background: a handful of soft colour blobs, laid out over the panel with an even (Vogel-disk) spread, drift and breathe forever on the same value-noise field that drives flow_field -- never looping on a fixed timeline the way a CSS @keyframes mesh gradient must. The nearest blob leans toward the pointer. This is the animated, canvas-driven sibling of the static mesh_gradient atom and the CSS-keyframe aurora_background: pick this one when the motion itself, not just the colour, needs to feel alive. Optional eyebrow/title/body copy sits opposite a readability veil. Honours prefers-reduced-motion (one pre-simulated frame, no loop), pauses when scrolled offscreen, DPR-aware. Pure canvas + requestAnimationFrame, zero dependencies, on the same shared kit as flow_field/signal_tunnel. Every option is an enum or a clamped integer and colours must be #rrggbb: the config is baked into inline script, so nothing free-form ever reaches it. Dark backgrounds only -- blobs blend additively and vanish on white.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Headline overlaid opposite the blobs. |
| eyebrow | string (optional). Small uppercase label above the title, tinted with the first palette colour. |
| body | string (optional). Supporting copy under the title (markdown inline supported). |
| align | "left" | "center" | "right"  (optional, default "left"). Where the overlaid copy sits; the veil that keeps it readable follows it. |
| colors | array of 1-4 "#rrggbb" strings (optional). Default ["#38bdf8","#818cf8","#f472b6"]. Blobs cycle through these colours. Invalid entries are dropped. |
| background | "#rrggbb" (optional). Default "#070a12". Keep it dark. |
| density | "low" | "normal" | "high"  (optional, default "normal"). Blob count: 3 / 4 / 6. |
| motion | "subtle" | "normal" | "wild"  (optional, default "normal"). Drift amplitude. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| height | integer (optional). Panel height in px, clamped 200-900. Default 360. |
| interactive | bool (optional). Nearest blob leans toward the pointer. Default true. |

## Example payload

```json
{
  "type": "gradient_mesh_live"
}
```

Live page: https://a2uicatalog.ai/atoms/gradient_mesh_live/
Full field contract: https://a2uicatalog.ai/spec.json
