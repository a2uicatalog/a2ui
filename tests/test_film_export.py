"""Film export from inside a host (2026-10-06).

A host's sandbox (claude.ai, ChatGPT, the site's own playground) has no allow-downloads, so a film's MP4/GIF
buttons in a host ask it to open the export page (ui/open-link) with the film in the link; the export page
paints it in the same-origin renderer bundle and the vendored exporter encodes it in the visitor's browser.
These checks keep the pieces wired together: the view's host bridge, the export page, the playground host's
open-link answer, and the vendored exporter with its licences. The browser end to end (auto GIF download) was
run headless when this shipped.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as bundle  # noqa: E402
import generate_atom_pages as pages  # noqa: E402

VENDOR = ROOT / "public" / "vendors" / "client-export"


def test_view_exports_through_the_host_only_inside_a_host():
    js = bundle.HANDSHAKE
    assert "method: 'ui/open-link'" in js
    assert "https://a2uicatalog.ai/surfaces/mcp-apps/export/" in js
    # never in a top-level page (the Android app) and never over an exporter the page already has
    assert "window.parent !== window && !window.A2UIExport" in js
    assert "_lastPayload = result.structuredContent" in js


def test_export_page_paints_then_exports():
    html = pages.MCP_APPS_EXPORT_HTML
    assert 'src="/surfaces/mcp-apps/renderer-bundle.html"' in html          # same origin: the page can reach the film
    assert "/vendors/client-export/client_export.min.js" in html            # lazy-loaded exporter
    i_set, i_paint = html.index("w.A2UIExport ="), html.index("w._A2UI_PAINT(payload)")
    assert i_set < i_paint, "the exporter must exist before the film starts, or it shows no buttons"
    assert re.search(r"k=\(mp4\|gif\)", html), "&k= picks the export to start"


def test_playground_host_answers_open_link_for_https_only():
    js = pages.MCP_APPS_HOST_JS
    assert "msg.method === 'ui/open-link'" in js
    assert "/^https:\\/\\//.test(link)" in js


def test_vendored_exporter_and_its_licences():
    lib = (VENDOR / "client_export.min.js").read_text()
    assert lib.startswith("/* A2UI Catalog film exporter") and "var ClientExport=" in lib
    lic = (VENDOR / "LICENSES.md").read_text()
    for name in ("gifenc", "mp4-muxer", "webm-muxer"):
        assert f"## {name} " in lic and "MIT" in lic
    assert "public/vendors/client-export/client_export.min.js" in (ROOT / "THIRD-PARTY-NOTICES.md").read_text()
