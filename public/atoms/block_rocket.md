# Block Rocket

A small toy-brick rocket: two grey nozzle bricks, red fins, a dark band, a white hull, a window and a red nose. A finished model of 9 toy bricks in one block: the brick list is fixed, so nothing needs writing out; it is the motion_bricks canvas with that list filled in, and every motion_bricks setting that does not name bricks works here the same way. Bricks drop into place in build order as p goes 0 to 1 and the model turns with the second dial (--s). Standalone it shows the finished model. Known limit, each brick canvas holds two WebGL contexts and a page allows about 16, so keep to about 7 brick canvases per page. Not affiliated with or endorsed by the LEGO Group. LEGO is a trademark of the LEGO Group.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| motion | object (optional). How the bricks arrive, same keys and defaults as motion_bricks motion (order, from, window, flight, distance, tilt, spin, spinAxis, gravity, jitter, support, seed, overshoot, rotOvershoot, recoil, travel, sharpness, direction). Absent = the plain build-up. |
| angle | number (optional). Starting turn in degrees, -360 to 360. Default 24. |
| elevation | number (optional). Camera elevation in degrees, 7-75. Default 26. |
| turns | number (optional). Full turns per unit of --s, -8 to 8. Default 1. |
| look | string (optional). One of "studio", "instructions". Default "studio" (a product shot: glossy plastic, no outlines); "instructions" is building-instructions style with dark edge lines. |
| base | string (optional). "none" for floating bricks (no plate, no plate shadow), or a "#rrggbb" colour for the baseplate. Default the classic green plate. |
| ratio | string (optional). One of "16:9", "4:3", "1:1", "3:4", "9:16". Default "16:9". |
| fill | boolean (optional). Fill the placed box height instead of using ratio. Default false. |
| label | string (optional, max 80). Accessible name. Default "Brick rocket". |

## Example payload

```json
{
  "type": "block_rocket"
}
```

Live page: https://a2uicatalog.ai/atoms/block_rocket/
Full field contract: https://a2uicatalog.ai/spec.json
