"""Validate EMITTED payloads against the PUBLISHED catalog — the closed loop.

Both prior roast rounds shared one root cause: every test checked either
emitter→spec-shape or catalog→spec-shape, never emitted-payload→published-catalog.
That gap hid the 215 false-required fields (a catalog that rejected its own
payloads under strict validation). This test closes the loop structurally:

  - every emitted component is either a standard A2UI basic-catalog component or
    a defined component in the published a2ui-atoms-v1 catalog;
  - every `required` field the catalog declares for a component is PRESENT on
    the emitted instance (requiredness truthfulness — the regression guard);
  - the catalog's required arrays stay opt-in (no mass false-required relapse).

Full JSON-Schema validation (DynamicString/ComponentCommon $refs) needs a
vendored common_types.json — deferred, tracked in the whole-system roast.
"""
import json
import glob
import os

from renderers.a2ui_v1 import emit_surface

ROOT = os.path.dirname(os.path.dirname(__file__))
CATALOG = os.path.join(ROOT, "public", "catalogue", "a2ui-atoms-v1.json")

# A2UI v1.0 basic-catalog components (a2ui.org basic catalog) — valid on any host,
# not defined in OUR catalog. Emitted structural nodes may use these freely.
BASIC = {"Text", "Image", "Icon", "Video", "AudioPlayer", "Row", "Column", "List",
         "Card", "Tabs", "Divider", "Modal", "Button", "CheckBox", "TextField",
         "DateTimeInput", "ChoicePicker", "Slider"}


def _catalog():
    return json.load(open(CATALOG))["components"]


def _emitted_surfaces(limit=6):
    """Real payloads + the synthetic sample from the emitter test suite."""
    from tests.test_a2ui_v1 import SAMPLE
    out = [emit_surface(SAMPLE)]
    for path in sorted(glob.glob(os.path.join(ROOT, "payloads", "*.json"))):
        try:
            d = json.load(open(path))
        except Exception:
            continue
        if isinstance(d, dict) and isinstance(d.get("blocks"), list) and d["blocks"]:
            out.append(emit_surface(d))
            if len(out) >= limit:
                break
    return out


def test_every_emitted_component_is_defined_somewhere():
    comps = _catalog()
    unknown = set()
    for msg in _emitted_surfaces():
        for c in msg["createSurface"]["components"]:
            name = c["component"]
            if name not in BASIC and name not in comps:
                unknown.add(name)
    # preview-stage atoms are repo-only by policy — they may legitimately be
    # absent from the published catalog; anything else unknown is a hole.
    import yaml
    atoms = yaml.safe_load(open(os.path.join(ROOT, "atoms", "schema.yaml")))["blocks"]
    preview = {a["type"] for a in atoms if a.get("stage") == "preview"}
    truly_unknown = unknown - preview
    assert not truly_unknown, f"emitted components with no catalog definition: {truly_unknown}"


def test_catalog_required_fields_hold_on_emitted_payloads():
    """THE regression guard: for every emitted component defined in the catalog,
    every field its catalog entry marks `required` must actually be present.
    Under the old required-unless-'optional' rule this fails ~immediately
    (sparkline.color etc.); under opt-in requiredness it must always hold."""
    comps = _catalog()
    violations = []
    for msg in _emitted_surfaces():
        for c in msg["createSurface"]["components"]:
            cdef = comps.get(c["component"])
            if not cdef:
                continue
            inner = cdef["allOf"][1]
            for req in inner.get("required", []):
                if req not in c:
                    violations.append(f"{c['component']}.{req} (component id {c['id']})")
    assert not violations, (
        "catalog marks fields required that emitted payloads legitimately omit "
        f"(false-required relapse): {violations[:10]}")


def test_requiredness_is_opt_in_not_heuristic():
    """The catalog-wide required count must stay near the explicitly-marked set
    (~105 of 1865 fields), never balloon back toward required-by-default."""
    comps = _catalog()
    total_required = sum(
        len(c["allOf"][1].get("required", [])) - 1        # minus 'component' itself
        for c in comps.values())
    assert total_required < 300, (
        f"{total_required} required fields across the catalog — smells like the "
        "required-by-default heuristic came back")
