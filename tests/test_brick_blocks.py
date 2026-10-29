"""The brick block catalogue (a2ui-bricks-v1, 2026-10-29): the two engine atoms (motion_bricks, brick_build_3d) plus the
pre-composed block_robot and block_rocket, which fill the motion_bricks canvas with a fixed hand-built brick list.

Held together here: the list in atoms_studio.gs (what renders), the list in atoms/brick-blocks.yaml (what a reviewer reads),
the existing brick validator's verdict on it (reported, not hidden), the schema typing (arrays, booleans, numbers as such),
the pack, the Python twin, and an offline Express compile of a hand-written reply against the four-atom slice."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from renderers import brick_validate as bv
from renderers.web_article import _RENDERERS

ROOT = Path(__file__).parent.parent
GS = (ROOT / "apps-script-surface/gas-wired-renderer/atoms_studio.gs").read_text()
BOM = yaml.safe_load((ROOT / "atoms/brick-blocks.yaml").read_text())
SCHEMA = {b["type"]: b for b in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"] if isinstance(b, dict) and b.get("type")}
SLICE = ["motion_bricks", "brick_build_3d", "block_robot", "block_rocket"]
EXPECT = {"block_robot": (10, 5), "block_rocket": (9, 3)}   # bricks; side-mounted bricks the stud-only anchor check cannot connect
EXPRESS = Path("/mnt/hdd2/work/express-prep")


def _gs_lists():
    m = re.search(r"^var _BLOCK_BRICKS = (\{.*?^\});", GS, re.S | re.M)
    return json.loads(m.group(1))


def test_lists_agree_between_renderer_and_bill_of_materials():
    gs = _gs_lists()
    assert BOM["catalogue"] == "a2ui-bricks-v1" and BOM["engines"] == ["motion_bricks", "brick_build_3d"]
    for blk in BOM["blocks"]:
        assert blk["bricks"] == gs[blk["id"]] and len(blk["bricks"]) == blk["bricks_count"] == EXPECT[blk["id"]][0]
        assert all(len(b) == 7 for b in blk["bricks"])


def test_validator_verdict_is_reported_honestly():
    for name, (_, floating) in EXPECT.items():
        bricks = [dict(zip("xyzwdhc", b)) for b in _gs_lists()[name]]
        r = bv.validate(bv.normalise(bricks)["bricks"])
        by = {c["id"]: c for c in r["checks"]}
        assert by["collisions"]["status"] == "pass"
        assert by["anchored"]["status"] == "fail" and r["floating"] == floating
        assert f"{floating} bricks not connected" in by["anchored"]["detail"]
        assert f"{floating} bricks not connected" in SCHEMA[name]["notes"]


def test_block_renders_as_the_canvas_with_its_list_filled_in():
    uid = re.compile(r"mt-[a-z0-9]{6}")
    for name in EXPECT:
        got = _RENDERERS[name]({"angle": -24, "text": "IGNORED", "shape": "torus", "fill": True})
        want = _RENDERERS["motion_bricks"]({"bricks": _gs_lists()[name], "angle": -24, "fill": True})
        assert uid.sub("mt-X", got) == uid.sub("mt-X", want)
        assert "IGNORED" not in got


def test_schema_types_and_placement():
    packs = yaml.safe_load((ROOT / "atoms/atom-packs.yaml").read_text())
    assert packs["a2ui-bricks-v1"] == SLICE
    assert not any(a in packs["a2ui-effects-v1"] for a in SLICE)
    for name in EXPECT:
        b = SCHEMA[name]
        assert b.get("stage", "stable") == "stable" and b["routing_text"] and len(b["intent_phrases"]) == 3
        assert b["surfaces"]["works_on"] and b["surfaces"]["degraded_on"] and b["surfaces"]["incompatible_on"]
        f = b["fields"]
        assert f["motion"].startswith("object") and f["fill"].startswith("boolean")
        assert all(f[k].startswith("number") for k in ("angle", "elevation", "turns"))
        assert "Not affiliated with or endorsed by the LEGO Group" in b["description"]
    assert SCHEMA["motion_bricks"]["fields"]["fill"].startswith("boolean")
    assert SCHEMA["motion_bricks"]["fields"]["bricks"].startswith("array")
    assert SCHEMA["brick_build_3d"]["fields"]["partsModel"].startswith("array")
    for atom in ("motion_bricks", "brick_build_3d"):
        assert SCHEMA[atom]["fields"]["base"].startswith("string")   # "none" | "#rrggbb" read as a two-value enum


_EXPRESS_SCRIPT = r'''
import json, sys
sys.path.insert(0, %(express)r)
import build_catalog
from a2ui.processor import A2uiGenerator, CatalogConfig
from a2ui.inference_formats import ExpressFormatFactory
out = sys.argv[1]
build_catalog.BASIC = {}
build_catalog.main(sys.argv[2], out, set(%(slice)r))
cat = CatalogConfig.from_path(out); cid = json.load(open(out))["catalogId"]
p = A2uiGenerator([cat], inference_format_factory=ExpressFormatFactory()).create_processor({"v0.9": {"supportedCatalogIds": [cid]}})
def run(reply):
    try:
        parts = p.parse_response(reply)
        comps = [c for x in parts if not isinstance(x, str) for m in x.a2ui if hasattr(m, "update_components") for c in m.update_components.components]
        return {"ok": True, "components": comps}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)}
print(json.dumps({
  "good": run('<a2ui>\nsurface("s")\nroot=block_robot(motion={order:"index", flight:1, window:9}, angle=-24, fill=false, label="Brick robot")\n</a2ui>'),
  "rocket": run('<a2ui>\nsurface("s")\nroot=block_rocket(_, -20, 26, 1, "studio", "none", "1:1", true, "Brick rocket")\n</a2ui>'),
  "outside": run('<a2ui>\nsurface("s")\nroot=badge("hello")\n</a2ui>'),
}))
'''


@pytest.mark.skipif(not (EXPRESS / ".venv/bin/python").exists() or not (EXPRESS / "upstream").exists(),
                    reason="the A2UI Express harness (/mnt/hdd2/work/express-prep) is not on this machine")
def test_express_reply_compiles_against_the_block_catalogue_slice(tmp_path):
    script = tmp_path / "express_check.py"
    script.write_text(_EXPRESS_SCRIPT % {"express": str(EXPRESS), "slice": SLICE})
    r = subprocess.run([str(EXPRESS / ".venv/bin/python"), str(script), str(tmp_path / "bricks.json"), str(ROOT / "atoms/schema.yaml")],
                       cwd=str(EXPRESS), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-800:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    good = out["good"]["components"][0]
    assert out["good"]["ok"] and good["component"] == "block_robot"
    assert good["motion"] == {"order": "index", "flight": 1, "window": 9} and good["angle"] == -24 and good["fill"] is False
    rk = out["rocket"]["components"][0]
    assert rk["component"] == "block_rocket" and rk["fill"] is True and rk["ratio"] == "1:1"
    assert not out["outside"]["ok"] and "Unknown component 'badge'" in out["outside"]["error"]
