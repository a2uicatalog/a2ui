# Brick Build 3D

Equation-driven toy-brick 3D model that assembles itself stud by stud, drawn in real brick proportions (8 mm pitch, 9.6 mm brick) with dependency-free WebGL — key-light shadows cast between parts, glossy plastic shading and an outline on every part edge, like an instruction-booklet render — and a canvas-2D fallback where WebGL is unavailable. Two kinds of model. Toy bricks (bricks or shape) are procedural boxes with studs, from a named shape (heart, sphere, torus, helix, pyramid, house) or an explicit bricks array. Real parts (partsModel) are baked geometry from the LDraw.org Parts Library, under CC BY. Every design is checked by deterministic geometry — collisions, every brick anchored through stud connections (real parts also through pins, hinges, axles and clips), connection count, centre of mass over the footprint — and the verdicts show beside the model. An instructions mode steps through the build layer by layer, and a parts list groups bricks by size and colour with an indicative cost. Known limit, each brick canvas holds two WebGL contexts and a page allows about 16, so keep to about 7 brick canvases per page. Not affiliated with or endorsed by the LEGO Group. LEGO is a trademark of the LEGO Group.

## Surfaces

google-apps-script-web, web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| shape | string (optional). heart, sphere, torus, helix, pyramid or house. Default heart. Ignored when bricks is set. |
| bricks | array (optional). Explicit model — objects {x, y, z, w, d, h, c}. x and z are stud positions, y is the layer (0 sits on the baseplate), w and d the footprint in studs, h the height in bricks (default 1), c a '#rrggbb' colour or a palette index. A brick may also be a compact array [x, y, z, w, d, c] or [x, y, z, w, d, h, c], about a third of the size. Up to 3000 bricks. A data-model binding such as {path '/bricks'} arrives resolved. |
| palette | array (optional). Up to 256 '#rrggbb' colours. A brick's c may be an integer index into it, which keeps large models small. |
| mode | string (optional). animate or steps. Default animate. |
| step | integer (optional). Initial instruction step when mode is steps. Default 1. |
| speed | number (optional). Animation speed multiplier. Default 1. |
| orbit | boolean (optional). Slow auto-orbit; dragging always orbits. Default true. |
| height | integer (optional). Canvas height px, 160 to 900. Default 380. |
| bg | string (optional). Canvas background colour. Transparent on the studio gradient by default. |
| scrubber | boolean (optional). Show the animate/instructions toggle and step slider. Default true. |
| checks | boolean (optional). Show the build-check verdicts. Default true. |
| parts | boolean (optional). Show the parts list with an indicative cost. Default false. |
| models | array (optional). Named models for the picker dropdown — up to 8 objects {name, bricks, palette}, each bricks array as above (up to 3000 bricks each; palette optional, else the top-level one). Entries with no usable bricks are skipped; a missing name becomes Model N. The dropdown lists the six built-in shapes followed by these. |
| model | string (optional). Name of the entry in models to show first. Ignored when bricks is set. |
| picker | boolean (optional). Show the model dropdown. Default true when models is given, otherwise false; set true to get a dropdown of the six built-in shapes alone. |
| partsModel | array (optional). Real parts from the LDraw.org Parts Library (CC BY) instead of procedural boxes, as [partId, x, y, z, rotation, colour] tuples (a real LDraw part id, x y z in LDraw units (20 per stud, 24 per brick height), a 0-23 rotation index, an LDraw colour code), or objects {p, x, y, z, r, c}. Takes precedence over bricks/shape when present, same "explicit wins" rule as bricks vs. shape. Up to 3000 parts. |
| look | "studio" | "instructions" (optional, default "instructions"). instructions: the original building-instructions style (glossy plastic, dark outline on every part edge). studio: a product-shot style — no outlines, edges catch light instead (same visual treatment as the sibling motion_bricks atom, default there). |
| base | string (optional). "none" for floating bricks (no plate, no plate shadow), or a "#rrggbb" colour for the baseplate. Default the classic green plate. |

## Example payload

```json
{
  "type": "brick_build_3d"
}
```

Live page: https://a2uicatalog.ai/atoms/brick_build_3d/
Full field contract: https://a2uicatalog.ai/spec.json
