# Motion Sketch

Strokes that draw themselves one after another as p goes 0 to 1, like an agent sketching: each stroke is path data (M, L, H, V, C, S, Q, T, A, Z with numbers; anything else and the stroke is dropped), drawn in a chosen colour and width, optionally with a soft fill that appears as it is drawn. Not raw SVG markup, so nothing but a path can reach the page. Sized by a viewBox (w by h, default 400 by 400) and scaled to its placed box. Plain SVG and CSS, no script: it moves with the --p custom property a motion_timeline p track sets, and standalone it renders the finished drawing.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| strokes | array (max 24) of {d, color?, width?, fill?, fill_opacity?}. d is path data (max 700 characters of path commands, numbers and separators). color and fill are "#rrggbb"; width 1-24 px (default 6); fill_opacity 0-1 (default 0.2). Strokes draw in order. |
| w | integer (optional). ViewBox width, 50-2000. Default 400. |
| h | integer (optional). ViewBox height, 50-2000. Default 400. |
| label | string (optional, max 60). Accessible name of the drawing. Default "Sketch". |

## Example payload

```json
{
  "type": "motion_sketch"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_sketch/
Full field contract: https://a2uicatalog.ai/spec.json
