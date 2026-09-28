# OBB + SAT Collision Geometry Implementation (Python Core)

## Status: COMPLETE (Python core geometry)

## Overview
This document records the Python-only implementation of Oriented Bounding Box (OBB) math and 15-axis Separating Axis Theorem (SAT) collision detection in `renderers/brick_parts_validate.py`, fulfilling items 1–4 of Section 4.1 in `ROTATION_MODEL_INVESTIGATION.md`.

This task intentionally delivers a self-contained, safety-critical Python geometry capability. It is not yet wired into any live consumer, ensuring zero production behavior change or parity drift until follow-up sessions implement the JavaScript twin and pipeline integrations.

---

## What Was Built

### 1. Unified Rotation Dispatch (`rot_ldu`)
`rot_ldu(r, p)` accepts either:
- `int` (`0..23`): looks up the precomputed orthogonal rotation in `PART_ROT[r]`.
- 9-tuple or list of 9 floats: treated directly as a continuous row-major $3 \times 3$ transformation matrix:
  $$\begin{bmatrix} x' \\ y' \\ z' \end{bmatrix} = \begin{bmatrix} m_0 & m_1 & m_2 \\ m_3 & m_4 & m_5 \\ m_6 & m_7 & m_8 \end{bmatrix} \begin{bmatrix} x \\ y \\ z \end{bmatrix}$$

Because connector transformation (`_conn_world`) and hole axis pairing (`hole_segs_world`) in `brick_parts_validate.py` only call `rot_ldu`, connector positions and directions become continuously rotatable immediately with zero additional changes.

### 2. World Occupancy Transformation (`_world_boxes`)
`_world_boxes(mesh, r, ex, ey, ez)` now implements a dual-mode return:
- **Axis-aligned (`isinstance(r, int)`)**: returns the existing list of 6-tuples `(min_x, max_x, min_y, max_y, min_z, max_z)`.
- **Arbitrary matrix (9-tuple/list)**: instantiates an Oriented Bounding Box (OBB) dict for each local box in `mesh['occupancy']`:
  - `center`: world center $C_{world} = \text{rot\_ldu}(r, C_{local}) + (ex, ey, ez)$.
  - `extents`: local half-extents $E = (|x_1 - x_0| / 2, |y_1 - y_0| / 2, |z_1 - z_0| / 2)$.
  - `axes`: $(u_0, u_1, u_2)$, the columns of $M$ representing the oriented box unit axes in world space:
    $$u_0 = (m_0, m_3, m_6), \quad u_1 = (m_1, m_4, m_7), \quad u_2 = (m_2, m_5, m_8)$$
  - `aabb`: enclosing axis-aligned bounding box 6-tuple `(min_x, max_x, min_y, max_y, min_z, max_z)` computed via projection radii:
    $$R_i = E_0 |u_{0, i}| + E_1 |u_{1, i}| + E_2 |u_{2, i}| \quad \text{for } i \in \{x, y, z\}$$
    $$\text{aabb} = (C_x - R_x, C_x + R_x, C_y - R_y, C_y + R_y, C_z - R_z, C_z + R_z)$$

### 3. Two-Tier Collision Overlap Engine (`_boxes_overlap`)
`_boxes_overlap(a, b)` provides:
- **Tier 1 (Fast Path)**: When neither $a$ nor $b$ is a dict (both are 6-tuples from integer rotations), the existing 6-comparison interval overlap check executes directly:
  $$\Delta x > 0.5 \text{ and } \Delta y > 0.5 \text{ and } \Delta z > 0.5$$
  This preserves $O(1)$ microsecond speed for 100% of existing axis-aligned models.
- **Tier 2 (General 15-Axis SAT)**: When either box is an OBB (or both), any 6-tuple is converted to an axis-aligned OBB, and the Separating Axis Theorem is evaluated across 15 candidate axes:
  - 3 axes of Box A: $u_{A0}, u_{A1}, u_{A2}$
  - 3 axes of Box B: $u_{B0}, u_{B1}, u_{B2}$
  - 9 cross-product axes: $u_{Ai} \times u_{Bj}$ for $i, j \in \{0, 1, 2\}$
  - On each candidate axis $L$ (skipping degenerate axes with $\|L\|^2 < 10^{-9}$):
    $$r_A = \sum_{i=0}^2 E_{Ai} |u_{Ai} \cdot L|, \quad r_B = \sum_{j=0}^2 E_{Bj} |u_{Bj} \cdot L|$$
    $$\text{dist} = |(C_B - C_A) \cdot L|$$
    $$\text{If } (r_A + r_B) - \text{dist} \le 0.5 \cdot \|L\|_2 \implies \text{Separated (return False early)}.$$
  - If penetration exceeds $0.5 \cdot \|L\|_2$ across all 15 axes $\implies$ Collision (return True).

### 4. Integration in `validate_parts`
- **Floor collision**: uses `b['aabb'][3] if isinstance(b, dict) else b[3]` to check penetration below the baseplate ($y > 0.5$).
- **80-LDU broadphase grid**: uses `b['aabb']` for OBBs to bucket coarse cells without missing potential collisions.
- **Center of mass & balance**: uses exact invariant OBB volume ($8 \cdot E_x \cdot E_y \cdot E_z$) and $C_{world}$ for mass moments.

---

## Real Test Cases and Verification Results

All tests are implemented in `tests/test_brick_parts_validate.py`.

### 1. Non-Axis-Aligned Matrices Tested (from Real Models)
- **Hinge Plate Pair (`2429`/`2430`) at ~29.7°** (from Technic set `8880-1` Super Car):
  `M_HINGE_29 = (-0.868, 0.0, 0.496, 0.0, 1.0, 0.0, -0.496, 0.0, -0.868)`
- **Metroliner (`10001-1`) 9V Train Cab Matrices**:
  - 30.0° Y-rotation: `(0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)`
  - 60.0° Y-rotation: `(0.5, 0.0, 0.866, 0.0, 1.0, 0.0, -0.866, 0.0, 0.5)`
  - 150.0° Y-rotation: `(-0.866, 0.0, 0.5, 0.0, 1.0, 0.0, -0.5, 0.0, -0.866)`
  - Pantograph arm at 16.5°: `(1.0, 0.284, 0.0, -0.284, 1.0, 0.0, 0.0, 0.0, 1.0)`
- **Technic Chassis Diagonal Brace at 33.9°** (from `8880-1`):
  `M_TECHNIC_33_9 = (0.0, 0.0, -1.0, -0.558, 0.83, 0.0, 0.83, 0.558, 0.0)`

### 2. Empirical Verification Results
- **Hard Regression Check**: All 15 existing fixtures in `tests/fixtures/bricks/parts_parity_cases.json` pass with byte-for-byte identical results (`F01_single_brick` through `F15_pin_one_side`).
- **Axis-Aligned Equivalence**:
  - Touching boxes (gap = 0.0 LDU) $\implies$ No collision.
  - Boundary tolerance checks: 0.49 LDU overlap $\implies$ No collision; 0.50 LDU $\implies$ No collision; 0.51 LDU $\implies$ Collision detected.
  - Random box fuzzing: 1,000 random box pairs tested; 0 mismatches between old interval check and SAT engine.
- **Real Rotated Hinge (No False Collision)**:
  - `2429` (Base) at origin ($r=0$) and `2430` (Top) mated at origin rotated by ~29.7° (`M_HINGE_29`).
  - Naive AABB inflation inflates `2430`'s bounding box to span $x \in [-17.36, 9.92]$, falsely overlapping `2429` by $17.36$ LDU.
  - OBB + SAT correctly proves all box pairs are separated: `report['overlaps'] == 0`, `[0, 1] not in report['collisions']`.
- **Rotated Collision Detection**:
  - Concentric placement and deliberate intersection of `2430` rotated by `M_HINGE_29` overlapping `2429` is correctly flagged by `_boxes_overlap` and recorded in `report['collisions']`.
- **Input Shape Flexibility**:
  - `rot_ldu`, `_world_boxes`, and `_boxes_overlap` verified across integer indices, 9-tuples, and 9-lists.

---

## OMR Importer Integration (`scripts/ldraw/omr_import.py`) — COMPLETE (2026-09-28)

`scripts/ldraw/omr_import.py` now integrates the OBB/SAT collision detection core:
- When `rot_index(m)` returns `None` (non-axis-aligned continuous rotation), `omr_import.py` evaluates candidate placement via `_safe_tilted_indices()`:
  - Generates world OBBs via `_world_boxes(mesh, m, *l['t'])`.
  - Excludes parts without baked occupancy.
  - Exempts intentional mated pin/hole and hinge connections from collision.
  - Evaluates potential overlaps with all adjacent parts using an 80-LDU broadphase spatial grid and the 15-axis SAT core `_boxes_overlap()`.
- Safe parts are counted as `renderable` in `coverage()`.
- `to_parts_model()` emits the continuous 9-tuple matrix directly in output rows for safe parts, and `bottom_y()` calculates floor elevation seamlessly for both integer indices and 9-tuple matrices.
- Tested and verified in `tests/test_omr_import.py` (7 tests passing).
- **Empirically Measured Real-World Impact**: Across 45 official LDraw OMR sets (`real_set_coverage.py`), renderable part instances jumped from 35,207 (57.0%) to 46,248 (74.8%), an increase of **+11,041 real parts rendered (+17.8 percentage points)**:
  - Imperial Star Destroyer UCS (`10030-1`): 13.6% -> 69.6% (+1,702 parts)
  - Millennium Falcon UCS (`10179-1`): 44.5% -> 72.6% (+1,518 parts)
  - Rebel Snowspeeder UCS (`10129-1`): 2.7% -> 82.1% (+1,155 parts)
  - Death Star II UCS (`10143-1`): 46.4% -> 78.3% (+938 parts)
  - Y-Wing Attack Starfighter UCS (`10134-1`): 2.6% -> 61.8% (+883 parts)
  - Metroliner 9V Train (`10001-1`): 24.1% -> 63.6% (+335 parts)

---

## What Is NOT Done Yet (Explicit Next Steps)

The following items are intentionally out of scope for this task and are documented for subsequent sessions:

1. **JavaScript Twin in `apps-script-surface/gas-wired-renderer/atoms_brick.gs`**:
   - Port `worldBoxes`, `boxesOverlap`, and `rotLDU` to match the Python implementation with identical 15-axis SAT math.
   - Run `tests/test_brick_parts_validate_js.py` and `scripts/gen_parts_parity_cases.mjs` to establish JS/Python twin parity.
2. **Live Rendering & Pipeline Integration**:
   - Update WebGL shader / matrix pipeline in `atoms_brick.gs` (`partTp`) to accept 9-element arrays directly.
   - Update Canvas-2D fallback renderer to draw projected OBB wireframes.
   - Update `_partsModelSanitise` and `_brick_parts_model_sanitise` schemas to accept 9-tuple matrix representations.
