"""Every published atom, emitted by renderers.a2ui_v1.emit_surface, conforms to the v1.0 schemas, and
every extension component the emitter produces validates against OUR published catalogue (the 2026-11-10
conformity sweep: 573 atoms; DEMO data where it exists, else a placeholder for the required fields)."""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import build_web_preview as b  # noqa: E402
from renderers.a2ui_capabilities import BASIC_CATALOG_IDS, ClientCapabilities  # noqa: E402
from renderers.a2ui_v1 import BASIC_COMPONENTS, emit_surface  # noqa: E402
from tests.a2ui_v1_conformance import (_REGISTRY, AGENT_TO_RENDERER, AGENT_TO_RENDERER_STRICT,  # noqa: E402
                                       _RegexAwareValidator)

CATALOG = json.load(open(os.path.join(ROOT, "public", "catalogue", "a2ui-atoms-v1.json")))
BASE = "https://a2ui.org/specification/v1_0/"
_COMPONENTS = json.loads(json.dumps(CATALOG["components"]).replace('"common_types.json#', f'"{BASE}common_types.json#'))
CAPS = ClientCapabilities(version="1.0", supported_catalog_ids=(BASIC_CATALOG_IDS["1.0"],))


def _stub(name):
    d = CATALOG["components"][name]
    out = {}
    for r in d.get("required", []):
        if r == "component":
            continue
        pr = d["properties"].get(r, {})
        ref, desc = pr.get("$ref", ""), pr.get("description", "")
        out[r] = (1 if ref.endswith("DynamicNumber") else True if ref.endswith("DynamicBoolean")
                  else [] if desc.startswith("array") else {} if desc.startswith("object") else "x")
    return out


def _ext_validator(name):
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
              "allOf": [{"$ref": BASE + "common_types.json#/$defs/ComponentCommon"}, {"$ref": f"#/components/{name}"}],
              "components": _COMPONENTS}
    return _RegexAwareValidator(schema, registry=_REGISTRY)


def test_every_atom_emits_conformant_v1_and_validates_against_our_catalogue():
    bad = []
    n_ext = 0
    for name in sorted(CATALOG["components"]):
        payload = {"title": name, "blocks": [dict(b.DEMO.get(name) or _stub(name), type=name)]}
        m = emit_surface(copy.deepcopy(payload))
        mb = emit_surface(copy.deepcopy(payload), capabilities=CAPS)
        if list(AGENT_TO_RENDERER.iter_errors(m)):
            bad.append((name, "default"))
        if list(AGENT_TO_RENDERER_STRICT.iter_errors(mb)):
            bad.append((name, "basic-degraded"))
        for c in m["createSurface"]["components"]:
            if c["component"] in BASIC_COMPONENTS:
                continue
            n_ext += 1
            if c["component"] not in CATALOG["components"] or list(_ext_validator(c["component"]).iter_errors(c)):
                bad.append((name, "extension:" + c["component"]))
    assert not bad, bad[:10]
    assert n_ext > 500


def test_tabs_atoms_with_no_tabs_still_emit_a_valid_tabs_component():
    for atom, field in (("content_tabs", "tabs"), ("tabs", "tabs"), ("hub", "subjects")):
        m = emit_surface({"title": atom, "blocks": [{"type": atom, field: []}]},
                         capabilities=CAPS)
        assert not list(AGENT_TO_RENDERER_STRICT.iter_errors(m)), atom
        tabs = [c for c in m["createSurface"]["components"] if c["component"] == "Tabs"]
        assert tabs and all(len(t["tabs"]) >= 1 for t in tabs)


def test_alias_table_matches_the_published_aliases_and_aliases_emit_canonically():
    from renderers.a2ui_v1 import ATOM_ALIASES
    spec = json.load(open(os.path.join(ROOT, "public", "spec.json")))["atoms"]
    published = {a: x["type"] for x in spec for a in x.get("aliases", [])}
    assert ATOM_ALIASES == published
    m = emit_surface({"title": "t", "blocks": [{"type": "data_table", "columns": [], "rows": []}]})
    names = {c["component"] for c in m["createSurface"]["components"]}
    assert "data_table" not in names and "data_table_sortable" in names


def test_every_component_id_is_a_uax31_identifier_and_references_resolve():
    """v1.0 requires every ComponentId to be a UAX #31 identifier (`user_card` valid, `user-card` / `1st_item` not).
    The JSON schema does not check it (ComponentId is a bare string); the stock v1.0 MessageProcessor does."""
    import regex
    rx = regex.compile(r"[\p{XID_Start}_][\p{XID_Continue}]*")
    bad = []
    for name in sorted(CATALOG["components"]):
        payload = {"title": name, "blocks": [dict(b.DEMO.get(name) or _stub(name), type=name)]}
        comps = emit_surface(copy.deepcopy(payload))["createSurface"]["components"]
        ids = {c["id"] for c in comps}
        bad += [(name, i) for i in ids if not rx.fullmatch(i)]
        for c in comps:                                  # string child refs point at emitted ids
            for ref in (c.get("children") if isinstance(c.get("children"), list) else []):
                if isinstance(ref, str) and ref not in ids:
                    bad.append((name, "dangling " + ref))
    assert not bad, bad[:10]
    # author-supplied ids are sanitised, not passed through
    m = emit_surface({"title": "t", "blocks": [{"type": "body", "id": "my-id 1", "text": "x"},
                                                 {"type": "body", "id": "1st", "text": "y"}]})
    got = [c["id"] for c in m["createSurface"]["components"] if c["id"] != "root"]
    assert got == ["my_id_1", "_1st"], got
