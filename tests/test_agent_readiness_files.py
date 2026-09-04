"""The agent-readiness artefacts must stay TRUE, not merely present.

Added 2026-08-02 alongside the server card, pricing.md and schema map. A static
file describing a live server is a file that goes stale silently — the whole
class of failure this repo spent two days gating against — so each assertion
here checks the artefact against the thing it describes rather than against
itself.
"""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(ROOT, "public")

sys.path.insert(0, str(Path(ROOT) / "scripts"))
import gen_openapi  # noqa: E402
import gen_server_card  # noqa: E402
import gen_trust_pages  # noqa: E402
import generate_ard_catalog  # noqa: E402

gen_openapi.main()
gen_trust_pages.main()
generate_ard_catalog.main([])


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

    Uses gen_server_card.live_tools() — the SAME import-and-execute
    extraction the generator itself uses — rather than a second,
    independent regex parse of tools.js. Two parsers of the same fact can
    disagree; a reformat of tools.js (prettier, a renamed allTools) would
    silently break a hand-rolled regex here without touching the
    generator at all. One source of truth for "what tools.js defines."

    mcp-worker is a sibling private repo, so skip when absent rather than
    fail — the public repo must still build standalone.
    """
    try:
        live = gen_server_card.live_tools()
    except FileNotFoundError:
        pytest.skip("mcp-worker not present (public repo standalone build)")
    live_names = {t["name"] for t in live}
    assert live_names, "tools.js's mcpTools(null) returned no tools — is tools.js broken?"

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


def test_developer_resource_pages_exist_and_include_product_name():
    """Developer resources must be discoverable at predictable URLs, with the product
    name explicitly present in <title> and headings (ora.ai developer-resource-discoverability)."""
    predictable_pages = [
        ("docs", "index.html"),
        ("api-docs", "index.html"),
        ("developers", "index.html"),
        ("auth", "index.html"),
        ("webhooks", "index.html"),
        ("versioning", "index.html"),
        ("pricing", "index.html"),
    ]
    for parts in predictable_pages:
        html = _load(*parts)
        assert "<title>" in html and "A2UI Atomic Catalog" in html.split("<title>")[1].split("</title>")[0], \
            f"{'/'.join(parts)} missing product name in <title>"
        assert "A2UI Atomic Catalog" in html, f"{'/'.join(parts)} missing product name in page body"
        # Must link to OpenAPI spec and MCP endpoint
        assert "/openapi.json" in html, f"{'/'.join(parts)} does not link to OpenAPI spec"
        assert "/mcp" in html, f"{'/'.join(parts)} does not link to MCP endpoint"


def test_predictable_redirects_route_correctly():
    """Predictable aliases must redirect to canonical doc pages, not bare generic 404/developers."""
    redirects_content = _load("_redirects")
    lines = [l.strip() for l in redirects_content.splitlines() if l.strip() and not l.startswith("#")]
    redirect_map = dict(l.split()[:2] for l in lines)

    assert redirect_map.get("/api-docs") == "/api-docs/"
    assert redirect_map.get("/docs") == "/docs/"
    assert redirect_map.get("/developer") == "/developers/"
    assert redirect_map.get("/developer-portal") == "/developers/"
    assert redirect_map.get("/swagger.json") == "/openapi.json"
    assert redirect_map.get("/openapi.yaml") == "/openapi.json"
    assert redirect_map.get("/.well-known/openapi.json") == "/openapi.json"
    assert redirect_map.get("/auth") == "/auth/"
    assert redirect_map.get("/security") == "/auth/"
    assert redirect_map.get("/docs/auth") == "/auth/"
    assert redirect_map.get("/webhooks") == "/webhooks/"
    assert redirect_map.get("/webhook") == "/webhooks/"
    assert redirect_map.get("/events") == "/webhooks/"
    assert redirect_map.get("/versioning") == "/versioning/"
    assert redirect_map.get("/deprecation") == "/versioning/"
    assert redirect_map.get("/pricing") == "/pricing/"
    assert redirect_map.get("/ard.json") == "/.well-known/ard.json"


def test_openapi_documents_and_async_job_pattern():
    """OpenAPI 3.1 specifications in JSON and YAML format, including async job pattern definitions."""
    openapi_json = json.loads(_load("openapi.json"))
    assert openapi_json["openapi"] == "3.1.0"
    assert "/api/render/batch" in openapi_json["paths"]
    assert "202" in openapi_json["paths"]["/api/render/batch"]["post"]["responses"]
    assert "/api/render/jobs/{id}" in openapi_json["paths"]
    assert "JobEnvelope" in openapi_json["components"]["schemas"]
    assert "JobStatus" in openapi_json["components"]["schemas"]

    import yaml
    openapi_yaml_txt = _load("openapi.yaml")
    parsed_yaml = yaml.safe_load(openapi_yaml_txt)
    assert parsed_yaml["openapi"] == "3.1.0"
    assert "/api/render/batch" in parsed_yaml["paths"]


def test_ard_catalog_and_discovery():
    """ARD v0.91 resource discovery catalog must exist at /.well-known/ard.json and be valid JSON."""
    ard_txt = _load(".well-known", "ard.json")
    ard = json.loads(ard_txt)
    assert ard.get("specVersion") == "1.0"
    assert ard.get("host", {}).get("displayName") == "A2UI Atomic Catalog"
    assert len(ard.get("entries", [])) > 0

    # Also verify backward compatible legacy file exists
    legacy = json.loads(_load(".well-known", "ai-catalog.json"))
    assert len(legacy.get("entries", [])) == len(ard.get("entries", []))

    robots = _load("robots.txt")
    assert "Agentmap: /.well-known/ard.json" in robots


def test_homepage_developer_resource_links():
    """Homepage must prominently link to documentation, developer portal, and ARD catalog."""
    html = _load("index.html")
    assert "/docs" in html
    assert "/.well-known/ard.json" in html
    assert 'rel="ard-catalog"' in html


def test_api_catalog_and_llms_advertise_developer_resources():
    """RFC 9727 api-catalog and llms.txt must advertise docs, openapi, mcp, and auth."""
    llms_txt = _load("llms.txt")
    assert "/docs/" in llms_txt or "/developers/" in llms_txt
    assert "/openapi.json" in llms_txt
    assert "/mcp" in llms_txt
    assert "/auth/" in llms_txt or "/auth.md" in llms_txt
    assert "/webhooks/" in llms_txt
    assert "/versioning/" in llms_txt or "/versioning.md" in llms_txt
    assert "/pricing/" in llms_txt or "/pricing.md" in llms_txt

    api_catalog = json.loads(_load(".well-known", "api-catalog"))
    linkset = api_catalog["linkset"][0]
    all_hrefs = [entry["href"] for group in ("describedby", "service-desc", "item", "describes")
                 for entry in linkset.get(group, [])]
    for required in (
        "https://a2uicatalog.ai/openapi.json",
        "https://a2uicatalog.ai/mcp",
        "https://a2uicatalog.ai/docs/",
        "https://a2uicatalog.ai/auth/",
        "https://a2uicatalog.ai/webhooks/",
        "https://a2uicatalog.ai/versioning/",
        "https://a2uicatalog.ai/pricing/",
    ):
        assert required in all_hrefs, f"api-catalog missing required developer resource link: {required}"

