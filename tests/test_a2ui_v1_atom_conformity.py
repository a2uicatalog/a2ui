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
