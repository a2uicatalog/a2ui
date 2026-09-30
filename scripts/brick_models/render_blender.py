#!/usr/bin/env python3
"""render_blender -- offline, high-quality Blender (Cycles) render of a real partsModel/BOM, the same data
shape atoms_brick.gs and scripts/brick_models/build_design_page.py's Three.js viewer already consume. Produces
a still hero image and a turntable video. v1 scope: standalone script, output-only (see
scripts/brick_models/requirements-blender.txt and the plan this was built from for the full reasoning).

Requires bpy (scripts/brick_models/requirements-blender.txt) -- run via the SAME Python that has it installed,
not necessarily Blender's own bundled interpreter, since the bpy PyPI wheel is a real, pip-installable module:
    .venv/bin/python3 scripts/brick_models/render_blender.py --parts-model bom.json --parts-dir public/parts \\
        --colours public/bricksdemo/ldraw_colours_full.json --out-dir public/bricksdemo/renders/<set_id>

WINDING/MIRROR (read before touching build_scene): confirmed empirically 2026-09-30 against
public/parts/4744p0m.json (a real printed part with 4 distinct triangle-colour groups -- an asymmetric graphic
makes a wrong winding/mirror immediately visible, unlike a plain symmetric brick). All three candidate
WINDING_MODE variants ('swap', 'mirror', 'doubleside') rendered the printed tie graphic identically and
correctly (right-side-up, not mirrored, proper outer-shell shape, correctly lit -- not flat/dark, which a
flipped shading normal would show). This means, for real baked part data, Cycles' own shading does not
visibly break under either handedness the way WebGL's explicit face-culling does in three.js -- Blender/Cycles
appears to auto-correct the shading normal for a backface by default rather than showing it mis-lit. Given all
three are empirically correct, chose 'doubleside' (materials render both faces, no culling at all) as the
MORE ROBUST option going forward: it has no dependency on every baked part's triangle winding being globally
consistent with the (a,c,b) swap assumption, which was only independently verified for three.js's OWN specific
WebGL culling behaviour (build_design_page.py's own comment), not re-derived for Blender's rendering model --
it just always works, regardless of a given part's own winding. This is the SAME empirical-not-assumed
discipline scripts/brick_models/threejs_view_math.js's own Y-flip fix used; it happened to reach a different
concrete answer (no culling needed at all) because Blender's rendering model genuinely differs from three.js's,
exactly the reason this was verified independently instead of copy-pasting three.js's fix.

A SEPARATE, genuinely new issue was found and fixed during this same verification: printed/decal triangle
groups in the baked part JSON sit EXACTLY coincident with the part's own main surface (confirmed: some decal
vertices are bit-for-bit identical to 'main' group vertices; the whole decal group for 4744p0m sits on the
exact z=-320 plane matching the part's own bounds). A ray tracer resolves exactly-coincident geometry
ambiguously -- the print was genuinely INVISIBLE in every render (confirmed with glaring, unmissable debug
colours, ruling out "just hard to see") before a small per-triangle normal-offset was added for decal groups
(see _DECAL_OFFSET below). Three.js's own renderer has no equivalent explicit offset and likely only avoids
this visually through an implicit, fragile WebGL depth-tie/draw-order coincidence, not a real fix -- not worth
porting; the offset is the real, robust fix, needed here regardless of which WINDING_MODE is chosen.
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.brick_models import blender_view_math as bvm  # noqa: E402

import bpy  # noqa: E402  (only this file imports bpy -- everything else stays testable without it)
from mathutils import Matrix  # noqa: E402


# One of 'swap', 'mirror', 'doubleside' -- set by the empirical test described in this file's own top comment.
# 'swap': apply build_design_page.py's (a,c,b) vertex-order swap at mesh-build time, no object-level mirror.
# 'mirror': no vertex swap, negative-scale object-level mirror on Y (matching three.js's own fix).
# 'doubleside': no swap, no mirror, material.use_backface_culling=False (a Blender-only option three.js has
# no equivalent of, since WebGL always culls one side).
WINDING_MODE = "doubleside"  # see this file's top comment for the empirical test that picked this


# ---------------------------------------------------------------------------
# Data loading -- no bpy needed for these three functions (kept bpy-free is not required here since this
# whole file already imports bpy, but keeping the SHAPE clean means these are easy to unit-test in isolation
# by monkeypatching bpy out, if that's ever useful).
# ---------------------------------------------------------------------------

# Twin of atoms_brick.gs's _partsModelSanitise row-shape handling (array [p,x,y,z,r,c] / [...,step], or object
# {p,x,y,z,r,c,s}) -- NOT a twin of its full defensive validation (range clamping etc: that function defends a
# public-facing API endpoint against adversarial input; this script reads data it already trusts, fetched or
# generated locally, so it only needs to understand the SHAPE, not re-implement every clamp). No existing
# Python function in this repo already does this row-shape parsing (renderers/brick_parts_validate.py's
# validate_parts expects ALREADY-parsed {p,x,y,z,r} dicts, not raw rows) -- this is new, but deliberately thin.
def load_parts_model(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = raw["partsModel"] if isinstance(raw, dict) and "partsModel" in raw else raw
    out = []
    for row in rows:
        if isinstance(row, list):
            p, x, y, z, r, c = row[0], row[1], row[2], row[3], row[4], row[5]
            step = row[6] if len(row) > 6 else 1
        elif isinstance(row, dict):
            p, x, y, z, r, c = row["p"], row["x"], row["y"], row["z"], row["r"], row["c"]
            step = row.get("s", 1)
        else:
            continue
        out.append({"p": p, "x": x, "y": y, "z": z, "r": int(r) % 24, "c": c, "step": step or 1})
    return out


def load_colour_table(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


_mesh_cache = {}


def load_part_mesh(part_id, parts_dir):
    if part_id not in _mesh_cache:
        mesh_path = Path(parts_dir) / f"{part_id}.json"
        _mesh_cache[part_id] = json.loads(mesh_path.read_text(encoding="utf-8"))
    return _mesh_cache[part_id]


# ---------------------------------------------------------------------------
# Scene construction
# ---------------------------------------------------------------------------

# Printed/decal colour groups (anything not 'main') are baked EXACTLY coincident with the part's own main
# surface in the source LDraw data -- confirmed empirically 2026-09-30 against public/parts/4744p0m.json (a
# real printed part): every one of its print groups' triangles sit on the exact same z=-320 plane as the
# part's own bounds, with some vertices exactly bit-for-bit identical to 'main' group vertices. A ray tracer
# (Cycles) resolves exactly-coincident geometry ambiguously -- confirmed live: the print was INVISIBLE in
# every render (including with glaring debug colours, ruling out "just hard to see"), the base surface won
# the intersection every time. This is a genuine geometry fix, not a winding-mode question (reproduced
# identically across all three WINDING_MODE variants) -- push each decal triangle's vertices a small distance
# along its OWN face normal, a standard "decal offset" technique, so it unambiguously sits in front of the
# surface it decorates. (Three.js's build_design_page.py has no equivalent explicit offset -- it likely only
# avoids this visually because WebGL's default depthFunc<=LEQUAL happens to let the LAST-drawn coincident
# fragment win ties, and JS bucket-iteration order happens to draw print groups after 'main' -- an implicit,
# fragile draw-order dependency, not a real fix worth porting.)
_DECAL_OFFSET = 0.6  # raw quant-scaled units -- small relative to a typical part's hundreds-of-units extent


def _face_normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / length, ny / length, nz / length)


def _triangle_groups_to_bpy_mesh(name, part, *, swap_winding):
    """Builds ONE bpy mesh datablock from a baked part's triangle groups. Returns (mesh, colour_key_per_face)
    so the caller can assign per-face materials matching build_design_page.py's localGeometryGroups -- 'main'
    groups tint to the instance's own colour; any other group value is a fixed '#rrggbb' (printed decals)."""
    verts = []
    faces = []
    face_colour_keys = []
    for group in part["triangles"]:
        if group["colour"] == "edge":
            continue
        is_decal = group["colour"] != "main"
        pos = group["pos"]
        for i in range(0, len(pos) - 2, 3):
            a, b, c = pos[i], pos[i + 1], pos[i + 2]
            tri = (a, c, b) if swap_winding else (a, b, c)
            if is_decal:
                nx, ny, nz = _face_normal(*tri)
                tri = tuple((v[0] + nx * _DECAL_OFFSET, v[1] + ny * _DECAL_OFFSET, v[2] + nz * _DECAL_OFFSET)
                            for v in tri)
            base = len(verts)
            verts.extend(tri)
            faces.append((base, base + 1, base + 2))
            face_colour_keys.append(None if group["colour"] == "main" else group["colour"])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # Material SLOTS (count, order, per-polygon index) are mesh-data properties -- shared correctly across
    # every instance of this part id, since the triangle topology is identical for all of them. The actual
    # MATERIAL each slot resolves to is deliberately NOT set here (see build_scene's own comment on why:
    # obj.data.materials is mesh-level, shared by every object using this same mesh datablock -- two
    # differently-coloured instances of the SAME part id would otherwise silently overwrite each other's
    # colour, confirmed live 2026-09-30 with a real two-colour multi-instance scene).
    distinct_keys = []
    for key in face_colour_keys:
        if key not in distinct_keys:
            distinct_keys.append(key)
    for _ in distinct_keys:
        mesh.materials.append(None)  # placeholder slot -- real material assigned per-OBJECT, not per-mesh
    slot_of = {key: i for i, key in enumerate(distinct_keys)}
    for poly, key in zip(mesh.polygons, face_colour_keys):
        poly.material_index = slot_of[key]

    return mesh, distinct_keys


_material_cache = {}


def _hex_to_rgba(hex_colour):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b, 1.0)


def get_material(colour_code_or_hex, colour_table):
    """Blender-side material cache, mirroring build_design_page.py's matCache -- one Principled BSDF material
    per distinct colour, built from blender_view_math.material_params_for_code's plain dict."""
    cache_key = colour_code_or_hex
    if cache_key in _material_cache:
        return _material_cache[cache_key]
    if isinstance(colour_code_or_hex, str) and colour_code_or_hex.startswith("#"):
        params = {"base_color_hex": colour_code_or_hex, "metallic": 0.05, "roughness": 0.85}
    else:
        params = bvm.material_params_for_code(colour_code_or_hex, colour_table)
    mat = bpy.data.materials.new(f"mat_{cache_key}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = _hex_to_rgba(params["base_color_hex"])
    bsdf.inputs["Metallic"].default_value = params.get("metallic", 0.05)
    bsdf.inputs["Roughness"].default_value = params.get("roughness", 0.85)
    if "coat_weight" in params:
        bsdf.inputs["Coat Weight"].default_value = params["coat_weight"]
        bsdf.inputs["Coat Roughness"].default_value = params["coat_roughness"]
    if "transmission_weight" in params:
        bsdf.inputs["Transmission Weight"].default_value = params["transmission_weight"]
        bsdf.inputs["IOR"].default_value = params["ior"]
    if WINDING_MODE == "doubleside":
        mat.use_backface_culling = False
    _material_cache[cache_key] = mat
    return mat


def build_scene(parts, parts_dir, colour_table):
    """Builds one bpy mesh datablock per distinct part id (bpy's own form of geometry reuse -- many objects
    sharing one mesh datablock, analogous to but structurally different from three.js's InstancedMesh), places
    one object per instance via matrix_world, assigns materials. Returns the accumulated world-space AABB as
    (box_min, box_max) for fit_camera."""
    mesh_cache = {}
    box_min = [math.inf, math.inf, math.inf]
    box_max = [-math.inf, -math.inf, -math.inf]
    collection = bpy.context.collection

    for row in parts:
        part = load_part_mesh(row["p"], parts_dir)
        quant = part.get("quant", 1) or 1
        if row["p"] not in mesh_cache:
            swap = WINDING_MODE == "swap"
            mesh_cache[row["p"]] = _triangle_groups_to_bpy_mesh(row["p"], part, swap_winding=swap)
        mesh_data, distinct_keys = mesh_cache[row["p"]]

        obj = bpy.data.objects.new(f"{row['p']}_{row['x']}_{row['y']}_{row['z']}_{row['r']}", mesh_data)
        collection.objects.link(obj)

        local_matrix = Matrix(bvm.instance_matrix(row["r"], (row["x"], row["y"], row["z"]), quant))
        # D=diag(1/20,-1/20,1/20): the LDraw Y-down->target-Y-up mirror+LDU-to-world scale, applied at the
        # OBJECT level here regardless of WINDING_MODE. WINDING_MODE is 'doubleside' (see this file's own
        # top comment for why), so this D matrix's sign is fixed and not itself part of what WINDING_MODE
        # varies -- 'swap'/'mirror' were tried as alternatives during the empirical verification that picked
        # 'doubleside', not as ongoing runtime options this D matrix needs to stay flexible for.
        d = Matrix(((1 / 20, 0, 0, 0), (0, -1 / 20, 0, 0), (0, 0, 1 / 20, 0), (0, 0, 0, 1)))
        obj.matrix_world = d @ local_matrix

        # Materials are assigned PER OBJECT, not per mesh-data ('main'-tint slots here need to resolve to
        # THIS instance's own colour, while distinct instances of the same part id -- e.g. a red 3001 and a
        # blue 3001 -- share the same mesh_data object by design, see _triangle_groups_to_bpy_mesh's own
        # comment). obj.data.materials (mesh-level) is shared across every object using this mesh_data --
        # assigning there would make the LAST-processed instance's colour silently overwrite every other
        # instance of the same part id. Confirmed live 2026-09-30 with a real two-colour scene (a yellow and
        # a green instance of the same part both rendered green). material_slots[i].link='OBJECT' is
        # Blender's real mechanism for a per-instance material override on shared mesh data.
        for i, key in enumerate(distinct_keys):
            mat = get_material(row["c"], colour_table) if key is None else get_material(key, colour_table)
            slot = obj.material_slots[i]
            slot.link = "OBJECT"
            slot.material = mat

        for corner in (
            (part["bounds"]["min"][0], part["bounds"]["min"][1], part["bounds"]["min"][2]),
            (part["bounds"]["max"][0], part["bounds"]["max"][1], part["bounds"]["max"][2]),
        ):
            world = obj.matrix_world @ Matrix.Translation(corner).translation
            for axis in range(3):
                box_min[axis] = min(box_min[axis], world[axis])
                box_max[axis] = max(box_max[axis], world[axis])

    return tuple(box_min), tuple(box_max)


def setup_lighting_and_world():
    """Simple studio 3-point-ish setup -- same PURPOSE as build_design_page.py's RoomEnvironment (procedural,
    no external HDRI asset/licensing), Blender-native primitives rather than a port of that JS."""
    world = bpy.data.worlds.new("studio_world")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.82, 0.84, 0.87, 1.0)
    bg.inputs["Strength"].default_value = 0.6
    bpy.context.scene.world = world

    key = bpy.data.lights.new("key", type="AREA")
    key.energy = 800
    key_obj = bpy.data.objects.new("key", key)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (6, 8, 10)
    key_obj.rotation_euler = (math.radians(50), 0, math.radians(35))

    fill = bpy.data.lights.new("fill", type="AREA")
    fill.energy = 250
    fill_obj = bpy.data.objects.new("fill", fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (-6, -4, 5)
    fill_obj.rotation_euler = (math.radians(70), 0, math.radians(-30))


def setup_camera(box_min, box_max, direction, fov_y_deg, aspect, margin=1.15):
    fit = bvm.fit_camera(box_min, box_max, direction, fov_y_deg, aspect, margin)
    cam_data = bpy.data.cameras.new("camera")
    cam_data.lens_unit = "FOV"
    cam_data.angle_y = math.radians(fov_y_deg)
    cam_data.sensor_fit = "VERTICAL"
    cam_data.clip_start = fit["near"]
    cam_data.clip_end = fit["far"]
    cam_obj = bpy.data.objects.new("camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    _point_camera(cam_obj, fit["position"], fit["target"])
    return cam_obj, fit


def _point_camera(cam_obj, position, target):
    cam_obj.location = position
    direction = (target[0] - position[0], target[1] - position[1], target[2] - position[2])
    length = math.sqrt(sum(c * c for c in direction)) or 1.0
    forward = tuple(c / length for c in direction)
    # Blender cameras look down their own local -Z with +Y up -- build a rotation that points -Z at target.
    world_up = (0.0, 1.0, 0.0)
    right = (
        forward[1] * world_up[2] - forward[2] * world_up[1],
        forward[2] * world_up[0] - forward[0] * world_up[2],
        forward[0] * world_up[1] - forward[1] * world_up[0],
    )
    rlen = math.sqrt(sum(c * c for c in right)) or 1.0
    right = tuple(c / rlen for c in right)
    up = (
        right[1] * forward[2] - right[2] * forward[1],
        right[2] * forward[0] - right[0] * forward[2],
        right[0] * forward[1] - right[1] * forward[0],
    )
    rot = Matrix((
        (right[0], up[0], -forward[0], 0),
        (right[1], up[1], -forward[1], 0),
        (right[2], up[2], -forward[2], 0),
        (0, 0, 0, 1),
    ))
    cam_obj.matrix_world = Matrix.Translation(position) @ rot


def configure_render(resolution, samples):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.image_settings.file_format = "PNG"


def render_still(out_path, resolution, samples=128):
    configure_render(resolution, samples)
    bpy.context.scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)


def render_turntable(out_dir, fit, direction, fov_y_deg, aspect, resolution, frames=90, fps=30, samples=64):
    """Orbits the camera around fit's ALREADY-computed target/distance -- one fit_camera call (done by the
    caller before this function runs), never a per-frame refit, so the subject doesn't visibly grow/shrink/
    drift across the video as its silhouette changes with rotation."""
    configure_render(resolution, samples)
    out_dir = Path(out_dir)
    frame_dir = out_dir / "_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)

    cam_obj = bpy.context.scene.camera
    target = fit["target"]
    radius_vec = (
        fit["position"][0] - target[0],
        fit["position"][1] - target[1],
        fit["position"][2] - target[2],
    )
    frame_paths = []
    for i in range(frames):
        angle = 2 * math.pi * i / frames
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        # rotate radius_vec about world-up (Y) by angle
        rotated = (
            radius_vec[0] * cos_a + radius_vec[2] * sin_a,
            radius_vec[1],
            -radius_vec[0] * sin_a + radius_vec[2] * cos_a,
        )
        position = (target[0] + rotated[0], target[1] + rotated[1], target[2] + rotated[2])
        _point_camera(cam_obj, position, target)
        frame_path = frame_dir / f"frame_{i:04d}.png"
        bpy.context.scene.render.filepath = str(frame_path)
        bpy.ops.render.render(write_still=True)
        frame_paths.append(frame_path)

    encode_video(frame_paths, out_dir / "turntable.mp4", fps)

    for frame_path in frame_paths:
        frame_path.unlink()
    frame_dir.rmdir()


def encode_video(frame_paths, out_path, fps):
    """bpy's own build has no FFMPEG output support (confirmed live 2026-09-30, see
    requirements-blender.txt's own comment) -- encodes the rendered PNG sequence with imageio-ffmpeg's bundled
    static ffmpeg binary via subprocess instead."""
    import subprocess
    import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    frame_dir = frame_paths[0].parent
    pattern = str(frame_dir / "frame_%04d.png")
    cmd = [
        ffmpeg_exe, "-y", "-framerate", str(fps), "-i", pattern,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parts-model", required=True)
    ap.add_argument("--parts-dir", default="public/parts")
    ap.add_argument("--colours", default="public/bricksdemo/ldraw_colours_full.json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--resolution", default="1600x1200")
    ap.add_argument("--frames", type=int, default=90)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--direction", default="1,0.6,1")
    ap.add_argument("--fov", type=float, default=45)
    ap.add_argument("--still-samples", type=int, default=128)
    ap.add_argument("--turntable-samples", type=int, default=64)
    ap.add_argument("--no-video", action="store_true")
    return ap.parse_args(argv)


def main(argv=None):
    # Blender swallows argv before a `--` separator when invoked as `blender --background --python script.py
    # -- <args>`; when run directly via a bpy-installed Python (this repo's recommended path, see this file's
    # own top comment), argv is just sys.argv[1:] as normal. Handle both.
    raw_argv = argv if argv is not None else sys.argv[1:]
    if "--" in raw_argv:
        raw_argv = raw_argv[raw_argv.index("--") + 1:]
    args = parse_args(raw_argv)

    bpy.ops.wm.read_factory_settings(use_empty=True)

    parts = load_parts_model(args.parts_model)
    colour_table = load_colour_table(args.colours)
    box_min, box_max = build_scene(parts, args.parts_dir, colour_table)
    setup_lighting_and_world()

    resolution = tuple(int(v) for v in args.resolution.split("x"))
    direction = tuple(float(v) for v in args.direction.split(","))
    aspect = resolution[0] / resolution[1]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cam_obj, fit = setup_camera(box_min, box_max, direction, args.fov, aspect)
    render_still(out_dir / "hero.png", resolution, samples=args.still_samples)

    if not args.no_video:
        render_turntable(out_dir, fit, direction, args.fov, aspect, resolution,
                          frames=args.frames, fps=args.fps, samples=args.turntable_samples)

    print(f"wrote {out_dir / 'hero.png'}" + ("" if args.no_video else f" and {out_dir / 'turntable.mp4'}"))


if __name__ == "__main__":
    main()
