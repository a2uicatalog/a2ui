"""Our custom properties must not collide with the OFFICIAL A2UI default theme's.

The official theme (@a2ui/web_core styles/default.js, used by the lit/react/angular renderers)
defines --a2ui-border as a border SHORTHAND ("1px solid var(--a2ui-color-border,#ccc)"). We used
the same name as a COLOUR (`border:1px solid var(--a2ui-border,#eaeaea)`): inside the official theme
the declaration became invalid at computed-value time and our card borders vanished. Our colour
token is now --asw-border. The official name list is atoms/official_a2ui_tokens.json, written by
scripts/gen_official_a2ui_tokens.py from the installed packages (refresh it after upgrading them).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL = set(json.loads((ROOT / "atoms" / "official_a2ui_tokens.json").read_text())["tokens"])
SOURCES = (sorted((ROOT / "apps-script-surface" / "gas-wired-renderer").glob("*.gs"))
           + sorted((ROOT / "apps-script-surface" / "gas-wired-renderer").glob("*.html"))
           + [ROOT / "renderers" / "web_article.py", ROOT / "renderers" / "_design_tokens.py"])
NAME = re.compile(r"--a2ui-[a-z0-9]+(?:-[a-z0-9]+)*")


def _names():
    found = {}
    for p in SOURCES:
        for m in NAME.finditer(p.read_text()):
            found.setdefault(m.group(0), p.name)
    return found


def test_official_list_is_plausible():
    assert "--a2ui-border" in OFFICIAL and "--a2ui-color-border" in OFFICIAL
    assert len(OFFICIAL) >= 30


def test_no_name_we_use_is_an_official_token():
    clash = {n: f for n, f in _names().items() if n in OFFICIAL}
    assert not clash, f"clashes with the official A2UI theme tokens: {clash}"


def test_nothing_reads_the_official_border_shorthand_as_a_colour():
    bad = [p.name for p in SOURCES if re.search(r"var\(\s*--a2ui-border\s*[,)]", p.read_text())]
    assert not bad, f"var(--a2ui-border...) reads the official shorthand: {bad}"


def test_palette_tokens_emit_private_border_name():
    from renderers._design_tokens import token_css
    css = token_css({"preset": "modern"})
    assert "--asw-border:#eaeaea;" in css and "--a2ui-border:" not in css
    assert "--a2ui-radius:12px;" in css
