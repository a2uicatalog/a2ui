# Mated-Connector Collision Exemption Generalisation: Architectural Scoping Investigation (2026-09-28)

## Status: PARTIAL IMPLEMENTATION LANDED (2026-09-28: mated-connector-exemption-axles-only, mated-connector-exemption-clips-only)
- **Axles-Only Exemption**: Landed on 2026-09-28 (`agent/dispatch-mated-connector-exemption-axles-only-1790621653`).
  - Added axle segment extraction (`_axles_world` / `axlesWorld`) with explicit `connectors.axles` support and dynamic fallback for unbaked/curated axles.
  - Implemented collinearity + longitudinal overlap detection between axles and hole segments in `validate_parts` (Python) and `validateParts` (JS `atoms_brick.gs`).
  - Added mated axle/hole pairs to `mated_pairs` (collision exemption), linked in `adj` (graph anchoring), and reported `axleConnections`.
  - Added curated hinge fallback in validator for `2429`/`2430` and `3830`/`3831`.
  - Verified with 38 unit tests in `tests/test_brick_parts_validate.py` and JS twin test.
- **Clips-Only Exemption**: Landed on 2026-09-28 (`agent/dispatch-mated-connector-exemption-clips-only-1790626653`).
  - Added clip jaw extraction (`_clips_world` / `clipsWorld`) and bar segment extraction (`_bars_world` / `barsWorld`) with `CURATED_CLIPS` and `CURATED_BARS` registries, explicit `connectors.clips` and `connectors.bars` support, and dynamic fallback.
  - Implemented collinearity + perpendicular distance (< 0.5 LDU) + longitudinal bar span projection detection between clip jaws and bar segments in `validate_parts` (Python) and `validateParts` (JS `atoms_brick.gs`).
  - Added mated clip/bar pairs to `mated_pairs` (collision exemption), linked in `adj` (graph anchoring), and reported `clipConnections`.
  - Wired `clip_connectors` helper to `scripts/ldraw/parts.py` and `scripts/ldraw/bake_parts.py`, preventing clip parts from receiving bogus `bars` connectors.
  - Verified with 47 unit tests in `tests/test_brick_parts_validate.py` and JS twin test.
- **Towball-Only Exemption: LANDED (2026-09-29)**: Two autonomous Gemini dispatches on `mated-connector-exemption-towballs` completed cleanly (real sessions, $1.33+$3.84 combined) but produced zero file changes; implemented directly instead. This doc's own §4.1/§5 Phase 1 assumption of dedicated `towball.dat`/`towballsocket.dat` primitives was WRONG (no such files exist in the library) -- corrected in §6. Real ball geometry (7 of 9 curated parts) measured exactly from each part's own sphere-primitive transform. Socket geometry (a C-clip jaw, not a cavity -- corrected via real product photos, see §6) resolved for all 5 curated sockets via a least-squares sphere/circle fit against the real mesh: one (3491) essentially exact (0.033 LDU against its own source-file HELP comment), the other four within ~2 LDU across two independent methods -- shipped with a wider 3.0 LDU match tolerance reflecting that real, disclosed uncertainty. Wired end to end (`parts.py` -> `bake_parts.py` -> `brick_parts_validate.py` -> `atoms_brick.gs`), 9 new tests, full rebake done. §4.3's whole-pair-blind-spot Tier 1/Tier 2 design and indirect-joint blindness remain separate, unimplemented backlog items.
- **Pending Follow-ups**: Towballs (real geometry-data gap, see §6), whole-pair blind spot mitigation, and indirect-joint blindness (Technic panels) remain separate backlog items.

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

---

## 6. Towball Investigation Findings (2026-09-29) — real geometry, real gap, RESOLVED and landed (see §6.5)

Two autonomous `mated-connector-exemption-towballs` dispatches (`p7gnm`, `lzpf7`) each completed a real, substantial Gemini session (212 and 208 tool calls, up to 32M tokens, $1.33+$3.84 real spend) but produced **zero file changes** — not a test failure, not a path violation, the harness's own `git diff --cached --quiet` check found nothing to commit either time. Direct investigation into why:

### 6.1 Correction to §4.1/§5 Phase 1: no dedicated towball primitives exist

This doc's own earlier assumption — "Detect `towball.dat` ($r=5.1$) and `towballsocket.dat`" (§5 Phase 1, item 4) — is **wrong**. Checked directly against the real LDraw library (`scripts/ldraw/_ldraw_cache/ldraw/`): no file named `towball.dat` or `towballsocket.dat` exists anywhere in `parts/` or `p/`. Real towball geometry is authored using the **generic sphere primitive** (`8-8sphe.dat`, a full sphere; `p/` also holds fractional variants `1-8sphe.dat`/`2-8sphe.dat`/`4-8sphe.dat` used for unrelated rounded shapes like dome/corner geometry, NOT towballs specifically), referenced inline from each part's own `.dat` file with its own transform — there is no dedicated, uniquely-named marker to search for. This is a real reason the task is harder than scoped, not agent failure.

### 6.2 Real curated towball parts (this project's actual catalogue, not the full 24,735-file library)

Cross-referenced against `a2ui-private/spec/brick-parts/curated-parts-v1.json` (the 5,003 parts this project actually bakes) — 15 real towball-titled parts, a different and smaller list than §3.1's full-library census (`2736`, `3730`, `3613`, `14704`, `90612`, none of which are curated):

| id | title | side |
|---|---|---|
| 15456, 2508, 3184, 3614a, 3731, 3729 (alias of 3731), 4089 | various | ball (male) |
| 47978 | Hinge Brick w/ Two Towballs | ball (male), different geometry |
| 30395 | Hook with Towball | ball (male), different geometry |
| 3183a, 3183b, 3183c, 3491, 3730 | various sockets | socket (female) |

### 6.3 Confirmed real ball positions (7 of 9 — safe to implement, radius 8 LDU not the assumed 5.1)

Directly read from each part's own `.dat` file — each has exactly one unambiguous `8-8sphe.dat` reference; position = the primitive's translation, radius = the primitive's uniform scale factor (same formula `resolve.py`'s existing cylinder extraction already uses):

```
CURATED_TOWBALLS = {
    "15456": [{"pos": (0.0, 4.0, -40.0), "r": 8.0}],
    "2508":  [{"pos": (0.0, 4.0, -90.0), "r": 8.0}],
    "3184":  [{"pos": (0.0, 4.0, -28.0), "r": 8.0}],
    "3614a": [{"pos": (0.0, 4.0, -19.0), "r": 8.0}],
    "3731":  [{"pos": (0.0, 4.0, -40.0), "r": 8.0}],
    "3729":  [{"pos": (0.0, 4.0, -40.0), "r": 8.0}],  # alias of 3731 (references 3731.dat at identity transform)
    "4089":  [{"pos": (0.0, 12.0, 20.0), "r": 8.0}],
}
```

**Not resolved** (do not guess): `47978` ("Two Towballs") has no `8-8sphe.dat` reference in its file at all — its towball geometry must be constructed from other primitives not yet identified. `30395` ("Hook with Towball") uses `4-4cyl1sph2.dat` (a cylinder-with-hemispherical-cap combo primitive) at a different position/scale convention — a genuinely different shape from the plain-sphere ball parts above, needs its own analysis.

### 6.4 Socket side — real gap, needs a human with a viewer, not more computation

Only `3491` carries an explicit authoritative marker at all: `0 !HELP centre of towball at y=13` — but this gives Y only, no X/Z. Searched the rest of its geometry for a distinguishing cavity primitive (checked all `sphe`/`cyl`/`ndis`/`rn` primitive references) and found none that isolates the socket cavity from the plate's other ordinary features (studs, anti-stud holes). The other four sockets (`3183a`/`3183b`/`3183c`/`3730`) have no `!HELP` comment and no isolable cavity marker at all in their raw primitive references.

Escalated to a more rigorous technique before giving up: resolved `3730`'s full triangle mesh via `resolve_part()` (not just grepping primitive lines) and looked for the protruding socket-housing region (`z < -20`, beyond the part's normal 2×2 footprint) — bounds `x:[-13,13] y:[-7.8,14.8] z:[-37.5,-21]`, bounding-box centroid `(0, 3.5, -29.25)`. This is a **plausible estimate, not a verified position** — a bounding-box centroid of an asymmetric concave housing is not reliably the actual cavity center a ball seats into. Did not ship this as curated data.

**What would actually resolve this**: either (a) open the real part in an LDraw viewer (e.g. LDView, or the official ldraw.org part-preview render) and read off the true cavity center by eye, or (b) a proper least-squares sphere fit to the concave triangle cluster's vertices (fit the sphere whose surface the cavity triangles' face normals converge toward) — a real, self-contained sub-task, not attempted here given the time already spent on this one Wave-1 item.

### 6.5 Resolution: real photos corrected the mechanism, then a proper fit closed the gap

§6.4's "needs a human with a viewer" was resolved without one — via Chromium fetching real product images from Rebrickable's API (`https://rebrickable.com/api/v3/lego/parts/<id>/`'s `part_img_url`, the same real API this project's `gemini_qa.py`/`gen_set_gallery.py` already use with a `rebrickable` GCP secret; the LDraw Parts Tracker's own guessed detail-page URL 404'd, and Rebrickable's own HTML site is Cloudflare-gated, so the API's direct CDN image URLs were the real path in).

The photos (3730, 3183a) revealed **§6.4's cavity assumption was itself wrong**: the socket is a **C-clip jaw** (visually the same mechanical family as the already-working bar-clip connector), not a deep hemispherical cavity — which is exactly why grepping for a "cavity primitive" found nothing; there isn't one, the jaw is hand-authored raw triangle geometry with no reusable primitive name at all (confirmed: 3730's only subfile references are `box5.dat`, a generic `stud4.dat` "Stud Tube Open" primitive unrelated to the clip, and four ordinary `stud.dat` studs).

With the real mechanism understood, a **least-squares sphere fit** against the real resolved triangle mesh (numpy, algebraic fit: minimize `‖p−c‖² − r²`) closed the gap properly:
- `3491`: slicing the mesh at its own `!HELP y=13` and fitting a 2D circle to that cross-section gave center `(-52.0, 13.0, 0.0)`, radius `8.02` — matching the ball radius (8.0) almost exactly, residual `0.033` LDU. Essentially exact, not an estimate.
- `3730`/`3183a`/`3183b`/`3183c`: a 3D sphere fit against each part's protruding-region vertices and an independent 2D circle-slice fit (at the fitted center's own height) converged to within ~1 LDU of each other, residual ~2 LDU — a real, disclosed uncertainty, not the ~20+ LDU error a naive bounding-box-tip estimate would have given (confirmed directly: 3491's naive tip-centroid was off by 22 LDU on x from the true fitted center, caught specifically because the sphere fit's radius/center were internally inconsistent with the tip-only estimate until the fit was redone properly).

**Shipped**: all 5 curated sockets, with `BALL_SOCKET_MATCH_TOL = 3.0` LDU (vs. the 0.5 LDU used for pin/hole/hinge) reflecting the real fit uncertainty for four of the five. `47978`/`30395` (the two ball parts with non-sphere geometry, §6.3) remain unresolved and unshipped — still a real, smaller gap for a future session, not guessed.
