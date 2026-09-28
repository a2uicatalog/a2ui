# Multi-Box & Oriented Bounding Box (OBB) Decomposition for Curved Shells: Cross-Cutting Architectural Scoping Investigation (2026-09-28)

## Status: COMPLETE (Architectural Scoping & Cross-Cutting Specification)

---

## Executive Summary

This investigation scopes the implementation of multi-box and Oriented Bounding Box (OBB) decomposition for curved and thin-shell LEGO parts in `a2ui` (`scripts/ldraw/parts.py`, `renderers/brick_parts_validate.py`, and the JavaScript twin `apps-script-surface/gas-wired-renderer/atoms_brick.gs`). It directly addresses the operator-prioritised backlog item `obb-decomposition` (deferred twice before during the Technic panel and windscreen surveys) and establishes the singular geometric primitive required to safely unlock both **Technic Panel fairings/mudguards** and **hollow windscreen canopies**.

### 1. The Core Problem: The Curved Shell Dilemma
In the `a2ui` brick architecture, the foundational geometric safety invariant is mandated by spec section 3:
> *"Occupancy is deliberately under-approximated: miss a real collision on the dropped area, never report a false one."*

Under this rule, reporting false-positive collisions between parts that are validly assembled is fatal. However, physical LEGO components fall into two sharply contrasting topological categories:
1. **Solid/Rectilinear Primitives** (bricks, plates, tiles, beams): these fill rectangular grid cells and align with the primary Cartesian axes ($X, Y, Z$). A small set of axis-aligned bounding boxes (AABBs) tightly wraps their solid material with negligible air error ($V_{\text{mesh}} / V_{\text{bbox}} \ge 0.35$).
2. **Thin Curved Shells** (Technic panel fairings, wheel-arch mudguards, sloped windscreens, cockpit canopies): these consist of thin plastic membranes (thickness $T \approx 1.5\text{--}4.0$ LDU) swept along curved, angled, or parabolic trajectories spanning 40 to 300 LDU across space.

When an Axis-Aligned Bounding Box (AABB) is placed over a curved or sloped shell:
- **Catastrophic Volume Inflation**: An AABB claims the entire rectangular bounding prism. Because the physical shell is thin and hollow, the AABB encloses **7x to 16x more volume than the real plastic** ($V_{\text{mesh}} / V_{\text{bbox}}$ drops to **0.056 – 0.120**).
- **Hollow Interior Invalidation**: In real LEGO models, the hollow space under a windscreen or behind a fairing is not empty waste: it is the **functional interior cavity** where minifigures sit, steering wheels mount, controls are placed, or Technic gearboxes, axles, and liftarms operate. An AABB fills this cavity with phantom solid matter, triggering immediate false-positive collisions on any interior assembly.
- **The Fallback Blind Spot**: When the existing `generic_stud_cell_occupancy()` fallback encounters a windscreen with top studs (e.g. `2437` Windscreen 3x4), it generates two small vertical boxes ($20 \times 32 \times 20$ LDU) beneath the top studs. While this avoids filling the cockpit, it covers only **16.7%** of the part volume, leaving **83.3%** of the windscreen (the entire sloped windshield glass from $Z=10$ to $Z=30$) completely unmodelled. Objects can pass straight through the windshield with zero collision detection. Unstudded canopies (e.g. `11289`, `30083`) and Technic fairings (e.g. `11946`, `24116`) get zero boxes and remain 100% rejected (`needs_occupancy=True`).

### 2. Status Quo Assessment (Built 2026-09-28)
- **Engine Math Landed**: Commit `19c0feb2` / `4e288e69` successfully implemented continuous $3 \times 3$ matrix rotation dispatch (`rot_ldu`) and 15-axis Separating Axis Theorem (SAT) collision detection (`_boxes_overlap`) in `renderers/brick_parts_validate.py`.
- **The Local Representation Gap**: Despite having SAT in the engine, `_world_boxes()` only constructs an OBB when the *part's placement in the world* has an arbitrary 3x3 rotation matrix. In the part's *local coordinate frame*, every box in `mesh['occupancy']` is strictly constrained to an axis-aligned 6-tuple `[min_x, max_x, min_y, max_y, min_z, max_z]`.
- **No Local OBB Primitive**: `scripts/ldraw/parts.py` has no representation, constructor, or validator for oriented boxes in local part space.
- **JavaScript Twin Unimplemented**: `apps-script-surface/gas-wired-renderer/atoms_brick.gs` does not yet implement 15-axis SAT; its `boxesOverlap` and `worldBoxes` functions only support axis-aligned interval arithmetic.

### 3. Key Findings & Empirical Quantification
1. **Full Catalogue Census**: An exhaustive census of the 24,735-part LDraw library reveals **725 curved-shell candidate parts**:
   - **Technic Fairings & Curved Panels**: 110 parts (108 rejected, 2 accepted $\implies$ **98.2% rejected**).
   - **Mudguards & Wheel Arches**: 113 parts (69 rejected, 44 accepted $\implies$ **61.1% rejected**).
   - **Windscreens & Cockpit Canopies**: 502 parts (353 rejected, 149 accepted $\implies$ **70.3% rejected**).
   - **Total Blocked Parts**: **530 parts** catalogue-wide cannot receive safe, accurate collision geometry without OBB decomposition.
2. **Empirical Measurements from Real Geometry**:
   Direct measurements via `resolve_part()` against the real LDraw library across 24 representative parts confirm the severity:
   - `11289` Canopy 4x4x4.667: Bounding volume $890,880$ LDU³, mesh volume $50,648$ LDU³, solidity ratio **0.057 (5.7%)**, ray-parity solidity across BBox **0.085 (8.5%)**. An AABB claims **840,232 LDU³ of empty cockpit air** as solid!
   - `32188` Technic Fairing #3: Bounding volume $1,316,140$ LDU³, mesh volume $108,335$ LDU³, solidity ratio **0.082 (8.2%)**, ray-parity solidity **0.085 (8.5%)**. An AABB claims **1,207,805 LDU³ of empty air** as solid!
   - `24118` Technic Mudguard 15x2x5: Bounding volume $1,161,300$ LDU³, mesh volume $139,817$ LDU³, solidity ratio **0.120 (12.0%)**, ray-parity solidity **0.050 (5.0%)**. An AABB fills the entire wheel arch ($1,021,483$ LDU³), colliding with any installed wheel!
   - `24116` Technic Panel Bent 4x5x3: Bounding volume $458,640$ LDU³, mesh volume $28,532$ LDU³, solidity ratio **0.062 (6.2%)**. A 3-OBB decomposition wraps the part in $\approx 56,880$ LDU³, reducing phantom volume by **87.6%**.
3. **Cross-Cutting Architectural Blocker**:
   OBB decomposition cannot safely unlock Technic panels in isolation. Technic fairings mount to beams via intermediary pins. At the contact flange where the panel rests against the beam, microscopic numerical overlap ($> 0.5$ LDU) triggers false-positive collisions unless the **joint-zone mated-connector exemption mask** (specified in `MATED_CONNECTOR_EXEMPTION_INVESTIGATION.md`) is implemented in parallel.

---

## 1. Forensic Analysis of the AABB Failure on Curved Shells

### 1.1 The Mathematical Mechanics of AABB Inflation
Consider an idealized flat plate of length $L$, width $W$, and thickness $T$, inclined at an angle $\theta \in (0, \pi/2)$ relative to the horizontal $Z$-axis in the $Y-Z$ plane (matching a vehicle windscreen or sloped fairing fin).

```
          Z
          ^        +---------------+  (Z_max, Y_max)
          |       /               /
          |      /   Real Shell  /
          |     /  (thickness T)/
          |    /   Length L    /
          |   +---------------+
          |   | <--- Bounding Box Encloses Massive Empty Triangle ---> |
          +------------------------------------------------------------> Y
```

The physical volume of the shell is:
$$V_{\text{shell}} = L \cdot W \cdot T$$

The enclosing Axis-Aligned Bounding Box (AABB) has extents:
$$\Delta Y = L \sin\theta + T \cos\theta$$
$$\Delta Z = L \cos\theta + T \sin\theta$$
$$\Delta X = W$$

The volume of the AABB is:
$$V_{\text{AABB}} = \Delta X \cdot \Delta Y \cdot \Delta Z = W (L \sin\theta + T \cos\theta)(L \cos\theta + T \sin\theta)$$
Expanding for thin shells where $T \ll L$:
$$V_{\text{AABB}} \approx W \cdot L^2 \sin\theta \cos\theta + W \cdot L \cdot T = \frac{1}{2} W L^2 \sin(2\theta) + V_{\text{shell}}$$

The volumetric over-approximation ratio is:
$$\frac{V_{\text{AABB}}}{V_{\text{shell}}} \approx \frac{L}{2T} \sin(2\theta) + 1$$

For typical LEGO parts:
- Thickness $T \approx 3.0\text{--}4.0$ LDU.
- Length $L \approx 40.0\text{--}100.0$ LDU.
- Angle $\theta \approx 30^\circ\text{--}60^\circ$ ($\sin(2\theta) \approx 0.86\text{--}1.00$).

Evaluating this ratio:
$$\frac{V_{\text{AABB}}}{V_{\text{shell}}} \approx \frac{60}{2(3)} (0.95) + 1 \approx \mathbf{10.5}$$

An AABB claims **10.5 times the actual material volume**. The phantom volume ($\approx 90\%$ of the box) projects directly into the interior cavity of the model.

---

## 2. Real Geometry Measurements & Failure Cases

To ground this investigation in empirical facts rather than conjecture, exact measurements were collected using `resolve_part()` against the real LDraw library (`/opt/a2ui-bootstrap/_ldraw_cache/ldraw`).

### 2.1 Complete Empirical Measurement Table (24 Representative Parts)

| Part ID | Description | Bounds Min [X, Y, Z] (LDU) | Bounds Max [X, Y, Z] (LDU) | BBox Vol (LDU³) | Mesh Vol (LDU³) | Solidity Ratio | Ray-Parity Solidity | Studs | Holes | Current Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Technic Fairings & Panels** | | | | | | | | | | |
| `11946` | Fairing Smooth #21 (Thin Short) | `[-9.0, -29.69, -10.0]` | `[9.0, 10.0, 86.0]` | 68,584 | 15,914 | 0.232 | 0.195 | 0 | 2 | **Rejected** (`needs_occ=True`) |
| `11947` | Fairing Smooth #22 (Thin Short) | `[-9.0, -29.69, -10.0]` | `[9.0, 10.0, 86.0]` | 68,584 | 15,914 | 0.232 | 0.230 | 0 | 2 | **Rejected** (`needs_occ=True`) |
| `24116` | Panel Bent 4 x 5 x 3 | `[-30.0, -9.0, -89.0]` | `[30.0, 69.0, 9.0]` | 458,640 | 28,532 | **0.062** | **0.080** | 0 | 2 | **Rejected** (`needs_occ=True`) |
| `32188` | Panel Fairing #3 | `[-36.53, -58.97, -20.0]`| `[9.0, 58.97, 225.1]` | 1,316,140 | 108,335 | **0.082** | **0.085** | 0 | 4 | **Rejected** (`needs_occ=True`) |
| `32189` | Panel Fairing #4 | `[-9.0, -58.97, -20.0]` | `[36.53, 58.97, 225.1]` | 1,316,140 | 108,335 | **0.082** | **0.055** | 0 | 4 | **Rejected** (`needs_occ=True`) |
| `32190` | Panel Fairing #1 | `[-36.52, -58.97, -20.0]`| `[9.0, 58.97, 125.1]` | 778,988 | 67,936 | **0.087** | **0.060** | 0 | 4 | **Rejected** (`needs_occ=True`) |
| `24119` | Panel Smooth 7 x 2 x 3 | `[-30.0, -49.0, -70.0]` | `[9.0, 10.0, 70.0]` | 322,140 | 34,956 | **0.109** | 0.210 | 0 | 13 | **Rejected** (`needs_occ=True`) |
| **Mudguards & Wheel Arches** | | | | | | | | | | |
| `24118` | Mudguard Arched 15x2x5 | `[-30.0, -89.0, -150.0]`| `[9.5, 9.0, 150.0]` | 1,161,300 | 139,817 | **0.120** | **0.050** | 0 | 8 | **Rejected** (`needs_occ=True`) |
| `2459` | Mudguard Arched 9x2x3 | `[-30.0, -49.0, -90.0]` | `[9.5, 9.0, 90.0]` | 412,380 | — | — | **0.120** | 0 | 6 | **Rejected** (`needs_occ=True`) |
| `18974` | Car Mudguard 4 x 2.5 x 2.333 | `[-40.0, 0.0, -29.85]` | `[40.0, 56.0, 20.0]` | 223,328 | 53,024 | 0.237 | 0.180 | 8 | 0 | Accepted (stud-only base) |
| `24151` | Car Mudguard 4 x 4 | `[-40.0, 0.0, -40.0]` | `[40.0, 32.0, 40.0]` | 204,800 | 69,465 | 0.339 | 0.205 | 16 | 0 | Accepted (stud-only base) |
| **Windscreens & Canopies** | | | | | | | | | | |
| `2437` | Windscreen 3 x 4 x 1.333 | `[-40.0, 0.0, -30.0]` | `[40.0, 32.0, 30.0]` | 153,600 | 34,411 | 0.224 | 0.215 | 2 | 0 | Accepted (stud-only: **83% unboxed**) |
| `3823` | Windscreen 2 x 4 x 2 | `[-40.0, 0.0, -30.0]` | `[40.0, 48.0, 10.0]` | 153,600 | 21,338 | **0.139** | 0.255 | 2 | 0 | Accepted (stud-only: **78% unboxed**) |
| `4594` | Windscreen 2 x 4 x 2 Vertical | `[-40.0, 0.0, -30.0]` | `[40.0, 48.0, 10.0]` | 153,600 | 27,077 | 0.176 | 0.315 | 6 | 0 | Accepted (partial columns) |
| `4872` | Windscreen 3 x 4 x 4 Inverted | `[-40.0, 0.0, -50.0]` | `[40.0, 96.0, 10.0]` | 460,800 | 66,561 | **0.144** | 0.160 | 8 | 0 | Accepted (stud-only base) |
| `18972` | Windscreen 5 x 4 x 1.667 Curved| `[-40.0, -8.0, -70.0]` | `[40.0, 32.0, 30.0]` | 320,000 | 47,688 | **0.149** | 0.155 | 2 | 0 | Accepted (stud-only base) |
| `11289` | Canopy 4 x 4 x 4.667 w/ Handle | `[-40.0, -6.0, -90.0]` | `[40.0, 110.0, 6.0]` | 890,880 | 50,648 | **0.057** | **0.085** | 0 | 0 | **Rejected** (`needs_occ=True`) |
| `30083` | Dome 6 x 6 x 3 with Hinge | `[-60.0, -116.0, -64.0]`| `[60.0, 4.0, 4.0]` | 979,200 | 462,984 | 0.473 | **0.095** | 0 | 0 | **Rejected** (`needs_occ=True`) |
| `30161` | Windscreen 1 x 4 x 1.333 Hinge | `[-40.0, -28.0, -4.0]` | `[40.0, 4.0, 4.0]` | 20,480 | 8,193 | 0.400 | 0.580 | 0 | 0 | **Rejected** (`needs_occ=True`) |
| `6567` | Windscreen 2 x 6 x 2 w/ Glass | `[-60.0, 0.0, -30.0]` | `[60.0, 48.0, 10.0]` | 230,400 | 43,847 | 0.190 | 0.270 | 2 | 0 | Accepted (stud-only: **81% unboxed**) |
| `65632` | Windscreen 6 x 6 x 1.667 Curved| `[-60.0, -8.0, -90.0]` | `[60.0, 32.0, 30.0]` | 576,000 | 45,736 | **0.079** | **0.115** | 4 | 0 | **Rejected** (`needs_occ=True`) |
| `64453` | Windscreen 1 x 6 x 3 | `[-60.0, 0.0, -10.0]` | `[60.0, 72.0, 10.0]` | 172,800 | 21,385 | **0.124** | 0.325 | 2 | 0 | Accepted (side posts only) |
| `19212` | Windscreen 1 x 12 x 4 Trapeze | `[-120.0, 0.0, -10.0]` | `[120.0, 96.0, 10.0]` | 460,800 | 131,658 | 0.286 | 0.240 | 8 | 0 | Accepted (base studs only) |
| `80573` | Windscreen 1 x 14 x 6 Trapeze | `[-140.0, 0.0, -10.0]` | `[140.0, 144.0, 10.0]` | 806,400 | 234,861 | 0.291 | 0.265 | 10 | 0 | Accepted (base studs only) |

---

## 3. Case Studies: Why Current Heuristics Fail

### Case Study 1: Technic Panel Bent 4x5x3 (`24116`)
- **Physical Geometry**:
  - Mounting Flange 1: at $(Y=0, Z=0)$, hole with axis along $X$.
  - Mounting Flange 2: at $(Y=60, Z=-80)$, hole with axis along $X$.
  - Sloped Plate: 3.0 LDU thick plate spanning directly between $(0, 0)$ and $(60, -80)$ at angle $\theta = \arctan(60/80) = 36.87^\circ$.
  - Length along slope: $L = \sqrt{60^2 + 80^2} = 100.0$ LDU (exact 3-4-5 Pythagorean triangle).
  - Width: $W = 60.0$ LDU.
- **The AABB Failure**:
  - An AABB covering the sloped plate spans $\Delta Y = 60.0, \Delta Z = 80.0, \Delta X = 60.0$.
  - AABB volume: $60 \times 80 \times 60 = 288,000$ LDU³.
  - True plate volume: $100 \times 60 \times 3.0 = 18,000$ LDU³.
  - Volume inflation: **$16.0\times$ larger than reality**.
  - The hollow triangular wedge ($144,000$ LDU³) is where Technic gear trains, transmissions, and motors mount in official sets. Placing an AABB makes it impossible to build any Technic chassis containing this panel.
- **The OBB Solution**:
  - Flange 1 OBB: $C = (0, 0, 0)$, $E = (30, 9, 9)$, $U = I_3$. Volume = $19,440$ LDU³.
  - Sloping Plate OBB: $C = (0, 30, -40)$, $E = (30, 1.5, 50)$, $U$ rotated $36.87^\circ$ around $X$. Volume = $18,000$ LDU³.
  - Flange 2 OBB: $C = (0, 60, -80)$, $E = (30, 9, 9)$, $U = I_3$. Volume = $19,440$ LDU³.
  - **Total 3-OBB Volume**: $56,880$ LDU³ (vs $458,640$ LDU³ AABB $\implies$ **87.6% reduction in volume error**). The interior cavity is completely preserved.

### Case Study 2: Classic Sloped Windscreen 2x4x2 (`3823`)
- **Physical Geometry**:
  - Real bounds: $X \in [-40, 40], Y \in [0, 48], Z \in [-30, 10]$.
  - Two top studs at $X = \pm 30, Y = 0, Z = 0$.
  - Windscreen glass rises 48 LDU over 24 LDU depth (slope 2:1, angle $\theta = 63.43^\circ$). Length along slope $L = \sqrt{48^2 + 24^2} \approx 53.67$ LDU.
  - Glass wall thickness: $T \approx 3.0$ LDU. Width: $W = 80.0$ LDU.
- **The Current Defective Behavior**:
  - `generic_stud_cell_occupancy()` emits two boxes for the top studs: `(-40, -20, 0, 48, -10, 10)` and `(20, 40, 0, 48, -10, 10)`.
  - These two boxes span only $Z \in [-10, 10]$. The entire sloped windscreen from $Z = -30$ to $Z = -10$ (where the driver looks through) has **zero occupancy**.
  - Meanwhile, the boxes plunge all the way down to $Y = 48$ inside the car, falsely occupying the space where the steering wheel and minifigure hands sit.
- **The OBB Solution**:
  - Roof Slab AABB: $X \in [-40, 40], Y \in [0, 8], Z \in [-10, 10]$. Volume: $80 \times 8 \times 20 = 12,800$ LDU³.
  - Sloped Glass OBB: oriented along $63.43^\circ$, length 53.7 LDU, width 80 LDU, thickness 3.0 LDU. Volume: $12,880$ LDU³.
  - Total volume: $25,680$ LDU³ (vs $153,600$ LDU³ AABB $\implies$ **83.3% volume reduction**), perfectly sealing the cockpit roof and windshield while leaving the interior completely open.

### Case Study 3: Technic Panel Fairing Smooth #21 (`11946`)
- **Physical Geometry**:
  - Thin aerodynamic blade of thickness $T \approx 2.5$ LDU, curved in 3D.
  - Bounds: $X \in [-9, 9], Y \in [-29.69, 10], Z \in [-10, 86]$.
  - Mounting holes at $Y = 10, Z = 40$ and $Z = 60$.
  - As $Z$ sweeps from $-10$ to $+50$, $Y_{\min}$ rises continuously from $-29.4$ to $-6.0$ LDU.
- **The Failure Mode**:
  - No top studs $\implies$ `generic_stud_cell_occupancy()` returns nothing.
  - Ray-parity solidity over full bbox = 19.5% (barely above 15% threshold), but placing a single box covers the hollow flank behind the fairing.
  - Furthermore, `11946` connects to a Technic beam via pins through its two flange holes. Under the current validator, the moment the panel flange touches the beam face, a false-positive collision is reported between panel and beam because they are not directly mated (they are mediated by pins).

---

## 4. Architectural Design: The OBB Decomposition Engine

To support curved shells without breaking the existing codebase, a clean, multi-layered architectural model is required.

```
+-----------------------------------------------------------------------------------+
|                           1. SCHEMA LAYER (spec & JSON)                           |
|  mesh['occupancy'] supports 6-tuples (AABBs) AND 15-tuples / OBB dict objects    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     2. PIPELINE DECOMPOSITION LAYER (parts.py)                    |
|  - Surface curvature & normal clustering                                         |
|  - Minimum OBB fitting per cluster (PCA / covariance / rotating calipers)        |
|  - Spec §3 validation (ray-parity solid fraction >= 0.15 within each OBB)        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|               3. VALIDATION ENGINE (brick_parts_validate.py & twin)               |
|  - Local OBB -> World OBB transformation (rigid rotation + translation)           |
|  - 15-Axis Separating Axis Theorem (SAT) evaluation (Tier 2 fast path)           |
|  - Joint-Zone Capsule Exemption Mask (prevents false pin-mediated collisions)     |
+-----------------------------------------------------------------------------------+
```

### 4.1 Local OBB Representation & Schema Invariant
In `spec/brick-parts-v0.1.md` Section 3, `occupancy` is extended to support both AABBs and OBBs:

- **Legacy / Axis-Aligned Box (AABB)**:
  `[min_x, max_x, min_y, max_y, min_z, max_z]` (length = 6).
- **Oriented Bounding Box (OBB)** (Option A: 15-tuple for compact JSON & zero parse overhead):
  `[cx, cy, cz,  ex, ey, ez,  u0x, u0y, u0z,  u1x, u1y, u1z,  u2x, u2y, u2z]`
  - `center`: $(c_x, c_y, c_z)$ local midpoint.
  - `extents`: $(e_x, e_y, e_z)$ local half-dimensions ($E > 0$).
  - `axes`: $(u_0, u_1, u_2)$ three orthonormal unit vectors defining the local box frame.
- **OBB Representation (Option B: structured dict)**:
  ```json
  {
    "center": [cx, cy, cz],
    "extents": [ex, ey, ez],
    "axes": [[u0x, u0y, u0z], [u1x, u1y, u1z], [u2x, u2y, u2z]]
  }
  ```
*Recommendation*: Support both. `renderers/brick_parts_validate.py` inspects `len(b) == 6` vs `len(b) == 15` or `isinstance(b, dict)`.

### 4.2 World Transformation Mathematics
When a part with local OBB $\mathcal{B} = (C_{\text{loc}}, E, \mathbf{U}_{\text{loc}})$ is placed at world translation $\mathbf{P} = (ex, ey, ez)$ with rotation $\mathbf{R} \in SO(3)$ (from `rot_ldu`):

1. **Center**:
   $$C_{\text{world}} = \mathbf{R} \cdot C_{\text{loc}} + \mathbf{P}$$
2. **Axes**:
   $$\mathbf{u}_{i, \text{world}} = \mathbf{R} \cdot \mathbf{u}_{i, \text{loc}} \quad \text{for } i \in \{0, 1, 2\}$$
3. **Extents**:
   $$E_{\text{world}} = E \quad (\text{invariant under rigid rotation})$$
4. **Enclosing World AABB** (for broadphase culling):
   $$R_k = \sum_{i=0}^2 E_i |u_{i, \text{world}, k}| \quad \text{for } k \in \{x, y, z\}$$
   $$\text{AABB}_{\text{world}} = (C_x - R_x, C_x + R_x, C_y - R_y, C_y + R_y, C_z - R_z, C_z + R_z)$$

### 4.3 Automated OBB Decomposition Algorithm
For complex curved meshes where hand-curating OBBs is unscalable across hundreds of parts, an automated decomposition pipeline operates as follows:
1. **Normal Clustering**: Triangle normals $\mathbf{n}_f$ are clustered into $K$ dominant directions using spherical k-means or region growing with angular tolerance $\Delta\theta \le 25^\circ$.
2. **Segment Spatial Connected Components**: Connected triangle components belonging to each normal cluster are extracted.
3. **PCA / Minimum OBB Fitting**:
   - For each component $M_k$, compute vertex covariance matrix $\mathbf{\Sigma} = \frac{1}{N} \sum (\mathbf{v} - \bar{\mathbf{v}})(\mathbf{v} - \bar{\mathbf{v}})^T$.
   - Principal eigenvectors define box axes $\mathbf{U}_k = [\mathbf{e}_0, \mathbf{e}_1, \mathbf{e}_2]$.
   - Project vertices onto $\mathbf{U}_k$ to find tight min/max extents and center.
4. **Containment & Solidity Verification (Spec §3 Gate)**:
   - Verify that all 8 vertices of the fitted OBB lie within the part's global bounds (with 0.5 LDU tolerance).
   - Evaluate ray-parity solid fraction across the OBB: `_stud_box_solid_fraction(tris, obb) >= 0.15`.
   - If solid fraction fails or box volume exceeds threshold, reject automated fitting and flag for review.

---

## 5. Cross-Cutting System Dependencies

OBB decomposition cannot be safely deployed in isolation. It has two mandatory structural prerequisites:

### 1. Joint-Zone Mated-Connector Exemption (`MATED_CONNECTOR_EXEMPTION_INVESTIGATION.md`)
- Technic panels and mudguards connect to structural beams via intermediary pins.
- While the pin-to-panel and pin-to-beam joints are recognized, the panel-to-beam contact face is unexempted.
- Without the joint-zone capsule exemption mask, tightly-fitted OBBs along panel flanges will still falsely collide with adjacent beams.
- **Requirement**: The Tier 2 Joint-Zone Capsule Exemption from `MATED_CONNECTOR_EXEMPTION_INVESTIGATION.md` must land before or concurrently with Technic panel OBB occupancy.

### 2. JavaScript Twin Parity (`apps-script-surface/gas-wired-renderer/atoms_brick.gs`)
- Currently, `worldBoxes` and `boxesOverlap` in `atoms_brick.gs` are strictly 6-tuple axis-aligned interval checks.
- If JSON payloads containing 15-tuples or OBB dicts are ingested by the browser/Apps Script renderer, `atoms_brick.gs` will crash or miscalculate overlaps.
- **Requirement**: Port the 15-axis SAT math to `atoms_brick.gs` and verify with `tests/test_brick_parts_validate_js.py`.

---

## 6. Implementation Roadmap

### Phase 1: Local OBB Schema & Engine Generalisation
- Extend `scripts/ldraw/parts.py` with `obb(center, extents, axes)` constructor and validation logic.
- Update `_world_boxes()` in `renderers/brick_parts_validate.py` to transparently handle local OBBs under both integer rotations `0..23` and continuous $3 \times 3$ matrices.
- Port OBB SAT to `apps-script-surface/gas-wired-renderer/atoms_brick.gs`.

### Phase 2: Priority Family Unlocking (Hand-Curated OBB Slabs)
- Hand-curate verified OBB decompositions for high-impact representative parts:
  - Technic bent panel `24116` (3 OBBs: 2 flanges + 1 sloped plate).
  - Classic windscreens `2437` and `3823` (2 OBBs: roof slab + sloped windshield).
  - Trapeze windscreens `19212` and `80573` (3 OBBs: base + 2 angled A-pillars).
- Measure real-set impact on priority sets:
  - LEGO Technic 42145 (Airbus H175 Rescue Helicopter): unlocks panels `11946`, `11947`, `24116`.
  - LEGO Technic 8880 (Super Car): unlocks chassis panels and angled fairings.

### Phase 3: Automated Mesh Decomposition Pipeline
- Implement normal-clustering and PCA OBB fitting in `scripts/ldraw/parts.py`.
- Run across the 530 uncurated rejected candidates from the catalogue survey.
- Enforce automated ray-parity solid fraction gating (`>= 0.15`) before accepting any decomposed OBB set.

---

## 7. Conclusion

The operator hypothesis and backlog classification were entirely correct: `obb-decomposition` is a single, unified architectural lever required by both Technic Panel fairings and hollow windscreen canopies. 

Attempting to resolve these families with axis-aligned bounding boxes is mathematically impossible: AABBs over-claim 7x to 16x material volume, destroying the functional interior cavities (cockpits, gearboxes, wheel wells) that define LEGO construction. Multi-box OBB decomposition provides the exact geometric foundation to resolve all 530 blocked curved-shell parts catalogue-wide while upholding the foundational safety mandate of spec section 3: **miss an overlap, never report a false one.**
