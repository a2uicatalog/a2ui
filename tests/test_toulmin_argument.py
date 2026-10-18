"""toulmin_argument: hostile input stays text in both renderers, and the record reports what it can and cannot back up."""
from test_gas_twins import _gas_batch, ATTACK
from test_motion_atoms import _py, core_js  # noqa: F401  (core_js is a fixture)

EXCERPT = "Teams in the pilot shipped 12 of 14 releases. Results may not hold for on-call teams."


def _both(core_js, block):
    return [_py(block), _gas_batch(core_js, [block])[0]]


def test_hostile_fields_are_escaped_everywhere(core_js):
    block = {"type": "toulmin_argument", "title": ATTACK, "claim": ATTACK, "qualifier": ATTACK, "warrant": ATTACK, "backing": ATTACK,
             "source_excerpt": ATTACK, "grounds": [{"quote": ATTACK, "text": ATTACK, "source": ATTACK}],
             "rebuttals": [{"text": ATTACK, "applies": True}]}
    for html in _both(core_js, block):
        assert "<img" not in html and "<script>" not in html, html[:300]
        assert 'aria-label="Argument: &quot;&gt;&lt;img' in html   # the attribute is escaped too, quotes included


def test_a_verified_record_stands(core_js):
    block = {"type": "toulmin_argument", "claim": "Extend the pilot", "source_excerpt": EXCERPT, "warrant": "w", "backing": "b",
             "grounds": [{"quote": "shipped 12 of 14 releases"}], "rebuttals": [{"text": "on-call teams", "applies": False}]}
    for html in _both(core_js, block):
        assert ">STANDS<" in html and "1 ground · 1 verified in source · 0 of 1 rebuttals apply" in html
        assert "UNVERIFIED" not in html and "⚠" not in html


def test_a_quote_not_in_the_source_is_flagged(core_js):
    block = {"type": "toulmin_argument", "claim": "c", "source_excerpt": EXCERPT, "grounds": [{"quote": "shipped 14 of 14 releases"}]}
    for html in _both(core_js, block):
        assert ">UNVERIFIED GROUNDS<" in html and "UNVERIFIED — not found in source_excerpt" in html and "0 verified in source" in html


def test_a_rebuttal_that_applies_wins(core_js):
    block = {"type": "toulmin_argument", "claim": "c", "source_excerpt": EXCERPT, "grounds": [{"quote": "shipped 12 of 14 releases"}],
             "rebuttals": [{"text": "the team is on call", "applies": True}]}
    for html in _both(core_js, block):
        assert ">REBUTTED<" in html and ">APPLIES<" in html and "1 of 1 rebuttals apply" in html


def test_gaps_are_shown_not_hidden(core_js):
    for html in _both(core_js, {"type": "toulmin_argument"}):
        assert ">UNGROUNDED<" in html
        for gap in ("no claim stated", "no grounds offered", "no warrant stated", "no backing", "no rebuttals considered"):
            assert gap in html, gap


def test_the_qualifier_survives(core_js):
    block = {"type": "toulmin_argument", "claim": "Extend the pilot", "qualifier": "probably", "grounds": [{"quote": "x"}]}
    for html in _both(core_js, block):
        assert ">probably</span>" in html
