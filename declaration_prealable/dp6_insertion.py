"""Generates the DP6/DP7/DP8 pieces -- real site photos plus a composited "insertion dans
l'environnement" mockup -- see declaration_prealable/README.md for the sourced grounding (confirmed
2026-10-02 against the real, current CERFA 16702*03 packet's own "Bordereau de dépôt des pièces
jointes"): these three pieces are required whenever the project creates or modifies a construction
VISIBLE FROM THE PUBLIC ROAD (espace public), or the site sits in a site patrimonial remarquable /
abords d'un monument historique -- NOT only in a "secteur protégé" as this project's README previously
(and wrongly) claimed.

  DP6 -- "Un document graphique permettant d'apprécier l'insertion du projet de construction dans
          son environnement" [Art. R.431-10 c] -- the "mockup after": the wall composited onto the
          applicant's own real site photo, to scale, in the right place.
  DP7 -- "Une photographie permettant de situer le terrain dans l'environnement proche"
          [Art. R.431-10 d] -- the "photo before": a real close-range site photo, as-is.
  DP8 -- "Une photographie permettant de situer le terrain dans le paysage lointain"
          [Art. R.431-10 d] -- a real wide/distant site photo, as-is (skippable only if the applicant
          can justify that no distant photo is possible).

DP6's compositing is a deliberately simple SAME-DEPTH-PLANE scale, not full perspective/camera
correction: the applicant clicks the wall's left and right BASE points on their own photo; since the
wall's real length_m is already known from the intake answers, the pixel distance between those two
clicks gives a local pixels-per-metre scale, and the wall is drawn as a vertical (screen-space)
extrusion of that scale times height_m. This is accurate when the wall sits roughly perpendicular to
the camera in a roughly level photo -- matching the official text's own tolerance ("aucune échelle
stricte n'est imposée," but proportions must look realistic) -- but it will visibly misjudge height if
the source photo is taken from a steep up/down angle. Documented here rather than oversold as a real
photogrammetric insertion.
"""
import io
import math

from PIL import Image, ImageDraw

from declaration_prealable.project_schema import WallSpec

MAX_PHOTO_WIDTH = 1600  # caps a phone-camera-sized upload (often 3000-4000px wide) to something that
                         # composites fast and keeps the base64 response reasonably small -- the DP6/7/8
                         # legal bar has no stated resolution floor, this is purely a practical ceiling.


def _hex_to_rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _load_and_resize(photo_bytes, max_width=MAX_PHOTO_WIDTH):
    """Returns (RGBA image, scale) where scale is what any ORIGINAL-image pixel coordinate (e.g. a
    click captured against the browser's naturalWidth/naturalHeight) must be multiplied by to land in
    the returned image's own pixel space."""
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
    w, h = img.size
    if w <= max_width:
        return img, 1.0
    scale = max_width / w
    return img.resize((max_width, round(h * scale)), Image.LANCZOS), scale


def _caption_band(img_rgb, text):
    draw = ImageDraw.Draw(img_rgb)
    w, _ = img_rgb.size
    draw.rectangle([(0, 0), (w, 22)], fill=(255, 255, 255))
    draw.text((6, 4), text, fill=(20, 20, 20))
    return img_rgb


def package_site_photo_bytes(photo_bytes, piece_code, piece_title, address, max_width=MAX_PHOTO_WIDTH):
    """DP7/DP8: the applicant's own real photo, captioned, no compositing. JPEG out (this is photo
    content, not line art) -- matches parcel_lookup.fetch_aerial_photo_bytes's own JPEG convention for
    a raw, unannotated photo."""
    img, _ = _load_and_resize(photo_bytes, max_width)
    rgb = img.convert("RGB")
    _caption_band(rgb, f"{piece_code} - {piece_title} - {address}")
    out = io.BytesIO()
    rgb.save(out, format="JPEG", quality=90)
    return out.getvalue()


def composite_dp6_insertion_bytes(photo_bytes, left_base_px, right_base_px, wall: WallSpec, address,
                                   max_width=MAX_PHOTO_WIDTH):
    """Composites a to-scale, correctly-coloured wall extrusion onto the applicant's own real photo --
    see module docstring for the scale derivation and its honest same-depth-plane limitation.
    left_base_px/right_base_px are [x, y] pixel coordinates in the ORIGINAL (un-resized) photo's own
    pixel space -- e.g. exactly what a browser reports against the uploaded image's naturalWidth/
    naturalHeight, or what a CLI user reads off the file in any image viewer."""
    if wall.length_m <= 0:
        raise ValueError("wall.length_m must be positive to derive a photo scale")

    img, scale = _load_and_resize(photo_bytes, max_width)
    lx, ly = left_base_px[0] * scale, left_base_px[1] * scale
    rx, ry = right_base_px[0] * scale, right_base_px[1] * scale
    w, h = img.size
    for x, y, name in ((lx, ly, "left_base_px"), (rx, ry, "right_base_px")):
        if not (0 <= x <= w and 0 <= y <= h):
            raise ValueError(f"{name} falls outside the photo (got {x:.0f},{y:.0f} in a {w}x{h} image)")

    base_dist_px = math.hypot(rx - lx, ry - ly)
    if base_dist_px < 2:
        raise ValueError("left_base_px and right_base_px are too close together to derive a scale")

    px_per_m = base_dist_px / wall.length_m
    h_px = wall.height_m * px_per_m
    top_l, top_r = (lx, ly - h_px), (rx, ry - h_px)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    fill_rgb = _hex_to_rgb(wall.finish_colour_hex)
    odraw.polygon([(lx, ly), (rx, ry), top_r, top_l], fill=fill_rgb + (200,),
                  outline=(60, 60, 60, 255), width=2)
    composited = Image.alpha_composite(img, overlay).convert("RGB")

    # Red leader-line material/colour callout -- same convention as dp5_elevation.py's own DP5 callout
    # (e.g. "Enduit lisse peint en blanc"), so the two pieces read as one consistent dossier.
    draw = ImageDraw.Draw(composited)
    cx, cy = (lx + rx) / 2, ly - h_px * 0.6
    label_x = min(cx + 40, w - 10)
    label_y = max(cy - 40, 24)
    draw.line([(cx, cy), (label_x, label_y)], fill=(217, 48, 37, 255), width=2)
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(217, 48, 37, 255))
    draw.text((label_x + 4, label_y - 10), "Mur à créer", fill=(217, 48, 37, 255))
    draw.text((label_x + 4, label_y + 4), wall.finish_label, fill=(217, 48, 37, 255))
    draw.text((label_x + 4, label_y + 18), f"Hauteur {wall.height_m:.2f} m", fill=(217, 48, 37, 255))

    _caption_band(composited, f"DP6 - Insertion du projet dans son environnement - {address}")
    out = io.BytesIO()
    composited.save(out, format="PNG")
    return out.getvalue()
