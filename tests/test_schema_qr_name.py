"""schema_qr: the QR code is an image, so its SVG must carry an accessible name (WCAG 1.1.1).

Found 2026-10-08: the axe ratchet flagged schema_qr for svg-img-alt (role="img" with no name), and the PPTX spike needed alt text for the same
shape. The name is "QR code for <url>", escaped; the interactive variant sets it from the live input at render time."""
import json, re, subprocess, sys, tempfile
from pathlib import Path
import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gen_mcp_apps_bundle as gen  # noqa: E402
from renderers.web_article import _RENDERERS  # noqa: E402

URL = "https://a2uicatalog.ai"
AMP = "https://x.y/?a=1&b=2"
HOSTILE = 'https://x.y/?a="b"<c>'


@pytest.fixture(scope="module")
def gas():
    core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", gen.build_bundle(), re.S) if "a2ui-core" in b[:300]][0]
    blocks = {"plain": {"type": "schema_qr", "url": URL}, "amp": {"type": "schema_qr", "url": AMP}, "hostile": {"type": "schema_qr", "url": HOSTILE},
              "live": {"type": "schema_qr", "url": URL, "is_interactive": True}}
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core + f"\nvar c = {json.dumps(blocks)}, o = {{}};"
                     "Object.keys(c).forEach(function(k){ o[k] = renderAtoms([c[k]], {}); }); console.log(JSON.stringify(o));")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-800:]
        return json.loads(p.stdout)


def _py(url, **kw): return _RENDERERS["schema_qr"]({"type": "schema_qr", "url": url, **kw})


def _svg(h): return re.search(r"<svg[^>]*>", h).group(0)


def test_static_svg_has_a_name_in_both_renderers(gas):
    for h in (gas["plain"], _py(URL)):
        s = _svg(h); assert 'role="img"' in s and f'aria-label="QR code for {URL}"' in s


def test_the_name_is_escaped_in_both_renderers(gas):
    for h in (gas["amp"], _py(AMP)):
        assert 'aria-label="QR code for https://x.y/?a=1&amp;b=2"' in _svg(h)


def test_a_hostile_url_never_reaches_the_name(gas):
    for h in (gas["hostile"], _py(HOSTILE)):
        markup = re.sub(r"<script>.*?</script>", "", h, flags=re.S)           # with the url dropped the atom falls back to the page URL, drawn by a script
        assert "<svg" not in markup and "QR code for https://x.y/?a=" not in h  # so no static svg exists to label, and the hostile text appears nowhere


def test_the_live_variant_names_the_svg_from_the_input_at_render_time(gas):
    assert 'setAttribute("aria-label","QR code for "+text)' in gas["live"]       # set with setAttribute, never concatenated into markup
    assert "setAttribute('aria-label','QR code for '+text)" in _py(URL, is_interactive=True)
