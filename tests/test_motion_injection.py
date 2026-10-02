"""Injection check for every motion atom (2026-10-01): each declared field gets attack strings in three shapes (string, list, list of
objects); the Python renderer's OUTPUT is parsed with a real HTML parser and must contain nothing the payload created: no injected
element, no on* handler calling the canary, no script body, no javascript: URL, no javascript:/alert( in a style. New motion atoms
are covered automatically because the atom list comes from the schema. The full-catalogue fuzz (JS renderer, plus real-browser
execution) lives in a2ui-private/security/xss-fuzz; this is the public tripwire that runs with the normal suite."""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from renderers import web_article as wa  # noqa: E402

TAG = '"><img src=x onerror=alert(1)>\'"><svg onload=alert(1)></script><script>alert(4)</script>'
CSS = 'red;background:url(javascript:alert(2))" onmouseover="alert(3)\' onfocus=\'alert(5)'
NQ = "x onmouseover=alert(11) y"
CODE = ["';alert(7);//", '";alert(8);//', "</script><script>alert(4)</script>", "javascript:alert(9)"]
KEYS = ("text", "label", "title", "value", "color", "accent", "name", "href", "url", "src", "icon", "caption", "d", "x", "y")
JS_STR = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hits, self.script = set(), False

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            v = v or ""
            if k.startswith("on") and re.search(r"alert\(\d+\)", JS_STR.sub('""', v)):
                self.hits.add("handler")
            if k == "style" and ("javascript:" in v or "alert(" in v):
                self.hits.add("style-inject")
            if k in ("href", "src", "xlink:href", "action") and v.strip().lower().startswith("javascript:"):
                self.hits.add("js-url")
        if tag in ("img", "svg") and any(k in ("onerror", "onload") and "alert(" in (v or "") for k, v in attrs):
            self.hits.add("tag-inject")
        if tag == "script":
            self.script = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.script = False

    def handle_data(self, d):
        if self.script and re.match(r"\s*alert\(\d+\)", d):
            self.hits.add("script-body")


def _motion_atoms():
    blocks = yaml.safe_load((ROOT / "atoms" / "schema.yaml").read_text())["blocks"]
    return [(a["type"], list((a.get("fields") or {}).keys())) for a in blocks if a["type"].startswith("motion_")]


def test_motion_atoms_are_listed():
    assert len(_motion_atoms()) >= 26


def test_no_motion_atom_field_can_inject():
    wa._mo_install()
    wa._gd_install()
    leaks = []
    for typ, fields in _motion_atoms():
        for f in fields:
            for payload in [TAG, CSS, NQ] + CODE:
                for v in (payload, [payload], [{k: payload for k in KEYS}]):
                    blk = {"type": typ, f: v}
                    if typ in ("motion_layer", "motion_group", "motion_mask", "motion_shake", "motion_device", "motion_repeat", "motion_wiggle"):
                        blk.setdefault("blocks", [{"type": "motion_pill", "text": payload, "href": payload}])
                    try:
                        out = wa._RENDERERS[typ](blk)
                    except Exception:  # a renderer may refuse hostile input; refusing is safe
                        continue
                    s = Scan()
                    s.feed(out)
                    if s.hits:
                        leaks.append((typ, f, sorted(s.hits)))
    assert not leaks, leaks[:10]
