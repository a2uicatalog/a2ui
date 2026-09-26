"""Microduck-scale stress test (spec/brick-parts-v0.1.md section 8) for both validators. The JS side is
tests/test_brick_parts_stress.mjs (run here via subprocess so `pytest tests/ -q` covers it); the Python twin is
run in-process on the same synthetic ~1,000-part model. Both must find it a fully valid build (no collisions,
nothing floating, every check passing) inside a time budget -- the test that found, and now guards, the O(n^2)
pairwise loops both validators originally had (~60 s at 1,000 parts before spatial hashing)."""
import json
import subprocess
import time
from pathlib import Path

from renderers.brick_parts_validate import validate_parts

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def test_js_validator_scales():
    proc = subprocess.run(["node", str(HERE / "test_brick_parts_stress.mjs")], capture_output=True, text=True,
                          timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "stress test passed" in proc.stdout


def _model():
    cols = rows = layers = 10
    parts = []
    for L in range(layers):
        for r in range(rows):
            for c in range(cols):
                parts.append({'p': '3001', 'x': 40 + c * 80 + (40 if L % 2 else 0), 'y': -24 * (L + 1),
                              'z': 20 + r * 40, 'r': 0})
    top_shift = 40 if (layers - 1) % 2 else 0
    top_y = -24 * layers
    for c in range(cols):
        parts.append({'p': '3024', 'x': 10 + top_shift + c * 80, 'y': top_y - 8, 'z': 10, 'r': 0})
    parts.append({'p': '6141', 'x': 10 + top_shift + 20, 'y': top_y - 8, 'z': 30, 'r': 0})
    parts.append({'p': '3070b', 'x': 10 + top_shift + 60, 'y': top_y - 8, 'z': 30, 'r': 0})
    return parts


def test_python_validator_scales():
    parts = _model()
    meshes = {pid: json.loads((ROOT / 'public' / 'parts' / (pid + '.json')).read_text())
              for pid in {e['p'] for e in parts}}
    t0 = time.time()
    r = validate_parts(parts, meshes)
    elapsed = time.time() - t0
    assert len(parts) >= 1000
    assert r['collisions'] == [] and r['floating'] == []
    assert r['ok'] and all(c['status'] == 'pass' for c in r['checks']), r['checks']
    assert elapsed < 30, elapsed
