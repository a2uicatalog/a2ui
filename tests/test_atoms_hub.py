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
    links = re.findall(r'<li data-q="[^"]*"(?: data-c="[^"]*")?><a href="/atoms/([a-z0-9_]+)/">', s)
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


def test_atom_pages_page_through_every_atom_category_by_category():
    # Owner 2026-11-01: a "next" shortcut on the atom pages, ideally on the keyboard. Design pass 2026-11-05: the order is
    # category by category (A to Z inside each) so neighbours are related, the pager says "i of n" in the category, and it wraps.
    packs = yaml.safe_load((ROOT / "atoms" / "atom-packs.yaml").read_text())
    cat = {t: cid[len("a2ui-"):-len("-v1")] for cid, types in packs.items() if isinstance(types, list) for t in types}
    published = set(_published())
    link = lambda s, rel: re.search(r'<a [^>]*rel="' + rel + r'" href="/atoms/([a-z0-9_]+)/"', s).group(1)
    start = sorted(published)[0]
    seen, t = [], start
    while True:
        s = (ROOT / "public" / "atoms" / t / "index.html").read_text()
        assert "ArrowRight" in s and 'nav.atom-pager a[rel="' in s, t
        nxt = link(s, "next")
        assert link((ROOT / "public" / "atoms" / nxt / "index.html").read_text(), "prev") == t, t
        seen.append(t); t = nxt
        if t == start:
            break
        assert t not in seen, t
    assert sorted(seen) == sorted(published)
    # one contiguous run per category, A to Z inside it, and the position shown matches
    runs = [c for i, c in enumerate(cat[x] for x in seen) if i == 0 or cat[seen[i - 1]] != c]
    assert len(runs) - (runs[0] == runs[-1] and len(runs) > 1) == len(set(runs)), runs
    for c in set(runs):
        members = [x for x in seen if cat[x] == c]
        assert members == sorted(members) or members[1:] + members[:1] == sorted(members), c
        first = sorted(members)[0]
        assert f'<span class="pg-pos">1 of {len(members)}</span>' in (ROOT / "public" / "atoms" / first / "index.html").read_text(), first


def test_atom_pages_cross_promote_three_related_atoms():
    # Design pass 2026-11-05: "More like this" shows three other published atoms, at least one from another category, plus "Keep exploring".
    packs = yaml.safe_load((ROOT / "atoms" / "atom-packs.yaml").read_text())
    cat = {t: cid[len("a2ui-"):-len("-v1")] for cid, types in packs.items() if isinstance(types, list) for t in types}
    published = set(_published())
    for t in sorted(published):
        s = (ROOT / "public" / "atoms" / t / "index.html").read_text()
        sec = s[s.index('<section class="x-more"'):s.index('</section>', s.index('<section class="x-more"'))]
        rel = re.findall(r'<a class="x-card[^"]*" href="/atoms/([a-z0-9_]+)/">', sec)
        assert len(rel) == 3 and len(set(rel)) == 3 and t not in rel and set(rel) <= published, (t, rel)
        assert any(cat[r] != cat[t] for r in rel) or all(cat[x] == cat[t] for x in published), (t, rel)
        assert 'class="x-up"' in s and 'rel="next"' in s, t


def test_every_atom_shows_its_catalog_and_the_hub_filters_cover_all_atoms():
    # Owner 2026-11-01: a category button, which also shows the catalogs agents are routed through.
    # The category is the atom's A2UI catalog from atoms/atom-packs.yaml (each atom in exactly one).
    packs = yaml.safe_load((ROOT / "atoms" / "atom-packs.yaml").read_text())
    cat = {t: cid[len("a2ui-"):-len("-v1")] for cid, types in packs.items() if isinstance(types, list) for t in types}
    hub = HUB.read_text()
    for t in _published():
        s = (ROOT / "public" / "atoms" / t / "index.html").read_text()
        assert f'class="cat-chip" href="/atoms/?catalog={cat[t]}"' in s, t
        assert f'data-c="{cat[t]}"><a href="/atoms/{t}/">' in hub, t
    counts = [int(n) for n in re.findall(r'<button type="button" class="hub-cat" data-c="[a-z-]+" aria-pressed="false">[^<]*<span>(\d+)</span>', hub)]
    assert sum(counts) == len(_published())
