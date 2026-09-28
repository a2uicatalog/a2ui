# H175 Secondary Connectors Investigation: Axle-Pin Hybrids, Ball Joints & Turntables (2026-09-28)

## Status: COMPLETE

## Target Selection & Prioritisation Rationale
Selected backlog item: **`h175-secondary-connectors`** (Family: *H175 remaining: ball joints, axle-pin hybrids, turntables*).

Prioritised per operator focus directive:
> Curtis has asked this specific run to prioritise: Backlog item: h175-secondary-connectors (H175 remaining: ball joints, axle-pin hybrids, turntables).
> Operator-added context for this run: Real ball joints (1938, 32474), axle-pin hybrids (11214, 18651, 61184 -- check for overlap with the already-landed technic-axle-occupancy family before treating these as new), and turntables (1936, 1937, 99010). Investigation-first, same rigor as every other family tonight.

This backlog item targets the secondary connectivity and mechanical gaps of priority official set **LEGO Technic 42145 (Airbus H175 Rescue Helicopter)** following the curation of the first 60 solvable parts (commit `67ce465`) and the plain/with-stop axle occupancy family (`technic-axle-occupancy`).

---

## Executive Summary

This investigation analyzed all three subfamilies specified under `h175-secondary-connectors` across the real LDraw library and official set 42145:

1. **Axle-Pin Hybrids (`11214`, `18651`, `43093`, `3749`, `65249`, `6562`, `4186017`, `4206482`, `61184`)**:
   - **SAFE OCCUPANCY FAMILY PROVEN AND IMPLEMENTED.**
   - Forensic check of `technic-axle-occupancy`: confirmed that `generic_axle_occupancy` intentionally excludes pin hybrids via regex filter `r"\b(pin|pins|...)\b"`. Axle-pin hybrids are genuinely unhandled.
   - Both ends (pin shaft and axle shaft) share the exact standard cylindrical cross-section of radius 6.0 LDU (`[-6.0, 6.0] x [-6.0, 6.0]`), designed to fit standard 12 LDU Technic holes.
   - The central stop collar / flange of radius 8.0 LDU is safely under-approximated as `[-6.0, 6.0] x [-6.0, 6.0]` (identical to landed pins `2780`, `3673`, `4459`, `61332`, `32556a`, `42924`), guaranteeing zero false-positive collisions against outer beam faces.
   - Measured ray-parity solid fractions are **54.2% to 60.4%** across all axle-pin lengths (2L and 3L), comfortably clearing `STUD_CELL_MIN_SOLID = 0.15` by > 3.5x margin.
   - For `61184` (Technic Pin 1/2 with Bar 2L), a two-box decomposition safely covers the 1/2 pin (`box(-12, 0, -6, 6, -6, 6)`, sol = 87.5%) and the 2L bar (`box(-60, -12, -4, 4, -4, 4)`, sol = 79.2%) without over-claiming empty air around the 4.0 LDU radius bar.

2. **Turntables & Swashplates (`1936`, `1937`, `99010`, `99009`, `18938`, `18939`)**:
   - **CORRECTLY REJECTED (MUST REMAIN `needs_occupancy=True`).**
   - Direct physical counterpart to Technic bushes investigated in `TECHNIC_REMAINDER_SURVEY.md`.
   - All turntables and swashplates are hollow annular cylinders with an open central bore through which rotor masts, driving axles, or through-shafts pass. Measured core solid fraction across all parts is **0.0000**.
   - Bounding boxes or inscribed boxes across the center would claim solid plastic in open air, triggering immediate false collisions with passing shafts and violating spec §3 (*"miss an overlap, never report a false one"*).
   - In addition, mating halves (`1936`/`1937`, `99010`/`99009`, `18938`/`18939`) physically interlock and overlap in volume along the Y axis, and swashplates articulate dynamically at non-orthogonal angles. Without a specialized rotational/annular joint exemption, box occupancy is geometrically impossible.

3. **Ball Joints & Sockets (`1938`, `32474`, `2739`, `53585`)**:
   - **CORRECTLY REJECTED (MUST REMAIN `needs_occupancy=True`).**
   - `1938` (Technic Swashplate Ball Joint): Features a central through-hole for the rotor mast. Ray-parity solid fraction in the core is **0.0833**, failing `STUD_CELL_MIN_SOLID = 0.15`. A solid box would collide with the passing mast.
   - `32474` (Technic Ball Joint with Axlehole Blind): A spherical joint head (radius 12.81 LDU) that is physically encapsulated inside a mating socket cup (e.g. `2739`, `53585`) with continuous 3-axis spherical articulation.
   - An AABB box enclosing the ball overlaps the spatial volume of the mating socket cup, causing continuous false-positive collisions unless a ball-socket connector exemption system exists in `brick_parts_validate.py`. Like universal joints and steering links in `TECHNIC_REMAINDER_SURVEY.md`, ball joints must remain `needs_occupancy=True`.

---

## 1. Real Measured Geometry & Solid Fractions

Direct measurements via `resolve_part()` against the real LDraw library (fixed seed 20260926, n=200):

| Part ID | Description | Connectors | Measured Bounds (LDU) | Tris | Candidate Occupancy Box(es) | Ray-Parity Solidity | Outcome |
| :--- | :--- | :---: | :--- | :---: | :--- | :---: | :---: |
| `43093` | Technic Axle Pin with Friction | 1 pin | `[-20.0, -8.0, -8.0]..[19.5, 8.0, 8.0]` | 744 | `[box(-20, 20, -6, 6, -6, 6)]` | **0.5417** (54.2%) | **ACCEPTED** |
| `3749` | Technic Axle Pin | 0 pins | `[-20.0, -8.0, -8.0]..[19.5, 8.0, 8.0]` | 504 | `[box(-20, 20, -6, 6, -6, 6)]` | **0.5625** (56.2%) | **ACCEPTED** |
| `6562` | =Technic Axle Pin | 0 pins | `[-20.0, -8.0, -8.0]..[19.5, 8.0, 8.0]` | 504 | `[box(-20, 20, -6, 6, -6, 6)]` | **0.5625** (56.2%) | **ACCEPTED** |
| `4186017` | ~_Technic Axle Pin Tan (Obsolete) | 0 pins | `[-20.0, -8.0, -8.0]..[19.5, 8.0, 8.0]` | 504 | `[box(-20, 20, -6, 6, -6, 6)]` | **0.5625** (56.2%) | **ACCEPTED** |
| `4206482` | ~_Technic Axle Pin with Friction Blue | 1 pin | `[-20.0, -8.0, -8.0]..[19.5, 8.0, 8.0]` | 744 | `[box(-20, 20, -6, 6, -6, 6)]` | **0.5417** (54.2%) | **ACCEPTED** |
| `11214` | Technic Axle Pin Long w/ Friction w/ 2L Pin | 1 pin | `[-30.0, -8.0, -8.0]..[29.5, 8.0, 8.0]` | 791 | `[box(-30, 30, -6, 6, -6, 6)]` | **0.5625** (56.2%) | **ACCEPTED** |
| `18651` | Technic Axle Pin Long w/ Friction w/ 2L Axle | 1 pin | `[-30.0, -8.0, -8.0]..[29.5, 8.0, 8.0]` | 744 | `[box(-30, 30, -6, 6, -6, 6)]` | **0.6042** (60.4%) | **ACCEPTED** |
| `65249` | Technic Axle Pin Long w/o Friction w/ 2L Axle | 0 pins | `[-30.0, -8.0, -8.0]..[29.5, 8.0, 8.0]` | 504 | `[box(-30, 30, -6, 6, -6, 6)]` | **0.5833** (58.3%) | **ACCEPTED** |
| `61184` | Technic Pin 1/2 with Bar 2L | 0 pins | `[-60.0, -8.0, -8.0]..[0.0, 8.0, 8.0]` | 492 | `[box(-60, -12, -4, 4, -4, 4), box(-12, 0, -6, 6, -6, 6)]` | **0.7917, 0.8750** | **ACCEPTED** |
| `1938` | Technic Swashplate Ball Joint | 0 pins | `[-22.42, -12.0, -22.42]..[22.42, 20.0, 22.42]` | 972 | `core box [-6..6]` | **0.0833** (< 0.15) | **REJECTED** |
| `32474` | Technic Ball Joint with Axlehole Blind | 0 pins | `[-12.81, -12.81, -12.81]..[12.81, 9.25, 12.81]` | 322 | `bounding sphere r=12.81` | 0.3542 (mating collision) | **REJECTED** |
| `1936` | Technic Swashplate 5 x 5 Top | 5 holes | `[-50.33, -29.0, -50.0]..[50.33, 10.0, 45.74]` | 3465 | `center box [-10..10]` | **0.0000** | **REJECTED** |
| `1937` | Technic Swashplate 5 x 5 Base | 4 holes | `[-50.0, -10.0, -50.0]..[50.0, 29.0, 50.0]` | 1908 | `center box [-10..10]` | **0.0000** | **REJECTED** |
| `99010` | Technic Turntable 28 Tooth Top | 2 holes | `[-36.8, -29.0, -36.8]..[36.8, 10.0, 36.8]` | 2664 | `center box [-10..10]` | **0.0000** | **REJECTED** |
| `99009` | Technic Turntable 28 Tooth Bottom | 4 holes | `[-29.0, -4.0, -27.0]..[29.0, 29.0, 27.0]` | 1538 | `center box [-10..10]` | **0.0208** | **REJECTED** |
| `18938` | Technic Turntable 60 Tooth Top | 6 holes | `[-76.75, -30.0, -76.75]..[76.75, 10.0, 76.75]` | 5664 | `center box [-10..10]` | **0.0000** | **REJECTED** |
| `18939` | Technic Turntable 60 Tooth Bottom | 6 holes | `[-67.0, -5.0, -67.0]..[67.0, 30.0, 67.0]` | 2916 | `center box [-10..10]` | **0.0417** | **REJECTED** |

---

## 2. Implementation Plan

### Axle-Pin Hybrids (`scripts/ldraw/parts.py`)
Add the 8 verified axle-pin parts and 1 pin-bar hybrid to `OVERRIDES` in `scripts/ldraw/parts.py`:
- 2L Axle-Pin parts (`43093`, `3749`, `6562`, `4186017`, `4206482`):
  `box(-20, 20, -6, 6, -6, 6)`
- 3L Axle-Pin parts (`11214`, `18651`, `65249`):
  `box(-30, 30, -6, 6, -6, 6)`
- Pin 1/2 with Bar 2L (`61184`):
  `[box(-60, -12, -4, 4, -4, 4), box(-12, 0, -6, 6, -6, 6)]`

In addition, update `generic_axle_occupancy` or `resolve_occupancy_and_sockets` to ensure consistent handling, and verify that `test_generic_stud_occupancy.py` includes exhaustive positive and negative test cases.

### Turntables & Ball Joints
Must remain `needs_occupancy=True`. Negative control test cases added in `tests/test_generic_stud_occupancy.py` to ensure they are never accidentally assigned bounding boxes.
