import math, sys
from brickgen import build, ell

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
ONLY = set(sys.argv[2:])

GREY, GREY2, DARK, SLATE = "#a3a2a4", "#8b8d8f", "#6d6e5c", "#3b4a5a"
YEL, ORG, BLK, RED, BRN, WHITE, GOLD = "#f2cd37", "#fe8a18", "#1b2a34", "#c91a09", "#6b2f1a", "#f2f3f2", "#e0a800"


def front_z(S, pred=None):
    zf = {}
    for (x, y, z) in S:
        if pred and not pred(x, y, z): continue
        if z > zf.get((x, y), -99): zf[(x, y)] = z
    return zf


# ---------------------------------------------------------------- Hogwarts tower
def tower():
    S = {}
    R = 7
    for y in range(0, 30):                                   # stone courses, alternating greys
        c = GREY if y % 2 == 0 else GREY2
        for x in range(-9, 10):
            for z in range(-9, 10):
                if x * x + z * z <= R * R + 1: S[(x, y, z)] = c
    for y in range(30, 32):                                  # overhanging parapet
        for x in range(-10, 11):
            for z in range(-10, 11):
                r2 = x * x + z * z
                if 30 <= r2 <= 72 and (y == 30 or ((x + z) % 2 == 0)): S[(x, y, z)] = DARK if y == 30 else GREY
    for i, y in enumerate(range(32, 50)):                    # conical slate roof
        r = 9.0 * (1 - i / 18.0)
        for x in range(-10, 11):
            for z in range(-10, 11):
                if x * x + z * z <= r * r + 0.3: S[(x, y, z)] = SLATE if i % 3 else "#2c3846"
    for y in range(50, 56): S[(0, y, 0)] = BRN               # flagpole
    for y in range(53, 56):
        for x in (1, 2): S[(x, y, 0)] = RED                  # pennant
    # windows and door: colour the outer shell on four sides
    outer = {}
    for (x, y, z), c in list(S.items()):
        if y < 30:
            for d, key in (((0, 1), "N"), ((0, -1), "S"), ((1, 0), "E"), ((-1, 0), "W")):
                if (x + d[0], y, z + d[1]) not in S: outer[(x, y, z, key)] = 1
    for (x, y, z, k) in outer:
        u = x if k in "NS" else z
        side = (k == "N")
        if abs(u) <= 1 and ((8 <= y <= 11) or (18 <= y <= 21)) and not (k == "S" and False):
            arch = (y in (11, 21)) and abs(u) == 1
            if not arch: S[(x, y, z)] = YEL
        if k == "N" and abs(x) <= 1 and 0 <= y <= 5 and not (y == 5 and abs(x) == 1): S[(x, y, z)] = BRN
    return build(S, "tower", spine=None, out_dir=OUT)


# ---------------------------------------------------------------- Sorting Hat
def hat():
    S = {}
    HAT, BAND = "#8a5a2b", "#4a2c14"
    for y in range(0, 2):                                    # brim
        for x in range(-12, 13):
            for z in range(-12, 13):
                r = math.hypot(x, z)
                if r <= 11.5 - 0.6 * y and (y == 0 or r <= 10): S[(x, y, z)] = HAT
    H = 24
    for y in range(2, 2 + H):
        t = (y - 2) / H
        r = 7.4 * (1 - t) ** 0.85 + 0.6
        cx = 0.0 if y < 14 else ((y - 14) ** 2) * 0.055      # the tip flops over
        cz = -0.0
        for x in range(-9, 22):
            for z in range(-9, 10):
                if (x - cx) ** 2 + (z - cz) ** 2 <= r * r:
                    S[(x, y, z)] = BAND if y in (7, 8) else HAT
    # face on the front (z+): eyes and a wide mouth
    zf = front_z({k: v for k, v in S.items() if k[1] >= 3}, lambda x, y, z: abs(x) <= 7)
    feat = {}
    for x, y in [(-3, 15), (3, 15), (-3, 14), (3, 14)]: feat[(x, y)] = BLK
    for x, y in [(-5, 10), (-4, 9), (-3, 9), (-2, 9), (-1, 9), (0, 9), (1, 9), (2, 9), (3, 9), (4, 9), (5, 10)]: feat[(x, y)] = BLK
    for x, y in [(-4, 17), (-3, 17), (-2, 16)] + [(2, 16), (3, 17), (4, 17)]: feat[(x, y)] = BLK   # brows
    for (x, y), c in feat.items():
        z = zf.get((x, y))
        if z is not None and S.get((x, y, z)) not in (None, BAND) or (z is not None and (x, y, z) in S): S[(x, y, z)] = c
    return build(S, "sorting_hat", out_dir=OUT)


# ---------------------------------------------------------------- Golden Snitch
def snitch():
    S = {}
    cy = 13
    for x in range(-7, 8):
        for y in range(6, 21):
            for z in range(-7, 8):
                if ell(x, y, z, 0, cy, 0, 5.2, 5.2, 5.2): S[(x, y, z)] = GOLD if abs(y - cy) > 0 else "#f2cd37"
    for y in range(0, 8):                                    # stand
        for x in (-1, 0, 1):
            for z in (-1, 0, 1): S[(x, y, z)] = GREY
    for sx in (-1, 1):                                       # rising wings, each step overlapping the last
        for i in range(0, 11):
            y = cy + 1 + i
            hw = int(round(3.4 * math.sin(math.pi * (i + 0.6) / 12)))    # half-width along z
            x0 = 3 + i * 1                                    # steps outward one stud at a time
            for x in range(x0, x0 + 4):
                for z in range(-hw, hw + 1):
                    S[(sx * x, y, z)] = WHITE if (x - x0) < 3 else GOLD
    return build(S, "snitch", do_hollow=False, out_dir=OUT)


# ---------------------------------------------------------------- Microduck
def duck():
    S = {}
    for x in range(-11, 12):                                 # body
        for y in range(5, 26):
            for z in range(-13, 12):
                if ell(x, y, z, 0, 15, -1, 8.2, 7.8, 9.5): S[(x, y, z)] = YEL
    head = {}
    for x in range(-8, 9):                                   # head
        for y in range(18, 37):
            for z in range(-4, 13):
                if ell(x, y, z, 0, 27.5, 4, 6.6, 7.0, 6.8): head[(x, y, z)] = YEL
    zf = front_z(head)
    for (x, y), c in {(-3, 29): BLK, (3, 29): BLK, (-3, 30): BLK, (3, 30): BLK}.items():
        z = zf.get((x, y))
        if z is not None: head[(x, y, z)] = c                # eyes
    for x in range(-2, 3):                                   # camera above the beak
        for y in (32, 33):
            z = zf.get((x, y))
            if z is not None: head[(x, y, z)] = "#3a3f45"
    S.update(head)
    top = max(k[2] for k in head if k[0] == 0 and k[1] == 27)
    for x in range(-2, 3):                                   # articulated beak: upper and lower halves
        for z in range(top - 1, top + 5):
            S[(x, 28, z)] = ORG; S[(x, 27, z)] = ORG
            if z < top + 4: S[(x, 26, z)] = "#e07800"
    for y in range(15, 20):                                  # tail
        for x in range(-1, 2):
            for z in range(-14, -8): S[(x, y, z)] = YEL
    for sx in (-1, 1):                                       # little wings
        for y in range(12, 19):
            for z in range(-4, 5):
                for x in range(6, 10):
                    if ell(x, y, z, 7, 15, 0, 3.6, 3.6, 4.8): S[(sx * x, y, z)] = "#e6b800"
    def legs(V):                                             # added after hollowing so the body floor rests on them
        for sx in (-1, 1):
            cx = sx * 4
            for y in range(1, 9):
                for x in range(cx - 1, cx + 2):
                    for z in range(-1, 2): V[(x, y, z)] = ORG
            for x in range(cx - 2, cx + 3):
                for z in range(-3, 8):
                    if z <= 4 or abs(x - cx) <= 1: V[(x, 0, z)] = ORG
            for x in range(cx - 2, cx + 3):
                for z in range(-2, 5):
                    if (x, 1, z) not in V: V[(x, 1, z)] = ORG
    return build(S, "microduck", post=legs, out_dir=OUT)


for name, fn in (("tower", tower), ("sorting_hat", hat), ("snitch", snitch), ("microduck", duck)):
    if not ONLY or name in ONLY: fn()
