#!/usr/bin/env python3
"""Compile the wired renderers into an ES module for the Cloudflare Worker.

WHY THIS EXISTS, AND WHY IT IS NOT gen_mcp_apps_bundle.py:

Workers forbid `eval` and `new Function`, so the Worker cannot fetch
renderer-bundle.html at runtime and execute it the way the ui:// view does.
The renderers must be compiled INTO the Worker script at build time. Same
sources, different output shape: an importable ES module instead of an HTML
document with <script> blocks.

Consequence, and it is a real one: a renderer change now has a FOURTH deploy
target (two GAS deployments, the MCP Apps bundle, and now the Worker). That is
the same two-deploy-drift class that produced the 2026-07-11 bundle fix and the
2026-08-01 ui:// cache incident — renderer-release owns it, and the generated
file carries a source hash so staleness is detectable rather than silent.

WHAT IT EMITS:
  a2ui-private/mcp-worker/src/renderers.generated.js
    export { renderAtoms, _RENDERERS, SOURCE_SHA }

Same file set as the MCP Apps bundle — PackMap.gs, atom.gs, then atoms_*.gs in
sorted (GAS load) order, minus atoms_schema_snapshot.gs, which is 124 KB of
docs with zero _RENDERERS entries. Code.gs is excluded (server routing), so the
prelude supplies the one cross-file symbol renderers call from it.

NOT included, deliberately:
  - the client partials (AtomScripts/A2UIState/A2uiUpdates) — they touch
    window/document at load time and there is no DOM in a Worker
  - the MCP Apps view handshake — that is a browser-iframe concern
  - class-C degraded cards — this renderer's CALLER refuses those atoms
    outright (a public endpoint that fetches a URL on a stranger's behalf is
    an SSRF surface), so a placeholder here would be misleading

STRICT MODE: ES modules are always strict; this code has only ever run in a
sloppy-mode <script>. The generated module is verified by executing it under
Node as a module, so a strict-mode failure (an undeclared assignment, an octal
literal) fails the build rather than the deploy.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parent.parent
RENDERER_DIR = ROOT / "apps-script-surface" / "gas-wired-renderer"
OUT = ROOT.parent / "a2ui-private" / "mcp-worker" / "src" / "renderers.generated.js"

EXCLUDE = {"atoms_schema_snapshot.gs", "Code.gs", "Code.private.gs",
           "exprs_schema_snapshot.gs", "training_parser.gs"}

PRELUDE = """
// ---- worker prelude ----
// Code.gs (server routing) is excluded; provide the one cross-file symbol
// renderers call from it. Sub-page links degrade to '#'. GAS host services
// stay DELIBERATELY undefined so guarded renderers take their mock path.
function _getWebAppUrl() { return '#'; }
var ScriptApp = { getService: function () { return { getUrl: function () { return '#'; } }; } };
var Utilities = {
  newBlob: function (s) { return { getBytes: function () { return s; } }; },
  base64EncodeWebSafe: function (s) {
    var str = typeof s === 'string' ? s : String(s);
    var b64 = btoa(unescape(encodeURIComponent(str)));
    return b64.replace(/\\+/g, '-').replace(/\\//g, '_');
  }
};
""".strip()


def gs_load_order():
    files = [RENDERER_DIR / "PackMap.gs", RENDERER_DIR / "atom.gs"]
    files += sorted(p for p in RENDERER_DIR.glob("atoms_*.gs") if p.name not in EXCLUDE)
    missing = [f for f in files if not f.exists()]
    if missing:
        print(f"✗ missing renderer sources: {[m.name for m in missing]}", file=sys.stderr)
        sys.exit(1)
    return files


def main():
    files = gs_load_order()
    parts, digest = [], hashlib.sha256()
    for f in files:
        src = f.read_text(encoding="utf-8")
        digest.update(src.encode("utf-8"))
        parts.append(f"// ===== {f.name} =====\n{src}")

    sha = digest.hexdigest()
    body = "\n\n".join(parts)

    # The staging boundary has to be compiled in. The concatenated sources
    # register EVERY atom the renderer knows (523), including stage: preview
    # ones, but a public endpoint is a publication surface and must serve only
    # what public/spec.json publishes (474) — same filter every other pipeline
    # applies, enforced by tests/test_staging.py. Read from the generated spec
    # rather than schema.yaml so this cannot drift from what is actually live.
    spec_path = ROOT / "public" / "spec.json"
    if not spec_path.exists():
        print("✗ public/spec.json missing — run ops.py run catalog-rebuild first", file=sys.stderr)
        sys.exit(1)
    published = sorted({a["type"] for a in json.loads(spec_path.read_text()).get("atoms", [])})
    if not published:
        print("✗ public/spec.json published no atoms — refusing to emit an empty allowlist", file=sys.stderr)
        sys.exit(1)

    # `var` at module top level is module-scoped, not global — which is what we
    # want: cross-file references (atoms_*.gs reaching _RENDERERS from atom.gs)
    # resolve inside the module and nothing leaks to globalThis.
    module = (
        "// GENERATED by scripts/gen_worker_renderers.py — DO NOT EDIT.\n"
        f"// source sha256: {sha}\n"
        f"// {len(files)} renderer sources, concatenated in GAS load order.\n\n"
        f"{PRELUDE}\n\n{body}\n\n"
        f'export const SOURCE_SHA = "{sha}";\n'
        f"export const PUBLISHED_ATOMS = new Set({json.dumps(published)});\n"
        "export { renderAtoms, _RENDERERS };\n"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(module, encoding="utf-8")
    n_atoms = len(set(re.findall(r"_RENDERERS\[\s*['\"]([a-z0-9_]+)['\"]\s*\]\s*=", body)))
    print(f"wrote {OUT} ({len(module)} bytes, {len(files)} files, {n_atoms} atoms)")
    print(f"source sha256: {sha[:16]}")


if __name__ == "__main__":
    main()
