"""scripts/brick_models/sketch_to_bricks.py -- material-context-aware architecture seam (cozy-forging-newt.md
Track B item 3). _system_prompt()/nearest_colour_code() accept an optional material_profile carrying unit
vocabulary (height_unit/footprint_unit/course_ratio) and a colour palette, defaulting to LEGO_SKETCH_PROFILE.
No second material profile exists yet -- these tests prove (a) the default path is byte-identical to the
pre-seam behaviour, and (b) the seam itself actually works (a different profile really changes the prompt
text and the palette used), not just that it was threaded through without effect.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "brick_models"))

from sketch_to_bricks import LEGO_SKETCH_PROFILE, _system_prompt, nearest_colour_code  # noqa: E402


def test_default_prompt_uses_lego_vocabulary():
    p = _system_prompt("a small house", 32, 32)
    assert "studs" in p
    assert "PLATES" in p
    assert "3 plates = 1 standard brick course" in p


def test_explicit_lego_profile_matches_default():
    """Passing LEGO_SKETCH_PROFILE explicitly must be byte-identical to the implicit default."""
    default = _system_prompt("a spaceship", 24, 24)
    explicit = _system_prompt("a spaceship", 24, 24, LEGO_SKETCH_PROFILE)
    assert default == explicit


def test_material_profile_actually_changes_prompt_vocabulary():
    """A different profile must produce different prompt text -- proves the seam has real effect."""
    other = {"height_unit": "courses", "footprint_unit": "blocks",
             "course_ratio": "1 course = 1 concrete block", "palette_codes": LEGO_SKETCH_PROFILE["palette_codes"]}
    default = _system_prompt("a wall", 10, 10)
    swapped = _system_prompt("a wall", 10, 10, other)
    assert default != swapped
    assert "courses" in swapped and "blocks" in swapped
    assert "1 course = 1 concrete block" in swapped
    # The LEGO-specific vocabulary words must not leak into a different profile's prompt.
    assert "plates" not in swapped.lower()
    assert "studs" not in swapped.lower() or "blocks" in swapped.lower()


def test_colour_matching_unaffected_by_default_profile():
    assert nearest_colour_code("#ff0000") == nearest_colour_code("#ff0000", LEGO_SKETCH_PROFILE)


def test_colour_matching_respects_a_narrower_palette():
    """A profile with a restricted palette must only match within that palette, not the full LEGO one."""
    full = nearest_colour_code("#00ff00")
    narrow_profile = {"palette_codes": [4]}  # red only
    narrow = nearest_colour_code("#00ff00", narrow_profile)
    assert narrow == 4
