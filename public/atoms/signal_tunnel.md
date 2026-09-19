# Signal Tunnel

Full-bleed animated hero background: light streaks travel along fixed radial lanes through a vanishing point (right, centre or left), converging into it by default (signals arriving) or, in "out" mode, radiating away from it (signals broadcasting). Each streak accelerates as it nears the vanishing point and is coloured by its lane angle, so the tunnel reads as many distinct signals rather than one; an additive glow marks the vanishing point itself. Optional eyebrow/title/body copy sits opposite the tunnel behind a readability veil, the same flow_field/try.cloudflare.com hero layout (copy on one side, motion on the other). Honours prefers-reduced-motion (renders one pre-simulated frame, no loop), pauses when scrolled offscreen, and is DPR-aware. Pure canvas + requestAnimationFrame, zero dependencies, on the same shared kit as flow_field/orbit_mark. Every option is an enum or a clamped integer and colours must be #rrggbb: the config is baked into inline script, so nothing free-form ever reaches it. Dark backgrounds only -- streaks are additive and vanish on white.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Headline overlaid opposite the tunnel. |
| eyebrow | string (optional). Small uppercase label above the title, tinted with the first palette colour. |
| body | string (optional). Supporting copy under the title (markdown inline supported). |
| align | "left" | "center" | "right"  (optional, default "left"). Where the overlaid copy sits; the veil that keeps it readable follows it. |
| direction | "in" | "out"  (optional, default "in"). "in" -- streaks converge on the vanishing point. "out" -- streaks radiate away from it. |
| position | "right" | "center" | "left"  (optional, default "right"). Where the vanishing point sits; put it opposite the copy. |
| colors | array of 1-4 "#rrggbb" strings (optional). Default ["#38bdf8","#818cf8","#f472b6"]. Streaks take a colour by lane angle so the tunnel reads as coloured bands; the first colour also tints the vanishing-point glow. Invalid entries are dropped. |
| background | "#rrggbb" (optional). Default "#070a12". Keep it dark. |
| density | "low" | "normal" | "high"  (optional, default "normal"). Streak count, scaled to the panel area. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| trail | "short" | "normal" | "long"  (optional, default "normal"). How long each streak's light trail lingers. |
| height | integer (optional). Panel height in px, clamped 200-900. Default 360. |
| interactive | bool (optional). Pointer nudges nearby streaks. Default true. |

## Example payload

```json
{
  "type": "signal_tunnel"
}
```

Live page: https://a2uicatalog.ai/atoms/signal_tunnel/
Full field contract: https://a2uicatalog.ai/spec.json
