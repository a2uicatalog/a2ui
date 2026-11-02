"""motion_arch on the atom page must move: a bare motion_arch is the finished diagram (its --p clock defaults to 1), so the
curated example is the converter's film, a motion_timeline that autoplays with controls (owner, 2 Nov: "motion_arch is not moving")."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import curated_examples as c  # noqa: E402
import generate_atom_pages as g  # noqa: E402


def test_the_motion_arch_example_is_a_playing_film():
    b = c.CURATED_EXAMPLE_BLOCKS["motion_arch"]
    assert b["type"] == "motion_timeline" and b["autoplay"] is True and b["controls"] is True and b["duration"] > 5
    inner = [x for x in b["blocks"] if x.get("type") == "motion_arch"]
    assert inner and inner[0]["nodes"] and inner[0]["edges"]                 # a real diagram, not an empty SVG
    assert any(t.get("target") == inner[0]["id"] for t in b["tracks"])      # the arch is driven by a track (--p goes 0 to 1)
    assert len(json.dumps(b)) < 20000                                        # fits the payload editor's cap


def test_the_generated_page_carries_the_film_clock_and_the_portrait_cap():
    html = g.render_page({"type": "motion_arch", "description": "d", "fields": {}, "surfaces": {"works_on": ["web"]}})
    i = html.find('class="preview-box')
    assert 'class="mt-root"' in html[i:] and "<script" in html[i:html.find("</section>", i)]   # the clock script is in the preview
    assert ".preview-box .mt-root:has(> .mt-vp" in html and "78vh" in html


def test_the_editor_keeps_a_typed_block_whole_even_when_it_has_children():
    js = g.editor_js()
    # motion_timeline carries its children in .blocks; unwrapping them dropped the clock and sent only a finished diagram
    assert "typeof v.type !== 'string' && Array.isArray(v.blocks)" in js
