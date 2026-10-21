"""The homepage heading outline must never skip a level (is-agentic.com
finding, 2026-10-21: H1 went straight to H3 atom cards). Parses the generated
public/index.html, so run it after scripts/generate_atom_pages.py."""
from html.parser import HTMLParser
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "public" / "index.html"


class _Headings(HTMLParser):
    def __init__(self):
        super().__init__()
        self.levels = []

    def handle_starttag(self, tag, attrs):
        if len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.levels.append((int(tag[1]), self.getpos()[0]))


def heading_levels(html: str):
    p = _Headings()
    p.feed(html)
    return p.levels


def test_exactly_one_h1_and_first_heading_is_h1():
    lv = heading_levels(INDEX.read_text())
    assert [l for l, _ in lv].count(1) == 1
    assert lv[0][0] == 1


def test_no_heading_level_is_skipped():
    prev = 0
    bad = []
    for level, line in heading_levels(INDEX.read_text()):
        if level > prev + 1:
            bad.append(f"h{prev} -> h{level} at line {line}")
        prev = level
    assert not bad, bad[:5]


def test_parser_catches_a_skip():
    assert heading_levels("<h1>a</h1><h3>b</h3>") == [(1, 1), (3, 1)]
