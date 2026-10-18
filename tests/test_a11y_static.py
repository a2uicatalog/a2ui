"""Fast accessibility guards for defects that a real scan found on the site (2026-10-17).

These are source and generated-HTML checks: no browser, a few seconds. The full axe audit stays a local/CI-scan job; this stops the specific
regressions that cost the most (an empty table header on 15 pages dropped the site score from 94 to 69).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"vendors", "node_modules", ".venv"}


def _html_pages():
    for p in (ROOT / "public").rglob("*.html"):
        if not SKIP_DIRS.intersection(p.parts):
            yield p


def test_no_empty_table_header_cells():
    """axe td-has-header (WCAG 1.3.1) read an empty <th></th> as 'no header'. Label every column."""
    bad = [str(p.relative_to(ROOT)) for p in _html_pages() if re.search(r"<th\b[^>]*>\s*</th>", p.read_text(errors="ignore"))]
    assert not bad, f"empty <th> cells in {len(bad)} page(s), e.g. {bad[:3]}: give the column a label (generate_atom_pages.fields_table)"


def test_renderers_do_not_hide_radios_with_display_none():
    """A display:none radio cannot take focus, so tabs/carousels built on it are unusable by keyboard (WCAG 2.1.1).
    Hide visually instead: position:absolute;opacity:0 plus a :focus-visible ring on the label."""
    files = list((ROOT / "renderers").glob("*.py")) + list((ROOT / "apps-script-surface/gas-wired-renderer").glob("*.gs")) + list((ROOT / "scripts").glob("generate_*.py"))
    bad = []
    for f in files:
        for n, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            if (re.search(r"input(?:\[type=(?:radio|checkbox)\])?\s*\{\{?\s*display:\s*none", line)
                    or re.search(r"<input\b(?=[^<>]*type=[\"'](?:radio|checkbox)[\"'])[^<>]*style=\"display:\s*none", line)):
                bad.append(f"{f.relative_to(ROOT)}:{n}")
    assert not bad, f"radio/checkbox hidden with display:none at {bad[:5]}"


def test_no_bold_only_paragraphs_in_content_markdown():
    """A bold line standing alone as a paragraph is a fake heading (axe p-as-heading, WCAG 1.3.1): use ### so it is a real heading."""
    bad = []
    for f in (ROOT / "content").glob("*.md"):
        lines = f.read_text(errors="ignore").splitlines()
        for i, line in enumerate(lines):
            if re.fullmatch(r"\*\*[^*]{3,120}\*\*", line.strip()) and (i == 0 or not lines[i - 1].strip()):
                bad.append(f"{f.name}:{i + 1}")
    assert not bad, f"bold-only lines used as headings: {bad[:5]}"


def test_overlay_canvases_are_hidden_from_assistive_tech():
    """The full-screen firework/rocket overlays are decorative (pointer-events:none); the wrapper must be aria-hidden."""
    bad = []
    for f in list((ROOT / "renderers").glob("*.py")) + list((ROOT / "apps-script-surface/gas-wired-renderer").glob("*.gs")):
        for m in re.finditer(r"<div id=[^>]*data-a2ui-overlay=", f.read_text(errors="ignore")):
            if 'aria-hidden="true"' not in m.group(0):
                bad.append(f.name)
    assert not bad, f"overlay wrapper without aria-hidden in {sorted(set(bad))}"
