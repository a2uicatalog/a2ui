"""Tests for declaration-prealable-api/server.py -- the lightweight, synchronous (no Job/GCS, unlike
premium-render-api) Cloud Run Service backing declaration_prealable's web intake form. Flask-test-client
style mirroring tests/test_premium_render_api.py's own convention for this estate's other Cloud Run
services.
"""
import base64
import importlib.util
import sys
from pathlib import Path

import pytest

DP_API = Path(__file__).parent.parent / "declaration-prealable-api"
# server.py does `from declaration_prealable import ...` at module scope -- needs the repo root
# (declaration_prealable's own parent) on sys.path BEFORE the module executes.
sys.path.insert(0, str(DP_API.parent))

pytest.importorskip("flask", reason="declaration-prealable-api's own dependency, not the base repo's")
pytest.importorskip("cairosvg", reason="declaration-prealable-api's own dependency, not the base repo's")

# Loaded via importlib with a UNIQUE module name, not a bare `import server` -- see
# tests/test_cloud_run_renderer.py's own comment on this exact spot: this repo has multiple
# subprojects each with their own server.py, and a bare `import server` collides across them in
# sys.modules (confirmed live 2026-10-01, running this file alongside test_premium_render_api.py).
_spec = importlib.util.spec_from_file_location("declaration_prealable_api_server", DP_API / "server.py")
dp_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dp_server)

TOKEN = "test-signing-key"
dp_server.DP_SIGNING_KEY = TOKEN


@pytest.fixture()
def client():
    return dp_server.app.test_client()


def _valid_body(**wall_overrides):
    wall = {"length_m": 8.5, "height_m": 1.9, "finish_label": "Enduit taloché gris clair (RAL 7035)",
            "finish_colour_hex": "#c9c7bf"}
    wall.update(wall_overrides)
    return {
        "commune": "Exemple-sur-Seine", "address": "12 rue des Tilleuls", "date_iso": "2026-10-01",
        "wall": wall,
        "plot": {
            "boundary_points_m": [[0, 0], [20, 0], [20, 25], [0, 25]],
            "existing_structures": [{"label": "Maison existante",
                                      "points_m": [[3, 10], [13, 10], [13, 18], [3, 18]]}],
            "wall_points_m": [[0.5, 3.0], [9.0, 3.0]],
            "north_angle_deg": 20.0,
        },
    }


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_generate_rejects_missing_token(client):
    r = client.post("/generate", json=_valid_body())
    assert r.status_code == 403
    assert r.get_json()["ok"] is False


def test_generate_rejects_wrong_token(client):
    r = client.post("/generate", json=_valid_body(), headers={"X-Render-Token": "wrong"})
    assert r.status_code == 403


def test_generate_rejects_missing_fields(client):
    r = client.post("/generate", json={"wall": {}}, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400
    assert "commune" in r.get_json()["error"]


def test_generate_rejects_bad_block_id(client):
    r = client.post("/generate", json=_valid_body(block_id="not-a-real-block"),
                     headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400
    assert "block_id" in r.get_json()["error"]


def test_generate_rejects_out_of_range_dimension(client):
    r = client.post("/generate", json=_valid_body(height_m=999), headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400
    assert "height_m" in r.get_json()["error"]


def test_generate_rejects_oversized_boundary(client):
    body = _valid_body()
    body["plot"]["boundary_points_m"] = [[i, i] for i in range(100)]
    r = client.post("/generate", json=body, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400


def test_generate_succeeds_and_returns_real_pngs(client):
    r = client.post("/generate", json=_valid_body(), headers={"X-Render-Token": TOKEN})
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    for key in ("dp2_png_base64", "dp5_png_base64"):
        png_bytes = base64.b64decode(data[key])
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_generate_works_with_empty_plot():
    client = dp_server.app.test_client()
    body = {"commune": "X", "address": "Y", "date_iso": "2026-10-01",
            "wall": {"length_m": 3.0, "height_m": 1.5}, "plot": {}}
    r = client.post("/generate", json=body, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_cors_headers_present(client):
    r = client.post("/generate", json=_valid_body(), headers={"X-Render-Token": TOKEN})
    assert r.headers.get("Access-Control-Allow-Origin") == "*"


def test_options_preflight(client):
    r = client.options("/generate")
    assert r.headers.get("Access-Control-Allow-Origin") == "*"
