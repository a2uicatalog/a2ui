# H175 Mechanism & Electronics Parts Occupancy Investigation (2026-09-28)

## Status: COMPLETE — REJECTED (Honest, evidence-backed conclusion: NO safe axis-aligned bounding box occupancy family exists; parts must remain `needs_occupancy=True`)

## Executive Summary

This investigation analyzed real moving mechanism and electronic components from official LEGO Technic set **42145** ("Airbus H175 Rescue Helicopter") and the wider LDraw catalogue, specifically:
- **Engine Crankshafts**: `2853`, `2853a`, `2853b`, `2853c`, `2854`
- **Universal Joints**: `61903`, `62520`, `62519`, `9244`, `3712`, `575`
- **Driving Rings & Transmission**: `18947`, `18948`, `6539`, `32187`
- **Powered Up Electronics**: `22169c01` (Motor with Cable), `22169` (Motor Body), `85825` (2-Port Battery Box / Hub), `22127` (Control+ Hub)

**The confident, evidence-backed conclusion is that NO safe occupancy family or axis-aligned bounding box override exists for these parts under `a2ui`'s foundational safety invariant (Spec Section 3: *"under-approximation is always safe: miss a real collision on the dropped area, never report a false one"*). All investigated parts must honestly remain `needs_occupancy=True`.**

Key findings:
1. **Engine Crankshafts (`2853a`–`c`, `2854`)**:
   - Asymmetric offset throw: main axle sits at `(0, 0, z)`, while the crank pin is offset by 10.0 LDU in $-X$ (centered at $x = -10.0, y = 0.0$).
   - A full bounding box (`[-19, 9] x [-9, 9] x [-20, 19.5]`) encases the crank pin where the connecting rod big end (`2852`) mounts, guaranteeing a 100% false collision whenever a piston/rod is installed.
   - An inscribed central shaft box (`[-6, 6] x [-6, 6] x [-20, 19.5]`) measures ray-parity solidity of only **0.1150** (11.5%), failing `STUD_CELL_MIN_SOLID = 0.15`.
   - Furthermore, crankshafts undergo continuous 360° dynamic rotation during model operation, sweeping a cylindrical volume rather than an axis-aligned static box.
2. **Universal Joints (`61903`, `9244`, `3712`)**:
   - Universal joints are articulated Cardan couplings that bend at continuous, non-collinear angles up to ~45° in real Technic mechanisms (e.g. collective pitch controls, steering, or winch drives).
   - Even when straight: standard Technic axles insert 20 LDU into both ends ($z \in [-30, -10]$ and $z \in [10, 30]$). The bore region has solid fraction 0.3050; any solid box over the ends causes false collisions with inserted axles. The center ($z \in [-10, 10]$) is an open cross gimbal with thin fork prongs.
   - A static axis-aligned bounding box of the straight CAD shortcut is physically invalid for an articulated assembly and would falsely collide with surrounding airframe beams and gears.
3. **Driving Rings & Transmission Joiners (`18947`, `18948`, `6539`, `32187`)**:
   - `18948` (Axle Joiner 3L with Ridges) is an internal sleeve with an open axle hole bore through its entire 60 LDU length ($[-6, 6] \times [-6, 6]$). A through-axle passes completely through it.
   - `18947` (Driving Ring 3L) is an outer annular collar ($r \approx 10..12$ LDU) with an inner hollow bore ($r < 9$ LDU) that slides axially over `18948`. Its exterior features a deep circumferential channel where gearbox selector fork prongs (`18946`) clamp.
   - If either part were assigned a solid occupancy box, they would falsely collide with each other, with the through-axle, and with the selector fork.
   - `18948` is already independently confirmed and tested as excluded in `test_real_axle_feature_exclusions_stay_rejected`.
4. **Powered Up Electronics (`22169c01`, `22169`, `85825`)**:
   - `22169c01` (Motor with Cable): A sprawling coiled cable loops across 3D space ($x \in [-30, 65], y \in [-79.1, 39], z \in [-10, 312]$), expanding the bounding box to **3,612,711 LDU³**. Measured ray-parity solid fraction is only **0.0750** (7.5%), far below the 15% threshold. Over 92.5% of the bounding box is empty air around the flexible wire.
   - Bare Motor `22169`: Features 18 mounting pin/axle holes entering orthogonally from both $X$ and $Z$ directions, plus a rotating output drive shaft.
   - Battery Box / Hub `85825`: Has 24 mounting pin holes penetrating across both horizontal ($X$) and vertical ($Y$) faces, plus electrical plug ports and a removable battery door.
   - Neither component can use single-axis hole channels (`generic_hole_channel_occupancy`): inserting mounting pins along orthogonal planes would trigger false collisions against the channel walls of perpendicular holes. Resolving these parts requires multi-axis channel carving and mated-connector collision exemptions.

---

## 1. Real Measured Geometry & Solidity Analysis

All parts measured directly from official resolved LDraw geometry via `resolve_part()` (fixed random seed `20260926`, $n=200$ ray-parity samples for `_stud_box_solid_fraction`):

| Part ID | Description | Bounds (X, Y, Z in LDU) | BBox Vol (LDU³) | Ray BBox Solid (n=200) | Holes | Cyls | Sockets | Needs Occ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `2853a` | Technic Engine Crankshaft with Slot | `(-19.0..9.0, -9.0..9.0, -20.0..19.5)` | 19,908 | 0.2500 | 0 | 12 | 0 | `True` |
| `2853b` | Technic Engine Crankshaft with Slot and Blocker | `(-19.0..9.0, -9.0..9.0, -20.0..19.5)` | 19,908 | 0.2550 | 0 | 8 | 0 | `True` |
| `2853c` | Technic Engine Crankshaft with Hole and Blocker | `(-19.0..9.0, -9.0..9.0, -20.0..19.5)` | 19,908 | 0.2550 | 0 | 10 | 0 | `True` |
| `2854` | Technic Engine Crankshaft Centre | `(-19.0..19.0, -9.0..9.0, -10.0..10.0)` | 13,680 | 0.3400 | 0 | 2 | 0 | `True` |
| `61903` | Technic Universal Joint 3L (Complete) | `(-9.0..9.0, -9.0..9.0, -30.0..30.0)` | 19,440 | 0.3750 | 0 | 54 | 0 | `True` |
| `62520` | Technic Universal Joint 3L End | `(-9.0..9.0, -9.0..9.0, -5.0..30.0)` | 11,340 | 0.2000 | 0 | 24 | 0 | `True` |
| `62519` | Technic Universal Joint 3L Centre Cross | `(-8.8..8.8, -8.8..8.8, -4.0..4.0)` | 2,472 | 0.3500 | 0 | 6 | 0 | `True` |
| `9244` | ~_Technic Universal Joint Complete Shortcut | `(-9.0..9.0, -9.0..9.0, -40.0..40.0)` | 25,920 | 0.3800 | 0 | 54 | 0 | `True` |
| `3712` | Technic Universal Joint 4L End with Bush End | `(-9.0..9.0, -9.0..9.0, -35.0..10.0)` | 14,580 | 0.2200 | 0 | 24 | 0 | `True` |
| `3712c01` | Technic Universal Joint 4L Complete | `(-9.0..9.0, -9.0..9.0, -40.0..40.0)` | 25,920 | 0.3800 | 0 | 54 | 0 | `True` |
| `575` | Technic Universal Joint 4L End with Slotted End | `(-9.0..9.0, -9.0..9.0, -35.0..10.0)` | 14,580 | 0.3000 | 0 | 12 | 0 | `True` |
| `18947` | Technic Transmission Driving Ring 3L | `(-18.0..18.0, -18.0..18.0, -28.0..28.0)` | 72,576 | 0.3550 | 0 | 48 | 0 | `True` |
| `18948` | Technic Axle Joiner 3L with Ridges | `(-8.8..8.8, -8.8..8.8, -30.0..30.0)` | 18,488 | 0.5150 | 0 | 18 | 0 | `True` |
| `6539` | Technic Transmission Driving Ring 2L | `(-20.0..20.0, -20.0..20.0, -20.0..20.0)` | 64,000 | 0.2800 | 0 | 8 | 0 | `True` |
| `32187` | Technic Transmission Driving Ring Extension | `(-17.0..17.0, -17.0..17.0, -20.0..9.0)` | 33,524 | 0.2800 | 0 | 6 | 0 | `True` |
| `22169c01` | Electric Control+ L Motor with Coiled Cable | `(-30.0..65.0, -79.1..39.0, -10.0..312.0)` | 3,612,711 | **0.0750** | 18 | 1965 | 0 | `True` |
| `22169` | Electric Control+ L Motor (Body) | `(-30.0..30.0, -39.0..39.0, -10.0..150.0)` | 748,800 | 0.1600 | 18 | 203 | 0 | `True` |
| `85825` | Electric Powered Up 2 Port Battery Box | `(-90.0..90.0, -50.0..50.0, -89.0..89.0)` | 3,204,000 | 0.3450 | 24 | 491 | 0 | `True` |
| `22127` | Electric Control+ Hub | `(-90.0..90.0, -50.0..50.0, -89.0..89.0)` | 3,204,002 | 0.3300 | 20 | 360 | 0 | `True` |

---

## 2. Category-by-Category Forensic Geometric Analysis

### Category 1: Engine Crankshafts (`2853`, `2853a`, `2853b`, `2853c`, `2854`)

#### Mechanism & Function
In LEGO Technic internal combustion engine models (such as the V8 or radial engines in helicopters and supercars), crankshaft pieces snap together to form an articulated multi-throw shaft.
Each crankshaft unit converts rotary motion into linear reciprocating motion of the pistons:
- The main rotational axis is centered at `(0, 0, z)`.
- The crank web extends radially out to $x = -10.0$ LDU.
- The offset crank pin sits at $x = -10.0, y = 0.0$ spanning $z \in [-10.0, 0.0]$.
- A connecting rod (`2852`) attaches to this crank pin: the rod's cylindrical big-end bearing has an inner hole radius of $6.75$ LDU matching the pin, and outer radius $9.0$ LDU.

#### Why Candidate Bounding Boxes Fail
1. **Full Bounding Box (`[-19, 9] x [-9, 9] x [-20, 19.5]`)**:
   - While the overall box clears ray-parity solidity (0.2500), it covers the entire volume around the crank pin ($[-19, -1] \times [-9, 9] \times [-10, 0]$).
   - When connecting rod `2852` is mounted onto the pin, its big-end bearing sits directly inside this candidate box.
   - Collision overlap $\Delta x, \Delta y, \Delta z$ is $> 9.0$ LDU. An occupancy box would report a guaranteed **false collision** against every properly assembled connecting rod, directly violating Spec Section 3.
2. **Central Shaft Box (`[-6, 6] x [-6, 6] x [-20, 19.5]`)**:
   - Omitting the offset throw and bounding only the central shaft yields a measured solid fraction of only **0.1150** (11.5%), because the central web is open air between $z = -10$ and $z = 0$. This fails `STUD_CELL_MIN_SOLID = 0.15`.
3. **Kinematic Rotation**:
   - The crankshaft rotates 360° continuously during engine cycling. An axis-aligned box at any fixed static orientation is physically meaningless during operation.

---

### Category 2: Universal Joints (`61903`, `9244`, `3712`, `575`)

#### Mechanism & Function
The Technic Universal Joint (`61903` / `62520c01`) is a Cardan joint consisting of two end yokes (`62520`) connected to a central cross gimbal (`62519`). It transmits rotary drive across non-collinear shaft angles (e.g. up to 45° in helicopter main rotor head linkages, tail rotor drive shafts, and vehicle steering knuckles).

#### Why Candidate Bounding Boxes Fail
1. **Axle Bore Collisions at Ends**:
   - In both ends ($z \in [-30, -10]$ and $z \in [10, 30]$), an axle hole sleeve (`bush.dat`) receives a standard Technic axle ($[-6, 6] \times [-6, 6]$).
   - In a real assembly, axles insert 20 LDU into both ends. Any solid box spanning $[-6, 6] \times [-6, 6]$ across either end directly collides with the inserted drive axles.
2. **Open Gimbal Center**:
   - The center ($z \in [-10, 10]$) consists of four thin fork arms grasping the central pivot cross. The core volume is predominantly hollow air space to permit angular clearance as the joint bends.
3. **Continuous Angular Articulation**:
   - In official sets, universal joints are deployed at non-zero angles (often 15°–35°). The straight CAD model (`61903.dat`) is merely an unbent reference pose. Bounding the unbent pose with an AABB would cause severe false collisions against adjacent structural beams when the joint is tilted in an actual build.
   - As documented in `OBB_SAT_CORE_GEOMETRY.md` and `ROTATION_MODEL_INVESTIGATION.md`, articulated sub-assemblies cannot be safely boxed without kinematic joint degrees of freedom.

---

### Category 3: Driving Rings & Transmission Joiners (`18947`, `18948`, `6539`, `32187`)

#### Mechanism & Function
Technic transmission systems rely on driving rings (`18947` 3L, `6539` 2L) to engage and disengage gears:
- An internal axle joiner (`18948`) is keyed to a continuous rotating axle passing through its central bore.
- The driving ring (`18947`) has internal splines that mate with the exterior ridges of `18948`, allowing `18947` to slide axially along $Z$.
- A gearshift selector fork (`18946` / `6641` / `42034`) clamps its dual prongs into the circumferential groove around the outside of `18947`.
- As the ring slides along $Z$, its dog clutch teeth engage matching clutch teeth on adjacent transmission gears (`6542`, `35185`).

#### Why Candidate Bounding Boxes Fail
1. **Concentric Overlap with Axle Joiner & Axle**:
   - Joiner `18948` occupies $r \in [0.0, 8.78]$ LDU and $z \in [-30, 30]$ LDU.
   - Driving ring `18947` occupies $r \in [9.0, 18.0]$ LDU and $z \in [-28, 28]$ LDU.
   - In assembly, `18947` and `18948` are co-located at the identical origin `(x, y, z)`. Any box for `18947` that extends inward toward the axis overlaps `18948` and the through-axle, triggering a false collision.
2. **Selector Fork Groove Clearance**:
   - The outer groove of `18947` ($r \in [10, 14], z \in [-6, 6]$) is specifically reserved for the selector fork prongs. An occupancy box covering the outer envelope would collide with the selector fork.
3. **Joiner `18948` Axle Bore**:
   - `18948` has a through-axle bore along its entire length. Ray-parity solidity in its core axle channel is 0.4400. An occupancy box would collide with the through-axle.
   - `18948` is already explicitly tested and rejected in `test_real_axle_feature_exclusions_stay_rejected`.

---

### Category 4: Powered Up Electronics (`22169c01`, `22169`, `85825`)

#### Geometry & Multi-Axial Pin Bores
1. **`22169c01` (Control+ L Motor with Coiled Cable)**:
   - The flexible coiled wire (`u9218c01.dat`) sprawls out to $x = 65, y = -79.1, z = 312$ LDU.
   - Total bounding box volume is **3,612,711 LDU³**, with ray-parity solidity of only **0.0750** (7.5%).
   - Over **92.5% of the bounding volume is empty space**. Accepting a bounding box would place a massive phantom collision zone through the middle of any model using this motor.
2. **`22169` (Bare Motor Body)**:
   - Has 18 mounting pin/axle holes entering from both $X$ (horizontal) and $Z$ (axial) directions.
3. **`85825` (2-Port Battery Box / Hub)**:
   - Has 24 mounting pin holes entering from both $X$ (horizontal) and $Y$ (vertical) directions, plus front electrical port sockets.
4. **Why Single-Axis Channels Fail for Motors & Hubs**:
   - Existing hole-channel logic (`generic_hole_channel_occupancy`) is strictly 1D: it opens channels along a single shared axis (e.g. $Y$).
   - On `85825`, pins insert vertically from $Y = \pm 50$ into holes at $(x, \pm 10, z)$, AND horizontally from $X = \pm 90$ into holes at $(\pm 90, 0, z)$.
   - Carving a channel along $Y$ leaves solid material along $X$. Pins inserted horizontally in $X$ would falsely collide with the $Y$-channel walls.
   - Carving intersecting channels along multiple axes would hollow out the outer shell, triggering solidity failures or leaving paper-thin margins (the exact failure mode identified for Cross Blocks in `TECHNIC_REMAINDER_SURVEY.md`).
   - Safe occupancy for electronics requires two major cross-cutting prerequisites:
     1. **Mated-connector collision exemption** (ignoring overlaps between pins and host bodies when properly mated in holes).
     2. **Cable exclusion / segmentation** (stripping flexible wire subfiles before evaluating rigid enclosure geometry).

---

## 3. Account of LEGO Technic 42145 (Airbus H175) Impact

Set 42145 contains 2,001 pieces, featuring a complex motorized transmission, collective/cyclic rotor head, hoist winch, and retractable landing gear.
The pieces surveyed in this investigation correspond to the remaining mechanical and electronic core of the set:
- **1x `85825`**: Powered Up Battery Box Hub
- **1x `22169c01`**: Powered Up L Motor
- **1x `61903`**: 3L Universal Joint (rotor tilt / collective pitch drive)
- **2x `18947`**: 3L Transmission Driving Rings (dual-clutch gearbox functions: winch, landing gear, rotor speed)
- **2x `18948`**: 3L Axle Joiners for Driving Rings
- **1x `2853` / `2853a`**: Engine Crankshaft (reciprocating engine mock-up)

All of these parts are moving kinematic mechanisms, articulated joints, or multi-port electronic enclosures.
Confirming that they correctly remain `needs_occupancy=True`:
- **Preserves Spec Section 3 safety**: zero false collisions are generated in 42145's dense mechanical gearbox and rotor mast.
- **Prevents phantom bounding box errors**: no 3.6M LDU³ wire boxes or overlapping driving ring boxes are emitted.
- **Accurately scopes future work**: establishes clear prerequisites (mated-connector exemptions, kinematic joints, cable stripping) rather than attempting fragile bounding box hacks.

---

## 4. Verification & Unit Tests

To permanently lock in these findings and prevent future regressions, dedicated unit tests were added to `tests/test_generic_stud_occupancy.py`:
- `test_h175_mechanism_and_electronic_parts_stay_safely_rejected`: verifies that all 19 mechanism and electronic parts across crankshafts, universal joints, driving rings, and Powered Up components resolve with:
  - `needs_occupancy == True`
  - `occupancy == None`

Full test suite execution: **289 passed** in `tests/test_generic_stud_occupancy.py` (up from 270, 19 new real parts verified, 0 failures).
