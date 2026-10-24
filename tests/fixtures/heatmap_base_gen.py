"""Writes heatmap_base_snapshot.json: what the heatmap atom rendered at base a2649e695 (before the optional variant fields),
for the payload shapes it has in the catalogue. test_heatmap.py proves those outputs are unchanged byte for byte.
Run once at the base commit: python3 tests/fixtures/heatmap_base_gen.py"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from test_heatmap import LEGACY
from test_motion_atoms import _gas_batch, _py
import re, test_motion_atoms as t
bundle = t.gen.build_bundle()
core = [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in b[:300]][0]
names = list(LEGACY)
gas = _gas_batch(core, [LEGACY[n] for n in names])
out = {n: {"py": _py(LEGACY[n]), "gas": g} for n, g in zip(names, gas)}
(Path(__file__).parent / "heatmap_base_snapshot.json").write_text(json.dumps(out, indent=0))
