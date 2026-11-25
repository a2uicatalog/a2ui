"""The home page (round-2 design 2, 2026-11-20): every number follows the data, every internal link resolves, the outline is clean, the film is gone, the
lockup line is on the home header only, and the specimen tiles and hero payload use only real atoms and declared fields. Parses the generated
public/index.html, so run scripts/generate_atom_pages.py first."""
import importlib.util
import json
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
HOME = (PUBLIC / "index.html").read_text(encoding="utf-8")
SPEC = json.loads((PUBLIC / "spec.json").read_text(encoding="utf-8"))["atoms"]
MATRIX = json.loads((PUBLIC / "catalogue" / "renderer-matrix-v1.json").read_text(encoding="utf-8"))
# Routes the Cloudflare workers answer; there is no file for them in public/.
WORKER_ROUTES = {"/mcp", "/blog", "/mcp-docs", "/api/sketch-demo"}

sys.path.insert(0, str(ROOT / "renderers"))
_spec = importlib.util.spec_from_file_location("gap_home", ROOT / "scripts" / "generate_atom_pages.py")
gap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gap)


def _stat(label):
    m = re.search(r'<span class="stat-num">([^<]+)</span><span class="stat-lbl">' + re.escape(label) + "<", HOME)
    assert m, label
    return m.group(1)


def test_counts_equal_the_data():
    assert _stat("Typed atoms") == str(len(SPEC))
    assert _stat("Renderers") == str(len(MATRIX["renderers"]))
    surfaces = {s for a in SPEC for s in ((a.get("surfaces") or {}).get("works_on") or [])}
    assert _stat("Surfaces") == str(len(surfaces))
    assert _stat("A2UI spec") == gap.A2UI_SPEC_VERSION
    n = len(SPEC)
    for phrase in (f"Explore {n} atoms", f"Search all {n} atoms", f"Search and preview {n} atoms"):
        assert phrase in HOME, phrase
    assert f"Draws with {len(MATRIX['renderers'])} renderers" in HOME


def test_chips_equal_the_renderer_ids():
    chips = re.findall(r'<li data-renderer="([^"]+)">([^<]+)</li>', HOME)
    assert [c[0] for c in chips] == list(MATRIX["renderers"])
    assert [c[1] for c in chips] == [r["name"] for r in MATRIX["renderers"].values()]


class _Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.levels, self.tags = [], [], []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.levels.append(int(tag[1]))


def _page(html=HOME):
    p = _Page()
    p.feed(html)
    return p


def _redirects():
    out = set()
    for line in (PUBLIC / "_redirects").read_text().splitlines():
        parts = line.split()
        if parts and not line.startswith("#"):
            out.add(parts[0])
    return out


def test_every_internal_href_resolves():
    redirects = _redirects()
    bad = []
    for h in _page().hrefs:
        if h.startswith(("http://", "https://", "mailto:")):
            continue
        path = h.split("#")[0].split("?")[0]
        if not path:
            continue   # a bare #fragment
        rel = path.lstrip("/")
        ok = (PUBLIC / rel).is_file() or (PUBLIC / rel / "index.html").is_file() or path in WORKER_ROUTES or path in redirects or re.fullmatch(r"/blog/\d{3}-[a-z0-9-]+/?", path) is not None   # an article served by the blog worker (the latest-post pill)
        if not ok:
            bad.append(h)
    assert not bad, bad


def test_one_h1_and_ordered_headings():
    lv = _page().levels
    assert lv.count(1) == 1 and lv[0] == 1
    prev = 0
    for l in lv:
        assert l <= prev + 1, lv
        prev = l


def test_no_video_and_no_film_on_home():
    for needle in ("<video", "film-hero", "data-film", "film-poster", 'class="mf '):
        assert needle not in HOME, needle


def test_lockup_on_home_only():
    line = gap.BRAND_LOCKUP
    assert line == "Where user and agent experience converge"
    hdr = HOME[HOME.index('<header class="site-header"'):HOME.index("</header>")]
    assert hdr.count(line) == 1 and 'class="brand-sub"' in hdr
    assert line not in gap.site_header("") and line in gap.site_header("", lockup=True)
    others = [PUBLIC / "atoms" / "index.html", PUBLIC / "what-is-a2ui" / "index.html", PUBLIC / "docs" / "index.html",
              PUBLIC / "renderers" / "index.html", PUBLIC / "about" / "index.html", PUBLIC / "atoms" / "stat_card" / "index.html"]
    for f in others:
        assert line not in f.read_text(encoding="utf-8"), f


def test_inline_listing_is_gone_and_the_explorer_is_linked():
    for needle in ('class="atom-card"', 'id="search"', 'class="filters"', 'id="grid"'):
        assert needle not in HOME, needle
    assert HOME.count('href="/atoms/"') >= 4
    assert "Illustrations of what an agent composes" in HOME and "Illustrative payload" in HOME


def test_spotlight_keeps_the_form_and_closes_the_long_text():
    assert 'id="sketch-demo-prompt"' in HOME and 'id="sketch-demo-submit"' in HOME and "/api/sketch-demo" in HOME
    m = re.search(r"<details class=\"spot-details\"[^>]*>", HOME)
    assert m and "open" not in m.group(0)
    det = HOME[m.start():HOME.index("</details>", m.start())]
    for needle in ("250 elements", "XML", "allowlist"):
        assert needle in det
    assert "250 elements" not in HOME.replace(det, "")
    assert "what-is-an-a2ui-catalog" in HOME and "list_catalogs" in HOME and "render_surface" in HOME and "/catalogue/index.json" in HOME


def test_agent_readiness_links_and_ard_link_survive():
    for needle in ('rel="ai-catalog"', 'rel="ard-catalog"', 'rel="api-catalog"', 'hreflang="fr"', 'rel="canonical"', "application/ld+json", 'class="skip-link"'):
        assert needle in HOME, needle
    assert ">ARD catalog</a>" in HOME and "https://github.com/a2uicatalog/a2ui" in HOME
    assert 'class="theme-btn"' in HOME and 'class="menu-btn"' in HOME and 'class="gh-pill"' in HOME


def test_tiles_and_payload_use_real_atoms_and_declared_fields():
    declared = {a["type"]: set((a.get("fields") or {}).keys()) for a in SPEC}
    assert len(gap.HOME_TILES) == 8
    for atom, fields in gap.HOME_TILES:
        assert atom in declared, atom
        assert set(fields) <= declared[atom], (atom, set(fields) - declared[atom])
    p = gap.HOME_HERO_PAYLOAD
    assert p["type"] in declared and set(p) - {"type"} <= declared[p["type"]]
    assert re.findall(r'<article class="card tile" data-atom="([^"]+)"', HOME) == [t for t, _ in gap.HOME_TILES]
    shown = json.loads(re.search(r'<pre class="flow-code" tabindex="0"><code>(.*?)</code></pre>', HOME, re.S).group(1).replace("&quot;", '"'))
    assert shown == p


def test_the_build_fails_clearly_for_a_missing_atom_or_field():
    atoms = [{"type": "stat_card", "fields": {"value": "string"}}]
    with pytest.raises(SystemExit, match="not in the catalog"):
        gap._home_check(atoms, tiles=[("no_such_atom", {})], payload={"type": "stat_card", "value": 1})
    with pytest.raises(SystemExit, match="not declared"):
        gap._home_check(atoms, tiles=[("stat_card", {"bogus": 1})], payload={"type": "stat_card", "value": 1})
    gap._home_check(atoms, tiles=[("stat_card", {"value": "1"})], payload={"type": "stat_card", "value": 1})


def test_svgs_are_hidden_or_named():
    for m in re.finditer(r"<svg\b[^>]*>(.*?)</svg>", re.sub(r"<script\b.*?</script>", "", HOME[HOME.index("<main"):], flags=re.S), re.S):
        tag = m.group(0)[:m.group(0).index(">") + 1]
        assert 'aria-hidden="true"' in tag or ('role="img"' in tag and ("<title>" in m.group(1) or 'aria-label="' in tag)), tag[:120]


def test_latest_post_slot_with_and_without_a_data_file():
    assert not gap.HOME_LATEST_POST.exists() or ">LATEST<" in HOME
    absent = gap._home_latest_pill(Path(tempfile.gettempdir()) / "no-such-latest-post.json")
    assert 'href="/what-is-a2ui/"' in absent and "plain-English guide" in absent
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "latest-post.json"
        f.write_text(json.dumps({"title": "Rich UI <in> Gemini", "slug": "023-rich-ui", "date": "2026-11-20"}))
        pill = gap._home_latest_pill(f)
        assert 'href="/blog/023-rich-ui"' in pill and "Rich UI &lt;in&gt; Gemini · 2026-11-20" in pill and ">LATEST<" in pill
        f.write_text(json.dumps({"title": "T", "slug": "s", "date": "2026-11-20", "pin_label": "FRESH"}))
        assert ">FRESH<" in gap._home_latest_pill(f)
        f.write_text(json.dumps({"title": "T", "slug": "../x", "date": "20 Nov"}))
        with pytest.raises(SystemExit):
            gap._home_latest_pill(f)


def test_home_has_ora_brand_terms_and_json_ld_below_main():
    # Ora (2026-11-18 scan): brand search needs JSON-LD keywords/knowsAbout or a meta keywords tag, and it counts the
    # JSON-LD text as text before the main content (limit 5,000 characters), so the block sits after </main>.
    assert 'name="keywords"' in HOME and '"knowsAbout"' in HOME and '"keywords"' in HOME
    assert HOME.index("application/ld+json") > HOME.index("</main>")
