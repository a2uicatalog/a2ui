# Electric Part Category Occupancy Investigation (2026-09-28)

## Status: COMPLETE

## Executive Summary
This investigation analyzed real Electric-category parts across the LDraw parts library and catalogue to determine whether a shared geometric occupancy family, generic rule, or safe `OVERRIDES` entry exists.

**The confident, evidence-backed conclusion is that NO safe generic occupancy family exists for the rejected Electric-category parts, and they must honestly remain `needs_occupancy=True`.**

Key findings:
1. **Full Survey Metrics (scripts/ldraw/survey_rejects.py)**:
   - Scanned the full library of 12,655 candidate parts using `survey_rejects.py` classification logic (`explicit_category` + `guessed_category`).
   - Identified **1,001 Electric candidate parts** across the library.
   - **245 parts already resolve cleanly with `needs_occupancy=False`**: every standard stud-bearing electrical brick (e.g. `15466c01` USB Flash Drive brick, `189c01` Train 4.5V switch, `19066c01` Power Functions 2.0 Hub, `20841` Tilt Sensor, `2383c01` Light & Sound brick, `2500c01` Lightbrick 1x8, `265ac01` Lightbrick 2x2) is already accepted by `generic_stud_cell_occupancy()` because its flush top studs pass the ray-parity solidity proof.
   - **756 parts are rejected (`needs_occupancy=True`)**:
     - **421 parts are internal CAD subparts (`~Electric`)**: halves of motor casings (`10089`, `10090`, `10130`), cable retainers (`10091`, `10132`), internal PCB plates (`10134`), ultrasonic sensor lens covers (`10361`), and sound buttons (`103683`). These are internal sub-assemblies never placed independently in official sets.
     - **335 parts are standalone electrical components**: spanning flexible cables, motors with moving outputs, hollow battery boxes, switches, plugs, and aftermarket electronics.
2. **Cables, Cords & Wire Harnesses (74 parts)**:
   - Flexible 1D/3D wires (Mindstorms EV3 cables `11145`/`11146`/`11147`, coiled cables `22168`/`22169c01`, extension leads `58118`, 9V twin wires `2775c03`).
   - Volumetric solidity is near zero: `22168` is **0.50% solid**, `22169c01` is **0.81% solid**, `58118` is **3.95% solid**, and `2775c03` is **4.04% solid**. Over **96% to 99.5% of the bounding box is empty air**.
   - Claiming an axis-aligned bounding box over a flexible wire routing across a model directly violates spec section 3 (*"miss a real collision on the dropped area, never report a false one"*): a 25 cm or 50 cm cable box would claim millions of cubic LDU of phantom solid plastic, triggering catastrophic false collisions with all surrounding bricks, gears, and minifigures.
3. **Electric Motors & Moving Shafts (71 parts)**:
   - Power Functions, Powered Up, Control+, and 9V motors (`22169` Control+ L, `22172` Control+ XL, `10089c01` PF Large Case, `58120` PF Medium, `58121`, `99499`, `2838c01`, `5292`, `8883`).
   - Crucially, motors feature rotating output axle hubs (e.g. `10095`, `10152`), transverse and axial pinholes for chassis mounting, and wire exit ports.
   - Any static bounding box occupancy across the drive face directly blocks the motor's own output socket, reporting false collisions against any legitimate Technic axle or gear connected to the motor.
4. **Battery Boxes, Hubs & Enclosures (65 parts)**:
   - Large hollow shells designed to accommodate 6x AA or AAA battery cells (`2847` 9V bottom is **5.86% solid**, `22167` Powered Up 2-Port box is **10.96% solid**, `22127` Control+ hub is **11.60% solid**).
   - Features include open battery compartments, sliding latch lids (`24853`), and connector ports where cable plugs dock. An occupancy box covering the case would falsely collide with cables plugged into the hub ports or chassis beams pinned along mounting recesses.
5. **Switches, Plugs & Mechanism Controls (56 parts)**:
   - Moving mechanism switches (`24854` toggle, `11237` EV3 slider, `2849` buttons) and electrical plug terminals (`23816a`, `2775c01`).
   - Plugs insert directly into hub sockets; an occupancy box would collide with the socket they are mated into.
6. **Third-Party Aftermarket Electronics (69 parts)**:
   - Circuit Cubes (`t1044`–`t1052`) and Brickstuff micro-LEDs/adapters (`t1006`–`t1013`). These are non-LEGO third-party parts with unique miniature footprints that do not follow LEGO System grids.
7. **Connection to Official Priority Sets (Airbus H175 Rescue Helicopter 42145)**:
   - This finding directly corroborates `H175_MECHANISM_INVESTIGATION.md`: set 42145's motorized functions rely on Powered Up / Control+ components (`22167` Battery Box, `22169` L Motor). Both are studless, feature moving mechanical connections, and have hollow internal compartments. Preserving them as `needs_occupancy=True` is the only safe and spec-compliant choice.

---

## 1. Real Measured Geometry & Solidity Analysis

Forensic measurement of 24 representative Electric-category parts, showing Part ID, Description, Studs, Holes, Bounding Box Extents (LDU), BBox Volume (LDU³), True Signed Mesh Volume (LDU³), Volume Solidity Ratio ($V_{\text{mesh}} / V_{\text{bbox}}$), and Ray-Parity Solid Fraction ($\text{solid\_fraction}$, seed 20260928, $n=200$):

| Part ID | Functional Group | Description | Studs | Holes | Bounding Box Extents (LDU) | BBox Vol (LDU³) | Mesh Vol (LDU³) | Vol Ratio | Ray BBox Solid ($n=200$) | Status |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| `22169` | Motor | Electric Control+ L Motor | 0 | 18 | `(-30.0, -39.0, -10.0)..(30.0, 39.0, 150.0)` | 748,800 | 73,900 | **0.0987** | 0.1600 | `needs_occupancy=True` |
| `22169c01`| Motor + Cable | Electric Control+ L Motor w/ Coiled Cable | 0 | 18 | `(-30.0, -79.1, -10.0)..(65.0, 39.0, 312.0)` | 3,612,711 | 29,361 | **0.0081** | 0.0750 | `needs_occupancy=True` |
| `22172` | Motor | Electric Control+ XL Motor | 0 | 54 | `(-50.0, -49.0, -10.0)..(50.0, 49.0, 150.0)` | 1,568,000 | 23,325 | **0.0149** | 0.1350 | `needs_occupancy=True` |
| `10089c01`| Motor Case | Electric Power Functions L Motor Case | 0 | 14 | `(-30.0, -39.5, 0.0)..(30.0, 39.5, 140.0)` | 663,600 | 28,595 | **0.0431** | 0.2200 | `needs_occupancy=True` |
| `10095` | Motor Hub | Electric PF Large Motor Axle Hub | 0 | 0 | `(-20.0, -20.0, 0.0)..(20.0, 20.0, 31.0)` | 49,600 | 7,614 | 0.1535 | 0.1450 | `needs_occupancy=True` |
| `58120` | Motor | Electric PF Medium Motor | 0 | 7 | `(-29.0, -29.0, 0.0)..(29.0, 30.0, 120.0)` | 410,661 | 325,809 | 0.7934 | 0.7250 | `needs_occupancy=True`* |
| `22127` | Battery Hub | Electric Control+ Hub | 0 | 20 | `(-90.0, -50.0, -89.0)..(90.0, 50.0, 89.0)` | 3,204,002 | 371,529 | **0.1160** | 0.3300 | `needs_occupancy=True` |
| `22167` | Battery Box | Electric Powered Up 2 Port Battery Box | 0 | 24 | `(-90.0, -50.0, -89.0)..(90.0, 50.0, 89.0)` | 3,204,002 | 351,218 | **0.1096** | 0.3350 | `needs_occupancy=True` |
| `2846` | Battery Cover | Electric 9V Battery Box 4 x 14 x 4 Cover | 38 | 0 | `(-40.0, -48.0, -140.0)..(40.0, 38.0, 140.0)` | 1,926,400 | 2,485,061** | 1.2900** | 0.1250 | `needs_occupancy=True` |
| `2847` | Battery Bottom| Electric 9V Battery Box 4 x 14 x 4 Bottom | 0 | 0 | `(-40.0, -44.5, -140.0)..(40.0, 48.0, 140.0)` | 2,072,000 | 121,332 | **0.0586** | 0.2350 | `needs_occupancy=True` |
| `2847c02` | Battery Bottom| Electric 9V Battery Box Bottom w/ Buttons | 0 | 0 | `(-40.0, -54.0, -140.0)..(40.0, 48.0, 140.0)` | 2,284,800 | 156,631 | **0.0686** | 0.1800 | `needs_occupancy=True` |
| `74650c01`| Battery Complete| Electric 9V Battery Box 4 x 14 x 4 Complete | 38 | 0 | `(-40.0, -54.0, -140.0)..(40.0, 48.0, 140.0)` | 2,284,800 | 2,328,430** | 1.0191** | 0.2850 | `needs_occupancy=True` |
| `11145` | Cable | Electric Mindstorms EV3 Cable 25 cm | 0 | 0 | `(-78.0, -12.5, -83.5)..(78.0, 12.5, 68.0)` | 590,873 | 234,967 | 0.3977 | 0.1400 | `needs_occupancy=True` |
| `2775c03` | Cable | Electric Cable Grey w/ Plugs (Twin) | 0 | 0 | `(-28.0, -9.5, -198.0)..(28.0, 9.5, 198.0)` | 421,344 | 17,033 | **0.0404** | 0.0800 | `needs_occupancy=True` |
| `22168` | Cable + LED | Electric Powered Up Light w/ Coiled Cable | 0 | 1 | `(-32.5, -79.4, -130.0)..(37.0, 10.0, 163.0)` | 1,820,455 | 9,146 | **0.0050** | 0.1100 | `needs_occupancy=True` |
| `58118` | Cable | Electric PF Extension Wire 50 cm | 4 | 0 | `(-20.0, -64.8, -20.0)..(120.0, 16.0, 220.4)` | 2,718,103 | 107,399 | **0.0395** | 0.1000 | `needs_occupancy=True` |
| `24854` | Switch | Electric Powered Up 2 Port Box Switch | 0 | 2 | `(-40.0, -10.0, -15.0)..(0.0, 8.0, 15.0)` | 21,600 | 8,073 | 0.3738 | 0.3600 | `needs_occupancy=True` |
| `24853` | Battery Lid | Electric Control+ Hub Battery Lid | 0 | 0 | `(-68.0, -32.5, -89.0)..(68.0, 0.0, 86.0)` | 773,500 | 21,803 | **0.0282** | 0.1850 | `needs_occupancy=True` |
| `11237` | Slider | Electric Mindstorms EV3 Selector Slider | 0 | 0 | `(-10.0, -4.0, -44.5)..(10.0, 3.0, 45.5)` | 12,600 | 5,881 | 0.4667 | 0.4200 | `needs_occupancy=True` |
| `23816a` | Plug | Electric Power Functions 2.0 Plug | 0 | 0 | `(-17.0, -9.0, -20.0)..(17.0, 9.0, 14.0)` | 20,808 | 7,055 | 0.3390 | 0.5600 | `needs_occupancy=True` |
| `2775c01` | Plug | Electric Plug (Type 4) Twin Extra-Wide | 0 | 0 | `(-28.0, -9.5, -14.0)..(28.0, 9.5, 15.0)` | 30,856 | 3,739 | **0.1212** | 0.2650 | `needs_occupancy=True` |
| `t1008` | Aftermarket | \| Brickstuff Pico LED | 0 | 0 | `(-5.0, -3.2, -5.0)..(5.0, 1.4, 5.0)` | 460 | 61 | 0.1316 | 0.2450 | `needs_occupancy=True` |
| `t1046c01`| Aftermarket | \| Circuit Cubes Battery | 0 | 0 | `(-40.0, -4.0, -40.0)..(40.0, 48.0, 40.0)` | 332,800 | 72,816 | 0.2188 | 0.3800 | `needs_occupancy=True` |
| `t1052c01`| Aftermarket | \| Circuit Cubes LED | 0 | 0 | `(-40.0, -4.0, -40.0)..(40.0, 48.0, 40.0)` | 332,800 | 47,338 | 0.1422 | 0.3000 | `needs_occupancy=True` |

*\* See Section 3 for detailed discussion of `58120` output shaft interference.*  
*\*\* Mesh volume exceeds bounding box volume on multi-part assemblies (`2846`, `74650c01`) due to internal self-intersecting component shells and sub-file overlaps in the LDraw definition.*

---

## 2. Forensic Analysis by Functional Sub-Group

### A. Cables, Cords, and Flexible Leads (74 parts)
Flexible electrical cables in LEGO sets are routed freely around models through air, clips, and Technic holes. In LDraw, cables are modeled in fixed, static poses (coiled, draped, or extended between fixed coordinates).
- **Physical Reality**: A physical LEGO wire has cross-sectional diameter $\approx 1.5$–$3.0$ LDU. However, when coiled or draped across a model, its 3D bounding box spans huge volumes:
  - `22168` (Powered Up Light with Coiled Cable): BBox volume is $1.82 \times 10^6$ LDU³, but mesh volume is only 9,146 LDU³ (**0.50% solid**). **99.5% of the bounding box is empty air.**
  - `22169c01` (Control+ L Motor with Coiled Cable): BBox volume is $3.61 \times 10^6$ LDU³, with mesh volume 29,361 LDU³ (**0.81% solid**).
  - `58118` (Power Functions 50 cm Extension Wire): BBox volume is $2.72 \times 10^6$ LDU³ (**3.95% solid**).
- **Spec Section 3 Safety Violation**:
  Spec section 3 dictates:
  > *"Occupancy is deliberately under-approximated (spec section 3: under-approximation is always safe): miss a real collision on the dropped area, never report a false one."*
  If an axis-aligned box were placed over a cable, it would claim solid plastic across the entire 3D volume spanned by the wire. Any brick placed within the wire's loop, under the coil, or adjacent to the connected motor would trigger a false collision against empty air. Cables must have zero occupancy (`occ: null`).

### B. Electric Motors and Rotating Hubs (71 parts)
LEGO motors (Power Functions, Powered Up, Control+, Mindstorms, 9V) are active electro-mechanical units.
- **Drive Interfaces and Axle Intersections**:
  - In parts like `58120` (PF Medium Motor), the outer case appears relatively solid ($V_{\text{ratio}} = 0.7934$), but its primary functional surface is at `Z = 0.0`: a central Technic axle socket surrounded by 4 mounting pinholes.
  - When a model is assembled, a Technic axle or gear is inserted directly into the motor's axle socket at `Z = 0.0`. If a static occupancy box covers the motor's front face (`Z \in [0.0, 120.0]`), the inserted axle or gear's occupancy boxes would overlap with the motor's occupancy box, triggering a false collision error.
  - In `22169` (Control+ L Motor) and `10089c01` (PF L Motor), the motor housing has rotating hubs (`10095`, `10152`) and multiple side mounting flanges with pinholes. The housing itself is only **4.3% to 9.8% solid** because of internal gear train cavities, wire routing channels, and weight-reducing recesses.
  - Attempting to author multi-box approximations for motors without dynamic clearance for rotating shafts inevitably creates false collisions on valid motorized drivetrains.

### C. Battery Boxes, Hubs, and Electronic Modules (65 parts)
Electronic battery boxes (`22127`, `22167`, `2847`, `2847c02`, `74650c01`) house batteries, circuit boards, and connectors.
- **Hollow Battery Cavities**:
  - `2847` (9V Battery Box Bottom): BBox volume is $2.07 \times 10^6$ LDU³, mesh volume is $121,332$ LDU³ (**5.86% solid**). It is a thin-walled open tray designed to hold 6 AA batteries.
  - `22127` (Control+ Hub) and `22167` (Powered Up 2-Port Box): Mesh volume is only $351,000$–$371,000$ LDU³ out of $3.20 \times 10^6$ LDU³ bbox volume (**10.96%–11.60% solid**).
- **Functional Ports and Sockets**:
  - Hubs feature wire connector ports on their top or front faces where plugs (`23816a`, `2775c01`) dock.
  - If the hub body is represented by a bounding box, any plug inserted into a port falsely collides with the hub.
  - Furthermore, `2846` and `74650c01` have studs on their covers at `Y = -48.0` (not standard `Y = 0.0`), but their large red toggle buttons protrude to `Y = -54.0` in the middle of the stud field, preventing clean planar stud-cell anchoring.

### D. Switches, Sliders, and Moving Mechanism Controls (32 parts)
- Parts like `24854` (Powered Up Battery Box Switch), `11237` (EV3 IR-Beacon Slider), `2849` (9V Battery Box Buttons), and `24853` (Hub Battery Lid) are kinetic mechanism parts.
- They are small components that slide, pivot, or detach during operation. Modeling them with static occupancy would prevent valid mechanical actuation and movement.

### E. Plugs, Connectors, and Terminals (24 parts)
- Electrical plugs (`23816a`, `2775c01`, `5306bc01`) are male connector ends.
- Their physical purpose is to mate inside the corresponding female receptacle on a battery box or hub. Under standard AABB/OBB collision rules without specialized plug-mating exemption masks (analogous to the pin/hole mated connector exemption in `renderers/brick_parts_validate.py`), a plug inside a socket is detected as a collision.

### F. Internal CAD Subparts (`~Electric`, 421 parts)
- Over 55% of all rejected electric parts in LDraw (421 of 756) are sub-files marked with the `~` prefix.
- Examples: `10089` (PF Large Motor Case Back), `10090` (PF Large Motor Case Front), `10091` (PF Large Motor Cable Retainer), `10130` (PF Servo Case Back), `10134` (PF Servo Internal Front Plate), `10361` (EV3 Ultrasonic Sensor Front).
- These files are internal CAD construction primitives used inside composite `.dat` files. They are never standalone inventory parts in official LEGO sets and must remain `needs_occupancy=True`.

### G. Third-Party Aftermarket Electronics (69 parts)
- 69 parts represent aftermarket lighting systems: Circuit Cubes (`t1044`–`t1052`) and Brickstuff (`t1006`–`t1013`).
- These non-LEGO parts have micro scale dimensions ($10 \times 4.6 \times 10$ LDU for `t1008`), custom pin/clip geometries, and non-standard stud pitches. They cannot be governed by LEGO System or Technic occupancy rules.

---

## 3. The 245 Already-Accepted Electric Parts

It is critical to note that the Electric category in `a2ui` is **not completely unhandled**.
A full scan confirms that **245 Electric parts already resolve cleanly with `needs_occupancy=False`**.
Every electric part that conforms to standard LEGO brick morphology (rigid plastic shell with flush top studs at `Y = 0.0`) is already handled automatically by `generic_stud_cell_occupancy()`:
- `15466c01`–`15466p01c02`: Electric Brick 2 x 4 with USB Flash Drive (8 boxes, 8 sockets).
- `189c01`: Electric Train 4.5V On/Off Switch Brick 2 x 4 (7 boxes, 7 sockets).
- `19066c01`: Electric Power Functions 2.0 Hub (20 boxes, 20 sockets).
- `19071`: Electric Power Functions 2.0 Hub with Battery Box (18 boxes, 18 sockets).
- `19079`: Electric Power Functions 2.0 Hub Battery Box (8 boxes, 8 sockets).
- `20841`: Electric Power Functions 2.0 Tilt Sensor (8 boxes, 8 sockets).
- `20844`: Electric Power Functions 2.0 IR Distance Sensor (6 boxes, 6 sockets).
- `21980`: Electric Power Functions 2.0 Medium Motor (4 boxes, 4 sockets).
- `2383c01` & 8 patterned variants: Electric Light & Sound Brick 1 x 2 x 1.667 (2 boxes, 2 sockets).
- `2500c01`: Electric Light & Sound Brick 1 x 8 with 3 Lights (8 boxes, 8 sockets).
- `265ac01`: Electric Lightbrick 2 x 2 Type 1 4.5V (4 boxes, 4 sockets).

These parts prove that the existing pipeline is working as intended: parts with true rigid brick morphology receive mathematically verified occupancy boxes, while non-rigid, motorized, hollow, or mechanism-bearing electronics are safely rejected.

---

## 4. Priority Set Impact: LEGO Technic 42145 (Airbus H175 Rescue Helicopter)

In official Technic set 42145-1 ("Airbus H175 Rescue Helicopter", 2,001 pieces):
- Motorization is powered by:
  - **`22167`** (Electric Powered Up 2 Port Battery Box, 6x AA)
  - **`22169`** (Electric Control+ L Motor)
- This investigation confirms that both `22167` and `22169` must remain `needs_occupancy=True`:
  - `22167` has 24 pinholes on side mounting rails, an open internal battery compartment, and front connector sockets for the motor lead.
  - `22169` has an orange rotating output hub where a Technic axle inserts to drive the helicopter's main rotor gearbox and winch.
- Forcing a box on either part would break the 42145 model validation by falsely reporting collisions against the drive axle and chassis pins.
- This fully validates the prior finding in `H175_MECHANISM_INVESTIGATION.md`.

---

## 5. Conclusion and Pipeline Verification

- **Verdict**: No new occupancy family should be introduced for Electric parts.
- **Safety**: Under spec section 3, omitting occupancy (`needs_occupancy=True`, `occupancy: null`) for complex motorized, hollow, and flexible parts ensures that valid user-built models and official sets will not suffer false collision rejections.
- **Regression Protection**: Added comprehensive exclusion tests in `tests/test_generic_stud_occupancy.py` covering representative motors, battery boxes, coiled cables, and switches to guarantee they remain safely rejected.
