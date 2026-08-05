"""The agent-readiness artefacts must stay TRUE, not merely present.

Added 2026-08-02 alongside the server card, pricing.md and schema map. A static
file describing a live server is a file that goes stale silently — the whole
class of failure this repo spent two days gating against — so each assertion
here checks the artefact against the thing it describes rather than against
itself.
"""
import json
import os
import re

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(ROOT, "public")


def _load(*parts):
    p = os.path.join(PUBLIC, *parts)
    assert os.path.isfile(p), f"{'/'.join(parts)} missing"
    with open(p, encoding="utf-8") as f:
        return f.read()


def test_server_card_shape():
    card = json.loads(_load(".well-known", "mcp", "server-card.json"))
    for field in ("name", "description", "version", "serverUrl", "tools"):
        assert card.get(field), f"server-card.json missing required field {field}"
    assert card["serverUrl"] == "https://a2uicatalog.ai/mcp"
    assert card["tools"], "server-card.json lists no tools"
    for t in card["tools"]:
        assert t.get("name") and t.get("description"), f"tool entry incomplete: {t}"


def test_server_card_tools_match_the_worker():
    """The card's tool list must match what the Worker actually exposes —
    in BOTH directions.

    scripts/gen_server_card.py regenerates the card FROM tools.js, but
    nothing stops someone hand-editing the card afterwards, so this stays a
    real assertion rather than trusting the generator ran. Bidirectional
    because one-directional (card subset-of live) is exactly how the
    2026-08-05 drift slipped through: the card advertised 15 tools while
    tools.js defined 25, and a subset check can't see under-listing.
    mcp-worker is a sibling private repo, so skip when absent rather than
    fail — the public repo must still build standalone.
    """
    tools_js = os.path.join(ROOT, "..", "a2ui-private", "mcp-worker", "src", "tools.js")
    if not os.path.isfile(tools_js):
        pytest.skip("mcp-worker not present (public repo standalone build)")
    with open(tools_js, encoding="utf-8") as f:
        src = f.read()

    # Scope the name search to the allTools array specifically — a bare
    # "name: '...'" search also matches unrelated object literals elsewhere
    # in the file (e.g. `MCP_SERVER = { name: 'a2uicatalog', ... }`), which
    # would silently inflate the live-tool set this test compares against.
    start = src.index("const allTools = [")
    end = src.index("\n  ];", start)
    all_tools_src = src[start:end]
    live_names = set(re.findall(r"\{\s*name:\s*'([a-zA-Z_][a-zA-Z0-9_]*)'", all_tools_src))
    assert live_names, "could not find any tool names in tools.js's allTools array — regex or markers stale?"

    card = json.loads(_load(".well-known", "mcp", "server-card.json"))
    card_names = {t["name"] for t in card["tools"]}
    for t in card["tools"]:
        assert t["name"] in live_names, \
            f"server-card.json advertises tool '{t['name']}' which tools.js does not define"
    missing = live_names - card_names
    assert not missing, \
        f"tools.js defines tool(s) {sorted(missing)} that server-card.json does not advertise " \
        "— rerun `ops.py run mcp-server-card-sync`"


def test_pricing_md_states_the_real_limits():
    """Numbers here are promises. They must match the code that enforces them."""
    txt = _load("pricing.md")
    assert "Free" in txt
    render_js = os.path.join(ROOT, "..", "a2ui-private", "mcp-worker", "src", "render.js")
    if os.path.isfile(render_js):
        with open(render_js, encoding="utf-8") as f:
            assert "DAILY_LIMIT = 50" in f.read(), \
                "pricing.md claims 50/day for /api/render; render.js disagrees"
    assert "50 requests per day" in txt


def test_schema_map_feeds_exist():
    import re
    xml = _load("schema-map.xml")
    locs = re.findall(r"<loc>https://a2uicatalog\.ai(/[^<]+)</loc>", xml)
    assert locs, "schema-map.xml lists no feeds"
    for path in locs:
        assert os.path.isfile(os.path.join(PUBLIC, path.lstrip("/"))), \
            f"schema-map.xml advertises {path}, which is not published"


def test_robots_points_at_the_schema_map():
    assert "Schemamap: https://a2uicatalog.ai/schema-map.xml" in _load("robots.txt")


def test_section_llms_txt_link_only_published_paths():
    import re
    for section in ("docs", "atoms"):
        txt = _load(section, "llms.txt")
        assert txt.startswith("# A2UI Atomic Catalog"), f"{section}/llms.txt missing a titled heading"
        for path in re.findall(r"https://a2uicatalog\.ai(/[\w./-]+)", txt):
            if path.endswith("/") or "<" in path:
                continue
            local = os.path.join(PUBLIC, path.lstrip("/"))
            if os.path.splitext(path)[1]:
                assert os.path.isfile(local), f"{section}/llms.txt links {path}, not published"
