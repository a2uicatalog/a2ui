# Windscreen Parts Occupancy Investigation

**Date:** 2026-09-28  
**Status:** COMPLETE (Investigation-only; no implementation)  
**Deliverable:** Ground-truth geometric survey of unresolved Windscreen-category parts in the LDraw library / OMR set sample, answering whether a shared occupancy family exists, determining why candidate parts fail, and detailing the architectural implications for collision detection.

---

## 1. Executive Summary

1. **No viable shared occupancy family exists for the unresolved Windscreen parts.**  
   An exhaustive survey of the 15 unresolved Windscreen parts (and the broader pool of 88 unresolved Windscreen-category parts in the LDraw library) confirms that these parts do not share a common geometric or topological structure that can be parameterized as a single occupancy family. They are a heterogeneous collection of curved, hollow, and articulated cockpit shells, bubbles, and loose glass inserts.

2. **Every candidate canopy is 85% to 96% hollow air.**  
   Using the exact ray-parity inside test (`_stud_box_solid_fraction` with 48 sample points per candidate volume), every single unresolved windscreen part measures between **4.17% and 14.58% solid plastic** over its bounding envelope. In contrast to ordinary LEGO bricks (which are hollowed underneath by 20–35% but present solid exterior walls and stud tubes), canopies are thin (2.0–2.5 LDU) shells enclosing an open cockpit cavity specifically designed to accommodate a seated minifigure pilot, steering wheel, and dashboard.

3. **Octagonal canopies (`2418a`, `2418b`, `2598`, `2598ps2`) fail both solidity and boundary containment proofs:**
   - **Solidity:** Although each carries 4 flush studs at the top apex ($Y=0$), the 20x20x$H$ column beneath the studs has a solid fraction of only **10.4%** (`2418a`/`b`, height 48 LDU) and **4.2%** (`2598`, height 96 LDU), failing the engine's `STUD_CELL_MIN_SOLID = 0.15` floor. The plastic below $Y=4$ is entirely hollow cabin air.
   - **Containment:** Even an under-approximation restricted to the thin roof plate ($Y \in [0, 4]$) cannot be represented as an axis-aligned bounding box. The apex is an octagon chamfered at 45° ($x + z = 30$); ray-parity testing confirms that the four corners of a $40 \times 40$ box (`(±19, 2, ±19)`) lie outside the mesh (`inside_points == False`), violating `part_checks.py`'s fundamental rule that occupancy boxes must lie within the part mesh.
   - **Connectivity:** No bottom sockets exist beneath the roof at $Y=4$ or $Y=8$. The canopy mounts to a cockpit base (`30200`) via hinge pins at the rear base ($Y=34, Z=50$).

4. **`30083` ("Windscreen 6 x 6 x 3 Dome with Hinge") is an articulated hinge part, not an occupancy candidate:**
   - Real geometry shows `30083` has **0 studs, 0 sockets, and 0 holes**.
   - It possesses 4 coaxial hinge cylinders of radius 4.0 LDU along the X-axis at $Y=0, Z=0$, designed to mesh with standard hinge fingers.
   - It functions as a rotating spherical turret (e.g. the Star Wars Republic Gunship side bubble turrets in sets 7163 and 75021) enclosing a clone trooper gunner.
   - Placing any static axis-aligned box over this 95.8% hollow hemisphere would falsely collide with the gunner and turret housing, and would be completely invalidated whenever the dome pivots. It belongs strictly to the Hinge Connector system scoped in `scripts/ldraw/HINGE_INVESTIGATION.md`.

5. **Loose glass inserts (`17457`, `13756`, `46103`) must remain without independent occupancy:**
   - These are loose transparent panes (thickness ~2 LDU) designed to snap inside vehicle windscreen frames (`17454`, `13760`, `45406`).
   - The frames themselves are **already fully resolved** in `public/parts/` with valid occupancy (e.g. `17454` has 6 stud-cell boxes, `13760c01` has 2 stud-cell boxes, `needs_occupancy: false`).
   - Giving the loose glass an independent occupancy box would cause a false self-collision bug whenever the glass is inserted into its matching frame.

6. **Why vehicle windscreens (`2437`, `3823`, `4594`, `6567`, `64453`) already work:**
   - In vehicle windshields that already have `needs_occupancy: false`, the studs are located on top of **solid vertical A-pillars / side uprights** running from $Y=0$ down to $Y=\text{height}$.
   - `generic_stud_cell_occupancy` generates boxes strictly for the side pillars (solid fraction $\ge 0.15$), while naturally leaving the sloped central glass and interior cabin open.
   - The occupancy engine is already operating at its theoretical optimum: parts with solid vertical columns get occupancy; parts that are hollow shells over cockpits are correctly rejected.

7. **Conclusion:**  
   No forced or guessed boxes should be added to `parts.py`. The 15 unresolved Windscreen parts should remain `needs_occupancy=True`.

---

## 2. Real Measured Background

A survey of the 10 representative parts from the 133-OMR-set sample, plus related windscreen components in the library, measured with exact bounds, connector counts, and ray-parity solid fractions:

| Part ID | Description | Studs | Holes | Cylinders | Resolved Bounds ($[X_{\min}, Y_{\min}, Z_{\min}] \dots [X_{\max}, Y_{\max}, Z_{\max}]$) | Full Bounding Box Solid % | Column Under Stud Solid % |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| **`13252`** | Windscreen 6 x 13 x 2 | 4 | 0 | 68 | `[-60.0, -18.0, -250.0] .. [60.0, 30.0, 6.0]` | **12.50%** | 10.42% (roof only; cabin hollow) |
| **`17457`** | Windscreen 2 x 6 x 2 Vertical Glass | 0 | 0 | 0 | `[-58.4, 3.8, -8.4] .. [58.4, 40.0, 30.0]` | **8.33%** | N/A (loose glass insert for frame 17454) |
| **`2418a`** | Windscreen 6 x 6 Octagonal Canopy w/o Axlehole | 4 | 0 | 4 | `[-60.0, 0.0, -60.0] .. [60.0, 48.0, 60.0]` | **10.42%** | 10.42% (roof $Y \in [0, 4]$; hollow below) |
| **`2418b`** | Windscreen 6 x 6 Octagonal Canopy w/ Axlehole | 4 | 0 | 12 | `[-60.0, 0.0, -60.0] .. [60.0, 48.0, 60.0]` | **10.42%** | 10.42% (roof $Y \in [0, 4]$; central axle hole) |
| **`2483`** | Windscreen 4 x 4 x 3.667 Helicopter | 0 | 0 | 0 | `[-40.0, -4.0, -76.0] .. [40.0, 100.0, 4.0]` | **8.33%** | N/A (curved shell; rear hinge tabs) |
| **`2507`** | Windscreen 10 x 4 x 2.333 Canopy | 0 | 0 | 0 | `[-40.0, -4.0, -196.0] .. [40.0, 52.0, 4.0]` | **8.33%** | N/A (spaceship cockpit canopy; rear hinge) |
| **`2598ps2`**| Windscreen 10 x 10 x 4 Octagonal Canopy w/ TIE | 4 | 0 | 9 | `[-100.0, 0.0, -100.0] .. [100.0, 96.0, 100.0]` | **4.17%** | 4.17% (roof $Y \in [0, 4]$; 92 LDU hollow) |
| **`30083`** | Windscreen 6 x 6 x 3 Dome with Hinge | 0 | 0 | 8 | `[-60.0, -116.0, -64.0] .. [60.0, 4.0, 4.0]` | **4.17%** | N/A (hemisphere; 4 hinge cylinders at $Y=0, Z=0$) |
| **`30384`** | Windscreen 4 x 7 x 2 Round Pointed | 0 | 0 | 0 | `[-40.0, -48.0, -46.0] .. [40.0, 0.0, 90.0]` | **6.25%** | N/A (hollow archway; 1 nose socket) |
| **`4474`** | Windscreen 6 x 4 x 2 Canopy | 0 | 0 | 6 | `[-40.0, -4.0, -116.0] .. [40.0, 44.0, 4.0]` | **14.58%** | N/A (curved cockpit canopy; 2 side hinge pins) |
| **`30161`** | Windscreen 1 x 4 x 1.333 Bottom Hinge | 0 | 0 | 4 | `[-40.0, -28.0, -4.0] .. [40.0, 4.0, 4.0]` | **12.50%** | N/A (4 hinge cylinders at $Y=0, Z=0$, radius 4) |
| **`13756`** | Glass for Windscreen 2 x 6 x 2 Frame | 0 | 0 | 0 | `[-60.0, 2.0, -30.0] .. [60.0, 40.0, 10.0]` | **10.42%** | N/A (loose glass insert for frame 13760) |
| **`35299`** | Windscreen 3 x 6 x 1 Curved w/ Stud Holder | 0 | 0 | 29 | `[-60.0, 0.0, -49.8] .. [60.0, 24.0, 10.0]` | **12.50%** | N/A (deflector; 3 bottom clip slots) |

*(Measurements computed directly using `resolve_part`, `_stud_box_solid_fraction`, and `numpy` ray-parity parity across LDraw cache geometry).*

---

## 3. Investigation of Question 1: Octagonal Canopies (`2418a`, `2418b`, `2598ps2`)

The octagonal canopies share identical top stud layouts and geometric architecture:
- `2418a` ("Windscreen 6 x 6 Octagonal Canopy without Axlehole"): 4 studs at `(±10, 0, ±10)` with direction `(0, -1, 0)`.
- `2418b` ("Windscreen 6 x 6 Octagonal Canopy with Axlehole"): identical, plus an axle hole at `(0, 0, 0)`.
- `2598` / `2598ps2` ("Windscreen 10 x 10 x 4 Octagonal Canopy"): 4 studs at `(±10, 0, ±10)` with direction `(0, -1, 0)`.

### 3.1. Ray-Parity Solidity Profile Across Height ($Y$)

We measured the solid fraction of the $20 \times 20 \times \Delta Y$ volume directly beneath the studs at various depths:

```
Depth Interval       2418a Solid %    2598 Solid %
--------------------------------------------------
Y in [0, 4]  (roof)     100.0%           93.8%
Y in [0, 8]  (1 plate)   60.4%           75.0%
Y in [0, 12]             35.4%           52.1%
Y in [0, 16] (2 plates)  25.0%           35.4%
Y in [0, 24] (1 brick)   14.6%           20.8%
Y in [0, 48] (full 2418) 10.4%           10.4%
Y in [0, 96] (full 2598)   N/A            4.2%
```

**Why generic stud cell occupancy rejects them:**
`generic_stud_cell_occupancy` requires `STUD_CELL_MIN_SOLID >= 0.15` across the part's full height (`bounds_max[1] - bounds_min[1]`). For `2418a`, the solid fraction across 48 LDU is **0.104 < 0.15**. For `2598`, across 96 LDU it is **0.042 < 0.15**. The engine correctly rejects them because 90% to 96% of the column beneath the studs is empty cockpit air.

### 3.2. Can a Partial-Height Under-Approximation (Roof Plate) Be Safe?

We tested whether an under-approximation covering only the top plate ($Y \in [0, 4]$ or $Y \in [0, 8]$) could be safely authored as a box.

**1. Geometric Violation of Mesh Containment:**
The apex roof of `2418a` is an **octagon**, defined in `2418a.dat` by 8 vertices chamfered at 45°:
`(20, 10)`, `(10, 20)`, `(-10, 20)`, `(-20, 10)`, `(-20, -10)`, `(-10, -20)`, `(10, -20)`, `(20, -10)`.
The chamfer boundary satisfies $|x| + |z| \le 30$.

If a $40 \times 40$ axis-aligned box `[-20, 20] x [0, 4] x [-20, 20]` is placed over the 4 studs:
- The four corners `(19, 2, 19)`, `(-19, 2, 19)`, `(19, 2, -19)`, and `(-19, 2, -19)` lie at $|x| + |z| = 38 > 30$.
- Tested with `part_checks.inside_points(T, pts)`: all 4 corner points return **`False`** (outside the part mesh).
- This violates `part_checks.py` line 152 (`test_occupancy_box_outside_bounds_is_an_error`), which treats any occupancy box protruding beyond the physical mesh as a fatal error.

**2. Inscribed Box Falls Off-Grid:**
To fit completely inside the octagon ($|x| + |z| \le 30$), an axis-aligned square cannot exceed half-side $s = 15$ LDU (a $30 \times 30$ box). A $30 \times 30 \times 4$ box is non-modular: it does not align with the 20 LDU stud pitch in X or Z, and has height 4 LDU (0.5 plates).

**3. Absence of Bottom Sockets:**
`generate_sockets(occupancy)` automatically generates downward-facing sockets at $Y_{\max}$ for every $20 \times 20$ footprint cell in the occupancy box. But on the underside of `2418a` at $Y=4$, there are **no anti-stud tubes or sockets** (lines 30–35 of `2418a.dat` include only `stug-2x2.dat` for top studs; the underside is flat plastic with zero stud tubes). Generating sockets would fabricate non-existent connection points.

**4. Articulated Function:**
In real sets, `2418a` and `2418b` are hinged canopies. They mate via two hinge pins at the rear base ($Y=34, Z=50$, primitives `4-4cylc.dat` and `2-4disc.dat`) to the cockpit base `30200` ("Cockpit 6 x 6 x 3.333 Octagonal Canopy Base"). When opened, the canopy swings through an arc. A static occupancy box cannot represent an opening canopy.

**Conclusion for Question 1:** The octagonal canopies cannot form a valid occupancy family, nor can they be safely under-approximated with static boxes.

---

## 4. Investigation of Question 2: `30083` ("Windscreen 6 x 6 x 3 Dome with Hinge")

`30083.dat` ("Windscreen 6 x 6 x 3 Dome with Hinge"):
- **Bounds:** `[-60.0, -116.0, -64.0] .. [60.0, 4.0, 4.0]`
- **Connectors:** Studs = 0, Holes = 0, Sockets = 0.
- **Hinge Cylinders:** 4 cylinders along the X-axis at $Y=0, Z=0$:
  - `cyl: [36.0, 0.0, 0.0] [-14.0, 0.0, 0.0] radius=4.0`
  - `cyl: [18.0, 0.0, 0.0] [-16.0, 0.0, 0.0] radius=4.0`
  - `cyl: [-36.0, 0.0, 0.0] [14.0, 0.0, 0.0] radius=4.0`
  - `cyl: [-18.0, 0.0, 0.0] [16.0, 0.0, 0.0] radius=4.0`

### 4.1. Relationship to Tonight's Hinge Investigation

In `scripts/ldraw/HINGE_INVESTIGATION.md`, the core architectural finding was:
> *"A LEGO hinge is always two separate static parts (e.g. 2429/2430, 4275b/4276b), never one part with internal articulation... The only missing capability is connector recognition (`hinges` axis pairing) in `brick_parts_validate.py`."*

`30083` is an exact application of this principle:
1. `30083` is the moving half of a finger hinge assembly. Its two pairs of dual fingers at $X \in [2, 18], [22, 36]$ and $X \in [-18, -2], [-36, -22]$ clip directly into matching hinge finger receivers on a vehicle hull.
2. The part itself is a pure hemisphere (`48\4-8sphe.dat` with radius 60 LDU). It is **95.83% empty air** (solid fraction = 0.0417).
3. In official models (e.g. Star Wars set 7163 Republic Gunship, using patterned variant `30083ps0`), the dome houses a clone trooper minifigure sitting at a turret console. The dome rotates about the X-axis at $Y=0, Z=0$ to open and aim.
4. Any static bounding box placed on `30083`:
   - Falsely occupies the interior cavity, colliding with the gunner minifigure.
   - Falsely reports collisions with the surrounding airframe whenever the turret is rotated to any non-zero angle in the model.
5. Related parts with the identical hinge architecture:
   - `50747` / `4505156`: "Windscreen 6 x 6 x 3 Dome Hinge Locking with Two Dual Fingers"
   - `95198`: "Windscreen 8 x 8 x 3.667 Dome Hinge Locking with 2 Dual Fingers"
   - `30161`: "Windscreen 1 x 4 x 1.333 Bottom Hinge" (car windshield with 4 hinge cylinders at $Y=0, Z=0$, radius 4)

**Conclusion for Question 2:** `30083` is not an occupancy problem. It has 0 studs and its physical constraint is defined entirely by its hinge rotation axis at $Y=0, Z=0$. It belongs to the `hinges` connector detector domain and must remain without static occupancy boxes.

---

## 5. Investigation of Question 3: The Remaining Windscreen Shapes

### 5.1. Loose Glass Inserts (`17457`, `13756`, `46103`)
- `17457` ("Windscreen 2 x 6 x 2 Vertical Glass"): bounds `[-58.4, 3.8, -8.4] .. [58.4, 40.0, 30.0]`, studs = 0.
- `13756` ("Glass for Windscreen 2 x 6 x 2 Frame"): bounds `[-60.0, 2.0, -30.0] .. [60.0, 40.0, 10.0]`, studs = 0.
- `46103` ("Glass for Windscreen 4 x 6 x 4 Cab with Hinge"): bounds `[-59.0, 22.0, -66.0] .. [59.0, 72.0, 10.0]`, studs = 0.

**Physical reality:**  
These parts are loose transparent plastic window panes designed to slide into mating frame parts:
- `17457` snaps into frame `17454` ("Windscreen 2 x 6 x 2 Vertical Frame").
- `13756` snaps into frame `13760` ("Windscreen 2 x 6 x 2 Frame").
- `46103` snaps into frame `45406` ("Windscreen 4 x 6 x 4 Cab with Hinge").

In the LDraw library, complete assemblies exist as shortcuts (`17454c01.dat`, `13760c01.dat`, `45406c01.dat`). Each shortcut places the frame and the glass at `(0, 0, 0)` with identity transform.
- The frames **already have full static occupancy** in `public/parts/`: `17454` has 6 stud-cell boxes (`occ=6`), `13760c01` has 2 stud-cell boxes (`occ=2`).
- If `17457` or `13756` were given occupancy boxes, when placed together in a shortcut or model, **the glass occupancy would collide with the frame occupancy**.
- Verdict: Loose glass inserts have no independent structural volume outside their frame and must remain `needs_occupancy=True` (or be classified as interior subparts).

### 5.2. Hinged Canopies and Cockpit Bubbles (`2483`, `2507`, `4474`)
- **`2483`** ("Windscreen 4 x 4 x 3.667 Helicopter"):
  Bounds `[-40, 40] x [-4, 100] x [-76, 4]`, studs = 0, solid fraction = 8.33%.
  Curved transparent bubble (thickness 2 LDU) with two bottom hinge tabs at $Y=98, Z=-56, X=\pm 30$. It encloses the entire helicopter cabin. Any axis-aligned box covering the bubble occupies the cabin and collides with the helicopter pilot.
- **`2507`** ("Windscreen 10 x 4 x 2.333 Canopy"):
  Bounds `[-40, 40] x [-4, 52] x [-196, 4]`, studs = 0, solid fraction = 8.33%.
  Classic long spaceship cockpit canopy (10 studs long). Rear hinge tabs at $Z \in [-8, 0]$. Encloses a 10-stud cockpit interior with seat, steering yoke, and computer slopes. Any axis-aligned box collides with the cockpit contents.
- **`4474`** ("Windscreen 6 x 4 x 2 Canopy"):
  Bounds `[-40, 40] x [-4, 44] x [-116, 4]`, studs = 0, solid fraction = 14.58%.
  Ice Planet cockpit canopy. Side hinge pins at $X = \pm 40, Y = 41.5, Z = 1.5$. Encloses the astronaut cockpit. Any axis-aligned box collides with the pilot.

### 5.3. Pointed Round Archways (`30384`, `89762`, `92279`)
- **`30384`** ("Windscreen 4 x 7 x 2 Round Pointed"):
  Bounds `[-40, 40] x [-48, 0] x [-46, 90]`, studs = 0, solid fraction = 6.25%.
  Rises from $Y=0$ up to $Y=-48$ (2 bricks tall). The front is a pointed dome; the rear is a 7-stud long hollow archway. It possesses one underside anti-stud socket at `(0, -4, -30)` facing up. Underneath the arch is open cockpit air. An axis-aligned box would fill the entire archway.

### 5.4. Cockpits with Non-Flush Studs and Handles (`13252`, `21849`, `27165`, `92579`)
- **`13252`** ("Windscreen 6 x 13 x 2"):
  Star Wars X-Wing cockpit canopy. 4 studs on the roof at $Y=-18, Z=-40$. Below $Y=-12$, it is hollow cockpit air (Luke Skywalker sits beneath). The solid fraction of the column under the studs across the 48 LDU height is 10.4%, failing solidity. A full-height column box would penetrate into the cockpit and collide with the pilot.
- **`21849` / `27165` / `92579` / `92580`**:
  Windscreens with handle bars. In all these parts, the studs sit at $Y=-2.0$, but the front handle bar extends to $Y=-6.0$ (`bounds_min[1] = -6.0`). Because $\text{abs}(Y_{\text{stud}} - Y_{\min}) = 4.0 > 0.1$, the studs are not flush with the top bound. Furthermore, the volume beneath is hollow canopy air.

---

## 6. Contrast: Why Vehicle Windscreens (`2437`, `3823`, `4594`, `6567`, `64453`) Already Resolve Cleanly

It is vital to contrast the unresolved parts with the 33 Windscreen parts already baked in `public/parts/` with `needs_occupancy: false`:

```
Part ID  Title                           Studs  Occupancy Boxes  Where Boxes Sit
-----------------------------------------------------------------------------------------------------
2437     Windscreen 3 x 4 x 1.333 Curved   2           2         (20..40, 0..32, -10..10) and (-40..-20, 0..32, -10..10)
3823     Windscreen 2 x 4 x 2              2           2         (20..40, 0..48, -10..10) and (-40..-20, 0..48, -10..10)
4594     Windscreen 2 x 4 x 2 Vertical     6           6         Left and right pillars + rear wall columns
6567     Windscreen 2 x 6 x 2 w/ Glass     2           2         (40..60, 0..48, -10..10) and (-60..-40, 0..48, -10..10)
64453    Windscreen 1 x 6 x 3              2           2         (40..60, 0..72, -10..10) and (-60..-40, 0..72, -10..10)
2352     Windscreen 2 x 4 x 3              4           2         Outer side pillars (-40..-20) and (20..40)
6267     Windscreen 2 x 12 x 4            12           2         Outer side pillars (-120..-100) and (100..120)
```

**The Structural Principle:**
1. These resolved vehicle windscreens have **solid vertical A-pillars (side uprights)** directly beneath their outer studs.
2. The columns beneath the outer studs are solid plastic from $Y=0$ down to $Y=\text{height}$ (solid fraction $\ge 0.15$).
3. The central glass area between the pillars has **zero studs**.
4. Consequently, `generic_stud_cell_occupancy` naturally emits occupancy boxes **only for the solid side pillars**, leaving the interior cabin completely unblocked.
5. In the unresolved canopies (`2418a`, `2598`, `13252`, `4474`, `2507`), there are **no solid side pillars**. The studs sit on the central roof over the pilot's head, or there are no studs at all.

---

## 7. Architectural Conclusions and Recommendation

1. **Investigation Verdict:**
   - **No shared occupancy family exists.** The unresolved windscreen parts cannot be parameterized by a single mathematical formula or family generator.
   - **No safe axis-aligned under-approximation exists.** Because these parts are hollow shells designed to enclose minifigures, any axis-aligned bounding box of modular thickness (8 or 24 LDU) would falsely collide with interior cockpit builds.
   - **Geometric containment prohibits roof overrides.** The apex of octagonal canopies is chamfered; any axis-aligned box covering the studs protrudes outside the physical mesh, causing fatal errors in CI checks.

2. **Action Taken:**
   - In accordance with the prompt mandate ("investigation only, do NOT implement; honest 'no pattern found' is a legitimate outcome; do not force a guessed box"), **zero speculative boxes were added to `parts.py`**.
   - No test regressions were introduced (`tests/test_generic_stud_occupancy.py` remains 51 passed).

3. **Recommended Follow-up Roadmap:**
   - **Hinged Canopies & Domes (`30083`, `30161`, `50747`, `2483`, `2507`, `4474`):**  
     Handle via the `hinges` connector detector in `brick_parts_validate.py` (scoped in `scripts/ldraw/HINGE_INVESTIGATION.md`). These parts derive their placement and physical validation from hinge axis pairing, not stud occupancy.
   - **Loose Glass Inserts (`17457`, `13756`, `46103`):**  
     Leave with `needs_occupancy=True` or mark as dependent subparts; their structural occupancy is already accounted for by their parent frames (`17454`, `13760`, `45406`).
   - **Hollow Cockpit Canopies (`2418a`, `2418b`, `2598`, `13252`):**  
     Leave as `needs_occupancy=True`. If collision detection in future spec revisions requires collision checking for thin shells, it should be handled via oriented bounding boxes (OBB) or mesh ray-casting, not coarse Cartesian AABBs that obliterate interior cavities.
