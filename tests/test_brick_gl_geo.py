"""The brick_build_3d WebGL renderer's unit box and stud must face outward and the box must be closed (backface
culling and the shadow pass depend on it), and its shaders must be well-formed. Delegates to
scripts/test_brick_gl_geo.mjs, which evals the real atoms_brick.gs; skipped when node is absent."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
NODE = shutil.which("node") or "/home/curtis/.config/nvm/versions/node/v24.11.1/bin/node"


@pytest.mark.skipif(not Path(NODE).exists() and not shutil.which("node"),
                    reason="node not available")
def test_webgl_geometry_and_shaders():
    result = subprocess.run(
        [NODE, str(ROOT / "scripts" / "test_brick_gl_geo.mjs")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
