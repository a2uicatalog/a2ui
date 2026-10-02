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

    print("\n-- Photos (DP6/DP7/DP8) --\n"
          "Required whenever the wall is visible from the public road (espace public) -- NOT only in "
          "a secteur protege, see README.md and art. R.431-10 c/d du code de l'urbanisme.")
    wall_visible = _ask_choice("Is the wall/cloture visible from the public road?", ["yes", "no"], "yes")
    wall_visible_from_public = (wall_visible == "yes")
    photos = None
    if wall_visible_from_public:
        proche_path = _ask("Path to a real close-range site photo (JPEG/PNG) -- becomes DP7, and the "
                            "base photo for DP6. Leave blank to skip DP6/DP7/DP8 for now.", "", str)
        if proche_path:
            try:
                from PIL import Image
                w_px, h_px = Image.open(proche_path).size
                print(f"  -> loaded {proche_path} ({w_px}x{h_px}px)")
                print("  Enter the pixel coordinates of the wall's LEFT and RIGHT base points in that "
                      "photo (open it in any image viewer to read these off).")
                lx = _ask("  Left base point, pixel x", round(w_px * 0.3), float)
                ly = _ask("  Left base point, pixel y", round(h_px * 0.7), float)
                rx = _ask("  Right base point, pixel x", round(w_px * 0.7), float)
                ry = _ask("  Right base point, pixel y", round(h_px * 0.7), float)
                lointain_path = _ask("Path to a real distant/wide landscape photo (optional, becomes "
                                      "DP8) -- leave blank only if none is possible", "", str)
                photos = {"proche_path": proche_path, "lointain_path": lointain_path or None,
                          "left_base_px": [lx, ly], "right_base_px": [rx, ry]}
            except Exception as e:
                print(f"  -> could not load that photo ({e}), skipping DP6/DP7/DP8")
        else:
            print("  -> no photo provided -- add DP6/DP7/DP8 manually before submitting, since the "
                  "wall is visible from the public road")

    date_iso = _ask("Date (ISO)", date.today().isoformat())

    return {
        "commune": commune, "address": address, "date_iso": date_iso,
        "wall": {"project_type": project_type, "block_id": block_id, "bond": bond,
                 "length_m": length_m, "height_m": height_m, "thickness_mm": thickness_mm,
                 "finish_label": finish_label, "finish_colour_hex": finish_colour_hex},
        "plot": plot,
        "parcel_lookup": parcel_lookup_meta,
        "wall_visible_from_public": wall_visible_from_public,
        "photos": photos,
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


def generate_dossier(project: DPProject, out_dir, include_3d=False, parcel_lookup_meta=None,
                      wall_visible_from_public=None, photos=None):
    """Writes every automatable DP piece into out_dir, plus project.json (the input, for
    reproducibility/audit) and a checklist.txt of the remaining manual steps. parcel_lookup_meta, when
    given (collect_answers_interactively's "parcel_lookup" key -- lon/lat/label/contenance_m2/zone
    info from parcel_lookup.build_plot_from_address), also generates DP1_situation.png and enriches
    the checklist with the real zone/document pointer instead of the generic manual-lookup line.

    wall_visible_from_public (True/False/None) and photos (collect_answers_interactively's "photos"
    key -- {proche_path, lointain_path, left_base_px, right_base_px}, or None) drive DP6/DP7/DP8: see
    dp6_insertion.py's own module docstring for why these are required whenever the wall is visible
    from the public road, not only in a secteur protégé (a wrong claim this project's README used to
    make, corrected 2026-10-02 against the real, current CERFA 16702*03 bordereau)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "project.json").write_text(json.dumps({
        "commune": project.commune, "address": project.address, "date_iso": project.date_iso,
        "wall": vars(project.wall),
        "plot": {**vars(project.plot)},
        "parcel_lookup": parcel_lookup_meta,
        "wall_visible_from_public": wall_visible_from_public,
        "photos": photos,
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

    if photos and photos.get("proche_path"):
        try:
            from declaration_prealable import dp6_insertion
            proche_bytes = Path(photos["proche_path"]).read_bytes()
            (out_dir / "DP7_photo_proche.jpg").write_bytes(dp6_insertion.package_site_photo_bytes(
                proche_bytes, "DP7", "Photo - environnement proche", project.address))
            written.append("DP7_photo_proche.jpg")

            (out_dir / "DP6_insertion.png").write_bytes(dp6_insertion.composite_dp6_insertion_bytes(
                proche_bytes, photos["left_base_px"], photos["right_base_px"], project.wall,
                project.address))
            written.append("DP6_insertion.png")

            if photos.get("lointain_path"):
                lointain_bytes = Path(photos["lointain_path"]).read_bytes()
                (out_dir / "DP8_photo_lointain.jpg").write_bytes(dp6_insertion.package_site_photo_bytes(
                    lointain_bytes, "DP8", "Photo - paysage lointain", project.address))
                written.append("DP8_photo_lointain.jpg")
            else:
                written.append("DP8_photo_lointain.jpg skipped -- no distant photo provided (legally "
                                "OK only if you can justify that none is possible)")
        except Exception as e:
            written.append(f"DP6/DP7/DP8 skipped -- {e}")

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

    if wall_visible_from_public is True:
        visibility_line = ("  - Wall/cloture noted as VISIBLE from the public road: DP6 (insertion "
                            "dans l'environnement), DP7 (photo proche) and DP8 (photo lointain) are "
                            "required per the official bordereau (art. R.431-10 c/d du code de "
                            "l'urbanisme) -- NOT only in a secteur protege. See pieces above; if DP8 "
                            "was skipped, confirm your justification still holds.")
    elif wall_visible_from_public is False:
        visibility_line = ("  - Wall/cloture noted as NOT visible from the public road, and not in a "
                            "site patrimonial remarquable / abords d'un monument historique: DP6/DP7/"
                            "DP8 are not required per the official bordereau (art. R.431-10 c/d) -- "
                            "verify this is still true for the real site before submitting.")
    else:
        visibility_line = ("  - Visibility from the public road was not specified: confirm whether "
                            "DP6/DP7/DP8 are required (art. R.431-10 c/d -- required if visible from "
                            "l'espace public, or in a site patrimonial remarquable / abords MH).")

    checklist = f"""Déclaration préalable dossier -- {project.address}, {project.commune}
Generated {project.date_iso}. This is a DRAFTING AID, not a legal guarantee of acceptance
(see declaration_prealable/README.md).

Automated pieces in this folder:
{chr(10).join('  - ' + w for w in written)}
{(chr(10) + area_line) if area_line else ""}

Still needed, manually (see README.md for sourcing):
  - CERFA n°16702*03 form itself, filled in: https://www.formulaires.service-public.gouv.fr/gf/cerfa_16702.do
{dp1_line}{plu_line}
{visibility_line}
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
                                parcel_lookup_meta=answers.get("parcel_lookup"),
                                wall_visible_from_public=answers.get("wall_visible_from_public"),
                                photos=answers.get("photos"))
    print(f"\nDossier written to {out_dir}:")
    for w in written:
        print(f"  - {w}")


if __name__ == "__main__":
    main()
