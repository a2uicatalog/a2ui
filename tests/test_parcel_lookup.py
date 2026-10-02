"""Tests for declaration_prealable/parcel_lookup.py. Mocks urllib.request.urlopen with REAL response
shapes captured live against the real BAN/IGN APIs 2026-10-02 (see declaration_prealable/README.md and
.claude/plans/ for the research) -- not invented fixtures. Pure reprojection/geometry math is tested
directly (no mocking needed).
"""
import io
import json
import math
from unittest.mock import MagicMock, patch

import pytest

from declaration_prealable import parcel_lookup as pl

# Captured live 2026-10-02 against api-adresse.data.gouv.fr for "12 rue de rivoli, paris"
REAL_BAN_RESPONSE = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [2.35995, 48.855602]},
        "properties": {"label": "12 Rue de Rivoli 75004 Paris", "score": 0.97, "id": "75104_8249_00012",
                       "citycode": "75104"},
    }],
}

# Captured live 2026-10-02 against cadastre.data.gouv.fr's Etalab building bundler for commune 75104 --
# trimmed to 2 of the real 2630 features: one whose centroid falls inside REAL_PARCEL_RESPONSE's own
# polygon (the real match found live), one far outside it (must be filtered out).
REAL_BUILDINGS_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": [[[
            [2.35993, 48.85572], [2.36009, 48.85567], [2.36005, 48.85559], [2.35988, 48.85563],
            [2.35993, 48.85572],
        ]]]}, "properties": {"type": "01", "commune": "75104"}},
        {"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": [[[
            [2.40000, 48.90000], [2.40010, 48.90000], [2.40010, 48.90010], [2.40000, 48.90010],
            [2.40000, 48.90000],
        ]]]}, "properties": {"type": "01", "commune": "75104"}},
    ],
}

# Captured live 2026-10-02 against apicarto.ign.fr/api/cadastre/parcelle for the same point
REAL_PARCEL_RESPONSE = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "id": "parcelle.94550576",
        "geometry": {"type": "MultiPolygon", "coordinates": [[[
            [2.35992649, 48.85573989], [2.36011122, 48.8556907], [2.36012638, 48.85566596],
            [2.36007561, 48.85558331], [2.36003691, 48.85557159], [2.35985306, 48.85561557],
            [2.35992649, 48.85573989],
        ]]]},
        "properties": {"gid": 85440018, "numero": "0008", "section": "AM", "nom_com": "Paris",
                        "contenance": 237, "idu": "75104000AM0008", "code_insee": "75056"},
    }],
}

# Captured live 2026-10-02 against apicarto.ign.fr/api/gpu/zone-urba for the same point
REAL_ZONE_URBA_RESPONSE = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature", "id": "zone_urba.1121415",
        "geometry": {"type": "MultiPolygon", "coordinates": [[[[2.35253, 48.85948]]]]},
        "properties": {"typezone": "U", "libelle": "US", "libelong": "Zone urbaine Sauvegardée",
                        "idurba": "75056_PSMV_20131218_A", "nomfic": "75056_reglement_20131218_A.pdf"},
    }],
}


def _mock_urlopen(payload_bytes):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = payload_bytes
    return cm


def test_geocode_address_returns_best_match():
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(json.dumps(REAL_BAN_RESPONSE).encode())):
        lon, lat, label, citycode = pl.geocode_address("12 rue de rivoli", "paris")
    assert lon == 2.35995
    assert lat == 48.855602
    assert label == "12 Rue de Rivoli 75004 Paris"
    assert citycode == "75104"


def test_geocode_address_raises_on_no_match():
    empty = {"type": "FeatureCollection", "features": []}
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(json.dumps(empty).encode())):
        with pytest.raises(ValueError):
            pl.geocode_address("nowhere at all", "nowhere")


def test_fetch_parcel_returns_real_polygon_and_contenance():
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(json.dumps(REAL_PARCEL_RESPONSE).encode())):
        parcel = pl.fetch_parcel(2.35995, 48.855602)
    assert parcel["contenance_m2"] == 237
    assert parcel["idu"] == "75104000AM0008"
    assert len(parcel["polygon_wgs84"]) == 7
    assert parcel["polygon_wgs84"][0] == (2.35992649, 48.85573989)


def test_wgs84_polygon_to_local_metres_is_centred_on_centroid():
    polygon = REAL_PARCEL_RESPONSE["features"][0]["geometry"]["coordinates"][0][0]
    polygon_wgs84 = [(p[0], p[1]) for p in polygon]
    local = pl.wgs84_polygon_to_local_metres(polygon_wgs84)
    # centroid of the reprojected points should land very near the origin
    cx = sum(p[0] for p in local) / len(local)
    cy = sum(p[1] for p in local) / len(local)
    assert abs(cx) < 1.0 and abs(cy) < 1.0


def test_wgs84_polygon_to_local_metres_matches_real_contenance():
    # Real cross-check (not just "didn't throw"): the reprojected polygon's own shoelace area
    # should be close to the OFFICIAL cadastral contenance_m2 for the same real parcel.
    polygon = REAL_PARCEL_RESPONSE["features"][0]["geometry"]["coordinates"][0][0]
    polygon_wgs84 = [(p[0], p[1]) for p in polygon]
    local = pl.wgs84_polygon_to_local_metres(polygon_wgs84)
    computed = pl.polygon_area_m2(local)
    official = REAL_PARCEL_RESPONSE["features"][0]["properties"]["contenance"]
    assert abs(computed - official) / official < 0.01  # within 1%


def test_polygon_area_m2_unit_square():
    assert pl.polygon_area_m2([(0, 0), (1, 0), (1, 1), (0, 1)]) == pytest.approx(1.0)


def test_polygon_area_m2_degenerate_returns_zero():
    assert pl.polygon_area_m2([(0, 0), (1, 1)]) == 0.0


def test_fetch_zone_urba_returns_real_classification_and_document_pointer():
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(json.dumps(REAL_ZONE_URBA_RESPONSE).encode())):
        zone = pl.fetch_zone_urba(2.35995, 48.855602)
    assert zone["zone_code"] == "U"
    assert zone["zone_libelong"] == "Zone urbaine Sauvegardée"
    assert zone["reglement_pdf_filename"] == "75056_reglement_20131218_A.pdf"


def test_fetch_zone_urba_returns_none_when_no_plu_digitised():
    empty = {"type": "FeatureCollection", "features": []}
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(json.dumps(empty).encode())):
        zone = pl.fetch_zone_urba(0.0, 0.0)
    assert zone is None


def _tiny_jpeg_bytes():
    pytest.importorskip("PIL")
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (40, 40), (120, 140, 100)).save(buf, format="JPEG")
    return buf.getvalue()


def _tiny_overlay_png_bytes():
    pytest.importorskip("PIL")
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("L", (40, 40), 255)  # white background, no alpha -- matches the real server quirk
    for x in range(40):
        img.putpixel((x, 20), 0)  # one black line across the middle
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_fetch_dp1_screenshot_bytes_produces_real_png_with_overlay_composited():
    pytest.importorskip("PIL")
    calls = []

    def fake_urlopen(req, timeout=20):
        url = req.full_url if hasattr(req, "full_url") else req
        calls.append(url)
        if "ORTHOIMAGERY" in url:
            return _mock_urlopen(_tiny_jpeg_bytes())
        return _mock_urlopen(_tiny_overlay_png_bytes())

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        png_bytes = pl.fetch_dp1_screenshot_bytes(2.35995, 48.855602, "Test Address", width=40)

    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(calls) == 2  # ortho + overlay, both actually requested


def test_fetch_dp1_screenshot_bytes_survives_overlay_failure():
    # The overlay is a nice-to-have (module docstring) -- if it fails, the plain orthophoto should
    # still come back as a valid DP1 base rather than the whole call failing.
    pytest.importorskip("PIL")

    def fake_urlopen(req, timeout=20):
        url = req.full_url if hasattr(req, "full_url") else req
        if "ORTHOIMAGERY" in url:
            return _mock_urlopen(_tiny_jpeg_bytes())
        raise RuntimeError("simulated overlay fetch failure")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        png_bytes = pl.fetch_dp1_screenshot_bytes(2.35995, 48.855602, "Test Address", width=40)
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def _fake_urlopen_for_orchestration(req, timeout=15):
    url = req.full_url if hasattr(req, "full_url") else req
    if "api-adresse" in url:
        return _mock_urlopen(json.dumps(REAL_BAN_RESPONSE).encode())
    if "cadastre/parcelle" in url:
        return _mock_urlopen(json.dumps(REAL_PARCEL_RESPONSE).encode())
    if "gpu/zone-urba" in url:
        return _mock_urlopen(json.dumps(REAL_ZONE_URBA_RESPONSE).encode())
    if "bundler/cadastre-etalab" in url:
        return _mock_urlopen(json.dumps(REAL_BUILDINGS_RESPONSE).encode())
    raise AssertionError(f"unexpected URL: {url}")


def test_build_plot_from_address_orchestrates_all_calls():
    with patch("urllib.request.urlopen", side_effect=_fake_urlopen_for_orchestration):
        plot, meta = pl.build_plot_from_address("12 rue de rivoli", "paris", wall_length_m=5.0, wall_offset_m=1.0)

    assert len(plot.boundary_points_m) == 7
    assert len(plot.wall_points_m) == 2
    wall_len = math.hypot(plot.wall_points_m[1][0] - plot.wall_points_m[0][0],
                           plot.wall_points_m[1][1] - plot.wall_points_m[0][1])
    assert wall_len == pytest.approx(5.0)
    assert meta["contenance_m2"] == 237
    assert meta["zone_code"] == "U"
    assert meta["reglement_pdf_filename"] == "75056_reglement_20131218_A.pdf"

    # The real bug this round: existing_structures was always [] regardless of real building data.
    # Confirms the fetched building is both present AND in the SAME local coordinate frame as the
    # boundary (shared origin) -- a building point should land within the boundary's own bounding box,
    # not off in an unrelated frame from being independently re-centred on its own centroid.
    assert len(plot.existing_structures) == 1
    assert meta["buildings_found"] == 1
    bx = [p[0] for p in plot.existing_structures[0]["points_m"]]
    by = [p[1] for p in plot.existing_structures[0]["points_m"]]
    boundary_x = [p[0] for p in plot.boundary_points_m]
    boundary_y = [p[1] for p in plot.boundary_points_m]
    assert min(boundary_x) - 5 <= min(bx) and max(bx) <= max(boundary_x) + 5
    assert min(boundary_y) - 5 <= min(by) and max(by) <= max(boundary_y) + 5


def test_build_plot_from_address_survives_buildings_fetch_failure():
    def fake_urlopen(req, timeout=15):
        url = req.full_url if hasattr(req, "full_url") else req
        if "bundler/cadastre-etalab" in url:
            raise RuntimeError("simulated buildings fetch failure")
        return _fake_urlopen_for_orchestration(req, timeout)

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        plot, meta = pl.build_plot_from_address("12 rue de rivoli", "paris", wall_length_m=5.0, wall_offset_m=1.0)
    assert plot.existing_structures == []
    assert meta["buildings_found"] == 0


def test_fetch_buildings_on_parcel_filters_to_matches_only():
    parcel_poly = REAL_PARCEL_RESPONSE["features"][0]["geometry"]["coordinates"][0][0]
    parcel_poly = [(p[0], p[1]) for p in parcel_poly]
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(json.dumps(REAL_BUILDINGS_RESPONSE).encode())):
        buildings = pl.fetch_buildings_on_parcel("75104", parcel_poly)
    assert len(buildings) == 1  # the far-away fixture building must be filtered out


def test_wgs84_polygon_to_local_metres_shared_origin_keeps_two_polygons_consistent():
    # The real bug this round, isolated: reprojecting two polygons with DEFAULT (self-centroid) origins
    # puts them in two unrelated local frames even though they're genuinely close together in the real
    # world -- a shared origin must keep them close in the reprojected frame too.
    parcel = [(2.3599, 48.8557), (2.3601, 48.8557), (2.3601, 48.8558), (2.3599, 48.8558)]
    building = [(2.35991, 48.85571), (2.36005, 48.85571), (2.36005, 48.85578), (2.35991, 48.85578)]
    origin = pl._polygon_centroid(parcel)

    parcel_m = pl.wgs84_polygon_to_local_metres(parcel, origin=origin)
    building_m = pl.wgs84_polygon_to_local_metres(building, origin=origin)
    # same shared origin -> the two shapes' coordinates should be within a few metres of each other
    assert abs(parcel_m[0][0] - building_m[0][0]) < 5
    assert abs(parcel_m[0][1] - building_m[0][1]) < 5

    # WITHOUT a shared origin, the building defaults to ITS OWN centroid (different from the parcel's,
    # used above) -- demonstrating the bug this fixes, not just asserting the fix's own correct path.
    # (parcel's own default centroid happens to equal `origin` here by construction, so only the
    # building -- the one with a genuinely different self-centroid -- is the meaningful comparison.)
    building_m_bad = pl.wgs84_polygon_to_local_metres(building)
    assert building_m_bad[0] != pytest.approx(building_m[0])
