#!/usr/bin/env python3
"""Regenerate the `tools` array in public/.well-known/mcp/server-card.json
from the LIVE tool list, so the card can't drift from the server it
describes the way a hand-written one silently did (orank flagged this
2026-08-05: card advertised 15 tools, the live server served 25).

The live list is `mcpTools(null)` in the private sibling repo's
a2ui-private/mcp-worker/src/tools.js — the same function the Worker calls
to answer a real `tools/list` request. `null` model = the unfiltered full
toolkit (what an anonymous/undeclared-model caller sees), matching what the
card should advertise. Invoked via a `node` subprocess because tools.js is
an ES module with real imports (catalog data, validators) that only resolve
inside the private repo — same cross-repo-generator idiom as
gen_worker_renderers.py (public -> private) and mcp-sdk-sync-data's
`node ...sync-data.mjs` step, just mirrored the other direction.

NOT run in CI (.github/workflows/deploy.yml never has the private repo
checked out either — gen_worker_renderers.py is likewise absent from that
workflow). Run locally via `ops.py run catalog-rebuild` whenever tools.js
changes.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_JS = ROOT.parent / "a2ui-private" / "mcp-worker" / "src" / "tools.js"
CARD = ROOT / "public" / ".well-known" / "mcp" / "server-card.json"

DESC_BUDGET = 180  # matches the existing card's own hand-truncated length


def _truncate(text):
    if len(text) <= DESC_BUDGET:
        return text
    cut = text[:DESC_BUDGET]
    last_space = cut.rfind(" ")
    return cut[:last_space] if last_space > 0 else cut


def _live_tools():
    if not TOOLS_JS.is_file():
        sys.exit(
            f"gen_server_card: {TOOLS_JS} not found — clone a2ui-private as a "
            "sibling of a2ui-catalogue (this generator reads the live tools/list "
            "straight from mcp-worker's tools.js, same as gen_worker_renderers.py)"
        )
    node_script = (
        f"import {{ mcpTools }} from {json.dumps(str(TOOLS_JS))};"
        "process.stdout.write(JSON.stringify(mcpTools(null).map(t => "
        "({name: t.name, description: t.description}))));"
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"gen_server_card: node import of tools.js failed:\n{result.stderr}")
    return json.loads(result.stdout)


def main():
    live = _live_tools()
    card = json.loads(CARD.read_text(encoding="utf-8"))
    card["tools"] = [
        {"name": t["name"], "description": _truncate(t["description"])}
        for t in live
    ]
    CARD.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"gen_server_card: wrote {len(live)} tools -> {CARD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
