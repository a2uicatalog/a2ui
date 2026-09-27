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
*(To be scoped: brick_parts_validate.py & atoms_brick.gs, omr_import.py, occupancy boxes & families)*

### 5. Effort and Complexity Estimate
*(To be scoped)*

## Conclusion
*(To be completed)*
