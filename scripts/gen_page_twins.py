#!/usr/bin/env python3
"""Generate a Markdown twin (/<path>.md) for every sitemap page that lacks one.

Agent-readiness scanners (Ora rules release 3, 2026-11-10: "1 of 3 sampled
content pages do not [return markdown]: /about.md") expect /<path>.md next
to each content page. Atom pages and the homepage already have twins from
generate_atom_pages.py, and auth/pricing/sdks/versioning have hand-written
ones; this fills the rest from the built HTML so a page edit can never leave
its twin stale.

Reads public/sitemap-pages.xml for the page list. A twin is (re)written only
when it is missing or was written by this script (it carries the
`generated_by: gen_page_twins.py` front-matter line), so hand-written twins
are never touched. Runs after generate_atom_pages.py in deploy.yml.
"""
import html
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(ROOT, "public")
SITE = "https://a2uicatalog.ai"
MARK = "generated_by: gen_page_twins.py"

SKIP_TAGS = {"script", "style", "noscript", "svg", "template", "button", "form",
             "iframe", "canvas", "video", "audio", "select", "textarea", "nav", "header", "footer"}
# Live atom previews (surface pages render one per atom) are demo content, not page text.
SKIP_CLASSES = {"preview-box"}
BLOCK = {"p", "div", "section", "article", "aside", "figure", "figcaption", "blockquote",
         "ul", "ol", "table", "tr", "details", "summary", "dl", "dt", "dd", "main", "br", "hr"}


class _ToMarkdown(HTMLParser):
    """Small stdlib HTML -> Markdown pass: headings, paragraphs, lists, links,
    inline and block code, tables. Enough for a readable agent copy."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.in_main = False
        self.saw_main = False
        self.lists = []
        self.href = []
        self.pre = 0
        self.row = None
        self.rows_done = 0
        self.title = ""
        self.description = ""
        self._in_title = False
        self._title_done = False

    def _emit(self, s):
        self.out.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title" and not self._title_done and not self.skip:
            self._in_title = True
        if tag == "meta" and a.get("name") == "description":
            self.description = a.get("content", "")
        if tag == "main":
            self.in_main = self.saw_main = True
        if self.skip or tag in SKIP_TAGS or SKIP_CLASSES & set((a.get("class") or "").split()):
            if tag not in ("br", "hr", "img", "input", "meta", "link"):
                self.skip += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._emit("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
        elif tag == "li":
            depth = max(len(self.lists) - 1, 0)
            kind = self.lists[-1] if self.lists else ["ul", 0]
            kind[1] += 1
            bullet = f"{kind[1]}." if kind[0] == "ol" else "-"
            self._emit("\n" + "  " * depth + bullet + " ")
        elif tag == "a":
            self.href.append(a.get("href") or "")
            self._emit("[")
        elif tag == "pre":
            self.pre += 1
            self._emit("\n\n```\n")
        elif tag == "code" and not self.pre:
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.row.append("")
        elif tag == "img" and a.get("alt"):
            self._emit(a["alt"])
        elif tag in BLOCK:
            self._emit("\n\n")

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            self._title_done = True
        if tag == "main":
            self.in_main = False
        if self.skip:
            if tag in SKIP_TAGS or tag not in ("br", "hr", "img", "input", "meta", "link"):
                self.skip -= 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._emit("\n\n")
        elif tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
            self._emit("\n")
        elif tag == "a" and self.href:
            href = self.href.pop()
            if href.startswith("/"):
                href = SITE + href
            if href and not href.startswith(("#", "javascript:")):
                self._emit(f"]({href})")
            else:
                self._emit("]")
        elif tag == "pre":
            self.pre = max(self.pre - 1, 0)
            self._emit("\n```\n\n")
        elif tag == "code" and not self.pre:
            self._emit("`")
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "tr" and self.row is not None:
            cells = [re.sub(r"\s+", " ", c).strip().replace("|", "\\|") for c in self.row]
            if cells:
                self._emit("\n| " + " | ".join(cells) + " |")
                if self.rows_done == 0:
                    self._emit("\n|" + "---|" * len(cells))
                self.rows_done += 1
            self.row = None
        elif tag == "table":
            self.rows_done = 0
            self._emit("\n\n")
        elif tag in BLOCK:
            self._emit("\n\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
            return
        if self.skip:
            return
        if self.row is not None and self.row:
            self.row[-1] += data
            return
        if self.pre:
            self._emit(data)
        else:
            self._emit(re.sub(r"\s+", " ", data))


def _body_markdown(raw):
    """Prefer <main>; pages without one fall back to the whole <body>."""
    m = re.search(r"<main\b.*?</main>", raw, re.S | re.I)
    p = _ToMarkdown()
    p.feed(raw if not m else re.sub(r"<body\b.*", "", raw, flags=re.S | re.I) + m.group(0))
    text = "".join(p.out)
    lines = [ln.rstrip() for ln in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = re.sub(r"\[\s*\]\([^)]*\)", "", text)
    text = re.sub(r"(?m)^\s*Live preview\s*\n", "", text)
    text = re.sub(r"(?m)^ +(?=\[)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return p, text


def page_list():
    xml = open(os.path.join(PUBLIC, "sitemap-pages.xml"), encoding="utf-8").read()
    paths = []
    for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
        path = loc.replace(SITE, "").strip("/")
        if not path or path.startswith(("atoms", "blog")):
            continue
        paths.append(path)
    return paths


def render_twin(path):
    src = os.path.join(PUBLIC, path, "index.html")
    if not os.path.isfile(src):
        return None
    raw = open(src, encoding="utf-8").read()
    p, body = _body_markdown(raw)
    title = html.unescape(p.title).strip() or path
    desc = html.unescape(p.description).strip()
    if not body.lstrip().startswith("# "):
        body = f"# {title}\n\n{body}"
    front = ["---", f"title: {title}"]
    if desc:
        front.append(f"description: {desc}")
    front += [f"canonical: {SITE}/{path}/", MARK, "---", ""]
    return "\n".join(front) + "\n" + body + "\n"


def main():
    wrote = kept = 0
    for path in page_list():
        twin = os.path.join(PUBLIC, path + ".md")
        if os.path.exists(twin) and MARK not in open(twin, encoding="utf-8").read():
            kept += 1
            continue
        md = render_twin(path)
        if md is None:
            continue
        with open(twin, "w", encoding="utf-8") as f:
            f.write(md)
        wrote += 1
    print(f"✓ {wrote} page twins written, {kept} hand-written twins kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
