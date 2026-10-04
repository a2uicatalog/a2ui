# Motion Leader

A callout line that draws itself from one point to another as p goes 0 to 1: straight or bent, with a start dot, an arrowhead that lands at the end, and a label that fades in beside the tip. The annotation that points at a part of a diagram, a map or a product shot. Points are in viewBox units (w by h, default 400 by 300) and the whole thing scales to its placed box. Plain SVG and CSS, no script: it moves with the --p custom property a motion_timeline p track sets, and standalone it renders finished.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| from | [x, y] (optional). Start point in viewBox units. Default [48, 210] on the default 400 by 300 box. |
| to | [x, y] (optional). End point, where the arrowhead lands. Default [352, 90]. |
| curve | integer (optional). Bend, -100 to 100, as a percentage of the line length at its middle. 0 is straight. Default 0. |
| label | string (optional, max 40). Text beside the tip. |
| label_at | "end" | "start" (optional, default "end") |
| arrow | bool (optional). Arrowhead. Default true. |
| dot | bool (optional). Dot at the start. Default true. |
| color | "#rrggbb" (optional). Line, dot and arrowhead. Default the stage accent. |
| label_color | "#rrggbb" (optional). Default the stage ink. |
| width | integer (optional). Line px, 1-24. Default 4. |
| size | integer (optional). Label px, 8-80. Default 22. |
| w | integer (optional). ViewBox width, 50-2000. Default 400. |
| h | integer (optional). ViewBox height, 50-2000. Default 300. |

## Example payload

```json
{
  "type": "motion_leader"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_leader/
Full field contract: https://a2uicatalog.ai/spec.json
