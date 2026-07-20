#!/usr/bin/env python3
"""render_atom_html.py — A2UI payload JSON in, rendered HTML fragment out.

Thin CLI wrapper around renderers.web_article.render(), for cross-repo reuse
(e.g. a2ui-private/blog-worker's generate_blog_pages.py splicing a graduated
atom into a blog post) without a direct Python import across repos.

Usage:
    python3 scripts/render_atom_html.py payload.a2ui.json
    python3 scripts/render_atom_html.py payload.a2ui.json --theme dark
    python3 scripts/render_atom_html.py payload.a2ui.json --out fragment.html
    cat payload.a2ui.json | python3 scripts/render_atom_html.py -

Payload is `{"title", "theme", "blocks": [...]}` (blocks keyed by "type",
per a2ui-private/CLAUDE.md's payload contract) or a bare `[...]` block list.
"""
import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from renderers.web_article import render as wa_render


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("payload", help="Path to payload JSON, or '-' for stdin")
    ap.add_argument("--theme", default=None, help="Override theme ('light' or 'dark'); defaults to the payload's own 'theme' field, then 'light'")
    ap.add_argument("--out", default=None, help="Write HTML fragment to this path instead of stdout")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.payload == "-" else Path(args.payload).read_text(encoding="utf-8")
    data = json.loads(raw)

    if isinstance(data, list):
        blocks, payload_theme = data, "light"
    elif isinstance(data, dict):
        blocks = data.get("blocks")
        if blocks is None:
            print(f"error: payload has no \"blocks\" list: {args.payload}", file=sys.stderr)
            sys.exit(1)
        payload_theme = data.get("theme", "light")
    else:
        print(f"error: payload must be a JSON object or block list, got {type(data).__name__}: {args.payload}", file=sys.stderr)
        sys.exit(1)

    html = wa_render(blocks, theme=args.theme or payload_theme)

    if args.out:
        Path(args.out).write_text(html, encoding="utf-8")
        print(f"✓ {len(blocks)} blocks → {args.out} ({len(html):,} bytes)", file=sys.stderr)
    else:
        print(html)


if __name__ == "__main__":
    main()
