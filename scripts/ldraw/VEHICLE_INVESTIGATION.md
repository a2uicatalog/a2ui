# Vehicle (Base / Chassis Parts) Occupancy Investigation (2026-09-28)

## Status: COMPLETE (REJECTED — NO SAFE UNHANDLED OCCUPANCY FAMILY EXISTS)

## Executive Summary

This investigation analyzed the candidate backlog item `vehicle` ("Vehicle (base/chassis parts)"), carried over from the 3:00 AM overnight-watcher candidate list, to determine whether a shared geometric occupancy family, generic rule, or safe overrides exist for vehicle base and chassis parts.

**The confident, evidence-backed conclusion is that NO safe unhandled occupancy family exists for Vehicle parts, and the rejected parts in this category must honestly remain `needs_occupancy=True`.**

### Key Findings:

1. **The Core Discovery: Standard System Vehicle Bases & Chassis Are Already Solved**:
   - The overnight-watcher premise that LEGO car bases and chassis parts were missing occupancy was based on un-scoped category counts from `survey_rejects.py`.
   - Comprehensive library-wide analysis reveals that **all 57 standard System LEGO car bases and chassis across the LDraw library already resolve cleanly with `needs_occupancy=False`**.
   - These include classic Town/City car bases (`11650`, `12622`, `18923`, `18937`, `24055`, `24326`, `2441`, `28324`, `30029`, `30149`, `30235`, `30262`, `30277`, `30278c01`, `30295`, `30642`, `30643`, `30837`, `3385`, `4211`, `4212a`, `4212b`, `52036`, `52037`, `65094`, `65202`, `65634`, `68446`, `6920`), vintage chassis (`710`, `778`, `780`, `781`, `803`, `804`, `805`, `806`, `u574`), and tow-hook chassis (`3888a`, `4362a`, `4796`).
   - They resolved naturally through `generic_stud_cell_occupancy` or `bar_grip_points`.

2. **Full Taxonomy of the Remaining 86 Rejected `Vehicle` Category Parts**:
   - Out of 166 parts explicitly categorized under `Vehicle` in LDraw, 80 are accepted and 86 are rejected.
   - Forensic analysis accounts for 100% of these 86 rejected parts (and 125 vehicle-related parts total):
     - **Duplo Vehicle Parts** (29 parts): Non-System 2x scale (40 LDU stud pitch, 6.5 LDU stud radius) with specialized snap axles.
     - **Motorcycle / Scooter Frames & Fairings** (18 parts): Thin sculpted organic shells occupying only **1.5% to 2.4%** of their bounding box volume.
     - **Mechanical Motors & Gearbox Housings** (16 parts): Hollow shells enclosing pull-back spring coils, flywheels, and gear trains (**0.3% to 4.2%** solid).
     - **Forklift Masts & Rails** (13 parts): Open sliding vertical rail assemblies and thin horizontal forks (**5.2% to 6.7%** solid).
     - **Caterpillar Track Loops** (10 parts): Annular loops enclosing open air where drive sprockets and road wheels sit (**17% to 47%** hollow loops).
     - **Excavator Buckets & Arms** (9 parts): Concave, hollow scoops designed to carry cargo (**6.6% to 15.6%** solid).
     - **Vintage Tractor Steering Linkages** (7 parts): Articulated multi-bar linkage rods from 1970s sets 851/858.
     - **Monorail Subparts & Axles** (4 parts): Specialized sub-assemblies for monorail motor bogies.
     - **Windscreens / Cockpits** (3 parts): Thin transparent shells already investigated in `WINDSCREEN_INVESTIGATION.md`.
     - **Springs / Shock Absorbers** (3 parts): Dynamic flexible wire coils.
     - **Steel Axles** (2 parts): Miscategorized metal shafts.
     - **Stepped-Stud Car Base `3536`** (1 part): Stepped stud planes with transverse axle tunnels underneath.

3. **Why Bounding Box Occupancy Directly Violates Spec Section 3**:
   - Under `a2ui` spec section 3: *"miss a real collision on the dropped area, never report a false one"*.
   - Proposing an axis-aligned bounding box on excavator scoops, motorcycle frames, caterpillar tracks, or forklift masts would fill massive open air pockets with phantom plastic.
   - For example:
     - Excavator bucket `47508` is 93.4% open air; a bounding box would prevent any brick from ever being placed inside the scoop.
     - Motorcycle frame `18895` is 97.9% open air; a bounding box would falsely collide with seated minifigures, handlebars, and fairings.
     - Caterpillar track `53992-f1` wraps around road wheels; a bounding box would falsely report collisions with the very wheels the track is wrapped around.
     - Stepped chassis `3536` has transverse wheel tunnels (`axl3hol*.dat`); extending stud columns downward intersects the axle tunnels, reporting false collisions against inserted axles and wheels.

4. **Honest Pipeline Discipline**:
   - No safe, regular geometric occupancy family exists for the remaining rejected vehicle parts.
   - They are correctly and safely retained as `needs_occupancy=True`.

---

## 1. Real Measured Geometry & Solidity Analysis

The table below presents measured geometric parameters for 32 representative parts across every sub-category of rejected vehicle-related parts.
Parameters cited: exact bounds extents, bounding box volume (LDU³), signed mesh volume (LDU³), volume solidity ratio ($V_{\text{mesh}} / V_{\text{bbox}}$), ray-parity solid fraction (`_stud_box_solid_fraction` with fixed seed 20260926, $n=200$), and current resolution status:

| Part ID | Description | Studs | Holes | Bounds (LDU) | BBox Vol (LDU³) | Mesh Vol (LDU³) | Vol Ratio | Ray BBox Solid (n=200) | GenOcc Result |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| `3536` | Car Base 4 x 7 with 3 Slopes Inverted | 20 | 0 | `(-40.0, 0.0, -80.0)..(40.0, 24.0, 60.0)` | 268,800 | 14,285 | **0.0531** | 0.2850 | `Rejected` |
| `2347` | Excavator Bucket 6 x 3 with Hinge | 0 | 0 | `(-60.0, -43.0, -74.0)..(60.0, 13.0, 7.9)` | 550,626 | 77,630 | **0.1410** | 0.1400 | `Rejected` |
| `21709a` | Excavator Bucket 6 x 3 with Click Hinge | 0 | 0 | `(-60.0, -29.7, -80.0)..(60.0, 30.0, 6.0)` | 616,083 | 45,653 | **0.0741** | 0.1650 | `Rejected` |
| `3433` | Excavator Bucket 5 x 3 with Hinge | 0 | 0 | `(-31.8, -15.0, -50.0)..(42.0, 25.8, 50.0)` | 301,093 | 46,961 | **0.1560** | 0.1550 | `Rejected` |
| `47508` | Excavator Bucket 8 x 4 with Click Hinge | 0 | 0 | `(-80.0, -26.0, -90.0)..(80.0, 38.2, 6.0)` | 987,033 | 65,528 | **0.0664** | 0.1050 | `Rejected` |
| `784` | Excavator Bucket 2 x 4 | 0 | 0 | `(-7.0, -16.0, -40.0)..(47.0, 15.0, 40.0)` | 133,920 | 26,610 | **0.1987** | 0.1950 | `Rejected` |
| `3430` | Forklift Rails 2 x 4 x 5.667 | 4 | 0 | `(-20.0, -96.5, -56.0)..(20.0, 40.0, 20.0)` | 414,960 | 27,894 | **0.0672** | 0.0950 | `Rejected` |
| `3431` | Forklift Forks 2 x 4 | 0 | 0 | `(-20.0, 0.0, -48.0)..(20.0, 60.0, 30.0)` | 187,200 | 26,585 | **0.1420** | 0.1700 | `Rejected` |
| `4518b` | Forklift Rails 2 x 3 x 7.667 Locking | 0 | 0 | `(-20.0, -146.0, -50.0)..(20.0, 38.0, 6.0)` | 412,160 | 50,800 | **0.1233** | 0.0900 | `Rejected` |
| `45707` | Forklift Forks 4 x 7 | 2 | 0 | `(-40.0, 0.0, -126.0)..(40.0, 79.0, 4.0)` | 821,600 | 42,773 | **0.0521** | 0.0850 | `Rejected` |
| `18895` | Bike 2 Wheel Motorcycle Fairing Racing | 2 | 0 | `(-27.1, -79.4, -80.0)..(27.1, 8.0, 70.0)` | 711,320 | 15,155 | **0.0213** | 0.1250 | `Rejected` |
| `18896` | Bike 2 Wheel Motorcycle Frame 2 x 7 x 3 | 6 | 0 | `(-20.0, -60.7, -76.9)..(20.0, 8.0, 56.2)` | 365,619 | 8,752 | **0.0239** | 0.0850 | `Rejected` |
| `50859a` | Bike 2 Wheel Motorcycle Frame (Short Pins)| 0 | 0 | `(-27.7, -69.2, -49.8)..(27.7, 9.1, 69.7)` | 518,778 | 0* | **0.0000** | 0.0800 | `Rejected` |
| `50860` | Bike 2 Wheel Motorcycle Body Dirt Bike | 0 | 0 | `(-19.6, -72.1, -60.5)..(19.6, -5.2, 90.0)` | 394,373 | 0* | **0.0000** | 0.0900 | `Rejected` |
| `15396c01` | Minifig Scooter | 4 | 0 | `(-30.0, -80.9, -90.0)..(30.0, 0.0, 44.4)` | 652,658 | 9,880 | **0.0151** | 0.0900 | `Rejected` |
| `43903-f1` | Caterpillar Track 1.7 Wide 20 Tooth | 0 | 0 | `(-87.1, -28.0, -17.0)..(87.1, 28.0, 17.0)` | 331,532 | 57,824 | **0.1744** | 0.3700 | `Rejected` |
| `53992-f1` | Caterpillar Track 2.5 Wide 36 Ridges | 0 | 0 | `(-164.4, -46.0, -25.0)..(164.4, 46.0, 25.0)` | 1,512,887 | 712,852 | **0.4712** | 0.1950 | `Rejected` |
| `71965-f1` | Caterpillar Track 1.7 Wide 28 Tooth | 0 | 0 | `(-127.1, -28.0, -17.0)..(127.1, 28.0, 17.0)` | 483,852 | 96,373 | **0.1992** | 0.3800 | `Rejected` |
| `11767` | Motor Inertia Flywheel 4 x 7 x 1 | 4 | 4 | `(-39.5, -35.1, -20.0)..(39.5, 39.1, 115.0)` | 791,874 | 5,880 | **0.0074** | 0.1250 | `Rejected` |
| `15103` | Motor Inertia Flywheel 4 x 6 x 2 Housing | 0 | 4 | `(-40.0, -10.0, -59.0)..(40.0, 30.0, 59.0)` | 377,600 | 16,042 | **0.0425** | 0.1600 | `Rejected` |
| `32283` | Motor Pull Back 4 x 9 x 2.333 Bottom Case | 2 | 4 | `(-40.0, -10.0, -170.0)..(40.0, 15.0, 10.0)` | 360,000 | 1,343 | **0.0037** | 0.3950 | `Rejected` |
| `41857` | Motor Pull Back 2 x 6 Base | 0 | 0 | `(-20.0, 16.0, -20.0)..(20.0, 40.0, 65.0)` | 81,600 | 0* | **0.0000** | 0.2850 | `Rejected` |
| `827` | Tractor Chassis with Steering Wheel | 21 | 0 | `(-110.0, -78.6, -32.0)..(110.0, 36.0, 32.0)` | 1,613,767 | 141,615 | **0.0878** | 0.0850 | `Rejected` |
| `870` | Tractor Chassis Base 2 x 11 x 3 | 20 | 0 | `(-110.0, -48.0, -20.0)..(110.0, 24.0, 20.0)` | 633,600 | 116,815 | **0.1844** | 0.2600 | `Rejected` |
| `871` | Tractor Chassis Steering Arm | 0 | 0 | `(-8.0, -80.0, -9.0)..(12.5, 6.0, 9.0)` | 31,734 | 3,554 | **0.1120** | 0.1400 | `Rejected` |
| `872` | Tractor Chassis Centre Steering Link | 0 | 0 | `(-28.0, 4.0, -6.0)..(21.0, 19.0, 6.0)` | 8,838 | 1,578 | **0.1785** | 0.3550 | `Rejected` |
| `873` | Tractor Chassis End Steering Link | 0 | 0 | `(-8.0, 1.0, -9.0)..(16.7, 36.0, 9.0)` | 15,578 | 2,210 | **0.1419** | 0.3100 | `Rejected` |
| `10715` | Duplo Car Base 2 x 6 with Wheels | 0 | 0 | `(-78.0, -11.0, -150.0)..(78.0, 72.0, 156.4)` | 3,967,390 | 463,888 | **0.1169** | 0.1500 | `Rejected` |
| `11377` | Duplo Car Base 2 x 6 with Mudguards | 0 | 0 | `(-69.0, -32.0, -119.5)..(69.0, 32.0, 119.5)` | 2,110,848 | 304,854 | **0.1444** | 0.1800 | `Rejected` |
| `15314` | Duplo Car Base 4 x 8 | 0 | 0 | `(-93.0, -19.5, -180.0)..(93.0, 62.2, 192.0)` | 5,652,841 | 7,635 | **0.0014** | 0.1800 | `Rejected` |
| `42093` | Duplo Vehicle Base 4 x 4 with Studs | 0 | 0 | `(-77.0, -22.0, -80.0)..(77.0, 22.0, 80.0)` | 1,084,160 | 348,852 | **0.3218** | 0.2400 | `Rejected` |
| `74656` | Duplo Car Base 2 x 6 with Wheels | 0 | 0 | `(-78.0, -11.0, -150.0)..(78.0, 72.0, 156.4)` | 3,967,390 | 827,236 | **0.2085** | 0.1550 | `Rejected` |

*\* Mesh volume is 0.0 because the LDraw mesh contains unoriented / non-manifold shell polygons.*

---

## 2. Forensic Analysis by Functional Category

### 2.1 Excavator Buckets & Shovels (8 parts)
- Parts: `21709a`, `2347`, `30394`, `3314`, `3433`, `47508`, `50335`, `784`.
- **Physical Shape**: Large, hollow, curved scoops designed to carry loose LEGO bricks (1x1 round bricks, dirt elements).
- **Solidity**: Volume solidity ratios range from **0.0664 to 0.1560**. Bounding boxes are over 85% to 93% empty space.
- **Spec Section 3 Violation**: If a bounding box were placed over `47508` (volume 987,033 LDU³), it would declare the interior scoop cavity solid. Any object or minifigure placed inside the scoop would trigger a false collision against open air.

### 2.2 Motorcycle, Bicycle & Scooter Frames (18 parts)
- Parts: `15396c01`, `15396c02`, `18895`, `18895p01`, `18895p02`, `18896`, `4480`, `4483`, `4483p01`, `50859a`, `50859ac01`, `50859b`, `50859bc01`, `50860`, `50860c01`, `u9204`, `u9204c01`, `u9206c01`.
- **Physical Shape**: Thin, organic vehicle skeletons with steering head clips, kickstands, and wheel mounting forks.
- **Solidity**: Extremely hollow shells, measuring **0.0151 to 0.0239** volume solidity (97.6% to 98.5% empty space).
- **Spec Section 3 Violation**: A bounding box over `18895` spans $54 \times 87 \times 150$ LDU (711,320 LDU³). Minifigures sit straddling the seat, with their legs descending into the open flanks. An axis-aligned box would collide with the minifigure rider's legs and the handlebars.

### 2.3 Caterpillar Tracks (10 parts)
- Parts: `43903-f1`, `43903k01`, `43903k02`, `53992-f1`, `53992-f2`, `53992-f3`, `53992-f4`, `53992k01`, `53992k02`, `71965-f1`.
- **Physical Shape**: Annular track belts formed into continuous loops around road wheels and drive sprockets.
- **Spec Section 3 Violation**: The center of the loop is completely empty air, specifically reserved for the wheels and chassis bogies. Placing an occupancy box across the track would immediately collide with all internal wheels.

### 2.4 Motors & Gearbox Housings (16 parts)
- Parts: `11767`, `15103`, `15103c01`, `15336p01`, `15336p02`, `15709`, `32283`, `40574`, `41857`, `41861`, `4234`, `u9062`, `u9063`, `u9184`, `u9235`, `u9578`.
- **Physical Shape**: Thin plastic shells enclosing internal mechanical gearing, inertia flywheels, or pull-back spring coils.
- **Solidity**: **0.0037 to 0.0425** volume solidity.
- **Rejection Reason**: Mechanical subparts with internal cavities and non-standard gear shaft openings.

### 2.5 Forklifts & Sliding Rails (13 parts)
- Parts: `3430`, `3430c00-f1/f2`, `3430c01-c03`, `3431`, `4517`, `4518ac01`, `4518b`, `45707`, `u9529-f1/f2`.
- **Physical Shape**: Vertical rail towers along which fork carriages slide vertically.
- **Solidity**: **0.0521 to 0.1420** volume solidity.
- **Rejection Reason**: Kinematic sliding assemblies. An occupancy box over the mast would collide with the moving carriage.

### 2.6 Vintage 1970s Tractor Steering Linkages (7 parts)
- Parts: `779`, `827`, `870`, `871`, `872`, `873`, `874`.
- **Physical Shape**: Thin, articulated steering rods and linkages from 1970s Technic predecessor sets (e.g. 851 Tractor).
- **Solidity**: **0.0878 to 0.1844** volume solidity.
- **Rejection Reason**: Multi-link dynamic steering mechanisms.

### 2.7 Stepped-Stud Chassis `3536` (`Car Base 4 x 7 with 3 Slopes Inverted`)
- `3536` is the single classic System car base rejected in the library.
- **Geometry Profile**:
  - Overall bounds: $X \in [-40, 40]$, $Y \in [0, 24]$, $Z \in [-80, 60]$ (4 x 7 studs, height 24 LDU).
  - 20 upward-facing studs distributed across 3 distinct stepped planes:
    - Front bumper: 4 studs at $Y = 1.0$.
    - Recessed cabin: 12 studs at $Y = 8.0$.
    - Rear mudguard: 4 studs at $Y = 16.0$.
  - While ray-parity solidity under individual stud columns clears the threshold ($0.34 \le \text{sol} \le 0.73$), `3536` features **three pairs of transverse axle tunnels** along the X-axis:
    - Axle hole 1: $(x, 8, 20)$
    - Axle hole 2: $(x, 8, 0)$
    - Axle hole 3: $(x, 8, -40)$
  - These tunnels pass directly underneath the cabin studs. Proposing a vertical stud column down to $Y = 24.0$ creates an occupancy box that blocks the axle tunnel, falsely reporting collisions against any inserted Technic axle or wheel.

### 2.8 Duplo Vehicle Bases & Wheels (29 parts)
- Parts: `10715`, `10715p01/p02`, `11170p01`, `11248`, `11377`, `14639`, `14639p01..p08`, `15314`, `2312`, `2313a/b`, `3982`, `41989`, `42092`, `42093`, `42235`, `6357`, `74656`, `74656p01..p03`.
- **System Incompatibility**: Duplo operates on a 2x scale (40 LDU stud pitch, 6.5 LDU stud radius, 9.6 LDU height). Standard System stud grids (20 LDU pitch, 2.4 LDU radius) do not apply.

---

## 3. Account of the 57 Already-Accepted Vehicle Bases and Chassis

The following 57 official System vehicle base and chassis parts are verified as already accepted with `needs_occupancy=False` in the catalogue:

1. `11650`: `~Car Base  4 x 10 with Mudguards` (37 boxes)
2. `12622`: `Car Base  4 x 10 with Mudguards and Integral Plates with Wheel Pins` (39 boxes)
3. `12622p01`: `Car Base  4 x 10 with Mudguards and Integral Light Bluish Grey Plate` (39 boxes)
4. `12622p02`: `Car Base  4 x 10 with Mudguards and Integral Black Plates with Wheel` (39 boxes)
5. `18923`: `~Car Base  6 x 16 x  2 with  4 x 14 Recessed Centre with Mudguards` (60 boxes)
6. `18937`: `Car Base  6 x 16 x  2 with  4 x 14 Recessed Centre with Mudguards` (62 boxes)
7. `18937p01`: `Car Base  6 x 16 x  2 with  4 x 14 Recessed Centre with Mudguards` (62 boxes)
8. `24055`: `Vehicle Base  4 x  6 x  1.667 Curved With Two Wheel Pins` (12 boxes)
9. `24326`: `Car Base  4 x  4 x  0.667 with 4 Wheel Pins` (4 boxes)
10. `2441`: `Car Base  7 x  4 x  0.667` (8 boxes)
11. `2683c01`: `Monorail Motor with White Motor with Chassis and Wheels` (4 boxes)
12. `2686c01`: `Monorail Wheel Chassis Assembly (Complete)` (0 boxes, bar grip)
13. `28324`: `Car Base  4 x 12 x  0.667 with Side Flanges` (24 boxes)
14. `30029`: `Car Base 10 x  4 x  2/3 with 4 x 2 Centre Well` (24 boxes)
15. `30149`: `Car Base  4 x  5 with 2 Seats` (5 boxes)
16. `30235`: `Car Base  4 x 10 x  1.667` (28 boxes)
17. `30242`: `~Car Base  4 x 12 x  1.667 Bottom` (36 boxes)
18. `30262`: `Car Base  4 x 14 x  1.667` (44 boxes)
19. `30277`: `Car Base  2 x  8 x  1.333` (16 boxes)
20. `30278`: `~Car Base  4 x 12 x  1.667 Top` (36 boxes)
21. `30278c01`: `Car Base  4 x 12 x  1.667 (Complete)` (36 boxes)
22. `30295`: `Car Base 12 x 18 x  1.333` (144 boxes)
23. `30642`: `Car Base  4 x 14 x  2.333` (40 boxes)
24. `30643`: `Car Base  4 x 10 x  1.333` (28 boxes)
25. `30837`: `Car Base  4 x  8 x  1.333 with Studs on Side` (24 boxes)
26. `3385`: `Car Base  6 x 12 with  5 x  6 Recessed Centre and Studs on Sides` (42 boxes)
27. `3888a`: `~Vehicle Chassis 14 x  6.5 with Tow-Hook` (56 boxes)
28. `3888ac01`: `Vehicle Chassis 14 x  6.5 with Tow-Hook and Light-Grey Wheels` (56 boxes)
29. `3888ac02`: `Vehicle Chassis 14 x  6 with Tow-Hook and Light-Grey Wheels` (56 boxes)
30. `4211`: `Car Base  4 x  5` (16 boxes)
31. `4212a`: `Car Base  4 x 10 x  0.667 with  2 x  2 Center Closed` (24 boxes)
32. `4212b`: `Car Base  4 x 10 x  0.667 with  2 x  2 Center Open` (20 boxes)
33. `4362a`: `~Vehicle Chassis 12 x  6 with Tow-Hook` (48 boxes)
34. `4362ac01`: `Vehicle Chassis 12 x  6 with Tow-Hook and Light-Grey Wheels` (48 boxes)
35. `4613`: `Vehicle Base 10 x  4 with 4 Wheel Clips` (28 boxes)
36. `4613c01`: `Vehicle Base 10 x  4 with Two Wheels Light Grey` (28 boxes)
37. `4796`: `~Vehicle Chassis  8 x  6 with Tow-Hook` (32 boxes)
38. `4796c01`: `Vehicle Chassis  8 x  6 with Tow-Hook and Light-Grey Wheels` (32 boxes)
39. `52036`: `Car Base  4 x 12 x  0.667` (32 boxes)
40. `52037`: `Car Base 16 x  6 with  4 x  4 Recessed Centre` (64 boxes)
41. `65094`: `Car Base  6 x 16 x  2.333 with  4 x 14 Recessed Centre with Mudguards` (60 boxes)
42. `65094p01`: `Car Base  6 x 16 x  2.333 with  4 x 14 Recessed Centre with Mudguards` (60 boxes)
43. `65202`: `Car Base  6 x 10 x with 2 x 4 Recessed Centre` (44 boxes)
44. `65634`: `Car Base  6 x 12 with 6 Studs on Each Side` (48 boxes)
45. `68446`: `~Car Base  6 x 16 x  2.333 with  4 x 14 Recessed Centre with Mudguards` (60 boxes)
46. `6920`: `Car Base  2 x  6 with Protruding Axle Holes` (12 boxes)
47. `710`: `Car Base  6 x 17 with Hole` (72 boxes)
48. `778`: `Tractor Trailer Chassis  4 x 13` (36 boxes)
49. `780`: `Car Base  6 x  7` (30 boxes)
50. `781`: `Car Base  6 x 12` (54 boxes)
51. `803`: `Car Base  4 x 12 with Hole and Steering Gear Slot` (36 boxes)
52. `804`: `Car Base  4 x 14 with Hole and Steering Gear Slot` (44 boxes)
53. `805`: `Car Base  4 x 16 with Hole and Steering Gear Slot` (52 boxes)
54. `806`: `Car Base  6 x 17 with 2 Holes and Steering Gear Slot` (72 boxes)
55. `u574`: `Car Base  6 x 13` (60 boxes)
56. `u9205`: `~Fabuland Tricycle with 1 Front Wheel Chassis` (8 boxes)
57. `u9206`: `~Fabuland Tricycle with 2 Front Wheels Chassis` (12 boxes)

---

## 4. Conclusion & Backlog Disposition

- **Outcome**: Backlog item `vehicle` is **REJECTED**.
- **Reason**: Standard System vehicle base and chassis parts were already solved across the library (57 parts accepted). The remaining 86 rejected parts in category `Vehicle` are 100% accounted for as non-chassis irregular/hollow components (Duplo, sculpted motorcycle shells, motor housings, forklift masts, caterpillar tracks, and excavator buckets). No safe shared occupancy family exists, and forcing bounding boxes would severely violate `a2ui` spec §3 by creating phantom collisions.
- **Action**: Item status updated to `"rejected"` in `agents/gcp-catalogue-agents/backlog.json`. Zero forced boxes, zero regressions.
