"""Tests for renderers/render_wrap.py's wrap_atom_html -- added 2026-09-04
after a real live bug: this function had NO theme awareness at all
(background hardcoded to #0b0b12 unconditionally), so a caller sending
`theme` anywhere upstream (a2h-printer's signed /render.png?b= payload)
had it silently dropped long before reaching here -- the actual root
cause of a Chat-posted icon staying on a black background even after the
CALLER-side fix (a2h-printer's render-to-chat.js sending theme:'light')
had already shipped. No Flask/Playwright dependency needed -- this is a
pure string-building function, deliberately tested in isolation from the
heavier cloud-run-renderer test file's dependency guards."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "renderers"))

from render_wrap import wrap_atom_html  # noqa: E402


def test_default_theme_is_light():
    html = wrap_atom_html("<div>x</div>", 620)
    assert "background:#ffffff" in html
    assert "background:#0b0b12" not in html


def test_theme_light_is_explicit_too():
    html = wrap_atom_html("<div>x</div>", 620, theme="light")
    assert "background:#ffffff" in html


def test_theme_dark_still_available():
    html = wrap_atom_html("<div>x</div>", 620, theme="dark")
    assert "background:#0b0b12" in html


def test_title_subtitle_colors_are_readable_on_light_background():
    # The bug this guards against: title/subtitle colors were hardcoded
    # for a dark background (#e5e7eb / #94a3b8, both near-white) -- fixing
    # only the body background would have made a titled render's text
    # nearly invisible on the new white ground.
    html = wrap_atom_html("<div>x</div>", 620, title="T", subtitle="S", theme="light")
    assert "#e5e7eb" not in html
    assert "#94a3b8" not in html


def test_title_subtitle_colors_unchanged_for_dark_theme():
    html = wrap_atom_html("<div>x</div>", 620, title="T", subtitle="S", theme="dark")
    assert "color:#e5e7eb" in html
    assert "color:#94a3b8" in html
