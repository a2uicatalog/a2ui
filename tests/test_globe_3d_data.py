"""I11: the Python web renderer for globe_3d must draw the payload's dots (pins) and arcs
(as the GAS twin atoms_globe.gs does), not ~200 decorative random points."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from renderers import web_article as wa  # noqa: E402

PAYLOAD = {
    "type": "globe_3d", "size": 240, "color": "#10b981",
    "dots": [{"lat": 48.85, "lon": 2.35, "label": "Paris"},
             {"lat": -33.87, "lon": 151.21, "label": "Sydney", "color": "#ef4444"}],
    "arcs": [{"from": [48.85, 2.35], "to": [-33.87, 151.21], "color": "#f59e0b"}],
}


def _script(html):
    return re.search(r"<script>(.*?)</script>", html, re.S).group(1)


def test_web_globe_embeds_payload_pins_and_arcs_not_random_points():
    js = _script(wa._RENDERERS["globe_3d"](json.loads(json.dumps(PAYLOAD))))
    assert "Math.random" not in js
    assert "Paris" in js and "Sydney" in js
    assert "48.85" in js and "151.21" in js
    m = re.search(r"var C=(\{.*?\});var x=", js, re.S)
    assert m, "pins/arcs must be passed to the draw loop as data"
    cfg = json.loads(m.group(1))
    dots, arcs = cfg["dots"], cfg["arcs"]
    assert [d["label"] for d in dots] == ["Paris", "Sydney"]
    assert arcs[0]["from"] == [48.85, 2.35] and arcs[0]["to"] == [-33.87, 151.21]


def test_web_globe_without_pins_draws_no_invented_points():
    js = _script(wa._RENDERERS["globe_3d"]({"type": "globe_3d"}))
    assert "Math.random" not in js


def test_web_globe_data_cannot_break_out_of_script():
    p = {"type": "globe_3d", "dots": [{"lat": 0, "lon": 0, "label": "</script><img src=x>"}]}
    html = wa._RENDERERS["globe_3d"](p)
    assert html.count("</script>") == 1
