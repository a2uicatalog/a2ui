"""Reusable data model for a French déclaration préalable (DP) project.

See declaration_prealable/README.md for the sourced legal grounding behind
why a standalone clôture needs DP1+DP2+DP5 (not DP4), the CERFA 16702*03 form
number, and the 2 m / secteur protégé DP trigger. This module carries no
legal logic itself -- it is the plain data shape that dp5_elevation.py and
dp2_plan_masse.py render from, so a future DP project (not just the wall this
was built for) only needs to fill in a new instance of these dataclasses.
"""
from dataclasses import dataclass, field


@dataclass
class WallSpec:
    """One masonry wall/clôture run. Block dimensions are real standard
    French construction sizes (500x200x200mm / 500x200x150mm parpaing,
    220x105x55mm brique), not placeholders."""
    project_type: str = "cloture"  # "cloture" | "soutenement"
    block_id: str = "parpaing200"  # key into dp5_elevation.BLOCKS
    bond: str = "running"  # "running" | "stack"
    length_m: float = 3.0
    height_m: float = 2.0
    thickness_mm: int = 200
    # Exact DP5-style callout text, e.g. "Enduit lisse peint en blanc" --
    # the official example image uses this precise red-leader-line wording
    # convention, so this field is free text matching that register, not a
    # coded enum.
    finish_label: str = "Enduit lisse peint en blanc"
    finish_colour_hex: str = "#f2f1ec"


@dataclass
class PlotGeometry:
    """Local site coordinates in metres, origin arbitrary (e.g. a plot
    corner) -- dp2_plan_masse.py projects these to page pixels itself."""
    boundary_points_m: list = field(default_factory=list)  # [(x, y), ...] polygon
    existing_structures: list = field(default_factory=list)  # [{"label": str, "points_m": [(x,y),...]}]
    wall_points_m: list = field(default_factory=list)  # [(x, y), (x, y)] wall placement as a line segment
    north_angle_deg: float = 0.0  # degrees clockwise from "up" on the page to true north


@dataclass
class DPProject:
    commune: str
    address: str
    wall: WallSpec
    plot: PlotGeometry
    date_iso: str
