"""The Apps Script parser port must stay deep-equal to the Python reference.
Delegates to scripts/test_parser_parity.mjs; skipped when node is absent."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
NODE = shutil.which("node") or "/home/curtis/.config/nvm/versions/node/v24.11.1/bin/node"


@pytest.mark.skipif(not Path(NODE).exists() and not shutil.which("node"),
                    reason="node not available")
def test_gas_port_matches_python_reference():
    result = subprocess.run(
        [NODE, str(ROOT / "scripts" / "test_parser_parity.mjs")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(not Path(NODE).exists() and not shutil.which("node"),
                    reason="node not available")
def test_roadmap_gas_port_matches_python_reference():
    result = subprocess.run(
        [NODE, str(ROOT / "scripts" / "test_roadmap_parity.mjs")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
