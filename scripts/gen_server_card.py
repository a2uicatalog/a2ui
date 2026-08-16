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
workflow). Run locally via `ops.py run mcp-server-card-sync` whenever
tools.js changes.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_JS = ROOT.parent / "a2ui-private" / "mcp-worker" / "src" / "tools.js"
CARD = ROOT / "public" / ".well-known" / "mcp" / "server-card.json"
# The a2uicatalog-docs server (docs-tools.js) — a genuinely separate MCP
# identity from the product server above, added 2026-08-16 to close an
# orank "Product + docs MCP coverage" finding. Its own card at a sibling
# .well-known path, same reasoning as the product card: a scanner that
# finds both servers should be able to match each against its OWN card
# rather than comparing this repo's one card against whichever MCP
# endpoint it most recently probed (confirmed live: orank flagged the
# product card as "drifted" against /mcp-docs's 2 tools once a second
# server existed to compare it to).
DOCS_TOOLS_JS = ROOT.parent / "a2ui-private" / "mcp-worker" / "src" / "docs-tools.js"
DOCS_CARD = ROOT / "public" / ".well-known" / "mcp-docs" / "server-card.json"

# 340, not the original card's incidental ~180: a card previewing tools
# before a caller opens a transport is exactly the wrong place to silently
# drop the trust/custody clauses on the two tools with real side effects
# (emit_deployment's "we hold no creds", publish_url's "ONE WEEK retention
# ... anyone with the link can view") — both sit past 180 chars in the live
# descriptions. 340 comfortably covers both without ballooning every entry.
DESC_BUDGET = 340


def _truncate(text):
    if len(text) <= DESC_BUDGET:
        return text
    cut = text[:DESC_BUDGET]
    last_space = cut.rfind(" ")
    cut = cut[:last_space] if last_space > 0 else cut
    return cut.rstrip(".,;:—-") + "…"  # visible marker — never a silent cut


def live_tools():
    """The live tool list: {"name", "description"} per tool, straight from
    tools.js's mcpTools(null) (imported and executed, not regexed) — the
    single source of truth both this generator AND
    tests/test_agent_readiness_files.py's parity check use, so there's one
    place that knows how to ask tools.js what it defines, not two that can
    independently drift.

    Raises FileNotFoundError if the private sibling repo isn't checked out,
    RuntimeError if the node import itself fails — callers decide what to
    do (the CLI below exits; the test skips on the former, fails on the
    latter).
    """
    if not TOOLS_JS.is_file():
        raise FileNotFoundError(str(TOOLS_JS))
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
        raise RuntimeError(f"node import of tools.js failed:\n{result.stderr}")
    return json.loads(result.stdout)


def live_docs_tools():
    """Same idea as live_tools(), for the separate a2uicatalog-docs server
    (docs-tools.js's docsMcpTools() — no model-gating parameter, unlike the
    product server's mcpTools(model))."""
    if not DOCS_TOOLS_JS.is_file():
        raise FileNotFoundError(str(DOCS_TOOLS_JS))
    node_script = (
        f"import {{ docsMcpTools }} from {json.dumps(str(DOCS_TOOLS_JS))};"
        "process.stdout.write(JSON.stringify(docsMcpTools().map(t => "
        "({name: t.name, description: t.description}))));"
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"node import of docs-tools.js failed:\n{result.stderr}")
    return json.loads(result.stdout)


def haiku_gated_names():
    """Names present in mcpTools(null) but absent from mcpTools('haiku') —
    derived by actually calling tools.js's own exported mcpTools() with
    both arguments and diffing, not by hand-copying MODEL_TOOL_GATES'
    'haiku' list (which isn't even exported). If tools.js ever adds a
    second gated tier, this only ever reports the haiku one — a hand-typed
    fact drifting is exactly the bug class this whole generator exists to
    prevent, so deliberately not doing that here for tiers this doesn't
    check.
    """
    node_script = (
        f"import {{ mcpTools }} from {json.dumps(str(TOOLS_JS))};"
        "const full = new Set(mcpTools(null).map(t => t.name));"
        "const haiku = new Set(mcpTools('haiku').map(t => t.name));"
        "process.stdout.write(JSON.stringify([...full].filter(n => !haiku.has(n))));"
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"node haiku-gate probe failed:\n{result.stderr}")
    return json.loads(result.stdout)


def main():
    try:
        live = live_tools()
    except FileNotFoundError as e:
        sys.exit(
            f"gen_server_card: {e} not found — clone a2ui-private as a sibling "
            "of a2ui-catalogue (this generator reads the live tools/list "
            "straight from mcp-worker's tools.js, same as gen_worker_renderers.py)"
        )
    except RuntimeError as e:
        sys.exit(f"gen_server_card: {e}")
    try:
        gated = haiku_gated_names()
    except RuntimeError as e:
        sys.exit(f"gen_server_card: {e}")

    card = json.loads(CARD.read_text(encoding="utf-8"))
    card["tools"] = [
        {"name": t["name"], "description": _truncate(t["description"])}
        for t in live
    ]
    # The card otherwise implies all tools are unconditionally available,
    # which is false: a caller that identifies itself (via identify_model)
    # as 'haiku' is served a curated subset server-side. Surfacing that
    # here is the difference between an agent discovering the gate by
    # having a call rejected and knowing about it up front.
    if gated:
        available = len(live) - len(gated)
        card["toolAvailabilityNotes"] = (
            f"All {len(live)} tools listed are served to most callers. Callers that "
            "declare their model via identify_model as 'haiku' are instead served a "
            f"curated {available}-of-{len(live)} subset (judgment-heavy tools like "
            "sizing/pagination removed) — currently excluded for that tier: "
            f"{', '.join(sorted(gated))}. Call identify_model first to get the tool "
            "set your model can reliably use."
        )
    else:
        card.pop("toolAvailabilityNotes", None)
    CARD.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"gen_server_card: wrote {len(live)} tools -> {CARD.relative_to(ROOT)}"
          + (f" ({len(gated)} gated for haiku)" if gated else ""))

    try:
        docs_live = live_docs_tools()
    except FileNotFoundError as e:
        sys.exit(f"gen_server_card: {e} not found — same sibling-repo requirement as above")
    except RuntimeError as e:
        sys.exit(f"gen_server_card: {e}")
    docs_card = json.loads(DOCS_CARD.read_text(encoding="utf-8"))
    docs_card["tools"] = [
        {"name": t["name"], "description": _truncate(t["description"])}
        for t in docs_live
    ]
    DOCS_CARD.write_text(json.dumps(docs_card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"gen_server_card: wrote {len(docs_live)} tools -> {DOCS_CARD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
