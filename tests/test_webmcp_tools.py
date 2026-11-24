"""WebMCP tool definitions must stay readable from the page source (Ora rules
release 3, 2026-11-10: tools built from the DOM at run time are not graded,
and the old form loop registered nothing on the homepage). Parses the
generated pages, so run it after scripts/generate_atom_pages.py."""
import re
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
TOOLS = ("search_atoms", "get_atom", "create_share_link", "delete_share_link")
READ_ONLY = 2


def _registrations(html: str):
    return re.findall(r"registerTool\(\{\s*name: '([a-z_]+)'", html)


def test_homepage_registers_literal_tools_with_honest_hints():
    html = (PUBLIC / "index.html").read_text()
    assert _registrations(html) == list(TOOLS)
    assert html.count("annotations: {readOnlyHint: true}") == READ_ONLY
    assert html.count("consequentialHint: true") == len(TOOLS) - READ_ONLY
    assert html.count("inputSchema: {") == len(TOOLS)
    assert "form[toolname]" not in html


def test_document_model_context_comes_before_the_navigator_alias():
    html = (PUBLIC / "index.html").read_text()
    assert html.index("document.modelContext") < html.index("navigator.modelContext")


def test_form_loop_only_on_pages_with_toolname_forms():
    for page in ("try", "frugal-ai-ops"):
        html = (PUBLIC / page / "index.html").read_text()
        assert "form[toolname]" in html
        assert _registrations(html) == list(TOOLS)
    atom = (PUBLIC / "atoms" / "gallery" / "index.html").read_text()
    assert "form[toolname]" not in atom
    assert _registrations(atom) == list(TOOLS)


def test_try_form_is_a_declarative_tool_with_a_schema_and_an_answer():
    """/try/ used to get a second, imperative registration from the generic form loop: no inputSchema, execute() ignored its
    arguments (an agent could not pass a prompt) and returned only {status:'submitted'} (it never saw the routing result).
    Found in the 2026-11-24 WebMCP review. The form is now a declarative tool and answers through SubmitEvent.respondWith."""
    html = (PUBLIC / "try" / "index.html").read_text()
    form = re.search(r'<form[^>]*id="try-form"[^>]*>', html).group(0)
    assert 'toolname="route_ui_request"' in form and "toolautosubmit" in form and 'data-webmcp="declarative"' in form
    area = re.search(r'<textarea[^>]*id="try-prompt"[^>]*>', html).group(0)
    assert 'name="prompt"' in area and "toolparamdescription=" in area, "the control needs a name and a description for the schema"
    handler = html[html.index("form.addEventListener('submit'"):]
    handler = handler[:handler.index("}});" if "}});" in handler else "});")]
    assert "e.agentInvoked" in handler and "e.respondWith(" in handler
    assert handler.index("e.preventDefault()") < handler.index("e.respondWith("), "preventDefault must come before respondWith"
    assert handler.count("submitPrompt(") == 1, "one request per submit: the agent path must reuse it, not fetch again"


def test_try_renders_inline_in_a_sandboxed_cross_origin_frame():
    """Phase 2 step 1 (2026-11-24): the routed blocks render on the page in the MCP Apps renderer, hosted the way the payload editor hosts it:
    a frame on play.a2uicatalog.ai (no cookies or storage of this site), messages accepted only from that frame and origin in a fixed shape,
    every request from the frame refused. The new-tab button stays as the second way."""
    html = (PUBLIC / "try" / "index.html").read_text()
    assert 'id="try-render"' in html and 'id="try-newtab"' in html and 'id="try-stage"' in html
    host = html[html.index("var STAGE_ORIGIN"):html.index("function renderInline")]
    assert "STAGE_ORIGIN = 'https://play.a2uicatalog.ai'" in host
    assert "ev.source !== stageFrame.contentWindow || ev.origin !== STAGE_ORIGIN" in host
    assert "postMessage(m, STAGE_ORIGIN)" in host, "never post to '*'"
    assert "code: -32601" in host, "requests from the frame (tools/call, open-link) must be refused"
    assert "innerHTML" not in host, "nothing the frame sends may be put into the page as markup"
    frame = html[html.index("function renderInline"):html.index("result.addEventListener('click'")]
    assert "sandbox', 'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox'" in frame
    assert "referrerpolicy" in frame and "no-referrer" in frame
    assert "renderer-bundle?v=" in host
    # a successful route draws straight away (no extra click); the buttons are only for drawing again or opening a tab
    draw = html[html.index("function render(data, status)"):html.index("function submitPrompt")]
    assert "if (lastBlocks) renderInline(lastBlocks);" in draw
    assert "Render again" in html and "Render it here" not in html


def test_generic_form_loop_skips_declarative_forms():
    for page in ("try", "frugal-ai-ops"):
        html = (PUBLIC / page / "index.html").read_text()
        assert """form[toolname]:not([data-webmcp="declarative"])""" in html
    # /frugal-ai-ops/ still uses the generic loop (known limit: no input schema), so its form must NOT carry the opt-out
    frugal = (PUBLIC / "frugal-ai-ops" / "index.html").read_text()
    assert 'data-webmcp="declarative"' not in re.search(r'<form[^>]*id="frugal-form"[^>]*>', frugal).group(0)


def test_every_sitemap_page_has_a_markdown_twin():
    xml = (PUBLIC / "sitemap-pages.xml").read_text()
    missing = []
    for loc in re.findall(r"<loc>https://a2uicatalog.ai/([^<]*)</loc>", xml):
        path = loc.strip("/")
        if path and not path.startswith(("atoms", "blog")) and not (PUBLIC / (path + ".md")).is_file():
            missing.append(path)
    assert not missing, missing
