"""blender_view_math -- pure, dependency-free math for the offline Blender render pipeline
(scripts/brick_models/render_blender.py). Port of scripts/brick_models/threejs_view_math.js's own math to
Python, for the SAME reason that file exists standalone: testable with nothing but the standard library, no
bpy import anywhere in this file, so tests/test_blender_view_math.py can run without Blender installed at all.

PART_ROT below is a GENERATED block (see gen_part_rot_table.py), not hand-typed -- it is the 5th twin of the
24-entry rotation table atoms_brick.gs/brick_parts_validate.py/threejs_view_math.js/omr-import.js already hand-
keep in sync ("edit all four together, in the same order"). Generating this one from
renderers/brick_parts_validate.py's own PART_ROT (already Python, already the same flat row-major shape) avoids
adding a SIXTH hand-copied twin that could silently drift -- run `python3 scripts/brick_models/gen_part_rot_table.py`
to refresh it after editing the source table; tests/test_blender_view_math.py asserts the checked-in block
matches a fresh run.

Coordinate-convention note (read before touching rotate/to_world): this file deliberately does NOT hard-code
three.js's own fix for where the LDraw Y-down mirror belongs (threejs_view_math.js's tjsToWorld/
tjsInstanceMatrixRowMajor comment: the mirror must live on the object's own transform, never baked per-instance,
because of three.js's specific matrixWorld-determinant winding check). Blender's own normal/winding/instancing
model is different, and that three.js-specific reasoning does not automatically transfer. `to_world` here applies
the SAME numeric transform (divide by quant, rotate, translate, scale by 1/20, negate Y) as a single combined
function -- exactly like tjsToWorld does -- and `instance_matrix` returns the pre-D matrix split out exactly like
tjsInstanceMatrixRowMajor does, for render_blender.py to compose with whatever object-level transform the Step 4
empirical winding test (see render_blender.py's own top-of-file comment once that test has been run) determines
is actually correct in Blender.
"""
import math

# BEGIN GENERATED PART_ROT -- do not hand-edit; run gen_part_rot_table.py to refresh from
# renderers/brick_parts_validate.py's PART_ROT.
PART_ROT = [
    (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0),
    (-1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, -1.0),
    (0.0, 0.0, -1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0),
    (-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0),
    (-1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -1.0, 0.0),
    (-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0),
    (0.0, -1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, -1.0),
    (0.0, -1.0, 0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 0.0),
    (0.0, -1.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0),
    (0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, -1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 0.0),
    (0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
    (0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
    (0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    (0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0),
    (1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, -1.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0),
]
# END GENERATED PART_ROT


def rot(r, p):
    """Twin of tjsRot(r,p): apply PART_ROT[r] to a local point p=(x,y,z)."""
    m = PART_ROT[r]
    return (
        m[0] * p[0] + m[1] * p[1] + m[2] * p[2],
        m[3] * p[0] + m[4] * p[1] + m[5] * p[2],
        m[6] * p[0] + m[7] * p[1] + m[8] * p[2],
    )


def to_world(p, q, r, inst_pos):
    """Twin of tjsToWorld(p,q,r,instPos): local part-mesh vertex (LDU, quant-scaled) -> world unit, for one
    instance at LDU position inst_pos with rotation index r. Divides by quant q, rotates by PART_ROT[r], adds
    the instance's LDU translation, then scales by 1/20 and negates Y (LDraw Y-down -> Y-up target
    convention) -- the SAME two-stage transform tjsToWorld applies, combined into one function exactly the
    same way. See this module's own top-of-file comment: whether Blender needs this same "always negate Y"
    answer, or something else (e.g. no negation, with an object-level transform elsewhere instead) is decided
    empirically, not assumed here -- this function returns the three.js answer as the STARTING point.
    """
    rp = rot(r, (p[0] / q, p[1] / q, p[2] / q))
    return (
        (rp[0] + inst_pos[0]) / 20,
        -(rp[1] + inst_pos[1]) / 20,
        (rp[2] + inst_pos[2]) / 20,
    )


def instance_matrix(r, inst_pos, q):
    """Twin of tjsInstanceMatrixRowMajor(r,instPos,q): row-major 4x4 nested-list matrix (directly consumable
    by mathutils.Matrix(rows) in Blender), deliberately NOT including to_world's D=diag(1/20,-1/20,1/20)
    scale/flip -- only the part's own rotation R(r), its quant scale, and the instance's LDU translation:
    worldPreD = R(r)*(p/q) + instPos. D belongs on the object-level transform instead, mirroring
    tjsInstanceMatrixRowMajor's own reasoning (see this module's top-of-file comment for why that specific
    three.js reasoning is NOT assumed to transfer unchanged, only the SAME split-out shape is kept so
    render_blender.py can compose it with whatever Step 4's empirical test determines).
    """
    m = PART_ROT[r]
    s = 1.0 / q
    return [
        [m[0] * s, m[1] * s, m[2] * s, inst_pos[0]],
        [m[3] * s, m[4] * s, m[5] * s, inst_pos[1]],
        [m[6] * s, m[7] * s, m[8] * s, inst_pos[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    length = math.sqrt(_dot(a, a)) or 1.0
    return (a[0] / length, a[1] / length, a[2] / length)


def fit_camera(box_min, box_max, direction, fov_y_deg, aspect, margin=1.15):
    """Direct port of tjsFitCamera -- see threejs_view_math.js's own comment for the full algorithm
    rationale (corner-projection onto the camera's own right/up basis, not a bounding-sphere heuristic).
    Returns a dict: {position, target, distance, near, far, ortho:{half_w, half_h}}. Pure, coordinate-system-
    agnostic math -- works identically whether box_min/box_max are in three.js's Y-up convention or whatever
    Blender's own convention turns out to be, since it only ever projects onto direction/right/up, never
    assumes a specific up axis beyond world_up=(0,1,0) matching whatever convention the caller's boxes use.
    """
    center = (
        (box_min[0] + box_max[0]) / 2,
        (box_min[1] + box_max[1]) / 2,
        (box_min[2] + box_max[2]) / 2,
    )
    unit_dir = _norm(direction)
    forward = (-unit_dir[0], -unit_dir[1], -unit_dir[2])
    world_up = (0.0, 1.0, 0.0)
    right = _cross(forward, world_up)
    right = (1.0, 0.0, 0.0) if _dot(right, right) < 1e-8 else _norm(right)
    up = _norm(_cross(right, forward))
    corners = [
        (box_min[0], box_min[1], box_min[2]), (box_max[0], box_min[1], box_min[2]),
        (box_min[0], box_max[1], box_min[2]), (box_max[0], box_max[1], box_min[2]),
        (box_min[0], box_min[1], box_max[2]), (box_max[0], box_min[1], box_max[2]),
        (box_min[0], box_max[1], box_max[2]), (box_max[0], box_max[1], box_max[2]),
    ]
    half_w = 0.0
    half_h = 0.0
    for corner in corners:
        v = _sub(corner, center)
        half_w = max(half_w, abs(_dot(v, right)))
        half_h = max(half_h, abs(_dot(v, up)))
    half_fov_y = math.radians(fov_y_deg) / 2
    half_fov_x = math.atan(math.tan(half_fov_y) * aspect)
    dist = margin * max(half_h / math.tan(half_fov_y), half_w / math.tan(half_fov_x), 0.5)
    return {
        "position": (
            center[0] + unit_dir[0] * dist,
            center[1] + unit_dir[1] * dist,
            center[2] + unit_dir[2] * dist,
        ),
        "target": center,
        "distance": dist,
        "near": max(dist / 100, 0.1),
        "far": dist * 10,
        "ortho": {"half_w": half_w * margin, "half_h": half_h * margin},
    }


# LDraw finish -> Blender Principled BSDF input values. Twin (in spirit, not byte-for-byte, since the target
# shader model differs) of build_design_page.py's materialForCode -- see that function's own comments for WHY
# each finish maps the way it does (chrome/metal/pearlescent clearcoat values, trans-clear real transmission
# over flat alpha). Blender's Principled BSDF has no direct analogue of MeshPhysicalMaterial's `thickness`
# (a fake absorption-depth hint three.js uses since it isn't tracing real refraction through solid geometry)
# -- Cycles computes transmission through the mesh's REAL volume instead, so there is no missing input to
# work around here, only a real parameter three.js had to fake.
def material_params_for_code(code, colour_table):
    """Returns a plain dict of Principled-BSDF-shaped values for an LDraw colour code -- no bpy objects
    created here, keeping this module 100% bpy-free. render_blender.py turns this dict into real Blender
    material nodes."""
    info = colour_table.get(str(code)) or colour_table.get(code)
    hex_colour = (info or {}).get("hex") or "#c91a09"
    finish = (info or {}).get("finish")
    alpha = (info or {}).get("alpha", 255)
    base = {"base_color_hex": hex_colour, "metallic": 0.05, "roughness": 0.85}
    if not info:
        return base
    if finish == "chrome":
        return {"base_color_hex": hex_colour, "metallic": 1.0, "roughness": 0.08,
                "coat_weight": 1.0, "coat_roughness": 0.05}
    if finish == "metal":
        return {"base_color_hex": hex_colour, "metallic": 0.9, "roughness": 0.25}
    if finish == "pearlescent":
        return {"base_color_hex": hex_colour, "metallic": 0.35, "roughness": 0.22,
                "coat_weight": 0.6, "coat_roughness": 0.2}
    if alpha < 255:
        return {"base_color_hex": hex_colour, "metallic": 0.0, "roughness": 0.04,
                "transmission_weight": 1.0, "ior": 1.5,
                "coat_weight": 1.0, "coat_roughness": 0.05}
    return base
