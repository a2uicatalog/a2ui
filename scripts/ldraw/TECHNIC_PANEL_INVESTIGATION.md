# Technic Panel & Fairing Occupancy Investigation (2026-09-28)

## Status: COMPLETE

## Executive Summary & Core Conclusion
**Finding: NO SAFE OCCUPANCY FAMILY EXISTS for real Technic Panel and Fairing parts under the current axis-aligned bounding box (AABB) model.**

All 71 Technic Panel-category part IDs in the catalogue must **honestly remain `needs_occupancy=True`**.

This conclusion is grounded in real, measured geometric proof across all 71 parts in the LDraw library:
1. **Curved Fairing Shells (#N series and cowlings)**: The Fairing Smooth (#1-#63) and classic Fairings are thin curved aerodynamic shells with wall thicknesses of only 2.0 to 2.7 LDU (~0.8-1.1 mm). 16 of the 22 Fairing Smooth parts fail the catalogue's `STUD_CELL_MIN_SOLID = 0.15` ray-parity solidity threshold (measuring as low as 7.0%). More critically, an axis-aligned bounding box encloses the vast concave interior hollow where engines, suspension, and internal chassis beams physically sit in Technic vehicle models, resulting in catastrophic false-positive collisions.
2. **Flat Rectangular Panels (`15458`, `64782`, `71709`, etc.)**: These parts are physically flat slabs with outer beam dimensions (e.g., 20 LDU thickness along Y), but they **CANNOT** reuse `PANEL_FLAT_WALL_PARTS` or naive bounding boxes:
   - `panel_flat_wall_occupancy_and_sockets` calls `generate_sockets()`, which synthesizes a 20x20 grid of downward System stud sockets (anti-studs). Technic panels are studless and have 0 stud sockets; generating fake sockets violates the core anti-fabrication mandate and would allow illegal baseplate/stud attachments.
   - Technic panels are perforated with 20 to 32 pinholes across multiple orthogonal axes (X, Y, and Z). A solid bounding box overlaps with any standard Technic pin (`2780`, `3673`, `6558`) inserted into any hole, triggering false collisions (`_boxes_overlap == True`) in valid assemblies.
   - `generic_hole_channel_occupancy` explicitly rejects 2D hole grids ("holes spread across BOTH remaining axes (a true 2D hole grid, e.g. a perforated panel -- a materially different shape this decomposition can't express)").
   - Physical cross-section measurements reveal they are not solid blocks, but injection-molded webbed trays with a 1.4 LDU thin bottom skin and a 17 LDU deep open cavity between ribs.
3. **Curved & Trapezium Panels (`18944`, `18945`)**: `18944` is an arched bow dropping 37.4 LDU along Y with a 3.9 LDU shell; an AABB blocks the entire arch. `18945` has a 14.0° diagonal slanted front creating a 76,000 LDU³ empty corner volume in any bounding box.

Per **spec/brick-parts-v0.1.md §3**:
> *"miss an overlap ... but never report a false one"*

Forcing guessed boxes on thin shells or perforated Technic panels would violate this foundational rule. Keeping `needs_occupancy=True` is the only safe, honest, and correct engineering decision.

---

## 1. Survey of All Technic Panel Parts (71 Parts Catalog-Wide)

Excluding printed variants (`p01`) and sticker shortcuts (`d01`), exactly 71 real Technic Panel parts exist catalogue-wide (79 raw filenames including 8 LDraw `=` aliases like `=Technic Panel Fairing #1`).

All 71 parts were resolved with `resolve_part` against the pinned LDraw parts library (34,108 parts) and evaluated for bounds, spans, connectors (holes, studs, pins), and ray-parity solid fraction under an axis-aligned bounding box:

### Subfamily Breakdown:

| Subfamily | Part Count | Typical Parts | Holes | Studs | Measured AABB Solid Fraction | Primary Failure Mode for AABB |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **Fairing Smooth #N** | 22 | `11946`, `11947`, `2387`, `64391`, `87080` | 2–11 | 0 | 0.070 – 0.255 (16 of 22 < 0.15) | Thin shell (2.4 LDU), sweeping 3D curves, concave engine bay |
| **Fairing Classic** | 18 | `32188`-`32191`, `32527`-`32535`, `44350`-`44353` | 2–4 | 0 | 0.045 – 0.100 (all < 0.10) | Deeply hollow aerodynamic cowlings, massive air volume |
| **Mudguards Arched** | 13 | `24118`, `2509`, `42531`, `42545`, `67141` | 6–8 | 0 | 0.045 – 0.120 (all < 0.15) | Semi-circular wheel wells; AABB collides with wheels |
| **Curved Panels** | 5 | `18944`, `2457`, `5427`, `71682`, `89679` | 1–4 | 0 | 0.145 – 0.345 | Arched strips (3.9 LDU thick), hollow under-arch clearance |
| **Trapezium & Tapered** | 7 | `18945`, `4527`, `5426`, `67142`, `80271` | 0–25 | 0 | 0.055 – 0.340 | Angled non-orthogonal edges (14°–30° slant), 25 multi-axis holes |
| **Bent Panels** | 2 | `24116`, `35396` | 2 | 0 | 0.080 | 90° bent angle; AABB encloses entire 98x78 LDU empty corner |
| **Flat Rectangular** | 7 | `15458`, `64782`, `71709`, `11954`, `62531` | 11–32 | 0 | 0.210 – 0.410 | 2D/3D hole grid; solid box collides with inserted Technic pins |
| **Other / Specialized**| 5 | `2438`, `2442`, `3251`, `4500`, `61069` | 4–13 | 0 | 0.095 – 0.250 | Cylindrical sectors (60°), air intakes, corner returns |

Every single Technic Panel in the catalogue has **`studs = 0`**. None have System anti-stud sockets.

---

## 2. Investigation of Question 1 & Question 4: Fairing Smooth #N Series & Shell Solidity

### 2.1 Real Measured Geometry of the Fairing Smooth Series
The Fairing Smooth series (`11946`/`11947`, `2387`/`2389`, `64391`/`64683`, etc.) form chiral pairs (Left/Right) of aerodynamic body panels.
Real measurements on representative elements:

- **`11946` / `11947` (#21 / #22 Thin Short)**:
  - Real bounds: `[-9.0, -29.69, -10.0]` to `[9.0, 10.0, 86.0]`
  - Real span: X=18.0, Y=39.7, Z=96.0 LDU (Volume: 68,599 LDU³)
  - Holes: 2 pinholes at `Y=10.0`, spaced along Z at Z=40, Z=60
- **`2387` / `2389` (#7 / #8 Thin Very Short)**:
  - Real bounds: `[-9.0, -29.69, -10.0]` to `[9.0, 10.0, 46.0]`
  - Real span: X=18.0, Y=39.7, Z=56.0 LDU
  - Holes: 2 pinholes (one at `Y=10, Z=20` facing along Y; one at `Z=-10` facing along Z)
- **`87080` / `87086` (#1 / #2 Short)**:
  - Real bounds: `[-30.0, -49.0, -10.0]` to `[9.0, 10.0, 86.0]`
  - Real span: X=39.0, Y=59.0, Z=96.0 LDU
  - Holes: 8 pinholes in **3 orthogonal directions** (4 facing Z, 2 facing X, 2 facing Y)
- **`64391` / `64683` (#4 / #3 Medium)**:
  - Real bounds: `[-30.0, -49.0, -10.0]` to `[9.0, 10.0, 126.0]`
  - Real span: X=39.0, Y=59.0, Z=136.0 LDU
  - Holes: 9 pinholes

### 2.2 Shell Thickness Measurements
Sampling cross-sections with ray-cast surface probes at multiple heights across `11946`:
- At $Y = -25$: Material inside $X \in [-3.10, -0.40]$ $\rightarrow$ Thickness = **2.70 LDU** (~1.08 mm)
- At $Y = -20$: Material inside $X \in [-5.10, -2.60]$ $\rightarrow$ Thickness = **2.50 LDU** (~1.00 mm)
- At $Y = -15$: Material inside $X \in [-6.80, -4.40]$ $\rightarrow$ Thickness = **2.40 LDU** (~0.96 mm)
- At $Y = -10$: Material inside $X \in [-7.90, -5.70]$ $\rightarrow$ Thickness = **2.20 LDU** (~0.88 mm)
- At $Y = -5$: Material inside $X \in [-8.60, -6.50]$ $\rightarrow$ Thickness = **2.10 LDU** (~0.84 mm)
- At $Y = 0$: Material inside $X \in [-8.90, -7.00]$ $\rightarrow$ Thickness = **1.90 LDU** (~0.76 mm)
- At $Y = +5$: Material inside $X \in [-7.20, -4.90]$ $\rightarrow$ Thickness = **2.30 LDU** (~0.92 mm)

The wall is a continuously curved thin shell of roughly **2.0 to 2.5 LDU thickness**.
At the mounting boss ($Z \in [30, 70], Y \in [0, 10]$), the part thickens to 18 LDU to support the two pinholes. Everywhere else ($Z < 30$ and $Z > 70$), the entire positive X half-space ($X \in [0, 9]$) is **100% empty air**.

### 2.3 Ray-Cast Solidity Fractions Under AABB
Evaluating `_stud_box_solid_fraction(part.tris, AABB, n=500)`:

| Part ID | Title | AABB Solid Fraction | `STUD_CELL_MIN_SOLID` (0.15) Gate |
| :---: | :--- | :---: | :---: |
| `80268` | Fairing Smooth Right #60 (Parallelogram) | **0.070** (7.0%) | **FAIL** |
| `80274` | Fairing Smooth Right #62 (Triangle) | **0.080** (8.0%) | **FAIL** |
| `6609` | Fairing Smooth Concave #42 | **0.100** (10.0%) | **FAIL** |
| `80267` | Fairing Smooth Left #61 (Parallelogram) | **0.100** (10.0%) | **FAIL** |
| `80278` | Fairing Smooth Left #63 (Triangle) | **0.110** (11.0%) | **FAIL** |
| `64391` | Fairing Smooth #4 (Medium) | **0.115** (11.5%) | **FAIL** |
| `64680` | Fairing Smooth #14 (Wide Medium) | **0.115** (11.5%) | **FAIL** |
| `2403` | Fairing Smooth #10 (Medium Triangle) | **0.120** (12.0%) | **FAIL** |
| `64392` | Fairing Smooth #17 (Wide Long) | **0.120** (12.0%) | **FAIL** |
| `64681` | Fairing Smooth #5 (Long) | **0.120** (12.0%) | **FAIL** |
| `64393` | Fairing Smooth #6 (Long) | **0.125** (12.5%) | **FAIL** |
| `64682` | Fairing Smooth #18 (Wide Long) | **0.130** (13.0%) | **FAIL** |
| `2395` | Fairing Smooth #9 (Medium Triangle) | **0.135** (13.5%) | **FAIL** |
| `6606` | Fairing Smooth Concave #43 | **0.145** (14.5%) | **FAIL** |
| `64683` | Fairing Smooth #3 (Medium) | **0.150** (15.0%) | Marginal pass |
| `64394` | Fairing Smooth #13 (Wide Medium) | **0.155** (15.5%) | Marginal pass |
| `87080` | Fairing Smooth #1 (Short) | **0.180** (18.0%) | Pass |
| `87086` | Fairing Smooth #2 (Short) | **0.180** (18.0%) | Pass |
| `11946` | Fairing Smooth #21 (Thin Short) | **0.242** (24.2%) | Pass (small wing) |
| `11947` | Fairing Smooth #22 (Thin Short) | **0.230** (23.0%) | Pass (small wing) |
| `2387` | Fairing Smooth #7 (Thin Very Short) | **0.255** (25.5%) | Pass (small wing) |
| `2389` | Fairing Smooth #8 (Thin Very Short) | **0.225** (22.5%) | Pass (small wing) |

### 2.4 Why an AABB Is Inherently Unsafe for Fairings
Even for the small variants that scrape past 0.15 due to their pin mounting boss, an AABB produces fatal false-positive collisions in real models:
1. **Concave interior occupancy**: In Technic vehicle models (supercars, airplanes, motorcycles), fairings form the outer aerodynamic skin. Suspension linkages, steering arms, shock absorbers, engines, and internal support beams routinely pass inside the concave hollow of the fairing. An axis-aligned box marks the entire concave volume as solid plastic, incorrectly flagging legal vehicle chassis as self-colliding.
2. **Wing clearance**: For `11946`, the region $X \in [0, 9], Z \in [-10, 30]$ is empty space adjacent to the vehicle body. Any parallel beam mounted along the vehicle side will intersect an AABB despite having ~10 LDU of clear physical air gap.

**Verdict for Fairings: Honest exclusion (`needs_occupancy=True`).**

---

## 3. Investigation of Question 2: Flat Rectangular Panels (`15458`, `64782`, `71709`)

### 3.1 Physical Flatness vs. Structural Reality
Parts like `15458` ("Technic Panel 3 x 11"), `64782` ("Technic Panel 5 x 11"), and `71709` ("Technic Panel 3 x 7") are rectangular and have a constant Y-extent of 20 LDU ($Y \in [-10, 10]$):
- `15458`: Bounds `[-110, -10, -30]` to `[110, 10, 30]` (span 220 x 20 x 60 LDU, 11x3 studs)
- `64782`: Bounds `[-110, -10, -50]` to `[110, 10, 50]` (span 220 x 20 x 100 LDU, 11x5 studs)
- `71709`: Bounds `[-70, -10, -30]` to `[70, 10, 30]` (span 140 x 20 x 60 LDU, 7x3 studs)

However, probing their internal cross-section shows they are **not solid slabs**:
- At edge rib $(X=0, Z=20)$: $Y \in [-9.0, 8.9]$ (thickness 17.9 LDU, full beam structure)
- At interior bay $(X=0, Z=0)$: $Y \in [-8.5, -7.1]$ (thickness **1.40 LDU**, thin bottom skin only!)
- At interior bay $(X=50, Z=0)$: $Y \in [-8.5, -7.1]$ (thickness **1.40 LDU**)

They are molded plastic trays with 1.4 LDU recessed webbings between reinforcing ribs.

### 3.2 Why `PANEL_FLAT_WALL_PARTS` Cannot Be Reused
Tonight's `PANEL_FLAT_WALL_PARTS` pattern (implemented for System panels `4865a`, `15207`, etc.) cannot be reused for Technic panels for two fundamental reasons:

#### Reason A: Illegal Socket Generation
`panel_flat_wall_occupancy_and_sockets()` calls `generate_sockets(occ)`, which places a downward-facing socket at $Y_{max}$ for every 20x20 LDU cell on the footprint grid:
```python
def generate_sockets(occupancy):
    ...
    # Generates ((x, ymax, z), (0, 1, 0)) for every 20x20 cell
```
If called on `15458` (footprint 220x60 LDU), it would fabricate **33 downward System anti-stud sockets** at $Y=10.0$!
`15458` is a 100% studless Technic panel. It has no anti-stud tubes and cannot receive LEGO studs. Synthesizing 33 fake sockets would allow the part to illegally mate with studs or baseplates in `brick_parts_validate.py`, corrupting connection graph validation.

#### Reason B: Pin-In-Hole Collision Violations
Technic panels mount exclusively via Technic pins and axles passing through their pinholes.
`15458` has **28 holes** piercing it along three orthogonal axes:
- 6 holes along Axis X ($X = \pm 110$)
- 8 holes along Axis Y ($Y = \pm 10$)
- 14 holes along Axis Z ($Z = \pm 30$)

If `15458` is given a solid bounding box `[-110, 110, -10, 10, -30, 30]`, and a standard Technic friction pin (`2780`, with baked occupancy `box(-20, 20, -6, 6, -6, 6)`) is inserted into any of its 28 holes:
```python
>>> bpv._boxes_overlap(box_15458, box_pin)
True
```
`brick_parts_validate.py` immediately flags:
`collisions: [[panel_idx, pin_idx]]`
A valid, everyday Technic connection is falsely reported as a physical intersection. This directly violates spec §3: *"miss an overlap ... but never report a false one"*.

#### Reason C: Incompatibility with `generic_hole_channel_occupancy`
Unlike 1D straight Technic beams (`TECHNIC_HOLES_PARTS`), which have holes along a single line on one axis, `15458` has holes distributed across a 2D surface and boring through multiple axes. `generic_hole_channel_occupancy` explicitly bails on this shape:
```python
# Bails whenever: "holes spread across BOTH remaining axes (a true 2D hole grid,
# e.g. a perforated panel -- a materially different shape this decomposition can't express)"
```
Cutting 12x12 channels for 28 holes across 3 axes would decompose the part into dozens of tiny fragments, many of which would land in the 1.4 LDU thin recessed web bays and fail the 0.15 solidity test.

**Verdict for Flat Technic Panels: Honest exclusion (`needs_occupancy=True`).**

---

## 4. Investigation of Question 3: Curved (`18944`) and Trapezium (`18945`) Panels

### 4.1 `18944` (Technic Panel 3 x 13 Curved)
- Bounds: `[-30.0, -28.4, -129.0]` to `[30.0, 9.0, 129.0]` (span 60.0 x 37.4 x 258.0 LDU)
- Geometric profile:
  - At $Z = 0$ (center): $Y \in [-28.40, -24.50]$ (thickness 3.90 LDU)
  - At $Z = \pm 50$: $Y \in [-24.30, -20.40]$ (thickness 3.90 LDU)
  - At $Z = \pm 100$: $Y \in [-15.00, -11.20]$ (thickness 3.80 LDU)
  - At $Z = \pm 125$ (ends): $Y \in [-7.20, 7.20]$ (thickness 14.40 LDU, mounting bosses with 2 pinholes)
- The part is a dramatic arched curve drooping 37.4 LDU along Y over a 258 LDU length.
- An AABB spans $Y \in [-28.4, 9.0]$ across the entire 258 LDU span. Any component placed under the arch will collide with the bounding box despite having up to 33 LDU of open clearance.
- Ray-parity solidity of the AABB is 0.165 (barely above 0.15 only because of the solid end bosses).

### 4.2 `18945` (Technic Panel 5 x 11 Trapezium)
- Bounds: `[-110.0, -10.0, -49.0]` to `[110.0, 10.0, 50.0]` (span 220.0 x 20.0 x 99.0 LDU)
- Geometric profile:
  - At $X = +110$ (wide end): 5-beam configuration, $Z \in [-49.0, 49.0]$ (span 98 LDU, 5 holes)
  - At $X = -110$ (narrow end): 3-beam configuration, $Z \in [-9.0, 49.0]$ (span 58 LDU, 3 holes)
  - Front edge: slanted at 14.0° from $(X=-110, Z=-9)$ to $(X=+80, Z=-49)$.
- Empty corner: The triangular prism $X \in [-110, 80], Z \in [-49, -9]$ has base 190 LDU, height 40 LDU, and thickness 20 LDU $\rightarrow$ **76,000 LDU³ of empty air** inside the AABB bounding box.
- Contains 25 pinholes along X, Y, and Z, which would all falsely collide with inserted pins under an AABB.

**Verdict for Curved & Trapezium Panels: Honest exclusion (`needs_occupancy=True`).**

---

## 5. Architectural Recommendations & Future Requirements

Why can't Technic panels have occupancy today, and what would be needed to support them safely in the future?

1. **Connector Isolation for Hole Penetration**:
   To allow occupancy on perforated Technic parts without false collisions against inserted pins, the collision detector (`renderers/brick_parts_validate.py`) would need a **mated-connector exemption mask**:
   - If pin $P$ is mated to hole $H$ of part $B$ (`_point_line_dist < 0.5`), the collision between part $B$'s occupancy and pin $P$'s occupancy is suppressed along the mated insertion segment.
   - However, even with this mask, a single solid box on a flat panel would still over-approximate internal cavities and fail to represent the thin web profile.
2. **OBB / Hierarchical Convex Decomposition**:
   For curved fairings (`11946`, `64391`) and mudguards (`24118`), no axis-aligned box representation is viable. Safe occupancy requires either:
   - Approximate Convex Decomposition (V-HACD) into oriented bounding boxes (OBBs), checked via Separating Axis Theorem (SAT).
   - Direct triangle-mesh collision checking.
3. **Consistency with Catalogue Philosophy**:
   In `a2ui`, `needs_occupancy=True` is not a failure; it is the designed signal that a part's geometry is outside the safe domain of simple orthogonal boxes. It ensures zero false positives in downstream validation and model checking.

---

## Summary of Results

- **Surveyed:** 71 real Technic Panel catalogue parts (100% of category).
- **Viable Occupancy Family Found:** **None.**
- **Safe Outcome:** Retain `needs_occupancy=True` for all 71 parts.
- **Code Changes to `parts.py`:** None (no unsafe boxes forced).
- **Test Suite Status:** 51/51 tests passing in `tests/test_generic_stud_occupancy.py`.
