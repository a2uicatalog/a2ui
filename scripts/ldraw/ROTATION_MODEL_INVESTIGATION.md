# Arbitrary Rotation Model Investigation (2026-09-27)

## Status: IN PROGRESS

## What I'm checking
- Real scale of non-axis-aligned rotations across real LDraw OMR sets (examining 3-5 sets directly, citing real part IDs and rotation matrices).
- Prior art in LDraw-ecosystem tools (LDCad, LeoCAD, LDraw spec, BrickLink Studio) for representing and collision-checking arbitrary rotations (continuous vs discrete/quantised, OBB/SAT vs AABB).
- Concrete scope of required changes across:
  - `renderers/brick_parts_validate.py` (`_world_boxes`, `_boxes_overlap`, `PART_ROT`/`rot_index`) and JS twin `apps-script-surface/gas-wired-renderer/atoms_brick.gs`.
  - `scripts/ldraw/omr_import.py` (`rot_index` and transform representations).
  - Occupancy boxes (`box(x0,x1,y0,y1,z0,z1)`) and existing occupancy families (`ROUND_PARTS`, `TYRE_PARTS`, stud grids, etc.).
  - Size/complexity estimation grounded in findings.

## Findings so far

### 1. Measured Evidence and Ground Truth (Baseline)
- From 133 real LDraw OMR sets:
  - 131,960 real part instances.
  - 90,305 (68.4%) have their part id in `public/parts/index.json`.
  - Only 64,083 (48.6% of the total) are renderable.
  - 26,222 (19.9% of the total) are baked but sit at a rotation matrix that `PART_ROT` (24 fixed axis-aligned rotations) and `rot_index()` cannot match.
  - A classification of 26 real sets with tilted instances showed:
    - 18 near-misses (tolerance issue, `tol=0.02`).
    - 7 pure reflections (`det ~ -1`, mirrored parts).
    - 6,106 (99.6%) genuinely non-axis-aligned placements with no close match to any of the 24 fixed rotations.
  - Only 1 of the 133 sampled sets currently renders 100% (`1869-1`, 82 parts).
  - The rotation model is the dominant remaining bottleneck to rendering complete real sets.

### 2. Empirical Scale & Real Examples from OMR Sets
*(To be investigated: examining 3-5 real sets, citing real part IDs and rotation matrices)*

### 3. Prior Art in the LDraw Ecosystem
*(To be investigated: LDCad, LeoCAD, LDraw spec, BrickLink Studio)*

### 4. Architectural Scope & Component Changes
*(To be scoped: brick_parts_validate.py & atoms_brick.gs, omr_import.py, occupancy boxes & families)*

### 5. Effort and Complexity Estimate
*(To be scoped)*

## Conclusion
*(To be completed)*
