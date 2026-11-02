"""The atom page's payload editor (design pass stage 2b-1): a Render button sends the edited payload to /api/render and shows the answer in an
iframe that can run nothing. These tests pin the page contract and the escaping the renderer owes us for hostile payloads."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import generate_atom_pages as g  # noqa: E402

TREEMAP = {"type": "treemap", "description": "d", "fields": {}, "surfaces": {"works_on": ["web"]}}


def page():
    return g.render_page(TREEMAP)


def test_page_keeps_static_payload_and_adds_labelled_editor():
    html = page()
    assert 'id="payload-code"' in html                                  # no-JS: the read-only payload stays
    assert '<label class="label" for="payload-editor">Payload (JSON)</label>' in html
    assert re.search(r'<textarea id="payload-editor"[^>]*aria-describedby="payload-status', html)
    assert 'id="payload-editor-wrap" hidden' in html                    # revealed only by script
    assert 'id="render-payload" hidden' in html and 'id="reset-payload" hidden' in html
    assert 'role="status" aria-live="polite"' in html                   # parse and schema errors are announced


def test_render_result_goes_into_an_iframe_that_cannot_run_scripts():
    js = g.EDITOR_JS
    assert "setAttribute('sandbox', 'allow-same-origin')" in js
    assert "allow-scripts" not in js and "allow-top-navigation" not in js and "allow-popups" not in js
    assert "innerHTML" not in js                                         # the answer is never parsed into the page itself
    assert "f.srcdoc = htmlText" in js


def test_editor_has_a_size_cap_and_a_daily_limit_message():
    js = g.EDITOR_JS
    assert "MAX = 20000" in js
    assert "r.status === 429" in js and "50 renders" in js
    assert "Ctrl+Enter" in page() and "e.ctrlKey || e.metaKey" in js
    assert "nothing is stored" in page()                                 # the page says it sends the payload; it must say what happens to it


def test_copy_payload_reads_the_edited_text():
    assert "document.getElementById('payload-editor')" in g.PREVIEW_JS


def test_hostile_strings_are_escaped_by_the_renderer_the_editor_calls():
    """The editor shows what the renderer returns. If the renderer let markup through, the iframe sandbox is the second wall; this is the first."""
    renderer = g._web_renderer
    if renderer is None:
        import pytest
        pytest.skip("web renderer not importable here")
    evil = ['<img src=x onerror="window.__pwn=1">', "<script>window.__pwn=2</script>", '"><svg onload=window.__pwn=3>']
    for text in evil:
        out = renderer.render([{"type": "heading", "text": text}, {"type": "text", "text": text}])
        assert "<script>window.__pwn" not in out
        assert not re.search(r"<(img|svg)[^>]*\son(error|load)=", out), out[:400]
        assert "&lt;" in out
