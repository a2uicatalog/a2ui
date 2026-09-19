# Wave Terrain

Full-bleed animated hero background: a live terrain flyover drawn as receding ridgelines. Rows of noise-shaped hills scroll toward the viewer while their heights keep evolving on the same value-noise field that drives flow_field, so the landscape never repeats; each row is filled with the background so nearer ridges occlude farther ones, and colour shifts along the palette from the horizon to the foreground. A calm valley runs down the middle with relief rising toward the edges. The pointer steers the camera sideways with a gentle parallax. The live sibling of the static, drag-to-rotate isometric_mesh. Optional eyebrow/title/body copy sits behind a readability veil. Honours prefers-reduced-motion (one still frame, no loop), pauses when scrolled offscreen, DPR-aware. Pure canvas + requestAnimationFrame, zero dependencies, on the same shared kit as flow_field. Every option is an enum or a clamped integer and colours must be #rrggbb: the config is baked into inline script, so nothing free-form ever reaches it. Dark backgrounds only.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Headline overlaid on the scene. |
| eyebrow | string (optional). Small uppercase label above the title, tinted with the first palette colour. |
| body | string (optional). Supporting copy under the title (markdown inline supported). |
| align | "left" | "center" | "right"  (optional, default "left"). Where the overlaid copy sits; the veil that keeps it readable follows it. |
| colors | array of 1-4 "#rrggbb" strings (optional). Default ["#38bdf8","#818cf8","#f472b6"]. Ridgelines blend from the first colour at the horizon to the last in the foreground; the first also tints the horizon glow. Invalid entries are dropped. |
| background | "#rrggbb" (optional). Default "#070a12". Keep it dark. |
| density | "low" | "normal" | "high"  (optional, default "normal"). Number of ridgeline rows: 22 / 34 / 48. |
| relief | "low" | "normal" | "high"  (optional, default "normal"). How tall the hills are. |
| scale | "fine" | "normal" | "broad"  (optional, default "normal"). Width of the hills across the terrain. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal"). Flyover speed. |
| height | integer (optional). Panel height in px, clamped 200-900. Default 380. |
| interactive | bool (optional). Pointer steers the camera sideways. Default true. |

## Example payload

```json
{
  "type": "wave_terrain"
}
```

Live page: https://a2uicatalog.ai/atoms/wave_terrain/
Full field contract: https://a2uicatalog.ai/spec.json
