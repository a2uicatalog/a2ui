"""Client-side A2UI streaming runtime and live atom controllers.
Runs tests-js suite (runtime.test.js, atoms-live.test.js) via node; skipped when node is absent.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
NODE = shutil.which("node") or "/home/curtis/.config/nvm/versions/node/v24.11.1/bin/node"


@pytest.mark.skipif(not Path(NODE).exists() and not shutil.which("node"),
                    reason="node not available")
def test_stream_runtime_and_atoms_live_node_suite():
    result = subprocess.run(
        [NODE, "--test", str(ROOT / "tests-js")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
