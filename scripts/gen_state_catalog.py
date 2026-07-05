#!/usr/bin/env python3
"""Generate the published a2ui-state catalog from spec/a2ui-state.yaml.

Output: public/catalogue/a2ui-state-v1.json — the machine-readable behavioral
vocabulary (state primitives + expression ops + column hints), companion to the
atom catalog (a2ui-atoms-v1). A wired surface declares both catalogIds so the
agent, the validator, and the renderer reference one agreed vocabulary.

Registered under the generators class in project.yaml.
"""
import json
import os

import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..")
SRC = os.path.join(ROOT, "spec", "a2ui-state.yaml")
ACTIONS_SRC = os.path.join(ROOT, "spec", "gas-actions-v1.yaml")
OUT = os.path.join(ROOT, "public", "catalogue", "a2ui-state-v1.json")
# The renderer's authoring-prompt snapshot is GENERATED from the same sources —
# both wired-renderer copies stay in lockstep (no hand-maintained drift).
SNAPSHOT_OUTS = [
    os.path.join(ROOT, "apps-script-surface", "gas-wired-renderer", "exprs_schema_snapshot.gs"),
    os.path.join(ROOT, "apps-script-surface", "gas-wired-renderer-starter", "exprs_schema_snapshot.gs"),
]
BASE_URL = "https://a2uicatalog.ai"
BAR = "━" * 51

# A2UI v1.0 catalog-document constants (github.com/google/A2UI basic catalog).
JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
COMPONENT_COMMON_REF = (
    "https://a2ui.org/specification/v1_0/common_types.json#/$defs/ComponentCommon"
)


def _state_component(prim):
    """A2UI-v1.0 component definition for one state primitive."""
    props = {"component": {"const": prim["id"]}}
    for k, v in (prim.get("props") or {}).items():
        props[k] = {"description": str(v)}
    inner = {"type": "object", "properties": props, "required": ["component"]}
    d = {
        "type": "object",
        "description": prim.get("purpose", ""),
        "allOf": [{"$ref": COMPONENT_COMMON_REF}, inner],
        "unevaluatedProperties": False,
    }
    if prim.get("readable_fields"):
        d["x-readableFields"] = prim["readable_fields"]
    if prim.get("action_targets"):
        d["x-actionTargets"] = prim["action_targets"]
    return d


def _hint_component(hint):
    """A2UI-v1.0 component definition for a data_table column render-hint."""
    extra = hint.get("extra_props")
    props = {"component": {"const": hint["type"]}}
    if isinstance(extra, dict):
        for k, v in extra.items():
            props[k] = {"description": str(v)}
    inner = {"type": "object", "properties": props, "required": ["component"]}
    d = {
        "type": "object",
        "description": hint.get("renders", ""),
        "allOf": [{"$ref": COMPONENT_COMMON_REF}, inner],
        "unevaluatedProperties": False,
    }
    if isinstance(extra, list):
        d["x-extraProps"] = extra
    if hint.get("column_key"):
        # frozen wire sentinel the renderer matches on the column KEY
        d["x-columnKey"] = hint["column_key"]
    return d


def _op_function(op):
    """A2UI-v1.0 function definition for one derived-store op."""
    args_props = {k: {"description": str(v)} for k, v in (op.get("props") or {}).items()}
    return {
        "type": "object",
        "description": op.get("output", ""),
        "returnType": "any",
        "properties": {
            "call": {"const": op["op"]},
            "args": {"type": "object", "properties": args_props},
        },
        "required": ["call"],
        "unevaluatedProperties": False,
    }


def _compose_instructions(src):
    """Markdown design guidance carried in the catalog's `instructions` — the prose
    that can't be a custom top-level key under the strict schema. Preserves the wire
    syntax, the companion-atom-catalog relationship, and the usage note."""
    ws = src.get("wire_syntax", {})
    return "\n".join([
        "A2UI **behavioral** catalog — the companion to the visual atom catalog "
        "`a2ui-atoms-v1`. A wired surface declares `supportedCatalogIds: "
        "[a2ui-atoms-v1, a2ui-state-v1]`: atoms are the visual vocabulary, these "
        "`components` (state primitives + column render-hints) and `functions` "
        "(derived-store ops) are the behavioral one.",
        "",
        f"Wire syntax: `{ws.get('form', '#node.field')}` — the `#` prefix is required. "
        "Atoms in `layout` use `wire` to subscribe to a primitive/action output field.",
        "",
        "Full prose descriptions, examples, and wiring patterns: see "
        f"{BASE_URL}/spec.json and the a2ui-state spec.",
    ])


def main():
    with open(SRC) as f:
        src = yaml.safe_load(f)

    # A2UI-v1.0 catalog-document maps: primitives + column hints are components,
    # derived-store ops are functions. Object maps keyed by conformant identifier.
    components = {p["id"]: _state_component(p) for p in src["primitives"]}
    for h in src.get("column_hints", []):
        components[h["type"]] = _hint_component(h)
    functions = {op["op"]: _op_function(op) for op in src.get("derived_store_ops", [])}

    # A2UI v1.0 catalog documents are restricted to a STRICT top-level key set
    # ($schema,$id,title,description,catalogId,instructions,components,functions,$defs)
    # — so the prose vocabulary (wire syntax, companion-catalog note, usage) rides in
    # `instructions` (markdown for the authoring agent), NOT as custom top-level keys.
    # $id/catalogId MUST be a resolvable URI (not the bare slug) — the URL this file
    # is served at, which createSurface.catalogId / supportedCatalogIds point to.
    catalog_uri = f"{BASE_URL}/catalogue/{src['catalogId']}.json"
    catalog = {
        "$schema": JSON_SCHEMA_DRAFT,
        "$id": catalog_uri,
        "catalogId": catalog_uri,
        "title": src.get("displayName", "A2UI State Catalog"),
        "description": " ".join(src["description"].split()),
        "instructions": _compose_instructions(src),
        "components": components,   # the 8 state primitives + column render-hints
        "functions": functions,     # the derived-store ops
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(catalog, f, indent=1, ensure_ascii=False)
        f.write("\n")
    size = os.path.getsize(OUT) / 1024
    print(f"wrote public/catalogue/a2ui-state-v1.json "
          f"({len(catalog['components'])} components, "
          f"{len(catalog['functions'])} functions, {size:.1f} KB)")

    # Renderer authoring-prompt snapshot — generated from the same source(s).
    snap = _render_snapshot(src)
    for path in SNAPSHOT_OUTS:
        if os.path.exists(os.path.dirname(path)):
            with open(path, "w") as f:
                f.write(snap)
            print(f"wrote {os.path.relpath(path, ROOT)}")


def _kvline(props):
    if isinstance(props, dict):
        return ", ".join(f"{k}: {v}" for k, v in props.items())
    return str(props)


def _render_snapshot(src):
    """Compose the _EXPR_SCHEMA_SNAPSHOT text: state vocab from a2ui-state.yaml,
    actions from gas-actions-v1.yaml — each section from its canonical source."""
    L = ["// A2UI STATE & EXPR VOCABULARY SNAPSHOT — GENERATED by scripts/gen_state_catalog.py",
         "// Source: spec/a2ui-state.yaml (state/expr) + spec/gas-actions-v1.yaml (actions).",
         "// Do NOT edit by hand — edit the sources and run catalog-rebuild.",
         "var _EXPR_SCHEMA_SNAPSHOT = `", BAR, "A2UI STATE & COMPUTATION VOCABULARY", BAR,
         'Payloads have three sections: state_primitives, actions, layout.',
         'Atoms in layout use "wire" to subscribe to primitive/action output fields.',
         f'Wire syntax: "{src["wire_syntax"]["form"]}" — the # prefix is required.',
         BAR, "1. STATE PRIMITIVES  (state_primitives array)", BAR]
    for p in src["primitives"]:
        L.append(f'{p["id"]} — {p["purpose"]}')
        if p.get("props"):
            L.append("  props: " + _kvline(p["props"]))
        if p.get("readable_fields"):
            L.append("  readable fields: " + ", ".join(p["readable_fields"]))
        if p.get("action_targets"):
            L.append("  action targets: " + ", ".join(p["action_targets"]))
        if p.get("example"):
            L.append("  example: " + json.dumps(p["example"]))
    L += [BAR, "2. DERIVEDSTORE OPS  (within augment_rows add array)", BAR]
    for op in src.get("derived_store_ops", []):
        L.append(f'{op["op"]} — props: {_kvline(op.get("props", {}))} → {op.get("output","")}')
    L += [BAR, "3. COLUMN RENDER HINTS  (data_table columns array)", BAR]
    for h in src.get("column_hints", []):
        L.append(f'{h["type"]} — {h.get("renders","")}'
                 + (f'  (extra: {_kvline(h.get("extra_props"))})' if h.get("extra_props") else ""))
    L += [BAR, "4. ACTION TYPES  (actions array) — from spec/gas-actions-v1.yaml", BAR]
    actions = yaml.safe_load(open(ACTIONS_SRC))["actions"]
    for verb, spec_a in actions.items():
        desc = (spec_a or {}).get("description", "") if isinstance(spec_a, dict) else ""
        L.append(f'gas:{verb} — {" ".join(str(desc).split())}')
    L += [BAR, "5. WIRING PATTERNS", BAR]
    for w in src.get("wiring_patterns", []):
        L.append(w["title"] + ":")
        L += ["  " + ln for ln in w["body"].rstrip().splitlines()]
    L.append("`;")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
