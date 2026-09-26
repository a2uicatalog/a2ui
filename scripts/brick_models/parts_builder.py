"""Deterministic voxel -> real-LEGO-parts builder (brick-parts Phase 4).

Takes a set of occupied stud-pitch cells {(cx, layer, cz)} (+ optional colour per cell) and tiles every layer
with real 1xN bricks in running bond (orientation alternates per layer so joints never stack), emitting
partsModel entries {p,x,y,z,r,c} in LDU. The result is gated by renderers.brick_parts_validate.validate_parts;
`repair` re-tiles the failing layers with a different bias until the build passes or gives up.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from renderers.brick_parts_validate import validate_parts  # noqa: E402

PITCH, BRICK_H = 20, 24
BRICKS = {4: '3010', 3: '3622', 2: '3004', 1: '3005'}   # 1xN bricks, long axis = local X at r=0
ROT_X, ROT_Z = 0, 1                                       # r=1 is 90 deg about Y: long axis along world Z

# LDraw colour code -> Rebrickable colour id (identity for the common solid colours; entries differ only where
# the two schemes diverge).
LDRAW_TO_REBRICKABLE = {c: c for c in (0, 1, 2, 4, 14, 15, 19, 25, 27, 28, 70, 71, 72, 272, 288, 320, 484)}


def _runs(cells, colour_of=lambda c: 0):
    """Split sorted consecutive ints into runs of length <= 4, also breaking wherever the colour changes."""
    runs, i = [], 0
    while i < len(cells):
        j = i
        while j + 1 < len(cells) and cells[j + 1] == cells[j] + 1 and colour_of(cells[j + 1]) == colour_of(cells[i]):
            j += 1
        start, n = cells[i], j - i + 1
        while n:
            k = min(4, n)
            runs.append((start, k))
            start += k
            n -= k
        i = j + 1
    return runs


def tile_layer(cells, layer, bias=0, colours=None, ly=0):
    """Tile one layer's cells [(cx, cz)] with 1xN bricks. Even layers run along X, odd along Z (flipped by bias)."""
    along_x = (layer + bias) % 2 == 0
    lines = {}
    for cx, cz in cells:
        lines.setdefault(cz if along_x else cx, []).append(cx if along_x else cz)
    out = []
    for line in sorted(lines):
        def colour_of(u, line=line):
            cell = (u, ly, line) if along_x else (line, ly, u)
            return (colours or {}).get(cell, (colours or {}).get('*', 4))
        for start, n in _runs(sorted(lines[line]), colour_of):
            mid = (start + n / 2.0) * PITCH
            fixed = (line + 0.5) * PITCH
            cell = (start, line) if along_x else (line, start)
            out.append((BRICKS[n], mid, fixed, ROT_X, cell) if along_x else (BRICKS[n], fixed, mid, ROT_Z, cell))
    return out


def build_parts(voxels, colours=None, bias=None):
    """voxels: iterable of (cx, layer, cz), layer 0 on the baseplate. colours: {(cx,layer,cz): ldraw_code}.
    bias: {layer: 0|1} orientation overrides used by repair()."""
    bias = bias or {}
    colours = colours or {}
    by_layer = {}
    for cx, ly, cz in voxels:
        by_layer.setdefault(ly, []).append((cx, cz))
    parts = []
    for ly in sorted(by_layer):
        for pid, x, z, r, (cx, cz) in tile_layer(by_layer[ly], ly, bias.get(ly, 0), colours, ly):
            code = colours.get((cx, ly, cz), colours.get('*', 4))
            parts.append({'p': pid, 'x': round(x), 'y': -BRICK_H * (ly + 1), 'z': round(z), 'r': r, 'c': code})
    return parts


def load_meshes(parts, parts_dir=None):
    d = parts_dir or os.path.join(ROOT, 'public', 'parts')
    out = {}
    for pid in {p['p'] for p in parts}:
        with open(os.path.join(d, pid + '.json'), encoding='utf-8') as f:
            out[pid] = json.load(f)
    return out


def validate(parts):
    return validate_parts(parts, load_meshes(parts))


def repair(voxels, colours=None, max_rounds=8):
    """Validate; on failure flip the orientation bias of every layer adjacent to a floating part and retry."""
    bias = {}
    parts = build_parts(voxels, colours, bias)
    report = validate(parts)
    for _ in range(max_rounds):
        if report['ok']:
            break
        layers = {round(-parts[i]['y'] / BRICK_H) - 1 for i in report['floating']}
        if not layers:
            break
        for ly in layers:
            bias[ly] = 1 - bias.get(ly, 0)
        parts = build_parts(voxels, colours, bias)
        report = validate(parts)
    return parts, report


def rebrickable_parts_list(parts):
    """[(part_num, rebrickable_colour_id, qty)] sorted, from a partsModel list."""
    counts = {}
    for p in parts:
        code = p.get('c', 4)
        col = LDRAW_TO_REBRICKABLE.get(code, code) if isinstance(code, int) else 0
        key = (p['p'].rstrip('abcdefghijklmnopqrstuvwxyz') if p['p'][:-1].isdigit() else p['p'], col)
        counts[key] = counts.get(key, 0) + 1
    return sorted((k[0], k[1], n) for k, n in counts.items())


def rebrickable_wanted_csv(parts):
    """Rebrickable 'Import wanted list' CSV."""
    lines = ['Part,Color,Quantity']
    lines += ['%s,%d,%d' % row for row in rebrickable_parts_list(parts)]
    return '\n'.join(lines) + '\n'
