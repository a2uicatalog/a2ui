"""Harry Potter bust as a voxel model, tiled into bricks with the same running-bond rule as the atom's engine."""
import json, math, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from renderers import brick_validate as bv

SKIN, HAIR, ROBE = "#f2c29b", "#2b1d16", "#1b2a34"
RED, GOLD, WHITE, GREEN, LIPS = "#c91a09", "#f2cd37", "#f2f3f2", "#237841", "#a63c2a"

S = {}                                   # (x,y,z) -> colour, solid model


def put(x, y, z, c):
    S[(x, y, z)] = c


# ---- robe, shirt, tie ----
for y in range(0, 12):
    rx, rz = 9.6 - 0.2 * y, 6.4 - 0.1 * y
    for x in range(-11, 12):
        for z in range(-8, 9):
            if (x / rx) ** 2 + (z / rz) ** 2 <= 1:
                put(x, y, z, ROBE)
# ---- Gryffindor scarf ----
for i, y in enumerate(range(12, 16)):
    for x in range(-9, 10):
        for z in range(-7, 8):
            if (x / 7.9) ** 2 + (z / 5.8) ** 2 <= 1:
                put(x, y, z, RED if i % 2 == 0 else GOLD)
# ---- neck ----
for y in range(16, 19):
    for x in range(-4, 5):
        for z in range(-4, 5):
            if x * x + z * z <= 10.5:
                put(x, y, z, SKIN)

# ---- head ----
CY = 27
head = {}
for y in range(17, 38):
    for x in range(-11, 12):
        for z in range(-11, 12):
            if (x / 9.5) ** 2 + ((y - CY) / 9.6) ** 2 + (z / 8.7) ** 2 <= 1:
                head[(x, y, z)] = SKIN


def fy(x):                               # bottom edge of the fringe
    v = 33
    if x in (-7, -6, -5): v -= 2
    if x in (-2, -1): v -= 1
    if x >= 6: v -= 2
    return v


def is_hair(x, y, z):
    if z < -1 and y >= 20: return True
    if y >= 30 and z <= 2: return True
    if abs(x) >= 8 and z < 2 and y >= 23: return True
    if z > 2 and y >= fy(x): return True
    return False


for k in list(head):
    if is_hair(*k):
        head[k] = HAIR
# hair shell just outside the skull, only where hair grows
for y in range(17, 41):
    for x in range(-12, 13):
        for z in range(-12, 13):
            if (x, y, z) in head: continue
            if (x / 10.8) ** 2 + ((y - CY - 0.5) / 10.2) ** 2 + (z / 9.9) ** 2 <= 1 and is_hair(x, y, z):
                head[(x, y, z)] = HAIR

# front surface of the face, for features
zf = {}
for (x, y, z), c in head.items():
    if z > zf.get((x, y), -99): zf[(x, y)] = z
front = lambda x, y: zf.get((x, y))

feat = {}
for (cx, cy) in ((-4, 26), (4, 26)):                 # round glasses + eyes
    for x in range(cx - 3, cx + 4):
        for y in range(cy - 3, cy + 4):
            d = math.hypot(x - cx, y - cy)
            if front(x, y) is None: continue
            if 1.6 <= d <= 2.7: feat[(x, y)] = ROBE
            if d < 0.6: feat[(x, y)] = GREEN
for x in (-1, 0, 1): feat[(x, 27)] = ROBE            # bridge
for (x, y) in [(-3, 22), (-2, 21), (-1, 21), (0, 21), (1, 21), (2, 21), (3, 22)]: feat[(x, y)] = LIPS
for (x, y) in [(2, 33), (1, 32), (2, 32), (1, 31), (0, 30)]: feat[(x, y)] = RED   # scar
for (x, y), c in feat.items():
    z = front(x, y)
    if z is not None and head.get((x, y, z)) != HAIR:
        head[(x, y, z)] = c
# nose and ears
for y in (23, 24):
    z = front(0, y)
    if z is not None: head[(0, y, z + 1)] = SKIN
for sx in (-1, 1):
    for y in (25, 26):
        for z in (-1, 0, 1): head[(sx * 10, y, z)] = SKIN
S.update(head)

# ---- hollow it out: keep a 2-stud shell, solid floors and roofs ----
def keep(x, y, z):
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if dx * dx + dz * dz <= 5 and (x + dx, y, z + dz) not in S: return True
    for dy in (1, 2):
        if (x, y + dy, z) not in S: return True
        if (x, y - dy, z) not in S: return True
    return False


V = {k: c for k, c in S.items() if keep(*k) or (k[0] ** 2 + k[2] ** 2 <= 11 and 6 <= k[1] <= 20)}   # solid spine under the head
print("solid cells", len(S), "after hollowing", len(V), file=sys.stderr)

# ---- tile into bricks (port of the engine's tileLayers, running bond) ----
xs = [k[0] for k in V]; ys = [k[1] for k in V]; zs = [k[2] for k in V]
X0, X1, Y0, Y1, Z0, Z1 = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def tile(cells):
    out = []
    for y in range(Y0, Y1 + 1):
        taken, par, zp = set(), (y & 1) * 2, y & 1
        for z in range(Z0, Z1 + 1):
            for x in range(X0, X1 + 1):
                if (x, z) in taken: continue
                c = cells.get((x, y, z))
                if not c: continue
                e = x + 1
                while e <= X1 and e - x < 4 and (e + par) % 4 != 0 and cells.get((e, y, z)) == c and (e, z) not in taken: e += 1
                d = 1
                if ((z + zp) % 2 + 2) % 2 == 0 and z + 1 <= Z1:
                    e2 = x
                    while e2 < e and cells.get((e2, y, z + 1)) == c and (e2, z + 1) not in taken: e2 += 1
                    if e2 > x: e, d = e2, 2
                for zz in range(z, z + d):
                    for q in range(x, e): taken.add((q, zz))
                out.append({"x": x, "y": y, "z": z, "w": e - x, "d": d, "h": 1, "c": c})
    return out


def unanchored(bricks):
    owner = {}
    for i, b in enumerate(bricks):
        for z in range(b["z"], b["z"] + b["d"]):
            for x in range(b["x"], b["x"] + b["w"]): owner[(x, b["y"], z)] = i
    adj = [[] for _ in bricks]; seen = set(); q = []
    for i, b in enumerate(bricks):
        if b["y"] == Y0: seen.add(i); q.append(i); continue
        for z in range(b["z"], b["z"] + b["d"]):
            for x in range(b["x"], b["x"] + b["w"]):
                j = owner.get((x, b["y"] - 1, z))
                if j is not None: adj[i].append(j); adj[j].append(i)
    while q:
        c = q.pop()
        for n in adj[c]:
            if n not in seen: seen.add(n); q.append(n)
    return [i for i in range(len(bricks)) if i not in seen]


cut = set(); trimmed = 0
for _ in range(8):
    cells = {k: c for k, c in V.items() if k not in cut}
    bricks = tile(cells)
    fl = unanchored(bricks)
    if not fl: break
    for i in fl:
        b = bricks[i]
        for z in range(b["z"], b["z"] + b["d"]):
            for x in range(b["x"], b["x"] + b["w"]): cut.add((x, b["y"], z)); trimmed += 1
print("bricks", len(bricks), "trimmed cells", trimmed, file=sys.stderr)

# shift to non-negative stud coordinates for the atom's 0..255 range
for b in bricks: b["x"] -= X0; b["z"] -= Z0; b["y"] -= Y0
json.dump(bricks, open(sys.argv[1], "w"), separators=(",", ":"))
M = bv.normalise(bricks)
rep = bv.validate(M["bricks"])
print("ok", rep["ok"], [(c["label"], c["status"], c["detail"]) for c in rep["checks"]], "cost", round(rep["cost"], 2), "steps", M["steps"], file=sys.stderr)
