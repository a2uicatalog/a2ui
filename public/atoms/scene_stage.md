# Scene Stage

An animated, looping pan/zoom SVG scene composed from a provenance-verified prop kit (original MIT artwork, each asset pinned by sha256 and restricted to an allowlist of SVG elements). Give a preset and the layout, backdrop, props and motion come from it; or write the layout in full. Props are referenced by id and never as SVG, so the agent cannot introduce script or external references. For a one-off shape use agent_sketchpad; for a diagram use a chart or d2 atom.

## Surfaces

mcp-apps

## Fields

| Field | Type |
|---|---|
| preset | string (optional). A ready-made place; supplies backdrop, ground, stage, camera, scenery and actors. PREFER a preset when one fits (it is a tested layout), and extend it with scenery_add / actors_add instead of rewriting it. One of: arctic-station, boardroom-meeting, call-centre, ci-cd-factory, city-skyline, construction-site, container-port, data-centre, desert-oasis, drone-delivery, factory-assembly-line, farm-harvest, fire-station-response, forest-campfire, highway-interchange, hospital-helipad, hospital-ward, hydro-dam, kanban-war-room, keynote-stage, laboratory-bench, library-archive, lighthouse-coast, message-post-office, metro-station, mine-quarry, mission-control, museum-gallery, observatory-night, offshore-platform, open-office, railway-station, restaurant-kitchen, river-ferry, school-classroom, ski-resort, solar-farm, space-station-orbit, street-market, substation-grid, trading-floor, vertical-farm, warehouse-logistics, water-treatment, wind-farm. |
| title | string (optional, max 80 chars). Accessible name and caption. Default is the preset id. |
| seed | integer (optional, 0..4294967295). Varies cloud and star placement. Default derives from the preset. |
| theme | {time: "dawn"|"day"|"dusk"|"night", weather: "clear"|"cloudy"|"overcast", setting: "countryside"|"coast"} (optional). Default day, clear, countryside. time: dawn = early morning, day = midday and afternoon, dusk = evening, night. Interiors dim with the time of day. |
| motion | {duration: number 6..40} (optional, seconds per loop). Default 20. |
| camera | {mode: "static"|"pan"|"push-in"} (optional). The preset has a default; without a preset the default is static. |
| accent | string (optional, #rrggbb). Tints props that take an accent colour. |
| backdrop | "sky-city"|"sky-hills"|"sky-sea"|"sky-mountains"|"sky-desert"|"sky-arctic"|"sky-flat"|"space"|"interior-office"|"interior-industrial"|"interior-lab"|"interior-civic"|"interior-dark" (required when there is no preset). |
| ground | "grass"|"road"|"sand"|"snow"|"concrete"|"water"|"none" (required when there is no preset). |
| stage | {width: 600..4000, zoom: 500..3200, focus_y: -800..200} (required when there is no preset). Scene units: x runs left to right from 0 to stage.width; the ground line is y=0, up is negative and positive y is toward the viewer. |
| scenery | array (optional, default empty; max 80) of {prop, x, y?, scale? 0.2..5, flip?, variant?}, or of {sketch, x, y?, scale?, flip?} when no prop fits. THE ESCAPE HATCH: give `sketch` instead of `prop`, an array of 1..40 SVG element strings (one element per string, origin at the ground point, up negative), e.g. ["<rect x=\"-30\" y=\"-24\" width=\"60\" height=\"24\" fill=\"#a9784a\"/>"]. Same rules as agent_sketchpad: tags rect, circle, ellipse, line, polyline, polygon, path, g; attributes cx, cy, r, rx, ry, x, y, width, height, x1, y1, x2, y2, points, d, fill, stroke, stroke-width, opacity, fill-opacity, stroke-opacity, stroke-linecap, stroke-linejoin, transform; values only letters, digits and # . , - ( ) %; no text, style, href or id; at most 8 sketches per scene; an invalid element refuses the scene with an error. Prefer a listed prop when one fits. HOUSE STYLE: dark rounded outlines are applied for you; colour with palette names written @name (dark, light, livery, glass, wood, brown, cream, skin, red, yellow ... listed with worked examples under conventions.sketch_style in the asset index) so the sketch matches the props and follows day and night; props are 40 to 150 units wide, so draw at that size. ANIMATION: give the item anim {kind: sway|bob|spin|pulse|blink|drift, period 0.3..30, amount, cx, cy}, or put animateTransform / animate (numbers only; targets transform, opacity, stroke-width, cx, cy, r and similar, never href or fill; at most 12 per element) inside a group to move a part. Props by id from the asset index (https://a2uicatalog.ai/catalogue/assets-index-v1.json); the strict JSON Schema of this block is https://a2uicatalog.ai/catalogue/scene-spec.schema.json. A ground prop needs no y (it stands on y=0); wall items need a negative y and interior ceiling lights use y=-620. Each prop's mount, scale, moves and size are in the asset index ("conventions" explains x, y and lanes). |
| actors | array (optional, default empty; max 30) of {prop, motion: "walk"|"ride"|"drive"|"fly"|"hover"|"orbit"|"takeoff"|"land", x0, x1, y, period 3..120, phase 0..1, scale?, variant?, ry?}. Movers that loop; y is a lane, 40..120 passes in front of props standing on the ground. takeoff rolls a plane along the ground, rotates and climbs away (ry = climb height, default 260); land descends, flares and rolls out. A sketch can be an actor too (give sketch instead of prop). A prop's suitable motions are its "moves" in the asset index. |
| scenery_add | array (optional, max 80 in total with the preset) of the same items as scenery. Appended to the preset's scenery instead of replacing it, e.g. add a cow and a chicken to farm-harvest. |
| actors_add | array (optional, max 30 in total with the preset) of the same items as actors. Appended to the preset's actors instead of replacing them. |

## Example payload

```json
{
  "type": "scene_stage",
  "backdrop": 1,
  "ground": "Ground",
  "stage": "Stage"
}
```

Live page: https://a2uicatalog.ai/atoms/scene_stage/
Full field contract: https://a2uicatalog.ai/spec.json
