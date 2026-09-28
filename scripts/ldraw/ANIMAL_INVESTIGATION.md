# Animal Part Occupancy Investigation (2026-09-28)

## Status: COMPLETE

## Executive Summary
This investigation analyzed real Animal-category parts across the catalogue and LDraw library to determine whether a shared geometric occupancy family, generic rule, or safe `OVERRIDES` entry exists.

**The confident, evidence-backed conclusion is that NO shared occupancy family exists for Animal figures, and the vast majority of this category must honestly remain `needs_occupancy=True`.**

Key findings:
1. **Physical Silhouette & Volume Ratios**: Individually-sculpted animal figures (bat, parrot, owl, frog, cat, horse) are hollow shells or thin organic curves occupying only a tiny fraction of their bounding boxes. For example, `30103` (Bat) is **2.6% solid**, `40232` (Owl) is **2.5% solid**, `2546` (Parrot) is **3.7% solid**, `20308` (Head Cuboid) is **1.9% solid**, and `4493c01` (Horse) is **9.3% solid**. Over 90% to 98% of their bounding box volume is open air. Proposing a bounding box occupancy directly violates the foundational safety invariant of `a2ui` (spec section 3: *"miss a real collision on the dropped area, never report a false one"*) by claiming phantom plastic across large regions of open space.
2. **Candidate `24946` (Animal Egg)**: An egg shape is closer to a solid primitive than a sculpted animal silhouette, but forensic analysis proves it **cannot be safely covered by an axis-aligned box override**:
   - The egg is an axisymmetric hollow shell of dimensions 24 x 24 x 32 LDU (1.2 x 1.2 x 1.333 studs). The interior has a hollow cylindrical cavity of radius 5.5 LDU spanning Y = -5.5 to -24.
   - At its tapered top (Y = -32 to -24), the outer diameter narrows to radius 2.0–4.0 LDU.
   - Any 20x20 or 24x24 box severely protrudes into open air at the top (corners extend to distance 14.1–17.0 LDU, over 3x the egg's actual width at that height), triggering `part_checks.py` warnings that 65%–74% of the occupancy volume lies outside the mesh (`OCC_OUTSIDE_WARN = 0.60`).
   - A 24x24 box also causes `generate_sockets()` to produce an off-grid socket at `(-2, 0, -2)`, 2 LDU off the true origin `(0, 0, 0)`.
   - Inscribed boxes centered at the origin fall entirely into the hollow internal cavity (measuring 0.00 solid fraction for half-width 4 LDU).
3. **Stud-Bearing Candidates (`4493c01`/`4493c02` Horse and `64648` Fish)**:
   - Neither requires any new code; existing safety mechanisms already reject them appropriately:
   - `4493c01`/`4493c02` (Horse Complete) has 2 flush studs at Y=0 on its back. `generic_stud_cell_occupancy` tests stud-cell columns spanning the horse's full vertical extent (Y = -89.0 to 57.0). Because the column spans open air above the back (Y < 0) and under the arched belly (Y > 24), its measured solid fractions are **0.0750** and **0.0850**, well below `STUD_CELL_MIN_SOLID = 0.15`. It is already correctly rejected.
   - `64648` (Fish Straight) has 1 stud at its mouth facing in -Z. The candidate 20x20 SNOT box has width 20 LDU in X (`[-10, 10]`), but the fish body is only 15.05 LDU wide (`[-7.525, 7.525]`). The box overflows the mesh bounds by 2.5 LDU on each side and is caught and rejected by `_boxes_within_bounds()` in `resolve_occupancy_and_sockets()`.
4. **Already-Handled Animal Parts in the Library**:
   - A full library scan of 419 animal candidates reveals that **52 animal parts already resolve cleanly with `needs_occupancy=False`**.
   - 43 of these are accessories resolved via `bar_grip_points()` (horns, wings, tails, webs with bars/clips).
   - 9 are brick-like animal components with genuine solid stud grids (e.g. `18904c01` Crocodile 4x9 body, `52258` Hungarian Horntail Dragon body, `4494c01` Horse body).
   - What remains rejected is solely the pool of organic, sculpted creature figures.

---

## 1. Real Measured Geometry & Solidity Analysis

The 13 representative Animal-category parts surveyed, showing exact bounding box volume, true signed mesh volume, volume solidity ratio, and ray-parity solid fraction (`_stud_box_solid_fraction` with fixed seed 20260926, n=200):

| Part ID | Description | Studs | Bounding Box Extents (LDU) | BBox Vol (LDU³) | Mesh Vol (LDU³) | Vol Ratio | Ray BBox Solid (n=200) | GenOcc Result |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| `15429` | Animal Cat Tail | 0 | `(-10.0, -13.5, -10.0)..(10.0, 32.0, 28.6)` | 35,081 | 14,334 | 0.4086 | 0.3300 | `None` |
| `20308` | Animal Head Cuboid | 0 | `(-20.0, -20.0, -41.0)..(20.0, 20.0, 10.0)` | 81,600 | 1,564 | **0.0192** | 0.2250 | `None` |
| `24946` | Animal Egg 1.2x1.2x1.333 w/ Hole | 0 | `(-12.0, -32.0, -12.0)..(12.0, 0.0, 12.0)` | 18,432 | 3,327 | 0.1805 | 0.3700 | `None` |
| `2546` | Animal Bird Parrot | 0 | `(-11.8, -49.8, -13.7)..(11.8, 24.0, 14.7)` | 49,071 | 1,812 | **0.0369** | 0.2650 | `None` |
| `30103` | Animal Bat | 0 | `(-28.2, -39.6, -7.8)..(28.2, 0.0, 8.5)` | 36,591 | 962 | **0.0263** | 0.1700 | `None` |
| `30115` | Animal Snake | 0 | `(-12.5, -8.2, -33.2)..(13.4, 0.0, 70.4)` | 22,159 | 5,575 | 0.2516 | 0.2200 | `None` |
| `33320` | Animal Frog | 0 | `(-11.3, -22.7, -18.7)..(11.3, 0.0, 10.4)` | 14,911 | 0.0* | 0.0000* | 0.2450 | `None` |
| `40232` | Animal Owl | 0 | `(-16.3, -63.8, -22.8)..(16.3, 0.0, 25.9)` | 101,476 | 2,551 | **0.0251** | 0.2450 | `None` |
| `40234` | Animal Rat | 0 | `(-11.4, -23.4, -26.4)..(12.9, 0.0, 63.7)` | 51,161 | 17,104 | 0.3343 | 0.2600 | `None` |
| `4493c01` | Animal Horse (Complete) | 2 | `(-20.0, -89.0, -96.1)..(20.0, 57.0, 86.0)` | 1,063,668 | 99,118 | **0.0932** | 0.2450 | `None` |
| `4493c02` | Animal Horse (Complete w/ Tack) | 2 | `(-20.0, -89.0, -96.1)..(20.0, 57.0, 86.0)` | 1,063,667 | 99,118 | **0.0932** | 0.2450 | `None` |
| `50687` | Animal Rat Standing | 0 | `(-14.1, -46.0, -22.6)..(12.0, 4.0, 15.8)` | 50,166 | 16,504 | 0.3290 | 0.3400 | `None` |
| `6251` | Animal Cat Crouching | 0 | `(-14.9, -36.8, -21.9)..(14.9, 0.0, 27.3)` | 53,910 | 0.0* | 0.0000* | 0.2450 | `None` |
| `64648` | Animal Fish Straight | 1 | `(-7.5, -14.4, 0.0)..(7.5, 11.1, 56.9)` | 21,837 | 8,075 | 0.3698 | 0.3850 | `[1 box]`** |

*\* Mesh volume is 0.0 because the LDraw mesh contains unoriented / non-manifold shell polygons (see Section 4).*  
*\*\* `generic_stud_cell_occupancy` generates 1 candidate box, but `resolve_occupancy_and_sockets()` immediately discards it via `_boxes_within_bounds()` because the 20 LDU box exceeds the fish's 15.05 LDU width (see Section 3).*

### Why Bounding Box Occupancy Is Unsound For Sculpted Animals
In `a2ui`, occupancy boxes are used by `renderers/brick_parts_validate.py` for spatial collision detection (`_boxes_overlap()`).
Under spec section 3:
> *"Occupancy is deliberately under-approximated (spec section 3: under-approximation is always safe): miss a real collision on the dropped area, never report a false one."*

If an animal figure's full bounding box were accepted as occupancy:
- For `30103` (Bat): The wingspan is 56.5 LDU wide, but the body is only 6 LDU thick and 16 LDU deep. The bounding box claims a solid block of 36,591 LDU³, of which **97.4% is open air**. Placing any brick beside the bat's feet or under its wings triggers a false collision against empty space.
- For `2546` (Parrot): Total volume is 49,071 LDU³, but **96.3% is empty air**. The tail hangs 24 LDU below the perch (`Y=24`), while the head rises 49.8 LDU above (`Y=-49.8`). Placing a perch brick or adjacent accessory brick falsely collides with the giant air box.
- For `4493c01` (Horse Complete): The bounding box is 40 x 146 x 182 LDU (over 1,063,000 LDU³). The volume under the horse's belly between front and back legs (height 33 LDU, length ~80 LDU), the volume in front of the chest, and the volume above the back are all empty space. An occupancy box over the bounding box would prevent placing saddles, riders, carts, or ground vegetation anywhere near the horse.

---

## 2. Forensic Investigation of Candidate `24946` (Animal Egg)

`24946` ("Animal Egg 1.2 x 1.2 x 1.333 with Hole on Top") was identified in the task brief as the most plausible candidate for an override due to its convex rotational profile.

### Geometry Profile
Inspecting `24946.dat` directly:
- Bounds: `X: [-12.0, 12.0]`, `Y: [-32.0, 0.0]`, `Z: [-12.0, 12.0]`.
- Title: 1.2 x 1.2 x 1.333 studs (24 x 24 x 32 LDU).
- Rotational cross-section measured at 4 LDU intervals along Y:
  - `Y =   0` (bottom rim): `min_r = 6.00`, `max_r = 8.00`
  - `Y =  -4`: `r = 10.0`
  - `Y =  -8`: `r = 11.5`
  - `Y = -12` (equator / max width): `r = 12.0`
  - `Y = -16`: `r = 11.5`
  - `Y = -24`: `min_r = 2.36`, `max_r = 5.50`
  - `Y = -28`: `min_r = 2.00`, `max_r = 5.00`
  - `Y = -32` (top hole): `min_r = 2.00`, `max_r = 4.00`

### Hollow Interior
`24946.dat` is not a solid lump of plastic; it contains:
1. `4-4cylo.dat` at `(0, 0, 0)`, radius 6.0 LDU, depth 5.5 LDU (bottom socket cavity).
2. `4-4cyli.dat` at `(0, -5.5, 0)`, radius 5.5 LDU, height 18.5 LDU (central hollow cavity from Y = -5.5 to -24).
3. `4-4cylo.dat` at `(0, -32, 0)`, radius 2.0 LDU, depth 4.0 LDU (top pin/feather hole).

### Why Every Candidate Box Fails
1. **Full Bounding Box `box(-12, 12, -32, 0, -12, 12)`**:
   - Volume = 18,432 LDU³. Mesh solid volume = 3,327 LDU³.
   - Sample points outside mesh: **74.0%**.
   - `part_checks.py` triggers an error/warning:
     `'74% of the occupancy volume lies outside the mesh (much larger than the part?)'` (exceeds `OCC_OUTSIDE_WARN = 0.60`).
   - At the corners `(±12, y, ±12)`, the radial distance is $\sqrt{12^2 + 12^2} = 16.97$ LDU. At the top (`Y = -32`), the real egg radius is only 4.0 LDU. The box corners stick out into open air by **13 LDU** (more than 3x the egg's width).
   - Furthermore, `generate_sockets()` computes `x0 + 10 = -12 + 10 = -2` and `z0 + 10 = -2`, fabricating a misaligned socket at `((-2, 0, -2), (0, 1, 0))` instead of the true center `(0, 0, 0)`.
2. **Standard 20x20 Stud-Cell Box `box(-10, 10, -32, 0, -10, 10)`**:
   - Volume = 12,800 LDU³. Sample points outside mesh: **65.0%** (exceeds `OCC_OUTSIDE_WARN = 0.60`).
   - At `Y = -28`, the real egg has radius 5.0 LDU. The box corners are at distance $\sqrt{10^2 + 10^2} = 14.14$ LDU, protruding into empty air by 9.14 LDU.
3. **Inscribed Centered Box `box(-4, 4, -32, 0, -4, 4)`**:
   - Because the interior has a hollow cylinder of radius 5.5 LDU, any box with half-width $\le 4$ LDU lies **entirely inside the empty hollow cavity**.
   - Measured solid fraction: **0.0000** for Y in `[-16, 0]` and `[-24, 0]`, and **0.0950** for full height. It has virtually no solid material.
4. **Conclusion on `24946`**:
   `24946` cannot be represented by a box override. Any box wide enough to touch the solid shell over-approximates the tapered top and produces false collisions; any box small enough to fit inside the top falls into the hollow internal air cavity. It must remain `needs_occupancy=True`.

---

## 3. Stud-Bearing Animal Parts Analysis

The catalogue contains several Animal-category parts with studs. We tested whether `generic_stud_cell_occupancy()` accepts or rejects them.

### `4493c01` and `4493c02` (Animal Horse Complete)
- Real studs: 2 studs on the horse's back at `(-10, 0, 0)` and `(10, 0, 0)`, facing up `(0, -1, 0)`.
- Vertical bounds: `Y = -89.0` (ears) to `Y = 57.0` (hooves). Total height = 146 LDU.
- When `generic_stud_cell_occupancy()` evaluates each flush stud, it tests a 20x20 column spanning the part's full Y extent: `box(-20, 0, -89.0, 57.0, -10, 10)` and `box(0, 20, -89.0, 57.0, -10, 10)`.
- Ray-parity solidity measured against the real mesh:
  - Stud 1: **0.0750** (7.5%)
  - Stud 2: **0.0850** (8.5%)
- Both values are strictly below `STUD_CELL_MIN_SOLID = 0.15`.
- **Verdict**: The existing ray-cast proof already correctly rejects both studs. No new code is needed; the horse remains safely rejected.

### `64648` (Animal Fish Straight) and `8043` (Fish Skeleton)
- `64648` has 1 stud at the mouth: `pos=(0.0, 0.0, 0.0)`, `dir=(0.0, 0.0, -1.0)` (SNOT stud along Z).
- When evaluated by `generic_stud_cell_occupancy()`, the SNOT logic creates a 20x20 box across X and Y: `box(-10.0, 10.0, -10.0, 10.0, 0.0, 56.9)`.
- Solid fraction of this box is 0.3850 (passes `STUD_CELL_MIN_SOLID`).
- **However**, the physical fish mesh bounds are:
  - `min = [-7.525, -14.4, 0.0]`
  - `max = [7.525, 11.1, 56.9]`
- The fish is only **15.05 LDU wide** in X. The candidate 20 LDU box (`[-10, 10]`) sticks out by 2.475 LDU beyond the fish on both the left and right sides.
- When `resolve_occupancy_and_sockets()` passes this box to `verified(occ, sockets)`:
  `_boxes_within_bounds()` checks `x0 >= bounds_min[0] - 0.5` (`-10.0 >= -8.025` is `False`).
- **Verdict**: The bounds verification gate catches the overflow and returns `(None, [], True)`. The fish remains safely rejected. The same mechanism rejects `8043` (Fish Skeleton, width 13.28 LDU).

### Complete Survey of All Stud-Bearing Animal Parts
Across all 36 stud-bearing parts in the LDraw library:
- **Accepted with real occupancy (9 parts)**:
  - `18904c01` (Crocodile 4x9): 6 flush studs on its back; full solid brick body beneath them.
  - `18970` (Clam Lower Half with 2x2 Plate): 2 flush studs on a standard plate base.
  - `24196` (Dragon Head Elves): 1 flush stud.
  - `26074` (Penguin): 1 SNOT stud within bounds.
  - `43746` (Serpent Basilisk Head): 3 flush studs.
  - `4491b` (Horse Saddle with 2 Clips): 1 flush stud.
  - `4494c01` (Horse Body): 1 flush stud on back.
  - `52258` (Dragon Body Hungarian Horntail): 8 flush studs on back.
  - `80672a` (Animal Felid): 1 flush stud on back.
- **Correctly Rejected (27 parts)**:
  - `10352c01` / `10509` / `4493c00-05` / `59228` / `93085` (Horse variants): hollow underbelly/tall neck, stud columns measure 5%–11% solid (< 0.15).
  - `1570` (Sheep Fleece): stud column measures 0.1400 (< 0.15).
  - `2490` (Horse Barding): stud columns measure 0.0950 and 0.1000 (< 0.15).
  - `75174` / `75174c01` (Dragon Body): stud columns measure 0.0833 to 0.1458 with n=48 (< 0.15).
  - `64648` / `8043` (Fish): candidate 20x20 box overflows narrow 15 LDU / 13 LDU body bounds.
  - `11241`, `24199`, `30218-f1/f2`, `37297`, `4587`, `6245`, `80497`, `93086`: studs are non-flush (positioned at Y = -72, -5, -8, +70, -21, -96, +64, -40.8).

---

## 4. Mesh Non-Manifoldness and Edge Discontinuities

Running `scripts/ldraw/part_checks.py` on these sculpted animal parts revealed significant geometric non-manifoldness:
- `30115` (Animal Snake): **651 open edges**, 2 non-manifold edges.
- `4493c01` (Animal Horse Complete): **496 open edges**, **230 non-manifold edges**.
- `64648` (Animal Fish): **150 open edges**, 8 non-manifold edges.
- `40234` (Animal Rat): **114 open edges**, 3 non-manifold edges.
- `33320` (Animal Frog) and `6251` (Animal Cat Crouching): signed volume is **0.0 LDU³** because the mesh is composed of zero-thickness open sheets and unoriented faces.

### Impact on Point-in-Mesh Algorithms
Ray-parity testing relies on the Jordan curve theorem in 3D: a closed, watertight 2-manifold divides space into an interior and exterior, and any ray from infinity has an odd number of surface intersections if and only if the test point is inside.
When a mesh has 100–600 open boundary edges (e.g. unclosed seams between body segments, hollow leg bases), rays escaping through boundary gaps do not increment the intersection counter. This causes ray parity to become direction-dependent and produce phantom "inside" hits in open air.
This further reinforces why automatic solid-fraction proofs cannot reliably construct synthetic bounding boxes for sculpted animal meshes.

---

## 5. Architectural Conclusion & Recommendations

1. **No Shared Geometric Family Exists**: Unlike `ROUND_PARTS`, `TYRE_PARTS`, or `SLOPE_BACK_WALL_PARTS`, Animal-category parts are organic, sculpted artistic meshes. They share no geometric primitive structure (no common radius, extrusion axis, or planar wall).
2. **`needs_occupancy=True` Is The Correct Status**: Maintaining `needs_occupancy=True` for these 19 parts is the honest, specification-compliant behavior. Proposing box approximations would report false collisions in models.
3. **Existing Gates Function As Designed**: `generic_stud_cell_occupancy()` and `_boxes_within_bounds()` already correctly reject all non-solid or out-of-bounds stud candidates in this category without modifications.
4. **Future Path**: If collision support for organic animal figures is desired in the future, it should be implemented via:
   - Oriented Bounding Boxes (OBB) or hierarchical convex hulls (e.g. separate boxes for torso, head, and legs, authored per part).
   - Alternatively, an explicit `is_decorative_figure` property that relaxes collision requirements while documenting that the part does not support stacking.
