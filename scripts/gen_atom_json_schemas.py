#!/usr/bin/env python3
"""
Generate a strict, per-atom JSON Schema for every published atom, combined into
one schema for "an array of blocks, each matching exactly one atom's shape."

Why: constraining an LLM's output with a JSON Schema that only enumerates atom
`type` values (via response_format.json_schema) stops it inventing nonexistent
types, but leaves every other field unconstrained — a small model will still
invent extra fields or malformed nesting. This generates the missing per-field
constraint from atoms/schema.yaml's free-text field grammar, so
`additionalProperties: false` can actually be enforced.

Adapted from an outsourced draft (2026-07-13) after two rounds of that draft's
own verification reports containing fabricated atom names and schemas that
didn't match what its own parser actually produced when run for real. The
parsing approach (ast.parse() for Python-repr-style nested literals, regex
fallbacks for prose enums/arrays-of-objects, the `type` field collision fix)
is real and was verified correct by running it against the live schema.yaml.
This version: fixes ROOT-relative paths to match this repo's other
scripts/gen_*.py, and additionally handles fields whose YAML value is ALREADY
a native list/dict (not a string containing Python-repr text) — the outsourced
version silently fell back on these even though they're the cleanest, most
structured data in the file.

Run:
  python3 scripts/gen_atom_json_schemas.py
  python3 scripts/gen_atom_json_schemas.py --check   # CI: exit 1 if stale
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
SCHEMA_YAML = ROOT / "atoms" / "schema.yaml"
OUTPUT = ROOT / "public" / "catalogue" / "atoms-json-schema.json"


def _object_schema_from_pairs(pairs: dict) -> dict:
    """pairs: {field_name: raw_type_string_or_nested}. Shared by the ast-literal
    path and the native-python-object path below — same shape, same rules."""
    properties, required = {}, []
    for k, v in pairs.items():
        if isinstance(v, str):
            is_opt = "optional" in v.lower() or v.strip().endswith("?")
            properties[k] = {"type": "string"}
        elif isinstance(v, dict):
            properties[k] = _object_schema_from_pairs(v)
            is_opt = False
        elif isinstance(v, list):
            item = _object_schema_from_pairs(v[0]) if v and isinstance(v[0], dict) else {"type": "string"}
            properties[k] = {"type": "array", "items": item}
            is_opt = False
        else:
            properties[k] = {"type": ["string", "number", "boolean", "object", "array"]}
            is_opt = True
        if not is_opt:
            required.append(k)
    schema = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        schema["required"] = required
    return schema


def evaluate_ast_node(node) -> dict:
    """Nested Python-repr-style literal (a string like "[{'label': 'string', ...}]")
    parsed via ast.parse(), then walked into a JSON Schema."""
    if isinstance(node, ast.List):
        if len(node.elts) == 1:
            return {"type": "array", "items": evaluate_ast_node(node.elts[0])}
        return {"type": "array", "items": {"type": ["string", "number", "boolean", "object", "array"]}}
    if isinstance(node, ast.Dict):
        properties, required = {}, []
        for k_node, v_node in zip(node.keys, node.values):
            if isinstance(k_node, ast.Constant):
                k = str(k_node.value)
            else:
                continue
            if isinstance(v_node, ast.Constant):
                v_str = str(v_node.value)
                is_opt = "optional" in v_str.lower() or "?" in v_str
                properties[k] = {"type": "string"}
            else:
                properties[k] = evaluate_ast_node(v_node)
                is_opt = False
            if not is_opt:
                required.append(k)
        schema = {"type": "object", "properties": properties, "additionalProperties": False}
        if required:
            schema["required"] = required
        return schema
    raise ValueError(f"unsupported literal node: {type(node).__name__}")


def advanced_parse_field(raw_string: str):
    s = raw_string.strip()
    s_lower = s.lower()
    is_optional = "optional" in s_lower or "?" in s_lower or "default" in s_lower

    if s.startswith("{") or s.startswith("["):
        try:
            tree = ast.parse(s, mode="eval")
            return evaluate_ast_node(tree.body), is_optional
        except Exception:
            pass

    array_obj_match = re.search(r"(?:array of\s*|list of\s*)?\{\s*([^}]+)\s*\}", s, re.IGNORECASE)
    if array_obj_match:
        tokens = re.split(r",\s*", array_obj_match.group(1))
        properties, required = {}, []
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            clean = re.sub(r"\(.*?\)", "", token).strip()
            field_opt = clean.endswith("?") or "optional" in token.lower()
            clean = clean.rstrip("?").strip()
            name = clean.split(":", 1)[0].strip() if ":" in clean else clean
            properties[name] = {"type": "string"}
            if not field_opt:
                required.append(name)
        schema = {"type": "array", "items": {"type": "object", "properties": properties, "additionalProperties": False}}
        if required:
            schema["items"]["required"] = required
        return schema, is_optional

    for sep in (" — ", " -- "):
        if sep in s:
            parts = s.split(sep, 1)
            if len(parts) > 1 and "," in parts[1]:
                enum_items = [re.sub(r"[.\s?]+", "", x).strip() for x in parts[1].split(",")]
                enum_items = [x for x in enum_items if x and not x.startswith("etc")]
                if enum_items:
                    return {"type": "string", "enum": enum_items}, is_optional

    if "|" in s:
        return {"type": "string", "enum": [v.strip("'\" ") for v in s.split("|")]}, is_optional

    if " or " in s_lower and "," not in s:
        clean_s = re.sub(r"\(.*?\)", "", s).strip()
        return {"type": "string", "enum": [v.strip() for v in re.split(r"\s+or\s+", clean_s, flags=re.IGNORECASE)]}, is_optional

    for kw, jt in (("bool", "boolean"), ("integer", "integer"), ("int", "integer"),
                   ("number", "number"), ("float", "number"), ("double", "number")):
        if kw in s_lower:
            return {"type": jt}, is_optional
    if "url" in s_lower or "uri" in s_lower:
        return {"type": "string", "format": "uri"}, is_optional
    if "string" in s_lower:
        return {"type": "string"}, is_optional
    if any(k in s_lower for k in ("gap", "size", "padding", "margin", "width", "height", "color", "label", "text", "message")):
        return {"type": "string"}, is_optional

    raise ValueError("irreducibly free-text")


def build_atom_schema(block: dict) -> dict:
    atom_type = block["type"]
    properties = {"type": {"type": "string", "const": atom_type}}
    required = ["type"]

    for field_name, field_raw in (block.get("fields") or {}).items():
        target = field_name
        try:
            if isinstance(field_raw, str):
                field_schema, is_optional = advanced_parse_field(field_raw)
            elif isinstance(field_raw, dict):
                field_schema, is_optional = _object_schema_from_pairs(field_raw), False
            elif isinstance(field_raw, list):
                item = _object_schema_from_pairs(field_raw[0]) if field_raw and isinstance(field_raw[0], dict) else {"type": "string"}
                field_schema, is_optional = {"type": "array", "items": item}, False
            else:
                raise ValueError(f"unhandled field_raw type: {type(field_raw).__name__}")
        except Exception as e:
            field_schema, is_optional = {"type": ["string", "number", "boolean", "object", "array"]}, True
            print(f"[FALLBACK] {atom_type}.{field_name} -> {field_raw!r} | {e}", file=sys.stderr)

        # atom's own field literally named "type" collides with the injected
        # discriminator above — namespace it rather than silently overwrite.
        if field_name == "type":
            target = f"{atom_type}_type"
            if isinstance(field_schema, dict):
                field_schema = dict(field_schema)
                field_schema["description"] = f"Renamed from 'type' to avoid the discriminator collision. Original: {field_raw}"

        properties[target] = field_schema
        if not is_optional:
            required.append(target)

    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exit 1 if output would differ from a fresh run")
    args = parser.parse_args()

    data = yaml.safe_load(SCHEMA_YAML.read_text())
    blocks = [b for b in data["blocks"] if b.get("stage") != "preview"]

    per_atom = [build_atom_schema(b) for b in blocks]
    combined = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "A2UI Block List Schema",
        "type": "array",
        "items": {"oneOf": per_atom},
    }
    output_str = json.dumps(combined, indent=2) + "\n"

    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != output_str:
            print(f"stale: {OUTPUT} does not match a fresh run", file=sys.stderr)
            sys.exit(1)
        print("up to date")
        return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output_str)
    print(f"✓ {len(per_atom)} atom schemas → {OUTPUT}")


if __name__ == "__main__":
    main()
