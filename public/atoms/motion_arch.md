# Motion Arch

An architecture diagram that draws itself on the film clock. Nodes (device, app, server, tool, model, store, surface, user) pop in, edges draw box edge to box edge with arrowheads and labels, and messages, the payloads that actually move, ride the edges as chips (back true for the reply). Each element has a window [at, at + dur] of the progress p a motion_timeline track drives; standalone it is the finished diagram. Pure SVG and CSS, no script.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| nodes | array (max 12) of {id, kind?, label, sub?, x, y, w?, h?, at?, dur?}. id ^[a-z][a-z0-9_-]{0,31}$. kind "device" | "app" | "server" | "tool" | "model" | "store" | "surface" | "user" (default "server") sets the glyph and tint. x, y are the centre in percent of the frame; w, h percent (default 20 and 15). at, dur are the appearance window in p (0-1). |
| edges | array (max 16) of {from, to, label?, style?, both?, curve?, color?, at?, dur?}. from and to are node ids. style "solid" (draws on) | "dashed" (fades in). both adds a second arrowhead. curve -100 to 100 bends it. |
| messages | array (max 12) of {edge, text, back?, color?, at?, dur?}. edge is an index into edges; text (max 40) is the payload chip; back true sends it from the edge's end to its start. |
| groups | array (max 4) of {label, x, y, w, h, at?, dur?}: dashed boundaries in percent of the frame. |
| w | integer (optional). ViewBox width, 200-2000. Default 1000. |
| h | integer (optional). ViewBox height, 120-2000. Default 560. |
| size | integer (optional). Label px, 8-40. Default 17. |
| accent | "#rrggbb" (optional). Device, app and surface nodes, and messages. Default the stage accent. |
| accent2 | "#rrggbb" (optional). Server and tool nodes, and edges. Default "#2ac4ce". |
| color | "#rrggbb" (optional). Label ink. Default the stage ink. |
| mute | "#rrggbb" (optional). Sub-labels and group frames. Default "#9ca5b1". |
| fill | "#rrggbb" (optional). Node fill. Default "#2d3642". |
| background | "#rrggbb" (optional). Halo behind edge labels; match the stage. Default "#1e2733". |
| label | string (optional, max 80). Accessible name. Default "Architecture diagram". |

## Example payload

```json
{
  "type": "motion_arch",
  "edges": [],
  "messages": 1,
  "groups": []
}
```

Live page: https://a2uicatalog.ai/atoms/motion_arch/
Full field contract: https://a2uicatalog.ai/spec.json
