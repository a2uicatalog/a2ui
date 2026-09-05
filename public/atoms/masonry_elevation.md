# Masonry Elevation

Coursed block/brick wall elevation — draws courses bottom-up from wall-shape inputs (dimensions, per-block dimensions, course/per-course counts, bond pattern), with a running-bond half-unit stagger on alternate courses or none for stack bond. Draws the geometry itself from the given shape rather than taking a pre-computed rectangle list, so a caller only needs to hand it the same numbers a wall-calculation tool already produced.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| width_mm | number. Actual built width in mm — the ROUNDED-to-whole-courses value (e.g. a calc tool's actual_w_mm), not the raw requested width, or the last partial course/column silently clips. |
| height_mm | number. Actual built height in mm, same rounding caveat as width_mm. |
| unit_l_mm | number. Per-block coordinating length in mm (block face length plus one mortar joint). |
| course_h_mm | number. Per-course coordinating height in mm (block face height plus one mortar joint). |
| courses | integer. Number of courses (rows), bottom to top. |
| per_course | integer (optional, echoed/validated only — width_mm/unit_l_mm already bound the draw loop). |
| pattern | string, "running" (half-unit stagger on alternate courses) or "stack" (no stagger, default "running"). |
| colour | string (optional hex, default |
| label | string (optional heading caption above the elevation). |
| stats_line | string (optional caption below the elevation, e.g. dimensions/ unit-count/weight summary — compose it from your calc result rather than having this atom re-derive display text). |
| render_style | string (optional), "flat" (solid fill, default), "textured" (alternating per-block shade for a material-variation look), or "blueprint" (dark ground, outline-only strokes, technical-drawing register). |

## Example payload

```json
{
  "type": "masonry_elevation",
  "width_mm": 1,
  "height_mm": 1,
  "unit_l_mm": 1,
  "course_h_mm": 1,
  "courses": 1
}
```

Live page: https://a2uicatalog.ai/atoms/masonry_elevation/
Full field contract: https://a2uicatalog.ai/spec.json
