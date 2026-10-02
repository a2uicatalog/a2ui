"""Tests declaration_prealable/intake.py's pure logic (build_project, generate_dossier) without going
through collect_answers_interactively()'s real input() prompts -- those are exercised manually, not
in CI, matching the general house convention of not unit-testing interactive terminal I/O directly.
"""
import json
from pathlib import Path

import pytest

from declaration_prealable import intake


def _sample_answers():
    return {
        "commune": "Exemple-sur-Seine", "address": "12 rue des Tilleuls", "date_iso": "2026-10-01",
        "wall": {"project_type": "cloture", "block_id": "parpaing200", "bond": "running",
                 "length_m": 8.5, "height_m": 1.9, "thickness_mm": 200,
                 "finish_label": "Enduit taloché gris clair (RAL 7035)", "finish_colour_hex": "#c9c7bf"},
        "plot": {
            "boundary_points_m": [[0, 0], [20, 0], [20, 25], [0, 25]],
            "existing_structures": [{"label": "Maison existante",
                                      "points_m": [[3, 10], [13, 10], [13, 18], [3, 18]]}],
            "wall_points_m": [[0.5, 3.0], [9.0, 3.0]],
            "north_angle_deg": 20.0,
        },
    }


def test_build_project_from_answers_dict():
    project = intake.build_project(_sample_answers())
    assert project.commune == "Exemple-sur-Seine"
    assert project.wall.length_m == 8.5
    assert project.plot.boundary_points_m == [(0, 0), (20, 0), (20, 25), (0, 25)]
    assert project.plot.wall_points_m == [(0.5, 3.0), (9.0, 3.0)]
    assert project.plot.existing_structures[0]["label"] == "Maison existante"


def test_build_project_handles_missing_plot():
    answers = _sample_answers()
    del answers["plot"]
    project = intake.build_project(answers)
    assert project.plot.boundary_points_m == []


def test_generate_dossier_writes_expected_files(tmp_path):
    project = intake.build_project(_sample_answers())
    written = intake.generate_dossier(project, tmp_path, include_3d=False)

    assert (tmp_path / "project.json").exists()
    assert (tmp_path / "checklist.txt").exists()
    assert "DP5_elevation.png" in written or any("DP5_elevation" in w for w in written)
    assert "DP2_plan_masse.png" in written or any("DP2_plan_masse" in w for w in written)

    checklist = (tmp_path / "checklist.txt").read_text()
    assert "CERFA" in checklist
    assert "16702" in checklist
    assert project.commune in checklist
    assert "DP1" in checklist and "geoportail" in checklist

    saved = json.loads((tmp_path / "project.json").read_text())
    assert saved["commune"] == project.commune
    assert saved["wall"]["length_m"] == 8.5


def test_generate_dossier_without_3d_does_not_mention_3d_file():
    project = intake.build_project(_sample_answers())
    written = intake.generate_dossier(project, project_dir := __import__("tempfile").mkdtemp(), include_3d=False)
    assert not any("3d" in w.lower() for w in written if w.endswith(".png"))


def test_generate_dossier_with_parcel_lookup_enriches_checklist_and_skips_manual_dp1_line(tmp_path, monkeypatch):
    project = intake.build_project(_sample_answers())
    meta = {"lon": 2.35995, "lat": 48.855602, "label": "12 Rue de Rivoli 75004 Paris",
            "contenance_m2": 237, "computed_area_m2": 236.4, "idu": "75104000AM0008",
            "zone_code": "U", "zone_libelle": "Zone urbaine Sauvegardée",
            "reglement_pdf_filename": "75056_reglement_20131218_A.pdf"}

    def fake_render_dp1_png(lon, lat, address, out_path):
        Path(out_path).write_bytes(b"\x89PNG\r\n\x1a\nfake")
        return out_path

    monkeypatch.setattr("declaration_prealable.dp1_situation.render_dp1_png", fake_render_dp1_png)
    written = intake.generate_dossier(project, tmp_path, parcel_lookup_meta=meta)

    assert (tmp_path / "DP1_situation.png").exists()
    assert any("DP1_situation.png" in w for w in written)
    checklist = (tmp_path / "checklist.txt").read_text()
    assert "75104000AM0008" in checklist
    assert "237 m2" in checklist
    assert "75056_reglement_20131218_A.pdf" in checklist
    assert "export an annotated extract from geoportail" not in checklist  # manual-DP1 line suppressed

    saved = json.loads((tmp_path / "project.json").read_text())
    assert saved["parcel_lookup"]["idu"] == "75104000AM0008"


def test_generate_dossier_without_parcel_lookup_keeps_manual_dp1_line(tmp_path):
    project = intake.build_project(_sample_answers())
    written = intake.generate_dossier(project, tmp_path)
    assert not any("DP1_situation" in w for w in written)
    checklist = (tmp_path / "checklist.txt").read_text()
    assert "export an annotated extract from geoportail" in checklist


def _write_fake_photo(path):
    from PIL import Image
    Image.new("RGB", (800, 600), (120, 160, 200)).save(path, format="JPEG")


def test_generate_dossier_with_photos_writes_dp6_dp7_dp8(tmp_path):
    project = intake.build_project(_sample_answers())
    proche_path = tmp_path / "proche.jpg"
    _write_fake_photo(proche_path)
    photos = {"proche_path": str(proche_path), "lointain_path": None,
              "left_base_px": [200, 500], "right_base_px": [600, 500]}
    out_dir = tmp_path / "out"

    written = intake.generate_dossier(project, out_dir, wall_visible_from_public=True, photos=photos)

    assert (out_dir / "DP6_insertion.png").exists()
    assert (out_dir / "DP7_photo_proche.jpg").exists()
    assert not (out_dir / "DP8_photo_lointain.jpg").exists()
    assert any("DP6_insertion.png" in w for w in written)
    assert any("DP7_photo_proche.jpg" in w for w in written)
    assert any("DP8_photo_lointain.jpg skipped" in w for w in written)

    checklist = (out_dir / "checklist.txt").read_text()
    assert "VISIBLE from the public road" in checklist
    assert "R.431-10" in checklist

    saved = json.loads((out_dir / "project.json").read_text())
    assert saved["wall_visible_from_public"] is True


def test_generate_dossier_with_photos_including_lointain(tmp_path):
    project = intake.build_project(_sample_answers())
    proche_path, lointain_path = tmp_path / "proche.jpg", tmp_path / "lointain.jpg"
    _write_fake_photo(proche_path)
    _write_fake_photo(lointain_path)
    photos = {"proche_path": str(proche_path), "lointain_path": str(lointain_path),
              "left_base_px": [200, 500], "right_base_px": [600, 500]}
    out_dir = tmp_path / "out"

    written = intake.generate_dossier(project, out_dir, wall_visible_from_public=True, photos=photos)

    assert (out_dir / "DP8_photo_lointain.jpg").exists()
    assert any("DP8_photo_lointain.jpg" in w and "skipped" not in w for w in written)


def test_generate_dossier_not_visible_notes_dp6_dp7_dp8_not_required(tmp_path):
    project = intake.build_project(_sample_answers())
    written = intake.generate_dossier(project, tmp_path, wall_visible_from_public=False)
    assert not any("DP6" in w for w in written)
    checklist = (tmp_path / "checklist.txt").read_text()
    assert "NOT visible from the public road" in checklist


def test_generate_dossier_visibility_unspecified_prompts_to_confirm(tmp_path):
    project = intake.build_project(_sample_answers())
    intake.generate_dossier(project, tmp_path)
    checklist = (tmp_path / "checklist.txt").read_text()
    assert "not specified" in checklist


def test_cli_end_to_end_with_answers_file(tmp_path):
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(json.dumps(_sample_answers()))
    out_dir = tmp_path / "dossier"

    intake.main(["--answers", str(answers_path), "--out-dir", str(out_dir)])

    assert (out_dir / "project.json").exists()
    assert (out_dir / "checklist.txt").exists()
