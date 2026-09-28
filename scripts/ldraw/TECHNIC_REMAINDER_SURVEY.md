# Technic Remainder Occupancy Survey

**Date**: 2026-09-27  
**Scope**: Remaining ~90–96 official LEGO Technic parts in the LDraw catalogue currently returning `needs_occupancy=True`.  
**Prior Art & Fixed Boundaries**:
- Straight Technic bricks (`3700`, `6541`, `32000`, `3701`, `3894`, `3702`, `3703`) are covered by `technic_holes_occupancy`.
- Bent Technic beams/liftarms were previously surveyed and proven NOT safely coverable by single-axis hole-channel math (`generic_hole_channel_occupancy` correctly rejects them because their holes span multiple non-collinear axes).
- Straight Technic axle rods and Technic gears were previously investigated and settled on `main`.

---

## 1. Executive Summary & Inventory Classification

Scanning official, non-shortcut LDraw parts with `survey_rejects.py` category matching identified 96 parts across the primary Technic mechanical buckets:
- **Technic Connector** (34 parts): e.g. `32039`, `32126`, `6538a`, `53586`, `45590`, `10197`, `11272`, `32192`, `90202`.
- **Technic Pin** (32 parts): e.g. `4459`, `89678`, `32002`, `32556a/b`, `39888`, `42924`, `61332`, `65304`, `77765`, `11214`, `18651`, `61184`.
- **Technic Cross** / Cross Blocks (18 parts): e.g. `32291`, `32557`, `63869`, `98989`, `44809`, `92907`.
- **Technic Bush** (12 parts): e.g. `3713`, `4265a/b/c`, `6577`, `32123a/b`, `584`, `585`, `57585`.
- **Mechanical Grab-Bag** (joints, links, suspension, transmission, treads): e.g. `2736`, `2739a`, `32293`, `2741`, `2723`, `32474`, `53585`, `62519`, `62520`, `32294`, `57515`, `3711`, `3873`, `4716`, `32007`, `4185a`, `61510`, `64451`.

### Key Conclusions:
1. **Cross Blocks**: Must remain `needs_occupancy=True`. They feature orthogonal hole bores (Z vs X). Subtracting intersecting hole channels leaves tiny 3 LDU boundary slivers that fail the 0.15 solidity floor (measured 0.062) due to the rounded outer lobes of Technic parts.
2. **Bushes**: Must remain `needs_occupancy=True`. Although rotationally symmetric in XY, they are hollow annular sleeves with an open axle bore along Z (center solidity = 0.000). A solid inscribed box would cause false collision detection whenever an axle slides through the bush.
3. **Simple Pins**: **10 genuine parts qualify for safe `OVERRIDES`** as exact geometric counterparts to existing landed overrides (`2780`, `3673`, `4274`, `32054`). Every part has ray-parity solidity between 0.417 and 0.542 (well above the 0.15 floor) and fits within standard 12x12 hole channels without false collisions.
4. **Mechanical Grab-Bag**: Must remain `needs_occupancy=True`. Verified individually against real geometry; each part exhibits articulated sub-components, non-orthogonal angles, spherical ball-and-socket joints, or dynamic gear/sprocket interfaces.

---

## 2. In-Depth Analysis: Cross Blocks (`32291`, `32557`, `63869`, `98989`)

Cross blocks connect pin holes on one plane to pin or axle holes on a perpendicular plane at a 90-degree offset.

| Part ID | Description | Bounds (LDU) | Holes & Axes | Ray-Parity Solidity |
|---|---|---|---|---|
| `32291` | Technic Cross Block 2 x 2 (Axle/Twin Pin) | `[-19, -9, -10]` .. `[19, 29, 10]` | 2 pin holes along Z (y=20), 1 axle hole along X (y=0) | Full: 0.312, Outer sliver: **0.062** |
| `32557` | Technic Cross Block 2 x 3 (Pin/Pin/Twin Pin) | `[-19, -29, -10]` .. `[19, 29, 10]` | 2 pin holes along Z (y=20), 2 pin holes along X (y=0, y=-20) | Full: 0.292 |
| `63869` | Technic Cross Block 3 x 2 (Axle/Triple Pin) | `[-29, -9, -10]` .. `[29, 29, 10]` | 3 pin holes along Z (y=20), 1 axle hole along X (y=0) | Full: 0.312 |
| `98989` | Technic Cross Block 2 x 4 (Axle/Pin/Pin/Twin Pin) | `[-19, -49, -10]` .. `[19, 29, 10]` | 2 pin holes along Z (y=20), 3 holes along X (y=-40, -20, 0) | Full: 0.250 |

### Structural & Collision Analysis:
1. **Orthogonal Hole Bores**: Unlike straight beams whose holes share a single bore axis, cross blocks have holes boring along both the **Z axis** and the **X axis**.
2. **Channel Clearance Necessity**: In a valid LEGO build, pins insert into the Z-holes and an axle or pin inserts into the X-holes. To avoid false collision reports against these inserted connectors, 12x12 LDU channels must be left open along *both* axes.
3. **Decomposition Failure (The Thin-Sliver Problem)**:
   - For `32291`, the total Z thickness is 20 LDU (`[-10, 10]`). Carving out the X-axis hole channel at `y: [-6, 6], z: [-6, 6]` and two Z-axis hole channels at `x: [-16, -4], [4, 16], y: [14, 26]` leaves only thin outer wall margins of 3 LDU (`[-19, -16]` and `[16, 19]` in X; `[-9, -6]` and `[6, 9]` in Y).
   - When sampling these remaining candidate boxes with ray-parity point-in-mesh tests, candidate box `(16, 19, -9, 29, -10, 10)` yields a solid fraction of **0.062**.
   - Why? Because Technic liftarm/cross block outer profiles are rounded semicircular lobes (radius 9 LDU), not sharp rectangular blocks. An axis-aligned box placed at the corner samples predominantly empty space.
4. **Verdict**: **Cross blocks must remain `needs_occupancy=True`.** A shared mini-family or hand-curated multi-box approximation cannot guarantee `never report a false one` while clearing orthogonal insertion channels.

---

## 3. In-Depth Analysis: Bushes (`3713`, `4265a`, `6577`, `32123a/b`, `57585`)

Bushes act as axle collars, spacers, and retention stops.

| Part ID | Description | Bounds (LDU) | Symmetry | Core Solidity |
|---|---|---|---|---|
| `3713` | Technic Bush with Two Flanges (1L) | `[-9, -9, -10]` .. `[9, 9, 10]` | Cylindrical in XY, length 20 (Z) | Core: **0.000**, Inscribed: **0.354** |
| `4265a` | Technic Bush 1/2 Type 1 (0.5L) | `[-9, -9, -5]` .. `[9, 9, 5]` | Cylindrical in XY, length 10 (Z) | Core: **0.000**, Inscribed: **0.354** |
| `6577` | Technic Bush 1/2 Type 2 (0.5L) | `[-9, -9, -5]` .. `[9, 9, 5]` | Cylindrical in XY, length 10 (Z) | Core: **0.000**, Inscribed: **0.354** |
| `32123a` | Technic Bush 1/2 Smooth with Axle Hole Reduced | `[-9, -9, -5]` .. `[9, 9, 5]` | Cylindrical in XY, length 10 (Z) | Core: **0.000**, Inscribed: **0.354** |
| `32123b` | Technic Bush 1/2 Smooth Axle Hole Semi-Reduced | `[-9, -9, -5]` .. `[9, 9, 5]` | Cylindrical in XY, length 10 (Z) | Core: **0.000**, Inscribed: **0.354** |
| `584` | Technic Bush with One Flange (Vintage) | `[-10, -10, -10]` .. `[10, 10, 10]` | Cylindrical in XY, length 20 (Z) | Core: **0.000**, Inscribed: **0.333** |
| `585` | Technic Bush with Three Flanges (Vintage) | `[-10, -10, -10]` .. `[10, 10, 10]` | Cylindrical in XY, length 20 (Z) | Core: **0.000**, Inscribed: **0.333** |
| `57585` | Technic Bush with Three Axles | `[-27.7, -10, -19]` .. `[27.7, 10, 29.5]` | Tri-axial star (120°) | Full: **0.188** (asymmetric) |

### Solidity & Physical Collision Rationale:
1. **The Inscribed Box Test**:
   - For an outer diameter of 18 LDU (radius 9), the standard inscribed square has half-width $w = 18 / (2\sqrt{2}) \approx 6.364$ LDU.
   - An axis-aligned box `[-6.36, 6.36, -6.36, 6.36, -10, 10]` samples across the central axis.
   - Ray-parity measurement across concentric sample boxes shows:
     - Radius 0–2 LDU: solid fraction = **0.000**
     - Radius 0–3 LDU: solid fraction = **0.083**
     - Radius 0–6.36 LDU: solid fraction = **0.354**
2. **Physical Collision Contradiction**:
   - In LEGO building, a bush is an axle sleeve whose sole purpose is to slide **onto an axle rod**.
   - If a solid box is placed at the bush's inscribed envelope, the collision detector will report an overlapping collision between the axle rod (which occupies radius ~4.5 LDU along Z) and the bush!
   - This violates spec §3's core tenet: **"never report a false one"**.
3. **Non-Cylindrical Bushes**:
   - Part `57585` ("Technic Bush with Three Axles") is not a collar at all; it is a central hub with three 2L axle rods projecting at 120-degree angles in the XZ plane. It completely fails circular symmetry.
4. **Verdict**: **Technic Bushes must remain `needs_occupancy=True`.** They cannot be modeled as solid cylinders without creating false collisions against the axles they mount upon.

---

## 4. Safe Proven Subset: Hand-Verified `OVERRIDES` for Technic Pins

Existing `OVERRIDES` in `scripts/ldraw/parts.py` already cover `2780` (2L friction pin), `3673` (2L pin), `4274` (1/2 pin), and `32054` (3L pin with stop bush).

Surveying the remaining Technic Pin pool reveals **10 official parts** that are direct geometric twins and extensions of these existing landed overrides:

| Part ID | Part Description | Real Bounds (LDU) | Override Box | Solid Fraction | Sockets Generated | Counterpart |
|---|---|---|---|---|---|---|
| `89678` | Technic Pin 1/2 with Friction | `[-20, 0, -8, 8, -8, 8]` | `box(-20, 0, -6, 6, -6, 6)` | **0.417** | `[((-10, 6, 4), (0, 1, 0))]` | Exact twin of `4274` |
| `4459` | Technic Pin with Friction | `[-20, 20, -8, 8, -8, 8]` | `box(-20, 20, -6, 6, -6, 6)` | **0.521** | 2 sockets (x = ±10) | Twin of `2780`, `3673` |
| `61332` | Technic Pin with Friction Type 2 | `[-20, 20, -7.4, 7.4, -8, 8]` | `box(-20, 20, -6, 6, -6, 6)` | **0.458** | 2 sockets (x = ±10) | Twin of `2780` |
| `32002` | Technic Pin 3/4 | `[-20, 10, -8, 8, -8, 8]` | `box(-20, 10, -6, 6, -6, 6)` | **0.479** | 1 socket (x = -10) | 1L + 0.5L pin body |
| `32556a` | Technic Pin Long without Friction, Single Slot | `[-30, 30, -8, 7.4, -8, 8]` | `box(-30, 30, -6, 6, -6, 6)` | **0.500** | 3 sockets (x = -20, 0, 20) | 3L pin family |
| `32556b` | Technic Pin Long without Friction, Dual Slots | `[-30, 30, -7.4, 7.4, -8, 8]` | `box(-30, 30, -6, 6, -6, 6)` | **0.542** | 3 sockets (x = -20, 0, 20) | 3L pin family |
| `39888` | Technic Pin Long without Friction Type 2 | `[-30, 30, -7.4, 7.4, -8, 8]` | `box(-30, 30, -6, 6, -6, 6)` | **0.542** | 3 sockets (x = -20, 0, 20) | 3L pin family |
| `42924` | Technic Pin Long with Friction Type 2 | `[-30, 30, -7.4, 7.4, -8, 8]` | `box(-30, 30, -6, 6, -6, 6)` | **0.500** | 3 sockets (x = -20, 0, 20) | 3L pin family |
| `77765` | Technic Pin Long with End Stop | `[-30, 30, -8, 8, -8, 8]` | `box(-30, 30, -6, 6, -6, 6)` | **0.521** | 3 sockets (x = -20, 0, 20) | 3L pin family |
| `65304` | Technic Pin Long with Stop Bush Type 2 | `[-30, 30, -8.3, 8.3, -9, 9]` | `box(-30, 30, -6, 6, -6, 6)` | **0.479** | 3 sockets (x = -20, 0, 20) | Twin of `32054` |

### Proof of Safety:
- **Strict Bounding**: All candidate boxes satisfy $\text{box}_{\min} \ge \text{part}_{\min}$ and $\text{box}_{\max} \le \text{part}_{\max}$ (`_boxes_within_bounds` passes for all 10).
- **High Solidity**: All 10 parts achieve ray-parity solid fractions between 0.417 and 0.542, far exceeding the 0.15 threshold established in `parts.py`.
- **Mating Compatibility**: The 12x12 LDU cross-section (`y: [-6, 6], z: [-6, 6]`) fits precisely inside the 12x12 LDU hole channels created by `technic_holes_occupancy` and `generic_hole_channel_occupancy`, ensuring zero false positive collisions when mated through beam holes.

---

## 5. Comprehensive Survey of Remaining Mechanical Types

The table below documents the remaining ~40 mechanical Technic parts surveyed and confirms why they must remain `needs_occupancy=True`:

| Part ID | Description | Measured Bounds (LDU) | Holes | Real Geometric / Mechanical Rationale for `needs_occupancy=True` |
|---|---|---|---|---|
| `32039` | Technic Connector (Axle/Bush) Type 1 | `[-10, -9, -29]` .. `[10, 9, 10]` | 0 | Orthogonal 90° axle sockets: one axle inserts along Z (z=0), another along X (z=-20). |
| `32126` | Technic Connector Toggle Joint Smooth | `[-10, -9, -29]` .. `[9, 9, 10]` | 2 | Orthogonal joint: axle collar along Z at z=0, pin hole along X at z=-20. |
| `6553` | Technic Connector (Axle) with Axle 1.5 | `[-10, -9, -9]` .. `[10, 49.5, 9]` | 0 | T-shaped connector: female axle sleeve at bottom, male 1.5L axle shaft extending in +Y. |
| `6538a` | Technic Axle Joiner | `[-10, -10, -20]` .. `[10, 10, 20]` | 0 | Axle sleeve (2L). Center is a hollow axle bore; solid box would collide with inserted axles. |
| `53586` | Technic Axle Joiner Perpendicular with Extension | `[-10, -9, -90]` .. `[10, 29, 10]` | 0 | T-connector with 4L extension arm; hollow perpendicular axle bores. |
| `45590` | Technic Axle Joiner Double Flexible | `[-9, -9, -10]` .. `[29, 9, 10]` | 0 | Dual-sleeve flexible rubber joint; dynamic bending deformation. |
| `2736` | Technic Axle Towball | `[-20, -8, -8]` .. `[17, 8, 8]` | 0 | 10.4 LDU spherical towball on 1L axle stem; articulates omnidirectionally in sockets. |
| `32474` | Technic Ball Joint with Axlehole Blind | `[-12.8, -12.8, -12.8]` .. `[12.8, 9.2, 12.8]` | 0 | Spherical ball-socket receiver with blind axle hole; omnidirectional non-orthogonal articulation. |
| `53585` | Technic Ball Joint with Axlehole Open | `[-12.8, -9.6, -12.8]` .. `[12.8, 9.6, 12.8]` | 0 | Open spherical ball-socket receiver cup; through axle hole. |
| `2739a` | Technic Steering Link 6L Type 1 | `[-10, -6, -10]` .. `[10, 6, 110]` | 0 | Thin 6L rod with spherical ball sockets at both extremities. |
| `32293` | Technic Steering Link 9L | `[-10, -9, -10]` .. `[10, 5, 170]` | 0 | Thin 9L rod with spherical ball sockets at both extremities. |
| `2741` | Technic Steering Wheel Large | `[-49.1, -23.1, -49.1]` .. `[49.1, 8, 49.1]` | 0 | Large open spoke wheel; solidity = **0.125** (fails the 0.15 solidity floor). |
| `2723` | Technic Disc 3 x 3 with Axlehole | `[-30, 0, -30]` .. `[30, 10, 30]` | 0 | Flat circular disc plate with central axle hole; thin rim with radial lightening slots. |
| `32192` | Technic Angle Connector #4 (135 degree) | `[-10, -27.4, -30]` .. `[10, 9, 27.4]` | 2 | Rigid 135-degree angled elbow; non-orthogonal hole arms cannot be decomposed into grid boxes. |
| `62519` | Technic Universal Joint 3L Centre | `[-8.8, -8.8, -4]` .. `[8.8, 8.8, 4]` | 0 | Cross-spider gimbal core of a 3-piece universal joint; dynamic 2-axis rotational freedom. |
| `62520` | Technic Universal Joint 3L End | `[-9, -9, -5]` .. `[9, 9, 30]` | 0 | U-yoke end bracket of universal joint with axle socket; rotates around `62519`. |
| `32294` | Technic Suspension Arm 1 x 9 x 2.5 | `[-9, -30, -89]` .. `[9, 20, 89]` | 6 | Wishbone A-arm with tapered angled struts; solidity = **0.146** (fails 0.15 floor). |
| `57515` | Technic Suspension Arm 2 x 6 | `[-20, -9, -110]` .. `[20, 9, 9]` | 6 | Triangular suspension wishbone with ball socket cups and pin mounts. |
| `3711` | Technic Chain Link | `[-9.8, -5, -5]` .. `[9.8, 5, 21]` | 0 | Single chain link; designed to mate continuously at arbitrary hinge pitch angles. |
| `3873` | Technic Chain Tread 2.5 Wide | `[-26, -8, -5]` .. `[26, 5, 21]` | 0 | Continuous crawler track shoe; interlinks dynamically. |
| `4716` | Technic Worm Gear 2L | `[-12.7, -12.7, -20]` .. `[12.7, 12.7, 20]` | 0 | Continuous helical screw thread over 2L cylinder with central axle bore. |
| `32007` | Technic Tread Sprocket Wheel | `[-28.6, -30, -25]` .. `[28.6, 30, 25]` | 2 | Radial drive sprocket with perimeter teeth engaging crawler treads. |
| `4185a` | Technic Wedge Belt Wheel | `[-30, -30, -5]` .. `[30, 30, 5]` | 0 | Deep V-groove pulley wheel designed to seat rubber transmission belts. |
| `90202` | Technic Pin Connector Round with 4 Clips | `[-24, -10, -24]` .. `[24, 10, 24]` | 2 | Central round pin core with 4 radial C-clips at 90° intervals in XZ plane. |
| `32530` | Technic Tile 1 x 2 with Two Holes | `[-20, -31, -10]` .. `[20, 8, 10]` | 4 | Stepped tile plate with two vertical pin barrels extending 31 LDU downward. |
| `61510` | Technic Reel 2 x 1 | `[-10, -20, -20]` .. `[10, 20, 20]` | 0 | Winch drum with deep spool valley; solid fraction = **0.208** across hollow drum core. |
| `64451` | Technic Link 4 x 6 Bent 53.13 | `[-9, -10, -9]` .. `[56.9, 10, 144.9]` | 6 | Diagonal link bent at acute 53.13° angle; solidity = **0.083** (fails 0.15 floor). |
| `10197` | Technic Axle and Pin Connector Hub with 2 Axles at 90° | `[-10, -29.5, -29.5]` .. `[10, 9, 9]` | 2 | L-shaped hub with male axle stubs in mutually perpendicular planes. |
| `11272` | Technic Axle Connector 2 x 3 Quadruple | `[-29, -9, -20]` .. `[29, 9, 20]` | 0 | Block of 4 parallel axle sleeves; hollow axle bores across all 4 channels. |
| `61184` | Technic Pin 1/2 with Bar 2L | `[-60, -8, -8]` .. `[0, 8, 8]` | 0 | Hybrid: 1/2 pin on -X side, 2L bar rod extending to x = -60. Minifig clip mount. |
| `11214` | Technic Axle Pin Long with Friction with 2L Pin | `[-30, -8, -8]` .. `[29.5, 8, 8]` | 0 | Hybrid: 2L pin on -X side, 1L axle rod on +X side. |
| `18651` | Technic Axle Pin Long with Friction with 2L Axle | `[-30, -8, -8]` .. `[29.5, 8, 8]` | 0 | Hybrid: 1L pin on -X side, 2L axle rod on +X side. |

---

## 6. Implementation and Follow-Up Plan

1. **Implement `OVERRIDES` Entries**:
   Add the 10 proven pin parts (`89678`, `4459`, `61332`, `32002`, `32556a`, `32556b`, `39888`, `42924`, `77765`, `65304`) to `OVERRIDES` in `scripts/ldraw/parts.py`.
2. **Add Unit Tests**:
   Add test cases in `tests/test_generic_stud_occupancy.py` covering:
   - Occupancy resolution and bounds verification for all 10 pin overrides.
   - Socket generation verification (correct count and spacing).
   - Ray-parity solidity threshold validation for the pin boxes.
   - Rejection verification confirming that Bushes (`3713`, `4265a`), Cross Blocks (`32291`, `32557`), and representative complex parts (`32039`, `2736`, `4716`, `64451`) strictly remain `needs_occupancy=True`.
3. **Status Log**:
   Record findings and unlock metrics in `BRICK_CATALOGUE_STATUS.md`.
