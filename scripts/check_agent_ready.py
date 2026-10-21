#!/usr/bin/env python3
"""Live agent-readiness regression check for the public site.

Usage: python3 scripts/check_agent_ready.py [BASE_URL] [--retries N] [--delay S]
Default BASE_URL is https://a2uicatalog.ai. Exits 1 if any check fails after
the retries (retries absorb deploy propagation). Stdlib only. Read-only GETs.

Checks (is-agentic.com findings, 2026-10-21):
  1. Accept: text/markdown on a nonexistent path -> 404 + text/markdown body
     of >= 20 chars.
  2. The homepage heading outline never skips a level.
"""
import argparse
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser


def fetch(url, accept):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "a2ui-ci-check/1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:  # 4xx/5xx still carry a body
        return e.code, e.headers, e.read()


class _H(HTMLParser):
    def __init__(self):
        super().__init__()
        self.levels = []

    def handle_starttag(self, tag, attrs):
        if len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.levels.append((int(tag[1]), self.getpos()[0]))


def skipped_levels(html):
    p = _H()
    p.feed(html)
    prev, bad = 0, []
    for lvl, line in p.levels:
        if lvl > prev + 1:
            bad.append(f"h{prev}->h{lvl} at line {line}")
        prev = lvl
    return bad


def check_markdown_404(base):
    status, h, body = fetch(f"{base}/ci-check-does-not-exist-{int(time.time())}", "text/markdown")
    ct = h.get("Content-Type", "")
    errs = []
    if status != 404:
        errs.append(f"status {status}, want 404")
    if not ct.lower().startswith("text/markdown"):
        errs.append(f"Content-Type {ct!r}, want text/markdown")
    if len(body) < 20:
        errs.append(f"body only {len(body)} bytes")
    return errs


def check_headings(base):
    status, _, body = fetch(f"{base}/", "text/html")
    if status != 200:
        return [f"homepage status {status}"]
    return skipped_levels(body.decode("utf-8", "replace"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?", default="https://a2uicatalog.ai")
    ap.add_argument("--retries", type=int, default=6)
    ap.add_argument("--delay", type=float, default=10)
    a = ap.parse_args()
    base = a.base.rstrip("/")
    checks = [("markdown 404", check_markdown_404), ("homepage heading levels", check_headings)]
    failed = False
    for name, fn in checks:
        for attempt in range(1, a.retries + 1):
            try:
                errs = fn(base)
            except Exception as e:  # network blip: treat as a failed attempt
                errs = [f"{type(e).__name__}: {e}"]
            if not errs:
                print(f"PASS {name}")
                break
            print(f"try {attempt}/{a.retries} {name}: {'; '.join(errs)}")
            if attempt < a.retries:
                time.sleep(a.delay)
        else:
            print(f"FAIL {name}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
