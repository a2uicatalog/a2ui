"""The in-browser captions (public/vendors/client-export/film_vtt.js) must equal scripts/film_vtt.py, byte for byte."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import film_still as fs  # noqa: E402
import film_vtt as fv  # noqa: E402
import generate_atom_pages as pages  # noqa: E402
from test_film_still import FILMS  # noqa: E402

JS = ROOT / "public" / "vendors" / "client-export" / "film_vtt.js"
RUNNER = "const FV=require(process.argv[1]);const j=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(FV.filmToVtt(j.film,j.cfg));"


def _js(film, cfg):
    r = subprocess.run(["node", "-e", RUNNER, str(JS)], input=json.dumps({"film": film, "cfg": cfg}),
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.mark.skipif(not shutil.which("node"), reason="node missing")
@pytest.mark.parametrize("path", FILMS)
def test_js_vtt_equals_python_vtt(path):
    film = json.loads((ROOT / path).read_text())["blocks"][0]
    cfg, _ = fs.film_cfg(film)
    want = fv.film_to_vtt(film)
    assert "-->" in want
    assert _js(film, cfg) == want


@pytest.mark.skipif(not shutil.which("node"), reason="node missing")
def test_js_vtt_demo_caption_and_escaping():
    film = {"type": "motion_timeline", "duration": 6, "blocks": [
        {"type": "motion_text", "id": "a", "text": "Fish & <chips> *now*", "place": {"x": 5, "y": 5, "w": 60}},
        {"type": "demo_caption", "id": "d", "lines": [{"who": "user", "text": "Hi <there>"}, {"text": "Hello"}]}]}
    cfg, _ = fs.film_cfg(film)
    want = fv.film_to_vtt(film)
    assert _js(film, cfg) == want


def test_export_page_offers_captions_only_with_cues():
    html = pages.MCP_APPS_EXPORT_HTML
    assert "/vendors/client-export/film_vtt.js" in html and "Captions (.vtt)" in html
    assert '<p id="cap" hidden>' in html and "indexOf('-->') < 0) return" in html
