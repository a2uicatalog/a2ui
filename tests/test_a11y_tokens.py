"""Accessibility: the colours the catalogue falls back to when an agent supplies none must pass WCAG AA.

Found 2026-10-08 by an axe-core sweep of every atom's example (a2ui-private/a11y): the default accent
#6366f1 is 4.46:1 against white, a hair under the 4.5:1 AA threshold for text. White text on it failed in 26
atoms and indigo text on white in 16 more, so one default was the largest single cause of contrast failures.
This test holds the fix: it needs no browser, so it runs in CI where the axe ratchet (private tier) does not.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
# atoms_schema_snapshot.gs is generated from schema.yaml's prose (it quotes the old colour in descriptions), so it is not a renderer
RENDERERS = [ROOT / "renderers" / "web_article.py",
             *[p for p in sorted((ROOT / "apps-script-surface" / "gas-wired-renderer").glob("atom*.gs")) if "schema_snapshot" not in p.name]]


def _lum(hex_):
    h = hex_.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_the_contrast_helper_matches_the_known_figure():
    assert round(contrast("#6366f1", "#ffffff"), 2) == 4.47       # the figure axe reported (4.46), by a hair
    assert contrast("#000000", "#ffffff") == 21


def test_the_default_accent_passes_aa_in_both_directions():
    py = (ROOT / "renderers" / "web_article.py").read_text()
    body = py[py.index("def _render_palette"):]
    m = re.search(r'accent\s*=\s*b\.get\("accent",\s*"(#[0-9a-fA-F]{6})"\)', body)
    py_default = m.group(1)
    gas = (ROOT / "apps-script-surface" / "gas-wired-renderer" / "atom.gs").read_text()
    g = re.search(r"_RENDERERS\['palette'\] = function\(b\) \{\s*var accent\s*=\s*b\.accent\s*\|\|\s*'(#[0-9a-fA-F]{6})'", gas)
    assert g, "palette default accent not found in atom.gs"
    assert py_default.lower() == g.group(1).lower(), "GAS and Python disagree on the default accent"
    assert contrast(py_default, "#ffffff") >= 4.5, f"{py_default} is {contrast(py_default, '#ffffff'):.2f}:1 on white"


def test_the_old_failing_default_is_gone_from_the_renderers():
    left = {p.name: len(re.findall(r"#6366f1", p.read_text(), re.I)) for p in RENDERERS}
    assert not {k: v for k, v in left.items() if v}, left
