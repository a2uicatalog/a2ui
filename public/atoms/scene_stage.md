# Scene Stage

An animated, looping pan/zoom SVG scene composed from a provenance-verified prop kit (original MIT artwork, each asset pinned by sha256 and restricted to an allowlist of SVG elements). Give a preset and the layout, backdrop, props and motion come from it; or write the layout in full. Props are referenced by id and never as SVG, so the agent cannot introduce script or external references. For a one-off shape use agent_sketchpad; for a diagram use a chart or d2 atom.

## Surfaces

mcp-apps

## Fields

| Field | Type |
|---|---|
| preset | string (optional). A ready-made place; supplies backdrop, ground, stage, camera, scenery and actors. One of: arctic-station, boardroom-meeting, call-centre, ci-cd-factory, city-skyline, construction-site, container-port, data-centre, desert-oasis, drone-delivery, factory-assembly-line, farm-harvest, fire-station-response, forest-campfire, highway-interchange, hospital-helipad, hospital-ward, hydro-dam, kanban-war-room, keynote-stage, laboratory-bench, library-archive, lighthouse-coast, message-post-office, metro-station, mine-quarry, mission-control, museum-gallery, observatory-night, offshore-platform, open-office, railway-station, restaurant-kitchen, river-ferry, school-classroom, ski-resort, solar-farm, space-station-orbit, street-market, substation-grid, trading-floor, vertical-farm, warehouse-logistics, water-treatment, wind-farm. |
| title | string (optional, max 80 chars). Accessible name and caption. Default is the preset id. |
| seed | integer (optional, 0..4294967295). Varies cloud and star placement. Default derives from the preset. |
| theme | {time: "dawn"|"day"|"dusk"|"night", weather: "clear"|"cloudy"|"overcast", setting: "countryside"|"coast"} (optional). Default day, clear, countryside. Interiors dim with the time of day. |
| motion | {duration: number 6..40} (optional, seconds per loop). Default 20. |
| camera | {mode: "static"|"pan"|"push-in"} (optional). The preset has a default; without a preset the default is static. |
| accent | string (optional, #rrggbb). Tints props that take an accent colour. |
| backdrop | "sky-city"|"sky-hills"|"sky-sea"|"sky-mountains"|"sky-desert"|"sky-arctic"|"sky-flat"|"space"|"interior-office"|"interior-industrial"|"interior-lab"|"interior-civic"|"interior-dark" (required when there is no preset). |
| ground | "grass"|"road"|"sand"|"snow"|"concrete"|"water"|"none" (required when there is no preset). |
| stage | {width: 600..4000, zoom: 500..3200, focus_y: -800..200} (required when there is no preset). Scene units: the ground line is y=0 and up is negative. |
| scenery | array (optional, default empty; max 80) of {prop, x, y?, scale? 0.2..5, flip?, variant?}. Props by id from the asset index (https://a2uicatalog.ai/catalogue/assets-index-v1.json); the strict JSON Schema of this block is https://a2uicatalog.ai/catalogue/scene-spec.schema.json. The default y is the prop's ground line. |
| actors | array (optional, default empty; max 30) of {prop, motion: "walk"|"ride"|"drive"|"fly"|"hover"|"orbit", x0, x1, y, period 3..120, phase 0..1, scale?, variant?, ry?}. Movers that loop. |

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
