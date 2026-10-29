"""/atoms/ hub: one crawlable page linking every published atom page.

/atoms/ was a 404 until 2026-10-29 (Search Console URL Inspection), so atom
pages had no parent page and Google reached them only through the homepage
grid and the sitemap. These pin the hub to the published set and keep the
atom-page breadcrumb pointing at it."""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / "public" / "atoms" / "index.html"


def _published():
    blocks = yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]
    return {b["type"] for b in blocks
            if b.get("type") and b.get("stage", "stable") == "stable" and b.get("visibility") != "private"}


def test_hub_links_every_published_atom_once_with_trailing_slash():
    s = HUB.read_text()
    links = re.findall(r'<li data-q="[^"]*"><a href="/atoms/([a-z0-9_]+)/">', s)
    assert len(links) == len(set(links))
    assert set(links) == _published()


def test_hub_is_canonical_and_its_jsonld_counts_match():
    s = HUB.read_text()
    assert '<link rel="canonical" href="https://a2uicatalog.ai/atoms/">' in s
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', s).group(1).replace("<\\/", "</"))
    page = next(g for g in ld["@graph"] if g["@type"] == "CollectionPage")
    items = page["mainEntity"]["itemListElement"]
    assert page["mainEntity"]["numberOfItems"] == len(items) == len(_published())
    assert all(i["url"].startswith("https://a2uicatalog.ai/atoms/") and i["url"].endswith("/") for i in items)


def test_hub_markdown_twin_lists_the_same_atoms():
    md = (ROOT / "public" / "atoms.md").read_text()
    assert set(re.findall(r"\(https://a2uicatalog\.ai/atoms/([a-z0-9_]+)/\)", md)) == _published()


def test_atom_page_breadcrumb_points_at_the_hub():
    for t in ("treemap", "motion_transition", "badge"):
        s = (ROOT / "public" / "atoms" / t / "index.html").read_text()
        assert f'<a href="/atoms/">atoms</a> / {t}' in s
        ld = json.loads(re.search(r'<script type="application/ld\+json">(\{"@context".*?)</script>', s).group(1).replace("<\\/", "</"))
        crumbs = next(g for g in ld["@graph"] if g["@type"] == "BreadcrumbList")["itemListElement"]
        assert [c["item"] for c in crumbs] == ["https://a2uicatalog.ai/", "https://a2uicatalog.ai/atoms/",
                                               f"https://a2uicatalog.ai/atoms/{t}/"]
