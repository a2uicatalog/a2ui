"""Voxel model -> hollowed, tiled, anchored, validated brick list. Shared by the model builders below."""
import json, math, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from renderers import brick_validate as bv


def hollow(S, spine=None, thick=2):
    def keep(x, y, z):
        for dx in range(-thick, thick + 1):
            for dz in range(-thick, thick + 1):
                if dx * dx + dz * dz <= thick * thick + 1 and (x + dx, y, z + dz) not in S: return True
        for dy in range(1, thick + 1):
            if (x, y + dy, z) not in S or (x, y - dy, z) not in S: return True
        return False
    return {k: c for k, c in S.items() if keep(*k) or (spine and spine(*k))}


def tile(cells, box):
    X0, X1, Y0, Y1, Z0, Z1 = box
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


def unanchored(bricks, y0):
    owner = {}
    for i, b in enumerate(bricks):
        for z in range(b["z"], b["z"] + b["d"]):
            for x in range(b["x"], b["x"] + b["w"]): owner[(x, b["y"], z)] = i
    adj = [[] for _ in bricks]; seen = set(); q = []
    for i, b in enumerate(bricks):
        if b["y"] == y0: seen.add(i); q.append(i); continue
        for z in range(b["z"], b["z"] + b["d"]):
            for x in range(b["x"], b["x"] + b["w"]):
                j = owner.get((x, b["y"] - 1, z))
                if j is not None: adj[i].append(j); adj[j].append(i)
    while q:
        c = q.pop()
        for n in adj[c]:
            if n not in seen: seen.add(n); q.append(n)
    return [i for i in range(len(bricks)) if i not in seen]


def build(S, name, do_hollow=True, spine=None, out_dir=".", post=None):
    V = hollow(S, spine) if do_hollow else dict(S)
    if post: post(V)
    xs = [k[0] for k in V]; ys = [k[1] for k in V]; zs = [k[2] for k in V]
    box = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    cut = set(); trimmed = 0
    for _ in range(10):
        cells = {k: c for k, c in V.items() if k not in cut}
        bricks = tile(cells, box)
        fl = unanchored(bricks, box[2])
        if not fl: break
        for i in fl:
            b = bricks[i]
            for z in range(b["z"], b["z"] + b["d"]):
                for x in range(b["x"], b["x"] + b["w"]): cut.add((x, b["y"], z)); trimmed += 1
    M = bv.normalise(bricks)
    rep = bv.validate(M["bricks"])
    print("%-12s solid %5d kept %5d bricks %5d trimmed %4d steps %3d ok=%s  %s" % (
        name, len(S), len(V), len(bricks), trimmed, M["steps"], rep["ok"],
        "; ".join("%s:%s" % (c["label"].split()[0], c["status"]) for c in rep["checks"])), file=sys.stderr)
    json.dump(bricks, open("%s/%s.json" % (out_dir, name), "w"), separators=(",", ":"))
    return bricks, rep


def ell(x, y, z, cx, cy, cz, rx, ry, rz):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2 <= 1
