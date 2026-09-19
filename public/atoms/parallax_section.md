# Parallax Section

Depth-layered background on canvas: three layers of soft colour orbs, large and faint at the back, small and sharp at the front, each layer shifting with the pointer by an amount proportional to its depth, plus a slow ambient drift when the pointer is away. Optional eyebrow/title/body copy centred on top. Pointer-driven rather than scroll-driven on purpose: MCP Apps hosts size the iframe to its content, so there is often no scroll to drive. Honours prefers-reduced-motion (one static frame), pauses offscreen, DPR-aware. Was a "canvas fallback placeholder" until 2026-09-19; now a real atom on the flow_field kit, identical on every renderer.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, alias: label, text). Heading centred over the layers. |
| eyebrow | string (optional). Small uppercase label above the title. |
| body | string (optional). Copy under the title (markdown inline supported). |
| colors | array of 1-4 "#rrggbb" strings (optional). Default indigo/pink/cyan. |
| background | "#rrggbb" (optional). Default "#0f172a". Keep it dark. |
| depth | "subtle" | "normal" | "deep"  (optional, default "normal"). How far the layers shift with the pointer. |
| height | integer (optional). Panel height in px, clamped 160-900. Default 300. |
| interactive | bool (optional). Pointer drives the parallax. Default true. |

## Example payload

```json
{
  "type": "parallax_section"
}
```

Live page: https://a2uicatalog.ai/atoms/parallax_section/
Full field contract: https://a2uicatalog.ai/spec.json
