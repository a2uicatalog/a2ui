"""Generic SVG-subset rasterizer — turns the SVG strings the web renderer
already produces for a handful of chart-family atoms (heatmap, gauge_sla,
stacked_area, scatter_trend, sankey_flow, sparkline, progress_circle) into a
real PNG, with no browser/chromium involved. Built for `scripts/printer.py`'s
Chat-image delivery path — see the plan discussion this was built from for
why (google-chat's cardsV2 has no inline SVG/Canvas support, but these atoms'
visuals are pure functions of data, not CSS/DOM layout, so a from-scratch
rasterizer avoids needing a real browser for this data-derived subset).

Supports exactly the SVG surface these atoms actually use (verified by
reading every one of their render functions), not the general SVG spec:
  elements  - svg, defs, linearGradient/stop, rect, circle, line, polygon,
              polyline, path (commands M/L/C/A/Z, absolute or relative), text
  fill      - flat colors, `url(#gradientId)` (linearGradient, objectBoundingBox
              units — the only kind these atoms emit), `none`
  stroke    - flat colors, stroke-width, stroke-dasharray, stroke-dashoffset
  ignored   - <filter>/feGaussianBlur glow effects (cosmetic only, real blur
              is a convolution for zero data-fidelity gain), <title> tooltips,
              CSS transforms, onmouseover/onmouseout, transitions

Strokes are rendered by stamping filled disks of radius stroke-width/2 along
the flattened path at a fine step — this is a deliberate simplification
(no true miter/bevel joins), but it gives round caps/joins "for free" and
handles straight lines, dashed lines, flattened Béziers and flattened arcs
with one routine instead of four. No anti-aliasing — hard-edged fills, in
keeping with the "recompile from scratch, keep it simple" scope of this
module rather than a general-purpose renderer.
"""

import re
import struct
import zlib
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def _load_bitmap_font():
    """File-path load rather than `from renderers.vendor import bitmap_font` —
    this module gets imported both as `renderers.svg_raster` (package-
    qualified) and as a bare top-level `svg_raster` (scripts/printer.py adds
    ROOT/renderers to sys.path directly, without ROOT itself on sys.path,
    same shape as the bug fixed in web_article.py's qrcodegen import), and
    only the first case can resolve a package-qualified import."""
    import importlib.util
    path = str(Path(__file__).parent / "vendor" / "bitmap_font.py")
    spec = importlib.util.spec_from_file_location("_a2ui_vendored_bitmap_font", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bitmap_font = _load_bitmap_font()

_SVG_NS = "{http://www.w3.org/2000/svg}"


def _tag(el):
    t = el.tag
    return t.split("}", 1)[1] if t.startswith("{") else t


# ── color parsing ────────────────────────────────────────────────────────

_NAMED = {
    "white": (255, 255, 255), "black": (0, 0, 0), "none": None,
    "transparent": None, "red": (255, 0, 0), "green": (0, 128, 0),
    "blue": (0, 0, 255),
}


def parse_color(s, opacity=1.0):
    """Returns (r,g,b,a) 0-255 ints, or None for 'none'/unset."""
    if s is None:
        return None
    s = s.strip()
    if s == "" or s == "none":
        return None
    a = 255
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            r, g, b = (int(c * 2, 16) for c in h)
        elif len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        elif len(h) == 8:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            a = int(h[6:8], 16)
        else:
            return None
    elif s.startswith("rgba(") or s.startswith("rgb("):
        nums = [float(x) for x in re.findall(r"[-\d.]+", s)]
        r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
        if len(nums) > 3:
            a = int(round(nums[3] * 255))
    elif s in _NAMED:
        c = _NAMED[s]
        if c is None:
            return None
        r, g, b = c
    else:
        return None
    a = int(round(a * opacity))
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)),
            max(0, min(255, a)))


def _num(s, default=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _pct_or_num(s, default=0.0):
    if s is None:
        return default
    s = s.strip()
    if s.endswith("%"):
        return _num(s[:-1], default * 100) / 100.0
    return _num(s, default)


# ── canvas ────────────────────────────────────────────────────────────────

class Canvas:
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = max(1, int(w)), max(1, int(h))
        self.buf = bytearray(bg * (self.w * self.h))

    def blend(self, x, y, rgba):
        if rgba is None:
            return
        x, y = int(x), int(y)
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        r, g, b, a = rgba
        if a <= 0:
            return
        i = (y * self.w + x) * 3
        if a >= 255:
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = r, g, b
            return
        ia = 255 - a
        self.buf[i] = (r * a + self.buf[i] * ia) // 255
        self.buf[i + 1] = (g * a + self.buf[i + 1] * ia) // 255
        self.buf[i + 2] = (b * a + self.buf[i + 2] * ia) // 255

    def to_png(self):
        return encode_png(self.buf, self.w, self.h)


def encode_png(rgb_buf, w, h):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # bitdepth 8, colortype 2 (RGB)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter type: None
        raw += rgb_buf[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


# ── fill (scanline polygon) ──────────────────────────────────────────────

def _bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def fill_polygon(canvas, points, color_fn):
    """color_fn(x, y) -> rgba. Nonzero-winding scanline fill."""
    if len(points) < 3:
        return
    ymin = max(0, int(math.floor(min(p[1] for p in points))))
    ymax = min(canvas.h - 1, int(math.ceil(max(p[1] for p in points))))
    n = len(points)
    for y in range(ymin, ymax + 1):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if y1 == y2:
                continue
            if (yc >= y1) != (yc >= y2):
                t = (yc - y1) / (y2 - y1)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa, xb = xs[i], xs[i + 1]
            xstart, xend = max(0, int(math.ceil(xa - 0.5))), min(canvas.w - 1, int(math.floor(xb - 0.5)))
            for x in range(xstart, xend + 1):
                canvas.blend(x, y, color_fn(x + 0.5, y + 0.5))


# ── stroke (stamped-disk along a flattened polyline) ─────────────────────

def _dash_on(dist, dasharray, dashoffset):
    if not dasharray:
        return True
    pattern = list(dasharray)
    if len(pattern) % 2 == 1:
        pattern = pattern * 2
    cycle = sum(pattern)
    if cycle <= 0:
        return True
    pos = (dist + dashoffset) % cycle
    acc = 0.0
    for i, seg in enumerate(pattern):
        acc += seg
        if pos < acc:
            return i % 2 == 0
    return True


def stroke_polyline(canvas, points, color_fn, width, dasharray=None, dashoffset=0.0, closed=False):
    """color_fn: either a flat (r,g,b,a) tuple or a callable(x, y) -> rgba."""
    if color_fn is None or len(points) < 2 or width <= 0:
        return
    sample = color_fn if callable(color_fn) else (lambda x, y, c=color_fn: c)
    r = max(width / 2.0, 0.5)
    step = max(0.5, r * 0.3)
    pts = list(points) + ([points[0]] if closed else [])
    dist = 0.0
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        seg_len = math.hypot(x2 - x1, y2 - y1)
        if seg_len == 0:
            continue
        n_steps = max(1, int(seg_len / step))
        for s in range(n_steps + 1):
            t = s / n_steps
            d = dist + t * seg_len
            if _dash_on(d, dasharray, dashoffset):
                px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
                _fill_disk(canvas, px, py, r, sample(px, py))
        dist += seg_len


def _fill_disk(canvas, cx, cy, r, rgba):
    x0, x1 = int(math.floor(cx - r)), int(math.ceil(cx + r))
    y0, y1 = int(math.floor(cy - r)), int(math.ceil(cy + r))
    r2 = r * r
    for y in range(max(0, y0), min(canvas.h - 1, y1) + 1):
        for x in range(max(0, x0), min(canvas.w - 1, x1) + 1):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r2:
                canvas.blend(x, y, rgba)


# ── path `d` parsing + flattening ────────────────────────────────────────

_PATH_TOKEN = re.compile(r"([MLCAZmlcaz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)")


def parse_path(d):
    """Returns a list of subpaths, each a flattened list of (x,y) points."""
    tokens = []
    for m in _PATH_TOKEN.finditer(d or ""):
        tokens.append(m.group(1) or m.group(2))
    subpaths = []
    pts = []
    cx = cy = 0.0
    start = (0.0, 0.0)
    i = 0
    cmd = None

    def nums(k):
        nonlocal i
        vals = [float(tokens[i + j]) for j in range(k)]
        i += k
        return vals

    while i < len(tokens):
        if tokens[i] in "MLCAZmlcaz":
            cmd = tokens[i]
            i += 1
        if cmd in ("M", "m"):
            x, y = nums(2)
            if cmd == "m":
                x, y = cx + x, cy + y
            if pts:
                subpaths.append(pts)
            pts = [(x, y)]
            cx, cy = x, y
            start = (x, y)
            cmd = "L" if cmd == "M" else "l"
        elif cmd in ("L", "l"):
            x, y = nums(2)
            if cmd == "l":
                x, y = cx + x, cy + y
            pts.append((x, y))
            cx, cy = x, y
        elif cmd in ("C", "c"):
            x1, y1, x2, y2, x, y = nums(6)
            if cmd == "c":
                x1, y1, x2, y2, x, y = cx + x1, cy + y1, cx + x2, cy + y2, cx + x, cy + y
            pts.extend(_flatten_cubic((cx, cy), (x1, y1), (x2, y2), (x, y)))
            cx, cy = x, y
        elif cmd in ("A", "a"):
            rx, ry, rot, laf, sf, x, y = nums(7)
            if cmd == "a":
                x, y = cx + x, cy + y
            pts.extend(_flatten_arc((cx, cy), rx, ry, rot, laf, sf, (x, y)))
            cx, cy = x, y
        elif cmd in ("Z", "z"):
            pts.append(start)
            cx, cy = start
        else:
            i += 1
    if pts:
        subpaths.append(pts)
    return subpaths


def _flatten_cubic(p0, p1, p2, p3, n=24):
    out = []
    for k in range(1, n + 1):
        t = k / n
        mt = 1 - t
        x = mt ** 3 * p0[0] + 3 * mt ** 2 * t * p1[0] + 3 * mt * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = mt ** 3 * p0[1] + 3 * mt ** 2 * t * p1[1] + 3 * mt * t ** 2 * p2[1] + t ** 3 * p3[1]
        out.append((x, y))
    return out


def _flatten_arc(p0, rx, ry, phi_deg, large_arc, sweep, p1, n=48):
    """SVG endpoint-to-center arc parameterization (spec appendix F.6.5)."""
    x1, y1 = p0
    x2, y2 = p1
    if rx == 0 or ry == 0 or (x1 == x2 and y1 == y2):
        return [p1]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(phi_deg)
    cos_p, sin_p = math.cos(phi), math.sin(phi)

    dx2, dy2 = (x1 - x2) / 2.0, (y1 - y2) / 2.0
    x1p = cos_p * dx2 + sin_p * dy2
    y1p = -sin_p * dx2 + cos_p * dy2

    lam = (x1p ** 2) / (rx ** 2) + (y1p ** 2) / (ry ** 2)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s

    sign = -1.0 if large_arc == sweep else 1.0
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    co = sign * math.sqrt(max(0.0, num / den)) if den != 0 else 0.0
    cxp = co * rx * y1p / ry
    cyp = -co * ry * x1p / rx

    cx = cos_p * cxp - sin_p * cyp + (x1 + x2) / 2.0
    cy = sin_p * cxp + cos_p * cyp + (y1 + y2) / 2.0

    def angle(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        length = math.hypot(ux, uy) * math.hypot(vx, vy)
        cosang = max(-1.0, min(1.0, dot / length)) if length else 1.0
        ang = math.acos(cosang)
        return -ang if (ux * vy - uy * vx) < 0 else ang

    theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if sweep == 0 and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep == 1 and dtheta < 0:
        dtheta += 2 * math.pi

    out = []
    for k in range(1, n + 1):
        t = theta1 + dtheta * (k / n)
        ex = cx + rx * math.cos(t) * cos_p - ry * math.sin(t) * sin_p
        ey = cy + rx * math.cos(t) * sin_p + ry * math.sin(t) * cos_p
        out.append((ex, ey))
    return out


# ── gradients ─────────────────────────────────────────────────────────────

class Gradient:
    def __init__(self, x1, y1, x2, y2, stops):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.stops = stops  # list of (offset 0..1, (r,g,b,a))

    def color_at(self, t):
        t = max(0.0, min(1.0, t))
        stops = self.stops
        if not stops:
            return (0, 0, 0, 255)
        if t <= stops[0][0]:
            return stops[0][1]
        if t >= stops[-1][0]:
            return stops[-1][1]
        for i in range(len(stops) - 1):
            o0, c0 = stops[i]
            o1, c1 = stops[i + 1]
            if o0 <= t <= o1:
                f = (t - o0) / (o1 - o0) if o1 > o0 else 0
                return tuple(int(round(c0[k] + (c1[k] - c0[k]) * f)) for k in range(4))
        return stops[-1][1]

    def sampler_for_bbox(self, bbox):
        x0, y0, x1v, y1v = bbox
        w, h = (x1v - x0) or 1.0, (y1v - y0) or 1.0
        gx1, gy1 = x0 + self.x1 * w, y0 + self.y1 * h
        gx2, gy2 = x0 + self.x2 * w, y0 + self.y2 * h
        dx, dy = gx2 - gx1, gy2 - gy1
        denom = dx * dx + dy * dy or 1.0

        def sample(px, py):
            t = ((px - gx1) * dx + (py - gy1) * dy) / denom
            return self.color_at(t)
        return sample


def _parse_gradients(root):
    grads = {}
    for defs in root.iter():
        if _tag(defs) == "linearGradient":
            gid = defs.get("id")
            if not gid:
                continue
            x1 = _pct_or_num(defs.get("x1"), 0.0)
            y1 = _pct_or_num(defs.get("y1"), 0.0)
            x2 = _pct_or_num(defs.get("x2"), 1.0)
            y2 = _pct_or_num(defs.get("y2"), 0.0)
            stops = []
            for stop in defs:
                if _tag(stop) != "stop":
                    continue
                off = _pct_or_num(stop.get("offset"), 0.0)
                sc = parse_color(stop.get("stop-color", "#000"), _num(stop.get("stop-opacity"), 1.0))
                stops.append((off, sc or (0, 0, 0, 255)))
            stops.sort(key=lambda s: s[0])
            grads[gid] = Gradient(x1, y1, x2, y2, stops)
    return grads


def _resolve_fill(fill_attr, opacity, grads):
    if fill_attr is None:
        return ("color", (0, 0, 0, int(255 * opacity)))
    fill_attr = fill_attr.strip()
    if fill_attr == "none":
        return ("none", None)
    m = re.match(r"url\(#([^)]+)\)", fill_attr)
    if m and m.group(1) in grads:
        return ("gradient", grads[m.group(1)])
    return ("color", parse_color(fill_attr, opacity))


# ── text ──────────────────────────────────────────────────────────────────

def draw_text(canvas, x, y, text, rgba, font_size, anchor="start"):
    if rgba is None or not text:
        return
    scale = max(1, round(font_size / 8.0))
    gw, gh = bitmap_font.GLYPH_W * scale, bitmap_font.GLYPH_H * scale
    spacing = scale
    total_w = len(text) * (gw + spacing) - spacing
    if anchor == "middle":
        x -= total_w / 2.0
    elif anchor == "end":
        x -= total_w
    top = y - gh
    for ch in text:
        rows = bitmap_font.glyph(ch)
        for ry, row in enumerate(rows):
            for rx, cell in enumerate(row):
                if cell == "#":
                    for dy in range(scale):
                        for dx in range(scale):
                            canvas.blend(x + rx * scale + dx, top + ry * scale + dy, rgba)
        x += gw + spacing


# ── element drawing ───────────────────────────────────────────────────────

def _style_attrs(el):
    """Attributes plus any inline style="k:v;..." pairs (style wins, matching CSS)."""
    attrs = dict(el.attrib)
    style = attrs.pop("style", "")
    for part in style.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            attrs[k.strip()] = v.strip()
    return attrs


def _draw_shape(canvas, points, attrs, grads, closed_fill=True, scale=1.0):
    opacity = _num(attrs.get("opacity"), 1.0)
    fill_op = _num(attrs.get("fill-opacity"), 1.0)
    fill_attr = attrs.get("fill")
    kind, fill_val = _resolve_fill(fill_attr, opacity * fill_op, grads)
    if kind != "none" and closed_fill and len(points) >= 3:
        bbox = _bbox(points)
        if kind == "gradient":
            sampler = fill_val.sampler_for_bbox(bbox)
            fill_polygon(canvas, points, lambda x, y: sampler(x, y))
        else:
            fill_polygon(canvas, points, lambda x, y, c=fill_val: c)

    stroke_attr = attrs.get("stroke")
    stroke_op = opacity * _num(attrs.get("stroke-opacity"), 1.0)
    skind, sval = _resolve_fill(stroke_attr, stroke_op, grads)
    sw = _num(attrs.get("stroke-width"), 1.0) * scale
    if skind != "none" and sval is not None and sw > 0:
        dash = None
        da = attrs.get("stroke-dasharray")
        if da and da != "none":
            dash = [_num(v) * scale for v in re.split(r"[,\s]+", da.strip()) if v]
        offset = _num(attrs.get("stroke-dashoffset"), 0.0) * scale
        if skind == "gradient":
            sampler = sval.sampler_for_bbox(_bbox(points))
            stroke_polyline(canvas, points, sampler, sw, dash, offset, closed=closed_fill and fill_attr != "none")
        else:
            stroke_polyline(canvas, points, sval, sw, dash, offset, closed=closed_fill and fill_attr != "none")


def _draw_element(canvas, el, grads, scale, ox, oy):
    tag = _tag(el)
    attrs = _style_attrs(el)

    def P(v):
        return (v[0] * scale + ox, v[1] * scale + oy)

    if tag == "rect":
        x, y = _num(attrs.get("x")), _num(attrs.get("y"))
        w, h = _num(attrs.get("width")), _num(attrs.get("height"))
        rx = _num(attrs.get("rx"), _num(attrs.get("ry"), 0.0))
        ry = _num(attrs.get("ry"), rx)
        rx, ry = min(rx, w / 2.0), min(ry, h / 2.0)
        if rx <= 0 or ry <= 0:
            pts = [P((x, y)), P((x + w, y)), P((x + w, y + h)), P((x, y + h))]
        else:
            pts = []
            corners = [(x + w - rx, y + ry, -90, 0), (x + w - rx, y + h - ry, 0, 90),
                       (x + rx, y + h - ry, 90, 180), (x + rx, y + ry, 180, 270)]
            for ccx, ccy, a0, a1 in corners:
                for k in range(9):
                    a = math.radians(a0 + (a1 - a0) * k / 8)
                    pts.append(P((ccx + rx * math.cos(a), ccy + ry * math.sin(a))))
        _draw_shape(canvas, pts, attrs, grads, scale=scale)
    elif tag == "circle":
        cx, cy, r = _num(attrs.get("cx")), _num(attrs.get("cy")), _num(attrs.get("r"))
        pts = [P((cx + r * math.cos(a), cy + r * math.sin(a)))
               for a in (2 * math.pi * k / 48 for k in range(48))]
        _draw_shape(canvas, pts, attrs, grads, scale=scale)
    elif tag == "line":
        pts = [P((_num(attrs.get("x1")), _num(attrs.get("y1")))),
               P((_num(attrs.get("x2")), _num(attrs.get("y2"))))]
        _draw_shape(canvas, pts, attrs, grads, closed_fill=False, scale=scale)
    elif tag in ("polygon", "polyline"):
        raw = attrs.get("points", "")
        nums = [float(v) for v in re.findall(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?", raw)]
        pts = [P((nums[i], nums[i + 1])) for i in range(0, len(nums) - 1, 2)]
        _draw_shape(canvas, pts, attrs, grads, closed_fill=(tag == "polygon"), scale=scale)
    elif tag == "path":
        for sub in parse_path(attrs.get("d", "")):
            pts = [P(p) for p in sub]
            closed = len(pts) > 2 and pts[0] == pts[-1]
            _draw_shape(canvas, pts, attrs, grads, closed_fill=True if closed or attrs.get("fill") not in (None, "none") else False, scale=scale)
    elif tag == "text":
        x, y = _num(attrs.get("x")), _num(attrs.get("y"))
        fs = _num(attrs.get("font-size"), 10.0) * scale
        color = parse_color(attrs.get("fill", "#000"), _num(attrs.get("opacity"), 1.0))
        anchor = attrs.get("text-anchor", "start")
        px, py = P((x, y))
        draw_text(canvas, px, py, "".join(el.itertext()), color, fs, anchor)


# ── entry point ───────────────────────────────────────────────────────────

def rasterize_svg_to_png(svg_string, target_width=None, background=(255, 255, 255)):
    """Render an SVG string (the subset described at module top) to PNG bytes."""
    m = re.search(r"<svg[\s\S]*?</svg>", svg_string)
    if not m:
        raise ValueError("no <svg>...</svg> found in input")
    xml_str = re.sub(r"<(\w+)([^>]*)/>", r"<\1\2></\1>", m.group(0))  # normalize self-closers for ET, no-op if already fine
    root = ET.fromstring(xml_str)

    vb = root.get("viewBox")
    if vb:
        _, _, vw, vh = [float(v) for v in re.split(r"[\s,]+", vb.strip())]
    else:
        vw = _num(root.get("width"), 300)
        vh = _num(root.get("height"), 150)

    scale = (target_width / vw) if target_width else 1.0
    w, h = max(1, round(vw * scale)), max(1, round(vh * scale))
    canvas = Canvas(w, h, bg=background)

    grads = _parse_gradients(root)

    def walk(el):
        t = _tag(el)
        if t in ("defs",):
            return
        if t not in ("svg", "g"):
            _draw_element(canvas, el, grads, scale, 0, 0)
        for child in el:
            walk(child)

    walk(root)
    return canvas.to_png()
