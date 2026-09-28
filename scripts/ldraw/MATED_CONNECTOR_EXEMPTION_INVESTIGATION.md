# Mated-Connector Collision Exemption Generalisation: Architectural Scoping Investigation (2026-09-28)

## Status: COMPLETE (Scoping Investigation & Architecture Specification)

---

## Executive Summary

This investigation scopes the generalisation of the mated-connector collision exemption mechanism in `renderers/brick_parts_validate.py` and its browser twin `apps-script-surface/gas-wired-renderer/atoms_brick.gs`. It directly addresses the architectural recommendation originating from `TECHNIC_PANEL_INVESTIGATION.md` and fulfills the backlog item `mated-connector-exemption-generalisation`.

### 1. The Core Problem
In the `a2ui` brick architecture, the foundational geometric safety invariant is defined by spec section 3:
> *"Occupancy is deliberately under-approximated: miss a real collision on the dropped area, never report a false one."*

Under this rule, reporting false-positive collisions between parts that are validly assembled is fatal. However, physical LEGO parts frequently connect by **interpenetrating** or **interleaving** at their interfaces:
- Standard bricks avoid collision because studs ($y \in [-4, 0]$ LDU) are deliberately excluded from brick occupancy boxes ($y \in [0, 24]$ LDU), meaning stacked bricks meet at a 2D boundary face ($y = 0$) with 0.0 LDU interior penetration.
- Non-brick mechanical connectors (Technic pins in pegholes, hinge knuckles along pivot axes, axles through liftarms and bushes, clips gripping bars, towballs inside socket cups, and Technic fairing panels mounted via perimeter pin flanges) physically share 3D space.
- Without an exemption mechanism, any realistic occupancy bounding box covering these connection features triggers false-positive collision reports (`_boxes_overlap() == True`).

### 2. Status Quo Assessment (Built 2026-09-28)
The initial implementation landed on 2026-09-28 (commit `6a976c1`) introduced a coarse whole-pair exemption:
- Evaluates `pin_conn` (pins mating into paired peghole segments within distance $< 0.5$ LDU).
- Evaluates `hinge_conn` (knuckle and finger pairs aligned along a shared axis within distance $< 0.5$ LDU via curated `HINGE_CONNECTORS`).
- If any pin/hole or hinge connector mates between Part $i$ and Part $j$, the pair $(i, j)$ is added to `mated_pairs`.
- In the collision loop: `if (a_i, b_i) in mated_pairs: continue` skips the entire collision check between $i$ and $j$.

### 3. Key Findings & Structural Deficiencies
1. **The Whole-Pair Blind Spot (False Negatives)**:
   Exempting the entire pair $(i, j)$ is safe for small parts (e.g. an isolated 2L pin in a beam), but creates a severe blind spot for large structural parts. If a 1x16 Technic Beam ($i$) and another 1x16 Technic Beam ($j$) are pinned at hole 1, and beam $j$ is rotated so that hole 16 physically smashes straight through beam $i$ at 90°, the validator reports **zero collisions** because $(i, j) \in \text{mated\_pairs}$.
2. **The Indirect Joint Blindness (Blocking Technic Panels)**:
   In real Technic assemblies, structural fairings and panels (`11946`, `11947`, `64782`, `24116`) connect to beams not directly, but via an intermediary pin $P$. Part $A$ mates with $P$, and Part $B$ mates with $P$. While $(A, P)$ and $(B, P)$ are exempted, the pair $(A, B)$ is **not** exempted. At the contact flange where the panel rests flush against the beam, microscopic numerical overlap ($> 0.5$ LDU) triggers an illegitimate collision between Panel $A$ and Beam $B$. This was the exact blocker identified by `TECHNIC_PANEL_INVESTIGATION.md`.
3. **Missing Connector Families (Trapping Bushes, Axles, Clips, and Towballs)**:
   Currently, only `pins`/`holes` and `hinges` participate in `mated_pairs`.
   - **Axles**: Plain axles register zero connectors. Axle-through-hole connections are unrecognized. This forced `TECHNIC_GEAR_PARTS` ($B = 6.0$ LDU) and `WHEEL_PARTS` ($B = 8.0$ LDU) to hollow out their centers with artificial central bore voids, and leaves bushes (`3713`, `4265c`) and cross-blocks (`32291`) trapped at `needs_occupancy=True`.
   - **Clips & Bars**: `bars` are baked, but clips have zero recognition and zero exemption. Clipping a bar into a clip reports a collision if modeled.
   - **Towballs & Sockets**: Towball socket cups must be omitted from occupancy to avoid false collisions.
4. **Real Catalogue & Library Impact**:
   - A full census of the 24,735-part LDraw library shows **979+ parts** across connector-dependent families (141 Technic panels, 14 bushes, 20 cross-blocks, 74 axles, 189 clips, 272 bars, 301 hinges, 81 ball joints).
   - In the priority set LEGO Technic 42145 "Airbus H175 Rescue Helicopter" (2,001 parts), over **150 axles**, **35 Technic panels**, and **80 bushes** cannot be validated without this generalisation.

---

## 1. Forensic Analysis of the Status Quo Collision Exemption

### The Current Implementation (`renderers/brick_parts_validate.py`)
```python
    mated_pairs = set()
    for i in range(n):
        for p in pins[i]:
            for j in range(n):
                if i == j:
                    continue
                for seg in hole_segs_world[j]:
                    half = _add3(p['pos'], tuple(d * 20 for d in p['dir']))
                    mid = _add3(p['pos'], tuple(d * 10 for d in p['dir']))
                    d1, _ = _point_line_dist(p['pos'], seg['a'], seg['b'])
                    d2, _ = _point_line_dist(half, seg['a'], seg['b'])
                    _, tm = _point_line_dist(mid, seg['a'], seg['b'])
                    if d1 < 0.5 and d2 < 0.5 and -0.02 <= tm <= 1.02:
                        pin_conn += 1
                        adj[i].add(j)
                        adj[j].add(i)
                        mated_pairs.add((min(i, j), max(i, j)))

    hinge_conn = 0
    for i in range(n):
        for ha in hinges[i]:
            for j in range(i + 1, n):
                for hb in hinges[j]:
                    if not _hinge_kinds_mate(ha['kind'], hb['kind']):
                        continue
                    if abs(_dot3(ha['dir'], hb['dir'])) <= 0.99:
                        continue
                    hb_end = _add3(hb['pos'], hb['dir'])
                    dist, _ = _point_line_dist(ha['pos'], hb['pos'], hb_end)
                    if dist < 0.5:
                        hinge_conn += 1
                        adj[i].add(j)
                        adj[j].add(i)
                        mated_pairs.add((i, j))

    # Collision loop:
    for a_i, b_i in sorted(pairs):
        if (a_i, b_i) in mated_pairs:
            continue
        if any(_boxes_overlap(a, b) for a in boxes[a_i] for b in boxes[b_i]):
            collisions.append([a_i, b_i])
```

### Critical Analysis

| Property | Current Status | Architectural Consequence |
| :--- | :--- | :--- |
| **Exemption Granularity** | Coarse Whole-Pair (`(i, j)`) | If two parts mate at one point, all collisions anywhere between them are masked. |
| **Connector Scope** | `pin/hole` and `hinge` only | Axles, bushes, clips, bars, towballs, and character anatomical joints have no exemption. |
| **Graph Relationship** | Direct 1-hop mating only | Cannot handle indirect 2-hop joints (e.g. Panel $A$ joined to Beam $B$ via Pin $C$). |
| **Performance Complexity** | Naive $O(N^2 \cdot P \cdot H)$ all-pairs loop | Scales poorly for large assemblies ($N > 500$); stud matching already uses spatial hashing. |
| **Apps Script Twin** | Identical logic in `atoms_brick.gs` | Twin maintenance required; any algorithmic divergence immediately breaks parity tests. |

---

## 2. Real Geometry Measurements & Failure Cases

To ground this investigation in empirical facts rather than conjecture, exact measurements were collected using `resolve_part()` against the real LDraw library (`/opt/a2ui-bootstrap/_ldraw_cache/ldraw`).

### 2.1 Finger Plate Hinges (`4275b` and `4276b`)
- `4275b` (Plate 1x2 with 3 Fingers) and `4276b` (Plate 1x2 with 2 Fingers) both have two occupancy boxes:
  - Box 0: `[0.0, 20.0, 0.0, 8.0, -10.0, 10.0]`
  - Box 1: `[-20.0, 0.0, 0.0, 8.0, -10.0, 10.0]`
- **Measured Overlap Without Exemption**:
  - Box 0 of `4275b` vs Box 0 of `4276b`: `ox = 20.0, oy = 8.0, oz = 20.0` $\implies$ **Direct Collision**.
  - Box 1 of `4275b` vs Box 1 of `4276b`: `ox = 20.0, oy = 8.0, oz = 20.0` $\implies$ **Direct Collision**.
- **Conclusion**: Finger plate hinges physically overlap across their entire knuckle volume ($20 \times 8 \times 20$ LDU). Without mated-pair exemption, **100% of finger hinge assemblies fail validation**.

### 2.2 Technic Bush (`3713`) on Technic Axle (`3705`)
- `3713` (Technic Bush with Two Flanges):
  - Bounds: $[-9.0, -9.0, -10.0]$ to $[9.0, 9.0, 10.0]$. Total volume = $18 \times 18 \times 20 = 6,480$ LDU³.
  - Outer cylinder radius $R = 9.0$ LDU. Axle bore through center: cross-hole with envelope $[-6.0, 6.0] \times [-6.0, 6.0]$.
  - Wall thickness = $9.0 - 6.0 = 3.0$ LDU.
- `3705` (Technic Axle 4):
  - Bounding cross-section: $[-6.0, 6.0] \times [-6.0, 6.0]$.
- **The Dilemma**:
  - If `3713` is given an outer bounding box $[-9, 9] \times [-9, 9] \times [-10, 10]$, its overlap with the axle is $12.0 \times 12.0 \times 20.0$ LDU, triggering a **false-positive collision**.
  - If `3713` is decomposed into 4 wall boxes (like `gear_occupancy`), each wall is only 3 LDU thick ($[-9, -6]$, $[6, 9]$). Because the outer profile is a rounded cylinder ($r=9$), the corners of a $3 \times 18$ box protrude into open air ($9\sqrt{2} \approx 12.7 > 9.0$), failing spec §3 containment, while the inner face touches the axle with 0 margin.
  - Hence, `3713` was correctly kept as `needs_occupancy=True`.
- **Conclusion**: A Technic bush CANNOT have occupancy without an axle/hole mated-connector exemption.

### 2.3 Technic Cross Block (`32291`)
- `32291` (Technic Cross Block 2x2 Axle/Twin Pin):
  - Bounds: $[-19.0, -9.0, -10.0]$ to $[19.0, 29.0, 10.0]$.
  - Features 2 pegholes along Z at $y=20$, and 1 orthogonal axle hole along X at $y=0$.
- **The Dilemma**:
  - Open channels must be maintained along both X (for axle) and Z (for pins).
  - The orthogonal intersection of a 12 LDU X-channel and two 12 LDU Z-channels leaves only thin 3 LDU corner lobes. Ray-parity solid fraction across the remaining lobes drops to $0.062 < 0.15$.
- **Conclusion**: Multi-axial connectors cannot be boxed without axle and pin exemptions.

### 2.4 Technic Panels (`64782` and `11946`)
- `64782` (Technic Panel 5x11):
  - Bounds: $[-110.0, -10.0, -50.0]$ to $[110.0, 10.0, 50.0]$ ($11 \times 1 \times 5$ studs).
  - Ray-parity solidity: **0.2833** (28.3% solid, well above the 0.15 threshold).
  - Hole count: **32 pegholes** running in 3 orthogonal directions (along X, Y, and Z).
- `11946` (Technic Panel Fairing Smooth #21):
  - Bounds: $[-9.0, -29.69, -10.0]$ to $[9.0, 10.0, 86.0]$.
  - Ray-parity solidity: **0.2433** (24.3% solid).
  - Hole count: 2 mounting pinholes on curved edge flanges.
- **Why Technic Panels Remain Unbaked (0 baked across entire catalogue)**:
  - When pins are inserted into any of the 32 holes of `64782`, or the 2 flange holes of `11946`, any occupancy box representing the panel's solid plate will intersect the pin shafts.
  - Furthermore, when the panel is pinned against a Technic Beam (e.g. `32278` 1x15 Beam), the contact surfaces of the panel and beam touch. Because the panel and beam are not directly mated (they are mediated by pins), whole-pair exemption does nothing to prevent false-positive collisions at the panel-to-beam interface.

---

## 3. Library & Catalogue Census: Impact Quantification

### 3.1 LDraw Library Census (24,735 Total Part Files)
An exhaustive scan of the LDraw library was performed to measure the exact number of parts governed by each connector interface:

| Connector Category | Representative Parts | Library Count | Currently Baked | Unbaked / Blocked |
| :--- | :--- | :---: | :---: | :---: |
| **Technic Panel** | `11946`, `11947`, `64782`, `24116`, `32527` | 141 | 0 | **141** |
| **Technic Bush** | `3713`, `4265a`, `4265b`, `4265c`, `32123a` | 14 | 1 | **13** |
| **Technic Cross Block** | `32291`, `32557`, `41678`, `32068`, `2393` | 20 | 5 | **15** |
| **Technic Axle & Hybrids**| `10197`, `11214`, `13670`, `15462`, `43093` | 74 | 11 | **63** |
| **Technic Pin & Joiners** | `15100`, `15555`, `15646`, `29219`, `32138` | 57 | 24 | **33** |
| **Plate / Tile with Clip** | `4085a-d`, `60470`, `48336`, `6157`, `30237` | 19 | 14* | **5** |
| **Bar / Weapon / Rod** | `4095`, `30374`, `2714a`, `11089`, `11090` | 272 | 26* | **246** |
| **Hinge Halves** | `44301a`/`44302a`, `44567a`/`44568`, `30552`/`30553` | 301 | 101 | **200** |
| **Towball / Ball Socket** | `2736`, `3730`, `3613`, `14704`, `90612` | 81 | 23* | **58** |
| **TOTAL** | | **979** | **205** | **774** |

*\* Baked with severely under-approximated occupancy (clip jaws and socket cups dropped, bars given empty occupancy) specifically to evade collision detection.*

### 3.2 Impact on Priority Set: LEGO Technic 42145 Airbus H175 Rescue Helicopter
Set 42145 is the primary official benchmark set (2,001 pieces). An analysis of its real bill of materials demonstrates the necessity of this work:
- **Axle Assemblies**: Over 150 plain axle instances (`4519` Axle 3, `3705` Axle 4, `32073` Axle 5, `3706` Axle 6, `44294` Axle 7, `3707` Axle 8, `60485` Axle 9).
- **Technic Panels**: Over 35 panel instances forming the cabin shell, fairings, tail boom, and engine cowling (`11946`, `11947`, `87080`, `87086`, `64782`, `24116`, `15458`).
- **Technic Bushes**: Over 80 bushes (`3713`, `4265c`) retaining gears, linkages, and rotor shafts.
- **Rotor Head & Winch Mechanism**: Multiple bar/clip, towball, and hinge connections.
- **Current Coverage Bottleneck**: Set 42145 was pushed from 37.0% to 70.8% coverage in commit `67ce465` by baking 60 standard liftarms and pins. The remaining 29.2% is composed almost entirely of panels, bushes, cross-blocks, and mechanisms that cannot pass validation without generalized mated-connector exemption.

---

## 4. Architectural Design: Socket-Type-Driven Generalisation

To replace ad-hoc loops with an extensible, type-safe, and performant framework, the collision exemption system should be refactored into a **socket-type-driven engine**.

```
                +---------------------------------------+
                |    Baked Part Mesh Connectors JSON    |
                +---------------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
     [studs/sockets]           [pins/holes]              [axles/bores]
          |                         |                         |
          v                         v                         v
+-------------------+     +-------------------+     +-------------------+
| StudSocketHandler |     |   PinHoleHandler  |     |  AxleBoreHandler  |
+-------------------+     +-------------------+     +-------------------+
          |                         |                         |
          +-------------------------+-------------------------+
                                    |
                                    v
                     +-----------------------------+
                     | Connector Mating Classifier |
                     +-----------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|  Tier 1: Fast Pair    |                       |  Tier 2: Joint Zone   |
|  Exemption (BBox Vol) |                       |  Capsule Mask (Panels)|
+-----------------------+                       +-----------------------+
            |                                               |
            +-----------------------+-----------------------+
                                    |
                                    v
                     +-----------------------------+
                     |   Filtered Collision SAT    |
                     +-----------------------------+
```

### 4.1 Schema Contract & Backward Compatibility
Existing baked JSON files in `public/parts/` already contain:
```json
"connectors": {
  "studs": [...],
  "sockets": [...],
  "holes": [...],
  "pins": [...],
  "bars": [...],
  "hinges": [...]
}
```
To guarantee 100% backward compatibility, existing keys are retained. New connector keys are added following the same dictionary shape:
- `"axles"`: `[{"pos": [x, y, z], "dir": [dx, dy, dz], "len": L}]` (Axle rod segments).
- `"clips"`: `[{"pos": [x, y, z], "dir": [dx, dy, dz], "kind": "c_clip"}]` (Bar receiving jaws).
- `"towballs"`: `[{"pos": [x, y, z]}]` (Spherical towball pivot).
- `"ball_sockets"`: `[{"pos": [x, y, z], "dir": [dx, dy, dz]}]` (Receiving cup).

### 4.2 The Typed Socket Interface Model
In `renderers/brick_parts_validate.py` (and `atoms_brick.gs`), connectors are processed through a registry of **Socket Types**:

```python
SOCKET_TYPES = {
    'stud': {
        'male': 'studs',
        'female': 'sockets',
        'geom': 'point',
        'tolerance_dist': 0.5,
        'tolerance_angle': -0.5,
        'exemption': 'none',        # Brick boxes do not overlap when stacked
    },
    'pin': {
        'male': 'pins',
        'female': 'holes',
        'geom': 'segment',
        'tolerance_dist': 0.5,
        'min_overlap': 10.0,
        'exemption': 'pair_or_zone',
    },
    'axle': {
        'male': 'axles',
        'female': 'holes',          # Technic pegholes, axleholes, and gear bores accept axles
        'geom': 'line_segment',
        'tolerance_dist': 0.5,
        'exemption': 'pair_or_zone',
    },
    'bar_clip': {
        'male': 'bars',
        'female': 'clips',
        'geom': 'segment_point',
        'tolerance_dist': 0.5,
        'tolerance_angle': 0.95,
        'exemption': 'pair_or_zone',
    },
    'hinge': {
        'male': 'hinges',
        'female': 'hinges',
        'geom': 'axis',
        'tolerance_dist': 0.5,
        'tolerance_angle': 0.99,
        'exemption': 'pair',
    },
    'towball': {
        'male': 'towballs',
        'female': 'ball_sockets',
        'geom': 'point',
        'tolerance_dist': 0.5,
        'exemption': 'pair',
    }
}
```

### 4.3 Two-Tier Exemption Pipeline

#### Tier 1: Small-Connector Whole-Pair Exemption (Fast Path)
Whole-pair exemption is mathematically sound and computationally optimal ($O(1)$ lookup) **if and only if at least one part is small**:
$$\min\left(\text{Volume}(\text{BBox}(A)), \text{Volume}(\text{BBox}(B))\right) \le V_{\text{thresh}}$$
where $V_{\text{thresh}} \approx 15,000\text{ LDU}^3$ (the volume of a 3L pin, bush, or towball).
- **Proof of Safety**: A 2L pin or bush has no distant geometry. Its entire volume is confined to the immediate socket/pin connection zone. It is physically impossible for a 2L pin to collide with a distant section of a beam. Therefore, exempting the pair $(A, B)$ when $B$ is a small connector part cannot produce a false negative.

#### Tier 2: Joint-Zone Capsule Exemption Mask (Surgical Path for Large Parts & Panels)
When both parts are large (e.g. Beam $A$ and Beam $B$, or Panel $A$ and Beam $B$):
- Each mated connector defines a localized **Joint Zone** $Z_{\text{joint}}$:
  $$Z_{\text{joint}} = \left\{ \mathbf{x} \in \mathbb{R}^3 : \text{dist}(\mathbf{x}, \mathbf{S}) \le R_{\text{clearance}} \right\}$$
  where $\mathbf{S}$ is the connector segment or center, and $R_{\text{clearance}} \approx 10.0$ LDU.
- When evaluating box $a \in \mathcal{B}_A$ and box $b \in \mathcal{B}_B$:
  - If both $a$ and $b$ intersect $Z_{\text{joint}}$, and their intersection volume is within $Z_{\text{joint}}$, the collision check for that specific box pair $(a, b)$ is skipped.
  - If boxes $a$ and $b$ are outside $Z_{\text{joint}}$ (e.g. at the opposite end of the beams, 200 LDU away), they are evaluated normally by SAT.
- **Transitive Joint Sharing (The Technic Panel Fix)**:
  If Part $A$ (Panel) and Part $B$ (Beam) both mate with Part $P$ (Pin) at the same joint location $\mathbf{S}_{\text{joint}}$:
  $$\| \mathbf{S}_{\text{joint}, A} - \mathbf{S}_{\text{joint}, B} \| \le 1.0\text{ LDU}$$
  Parts $A$ and $B$ are recognized as a **co-joined pair**. The Joint Zone $Z_{\text{joint}}$ is applied to the contact interface between $A$ and $B$, exempting the mounting flange interface while preserving full collision detection across the rest of the panel!

### 4.4 Algorithmic Complexity & Google Apps Script Performance
Currently, pin matching uses a naive $O(N^2)$ all-pairs loop.
In sets with $N = 2,001$ parts (such as 42145), an $N^2$ loop executes $\sim 4 \times 10^6$ iterations, which exceeds the execution timeout of Google Apps Script.
- **Solution: 20-LDU Spatial Hashing**:
  Stud matching in `atoms_brick.gs` and `brick_parts_validate.py` already uses a 20-LDU spatial hash (`sock_hash`).
  All point and segment connectors should be bucketed into the same spatial hash structure.
  Each connector queries only its $3 \times 3 \times 3 = 27$ neighbouring hash cells.
  This reduces connector classification from $O(N^2)$ to $O(N)$ expected time, ensuring real-time execution in both Python and browser JS.

---

## 5. Implementation Roadmap

### Phase 1: Connector Extraction in Pipeline (`scripts/ldraw/parts.py` & `bake_parts.py`)
1. **Technic Axles**: Extract axle centerline segments from axle primitives (`axleconnect.dat`) and plain axle bounds. Populate `connectors.axles`.
2. **Axle Holes**: Extend `AXLE_HOLE_RE` to include all DOS 8.3 truncated variants (`axlehol2.dat`, `axlehol5.dat`).
3. **Clips**: Implement clip jaw recognition (detecting C-clips from cylindrical arcs and opening angles). Populate `connectors.clips`.
4. **Towballs & Sockets**: Detect `towball.dat` ($r=5.1$) and `towballsocket.dat`. Populate `connectors.towballs` and `connectors.ball_sockets`.

### Phase 2: Engine Generalisation (`renderers/brick_parts_validate.py` & `atoms_brick.gs`)
1. Implement the unified `SOCKET_TYPES` table.
2. Implement 20-LDU spatial hashing for all connector categories.
3. Add Tier 1 (volume-gated pair exemption) and Tier 2 (co-joined triad exemption for pins/axles).
4. Run `scripts/gen_parts_parity_cases.mjs` to ensure 100% byte-for-byte agreement between Python and JS twins.

### Phase 3: Part Family Unlocking
1. **Technic Bush Family** (`3713`, `4265c`): Add occupancy boxes with axle bore, unlocked by axle exemption.
2. **Technic Cross Blocks** (`32291`, `32557`): Add dual-axis occupancy boxes, unlocked by orthogonal pin/axle exemption.
3. **Technic Panels** (`64782`, `11946`, `11947`): Add flat and curved shell occupancy, unlocked by co-joined triad exemption.

---

## 6. Verification & Test Plan

1. **Synthetic Unit Proofs**:
   - `test_mated_exemption_far_end_collision_detected`: Verify that two 1x16 beams pinned at hole 1 still detect collisions when folded onto each other at hole 16.
   - `test_cojoined_triad_exemption`: Verify that Panel $A$ and Beam $B$ joined via Pin $P$ do not flag collisions at their contact flange.
   - `test_axle_through_bush_exemption`: Verify that Axle $A$ passing through Bush $B$ reports zero collisions and registers an axle connection.
2. **Real Resolved Geometry Tests**:
   - Real 42145 fuselage joint: `11946` + `2780` + `32523` (Panel + Pin + Liftarm) clears with 0 collisions and 2 connections.
   - Real drivetrain joint: `3705` + `3713` + `3648b` (Axle + Bush + 24T Gear) clears with 0 collisions and 2 connections.
3. **Twin Parity Verification**:
   - Full execution of `pytest tests/test_brick_parts_validate.py` (all tests passing).
   - Full execution of `pytest tests/test_brick_parts_validate_js.py` (JS parity passing).

---

## Conclusion

The 2026-09-28 pin/hole and hinge exemption was a vital first step, but its coarse whole-pair scope and two-connector limitation inherently block Technic panels, bushes, cross-blocks, and large mechanical sets.

By generalising the architecture into a **socket-type-driven engine with two-tier exemption (coarse for small connectors, localized joint-zone masks for structural parts)**, over **770+ currently blocked LDraw parts** can be safely unlocked across the catalogue, enabling official sets like LEGO 42145 to achieve full physical validation without compromising spec §3 safety.
