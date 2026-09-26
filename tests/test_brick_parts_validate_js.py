"""Pytest wrapper for tests/test_brick_parts_validate.mjs so `pytest tests/ -q` actually runs it (a bare .mjs
file is not pytest-collected on its own). See that file's own docstring for what it verifies and why."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_brick_parts_validator_matches_all_fixtures():
    proc = subprocess.run(["node", str(HERE / "test_brick_parts_validate.mjs")],
                           capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "15/15 fixtures pass" in proc.stdout, proc.stdout
