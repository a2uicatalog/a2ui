"""declaration-prealable-api -- lightweight (no GPU/bpy, no Playwright) Cloud Run SERVICE backing
declaration_prealable's web intake form on full.a2uicatalog.ai. A single synchronous POST, unlike
premium-render-api's async trigger+poll Job pattern -- cairosvg (the only real dependency) runs in well
under a second, so there's no Job/GCS/signed-URL round trip; both generated PNGs are base64-encoded
directly into the JSON response.

Access control: full.a2uicatalog.ai itself is gated by Cloudflare Access, but that only protects the
STATIC PAGE -- this service's own Cloud Run URL is reachable independently of that gate. Reuses
cloud-run-renderer/server.py's own X-Render-Token mechanism (HMAC compare against a Secret-Manager-bound
signing key) rather than inventing a new one -- Curtis's own choice, 2026-10-01, over premium-render-api's
open-plus-rate-limit posture, specifically because this backend's URL is NOT advertised the way a public
product feature's is.
"""
import hashlib  # noqa: F401 -- kept alongside hmac for parity with cloud-run-renderer's own imports
import hmac
import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, request  # noqa: E402

from declaration_prealable import dp1_situation, dp2_plan_masse, dp5_elevation, parcel_lookup  # noqa: E402
from declaration_prealable.intake import build_project  # noqa: E402

# Same posture as cloud-run-renderer/server.py's own RENDER_SIGNING_KEY: a Secret-Manager-bound env var
# in real deployments, an ephemeral per-process key (with a loud warning) for local testing only -- see
# that file's own comment for why an ephemeral key WOULD silently break verification across multiple
# Cloud Run instances in production.
DP_SIGNING_KEY = os.environ.get("DP_SIGNING_KEY", "")
if not DP_SIGNING_KEY:
    DP_SIGNING_KEY = secrets.token_hex(32)
    print("WARNING: DP_SIGNING_KEY not set -- generated an ephemeral per-process key. Fine for local "
          "testing; in a real multi-instance Cloud Run deployment this WILL cause spurious \"invalid "
          "token\" failures. Set DP_SIGNING_KEY explicitly (Secret Manager, --set-secrets) before "
          "deploying.", flush=True)

# Real, scoped caps -- mirrors premium-render-api's own MAX_PARTS_MODEL_ROWS discipline. A wall/plot
# is always small input; these exist to reject a malformed or pathological body cheaply, not because
# any real project is expected to approach them.
MAX_STRING_LEN = 200
MAX_POINTS = 50
MAX_STRUCTURES = 10
MAX_COORD_M = 1000.0
MAX_LENGTH_M = 100.0
MAX_HEIGHT_M = 10.0
MAX_THICKNESS_MM = 1000.0

app = Flask(__name__)


def _forbidden(msg):
    return jsonify({"ok": False, "error": msg}), 403


def _require_token():
    # HEADER ONLY, deliberately -- same reasoning as cloud-run-renderer's own _require_token: a query
    # param would land in Cloud Run request logs and any log sink.
    supplied = request.headers.get("X-Render-Token", "")
    if supplied and hmac.compare_digest(supplied, DP_SIGNING_KEY):
        return None
    return _forbidden("missing or invalid X-Render-Token")


def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Render-Token"
    return resp


@app.after_request
def _add_cors(resp):
    return _cors(resp)


class ValidationError(ValueError):
    pass


def _str(value, name, default=None):
    if value is None and default is not None:
        value = default
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_STRING_LEN:
        raise ValidationError(f"{name} must be a non-empty string under {MAX_STRING_LEN} chars")
    return value


def _num(value, name, lo, hi):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a number")
    if not (lo <= v <= hi):
        raise ValidationError(f"{name} must be between {lo} and {hi}")
    return v


def _point(p, name):
    if not (isinstance(p, (list, tuple)) and len(p) == 2):
        raise ValidationError(f"{name} must be a [x, y] pair")
    return [_num(p[0], f"{name}.x", -MAX_COORD_M, MAX_COORD_M),
            _num(p[1], f"{name}.y", -MAX_COORD_M, MAX_COORD_M)]


def _points(points, name):
    if not isinstance(points, list) or len(points) > MAX_POINTS:
        raise ValidationError(f"{name} must be an array of at most {MAX_POINTS} points")
    return [_point(p, f"{name}[]") for p in points]


def validate_answers(body):
    """Mirrors intake.collect_answers_interactively()'s output shape exactly -- the same dict
    build_project() already consumes, so validation and construction never drift against each other."""
    if not isinstance(body, dict):
        raise ValidationError("body must be a JSON object")

    wall = body.get("wall")
    if not isinstance(wall, dict):
        raise ValidationError("wall must be an object")
    block_id = wall.get("block_id", "parpaing200")
    if block_id not in dp5_elevation.BLOCKS:
        raise ValidationError(f"wall.block_id must be one of {list(dp5_elevation.BLOCKS)}")
    bond = wall.get("bond", "running")
    if bond not in ("running", "stack"):
        raise ValidationError('wall.bond must be "running" or "stack"')
    project_type = wall.get("project_type", "cloture")
    if project_type not in ("cloture", "soutenement"):
        raise ValidationError('wall.project_type must be "cloture" or "soutenement"')

    plot = body.get("plot") or {}
    if not isinstance(plot, dict):
        raise ValidationError("plot must be an object")
    structures = plot.get("existing_structures") or []
    if not isinstance(structures, list) or len(structures) > MAX_STRUCTURES:
        raise ValidationError(f"plot.existing_structures must be an array of at most {MAX_STRUCTURES}")
    validated_structures = []
    for s in structures:
        if not isinstance(s, dict):
            raise ValidationError("each existing_structures entry must be an object")
        validated_structures.append({
            "label": _str(s.get("label"), "structure.label", default="Structure"),
            "points_m": _points(s.get("points_m") or [], "structure.points_m"),
        })

    wall_points = plot.get("wall_points_m") or []
    if len(wall_points) not in (0, 2):
        raise ValidationError("plot.wall_points_m must have exactly 2 points, or be omitted")

    return {
        "commune": _str(body.get("commune"), "commune"),
        "address": _str(body.get("address"), "address"),
        "date_iso": _str(body.get("date_iso"), "date_iso", default="2026-01-01"),
        "wall": {
            "project_type": project_type, "block_id": block_id, "bond": bond,
            "length_m": _num(wall.get("length_m", 3.0), "wall.length_m", 0.2, MAX_LENGTH_M),
            "height_m": _num(wall.get("height_m", 1.8), "wall.height_m", 0.2, MAX_HEIGHT_M),
            "thickness_mm": _num(wall.get("thickness_mm", 200), "wall.thickness_mm", 50, MAX_THICKNESS_MM),
            "finish_label": _str(wall.get("finish_label"), "wall.finish_label",
                                  default="Enduit lisse peint en blanc"),
            "finish_colour_hex": _str(wall.get("finish_colour_hex"), "wall.finish_colour_hex",
                                       default="#f2f1ec"),
        },
        "plot": {
            "boundary_points_m": _points(plot.get("boundary_points_m") or [], "plot.boundary_points_m"),
            "wall_points_m": _points(wall_points, "plot.wall_points_m"),
            "existing_structures": validated_structures,
            "north_angle_deg": _num(plot.get("north_angle_deg", 0.0), "plot.north_angle_deg", -360, 360),
        },
    }


@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return _cors(app.make_default_options_response())

    token_err = _require_token()
    if token_err:
        return token_err

    body = request.get_json(silent=True)
    try:
        answers = validate_answers(body)
    except ValidationError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    project = build_project(answers)

    try:
        dp2_png = dp2_plan_masse.render_dp2_png_bytes(project)
        dp5_png = dp5_elevation.render_dp5_png_bytes(project)
    except Exception as e:  # noqa: BLE001 -- report to the client, don't leak a stack trace
        return jsonify({"ok": False, "error": f"could not generate documents: {e}"}), 500

    import base64
    return jsonify({
        "ok": True,
        "dp2_png_base64": base64.b64encode(dp2_png).decode(),
        "dp5_png_base64": base64.b64encode(dp5_png).decode(),
    })


@app.route("/lookup-parcel", methods=["POST", "OPTIONS"])
def lookup_parcel():
    """Real parcel geometry/area/PLU-zone lookup via free/keyless government APIs (BAN + IGN
    APIcarto), see declaration_prealable/parcel_lookup.py's own module docstring for the sourced
    grounding. Same synchronous/no-GCS shape and X-Render-Token gate as /generate -- the three
    outbound calls (geocode, cadastre, zone-urba) plus one WMS image fetch are all sub-second."""
    if request.method == "OPTIONS":
        return _cors(app.make_default_options_response())

    token_err = _require_token()
    if token_err:
        return token_err

    body = request.get_json(silent=True) or {}
    try:
        if not isinstance(body, dict):
            raise ValidationError("body must be a JSON object")
        address = _str(body.get("address"), "address")
        commune = _str(body.get("commune"), "commune")
        wall_length_m = _num(body.get("wallLengthM", 3.0), "wallLengthM", 0.2, MAX_LENGTH_M)
        wall_offset_m = _num(body.get("wallOffsetM", 1.0), "wallOffsetM", 0.0, MAX_COORD_M)
        include_raw_aerial = bool(body.get("includeRawAerial", False))
    except ValidationError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    try:
        plot, meta = parcel_lookup.build_plot_from_address(address, commune, wall_length_m, wall_offset_m)
        dp1_png = dp1_situation.render_dp1_png_bytes(meta["lon"], meta["lat"], address)
        aerial_jpeg = (parcel_lookup.fetch_aerial_photo_bytes(meta["lon"], meta["lat"])
                       if include_raw_aerial else None)
    except Exception as e:  # noqa: BLE001 -- report to the client, don't leak a stack trace
        return jsonify({"ok": False, "error": f"could not look up parcel: {e}"}), 502

    import base64
    response = {
        "ok": True,
        "boundaryPointsM": plot.boundary_points_m,
        "existingStructures": plot.existing_structures,
        "wallPointsM": plot.wall_points_m,
        "contenanceM2": meta["contenance_m2"],
        "idu": meta["idu"],
        "zoneCode": meta["zone_code"],
        "zoneLibelle": meta["zone_libelle"],
        "reglementPdfFilename": meta["reglement_pdf_filename"],
        "dp1PngBase64": base64.b64encode(dp1_png).decode(),
    }
    if aerial_jpeg is not None:
        response["aerialPhotoJpegBase64"] = base64.b64encode(aerial_jpeg).decode()
    return jsonify(response)


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
