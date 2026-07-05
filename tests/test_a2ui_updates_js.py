"""The client-side A2UI incremental-update applier (A2uiUpdates.html) must match
the Python reference semantics (renderers/a2ui_v1_updates). Delegates to
scripts/test_a2ui_updates_js.mjs; skipped when node is absent."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
NODE = shutil.which("node") or "/home/curtis/.config/nvm/versions/node/v24.11.1/bin/node"


@pytest.mark.skipif(not Path(NODE).exists() and not shutil.which("node"),
                    reason="node not available")
def test_client_applier_matches_python_reference():
    result = subprocess.run(
        [NODE, str(ROOT / "scripts" / "test_a2ui_updates_js.mjs")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
