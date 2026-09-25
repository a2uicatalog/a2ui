"""brick_validate — deterministic build checks for a brick model (the `brick_build_3d` atom's `bricks` array).

A model is a list of bricks ``{x, y, z, w, d, h, c}``: ``x``/``z`` are stud positions, ``y`` the brick layer
(0 = on the baseplate), ``w``/``d`` the footprint in studs, ``h`` the height in bricks, ``c`` a hex colour.

Nothing here judges a design by looking at it. The checks are plain geometry over the brick list:

  collisions   no two bricks occupy the same stud cell on the same layer
  anchored     every brick reaches the baseplate through stud-to-tube connections
  connections  at least one stud engaged (the count is reported)
  balance      the centre of mass lies inside the convex hull of the ground-level footprint

The same functions exist in JavaScript inside the atom renderer so the browser can re-derive them live;
tests/test_brick_validate.py replays shared fixtures (tests/fixtures/bricks/parity_cases.json, recorded from the
JS) so the two sides cannot drift silently. Prices are an indicative formula, not BrickLink data.
"""
import math
from decimal import Decimal, ROUND_HALF_UP

STEP_SIZE = 6            # instruction steps: one layer at a time, at most this many bricks each
BALANCE_TIGHT = 0.5      # studs of margin below which the balance check warns

PALETTE_NAMES = {
    '#c91a09': 'red', '#fe8a18': 'orange', '#f2cd37': 'yellow', '#a5ca18': 'lime', '#237841': 'green',
    '#36aebf': 'azure', '#0055bf': 'blue', '#6a3a9c': 'purple', '#f2f3f2': 'white', '#1b2a34': 'black',
    '#6b2f1a': 'brown', '#e4adc8': 'pink',
}


def _fixed(x, digits):
    """Format like JavaScript's Number.prototype.toFixed (exact ties round away from zero)."""
    q = Decimal(1).scaleb(-digits)
    return format(Decimal(x).quantize(q, rounding=ROUND_HALF_UP), 'f')


def _brick(b):
    if isinstance(b, dict):
        x, y, z = b['x'], b['y'], b['z']
        w, d, h, c = b.get('w', 1), b.get('d', 1), b.get('h', 1), b.get('c', '#c91a09')
    else:
        x, y, z, w, d, h, c = b
    for name, v in (('x', x), ('y', y), ('z', z), ('w', w), ('d', d), ('h', h)):
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError('brick %s must be an integer, got %r' % (name, v))
    if w < 1 or d < 1 or h < 1:
        raise ValueError('brick w, d and h must be at least 1')
    if x < 0 or y < 0 or z < 0:
        raise ValueError('brick x, y and z must be non-negative (normalise() shifts a model to the origin)')
    return {'x': x, 'y': y, 'z': z, 'w': w, 'd': d, 'h': h, 'c': str(c).lower()}


def normalise(bricks):
    """Shift a model to the origin, order it for building (layer by layer, sweeping round the centre) and
    number the instruction steps. Returns ``{bricks, W, D, L, steps}``."""
    raw = []
    for b in bricks:
        if isinstance(b, dict):
            raw.append({'x': b['x'], 'y': b['y'], 'z': b['z'], 'w': b.get('w', 1), 'd': b.get('d', 1),
                        'h': b.get('h', 1), 'c': str(b.get('c', '#c91a09')).lower()})
        else:
            x, y, z, w, d, h, c = b
            raw.append({'x': x, 'y': y, 'z': z, 'w': w, 'd': d, 'h': h, 'c': str(c).lower()})
    if not raw:
        raise ValueError('a model needs at least one brick')
    mx = min(b['x'] for b in raw)
    my = min(b['y'] for b in raw)
    mz = min(b['z'] for b in raw)
    for b in raw:
        b['x'] -= mx
        b['y'] -= my
        b['z'] -= mz
    W = max(b['x'] + b['w'] for b in raw)
    D = max(b['z'] + b['d'] for b in raw)
    L = max(b['y'] + b['h'] for b in raw)
    raw.sort(key=lambda b: (b['y'], math.atan2(b['z'] + b['d'] / 2 - D / 2, b['x'] + b['w'] / 2 - W / 2)))
    step, last_y, count = 0, -1, 0
    for b in raw:
        if b['y'] != last_y or count >= STEP_SIZE:
            step += 1
            count = 0
            last_y = b['y']
        b['step'] = step
        count += 1
    return {'bricks': raw, 'W': W, 'D': D, 'L': L, 'steps': step}


def _cell(x, y, z):
    return (y * 4096 + z) * 4096 + x


def _hull(points):
    pts = sorted(set(map(tuple, points)))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def validate(bricks):
    """Run the build checks on a brick list (already at the origin: ``y == 0`` is the baseplate layer).

    Returns ``{ok, checks, connections, overlaps, floating, com, parts, cost}`` where ``checks`` is a list of
    ``{id, label, status, detail}`` with status ``pass`` / ``warn`` / ``fail``.
    """
    bs = [_brick(b) for b in bricks]
    if not bs:
        raise ValueError('a model needs at least one brick')

    owner, overlap_cells, pairs = {}, 0, set()
    for i, b in enumerate(bs):
        for y in range(b['y'], b['y'] + b['h']):
            for z in range(b['z'], b['z'] + b['d']):
                for x in range(b['x'], b['x'] + b['w']):
                    k = _cell(x, y, z)
                    if k in owner:
                        overlap_cells += 1
                        pairs.add((min(i, owner[k]), max(i, owner[k])))
                    else:
                        owner[k] = i

    adj = [set() for _ in bs]
    conn, grounded = 0, []
    for i, b in enumerate(bs):
        for z in range(b['z'], b['z'] + b['d']):
            for x in range(b['x'], b['x'] + b['w']):
                if b['y'] == 0:
                    conn += 1
                    grounded.append(i)
                    continue
                j = owner.get(_cell(x, b['y'] - 1, z))
                if j is not None and j != i:
                    conn += 1
                    adj[i].add(j)
                    adj[j].add(i)
    seen, queue = set(), []
    for g in grounded:
        if g not in seen:
            seen.add(g)
            queue.append(g)
    while queue:
        c = queue.pop()
        for n in adj[c]:
            if n not in seen:
                seen.add(n)
                queue.append(n)
    floating = len(bs) - len(seen)

    mass = cx = cz = 0.0
    foot = []
    for b in bs:
        v = b['w'] * b['d'] * b['h']
        mass += v
        cx += (b['x'] + b['w'] / 2) * v
        cz += (b['z'] + b['d'] / 2) * v
        if b['y'] == 0:
            foot += [(b['x'], b['z']), (b['x'] + b['w'], b['z']),
                     (b['x'] + b['w'], b['z'] + b['d']), (b['x'], b['z'] + b['d'])]
    cx /= mass
    cz /= mass
    margin = -1.0
    if foot:
        hp = _hull(foot)
        margin = 1e9
        for i, a in enumerate(hp):
            e = hp[(i + 1) % len(hp)]
            margin = min(margin, ((e[0] - a[0]) * (cz - a[1]) - (e[1] - a[1]) * (cx - a[0]))
                         / math.hypot(e[0] - a[0], e[1] - a[1]))

    part_map = {}
    for b in bs:
        colour = PALETTE_NAMES.get(b['c'], b['c'])
        key = '%d×%d|%s' % (b['w'], b['d'], colour)
        p = part_map.setdefault(key, {'size': '%d×%d' % (b['w'], b['d']), 'colour': colour, 'hex': b['c'],
                                      'count': 0, 'unit': 0.03 + 0.04 * b['w'] * b['d']})
        p['count'] += 1
    parts = sorted(part_map.values(), key=lambda p: -p['count'])
    cost = 0.0
    for p in parts:
        p['line'] = p['count'] * p['unit']
        cost += p['line']

    np_ = len(pairs)
    checks = [
        {'id': 'collisions', 'label': 'No collisions', 'status': 'fail' if np_ else 'pass',
         'detail': ('%d brick pair%s share %d stud cell%s' % (np_, 's' if np_ > 1 else '', overlap_cells,
                                                              's' if overlap_cells > 1 else ''))
         if np_ else '0 shared cells'},
        {'id': 'anchored', 'label': 'Every brick anchored', 'status': 'fail' if floating else 'pass',
         'detail': ('%d brick%s not connected to the baseplate' % (floating, 's' if floating > 1 else ''))
         if floating else 'all %d bricks reach the baseplate' % len(bs)},
        {'id': 'connections', 'label': 'Stud connections', 'status': 'pass' if conn else 'fail',
         'detail': '%d engaged' % conn},
        {'id': 'balance', 'label': 'Centre of mass over footprint',
         'status': 'fail' if margin < 0 else 'warn' if margin < BALANCE_TIGHT else 'pass',
         'detail': '(%s, %s) · %s%s studs' % (_fixed(cx, 1), _fixed(cz, 1),
                                              'outside by ' if margin < 0 else 'margin ', _fixed(abs(margin), 2))},
    ]
    return {'ok': all(c['status'] != 'fail' for c in checks), 'checks': checks, 'connections': conn,
            'overlaps': np_, 'floating': floating, 'com': {'x': cx, 'z': cz, 'margin': margin},
            'parts': parts, 'cost': cost}
