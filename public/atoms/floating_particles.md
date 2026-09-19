# Floating Particles

Soft bokeh particle field on canvas: dozens of luminous, depth-sized orbs drift upward, swaying on a slow noise field, drawn additively so they glow where they overlap; the pointer nudges them aside. Optional eyebrow/title/body copy centred over the field behind a readability veil. Honours prefers-reduced-motion (one static frame), pauses offscreen, DPR-aware. Was a "canvas fallback placeholder" until 2026-09-19 (a grey box on GAS and MCP Apps); now a real atom on the same kit as flow_field, identical on every renderer. Every option is an enum or a clamped int; colours must be #rrggbb.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, alias: label, text). Heading centred over the field. |
| eyebrow | string (optional). Small uppercase label above the title. |
| body | string (optional). Copy under the title (markdown inline supported). |
| colors | array of 1-4 "#rrggbb" strings (optional). Default indigo/violet/pink/cyan. |
| background | "#rrggbb" (optional). Default "#0f172a". Keep it dark. |
| density | "low" | "normal" | "high"  (optional, default "normal") |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| height | integer (optional). Panel height in px, clamped 120-900. Default 240. |
| interactive | bool (optional). Pointer nudges the particles. Default true. |

## Example payload

```json
{
  "type": "floating_particles"
}
```

Live page: https://a2uicatalog.ai/atoms/floating_particles/
Full field contract: https://a2uicatalog.ai/spec.json
