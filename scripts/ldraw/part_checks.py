#!/usr/bin/env python3
"""Deterministic geometry checks for baked LDraw parts (public/parts/<id>.json). No LLM, no network.

Every check is a fact about the baked data, reproducible from the file alone:

  mesh integrity   degenerate triangles, open (boundary) edges, non-manifold edges, signed volume
  bounds           the declared bounds equal the triangle extents (stale bounds break collision + camera fit)
  footprint        "Brick 2 x 4" style titles: the x/z extent matches W*20 x D*20 LDU (either orientation)
  connectors       every stud/socket lies inside the part's bounds; plain WxD parts carry exactly W*D studs
  occupancy        every occupancy box lies inside the declared bounds (hard error otherwise: it would collide in
                   empty space), and the box volume is not wildly larger than the mesh (ray-parity on a sample grid;
                   bricks are hollow underneath and their occupancy is deliberately a solid box, so 20-35% of sample
                   points legitimately fall outside -- only a much higher fraction is worth a warning)

A check returns findings {check, level: error|warn|info, msg}. level=error means the part must not ship as-is.
Metrics are always returned too, so the queue can show distributions and thresholds can be tuned from data.
"""
import json
import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "public" / "parts"

OPEN_EDGE_WARN = 0.35          # fraction of unique edges that are boundary edges (LDraw parts are often open at studs/undersides)
OCC_OUTSIDE_WARN = 0.60        # fraction of occupancy sample points outside the mesh (solid boxes over hollow bricks sit at 20-35%)
OCC_SAMPLES = 5                # per axis per box


def load(pid, parts_dir=PARTS):
    return json.loads((Path(parts_dir) / (pid + ".json")).read_text())


def triangles(mesh):
    q = mesh["quant"]
    tris = [np.array(g["pos"], dtype=np.int64).reshape(-1, 3, 3) for g in mesh["triangles"] if g["pos"]]
    return (np.concatenate(tris) if tris else np.zeros((0, 3, 3), dtype=np.int64)), q


def edge_stats(T):
    """(unique_edges, open_edges, nonmanifold_edges) using exact quantised vertex identity."""
    if len(T) == 0:
        return 0, 0, 0
    flat = T.reshape(-1, 3)
    _, inv = np.unique(flat, axis=0, return_inverse=True)
    ids = inv.reshape(-1, 3)
    e = np.concatenate([ids[:, [0, 1]], ids[:, [1, 2]], ids[:, [2, 0]]])
    e = np.sort(e, axis=1)
    e = e[e[:, 0] != e[:, 1]]
    _, counts = np.unique(e, axis=0, return_counts=True)
    return len(counts), int((counts == 1).sum()), int((counts > 2).sum())


def signed_volume(Tf):
    a, b, c = Tf[:, 0], Tf[:, 1], Tf[:, 2]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def inside_points(Tf, pts):
    """Ray-parity point-in-mesh (ray toward +x, Moller-Trumbore, vectorised over triangles per chunk of points)."""
    inside = np.zeros(len(pts), dtype=bool)
    if len(Tf) == 0:
        return inside
    v0, v1, v2 = Tf[:, 0], Tf[:, 1], Tf[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    d = np.array([1.0, 0.0, 0.0])
    h = np.cross(d, e2)
    a = np.einsum("ij,ij->i", e1, h)
    ok = np.abs(a) > 1e-9
    v0, e1, e2, h, a = v0[ok], e1[ok], e2[ok], h[ok], a[ok]
    for i in range(0, len(pts), 64):
        P = pts[i:i + 64] + np.array([0.0, 1e-3, 2e-3])         # nudge off edges shared by triangles
        s = P[:, None, :] - v0[None]
        u = np.einsum("pij,ij->pi", s, h) / a
        qv = np.cross(s, e1[None])
        v = qv[:, :, 0] / a
        t = np.einsum("pij,ij->pi", qv, e2) / a
        hit = (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)
        inside[i:i + 64] = (hit.sum(axis=1) % 2) == 1
    return inside


def _title_footprint(title):
    m = re.search(r"(\d+)\s*x\s*(\d+)", title or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


PLAIN_FAMILY = re.compile(r"^\s*(Brick|Plate|Tile)\s+\d+\s*x\s*\d+\s*$", re.I)


def check_part(mesh):
    findings, metrics = [], {}
    add = lambda check, level, msg: findings.append({"check": check, "level": level, "msg": msg})  # noqa: E731
    T, q = triangles(mesh)
    metrics["triangles"] = int(len(T))
    if len(T) == 0:
        add("mesh", "error", "no triangles")
        return findings, metrics
    Tf = T.astype(float) / q
    area = np.linalg.norm(np.cross(Tf[:, 1] - Tf[:, 0], Tf[:, 2] - Tf[:, 0]), axis=1) / 2
    metrics["degenerate"] = int((area < 1e-9).sum())
    if metrics["degenerate"] > 0.02 * len(T):
        add("mesh", "warn", "%d degenerate triangles" % metrics["degenerate"])
    uniq, openE, nonman = edge_stats(T)
    metrics.update(unique_edges=uniq, open_edges=openE, nonmanifold=nonman,
                   open_frac=round(openE / uniq, 4) if uniq else 0.0)
    if metrics["open_frac"] > OPEN_EDGE_WARN:
        add("mesh", "warn", "%.0f%% of edges are open (surface not closed)" % (100 * metrics["open_frac"]))
    vol = signed_volume(Tf)
    metrics["signed_volume"] = round(vol, 1)

    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    b = mesh["bounds"]
    metrics["stale_bounds"] = bool(list(lo) != list(b["min"]) or list(hi) != list(b["max"]))
    if metrics["stale_bounds"]:
        add("bounds", "error", "declared bounds differ from the triangle extents")

    span = [(b["max"][i] - b["min"][i]) / q for i in range(3)]
    metrics["span_ldu"] = [round(v, 1) for v in span]
    fp = _title_footprint(mesh.get("title"))
    if fp and PLAIN_FAMILY.match(mesh.get("title", "")):
        w, d = fp[0] * 20, fp[1] * 20
        ok = (abs(span[0] - w) < 1 and abs(span[2] - d) < 1) or (abs(span[0] - d) < 1 and abs(span[2] - w) < 1)
        if not ok:
            add("footprint", "error", "title says %dx%d studs but x/z extent is %.0fx%.0f LDU" % (fp[0], fp[1], span[0], span[2]))

    c = mesh["connectors"]
    metrics.update(studs=len(c["studs"]), sockets=len(c["sockets"]), holes=len(c["holes"]), pins=len(c["pins"]))
    pad = 1.0
    for kind in ("studs", "sockets"):
        for k in c[kind]:
            p = [v / q for v in k["pos"]]
            if not all(b["min"][i] / q - pad <= p[i] <= b["max"][i] / q + pad for i in range(3)):
                add("connectors", "error", "%s at %s lies outside the bounds" % (kind[:-1], [round(v) for v in p]))
                break
    if fp and PLAIN_FAMILY.match(mesh.get("title", "")) and re.match(r"^\s*(Brick|Plate)", mesh["title"], re.I):
        if len(c["studs"]) != fp[0] * fp[1]:
            add("connectors", "error", "plain %dx%d part has %d studs (expected %d)" % (fp[0], fp[1], len(c["studs"]), fp[0] * fp[1]))

    occ = mesh.get("occupancy")
    metrics["occupancy_boxes"] = len(occ) if occ else 0
    if occ:
        tol = 0.5 * q
        for bx in occ:
            x0, x1, y0, y1, z0, z1 = bx                              # raw LDU (not quantised), unlike the connectors
            lo3 = [b["min"][i] / q - 0.5 for i in range(3)]
            hi3 = [b["max"][i] / q + 0.5 for i in range(3)]
            if x0 < lo3[0] or x1 > hi3[0] or y0 < lo3[1] or y1 > hi3[1] or z0 < lo3[2] or z1 > hi3[2] or x1 <= x0 or y1 <= y0 or z1 <= z0:
                add("occupancy", "error", "occupancy box %s is empty or lies outside the part bounds" % [round(v, 1) for v in bx])
                break
        pts = []
        for x0, x1, y0, y1, z0, z1 in occ:
            g = lambda a, z: np.linspace(a + 0.5, z - 0.5, OCC_SAMPLES) if z - a > 1.0 else np.array([(a + z) / 2])  # noqa: E731
            X, Y, Z = np.meshgrid(g(x0, x1), g(y0, y1), g(z0, z1), indexing="ij")
            pts.append(np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1))
        pts = np.concatenate(pts)
        if len(pts) > 6000:
            pts = pts[np.linspace(0, len(pts) - 1, 6000).astype(int)]
        out_frac = float(1 - inside_points(Tf, pts).mean())
        metrics["occupancy_outside_frac"] = round(out_frac, 4)
        if out_frac > OCC_OUTSIDE_WARN:
            add("occupancy", "warn", "%.0f%% of the occupancy volume lies outside the mesh (much larger than the part?)" % (100 * out_frac))
    return findings, metrics


def check_id(pid, parts_dir=PARTS):
    return check_part(load(pid, parts_dir))


if __name__ == "__main__":
    import sys
    ids = sys.argv[1:] or sorted(json.loads((PARTS / "index.json").read_text())["parts"])
    for pid in ids:
        f, m = check_id(pid)
        print("%-8s %s  %s" % (pid, "ERR " if any(x["level"] == "error" for x in f) else ("warn" if f else "ok  "),
                              "; ".join("%s: %s" % (x["check"], x["msg"]) for x in f)[:150]))
