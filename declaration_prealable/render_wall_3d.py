"""Optional supplementary 3D visual for a DP5 piece -- see declaration_prealable/README.md: DP5 is
explicitly allowed to be a hand sketch, a photomontage, OR a computer simulation; this is the third
option, NOT a substitute for dp5_elevation.py's 2D dimensioned/annotated piece (which stays the
primary DP5 submission -- this script's own output is labelled as a supplementary extra).

Reuses scripts/brick_models/render_blender.py's Cycles scene infrastructure (lighting, camera fit,
render settings, the hero-still render call) -- that module's GEOMETRY/MATERIAL layer is LDraw-brick-
specific (part meshes loaded by LDraw part id, materials keyed to LDraw colour codes) and is NOT
reused here. This module builds one plain parametric wall slab directly in real-world metres (no
LDU/stud scale matrix -- that conversion was specific to LDraw's unit system) with a flat
rendered-masonry ("enduit") material instead of the brick-plastic Principled BSDF setup.

A rendered/enduit finish is genuinely flat and smooth in real life (the point of rendering over
blockwork is to hide the individual block joints), so a single slab with a rough, non-metallic
material and a subtle hand-trowelled bump texture is an accurate representation, not a simplification
of a more "correct" coursed-block render.

Run with the same bpy-installed Python as render_blender.py (see
scripts/brick_models/requirements-blender.txt):
    python3 declaration_prealable/render_wall_3d.py --project path/to/project.json --out-dir /tmp/out
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import bpy  # noqa: E402

from scripts.brick_models import render_blender as rb  # noqa: E402
from declaration_prealable.project_schema import DPProject, PlotGeometry, WallSpec  # noqa: E402


def _hex_to_rgba(hex_colour):
    # Tiny, stable, pure function -- duplicated rather than reached into render_blender.py's own
    # underscore-prefixed _hex_to_rgba, matching this directory's existing convention (README.md) of
    # not importing another module's private helpers across a domain boundary.
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b, 1.0)


def build_wall_scene(project: DPProject):
    """Builds a single rendered-masonry wall slab in real-world metres, base on the ground plane
    (Y-up, matching render_blender.py's own Y-up world convention -- NOT Blender's own native Z-up
    default; every object/camera/light in this scene is authored consistently with Y as "up"). Also
    adds a ground plane so the wall has a visible contact shadow/sense of scale instead of floating
    in void. Returns (box_min, box_max) for rb.setup_camera's fit_camera call, matching
    render_blender.py's build_scene contract.

    Found live 2026-10-01: primitive_cube_add(size=1) already has HALF-extent 0.5 (full extent 1) --
    setting obj.scale to length/2 halved the wall's actual size a second time, rendering a wall at
    half its intended dimensions (confirmed by a real render showing the wall far smaller in frame
    than fit_camera's own math, computed from the INTENDED box_min/box_max, called for)."""
    w = project.wall
    length, height, thickness = w.length_m, w.height_m, w.thickness_mm / 1000.0

    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.active_object
    obj.name = "wall"
    obj.scale = (length, height, thickness)
    obj.location = (0, height / 2, 0)

    mat = bpy.data.materials.new("wall_render_finish")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = _hex_to_rgba(w.finish_colour_hex)
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Metallic"].default_value = 0.0

    # Subtle taloché/crépi surface texture via Noise -> Bump -- a real rendered masonry finish has
    # visible hand-trowelled texture even at a uniform colour, unlike a flat plastic-smooth material.
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 80.0
    noise.inputs["Detail"].default_value = 4.0
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    obj.data.materials.append(mat)

    # Ground plane -- default primitive_plane_add lies flat in LOCAL XY (normal +Z), which is
    # upright/wrong in this scene's Y-up convention; rotate so its normal points +Y instead.
    ground_size = max(length, 3.0) * 3.0
    bpy.ops.mesh.primitive_plane_add(size=ground_size)
    ground = bpy.context.active_object
    ground.name = "ground"
    ground.rotation_euler = (math.radians(-90), 0, 0)
    gmat = bpy.data.materials.new("ground_mat")
    gmat.use_nodes = True
    gbsdf = gmat.node_tree.nodes.get("Principled BSDF")
    gbsdf.inputs["Base Color"].default_value = (0.42, 0.46, 0.36, 1.0)  # muted ground, distinct from both sky and wall
    gbsdf.inputs["Roughness"].default_value = 0.95
    gbsdf.inputs["Metallic"].default_value = 0.0
    ground.data.materials.append(gmat)

    half_l, half_h, half_t = length / 2, height / 2, thickness / 2
    box_min = (-half_l, 0.0, -half_t)
    box_max = (half_l, height, half_t)
    return box_min, box_max


def setup_wall_lighting_and_world():
    """Outdoor daylight rig, NOT a reuse of render_blender.py's setup_lighting_and_world -- that
    one's two AREA lights are positioned/energy-tuned for LEGO-scale (tens of cm) subjects; a
    multi-metre wall needs a distance-independent light. A Sun lamp (irradiance in W/m2, not
    distance-dependent like an Area light) plus a light-sky-blue world background scales correctly
    regardless of the wall's real-world dimensions, and reads as an outdoor site photo, matching the
    DP5 "photomontage" register this visual is meant to support."""
    world = bpy.data.worlds.new("outdoor_world")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.65, 0.78, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = world

    sun = bpy.data.lights.new("sun", type="SUN")
    sun.energy = 3.5
    sun.angle = math.radians(3)
    sun_obj = bpy.data.objects.new("sun", sun)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(55), 0, math.radians(35))


def load_project(path) -> DPProject:
    data = json.loads(Path(path).read_text())
    wall = WallSpec(**data["wall"])
    plot = PlotGeometry(**data.get("plot", {}))
    return DPProject(commune=data["commune"], address=data["address"], wall=wall, plot=plot,
                      date_iso=data.get("date_iso", ""))


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True, help="path to a DPProject JSON (see project_schema.py)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--resolution", default="1600x1200")
    ap.add_argument("--direction", default="0,0.35,1", help="mostly front-on, slightly elevated -- a front-elevation-style view angle")
    ap.add_argument("--fov", type=float, default=40)
    ap.add_argument("--samples", type=int, default=128)
    return ap.parse_args(argv)


def render_wall_3d_png(project: DPProject, out_path, resolution=(1600, 1200),
                        direction=(0.0, 0.35, 1.0), fov=40.0, samples=128):
    """The single reusable entry point -- both this module's own CLI (main(), below) and
    declaration_prealable/intake.py's generate_dossier() call this, so the real scene-setup sequence
    (factory reset, colour management, geometry, lighting, camera fit, render) exists in exactly one
    place rather than being duplicated between a CLI wrapper and a dossier-assembly caller."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Blender's factory default view transform is AgX, a filmic-style tone-mapper that noticeably
    # desaturates/compresses muted colours (confirmed live 2026-10-01: a light sky-blue world
    # background rendered as flat grey). render_blender.py's LEGO renders never hit this visibly
    # because brick-plastic colours are fully saturated; this module's outdoor sky/ground/render-finish
    # palette is exactly the muted range AgX crushes hardest, and a planning-document visual should be
    # predictable/literal, not cinematic -- Standard is the right choice here, not a tuning workaround.
    bpy.context.scene.view_settings.view_transform = "Standard"

    box_min, box_max = build_wall_scene(project)
    setup_wall_lighting_and_world()

    aspect = resolution[0] / resolution[1]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rb.setup_camera(box_min, box_max, direction, fov, aspect)
    rb.render_still(out_path, resolution, samples=samples)
    return out_path


def main(argv=None):
    raw_argv = argv if argv is not None else sys.argv[1:]
    if "--" in raw_argv:
        raw_argv = raw_argv[raw_argv.index("--") + 1:]
    args = parse_args(raw_argv)

    project = load_project(args.project)
    resolution = tuple(int(v) for v in args.resolution.split("x"))
    direction = tuple(float(v) for v in args.direction.split(","))

    out_path = render_wall_3d_png(project, Path(args.out_dir) / "wall_3d.png",
                                   resolution=resolution, direction=direction,
                                   fov=args.fov, samples=args.samples)
    print(f"wrote {out_path} -- supplementary visual only, NOT a substitute for the DP5 2D elevation "
          f"(declaration_prealable/dp5_elevation.py)")


if __name__ == "__main__":
    main()
