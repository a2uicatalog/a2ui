"""brick_parts_validate -- deterministic build checks for a real-parts brick_build_3d model (the atom's
partsModel array), spec/brick-parts-v0.1.md sections 2 (connectors), 3 (collisions) and 4 (balance).

A model is a list of placed parts ``{p, x, y, z, r}``: ``p`` an LDraw part id (already alias-resolved -- see
_PART_ID_ALIAS in web_article.py), ``x``/``y``/``z`` its origin in real LDU (Y down), ``r`` a 0-23 index into
PART_ROT. Unlike the procedural ``bricks`` validator (brick_validate.py), positions are NOT on an integer stud
grid -- parts sit at arbitrary LDU coordinates and one of 24 fixed rotations, so all geometry here works in real
LDU world space via rot_ldu (a pure rotation, not brick_parts's render-space partTp scale/reflection).

Nothing here judges a design by looking at it. The checks are plain geometry over each part's baked mesh data
(occupancy boxes, stud/socket/pin/hole connectors -- see public/parts/<id>.json):

  collisions   no two parts' occupancy boxes overlap by more than 0.5 LDU on all three axes
  anchored     every part reaches the baseplate through stud-to-socket or pin-to-hole connections
  connections  stud + pin connections engaged (each reported separately, and as a total)
  balance      the centre of mass lies inside the convex hull of the baseplate-resting footprint

Parts with no occupancy data yet (needs_occupancy=true in the baked mesh) are reported as "not checked",
never silently treated as collision-free or omitted -- spec section 3's honesty requirement.

The same functions exist in JavaScript inside the atom renderer (atoms_brick.gs's validateParts) so the
browser can re-derive them live; tests/test_brick_parts_validate.py replays
tests/fixtures/bricks/parts_parity_cases.json (captured from the JS, via
scripts/gen_parts_parity_cases.mjs) so the two sides cannot drift silently -- the same guarantee
tests/test_brick_validate.py already gives the procedural validator, and the same reason it exists: an
agent-supplied real-parts design checked server-side gets the same verdict the browser would show.
"""
import math

# Twin of PART_ROT in atoms_brick.gs -- edit BOTH. 24 fixed axis-aligned rotations, world = M . local + t,
# stored flat (row-major 3x3) to match the JS side exactly.
PART_ROT = [
    (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0),
    (-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0),
    (0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0),
    (-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0),
    (-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0),
    (-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0),
    (0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0),
    (0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0),
    (0.0, -1.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0),
    (0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, -1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0),
    (0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
    (0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0),
    (1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0),
]


def rot_ldu(r, p):
    m = PART_ROT[r]
    return (m[0] * p[0] + m[1] * p[1] + m[2] * p[2],
            m[3] * p[0] + m[4] * p[1] + m[5] * p[2],
            m[6] * p[0] + m[7] * p[1] + m[8] * p[2])


def _dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _dist3(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add3(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _conn_world(mesh, kind, r, ex, ey, ez):
    q = mesh['quant']
    out = []
    for c in (mesh.get('connectors') or {}).get(kind) or []:
        lp = (c['pos'][0] / q, c['pos'][1] / q, c['pos'][2] / q)
        wp = rot_ldu(r, lp)
        wd = rot_ldu(r, c['dir'])
        out.append({'pos': (wp[0] + ex, wp[1] + ey, wp[2] + ez), 'dir': wd})
    return out


def _world_boxes(mesh, r, ex, ey, ez):
    occ = mesh.get('occupancy')
    if not occ:
        return None
    out = []
    for b in occ:
        c0 = rot_ldu(r, (b[0], b[2], b[4]))
        c1 = rot_ldu(r, (b[1], b[3], b[5]))
        out.append((min(c0[0], c1[0]) + ex, max(c0[0], c1[0]) + ex,
                    min(c0[1], c1[1]) + ey, max(c0[1], c1[1]) + ey,
                    min(c0[2], c1[2]) + ez, max(c0[2], c1[2]) + ez))
    return out


def _boxes_overlap(a, b):
    ox = min(a[1], b[1]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[2], b[2])
    oz = min(a[5], b[5]) - max(a[4], b[4])
    return ox > 0.5 and oy > 0.5 and oz > 0.5


def _on_grid(v):
    # JS's onGrid does `((v-10)%20+20)%20` to force a non-negative remainder, since JS `%` keeps the dividend's
    # sign; Python's `%` already returns a non-negative result for a positive divisor, so the extra +20%20 the
    # JS side needs would be redundant (harmless, but pointless) here -- do not "restore" it to look more like
    # the JS source, they are equivalent for divisor 20.
    m = (v - 10) % 20
    return m < 0.5 or m > 19.5


def _point_line_dist(p, a, b):
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ap = (p[0] - a[0], p[1] - a[1], p[2] - a[2])
    l2 = _dot3(ab, ab) or 1e-9
    t = _dot3(ap, ab) / l2
    proj = (a[0] + ab[0] * t, a[1] + ab[1] * t, a[2] + ab[2] * t)
    return _dist3(p, proj), t


def _pair_holes(mesh):
    """Pair a mesh's local hole entries (one {pos,dir} per face) into (a,b) segments: greedy nearest
    opposite-direction match, in LOCAL (unquantised LDU) space -- spec section 2's "the segment between the
    pair is the hole axis"."""
    q = mesh['quant']
    holes = [{'pos': (h['pos'][0] / q, h['pos'][1] / q, h['pos'][2] / q), 'dir': h['dir']}
             for h in (mesh.get('connectors') or {}).get('holes') or []]
    used = [False] * len(holes)
    segs = []
    for i in range(len(holes)):
        if used[i]:
            continue
        best, best_d = -1, float('inf')
        for j in range(i + 1, len(holes)):
            if used[j] or _dot3(holes[i]['dir'], holes[j]['dir']) > -0.9:
                continue
            d = _dist3(holes[i]['pos'], holes[j]['pos'])
            if d < best_d:
                best_d, best = d, j
        if best >= 0:
            used[i] = used[best] = True
            segs.append((holes[i]['pos'], holes[best]['pos']))
    return segs


def _hull2(pts):
    """Twin of hull2 in atoms_brick.gs -- edit BOTH (validate_parts and validate share this exact shape via
    JS's own single hull2; this is a faithful, separate port for the Python side)."""
    pts = sorted(pts)

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def validate_parts(parts, meshes):
    """parts: list of {p, x, y, z, r} (already sanitised/alias-resolved). meshes: dict of part id -> baked mesh
    dict (as read from public/parts/<id>.json), or a value of None/'loading'/'error' for a part id whose mesh
    could not be resolved -- reported as "not checked", never silently skipped from the count.

    Returns {ok, checks, connections, studConnections, pinConnections, collisions, overlaps, floating,
    balance, com, parts, cost} -- the last two always empty/0 (real per-part pricing needs a BrickLink/
    Rebrickable catalogue, out of scope here), matching what atoms_brick.gs's validateParts() returns so a
    server-side caller and the browser agree field for field.
    """
    n = len(parts)
    mesh_list = [meshes.get(e['p']) for e in parts]
    studs, sockets, pins, boxes, hole_segs_world = [], [], [], [], []
    not_checked = 0
    for e, m in zip(parts, mesh_list):
        if not m or m in ('loading', 'error'):
            studs.append([]); sockets.append([]); pins.append([]); boxes.append(None); hole_segs_world.append([])
            not_checked += 1
            continue
        studs.append(_conn_world(m, 'studs', e['r'], e['x'], e['y'], e['z']))
        sockets.append(_conn_world(m, 'sockets', e['r'], e['x'], e['y'], e['z']))
        pins.append(_conn_world(m, 'pins', e['r'], e['x'], e['y'], e['z']))
        boxes.append(_world_boxes(m, e['r'], e['x'], e['y'], e['z']))
        if not m.get('occupancy'):
            not_checked += 1
        local_segs = _pair_holes(m)
        hole_segs_world.append([
            {'a': _add3(rot_ldu(e['r'], s[0]), (e['x'], e['y'], e['z'])),
             'b': _add3(rot_ldu(e['r'], s[1]), (e['x'], e['y'], e['z']))}
            for s in local_segs
        ])

    stud_conn = pin_conn = 0
    adj = [set() for _ in range(n)]
    base_adj = set()
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            for s in studs[i]:
                for k in sockets[j]:
                    if _dist3(s['pos'], k['pos']) < 0.5 and _dot3(s['dir'], k['dir']) < -0.5:
                        stud_conn += 1
                        adj[i].add(j)
                        adj[j].add(i)
        for k in sockets[i]:
            if (abs(k['pos'][1]) < 0.5 and _on_grid(k['pos'][0]) and _on_grid(k['pos'][2])
                    and _dot3(k['dir'], (0, -1, 0)) < -0.5):
                base_adj.add(i)
                stud_conn += 1

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

    seen = set(base_adj)
    queue = list(base_adj)
    while queue:
        c = queue.pop()
        for nb in adj[c]:
            if nb not in seen:
                seen.add(nb)
                queue.append(nb)
    floating = [i for i in range(n) if i not in seen]

    collisions = []
    for i in range(n):
        if not boxes[i]:
            continue
        for b in boxes[i]:
            if b[3] > 0.5:
                collisions.append([-1, i])
                break
    for i in range(n):
        for j in range(i + 1, n):
            if not boxes[i] or not boxes[j]:
                continue
            if any(_boxes_overlap(a, b) for a in boxes[i] for b in boxes[j]):
                collisions.append([i, j])

    rest_idx = sorted(base_adj)
    balance, margin = 'none', None
    if rest_idx:
        mass = cx = cz = 0.0
        for i in range(n):
            if not boxes[i]:
                continue
            for b in boxes[i]:
                vol = (b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4])
                mass += vol
                cx += (b[0] + b[1]) / 2 * vol
                cz += (b[4] + b[5]) / 2 * vol
        cx /= mass
        cz /= mass
        foot = []
        for k in rest_idx:
            if boxes[k]:
                for b in boxes[k]:
                    foot += [(b[0], b[4]), (b[1], b[4]), (b[1], b[5]), (b[0], b[5])]
        hp = _hull2(foot)
        margin = 1e9
        for i in range(len(hp)):
            pa, pb = hp[i], hp[(i + 1) % len(hp)]
            margin = min(margin, ((pb[0] - pa[0]) * (cz - pa[1]) - (pb[1] - pa[1]) * (cx - pa[0]))
                         / math.hypot(pb[0] - pa[0], pb[1] - pa[1]))
        margin /= 20
        balance = 'fail' if margin < 0 else 'warn' if margin < 0.5 else 'pass'

    overlaps = sum(1 for c in collisions if c[0] != -1)
    checks = [
        {'id': 'collisions', 'label': 'No collisions', 'status': 'fail' if overlaps else 'pass',
         'detail': ('%d part pair%s overlap' % (overlaps, 's' if overlaps > 1 else '') if overlaps else '0 overlaps')
         + (' (%d part%s not checked, no occupancy data yet)' % (not_checked, 's' if not_checked > 1 else '')
            if not_checked else '')},
        {'id': 'anchored', 'label': 'Every part anchored', 'status': 'fail' if floating else 'pass',
         'detail': ('%d part%s not connected to the baseplate' % (len(floating), 's' if len(floating) > 1 else ''))
         if floating else 'all %d parts reach the baseplate' % n},
        {'id': 'connections', 'label': 'Stud + pin connections',
         'status': 'pass' if (stud_conn + pin_conn) else 'fail',
         'detail': '%d stud + %d pin' % (stud_conn, pin_conn)},
        {'id': 'balance', 'label': 'Centre of mass over footprint',
         'status': 'fail' if balance == 'none' else balance,
         'detail': 'no part rests on the baseplate to measure' if balance == 'none'
         else '(margin %s studs%s)' % (('%.2f' % abs(margin)), ', outside footprint' if balance == 'fail' else '')},
    ]
    return {
        'ok': all(c['status'] != 'fail' for c in checks), 'checks': checks,
        'connections': stud_conn + pin_conn, 'studConnections': stud_conn, 'pinConnections': pin_conn,
        'collisions': collisions, 'overlaps': overlaps, 'floating': floating, 'balance': balance,
        'com': {'margin': margin}, 'parts': [], 'cost': 0,
    }
