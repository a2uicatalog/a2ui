"""sequence_diagram `animate` flag: opt-in CSS-only reveal; off = byte-identical output."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "renderers"))
import web_article  # noqa: E402

R = web_article._RENDERERS["sequence_diagram"]
BASE = {"type": "sequence_diagram", "autonumber": True,
        "actors": ["A", "B"],
        "messages": [{"from": "A", "to": "B", "text": "one"},
                     {"frame": "loop", "label": "L", "messages": [
                         {"from": "B", "to": "A", "text": "two", "kind": "return"}]},
                     {"note": True, "text": "n"},
                     {"from": "A", "to": "B", "text": "three"}]}


def _delays(h):
    return [int(x) for x in re.findall(r"a2ui-seq-in \.45s ease (\d+)ms both", h)]


def test_off_is_byte_identical_and_has_no_animation():
    plain = R(dict(BASE))
    assert R(dict(BASE, animate=False)) == plain
    assert R(dict(BASE, animate_step_ms=900)) == plain
    assert "a2ui-seq" not in plain and "<style" not in plain


def test_animate_reveals_in_order_frames_static():
    h = R(dict(BASE, animate=True))
    assert _delays(h) == [0, 600, 1200, 1800]       # 3 messages + 1 note, frame box excluded
    assert h.count('class="a2ui-seq-row"') == 4
    assert "prefers-reduced-motion:reduce" in h
    assert "opacity" in h and "transform" not in h.split("</style>")[0]
    for t in ("one", "two", "three"):               # content stays in the DOM
        assert t in h


def test_step_bounds_and_cap():
    assert _delays(R(dict(BASE, animate=True, animate_step_ms=1000)))[1] == 1000
    for bad in (50, 5000, "x", True, 1.5):
        assert _delays(R(dict(BASE, animate=True, animate_step_ms=bad)))[1] == 600
    big = dict(BASE, animate=True, animate_step_ms=2000,
               messages=[{"from": "A", "to": "B", "text": str(i)} for i in range(100)])
    d = _delays(R(big))
    assert max(d) <= 20000          # whole reveal bounded: 20 s + 0.45 s fade


def test_gas_renderer_mirrors_python():
    src = (ROOT / "apps-script-surface/gas-wired-renderer/atoms_charts.gs").read_text()
    body = src[src.index("_RENDERERS['sequence_diagram']"):src.index("_RENDERERS['tooltip_glossary']")]
    for tok in ("b.animate === true", "animate_step_ms", "a2ui-seq-in", "20000", "prefers-reduced-motion"):
        assert tok in body
    bundle = (ROOT / "public/surfaces/mcp-apps/renderer-bundle.html").read_text()
    assert "a2ui-seq-in" in bundle


def test_schema_and_examples():
    spec = json.loads((ROOT / "public/catalogue/atoms-json-schema.json").read_text())
    br = [b for b in spec["items"]["oneOf"] if b["properties"]["type"].get("const") == "sequence_diagram"][0]
    assert "animate" in br["properties"] and "animate_step_ms" in br["properties"]
    for f in ("animate-login", "animate-loop"):
        blocks = json.loads((ROOT / f"examples/sequence-diagram/{f}.json").read_text())
        assert blocks[0]["animate"] is True
        assert "a2ui-seq-in" in R(blocks[0])
