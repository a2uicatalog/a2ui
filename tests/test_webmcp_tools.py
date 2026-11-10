"""WebMCP tool definitions must stay readable from the page source (Ora rules
release 3, 2026-11-10: tools built from the DOM at run time are not graded,
and the old form loop registered nothing on the homepage). Parses the
generated pages, so run it after scripts/generate_atom_pages.py."""
import re
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
TOOLS = ("search_atoms", "get_atom")


def _registrations(html: str):
    return re.findall(r"registerTool\(\{\s*name: '([a-z_]+)'", html)


def test_homepage_registers_literal_read_only_tools():
    html = (PUBLIC / "index.html").read_text()
    assert _registrations(html) == list(TOOLS)
    assert html.count("annotations: {readOnlyHint: true}") == len(TOOLS)
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
