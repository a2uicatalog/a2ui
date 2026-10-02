"""Real parcel data lookup for a déclaration préalable project, via free/keyless French government
open-data APIs -- see declaration_prealable/README.md for the sourced grounding behind each endpoint
(confirmed live 2026-10-02, real responses captured and tested, not assumed from documentation alone).

  geocode_address      -> BAN (api-adresse.data.gouv.fr)
  fetch_parcel          -> IGN APIcarto cadastre (apicarto.ign.fr/api/cadastre/parcelle)
  fetch_zone_urba       -> IGN APIcarto GPU (apicarto.ign.fr/api/gpu/zone-urba)
  fetch_dp1_screenshot_bytes -> IGN WMS (data.geopf.fr/wms-r), composited with Pillow

Honest limit: fetch_zone_urba returns the real PLU zone CLASSIFICATION and the applicable règlement
PDF's filename -- NOT parsed numeric rule values (height/material/colour limits). Those live only in
that PDF's prose, which is not reliably machine-extractable (non-standardised per-commune documents).
This module stops at the document pointer; a human still reads the PDF.
"""
import gzip
import json
import math
import urllib.parse
import urllib.request

BAN_URL = "https://api-adresse.data.gouv.fr/search/"
CADASTRE_URL = "https://apicarto.ign.fr/api/cadastre/parcelle"
ZONE_URBA_URL = "https://apicarto.ign.fr/api/gpu/zone-urba"
WMS_URL = "https://data.geopf.fr/wms-r"
BUILDINGS_URL_TMPL = "https://cadastre.data.gouv.fr/bundler/cadastre-etalab/communes/{citycode}/geojson/batiments"

_UA = {"User-Agent": "declaration-prealable (a2uicatalog.ai)"}


def _get_json(url, timeout=15):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    # cadastre.data.gouv.fr's building bundler sends real gzip bytes regardless of whether the
    # request advertised Accept-Encoding support (confirmed live 2026-10-02: urllib.request sends no
    # such header by default, yet the response still starts with the gzip magic bytes \x1f\x8b) --
    # detect and decompress explicitly rather than relying on the server to honour a header it
    # apparently ignores.
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def geocode_address(address, commune):
    """Returns (lon, lat, label, citycode) for the best-scored match, or raises ValueError if nothing
    matched. citycode is the real INSEE commune code BAN resolved the address to -- needed (not the
    cadastre parcelle response's own code_insee) because Paris/Lyon/Marseille address geocoding
    resolves to an ARRONDISSEMENT-level code (e.g. "75104"), which is what fetch_buildings needs to
    match the commune-level building dataset; the cadastre response's code_insee is the city-level
    code (e.g. "75056") and does not match that dataset's own per-arrondissement keying."""
    q = f"{address}, {commune}"
    url = BAN_URL + "?" + urllib.parse.urlencode({"q": q, "limit": 1})
    data = _get_json(url)
    features = data.get("features") or []
    if not features:
        raise ValueError(f"no BAN geocoding match for {q!r}")
    f = features[0]
    lon, lat = f["geometry"]["coordinates"]
    props = f["properties"]
    return lon, lat, props.get("label", q), props.get("citycode")


def fetch_parcel(lon, lat):
    """Returns the real cadastral parcel at (lon, lat): {polygon_wgs84, contenance_m2, idu, commune}.
    polygon_wgs84 is a flat list of (lon, lat) tuples for the parcel's outer ring (first ring of the
    first polygon -- a real parcel can be a MultiPolygon, but a single outer ring is what every piece
    downstream needs)."""
    geom = json.dumps({"type": "Point", "coordinates": [lon, lat]})
    url = CADASTRE_URL + "?" + urllib.parse.urlencode({"geom": geom})
    data = _get_json(url)
    features = data.get("features") or []
    if not features:
        raise ValueError(f"no cadastral parcel found at ({lon}, {lat})")
    f = features[0]
    geom_type = f["geometry"]["type"]
    coords = f["geometry"]["coordinates"]
    ring = coords[0][0] if geom_type == "MultiPolygon" else coords[0]
    polygon_wgs84 = [(pt[0], pt[1]) for pt in ring]
    props = f.get("properties", {})
    return {
        "polygon_wgs84": polygon_wgs84,
        "contenance_m2": props.get("contenance"),
        "idu": props.get("idu"),
        "commune": props.get("nom_com"),
    }


def wgs84_polygon_to_local_metres(polygon_wgs84, origin=None):
    """Flat local-tangent-plane reprojection -- accurate at parcel scale (tens of metres), no
    projection-library dependency needed. origin=(lon0, lat0), when given, MUST be used whenever more
    than one polygon needs to land in the same local frame (e.g. a parcel boundary and a building on
    it) -- each call defaulting to ITS OWN centroid (the pre-2026-10-02 behaviour) is only safe for a
    single, standalone polygon; reprojecting a parcel and a building independently would silently put
    them in two unrelated local coordinate systems, with no error, just a wrong drawing."""
    if origin is None:
        lon0 = sum(p[0] for p in polygon_wgs84) / len(polygon_wgs84)
        lat0 = sum(p[1] for p in polygon_wgs84) / len(polygon_wgs84)
    else:
        lon0, lat0 = origin
    m_per_deg_lat = 111320.0
    m_per_deg_lon = 111320.0 * math.cos(math.radians(lat0))
    return [((lon - lon0) * m_per_deg_lon, (lat - lat0) * m_per_deg_lat) for lon, lat in polygon_wgs84]


def _point_in_polygon(x, y, poly):
    """Standard ray-casting test -- pure Python, no geometry-library dependency (matches this
    module's own no-pyproj/no-shapely convention)."""
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _polygon_centroid(polygon_wgs84):
    return (sum(p[0] for p in polygon_wgs84) / len(polygon_wgs84),
            sum(p[1] for p in polygon_wgs84) / len(polygon_wgs84))


def fetch_buildings_on_parcel(citycode, parcel_polygon_wgs84):
    """Real building footprints on this parcel, via the Etalab cadastre.data.gouv.fr per-commune
    building bundle (apicarto's own "wfs-geoportail" module cannot serve BDTOPO reliably -- a real
    geometry-field configuration gap in that API, confirmed via its own documentation -- this Etalab
    bundler is the real, working alternative). Returns a list of polygon_wgs84 rings (outer ring only,
    matching fetch_parcel's own convention) for every building whose centroid falls inside the parcel
    -- confirmed live 2026-10-02 against a real Paris parcel. The bundle itself covers the WHOLE
    commune (thousands of buildings for a dense arrondissement), so this always filters before
    returning -- never hand the raw bundle to a caller."""
    url = BUILDINGS_URL_TMPL.format(citycode=citycode)
    data = _get_json(url, timeout=25)
    matches = []
    for f in data.get("features") or []:
        geom = f.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            continue
        ring = coords[0][0] if gtype == "MultiPolygon" else coords[0]
        polygon_wgs84 = [(pt[0], pt[1]) for pt in ring]
        cx, cy = _polygon_centroid(polygon_wgs84)
        if _point_in_polygon(cx, cy, parcel_polygon_wgs84):
            matches.append(polygon_wgs84)
    return matches


def polygon_area_m2(points_m):
    """Shoelace formula -- used as a real cross-check against the official contenance_m2, not just a
    sanity assertion that the function ran."""
    n = len(points_m)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = points_m[i]
        x2, y2 = points_m[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def fetch_zone_urba(lon, lat):
    """Real PLU zone classification + a pointer to the applicable règlement PDF -- NOT parsed rule
    values, see module docstring. Returns None if no zone is found (e.g. commune has no digitised
    PLU yet) rather than raising -- this is a legitimate, common real-world case, not an error."""
    geom = json.dumps({"type": "Point", "coordinates": [lon, lat]})
    url = ZONE_URBA_URL + "?" + urllib.parse.urlencode({"geom": geom})
    data = _get_json(url)
    features = data.get("features") or []
    if not features:
        return None
    props = features[0].get("properties", {})
    return {
        "zone_code": props.get("typezone"),
        "zone_libelle": props.get("libelle"),
        "zone_libelong": props.get("libelong"),
        "idurba": props.get("idurba"),
        "reglement_pdf_filename": props.get("nomfic"),
    }


def _draw_annotations(img_bytes, bbox, address):
    """Composites a north arrow, scale bar, and address caption onto the raw WMS tile -- raster
    (PIL ImageDraw), not hand-rolled SVG, since the base layer is already a raster tile (unlike
    dp5_elevation.py/dp2_plan_masse.py's own from-scratch SVG drawings)."""
    import io
    from PIL import Image, ImageDraw

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # North arrow -- fixed "up", WMS tiles in this CRS are north-up by convention.
    nx, ny = W - 40, 40
    draw.line([(nx, ny + 20), (nx, ny - 20)], fill=(20, 20, 20), width=3)
    draw.polygon([(nx, ny - 26), (nx - 7, ny - 14), (nx + 7, ny - 14)], fill=(20, 20, 20))
    draw.text((nx - 5, ny - 42), "N", fill=(20, 20, 20))

    # Scale bar -- real-world metres per pixel from the actual requested bbox.
    lon_min, lat_min, lon_max, lat_max = bbox
    lat_mid = (lat_min + lat_max) / 2
    width_m = (lon_max - lon_min) * 111320.0 * math.cos(math.radians(lat_mid))
    m_per_px = width_m / W
    bar_m = 20.0
    bar_px = bar_m / m_per_px
    by = H - 30
    draw.line([(20, by), (20 + bar_px, by)], fill=(20, 20, 20), width=3)
    draw.text((20, by - 16), f"{bar_m:.0f} m", fill=(20, 20, 20))

    # Caption band.
    draw.rectangle([(0, 0), (W, 24)], fill=(255, 255, 255))
    draw.text((6, 5), f"DP1 - {address}", fill=(20, 20, 20))

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def fetch_dp1_screenshot_bytes(lon, lat, address, radius_m=120, width=1200):
    """Real DP1 plan-de-situation image: an orthophoto centred on (lon, lat) with the cadastral
    parcel-boundary overlay composited on top, annotated with a north arrow, scale bar, and address
    caption. radius_m=120 gives a roughly 1/2000-1/4000 view -- well inside the official 1/5000-1/25000
    range, close enough to actually show the parcel rather than a dot."""
    lat_mid = lat
    d_lat = radius_m / 111320.0
    d_lon = radius_m / (111320.0 * math.cos(math.radians(lat_mid)))
    lon_min, lon_max = lon - d_lon, lon + d_lon
    lat_min, lat_max = lat - d_lat, lat + d_lat
    bbox = (lon_min, lat_min, lon_max, lat_max)
    height = width

    def _wms_get(layers, fmt, transparent=False):
        params = {
            "LAYERS": layers, "FORMAT": fmt, "SERVICE": "WMS", "VERSION": "1.3.0",
            "REQUEST": "GetMap", "STYLES": "", "CRS": "EPSG:4326",
            "BBOX": f"{lat_min},{lon_min},{lat_max},{lon_max}",
            "WIDTH": str(width), "HEIGHT": str(height),
        }
        if transparent:
            params["TRANSPARENT"] = "true"
        url = WMS_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read()

    ortho_bytes = _wms_get("ORTHOIMAGERY.ORTHOPHOTOS", "image/jpeg")

    import io
    from PIL import Image
    base = Image.open(io.BytesIO(ortho_bytes)).convert("RGBA")
    try:
        # The IGN WMS server returns this layer as an OPAQUE white-background image even with
        # TRANSPARENT=true requested (confirmed live 2026-10-02: PIL reports mode "L", no alpha
        # channel at all) -- a real server quirk, not a request-parameter bug. Chroma-key the
        # near-white background to transparent ourselves before compositing, so the black
        # parcel-boundary hatching/lines still overlay the orthophoto instead of replacing it.
        overlay_bytes = _wms_get("CADASTRALPARCELS.PARCELS", "image/png", transparent=True)
        overlay = Image.open(io.BytesIO(overlay_bytes)).convert("L").resize(base.size)
        overlay_rgba = Image.new("RGBA", overlay.size)
        overlay_rgba.paste((20, 20, 20, 255), mask=overlay.point(lambda p: 255 - p))
        base = Image.alpha_composite(base, overlay_rgba)
    except Exception:
        pass  # overlay is a nice-to-have; the orthophoto alone is still a valid DP1 base

    out = io.BytesIO()
    base.convert("RGB").save(out, format="PNG")
    return _draw_annotations(out.getvalue(), bbox, address)


def build_plot_from_address(address, commune, wall_length_m, wall_offset_m=1.0):
    """Orchestrates geocode -> parcel -> reprojection -> zone lookup -> real building footprints into
    a populated PlotGeometry plus a metadata dict for the UI/checklist to surface. wall_points_m stays
    the caller's own data (not government-sourced); boundary_points_m AND existing_structures are both
    real, reprojected onto the SAME shared local origin (the parcel's own centroid) -- see
    wgs84_polygon_to_local_metres's own docstring for why a shared origin is required, not optional,
    once more than one polygon is being placed on the same drawing."""
    from declaration_prealable.project_schema import PlotGeometry

    lon, lat, label, citycode = geocode_address(address, commune)
    parcel = fetch_parcel(lon, lat)
    origin = _polygon_centroid(parcel["polygon_wgs84"])
    boundary_m = wgs84_polygon_to_local_metres(parcel["polygon_wgs84"], origin=origin)
    zone = fetch_zone_urba(lon, lat)

    existing_structures = []
    if citycode:
        try:
            for i, building_wgs84 in enumerate(fetch_buildings_on_parcel(citycode, parcel["polygon_wgs84"])):
                building_m = wgs84_polygon_to_local_metres(building_wgs84, origin=origin)
                label_n = "Bâtiment existant" if i == 0 else f"Bâtiment existant {i + 1}"
                existing_structures.append({"label": label_n, "points_m": building_m})
        except Exception:
            pass  # real building footprints are a nice-to-have -- a fetch failure shouldn't block
                  # the rest of the lookup, same posture as the DP1 overlay's own failure handling

    min_x = min(p[0] for p in boundary_m)
    min_y = min(p[1] for p in boundary_m)
    wx0 = min_x + wall_offset_m
    wy0 = min_y + wall_offset_m
    wall_points_m = [(wx0, wy0), (wx0 + wall_length_m, wy0)]

    plot = PlotGeometry(boundary_points_m=boundary_m, existing_structures=existing_structures,
                         wall_points_m=wall_points_m, north_angle_deg=0.0)
    meta = {
        "label": label, "lon": lon, "lat": lat,
        "contenance_m2": parcel["contenance_m2"],
        "computed_area_m2": round(polygon_area_m2(boundary_m), 1),
        "idu": parcel["idu"],
        "buildings_found": len(existing_structures),
        "zone_code": zone["zone_code"] if zone else None,
        "zone_libelle": zone["zone_libelong"] if zone else None,
        "reglement_pdf_filename": zone["reglement_pdf_filename"] if zone else None,
    }
    return plot, meta
