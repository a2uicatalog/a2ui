# Minifig Accessory Category Investigation (2026-09-28)

## Status: COMPLETE (Verdict: REJECTED for Category-Wide Box Occupancy; Bar Grip Hypothesis CONFIRMED)

## Executive Summary
This investigation analyzed all 820 parts in the LDraw Parts Library carrying the `!CATEGORY Minifig Accessory` declaration to evaluate whether a shared geometric occupancy family, generic rule, or safe set of `OVERRIDES` exists.

The investigation was specifically launched with an operator steer prioritizing the **minifig-accessory** backlog item, with the guiding hypothesis that many sword, blade, and tool shapes might already resolve cleanly via the existing `bar_grip_points()` mechanism (rod connector detection).

### Key Findings & Verdict
1. **Operator Hypothesis CONFIRMED (High-Value Existing Coverage)**:
   - Exactly **361 Minifig Accessory parts** (44.0% of the entire 820-part category) ALREADY resolve cleanly with `needs_occupancy: false` via the existing `bar_grip_points()` connector detection in `scripts/ldraw/parts.py` (lines 890–930).
   - Together with 99 parts accepted via `generic_stud_cell_occupancy()` and 9 parts accepted via `minifig_headwear_socket()`, a total of **417 parts (50.9%)** of the category are already accepted without requiring any new code.
   - Real operator-cited examples confirmed passing today:
     - `10050` (Minifig Sword Uruk-Hai): 1 bar grip, `needs_occupancy: false`
     - `11439` (Minifig Sword with Jagged Edges) and 4 printed variants (`11439p01`–`p04`): 1 bar grip, `needs_occupancy: false`
     - `12885` (Minifig Paint Roller Brush Handle): 2 bar grips, `needs_occupancy: false`
     - `11640` (Minifig Electric Guitar Classic) and printed variants (`11640p01`, `p02`): 1 bar grip, `needs_occupancy: false`
     - `11103` (Minifig Sword Double Blade with Bar Holder): 1 bar grip, `needs_occupancy: false`
     - `11250` (Minifig Tool Gavel): 1 bar grip, `needs_occupancy: false`
     - `13571` (Minifig Tomahawk): 1 bar grip, `needs_occupancy: false`
     - `15391` (Minifig Gun Shooting Blaster): 1 bar grip, `needs_occupancy: false`
     - Plus 40 shields, 28 tools, 20 guns/blasters, 8 axes, 8 spears/staffs, and 6 lightsabers.

2. **Category-Wide Occupancy Rule Strictly REJECTED**:
   - The remaining **403 parts** (49.1% of the category; 260 in the uncurated candidate pool) are extremely heterogeneous and **CANNOT be safely assigned an axis-aligned box occupancy family**.
   - Under `a2ui` core specification section 3:
     > *"Occupancy is deliberately under-approximated (spec section 3: under-approximation is always safe): miss a real collision on the dropped area, never report a false one."*
   - Fabricating bounding boxes across these 403 parts would violate this foundational invariant by claiming massive volumes of empty air (solid fractions commonly range from 7% to 25%), creating persistent false collision errors in models where minifigures hold accessories.

---

## 1. Real Measured Catalogue Statistics

Survey conducted against the complete LDraw parts library (via `resolve.py` and `parts.py`):

| Scope | Count | Status | Notes |
| :--- | :---: | :---: | :--- |
| **Total LDraw Library Minifig Accessories** | **820** | 100.0% | Explicit `0 !CATEGORY Minifig Accessory` |
| **Accepted by existing code** | **417** | **50.9%** | `needs_occupancy: false` |
| - *via `bar_grip_points()`* | *361* | *44.0%* | Rod grips extending to part extremity |
| - *via `generic_stud_cell_occupancy()`* | *99* | *12.1%* | Parts with genuine flush stud grids |
| - *via `minifig_headwear_socket()`* | *9* | *1.1%* | Feathers, plumes, visors |
| - *(overlap between rules)* | *52* | - | Both stud and bar grip detected |
| **Rejected by existing code** | **403** | **49.1%** | `needs_occupancy: true` |
| - *Uncurated candidates (`survey_rejects.py`)* | *260* | - | Excluding printed variants & curated set |

---

## 2. Forensic Analysis of Rejected Sub-Families

The 403 rejected parts were classified into discrete sub-families to determine why existing rules reject them and whether any sub-family could support a safe occupancy representation:

### Sub-Family A: Shields (55 rejected parts)
- **Representative parts**: `10049` (Broad Shield), `18836` (Triangular Shield), `10520` (Round Bowed Shield), `2586` (Ovoid Shield).
- **Physical Shape**: Thin curved shells of molded plastic (wall thickness $\approx 1.5–2.0$ LDU) spanning 40 to 60 LDU in height and width.
- **Measured Geometry**:
  - `18836`: Bounds `[-20.0, -30.0, -12.0]` to `[20.0, 30.0, 4.0]`. Bounding box volume = 38,400 LDU³. Measured ray-parity solid fraction = **0.1950** (80.5% open air).
  - `10049`: Bounds `[-20.0, -31.0, -11.0]` to `[20.0, 35.0, 8.0]`. Bounding box volume = 50,160 LDU³. Measured ray-parity solid fraction = **0.1000** (90.0% open air).
  - `10520`: Bounds `[-24.0, -24.0, -9.2]` to `[24.0, 24.0, 8.0]`. Bounding box volume = 39,629 LDU³. Measured ray-parity solid fraction = **0.1500** (85.0% open air).
- **Handle Placement**: The bar handle is located on the concave back surface, centered at $X \in [-7.5, 7.5]$, $Y=0, Z=0$ or $4$. The part extents in X are $[-20, 20]$ or $[-24, 24]$.
- **Why It Fails**:
  1. The handle is recessed in the concave interior of the shield; neither cylinder end is within `BAR_EXTREMITY_TOL = 3.0` LDU of the part bounds, so `bar_grip_points()` correctly rejects it to avoid false positive triggers.
  2. If an axis-aligned box were defined for the shield, the box would encompass the space behind the shield where the minifigure's hand, forearm, and torso sit. This would generate severe false collisions between the shield and the minifig holding it.

### Sub-Family B: Sculpted Weapons & Handheld Tools (34 weapons + 33 tools)
- **Representative parts**: `2530` (Cutlass), `18031` (Longsword), `10053` (Curved Sword), `11601` (Spiked Blade), `2542` (Oar), `18920` (Scissors), `21700` (Sonic Screwdriver).
- **Physical Shape**: Intricate sculpted objects with thin blades, crossguards, pommels, or sculpted tool heads.
- **Measured Geometry**:
  - `2530` (Cutlass): Bounds `[-6.0, -62.0, -12.0]` to `[6.0, 14.0, 8.0]`. The handle cylinder has length 12.0 LDU from $Y=-6.0$ to $Y=6.0$. A curved pommel knob extends 8 LDU further to $Y=14.0$, and the blade/hilt extends to $Y=-62.0$. Bounding box solid fraction = **0.1450** (85.5% open air).
  - `18031` (Longsword): Bounds `[-6.0, -73.5, -15.0]` to `[6.0, 22.0, 15.0]`. Handle cylinder length 16.0 LDU ($Y=0$ to $16$). The pommel extends to $Y=22.0$, and the blade/crossguard extends to $Y=-73.5$. Bounding box solid fraction = **0.1100** (89.0% open air).
  - `10053` (Curved Sword): Bounds `[-4.5, -54.8, -9.8]` to `[4.5, 14.2, 9.8]`. Handle length 18.5 LDU ($Y=-7.4$ to $11.1$). Pommel extends to $Y=14.16$.
  - `2542` (Oar): Bounds `[-10.0, -4.0, -4.0]` to `[10.0, 140.0, 4.0]`. Handle cylinder length 80.0 LDU ($Y=0$ to $80$). The grip knob extends to $Y=-4.0$ and the blade extends to $Y=140.0$.
- **Why It Fails**:
  1. Neither end of the handle cylinder is at the extreme bound of the part because pommel knobs, end caps, crossguards, or tool heads extend beyond the cylinder.
  2. Relaxing `BAR_EXTREMITY_TOL` is unsafe because doors (`5258`), wheels (`100942`), and hinge knuckles (`3937`) contain radius-4 cylinders embedded inside their bodies.
  3. Bounding box occupancy for a sword or tool would project a giant phantom box around thin blades and handles, colliding with adjacent scenery or figures.

### Sub-Family C: Cups, Goblets, Trophies & Tableware (35 parts)
- **Representative parts**: `10172` (Trophy Cup 2.4L), `3899` (Minifig Cup), `2343` (Minifig Goblet).
- **Physical Shape**: Axisymmetric hollow vessels with protruding loop handles.
- **Measured Geometry**:
  - `10172` (Trophy Cup): Bounds `[-24.0, -48.0, -10.0]` to `[24.0, 0.0, 10.0]`. Solid fraction = **0.2400**. The central cup is hollow; the two handles are thin loops at $X=\pm 20.0$.
  - `3899` (Minifig Cup): Bounds `[-10.0, 0.0, -10.0]` to `[10.0, 24.0, 24.0]`. Solid fraction = **0.2100**. Hollow cup body ($Z \in [-10, 10]$) with a thin handle extending to $Z=24.0$.
  - `2343` (Minifig Goblet): Bounds `[-10.0, 0.0, -10.0]` to `[10.0, 40.0, 10.0]`. Stem cylinder length 14.0 LDU ($Y=18$ to $32$). Solid fraction = **0.2350**.
- **Why It Fails**: Hollow drinking vessels cannot be boxed without filling the drinking cavity with phantom plastic, preventing placement of accessories inside cups or goblets.

### Sub-Family D: Sacks, Bags & Body-Worn Accessories (20 parts)
- **Representative parts**: `10169` (Minifig Sack), `61976` (Minifig Satchel).
- **Physical Shape**: Organic sculpted cloth bags and shoulder straps designed to wrap around or hang off a minifigure torso.
- **Measured Geometry**:
  - `61976` (Satchel): Bounds `[-14.0, -3.5, -12.0]` to `[26.2, 57.0, 12.0]`. Measured solid fraction = **0.0700** (93.0% open air!).
  - `10169` (Sack): Bounds `[-18.1, -39.5, -15.8]` to `[23.5, 0.0, 16.3]`. Solid fraction = **0.2750**.
- **Why It Fails**: The satchel strap encloses the minifigure torso and arm; an axis-aligned bounding box would engulf the minifigure itself, triggering constant false collisions.

### Sub-Family E: Musical Instruments (12 parts)
- **Representative parts**: `13808` (Saxophone), `13808p01`.
- **Physical Shape**: Intricate curved hollow tubes wrapping around figure hands.
- **Measured Geometry**:
  - `13808`: Bounds `[-8.7, -51.2, -24.0]` to `[8.7, 14.4, 14.9]`. Solid fraction = **0.1600** (84.0% open air).
- **Why It Fails**: Curved non-planar centerline; no straight axis-aligned cylinder; low solid fraction.

### Sub-Family F: Food Items (19 parts)
- **Representative parts**: `10170` (Pretzel), `33125` (Croissant), `33183` (Carrot Top), `33051` (Apple).
- **Physical Shape**: Sculpted organic foodstuffs with loops, curved tapers, and irregular profiles.
- **Measured Geometry**:
  - `10170` (Pretzel): Bounds `[-19.9, -15.8, -6.0]` to `[19.9, 19.0, 4.0]`. Solid fraction = **0.2550**. Contains large open holes.
  - `33125` (Croissant): Bounds `[-19.6, -18.0, -24.7]` to `[9.7, 0.0, 24.7]`. Solid fraction = **0.3200**. Curved crescent shape.
- **Why It Fails**: Organic geometries with large concavities and non-rectilinear shapes.

### Sub-Family G: Misfiled Creature & Animal Figures (38 parts)
- **Representative parts**: `13665` (Animal Bird Crow), `1613` (Animal Antlers with Pin), `33048c01` (Turkey).
- **Why It Fails**: These are animal figures misfiled under `!CATEGORY Minifig Accessory` in LDraw. They are already covered by `ANIMAL_INVESTIGATION.md`, which established that sculpted creatures cannot safely receive bounding box occupancy.

### Sub-Family H: Stud-Bearing Accessories Failing Containment (51 parts)
- **Representative parts**: `30089a` (Camera), `3962a` (Radio), `64567a` (Lightsaber Hilt), `30340` (Life Ring), `102498` (Wand).
- **Why It Fails**:
  - While these parts contain studs, standard stud cells are $20.0 \times 20.0$ LDU.
  - For `30089a` (Camera): Total height is only 22 LDU ($Y \in [-14, 8]$). A standard 20x20 stud-cell box extends to $Y=10.0$, protruding 2.0 LDU into open air.
  - For `64567a` (Lightsaber Hilt): Outer diameter is 16.0 LDU ($X, Z \in [-8, 8]$). The candidate 20x20 box ($[-10, 10]$) protrudes by 2.0 LDU on all four sides into open air.
  - In each case, `_boxes_within_bounds()` in `parts.py` correctly detects that the stud cell overflows the part's real boundary and discards it. This is a critical safety check preventing false collisions against adjacent bricks.

---

## 3. Conclusions and Recommended Architecture

1. **Category Status**:
   - The backlog item `minifig-accessory` is **REJECTED** as a target for a category-wide occupancy family.
   - 417 parts are already correctly accepted by existing mechanisms.
   - The remaining 403 parts are honestly and safely left as `needs_occupancy: true`.

2. **No Hacky Box Guesses**:
   - Forcing arbitrary bounding boxes on swords, shields, or instruments would introduce false collision errors across all minifigure-holding scenes in the catalogue.
   - Under-approximation (leaving occupancy empty or unboxed) remains the strictly correct, evidence-based stance under spec section 3.

3. **Future Connector Enablers**:
   - The long-term architectural solution for held accessories (swords, shields, utensils) is **connector-based anchoring**:
     - Introducing hand/clip connector recognition (pairing minifig hands `clip` with bar `bars`).
     - Introducing mated-connector collision exemptions for held items (similar to the hinge knuckle exemption added in 2026-09-28).
