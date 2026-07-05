#!/usr/bin/env python3
"""Batch atom generator — uses Gemini to generate new atoms from a category prompt.

Usage:
    python3 scripts/batch_generate_atoms.py --category "data visualization" --count 5
    python3 scripts/batch_generate_atoms.py --category "navigation" --count 3 --dry-run

The script:
1. Loads the system prompt and existing schema
2. Calls Gemini Flash with the category prompt
3. Parses and validates the returned YAML
4. Runs test_schema.py against new atoms
5. If valid, appends to atoms/schema.yaml
6. Generates renderer stubs in renderers/web_article_stubs.py
7. Regenerates the compatibility table in README.md
"""

import argparse
import subprocess
import sys
import yaml
from pathlib import Path

CATALOGUE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CATALOGUE_ROOT))

SCHEMA_PATH       = CATALOGUE_ROOT / "atoms" / "schema.yaml"
PROMPT_PATH       = CATALOGUE_ROOT / "prompts" / "atom_generator.md"
STUBS_PATH        = CATALOGUE_ROOT / "renderers" / "web_article_stubs.py"
README_PATH       = CATALOGUE_ROOT / "README.md"

CATEGORIES = {
    "data_viz":    "Data visualisation atoms — sparkline, heatmap, donut stat, metric delta, trend indicator",
    "navigation":  "Navigation and structure atoms — breadcrumb, pagination, stepper, tab bar, anchor list",
    "content":     "Rich content atoms — FAQ accordion, glossary term, footnote, blockquote with avatar, pull stat",
    "social":      "Social proof atoms — testimonial card, star rating, avatar group, contributor list",
    "media":       "Media atoms — audio embed, PDF preview, video thumbnail, code diff, screenshot frame",
    "status":      "Status and feedback atoms — alert banner, toast notification, loading skeleton, empty state",
    "comparison":  "Comparison atoms — feature matrix, pricing tier, pros/cons list, side-by-side spec",
    "interactive": "Interactive CSS-only atoms — accordion, tooltip, hover card, collapsible section",
}


def load_existing_atom_types() -> list:
    with open(SCHEMA_PATH) as f:
        schema = yaml.safe_load(f)
    return [b["type"] for b in schema.get("blocks", [])]


def call_gemini(system_prompt: str, user_prompt: str, project: str, region: str) -> str:
    """Call Gemini Flash via the google-genai SDK."""
    import google.genai as genai
    from google.genai import types

    client = genai.Client(vertexai=True, project=project, location=region)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4,
        )
    )
    return response.text


def sanitise_yaml(raw: str) -> str:
    """Fix common LLM YAML mistakes that cause parse errors."""
    import re
    lines = raw.split("\n")
    cleaned = []
    for line in lines:
        # Strip inline | type alternatives: `string | integer` → `string`
        line = re.sub(r'(:\s+\S+)\s*\|\s*\S+', r'\1', line)
        # Strip parenthetical annotations from field lines: `boolean (default true)` → `boolean`
        line = re.sub(r'(:\s+\w+)\s*\([^)]*\)', r'\1', line)
        # Strip inline comments after field values that contain colons
        line = re.sub(r'(:\s+\w+)\s+#.*$', r'\1', line)
        # Fix "list of X" or "list of {..." → "list"
        line = re.sub(r':\s+list of .*$', ': list', line)
        # Fix inline object descriptors: "list of {key: type}" → "list"
        line = re.sub(r':\s+list \{.*$', ': list', line)
        cleaned.append(line)
    return "\n".join(cleaned)


def parse_yaml_atoms(raw: str) -> list:
    """Parse YAML from LLM response, stripping markdown fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    raw = sanitise_yaml(raw)
    parsed = yaml.safe_load(raw)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return [parsed]
    raise ValueError(f"Unexpected YAML structure: {type(parsed)}")


def validate_atoms(new_atoms: list, existing_types: list) -> tuple[list, list]:
    """Validate atoms against schema rules. Returns (valid, errors)."""
    required_fields = ["type", "description", "source", "surfaces"]
    required_source = ["name", "url", "license"]
    surfaces_known  = {"web", "meet-stage", "googlechat", "email", "pdf"}

    valid  = []
    errors = []

    for atom in new_atoms:
        atype = atom.get("type", "?")

        if atype in existing_types:
            errors.append(f"  SKIP {atype}: already exists")
            continue

        for f in required_fields:
            if f not in atom:
                errors.append(f"  FAIL {atype}: missing '{f}'")
                break
        else:
            src = atom.get("source", {})
            for sf in required_source:
                if not src.get(sf):
                    errors.append(f"  FAIL {atype}: source missing '{sf}'")
                    break
            else:
                works = set(atom.get("surfaces", {}).get("works_on", []))
                bad = works - surfaces_known
                if bad:
                    errors.append(f"  FAIL {atype}: unknown surface(s) {bad}")
                else:
                    valid.append(atom)

    return valid, errors


def append_to_schema(new_atoms: list):
    with open(SCHEMA_PATH) as f:
        schema = yaml.safe_load(f)
    schema["blocks"].extend(new_atoms)
    header = (
        "# atoms/schema.yaml — universal block vocabulary\n"
        "#\n"
        "# Surface compatibility:\n"
        "#   works_on:        full support\n"
        "#   degraded_on:     renders with caveats\n"
        "#   incompatible_on: do not use — substitute hint provided\n"
        "#\n"
        "# Source credit:\n"
        "#   Every atom declares its origin. a2ui-catalogue atoms are MIT.\n"
        "#   Third-party atoms credit the original author and license.\n"
        "#\n"
        "# Surfaces: web | meet-stage | googlechat | email | pdf\n\n"
    )
    with open(SCHEMA_PATH, "w") as f:
        f.write(header)
        yaml.dump(schema, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def generate_stubs(new_atoms: list):
    """Append renderer stub functions to web_article_stubs.py."""
    lines = []
    if not STUBS_PATH.exists():
        lines.append('"""Renderer stubs — implement these in web_article.py."""\n\n')

    for atom in new_atoms:
        atype = atom["type"]
        desc  = atom.get("description", "")
        lines.append(f'\ndef _render_{atype}(b: dict) -> str:')
        lines.append(f'    """TODO: {desc}"""')
        lines.append(f'    # fields: {list(atom.get("fields", {}).keys())}')
        lines.append(f'    return f\'<div><!-- {atype} stub --></div>\'')
        lines.append("")

    with open(STUBS_PATH, "a") as f:
        f.write("\n".join(lines))


def regenerate_readme():
    result = subprocess.run(
        ["python3", "tests/generate_compat_table.py"],
        capture_output=True, text=True, cwd=CATALOGUE_ROOT
    )
    if result.returncode != 0:
        print(f"  ⚠️  Table generation failed: {result.stderr}")
        return
    table = result.stdout
    readme = README_PATH.read_text()
    # Replace between matrix header and next ---
    import re
    readme = re.sub(
        r'(## Surface Compatibility Matrix\n\n).*?(\n---)',
        r'\1' + table.replace('\\', '\\\\') + r'\2',
        readme, flags=re.DOTALL
    )
    README_PATH.write_text(readme)


def main():
    parser = argparse.ArgumentParser(description="Batch generate atoms via Gemini")
    parser.add_argument("--category", choices=list(CATEGORIES.keys()),
                        required=True, help="Atom category to generate")
    parser.add_argument("--count", type=int, default=5,
                        help="Number of atoms to request (default 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and validate without writing to schema")
    parser.add_argument("--project", default=None,
                        help="GCP project (defaults to GEMINI_PROJECT env var)")
    parser.add_argument("--region", default="us-central1")
    args = parser.parse_args()

    import os
    project = args.project or os.environ.get("GEMINI_PROJECT")
    if not project:
        print("❌ Set GEMINI_PROJECT env var or pass --project")
        sys.exit(1)

    existing = load_existing_atom_types()
    print(f"📚 Existing atoms: {len(existing)}")

    system_prompt = PROMPT_PATH.read_text()
    user_prompt = (
        f"Generate exactly {args.count} new atoms for the category: "
        f"**{CATEGORIES[args.category]}**\n\n"
        f"Do not generate any of these existing types: {', '.join(existing)}\n\n"
        f"Return only valid YAML, no explanation."
    )

    print(f"🤖 Calling Gemini Flash for category: {args.category}...")
    raw = call_gemini(system_prompt, user_prompt, project, args.region)

    print(f"\n📥 Raw response:\n{raw[:500]}{'...' if len(raw) > 500 else ''}\n")

    try:
        new_atoms = parse_yaml_atoms(raw)
    except Exception as e:
        print(f"❌ YAML parse error: {e}")
        sys.exit(1)

    valid, errors = validate_atoms(new_atoms, existing)

    if errors:
        print("⚠️  Validation issues:")
        for e in errors:
            print(e)

    print(f"\n✅ Valid atoms: {len(valid)}/{len(new_atoms)}")
    for a in valid:
        works = a['surfaces'].get('works_on', [])
        print(f"  + {a['type']} ({', '.join(works)})")

    if args.dry_run:
        print("\n[dry-run] No changes written.")
        return

    if not valid:
        print("❌ No valid atoms to add.")
        sys.exit(1)

    append_to_schema(valid)
    generate_stubs(valid)
    regenerate_readme()

    print(f"\n🎉 Added {len(valid)} atoms to schema.")
    print(f"   Stubs written to: renderers/web_article_stubs.py")
    print(f"   README table regenerated.")
    print(f"\nNext: implement stubs in renderers/web_article.py, add tests, run pytest.")


if __name__ == "__main__":
    main()
