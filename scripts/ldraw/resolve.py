"""LDraw file resolution: find a part by id, walk its subfile tree with transforms, BFC winding and colour
resolution, and collect triangles (consistently wound CCW as seen from outside), type-2 edge lines and type-5
conditional lines. Colour 16 ("main") and 24 ("edge") are left unresolved in the output — the renderer tints them
per part instance — every other colour code is resolved to its LDConfig RGB immediately (decorated/printed parts
are not in the curated set, but a stray fixed colour should still bake correctly rather than silently vanish).

Pinned library location: set LDRAW_DIR, or run scripts/ldraw/fetch_library.py first (see its docstring for the
pinned release and checksum). See spec/brick-parts-v0.1.md section 5 for the mesh contract this produces.
"""
import functools
import os
import re

LD = os.environ.get("LDRAW_DIR") or os.path.join(os.path.dirname(__file__), "_ldraw_cache", "ldraw")
SEARCH_DIRS = ["parts", "parts/s", "p", "p/48", "p/8"]
STUD_RE = re.compile(r"^stud(2a?|10|15)?\.dat$")

ID = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)   # 3x4 affine: a..i (rotation/scale), x,y,z


def _det(M):
    a, b, c, d, e, f, g, h, i = M[:9]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def mat_mul(A, B):
    """A applied after B: world = A(B(local))."""
    a = [[A[0], A[1], A[2], A[9]], [A[3], A[4], A[5], A[10]], [A[6], A[7], A[8], A[11]]]
    b = [[B[0], B[1], B[2], B[9]], [B[3], B[4], B[5], B[10]], [B[6], B[7], B[8], B[11]]]
    r = [[sum(a[i][k] * b[k][j] for k in range(3)) + (a[i][3] if j == 3 else 0) for j in range(4)] for i in range(3)]
    return (r[0][0], r[0][1], r[0][2], r[1][0], r[1][1], r[1][2], r[2][0], r[2][1], r[2][2], r[0][3], r[1][3], r[2][3])


def apply(M, p):
    return (M[0] * p[0] + M[1] * p[1] + M[2] * p[2] + M[9],
            M[3] * p[0] + M[4] * p[1] + M[5] * p[2] + M[10],
            M[6] * p[0] + M[7] * p[1] + M[8] * p[2] + M[11])


class Library:
    """Indexes a pinned LDraw tree once; `find`/`lines` are cached, so resolving 116 parts re-reads nothing."""

    def __init__(self, root=None):
        self.root = root or LD
        self._index = {}
        for d in SEARCH_DIRS:
            full = os.path.join(self.root, d)
            if not os.path.isdir(full):
                continue
            for f in os.listdir(full):
                if not f.lower().endswith(".dat"):
                    continue
                rel = (d.split("/", 1)[1] + "/" if d.startswith("parts/") else "") + f
                key = rel.lower().replace("\\", "/")
                self._index.setdefault(key, os.path.join(full, f))
                if d in ("p", "p/48", "p/8"):
                    # bare filename (files under p/ are referenced without a prefix) and, for the 48/ and 8/
                    # high-resolution primitive subdirs, also under their own prefix ("48\1-8chrd.dat" in .dat files)
                    self._index.setdefault(f.lower(), os.path.join(full, f))
                if d in ("p/48", "p/8"):
                    sub = d.split("/", 1)[1]  # "48" or "8"
                    self._index.setdefault(sub + "/" + f.lower(), os.path.join(full, f))
        if not self._index:
            raise RuntimeError(
                "LDraw library not found at %r. Run scripts/ldraw/fetch_library.py, or set LDRAW_DIR." % self.root)

    def find(self, name):
        n = name.lower().replace("\\", "/")
        for key in (n, "s/" + n if not n.startswith("s/") else n):
            if key in self._index:
                return self._index[key]
        return None

    @functools.lru_cache(maxsize=None)
    def _lines_cached(self, path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            return tuple(l.rstrip("\n") for l in fh if l.strip())

    def lines(self, path):
        return self._lines_cached(path)


class ColourTable:
    """Parses LDConfig.ldr: code -> {name, rgb '#rrggbb', edge '#rrggbb'}."""

    LINE_RE = re.compile(
        r"^0\s+!COLOUR\s+(\S+)\s+CODE\s+(\d+)\s+VALUE\s+(#[0-9A-Fa-f]{6})\s+EDGE\s+(#[0-9A-Fa-f]{6})")

    def __init__(self, lib):
        self.by_code = {16: {"name": "Main_Colour", "rgb": None, "edge": None},
                        24: {"name": "Edge_Colour", "rgb": None, "edge": None}}
        path = lib.find("ldconfig.ldr") or os.path.join(lib.root, "LDConfig.ldr")
        if not os.path.isfile(path):
            raise RuntimeError("LDConfig.ldr not found under %r" % lib.root)
        for l in open(path, encoding="utf-8", errors="replace"):
            m = self.LINE_RE.match(l.strip())
            if m:
                name, code, rgb, edge = m.groups()
                self.by_code[int(code)] = {"name": name, "rgb": rgb.lower(), "edge": edge.lower()}

    def resolve(self, code):
        """Returns ('main' | 'edge' | '#rrggbb', same-for-edge-lines) — main/edge are left for the renderer to tint."""
        if code == 16:
            return "main"
        if code == 24:
            return "edge"
        c = self.by_code.get(code)
        if c is None or c["rgb"] is None:
            return "main"          # unknown code: safer to inherit the instance colour than to guess a wrong one
        return c["rgb"]


class Part:
    """Resolved geometry of one part, in its own local LDU frame, at the origin."""

    def __init__(self):
        self.tris = []      # list of (p0, p1, p2, colour) — CCW as seen from outside; colour is 'main'/'edge'/#hex
        self.edges = []      # list of (p0, p1, colour)
        self.cond = []       # list of (p0, p1, ctl0, ctl1, colour)
        self.studs = []      # list of (pos, dir) — dir is the stud's local -Y through its transform
        self.holes = []      # list of (pos, dir) from peghole.dat
        self.pins = []       # list of (pos, dir) from confric*.dat
        self.min = [1e9, 1e9, 1e9]
        self.max = [-1e9, -1e9, -1e9]
        self.license = None
        self.title = None
        self.missing = set()

    def _bound(self, p):
        for k in range(3):
            self.min[k] = min(self.min[k], p[k])
            self.max[k] = max(self.max[k], p[k])


def resolve_part(lib, colours, name, bake_studs=False):
    """Resolves `name` (e.g. '3001.dat') to a Part. Studs are recorded as connectors and NOT baked into `tris`
    unless bake_studs=True (used by tests that want to see the whole part, e.g. a visual sanity render)."""
    part = Part()
    _walk(lib, colours, part, name, ID, colour_code=16, winding_ccw=True, invert=False, bake_studs=bake_studs, depth=0)
    return part


def _walk(lib, colours, part, name, M, colour_code, winding_ccw, invert, bake_studs, depth):
    path = lib.find(name)
    if not path:
        part.missing.add(name)
        return
    base = os.path.basename(name.lower().replace("\\", "/"))
    local_invert_next = False
    local_ccw = winding_ccw
    certified = None      # None until this file states BFC CERTIFY; NOCERTIFY files are treated as double-sided
    for raw in lib.lines(path):
        l = raw.strip()
        if not l:
            continue
        t = l.split()
        cmd = t[0]
        if cmd == "0":
            if depth == 0 and len(t) > 1 and t[1] == "!LICENSE":
                part.license = l[2:]
            if depth == 0 and part.title is None and not l.startswith("0 !") and not l.startswith("0 BFC") and not l.startswith("0 //"):
                part.title = l[2:].strip()
            if len(t) >= 2 and t[1] == "BFC":
                rest = t[2:]
                if "CERTIFY" in rest:
                    certified = True
                    if "CW" in rest:
                        local_ccw = False
                    elif "CCW" in rest:
                        local_ccw = True
                elif "NOCERTIFY" in rest:
                    certified = False
                elif "CW" in rest and "INVERTNEXT" not in rest:
                    local_ccw = False
                elif "CCW" in rest and "INVERTNEXT" not in rest:
                    local_ccw = True
                if "INVERTNEXT" in rest:
                    local_invert_next = True
            continue
        if cmd == "1" and len(t) >= 15:
            code = 16 if t[1] == "16" else (int(t[1]) if t[1].lstrip("-").isdigit() else 16)
            transform = tuple(float(v) for v in t[5:14]) + tuple(float(v) for v in t[2:5])
            N = mat_mul(M, transform)
            sub_invert = invert != (local_invert_next) != (_det(transform) < 0)
            sub_ccw = winding_ccw if not sub_invert else not winding_ccw
            sub_name = " ".join(t[14:])
            sub_base = os.path.basename(sub_name.lower().replace("\\", "/"))
            resolved_code = code if code not in (16, 24) else colour_code
            if not bake_studs and STUD_RE.match(sub_base):
                part.studs.append((apply(N, (0, 0, 0)), (-N[1], -N[4], -N[7])))
            elif sub_base == "peghole.dat":
                part.holes.append((apply(N, (0, 0, 0)), (N[1], N[4], N[7])))
                _walk(lib, colours, part, sub_name, N, resolved_code, sub_ccw, sub_invert, bake_studs, depth + 1)
            elif re.match(r"confric\d*\.dat$", sub_base):
                part.pins.append((apply(N, (0, 0, 0)), (N[1], N[4], N[7])))
                _walk(lib, colours, part, sub_name, N, resolved_code, sub_ccw, sub_invert, bake_studs, depth + 1)
            else:
                _walk(lib, colours, part, sub_name, N, resolved_code, sub_ccw, sub_invert, bake_studs, depth + 1)
            local_invert_next = False
        elif cmd == "2" and len(t) >= 8:
            code = int(t[1]) if t[1].lstrip("-").isdigit() else 24
            p0 = apply(M, tuple(float(v) for v in t[2:5]))
            p1 = apply(M, tuple(float(v) for v in t[5:8]))
            part.edges.append((p0, p1, colours.resolve(code if code != 16 else colour_code)))
        elif cmd == "5" and len(t) >= 14:
            code = int(t[1]) if t[1].lstrip("-").isdigit() else 24
            p0 = apply(M, tuple(float(v) for v in t[2:5]))
            p1 = apply(M, tuple(float(v) for v in t[5:8]))
            c0 = apply(M, tuple(float(v) for v in t[8:11]))
            c1 = apply(M, tuple(float(v) for v in t[11:14]))
            part.cond.append((p0, p1, c0, c1, colours.resolve(code if code != 16 else colour_code)))
        elif cmd in ("3", "4") and len(t) >= 2 + 3 * int(cmd):
            n = int(cmd)
            code = int(t[1]) if t[1].lstrip("-").isdigit() else colour_code
            pts_local = [tuple(float(v) for v in t[2 + 3 * i:5 + 3 * i]) for i in range(n)]
            pts = [apply(M, p) for p in pts_local]
            for p in pts:
                part._bound(p)
            wound_ccw = local_ccw if certified is not False else None   # None = not certified -> emit both windings
            colour = colours.resolve(code if code != 16 else colour_code)
            tris = [(pts[0], pts[1], pts[2])] if n == 3 else [(pts[0], pts[1], pts[2]), (pts[0], pts[2], pts[3])]
            for tri in tris:
                if wound_ccw is None:
                    part.tris.append((tri[0], tri[1], tri[2], colour))
                    part.tris.append((tri[0], tri[2], tri[1], colour))
                elif wound_ccw:
                    part.tris.append((tri[0], tri[1], tri[2], colour))
                else:
                    part.tris.append((tri[0], tri[2], tri[1], colour))
