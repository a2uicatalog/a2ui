# Motion Shape

A form that draws or grows with p: a bar or rule (grow-x, grow-y), a disc (scale), a ring that sweeps round like a progress dial (sweep), or a fade; solid or a two-colour gradient at an angle, with rounded corners, and an optional heavy blur that makes it a soft glow behind everything. Fills its placed box, or w/h px. Plain HTML and CSS, no script: it moves with the --p custom property that a motion_timeline p track sets, and standalone it renders its final state.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| shape | "rect" | "circle" | "ring" | "line" (optional, default "rect") |
| fill | "#rrggbb" (optional). Default the stage accent. |
| fill2 | "#rrggbb" (optional). Second colour; makes a gradient (for a ring, the sweep colour). |
| angle | integer (optional). Gradient angle in degrees, 0-360. Default 90. |
| thickness | integer (optional). Ring and line thickness px, 1-200. Default 6. |
| radius | integer (optional). Rect corner radius px, 0-500. Default 0. |
| draw | "grow-x" | "grow-y" | "scale" | "sweep" | "fade" | "none" (optional). Default grow-x for rect and line, scale for circle, sweep for ring. sweep is ring only. |
| blur | integer (optional). Blur px, 0-200. A big blur on a gradient disc is an ambient glow. Default 0. |
| w | integer (optional). Width px, 1-3000. Default 100% of the placed box. |
| h | integer (optional). Height px, 1-3000. Default 100% of the placed box. A line is thickness tall. |

## Example payload

```json
{
  "type": "motion_shape"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_shape/
Full field contract: https://a2uicatalog.ai/spec.json
