#!/usr/bin/env python3
"""Generate public/sitemap.xml from real build output.

Walks public/ for every index.html (the page convention this repo uses),
skipping paths robots.txt already Disallows (try/, frugal-ai-ops/) — no
point telling crawlers about a page and blocking them from it in the same
breath. Must run AFTER the other generators in deploy.yml so it reflects
the actual build, not a partial tree.

<lastmod> comes from real git commit history (each page's most recent
commit touching its index.html), not file mtimes — mtimes on a fresh CI
checkout are all just "checkout time," not a meaningful freshness signal,
and would make the output non-deterministic across an otherwise-identical
rebuild. git history has neither problem: it's the same regardless of
when/where it's checked out. An agent-readiness finding (2026-08-16) asked
for lastmod on at least half the sampled entries; pages with no git
history yet (freshly generated, not committed) simply omit <lastmod>
rather than fabricate a date — real coverage on real pages, not 100% via
invented ones.
"""
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(ROOT, "public")
BASE_URL = "https://a2uicatalog.ai"

EXCLUDE_PREFIXES = ("try/", "frugal-ai-ops/")


def collect_urls():
    """Returns (url, repo-relative index.html path) pairs — the path is
    what git_lastmod_map()'s keys are, so main() can join the two."""
    urls = []
    for dirpath, _dirnames, filenames in os.walk(PUBLIC):
        if "index.html" not in filenames:
            continue
        rel_dir = os.path.relpath(dirpath, PUBLIC)
        rel_dir = "" if rel_dir == "." else rel_dir + "/"
        if rel_dir.startswith(EXCLUDE_PREFIXES):
            continue
        rel_file = os.path.join("public", rel_dir, "index.html").replace(os.sep, "/")
        urls.append((f"{BASE_URL}/{rel_dir}", rel_file))
    return sorted(set(urls))


def git_lastmod_map():
    """repo-relative path -> ISO 8601 date of its most recent commit.

    One `git log` walk over the whole public/ tree, not one process per
    file — several hundred individual `git log` calls would be slow, and
    this repo's other generators batch exactly this kind of thing rather
    than shell out per item. `git log` defaults to reverse-chronological
    order, so the FIRST time a path is seen below is its most recent
    commit — never overwritten after that.

    Returns {} (not an error) if git isn't available or the walk fails —
    a sitemap with no <lastmod> anywhere is a strictly worse but still
    valid fallback, not something worth failing the build over.
    """
    try:
        out = subprocess.run(
            ["git", "log", "--name-only", "--format=%x00%cI", "--", "public/"],
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=30,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError,
            subprocess.TimeoutExpired, OSError):
        return {}
    lastmod = {}
    current_date = None
    for line in out.splitlines():
        if line.startswith("\x00"):
            current_date = line[1:]
            continue
        if not line.strip() or current_date is None:
            continue
        lastmod.setdefault(line, current_date)
    return lastmod


def main():
    urls = collect_urls()
    if not urls:
        print("ERROR: no index.html pages found under public/ — refusing to "
              "write an empty sitemap", file=sys.stderr)
        sys.exit(1)

    lastmod_map = git_lastmod_map()
    with_date = 0

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url, relpath in urls:
        lastmod = lastmod_map.get(relpath)
        if lastmod:
            with_date += 1
            lines.append(f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>")
        else:
            lines.append(f"  <url><loc>{url}</loc></url>")
    lines.append("</urlset>")

    pages_path = os.path.join(PUBLIC, "sitemap-pages.xml")
    with open(pages_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {pages_path} ({len(urls)} urls, {with_date} with lastmod)")

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
