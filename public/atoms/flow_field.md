# Flow Field

Full-bleed animated hero background: hundreds of luminous streams ride a slowly evolving noise vector field on a dark canvas, leave additive long-exposure light trails, and converge on a soft glowing focus point. The pointer bends the field around it. Optional eyebrow/title/body copy sits on the opposite side behind a readability veil -- the try.cloudflare.com hero layout (copy left, light right) as one atom. Honours prefers-reduced-motion (renders one pre-simulated long-exposure frame, no loop), pauses when scrolled offscreen, and is DPR-aware. Pure canvas + requestAnimationFrame, zero dependencies. Every option is an enum or a clamped integer and colours must be #rrggbb: the config is baked into inline script, so nothing free-form ever reaches it (bad values fall back to defaults). Dark backgrounds only -- trails are drawn additively and vanish on white.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Headline overlaid on the field. |
| eyebrow | string (optional). Small uppercase label above the title, tinted with the first palette colour. |
| body | string (optional). Supporting copy under the title (markdown inline supported). |
| align | "left" | "center" | "right"  (optional, default "left"). Where the overlaid copy sits; the veil that keeps it readable follows it. |
| focus | "right" | "center" | "left" | "none"  (optional, default "right"). Where the glowing sink is that every stream converges on. Put it opposite the copy. |
| colors | array of 1-4 "#rrggbb" strings (optional). Default ["#38bdf8","#818cf8","#f472b6"]. Streams take a colour by region so the field reads as coloured ribbons; the first colour also tints the focus glow. Invalid entries are dropped. |
| background | "#rrggbb" (optional). Default "#070a12". Keep it dark. |
| density | "low" | "normal" | "high"  (optional, default "normal"). Stream count, scaled to the panel area. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| trail | "short" | "normal" | "long"  (optional, default "normal"). How long each stream's light trail lingers. |
| scale | "fine" | "normal" | "broad"  (optional, default "normal"). Size of the swirls. |
| height | integer (optional). Panel height in px, clamped 200-900. Default 360. |
| interactive | bool (optional). Pointer bends the field. Default true. |

## Example payload

```json
{
  "type": "flow_field"
}
```

Live page: https://a2uicatalog.ai/atoms/flow_field/
Full field contract: https://a2uicatalog.ai/spec.json
