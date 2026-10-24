"""The 3D Sankey cinema scene (I122): a composition of existing atoms, plus one opt-in field on sankey_flow (keyed).

Concept credit: Cornelius van Heerden. The scene is built by scripts/sankey_scene.py; payloads/sankey-cinema.json is its output.
Covers: the keyed field in both twins (and unchanged bytes without it), the scene renders and passes the flash lint, the particle cap,
keys that join the map and the Sankey, the settled (poster) frame is the flat Sankey with its text table, and in Chromium that the
particle curves sit on the Sankey's drawn flows.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))
import film_still  # noqa: E402
import motion_lint  # noqa: E402
import sankey_scene as ss  # noqa: E402
from test_motion_atoms import _node_raw, _norm, _py_keyed, browser, core_js  # noqa: E402,F401

import renderers.web_article as wa  # noqa: E402

KEYED = re.compile(r' data-(?:cb|key)="[^"]*"')


def test_keyed_is_opt_in_and_purely_additive():
    plain, keyed = ss.sankey_block(False), ss.sankey_block(True)
    assert "keyed" not in plain
    a, b = _py_keyed(plain), _py_keyed(keyed)
    assert "data-cb" not in a and "data-key" not in a
    assert KEYED.sub("", b) == a, "keyed only adds data-cb and data-key attributes"
    assert _py_keyed(dict(plain, keyed=False)) == a and _py_keyed(dict(plain, keyed="yes")) == a, "only true turns it on"


def test_keyed_markup_carries_node_label_and_link_keys():
    h = _py_keyed(ss.sankey_block(True))
    nodes = re.findall(r'<rect data-cb="node" data-key="([^"]+)"', h)
    labels = re.findall(r'<text data-cb="label" data-key="([^"]+)"', h)
    links = re.findall(r'<path class="sk-l" data-cb="link" data-key="([^"]+)"', h)
    ids = [i for i, _ in ss.COUNTRIES + ss.CARGO + ss.REGIONS]
    assert sorted(nodes) == sorted(ids) and sorted(labels) == sorted(ids)
    want = [s + "&gt;" + t for s, t, _ in ss.FLOWS]
    assert sorted(links) == sorted(want) and len(set(links)) == len(links)


def test_a_repeated_pair_gets_a_numbered_key():
    b = {"type": "sankey_flow", "keyed": True, "nodes": [{"id": "A"}, {"id": "B"}],
         "links": [{"source": "A", "target": "B", "value": 3}, {"source": "A", "target": "B", "value": 2}]}
    assert re.findall(r'data-cb="link" data-key="([^"]+)"', _py_keyed(b)) == ["A&gt;B", "A&gt;B#2"]


def test_python_twin_matches_gas_exactly(core_js):
    cases = [ss.sankey_block(True), ss.sankey_block(False),
             {"type": "sankey_flow", "keyed": True, "nodes": [{"id": 'x"<b>'}, {"id": "B"}],
              "links": [{"source": 'x"<b>', "target": "B", "value": 3}, {"source": 'x"<b>', "target": "B", "value": 2}]},
             {"type": "sankey_flow", "keyed": "true", "nodes": [{"id": "A"}, {"id": "B"}], "links": [{"source": "A", "target": "B", "value": 1}]}]
    got = _node_raw(core_js, "var B = %s; console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));" % json.dumps(cases))
    for c, g in zip(cases, got):
        assert _norm(_py_keyed(dict(c))) == _norm(g), str(c)[:80]
    assert "data-cb" in got[0] and "data-cb" not in got[1] and "data-cb" not in got[3]


def test_the_film_renders_and_passes_the_flash_lint():
    f = ss.film()
    assert not motion_lint.lint(f), motion_lint.lint(f)      # no errors and no warnings
    html = wa._render_motion_timeline(f)
    assert "motion_timeline ignored" not in html
    assert html.count('data-cb="node"') >= 13           # the keyed Sankey (B) is in the page
    assert html.count('data-cb="tile"') >= 6            # and so is the map (A), whose tiles carry the same ISO codes


def test_particles_are_capped_and_the_cap_is_stated():
    heads, els = ss.particle_count()
    assert els == heads * (1 + ss.TRAIL_N) <= ss.PARTICLE_CAP == 200
    html = wa._render_motion_timeline(ss.film())
    assert len(re.findall(r'data-mt-id="(?:d\d+|tr\d+g\d+)"', html)) == els
    p = ss.payload()
    assert "capped at 200" in p["blocks"][1]["text"] and "Cornelius van Heerden" in p["blocks"][1]["text"]
    assert any("Cornelius van Heerden" in b.get("text", "") for b in p["blocks"][0]["blocks"] if b["type"] == "motion_text")


def test_every_exporter_is_a_map_region_so_the_morph_has_something_to_join():
    codes = {r[0] for r in wa._ch_regions("world-countries")}
    assert {i for i, _ in ss.COUNTRIES} <= codes
    a = _py_keyed(ss.map_block())
    for i, _ in ss.COUNTRIES:
        assert 'data-cb="tile" data-key="%s"' % i in a


def test_the_settled_frame_is_the_flat_sankey_with_its_text_table():
    doc = film_still.film_poster_document(ss.film())
    assert "<script" not in doc.lower() and "animation:" not in doc
    assert '<th scope="col">Source</th>' in doc and "<svg" in doc
    for _, name in ss.COUNTRIES:
        assert name in doc
    assert not re.search(r'data-mt-id="d\d+"[^>]*opacity:0\.[1-9]', doc), "no particle is visible on the settled frame"
    assert ss.film()["poster"] == ss.DURATION and ss.film()["loop"] is False


def test_the_camera_returns_flat_and_the_particles_end_hidden():
    f = ss.film()
    last = f["camera"]["keys"][-1]
    assert last["rx"] == 0 and last["ry"] == 0 and last["zoom"] == 1.0 and last["t"] < f["duration"]
    for t in f["tracks"]:
        if t["target"].startswith("d"):
            assert t["keys"][-1]["opacity"] == 0 and t["keys"][-1]["t"] < f["duration"]


def test_the_showcase_payload_is_the_generator_output():
    got = json.loads((ROOT / "payloads" / "sankey-cinema.json").read_text())
    assert got == ss.payload(), "run: python3 scripts/sankey_scene.py payloads/sankey-cinema.json"


def test_the_showcase_payload_renders_as_a_page():
    page = ss.demo_page()
    assert page.startswith("<!doctype html><html lang=") and "<title>" in page and "mt-root" in page


@browser
def test_the_particle_curves_sit_on_the_drawn_flows():
    """Measured in Chromium at the settled frame: the Sankey SVG's box equals the box svg_frame() assumes (2 px), so the curves handed to
    the particle tracks are the flows' own curves."""
    import subprocess
    import tempfile

    from test_motion_atoms import CHROMIUM
    probe = ("<script>window.addEventListener('load',function(){setTimeout(function(){var st=document.querySelector('.mt-root');"
             "var sv=document.querySelector('.mtr-b svg');var s=st.getBoundingClientRect(),v=sv.getBoundingClientRect(),k=s.width/1280;"
             "document.documentElement.setAttribute('data-probe',JSON.stringify([(v.x-s.x)/k,(v.y-s.y)/k,v.width/k,v.height/k]))},300)});</script>")
    page = ss.demo_page().replace("</body>", probe + "</body>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--window-size=1300,900",
                              "--virtual-time-budget=8000", "--use-angle=swiftshader", "--user-data-dir=" + td + "/prof", "--dump-dom",
                              "file://" + str(f) + "#t=16"], capture_output=True, text=True, timeout=120).stdout
    m = re.search(r'data-probe="([^"]*)"', out)
    assert m, out[:300]
    x, y, w, h = json.loads(m.group(1).replace("&quot;", '"'))
    mdl = wa._sk_model(ss.sankey_block(False))
    ox, oy, sc = ss.svg_frame(mdl)
    assert abs(x - ox) < 2 and abs(y - oy) < 2 and abs(w - mdl["w"] * sc) < 2 and abs(h - mdl["h"] * sc) < 2, (x, y, w, h, ox, oy, mdl["w"] * sc)
