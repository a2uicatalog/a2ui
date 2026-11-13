"""Homepage film (2026-10-01): the four films in landing/ use only stable atoms, render without dropped items, and the homepage carries
them once, with the controls and labels a visitor and a screen reader need."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
FILMS = sorted((ROOT / "landing").glob("film-*.json"))


def _types(v, acc):
    if isinstance(v, dict):
        if isinstance(v.get("type"), str):
            acc.add(v["type"])
        for x in v.values():
            _types(x, acc)
    elif isinstance(v, list):
        for x in v:
            _types(x, acc)
    return acc


def test_four_films_exist():
    assert [f.name for f in FILMS] == ["film-tall-dark.json", "film-tall-light.json", "film-wide-dark.json", "film-wide-light.json"]


def test_films_use_only_stable_atoms():
    spec = {a["type"]: a for a in yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]}
    for f in FILMS:
        for t in _types(json.loads(f.read_text()), set()):
            assert t in spec, (f.name, t)
            assert spec[t].get("stage") != "preview", (f.name, t)


def test_homepage_carries_the_film_once():
    html = (ROOT / "public" / "index.html").read_text()
    assert html.count('class="film-hero"') == 1 and html.count('id="film-hero-js"') == 1
    assert "ignored" not in html[html.index('class="film-hero"'):html.index('<main class="wrap">')]
    for a in ("wide", "tall"):
        for t in ("light", "dark"):
            assert f'class="mf mf-{a} mf-{t}"' in html
    assert 'aria-label="A2UI Catalog introduction"' in html
    assert 'data-film="replay"' in html and 'data-film="skip"' in html
    assert "prefers-reduced-motion" in html


def test_homepage_size_budget():
    assert len((ROOT / "public" / "index.html").read_bytes()) < 2_600_000


def test_film_scripts_are_inert_until_their_variant_is_on_screen_and_posters_exist():
    """Speed (2026-10-29): the four variants ship their scripts as type=text/plain; film-hero-js starts only the visible one. Each variant has a poster."""
    import importlib.util
    import sys
    sys.path.insert(0, str(ROOT / "renderers"))
    spec = importlib.util.spec_from_file_location("gap", ROOT / "scripts" / "generate_atom_pages.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    html = mod.render_landing_film()
    assert "<script>" not in html and html.count('<script type="text/plain" data-film-js>') >= 4
    assert "script[data-film-js]" in mod.LANDING_FILM_JS and "film-live" in mod.LANDING_FILM_JS
    for aspect in ("wide", "tall"):
        for theme in ("light", "dark"):
            assert f"/brand/film-poster-{aspect}-{theme}.webp" in mod.LANDING_FILM_CSS
            assert (ROOT / "public" / "brand" / f"film-poster-{aspect}-{theme}.webp").stat().st_size > 2000


def test_grid_thumbnails_are_lazy_described_and_the_card_text_stays_in_the_page():
    """Speed (2026-10-29): card thumbnails move to /atoms/stages.json. Design pass (2026-11-01): the slot is role=img with a text alternative (it was aria-hidden); the
    lazy fill inside stays aria-hidden/inert; an atom with no thumbnail gets the schema card, not a blank box."""
    import importlib.util
    import sys
    sys.path.insert(0, str(ROOT / "renderers"))
    spec = importlib.util.spec_from_file_location("gap", ROOT / "scripts" / "generate_atom_pages.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._STAGES.clear()
    html = mod.card_stage({"type": "quote"})
    if "data-stage" not in html:   # the atom has no card preview; the schema card stays inline
        assert "schema-card" in html and 'role="img"' in html and "open for live preview" in html
        return
    assert 'role="img"' in html and 'aria-label="Preview of Quote' in html and 'data-stage="quote"' in html and "stage-inner" not in html and "aria-hidden" not in html
    assert 'aria-hidden="true" inert' in mod._STAGES["quote"] and "<script" not in mod._STAGES["quote"].lower()
    assert "/atoms/stages.json" in mod.INDEX_JS


def test_design_pass_header_menu_atoms_current_and_treemap_example():
    """Design pass (2026-11-01): the nav folds behind a Menu button (aria-expanded/aria-controls), 'Atoms' is current only on /atoms/ pages, and the treemap example payload is the
    hand-written one (4+ items), not the heuristic's {"items": 1}."""
    import importlib.util, json, sys
    sys.path.insert(0, str(ROOT / "renderers"))
    spec = importlib.util.spec_from_file_location("gap2", ROOT / "scripts" / "generate_atom_pages.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    h = mod.site_header("atoms")
    assert 'class="menu-btn"' in h and 'aria-expanded="false"' in h and 'aria-controls="site-menu"' in h and 'id="site-menu"' in h
    assert '<a href="/atoms/" aria-current="page">Atoms</a>' in h and mod.site_header("").count("aria-current") == 0
    ex = json.loads(mod.example_payload({"type": "treemap", "fields": {"items": "list of items (4-12 objects)"}}))
    assert ex["type"] == "treemap" and isinstance(ex["items"], list) and 4 <= len(ex["items"]) <= 12
