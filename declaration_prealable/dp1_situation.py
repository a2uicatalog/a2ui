"""Generates the DP1 piece ("plan de situation") -- see declaration_prealable/README.md: the official
guidance itself says to source this from a public mapping site, not to custom-render it; this module
does exactly that programmatically (a real IGN orthophoto + cadastral parcel overlay, not a hand-drawn
substitute), closing the gap that was previously left as a pure manual step.
"""
from pathlib import Path

from declaration_prealable import parcel_lookup


def render_dp1_png(lon, lat, address, out_path, radius_m=120):
    """Thin wrapper around parcel_lookup.fetch_dp1_screenshot_bytes -- kept as its own module so
    intake.py/server.py import "the DP1 piece" the same way they import dp2_plan_masse/dp5_elevation,
    not a one-off inline call."""
    png_bytes = parcel_lookup.fetch_dp1_screenshot_bytes(lon, lat, address, radius_m=radius_m)
    Path(out_path).write_bytes(png_bytes)
    return out_path


def render_dp1_png_bytes(lon, lat, address, radius_m=120) -> bytes:
    """Bytes-only form for a synchronous web caller -- see dp5_elevation.render_dp5_png_bytes's own
    docstring for why this split exists."""
    return parcel_lookup.fetch_dp1_screenshot_bytes(lon, lat, address, radius_m=radius_m)
