"""Generates the DP5 piece ("représentation de l'aspect extérieur du projet") for a standalone
mur de clôture -- see declaration_prealable/README.md for why a freestanding wall uses DP5 and
not DP4 (DP4 only applies when modifying an EXISTING building's façade).

The official DP5 convention (confirmed 2026-10-01 against a real municipal guide's own worked
example) is a dimensioned elevation drawing with red leader-line callouts naming each visible
material/colour, e.g. "Enduit lisse peint en blanc" -- not a photorealistic render. This module
reproduces that convention directly: a to-scale course-by-course block elevation (same real
block-coursing approach as renderers/web_article.py's _wall_calc/_wall_svg, adapted here rather
than imported -- that module is a hobbyist cost/weight/build-time UI card for a different purpose
and explicitly disclaims its own height threshold as illustrative-only; this module's
DP_WALL_HEIGHT_THRESHOLD_M is a real, sourced legal figure and the two must not be conflated),
plus dimension lines, a material/colour leader-line callout, a scale bar, and a title block.
"""
import math
from pathlib import Path

from declaration_prealable.project_schema import DPProject

# Real standard French construction block sizes (mm), matching
# renderers/web_article.py's WALL_BLOCKS -- these are genuine industry-standard
# dimensions, not placeholders, so re-declaring them locally (rather than
# importing a private helper from a differently-scoped module) duplicates a
# fact, not a design.
BLOCKS = {
    "parpaing200": {"label": "Parpaing 500×200×200", "unit_l": 510, "course_h": 210, "colour": "#8d9499"},
    "parpaing150": {"label": "Parpaing 500×200×150", "unit_l": 510, "course_h": 210, "colour": "#9aa0a6"},
    "brique": {"label": "Brique 220×105×55", "unit_l": 230, "course_h": 65, "colour": "#c1440e"},
}

# Source: https://www.service-public.gouv.fr/particuliers/vosdroits/F3131
# ("Vous devez également déposer une DP si votre mur de clôture mesure 2
# mètres ou plus"), confirmed live 2026-10-01. A real, cited legal figure --
# NOT the same as renderers/web_article.py's WALL_ADVISORY_HEIGHT_M, which
# that module's own comment explicitly marks as illustrative/unresearched.
DP_WALL_HEIGHT_THRESHOLD_M = 2.0


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _wrap_text(text, max_chars):
    """Greedy word-wrap, used so a long finish_label stays inside the callout's reserved width
    instead of overflowing it on one line."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [text]


def wall_coursing(block_id, length_m, height_m, bond="running"):
    b = BLOCKS.get(block_id, BLOCKS["parpaing200"])
    length_mm, height_mm = round(length_m * 1000), round(height_m * 1000)
    courses = max(1, math.ceil(height_mm / b["course_h"]))
    per_course = max(1, math.ceil(length_mm / b["unit_l"]))
    return {
        "block": b, "block_id": block_id, "bond": bond,
        "courses": courses, "per_course": per_course,
        "actual_h_mm": courses * b["course_h"], "actual_w_mm": per_course * b["unit_l"],
        "requested_length_m": length_m, "requested_height_m": height_m,
    }


def _dim_line_h(x1, x2, y, label):
    """Horizontal dimension: extension ticks + arrowed line + centred label above it."""
    return (
        f'<line x1="{x1:.1f}" y1="{y-6:.1f}" x2="{x1:.1f}" y2="{y+6:.1f}" stroke="#3c4043" stroke-width="1"/>'
        f'<line x1="{x2:.1f}" y1="{y-6:.1f}" x2="{x2:.1f}" y2="{y+6:.1f}" stroke="#3c4043" stroke-width="1"/>'
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="#3c4043" stroke-width="1" '
        f'marker-start="url(#arrow)" marker-end="url(#arrow)"/>'
        f'<text x="{(x1+x2)/2:.1f}" y="{y-9:.1f}" text-anchor="middle" font-family="Roboto,Arial,sans-serif" '
        f'font-size="13" fill="#202124">{_esc(label)}</text>'
    )


def _dim_line_v(y1, y2, x, label):
    """Vertical dimension: extension ticks + arrowed line + rotated label beside it."""
    return (
        f'<line x1="{x-6:.1f}" y1="{y1:.1f}" x2="{x+6:.1f}" y2="{y1:.1f}" stroke="#3c4043" stroke-width="1"/>'
        f'<line x1="{x-6:.1f}" y1="{y2:.1f}" x2="{x+6:.1f}" y2="{y2:.1f}" stroke="#3c4043" stroke-width="1"/>'
        f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="#3c4043" stroke-width="1" '
        f'marker-start="url(#arrow)" marker-end="url(#arrow)"/>'
        f'<text x="{x-10:.1f}" y="{(y1+y2)/2:.1f}" text-anchor="middle" font-family="Roboto,Arial,sans-serif" '
        f'font-size="13" fill="#202124" transform="rotate(-90 {x-10:.1f} {(y1+y2)/2:.1f})">{_esc(label)}</text>'
    )


def render_dp5_svg(project: DPProject) -> str:
    w = project.wall
    calc = wall_coursing(w.block_id, w.length_m, w.height_m, w.bond)

    W, H = 900, 650
    mx = 90  # left margin, room for the vertical dimension + its label
    callout_w = 230  # fixed right-hand band reserved for the material/colour callout, independent of
                      # wall width/aspect ratio -- found live: anchoring the callout off the wall's own
                      # right edge let long finish labels run off the canvas entirely when the wall was wide
    top, bottom = 150, 430  # drawing band; space above for title block, below for horizontal dim + scale bar
    draw_w, draw_h = W - mx - callout_w, bottom - top
    scale = min(draw_w / calc["actual_w_mm"], draw_h / calc["actual_h_mm"])
    unit_px = calc["block"]["unit_l"] * scale
    course_px = calc["block"]["course_h"] * scale
    wall_w_px = calc["actual_w_mm"] * scale
    wall_h_px = calc["actual_h_mm"] * scale
    x0 = mx + (draw_w - wall_w_px) / 2
    gap = max(1.0, min(2.5, course_px * 0.08))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">'
        '<path d="M0,1 L7,4 L0,7 Z" fill="#3c4043"/></marker></defs>',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        # Title block
        f'<text x="40" y="40" font-family="Roboto,Arial,sans-serif" font-size="20" font-weight="700" '
        f'fill="#202124">DP5 — Représentation de l’aspect extérieur du projet</text>',
        f'<text x="40" y="64" font-family="Roboto,Arial,sans-serif" font-size="14" fill="#3c4043">'
        f'{_esc(project.address)}, {_esc(project.commune)}</text>',
        f'<text x="40" y="84" font-family="Roboto,Arial,sans-serif" font-size="14" fill="#3c4043">'
        f'{_esc(calc["block"]["label"])} · {_esc("Appareillage en panneresse" if w.bond == "running" else "Appareillage droit")}'
        f' · {_esc(project.date_iso)}</text>',
        f'<line x1="40" y1="96" x2="{W-40}" y2="96" stroke="#dadce0" stroke-width="1"/>',
    ]

    # Wall block courses (deterministic, scale-accurate -- same bond logic as
    # renderers/web_article.py's own wall elevation card, adapted here).
    parts.append(f'<rect x="{x0:.1f}" y="{bottom - wall_h_px:.1f}" width="{wall_w_px:.1f}" '
                 f'height="{wall_h_px:.1f}" fill="{w.finish_colour_hex}" stroke="#3c4043" stroke-width="1.5"/>')
    if calc["block"]["colour"]:
        for c in range(calc["courses"]):
            y = bottom - (c + 1) * course_px
            offset = (unit_px / 2) if (w.bond == "running" and c % 2) else 0.0
            x = x0 - offset
            while x < x0 + wall_w_px - 0.5:
                bx = max(x, x0)
                bw = min(x + unit_px, x0 + wall_w_px) - bx - gap
                if bw > 1:
                    parts.append(f'<rect x="{bx:.1f}" y="{y+gap:.1f}" width="{bw:.1f}" '
                                 f'height="{course_px-gap:.1f}" fill="none" stroke="#3c4043" stroke-width="0.6" '
                                 f'stroke-opacity="0.35"/>')
                x += unit_px

    # Ground line
    parts.append(f'<line x1="{x0-40:.1f}" y1="{bottom:.1f}" x2="{x0+wall_w_px+40:.1f}" '
                 f'y2="{bottom:.1f}" stroke="#202124" stroke-width="2.5"/>')
    parts.append(f'<text x="{x0-44:.1f}" y="{bottom+4:.1f}" text-anchor="end" font-family="Roboto,Arial,sans-serif" '
                 f'font-size="11" fill="#5f6368">TN ± 0,00</text>')

    # Dimensions: length along the bottom, height along the left
    parts.append(_dim_line_h(x0, x0 + wall_w_px, bottom + 34, f'{calc["actual_w_mm"]/1000:.2f} m'))
    parts.append(_dim_line_v(bottom, bottom - wall_h_px, x0 - 28, f'{calc["actual_h_mm"]/1000:.2f} m'))

    # Material/colour callout -- red leader line, matching the official
    # DP5 example's exact convention (e.g. "Enduit lisse peint en blanc").
    # Anchored at a FIXED point inside the reserved callout_w band (not
    # relative to the wall's own right edge), so the label never runs off
    # the canvas regardless of wall width/aspect ratio.
    cx, cy = min(x0 + wall_w_px * 0.75, x0 + wall_w_px - 4), bottom - wall_h_px * 0.55
    lx, ly = W - callout_w + 20, top + 20
    parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="#d93025" stroke-width="1.2"/>')
    parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.5" fill="#d93025"/>')
    max_chars = max(10, (callout_w - 30) // 7)
    lines = _wrap_text(w.finish_label, max_chars)
    for i, line in enumerate(lines):
        parts.append(f'<text x="{lx:.1f}" y="{ly + i * 17:.1f}" font-family="Roboto,Arial,sans-serif" '
                     f'font-size="13" font-weight="600" fill="#d93025">{_esc(line)}</text>')

    # Scale bar -- DP5 has no strict scale requirement, but a bar makes the
    # proportions verifiable at a glance (the official guidance's own point).
    bar_m = 1.0
    bar_px = bar_m * 1000 * scale
    by = H - 70
    parts.append(f'<line x1="40" y1="{by:.1f}" x2="{40+bar_px:.1f}" y2="{by:.1f}" stroke="#202124" stroke-width="2"/>')
    for i in range(2):
        tx = 40 + i * bar_px
        parts.append(f'<line x1="{tx:.1f}" y1="{by-5:.1f}" x2="{tx:.1f}" y2="{by+5:.1f}" stroke="#202124" stroke-width="2"/>')
    parts.append(f'<text x="40" y="{by+20:.1f}" font-family="Roboto,Arial,sans-serif" font-size="12" '
                 f'fill="#5f6368">Échelle — {bar_m:.0f} m</text>')

    if w.height_m >= DP_WALL_HEIGHT_THRESHOLD_M:
        parts.append(f'<text x="{W-40}" y="40" text-anchor="end" font-family="Roboto,Arial,sans-serif" '
                     f'font-size="11" fill="#7a5c00">Hauteur ≥ {DP_WALL_HEIGHT_THRESHOLD_M:.0f} m — '
                     f'DP obligatoire (art. R421-12, vérifier aussi le PLU)</text>')

    parts.append("</svg>")
    return "".join(parts)


def render_dp5_png_bytes(project: DPProject, width=1600) -> bytes:
    """Rasterizes render_dp5_svg's output to raw PNG bytes, matching scripts/a2a_agent_sketch.py's own
    cairosvg.svg2png convention (same library, same call shape) -- an optional dependency,
    `pip install cairosvg`, not required for the SVG path above. The bytes-only form exists so a
    synchronous web caller (declaration-prealable-api/server.py) can base64-encode the result directly
    without touching disk; render_dp5_png below is the file-writing convenience wrapper around it."""
    import cairosvg
    svg = render_dp5_svg(project)
    return cairosvg.svg2png(bytestring=svg.encode(), output_width=width, background_color="white")


def render_dp5_png(project: DPProject, out_path, width=1600):
    Path(out_path).write_bytes(render_dp5_png_bytes(project, width))
    return out_path
