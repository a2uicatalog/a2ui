"""Generates the DP2 piece ("plan de masse") for a declaration préalable project: the whole-plot
site plan showing the plot boundary, existing structures, the proposed wall's placement, its
distance to the plot boundary, a north arrow, and a scale bar -- the required elements per
declaration_prealable/README.md's sourced guidance (échelle 1/50-1/500, 3D-coté, distances aux
limites du terrain, orientation Nord, constructions existantes, clôture à créer).

Coordinates in project.plot are local site metres with an arbitrary origin; this module projects
them to page pixels itself (y-up real-world -> y-down SVG), scaled to fit the page.
"""
import math

from declaration_prealable.project_schema import DPProject


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _text_with_halo(x, y, text, font_size, fill, anchor="middle", weight="400", halo_width=4):
    """A white-halo label, built as two stacked <text> elements (stroke-only copy behind, fill-only
    copy in front) rather than the CSS `paint-order` property -- cairosvg (used by render_dp2_png)
    does not support paint-order and silently defaults to painting stroke OVER fill, which made a
    single paint-order="stroke" text element invisible (confirmed live 2026-10-01, a real
    4px-opaque-white-stroke-over-red-fill result, not a cairosvg bug report guess)."""
    common = (f'x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
              f'font-family="Roboto,Arial,sans-serif" font-size="{font_size}" font-weight="{weight}"')
    halo = (f'<text {common} fill="none" stroke="#ffffff" stroke-width="{halo_width}">{_esc(text)}</text>')
    label = f'<text {common} fill="{fill}">{_esc(text)}</text>'
    return halo + label


def _bbox(all_points):
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    return min(xs), min(ys), max(xs), max(ys)


def distance_point_to_segment(p, a, b):
    """Shortest distance from point p to segment a-b, plus the closest point on it."""
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0:
        return math.hypot(px - ax, py - ay), (ax, ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy), (cx, cy)


def nearest_boundary_distance(point, boundary_points_m):
    """Shortest distance from `point` to any edge of the (closed) boundary polygon."""
    n = len(boundary_points_m)
    if n < 2:
        return None, None
    best_d, best_pt = None, None
    for i in range(n):
        a, b = boundary_points_m[i], boundary_points_m[(i + 1) % n]
        d, pt = distance_point_to_segment(point, a, b)
        if best_d is None or d < best_d:
            best_d, best_pt = d, pt
    return best_d, best_pt


class _Projector:
    """Maps site metres -> page pixels, fitting all supplied points into
    [margin, size-margin] with y flipped (SVG y grows downward)."""

    def __init__(self, all_points_m, page_w, page_h, margin):
        x0, y0, x1, y1 = _bbox(all_points_m)
        self.x0, self.y0 = x0, y0
        span_x, span_y = max(x1 - x0, 0.1), max(y1 - y0, 0.1)
        draw_w, draw_h = page_w - 2 * margin, page_h - 2 * margin
        self.scale = min(draw_w / span_x, draw_h / span_y)
        self.off_x = margin + (draw_w - span_x * self.scale) / 2
        self.off_y = margin + (draw_h - span_y * self.scale) / 2
        self.page_h = page_h
        self.margin = margin

    def pt(self, p):
        x, y = p
        px = self.off_x + (x - self.x0) * self.scale
        py = self.page_h - (self.off_y + (y - self.y0) * self.scale)  # flip y
        return px, py


def render_dp2_svg(project: DPProject) -> str:
    plot = project.plot
    all_pts = list(plot.boundary_points_m)
    for s in plot.existing_structures:
        all_pts.extend(s.get("points_m", []))
    all_pts.extend(plot.wall_points_m)
    if not all_pts:
        all_pts = [(0, 0), (10, 10)]

    W, H, margin = 900, 650, 110
    proj = _Projector(all_pts, W, H - 150, margin)  # reserve top band for title block

    def shift(pt_px):
        return pt_px[0], pt_px[1] - 0  # top band already excluded from projector's page_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        f'<text x="40" y="40" font-family="Roboto,Arial,sans-serif" font-size="20" font-weight="700" '
        f'fill="#202124">DP2 — Plan de masse</text>',
        f'<text x="40" y="64" font-family="Roboto,Arial,sans-serif" font-size="14" fill="#3c4043">'
        f'{_esc(project.address)}, {_esc(project.commune)}</text>',
        f'<text x="40" y="84" font-family="Roboto,Arial,sans-serif" font-size="14" fill="#3c4043">'
        f'{_esc(project.date_iso)}</text>',
        f'<line x1="40" y1="96" x2="{W-40}" y2="96" stroke="#dadce0" stroke-width="1"/>',
        '<g transform="translate(0,120)">',
    ]

    # Boundary polygon
    if len(plot.boundary_points_m) >= 2:
        pts_px = [proj.pt(p) for p in plot.boundary_points_m]
        path = " ".join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts_px))
        parts.append(f'<path d="{path} Z" fill="none" stroke="#202124" stroke-width="2" '
                     f'stroke-dasharray="6,3"/>')

    # Existing structures
    for s in plot.existing_structures:
        pts = s.get("points_m", [])
        if len(pts) < 2:
            continue
        pts_px = [proj.pt(p) for p in pts]
        path = " ".join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts_px))
        cx = sum(x for x, _ in pts_px) / len(pts_px)
        cy = sum(y for _, y in pts_px) / len(pts_px)
        parts.append(f'<path d="{path} Z" fill="#e8eaed" stroke="#5f6368" stroke-width="1.5"/>')
        if s.get("label"):
            parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
                         f'font-family="Roboto,Arial,sans-serif" font-size="12" fill="#3c4043">'
                         f'{_esc(s["label"])}</text>')

    # Proposed wall ("clôture à créer")
    if len(plot.wall_points_m) == 2:
        a_m, b_m = plot.wall_points_m
        a_px, b_px = proj.pt(a_m), proj.pt(b_m)
        parts.append(f'<line x1="{a_px[0]:.1f}" y1="{a_px[1]:.1f}" x2="{b_px[0]:.1f}" y2="{b_px[1]:.1f}" '
                     f'stroke="#d93025" stroke-width="4"/>')
        wall_len_m = math.hypot(b_m[0] - a_m[0], b_m[1] - a_m[1])
        mid_px = ((a_px[0] + b_px[0]) / 2, (a_px[1] + b_px[1]) / 2)
        # A short leader line to a FIXED, generous offset -- not just a halo at a small fixed offset.
        # Found live with a real (short, tight-cornered) urban parcel: when the wall is short relative
        # to the plot's own drawn scale and sits close to a corner, a small offset still collided with
        # the nearby boundary-distance callouts even with a halo. A leader line to a guaranteed-clear
        # position (matching dp5_elevation.py's own material-callout leader-line fix for the same
        # class of problem) is robust regardless of scale, unlike tuning one more pixel offset.
        label_px = (mid_px[0], mid_px[1] - 46)
        parts.append(f'<line x1="{mid_px[0]:.1f}" y1="{mid_px[1]-6:.1f}" x2="{label_px[0]:.1f}" '
                     f'y2="{label_px[1]+6:.1f}" stroke="#d93025" stroke-width="1"/>')
        parts.append(_text_with_halo(label_px[0], label_px[1], f'Clôture à créer — {wall_len_m:.2f} m',
                                      12, "#d93025", weight="600"))

        # Distance from each wall endpoint to the nearest plot boundary edge --
        # the "distances between the construction and the limits of the
        # terrain" the official guide requires on DP2. Computed from the
        # supplied plot geometry, not surveyed -- labelled as such.
        if len(plot.boundary_points_m) >= 2:
            for end_m, end_px in ((a_m, a_px), (b_m, b_px)):
                d, nearest_m = nearest_boundary_distance(end_m, plot.boundary_points_m)
                if d is None:
                    continue
                nearest_px = proj.pt(nearest_m)
                parts.append(f'<line x1="{end_px[0]:.1f}" y1="{end_px[1]:.1f}" '
                             f'x2="{nearest_px[0]:.1f}" y2="{nearest_px[1]:.1f}" '
                             f'stroke="#1a73e8" stroke-width="1" stroke-dasharray="3,2"/>')
                # 75% of the way toward the boundary point, not the midpoint -- found live with a
                # real (short, tight-cornered) urban parcel: a midpoint anchor sits right next to the
                # wall's own length label when the wall is close to a corner, overlapping it even with
                # a halo. Biasing toward the boundary end keeps real clearance from the wall label.
                lx = end_px[0] + 0.75 * (nearest_px[0] - end_px[0])
                ly = end_px[1] + 0.75 * (nearest_px[1] - end_px[1])
                parts.append(_text_with_halo(lx, ly - 4, f'{d:.2f} m', 11, "#1a73e8", halo_width=3))

    parts.append("</g>")

    # North arrow
    nx, ny, r = W - 70, 150, 22
    rad = math.radians(plot.north_angle_deg)
    tip = (nx + r * math.sin(rad), ny - r * math.cos(rad))
    tail = (nx - r * math.sin(rad), ny + r * math.cos(rad))
    parts.append(f'<line x1="{tail[0]:.1f}" y1="{tail[1]:.1f}" x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" '
                 f'stroke="#202124" stroke-width="2" marker-end="url(#north-arrow)"/>')
    parts.append(f'<text x="{tip[0]:.1f}" y="{tip[1]-8:.1f}" text-anchor="middle" '
                 f'font-family="Roboto,Arial,sans-serif" font-size="13" font-weight="700" fill="#202124">N</text>')
    parts.insert(2, '<defs><marker id="north-arrow" markerWidth="10" markerHeight="10" refX="5" refY="8" '
                    'orient="auto"><path d="M0,0 L5,9 L10,0 Z" fill="#202124"/></marker></defs>')

    # Scale bar
    bar_m = 5.0
    bar_px = bar_m * proj.scale
    by = H - 40
    parts.append(f'<line x1="40" y1="{by:.1f}" x2="{40+bar_px:.1f}" y2="{by:.1f}" stroke="#202124" stroke-width="2"/>')
    for i in range(2):
        tx = 40 + i * bar_px
        parts.append(f'<line x1="{tx:.1f}" y1="{by-5:.1f}" x2="{tx:.1f}" y2="{by+5:.1f}" stroke="#202124" stroke-width="2"/>')
    parts.append(f'<text x="40" y="{by+20:.1f}" font-family="Roboto,Arial,sans-serif" font-size="12" '
                 f'fill="#5f6368">Échelle — {bar_m:.0f} m</text>')

    parts.append("</svg>")
    return "".join(parts)


def render_dp2_png_bytes(project: DPProject, width=1600) -> bytes:
    """Rasterizes render_dp2_svg's output to raw PNG bytes -- see
    dp5_elevation.render_dp5_png_bytes's own docstring for the cairosvg convention and why the
    bytes-only form exists (declaration-prealable-api/server.py's synchronous web caller)."""
    import cairosvg
    svg = render_dp2_svg(project)
    return cairosvg.svg2png(bytestring=svg.encode(), output_width=width, background_color="white")


def render_dp2_png(project: DPProject, out_path, width=1600):
    from pathlib import Path
    Path(out_path).write_bytes(render_dp2_png_bytes(project, width))
    return out_path
