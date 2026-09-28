# Windscreen Parts Occupancy Investigation

**Date:** 2026-09-28
**Status:** In Progress
**Scope:** Investigation of 15 unresolved Windscreen-category parts (`needs_occupancy=True`) to determine if any viable, safe, provable occupancy family exists, or whether windscreen parts are inherently heterogeneous canopy/dome/glass forms requiring either individual hand-verified overrides or honest exclusion.

---

## 1. Executive Summary

(To be populated with empirical findings)

---

## 2. Background and Part Inventory

The 15 unresolved windscreen parts identified in the OMR / catalogue dataset:

1. `13252` - Windscreen 6 x 13 x 2 (studs=4, bounds `(-60, -18, -250)..(60, 30, 6)`)
2. `17457` - Windscreen 2 x 6 x 2 Vertical Glass (studs=0, bounds `(-58.4, 3.8, -8.4)..(58.4, 40, 30)`)
3. `2418a` - Windscreen 6 x 6 Octagonal Canopy w/o Axlehole (studs=4, bounds `(-60, 0, -60)..(60, 48, 60)`)
4. `2418b` - Windscreen 6 x 6 Octagonal Canopy w/ Axlehole (studs=4, bounds `(-60, 0, -60)..(60, 48, 60)`)
5. `2483` - Windscreen 4 x 4 x 3.667 Helicopter (studs=0, bounds `(-40, -4, -76)..(40, 100, 4)`)
6. `2507` - Windscreen 10 x 4 x 2.333 Canopy (studs=0, bounds `(-40, -4, -196)..(40, 52, 4)`)
7. `2598ps2` - Windscreen 10 x 10 x 4 Octagonal Canopy w/ TIE Adapter (studs=4, bounds `(-100, 0, -100)..(100, 96, 100)`)
8. `30083` - Windscreen 6 x 6 x 3 Dome with Hinge (studs=0, bounds `(-60, -116, -64)..(60, 4, 4)`)
9. `30384` - Windscreen 4 x 7 x 2 Round Pointed (studs=0, bounds `(-40, -48, -46)..(40, 0, 90)`)
10. `4474` - Windscreen 6 x 4 x 2 Canopy (studs=0, bounds `(-40, -4, -116)..(40, 44, 4)`)
(and any additional unresolved windscreen parts in the catalogue)

---

## 3. Investigation Methodology

1. Parse LDraw subfile / triangle geometry and stud positions for each part.
2. Examine octagonal canopy family (`2418a`, `2418b`, `2598ps2`): check base, stud cell alignment, interior hollow cavity, and solid bounding region.
3. Examine hinge/pivot connection in `30083` ("Dome with Hinge").
4. Examine canopies, helicopter glass, and round windscreens (`2483`, `2507`, `4474`, `13252`, `17457`, `30384`).
5. Raycast / cross-section analysis for solid occupancy volume.
6. Honest conclusions on whether a parameterizable family, individual hand overrides, or "no safe under-approximation" is warranted.
