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
