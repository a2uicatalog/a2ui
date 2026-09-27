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
# A proportion- and palette-accurate stand-in for the real reference this whole project started from: Victor
# Mustar's "Microduck" booklet (huggingface.co/buckets/victor/microduck-lego-booklet) is NOT a bird -- it's Pollen
# Robotics' small biped robot (dome helmet head with a big round "eye"/visor, boxy torso, two jointed robot legs
# with flared feet), 1113 real parts / 243 steps, 27cm tall x 14cm wide x 12cm deep, in exactly 6 real LEGO
# colours (found and confirmed 2026-09-27 by reading the actual PDF -- the old version of this function built an
# organic bird shape that shares nothing with the reference it was named after). This is NOT a step-for-step
# transcription of the real booklet (no machine-readable source exists, only 138 page images) -- it is a fresh
# shape built at the real model's proportions and colours, in this repo's own voxel-to-brick style. Real height
# 27cm / 9.6mm per brick-layer =~ 28 layers; 14cm / 8mm per stud =~ 17-18 studs wide -- used as the scale target.
BOT_WHITE, BOT_ORG, BOT_BLORG, BOT_DGRY, BOT_LGRY, BOT_BLK = "#f2f3f2", "#fe8a18", "#f8ab3d", "#59605f", "#a3a2a4", "#1b1b1b"


def duck():
    S = {}
    # Torso: a boxy white body with an orange belt and a dark centre seam, y13-19.
    for x in range(-6, 7):
        for y in range(13, 20):
            for z in range(-3, 4):
                if abs(x) <= 6 and abs(z) <= 3: S[(x, y, z)] = BOT_WHITE
    for x in range(-6, 7):                                   # belt stripe
        for z in (-3, 3): S[(x, 15, z)] = BOT_ORG
        for z in range(-2, 3): S[(x, 15, z)] = BOT_ORG if abs(x) == 6 else S.get((x, 15, z), BOT_ORG)
    for y in range(13, 20): S[(0, y, 3)] = BOT_DGRY          # centre seam, front face
    for sx in (-1, 1):                                       # shoulder stubs
        for y in range(17, 19):
            for x in range(6, 8): S[(sx * x, y, 0)] = BOT_DGRY
        S[(sx * 7, 17, 0)] = BOT_BLK                          # shoulder joint dot
    # Neck: a narrow grey collar, y20-21.
    for x in range(-3, 4):
        for y in (20, 21):
            for z in range(-2, 3): S[(x, y, z)] = BOT_LGRY
    # Head: a rounded white dome (hemisphere-ish, narrower at the neck, widest a third of the way up, rounding
    # inward at the crown) with a front orange visor band and a big round orange "eye" with a black pupil --
    # the real robot's most recognisable feature, and the reason it reads as duck-billed/beaked at a glance.
    head = {}
    for x in range(-7, 8):
        for y in range(22, 29):
            for z in range(-6, 7):
                if ell(x, y, z, 0, 24, 0, 7.2, 5.0, 6.6): head[(x, y, z)] = BOT_WHITE
    zf = front_z(head)
    for x in range(-3, 4):                                  # visor band across the lower-front of the dome
        for y in (22, 23):
            z = zf.get((x, y))
            if z is not None: head[(x, y, z)] = BOT_BLORG
    eye = {}
    for x in range(-2, 3):                                  # the big round eye, centred on the visor band
        for y in (23, 24, 25):
            if ell(x, y, 0, 0, 24, 0, 2.4, 1.6, 1): eye[(x, y)] = BOT_ORG
    for x, y in [(0, 24)]: eye[(x, y)] = BOT_BLK             # pupil, dead centre
    for (x, y), c in eye.items():
        z = zf.get((x, y))
        if z is not None: head[(x, y, z)] = c
    S.update(head)

    def legs_and_feet(V):                                    # added after hollowing so the floor rests on them
        for sx in (-1, 1):
            cx = sx * 4
            for y in range(3, 11):                           # legs: grey, tapering slightly is skipped for
                for x in range(cx - 1, cx + 2):               # simplicity -- a plain column reads fine at this
                    for z in range(0, 3): V[(x, y, z)] = BOT_LGRY if y < 7 else BOT_DGRY
            V[(cx, 6, 1)] = BOT_BLK                            # knee joint dot
            for x in range(cx - 2, cx + 3):                   # hip bridge over the leg gap
                for z in range(0, 3): V[(x, 11, z)] = BOT_DGRY
                for z in range(0, 3): V[(x, 12, z)] = BOT_DGRY
            for x in range(cx - 3, cx + 4):                   # flared foot -- wider than the leg above it, the
                for z in range(-2, 5):                        # single detail that most reads as "duck feet"
                    if abs(x - cx) <= (3 if z >= 0 else 1): V[(x, 0, z)] = BOT_ORG; V[(x, 1, z)] = BOT_ORG
            for x in range(cx - 3, cx + 4):
                for z in range(-2, 5):
                    if abs(x - cx) <= (3 if z >= 0 else 1): V[(x, 2, z)] = BOT_ORG
    return build(S, "microduck", do_hollow=False, post=legs_and_feet, out_dir=OUT)


for name, fn in (("tower", tower), ("sorting_hat", hat), ("snitch", snitch), ("microduck", duck)):
    if not ONLY or name in ONLY: fn()
