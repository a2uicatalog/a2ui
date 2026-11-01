import os

import pytest

from a2uicatalog import Client

pytestmark = [pytest.mark.live, pytest.mark.skipif(os.environ.get("A2UI_LIVE") != "1", reason="set A2UI_LIVE=1")]


def test_live_read_only_endpoints():
    c = Client()
    assert c.spec()["atomCount"] > 400
    assert "catalogs" in c.catalogs()
    assert c.atom_schema("heading")["properties"]["type"]["const"] == "heading"
    assert c.ask("countdown timer")["results"]


def test_live_render_one_payload():
    html = Client().render([{"type": "heading", "text": "Hi"}])
    assert "<h1" in html or "Hi" in html
