"""ChildList TEMPLATE variant decode — atoms_v1_decode.gs (Phase 2).

The Phase-1 shim resolved only the array variant; these tests lock the
template variant ({componentId, path}) against the UPSTREAM spec semantics
(spec/a2ui-v1.0-upstream, a2ui-private): JSON Pointer resolution, Child Scope
relative paths, @index, DataBinding properties, progressive-render grace —
executed through the REAL bundle core in Node, the same decoder both surfaces
ship (GAS by .gs concatenation, MCP Apps by bundle concatenation).
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    core = [b for b in blocks if "a2ui-core" in b[:300]]
    assert core, "a2ui-core script block missing"
    return core[0]


def _decode(core_js, surface, also_render=False):
    """Run _rehydrateV1Surface (and optionally renderAtoms) in Node."""
    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "d.js"
        driver.write_text(
            "global.window = global;\n" + core_js + f"""
var surface = {json.dumps(surface)};
var out = _rehydrateV1Surface(surface);
var html = {'renderAtoms(out.blocks, {theme: out.theme})' if also_render else "''"};
console.log(JSON.stringify({{out: out, html: html}}));
""")
        proc = subprocess.run(["node", str(driver)], capture_output=True,
                              text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr[-1000:]
        return json.loads(proc.stdout)


# The spec's own worked example ("Data model representation: binding, scope"),
# verbatim shape: template over /employees, relative `name`, absolute /company.
SPEC_EMPLOYEES = {
    "dataModel": {
        "company": "Acme Corp",
        "employees": [{"name": "Alice", "role": "Engineer"},
                      {"name": "Bob", "role": "Designer"}],
    },
    "surfaceProperties": {"title": "Spec example", "theme": "light"},
    "components": [
        {"id": "root", "component": "Column", "children": ["employee_list"]},
        {"id": "employee_list", "component": "Column",
         "children": {"componentId": "employee_card_template", "path": "/employees"}},
        {"id": "employee_card_template", "component": "Column",
         "children": ["name_text", "company_text"]},
        {"id": "name_text", "component": "Text", "text": {"path": "name"}},
        {"id": "company_text", "component": "Text", "text": {"path": "/company"}},
    ],
}


def test_spec_employee_example_decodes(core_js):
    r = _decode(core_js, SPEC_EMPLOYEES, also_render=True)
    lst = r["out"]["blocks"][0]
    cards = lst["blocks"]
    assert len(cards) == 2, "one instantiation per data item"
    assert cards[0]["blocks"][0]["text"] == "Alice"      # relative -> /employees/0/name
    assert cards[1]["blocks"][0]["text"] == "Bob"        # relative -> /employees/1/name
    assert cards[0]["blocks"][1]["text"] == "Acme Corp"  # absolute wins inside scope
    assert cards[1]["blocks"][1]["text"] == "Acme Corp"
    # end to end through the real standard-component renderers
    for needle in ("Alice", "Bob", "Acme Corp"):
        assert needle in r["html"]


def test_index_function_with_offset(core_js):
    surface = {
        "dataModel": {"players": [{"n": "Ana"}, {"n": "Ben"}, {"n": "Cy"}]},
        "components": [
            {"id": "root", "component": "Column",
             "children": {"componentId": "row", "path": "/players"}},
            {"id": "row", "component": "Text",
             "text": {"path": "n"},
             "badge": {"call": "@index", "args": {"offset": 1}}},
        ],
    }
    rows = _decode(core_js, surface)["out"]["blocks"]
    assert [b["badge"] for b in rows] == [1, 2, 3]
    assert [b["text"] for b in rows] == ["Ana", "Ben", "Cy"]


def test_nested_templates_scope_correctly(core_js):
    """Template inside a template: inner relative path resolves against the
    INNER scope (rounds/N/matches/M), the spec's nested Collection case."""
    surface = {
        "dataModel": {"rounds": [
            {"label": "R1", "matches": [{"a": "P1 & P8"}, {"a": "P3 & P6"}]},
            {"label": "R2", "matches": [{"a": "P1 & P2"}]},
        ]},
        "components": [
            {"id": "root", "component": "Column",
             "children": {"componentId": "round", "path": "/rounds"}},
            {"id": "round", "component": "Column",
             "title": {"path": "label"},
             "children": {"componentId": "match", "path": "matches"}},
            {"id": "match", "component": "Text", "text": {"path": "a"}},
        ],
    }
    rounds = _decode(core_js, surface)["out"]["blocks"]
    assert rounds[0]["title"] == "R1" and rounds[1]["title"] == "R2"
    assert [m["text"] for m in rounds[0]["blocks"]] == ["P1 & P8", "P3 & P6"]
    assert [m["text"] for m in rounds[1]["blocks"]] == ["P1 & P2"]


def test_missing_data_renders_empty_not_throw(core_js):
    """Progressive rendering: path not (yet) in the data model -> empty
    children, undefined bindings -> '' — per the spec's grace note."""
    surface = {
        "components": [
            {"id": "root", "component": "Column", "children": ["lst", "txt"]},
            {"id": "lst", "component": "Column",
             "children": {"componentId": "item", "path": "/not/here"}},
            {"id": "item", "component": "Text", "text": {"path": "x"}},
            {"id": "txt", "component": "Text", "text": {"path": "/also/missing"}},
        ],
    }
    out = _decode(core_js, surface)["out"]
    assert out["blocks"][0]["blocks"] == []
    assert out["blocks"][1]["text"] == ""


def test_template_reinstantiation_is_not_a_cycle(core_js):
    """Phase-1's shared seen-map made a template's SECOND instantiation
    resolve to null. The guard must be path-based: N instances legal,
    a component referencing itself still blocked."""
    surface = {
        "dataModel": {"xs": [{"v": "one"}, {"v": "two"}, {"v": "three"}]},
        "components": [
            {"id": "root", "component": "Column",
             "children": {"componentId": "t", "path": "/xs"}},
            {"id": "t", "component": "Text", "text": {"path": "v"}},
        ],
    }
    assert len(_decode(core_js, surface)["out"]["blocks"]) == 3

    cyclic = {"components": [
        {"id": "root", "component": "Column", "children": ["root"]},
    ]}
    assert _decode(core_js, cyclic)["out"]["blocks"] == []  # guarded, no hang


def test_strict_upstream_properties_nesting_decodes(core_js):
    """The estate's emitters flatten properties; STRICT upstream payloads nest
    them under `properties`. Both shapes must decode identically."""
    surface = {
        "dataModel": {"user": {"name": "Curtis"}},
        "components": [
            {"id": "root", "component": "Column", "children": ["greet"]},
            {"id": "greet", "component": "Text",
             "properties": {"text": {"path": "/user/name"}}},
        ],
    }
    assert _decode(core_js, surface)["out"]["blocks"][0]["text"] == "Curtis"


def test_legacy_array_variant_unchanged(core_js):
    """Phase-1 behavior regression: array-variant surfaces (no templates, no
    dataModel) decode exactly as before, including tabs child refs."""
    surface = {
        "surfaceProperties": {"title": "T", "theme": "dark", "hub_slug": "t-hub"},
        "components": [
            {"id": "root", "component": "Column", "children": ["tabs1"]},
            {"id": "tabs1", "component": "Tabs",
             "tabs": [{"label": "A", "child": "a"}, {"label": "B", "child": "b"}]},
            {"id": "a", "component": "Text", "text": "aye"},
            {"id": "b", "component": "Text", "text": "bee"},
        ],
    }
    out = _decode(core_js, surface)["out"]
    assert out["theme"] == "dark" and out["hub_slug"] == "t-hub"
    tabs = out["blocks"][0]["tabs"]
    assert tabs[0]["label"] == "A" and tabs[0]["blocks"][0]["text"] == "aye"
    assert tabs[1]["blocks"][0]["text"] == "bee"


def test_americano_acceptance_renders_catalogue_atoms(core_js):
    """The gap-analysis acceptance case: player grid + per-round matches as
    templates over the data model, rendered through REAL catalogue atoms
    (heading + body), end to end. Schedule-as-data, names bound per item."""
    surface = {
        "dataModel": {
            "tournament": {"title": "Club Night"},
            "players": [{"name": "Ana"}, {"name": "Ben"},
                        {"name": "Caro"}, {"name": "Dan"}],
            "rounds": [
                {"label": "Round 1",
                 "matches": [{"teams": "Ana & Dan vs Ben & Caro"}]},
                {"label": "Round 2",
                 "matches": [{"teams": "Ana & Ben vs Caro & Dan"}]},
            ],
        },
        "surfaceProperties": {"title": "Americano", "theme": "light"},
        "components": [
            {"id": "root", "component": "Column",
             "children": ["title", "roster", "sched"]},
            {"id": "title", "component": "heading",
             "text": {"path": "/tournament/title"}},
            {"id": "roster", "component": "Column",
             "children": {"componentId": "player_row", "path": "/players"}},
            {"id": "player_row", "component": "body", "text": {"path": "name"}},
            {"id": "sched", "component": "Column",
             "children": {"componentId": "round_block", "path": "/rounds"}},
            {"id": "round_block", "component": "Column",
             "children": ["round_head", "round_matches"]},
            {"id": "round_head", "component": "subheading", "text": {"path": "label"}},
            {"id": "round_matches", "component": "Column",
             "children": {"componentId": "match_row", "path": "matches"}},
            {"id": "match_row", "component": "body", "text": {"path": "teams"}},
        ],
    }
    r = _decode(core_js, surface, also_render=True)
    for needle in ("Club Night", "Ana", "Caro", "Round 2",
                   "Ana &amp; Ben vs Caro &amp; Dan"):
        assert needle in r["html"], f"missing from rendered HTML: {needle}"
