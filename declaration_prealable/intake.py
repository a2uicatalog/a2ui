"""Interactive intake + full dossier assembler for a déclaration préalable project. Asks a short set
of questions (or reads them from a JSON file for scripted/reproducible runs), builds a DPProject, then
generates every automatable piece into one output directory, plus a checklist of the remaining manual
steps -- see declaration_prealable/README.md for the sourced legal grounding behind what's
automated vs. manual, and why.

    python3 declaration_prealable/intake.py                         # interactive
    python3 declaration_prealable/intake.py --answers data.json     # scripted, same shape as the
                                                                      # interactive prompts collect
    python3 declaration_prealable/intake.py --answers data.json --3d   # also render the optional
                                                                         # 3D supplementary visual
                                                                         # (needs bpy, see render_wall_3d.py)

This is a drafting aid, not a legal guarantee of acceptance -- every real dossier still needs a human
sanity-check against the official DP5 example convention and the real commune's PLU before submission
(see README.md).
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from declaration_prealable.project_schema import DPProject, PlotGeometry, WallSpec  # noqa: E402
from declaration_prealable import dp5_elevation, dp2_plan_masse  # noqa: E402

BLOCK_CHOICES = list(dp5_elevation.BLOCKS.keys())


def _ask(prompt, default=None, cast=str):
    suffix = f" [{default}]" if default is not None else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    if not raw:
        if default is None:
            raise ValueError(f"a value is required for: {prompt}")
        return default
    return cast(raw)


def _ask_choice(prompt, choices, default):
    raw = _ask(f"{prompt} ({'/'.join(choices)})", default)
    if raw not in choices:
        print(f"  not one of {choices}, using default {default!r}")
        return default
    return raw


def collect_answers_interactively():
    """Asks the question set, returns a plain dict in the same shape build_project expects --
    identical shape to what --answers reads from a JSON file, so the interactive path and the
    scripted path share exactly one downstream pipeline."""
    print("Déclaration préalable -- wall/clôture project intake\n"
          "(press Enter to accept a shown default; see declaration_prealable/README.md for what "
          "each DP piece needs this for)\n")

    commune = _ask("Commune")
    address = _ask("Address")

    print("\n-- Wall --")
    project_type = _ask_choice("Project type", ["cloture", "soutenement"], "cloture")
    block_id = _ask_choice("Block type", BLOCK_CHOICES, "parpaing200")
    bond = _ask_choice("Bond pattern", ["running", "stack"], "running")
    length_m = _ask("Wall length (m)", 3.0, float)
    height_m = _ask("Wall height (m)", 1.8, float)
    if height_m >= dp5_elevation.DP_WALL_HEIGHT_THRESHOLD_M:
        print(f"  -> height >= {dp5_elevation.DP_WALL_HEIGHT_THRESHOLD_M:.0f} m: DP is mandatory "
              "regardless of PLU (see README.md, service-public.gouv.fr/particuliers/vosdroits/F3131)")
    thickness_mm = int(_ask("Wall thickness (mm)", 200, float))
    finish_label = _ask("Finish, DP5-style wording", "Enduit lisse peint en blanc")
    finish_colour_hex = _ask("Finish colour (hex)", "#f2f1ec")

    print("\n-- Plot (used for DP2) --")
    parcel_lookup_meta = None
    use_real = _ask_choice("Look up the real parcel boundary for this address? (BAN + IGN cadastre, "
                            "free/keyless government APIs)", ["yes", "no"], "yes")
    if use_real == "yes":
        try:
            from declaration_prealable import parcel_lookup
            wall_offset_m = _ask("Wall start: distance from the parcel's bounding-box corner (m)", 1.0, float)
            plot_obj, meta = parcel_lookup.build_plot_from_address(address, commune, length_m, wall_offset_m)
            print(f"  -> found: {meta['label']}, {meta['contenance_m2']} m2 (computed from the real "
                  f"boundary: {meta['computed_area_m2']} m2), zone {meta.get('zone_libelle') or 'unknown'}")
            north_angle_deg = _ask("North angle, degrees clockwise from 'up' on the page", 0.0, float)
            plot = {
                "boundary_points_m": plot_obj.boundary_points_m,
                "existing_structures": plot_obj.existing_structures,
                "wall_points_m": plot_obj.wall_points_m,
                "north_angle_deg": north_angle_deg,
            }
            parcel_lookup_meta = meta
        except Exception as e:
            print(f"  -> lookup failed ({e}), falling back to manual plot entry")
            use_real = "no"

    if use_real != "yes":
        print("Quick mode: a rectangular plot. For a precise/irregular plot, pass --answers with a full "
              "'plot' block instead (see project_schema.PlotGeometry).")
        plot_width_m = _ask("Plot width, along the street-facing side (m)", 20.0, float)
        plot_depth_m = _ask("Plot depth (m)", 25.0, float)
        wall_offset_x_m = _ask("Wall start: distance from the left boundary (m)", 0.5, float)
        wall_offset_y_m = _ask("Wall start: distance from the front/street boundary (m)", 2.0, float)
        north_angle_deg = _ask("North angle, degrees clockwise from 'up' on the page", 0.0, float)

        has_existing = _ask_choice("Existing structure to show (e.g. the house)?", ["yes", "no"], "no")
        existing_structures = []
        if has_existing == "yes":
            sx = _ask("  structure: distance from left boundary (m)", 3.0, float)
            sy = _ask("  structure: distance from front boundary (m)", 10.0, float)
            sw = _ask("  structure: width (m)", 10.0, float)
            sd = _ask("  structure: depth (m)", 8.0, float)
            existing_structures = [{"label": "Maison existante",
                                     "points_m": [(sx, sy), (sx + sw, sy), (sx + sw, sy + sd), (sx, sy + sd)]}]

        plot = {
            "boundary_points_m": [(0, 0), (plot_width_m, 0), (plot_width_m, plot_depth_m), (0, plot_depth_m)],
            "existing_structures": existing_structures,
            "wall_points_m": [(wall_offset_x_m, wall_offset_y_m), (wall_offset_x_m + length_m, wall_offset_y_m)],
            "north_angle_deg": north_angle_deg,
        }

    date_iso = _ask("Date (ISO)", date.today().isoformat())

    return {
        "commune": commune, "address": address, "date_iso": date_iso,
        "wall": {"project_type": project_type, "block_id": block_id, "bond": bond,
                 "length_m": length_m, "height_m": height_m, "thickness_mm": thickness_mm,
                 "finish_label": finish_label, "finish_colour_hex": finish_colour_hex},
        "plot": plot,
        "parcel_lookup": parcel_lookup_meta,
    }


def build_project(answers: dict) -> DPProject:
    wall = WallSpec(**answers["wall"])
    plot_data = dict(answers.get("plot") or {})
    if "boundary_points_m" in plot_data:
        plot_data["boundary_points_m"] = [tuple(p) for p in plot_data["boundary_points_m"]]
    if "wall_points_m" in plot_data:
        plot_data["wall_points_m"] = [tuple(p) for p in plot_data["wall_points_m"]]
    for s in plot_data.get("existing_structures", []):
        s["points_m"] = [tuple(p) for p in s["points_m"]]
    plot = PlotGeometry(**plot_data)
    return DPProject(commune=answers["commune"], address=answers["address"], wall=wall, plot=plot,
                      date_iso=answers.get("date_iso", date.today().isoformat()))


def generate_dossier(project: DPProject, out_dir, include_3d=False, parcel_lookup_meta=None):
    """Writes every automatable DP piece into out_dir, plus project.json (the input, for
    reproducibility/audit) and a checklist.txt of the remaining manual steps. parcel_lookup_meta, when
    given (collect_answers_interactively's "parcel_lookup" key -- lon/lat/label/contenance_m2/zone
    info from parcel_lookup.build_plot_from_address), also generates DP1_situation.png and enriches
    the checklist with the real zone/document pointer instead of the generic manual-lookup line."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "project.json").write_text(json.dumps({
        "commune": project.commune, "address": project.address, "date_iso": project.date_iso,
        "wall": vars(project.wall),
        "plot": {**vars(project.plot)},
        "parcel_lookup": parcel_lookup_meta,
    }, indent=2, default=list))

    written = []
    try:
        dp5_elevation.render_dp5_png(project, out_dir / "DP5_elevation.png")
        written.append("DP5_elevation.png")
    except ImportError:
        (out_dir / "DP5_elevation.svg").write_text(dp5_elevation.render_dp5_svg(project))
        written.append("DP5_elevation.svg (cairosvg not installed -- SVG only, see README.md)")

    try:
        dp2_plan_masse.render_dp2_png(project, out_dir / "DP2_plan_masse.png")
        written.append("DP2_plan_masse.png")
    except ImportError:
        (out_dir / "DP2_plan_masse.svg").write_text(dp2_plan_masse.render_dp2_svg(project))
        written.append("DP2_plan_masse.svg (cairosvg not installed -- SVG only, see README.md)")

    if parcel_lookup_meta:
        try:
            from declaration_prealable import dp1_situation
            dp1_situation.render_dp1_png(parcel_lookup_meta["lon"], parcel_lookup_meta["lat"],
                                          project.address, out_dir / "DP1_situation.png")
            written.append("DP1_situation.png (real IGN orthophoto + cadastral overlay)")
        except Exception as e:
            written.append(f"DP1_situation.png skipped -- {e}")

    if include_3d:
        try:
            from declaration_prealable import render_wall_3d
            render_wall_3d.render_wall_3d_png(project, out_dir / "DP5_supplementary_3d.png")
            written.append("DP5_supplementary_3d.png (optional, NOT a substitute for DP5_elevation)")
        except ImportError as e:
            written.append(f"3D supplementary visual skipped -- bpy not available ({e})")

    if parcel_lookup_meta:
        area_line = (f"  - Real parcel: {parcel_lookup_meta.get('idu', 'unknown')}, "
                     f"{parcel_lookup_meta.get('contenance_m2', '?')} m2 (official cadastre figure).")
        zone = parcel_lookup_meta.get("zone_libelle")
        doc = parcel_lookup_meta.get("reglement_pdf_filename")
        if zone:
            plu_line = (f"  - PLU zone: {zone}. Applicable règlement document: {doc or 'not found'} -- "
                        f"this is the real document reference, but its actual height/material/colour "
                        f"VALUES are not parsed automatically (see README.md) -- open it and read the "
                        f"rules for this zone before finalizing.")
        else:
            plu_line = (f"  - No digitised PLU zone found for this address via the Géoportail de "
                        f"l'Urbanisme -- verify with the mairie directly.")
    else:
        area_line = None
        plu_line = (f"  - Verify the real commune's PLU ({project.commune}) for wall height/material/"
                    f"colour rules before finalizing -- this dossier's generated pieces reflect the "
                    f"figures you entered, not a PLU lookup.")

    dp1_line = ("" if parcel_lookup_meta else
                f"  - DP1 (plan de situation): export an annotated extract from geoportail.gouv.fr or "
                f"cadastre.gouv.fr centred on {project.address} -- not auto-generated, the official "
                f"guidance itself expects this.\n")

    checklist = f"""Déclaration préalable dossier -- {project.address}, {project.commune}
Generated {project.date_iso}. This is a DRAFTING AID, not a legal guarantee of acceptance
(see declaration_prealable/README.md).

Automated pieces in this folder:
{chr(10).join('  - ' + w for w in written)}
{(chr(10) + area_line) if area_line else ""}

Still needed, manually (see README.md for sourcing):
  - CERFA n°16702*03 form itself, filled in: https://www.formulaires.service-public.gouv.fr/gf/cerfa_16702.do
{dp1_line}{plu_line}
  - DP3 (coupe) only if the site's terrain profile changes -- not included here.
  - Two complete paper dossiers for a mail submission (more if in a secteur protege).
"""
    (out_dir / "checklist.txt").write_text(checklist)
    written.append("checklist.txt")
    written.append("project.json")
    return written


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--answers", help="JSON file with the same shape collect_answers_interactively() "
                                       "produces -- skips the interactive prompts")
    ap.add_argument("--out-dir", default=None, help="default: declaration_prealable/dossiers/<date>_<slug>")
    ap.add_argument("--3d", dest="include_3d", action="store_true",
                     help="also render the optional 3D supplementary visual (needs bpy)")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.answers:
        answers = json.loads(Path(args.answers).read_text())
    else:
        answers = collect_answers_interactively()

    project = build_project(answers)

    out_dir = args.out_dir
    if not out_dir:
        slug = project.commune.lower().replace(" ", "-")
        out_dir = Path(__file__).resolve().parent / "dossiers" / f"{project.date_iso}_{slug}"

    written = generate_dossier(project, out_dir, include_3d=args.include_3d,
                                parcel_lookup_meta=answers.get("parcel_lookup"))
    print(f"\nDossier written to {out_dir}:")
    for w in written:
        print(f"  - {w}")


if __name__ == "__main__":
    main()
