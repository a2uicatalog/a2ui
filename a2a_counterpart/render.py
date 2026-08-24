"""a2a_counterpart/render.py — Phase 3: render a StatefulSurfaceExecutor
derived-state dict to real HTML, for a human to actually SEE what Phase
1/2 proved in assertions. Dev/demo tool only, not the core deliverable —
A2A's real audience is other agents (Gemini design review, 2026-08-24):
this exists so a person can watch an A2A-driven, multi-agent-composed
surface build, not because A2A itself needs visual rendering.

Reuses the SAME decode+render pipeline GAS and the MCP Apps bundle
already ship in production (gen_mcp_apps_bundle's "a2ui-core" script
block, executed via Node — the same mechanism
tests/test_v1_template_decode.py already uses to test it) rather than
building a second renderer. Pull-based (render on request), not push —
this estate has no working Firestore-onSnapshot wiring to reuse (checked
before choosing this design, see the Phase 3 design note), and pull is
lower-risk for a dev tool with no real traffic.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

_core_js_cache: str | None = None


def _core_js() -> str:
    """Cached: gen_mcp_apps_bundle.build_bundle() concatenates 34+ files
    (~2MB) -- fine once per process, not per request."""
    global _core_js_cache
    if _core_js_cache is None:
        import gen_mcp_apps_bundle as gen
        bundle = gen.build_bundle()
        blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
        core = [b for b in blocks if "a2ui-core" in b[:300]]
        if not core:
            raise RuntimeError("a2ui-core script block missing from generated bundle")
        _core_js_cache = core[0]
    return _core_js_cache


class RenderError(RuntimeError):
    pass


def render_state_to_html(state: Dict[str, Any]) -> str:
    """`state` is one StatefulSurfaceExecutor.state[...] entry (components
    keyed by id, plus dataModel) -- converted here into the components-
    LIST shape _rehydrateV1Surface expects (the same shape a real
    createSurface message carries). metadata/title/theme are not captured
    by surface_state_from_create() today (a known, pre-existing Phase 1
    gap, not fixed here to avoid reopening an already-reviewed function) --
    renders with blank title/theme, blocks unaffected."""
    surface = {
        "components": list((state.get("components") or {}).values()),
        "dataModel": state.get("dataModel") or {},
    }
    core_js = _core_js()
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "d.js"
        driver.write_text(
            "global.window = global;\n" + core_js + f"""
var surface = {json.dumps(surface)};
var out = _rehydrateV1Surface(surface);
var html = renderAtoms(out.blocks, {{theme: out.theme}});
console.log(JSON.stringify({{html: html}}));
""")
        proc = subprocess.run(["node", str(driver)], capture_output=True,
                              text=True, timeout=30)
        if proc.returncode != 0:
            raise RenderError(proc.stderr[-2000:])
        return json.loads(proc.stdout)["html"]


PAGE_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8">
<title>a2a_counterpart — {surface_id}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; }}
  .asw-v1-card {{ border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin: 1rem 0; }}
  .asw-body {{ line-height: 1.5; }}
  a.asw-button {{ display: inline-block; padding: 10px 20px; border-radius: 8px; background: #6366f1; color: #fff; text-decoration: none; }}
</style></head>
<body>
<p style="color:#888;font-size:0.85rem;">a2a_counterpart Phase 3 — rendered from real derived A2A state
(context_id={context_id}, surfaceId={surface_id}). Dev/demo tool, not the core deliverable.</p>
<hr>
{html}
</body></html>"""
