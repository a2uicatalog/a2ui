#!/usr/bin/env python3
"""
Generate atoms_schema_snapshot.gs from the local schema.yaml.

Run this before `clasp push` whenever atoms are added or changed:
  python3 scripts/gen_schema_snapshot.py

Output: apps-script-surface/a2ui-gem-renderer/atoms_schema_snapshot.gs
"""
import yaml
import os

SCHEMA = os.path.join(os.path.dirname(__file__), '..', 'atoms', 'schema.yaml')
OUTPUT = os.path.join(
    os.path.dirname(__file__), '..', 'apps-script-surface',
    'a2ui-gem-renderer', 'atoms_schema_snapshot.gs'
)

with open(SCHEMA) as f:
    raw = yaml.safe_load(f)

blocks = raw.get('blocks', [])
lines = []
for b in blocks:
    surfaces = b.get('surfaces', {})
    works_on = surfaces.get('works_on', [])
    if 'google-apps-script-web' not in works_on:
        continue
    t = b.get('type', '')
    desc = b.get('compact_description') or b.get('description', '')
    fields = b.get('fields', {})
    if isinstance(fields, dict):
        fstr = ', '.join(
            (k + ': ' + str(v)) if isinstance(v, str) else (k + ' (' + str(v) + ')')
            for k, v in fields.items()
        )
    else:
        fstr = str(fields) if fields else ''
    lines.append(t + '  — ' + desc)
    if fstr:
        lines.append('  fields: ' + fstr)
    connectors = b.get('connectors', [])
    if connectors:
        cstr = '; '.join(
            c.get('id','') + '(' +
            ('|'.join(c.get('surfaces',[])) if c.get('surfaces') != ['*'] else 'all-surfaces') +
            ',' + ('live' if c.get('live') else 'static') + ')'
            for c in connectors
        )
        lines.append('  connectors: ' + cstr)

schema_text = '\n'.join(lines)
# Escape for embedding in a JS template literal
escaped = schema_text.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

gs_content = (
    '// AUTO-GENERATED — run scripts/gen_schema_snapshot.py before clasp push\n'
    '// Source: atoms/schema.yaml  (google-apps-script-web surface only)\n'
    '// Do not edit by hand.\n\n'
    'var _ATOM_SCHEMA_SNAPSHOT = `' + escaped + '`;\n'
)

with open(OUTPUT, 'w') as f:
    f.write(gs_content)

atom_count = len([l for l in lines if not l.startswith('  ')])
print(f"✓ {atom_count} atoms · {len(schema_text):,} chars (~{len(schema_text)//4:,} tokens)")
print(f"  → {os.path.relpath(OUTPUT)}")

# ── Drift check: warn if renderer has atoms not in schema ─────────────────────
import re, glob

RENDERER_DIR = os.path.join(os.path.dirname(__file__), '..', 'apps-script-surface', 'a2ui-gem-renderer')
renderer_types = set()
for gs_file in glob.glob(os.path.join(RENDERER_DIR, 'atom*.gs')):
    with open(gs_file) as f:
        for m in re.finditer(r"_RENDERERS\['([^']+)'\]", f.read()):
            renderer_types.add(m.group(1))

schema_types = set(b.get('type','') for b in blocks if 'google-apps-script-web' in b.get('surfaces',{}).get('works_on',[]))
missing = sorted(renderer_types - schema_types)
if missing:
    print(f"\n⚠️  {len(missing)} renderer atom(s) not in schema — add them before clasp push:")
    for t in missing:
        print(f"    • {t}")
else:
    print(f"✓ schema in sync with renderer ({len(renderer_types)} renderer atoms)")
