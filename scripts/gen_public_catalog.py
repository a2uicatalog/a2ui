#!/usr/bin/env python3
"""
Generate the machine-readable catalog artifacts served from public/.

Outputs:
  public/spec.json                    — full atom catalog (the URL ai-catalog.json points at)
  public/atoms/index.json             — compact index: type + compact_description + surfaces
  public/runbooks/index.json          — runbook library compiled from runbooks/*.yaml
  public/catalogue/gdm-v0.2.json      — stable URI copy of the GDM component catalog
  public/catalogue/a2ui-atoms-v1.json — A2UI-v1.0-conformant catalog document that
                                        RESOLVES the catalogId the emitter carries
                                        (createSurface.catalogId == "a2ui-atoms-v1"):
                                        a JSON-Schema doc ($schema/$id) whose `components`
                                        object map defines every stable atom as an A2UI
                                        component. Schema per a2ui.org/specification/v1.0-a2ui/.

Run:
  python3 scripts/gen_public_catalog.py
"""
import json
import os
import shutil
import sys

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCHEMA = os.path.join(ROOT, "atoms", "schema.yaml")
RUNBOOKS_DIR = os.path.join(ROOT, "runbooks")
GDM_SPEC = os.path.join(ROOT, "spec", "gdm-v0.2.json")
PUBLIC = os.path.join(ROOT, "public")

BASE_URL = "https://a2uicatalog.ai"

# A2UI v1.0 catalog-document constants (github.com/google/A2UI,
# specification/v1_0/catalogs/basic/catalog.json). A catalog document is a
# JSON-Schema file: components/functions are declared as object maps directly
# under the top-level `components`/`functions` keys, each component carrying a
# `component: {const: <name>}` discriminator and referencing ComponentCommon.
JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
_COMMON_TYPES = "https://a2ui.org/specification/v1_0/common_types.json#/$defs/"
COMPONENT_COMMON_REF = _COMMON_TYPES + "ComponentCommon"
# typed, BINDABLE property refs — v1.0 conformance: a host learns which props accept
# a `{path}` data-binding from these (Google's basic catalog types every prop this way).
DYNAMIC_STRING_REF = _COMMON_TYPES + "DynamicString"
CHILD_LIST_REF = _COMMON_TYPES + "ChildList"
ATOMS_CATALOG_ID = "a2ui-atoms-v1"                                   # slug / filename
# The catalogId/$id MUST be a resolvable URI (Google's is the full catalog.json URL);
# a bare token can't be dereferenced. This is what createSurface.catalogId points at.
ATOMS_CATALOG_URI = f"{BASE_URL}/catalogue/{ATOMS_CATALOG_ID}.json"

# field-name hints for component-child lists (-> ChildList of ComponentId refs)
_CHILD_FIELDS = {"blocks", "children", "items", "tabs", "slides", "panes", "content"}


def _prop_schema(fname, fspec):
    """Type a component property. Bindable display strings -> DynamicString; child
    block-lists -> ChildList; everything else keeps a loose json type + description.
    Conservative: types the common bindable cases so a host/validator isn't blind to
    them, without over-asserting a precise type for every prose field hint."""
    s = str(fspec)
    low = s.lower()
    if fname in _CHILD_FIELDS or ("array" in low and any(w in low for w in
            ("block", "component", "atom", "slide"))):
        return {"$ref": CHILD_LIST_REF, "description": s}
    if low.startswith("string") and "array" not in low:            # bindable display string
        return {"$ref": DYNAMIC_STRING_REF, "description": s}
    prop = {"description": s}
    jt = _json_type(fspec)
    if jt:
        prop["type"] = jt
    return prop


def load_blocks():
    with open(SCHEMA) as f:
        blocks = yaml.safe_load(f)["blocks"]
    # Staging: only stable atoms are published; preview stays repo-only.
    # Runbook validation still checks against ALL types (renderer reality).
    stable = [b for b in blocks if b.get("stage", "stable") == "stable"]
    return stable, {b["type"] for b in blocks}


def write_json(rel_path, payload):
    path = os.path.join(PUBLIC, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
        f.write("\n")
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✅ public/{rel_path} ({size_kb:.1f} KB)")


def gen_spec(blocks):
    atoms = []
    for b in blocks:
        entry = {
            "type": b["type"],
            "description": b.get("description", ""),
            "compact_description": b.get("compact_description", ""),
            "surfaces": b.get("surfaces", {}),
            "fields": b.get("fields", {}),
            "source": b.get("source", {}),
        }
        if b.get("source_inspiration"):
            entry["source_inspiration"] = b["source_inspiration"]
        if b.get("aliases"):
            entry["aliases"] = b["aliases"]
        atoms.append(entry)
    return {
        "catalogId": "a2ui-atoms-v1",
        "displayName": "A2UI Multi-Surface Renderer",
        "type": "application/vnd.a2ui.renderer+json",
        "atomCount": len(atoms),
        "compactIndex": f"{BASE_URL}/atoms/index.json",
        "runbooks": f"{BASE_URL}/runbooks/index.json",
        "trainingPrompt": f"{BASE_URL}/prompts/training-md-gem.md",
        "builderPrompt": f"{BASE_URL}/prompts/a2ui-builder-gem.md",
        "thirdPartyNotices": f"{BASE_URL}/THIRD-PARTY-NOTICES.md",
        "attributionModel": ("Three tiers: 'source' credits derived or adapted work "
                             "(vendor name + license); 'source_inspiration' credits a "
                             "visual/pattern origin with no code derivation; atoms with "
                             "source a2uicatalog and no inspiration field are original. "
                             "Full notices and per-vendor manifests at /THIRD-PARTY-NOTICES.md "
                             "and /vendors/."),
        "atoms": atoms,
    }


def gen_compact_index(blocks):
    return {
        "catalogId": "a2ui-atoms-v1",
        "atomCount": len(blocks),
        "fullSpec": f"{BASE_URL}/spec.json",
        "atoms": [
            {
                "type": b["type"],
                "compact": b.get("compact_description", ""),
                "surfaces": b.get("surfaces", {}).get("works_on", []),
                **({"aliases": b["aliases"]} if b.get("aliases") else {}),
            }
            for b in blocks
        ],
    }


def _json_type(field_spec: str):
    """Best-effort map a schema.yaml field type-string to a JSON-Schema `type`.
    Returns None when no confident mapping exists (the property then carries only
    its description, still valid under the component's unevaluatedProperties)."""
    s = str(field_spec).strip().lower()
    if s.startswith(("string", "url", "markdown", "text", "color", "colour",
                     "hex", "enum", "icon", "date", "email", "html", "css")):
        return "string"
    if s.startswith(("integer", "number", "int", "float", "percent", "ms")):
        return "number"
    if s.startswith("bool"):
        return "boolean"
    if s.startswith(("array", "list", "[")) or "array of" in s or "list of" in s:
        return "array"
    if s.startswith(("object", "dict", "map", "{")):
        return "object"
    return None


def _component_def(atom: dict) -> dict:
    """One A2UI-v1.0 component definition for an atom: a JSON-Schema object
    with the `component: {const: <type>}` discriminator + a property per field,
    composed over the shared ComponentCommon (id/children/etc.)."""
    props = {"component": {"const": atom["type"]}}
    required = ["component"]
    for fname, fspec in (atom.get("fields") or {}).items():
        props[fname] = _prop_schema(fname, fspec)
        # requiredness is OPT-IN: only fields whose spec explicitly says "required".
        # The old rule (required unless the word "optional" appeared) marked 215
        # defaulted/example fields required — strict validators then REJECTED real
        # payloads (whole-system roast, 2026-07-05). False-accept beats false-reject
        # for a catalog; the durable fix is structured field metadata in schema.yaml.
        if "required" in str(fspec).lower():
            required.append(fname)
    inner = {"type": "object", "properties": props, "required": required}
    definition = {
        "type": "object",
        "description": atom.get("description", ""),
        "allOf": [{"$ref": COMPONENT_COMMON_REF}, inner],
        "unevaluatedProperties": False,
    }
    surfaces = atom.get("surfaces", {}).get("works_on")
    if surfaces:
        definition["x-surfaces"] = surfaces
    if atom.get("aliases"):
        definition["x-aliases"] = atom["aliases"]
    return definition


def gen_atoms_catalog(blocks):
    """The A2UI-v1.0 catalog document that RESOLVES the emitter's catalogId.

    createSurface carries catalogId "a2ui-atoms-v1"; a host loads THIS document
    at that id to learn how to render the catalog's components. Conforms to the
    v1.0 catalog schema (github.com/google/A2UI basic catalog): $schema + $id,
    `components` object map keyed by component name, each a JSON-Schema definition.
    """
    components = {b["type"]: _component_def(b) for b in blocks}
    return {
        "$schema": JSON_SCHEMA_DRAFT,
        "$id": ATOMS_CATALOG_URI,
        "catalogId": ATOMS_CATALOG_URI,
        "title": "A2UI Atoms Catalog",
        "description": ("The A2UI multi-surface atom vocabulary as an A2UI-v1.0 "
                        "catalog document. Each stable atom is a component; a host "
                        "resolves createSurface.catalogId (this file's URL) to it."),
        # v1.0 restricts catalog top-level keys to the strict set — informational
        # pointers (canonical URI, full spec, count) ride in `instructions`.
        "instructions": ("Every key under `components` is a valid `component` value "
                         f"({len(components)} components). Compose layouts with "
                         "Column/Row containers; each component's fields are its "
                         f"properties. Canonical URI: {ATOMS_CATALOG_URI} — full prose "
                         f"spec (descriptions, surfaces, attribution): {BASE_URL}/spec.json"),
        "components": components,
        "functions": {},
    }


def gen_runbooks_index(known_types):
    runbooks = []
    if not os.path.isdir(RUNBOOKS_DIR):
        return {"runbooks": []}
    for name in sorted(os.listdir(RUNBOOKS_DIR)):
        if not name.endswith((".yaml", ".yml")):
            continue
        with open(os.path.join(RUNBOOKS_DIR, name)) as f:
            rb = yaml.safe_load(f)
        unknown = [s["atom"] for s in rb.get("sequence", []) if s.get("atom") not in known_types]
        # stampable runbooks (kind: stampable) declare their BOM in `composition`
        # instead of `sequence` — validate those atom refs with the same check.
        if rb.get("kind") == "stampable":
            comp = rb.get("composition") or {}
            comp_atoms = list((comp.get("slide_kind_atoms") or {}).values())
            for key in ("container_atom", "hero_atom"):
                if comp.get(key):
                    comp_atoms.append(comp[key])
            unknown += [a for a in comp_atoms if a not in known_types]
        if unknown:
            print(f"  ❌ {name}: unknown atom types {unknown}", file=sys.stderr)
            sys.exit(1)
        runbooks.append(rb)
    return {"catalogId": "a2ui-atoms-v1", "runbookCount": len(runbooks), "runbooks": runbooks}


def main():
    blocks, known_types = load_blocks()
    print(f"🔄 Generating public catalog artifacts ({len(blocks)} atoms)")

    write_json("spec.json", gen_spec(blocks))
    write_json("atoms/index.json", gen_compact_index(blocks))
    write_json("catalogue/a2ui-atoms-v1.json", gen_atoms_catalog(blocks))
    write_json("runbooks/index.json", gen_runbooks_index(known_types))

    # Publication decisions live in project.yaml — the manifest is the
    # single allowlist; internal working prompts stay unpublished
    with open(os.path.join(ROOT, "project.yaml")) as mf:
        PUBLISHED_PROMPTS = yaml.safe_load(mf)["published_prompts"]
    prompts_dir = os.path.join(ROOT, "prompts")
    for name in PUBLISHED_PROMPTS:
        if not os.path.isfile(os.path.join(prompts_dir, name)):
            continue
        out = os.path.join(PUBLIC, "prompts", name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(os.path.join(prompts_dir, name), out)
        print(f"  ✅ public/prompts/{name} (copied from prompts/)")

    shutil.copyfile(os.path.join(ROOT, "THIRD-PARTY-NOTICES.md"),
                    os.path.join(PUBLIC, "THIRD-PARTY-NOTICES.md"))
    print("  ✅ public/THIRD-PARTY-NOTICES.md")
    vendors_dir = os.path.join(ROOT, "vendors")
    for v in sorted(os.listdir(vendors_dir)):
        man = os.path.join(vendors_dir, v, "MANIFEST.md")
        if os.path.isfile(man):
            out_v = os.path.join(PUBLIC, "vendors", v, "MANIFEST.md")
            os.makedirs(os.path.dirname(out_v), exist_ok=True)
            shutil.copyfile(man, out_v)
    for extra in ("MANIFEST.md", "LANDSCAPE.md"):
        src = os.path.join(vendors_dir, extra)
        if os.path.isfile(src):
            os.makedirs(os.path.join(PUBLIC, "vendors"), exist_ok=True)
            shutil.copyfile(src, os.path.join(PUBLIC, "vendors", extra))
    print("  ✅ public/vendors/ (manifests + landscape)")

    gdm_out = os.path.join(PUBLIC, "catalogue", "gdm-v0.2.json")
    os.makedirs(os.path.dirname(gdm_out), exist_ok=True)
    shutil.copyfile(GDM_SPEC, gdm_out)
    print("  ✅ public/catalogue/gdm-v0.2.json (copied from spec/)")


if __name__ == "__main__":
    main()
