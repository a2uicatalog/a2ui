"""Minifig character templates for brick_build_3d (brick-parts Phase 6, preview).

Each template names one real LDraw part per minifig slot (headgear, head print, torso print, arms, hands, hips,
legs, optional back/hand accessory) plus LDraw colour codes. `template_dat` assembles them into a synthetic LDraw
model at the standard minifig offsets, and bake_parts.py bakes that like any other part into
public/parts/mf-<id>.json, so a character is ONE partsModel entry ({p: "mf-knight", ...}) that the renderer
already knows how to draw, rotate and step.

Frame: the torso's own LDraw frame (origin at the top centre of the torso, the neck; Y down), turned 180 degrees
about Y so the figure faces +Z. LDraw minifigs face -Z, but brick_build_3d's camera looks at a model's +Z side, so
this way a character placed with r=0 shows its face. The feet sit at y=+72, so standing a character on a
baseplate means placing it at y=-72; on top of a brick whose top is at y=T, at y=T-72.

Offsets are measured, not remembered: they are the unposed "standing" placements used by the LDraw Official Model
Repository files 6597-1 (hands) and 6080-1 (everything else), re-expressed relative to the torso.

Occupancy is deliberately under-approximated (spec section 3: under-approximation is always safe): one box for
the legs and hips (the part that stands on studs) and one for the torso and head column. Arms, hands, headgear
and accessories are cosmetic for collision purposes. The legs have two anti-stud holes, so a character stands
on a 1x2 stud pair: two downward sockets at (+-10, 72, 0).
"""

# Colour codes (LDraw): 0 black, 1 blue, 2 green, 4 red, 6 brown, 7 light grey, 8 dark grey, 14 yellow,
# 15 white, 19 tan, 25 orange, 70 reddish brown, 71 light bluish grey, 72 dark bluish grey, 272 dark blue,
# 320 dark red, 334 chrome gold (drawn as its base colour), 383 chrome silver.
SKIN = 14

# (x, y, z, 3x3 row-major rotation) per slot, in the torso's LDraw frame (facing -Z); template_dat turns the
# assembled figure to face +Z.
_I = (1, 0, 0, 0, 1, 0, 0, 0, 1)
OFFSETS = {
    "torso": (0, 0, 0, _I),
    "hips": (0, 32, 0, _I),
    "leg_r": (0, 44, 0, _I),
    "leg_l": (0, 44, 0, _I),
    "arm_r": (-15.552, 9, 0, (0.985, -0.17, 0, 0.17, 0.985, 0, 0, 0, 1)),
    "arm_l": (15.552, 9, 0, (0.985, 0.17, 0, -0.17, 0.985, 0, 0, 0, 1)),
    "hand_r": (-23.5, 26, -10.1, (0.985, -0.121, 0.121, 0.171, 0.694, -0.699, 0.001, 0.709, 0.705)),
    "hand_l": (23.5, 26, -10.1, (0.985, 0.121, -0.121, -0.171, 0.694, -0.699, 0.001, 0.709, 0.705)),
    "head": (0, -24, 0, _I),
    "headgear": (0, -24, 0, _I),
    "back": (0, 0, 0, _I),          # capes and quivers: their LDraw origin is the torso's neck
}
FEET_Y = 72

# Back accessories whose LDraw frame faces the other way: a quiver is modelled facing -Z like the torso, so it is
# turned 180 degrees to sit on the back (as 6080-1 places it). Capes are already modelled hanging behind.
SLOT_ROTATION = {("back", "4498"): (-1, 0, 0, 0, 1, 0, 0, 0, -1)}

# Standard parts per slot; a template overrides only what differs.
DEFAULT_PARTS = {"torso": "973", "hips": "3815", "leg_r": "3816", "leg_l": "3817", "arm_r": "3818",
                 "arm_l": "3819", "hand_r": "3820", "hand_l": "3820", "head": "3626bp01"}

# name, tags (search words), and slot -> (part, colour). `torso`/`legs`/`arms`/`hands` colour shorthands fan out.
TEMPLATES = [
    {"id": "knight", "name": "Castle knight", "tags": ["castle", "medieval", "soldier", "armour", "helmet"],
     "torso": ("973p42", 15), "arms": 15, "legs": 0, "hips": 0, "head": ("3626bp01", SKIN),
     "headgear": ("3896", 71)},
    {"id": "lion-knight", "name": "Lion knight", "tags": ["castle", "medieval", "royal", "armour", "lion"],
     "torso": ("973p4f", 1), "arms": 1, "legs": 1, "hips": 0, "headgear": ("4503", 71)},
    {"id": "king", "name": "King", "tags": ["castle", "royal", "crown", "medieval", "cape", "ruler"],
     "torso": ("973p4j", 272), "arms": 272, "legs": 272, "hips": 272, "head": ("3626bp0a", SKIN),
     "back": ("4524", 4)},
    {"id": "forestman", "name": "Forestman", "tags": ["castle", "archer", "outlaw", "forest", "robin hood"],
     "torso": ("973p46", 2), "arms": 2, "legs": 70, "hips": 70, "head": ("3626bp03", SKIN),
     "headgear": ("3901", 70), "back": ("4498", 70)},
    {"id": "wizard", "name": "Wizard", "tags": ["magic", "castle", "sorcerer", "hat", "fantasy"],
     "torso": ("973", 272), "arms": 272, "legs": 272, "hips": 272, "head": ("3626bp0e", SKIN),
     "headgear": ("6131", 272), "back": ("4524", 272)},
    {"id": "astronaut", "name": "Classic space astronaut", "tags": ["space", "spaceman", "helmet", "sci-fi"],
     "torso": ("973p90", 4), "arms": 4, "legs": 4, "hips": 4, "headgear": ("3842a", 4)},
    {"id": "pirate", "name": "Pirate", "tags": ["pirate", "sailor", "stripes", "sea"],
     "torso": ("973p31", 15), "arms": 15, "legs": 1, "hips": 1, "head": ("3626bp0c", SKIN),
     "headgear": ("3901", 6)},
    {"id": "pirate-captain", "name": "Pirate captain", "tags": ["pirate", "captain", "sea", "ship"],
     "torso": ("973p36", 1), "arms": 1, "legs": 0, "hips": 0, "head": ("3626bp03", SKIN),
     "headgear": ("2528", 0)},
    {"id": "police", "name": "Police officer", "tags": ["town", "city", "police", "cop", "officer"],
     "torso": ("973p1f", 0), "arms": 0, "legs": 0, "hips": 0, "head": ("3626bp04", SKIN),
     "headgear": ("3624", 0)},
    {"id": "firefighter", "name": "Firefighter", "tags": ["town", "city", "fire", "rescue", "helmet"],
     "torso": ("973p21", 0), "arms": 0, "legs": 0, "hips": 0, "head": ("3626bp05", SKIN),
     "headgear": ("3834", 15)},
    {"id": "chef", "name": "Chef", "tags": ["town", "city", "cook", "kitchen", "food", "restaurant"],
     "torso": ("973p2a", 15), "arms": 15, "legs": 0, "hips": 0, "head": ("3626bp05", SKIN),
     "headgear": ("3898", 15)},
    {"id": "builder", "name": "Construction worker", "tags": ["town", "city", "construction", "builder", "worker",
                                                                "hard hat"],
     "torso": ("973p13", 1), "arms": 1, "legs": 1, "hips": 1, "head": ("3626bp07", SKIN),
     "headgear": ("3833", 14)},
    {"id": "scientist", "name": "Scientist", "tags": ["town", "lab", "science", "doctor", "coat"],
     "torso": ("973p0r", 15), "arms": 15, "legs": 71, "hips": 71, "head": ("3626bp09", SKIN),
     "headgear": ("3625", 0)},
    {"id": "cowboy", "name": "Cowboy", "tags": ["western", "wild west", "cowboy", "hat", "sheriff"],
     "torso": ("973p0u", 71), "arms": 70, "legs": 19, "hips": 19, "head": ("3626bp0c", SKIN),
     "headgear": ("3629", 70)},
    {"id": "gentleman", "name": "Gentleman", "tags": ["town", "suit", "top hat", "victorian", "formal"],
     "torso": ("973p18", 0), "arms": 0, "legs": 0, "hips": 0, "head": ("3626bp03", SKIN),
     "headgear": ("3878", 0)},
    {"id": "plain", "name": "Plain minifig", "tags": ["basic", "classic", "blank", "smiley"],
     "torso": ("973", 4), "arms": 4, "legs": 1, "hips": 1, "headgear": ("3901", 6)},
]


def template_slots(t):
    """Expand a template into {slot: (part, colour)} for every slot it uses."""
    torso_part, torso_c = t["torso"]
    arms = t.get("arms", torso_c)
    legs = t.get("legs", 1)
    slots = {
        "torso": (torso_part, torso_c),
        "hips": (DEFAULT_PARTS["hips"], t.get("hips", legs)),
        "leg_r": (DEFAULT_PARTS["leg_r"], legs),
        "leg_l": (DEFAULT_PARTS["leg_l"], legs),
        "arm_r": (DEFAULT_PARTS["arm_r"], arms),
        "arm_l": (DEFAULT_PARTS["arm_l"], arms),
        "hand_r": (DEFAULT_PARTS["hand_r"], t.get("hands", SKIN)),
        "hand_l": (DEFAULT_PARTS["hand_l"], t.get("hands", SKIN)),
        "head": t.get("head", (DEFAULT_PARTS["head"], SKIN)),
    }
    for slot in ("headgear", "back"):
        if slot in t:
            slots[slot] = t[slot]
    return slots


def character_id(t):
    return "mf-" + t["id"]


def _num(v):
    return "0" if v == 0 else "%g" % v    # no "-0" in the generated file


def template_dat(t):
    """The synthetic LDraw model text for template `t` (fed to resolve.py through Library.add_virtual)."""
    lines = ["0 %s" % t["name"], "0 Name: %s.dat" % character_id(t),
             "0 !LICENSE Licensed under CC BY 4.0 : see CAreadme.txt", "0 BFC CERTIFY CCW"]
    for slot, (part, colour) in template_slots(t).items():
        x, y, z, m = OFFSETS[slot]
        m = SLOT_ROTATION.get((slot, part), m)
        # face +Z: pre-multiply by a 180-degree turn about Y, diag(-1, 1, -1), which negates rows 0 and 2
        x, z, m = -x, -z, (-m[0], -m[1], -m[2], m[3], m[4], m[5], -m[6], -m[7], -m[8])
        lines.append("1 %d %s %s %s %s %s.dat" % (colour, _num(x), _num(y), _num(z), " ".join(_num(v) for v in m), part))
    return "\n".join(lines) + "\n"


def occupancy_and_sockets():
    """Shared by every template (same body geometry): legs+hips box, torso+head column, two feet sockets."""
    occ = [(-20, 20, 32, FEET_Y, -10, 10),      # hips and legs: 2x1 studs footprint
           (-10, 10, -24, 32, -8, 8)]           # torso centre and head column (arms/headgear cosmetic)
    sockets = [((-10, FEET_Y, 0), (0, 1, 0)), ((10, FEET_Y, 0), (0, 1, 0))]
    return occ, sockets


def search(query, templates=TEMPLATES):
    """Case-insensitive match on name/id/tags; every word of the query must match something. Empty -> all."""
    words = [w for w in query.lower().split() if w]
    out = []
    for t in templates:
        hay = " ".join([t["id"], t["name"].lower()] + t["tags"]).lower()
        if all(w in hay for w in words):
            out.append(t)
    return out
