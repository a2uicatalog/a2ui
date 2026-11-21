"""arch_motion (v3): Basic-Catalog architecture diagram macro with verify_rich-compliant SMIL motion.

Takes the motion_arch atom contract (nodes, edges, messages, groups, w, h, size, radius, accent, accent2, color,
mute, fill, background, label) plus motion=True, and returns a wide variant (the payload's own percentage layout,
labels and chips placed by a scored search) and a narrow phone variant (one column, its own lane and row per item).
Pure Python 3.11 standard library; zero subprocesses, zero network, zero model calls. See the design note at the end.
"""
from __future__ import annotations

import itertools
import math
import re
import unicodedata

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # macro-packs/ (the import root): archpack reads d3pack's shared helpers
from d3pack import common as C
from d3pack.rich import verify_rich

MAX_NODES = 12
MAX_EDGES = 16
MAX_MESSAGES = 12
MAX_GROUPS = 4
MAX_POINTS = 10
MAX_STAGES = 5
MAX_ANIMATED = 20

NODE_ID_RE = re.compile(r'^[a-z][a-z0-9_-]{0,31}\Z')
HEX6_RE = re.compile(r'^#[0-9a-fA-F]{6}\Z')

KINDS = ('user', 'device', 'app', 'surface', 'server', 'tool', 'model', 'store')  # glyphs: _glyph() vector paths
EDGE_STYLES = ('solid', 'dashed')

DEFAULT_COLOURS = {
    'accent': '#8d98ff',
    'accent2': '#2ac4ce',
    'color': '#eaeff5',
    'mute': '#9ca5b1',
    'fill': '#2d3642',
    'background': '#1e2733',
}


def _n(val: float, places: int = 1) -> str:
    """Format finite coordinate without scientific notation or -0."""
    if not math.isfinite(val):
        return '0'
    scale = 10 ** places
    rounded = math.floor(abs(val) * scale + 0.5) / scale
    if rounded == 0:
        return '0'
    sign = '-' if val < 0 else ''
    text = f'{rounded:.{places}f}'.rstrip('0').rstrip('.')
    return sign + (text or '0')


def _sec(val: float) -> str:
    """Format seconds strictly matching rich.py _SEC: (\\d{1,2}(?:\\.\\d{1,3})?)s."""
    clamped = max(0.0, min(4.95, float(val)))
    rounded = math.floor(clamped * 100 + 0.5) / 100
    if rounded == 0:
        return '0s'
    text = f'{rounded:.2f}'.rstrip('0').rstrip('.')
    return f'{text}s'


def _mix_hex(hex_a: str, hex_b: str, t: float) -> str:
    """Interpolate two #rrggbb colours (avoids stroke-opacity where rich.py forbids it)."""
    ra, ga, ba = (int(hex_a[i:i + 2], 16) for i in (1, 3, 5))
    rb, gb, bb = (int(hex_b[i:i + 2], 16) for i in (1, 3, 5))
    lerp = lambda a, b: max(0, min(255, int(math.floor(a + (b - a) * t + 0.5))))
    return f'#{lerp(ra, rb):02x}{lerp(ga, gb):02x}{lerp(ba, bb):02x}'


def _clean_hex(val, key: str, bad_cols: list[str]) -> str:
    if val is None:
        return DEFAULT_COLOURS[key]
    if isinstance(val, str) and HEX6_RE.match(val.strip()):
        return val.strip().lower()
    bad_cols.append(key)
    return DEFAULT_COLOURS[key]


def _clean_str(val, maxlen: int, trunc_count: list[int], default: str = '') -> str:
    if isinstance(val, bool) or val is None:
        return default
    if isinstance(val, (int, float)):
        fv = C.finite(val, -1e15, 1e15)
        if fv is None:
            return default
        raw = C.fmt(fv) if isinstance(val, float) else str(int(val))
    elif isinstance(val, str):
        raw = C.plain(val).strip()
    else:
        return default
    if not raw:
        return default
    if len(raw) > maxlen:
        trunc_count[0] += 1
        return raw[:maxlen].rstrip()
    return raw


def _clamp_int(val, default: int, lo: int, hi: int, name: str, clamped_opts: list[str]) -> int:
    if val is None:
        return default
    fv = C.finite(val, -1e12, 1e12)
    if fv is None:
        clamped_opts.append(name)
        return default
    iv = int(fv)
    if iv < lo or iv > hi:
        clamped_opts.append(name)
        return max(lo, min(hi, iv))
    return iv


def _clamp_pct(val, default: float, lo: float, hi: float, clamped_flag: list[int]) -> float:
    if val is None:
        return default
    fv = C.finite(val, -1e9, 1e9)
    if fv is None:
        clamped_flag[0] += 1
        return default
    if fv < lo or fv > hi:
        clamped_flag[0] += 1
        return max(lo, min(hi, fv))
    return float(fv)


def _parse_spec(
    nodes, edges, messages, groups, w, h, size, radius,
    accent, accent2, color, mute, fill, background, label, extra_keys,
) -> tuple[dict, list[str]]:
    """Validate and clean motion_arch inputs using d3pack tolerant-reader conventions."""
    notes: list[str] = []
    bad_cols: list[str] = []
    trunc_count = [0]
    clamped_opts: list[str] = []
    clamped_coords = [0]

    W = _clamp_int(w, 1000, 200, 2000, 'w', clamped_opts)
    H = _clamp_int(h, 560, 120, 2000, 'h', clamped_opts)
    sz = _clamp_int(size, 17, 8, 40, 'size', clamped_opts)
    rad = _clamp_int(radius, 10, 0, 60, 'radius', clamped_opts)
    if sz < 17:
        notes.append('Wide variant: text that size would put under 12 px (sub-labels, group headers, edge labels) is drawn at 12 px, the legibility floor.')

    pal = {
        'accent': _clean_hex(accent, 'accent', bad_cols),
        'accent2': _clean_hex(accent2, 'accent2', bad_cols),
        'color': _clean_hex(color, 'color', bad_cols),
        'mute': _clean_hex(mute, 'mute', bad_cols),
        'fill': _clean_hex(fill, 'fill', bad_cols),
        'background': _clean_hex(background, 'background', bad_cols),
    }
    aria_label = _clean_str(label, 80, trunc_count, 'Architecture diagram') or 'Architecture diagram'

    # 1. Groups (max 4)
    clean_groups: list[dict] = []
    if groups is not None:
        if not isinstance(groups, list):
            notes.append('The groups field was not a list, so it was ignored.')
        else:
            if len(groups) > MAX_GROUPS:
                notes.append(f'{len(groups) - MAX_GROUPS} groups beyond the {MAX_GROUPS}th were not drawn.')
            bad_grp = 0
            for g in groups[:MAX_GROUPS]:
                if not isinstance(g, dict):
                    bad_grp += 1
                    continue
                gx = _clamp_pct(g.get('x'), 0.0, 0.0, 100.0, clamped_coords)
                gy = _clamp_pct(g.get('y'), 0.0, 0.0, 100.0, clamped_coords)
                gw = _clamp_pct(g.get('w'), 30.0, 1.0, 100.0, clamped_coords)
                gh = _clamp_pct(g.get('h'), 30.0, 1.0, 100.0, clamped_coords)
                gat = _clamp_pct(g.get('at'), 0.0, 0.0, 1.0, clamped_coords)
                gdur = _clamp_pct(g.get('dur'), 0.1, 0.01, 1.0, clamped_coords)
                glbl = _clean_str(g.get('label'), 40, trunc_count, '')
                clean_groups.append({'label': glbl, 'x': gx, 'y': gy, 'w': gw, 'h': gh, 'at': gat, 'dur': gdur})
            if bad_grp:
                notes.append(f'{bad_grp} group entries were not objects and were left out.')

    # 2. Nodes (max 12, at least 1 required)
    if not isinstance(nodes, list) or not nodes:
        raise ValueError('nodes must be a non-empty list of node objects')
    if len(nodes) > MAX_NODES:
        notes.append(f'{len(nodes) - MAX_NODES} nodes beyond the {MAX_NODES}th were not drawn.')

    clean_nodes: list[dict] = []
    seen_ids: set[str] = set()
    bad_nodes = bad_ids = bad_kinds = 0
    for idx, raw_n in enumerate(nodes[:MAX_NODES]):
        if not isinstance(raw_n, dict):
            bad_nodes += 1
            continue
        raw_id = raw_n.get('id')
        if isinstance(raw_id, str) and NODE_ID_RE.match(raw_id) and raw_id not in seen_ids:
            nid = raw_id
        else:
            bad_ids += 1
            nid = f'n{idx}'
            while nid in seen_ids:
                idx += 1
                nid = f'n{idx}'
        seen_ids.add(nid)

        raw_kind = raw_n.get('kind')
        if raw_kind is None:
            kind = 'server'
        elif isinstance(raw_kind, str) and raw_kind in KINDS:
            kind = raw_kind
        else:
            bad_kinds += 1
            kind = 'server'

        nlbl = _clean_str(raw_n.get('label'), 40, trunc_count, nid) or nid
        nsub = _clean_str(raw_n.get('sub'), 40, trunc_count, '')
        nx = _clamp_pct(raw_n.get('x'), 50.0, 0.0, 100.0, clamped_coords)
        ny = _clamp_pct(raw_n.get('y'), 50.0, 0.0, 100.0, clamped_coords)
        nw = _clamp_pct(raw_n.get('w'), 20.0, 4.0, 100.0, clamped_coords)
        nh = _clamp_pct(raw_n.get('h'), 15.0, 4.0, 100.0, clamped_coords)
        nat = _clamp_pct(raw_n.get('at'), min(1.0, len(clean_nodes) * 0.05), 0.0, 1.0, clamped_coords)
        ndur = _clamp_pct(raw_n.get('dur'), 0.08, 0.01, 1.0, clamped_coords)
        clean_nodes.append({
            'id': nid, 'kind': kind, 'label': nlbl, 'sub': nsub,
            'x': nx, 'y': ny, 'w': nw, 'h': nh, 'at': nat, 'dur': ndur,
        })

    if not clean_nodes:
        raise ValueError('nodes contained no usable node objects')
    if bad_nodes:
        notes.append(f'{bad_nodes} node entries were not objects and were left out.')
    if bad_ids:
        notes.append(f'{bad_ids} node ids were missing, invalid or repeated, so fallback ids were assigned.')
    if bad_kinds:
        notes.append(f'{bad_kinds} unknown node kinds defaulted to server.')

    node_by_id = {n['id']: n for n in clean_nodes}

    # 3. Edges (max 16; keep original slot index so message.edge stays aligned)
    edge_slots: list[dict | None] = []
    if edges is not None:
        if not isinstance(edges, list):
            notes.append('The edges field was not a list, so it was ignored.')
        else:
            if len(edges) > MAX_EDGES:
                notes.append(f'{len(edges) - MAX_EDGES} edges beyond the {MAX_EDGES}th were not drawn.')
            bad_edge_objs = missing_refs = bad_styles = bad_pts = bad_lat = 0
            for idx, raw_e in enumerate(edges[:MAX_EDGES]):
                if not isinstance(raw_e, dict):
                    bad_edge_objs += 1
                    edge_slots.append(None)
                    continue
                frm = raw_e.get('from')
                to = raw_e.get('to')
                if not isinstance(frm, str) or not isinstance(to, str) or frm not in node_by_id or to not in node_by_id or frm == to:
                    missing_refs += 1
                    edge_slots.append(None)
                    continue

                raw_style = raw_e.get('style')
                if raw_style is None:
                    estyle = 'solid'
                elif isinstance(raw_style, str) and raw_style in EDGE_STYLES:
                    estyle = raw_style
                else:
                    bad_styles += 1
                    estyle = 'solid'

                ecurve = _clamp_pct(raw_e.get('curve'), 0.0, -100.0, 100.0, clamped_coords)
                ecol = pal['accent2']
                if raw_e.get('color') is not None:
                    if isinstance(raw_e.get('color'), str) and HEX6_RE.match(raw_e['color'].strip()):
                        ecol = raw_e['color'].strip().lower()
                    else:
                        bad_cols.append(f'edge[{idx}].color')

                pts_out: list[tuple[float, float]] | None = None
                if raw_e.get('points') is not None:
                    raw_p = raw_e.get('points')
                    if isinstance(raw_p, list):
                        if len(raw_p) > MAX_POINTS:
                            notes.append(f'Edge {idx} had more than {MAX_POINTS} route points; extra points were dropped.')
                        parsed_pts: list[tuple[float, float]] = []
                        ok_all = True
                        for pt in raw_p[:MAX_POINTS]:
                            if not isinstance(pt, dict):
                                ok_all = False
                                break
                            px = C.finite(pt.get('x'), 0.0, 100.0)
                            py = C.finite(pt.get('y'), 0.0, 100.0)
                            if px is None or py is None:
                                ok_all = False
                                break
                            pair = (round(px, 2), round(py, 2))
                            if not parsed_pts or parsed_pts[-1] != pair:
                                parsed_pts.append(pair)
                        if ok_all and len(parsed_pts) >= 2:
                            pts_out = parsed_pts
                        else:
                            bad_pts += 1
                    else:
                        bad_pts += 1

                lat_out: tuple[float, float] | None = None
                if raw_e.get('label_at') is not None:
                    rl = raw_e.get('label_at')
                    if isinstance(rl, dict):
                        lx = C.finite(rl.get('x'), 0.0, 100.0)
                        ly = C.finite(rl.get('y'), 0.0, 100.0)
                        if lx is not None and ly is not None:
                            lat_out = (round(lx, 2), round(ly, 2))
                        else:
                            bad_lat += 1
                    else:
                        bad_lat += 1

                elbl = _clean_str(raw_e.get('label'), 48, trunc_count, '')
                elbl2 = _clean_str(raw_e.get('label2'), 48, trunc_count, '') if elbl else ''
                eat = _clamp_pct(raw_e.get('at'), min(1.0, 0.25 + idx * 0.05), 0.0, 1.0, clamped_coords)
                edur = _clamp_pct(raw_e.get('dur'), 0.10, 0.01, 1.0, clamped_coords)
                edge_slots.append({
                    'index': idx, 'from': frm, 'to': to, 'label': elbl, 'label2': elbl2,
                    'style': estyle, 'both': raw_e.get('both') is True, 'curve': ecurve,
                    'points': pts_out, 'label_at': lat_out, 'color': ecol, 'at': eat, 'dur': edur,
                })
            if bad_edge_objs:
                notes.append(f'{bad_edge_objs} edge entries were not objects and were left out.')
            if missing_refs:
                notes.append(f'{missing_refs} edges pointed at missing or identical nodes and were left out.')
            if bad_styles:
                notes.append(f'{bad_styles} unknown edge styles defaulted to solid.')
            if bad_pts:
                notes.append(f'{bad_pts} invalid edge point routes were ignored in favour of curves.')
            if bad_lat:
                notes.append(f'{bad_lat} invalid edge label_at positions were ignored.')

    # 4. Messages (max 12)
    clean_msgs: list[dict] = []
    if messages is not None:
        if not isinstance(messages, list):
            notes.append('The messages field was not a list, so it was ignored.')
        else:
            if len(messages) > MAX_MESSAGES:
                notes.append(f'{len(messages) - MAX_MESSAGES} messages beyond the {MAX_MESSAGES}th were not drawn.')
            bad_m_objs = bad_m_edges = 0
            for idx, raw_m in enumerate(messages[:MAX_MESSAGES]):
                if not isinstance(raw_m, dict):
                    bad_m_objs += 1
                    continue
                ek = raw_m.get('edge')
                if isinstance(ek, bool) or not isinstance(ek, int) or not (0 <= ek < len(edge_slots)) or edge_slots[ek] is None:
                    bad_m_edges += 1
                    continue
                mtxt = _clean_str(raw_m.get('text'), 40, trunc_count, 'payload') or 'payload'
                mcol = pal['accent']
                if raw_m.get('color') is not None:
                    if isinstance(raw_m.get('color'), str) and HEX6_RE.match(raw_m['color'].strip()):
                        mcol = raw_m['color'].strip().lower()
                    else:
                        bad_cols.append(f'message[{idx}].color')
                edge_at = edge_slots[ek]['at']  # type: ignore[index]
                mat = _clamp_pct(raw_m.get('at'), min(1.0, edge_at + 0.04 + idx * 0.04), 0.0, 1.0, clamped_coords)
                mdur = _clamp_pct(raw_m.get('dur'), 0.10, 0.01, 1.0, clamped_coords)
                clean_msgs.append({
                    'index': idx, 'edge': ek, 'text': mtxt, 'back': raw_m.get('back') is True,
                    'color': mcol, 'at': mat, 'dur': mdur,
                })
            if bad_m_objs:
                notes.append(f'{bad_m_objs} message entries were not objects and were left out.')
            if bad_m_edges:
                notes.append(f'{bad_m_edges} messages pointed at a missing or dropped edge and were left out.')

    if bad_cols:
        notes.append(f'Invalid #rrggbb colours defaulted on: {", ".join(bad_cols[:8])}.')
    if clamped_opts:
        notes.append(f'Out-of-range or invalid options clamped: {", ".join(clamped_opts)}.')
    if clamped_coords[0]:
        notes.append(f'{clamped_coords[0]} out-of-range coordinate or timing values were clamped.')
    if trunc_count[0]:
        notes.append(f'{trunc_count[0]} text fields exceeded their character limit and were truncated.')
    if extra_keys:
        plural = 's' if len(extra_keys) > 1 else ''
        notes.append(f'Unknown option{plural} ignored: {", ".join(C.plain(k)[:30] for k in extra_keys)}.')

    spec = {
        'w': W, 'h': H, 'size': sz, 'radius': rad, 'label': aria_label, 'pal': pal,
        'groups': clean_groups, 'nodes': clean_nodes, 'edge_slots': edge_slots, 'messages': clean_msgs,
    }
    return spec, notes


def _rim(cx: float, cy: float, hw: float, hh: float, dx: float, dy: float) -> tuple[float, float]:
    tx = 1e9 if abs(dx) < 1e-9 else hw / abs(dx)
    ty = 1e9 if abs(dy) < 1e-9 else hh / abs(dy)
    t = min(tx, ty)
    return (cx + dx * t, cy + dy * t)


def _rounded_poly_d(pts: list[tuple[float, float]], rad: int) -> str:
    d = f'M{_n(pts[0][0])} {_n(pts[0][1])}'
    for i in range(1, len(pts) - 1):
        ax, ay = pts[i - 1]
        cx, cy = pts[i]
        zx, zy = pts[i + 1]
        l1 = math.hypot(cx - ax, cy - ay)
        l2 = math.hypot(zx - cx, zy - cy)
        rr = min(float(rad), l1 / 2.0, l2 / 2.0)
        cross = (cx - ax) * (zy - cy) - (cy - ay) * (zx - cx)
        if rr < 0.5 or abs(cross) < 0.01 or l1 < 1e-6 or l2 < 1e-6:
            d += f' L{_n(cx)} {_n(cy)}'
        else:
            p1x, p1y = cx - (cx - ax) / l1 * rr, cy - (cy - ay) / l1 * rr
            p2x, p2y = cx + (zx - cx) / l2 * rr, cy + (zy - cy) / l2 * rr
            d += f' L{_n(p1x)} {_n(p1y)} Q{_n(cx)} {_n(cy)} {_n(p2x)} {_n(p2y)}'
    d += f' L{_n(pts[-1][0])} {_n(pts[-1][1])}'
    return d


def _dash_segments_d(pts: list[tuple[float, float]], dash: float = 8.0, gap: float = 7.0) -> str:
    """Convert a polyline into dashed M/L subpaths (1 <path>, zero stroke-dasharray)."""
    if len(pts) < 2:
        return ''
    cmds: list[str] = []
    period = dash + gap
    dist_along = 0.0
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        seg_len = math.hypot(x1 - x0, y1 - y0)
        if seg_len < 1e-6:
            continue
        ux, uy = (x1 - x0) / seg_len, (y1 - y0) / seg_len
        pos = 0.0
        while pos < seg_len - 1e-6:
            phase = (dist_along + pos) % period
            if phase < dash:
                step = min(dash - phase, seg_len - pos)
                sx, sy = x0 + ux * pos, y0 + uy * pos
                ex, ey = x0 + ux * (pos + step), y0 + uy * (pos + step)
                cmds.append(f'M{_n(sx)} {_n(sy)} L{_n(ex)} {_n(ey)}')
                pos += step
            else:
                pos += min(period - phase, seg_len - pos)
        dist_along += seg_len
    return ' '.join(cmds)


def _dashed_rect_d(x: float, y: float, w: float, h: float, rx: float = 18.0) -> str:
    r = min(rx, w / 2.0, h / 2.0)
    pts: list[tuple[float, float]] = []
    corners = [
        (x + w - r, y + r, -math.pi / 2, 0.0),
        (x + w - r, y + h - r, 0.0, math.pi / 2),
        (x + r, y + h - r, math.pi / 2, math.pi),
        (x + r, y + r, math.pi, 1.5 * math.pi),
    ]
    for ccx, ccy, a0, a1 in corners:
        for step in range(4):
            ang = a0 + (a1 - a0) * (step / 3.0)
            pts.append((ccx + r * math.cos(ang), ccy + r * math.sin(ang)))
    pts.append(pts[0])
    return _dash_segments_d(pts, dash=8.0, gap=7.0)


def _sample_quad(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], steps: int = 28) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        v = 1.0 - t
        out.append((
            v * v * p0[0] + 2 * v * t * p1[0] + t * t * p2[0],
            v * v * p0[1] + 2 * v * t * p1[1] + t * t * p2[1],
        ))
    return out


def _point_and_tangent(samples: list[tuple[float, float]], u: float) -> tuple[float, float, float, float]:
    """Return (x, y, unit_tx, unit_ty) at arc-length fraction u in [0, 1]."""
    if len(samples) < 2:
        return (samples[0][0], samples[0][1], 1.0, 0.0)
    cum = [0.0]
    for i in range(len(samples) - 1):
        cum.append(cum[-1] + math.hypot(samples[i + 1][0] - samples[i][0], samples[i + 1][1] - samples[i][1]))
    tot = cum[-1]
    if tot < 1e-6:
        return (samples[0][0], samples[0][1], 1.0, 0.0)
    target = max(0.0, min(1.0, u)) * tot
    for i in range(len(samples) - 1):
        if cum[i + 1] >= target - 1e-9 or i == len(samples) - 2:
            seg = max(cum[i + 1] - cum[i], 1e-6)
            f = max(0.0, min(1.0, (target - cum[i]) / seg))
            dx = samples[i + 1][0] - samples[i][0]
            dy = samples[i + 1][1] - samples[i][1]
            ln = math.hypot(dx, dy) or 1.0
            return (samples[i][0] + dx * f, samples[i][1] + dy * f, dx / ln, dy / ln)
    return (samples[-1][0], samples[-1][1], 1.0, 0.0)


def _overlap_area(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return ox * oy if (ox > 0 and oy > 0) else 0.0



def _arrowhead_path(tip: tuple[float, float], prev: tuple[float, float], col: str) -> str:
    hx, hy = tip[0] - prev[0], tip[1] - prev[1]
    hl = math.hypot(hx, hy) or 1.0
    ux, uy = hx / hl, hy / hl
    x1, y1 = tip[0] - ux * 10.5 - uy * 5.5, tip[1] - uy * 10.5 + ux * 5.5
    x2, y2 = tip[0] - ux * 10.5 + uy * 5.5, tip[1] - uy * 10.5 - ux * 5.5
    return (
        f'<path d="M{_n(x1)} {_n(y1)} L{_n(tip[0])} {_n(tip[1])} L{_n(x2)} {_n(y2)}" '
        f'fill="none" stroke="{col}" stroke-width="2.2"/>'
    )


# ---------------------------------------------------------------------------
# Text metrics: advance widths in 1/100 em of the Helvetica-metric sans-serif that Chromium resolved
# 'sans-serif' to on the test machine (measured with getComputedTextLength). Order: ASCII 32..126, then _EXTRA.
# Estimates carry a 6 % margin for wider faces; wider fallbacks (DejaVu Sans) are not covered, see the note.
# ---------------------------------------------------------------------------
_EXTRA = '·…–—’'
_ADV_R = (28, 28, 36, 56, 56, 89, 67, 19, 33, 33, 39, 58, 28, 33, 28, 28, 56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 28, 28, 58, 58, 58, 56,
          102, 67, 67, 72, 72, 67, 61, 78, 72, 28, 50, 67, 56, 83, 72, 78, 67, 78, 72, 67, 61, 72, 67, 94, 67, 67, 61, 28, 28, 28, 47, 56,
          33, 56, 56, 50, 56, 56, 28, 56, 56, 22, 22, 50, 22, 83, 56, 56, 56, 56, 33, 50, 28, 56, 50, 72, 50, 50, 50, 33, 26, 33, 58,
          33, 100, 56, 100, 22)
_ADV_B = (28, 33, 47, 56, 56, 89, 72, 24, 33, 33, 39, 58, 28, 33, 28, 28, 56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 33, 33, 58, 58, 58, 61,
          98, 72, 72, 72, 72, 67, 61, 78, 72, 28, 56, 72, 61, 83, 72, 78, 67, 78, 72, 67, 61, 72, 67, 94, 67, 67, 61, 33, 28, 33, 58, 56,
          33, 56, 61, 56, 61, 56, 33, 61, 61, 28, 28, 56, 28, 89, 61, 61, 61, 61, 39, 56, 33, 61, 56, 78, 56, 56, 50, 39, 28, 39, 58,
          33, 100, 56, 100, 28)


def _tw(text: str, fs: float, bold: bool = False) -> float:
    """Estimated rendered width of text in px."""
    tab = _ADV_B if bold else _ADV_R
    tot = 0
    for ch in text:
        o = ord(ch)
        if 32 <= o <= 126:
            tot += tab[o - 32]
        elif ch in _EXTRA:
            tot += tab[95 + _EXTRA.index(ch)]
        elif unicodedata.east_asian_width(ch) in ('W', 'F'):
            tot += 100
        else:
            tot += 62
    return tot / 100.0 * fs * 1.06


def _fit(text: str, max_px: float, fs: float, bold: bool, cut: list[int]) -> str:
    """Return text unchanged if it fits max_px, else the longest prefix + ellipsis that fits (counted in cut)."""
    if not text or _tw(text, fs, bold) <= max_px:
        return text
    cut[0] += 1
    k = len(text)
    while k > 1 and _tw(text[:k].rstrip() + '…', fs, bold) > max_px:
        k -= 1
    return text[:k].rstrip() + '…'


def _glyph(kind: str, cx: float, cy: float, tint: str, k: float = 1.0) -> str:
    """One font-independent vector path per node kind (no glyph fonts needed)."""
    def P(dx: float, dy: float) -> str:
        return f'{_n(cx + dx * k)} {_n(cy + dy * k)}'
    sw = _n(1.6 * k)
    if kind == 'user':
        d = (f'M{P(-3, -2.5)} Q{P(-3, -6)} {P(0, -6)} Q{P(3, -6)} {P(3, -2.5)} Q{P(3, 1)} {P(0, 1)} Q{P(-3, 1)} {P(-3, -2.5)} Z '
             f'M{P(-6, 6.5)} Q{P(0, 0)} {P(6, 6.5)}')
    elif kind == 'device':
        d = f'M{P(-3.8, -6)} L{P(3.8, -6)} L{P(3.8, 6)} L{P(-3.8, 6)} Z M{P(-1.2, 3.8)} L{P(1.2, 3.8)}'
    elif kind == 'app':
        d = f'M{P(-5.5, -5)} L{P(5.5, -5)} L{P(5.5, 5)} L{P(-5.5, 5)} Z M{P(-5.5, -1.8)} L{P(5.5, -1.8)}'
    elif kind == 'surface':
        d = f'M{P(-5.5, -4.8)} L{P(5.5, -4.8)} L{P(5.5, 4.8)} L{P(-5.5, 4.8)} Z M{P(-1.8, -4.8)} L{P(-1.8, 4.8)}'
    elif kind == 'tool':
        d = f'M{P(0, -6)} L{P(6, 0)} L{P(0, 6)} L{P(-6, 0)} Z'
    elif kind == 'store':
        d = f'M{P(-5, -4.5)} L{P(5, -4.5)} L{P(5, 4.5)} L{P(-5, 4.5)} Z M{P(-5, -1.2)} L{P(5, -1.2)} M{P(-5, 1.8)} L{P(5, 1.8)}'
    elif kind == 'model':
        d = (f'M{P(0, -6.2)} L{P(1.9, -1.9)} L{P(6.2, 0)} L{P(1.9, 1.9)} L{P(0, 6.2)} L{P(-1.9, 1.9)} '
             f'L{P(-6.2, 0)} L{P(-1.9, -1.9)} Z')
        return f'<path d="{d}" fill="{tint}"/>'
    else:  # server
        d = (f'M{P(-5.5, -4.8)} L{P(5.5, -4.8)} L{P(5.5, -0.8)} L{P(-5.5, -0.8)} Z '
             f'M{P(-5.5, 1.2)} L{P(5.5, 1.2)} L{P(5.5, 5.2)} L{P(-5.5, 5.2)} Z')
    return f'<path d="{d}" fill="none" stroke="{tint}" stroke-width="{sw}"/>'


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def _ov(a, b, tol: float = 0.0) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > tol and min(a[3], b[3]) - max(a[1], b[1]) > tol


def _inside(a, b) -> bool:
    return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]


def _infl(b, d: float):
    return (b[0] - d, b[1] - d, b[2] + d, b[3] + d)


def _pt_box_dist(p, b) -> float:
    dx = max(b[0] - p[0], 0.0, p[0] - b[2])
    dy = max(b[1] - p[1], 0.0, p[1] - b[3])
    return math.hypot(dx, dy)


def _chunks(pts, size=8):
    """(x0, x1, y0, y1, first, last) bounding boxes of consecutive runs of points, for _nearest."""
    out = []
    for i in range(0, len(pts), size):
        run = pts[i:i + size]
        xs = [q[0] for q in run]
        ys = [q[1] for q in run]
        out.append((min(xs), max(xs), min(ys), max(ys), i, i + len(run)))
    return out


def _nearest(pts, box, chunks=None):
    """Same result as min((_pt_box_dist(p, box), p) for p in pts): the smallest distance, the smallest point among equal distances.
    Squared distances are used to find the nearest points (whole runs of points are skipped when their bounding box is already
    farther than the best so far, with a wide margin for rounding); only the points within that margin of the smallest get the
    exact hypot."""
    b0, b1, b2, b3 = box
    if not pts:
        raise ValueError("min() arg is an empty sequence")
    if chunks is None:
        chunks = [(float('-inf'), float('inf'), float('-inf'), float('inf'), 0, len(pts))]
    best2 = float('inf')
    lim = float('inf')
    cand = []
    for x0, x1, y0, y1, i0, i1 in chunks:
        gx = b0 - x1
        if gx <= 0.0:
            gx = x0 - b2
            if gx < 0.0:
                gx = 0.0
        gy = b1 - y1
        if gy <= 0.0:
            gy = y0 - b3
            if gy < 0.0:
                gy = 0.0
        if gx * gx + gy * gy > lim:
            continue
        for i in range(i0, i1):
            p = pts[i]
            px = p[0]
            py = p[1]
            dx = b0 - px
            if dx <= 0.0:
                dx = px - b2
                if dx < 0.0:
                    dx = 0.0
            dy = b1 - py
            if dy <= 0.0:
                dy = py - b3
                if dy < 0.0:
                    dy = 0.0
            d2 = dx * dx + dy * dy
            if d2 <= lim:
                cand.append((d2, p))
                if d2 < best2:
                    best2 = d2
                    lim = d2 * 1.000001 + 1e-9
    hyp = math.hypot
    best_d = float('inf')
    best_p = None
    for d2, p in cand:
        if d2 > lim:
            continue
        px = p[0]
        py = p[1]
        d = hyp(max(b0 - px, 0.0, px - b2), max(b1 - py, 0.0, py - b3))
        if d < best_d or (d == best_d and p < best_p):
            best_d = d
            best_p = p
    return best_d, best_p


def _resample(pts: list[tuple[float, float]], step: float = 4.0) -> list[tuple[float, float]]:
    out = [pts[0]]
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / step))
        for k in range(1, n + 1):
            out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    return out


def _bbox(pts) -> tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _arc_len(samples) -> float:
    return sum(math.hypot(samples[i + 1][0] - samples[i][0], samples[i + 1][1] - samples[i][1]) for i in range(len(samples) - 1))


# ---------------------------------------------------------------------------
# Scene: every variant is built as one pixel-space scene, then emitted by _emit_svg.
#   groups: {i, box, label, hx, hy, hbox, at}      nodes: {i, id, kind, box, label, sub, at, tfs}
#   edges:  {index, samples, d, heads, style, color, at, from, to, lines, lbox}
#   chips:  {msg, edge, box, text, color, at, dir}
# ---------------------------------------------------------------------------
def _edge_route(e: dict, boxes: dict, W: float, H: float, rad: int) -> dict:
    fx, fy, fhw, fhh = boxes[e['from']]
    tx2, ty2, thw, thh = boxes[e['to']]
    if e['points']:
        pts = [(px * W / 100.0, py * H / 100.0) for px, py in e['points']]
        samples = _resample(pts, 3.0)
        d = _rounded_poly_d(pts, rad)
        heads = [(pts[-1], pts[-2])] + ([(pts[0], pts[1])] if e['both'] else [])
    else:
        dx, dy = tx2 - fx, ty2 - fy
        ln = math.hypot(dx, dy) or 1.0
        a = _rim(fx, fy, fhw, fhh, dx, dy)
        z = _rim(tx2, ty2, thw, thh, -dx, -dy)
        mx, my = (a[0] + z[0]) / 2.0, (a[1] + z[1]) / 2.0
        bend = e['curve'] / 100.0
        ctrl = (mx - (dy / ln) * bend * ln * 0.5, my + (dx / ln) * bend * ln * 0.5)
        samples = _resample(_sample_quad(a, ctrl, z, steps=40), 3.0)
        d = f'M{_n(a[0])} {_n(a[1])} Q{_n(ctrl[0])} {_n(ctrl[1])} {_n(z[0])} {_n(z[1])}'
        heads = [(z, samples[-2])] + ([(a, samples[1])] if e['both'] else [])
    return {'samples': samples, 'd': d, 'heads': heads}


def _middle(samples):
    """The middle 70 % of an edge's samples: a leader never lands on the edge where it leaves or enters a node."""
    n = len(samples)
    return samples[int(n * 0.15): max(int(n * 0.15) + 1, int(math.ceil(n * 0.85)))]


def _middle_on_ink(samples, dashed: bool):
    """_middle(), and for a dashed edge only the points that lie on a drawn dash (7 on, 6 off, as _emit_svg draws it),
    so a leader always ends on ink, never in a gap between dashes."""
    mid = _middle(samples)
    if not dashed:
        return mid
    cum, keep, acc = {}, [], 0.0
    for i, q in enumerate(samples):
        if i:
            acc += math.hypot(q[0] - samples[i - 1][0], q[1] - samples[i - 1][1])
        cum[i] = acc
    lo = samples.index(mid[0])
    for k, q in enumerate(mid):
        if 2.0 <= cum[lo + k] % 13.0 <= 5.0:
            keep.append(q)
    return keep or mid


def _leader(box, p) -> tuple[float, float]:
    """Point on the box outline nearest to p (start of a chip's leader line)."""
    return (min(max(p[0], box[0]), box[2]), min(max(p[1], box[1]), box[3]))


def _leader_pts(box, near) -> list[tuple[float, float]]:
    a = _leader(box, near)
    return [(a[0] + (near[0] - a[0]) * k / 16.0, a[1] + (near[1] - a[1]) * k / 16.0) for k in range(1, 16)]


class _Placer:
    """Scores candidate boxes for labels and chips against everything already on the canvas."""

    def __init__(self, W, H, node_boxes, header_boxes, group_boxes, edges):
        self.W, self.H = W, H
        self.nodes = [_infl(b, 4.0) for b in node_boxes]
        self.headers = [_infl(b, 3.0) for b in header_boxes]
        self.groups = group_boxes
        self.edges = {e['index']: (_infl(_bbox(e['samples']), 2.0), e['samples']) for e in edges}
        self.mid = {e['index']: _middle_on_ink(e['samples'], e['style'] == 'dashed') for e in edges}
        self.mid_chunks = {i: _chunks(m) for i, m in self.mid.items()}
        self.placed: list[tuple[tuple[float, float, float, float], int, str]] = []
        self.total = 0.0
        self.leaders: list[tuple[list[tuple[float, float]], int]] = []

    def cost(self, box, own: int, kind: str, ideal) -> float:
        W, H = self.W, self.H
        c = 0.0
        if box[0] < 4 or box[1] < 4 or box[2] > W - 4 or box[3] > H - 4:
            c += 5000.0
        b0, b1, b2, b3 = box
        n_ov = 0
        for b in self.nodes:
            if min(b2, b[2]) - max(b0, b[0]) > 0.0 and min(b3, b[3]) - max(b1, b[1]) > 0.0:
                n_ov += 1
        c += 2000.0 * n_ov
        n_ov = 0
        for b in self.headers:
            if min(b2, b[2]) - max(b0, b[0]) > 0.0 and min(b3, b[3]) - max(b1, b[1]) > 0.0:
                n_ov += 1
        c += 2000.0 * n_ov
        n_ov = 0
        for b, _, _ in self.placed:
            if min(b2, b[2]) - max(b0, b[0]) > 0.0 and min(b3, b[3]) - max(b1, b[1]) > 0.0:
                n_ov += 1
        c += 2000.0 * n_ov
        ib = _infl(box, 2.0)
        i0, i1, i2, i3 = ib
        for idx, (bb, pts) in self.edges.items():
            if not (min(i2, bb[2]) - max(i0, bb[0]) > 0.0 and min(i3, bb[3]) - max(i1, bb[1]) > 0.0):
                continue
            hit = False
            for p in pts:
                if i0 < p[0] < i2 and i1 < p[1] < i3:
                    hit = True
                    break
            if hit:
                if idx != own:
                    c += 600.0
                elif kind == 'label':
                    c += 150.0
        c += 250.0 * sum(1 for g in self.groups if _ov(box, g) and not _inside(box, g))
        for pts, ed in self.leaders:
            if not (kind == 'chip' and ed == own) and any(box[0] + 1 < q[0] < box[2] - 1 and box[1] + 1 < q[1] < box[3] - 1 for q in pts):
                c += 600.0
        dist, near = _nearest(self.mid[own], box, self.mid_chunks[own])
        if kind == 'label' and dist > 14.0:
            c += 400.0 + dist * 4.0
        elif kind == 'chip' and dist > 9.0:
            # a chip that cannot sit on its line gets a leader to the nearest point of it: the leader must cross nothing
            c += 200.0 + dist * 3.0
            for b in self.nodes + self.headers + [b for b, ed, kd in self.placed if not (ed == own and kd == 'chip')]:
                if any(b[0] + 4 < q[0] < b[2] - 4 and b[1] + 4 < q[1] < b[3] - 4 for q in _leader_pts(box, near)):
                    c += 600.0
        cx, cy = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
        return c + math.hypot(cx - ideal[0], cy - ideal[1])

    def best(self, cands, bw, bh, own, kind, ideal, fallback=None):
        best_box, best_c = None, float('inf')
        for pool in (cands, fallback):
            if pool is None or (pool is fallback and best_c < 200.0):
                continue   # the wider grid is only searched when the near candidates all carry a penalty
            for cx, cy in pool:
                box = (cx - bw / 2.0, cy - bh / 2.0, cx + bw / 2.0, cy + bh / 2.0)
                c = self.cost(box, own, kind, ideal)
                if c < best_c:
                    best_box, best_c = box, c
        self.placed.append((_infl(best_box, 3.0), own, kind))
        if kind == 'chip':
            dist, near = _nearest(self.mid[own], best_box, self.mid_chunks[own])
            if dist > 9.0:
                self.leaders.append((_leader_pts(best_box, near), own))
        self.total += best_c
        return best_box


def _label_lines(e: dict, max_px: float, fs: float, cut: list[int]) -> list[str]:
    if not e['label']:
        return []
    out = [_fit(e['label'], max_px, fs, True, cut)]
    if e['label2']:
        out.append(_fit(e['label2'], max_px, fs, True, cut))
    return out


def _label_size(lines: list[str], fs: float) -> tuple[float, float]:
    lw = max(_tw(t, fs, True) for t in lines) + 12.0
    lh = (fs * 2.25 + 8.0) if len(lines) == 2 else (fs + 8.0)
    return lw, lh


def _chip_size(text: str, fs: float) -> tuple[float, float]:
    return max(44.0, _tw(text, fs, True) + 20.0), fs + 12.0



def _node_min_w(nd: dict, F: dict) -> float:
    """Narrowest node box that still shows its texts at full size (same formula _emit_svg uses to place them)."""
    nh = nd['box'][3] - nd['box'][1]
    br = max(9.0, min(13.0, nh * 0.22))
    tw = max(_tw(nd['label'], F['title'], True), _tw(nd['sub'], F['sub'], False) if nd['sub'] else 0.0)
    return 2.0 * br + 20.0 + tw + 14.0


def _relieve_gaps(groups: list, nodes: list, boxes: dict, spec: dict, F: dict, cut: list) -> None:
    """Gap relief. A label or chip on an edge between two groups must fit wholly in the gap between their outlines:
    it may not straddle one. When the authored gap is narrower than the widest such label or chip, (1) the facing
    sides of the two outlines move toward their own contents (a node plus padding), then (2) if that is still not
    enough, the facing nodes are narrowed to their text width (never below it). Gaps that are already wide enough
    are left exactly as authored, so layouts that already pass do not move. Edited in place before edges are routed."""
    memb = {}
    for g in groups:
        b = g['box']
        memb[g['i']] = [n for n in nodes if b[0] <= (n['box'][0] + n['box'][2]) / 2.0 <= b[2] and b[1] <= (n['box'][1] + n['box'][3]) / 2.0 <= b[3]]
    owner = {n['id']: g['i'] for g in groups for n in memb[g['i']]}
    real = {g['i'] for g in groups}
    regs = list(groups)
    for n in nodes:
        if n['id'] not in owner:
            # an ungrouped node is a region of its own (no outline, no padding): the gap between a group outline and
            # such a node holds labels and chips just the same, but only the group outline and the node can move
            k = ('n', n['i'])
            owner[n['id']] = k
            memb[k] = [n]
            regs.append({'i': k, 'box': n['box'], 'hbox': None, 'pseudo': True})
    chips_by_edge: dict[int, list] = {}
    for m in spec['messages']:
        chips_by_edge.setdefault(m['edge'], []).append(m)
    PAD, HDR = 12.0, 34.0
    for ga in regs:
        for gb in regs:
            if ga['i'] == gb['i'] or not memb[ga['i']] or not memb[gb['i']] or (ga['i'] not in real and gb['i'] not in real):
                continue
            for ax in (0, 1):
                lo, hi = ax, ax + 2
                A, B = ga['box'], gb['box']
                if B[lo] < A[hi] - 1e-6 or not (min(A[3 - ax], B[3 - ax]) > max(A[1 - ax], B[1 - ax])):
                    continue
                need = 0.0
                for e in spec['edge_slots']:
                    if e is None or {owner.get(e['from']), owner.get(e['to'])} != {ga['i'], gb['i']}:
                        continue
                    lines = _label_lines(e, float(spec['w']) * 0.4, F['lbl'], [0])
                    sizes = [_label_size(lines, F['lbl'])] if lines else []
                    sizes += [_chip_size(m['text'], F['chip']) for m in chips_by_edge.get(e['index'], [])]
                    for sz_ in sizes:
                        need = max(need, sz_[ax] + 8.0)
                if need <= B[lo] - A[hi]:
                    continue
                for attempt in (0, 1):
                    A, B = ga['box'], gb['box']
                    gap = B[lo] - A[hi]
                    if need <= gap:
                        break
                    ca = max(n['box'][hi] for n in memb[ga['i']]) + (0.0 if ga.get('pseudo') else PAD)
                    cb = min(n['box'][lo] for n in memb[gb['i']]) - (0.0 if gb.get('pseudo') else PAD + ((HDR - PAD) if ax == 1 else 0.0))
                    room_a, room_b = max(0.0, A[hi] - ca), max(0.0, cb - B[lo])
                    want = need - gap
                    db = min(room_b, want / 2.0)
                    da = min(room_a, want - db)
                    db = min(room_b, want - da)
                    nA, nB = list(A), list(B)
                    nA[hi] -= da
                    nB[lo] += db
                    ga['box'], gb['box'] = tuple(nA), tuple(nB)
                    if attempt == 0 and ax == 0 and need > gb['box'][0] - ga['box'][2]:
                        # step 2: narrow the facing nodes to their text, then pull the outlines in again (second pass)
                        for g_, side in ((ga, 1), (gb, 0)):
                            edge = (max if side else min)(n['box'][2 if side else 0] for n in memb[g_['i']])
                            for n in memb[g_['i']]:
                                x0, y0, x1, y1 = n['box']
                                if abs((x1 if side else x0) - edge) > 1.0:
                                    continue
                                mw = _node_min_w(n, F)
                                cut_ = max(0.0, (x1 - x0) - mw)
                                nb = (x0, y0, x1 - cut_, y1) if side else (x0 + cut_, y0, x1, y1)
                                n['box'] = nb
                                boxes[n['id']] = ((nb[0] + nb[2]) / 2.0, (nb[1] + nb[3]) / 2.0, (nb[2] - nb[0]) / 2.0, (nb[3] - nb[1]) / 2.0)
                        for r_ in (ga, gb):
                            if r_.get('pseudo'):
                                r_['box'] = memb[r_['i']][0]['box']
    # edges between two side-by-side nodes whose clear span is narrower than their label or chips: narrow the two nodes
    # toward their text width (never below it) so the label can sit by the line instead of being parked away from it
    byid = {n['id']: n for n in nodes}
    for e in spec['edge_slots']:
        if e is None or e['points'] or e['from'] not in byid or e['to'] not in byid:
            continue
        na, nb_ = byid[e['from']], byid[e['to']]
        if na['box'][0] > nb_['box'][0]:
            na, nb_ = nb_, na
        A, B = na['box'], nb_['box']
        if B[0] < A[2] - 1e-6 or not (min(A[3], B[3]) > max(A[1], B[1])):
            continue
        lines = _label_lines(e, float(spec['w']) * 0.4, F['lbl'], [0])
        sizes = [_label_size(lines, F['lbl'])] if lines else []
        sizes += [_chip_size(m['text'], F['chip']) for m in chips_by_edge.get(e['index'], [])]
        need = max((z[0] for z in sizes), default=0.0) + 8.0
        want = need - (B[0] - A[2])
        if want <= 0:
            continue
        ca_ = max(0.0, (A[2] - A[0]) - _node_min_w(na, F))
        cb_ = max(0.0, (B[2] - B[0]) - _node_min_w(nb_, F))
        da = min(ca_, want / 2.0)
        db = min(cb_, want - da)
        da = min(ca_, want - db)
        for n, (x0, y0, x1, y1) in ((na, (A[0], A[1], A[2] - da, A[3])), (nb_, (B[0] + db, B[1], B[2], B[3]))):
            n['box'] = (x0, y0, x1, y1)
            boxes[n['id']] = ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) / 2.0, (y1 - y0) / 2.0)
    for g in groups:
        if g['hbox']:
            w_ = g['hbox'][2] - g['hbox'][0]
            g['hx'], g['hy'] = g['box'][0] + 14.0, g['box'][1] + 22.0
            g['hbox'] = (g['hx'] - 1.0, g['hy'] - F['hdr'] * 0.95, g['hx'] - 1.0 + w_, g['hy'] + F['hdr'] * 0.25)


def _wide_scene(spec: dict) -> dict:
    W, H = float(spec['w']), float(spec['h'])
    sz = spec['size']
    F = {'title': max(12, sz), 'sub': max(12, sz - 5), 'lbl': max(12, sz - 4), 'chip': max(12, sz - 4), 'hdr': max(12, sz - 5)}
    cut = [0]
    groups = []
    for i, g in enumerate(spec['groups']):
        box = (g['x'] * W / 100.0, g['y'] * H / 100.0, (g['x'] + g['w']) * W / 100.0, (g['y'] + g['h']) * H / 100.0)
        hx, hy = box[0] + 14.0, box[1] + 22.0
        txt = _fit(g['label'].upper(), box[2] - box[0] - 28.0, F['hdr'], True, cut) if g['label'] else ''
        hbox = (hx - 1.0, hy - F['hdr'] * 0.95, hx + _tw(txt, F['hdr'], True), hy + F['hdr'] * 0.25) if txt else None
        groups.append({'i': i, 'box': box, 'label': txt, 'hx': hx, 'hy': hy, 'hbox': hbox, 'at': g['at']})
    nodes, boxes = [], {}
    for i, nd in enumerate(spec['nodes']):
        cx, cy = nd['x'] * W / 100.0, nd['y'] * H / 100.0
        hw, hh = nd['w'] * W / 200.0, nd['h'] * H / 200.0
        boxes[nd['id']] = (cx, cy, hw, hh)
        nodes.append({'i': i, 'id': nd['id'], 'kind': nd['kind'], 'box': (cx - hw, cy - hh, cx + hw, cy + hh),
                      'label': nd['label'], 'sub': nd['sub'], 'at': nd['at']})
    _relieve_gaps(groups, nodes, boxes, spec, F, cut)
    edges = []
    for e in spec['edge_slots']:
        if e is None:
            continue
        r = _edge_route(e, boxes, W, H, spec['radius'])
        edges.append({**r, 'index': e['index'], 'style': e['style'], 'color': e['color'], 'at': e['at'],
                      'from': e['from'], 'to': e['to'], 'lines': _label_lines(e, W * 0.4, F['lbl'], cut), 'lbox': None,
                      'label_at': e['label_at']})
    eby = {e['index']: e for e in edges}

    def place_labels(placer, lbox):
        for e in edges:
            if not e['lines']:
                continue
            lw, lh = _label_size(e['lines'], F['lbl'])
            cands, ideal = [], None
            s = e['samples']
            for u in (0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74, 0.18, 0.82):
                px, py, ux, uy = _point_and_tangent(s, u)
                nx, ny = -uy, ux
                base = abs(nx) * lw / 2.0 + abs(ny) * lh / 2.0 + 5.0
                for extra in (0.0, 6.0, 12.0, 20.0, 30.0, 42.0, 56.0):
                    for sgn in (1.0, -1.0):
                        cands.append((px + nx * (base + extra) * sgn, py + ny * (base + extra) * sgn))
                if ideal is None:
                    # default side: above a horizontal-ish line, left of a vertical-ish one
                    sgn = -1.0 if (ny > 0 if abs(uy) <= 0.72 else nx > 0) else 1.0
                    ideal = (px + nx * base * sgn, py + ny * base * sgn)
            if e['label_at']:
                lx, ly = e['label_at'][0] * W / 100.0, e['label_at'][1] * H / 100.0
                ideal = (lx, ly)
                for dy in range(-32, 33, 8):
                    for dx in range(-48, 49, 8):
                        cands.append((lx + dx, ly + dy))
            lbox[e['index']] = placer.best(cands, lw, lh, e['index'], 'label', ideal)

    def place_chips(placer, chips):
        by_edge: dict[int, list[dict]] = {}
        for m in spec['messages']:
            by_edge.setdefault(m['edge'], []).append(m)
        for m in spec['messages']:
            e = eby.get(m['edge'])
            if e is None:
                continue
            sib = by_edge[m['edge']]
            rank, cnt = sib.index(m), len(sib)
            u_pref = 0.5 if cnt == 1 else 0.3 + 0.4 * rank / (cnt - 1)
            cw, ch = _chip_size(m['text'], F['chip'])
            s = e['samples']
            total = _arc_len(s)
            cands = []
            us = sorted((k / 50.0 for k in range(8, 43)), key=lambda u: (abs(u - u_pref), u))
            for u in us:
                px, py, ux, uy = _point_and_tangent(s, u)
                half_along = abs(ux) * cw / 2.0 + abs(uy) * ch / 2.0 + 14.0
                if u * total < half_along or (1 - u) * total < half_along:
                    continue
                cands.append((px, py))
            for q, u in enumerate(us):
                px, py, ux, uy = _point_and_tangent(s, u)
                nx, ny = -uy, ux
                for extra in (4.0, 12.0, 22.0, 34.0, 48.0, 64.0, 82.0) if q < 12 else (4.0, 12.0):
                    off = abs(nx) * cw / 2.0 + abs(ny) * ch / 2.0 + extra
                    cands += [(px + nx * off, py + ny * off), (px - nx * off, py - ny * off)]
            ideal = _point_and_tangent(s, u_pref)[:2]
            mx0, my0 = ideal
            grid = [(mx0 + dx, my0 + dy) for dy in range(-96, 97, 12) for dx in range(-int(cw / 2 + 80), int(cw / 2 + 81), 12)]
            box = placer.best(cands, cw, ch, e['index'], 'chip', ideal, fallback=grid)
            cxm, cym = (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0
            j = min(range(len(s)), key=lambda q: math.hypot(s[q][0] - cxm, s[q][1] - cym))
            a, b = s[max(0, j - 1)], s[min(len(s) - 1, j + 1)]
            ln = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            dvec = ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
            if m['back']:
                dvec = (-dvec[0], -dvec[1])
            dist, near = min((_pt_box_dist(p, box), p) for p in placer.mid[e['index']])
            leader = (_leader(box, near), near) if dist > 9.0 else None
            chips.append({'msg': m['index'], 'edge': m['edge'], 'box': box, 'text': m['text'], 'color': m['color'], 'at': m['at'], 'dir': dvec,
                          'leader': leader})

    # try labels-first (the author's label_at wins) and chips-first; keep the cheaper layout (ties: labels first)
    best = None
    for order in ('labels', 'chips'):
        placer = _Placer(W, H, [n['box'] for n in nodes], [g['hbox'] for g in groups if g['hbox']], [g['box'] for g in groups], edges)
        lbox, chips = {}, []
        for step in ((place_labels, lbox), (place_chips, chips)) if order == 'labels' else ((place_chips, chips), (place_labels, lbox)):
            step[0](placer, step[1])
        if best is None or placer.total < best[0] - 1e-6:
            best = (placer.total, lbox, chips)
    _, lbox, chips = best
    for e in edges:
        e['lbox'] = lbox.get(e['index'])
    return {'W': W, 'H': H, 'F': F, 'groups': groups, 'nodes': nodes, 'edges': edges, 'chips': chips, 'cut': cut[0], 'badge': None}


def _order_bands(bands: list, edges: list) -> list:
    """Reorder nodes inside each group band (up to 6 members) and the run of ungrouped nodes (up to 7) so that as many
    edges as possible join neighbouring rows: fewer skip edges means fewer lanes. Ties keep the payload's order."""
    grouped = [b for b in bands if b[0] is not None]
    loose = [b[1][0] for b in bands if b[0] is None]

    def cost(bs, lo):
        order = [n['id'] for _, mem in bs for n in mem] + [n['id'] for n in lo]
        r = {nid: i for i, nid in enumerate(order)}
        return sum(abs(r[e['from']] - r[e['to']]) - 1 for e in edges)

    for _ in range(2):
        for bi, (gi, mem) in enumerate(grouped):
            if len(mem) > 6:
                continue
            best = min(itertools.permutations(mem), key=lambda p: cost(grouped[:bi] + [(gi, list(p))] + grouped[bi + 1:], loose))
            grouped[bi] = (gi, list(best))
        if 1 < len(loose) <= 7:
            loose = list(min(itertools.permutations(loose), key=lambda p: cost(grouped, list(p))))
    return grouped + [(None, [n]) for n in loose]


def _narrow_scene(spec: dict) -> dict:
    """Phone layout: one column of nodes. Edges between neighbouring rows run straight down a line near the left
    of the boxes; edges that skip rows run in their own lane right of the boxes (nested, shortest span innermost).
    Every label and every chip gets its own row in a gap, beside its own line, so nothing can collide."""
    W = 420.0
    F = {'title': 18, 'sub': 15, 'lbl': 16, 'chip': 16, 'hdr': 14}
    cut = [0]
    nodes_in, groups_in = spec['nodes'], spec['groups']
    assigned: set[str] = set()
    bands: list[tuple[int | None, list[dict]]] = []
    for gi, g in enumerate(groups_in):
        mem = [n for n in nodes_in if n['id'] not in assigned and g['x'] <= n['x'] <= g['x'] + g['w'] and g['y'] <= n['y'] <= g['y'] + g['h']]
        mem.sort(key=lambda it: (it['y'], it['x']))
        if mem:
            assigned.update(m['id'] for m in mem)
            bands.append((gi, mem))
    for ln in sorted((n for n in nodes_in if n['id'] not in assigned), key=lambda it: (round(it['x'] / 20.0), it['y'])):
        bands.append((None, [ln]))
    bands = _order_bands(bands, [e for e in spec['edge_slots'] if e is not None])
    rows = [n for _, mem in bands for n in mem]
    band_of_row = [bi for bi, (_, mem) in enumerate(bands) for _ in mem]
    row_of = {n['id']: r for r, n in enumerate(rows)}
    R = len(rows)
    edges_in = [e for e in spec['edge_slots'] if e is not None]
    # lanes for skip edges
    skips = sorted((e for e in edges_in if abs(row_of[e['from']] - row_of[e['to']]) > 1),
                   key=lambda e: (abs(row_of[e['from']] - row_of[e['to']]), e['index']))
    lane: dict[int, int] = {}
    span = {e['index']: (min(row_of[e['from']], row_of[e['to']]), max(row_of[e['from']], row_of[e['to']])) for e in edges_in}
    for e in skips:
        lo, hi = span[e['index']]
        k = 0
        while any(lane[o] == k and not (span[o][1] < lo or span[o][0] > hi) for o in lane):
            k += 1
        lane[e['index']] = k
    L = (max(lane.values()) + 1) if lane else 0
    node_l = 22.0
    node_r = 398.0 if L == 0 else max(250.0, 388.0 - 16.0 * L)
    lane_step = 16.0 if L == 0 else min(16.0, (402.0 - node_r - 16.0) / max(1, L - 1) if L > 1 else 16.0)
    lane_x = {idx: node_r + 16.0 + lane_step * k for idx, k in lane.items()}
    x_adj0 = node_l + 32.0
    # gap assignments
    adj_in_gap: dict[int, list[int]] = {}
    for e in edges_in:
        if e['index'] not in lane:
            adj_in_gap.setdefault(span[e['index']][0], []).append(e['index'])
    x_line = {}
    for g, lst in adj_in_gap.items():
        for k, idx in enumerate(lst):
            x_line[idx] = x_adj0 + 22.0 * k
    content_gap: dict[int, int] = {}
    for e in edges_in:
        idx = e['index']
        lo, hi = span[idx]
        if idx not in lane:
            content_gap[idx] = lo
            continue
        down = row_of[e['to']] > row_of[e['from']]
        best = None
        for g in range(lo, hi):
            inner = sum(1 for o in lane if lane[o] < lane[idx] and span[o][0] <= g < span[o][1])
            near = (g - lo) if down else (hi - 1 - g)
            key = (inner, near)
            if best is None or key < best[0]:
                best = (key, g)
        content_gap[idx] = best[1]
    msgs_by_edge: dict[int, list[dict]] = {}
    for m in spec['messages']:
        msgs_by_edge.setdefault(m['edge'], []).append(m)
    # items per gap: (edge index, 'label'|'chip', payload)
    items: dict[int, list[tuple]] = {}
    for e in sorted(edges_in, key=lambda e: (e['index'] in lane, e['index'])):
        g = content_gap[e['index']]
        if e['label']:
            items.setdefault(g, []).append((e['index'], 'label', e))
        for m in msgs_by_edge.get(e['index'], []):
            items.setdefault(g, []).append((e['index'], 'chip', m))

    def item_h(it) -> float:
        if it[1] == 'chip':
            return F['chip'] + 12.0
        return (F['lbl'] * 2.25 + 8.0) if it[2]['label2'] else (F['lbl'] + 8.0)

    row_h = 64.0
    top_m, bot_m, sp = 16.0, 18.0, 8.0
    y = 12.0
    node_box: dict[str, tuple] = {}
    band_box: dict[int, list[float]] = {}
    gap_top: dict[int, float] = {}
    hdr_cross: set[int] = set()
    for r, nd in enumerate(rows):
        bi = band_of_row[r]
        gi = bands[bi][0]
        if r == 0 or band_of_row[r - 1] != bi:
            if r > 0:
                y += 14.0
            band_box[bi] = [y, 0.0]
            if gi is not None:
                y += 34.0
                if r > 0 and any(span[i] == (r - 1, r) for i in x_line):
                    hdr_cross.add(bi)
        node_box[nd['id']] = (node_l, y, node_r, y + row_h)
        y += row_h
        last_in_band = r == R - 1 or band_of_row[r + 1] != bi
        if r < R - 1:
            its = items.get(r, [])
            gap_top[r] = y + top_m
            content = sum(item_h(it) for it in its) + sp * max(0, len(its) - 1)
            if last_in_band:
                y += (top_m + content + 10.0) if its else 14.0
            else:
                y += max(44.0, top_m + content + bot_m)
        if last_in_band:
            band_box[bi][1] = y + (4.0 if gi is not None else 0.0)
            y = band_box[bi][1]
    H = float(int(math.ceil(y + 12.0)))
    # groups
    groups = []
    for bi, (gi, mem) in enumerate(bands):
        if gi is None:
            continue
        g = groups_in[gi]
        box = (6.0, band_box[bi][0], W - 6.0, band_box[bi][1])
        hx = (x_adj0 + 14.0) if bi in hdr_cross else 20.0
        hy = box[1] + 23.0
        r0 = row_of[mem[0]['id']]
        lanes_here = [lane_x[i] for i in lane if span[i][0] <= r0 - 1 < span[i][1]]
        limit = (min(lanes_here) - 8.0) if lanes_here else (W - 20.0)
        txt = _fit(g['label'].upper(), limit - hx, F['hdr'], True, cut) if g['label'] else ''
        hbox = (hx - 1.0, hy - F['hdr'] * 0.95, hx + _tw(txt, F['hdr'], True), hy + F['hdr'] * 0.25) if txt else None
        groups.append({'i': gi, 'box': box, 'label': txt, 'hx': hx, 'hy': hy, 'hbox': hbox, 'at': g['at']})
    nodes = [{'i': i, 'id': nd['id'], 'kind': nd['kind'], 'box': node_box[nd['id']], 'label': nd['label'], 'sub': nd['sub'], 'at': nd['at']}
             for i, nd in enumerate(nodes_in)]
    # ports on the right rim for lane edges: upward stubs on top (inner lane first), downward below (outer lane first)
    ports: dict[str, list[tuple]] = {}
    for e in edges_in:
        if e['index'] not in lane:
            continue
        for end, other in ((e['from'], e['to']), (e['to'], e['from'])):
            up = row_of[other] < row_of[end]
            key = (0, lane[e['index']]) if up else (1, -lane[e['index']])
            ports.setdefault(end, []).append((key, e['index']))
    port_y: dict[tuple[str, int], float] = {}
    for nid, lst in ports.items():
        lst.sort()
        b = node_box[nid]
        cy = (b[1] + b[3]) / 2.0
        n = len(lst)
        stepy = min(12.0, (row_h - 20.0) / max(1, n - 1))
        for k, (_, idx) in enumerate(lst):
            port_y[(nid, idx)] = cy + (k - (n - 1) / 2.0) * stepy
    edges = []
    for e in edges_in:
        idx = e['index']
        bf, bt = node_box[e['from']], node_box[e['to']]
        if idx in lane:
            lx = lane_x[idx]
            pts = [(node_r, port_y[(e['from'], idx)]), (lx, port_y[(e['from'], idx)]), (lx, port_y[(e['to'], idx)]), (node_r, port_y[(e['to'], idx)])]
        else:
            x = x_line[idx]
            down = row_of[e['to']] > row_of[e['from']]
            pts = [(x, bf[3] if down else bf[1]), (x, bt[1] if down else bt[3])]
        samples = _resample(pts, 3.0)
        d = _rounded_poly_d(pts, 8)
        heads = [(pts[-1], pts[-2])] + ([(pts[0], pts[1])] if e['both'] else [])
        edges.append({'samples': samples, 'd': d, 'heads': heads, 'index': idx, 'style': e['style'], 'color': e['color'], 'at': e['at'],
                      'from': e['from'], 'to': e['to'], 'lines': [], 'lbox': None, 'pts': pts})
    eby = {e['index']: e for e in edges}
    chips = []
    for g, its in items.items():
        yy = gap_top[g]
        adj_here = [x_line[i] for i in adj_in_gap.get(g, [])]
        left_lim = (max(adj_here) + 6.0) if adj_here else node_l
        lanes_here = sorted(lane_x[i] for i in lane if span[i][0] <= g < span[i][1])
        for idx, kind, obj in its:
            h_it = item_h((idx, kind, obj))
            if idx in lane:
                inner = [x for x in lanes_here if x < lane_x[idx]]
                right = (min(inner) if inner else lane_x[idx]) - 6.0
                maxw = right - left_lim
            else:
                left = left_lim
                right_lim = (min(lanes_here) - 6.0) if lanes_here else W - 20.0
                maxw = right_lim - left
            if kind == 'label':
                fs = F['lbl']
                lines = _label_lines(obj, maxw - 12.0, fs, cut)
                bw, _ = _label_size(lines, fs)
            else:
                fs = F['chip']
                txt = _fit(obj['text'], maxw - 20.0, fs, True, cut)
                bw, _ = _chip_size(txt, fs)
            x0 = (right - bw) if idx in lane else left
            box = (x0, yy, x0 + bw, yy + h_it)
            if kind == 'label':
                eby[idx]['lines'], eby[idx]['lbox'] = lines, box
            else:
                down = row_of[eby[idx]['to']] > row_of[eby[idx]['from']]
                dy = 1.0 if down != obj['back'] else -1.0
                chips.append({'msg': obj['index'], 'edge': idx, 'box': box, 'text': txt, 'color': obj['color'], 'at': obj['at'], 'dir': (0.0, dy)})
            yy += h_it + sp
    chips.sort(key=lambda c: c['msg'])
    return {'W': W, 'H': H, 'F': F, 'groups': groups, 'nodes': nodes, 'edges': edges, 'chips': chips, 'cut': cut[0], 'badge': 13.0}


def _stages(scene: dict) -> tuple[list[float], dict]:
    """Quantise the items' `at` into <= MAX_STAGES stages (nearest bucket), then enforce cause before effect:
    an edge never appears before its two nodes, a chip never before its edge. Returns (stage start times, stage per item key)."""
    items = [('g', g['i'], g['at']) for g in scene['groups']] + [('n', n['id'], n['at']) for n in scene['nodes']] + \
            [('e', e['index'], e['at']) for e in scene['edges']] + [('m', c['msg'], c['at']) for c in scene['chips']]
    ats = sorted({round(a, 3) for _, _, a in items})
    if len(ats) <= MAX_STAGES:
        buckets = ats
    else:
        buckets = [ats[int(round(i * (len(ats) - 1) / (MAX_STAGES - 1)))] for i in range(MAX_STAGES)]
    near = lambda a: min(range(len(buckets)), key=lambda i: (abs(buckets[i] - a), i))
    st = {(k, i): near(a) for k, i, a in items}
    for e in scene['edges']:
        st[('e', e['index'])] = max(st[('e', e['index'])], st[('n', e['from'])], st[('n', e['to'])])
    for c in scene['chips']:
        st[('m', c['msg'])] = max(st[('m', c['msg'])], st[('e', c['edge'])])
    lo, hi = buckets[0], buckets[-1]
    spn = max(hi - lo, 1e-6)
    times: list[float] = []
    for i, b in enumerate(buckets):
        if i == 0:
            times.append(0.0)
        else:
            times.append(round(min(3.75, max(times[-1] + 0.45, 0.55 + (b - lo) / spn * 3.15)), 2))
    return times, st


def _emit_svg(scene: dict, spec: dict, motion: bool) -> tuple[str, int, int]:
    W, H, F = scene['W'], scene['H'], scene['F']
    pal = spec['pal']
    paper, fill, ink, mute = pal['background'], pal['fill'], pal['color'], pal['mute']
    acc, acc2 = pal['accent'], pal['accent2']
    tints = {'device': acc, 'app': acc, 'surface': acc, 'server': acc2, 'tool': acc2, 'model': '#f0b45a', 'store': '#81c995', 'user': ink}
    times, st = _stages(scene)
    chunks: list[list[str]] = [[] for _ in times]
    grp_stroke = _mix_hex(paper, mute, 0.48)
    for g in scene['groups']:
        b = g['box']
        s = f'<g id="g{g["i"]}"><path d="{_dashed_rect_d(b[0], b[1], b[2] - b[0], b[3] - b[1], rx=16.0)}" fill="none" stroke="{grp_stroke}" stroke-width="1.5"/>'
        if g['label']:
            s += (f'<text x="{_n(g["hx"])}" y="{_n(g["hy"])}" font-size="{F["hdr"]}" font-weight="700" font-family="sans-serif" '
                  f'text-anchor="start" fill="{mute}">{C.esc(g["label"])}</text>')
        chunks[st[('g', g['i'])]].append(s + '</g>')
    cut = [scene['cut']]
    for nd in scene['nodes']:
        x0, y0, x1, y1 = nd['box']
        nw, nh = x1 - x0, y1 - y0
        cy = (y0 + y1) / 2.0
        tint = tints[nd['kind']]
        br = scene['badge'] or max(9.0, min(13.0, nh * 0.22))
        ix = x0 + br + 11.0
        tx = ix + br + 9.0
        avail = max(28.0, x1 - 10.0 - tx)
        tfs = F['title'] if _tw(nd['label'], F['title'], True) <= avail else max(12, F['title'] - 2)
        lbl = _fit(nd['label'], avail, tfs, True, cut)
        sub = _fit(nd['sub'], avail, F['sub'], False, cut) if nd['sub'] else ''
        ly = (cy - 3.0 - (F['sub'] - 12) * 0.35) if sub else cy + tfs * 0.35
        sy = cy + F['sub'] * 1.12
        s = (f'<g id="n{nd["i"]}"><rect x="{_n(x0)}" y="{_n(y0)}" width="{_n(nw)}" height="{_n(nh)}" rx="14" fill="{fill}" stroke="{tint}" stroke-width="1.6"/>'
             f'<circle cx="{_n(ix)}" cy="{_n(cy)}" r="{_n(br)}" fill="{_mix_hex(fill, tint, 0.22)}"/>'
             + _glyph(nd['kind'], ix, cy, tint, br / 12.0) +
             f'<text x="{_n(tx)}" y="{_n(ly)}" font-size="{tfs}" font-weight="700" font-family="sans-serif" text-anchor="start" fill="{ink}">{C.esc(lbl)}</text>')
        if sub:
            s += f'<text x="{_n(tx)}" y="{_n(sy)}" font-size="{F["sub"]}" font-weight="400" font-family="sans-serif" text-anchor="start" fill="{mute}">{C.esc(sub)}</text>'
        chunks[st[('n', nd['id'])]].append(s + '</g>')
    for e in scene['edges']:
        col = e['color']
        d = _dash_segments_d(e['samples'], dash=7.0, gap=6.0) if e['style'] == 'dashed' else e['d']
        parts = [f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.2"/>'] + [_arrowhead_path(t, p, col) for t, p in e['heads']]
        if e['lines'] and e['lbox']:
            b = e['lbox']
            fs = F['lbl']
            cx, cy = (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0
            parts.append(f'<rect x="{_n(b[0])}" y="{_n(b[1])}" width="{_n(b[2] - b[0])}" height="{_n(b[3] - b[1])}" rx="5" fill="{paper}" fill-opacity="0.92"/>')
            ys = [cy - fs * 0.22, cy + fs * 0.93] if len(e['lines']) == 2 else [cy + fs * 0.35]
            for t, yy in zip(e['lines'], ys):
                parts.append(f'<text x="{_n(cx)}" y="{_n(yy)}" font-size="{fs}" font-weight="600" font-family="sans-serif" text-anchor="middle" fill="{ink}">{C.esc(t)}</text>')
        chunks[st[('e', e['index'])]].append(f'<g id="e{e["index"]}">' + ''.join(parts) + '</g>')
    n_stage_anim = (1 + 2 * (len(times) - 1)) if motion else 0
    chip_budget = max(0, MAX_ANIMATED - n_stage_anim) if motion else 0
    used = 0
    for c in scene['chips']:
        b = c['box']
        fs = F['chip']
        cx, cy = (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0
        si = st[('m', c['msg'])]
        anim = ''
        if motion and used < chip_budget:
            dx, dy = c['dir']
            anim = (f'<animateTransform attributeName="transform" type="translate" from="{_n(-dx * 28.0)} {_n(-dy * 28.0)}" to="0 0" '
                    f'begin="{_sec(times[si])}" dur="0.65s" repeatCount="1" fill="freeze"/>')
            used += 1
        chunks[si].append(
            f'<g id="m{c["msg"]}e{c["edge"]}">' + (
                f'<path d="M{_n(c["leader"][0][0])} {_n(c["leader"][0][1])} L{_n(c["leader"][1][0])} {_n(c["leader"][1][1])}" '
                f'fill="none" stroke="{c["color"]}" stroke-width="1.5"/>' if c.get('leader') else '') +
            f'<rect x="{_n(b[0])}" y="{_n(b[1])}" width="{_n(b[2] - b[0])}" height="{_n(b[3] - b[1])}" '
            f'rx="{_n((b[3] - b[1]) / 2.0)}" fill="{c["color"]}" stroke="{paper}" stroke-width="1.2"/>'
            f'<text x="{_n(cx)}" y="{_n(cy + fs * 0.35)}" font-size="{fs}" font-weight="700" font-family="sans-serif" text-anchor="middle" '
            f'fill="{C.text_on(c["color"])}">{C.esc(c["text"])}</text>{anim}</g>')
    body = [f'<rect x="0" y="0" width="{int(W)}" height="{int(H)}" rx="18" fill="{paper}"/>']
    total = used
    for i, ch in enumerate(chunks):
        if not ch:
            continue
        a = ''
        if motion:
            t0 = times[i]
            if i == 0 or t0 <= 0:
                a = f'<animate attributeName="opacity" from="0" to="1" begin="0s" dur="0.45s" repeatCount="1" fill="freeze"/>'
                total += 1
            else:
                a = (f'<animate attributeName="opacity" from="0" to="0" begin="0s" dur="{_sec(t0)}" repeatCount="1" fill="freeze"/>'
                     f'<animate attributeName="opacity" from="0" to="1" begin="{_sec(t0)}" dur="0.45s" repeatCount="1" fill="freeze"/>')
                total += 2
        body.append('<g>' + ''.join(ch) + a + '</g>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(W)}" height="{int(H)}" viewBox="0 0 {int(W)} {int(H)}" role="img" '
           f'aria-label="{C.esc(spec["label"])}">' + ''.join(body) + '</svg>')
    verify_rich(svg)
    scene['cut'] = cut[0]
    return svg, len(re.findall(r'<[a-zA-Z]', svg)), total


def _build_steps(spec: dict) -> list[str]:
    """Generate deterministic plain-English step sentences from edges and messages."""
    node_name = {n['id']: n['label'] for n in spec['nodes']}
    events: list[tuple[float, int, str]] = []
    edges_with_msgs = {m['edge'] for m in spec['messages']}

    for e in spec['edge_slots']:
        if e is None or e['index'] in edges_with_msgs:
            continue
        src = node_name[e['from']]
        dst = node_name[e['to']]
        lbl = f"{e['label']} ({e['label2']})" if e['label2'] else e['label']
        sentence = f'{src} connects to {dst} for {lbl}.' if lbl else f'{src} calls {dst}.'
        events.append((e['at'], e['index'], sentence))

    for m in spec['messages']:
        e = spec['edge_slots'][m['edge']]
        if e is None:
            continue
        src = node_name[e['to'] if m['back'] else e['from']]
        dst = node_name[e['from'] if m['back'] else e['to']]
        verb = 'returns' if m['back'] else 'sends'
        via = f" ({e['label']})" if e['label'] else ''
        sentence = f"{src} {verb} {m['text']} to {dst}{via}."
        events.append((m['at'], 100 + m['index'], sentence))

    events.sort(key=lambda item: (item[0], item[1]))
    return [f'{idx + 1}. {text}' for idx, (_, _, text) in enumerate(events)]


def _make_result(title: str, svg_str: str, elem_count: int, anim_count: int, steps: list[str], spec: dict, notes: list[str]) -> C.Result:
    n_cnt = len(spec['nodes'])
    e_cnt = sum(1 for e in spec['edge_slots'] if e is not None)
    m_cnt = len(spec['messages'])
    summary = f'{n_cnt} nodes, {e_cnt} connections and {m_cnt} message payloads ({len(steps)} steps).'
    table = '; '.join(steps) if steps else summary
    clean_title = C.plain(title)
    clean_notes = [C.plain(x) for x in notes]
    body = summary + (' Notes: ' + ' '.join(clean_notes) if clean_notes else '')
    alt = f'Arch motion: {clean_title}. {body}' if clean_title else f'Arch motion. {body}'
    res = C.Result(
        kind='arch_motion',
        title=clean_title,
        svg=svg_str,
        policy='rich',
        summary=summary,
        table=table,
        steps=steps,
        notes=clean_notes,
        elements=elem_count,
        animated=anim_count,
        bytes=len(svg_str.encode('utf-8')),
        alt=alt,
    )
    return res


def arch_motion(
    nodes=None,
    edges=None,
    messages=None,
    groups=None,
    w=1000,
    h=560,
    size=17,
    radius=10,
    accent=None,
    accent2=None,
    color=None,
    mute=None,
    fill=None,
    background=None,
    label='Architecture diagram',
    motion=True,
    variants=None,
    **extra,
) -> dict:
    """d3pack macro returning {'wide': Result, 'narrow': Result, '_default': ...}.

    variants: optional tuple/list of 'wide' / 'narrow'. Only those are drawn (a caller that shows one variant skips the other draw); the
    result then holds just those keys, and '_default' names the first of them when the usual default was not drawn. None draws both, as before.
    """
    extra_keys = sorted(str(k) for k in extra)
    spec_wide, notes = _parse_spec(
        nodes, edges, messages, groups, w, h, size, radius,
        accent, accent2, color, mute, fill, background, label, extra_keys,
    )
    use_motion = motion is not False
    steps = _build_steps(spec_wide)
    out = {}
    want = ('wide', 'narrow') if variants is None else tuple(v for v in ('wide', 'narrow') if v in variants)
    for key, build in (('wide', _wide_scene), ('narrow', _narrow_scene)):
        if key not in want:
            continue
        scene = build(spec_wide)
        svg_s, n_el, n_an = _emit_svg(scene, spec_wide, use_motion)
        v_notes = list(notes)
        if scene['cut']:
            v_notes.append(f'{scene["cut"]} text item(s) in the {key} layout were shortened with an ellipsis to fit their box; the full text is in the steps list.')
        title = spec_wide['label'] if key == 'wide' else f"{spec_wide['label']} (narrow)"
        out[key] = _make_result(title, svg_s, n_el, n_an, steps, spec_wide, v_notes)
    default_key = 'narrow' if spec_wide['h'] > spec_wide['w'] else 'wide'
    if variants is None:
        return {'wide': out['wide'], 'narrow': out['narrow'], '_default': default_key}
    if default_key not in out and out:
        default_key = next(iter(out))
    return {**out, '_default': default_key}


def arch_motion_card(title: str = '', params: dict | None = None, surface_id: str = 'arch', motion: bool = True):
    """Build Basic Catalog 1.0 Card > Column > [title, Image, Wide/Narrow buttons, Steps, step_1..N, status]."""
    p = dict(params or {})
    p['motion'] = motion
    variants = arch_motion(**p)
    default_key = variants.pop('_default')
    names = list(variants)
    for k in names:
        variants[k]['status'] = f'Showing {k} layout.'

    steps: list[str] = variants[default_key]['steps']
    head_text = C.plain(title or variants[default_key]['title'] or 'Architecture diagram')[:80]

    step_ids = [f'step_{i + 1}' for i in range(len(steps))]
    kids = ['title', 'img'] + (['row'] if len(names) > 1 else []) + (['steps_hd'] + step_ids if steps else []) + ['status']

    comps: list[dict] = [
        {'id': 'root', 'component': 'Card', 'child': 'col'},
        {'id': 'col', 'component': 'Column', 'children': kids},
        {'id': 'title', 'component': 'Text', 'text': f'**{C.md_safe(head_text)}**'},
        {'id': 'img', 'component': 'Image', 'url': {'@path': '/img'}, 'description': {'@path': '/alt'}, 'variant': 'mediumFeature', 'fit': 'contain'},
    ]
    if len(names) > 1:
        comps.append({'id': 'row', 'component': 'Row', 'justify': 'center', 'children': [f'b_{k}' for k in names]})
        for k in names:
            comps.append({
                'id': f'b_{k}', 'component': 'Button', 'child': f't_{k}',
                'action': {'event': {'name': 'set_variant', 'context': {'variant': k}}},
            })
            comps.append({'id': f't_{k}', 'component': 'Text', 'text': k.capitalize()})
    if steps:
        comps.append({'id': 'steps_hd', 'component': 'Text', 'text': '**Steps**'})
        for i, line in enumerate(steps):
            comps.append({'id': f'step_{i + 1}', 'component': 'Text', 'text': C.md_safe(line)})
    comps.append({'id': 'status', 'component': 'Text', 'text': {'@path': '/status'}, 'accessibility': {'live': 'polite'}})

    dm_for = lambda r: {'img': C.data_uri(r['svg'], 'rich'), 'alt': r['alt'][:1500], 'status': r['status']}
    create = {
        'version': '1.0',
        'createSurface': {
            'surfaceId': surface_id,
            'catalogId': C.BASIC,
            'components': comps,
            'dataModel': dm_for(variants[default_key]),
        },
    }
    updates = {
        k: {'version': '1.0', 'updateDataModel': {'surfaceId': surface_id, 'path': '/', 'value': dm_for(variants[k])}}
        for k in names
    }
    return create, updates, variants


# ---------------------------------------------------------------------------
# Demo Inputs & d3pack Registry Entries
# ---------------------------------------------------------------------------

TRIP_PLANNER_DEMO = {
    'label': 'How the A2UI trip planner works (Basic Catalog, zero tokens)',
    'w': 1000,
    'h': 560,
    'size': 17,
    'groups': [
        {'label': 'Your browser', 'x': 1.5, 'y': 4, 'w': 28, 'h': 92, 'at': 0.0},
        {'label': 'Cloudflare', 'x': 33, 'y': 4, 'w': 32, 'h': 92, 'at': 0.14},
    ],
    'nodes': [
        {'id': 'page', 'kind': 'app', 'label': 'Hosted page', 'sub': 'Form · static HTML', 'x': 15.5, 'y': 26, 'w': 23, 'h': 14, 'at': 0.04},
        {'id': 'renderer', 'kind': 'surface', 'label': 'A2UI renderer', 'sub': '@a2ui/react · Basic', 'x': 15.5, 'y': 76, 'w': 23, 'h': 14, 'at': 0.56},
        {'id': 'worker', 'kind': 'server', 'label': 'Python Worker', 'sub': 'Rules · 0 tokens', 'x': 49, 'y': 34, 'w': 26, 'h': 14, 'at': 0.16},
        {'id': 'air', 'kind': 'store', 'label': 'Frozen airline store', 'sub': '60 airports · 14 Nov 2026', 'x': 49, 'y': 78, 'w': 26, 'h': 14, 'at': 0.68},
        {'id': 'meteo', 'kind': 'tool', 'label': 'Open-Meteo', 'sub': 'Forecast API', 'x': 85, 'y': 26, 'w': 22, 'h': 14, 'at': 0.28},
        {'id': 'wiki', 'kind': 'store', 'label': 'Wikipedia', 'sub': 'Summary · CC BY-SA', 'x': 85, 'y': 70, 'w': 22, 'h': 14, 'at': 0.28},
    ],
    'edges': [
        {
            'from': 'page', 'to': 'worker', 'label': 'trip request', 'at': 0.18,
            'points': [{'x': 15.5, 'y': 19}, {'x': 15.5, 'y': 15}, {'x': 49, 'y': 15}, {'x': 49, 'y': 27}],
            'label_at': {'x': 31, 'y': 11},
        },
        {
            'from': 'worker', 'to': 'meteo', 'label': 'parallel weather', 'style': 'dashed', 'both': True, 'at': 0.30,
            'points': [{'x': 62, 'y': 30}, {'x': 73, 'y': 30}, {'x': 73, 'y': 15}, {'x': 85, 'y': 15}, {'x': 85, 'y': 19}],
            'label_at': {'x': 79, 'y': 11},
        },
        {
            'from': 'worker', 'to': 'wiki', 'label': 'parallel summary', 'style': 'dashed', 'both': True, 'at': 0.30,
            'points': [{'x': 62, 'y': 38}, {'x': 73, 'y': 38}, {'x': 73, 'y': 50}, {'x': 85, 'y': 50}, {'x': 85, 'y': 63}],
            'label_at': {'x': 85, 'y': 45},
        },
        {
            'from': 'worker', 'to': 'renderer', 'label': 'A2UI messages', 'at': 0.58,
            'points': [{'x': 36, 'y': 38}, {'x': 31, 'y': 38}, {'x': 31, 'y': 52}, {'x': 15.5, 'y': 52}, {'x': 15.5, 'y': 69}],
            'label_at': {'x': 23, 'y': 47},
        },
        {'from': 'worker', 'to': 'air', 'label': 'route lookup', 'style': 'dashed', 'at': 0.72},
    ],
    'messages': [
        {'edge': 0, 'text': 'GET /trip', 'at': 0.20, 'dur': 0.09},
        {'edge': 1, 'text': 'forecast JSON', 'back': True, 'at': 0.40, 'dur': 0.08, 'color': '#2ac4ce'},
        {'edge': 2, 'text': 'extract · CC BY-SA', 'back': True, 'at': 0.42, 'dur': 0.08, 'color': '#81c995'},
        {'edge': 3, 'text': 'createSurface', 'at': 0.62, 'dur': 0.10, 'color': '#2ac4ce'},
        {'edge': 4, 'text': 'origin, dest', 'at': 0.74, 'dur': 0.08},
        {'edge': 3, 'text': 'Getting there', 'at': 0.86, 'dur': 0.10, 'color': '#2ac4ce'},
    ],
}

TRIP_CONTAINER_DEMO = {
    'label': 'How the A2UI trip planner works: a Cloudflare Python Worker, no model',
    'w': 1000,
    'h': 560,
    'size': 17,
    'groups': [
        {'label': 'Your browser', 'x': 1.5, 'y': 4, 'w': 26.5, 'h': 92, 'at': 0.0},
        {'label': 'Cloudflare Python Worker', 'x': 31, 'y': 4, 'w': 39, 'h': 92, 'at': 0.12},
        {'label': 'Public data', 'x': 73, 'y': 4, 'w': 25.5, 'h': 92, 'at': 0.12},
    ],
    'nodes': [
        {'id': 'page', 'kind': 'app', 'label': 'Hosted page', 'sub': 'Form · static HTML', 'x': 14.8, 'y': 28, 'w': 22.5, 'h': 13, 'at': 0.04},
        {'id': 'renderer', 'kind': 'surface', 'label': 'A2UI renderer', 'sub': '@a2ui/react · Basic', 'x': 14.8, 'y': 78, 'w': 22.5, 'h': 13, 'at': 0.60},
        {'id': 'entry', 'kind': 'server', 'label': 'Worker entrypoint', 'sub': 'Python · 0 tokens', 'x': 51.5, 'y': 17, 'w': 33, 'h': 11, 'at': 0.16},
        {'id': 'sdk', 'kind': 'tool', 'label': 'A2UI Python SDK', 'sub': 'Basic catalog · Express', 'x': 51.5, 'y': 34, 'w': 33, 'h': 11, 'at': 0.34},
        {'id': 'macro', 'kind': 'tool', 'label': 'Macro pack: Python', 'sub': 'WeatherCard · latency ledger', 'x': 51.5, 'y': 51, 'w': 33, 'h': 11, 'at': 0.34},
        {'id': 'rules', 'kind': 'server', 'label': 'Our rules: Python', 'sub': 'packing · distance · credits', 'x': 51.5, 'y': 68, 'w': 33, 'h': 11, 'at': 0.50},
        {'id': 'air', 'kind': 'store', 'label': 'Frozen airline data', 'sub': '60 airports · 14 Nov 2026', 'x': 51.5, 'y': 87, 'w': 33, 'h': 10.5, 'at': 0.66},
        {'id': 'meteo', 'kind': 'tool', 'label': 'Open-Meteo', 'sub': 'Forecast API', 'x': 85.8, 'y': 34, 'w': 21.5, 'h': 13, 'at': 0.26},
        {'id': 'wiki', 'kind': 'store', 'label': 'Wikipedia', 'sub': 'Summary · CC BY-SA', 'x': 85.8, 'y': 74, 'w': 21.5, 'h': 13, 'at': 0.26},
    ],
    'edges': [
        {
            'from': 'page', 'to': 'entry', 'label': 'trip request', 'at': 0.18,
            'points': [{'x': 14.8, 'y': 21.5}, {'x': 14.8, 'y': 15.5}, {'x': 35.0, 'y': 15.5}],
            'label_at': {'x': 24.5, 'y': 11.5},
        },
        {
            'from': 'entry', 'to': 'meteo', 'label': 'parallel weather', 'style': 'dashed', 'both': True, 'at': 0.28,
            'points': [{'x': 68.0, 'y': 15.5}, {'x': 85.8, 'y': 15.5}, {'x': 85.8, 'y': 27.5}],
            'label_at': {'x': 77.5, 'y': 11.5},
        },
        {
            'from': 'entry', 'to': 'wiki', 'label': 'parallel summary', 'style': 'dashed', 'both': True, 'at': 0.28,
            'points': [{'x': 68.0, 'y': 19.0}, {'x': 71.5, 'y': 19.0}, {'x': 71.5, 'y': 54.0}, {'x': 85.8, 'y': 54.0}, {'x': 85.8, 'y': 67.5}],
            'label_at': {'x': 85.8, 'y': 48.0},
        },
        {'from': 'entry', 'to': 'sdk', 'at': 0.36},
        {'from': 'sdk', 'to': 'macro', 'at': 0.40},
        {'from': 'macro', 'to': 'rules', 'at': 0.52},
        {'from': 'rules', 'to': 'air', 'label': 'route lookup', 'style': 'dashed', 'at': 0.68},
        {
            'from': 'entry', 'to': 'renderer', 'label': 'A2UI messages', 'at': 0.62,
            'points': [{'x': 35.0, 'y': 19.0}, {'x': 29.5, 'y': 19.0}, {'x': 29.5, 'y': 53.0}, {'x': 14.8, 'y': 53.0}, {'x': 14.8, 'y': 71.5}],
            'label_at': {'x': 21.5, 'y': 46.5},
        },
    ],
    'messages': [
        {'edge': 0, 'text': 'GET /trip', 'at': 0.19, 'dur': 0.10},
        {'edge': 1, 'text': 'forecast JSON', 'back': True, 'at': 0.40, 'dur': 0.08},
        {'edge': 2, 'text': 'extract · CC BY-SA', 'back': True, 'at': 0.42, 'dur': 0.08},
        {'edge': 7, 'text': 'createSurface', 'at': 0.64, 'dur': 0.10},
        {'edge': 6, 'text': 'origin, dest', 'at': 0.70, 'dur': 0.08},
        {'edge': 7, 'text': 'Getting there', 'at': 0.84, 'dur': 0.10},
    ],
}

PACK_ARCH = {'arch_motion': arch_motion}
PACK = {'arch_motion': arch_motion}
DEMOS = {
    'trip_planner_arch': TRIP_PLANNER_DEMO,
    'trip_container_arch': TRIP_CONTAINER_DEMO,
}
_DEMO_MACRO = {
    'trip_planner_arch': 'arch_motion',
    'trip_container_arch': 'arch_motion',
}

# ---------------------------------------------------------------------------
# DESIGN AND GUARDRAIL NOTE (v3, 14 Nov 2026)
#
# Output passes d3pack/rich.py verify_rich UNCHANGED (the macro calls it on every SVG and raises if it fails).
#
# Dropped from the atom's behaviour, and why:
#  - The film clock. The atom gives each element a window [at, at + dur] driven by a motion_timeline track. verify_rich
#    admits only SMIL opacity/translate/rotate that ends within 5 s and at most 20 animated elements, so the `at` values
#    are quantised into at most 5 stages (nearest bucket), shown by one opacity fade per stage group (stage 0: 1 animate,
#    later stages: 2, a hold at 0 then a 0.45 s fade), with cause before effect enforced (an edge never before its nodes,
#    a chip never before its edge). Per-item `dur` is not used. Stage starts lie in [0, 3.75] s.
#  - Messages do not travel the whole edge. Each chip slides 28 px into its resting place (0.65 s animateTransform
#    translate) in the direction it travels (back=true reverses it). Chips beyond the 20-animation budget appear with
#    their stage, unanimated. Edges do not "draw on": solid and dashed edges both fade in with their stage.
#  - stroke-dasharray is not admitted, so dashed edges and group frames are emitted as many short M/L subpaths.
#  - The atom's CSS/script is not used: pure SVG, no <style>, no filter, no gradient, no external reference.
#  - Node icons are single vector paths per kind (font-independent; the v2 Unicode glyphs depended on the fallback font).
#
# Wide layout: the payload's own percentages (nodes, groups, edge points, curves). Edge labels and message chips are
#  placed by a scored search (_Placer): hard costs for overlapping a node, header, label or chip, for another edge's line
#  running through the box, for leaving the viewBox; softer costs for straddling a group outline and for distance from the
#  author's label_at / the chip's preferred spot. Chips sit ON their own edge line when there is room; a chip that cannot
#  (a short edge between two boxes) is parked in the nearest free spot and joined to its edge by a 1.5 px leader in the
#  chip's colour. Two orders are tried (labels first, chips first) and the cheaper layout wins.
#
# Narrow layout (420 px wide; title 18, sub 15, labels and chips 16, group headers 14 px): one column of nodes, grouped
#  in bands in group order (order inside a band chosen to minimise rows skipped by edges, ties keep the payload order).
#  Edges between neighbouring rows run straight down a line 32 px inside the left of the boxes; edges that skip rows run
#  in their own lane right of the boxes (nested: shortest span innermost; right-rim ports ordered so stubs do not cross
#  at the node). Every label and every chip gets its own row in a gap: neighbour-edge items sit just right of their line,
#  lane-edge items right-aligned against their own lane, in the gap along the lane with no inner lane crossing it.
#  Nothing is placed by search, so the narrow layout cannot collide by construction (and check_layout.py confirms it).
#
# Measured (gen.py, this file, 14 Nov 2026; elements = opening tags, bytes = UTF-8):
#   case       variant  motion  elements  animated  last end  bytes
#   trip       wide     on        109        15      4.35 s   19385   | off: 94 elements, 0 animated, 17611 bytes
#   trip       narrow   on        109        15      4.35 s   19186   | off: 94, 0, 17414
#   container  wide     on        139        15      4.35 s   25143   | off: 124, 0, 23370
#   container  narrow   on        139        15      4.35 s   28907   | off: 124, 0, 27135
#   android    wide     on        131        17      4.35 s   18119   | off: 114, 0, 16049
#   android    narrow   on        127        17      4.35 s   19400   | off: 110, 0, 17346
#  All 12 pass verify_rich and are byte-identical across two runs. check_layout.py: 0 problems in every narrow and in the
#  trip and container wide variants; android wide has 8 group-border straddles (two labels and four chips in the 45 px
#  gutter between its groups) and 4 chips joined by leaders, zero overlaps. See the report for the v2 / r2 baselines.
#
# Not verified: text widths are estimated from Helvetica-metric advances (what Chromium on the test machine used for
#  sans-serif) plus 6 %; a host whose sans-serif is wider (DejaVu Sans, roughly 10-15 % wider) could push text past its
#  box. Only Chromium was used to render (no Safari/Firefox, no Android WebView, no real phone). Inputs other than the
#  three demos were not fuzzed for the narrow layout (e.g. 12 nodes with many skip edges, labels near 48 characters).
# ---------------------------------------------------------------------------
