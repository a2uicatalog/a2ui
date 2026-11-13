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
    assert "MAX = 60000" in js and "t.length > MAX" in js
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


def test_the_box_is_fixed_and_a_size_report_never_resizes_it():
    """Root cause of the runaway height: the host sized the frame to the renderer's reported height + 2, the renderer measured its own (now taller)
    document and reported +2 again, forever (measured 50-59 reports in 6 s, 2 px each, to the cap). The host no longer feeds sizes back."""
    js = g.editor_js()
    assert "frame.style.height" not in js                                   # no code path sizes the frame from a report
    assert "Math.min(1600" not in js
    body = js[js.index("ui/notifications/size-changed"):]
    body = body[:body.index("else if (hasId)")]
    assert "style.height" not in body and "sizeReports++" in body           # a report only lifts the loading veil, once
    assert "target.style.height = Math.min(cap" in js                       # pinned in px to the static preview's height, clamped
    assert "0.6 : 0.8" in js                                                # 60% of the screen on a phone, 80% elsewhere
    css = g.ATOM_PAGE_CSS
    assert ".preview-box.is-custom iframe{display:block;width:100%;height:100%" in css   # the frame fills the box and scrolls inside it
    assert "frame.tabIndex = 0" in js                                       # the scrolling frame is a keyboard stop


def test_a_render_has_one_path_and_no_server_fallback():
    js = g.editor_js()
    assert "api/render" not in js and "fetch(" not in js and "XMLHttpRequest" not in js
    assert "did not answer" in js and "10000" in js                          # the 10 s error message stays


def test_loading_veil_sits_inside_the_same_box_and_respects_reduced_motion():
    js, css = g.editor_js(), g.ATOM_PAGE_CSS
    assert "custom-loading" in js and ".custom-loading" in css
    assert "@media (prefers-reduced-motion:reduce){.custom-spin{animation:none" in css


def test_pause_button_is_in_every_page_and_hidden_unless_something_moves():
    static = page()
    assert 'id="pause-preview"' in static and re.search(r'id="pause-preview"[^>]*\shidden', static)       # treemap does not move: hidden
    moving = g.render_page({"type": "message_lanes", "description": "d", "fields": {}, "surfaces": {"works_on": ["web"]}})
    m = re.search(r'<button[^>]*id="pause-preview"[^>]*>', moving)
    assert m and " hidden" not in m.group(0) and 'aria-pressed="false"' in m.group(0) and 'aria-label="Pause ' in m.group(0)


def test_pause_drives_the_custom_frame_and_keeps_its_label_and_state_in_sync():
    js = g.editor_js()
    assert "MutationObserver" in js and "attributeFilter: ['aria-pressed']" in js        # follows the one Pause button
    assert "function setPaused" in js and "custom-paused" in js
    assert "removeChild(frame)" in js or "frame.parentNode.removeChild(frame)" in js     # no pause message exists: the frame is torn down
    assert "pauseBtn(false)" in js                                                       # Render means run it; Reset restores the static state
    assert "matchMedia('(prefers-reduced-motion: reduce)')" in js                        # Reset keeps a reduced-motion visitor still
    assert "postMessage(m, '*')" not in js


def test_the_frame_is_always_told_the_light_theme_because_its_box_is_white():
    assert "function theme(){ return 'light'; }" in g.editor_js()
