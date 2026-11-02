"""The atom page's payload editor (design pass stage 2b-1): a Render button hands the edited payload to the site's own MCP Apps renderer (separate origin, postMessage) in an iframe. These tests pin the page contract and the escaping the renderer owes us for hostile payloads."""
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


def test_render_runs_in_the_separate_origin_renderer_and_the_page_checks_every_message():
    js = g.editor_js()
    assert "https://play.a2uicatalog.ai/renderer-bundle?v=" in js.replace("' + '", "").replace("ORIGIN + '/renderer-bundle?v=", "https://play.a2uicatalog.ai/renderer-bundle?v=")
    assert "__BUNDLE_HASH__" not in js and re.search(r"renderer-bundle\?v=[0-9a-f]+", js)       # cache-buster stamped
    assert "srcdoc" not in js and "innerHTML" not in js and "fetch(" not in js                 # nothing parsed into the page, no server call
    assert "ev.source !== frame.contentWindow" in js and "ev.origin !== ORIGIN" in js
    assert "m.jsonrpc !== '2.0'" in js
    assert "postMessage(m, ORIGIN)" in js and "postMessage(m, '*')" not in js                  # outgoing messages name the origin
    assert "allow-top-navigation" not in js and "allow-forms" not in js and "allow-modals" not in js
    assert "-32601" in js                                                                      # tools/call and open-link from the frame are refused


def test_editor_has_a_size_cap_and_says_where_rendering_happens():
    js = g.editor_js()
    assert "MAX = 20000" in js and "t.length > MAX" in js
    assert "Ctrl+Enter" in page() and "e.ctrlKey || e.metaKey" in js
    html = page()
    assert "drawn in your browser" in html and "play.a2uicatalog.ai" in html
    assert "50 renders" not in html and "sends the payload" not in html


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
