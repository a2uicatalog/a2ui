"""A2UI v1.0 CATALOG-DOCUMENT conformance — public/catalogue/*.json (Track A).

These are the documents a host loads to RESOLVE a `catalogId` carried in a
`createSurface` message. They must obey the v1.0 catalog schema: a strict
top-level key set, `$schema`/`$id`/`catalogId`, `components`/`functions` object
maps keyed by UAX#31 identifiers, and each component carrying its `component`
const. Also locks that the emitter's default catalogId dereferences to a real doc.

Reference: https://a2ui.org/specification/v1.0-a2ui/ (catalog document schema).
"""
import json
import os
import re

import pytest

from renderers.a2ui_v1 import DEFAULT_CATALOG_ID

ROOT = os.path.dirname(os.path.dirname(__file__))
CATALOGUE = os.path.join(ROOT, "public", "catalogue")

# v1.0: catalog.json is restricted to these root-level keys — STRICT, no local
# allowlist (the R2 roast caught us exempting our own extra keys; they now live
# in `instructions` where the spec puts informational prose).
ALLOWED_TOP = {"$schema", "$id", "protocolVersion", "title", "description", "catalogId",
               "instructions", "components", "functions", "$defs"}
# UAX #31: XID_Start|_, then XID_Continue; no leading digit, no hyphen/space.
UAX31 = re.compile(r"^[^\W\d]\w*$", re.UNICODE)   # \w includes _ ; [^\W\d] = letter or _

CATALOG_FILES = ["a2ui-atoms-v1.json", "a2ui-state-v1.json", "a2ui-bricks-v1.json"]


@pytest.mark.parametrize("fname", CATALOG_FILES)
def test_catalog_document_conformant(fname):
    path = os.path.join(CATALOGUE, fname)
    assert os.path.exists(path), f"{fname} not generated — run the catalog generators"
    d = json.load(open(path))

    # STRICT top-level keys per the v1.0 catalog schema
    extra = set(d) - ALLOWED_TOP
    assert not extra, f"{fname}: non-conformant top-level keys {extra}"

    assert d["$schema"], f"{fname}: missing $schema"
    assert d["$id"], f"{fname}: missing $id"
    # catalogs targeting 1.0 MUST declare it (an omitted value defaults to "0.9")
    assert d.get("protocolVersion") == "1.0", f"{fname}: protocolVersion must be '1.0'"
    assert d["catalogId"] == d["$id"], f"{fname}: catalogId must equal $id"
    # RESOLVABLE URI, not a bare token — Google's catalogId is the catalog.json URL;
    # a host dereferences createSurface.catalogId, so it must be fetchable.
    assert d["catalogId"].startswith("http"), f"{fname}: catalogId must be a URI, got {d['catalogId']!r}"

    comps = d.get("components", {})
    assert isinstance(comps, dict) and comps, f"{fname}: components must be a non-empty object map"

    for name, cdef in comps.items():
        assert UAX31.match(name), f"{fname}: component name '{name}' violates UAX#31"
        # each component must declare its own `component` const somewhere in the def
        blob = json.dumps(cdef)
        assert '"const"' in blob and name in blob, f"{fname}: {name} missing component const"

    for name in d.get("functions", {}):
        assert UAX31.match(name), f"{fname}: function name '{name}' violates UAX#31"


def test_emitter_catalogid_resolves():
    """The emitter stamps createSurface.catalogId = DEFAULT_CATALOG_ID; a document
    with that $id MUST exist — otherwise every emitted surface points at nothing."""
    ids = set()
    for fname in CATALOG_FILES:
        path = os.path.join(CATALOGUE, fname)
        if os.path.exists(path):
            ids.add(json.load(open(path))["$id"])
    assert DEFAULT_CATALOG_ID in ids, (
        f"emitter default catalogId '{DEFAULT_CATALOG_ID}' does not resolve to any "
        f"published catalog document (have: {ids})")


def test_atoms_catalog_covers_extension_passthrough():
    """An extension atom the emitter passes through (e.g. glowing_stat) must be a
    defined component in a2ui-atoms-v1 — otherwise a host can't render it."""
    d = json.load(open(os.path.join(CATALOGUE, "a2ui-atoms-v1.json")))
    assert "glowing_stat" in d["components"], "extension atom missing from resolved catalog"


# The component-definition shape of the final v1.0 Basic catalog (and upstream's VegaChart custom catalog):
# {type:object, properties:{component:{const:<name>}, ...}, required:[component, ...]}; ComponentCommon is
# composed by the ENVELOPE, not $ref'd by the catalog; standard types are referenced RELATIVELY.
COMMON_TYPES = "common_types.json#/$defs/"


@pytest.mark.parametrize("fname", CATALOG_FILES)
def test_conforms_to_google_component_pattern(fname):
    """Lock our component defs to Google's DOCUMENTED shape — not our own reading.
    This is the external-conformance guard the roast asked for."""
    d = json.load(open(os.path.join(CATALOGUE, fname)))
    for name, c in d["components"].items():
        assert c.get("type") == "object", f"{fname}:{name} not type:object"
        assert "allOf" not in c and "unevaluatedProperties" not in c, f"{fname}:{name} still composes ComponentCommon"
        assert c["properties"]["component"]["const"] == name, f"{fname}:{name} component const mismatch"
        assert "component" in c["required"], f"{fname}:{name} component not required"
        assert not set(c["properties"]) & {"id", "catalogId", "accessibility", "metadata"}, \
            f"{fname}:{name} redeclares an envelope (ComponentCommon) property"
    # any common-type $ref we emit must target the canonical common_types URL
    refs = [r for r in _all_refs(d["components"]) if "common_types.json" in r]
    for r in refs:
        assert r.startswith(COMMON_TYPES), f"{fname}: non-canonical common-type ref {r}"


@pytest.mark.parametrize("fname", ["a2ui-atoms-v1.json", "a2ui-state-v1.json", "a2ui-bricks-v1.json"])
def test_v1_catalog_rules(fname):
    """Upstream loader rules (evolution_guide 2.x): $ref only to the catalog's own #/ definitions or the
    relative common_types.json (rule 3); $defs.anyComponent/anyFunction present and covering every
    definition; functions use the `@call` discriminator and declare a returnType."""
    d = json.load(open(os.path.join(CATALOGUE, fname)))
    bad = [r for r in _all_refs({k: d.get(k) for k in ("components", "functions", "$defs")})
           if not (r.startswith("#/") or r.startswith("common_types.json#/"))]
    assert not bad, f"{fname}: {len(bad)} non-relative/foreign $refs, e.g. {sorted(set(bad))[:3]}"
    any_c = {x["$ref"].rsplit("/", 1)[1] for x in d["$defs"]["anyComponent"]["oneOf"]}
    assert any_c == set(d["components"]), f"{fname}: anyComponent does not list exactly the components"
    fns = d.get("functions", {})
    if fns:
        any_f = {x["$ref"].rsplit("/", 1)[1] for x in d["$defs"]["anyFunction"]["oneOf"]}
        assert any_f == set(fns)
    else:
        assert d["$defs"]["anyFunction"] == {"not": {}}
    for n, f in fns.items():
        assert f["properties"]["@call"]["const"] == n and "@call" in f["required"], f"{fname}:{n} not @call-shaped"
        assert f.get("returnType"), f"{fname}:{n} missing returnType"


def test_bindable_props_are_typed():
    """DynamicString must actually APPEAR — the roast's finding was that it was
    entirely absent, so a host couldn't tell any prop accepted a {path} binding."""
    d = json.load(open(os.path.join(CATALOGUE, "a2ui-atoms-v1.json")))
    blob = json.dumps(d["components"])
    assert COMMON_TYPES + "DynamicString" in blob, "no DynamicString-typed props — bindability invisible to hosts"


def _all_refs(obj):
    out = []
    if isinstance(obj, dict):
        if isinstance(obj.get("$ref"), str):
            out.append(obj["$ref"])
        for v in obj.values():
            out.extend(_all_refs(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_all_refs(v))
    return out
