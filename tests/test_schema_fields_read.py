"""Every field an atom declares in atoms/schema.yaml should be read by its renderer.

Found 2026-10-04 on a Pixel: alert_banner declares action_label/action_url but the
shared renderer never drew the button, and document_link declares document_url/label/
icon_type but the renderer read url/title/type, so its link pointed at the site root.
An agent that fills in a declared field gets nothing, on every surface the bundle
serves (MCP Apps, Apps Script, Android).

The check is lexical: a field counts as read if its renderer's source mentions it
(`b.field`, `['field']` or `'field'`). That misses fields read through a helper, so
gaps that exist today are recorded in a baseline. This is a ratchet, not an
allowlist: a NEW unread field fails, and so does a baseline entry that is now read
(delete it). Regenerate after a deliberate change with

    A2UI_WRITE_FIELD_BASELINE=1 python3 -m pytest tests/test_schema_fields_read.py
"""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "public" / "surfaces" / "mcp-apps" / "renderer-bundle.html"
BASELINE = Path(__file__).resolve().parent / "schema_fields_unread_baseline.json"


def _renderer_sources():
    """Source text of each _RENDERERS entry, up to the next assignment."""
    src = BUNDLE.read_text()
    starts = [(m.group(1) or m.group(2), m.start()) for m in
              re.finditer(r"_RENDERERS(?:\[['\"](\w+)['\"]\]|\.(\w+))\s*=", src)]
    out = {}
    for i, (name, s) in enumerate(starts):
        e = starts[i + 1][1] if i + 1 < len(starts) else len(src)
        out[name] = out.get(name, "") + src[s:e]
    return out


def _unread(atoms):
    bodies = _renderer_sources()
    gaps = {}
    for a in atoms.values():
        body = bodies.get(a["type"])
        if body is None:            # drawn elsewhere (delegated); covered by surface tests
            continue
        missing = sorted(f for f in (a.get("fields") or {})
                         if not re.search(r"\.%s\b|\[['\"]%s['\"]\]|['\"]%s['\"]" % (f, f, f), body))
        if missing:
            gaps[a["type"]] = missing
    return gaps


def test_declared_fields_are_read_by_the_renderer(atoms):
    now = _unread(atoms)
    if os.environ.get("A2UI_WRITE_FIELD_BASELINE"):
        BASELINE.write_text(json.dumps(now, indent=1, sort_keys=True) + "\n")
    base = json.loads(BASELINE.read_text())
    new = {t: [f for f in fs if f not in base.get(t, [])] for t, fs in now.items()}
    new = {t: fs for t, fs in new.items() if fs}
    fixed = {t: [f for f in fs if f not in now.get(t, [])] for t, fs in base.items()}
    fixed = {t: fs for t, fs in fixed.items() if fs}
    assert not new, ("schema fields the renderer never reads (fix the renderer, or the "
                     "schema if the field is wrong):\n" + json.dumps(new, indent=1))
    assert not fixed, ("now read, so delete from tests/schema_fields_unread_baseline.json:\n"
                       + json.dumps(fixed, indent=1))
