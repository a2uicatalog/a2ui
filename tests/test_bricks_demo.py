"""a2uicatalog.ai/bricksdemo — the committed page must be what the generators produce, every model in it must be
buildable (no collisions, every brick anchored, balanced), and the page must stay self-contained and unlisted."""
import importlib.util
import re
from pathlib import Path

import pytest

from renderers import brick_validate as bv

ROOT = Path(__file__).parent.parent
PAGE = ROOT / "public" / "bricksdemo" / "index.html"

spec = importlib.util.spec_from_file_location("build_demo", ROOT / "scripts" / "brick_models" / "build_demo.py")
build_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_demo)


@pytest.fixture(scope="module")
def models():
    return build_demo.build_models()


def test_committed_page_is_what_the_generators_produce(models):
    assert PAGE.read_text(encoding="utf-8") == build_demo.render_page(models), \
        "public/bricksdemo/index.html is stale: run python3 scripts/brick_models/build_demo.py"


def test_every_model_is_buildable(models):
    assert [m["name"] for m in models] == ["Harry Potter", "Hogwarts Tower", "Sorting Hat", "Golden Snitch", "Microduck"]
    for m in models:
        bricks = [[x, y, z, w, d, 1, m["palette"][c]] for x, y, z, w, d, c in m["bricks"]]
        rep = bv.validate(bv.normalise(bricks)["bricks"])
        assert rep["ok"], (m["name"], [c for c in rep["checks"] if c["status"] == "fail"])
        assert 300 <= len(bricks) <= 3000, (m["name"], len(bricks))
    assert sum(len(m["bricks"]) for m in models) > 1000


def test_page_is_unlisted_self_contained_and_lists_every_model():
    html = PAGE.read_text(encoding="utf-8")
    assert 'name="robots" content="noindex, nofollow"' in html
    assert not re.search(r'<script[^>]+src=', html), "no external scripts"
    assert not re.search(r'<link[^>]+href="https?://', html), "no external stylesheets"
    assert "buildPicker" in html and "setAttribute('aria-label', 'Model')" in html      # the dropdown is built at runtime
    for name in ("Harry Potter", "Hogwarts Tower", "Sorting Hat", "Golden Snitch", "Microduck"):
        assert '"name":"%s"' % name in html, name
    assert '"picker":true' in html and '"start":0' in html
    assert "not affiliated with or endorsed by the LEGO Group" in html
    assert len(html) < 1_000_000
