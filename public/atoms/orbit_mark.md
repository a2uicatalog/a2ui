# Orbit Mark

The catalogue's own orbit mark, alive: the header logo (three orbit ellipses, nucleus, electron) drawn on canvas with a flow field around it -- hundreds of luminous streams ride a noise field and, when they pass near an orbit, get captured into it and circle the nucleus like electrons before drifting off again; the nucleus glows as a sink and a real electron runs the first orbit. Optional eyebrow/title/body copy sits beside the mark behind a readability veil, so it works as a brand hero or a cover slide. Pointer bends the field. Honours prefers-reduced-motion (one pre-simulated frame), pauses offscreen, DPR-aware. Dark backgrounds only. Same kit and hardening as flow_field: every option is an enum or a clamped int, colours must be #rrggbb.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Headline beside the mark. |
| eyebrow | string (optional). Small uppercase label above the title, tinted with the first colour. |
| body | string (optional). Supporting copy under the title (markdown inline supported). |
| align | "left" | "center" | "right"  (optional, default "left"). Where the copy sits. |
| mark_position | "center" | "right" | "left"  (optional, default "center"). Where the mark sits; put it opposite the copy. |
| size | "small" | "normal" | "large"  (optional, default "normal"). Mark diameter relative to the panel. |
| colors | array of 1-4 "#rrggbb" strings (optional). Default ["#6366f1","#a855f7","#22d3ee"]. First colour is the orbits and nucleus, second the electron, all of them the streams. |
| background | "#rrggbb" (optional). Default "#070a12". Keep it dark. |
| density | "low" | "normal" | "high"  (optional, default "normal") |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| trail | "short" | "normal" | "long"  (optional, default "normal") |
| electron | bool (optional). Animate an electron along the first orbit. Default true. |
| height | integer (optional). Panel height in px, clamped 200-900. Default 360. |
| interactive | bool (optional). Pointer bends the field. Default true. |

## Example payload

```json
{
  "type": "orbit_mark"
}
```

Live page: https://a2uicatalog.ai/atoms/orbit_mark/
Full field contract: https://a2uicatalog.ai/spec.json
