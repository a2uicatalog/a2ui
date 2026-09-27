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
# Victor Mustar's "Microduck" booklet (huggingface.co/buckets/victor/microduck-lego-booklet) is NOT a bird -- it's
# Pollen Robotics' small biped robot (dome-helmet head with a big round "eye"/visor, boxy torso, two jointed robot
# legs with flared feet, NO ARMS -- the real robot picks things up with its beak), 1113 real parts / 243 steps,
# 27cm tall x 14cm wide x 12cm deep, in exactly 6 real LEGO colours. The 2026-09-27 rewrite of this function was a
# proportion/palette-accurate stand-in built from the parts-list TEXT alone (never having viewed a single page
# image); THIS version was built after actually reading the booklet's own clean reference renders -- the cover
# (p1), the "build overview" full-figure render (p4), and each section's own finished-sub-assembly picture (Trunk
# p5, Left foot p28, Left shin p33, Left thigh p41, Left leg p48, Head p79, Neck p116, Final assembly p126) -- so
# shape AND colour per body part are now matched to the real geometry, not guessed from a one-line description.
# Two real fixes the text-only version got backwards: the eye is BRIGHT LIGHT ORANGE with the head's own
# lower-shell band in plain ORANGE (the old code had these swapped), and the trunk carries NO orange at all --
# it's white/black/grey (section 1's own subtitle: "White shell, dark grey battery, black base, grey hip
# brackets"); the old code's orange "belt" and shoulder-stub "arms" were both inventions with no basis in the
# reference. Still not a literal step-for-step transcription (that needs reading all 243 individual steps, a real
# multi-session undertaking with no machine-readable source -- only page images exist) -- the leg is a straight
# column rather than the real model's bent-knee pose, and exact stud-level part choices are this repo's own
# generic tiler, not the booklet's real part IDs. Real height 27cm / 9.6mm per brick-layer =~ 28 layers; 14cm /
# 8mm per stud =~ 17-18 studs wide -- used as the scale target, matched by y0-29 below.
BOT_WHITE, BOT_ORG, BOT_BLORG, BOT_DGRY, BOT_LGRY, BOT_BLK = "#f2f3f2", "#fe8a18", "#f8ab3d", "#59605f", "#a3a2a4", "#1b1b1b"


def duck():
    S = {}
    # Trunk (p5): white shell, y13-19, with a dark-grey "battery" band low on the front and a black base below
    # it (y12). No orange anywhere on the trunk, and no arms -- both real per the section's own subtitle/photo.
    for x in range(-6, 7):
        for y in range(13, 20):
            for z in range(-3, 4):
                S[(x, y, z)] = BOT_DGRY if y == 14 else BOT_WHITE
    for x in range(-6, 7):                                   # black base, under the trunk
        for z in range(-3, 4): S[(x, 12, z)] = BOT_BLK
    # Neck (p116): dark grey collar, y20-21, with a lighter ring at the top (the joint collar between neck and
    # head visible in the reference).
    for x in range(-3, 4):
        for z in range(-2, 3):
            S[(x, 20, z)] = BOT_DGRY
            S[(x, 21, z)] = BOT_LGRY
    # Head (p79, p1): NOT a hemisphere -- a barrel/arch dome (flat bottom, rounded top, roughly constant
    # cross-section front-to-back, like a covered wagon), tapering slightly only at the very front/back for
    # rounded corners. White shell; a plain-orange lower-shell band and the big bright-light-orange eye (dark
    # centre) are painted on the frontmost surface, the same front_z technique hat() uses for its face.
    head = {}
    HY0, HH, HW = 22, 7, 7                                   # base y, arch height, half-width
    for z in range(-6, 7):
        taper = 0.8 if abs(z) >= 6 else 1.0
        hw = HW * taper
        for x in range(-7, 8):
            if abs(x) > hw: continue
            top = HY0 + HH * math.sqrt(max(0.0, 1 - (x / hw) ** 2)) * taper
            for y in range(HY0, int(round(top)) + 1):
                head[(x, y, z)] = BOT_WHITE
    zf = front_z(head)
    for x in range(-4, 5):                                  # lower-shell band across the front of the dome
        for y in (HY0, HY0 + 1):
            z = zf.get((x, y))
            if z is not None: head[(x, y, z)] = BOT_ORG
    eye = {}
    for x in range(-2, 3):                                  # the big round eye, centred on the lower-shell band
        for y in (HY0 + 1, HY0 + 2, HY0 + 3):
            if ell(x, y, 0, 0, HY0 + 2, 0, 2.4, 1.6, 1): eye[(x, y)] = BOT_BLORG
    eye[(0, HY0 + 2)] = BOT_BLK                              # pupil, dead centre
    for (x, y), c in eye.items():
        z = zf.get((x, y))
        if z is not None: head[(x, y, z)] = c
    S.update(head)

    def legs_and_feet(V):                                    # added after hollowing so the floor rests on them
        for sx in (-1, 1):
            cx = sx * 4
            for y in range(9, 12):                           # thigh (p41): white shell + a dark-grey knee-servo
                for x in range(cx - 1, cx + 2):               # accent on the column's inner (body-facing) side
                    inner = x == (cx - 1 if sx > 0 else cx + 1)
                    for z in range(0, 3): V[(x, y, z)] = BOT_DGRY if inner else BOT_WHITE
            for y in range(3, 9):                            # shin (p33): grey link with a lighter top cap
                for x in range(cx - 1, cx + 2):               # (the ankle-servo detail)
                    for z in range(0, 3): V[(x, y, z)] = BOT_LGRY if y >= 8 else BOT_DGRY
            for x in range(cx - 2, cx + 3):                   # hip bridge over the leg gap (grey hip brackets)
                for z in range(0, 3): V[(x, 11, z)] = BOT_DGRY
                for z in range(0, 3): V[(x, 12, z)] = BOT_DGRY
            for x in range(cx - 3, cx + 4):                   # foot (p28): orange body on a bright-light-orange
                for z in range(-2, 5):                        # sole, a stepped/flared footprint -- the single
                    if abs(x - cx) <= (3 if z >= 0 else 1):    # detail that most reads as a chunky robot foot
                        V[(x, 0, z)] = BOT_BLORG
                        V[(x, 1, z)] = BOT_ORG
            for x in range(cx - 3, cx + 4):
                for z in range(-2, 5):
                    if abs(x - cx) <= (3 if z >= 0 else 1): V[(x, 2, z)] = BOT_ORG
            for x in (cx - 2, cx + 2):                        # raised back corner nubs (the ankle-post look)
                V[(x, 3, -1)] = BOT_ORG
    return build(S, "microduck", do_hollow=False, post=legs_and_feet, out_dir=OUT)


for name, fn in (("tower", tower), ("sorting_hat", hat), ("snitch", snitch), ("microduck", duck)):
    if not ONLY or name in ONLY: fn()
