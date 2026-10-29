# Motion Bricks

A toy-brick sculpture on the film clock: procedural boxes with real brick proportions, studs, shadows and instruction-style edges (the brick_build_3d engine, here with boxes only; real LDraw parts are brick_build_3d's partsModel), drawn on a transparent stage so it sits inside a film. Bricks drop into place in build order as p goes 0 to 1 (p 1 = every brick settled) and the model turns with the second dial (--s, turns per unit), so a step track spins it and seeking shows exactly that frame. Give text to set a word in bricks (each character of a 5x7 dot font, every row merged into 1x1 to 1x4 bricks, depth studs deep), bricks for an explicit model, or a named shape. The optional motion object sets how the bricks arrive: the order they launch in, where they fly in from, how long each flight lasts, how much they tumble, and a small overshoot and recoil as they seat; all of it is numbers and fixed names that are clamped, and a stud-cell pass keeps a brick from launching before the brick it rests on. Standalone it shows the finished model. The engine is fixed code and the config is numbers, colours and the brick list, so nothing in the payload becomes code; without WebGL the engine draws with a 2D canvas painter instead. Known limit: each brick canvas holds two WebGL contexts and a page allows about 16, so keep to about 7 brick canvases per page. Not affiliated with or endorsed by the LEGO Group. LEGO is a trademark of the LEGO Group.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| text | string (optional, max 12). Builds the word in bricks: A-Z, 0-9 and . , ! ? - : ' (others leave a gap). |
| bricks | array (optional). Explicit toy-brick model (procedural boxes, up to 3000), same format as brick_build_3d: {x, y, z, w, d, h, c} or [x, y, z, w, d, c] / [x, y, z, w, d, h, c]. Used when text is absent. |
| shape | "heart" | "sphere" | "torus" | "helix" | "pyramid" | "house" (optional, default "heart"). Used when neither text nor bricks is given. |
| color | "#rrggbb" (optional). One colour for every lettering brick; otherwise letters cycle through palette or the classic brick colours. |
| palette | array of "#rrggbb" (optional). Colours for lettering (cycled per letter) and for integer colour indexes in bricks. |
| depth | integer (optional). Lettering depth in studs, 1-4. Default 2. |
| base | string (optional). "none" for floating bricks (no plate, no plate shadow), or a "#rrggbb" colour for the baseplate. Default the classic green plate. |
| look | "studio" | "instructions" (optional, default "studio"). studio: a product shot (glossy ABS, softbox reflections, edges that catch light, no outlines). instructions: the building-instructions style of brick_build_3d (dark edge lines). |
| angle | number (optional). Starting turn in degrees, -360 to 360. Default 24. |
| elevation | number (optional). Camera elevation in degrees, 7-75. Default 26. |
| turns | number (optional). Full turns per unit of --s, -8 to 8. Default 1. |
| motion | object (optional). How the bricks arrive; absent = the plain build-up. Every key is optional and clamped, unknown keys are ignored, and a value that is not a number or a known name falls back to its default. order: "index" (the brick list order) | "base-up" (layer by layer) | "diagonal" | "radial" (default "diagonal"). from: "above" | "outward" | "scatter" (where bricks start; default "above"). spinAxis: "y" | "x" | "z" (default "y"). window: 0-30, default 2.4, how widely the launch times are spread. flight: 0.1-5, default 0.62, how long one brick is in the air; together they set the pace, since p 0 to 1 covers window + flight. distance: 0-60, default 9, start distance in stud units. tilt: 0-360, default 70, random start tumble in degrees. spin: -8 to 8, default 0.5, extra turns while flying. gravity: 0-1, default 0.5, how strongly lower bricks go first (diagonal and radial orders). jitter: 0-1, default 0.15, random shuffle of the order. support: 0 or 1, default 1, a brick never launches before the brick it rests on. seed: integer 0-2147483646, default 7. overshoot 0-1 (0.12), rotOvershoot 0-0.5 (0.08), recoil 0-1 (0.45), travel 0.2-0.9 (0.58), sharpness 1.5-8 (4): the seat-and-settle curve. direction: [x, y, z], default [1, 0.55, 0.8], the sweep direction for the diagonal order. |
| ratio | "16:9" | "4:3" | "1:1" | "3:4" | "9:16" (optional, default "16:9") |
| fill | boolean (optional). Fill the placed box height instead of using ratio. Default false. |
| label | string (optional, max 80). Accessible name. |

## Example payload

```json
{
  "type": "motion_bricks"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_bricks/
Full field contract: https://a2uicatalog.ai/spec.json
