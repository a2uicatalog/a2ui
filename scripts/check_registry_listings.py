#!/usr/bin/env python3
"""
Drift check for the Smithery listing of the A2UI Atomic Catalog MCP server.

The listing's name and description are entered by hand in Smithery's dashboard (Smithery documents no CLI flag or CI
token for them), and its tool list is whatever Smithery scanned when the server was published. Both go stale silently:
the listing once said "474 components" and "15 tools" while the server served 548 atoms and 40 tools.

This compares the public registry entry with the live server and with the expectations below, and exits non-zero on
any mismatch. Read-only, no secrets. Run weekly by .github/workflows/registry-drift.yml; also safe to run by hand:

    python3 scripts/check_registry_listings.py

Exit codes: 0 = in step, 1 = drift (the message says exactly what to change in the dashboard), 2 = could not check
(network or an unexpected response; retried first).

Smithery's registry is cached by a CDN for hours; a cache-busting query parameter returns the current entry.
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REGISTRY_URL = "https://registry.smithery.ai/servers/a2uicatalog/a2uicatalog"
MCP_URL = "https://a2uicatalog.ai/mcp"

# What the listing must say. Edit here when the listing text is deliberately changed.
EXPECT_NAME_PREFIX = "A2UI Atomic Catalog"
EXPECT_DESCRIPTION_CONTAINS = ["A2UI Atomic Catalog", "MCP server", "no signup"]
# A hand-typed exact count in a manual field goes stale (474 did). Use a round figure such as "500+".
FORBID_DESCRIPTION = [(r"\b\d{3}\s+(?:typed\s+)?(?:UI\s+)?(?:atoms|components)\b", 'an exact count such as "548 atoms" (use "500+")')]


def fetch_json(url, data=None, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={
                "accept": "application/json, text/event-stream", "content-type": "application/json",
                "user-agent": "a2uicatalog-registry-drift-check"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:                      # network, HTTP error, bad JSON: retry, then report as "could not check"
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


def live_tool_count():
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
    return len(fetch_json(MCP_URL, body)["result"]["tools"])


def registry_entry():
    return fetch_json(f"{REGISTRY_URL}?cb={int(time.time())}")


def compare(entry, live_tools):
    """Pure comparison; returns a list of human-readable problems (empty = in step)."""
    problems = []
    name = entry.get("displayName") or ""
    if not name.startswith(EXPECT_NAME_PREFIX):
        problems.append(f'display name is "{name}"; it should start with "{EXPECT_NAME_PREFIX}" (Smithery dashboard > edit listing)')
    desc = entry.get("description") or ""
    for needle in EXPECT_DESCRIPTION_CONTAINS:
        if needle.lower() not in desc.lower():
            problems.append(f'description no longer contains "{needle}" (Smithery dashboard > edit listing)')
    for pattern, what in FORBID_DESCRIPTION:
        m = re.search(pattern, desc, re.I)
        if m:
            problems.append(f'description contains {what}: found "{m.group(0)}"')
    listed = len(entry.get("tools") or [])
    if listed != live_tools:
        problems.append(f"Smithery lists {listed} tools but the live server serves {live_tools}: "
                        f'republish to re-scan (smithery mcp publish "{MCP_URL}" -n a2uicatalog/a2uicatalog)')
    return problems


def main():
    try:
        entry, live = registry_entry(), live_tool_count()
    except Exception as e:
        print(f"could not check: {e}", file=sys.stderr)
        return 2
    problems = compare(entry, live)
    if problems:
        print(f"Smithery listing a2uicatalog/a2uicatalog is out of step ({len(problems)} problem(s)):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f'✓ Smithery listing in step: "{entry.get("displayName")}", {live} tools, description as expected')
    return 0


if __name__ == "__main__":
    sys.exit(main())
