# Technic Remainder Occupancy Survey

## 1. Background and Scope

This survey investigates the remaining ~90 Technic parts in the LDraw library that currently yield `needs_occupancy=True`.

Previous work established:
- **Technic Straight Holes**: `3700`, `6541`, `32000`, `3701`, `3894`, `3702`, `3703` covered by `technic_holes_occupancy`.
- **Technic Axle Rods** & **Gears**: Already investigated and landed or settled.
- **Technic Beams (bent liftarms)**: Holes span multiple non-coplanar / multi-axial directions, which correctly fail the single-axis hole channel model (`generic_hole_channel_occupancy` correctly refuses them).

The remaining pool consists of Technic connectors, joints, bushes, cross blocks, pins, links, and mechanical components.

## 2. Research Questions & Focus Areas

1. **Cross Blocks** (`32291`, `32557`, `63869`, `98989`, etc.): Do they share a common cuboid connector body with axle/pin holes at right angles suitable for a mini-family or safe `OVERRIDES`?
2. **Bushes** (`3713`, `57585`, etc.): Are they solid cylindrical/short shapes where inscribed-shape or cylindrical bounding math applies safely?
3. **Simple Connector Pins / Toggles** (`32039`, `32126`, `61184`, `89678`, etc.): Can small, rigid connector parts qualify for hand-verified `OVERRIDES` entries matching existing pin conventions (`2780`, `3673`, `4274`, `6558`, `32054`)?
4. **Irregular / Dynamic / Complex Parts**: Detailed reasons for retaining `needs_occupancy=True` (solidity floors, thin bridges, non-orthogonal geometry, multi-part assemblies).

## 3. Inventory & Measurements

(In progress: running geometric analysis across the full Technic reject set.)
