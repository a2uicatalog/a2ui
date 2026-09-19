# Message Lanes

The A2UI pitch, drawn: small packets stream from an agent node on the left down curved lanes into a surface node on the right, leaving light trails; every arrival makes the surface flash and unfolds a small card outline inside it, the newest on top, older ones fading. Labels for both nodes are agent-supplied (up to 24 characters each). Optional eyebrow/title/body copy. Honours prefers-reduced-motion (one pre-simulated frame with packets mid-flight), pauses offscreen, DPR-aware. Dark backgrounds only. Every option is an enum or a clamped int; colours must be #rrggbb.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| from_label | string (optional). Label under the left node. Default "agent". |
| to_label | string (optional). Label under the right node. Default "surface". |
| lanes | integer (optional). Number of lanes, clamped 1-6. Default 4. |
| rate | "slow" | "normal" | "fast"  (optional, default "normal"). Packet speed. |
| title | string (optional). Headline overlaid on the scene. |
| eyebrow | string (optional). Small uppercase label above the title. |
| body | string (optional). Copy under the title (markdown inline supported). |
| align | "left" | "center" | "right"  (optional, default "center") |
| colors | array of 1-4 "#rrggbb" strings (optional). Default sky/violet/pink; the first colours the agent node, the second the surface. |
| background | "#rrggbb" (optional). Default "#070a12". Keep it dark. |
| height | integer (optional). Panel height in px, clamped 200-900. Default 320. |

## Example payload

```json
{
  "type": "message_lanes"
}
```

Live page: https://a2uicatalog.ai/atoms/message_lanes/
Full field contract: https://a2uicatalog.ai/spec.json
