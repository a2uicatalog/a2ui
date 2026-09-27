# Brick Catalogue Status

## 2026-09-27: Hinge Occupancy & Feasibility Investigation
- Completed scoping investigation for LEGO hinge representation and occupancy: see [scripts/ldraw/HINGE_INVESTIGATION.md](scripts/ldraw/HINGE_INVESTIGATION.md).
- **Key finding**: True hinges do NOT require a pose parameter or a dynamic multi-body occupancy model. In both physical LEGO and LDraw, hinges are two separate static parts (e.g. `2429`/`2430`, `4275b`/`4276b`, `3937`/`3938`). Most hinge halves are already baked with valid static occupancy and do not collide when mated at orthogonal angles. The only missing capability is connector recognition (`hinges` axis pairing) in `brick_parts_validate.py`.
