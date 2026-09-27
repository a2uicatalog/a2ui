# Hinge occupancy investigation (2026-09-27)

## Status: IN PROGRESS

## What I'm checking
- Real hinge part representation (one part with a pose, or two static parts?)
- Evidence: real part ids and their actual geometry

## Findings so far

### 1. Hinge Primitives in LDraw (`p/`)
- The primitives `dhingesocket.dat`, `dhingepin1.dat`, `dhingepin2.dat`, `ddoorhinge.dat`, `ddoorhingepin.dat` are **Duplo primitives** (the `d` prefix stands for Duplo). Across 34,108 LDraw parts, they are only referenced by Duplo parts:
  - `13358.dat`: "Duplo Brick 2 x 2 Hinge Base"
  - `15449.dat`: "Duplo Brick 2 x 2 with Hinge Pin"
  - `21996.dat`: "Duplo Train Track Bridge Middle with Hinge"
  - `2294.dat`: "Duplo Door 1 x 4 x 4"
  - `2332a.dat`: "Duplo Door Frame 1 x 4 x 4"
  Standard LEGO System parts do NOT use these Duplo primitives.
- Standard LEGO System hinge primitives in `p/` are:
  - `h1.dat`: "Hinge Plate 2 Fingers" (used by `4276b.dat`)
  - `h2.dat`: "Hinge Plate 3 Fingers" (used by `4275b.dat`)
  - `clh1.dat` through `clh15.dat`: Click Lock Hinge primitives (e.g. `clh4.dat` "Click Lock Hinge Half Dual Finger" in `44302a.dat`, `clh6.dat` "Click Lock Hinge Single Finger for Plate Ends" in `44567a.dat`).

### 2. How LDraw Represents Hinges
In physical LEGO and in LDraw, a hinge is **TWO separate physical parts**, each with its own static geometry:
- **Classic 1x2 brick hinge**: `3937.dat` ("Hinge 1 x 2 Base") and `3938.dat` ("Hinge 1 x 2 Top").
- **Classic 1x4 plate hinge**: `2429.dat` ("Hinge Plate 1 x 4 Base") and `2430.dat` ("Hinge Plate 1 x 4 Top").
- **Finger hinge plates (friction)**: `4275b.dat` ("Hinge Plate 1 x 2 with 3 Fingers") and `4276b.dat` ("Hinge Plate 1 x 2 with 2 Fingers").
- **Locking / Click hinge plates (end)**: `44301a.dat` ("Hinge Plate 1 x 2 Locking with 1 Finger on End") and `44302a.dat` ("Hinge Plate 1 x 2 Locking with 2 Fingers on End").
- **Locking / Click hinge plates (side)**: `44567a.dat` ("Hinge Plate 1 x 2 Locking with 1 Finger on Side") and `44568.dat` ("Hinge Plate 1 x 4 Locking with 2 Fingers on Side").
- **Brick hinges**: `3831.dat` ("Hinge Brick 1 x 4 Base") and `3830.dat` ("Hinge Brick 1 x 4 Top").
- **Technic click hinge arms**: `30552.dat` ("Hinge Arm Locking with Single Finger") and `30553.dat` ("Hinge Arm Locking with Dual Finger").
- **Doors and frames**: `60596.dat` ("Door 1 x 4 x 6 Frame") and `7930.dat` ("Door 1 x 3 x 4").

LDraw provides convenience "Shortcut" assemblies (e.g. `73983.dat` / `2429c01.dat`, `3937c01.dat`, `3149ec01.dat`). These files contain no moving joints or parametric kinematics. They are static shortcut wrappers containing two subfile calls with identity transforms:
```ldraw
1 16 0 0 0 1 0 0 0 1 0 0 0 1 2429.dat
1 16 0 0 0 1 0 0 0 1 0 0 0 1 2430.dat
```
In real models (including official sets in the LDraw OMR repo), model builders place the two separate component parts (`2429` and `2430`, or `3937` and `3938`) with their own respective transformation matrices.

### 3. Current Status in `public/parts/` and Occupancy Resolution
Survey of baked parts in the current catalogue (4,761 parts):
- Almost all hinge halves are **ALREADY baked** into `public/parts/` with static occupancy:
  - `2429` (Plate 1x4 Base): baked, `occupancy`: `[[-40, -20, 0, 8, 0, 20], [-20, 0, 0, 8, 0, 20]]`, 2 sockets, `needs_occupancy: false`.
  - `2430` (Plate 1x4 Top): baked, `occupancy`: `[[0, 20, 0, 8, 0, 20], [20, 40, 0, 8, 0, 20]]`, 2 sockets, `needs_occupancy: false`.
  - `4275b` (Plate 1x2 3 Fingers): baked, `occupancy`: 2 boxes covering (-20..20, 0..8, -10..10), 2 sockets, `needs_occupancy: false`.
  - `4276b` (Plate 1x2 2 Fingers): baked, `occupancy`: 2 boxes covering (-20..20, 0..8, -10..10), 2 sockets, `needs_occupancy: false`.
  - `44301a`, `44302a`, `44567a`, `44568`, `3830`, `3831`, `4315`, `2452`: all baked with valid static occupancy and sockets.
- Why do they already have valid occupancy?
  - `generic_stud_cell_occupancy` in `parts.py` under-approximates occupancy to 20x20xheight boxes verified under each flush top stud via ray-parity proof.
  - The protruding hinge fingers / tabs (which mesh together) lie outside the stud-cell columns and are not in the occupancy boxes.
  - As a result, when two halves (e.g. `2429` and `2430`, or `4275b` and `4276b`) are placed together in a model, their occupancy boxes **do not collide** (overlap = 0 LDU <= 0.5 LDU tolerance).
- Parts that currently have `needs_occupancy: true` (e.g. `3937` Base, `30552` Technic arm):
  - They lack occupancy solely because they have no top studs flush at Y=0, so `generic_stud_cell_occupancy` cannot anchor boxes off studs. This is a static box-authoring question for studless parts, NOT an articulation/pose issue.

### 4. Is a Hinge ONE Part with a Pose, or TWO Static Parts?
**A hinge in this codebase and in LDraw is unequivocally TWO separate parts, each with its own static geometry.**

- **Physical & Data Model Reality**:
  - A LEGO hinge is never one part with an internal moving joint. It is two separate rigid parts (e.g. `2429` Base + `2430` Top; `4275b` 3-finger plate + `4276b` 2-finger plate; `3937` Base + `3938` Top).
  - Each half is an independent rigid body of molded ABS plastic. Neither half has internal degrees of freedom, moving sub-assemblies, or variable geometry.
  - The apparent single-part hinges in LDraw (such as `73983.dat` / `2429c01.dat` "Hinge Plate 1 x 4 (Complete)") are classified as `Shortcut` files. They contain no kinematics; they are simply convenience wrappers that place the two separate component parts (`2429` and `2430`) at (0, 0, 0) with identity transforms.
  - In real models (e.g. Official Model Repository / OMR), builders place each half as a distinct entry with its own position and rotation.

- **Does a Part Need a Pose Parameter?**:
  - **NO.** Neither `Part` in `resolve.py` nor the baked mesh format in `public/parts/<id>.json` needs a pose parameter.
  - The earlier hypothesis that hinges require an open-ended data-model redesign with a pose parameter was based on a fundamental misunderstanding: treating convenience shortcut assemblies (like `73983`) as monolithic parts that need to articulate internally.

- **Does Existing Occupancy Machinery Work?**:
  - **YES.** Because each half is static, each half has its OWN static occupancy boxes in its local reference frame.
  - For orthogonal angles (0°, 90°, 180°, 270°), the existing `PART_ROT` (24 cubic rotations) and `_world_boxes` in `brick_parts_validate.py` already work out of the box:
    - Tested empirically: `2429` (Base) and `2430` (Top) placed flat (0°) validate with `ok: True`, 0 collisions, 0 overlaps.
    - Tested empirically: `2429` and `2430` placed at a 90° bend (`r=1`) validate with `ok: True`, 0 collisions, 0 overlaps.
    - Tested empirically: `2429` and `2430` placed folding backwards into each other (270°, `r=3`) correctly fail with `collisions: [[0, 1]]` (real physical self-intersection detected).

- **What Is Actually Missing?**:
  The limitation is NOT in the part representation or occupancy model. The real missing pieces are:
  1. **Connector / Connectivity recognition**: `brick_parts_validate.py` only builds graph edges for `stud_conn` and `pin_conn`. It has no detector for hinge mating (matching hinge axes). As a result, the pivoted half is flagged as `floating` unless anchored to other bricks or the baseplate.
  2. **Non-orthogonal rotation angles in `partsModel`**: `partsModel` entries use integer `r` (0..23). Angling a hinge at 45° or 30° cannot be expressed in `r: 0..23`. This is a model-level rotation/transform question, not a part-level pose parameter.

## Conclusion
(fill in last)
