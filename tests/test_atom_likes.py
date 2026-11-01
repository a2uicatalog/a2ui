"""I160 atom likes: the page side (button markup, hub counts, failure behaviour) and the Worker side (src/likes.js, run with node).

Acceptance points 1-5 of pm/evidence/owner/2026-11-01-atom-likes-spec.md: the like round trip and ">= 0" clamp are in
tests/likes_worker.test.mjs; here the pages are checked as generated, and the script's behaviour with the endpoint down."""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _gap():
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT / "renderers"))
    spec = importlib.util.spec_from_file_location("gap_likes", ROOT / "scripts" / "generate_atom_pages.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_worker_likes_module():
    r = subprocess.run(["node", "--test", str(ROOT / "tests" / "likes_worker.test.mjs")], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-1000:]


def test_the_worker_routes_likes_to_the_module_and_declares_the_binding_note():
    w = (ROOT / "src" / "worker.js").read_text()
    assert "handleLikes" in w and "/api/likes" in w
    assert "kv_namespaces" in (ROOT / "wrangler.toml").read_text()


def test_button_is_a_named_pressed_toggle_hidden_until_counts_load():
    m = _gap()
    b = m.like_button("treemap", "Treemap")
    assert 'aria-label="Like Treemap"' in b and 'aria-pressed="false"' in b and " hidden" in b
    assert 'type="button"' in b and 'data-like="treemap"' in b
    assert 'aria-describedby="like-n"' in b and 'id="like-n"' in b


def test_script_fails_quietly_and_keeps_state_in_localstorage_only():
    js = _gap().LIKES_JS
    assert "fetch('/api/likes')" in js and ".catch(function(){})" in js          # endpoint down: nothing happens, button stays hidden
    assert "btn.hidden = false" in js and js.index("btn.hidden = false") > js.index("counts = c")   # shown only after a good answer
    assert js.count("try {") >= 2 and "localStorage" in js                         # blocked storage must not throw
    assert "{ delta: d }" in js                                                      # the POST carries a delta and nothing else
    assert "document.cookie" not in js


def test_atom_page_and_hub_carry_the_likes_ui():
    m = _gap()
    import yaml
    raw = yaml.safe_load(open(m.SCHEMA))
    seen, atoms = set(), []
    for b in raw.get("blocks", []):
        t = b.get("type")
        if b.get("stage", "stable") == "stable" and b.get("visibility") != "private" and t and t not in seen:
            seen.add(t)
            atoms.append(b)
    page = m.render_page(next(a for a in atoms if a["type"] == "treemap"))
    assert 'class="title-row"><h1>Treemap</h1><button' in page and "LIKES_JS" not in page and "/api/likes" in page
    assert page.count("<h1") == 1
    hub = m.render_atoms_hub(atoms)
    assert hub.count('class="hub-likes"') == len(atoms) and "/api/likes" in hub
