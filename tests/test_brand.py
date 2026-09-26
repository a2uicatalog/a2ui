"""Brand consistency as a build gate (visual side; check_brand.py covers the name/tagline strings).

atoms/brand-tokens.yaml is the single source; gen_brand.py stamps it into the site CSS/logo. Every
page that carries the site header must carry the CURRENT `/*brand-tokens:<hash>*/` marker, so a page
built before a token change, or one that hand-forked its palette, fails here instead of quietly
looking "random". Pages that do NOT carry the site chrome are declared debt in
tests/brand_exempt.json; the list can only shrink.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from _brand_generated import BRAND_HASH  # noqa: E402

EXEMPT = ROOT / "tests" / "brand_exempt.json"
SKIP_PARTS = ("/vendors/", "public-full", "renderer-bundle.html")


def _pages():
    for f in sorted((ROOT / "public").rglob("*.html")):
        rel = f.relative_to(ROOT).as_posix()
        if any(s in "/" + rel for s in SKIP_PARTS):
            continue
        yield rel, f.read_text(errors="ignore")


def test_generated_brand_outputs_are_current():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_brand.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_page_with_the_site_header_carries_the_current_brand_marker():
    marker = f"/*brand-tokens:{BRAND_HASH}*/"
    stale = [rel for rel, t in _pages() if 'class="site-header"' in t and marker not in t]
    assert not stale, (f"{len(stale)} page(s) carry the site header but not the current brand tokens "
                       f"(rebuild: ops.py run catalog-rebuild): {stale[:8]}")


def test_pages_without_the_site_chrome_are_declared_and_only_shrink():
    exempt = set(json.loads(EXEMPT.read_text())["pages"])
    bare = {rel for rel, t in _pages() if 'class="site-header"' not in t}
    new = sorted(bare - exempt)
    assert not new, (f"page(s) without the shared site header/tokens: {new}. Give them the shared chrome "
                     f"(generate_atom_pages.site_header + SITE_BASE_CSS); do not add to brand_exempt.json.")
    paid = sorted(exempt - bare)
    assert not paid, f"{paid} now carry the site header -- remove them from tests/brand_exempt.json."
