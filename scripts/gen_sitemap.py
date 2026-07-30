#!/usr/bin/env python3
"""Generate public/sitemap.xml from real build output.

Walks public/ for every index.html (the page convention this repo uses),
skipping paths robots.txt already Disallows (try/, frugal-ai-ops/) — no
point telling crawlers about a page and blocking them from it in the same
breath. Must run AFTER the other generators in deploy.yml so it reflects
the actual build, not a partial tree.

No <lastmod>: file mtimes on a fresh CI checkout are not a meaningful
freshness signal and would make the output non-deterministic across an
otherwise-identical rebuild.
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(ROOT, "public")
BASE_URL = "https://a2uicatalog.ai"

EXCLUDE_PREFIXES = ("try/", "frugal-ai-ops/")


def collect_urls():
    urls = []
    for dirpath, _dirnames, filenames in os.walk(PUBLIC):
        if "index.html" not in filenames:
            continue
        rel_dir = os.path.relpath(dirpath, PUBLIC)
        rel_dir = "" if rel_dir == "." else rel_dir + "/"
        if rel_dir.startswith(EXCLUDE_PREFIXES):
            continue
        urls.append(f"{BASE_URL}/{rel_dir}")
    return sorted(set(urls))


def main():
    urls = collect_urls()
    if not urls:
        print("ERROR: no index.html pages found under public/ — refusing to "
              "write an empty sitemap", file=sys.stderr)
        sys.exit(1)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        lines.append(f"  <url><loc>{url}</loc></url>")
    lines.append("</urlset>")

    pages_path = os.path.join(PUBLIC, "sitemap-pages.xml")
    with open(pages_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {pages_path} ({len(urls)} urls)")

    # /sitemap.xml is a sitemap INDEX, not a flat list. The blog lives in a
    # SEPARATE Cloudflare Worker (a2ui-private/blog-worker owns
    # a2uicatalog.ai/blog*), so this repo cannot enumerate its URLs at build
    # time — for a while that meant the sitemap advertised 474 atom pages and
    # ZERO articles, pointing crawl budget at the thinnest content on the
    # domain. The blog generates its own /blog/sitemap.xml from its posts;
    # this index is what ties the two together under one submitted URL.
    idx = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
           f"  <sitemap><loc>{BASE_URL}/sitemap-pages.xml</loc></sitemap>",
           f"  <sitemap><loc>{BASE_URL}/blog/sitemap.xml</loc></sitemap>",
           "</sitemapindex>"]
    out_path = os.path.join(PUBLIC, "sitemap.xml")
    with open(out_path, "w") as f:
        f.write("\n".join(idx) + "\n")
    print(f"wrote {out_path} (index -> sitemap-pages.xml + blog/sitemap.xml)")


if __name__ == "__main__":
    main()
