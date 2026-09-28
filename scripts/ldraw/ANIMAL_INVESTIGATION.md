# Animal Part Occupancy Investigation (2026-09-28)

## Status: IN PROGRESS

## Task & Scope
Investigate real Animal-category parts in the catalogue (`needs_occupancy=True`) for any viable occupancy pattern.
Follow the same rigor and honesty standard as `scripts/ldraw/HINGE_INVESTIGATION.md`.
Individually-sculpted creature figures (parrot, bat, snake, frog, owl, rat, cat, horse, fish) are strong priors against a shared geometric family.

## Real Animal-Category Parts Under Investigation
The 19 Animal-category part IDs in the catalogue with `needs_occupancy=True`:
- `15429`: Animal Cat Tail (studs=0)
- `20308`: Animal Head Cuboid (studs=0)
- `24946`: Animal Egg 1.2x1.2x1.333 w/ Hole (studs=0)
- `2546`: Animal Bird Parrot (studs=0)
- `30103`: Animal Bat (studs=0)
- `30115`: Animal Snake (studs=0)
- `33320`: Animal Frog (studs=0)
- `40232`: Animal Owl (studs=0)
- `40234`: Animal Rat (studs=0)
- `4493c01`: Animal Horse (Complete) (studs=2)
- `4493c02`: Animal Horse (Complete w/ Black Eyes/Nose) (studs=2)
- `50687`: Animal Rat Standing (studs=0)
- `6251`: Animal Cat Crouching (studs=0)
- `64648`: Animal Fish Straight (studs=1)
(and remaining Animal-category entries in the catalogue).

## Investigation Questions
1. Solidity fraction of full bounding box:
   Do sculpted animal silhouettes have solidity fractions far below `STUD_CELL_MIN_SOLID = 0.15`?
   If so, a bounding box occupancy under-approximation is physically unsound and dangerous for collision detection.
2. Candidate `24946` (Animal Egg):
   Does this have a genuinely high, solid volume fraction that safely justifies an override or rule?
3. Candidates with studs: `4493c01`/`4493c02` (Horse) and `64648` (Fish):
   How does `generic_stud_cell_occupancy` currently treat these? Do they produce safe occupancy or are they rejected?
