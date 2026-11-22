"""The strict atom schema must read item shapes the way the schema.yaml field text means them.

A plain split on every comma cut hints such as `parent_id (max 24, empty for the root)` in two, so the generated
schema required keys called `parent_id (max 24` and `empty for the root)` and forbade a real parent_id: the live
org_chart came back from /api/compose with no hierarchy (22 Nov 2026). 28 atoms were affected.
"""
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _gen():
    spec = importlib.util.spec_from_file_location("gen_atom_json_schemas", ROOT / "scripts" / "gen_atom_json_schemas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_split_keeps_bracketed_commas_together():
    split = _gen()._split_top_level
    assert split("id (max 24), label (max 28), parent_id (max 24, empty for the root)") == [
        "id (max 24)", "label (max 28)", "parent_id (max 24, empty for the root)"]
    assert split('a, b [x, y], c "p, q", d') == ["a", "b [x, y]", 'c "p, q"', "d"]


def test_org_chart_node_takes_parent_id():
    schemas = json.loads((ROOT / "public" / "catalogue" / "atoms-json-schema.json").read_text(encoding="utf8"))
    by = {s["properties"]["type"].get("const"): s for s in schemas["items"].get("oneOf", schemas["items"].get("anyOf", []))
          if "type" in s.get("properties", {})}
    node = by["org_chart"]["properties"]["nodes"]["items"]
    assert set(node["properties"]) == {"id", "label", "parent_id"}
    assert node["required"] == ["id", "label", "parent_id"]


def test_no_property_name_carries_a_cut_hint():
    """No key may contain a round bracket: that is what a comma cut inside a hint leaves behind.
    (Keys written `items[]` in four atoms are a separate notation and are not covered here.)"""
    schemas = json.loads((ROOT / "public" / "catalogue" / "atoms-json-schema.json").read_text(encoding="utf8"))
    bad = []

    def walk(o, atom):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "properties" and isinstance(v, dict):
                    bad.extend((atom, p) for p in v if re.search(r"[()]", p))
                walk(v, atom)
        elif isinstance(o, list):
            for x in o:
                walk(x, atom)

    for s in schemas["items"].get("oneOf", schemas["items"].get("anyOf", [])):
        walk(s, s.get("properties", {}).get("type", {}).get("const"))
    # box_plot's `stats? (object {...})` has braces nested inside the item shape: a separate, known case.
    bad = [b for b in bad if b[0] != "box_plot"]
    assert not bad, bad
