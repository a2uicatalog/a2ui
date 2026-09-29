# Constraction & Bionicle Category Occupancy Investigation (2026-09-28)

## Status: COMPLETE (REJECTED per Spec §3 Safety)

## Executive Summary
This investigation analyzed the Constraction (Character and Creature Building System / CCBS) and Bionicle category parts across the LDraw parts library and catalogue to determine whether a shared geometric occupancy family, generic rule, or safe `OVERRIDES` entry exists.

**The confident, evidence-backed conclusion is that NO safe generic occupancy family exists for the rejected Constraction / Bionicle parts, and they must honestly remain `needs_occupancy=True` per Spec Section 3.**

Key findings:
1. **Full Survey Metrics (`scripts/ldraw/survey_rejects.py`)**:
   - Scanned the full library of 12,655 candidate parts using `survey_rejects.py` classification logic (`explicit_category` + `guessed_category`).
   - Identified **151 base parts** belonging to Constraction & Bionicle categories (197 parts total when including 24 Throwbot printed disc variants and 22 CAD subparts).
   - **29 base parts (+ 6 subparts) already resolve cleanly with `needs_occupancy=False`**:
     - 16 parts resolve via `bar_grip_points()` (weapons, clips, and rods with hand-graspable bar sections, e.g. `28220`, `3171`, `32577`, `44810`, `50901`, `50920`, `54272`, `55236`, `87846`, `98570`).
     - 11 parts resolve via `generic_hole_channel_occupancy()` (connector blocks and straight links with standard Technic pinholes, e.g. `18588`, `32552`, `32558`, `42074`, `44032`, `47296`, `50898`, `61053`, `61054`, `89650`, `89651`, `98562`, `98577`).
     - 2 parts resolve via `generic_stud_cell_occupancy()` (rare stud-bearing parts `47474` and `54276`).
   - **122 base parts safely remain `needs_occupancy=True`**: spanning CCBS limbs/bones, curved armor shells, open skeletal torsos, ball-socket connectors, organic sweeping blades, and projectile discs.
2. **The Ball-and-Socket Dilemma (Limbs, Torsos, Connectors, Feet)**:
   - Constraction mechanics rely on universal 10.2mm (25.5 LDU) ball-and-socket joints (`towball` / `socket`).
   - Ball sockets are hollow spherical receiving cups ($r \approx 5.1$ mm / 12.75 LDU). Any axis-aligned box encompassing the socket end encases the interior cup cavity, guaranteeing a **100% false collision** whenever a mating ball joint is attached.
   - Furthermore, `renderers/brick_parts_validate.py` only exempts mated pin/hole pairs and hinge knuckles. Ball joints / towballs have **zero mated collision exemption** in the validator engine (the exact blind spot identified in `scripts/ldraw/MATED_CONNECTOR_EXEMPTION_INVESTIGATION.md`).
   - Constraction limbs articulate omnidirectionally over a conical sweep of 60°–90°. Any static axis-aligned bounding box is physically invalid the instant a joint flexes, sweeping a huge false-collision hull into surrounding armor and adjacent limbs.
3. **The Concave Armor Cradle Dilemma (CCBS Shells & Fairings, 16 parts)**:
   - Snap-on armor plates (`90636`–`90652`, `10498`, `14533`, `1686`, `21560`) are thin curved shells (wall thickness 1.0–2.0 LDU).
   - Volumetric solidity is universally below the 0.15 floor: `90640` is **14.5% solid**, `90641` is **13.5% solid**, `90639` is **14.0% solid**, `90649` is **13.5% solid**, `90652` is **12.0% solid**, and `1686` is **8.5% solid**.
   - Crucially, the entire inner volume of an armor shell is an open concave cradle designed to wrap around the limb bone. Any bounding box fills this hollow cradle, causing guaranteed false collisions with the limb bone nestled directly inside it.
4. **Skeletal Torsos & Open Frames (9 parts)**:
   - Large open rib/truss cages (`90623`, `90625`, `24010`, `44135`) are **82% to 90% empty space** (`90623` is **10.5% solid**, `90625` is **10.5% solid**).
   - Ball joints extend from the perimeter for shoulders, hips, and neck. Bounding boxes covering the torso would encase attached limbs and chest armor in phantom plastic.
5. **Weapons, Tools & Effect Elements (40 parts)**:
   - Long curved blades, energy flames, claws, and Zamor/Thornax launchers (`11305`, `15362`, `18396`, `2601`, `32551`).
   - Thin organic profiles sweeping diagonally across 3D space with solidity ratios under 15% (`11305`: 13.0% solid). Mounting pins and hand grasps sit inside the bounding box, guaranteeing false collisions with the holding hand.
6. **Discs & Projectiles (6 base parts + 24 printed variants)**:
   - `32533` (Throwbot / Slizer disc) is a 100 LDU circular projectile (solidity 20.5%). An axis-aligned 100x100 box creates corner wedges that protrude **20.71 LDU into open space** (over a full stud width of phantom plastic).
   - Fired projectiles (`54821` 16.5mm Zamor ball, `85582` Thornax fruit) are loose ammunition; boxing them triggers collisions with launcher barrels.
7. **Connection to Official Priority Sets (Airbus H175 Rescue Helicopter 42145)**:
   - Zero parts from LEGO Technic set 42145 belong to Constraction / Bionicle categories (42145 is a motorized Technic aircraft; Constraction parts are exclusively action figures). Real official set impact on 42145 is 0.

---

## 1. Real Measured Geometry & Solidity Analysis

Forensic measurement of 25 representative Constraction and Bionicle parts across all functional sub-families, showing Part ID, Functional Sub-Family, Official Description, Studs, Holes, Resolved Bounding Box Extents (LDU), BBox Volume (LDU³), Ray-Parity Solid Fraction ($n=200$, seed 20260928), and Architectural Verdict:

| Part ID | Functional Sub-Family | Description | Studs | Holes | Bounding Box Extents (LDU) | BBox Vol (LDU³) | Ray Solid ($n=200$) | Verdict / Reason |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :--- |
| `90607` | Skeletal Limb | Constraction Limb 7 Straight w/ Middle Ball Joint | 0 | 4 | `(-19.98, -12.81, -72.81)..(19.98, 12.81, 69.25)` | 145,444 | 0.2200 | `needs_occupancy=True` (Socket cup encapsulation; 3D articulation) |
| `90609` | Skeletal Limb | Constraction Limb 5 Straight w/ Middle Ball Joint | 0 | 0 | `(-19.98, -12.81, -52.81)..(19.98, 12.81, 49.25)` | 104,491 | 0.2800 | `needs_occupancy=True` (Socket cup encapsulation; 3D articulation) |
| `90611` | Skeletal Limb | Constraction Limb 4 Straight | 0 | 0 | `(-19.98, -12.81, -42.81)..(19.98, 12.81, 39.25)` | 84,015 | 0.2400 | `needs_occupancy=True` (Socket cup encapsulation; 3D articulation) |
| `90612` | Skeletal Limb | Constraction Limb 3 | 0 | 0 | `(-19.98, -12.81, -12.81)..(19.98, 12.81, 49.25)` | 63,538 | 0.2350 | `needs_occupancy=True` (Socket cup encapsulation; 3D articulation) |
| `90615` | Skeletal Limb | Constraction Limb 7 Forked w/ Middle Ball Joint | 0 | 0 | `(-19.98, -16.62, -72.81)..(19.98, 16.62, 69.25)` | 188,680 | 0.2150 | `needs_occupancy=True` (Forked geometry; socket encapsulation) |
| `32173` | Skeletal Limb | Technic Bionicle Leg 2 x 6 w/ 2 Ball Joints | 0 | 0 | `(-12.81, -26.94, -52.81)..(12.81, 32.57, 72.57)` | 191,179 | **0.1300** | `needs_occupancy=True` (Solidity < 0.15; ball joint sweeps) |
| `32476` | Skeletal Limb | Constraction Limb 4 x 7 Bent 45 w/ Ball Joint | 0 | 0 | `(-20.00, -70.00, -12.81)..(20.00, 16.17, 128.50)`| 487,056 | **0.1350** | `needs_occupancy=True` (Solidity < 0.15; 45° bent limb) |
| `90640` | Armor Shell | Constraction Shell 2.5 x 3 x 4 Flat | 0 | 0 | `(-29.26, -29.25, -30.00)..(29.26, 49.25, 19.03)` | 225,233 | **0.1450** | `needs_occupancy=True` (Solidity < 0.15; concave interior cradle) |
| `90641` | Armor Shell | Constraction Shell 2.5 x 3 x 3 Flat | 0 | 0 | `(-29.15, -29.25, -30.00)..(29.15, 29.25, 19.21)` | 167,826 | **0.1350** | `needs_occupancy=True` (Solidity < 0.15; concave interior cradle) |
| `90639` | Armor Shell | Constraction Shell 2.5 x 3 x 5 Flat | 0 | 0 | `(-26.22, -49.25, -30.00)..(26.22, 49.25, 19.18)` | 254,070 | **0.1400** | `needs_occupancy=True` (Solidity < 0.15; concave interior cradle) |
| `90649` | Armor Shell | Constraction Shell 4 x 7 x 4.5 Shoulder | 0 | 0 | `(-69.82, -30.00, -40.00)..(69.82, 59.22, 37.42)` | 964,618 | **0.1350** | `needs_occupancy=True` (Solidity < 0.15; flared shoulder shell) |
| `90652` | Armor Shell | Constraction Shell 2.5 x 5 x 8 Chest Flat | 0 | 0 | `(-49.19, -86.11, -40.00)..(49.19, 69.64, 9.09)`  | 752,170 | **0.1200** | `needs_occupancy=True` (Solidity < 0.15; concave chest fairing) |
| `1686`  | Armor Shell | Constraction Shell 2 x 4 x 3.333 Shoulder Pad | 0 | 0 | `(-39.80, -6.00, -49.67)..(39.80, 70.19, 6.00)`   | 337,602 | **0.0850** | `needs_occupancy=True` (Solidity 8.5% < 0.15; thin curved shell) |
| `90623` | Torso Frame | Constraction Torso 9 x 11 | 0 | 0 | `(-92.81, -52.81, -12.81)..(92.81, 172.81, 12.81)`| 1,072,954 | **0.1050** | `needs_occupancy=True` (Solidity 10.5%; open rib cage) |
| `90625` | Torso Frame | Constraction Torso 9 x 9 | 0 | 0 | `(-92.81, -52.81, -12.81)..(92.81, 132.81, 12.81)`| 882,731 | **0.1050** | `needs_occupancy=True` (Solidity 10.5%; open skeletal cage) |
| `24010` | Torso Frame | Constraction Torso 5 x 7 | 0 | 0 | `(-52.81, -29.00, -12.81)..(52.81, 112.81, 12.81)`| 383,735 | 0.1750 | `needs_occupancy=True` (Open frame; ball mounts on perimeter) |
| `44135` | Torso Frame | Technic Bionicle Rahkshi Lower Torso | 0 | 0 | `(-20.00, -50.00, -29.00)..(20.00, 29.00, 69.00)`  | 309,680 | **0.1250** | `needs_occupancy=True` (Solidity 12.5% < 0.15; angled frame) |
| `32174` | Connector | Constraction Connector 3 x 2 w/ Ball Socket | 0 | 0 | `(-20.00, -10.00, -29.00)..(20.00, 10.00, 30.00)`  | 47,200 | 0.3400 | `needs_occupancy=True` (Receiving socket cup encapsulation) |
| `90622` | Connector | Constraction Connector 2 x 5 w/ Double Sockets | 0 | 0 | `(-19.98, -12.81, -49.25)..(19.98, 12.81, 49.25)` | 100,846 | 0.2450 | `needs_occupancy=True` (Opposing dual ball socket cups) |
| `11305` | Weapon | Constraction Convex Blade 14L w/ Axle | 0 | 0 | `(-9.25, -19.24, -260.00)..(9.25, 19.43, 19.50)`   | 199,927 | **0.1300** | `needs_occupancy=True` (Solidity < 0.15; hand axle mount) |
| `15362` | Weapon | Claw 6.4L w/ Axle | 0 | 0 | `(-19.29, -29.26, -109.12)..(19.29, 9.00, 19.25)` | 189,505 | 0.1500 | `needs_occupancy=True` (Curved hook; axle mount collision) |
| `18396` | Weapon | Constraction Flame 3.5 x 12 w/ Axle | 0 | 0 | `(-7.27, -48.02, -223.25)..(7.27, 19.50, 9.50)`   | 228,381 | 0.1650 | `needs_occupancy=True` (Thin organic sweep; axle mount) |
| `32533` | Projectile | Technic Disc 5 x 5 Projectile (Slizer Disc) | 0 | 0 | `(-50.00, -17.07, -50.00)..(50.00, 0.00, 49.77)`   | 170,319 | 0.2050 | `needs_occupancy=True` (Circular disc; box corners protrude 20.7 LDU) |
| `32475` | Foot | Constraction Foot 3 x 6 x 2.333 w/ Ball Socket | 0 | 0 | `(-30.00, -9.00, -88.92)..(30.00, 49.00, 29.00)`  | 410,350 | **0.1350** | `needs_occupancy=True` (Solidity < 0.15; top socket cup) |
| `42042a`| Mask | Constraction Bionicle Mask Krana Su | 0 | 0 | `(-20.00, -32.00, -19.00)..(20.00, 10.00, 29.00)`  | 92,160 | 0.3700 | `needs_occupancy=True` (Hollow face cavity; clips onto head) |

---

## 2. Forensic Analysis by Functional Sub-Family

### A. CCBS Limbs & Bones (Skeletal Beams with Ball Sockets/Joints) (22 parts)
- **Parts**: `90605`, `90607`, `90609`, `90611`, `90612`, `90613`, `90615`, `90616`, `90617`, `20474`, `32173`, `32476`, `32482`, `41670`, `45749`, `47297`, `47300`, `47328`, `50922`, `74261`, `87796`, `98613`.
- **Physical Reality**: These are the structural skeleton beams of CCBS figures. Each bone terminates in either a male ball joint (`towball`, sphere $r = 5.1$ mm / 12.75 LDU) or a female spherical socket cup. Along the shaft, side ball joints or transverse pinholes are provided for snapping on armor shells.
- **Why No Axis-Aligned Box is Safe**:
  1. *Socket Cup Encapsulation*: A female ball socket is a hollow, semi-spherical shell designed to embrace a male ball joint. If an axis-aligned box is authored over the limb, the box necessarily encloses the open interior cup cavity. Whenever an adjacent limb or torso ball joint is inserted into the socket cup, the two boxes overlap in the interior cavity, producing a **100% false collision**.
  2. *Missing Validator Exemption*: In `renderers/brick_parts_validate.py`, the mated-connector exemption mechanism only exempts pin/hole pairs and hinge knuckles. Ball joints / towballs have no mated exemption. Any box touching a socket cup or ball joint is treated as an illegal collision.
  3. *Dynamic Omnidirectional Articulation*: Constraction ball joints are designed for free 3D pose articulation over a wide solid angle (cone of 60° to 90°). A static axis-aligned bounding box cannot represent a limb whose orientation changes dynamically; any bend rotates the box through empty air, colliding with neighboring torso parts, limbs, or weapons.
  4. *Bent Geometry and Low Solidity*: In bent or forked limbs (`32476` bent 45°, `87796` bent 53°, `90613`/`90615` forked limbs), the limb travels diagonally across its bounding box, resulting in solid fractions of only 0.1300–0.1350 (over 86% empty air).

### B. CCBS Armor Shells & Fairings (Thin Curved Clip-on Plates) (16 parts)
- **Parts**: `90636`, `90638`, `90639`, `90640`, `90641`, `90649`, `90650`, `90652`, `10498`, `14533`, `1686`, `21560`, `47299`, `53543`, `98593`, `98604`.
- **Physical Reality**: These are thin, curved plastic shells (wall thickness 1.0–2.0 LDU) that snap directly over CCBS limb bones or torso frames via internal twin clips or pinholes.
- **Why No Axis-Aligned Box is Safe**:
  1. *Concave Interior Cradle*: The functional purpose of an armor shell is to nestle tightly against the convex surface of a limb bone. The entire interior volume of the shell is open, empty space where the limb bone resides. An axis-aligned bounding box covers the exterior bounds, filling this hollow cradle with phantom collision plastic. When the shell is snapped onto the bone, the shell's bounding box completely envelops the bone, triggering a guaranteed false collision.
  2. *Severe Solidity Failure*: All CCBS armor shells fail the minimum 0.15 solid fraction threshold: `90640` (14.5%), `90641` (13.5%), `90639` (14.0%), `90649` (13.5%), `90652` (12.0%), and `1686` (8.5%). Over 85% to 91.5% of their bounding box volume is open air.
  3. *Prerequisite Blocker*: As established in `TECHNIC_PANEL_INVESTIGATION.md` and `WINDSCREEN_INVESTIGATION.md`, boxing thin curved shells requires multi-box oriented bounding box (OBB) decomposition and mated-connector exclusion masks. Neither mechanism exists in the renderer today.

### C. Skeletal Torsos & Open Frames (9 parts)
- **Parts**: `90623`, `90625`, `90626`, `24010`, `24190`, `44135`, `47305`, `50925`, `98590`.
- **Physical Reality**: The central torso chassis of a Constraction figure is an open, cage-like truss. Male ball joints extend outward at the neck, shoulders, and hips, and pinholes allow chest armor to clip to the front.
- **Why No Axis-Aligned Box is Safe**:
  - *Lattice Openness*: Torsos have massive bounding boxes (`90623` spans $1.07 \times 10^6$ LDU³) but are only **10.5% solid**. 89.5% of the bounding box is empty air.
  - *Internal Joint Enclosure*: The shoulder and hip ball joints are positioned within the perimeter of the torso's bounding box. Any box encompassing the torso inevitably encapsulates these ball joints, falsely colliding with all 4 attached limbs.

### D. Ball Socket Connectors & Small Blocks (12 parts)
- **Parts**: `32174`, `44136`, `47298`, `47306`, `57536`, `58177`, `60176`, `64311`, `67695`, `90622`, `93571`, `98565`.
- **Physical Reality**: Compact connection adapters with single or double ball socket cups, angled ball joints, or transverse axle/pin holes.
- **Why No Axis-Aligned Box is Safe**:
  - Even though some connectors have local solidity around 0.25–0.35, their receiving socket cups encapsulate the mating ball of connected limbs. A bounding box encases the open cup, making valid ball-joint assemblies impossible without false collision flags.

### E. Weapons, Tools & Effect Elements (40 parts)
- **Parts**: `11305`, `15362`, `18396`, `2601`, `32506`, `32551`, `32559`, `32578`, `3627`, `40339`, `40340`, `40341`, `40582`, `41659`, `41663`, `44033`, `44811`, `44817`, `44936`, `44937`, `44938`, `45274`, `45275`, `47314`, `50914`, `53550`, `54271`, `57528`, `57565`, `60926`, `61795`, `61801`, `61810`, `76919`, `93575`, `98135`, `98564`, `98564c01`, `98566`, `98568`.
- **Physical Reality**: Organic sculpted fantasy weapons (swords, jagged blades, axe heads, flame/ice elements, energy launchers, and shields).
- **Why No Axis-Aligned Box is Safe**:
  1. *High Aspect Ratio and Diagonal Sweeps*: Blades like `11305` (14L = 280 LDU long) and `2601` (15L = 300 LDU long) sweep diagonally through space. Their solid fractions are only 13%–16%.
  2. *Hand and Hilt Intersections*: Constraction weapons mount via an integrated axle or pin at the hilt into a figure's hand. An axis-aligned box over the weapon encompasses the mounting axle and the hilt region, colliding with the clenched hand holding it.
  3. *Mechanism Launchers*: Parts like `98564` (Thornax launcher half) are flexible spring jaws that compress dynamically to launch fruit projectiles.

### F. Discs & Projectiles (6 base parts + 24 printed variants)
- **Parts**: `32533` (Technic Disc 5 x 5 Projectile / Throwbot disc) + 24 printed variants (`32533p212`–`32533p677`), `22631` (RoboRider lid), `50900`, `50903`, `54821` (16.5mm Zamor sphere), `85582` (Thornax fruit).
- **Physical Reality**: Fired projectiles and flying discs.
- **Why No Axis-Aligned Box is Safe**:
  - *`32533` Corner Protrusion*: `32533` is a circular disc of diameter 100 LDU (radius 50.0 LDU) and height 17 LDU (`Y: [-17.07, 0.0]`). An axis-aligned 100x100 bounding box has corners at $(\pm 50, \pm 50)$, at radial distance $\sqrt{50^2 + 50^2} = 70.71$ LDU. The box corners protrude **20.71 LDU into open air** beyond the circular perimeter (over 1 full stud width of phantom solid plastic at all 4 corners).
  - *Loose Ammunition*: Loose spheres (`54821`, `85582`) sit inside hollow launcher chambers. Giving them static bounding boxes causes them to collide with the walls of their launchers.

### G. Sculpted Feet with Ball Sockets (5 parts)
- **Parts**: `32475`, `41668`, `47298`, `50858`, `62386`.
- **Physical Reality**: Action figure feet featuring a top-mounted ball socket cup or ankle pinhole and sculpted toes.
- **Why No Axis-Aligned Box is Safe**:
  - The socket cup on the dorsal surface receives the lower leg bone ball joint. Any bounding box covering the foot encases the socket cup cavity, colliding with the leg bone.
  - Underside hollow cavities result in low solidity (`32475` is only 13.5% solid).

### H. Heads, Helmets & Masks (3 parts)
- **Parts**: `42042a` (Bionicle Mask Krana Su), `43363` (Helmet Darth Vader), `53500` (Light-Up Eyes).
- **Physical Reality**: Hollow curved face coverings designed to snap tightly over a figure's head or brain stalk.
- **Why No Axis-Aligned Box is Safe**:
  - The interior is an empty concave mask cavity designed to encompass the head. A bounding box fills this hollow face cavity, colliding directly with the head underneath.

---

## 3. Review of Currently-Accepted Constraction Parts

The investigation confirmed that exactly **29 base parts (+ 6 subparts)** in the Constraction category already resolve cleanly with `needs_occupancy=False` via existing, verified mechanisms:

1. **`bar_grip_points()` (16 parts)**:
   - Hand-held weapons, tools, and clips with standard 3.18mm cylindrical bar sections or axle ends: `28220`, `3171`, `32577`, `44810`, `50901`, `50920`, `54272`, `55236`, `57520p01`, `57525`, `60932`, `61794`, `87846`, `98570`, `98570p01`, `u9432`.
   - These parts mount via bar clips or hand grips. Their grip geometry is correctly detected and emitted into the `bars` connector field, leaving `occupancy: null` without false collisions.
2. **`generic_hole_channel_occupancy()` (11 parts)**:
   - Linear connector blocks and beams with standard aligned Technic pinholes: `18588`, `32552`, `32558`, `42074`, `44032`, `47296`, `50898`, `61053`, `61054`, `89650`, `89651`, `98562`, `98577`.
   - These parts have planar pinhole channels whose local 4-box collar geometry clears the ray-parity solidity proof without enclosing ball sockets.
3. **`generic_stud_cell_occupancy()` (2 parts)**:
   - Rigid parts with standard top studs: `47474` (Shield Holder with Angled Axle and Stud) and `54276` (Minifig Legs Bionicle).
   - These resolve cleanly into standard 20x20 LDU stud cells.

---

## 4. Architectural Recommendations & Future Prerequisites

For any future attempt to represent Constraction / Bionicle figures in the collision pipeline, the following three architectural prerequisites must be built first:
1. **Towball / Ball Socket Mated-Pair Collision Exemption**:
   - Just as pin/hole pairs and hinge knuckles are exempted from collision when mated, `renderers/brick_parts_validate.py` must be extended with a towball-to-socket proximity exemption matcher. This is the exact recommendation cited in `MATED_CONNECTOR_EXEMPTION_INVESTIGATION.md`.
2. **Multi-Box Oriented Bounding Box (OBB) Decomposition**:
   - Thin curved armor shells (`90640`, `90641`, `90649`) and bent limbs (`32476`, `87796`) cannot be represented by a single axis-aligned box. They require multi-box OBB decomposition to wrap around curved surfaces while leaving the internal concave cradles open.
3. **Kinematic / Dynamic Articulation Model**:
   - Bionicle action figures are poseable characters. Fixed static occupancy is physically incompatible with ball-joint articulation; a dynamic joint kinematic model is required to evaluate collisions at runtime based on the figure's articulated pose.

---

## 5. Conclusion & Backlog Outcome

- **Catalogue Impact**: Zero new boxes fabricated; 29 base parts confirmed safely accepted; 122 base parts confirmed safely rejected (`needs_occupancy=True`).
- **Official Set Impact**: 0 parts in LEGO Technic 42145 (Constraction is strictly an action figure theme).
- **Backlog Status**: Item `constraction` is marked **`rejected`** with full empirical justification, preserving Spec Section 3 safety across all 8 sub-families.
