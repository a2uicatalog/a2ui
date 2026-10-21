# Motion Rays

A sunburst that fans out behind a hero as p goes 0 to 1 (kind burst, --s turns it), or horizontal speed streaks that sweep across the frame (kind speed, --s slides them). Plain CSS gradients, no script; standalone it renders finished.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| kind | "burst" | "speed" (optional, default "burst") |
| angle | integer (optional). Kind speed only: the direction the lines run, in degrees clockwise from horizontal, -180 to 180. Default 0 (horizontal lines streaming left to right as step advances). The lines and their travel turn together inside the same 16:9 frame, clipped to it. Ignored by burst; 0 or a non-number keeps the horizontal look exactly. |
| count | integer (optional). Rays or lines, 4-64. Default 24. |
| thickness | number (optional). Share of each step that is ray, 0.1-0.9. Default 0.5. |
| spin | integer (optional). Degrees turned at --s = 1 (burst), -360 to 360. Default 45. |
| strength | number (optional). Peak opacity, 0.05-1. Default 0.35. |
| accent | "#rrggbb" (optional). Default the stage accent. |

## Example payload

```json
{
  "type": "motion_rays"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_rays/
Full field contract: https://a2uicatalog.ai/spec.json
