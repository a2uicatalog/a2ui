"""A browser strips leading C0 controls and spaces before it reads a URL's scheme, so "\x01javascript:..." navigates as
javascript:. Every scheme check must treat it the same way (found by the I136 review, 2026-10-24)."""
import json
import subprocess
from pathlib import Path

import pytest

from renderers import web_article as wa

ROOT = Path(__file__).resolve().parent.parent
BAD = ['\x01javascript:alert(1)', '\x00javascript:alert(1)', ' \x1fjavascript:alert(1)', '\x08JaVaScRiPt:alert(1)', '\x01data:text/html,x']


@pytest.mark.parametrize('v', BAD)
def test_md_url_ok_rejects_c0_prefixed_schemes(v):
    assert not wa._md_url_ok(v)


@pytest.mark.parametrize('v', BAD)
def test_safe_href_rejects_c0_prefixed_schemes(v):
    assert wa._safe_href(v) == ''


def test_plain_and_relative_links_still_pass():
    for v in ('https://a2uicatalog.ai/x', '/docs', '#top', '?q=1', 'mailto:a@b.c'):
        assert wa._md_url_ok(v) and wa._safe_href(v) == v


def test_markdown_link_with_c0_prefix_loses_its_href():
    h = wa._RENDERERS['bullet_list']({'type': 'bullet_list', 'items': [{'text': '[c](\u0001javascript:alert%281%29)'}]})
    import re
    assert not [a for a in re.findall(r'href="([^"]*)"', h) if 'javascript' in a.lower()]


def test_gas_href_is_safe_rejects_c0_prefixed_schemes():
    src = (ROOT / 'apps-script-surface/gas-wired-renderer/atom.gs').read_text()
    start = src.index('function _hrefIsSafe(')
    fn = src[src.index('var _HREF_SAFE_SCHEMES'):src.index('\n}\n', start) + 3]
    js = fn + ';console.log(JSON.stringify(%s.map(_hrefIsSafe)))' % json.dumps(BAD + ['https://x.y/z', '/rel'])
    out = json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)
    assert out[:len(BAD)] == [''] * len(BAD)
    assert out[len(BAD):] == ['https://x.y/z', '/rel']
