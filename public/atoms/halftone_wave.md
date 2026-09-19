# Halftone Wave

The canvas hero that works on a white page. A grid of dots whose size follows a travelling wave -- organic noise, a ripple spreading from a focus point, or a diagonal sweep -- like print halftone brought to life; wave peaks tint to the accent colour, and the pointer swells the dots around it. Ink on paper by default, so it sits inside a light document; flip ink and paper for a dark version. Optional eyebrow/title/body copy behind a veil. Honours prefers-reduced-motion (one static frame), pauses offscreen, DPR-aware. Same kit and hardening as flow_field: every option is an enum or a clamped int; colours must be #rrggbb.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Headline overlaid on the grid. |
| eyebrow | string (optional). Small uppercase label above the title. |
| body | string (optional). Copy under the title (markdown inline supported). |
| align | "left" | "center" | "right"  (optional, default "left") |
| wave | "noise" | "ripple" | "sweep"  (optional, default "noise"). Organic field, concentric ripple from the focus, or a diagonal front. |
| focus | "center" | "left" | "right"  (optional, default "center"). Ripple origin. |
| ink | "#rrggbb" (optional). Dot colour. Default "#0f172a". |
| paper | "#rrggbb" (optional). Ground colour. Default "#f7f7f5". |
| accent | "#rrggbb" (optional). Colour of the wave peaks; when absent, peaks stay in ink. |
| spacing | "fine" | "normal" | "coarse"  (optional, default "normal"). Dot pitch 10 / 14 / 20 px. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| height | integer (optional). Panel height in px, clamped 160-900. Default 320. |
| interactive | bool (optional). Pointer swells nearby dots. Default true. |

## Example payload

```json
{
  "type": "halftone_wave"
}
```

Live page: https://a2uicatalog.ai/atoms/halftone_wave/
Full field contract: https://a2uicatalog.ai/spec.json
