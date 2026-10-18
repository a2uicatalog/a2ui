"""The published-atom count is quoted by hand in a few public files (the MCP server card, the listing text, SKILL.md, the MCP README).
It went stale once (474 while 548 were published), and registries such as Smithery and MCP Market copy those files.
scripts/gen_atom_count.py owns the list of claims and rewrites them; deploy.yml runs it with --check. These tests keep the generator honest."""
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "gen_atom_count.py"
spec = importlib.util.spec_from_file_location("gen_atom_count", SCRIPT)
gac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gac)


def test_quoted_atom_counts_match_the_published_catalogue():
    r = subprocess.run([sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_every_claim_still_matches_its_pattern():
    # stale() exits (SystemExit) if a file no longer contains a claim, so a reworded sentence cannot silently escape the check
    assert gac.stale(gac.published_count()) == []


def test_check_mode_reports_a_wrong_number_without_writing(tmp_path, monkeypatch):
    card = tmp_path / "card.json"
    card.write_text('{"description": "1 typed UI atoms"}')
    monkeypatch.setattr(gac, "ROOT", tmp_path)
    monkeypatch.setattr(gac, "CLAIMS", [("card.json", r"(\d+) typed UI atoms")])
    assert gac.stale(548) == [("card.json", r"(\d+) typed UI atoms", ["1"])]
    assert card.read_text() == '{"description": "1 typed UI atoms"}'
