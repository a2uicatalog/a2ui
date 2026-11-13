"""The Mermaid / D2 paste window (scripts/gen_try_mermaid.py, scripts/try_mermaid/): checked as generated.

The browser end to end (paste, convert in the worker, film in the renderer frame, Focus, Pause) was run headless when this was built;
the converter limits are in tests/try_mermaid_worker.test.mjs (node --test), run from here when node is available.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_try_mermaid as gen  # noqa: E402

SRC = ROOT / "scripts" / "try_mermaid"


def test_worker_is_one_classic_script_with_the_limits_inside():
    js = gen.worker_script()
    assert not re.search(r"^\s*(import|export)\s", js, flags=re.M)
    for name in ("parseMermaid", "parseD2", "graphToArch", "ArchError"):
        assert name in js
    assert "TM_MAX_CHARS = 20000" in js and "TM_MAX_LINE = 500" in js and "TM_MAX_NODES = 12" in js and "TM_MAX_EDGES = 16" in js
    assert "self.onmessage" in js and "fetch(" not in js and "XMLHttpRequest" not in js and "importScripts" not in js


def test_component_never_puts_text_into_the_page_as_markup():
    js = (SRC / "try-mermaid.js").read_text()
    for bad in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
        assert bad not in js, bad
    # the frame is checked on every message: source, origin, JSON-RPC shape; tool calls and links are refused
    assert "ev.source !== frame.contentWindow || ev.origin !== origin" in js
    assert "m.jsonrpc !== '2.0'" in js and "-32601" in js
    # the renderer's reported height is never used for sizing (it grew the frame without end), Focus has Esc and a trap
    assert "style.height" not in js
    assert "e.key === 'Escape'" in js and "n.inert = false" in js and "sib.inert = true" in js
    # the worker is stopped after five seconds and input is debounced
    assert "KILL_MS = 5000" in js and "DEBOUNCE_MS = 300" in js and "worker.terminate()" in js


def test_page_has_the_window_the_limits_and_live_regions():
    html = gen.page_html()
    assert 'id="try-mermaid"' in html and 'data-worker="/try-mermaid/convert.worker.js"' in html
    assert re.search(r'data-bundle="https://play\.a2uicatalog\.ai/renderer-bundle\?v=[0-9a-f]+"', html)
    assert "TryMermaid.mount" in html and "12 nodes, 16 edges, 20,000 characters" in html
    assert 'name="robots"' in html and "noindex" in html
    js = (SRC / "try-mermaid.js").read_text()
    assert "aria-live" in js and "role: 'status'" in js and "'aria-label': 'Input language'" in js
    assert "Mermaid or D2 source" in js and "Show relation column" in js
    # the relation column is off unless the visitor ticks it
    assert "cbRel = el('input', { type: 'checkbox', id: id('rel') })" in js and "checked" not in js.split("cbRel = el(")[1].split("\n")[0]


def test_no_upload_copy_only_after_it_was_verified():
    html = gen.page_html()
    js = (SRC / "try-mermaid.js").read_text()
    assert "Your diagram is not uploaded" in js and "verified ? 'Runs in your browser. Your diagram is not uploaded. ' : ''" in js
    assert ('data-noupload="1"' in html) == gen.NO_UPLOAD_VERIFIED


def test_the_build_step_is_in_ci_and_the_path_is_declared():
    assert "scripts/gen_try_mermaid.py" in (ROOT / ".github" / "workflows" / "deploy.yml").read_text()
    assert "public/try-mermaid/**" in (ROOT / "project.yaml").read_text()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_worker_limits_hold_inside_the_worker():
    gen.OUT.mkdir(parents=True, exist_ok=True)
    (gen.OUT / "convert.worker.js").write_text(gen.worker_script())
    r = subprocess.run(["node", "--test", str(ROOT / "tests" / "try_mermaid_worker.test.mjs")], capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stdout[-2500:] + r.stderr[-800:]


def test_motion_arch_inspector_has_a_mermaid_tab_and_no_other_atom_does():
    import generate_atom_pages as g
    box = g.mermaid_panel("motion_arch")
    assert 'id="panel-mermaid"' in box and 'data-mode="inspector"' in box and "/try-mermaid/try-mermaid.js" in box and "renderer-bundle?v=" in box
    assert g.mermaid_panel("button") == ""
    assert 'id="tab-mermaid"' in g.atom_inspector({"type": "motion_arch", "fields": []}, "")
    assert "A2UIEditor" in g.EDITOR_JS


def test_mermaid_pasted_while_d2_is_on_switches_language():
    js = (ROOT / "scripts" / "try_mermaid" / "try-mermaid.js").read_text()
    assert "looksMermaid" in js and "Mermaid button is now on" in js
