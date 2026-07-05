#!/usr/bin/env python3
"""
Dereference every URL in the published discovery documents against the
public/ build output. A discovery document that points at a URL which
doesn't exist in the deploy artifact is a build failure, not a runtime
surprise — this is what let /spec.json 404 for weeks while ai-catalog.json
stayed structurally "compliant".

Checks:
  public/.well-known/ai-catalog.json — every "url" field, recursively
  public/spec.json                   — compactIndex and runbooks pointers

A URL passes if its path maps to a file in public/: exact file, or
<path>/index.html for pretty paths.

Run:
  python3 scripts/check_catalog_links.py
"""
import json
import os
import sys
from urllib.parse import urlparse

ROOT = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(ROOT, "public")
OWN_HOSTS = {"a2uicatalog.ai", "www.a2uicatalog.ai"}


def collect_urls(node, found):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("url", "compactIndex", "runbooks", "fullSpec") and isinstance(value, str):
                found.append(value)
            else:
                collect_urls(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_urls(item, found)


def path_exists(url_path):
    rel = url_path.lstrip("/")
    candidates = [
        os.path.join(PUBLIC, rel),
        os.path.join(PUBLIC, rel, "index.html"),
    ]
    return any(os.path.isfile(c) for c in candidates)


def main():
    docs = [
        os.path.join(PUBLIC, ".well-known", "ai-catalog.json"),
        os.path.join(PUBLIC, "spec.json"),
    ]
    urls = []
    for doc in docs:
        if not os.path.isfile(doc):
            print(f"❌ missing document: {doc}", file=sys.stderr)
            sys.exit(1)
        with open(doc) as f:
            collect_urls(json.load(f), urls)

    checked, dead = 0, []
    for url in urls:
        parsed = urlparse(url)
        if parsed.hostname not in OWN_HOSTS:
            continue  # external URLs are not part of the deploy artifact
        checked += 1
        if not path_exists(parsed.path):
            dead.append(url)

    if dead:
        print(f"❌ {len(dead)} dead link(s) in discovery documents:", file=sys.stderr)
        for url in dead:
            print(f"   {url}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ {checked} own-host URLs dereferenced against public/ — all resolve")


if __name__ == "__main__":
    main()
