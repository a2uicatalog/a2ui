# Technic Panel & Fairing Occupancy Investigation (2026-09-28)

## Status: IN PROGRESS

## Task & Scope
Investigate real Technic Panel and Fairing parts (71 real Technic Panel-category part IDs catalog-wide, currently all `needs_occupancy=True`) for a viable occupancy family.
Standard of rigor: same honesty and empirical verification as `scripts/ldraw/HINGE_INVESTIGATION.md`. "No safe pattern found" is a legitimate and acceptable outcome where geometry does not support a safe box approximation.

## Questions to Investigate
1. **The "Fairing Smooth #N" series** (`11946`, `11947`, `2387`, `2389`, and all other numbered variants catalog-wide):
   - Survey the complete list of Fairing Smooth parts in LDraw.
   - Do they share a provable common structure (consistent thin-shell thickness, consistent solidity-proof envelope)?
   - Or is each a distinct 3D spatial curve requiring individual verification or honest exclusion?
2. **Flat / Rectangular Technic Panels** (`15458` "Technic Panel 3 x 11", etc.):
   - Are these actually FLAT?
   - How do their pinholes / pin-sockets / axle holes interact with occupancy?
   - Could they reuse the `PANEL_FLAT_WALL_PARTS` or `generic_hole_channel_occupancy` or do they have distinct 2D hole grids / ribbing?
3. **Curved & Shaped Panels** (`18944` "Curved", `18945` "Trapezium", etc.):
   - Measure real geometry, thickness, curvature, and hole layouts.
   - Determine whether individual treatment or honest exclusion is appropriate.
4. **Thin Curved Shell Solidity & Axis-Aligned Bounding Box (AABB) Safety**:
   - What is the actual ray-cast solid fraction under an axis-aligned bounding box?
   - Does it pass or fail the `STUD_CELL_MIN_SOLID = 0.15` threshold?
   - Would an axis-aligned box cause false collisions in legitimate assemblies?
