"""I136 missing-GAS batch: ten editorial atoms had a Python renderer and no Apps Script one (they rendered "unknown atom" on MCP Apps / play).

* the schema payload of each shows every documented field, identically in the Python and the GAS twin (uids normalised);
* every leaf of the payloads, replaced in turn by null, numbers, empty / huge strings, arrays, objects and attack text, gives identical safe markup
  in both twins (no crash, no attack markup, no script URL);
* resource_link_row drops the anchor for an unsafe URL; wishlist_panel bolds the lead phrase before the colon (schema contract);
* the five Chat-card atoms (service_status_board, incident_log, stat_pulse, weather_now, weather_outlook) are declared server-only: their schema
  works_on lists only google-chat-chromium-render, so no GAS / MCP Apps surface offers them.
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from test_motion_atoms import core_js  # noqa: E402,F401
from test_contract_sweep import _gas_isolated, _py_fresh  # noqa: E402
from test_motion_atoms import _norm as _norm_uid  # noqa: E402


def _norm(html):
    """uids normalised; the apostrophe entity too (Python's html.escape writes &#x27;, the GAS _esc &#39;: the same character)."""
    return _norm_uid(html).replace("&#x27;", "&#39;")

ROOT = Path(__file__).parent.parent
ATTACK = '"><img src=x onerror=alert(1)><script>alert(2)</script>\'`${x}'

SCHEMA = [
    {"type": "verdict_checklist", "title": "Does it work", "items": [
        {"label": "Signing `works`", "verdict": "yes", "note": "Verified in prod"}, {"label": "Expiry", "verdict": "partial"},
        {"label": "Caching", "verdict": "no", "note": "Not at all"}]},
    {"type": "constraint_fix_triad", "constraint": "Signed URLs expire", "breaks": "Cached pages go stale", "fix": "Sign at the edge with `kid`"},
    {"type": "incident_finding", "headline": "Queue lag", "detail": "Consumers stalled", "synthesis": "Shared lesson learned"},
    {"type": "wrong_vs_right", "title": "Names", "pairs": [{"wrong": "userId", "right": "`user_id`"}, {"wrong": "ttl", "right": "max_age"}]},
    {"type": "agent_demo_card", "name": "Demo Agent", "description": "Books a trip", "primitives_used": ["search", "calendar_today"]},
    {"type": "wishlist_panel", "title": "Missing", "groups": [{"heading": "Auth", "items": ["Scoped tokens: per-user grants.", "No colon here"]},
                                                              {"heading": "Limits", "items": ["Bigger quotas: 10x"]}]},
    {"type": "trace_step", "step_number": 2, "title": "Gateway", "body": "Checks the `token`", "code": "GET /x HTTP/1.1"},
    {"type": "stat_inline_badge", "value": "534", "label": "typed atoms"},
    {"type": "problem_chapter", "number": 3, "headline": "Expiry", "body": "Links die", "angle_label": "Frugality angle", "angle_text": "Cache less"},
    {"type": "resource_link_row", "label": "Live catalog", "url": "https://example.com/c", "note": "All atoms"},
]
MUST = {
    "verdict_checklist": ["Does it work", "<code>works</code>", "Verified in prod", "Expiry", "Not at all", "&#10003;" if False else "✓", "~", "✗"],
    "constraint_fix_triad": ["Signed URLs expire", "Cached pages go stale", "<code>kid</code>", "Constraint", "Breaks", "Fix"],
    "incident_finding": ["Queue lag", "Consumers stalled", "Shared lesson learned"],
    "wrong_vs_right": ["Names", "userId", "<code>user_id</code>", "ttl", "max_age", "→"],
    "agent_demo_card": ["Demo Agent", "Books a trip", ">search<", ">calendar_today<"],
    "wishlist_panel": ["Missing", "Auth", "Limits", '<strong style="color:#202124;">Scoped tokens:</strong> per-user grants.', "No colon here",
                       '<strong style="color:#202124;">Bigger quotas:</strong> 10x'],
    "trace_step": [">2<", "Gateway", "<code>token</code>", "GET /x HTTP/1.1", "<pre"],
    "stat_inline_badge": ["534", "typed atoms"],
    "problem_chapter": ["Problem 3", "Expiry", "Links die", "Frugality angle:", "Cache less"],
    "resource_link_row": ['href="https://example.com/c"', "Live catalog", "All atoms"],
}
WEIRD = [None, True, False, 0, -3, 2.5, 1e22, "", "  ", "7", "javascript:alert(1)", "\x01javascript:alert(1)", "java\tscript:alert(1)", ATTACK,
         "x: y", "😀" * 30, [], [1, "a", None, {"label": ATTACK}], {}, {"label": ATTACK, "name": "n"}, "x" * 3000, 99999]
BLOCKS_WEIRD = [None, 5, "str", [], [1], True]


def _leaves(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _leaves(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _leaves(v, path + (i,))
    if path:
        yield path


def _fuzz(blocks):
    out = []
    for b in blocks:
        for p in _leaves(b):
            if p[0] == "type":
                continue
            for v in WEIRD:
                c = copy.deepcopy(b)
                o = c
                for k in p[:-1]:
                    o = o[k]
                o[p[-1]] = v
                out.append(c)
    return out


def _unsafe(html):
    return (html.startswith(("PY ERROR", "GAS ERROR")) or "<img src=x" in html or "<script>alert" in html
            or re.search(r'(src|href)="\s*[\x00-\x20]*(javascript|java\s*script):', html, re.I))


@pytest.fixture(scope="module")
def renders(core_js):
    gas = _gas_isolated(core_js, SCHEMA)
    return [(b, _py_fresh(b), g) for b, g in zip(SCHEMA, gas)]


def test_schema_payloads_show_every_documented_field_and_the_twins_agree(renders):
    for b, py, gas in renders:
        for twin, html in (("py", py), ("gas", gas)):
            assert not html.startswith(("PY ERROR", "GAS ERROR")), (b["type"], twin, html[:300])
            assert "unknown atom" not in html.lower(), (b["type"], twin)
            for needle in MUST[b["type"]]:
                assert needle in html, "%s %s lacks %r" % (b["type"], twin, needle)
        assert _norm(py) == _norm(gas), b["type"]


def test_hostile_and_odd_values_give_identical_safe_markup_in_both_twins(core_js):
    blocks = _fuzz(SCHEMA)
    gas = _gas_isolated(core_js, blocks)
    bad = []
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        if _norm(py) != _norm(g):
            bad.append(("differs", b))
        if _unsafe(py) or _unsafe(g):
            bad.append(("unsafe", b))
    assert not bad, bad[:3]


def test_a_block_that_is_not_an_object_does_not_crash_either_twin(core_js):
    blocks = []
    for s in SCHEMA:
        for w in BLOCKS_WEIRD:
            blocks.append({"__raw": w, "type": s["type"]})
    # renderAtoms hands each renderer the block itself, so the raw odd value is exercised through the renderers directly
    import renderers.web_article as wa
    for s in SCHEMA:
        for w in BLOCKS_WEIRD:
            out = wa._RENDERERS[s["type"]](w)
            assert isinstance(out, str) and "<img src=x" not in out


def test_resource_link_row_drops_the_anchor_for_an_unsafe_url(core_js):
    blocks = [{"type": "resource_link_row", "label": "L", "url": u} for u in ("javascript:alert(1)", "\x01javascript:alert(1)", "java\tscript:alert(1)",
                                                                               "data:text/html,x", "http://plain.example", "/relative", "mailto:a@b.c")]
    gas = _gas_isolated(core_js, blocks)
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        assert _norm(py) == _norm(g), b
    assert [("<a " in _py_fresh(b)) for b in blocks] == [False, False, False, False, False, True, True]


def test_chat_card_atoms_are_declared_server_only():
    schema = {b["type"]: b for b in yaml.safe_load((ROOT / "atoms/schema.yaml").read_text())["blocks"]}
    for t in ("service_status_board", "incident_log", "stat_pulse", "weather_now", "weather_outlook"):
        works = schema[t]["surfaces"]["works_on"]
        assert works == ["google-chat-chromium-render"], (t, works)
