"""Discovery documents must dereference — every URL they publish must
exist in the public/ deploy artifact. See scripts/check_catalog_links.py."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "check_catalog_links.py"


def test_discovery_urls_dereference():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr or result.stdout
