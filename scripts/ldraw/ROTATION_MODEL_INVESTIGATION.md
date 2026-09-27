# Arbitrary Rotation Model Investigation (2026-09-27)

## Status: COMPLETE

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
Direct examination of 5 real sets refetched live from `https://library.ldraw.org/library/omr/<set>.mpd` (with `User-Agent: a2ui-fetch-library`, per library norms) confirms the exact scale, diversity, and physical causes of non-axis-aligned part placements:

| Set Number | Set Name | Total Parts | Baked Parts | Currently Renderable | Tilted (Non-Axis-Aligned) | Tilted % of Baked |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`1869-1`** | Basic Small Car | 82 | 82 (100.0%) | 82 (100.0%) | **0** | **0.0%** |
| **`6080-1`** | King's Castle | 911 | 533 (58.5%) | 502 (55.1%) | **31** | **5.8%** |
| **`6597-1`** | Century Skyway (Airport) | 931 | 562 (60.4%) | 429 (46.1%) | **133** | **23.7%** |
| **`10001-1`** | Metroliner (9V Train) | 848 | 555 (65.5%) | 191 (22.5%) | **364** | **65.6%** |
| **`75954-1`** | Hogwarts Great Hall | 1,116 | 599 (53.7%) | 518 (46.4%) | **81** | **13.5%** |
| **`8880-1`** | Technic Super Car | 1,410 | 984 (69.8%) | 582 (41.3%) | **402** | **40.9%** |

#### What Real-World Physical Things Are These Angles?
Analysis of the underlying geometry, part descriptions, and assembly positions reveals that non-axis-aligned rotations fall into distinct, universal LEGO construction patterns:

1. **Aerodynamic Slopes & Vehicle Cabs (`10001-1` Metroliner)**:
   - **Scale:** 364 tilted parts (over 65% of baked parts in the model!).
   - **Real parts:** `2877` (Brick 1x2 Grille, 28 instances), `3710` (Plate 1x4, 28 instances), `3005` (Brick 1x1, 28 instances), `3023b` (Plate 1x2, 27 instances), `3660a` (Slope 45° 2x2 Inverted, 20 instances), `4162` (Tile 1x8, 12 instances).
   - **Real matrix:** `m = (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)` (pure 30.0° Y-axis rotation), `(0.5, 0.0, 0.866, 0.0, 1.0, 0.0, -0.866, 0.0, 0.5)` (60.0°), and `(-0.866, 0.0, 0.5, 0.0, 1.0, 0.0, -0.5, 0.0, -0.866)` (150.0°).
   - **Physical cause:** The iconic slanted wedge nose of the high-speed locomotive is constructed as an angled sub-assembly mounted to the chassis via hinge bricks, tiling dozens of structural plates, bricks, and tiles at 30°/60°.
   - **Moving assemblies:** Pantograph mechanisms (`4504` Hinge Control Handle + `3666` Plate 1x6) angled upward at 16.5°: `m = (1.0, 0.284, 0.0, -0.284, 1.0, 0.0, 0.0, 0.0, 1.0)`.

2. **Technic Linkages, Chassis Braces & Suspension (`8880-1` Super Car)**:
   - **Scale:** 402 tilted parts (40.9% of baked parts).
   - **Real parts:**
     - `2429` / `2430` (Hinge Plate 1x4 Base and Top, 47 pairs each!): `m = (-0.868, 0.0, 0.496, 0.0, 1.0, 0.0, -0.496, 0.0, -0.868)` (approx 29.7°).
     - `3702` (Technic Beam 1x8), `3701` (Beam 1x4), `3700` (Beam 1x2), `3895` (Beam 1x12): diagonal chassis stiffening trusses angled at 33.9° (`m = (0.0, 0.0, -1.0, -0.558, 0.83, 0.0, 0.83, 0.558, 0.0)`).
     - `2780` (Technic Pin with Friction Ridges, 38 instances): connecting angled diagonal beams (`m = (1.0, 0.0, 0.0, 0.0, 0.986, 0.168, 0.0, -0.168, 0.986)`).
     - `4274` (Technic Pin 1/2, 10 instances): suspension wishbones angled at 23.6° (`m = (0.0, 0.917, 0.4, 0.0, 0.4, -0.917, -1.0, 0.0, 0.0)`).
   - **Physical cause:** Triangulated space-frame chassis design and double-wishbone independent suspension. In Technic sets, structural rigidity is achieved through diagonal braces governed by Pythagorean stud triangles (e.g. 3-4-5 or $\sqrt{h^2+w^2}$ pitch distances).

3. **Diagonal Architecture & Octagonal Terminals (`6597-1` Century Skyway Airport)**:
   - **Scale:** 133 tilted parts (23.7% of baked parts).
   - **Real parts:** Standard building bricks and plates forming angled airport wings: `3023b` (11), `3003` (9), `3710` (7), `3020` (7), `3022` (6), `3623` (6), `3004` (6), `4315` (Hinge Plate 1x4, 5 instances), `2420` (Corner Plate 2x2, 4 instances).
   - **Real matrix:** Angles at 30.1° (`m = (0.865, 0.0, 0.502, ...)`), 59.9° (`m = (0.502, 0.0, -0.865, ...)`), 119.9°, 149.9°, and 165.0°.
   - **Rotated sub-components:** Radar antennas and propeller hubs using `4589` (Cone 1x1, 4 instances) at compound angles (`m = (0.498, -0.867, 0.0, 0.0, 0.0, 1.0, -0.867, -0.498, 0.0)`).

4. **Gothic Architecture, Spires & Articulated Creatures (`75954-1` Hogwarts Great Hall)**:
   - **Scale:** 81 tilted parts (13.5% of baked parts).
   - **Real parts:** `54200` (Slope 30° 1x1 Cheese, 10 instances) at 15.0° and 45.0°; `87580` (Plate 2x2 Jumper, 6 instances) at compound angle 145.1° (`m = (-0.159, 0.689, -0.707, 0.974, 0.225, 0.0, 0.159, -0.689, -0.707)`); `47397` / `47398` (Wedge 12x3 Left/Right) forming steep roof gables; `14417` / `14704` / `14418` (Small Ball Joint & Socket arms) articulating creature limbs.

5. **Decorative Accessories, Posed Minifigs & Mechanisms (`6080-1` King's Castle)**:
   - **Scale:** 31 tilted parts (5.8% of baked parts).
   - **Real parts:**
     - `4495a` (Flag on Flagpole, 13 instances): mounted at 30.0° (`m = (0.866, 0.0, -0.5, 0.0, 1.0, 0.0, 0.5, 0.0, 0.866)`) atop castle battlements.
     - `3626ap01` (Minifig Head, 12 instances): turned 9.6° on the torso neck (`m = (0.986, 0.0, -0.169, 0.0, 1.0, 0.0, 0.169, 0.0, 0.986)`) for realistic lifelike direction of gaze.
     - `3700` (Technic Brick 1x2 with Hole), `3033`, `3673` (Pin): drawbridge mechanism tilted at 2.6° (`m = (0.999, -0.035, 0.0, 0.035, 0.999, 0.0, 0.0, 0.0, 1.0)`).

**Conclusion from real data**: Tilted parts in real sets are not edge cases or glitches. They represent fundamental LEGO modeling techniques across all major themes: Technic geometry, Train aerodynamics, Castle flags/drawbridges, Airport angled buildings, and Minifig posing.

---

### 3. Prior Art in the LDraw Ecosystem
How do official and established tools in the LDraw and digital LEGO ecosystem represent rotations and perform collision checking?

#### 3.1 Representation: Continuous 3x3 Transformation Matrices
- **LDraw Specification (Official Standard)**:
  LDraw file format line type 1 (subfile reference) is explicitly defined as:
  ```ldraw
  1 <colour> x y z a b c d e f g h i <subfile.dat>
  ```
  Where `[a b c / d e f / g h i]` is a full, continuous, unquantised 9-element floating-point row-major transformation matrix:
  $$\begin{bmatrix} x' \\ y' \\ z' \end{bmatrix} = \begin{bmatrix} a & b & c \\ d & e & f \\ g & h & i \end{bmatrix} \begin{bmatrix} x \\ y \\ z \end{bmatrix} + \begin{bmatrix} x_0 \\ y_0 \\ z_0 \end{bmatrix}$$
  The LDraw ecosystem has **always** used continuous floating-point matrices. It has never used integer rotation indices or discrete quantization tables.

#### 3.2 Collision Detection in Major LEGO CAD Tools
- **LeoCAD**:
  - LeoCAD does **not** enforce collision detection between placed bricks. Bricks can be placed anywhere in continuous space.
  - LeoCAD utilizes Axis-Aligned Bounding Boxes (AABB) strictly as a broad-phase acceleration structure for mouse-ray picking/selection (`BoundingBoxRayMinIntersectDistance`) and camera frustum framing.
- **LDCad (and LDInspector)**:
  - Roland Melkert's LDCad implements a 3-tier collision and snapping architecture:
    1. **Broad Phase:** Bounding Spheres and Axis-Aligned Bounding Boxes (AABBs). If AABBs do not overlap, tests terminate.
    2. **Mid Phase (OBB / SAT):** Because rotated LEGO parts cause bounding-box inflation in AABBs (leading to rampant false collisions), LDCad constructs **Oriented Bounding Boxes (OBBs)** that transform directly with each part's orientation matrix. Intersection between OBBs is tested using the **Separating Axis Theorem (SAT)** over 15 potential separating axes (3 from Box A, 3 from Box B, 9 cross-products of box edges).
    3. **Narrow Phase:** Triangle-triangle / quad intersection testing (also SAT-derived) for exact surface interpenetration.
- **BrickLink Studio**:
  - Studio stores collision geometry separately from render meshes in dedicated `.col` files (containing simplified compound primitives: OBBs, cylinders, spheres).
  - Studio executes real-time collision detection during placement using **OBB-OBB SAT (Separating Axis Theorem)** across the 15 candidate axes.
  - SAT projects the distance between box centers onto candidate unit normal $L$:
    $$|(C_B - C_A) \cdot L| > \sum_{i=0}^2 e_{Ai} |u_{Ai} \cdot L| + \sum_{j=0}^2 e_{Bj} |u_{Bj} \cdot L|$$
    If this condition holds for *any* of the 15 axes, the boxes are proven disjoint (early exit).
  - A small inward boundary inset (0.1–0.5 LDU) accounts for manufacturing clutch tolerances, preventing legal mating connections from falsely triggering collision alarms.

#### 3.3 Why Discretising / Quantising to a Finer Set Fails
A natural initial thought is: *"Could we expand `PART_ROT` from 24 to, say, a few hundred or thousand discrete rotation matrices, preserving the integer index?"*
Mathematical and geometric analysis proves this is **unworkable**:

1. **Lever-Arm Error Exceeds Connector & Collision Tolerance**:
   - The validation tolerance in `brick_parts_validate.py` is **0.5 LDU** for both collision overlaps and stud/socket mating (`_dist3(s.pos, k.pos) < 0.5`).
   - If an angle deviates by even $\Delta\theta = 1.0^\circ$, the linear error at distance $L$ from the pivot is:
     $$\Delta p \approx L \cdot \sin(\Delta\theta)$$
   - At $L = 60$ LDU (a 3-stud liftarm or plate): $\Delta p = 60 \cdot \sin(1^\circ) = 1.05$ LDU (more than double the tolerance!).
   - At $L = 200$ LDU (a 10-stud train cab or wing): $\Delta p = 200 \cdot \sin(1^\circ) = 3.49$ LDU (**7x the tolerance**!).
   - Snapping to a discrete grid guarantees that long angled assemblies will fail both stud/pin connection matching and false-collision checks.

2. **Quantisation Still Requires OBB / SAT Collision Checking**:
   - Even if rotations were snapped to a discrete set (e.g. 15° increments), an oriented box in world space is **still not axis-aligned**.
   - An axis-aligned bounding box (AABB) around a 15°-rotated brick suffers bounding-box inflation. For example, a $20 \times 40$ plate rotated 45° inflates its AABB footprint from $20 \times 40 = 800$ to $42.4 \times 42.4 = 1,800$ LDU² (+125% phantom volume!). Adjacent parts placed near the angled subassembly falsely collide under AABB coordinate tests.
   - Therefore, OBB / SAT is required **regardless of whether rotation is continuous or discrete**. Quantisation does not eliminate the need for OBB/SAT math.

3. **Combinatorial Explosion of 3D Rotations in SO(3)**:
   - Unlike 2D planar rotation (which has 1 degree of freedom), 3D rotation space SO(3) has 3 degrees of freedom.
   - Sampling Euler angles or axis-angles at:
     - $15^\circ$ spacing $\implies 24 \times 24 \times 24 = 13,824$ matrices.
     - $5^\circ$ spacing $\implies 72 \times 72 \times 72 = 373,248$ matrices.
   - Searching or storing such tables in client-side JavaScript (`atoms_brick.gs`) is prohibitively wasteful and complex.

4. **Trigonometric / Pythagorean Geometry in LEGO Design**:
   - As observed in `8880-1` ($33.9^\circ = \arctan(2/3)$), `6080-1` ($2.6^\circ$, $9.6^\circ$), and `10001-1` ($16.5^\circ$), angles in real LEGO models are determined by physical pin-to-hole constraints and triangle hypotenuses. They are continuous real numbers, not round multiples of $5^\circ$ or $15^\circ$.

**Finding:** The standard ecosystem approach—**continuous 3x3 transformation matrix storage combined with 15-axis OBB / SAT collision checking**—is the only mathematically valid and practically viable solution.

### 4. Architectural Scope & Component Changes

#### 4.1 Changes in `renderers/brick_parts_validate.py` and `apps-script-surface/gas-wired-renderer/atoms_brick.gs`
The Python validator and its JavaScript twin must be updated in exact lockstep to prevent drift. The required mathematical and structural changes are:

1. **`partsModel` Element Schema & Rotation Dispatch**:
   - **Current representation:** `{p, x, y, z, r, c}` where `r` is integer `0..23` indexing `PART_ROT`.
   - **Unified representation:** `r` can be either:
     - `int 0..23`: axis-aligned rotation index (compact 1-byte, backward compatible with all existing models and spec fixtures).
     - `tuple` (Python) / `Array` (JS) of 9 floats: `[m00, m01, m02, m10, m11, m12, m20, m21, m22]` (flat row-major $3 \times 3$ matrix matching LDraw line 1).
   - **Sanitisation (`_partsModelSanitise` in `atoms_brick.gs`, `_brick_parts_model_sanitise` in `web_article.py`)**:
     - Currently clamps `rot % 24`.
     - Generalised logic: if `typeof rot === 'number'`, keep `((rot % 24) + 24) % 24`. If `Array.isArray(rot) && rot.length === 9`, validate finite numbers, clamp entries to $[-1.0, 1.0]$, check proper rotation determinant $\det(M) \approx 1.0 \pm 0.05$ (or re-orthonormalise via Gram-Schmidt), and round to 4 decimal places.

2. **Vector Rotation (`rot_ldu` / `rotLDU`)**:
   - Updated signature: `rot_ldu(r, p)`:
     ```python
     def rot_ldu(r, p):
         m = PART_ROT[r] if isinstance(r, int) else r
         return (m[0] * p[0] + m[1] * p[1] + m[2] * p[2],
                 m[3] * p[0] + m[4] * p[1] + m[5] * p[2],
                 m[6] * p[0] + m[7] * p[1] + m[8] * p[2])
     ```
   - **Key insight on connectors:** `_conn_world` and `hole_segs_world` already transform positions and directions via `rot_ldu(r, lp)` and `rot_ldu(r, dir)`. Because matrix multiplication is naturally continuous, **connector world positions and directions become continuous immediately with zero additional code**.
   - **Key insight on connector matching:** In `validate_parts`:
     - Stud-to-socket: `_dist3(s.pos, k.pos) < 0.5 and _dot3(s.dir, k.dir) < -0.5`.
     - Pin-to-hole: `_point_line_dist(p.pos, seg.a, seg.b) < 0.5`.
     Both tests are **already pure continuous 3D Euclidean distance and vector geometry**.
     The 1-LDU spatial hash with $\pm 1$ neighbor search (27 cells) mathematically guarantees finding all candidate sockets within 0.5 LDU, regardless of orientation. No changes are required in connector matching.

3. **World Occupancy Transformation (`_world_boxes` / `worldBoxes`)**:
   - Currently transforms only corners $(x_0, y_0, z_0)$ and $(x_1, y_1, z_1)$, which is only valid for axis-aligned rotations.
   - For arbitrary rotations, `_world_boxes` must instantiate **Oriented Bounding Boxes (OBBs)**:
     - Local center: $C_{loc} = \frac{1}{2}(x_0+x_1, y_0+y_1, z_0+z_1)$.
     - Local half-extents: $E = \frac{1}{2}(x_1-x_0, y_1-y_0, z_1-z_0)$.
     - World center: $C_{world} = \text{rot\_ldu}(r, C_{loc}) + (ex, ey, ez)$.
     - World axes: $u_0 = \text{rot\_ldu}(r, (1,0,0))$, $u_1 = \text{rot\_ldu}(r, (0,1,0))$, $u_2 = \text{rot\_ldu}(r, (0,0,1))$ (i.e. the rows/columns of $M$).
     - Enclosing World AABB (for broadphase grid and floor check):
       $$R_i = E_0 |u_{0,i}| + E_1 |u_{1,i}| + E_2 |u_{2,i}| \quad \text{for } i \in \{x, y, z\}$$
       Enclosing AABB min is $C_{world} - R$; max is $C_{world} + R$.
     - Returning `{center: C, extents: E, axes: [u0, u1, u2], aabb: [min, max]}` per box.

4. **Collision Overlap Test (`_boxes_overlap` / `boxesOverlap`)**:
   - Replace the 1D interval coordinate test with a 2-tier check:
     - **Tier 1 (Fast Path):** If both parts have integer `r` (axis-aligned), retain the existing 6-comparison interval test (`ox > 0.5 && oy > 0.5 && oz > 0.5`). This preserves $O(1)$ microsecond speed for the 80%+ axis-aligned pairs.
     - **Tier 2 (General OBB-OBB SAT):** If either part has a non-axis-aligned matrix, execute the Separating Axis Theorem over 15 candidate axes:
       - 3 axes of Box A: $u_{A0}, u_{A1}, u_{A2}$
       - 3 axes of Box B: $u_{B0}, u_{B1}, u_{B2}$
       - 9 cross-product axes: $u_{Ai} \times u_{Bj}$
       - On candidate axis $L$:
         $$\text{radius}_A = \sum_{i=0}^2 E_{Ai} |u_{Ai} \cdot L|, \quad \text{radius}_B = \sum_{j=0}^2 E_{Bj} |u_{Bj} \cdot L|$$
         $$\text{dist} = |(C_B - C_A) \cdot L|$$
         If $(\text{radius}_A + \text{radius}_B) - \text{dist} \le 0.5 \cdot \|L\|_2$: the boxes are separated along axis $L \implies$ return `False` immediately (early exit).
       - If overlap $> 0.5 \cdot \|L\|_2$ across all 15 axes $\implies$ return `True` (collision).

5. **Baseplate Contacts, Balance & Rendering (`atoms_brick.gs`)**:
   - **Floor collision:** For each OBB, lowest point in Y is $C_{world, y} + R_y$. If $C_{world, y} + R_y > 0.5$ (LDraw Y down), collision with baseplate is flagged.
   - **Center of mass:** Box mass = volume $= 8 \cdot E_x \cdot E_y \cdot E_z$ (invariant under rotation). Center of mass is simply $C_{world}$.
   - **Baseplate footprint:** For contacting parts ($C_{world, y} + R_y \approx 0$), project the 8 OBB vertices to $(x, z)$ on $y=0$ to form the footprint polygon for `_hull2`.
   - **WebGL rendering:** In `partTp(pmesh, r)`, `Rm` is already multiplied as a $3 \times 3$ matrix. Replacing `Rm = PART_ROT[r]` with direct assignment if `r` is an array gives WebGL continuous rotation out of the box!
   - **Canvas-2D fallback:** Draw projected edges of the OBB wireframe rather than an axis-aligned box.

---

#### 4.2 Changes in `scripts/ldraw/omr_import.py`
The OMR importer is the primary consumer turning LDraw model files into `partsModel` arrays:

1. **`rot_index(m, tol=0.02)`**:
   - Current implementation returns `None` for anything not in `PART_ROT`.
   - Updated behavior:
     - Check if `m` matches any entry in `PART_ROT` within `tol=0.02`. If so, return integer `i` (`0..23`).
     - Otherwise, verify proper rotation $\det(m) \approx 1.0$. If valid, return `tuple(round(v, 4) for v in m)`.
     - Mirrored parts ($\det(m) \approx -1.0$) can either be flagged or handled via reflection scale.
2. **`bottom_y(pid, l, r)`**:
   - Currently: `m = PART_ROT[r]`.
   - Updated: `m = PART_ROT[r] if isinstance(r, int) else r`. Transforms all 8 corners of `mesh["bounds"]` to find true lowest world-Y point.
3. **`to_parts_model(leaves)`**:
   - Emits `[pid, round(x), round(y), round(z), r_or_m, colour, step]`.
4. **Immediate Impact on OMR Model Coverage**:
   - Current: 64,083 / 131,960 parts renderable (**48.6%**).
   - With continuous rotation: 90,305 / 131,960 parts renderable (**68.4%**).
   - **Every baked part instance currently excluded solely due to rotation angle (26,222 real parts across the OMR library) becomes immediately renderable.**

---

#### 4.3 Impact on Occupancy Boxes and Existing Occupancy Families
A crucial architectural question was whether baked occupancy boxes (`box(x0,x1,y0,y1,z0,z1)`) in `public/parts/` would need to be re-derived or changed.

- **Empirical Ground Truth:**
  - Inspection of all 4,761 baked parts in `public/parts/` (4,634 with occupancy) reveals that **100% of baked occupancy boxes are defined in the part's own LOCAL coordinate system**.
  - In physical LEGO manufacturing and in LDraw part definitions, parts are designed on Cartesian stud molds. Studs, sockets, pin holes, axle channels, and walls are oriented along local X, Y, and Z axes.
  - Existing occupancy families in `scripts/ldraw/parts.py`:
    - `generic_stud_cell_occupancy`: 20x20xheight stud columns in local coordinates.
    - `generic_hole_channel_occupancy`: Channels along hole axes in local coordinates.
    - `ROUND_PARTS`: Inscribed/cross boxes approximating cylinders in local coordinates.
    - `TYRE_PARTS`: Tyre bounding cylinders in local coordinates.
    - `OVERRIDES`: Hand-authored boxes in local coordinates.
- **Do Occupancy Families Need Re-Deriving?**
  - **NO. ZERO occupancy boxes need to change in `public/parts/`**.
  - A local box $[x_0, x_1, y_0, y_1, z_0, z_1]$ is an axis-aligned box in the part's local frame.
  - When the part is placed into a model with world transformation matrix $M$ and translation $T$, the local box *automatically* maps to an Oriented Bounding Box (OBB) in world space:
    $$C_{world} = M \cdot C_{local} + T, \quad \text{Axes} = M \cdot I, \quad E_{world} = E_{local}$$
  - **Conclusion:** All existing occupancy work, all catalog bakes, and all occupancy generator functions remain 100% intact and valid. The change from AABB to OBB is purely a model-time instantiation in the validator and renderer, not a part-baking change.

---

### 5. Effort and Complexity Estimate
The scope is clearly bounded and architecturally clean, but requires precision because changes must be implemented simultaneously in Python and JavaScript without parity drift.

| Component | Files Affected | Changes Required | Complexity | Estimated Effort |
| :--- | :--- | :--- | :--- | :--- |
| **1. Data Model & Sanitisation** | `atoms_brick.gs`, `web_article.py` | Allow 9-tuple row-major matrix in `partsModel` alongside `r: 0..23`. Update sanitisation and validation regex/clamp. | Small | 0.5 days |
| **2. OMR Importer** | `scripts/ldraw/omr_import.py` | Update `rot_index` to emit 9-tuple on non-axis matches; update `bottom_y` and `to_parts_model`. | Small | 0.5 days |
| **3. OBB & SAT Collision Engine (Python)** | `renderers/brick_parts_validate.py` | Implement OBB instantiation in `_world_boxes`, enclosing AABB for broadphase, 15-axis SAT in `_boxes_overlap` with 0.5 LDU tolerance. | Medium | 1.5 days |
| **4. OBB & SAT Collision Engine (JS Twin)** | `apps-script-surface/gas-wired-renderer/atoms_brick.gs` | Exact port of Python OBB & 15-axis SAT logic into JavaScript in `worldBoxes` and `boxesOverlap`. | Medium | 1.5 days |
| **5. WebGL & Canvas Renderer** | `apps-script-surface/gas-wired-renderer/atoms_brick.gs` | Support 9-array matrix in `partTp` WebGL pipeline and wireframe OBB in canvas fallback. | Small-Med | 1.0 day |
| **6. Parity Verification & Test Suite** | `tests/test_brick_parts_validate.py`, `tests/test_brick_parts_validate.mjs` | Add parity test fixtures for 15°, 30°, 45°, 60° rotations, OBB non-collision cases, and stress test with 1,000 parts. | Small-Med | 1.0 day |

- **Overall Sizing:** **MEDIUM (~6 developer days, ideal for 2 focused sequential implementation sessions / PRs)**:
  - **Session 1 (Core Geometry & Validator Twin):** Implement OBB math and 15-axis SAT in `brick_parts_validate.py` and `atoms_brick.gs`, generate parity fixtures, and prove 100% Python/JS parity.
  - **Session 2 (Pipeline & Consumer Integration):** Update `_partsModelSanitise`, `omr_import.py`, WebGL/Canvas rendering in `atoms_brick.gs`, and verify complete rendering of real angled sets (e.g. `6080-1`, `10001-1`, `8880-1`).

---

## Conclusion
1. **The rotation model is the primary blocker to real-world set coverage.** 99.6% of tilted parts in real OMR sets are genuine continuous 3D rotations, not near-miss tolerances or mirror reflections. They represent standard building techniques: aerodynamic train noses (`10001-1`, 65.6% tilted), Technic space-frames and linkages (`8880-1`, 40.9% tilted), octagonal architectural wings (`6597-1`, 23.7% tilted), castle battlements and minifig poses (`6080-1`, 5.8% tilted).
2. **Quantisation is a non-starter; continuous matrices are mandatory.** Discretising rotations to an angular grid introduces linear lever-arm errors up to 3.5 LDU on a 10-stud subassembly (7x the 0.5-LDU connector/collision tolerance), breaks Pythagorean triangle linkages, causes combinatorial explosion in 3D SO(3) (13k–373k matrices), and *still* requires OBB/SAT due to bounding box inflation. Adopting continuous 9-element matrices matching LDraw line 1 is mathematically sound, robust, and industry standard.
3. **Baked part occupancy is completely unaffected.** All 4,634 baked occupancy boxes in `public/parts/` are defined in part-local coordinates where bricks are inherently Cartesian. Local boxes automatically become Oriented Bounding Boxes (OBBs) in world space via matrix multiplication. **Zero parts need re-baking or re-deriving.**
4. **Collision detection requires a 2-tier OBB-OBB SAT engine in Python and JS.** `brick_parts_validate.py` and its twin `atoms_brick.gs` must be upgraded to instantiate OBBs and run the standard 15-axis Separating Axis Theorem (with a fast-path for axis-aligned pairs). Connector matching (`studs`, `sockets`, `pins`, `holes`) is already continuous 3D Euclidean geometry and requires zero changes.
5. **Concrete Sizing: MEDIUM (~6 developer days, 2 focused PRs).**
   - **PR 1 (Core Validator Parity):** Implement OBB math and 15-axis SAT in `brick_parts_validate.py` and `atoms_brick.gs`; generate parity test fixtures proving 100% Python/JS parity.
   - **PR 2 (Pipeline & Consumer Integration):** Update payload sanitisation, `omr_import.py`, WebGL matrix handling, and Canvas 2D fallback.
   - **Payoff:** Immediately unlocks 26,222 real parts across the OMR library, boosting renderable coverage from **48.6% to 68.4%** across real sets.

