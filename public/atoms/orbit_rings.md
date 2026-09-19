# Orbit Rings

A system map that moves: up to three tilted orbit rings around a centre node, where each ring is a TIER of agent-supplied labelled items (for example tools / data / surfaces) and every item is a satellite with a light trail and its own label. Inner rings turn faster than outer ones, satellites are larger and brighter on the near side of their ring and dimmer behind the centre, and each ring carries its tier name, so the rings encode structure rather than decoration. The pointer tilts and turns the whole view. This is the hero-class sibling of the single-ring orbit_diagram; orbit_mark remains the fixed brand logo. Optional eyebrow/title/body copy sits behind a readability veil. Honours prefers-reduced-motion (one still frame, no loop), pauses when scrolled offscreen, DPR-aware. Pure canvas + requestAnimationFrame, zero dependencies, on the same shared kit as flow_field. Every option is an enum or a clamped integer and colours must be #rrggbb; agent-supplied labels are trimmed, length-capped and JSON-encoded with "<" escaped, so they can never break out of the script. Dark backgrounds only.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| center | string (optional). Label under the centre node, trimmed to 24 characters. Default "agent". |
| rings | array of 1-3 {label, items} objects (optional). Each ring is a tier: label is the tier name (up to 24 characters), items is an array of 1-6 strings (up to 24 characters each) orbiting on that ring. Entries that are not objects, and items that are not strings, are dropped. Default three rings: tools, data, surfaces. |
| title | string (optional). Headline overlaid opposite the rings. |
| eyebrow | string (optional). Small uppercase label above the title, tinted with the first palette colour. |
| body | string (optional). Supporting copy under the title (markdown inline supported). |
| align | "left" | "center" | "right"  (optional, default "left"). Where the overlaid copy sits; the veil that keeps it readable follows it. |
| position | "right" | "center" | "left"  (optional, default "right"). Where the rings sit; put them opposite the copy. |
| colors | array of 1-4 "#rrggbb" strings (optional). Default ["#38bdf8","#818cf8","#f472b6"]. Ring i takes colour i (cycling); the first colour also tints the centre node. Invalid entries are dropped. |
| background | "#rrggbb" (optional). Default "#070a12". Keep it dark. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| height | integer (optional). Panel height in px, clamped 240-900. Default 420. |
| interactive | bool (optional). Pointer tilts and turns the view. Default true. |

## Example payload

```json
{
  "type": "orbit_rings"
}
```

Live page: https://a2uicatalog.ai/atoms/orbit_rings/
Full field contract: https://a2uicatalog.ai/spec.json
