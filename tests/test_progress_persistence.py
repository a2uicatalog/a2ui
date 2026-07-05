"""Progress-persistence server logic must hold its invariants (identity
isolation, anonymous clientId fallback, per-slug scoping). Delegates to
scripts/test_progress_persistence.mjs; skipped when node is absent."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
NODE = shutil.which("node") or "/home/curtis/.config/nvm/versions/node/v24.11.1/bin/node"


@pytest.mark.skipif(not Path(NODE).exists() and not shutil.which("node"),
                    reason="node not available")
def test_progress_persistence_invariants():
    result = subprocess.run(
        [NODE, str(ROOT / "scripts" / "test_progress_persistence.mjs")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stdout + result.stderr
