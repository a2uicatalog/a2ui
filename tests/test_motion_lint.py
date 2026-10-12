"""motion_lint: the evidence-based limits for animated text, checked on whole films (scripts/motion_lint.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import motion_lint as ml  # noqa: E402


def film(text_block, keys, duration=8, **kw):
    b = dict({"type": "motion_text", "id": "tx", "size": 56}, **text_block)
    return dict({"type": "motion_timeline", "duration": duration, "blocks": [{"type": "motion_layer", "id": "s1", "blocks": [b]}], "tracks": [{"target": "tx", "keys": keys}]}, **kw)


def rules(f):
    return {x["rule"] for x in ml.lint(f)}


def test_a_comfortable_film_has_no_warnings():
    f = film({"text": "Made tidy for everyone", "mode": "words"}, [{"t": 0.5, "p": 0}, {"t": 1.5, "p": 1}], duration=6)
    assert not [x for x in ml.lint(f) if x["level"] in ("warn", "error")], ml.lint(f)


def test_characters_too_fast_and_too_slow():
    fast = film({"text": "Hello there, this is a long line", "mode": "chars"}, [{"t": 0, "p": 0}, {"t": 0.5, "p": 1}], duration=6)
    slow = film({"text": "Hi", "mode": "chars"}, [{"t": 0, "p": 0}, {"t": 4, "p": 1}], duration=8)
    assert "chars-too-fast" in rules(fast) and "chars-too-slow" in rules(slow)
    ok = film({"text": "Hello world", "mode": "chars"}, [{"t": 0, "p": 0}, {"t": 0.55, "p": 1}], duration=6)
    assert not rules(ok) & {"chars-too-fast", "chars-too-slow"}, ml.lint(ok)


def test_the_finished_text_must_be_held():
    short = film({"text": "Read this headline now", "mode": "words"}, [{"t": 0, "p": 0}, {"t": 1, "p": 1}], duration=1.3)
    assert "hold-short" in rules(short)
    # the scene ends a moment after the text arrives
    f = film({"text": "Read this headline now", "mode": "words"}, [{"t": 0, "p": 0}, {"t": 1, "p": 1}], duration=9)
    f["blocks"].append({"type": "motion_layer", "id": "s2", "blocks": []})
    f["scenes"] = [{"layer": "s1", "t": 0}, {"layer": "s2", "t": 1.2}]
    f["overlap"] = 0.1
    assert "hold-short" in rules(f)
    long = film({"text": "Read this headline now", "mode": "words"}, [{"t": 0, "p": 0}, {"t": 1, "p": 1}], duration=6)
    assert not rules(long) & {"hold-short", "hold-below-reading"}


def test_beats_use_a_hold_budget_of_words_times_300ms_plus_200():
    six = film({"text": "one two three four five six", "mode": "words"}, [{"t": 0, "p": 0}, {"t": 1, "p": 1}], duration=2.6)   # held 1.6 s, budget 2.0 s
    assert "hold-below-reading" in rules(six) and "hold-short" not in rules(six)


def test_noisy_reveals_over_a_big_area_are_an_error_and_small_ones_are_not():
    big = film({"text": "A LONG HEADLINE ACROSS THE WHOLE SCREEN", "mode": "chars", "reveal": "decode", "size": 120}, [{"t": 0, "p": 0}, {"t": 1.2, "p": 1}], duration=6)
    assert any(x["level"] == "error" and x["rule"] == "flash-risk" for x in ml.lint(big))
    small = film({"text": "ok", "mode": "chars", "reveal": "decode", "size": 24}, [{"t": 0, "p": 0}, {"t": 0.6, "p": 1}], duration=6)
    assert not any(x["level"] == "error" for x in ml.lint(small))
    calm = film({"text": "A LONG HEADLINE ACROSS THE WHOLE SCREEN", "mode": "chars", "reveal": "decode", "size": 120}, [{"t": 0, "p": 0}, {"t": 5, "p": 1}], duration=9)
    assert not any(x["level"] == "error" for x in ml.lint(calm))


def test_tracking_range_only_matters_at_reading_size():
    assert "tracking-range" in rules(film({"text": "Wide spacing", "tracking": 0.4, "size": 24}, [{"t": 0, "p": 0}, {"t": 1, "p": 1}], duration=6))
    assert "tracking-range" not in rules(film({"text": "Wide spacing", "tracking": 0.4, "size": 120}, [{"t": 0, "p": 0}, {"t": 1, "p": 1}], duration=6))


def test_loops_without_controls_and_big_zooms_and_rotation():
    f = film({"text": "x"}, [{"t": 0, "p": 0}, {"t": 1, "p": 1}], duration=9, loop=True, controls=False)
    assert "pause-control" in rules(f)
    assert "vestibular-zoom" in rules(film({"text": "x", "start_scale": 6}, [{"t": 0, "p": 0}, {"t": 1, "p": 1}], duration=6))
    pat = {"type": "motion_timeline", "duration": 4, "blocks": [{"type": "motion_pattern", "id": "pt", "angle": 80}], "tracks": []}
    assert "rotated-text" in rules(pat)


def test_beats_and_junk_input_never_crash():
    f = film({"text": "Beat timing", "mode": "words"}, [{"beat": 0, "p": 0}, {"beat": 2, "p": 1}], duration=6, bpm=120)
    assert isinstance(ml.lint(f), list)
    for junk in (None, [], {}, {"tracks": [None, 3, {"target": "nope"}]}, {"blocks": "x", "tracks": [{"target": "a", "keys": "x"}]}, {"duration": "x", "bpm": "y", "blocks": [{"id": "a", "type": "motion_text"}], "tracks": [{"target": "a", "keys": [{"t": "z", "p": 1}]}]}):
        assert isinstance(ml.lint(junk), list)


def test_the_made_tidy_sting_lints_with_no_errors():
    sting = Path("/tmp/claude-1000/-home-curtis/f653dbd2-ecb0-42da-a5ac-72ec1fe36292/scratchpad/film.json")
    if not sting.exists():
        return
    out = ml.lint(json.loads(sting.read_text()))
    assert not [x for x in out if x["level"] == "error"], out
