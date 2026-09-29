#!/usr/bin/env python3
"""Gemini sketches a shape as validated SVG-primitive volumes -> deterministic voxels -> real bricks.

Adapts streaming-testbench's sketch_agent.py (forced function-calling loop, real XML-parser SVG
allowlist validation) for this catalogue's own brickgen.py tiler, instead of that demo's flat 2D canvas
renderer. The division of labour is the same as the existing "Pick a template" mode: Gemini never invents
raw voxel coordinates or picks real LEGO part ids (both hard, unreliable tasks) -- it only places simple
SVG primitives (box/cylinder/polygon footprints) with a base height and thickness in real stud/plate
units, one call at a time. Converting those into a real, collision-checked, anchored brick model is 100%
deterministic and already proven (brickgen.build), unchanged here.

`path` is deliberately NOT in the allowed tag list (v1): real bezier curves need real curve-flattening
to rasterize correctly, and a half-implemented version would silently produce wrong footprints rather
than fail loudly. rect/circle/ellipse/polygon/g already cover blocky letters and architecture massing --
the two cases this was built for -- honestly, without pretending to support freeform curves.

Usage:
    python3 scripts/brick_models/sketch_to_bricks.py --topic "a simple house with a triangular roof" \
        --name house_sketch --out-dir /tmp
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import brickgen  # noqa: E402
from renderers.web_article import _LDRAW_COLOURS  # noqa: E402
from build_design_page import CODES, CNAMES  # noqa: E402

PROJECT = "artful-patrol-502116-b7"
MODEL = "gemini-3.7-flash"
PRICES = {"gemini-3.7-flash": (0.75, 3.75), "gemini-3.5-flash-lite": (0.30, 2.50)}
ENDPOINT = "https://aiplatform.googleapis.com/v1beta1/publishers/google/models/%s:generateContent"


def _gcloud(args):
    return subprocess.run(["gcloud"] + args, capture_output=True, text=True, check=True).stdout


def get_key():
    """Same real pattern as scripts/ldraw/gemini_qa.py's get_key() -- the project holds more than one
    API key for different features, so pick the one actually restricted to this ENDPOINT's host."""
    host = ENDPOINT.split("/")[2]
    names = _gcloud(["services", "api-keys", "list", "--project", PROJECT, "--format=value(name)"]).split()
    for name in names:
        restriction = _gcloud(["services", "api-keys", "describe", name, "--project", PROJECT,
                               "--format=value(restrictions.apiTargets[0].service)"]).strip()
        if restriction == host:
            return _gcloud(["services", "api-keys", "get-key-string", name, "--format=value(keyString)"]).strip()
    raise RuntimeError("no API key in project %s is restricted to %s" % (PROJECT, host))


# ---- SVG validation: ported from sketch_agent.py's validate_svg_fragment / web_article.py's
# _validate_sketchpad_element (same allowlist, same real XML parser rather than a regex -- a crafted
# fragment can bypass a regex via parser-differential tricks). `path` excluded, see module docstring. ----
_ALLOWED_TAGS = {"circle", "ellipse", "rect", "polygon", "g"}
_ALLOWED_ATTRS = {"cx", "cy", "r", "rx", "ry", "x", "y", "width", "height", "points", "fill"}
_SAFE_VALUE = re.compile(r"^[A-Za-z0-9#.,\-\s()%]*$")


def validate_svg_fragment(fragment: str) -> Optional[ET.Element]:
    if not fragment or len(fragment) > 4096:
        return None
    try:
        root = ET.fromstring("<g>" + fragment + "</g>")
    except ET.ParseError:
        return None
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "g" and el is root:
            continue
        if tag not in _ALLOWED_TAGS:
            return None
        for k, v in el.attrib.items():
            if k not in _ALLOWED_ATTRS or not _SAFE_VALUE.match(v):
                return None
    return root


# ---- fill -> nearest real LEGO colour code. Gemini is told to prefer hex; a small named fallback covers
# the common case where it doesn't. Nearest-match (not exact-match-or-default) so an odd hex still lands
# on a real, existing brick colour rather than silently falling back to one fixed default every time. ----
_NAMED = {"red": "#c91a09", "blue": "#0055bf", "green": "#237841", "yellow": "#f2cd37", "white": "#f4f4f4",
          "black": "#1b2a34", "orange": "#d67923", "tan": "#e4cd9e", "brown": "#582a12", "grey": "#969696",
          "gray": "#969696", "lime": "#bbe90b"}


def _hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _first_fill(el: ET.Element) -> Optional[str]:
    """Depth-first: the shape's own fill wins; falls through to a nested/parent g's fill only if the
    shape itself didn't set one. Reads the already-validated ET tree, not the raw fragment string --
    string-slicing on 'fill=\"...\"' would break on attribute order, quoting, or a fill inside a nested
    element's own value."""
    if el.get("fill"):
        return el.get("fill")
    for child in el:
        f = _first_fill(child)
        if f:
            return f
    return None


# Material-context-aware architecture seam (2026-09-29, cozy-forging-newt.md Track B item 3): LEGO's own
# unit vocabulary ("studs"/"plates", 3-plates-per-course) and its 17-entry curated real-LDraw colour
# palette are the CURRENT profile, not the only possible shape of this tool -- the footprint/support-check
# logic beneath both (already generic) doesn't care what the units are called or what colours are legal.
# LEGO stays the only populated profile; this is the seam, not a second material's rollout.
LEGO_SKETCH_PROFILE = {
    "height_unit": "plates",
    "footprint_unit": "studs",
    "course_ratio": "3 plates = 1 standard brick course",
    "palette_codes": CODES,
}


def nearest_colour_code(fill: Optional[str], material_profile: Optional[Dict] = None) -> int:
    mp = material_profile or LEGO_SKETCH_PROFILE
    if not fill:
        return 4  # red, this project's own SENTINEL/default fill
    h = _NAMED.get(fill.strip().lower(), fill.strip())
    if not re.match(r"^#[0-9a-fA-F]{3}$|^#[0-9a-fA-F]{6}$", h):
        return 4
    target = _hex_to_rgb(h)
    best, best_d = 4, float("inf")
    for code in mp["palette_codes"]:
        rgb = _hex_to_rgb(_LDRAW_COLOURS[code])
        d = sum((a - b) ** 2 for a, b in zip(target, rgb))
        if d < best_d:
            best, best_d = code, d
    return best


# ---- SVG element -> filled (x, z) footprint cells, in stud units. y0/height (plates) come from the tool
# call, not the SVG itself -- one call places one vertical slab, possibly multi-shape in its footprint via
# nested <g>. ----
def _footprint(el: ET.Element) -> List[Tuple[int, int]]:
    tag = el.tag.split("}")[-1]
    cells: List[Tuple[int, int]] = []
    if tag == "g":
        for child in el:
            cells.extend(_footprint(child))
        return cells
    try:
        if tag == "rect":
            x0, z0 = float(el.get("x", 0)), float(el.get("y", 0))
            w, d = float(el.get("width", 0)), float(el.get("height", 0))
            for x in range(int(x0), int(x0 + w)):
                for z in range(int(z0), int(z0 + d)):
                    cells.append((x, z))
        elif tag in ("circle", "ellipse"):
            cx, cz = float(el.get("cx", 0)), float(el.get("cy", 0))
            rx = float(el.get("r", el.get("rx", 0)))
            rz = float(el.get("r", el.get("ry", rx)))
            if rx <= 0 or rz <= 0:
                return cells
            for x in range(int(cx - rx), int(cx + rx) + 1):
                for z in range(int(cz - rz), int(cz + rz) + 1):
                    if ((x + 0.5 - cx) / rx) ** 2 + ((z + 0.5 - cz) / rz) ** 2 <= 1:
                        cells.append((x, z))
        elif tag == "polygon":
            pts = [tuple(map(float, p.split(","))) for p in el.get("points", "").split() if "," in p]
            if len(pts) < 3:
                return cells
            xs = [p[0] for p in pts]
            zs = [p[1] for p in pts]
            for x in range(int(min(xs)), int(max(xs)) + 1):
                for z in range(int(min(zs)), int(max(zs)) + 1):
                    if _point_in_polygon(x + 0.5, z + 0.5, pts):
                        cells.append((x, z))
    except (ValueError, ZeroDivisionError):
        return []
    return cells


def _point_in_polygon(px, pz, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1, z1 = pts[i]
        x2, z2 = pts[(i + 1) % n]
        if (z1 > pz) != (z2 > pz):
            xint = x1 + (pz - z1) * (x2 - x1) / (z2 - z1)
            if px < xint:
                inside = not inside
    return inside


PLACE_SHAPE_TOOL = {
    "name": "place_shape",
    "description": (
        "Place ONE solid volume on the build plate. Call this once per volume -- build up the model "
        "incrementally, background/large volumes (the base, the main body) first, details last."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "svg_fragment": {
                "type": "STRING",
                "description": (
                    "Exactly one raw SVG element describing the volume's FOOTPRINT (looking straight down "
                    "from above), e.g. '<rect x=\"4\" y=\"4\" width=\"24\" height=\"24\" fill=\"#c91a09\"/>'. "
                    "Coordinates and width/height/r/rx/ry are in STUDS. Allowed tags: rect, circle, ellipse, "
                    "polygon, g (g may nest further allowed elements, e.g. an L-shaped footprint from two "
                    "rects). Allowed attributes: x, y, width, height, cx, cy, r, rx, ry, points, fill. "
                    "path is NOT supported -- build curved-looking shapes from circle/ellipse/polygon "
                    "instead. fill should be a hex colour (#rrggbb) or one of: red, blue, green, yellow, "
                    "white, black, orange, tan, brown, grey, lime."
                ),
            },
            "y0": {"type": "INTEGER", "description": "Base height in PLATES, 0 = sits on the ground plate."},
            "height": {"type": "INTEGER", "description": "Thickness in PLATES (>= 1). 3 plates = 1 standard brick course."},
            "label": {"type": "STRING", "description": "3-6 words describing what this volume is, e.g. 'the roof'."},
        },
        "required": ["svg_fragment", "y0", "height", "label"],
    },
}

CARVE_OPENING_TOOL = {
    "name": "carve_opening",
    "description": (
        "Remove material to cut a real opening -- a window, a door, a wheel well, a cockpit recess -- out "
        "of volume(s) already placed with place_shape. Call this AFTER the solid volume you want to cut "
        "into already exists. Unlike place_shape this only ever REMOVES cells; it never adds new colour."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "svg_fragment": {
                "type": "STRING",
                "description": (
                    "Exactly one raw SVG element describing the opening's FOOTPRINT, same coordinate "
                    "system and allowed tags as place_shape (rect, circle, ellipse, polygon, g), in STUDS. "
                    "fill is ignored (removing material has no colour). e.g. a window: "
                    "'<rect x=\"6\" y=\"4\" width=\"2\" height=\"2\"/>' with a y0/height matching where in "
                    "the wall it should be cut."
                ),
            },
            "y0": {"type": "INTEGER", "description": "Base height in PLATES of the opening."},
            "height": {"type": "INTEGER", "description": "How tall the opening is, in PLATES (>= 1)."},
            "label": {"type": "STRING", "description": "3-6 words describing the opening, e.g. 'front door opening'."},
        },
        "required": ["svg_fragment", "y0", "height", "label"],
    },
}

FINISH_TOOL = {
    "name": "finish",
    "description": "Call once the model is complete and represents the topic well.",
    "parameters": {"type": "OBJECT", "properties": {
        "summary": {"type": "STRING", "description": "One-sentence summary of what was built."}}, "required": ["summary"]},
}


def _system_prompt(topic: str, plate_w: int, plate_d: int, material_profile: Optional[Dict] = None) -> str:
    mp = material_profile or LEGO_SKETCH_PROFILE
    hu, fu = mp["height_unit"], mp["footprint_unit"]
    return (
        "You are a minimalist LEGO model designer working in real physical units, not free-form art. "
        f"The build plate is {plate_w} x {plate_d} {fu}, (0,0) at one corner, X and Z are the two "
        f"horizontal axes. Y (height) is separate, in {hu.upper()} -- {mp['course_ratio']}, so a "
        f"typical wall is a multiple of 3 {hu} tall.\n\n"
        f"Topic: {topic}\n\n"
        "Plan a simple, recognisable, BLOCKY form -- this becomes real tiled LEGO bricks, not a smooth "
        "render, so think in terms of stacked rectangular/cylindrical volumes rather than fine detail. "
        "PHYSICAL CONNECTIVITY IS REAL, not just visual: any volume whose footprint does not actually "
        "overlap the footprint of a volume already sitting directly below it (touching y0 to that lower "
        "volume's own top) is unsupported and WILL BE DELETED before the model is built -- exactly like a "
        "real LEGO piece floating in mid-air with nothing under it. Every volume except your first "
        "(ground) one must sit on top of, and overlap the footprint of, something already placed. "
        "Call place_shape once per volume, background/large/GROUND volumes first (these must cover most "
        "of the footprint of anything you stack on them later), details last (aim for 3-12 calls total). "
        "Keep every shape's footprint within the plate bounds.\n\n"
        "IMPORTANT -- a single place_shape call is a SOLID EXTRUSION: its footprint stays exactly the same "
        "shape from y0 all the way up to y0+height. It CANNOT taper or narrow within one call. A peaked/"
        "pitched roof, a pyramid, a dome, or any shape that narrows as it rises MUST be built as SEVERAL "
        "calls, each with a smaller footprint than the one below it, like a stepped pyramid -- e.g. a "
        "simple pitched roof over an 12x8 house: place_shape rect x=0,y=0,w=12,h=8 at y0=20,height=2 "
        "(wide base eave), then rect x=2,y=1,w=8,h=6 at y0=22,height=2 (narrower), then rect x=4,y=2,w=4,"
        "h=4 at y0=24,height=2 (narrower still), then a final thin ridge on top. A single flat-topped box "
        "for a roof looks wrong -- always step it down in at least 3-4 shrinking stages. The same rule "
        "applies to any other tapering form (a spire, a rocket nose, a dome).\n\n"
        "OPENINGS: place_shape only ever ADDS solid material -- a 'window' placed as a small coloured "
        "rect is just a coloured patch on the surface, not a real opening, and looks wrong. For a real "
        "window, door, wheel well, or cockpit recess: first place_shape the solid volume (the wall, the "
        "car body), THEN call carve_opening with a smaller footprint at the right y0/height to cut an "
        "actual hole out of it. carve_opening only removes, never adds colour. Use it for anything that "
        "should read as a hole or recess rather than a coloured mark -- this applies to vehicles just as "
        "much as buildings (wheel wells, window cutouts, cockpit openings).\n\n"
        "HOLLOW INTERIORS for anything with rooms: place_shape's walls are SOLID -- if you only carve small "
        "window/door holes into a solid block, those holes open onto more solid material behind them, not "
        "into a real room. For any building, after placing the solid exterior walls, ALSO call "
        "carve_opening with a LARGE footprint inset from the outer walls by the wall thickness (e.g. walls "
        f"2 {fu} thick on a 16x16 footprint -> carve the interior at x=2,y=2,width=12,height=12), spanning "
        "most of the interior height, to hollow the whole inside out into one open room BEFORE (or after -- "
        "order doesn't matter) carving the smaller window/door holes that connect that hollow room to the "
        "outside. Do this for every floor. Skipping this step is the single most common mistake -- a "
        "building that is not hollowed out this way looks wrong no matter how good its window cutouts are.\n\n"
        f"PROPORTIONS -- HARD LIMIT: the TOTAL height of the model, ground to its single highest point "
        f"(roof ridge, chimney, antenna, anything), must not exceed {max(18, min(plate_w, plate_d))} "
        f"{hu}, UNLESS the topic is explicitly a tower/spire/skyscraper/rocket. This is a hard budget, "
        f"not a suggestion -- plan it before you start placing: e.g. one storey of wall = 8 {hu}, a roof "
        f"= 3 tapering steps of 2 {hu} each (6 {hu}) is already a complete, good-looking roof. Do NOT "
        "add a 5th or 6th roof tier just because tapering is good -- 3 steps (occasionally 4 for a large "
        "building) is enough; more steps must come out of the SAME total height budget, not add to it. If "
        "you are about to exceed the limit, make existing volumes shorter, not add more of them.\n\n"
        "SYMMETRY: when a face has more than one similar opening (windows) or feature, place them "
        "symmetrically about that face's own centreline unless the topic explicitly calls for an "
        "asymmetric design -- e.g. a centred door with one matching window mirrored on each side, and the "
        "SAME window arrangement repeated at the same x/z position on every floor (just at a different "
        "y0). Before calling finish, check: does every floor of the same face have the same number of "
        "openings in mirrored positions? A lopsided arrangement (a window on one side of a door but not "
        "the other, or windows on one floor but not the matching floor above it) looks like a mistake, "
        "not a design choice.\n\n"
        "When done, call finish with a one-sentence summary."
    )


def _call_gemini(key: str, contents: List[Dict], system_prompt: str) -> Dict:
    body = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "tools": [{"functionDeclarations": [PLACE_SHAPE_TOOL, CARVE_OPENING_TOOL, FINISH_TOOL]}],
        "toolConfig": {"functionCallingConfig": {"mode": "ANY"}},
        # thinkingBudget=0: same real fix as scripts/ldraw/gemini_qa.py's ask() -- found live, first real
        # run here, that default (extended) thinking burns ~2000 tokens then produces a
        # MALFORMED_FUNCTION_CALL instead of a valid tool call under forced mode=ANY.
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1024, "thinkingConfig": {"thinkingBudget": 0}},
    }
    req = urllib.request.Request(ENDPOINT % MODEL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(4 * 2 ** attempt)
                continue
            raise RuntimeError("gemini HTTP %d: %s" % (e.code, e.read().decode()[:500]))


def run_sketch_to_bricks(topic: str, name: str, out_dir: str = ".", plate_w: int = 32, plate_d: int = 32,
                          max_turns: int = 15, material_profile: Optional[Dict] = None) -> Tuple[List[Dict], Dict, List[str]]:
    """Returns (bricks, validation_report, log_lines) -- log_lines records every shape placed/rejected and
    the model's own labels, so a caller can show real provenance, not just the final geometry."""
    mp = material_profile or LEGO_SKETCH_PROFILE
    key = get_key()
    system_prompt = _system_prompt(topic, plate_w, plate_d, mp)
    # The API requires >=1 contents entry even though the real instructions live in systemInstruction --
    # an empty list 400s with "at least one contents field is required" (found live, first real run).
    contents: List[Dict] = [{"role": "user", "parts": [{"text": "Begin."}]}]
    S: Dict[Tuple[int, int, int], int] = {}
    log: List[str] = []
    finished = False

    for turn in range(max_turns):
        # MALFORMED_FUNCTION_CALL is an intermittent real failure mode under forced tool_config mode=ANY
        # (found live: thinkingBudget=0 isn't always fully honoured -- thoughtsTokenCount showed ~2000
        # even with it set). It's a same-turn retry, not a fresh turn -- contents is NOT appended to on a
        # malformed attempt, so a retry just re-asks the same question rather than burning a real turn.
        for attempt in range(3):
            resp = _call_gemini(key, contents, system_prompt)
            cand = resp["candidates"][0]
            if cand.get("finishReason") != "MALFORMED_FUNCTION_CALL":
                break
            log.append("retry %d/3: MALFORMED_FUNCTION_CALL on turn %d" % (attempt + 1, turn))
        else:
            raise RuntimeError("MALFORMED_FUNCTION_CALL 3x in a row on turn %d -- giving up. Log:\n%s" %
                               (turn, "\n".join(log)))
        parts = cand["content"]["parts"]
        contents.append({"role": "model", "parts": parts})
        fn_responses = []
        for part in parts:
            fc = part.get("functionCall")
            if not fc:
                continue
            fn_name, args = fc["name"], fc.get("args", {})
            if fn_name == "finish":
                log.append("finish: %s" % args.get("summary", ""))
                finished = True
                fn_responses.append({"functionResponse": {"name": fn_name, "response": {"ok": True}}})
                continue
            if fn_name not in ("place_shape", "carve_opening"):
                fn_responses.append({"functionResponse": {"name": fn_name, "response": {"ok": False, "error": "unknown tool"}}})
                continue
            root = validate_svg_fragment(args.get("svg_fragment", ""))
            if root is None:
                log.append("REJECTED (invalid/disallowed svg): %r" % args.get("svg_fragment", "")[:120])
                fn_responses.append({"functionResponse": {"name": fn_name, "response": {
                    "ok": False, "error": "svg_fragment failed validation -- only rect/circle/ellipse/polygon/g "
                                           "with x,y,width,height,cx,cy,r,rx,ry,points,fill are allowed, no path"}}})
                continue
            y0, height = int(args.get("y0", 0)), max(1, int(args.get("height", 1)))
            cells = _footprint(root)
            cells = [(x, z) for x, z in cells if 0 <= x < plate_w and 0 <= z < plate_d]
            label = args.get("label", "")
            if not cells:
                log.append("REJECTED (empty footprint): %r" % label)
                fn_responses.append({"functionResponse": {"name": fn_name, "response": {
                    "ok": False, "error": "footprint is empty after clamping to the plate bounds "
                                           "(0..%d x 0..%d) -- check the shape's coordinates" % (plate_w - 1, plate_d - 1)}}})
                continue

            if fn_name == "carve_opening":
                # Pure removal -- no support check needed (you can't make a hole float), no colour. Silent
                # no-op cells (nothing was there to remove) are reported honestly rather than pretended away,
                # so the model can tell "I cut the window" apart from "I aimed at empty air".
                removed = 0
                for x, z in cells:
                    for y in range(y0, y0 + height):
                        if S.pop((x, y, z), None) is not None:
                            removed += 1
                log.append("carved %r: %d/%d cells actually removed, y%d-%d" % (
                    label, removed, len(cells) * height, y0, y0 + height - 1))
                fn_responses.append({"functionResponse": {"name": fn_name, "response": {
                    "ok": True, "cells_removed": removed}}})
                continue

            code = nearest_colour_code(_first_fill(root), mp)
            # brickgen.tile() does `if not c: continue` -- LDraw colour code 0 (Black) is falsy in Python,
            # so every Black-coded cell was silently dropped from the tiled output (found live: an
            # all-black-heavy model collapsed to zero surviving bricks). Store the hex string instead of
            # the bare int code -- a non-empty string is always truthy, and hex is already a valid `c`
            # representation downstream (see _brick_parts_model_sanitise's own docstring). brickgen.py
            # itself is untouched; every other existing caller just never happened to place code-0 cells.
            stored_colour = _LDRAW_COLOURS[code]
            # Real physical-connectivity check, not just a prompt-text warning (a text-only warning was
            # tried first and was NOT enough -- Gemini placed disconnected geometry anyway; found live,
            # the whole model collapsed to zero surviving bricks after brickgen's own anchoring pass ran
            # at the very end, with no chance to fix it). Reject HERE, mid-generation, with the real reason,
            # so the model can retry with an adjusted footprint/y0 instead of silently losing the piece 15
            # turns later. y0==0 always passes (it sits on the real ground plate).
            supported = y0 == 0 or any((x, y0 - 1, z) in S for x, z in cells)
            if not supported:
                log.append("REJECTED (unsupported, y0=%d): %r" % (y0, label))
                fn_responses.append({"functionResponse": {"name": fn_name, "response": {
                    "ok": False, "error": (
                        "unsupported: none of this shape's %d footprint cells sit directly above an "
                        "existing shape at y=%d. It would float in mid-air and be deleted. Either lower "
                        "y0 so it touches the top of something already placed, or move/resize its "
                        "footprint so it overlaps a shape that's already there.") % (len(cells), y0 - 1)}}})
                continue
            placed = 0
            for x, z in cells:
                for y in range(y0, y0 + height):
                    S[(x, y, z)] = stored_colour
                    placed += 1
            log.append("placed %r: %d cells, y%d-%d, colour %s" % (
                label, len(cells), y0, y0 + height - 1, CNAMES.get(code, code)))
            fn_responses.append({"functionResponse": {"name": fn_name, "response": {
                "ok": True, "cells_placed": placed, "footprint_cells": len(cells)}}})
        if fn_responses:
            contents.append({"role": "user", "parts": fn_responses})
        if finished:
            break
    else:
        log.append("WARNING: hit max_turns (%d) without an explicit finish call" % max_turns)

    if not S:
        raise RuntimeError("no valid shapes were placed -- nothing to build. Log:\n" + "\n".join(log))
    try:
        bricks, rep = brickgen.build(S, name, out_dir=out_dir)
    except Exception as e:
        # brickgen.build can legitimately end up with zero surviving bricks (e.g. every placed shape sat
        # above y0 with nothing anchoring it down to the ground plate -- the anchoring pass trims a fully
        # disconnected structure to nothing over its iterations). Surface the real placement log either
        # way rather than losing it to a bare traceback -- that's the only way to tell "the model never
        # touched the ground" apart from any other failure.
        print("\n".join(log), file=sys.stderr)
        Path("/tmp/_sketch_debug_S.json").write_text(json.dumps({"%d,%d,%d" % k: v for k, v in S.items()}))
        raise RuntimeError("brickgen.build failed after placing %d voxel cells across %d shapes: %s" %
                            (len(S), len([l for l in log if l.startswith("placed")]), e)) from e
    return bricks, rep, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--plate-w", type=int, default=32)
    ap.add_argument("--plate-d", type=int, default=32)
    ap.add_argument("--max-turns", type=int, default=15)
    a = ap.parse_args()
    bricks, rep, log = run_sketch_to_bricks(a.topic, a.name, a.out_dir, a.plate_w, a.plate_d, a.max_turns)
    print("\n".join(log), file=sys.stderr)
    print("%d bricks, ok=%s" % (len(bricks), rep["ok"]), file=sys.stderr)
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
