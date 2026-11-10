"""Our published catalogue documents validate against the upstream v1.0 catalog meta-schema
(tests/fixtures/a2ui_v1_0_spec/json/catalog_definition.json, vendored byte-identical), and an
extension component validates against its own definition once composed with ComponentCommon
the way the envelope does it."""
import json
import os

import pytest

from tests.a2ui_v1_conformance import _REGISTRY, _RegexAwareValidator

ROOT = os.path.dirname(os.path.dirname(__file__))
CATALOGUE = os.path.join(ROOT, "public", "catalogue")
FILES = ["a2ui-atoms-v1.json", "a2ui-state-v1.json", "a2ui-bricks-v1.json"]


@pytest.mark.parametrize("fname", FILES)
def test_catalog_validates_against_upstream_meta_schema(fname):
    d = json.load(open(os.path.join(CATALOGUE, fname)))
    v = _RegexAwareValidator({"$ref": "https://a2ui.org/specification/v1_0/catalog_definition.json"},
                             registry=_REGISTRY)
    errs = [e.message[:200] for e in v.iter_errors(d)]
    assert not errs, errs[:3]


def test_extension_component_validates_against_its_definition():
    d = json.load(open(os.path.join(CATALOGUE, "a2ui-atoms-v1.json")))
    # a loader resolves the relative `common_types.json#/...` refs to its bundled copy: do the same here
    base = "https://a2ui.org/specification/v1_0/"
    comps = json.loads(json.dumps(d["components"]).replace('"common_types.json#', f'"{base}common_types.json#'))
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://a2uicatalog.ai/catalogue/a2ui-atoms-v1.json",
        "allOf": [{"$ref": base + "common_types.json#/$defs/ComponentCommon"},
                  {"$ref": "#/components/glowing_stat"}],
        "components": comps,
    }
    v = _RegexAwareValidator(schema, registry=_REGISTRY)
    good = {"id": "s1", "component": "glowing_stat", "catalogId": d["$id"], "value": {"@path": "/v"}, "label": "ok"}
    assert not list(v.iter_errors(good))
    bad = dict(good, id=5)                 # envelope-level: id must be a ComponentId string
    assert list(v.iter_errors(bad))
    bad2 = dict(good, value={"path": "/v", "extra": 1})   # DynamicString: an object that is neither binding nor call
    assert list(v.iter_errors(bad2))
