"""I136: benchmark_comparison, rating_stars, tag_cloud, versus_block, comparison_grid and side_by_side_spec read the schema's fields in BOTH twins.

* every documented field of a schema payload shows in the Python and the GAS output, and the two outputs are identical (uids normalised);
* old GAS field names (benchmarks, value, left / right, items) still render, in the same shared markup;
* every leaf of the payloads, replaced in turn by null, numbers, empty / huge strings, arrays, objects and attack text, renders identically
  in both twins and never lets attack markup or a script URL through.
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_motion_atoms import _norm, core_js  # noqa: E402,F401
from test_contract_sweep import _gas_isolated, _py_fresh  # noqa: E402

ATTACK = '"><img src=x onerror=alert(1)><script>alert(2)</script>\'`${x}'

SCHEMA = [
    {"type": "benchmark_comparison", "items": [{"label": "Direct Memory", "value": 12.4}, {"label": "Redis Cache", "value": 45.1}]},
    {"type": "rating_stars", "rating": 3, "max_rating": 6, "is_interactive": True},
    {"type": "tag_cloud", "title": "Domains", "min_size": 14, "max_size": 30, "accent": "#0f766e",
     "tags": [{"label": "Kubernetes", "weight": 5}, {"label": "Kafka", "weight": 2, "color": "#b91c1c"}, "plain"]},
    {"type": "versus_block", "entity_a_name": "REST API", "entity_a_description": "Resource oriented", "entity_a_image_url": "https://example.com/a.png",
     "entity_b_name": "gRPC", "entity_b_description": "Binary over HTTP/2", "entity_b_image_url": "https://example.com/b.png",
     "comparison_points": ["Wire payload size", "Browser support"]},
    {"type": "comparison_grid", "products": ["Postgres", "MongoDB"], "features": [{"name": "ACID", "values": ["Full", True]}, {"name": "Query", "values": ["SQL", False]}]},
    {"type": "side_by_side_spec", "item_a_name": "Aurora", "item_b_name": "RDS",
     "specs": [{"name": "Scaling", "item_a": "Under 2 seconds", "item_b": "5-10 minutes"}]},
]
# what each schema payload must show (visible text or attribute)
MUST = {
    "benchmark_comparison": ["Direct Memory", "Redis Cache", "12.4", "45.1"],
    "rating_stars": ['aria-label="Rate 6 of 6"', "3"],
    "tag_cloud": ["Domains", "Kubernetes", "Kafka", "plain", "font-size:30px", "font-size:17px", "#b91c1c", "#0f766e"],
    "versus_block": ["REST API", "gRPC", "Resource oriented", "Binary over HTTP/2", "https://example.com/a.png", "https://example.com/b.png",
                     "Wire payload size", "Browser support"],
    "comparison_grid": ["Postgres", "MongoDB", "ACID", "Query", "Full", "SQL", "&#10003;", "&#10007;"],
    "side_by_side_spec": ["Aurora", "RDS", "Scaling", "Under 2 seconds", "5-10 minutes"],
}
OLD = [
    {"type": "benchmark_comparison", "title": "Latency", "benchmarks": [{"name": "Alpha", "value": 10, "unit": "ms", "color": "#ff0000"}, {"name": "Beta", "value": 30, "max_value": 50}]},
    {"type": "rating_stars", "value": 2.5, "label": "Quality"},
    {"type": "tag_cloud", "items": [{"text": "One", "weight": 1}, {"text": "Two", "weight": 3}]},
    {"type": "versus_block", "metric_label": "Speed", "left": {"title": "Left One", "items": ["fast", "cheap"]}, "right": {"title": "Right One", "items": ["slow", "dear"]}},
    {"type": "comparison_grid", "title": "Numbers", "items": [{"name": "Speed", "value": "2x", "highlight": True}, {"name": "Cost", "value": "$5"}]},
    {"type": "side_by_side_spec", "left": {"title": "X100", "specs": [{"label": "Weight", "value": "1.2 kg"}]}, "right": {"title": "X200", "specs": [{"label": "Weight", "value": "1.5 kg"}]}},
]
OLD_WORDS = {
    "benchmark_comparison": ["Latency", "Alpha", "Beta", "10 ms", "30"],
    "rating_stars": ["Quality", "2.5"],
    "tag_cloud": ["One", "Two"],
    "versus_block": ["Speed", "Left One", "Right One", "fast", "cheap", "slow", "dear"],
    "comparison_grid": ["Numbers", "Speed", "2x", "Cost", "$5"],
    "side_by_side_spec": ["X100", "X200", "Weight", "1.2 kg", "1.5 kg"],
}
WEIRD = [None, True, False, 0, -3, 2.5, 1e22, "", "  ", "7", "12ms", "javascript:alert(1)", "\x01javascript:alert(1)", ATTACK, "😀" * 30, [], [1, "a"], {},
         {"label": ATTACK, "name": "n"}, "x" * 3000, 99999]


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


@pytest.fixture(scope="module")
def renders(core_js):
    blocks = SCHEMA + OLD
    gas = _gas_isolated(core_js, blocks)
    return [(b, _py_fresh(b), g) for b, g in zip(blocks, gas)]


def test_schema_payloads_show_every_documented_field_and_the_twins_agree(renders):
    for b, py, gas in renders[:len(SCHEMA)]:
        for twin, html in (("py", py), ("gas", gas)):
            for needle in MUST[b["type"]]:
                assert needle in html, "%s %s lacks %r" % (b["type"], twin, needle)
        assert _norm(py) == _norm(gas), b["type"]


def test_old_field_names_still_render_the_same_content_in_both_twins(renders):
    for b, py, gas in renders[len(SCHEMA):]:
        for twin, html in (("py", py), ("gas", gas)):
            text = re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>", "", html, flags=re.S))
            for w in OLD_WORDS[b["type"]]:
                assert w in " ".join(text.split()), "%s %s lacks %r" % (b["type"], twin, w)
        assert _norm(py) == _norm(gas), b["type"]


def test_hostile_and_odd_values_give_identical_safe_markup_in_both_twins(core_js):
    blocks = _fuzz(SCHEMA + OLD)
    gas = _gas_isolated(core_js, blocks)
    bad = []
    for b, g in zip(blocks, gas):
        py = _py_fresh(b)
        if _norm(py) != _norm(g):
            bad.append(("differs", b))
        for html in (py, g):
            if html.startswith(("PY ERROR", "GAS ERROR")) or "<img src=x" in html or "<script>alert" in html or re.search(r'(src|href)="\s*[\x00-\x20]*javascript:', html, re.I):
                bad.append(("unsafe", b))
    assert not bad, bad[:3]


def test_field_choice_and_big_numbers_match_javascript(core_js):
    blocks = [{"type": "rating_stars", "rating": [], "value": 3},
              {"type": "rating_stars", "rating": 0, "value": 3},
              {"type": "benchmark_comparison", "items": [{"label": "big", "value": 1152921504606846976}, {"label": "huge", "value": 1e25}]}]
    gas = _gas_isolated(core_js, blocks)
    py = [_py_fresh(b) for b in blocks]
    for p, g in zip(py, gas):
        assert _norm(p) == _norm(g)
    assert "1152921504606847000" in py[2] and "1e+25" in py[2]
