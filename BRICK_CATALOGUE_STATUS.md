# Brick Catalogue Status

## 2026-09-27: TYRE_PARTS Occupancy Family

- **Task**: Add real occupancy support for rotationally symmetric Tyre parts (`scripts/ldraw/parts.py`).
- **Implementation**:
  - Added `TYRE_PARTS` family and `tyre_occupancy(bounds_min, bounds_max)` function in `scripts/ldraw/parts.py`.
  - Tyres in LDraw are modeled rotationally symmetric about the Z axis (wheel axle) with their circular cross-section in the XY plane, centered at `(0, 0)`.
  - Like `ROUND_PARTS` and `DISH_PARTS`, occupancy is computed as an axis-aligned square inscribed in that outer circular cross-section (`half_inscribed = diameter / (2 * sqrt(2))`), spanning the part's real Z bounds (`[z_min, z_max]`).
  - By inscribed-circle geometry, any point within the square has radius $r \le \text{diameter} / 2$, provably containing the collision box entirely within the physical tyre cylinder envelope without falsely flagging collisions in surrounding empty air (spec §3's under-approximation guarantee).
  - Tyres have no studs, pegholes, or pins (`studs == []`, `holes == []`, `pins == []`), so sockets are explicitly empty (`sockets = []`).
  - Added deterministic constants derived from real resolved geometry for all 92 clean, undeformed, rotationally-symmetric tyre parts.
  - Excluded 2 unfinished / deformed parts (`2807` marked "Needs Work" and `6578c01` marked "Deformed to 10/ 67 x 24") which remain `needs_occupancy=True`.
- **Catalogue Impact**:
  - Rejects survey (`scripts/ldraw/survey_rejects.py`) showed 94 total Tyre-category parts rejected prior to change.
  - Post-implementation survey unlocks **92 real tyre parts** (`Tyre` reject count dropped from 94 to 2).
- **Verification**:
  - Added targeted test cases in `tests/test_generic_stud_occupancy.py` (pure math tests, dispatcher tests, and real resolved geometry tests for a representative sample of 10 tyre parts plus rejection tests for excluded parts). All 28 tests pass.
