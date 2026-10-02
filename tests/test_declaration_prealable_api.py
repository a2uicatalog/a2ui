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


# -- /generate with DP6/DP7/DP8 photos -- see declaration_prealable/dp6_insertion.py's own module
# docstring for why these are required whenever the wall is visible from the public road, not only in
# a secteur protégé.

def _fake_jpeg_base64(width=400, height=300):
    import base64
    import io
    from PIL import Image
    img = Image.new("RGB", (width, height), (100, 140, 180))
    out = io.BytesIO()
    img.save(out, format="JPEG")
    return base64.b64encode(out.getvalue()).decode()


def test_generate_without_photos_omits_dp6_dp7_dp8_keys(client):
    r = client.post("/generate", json=_valid_body(), headers={"X-Render-Token": TOKEN})
    assert r.status_code == 200
    data = r.get_json()
    for key in ("dp6_png_base64", "dp7_jpeg_base64", "dp8_jpeg_base64"):
        assert key not in data


def test_generate_with_photo_proche_returns_dp6_and_dp7(client):
    body = _valid_body()
    body["photoProcheBase64"] = _fake_jpeg_base64()
    body["wallBaseLeftPx"] = [100, 250]
    body["wallBaseRightPx"] = [300, 250]
    r = client.post("/generate", json=body, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    dp6_bytes = base64.b64decode(data["dp6_png_base64"])
    assert dp6_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    dp7_bytes = base64.b64decode(data["dp7_jpeg_base64"])
    assert dp7_bytes[:3] == b"\xff\xd8\xff"
    assert "dp8_jpeg_base64" not in data  # no distant photo given -> not returned


def test_generate_with_both_photos_returns_dp6_dp7_dp8(client):
    body = _valid_body()
    body["photoProcheBase64"] = _fake_jpeg_base64()
    body["wallBaseLeftPx"] = [100, 250]
    body["wallBaseRightPx"] = [300, 250]
    body["photoLointainBase64"] = _fake_jpeg_base64()
    r = client.post("/generate", json=body, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 200
    data = r.get_json()
    assert base64.b64decode(data["dp8_jpeg_base64"])[:3] == b"\xff\xd8\xff"


def test_generate_rejects_photo_proche_without_base_points(client):
    body = _valid_body()
    body["photoProcheBase64"] = _fake_jpeg_base64()
    r = client.post("/generate", json=body, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400
    assert "wallBaseLeftPx" in r.get_json()["error"]


def test_generate_rejects_coincident_base_points(client):
    body = _valid_body()
    body["photoProcheBase64"] = _fake_jpeg_base64()
    body["wallBaseLeftPx"] = [200, 250]
    body["wallBaseRightPx"] = [200, 250]
    r = client.post("/generate", json=body, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400
    assert "too close" in r.get_json()["error"]


def test_generate_rejects_bad_base64_photo(client):
    body = _valid_body()
    body["photoProcheBase64"] = "not-valid-base64!!!"
    body["wallBaseLeftPx"] = [100, 250]
    body["wallBaseRightPx"] = [300, 250]
    r = client.post("/generate", json=body, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400


def test_generate_rejects_oversized_photo(client):
    body = _valid_body()
    body["photoProcheBase64"] = base64.b64encode(b"x" * (dp_server.MAX_PHOTO_BYTES + 1)).decode()
    body["wallBaseLeftPx"] = [100, 250]
    body["wallBaseRightPx"] = [300, 250]
    r = client.post("/generate", json=body, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400
    assert "exceeds" in r.get_json()["error"]


# -- /lookup-parcel -- parcel_lookup's own outbound network calls are mocked, same discipline as
# /generate never hitting real GCP in a unit test.

_REAL_PLOT = type("P", (), {"boundary_points_m": [(0, 0), (10, 0), (10, 10), (0, 10)],
                             "wall_points_m": [(1, 1), (6, 1)],
                             "existing_structures": [{"label": "Bâtiment existant",
                                                       "points_m": [(2, 2), (8, 2), (8, 8), (2, 8)]}]})()
_REAL_META = {"lon": 2.35995, "lat": 48.855602, "label": "12 Rue de Rivoli 75004 Paris",
              "contenance_m2": 237, "computed_area_m2": 236.4, "idu": "75104000AM0008",
              "zone_code": "U", "zone_libelle": "Zone urbaine Sauvegardée",
              "reglement_pdf_filename": "75056_reglement_20131218_A.pdf"}


def test_lookup_parcel_rejects_missing_token(client):
    r = client.post("/lookup-parcel", json={"address": "1 rue X", "commune": "Paris"})
    assert r.status_code == 403


def test_lookup_parcel_rejects_missing_fields(client):
    r = client.post("/lookup-parcel", json={}, headers={"X-Render-Token": TOKEN})
    assert r.status_code == 400


def test_lookup_parcel_succeeds_and_returns_real_shape(client, monkeypatch):
    monkeypatch.setattr(dp_server.parcel_lookup, "build_plot_from_address",
                         lambda address, commune, length, offset: (_REAL_PLOT, _REAL_META))
    monkeypatch.setattr(dp_server.dp1_situation, "render_dp1_png_bytes",
                         lambda lon, lat, address: b"\x89PNG\r\n\x1a\nfake")

    r = client.post("/lookup-parcel", json={"address": "12 rue de rivoli", "commune": "paris",
                                             "wallLengthM": 5.0, "wallOffsetM": 1.0},
                     headers={"X-Render-Token": TOKEN})
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert data["contenanceM2"] == 237
    assert data["zoneLibelle"] == "Zone urbaine Sauvegardée"
    assert data["reglementPdfFilename"] == "75056_reglement_20131218_A.pdf"
    assert data["boundaryPointsM"] == [[0, 0], [10, 0], [10, 10], [0, 10]]
    # Real bug found live 2026-10-02: existingStructures (the real building footprint) was never
    # returned to the frontend at all -- confirm it actually flows through the response now.
    assert data["existingStructures"] == [{"label": "Bâtiment existant",
                                            "points_m": [[2, 2], [8, 2], [8, 8], [2, 8]]}]
    png_bytes = base64.b64decode(data["dp1PngBase64"])
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert "aerialPhotoJpegBase64" not in data  # not requested -> not fetched, not returned


def test_lookup_parcel_includes_raw_aerial_when_requested(client, monkeypatch):
    monkeypatch.setattr(dp_server.parcel_lookup, "build_plot_from_address",
                         lambda address, commune, length, offset: (_REAL_PLOT, _REAL_META))
    monkeypatch.setattr(dp_server.dp1_situation, "render_dp1_png_bytes",
                         lambda lon, lat, address: b"\x89PNG\r\n\x1a\nfake")
    calls = []
    monkeypatch.setattr(dp_server.parcel_lookup, "fetch_aerial_photo_bytes",
                         lambda lon, lat: calls.append((lon, lat)) or b"\xff\xd8\xff\xe0fakejpeg")

    r = client.post("/lookup-parcel", json={"address": "12 rue de rivoli", "commune": "paris",
                                             "includeRawAerial": True},
                     headers={"X-Render-Token": TOKEN})
    assert r.status_code == 200
    data = r.get_json()
    assert len(calls) == 1  # only fetched when actually requested
    jpeg_bytes = base64.b64decode(data["aerialPhotoJpegBase64"])
    assert jpeg_bytes[:3] == b"\xff\xd8\xff"


def test_lookup_parcel_reports_upstream_failure_without_crashing(client, monkeypatch):
    def fail(*a, **kw):
        raise ValueError("no BAN geocoding match")
    monkeypatch.setattr(dp_server.parcel_lookup, "build_plot_from_address", fail)

    r = client.post("/lookup-parcel", json={"address": "nowhere", "commune": "nowhere"},
                     headers={"X-Render-Token": TOKEN})
    assert r.status_code == 502
    assert r.get_json()["ok"] is False


def test_lookup_parcel_options_preflight(client):
    r = client.options("/lookup-parcel")
    assert r.headers.get("Access-Control-Allow-Origin") == "*"
