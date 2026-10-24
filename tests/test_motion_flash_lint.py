"""motion_lint flash rate: WCAG 2.3.1 (at most 3 flashes in any one second), computed statically from a film's tracks (scripts/motion_lint.py)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import motion_lint as ml  # noqa: E402


def film(block, keys, duration=6, **kw):
    b = dict({"id": "x", "place": {"x": 0, "y": 0, "w": 100, "h": 100}}, **block)
    return dict({"type": "motion_timeline", "duration": duration, "blocks": [b], "tracks": [{"target": "x", "keys": keys}]}, **kw)


def pulses(hz, n, p0=0.5):
    """n motion_flash pulses at hz: p jumps to 0 (a hold key) and runs to 1 over each period."""
    per = 1.0 / hz
    keys = []
    for i in range(n):
        keys += [{"t": p0 + i * per, "p": 0, "ease": "hold"}, {"t": p0 + (i + 1) * per, "p": 1}]
    return keys


def blink(hz, n, hi=1.0, t0=0.5):
    """n opacity blinks at hz: on for half a period, off for the other half."""
    per, keys = 1.0 / hz, []
    for i in range(n):
        keys += [{"t": t0 + i * per, "opacity": hi, "ease": "hold"}, {"t": t0 + (i + 0.5) * per, "opacity": 0, "ease": "hold"}]
    return keys


def flags(f, rule="flash-general"):
    return [x for x in ml.lint(f) if x["rule"] == rule]


def test_a_lightning_with_one_strike_and_a_flash_passes():
    f = film({"type": "motion_lightning", "flash": True}, [{"t": 1, "p": 0}, {"t": 2.2, "p": 1}])
    assert not [x for x in ml.lint(f) if x["level"] == "error"], ml.lint(f)


def test_a_lightning_strike_replayed_five_times_a_second_fails():
    keys = []
    for i in range(10):
        keys += [{"t": 0.5 + i * 0.2, "p": 0, "ease": "hold"}, {"t": 0.5 + (i + 1) * 0.2, "p": 1}]
    out = flags(film({"type": "motion_lightning", "flash": True, "blocks": [{"type": "text", "text": "hi"}]}, keys))
    assert out and out[0]["level"] == "error" and out[0]["target"] == "x"


def test_a_five_hertz_strobe_fails_and_names_the_block_and_time():
    out = flags(film({"type": "motion_flash"}, pulses(5, 10)))
    assert len(out) == 1 and out[0]["level"] == "error" and out[0]["target"] == "x"
    assert "motion_flash 'x'" in out[0]["message"] and " s and " in out[0]["message"] and "WCAG 2.3.1" in out[0]["message"]
    assert flags(film({"type": "motion_text"}, blink(5, 10)))     # the same rate as an opacity blink on any block


def test_exactly_three_flashes_in_a_second_passes_and_four_fails():
    assert not flags(film({"type": "motion_flash"}, pulses(3, 12)))                    # a steady 3 Hz, for four seconds
    assert not flags(film({"type": "motion_flash"}, pulses(3.2, 3)))
    assert flags(film({"type": "motion_flash"}, pulses(4.5, 4)))                       # four pulses 0.22 s apart
    assert not flags(film({"type": "motion_flash"}, pulses(4.5, 3)))                   # the same, stopped after three
    assert not flags(film({"type": "motion_text"}, blink(3, 9)))
    assert flags(film({"type": "motion_text"}, blink(4, 8)))


def test_flashes_spread_over_more_than_a_second_pass():
    keys = pulses(3, 3, 0.5) + [dict(k, t=k["t"] + 1.5) for k in pulses(3, 3, 0.5)]
    assert not flags(film({"type": "motion_flash"}, keys, duration=8))


def test_small_changes_and_small_areas_do_not_error():
    dim = blink(5, 10, hi=0.05)                                    # opacity 0.05: far under a 10% luminance change
    assert not flags(film({"type": "motion_text"}, dim))
    tiny = film({"type": "motion_flash", "place": {"x": 0, "y": 0, "w": 5, "h": 5}}, pulses(5, 10))
    out = [x for x in ml.lint(tiny) if x["rule"] in ("flash-general", "flash-small-area")]
    assert out and all(x["level"] == "info" for x in out)


def test_a_bright_state_pair_is_not_a_flash():
    # the darker state must be below 0.80 relative luminance: two near-white states swapping are not a flash
    f = film({"type": "motion_beats", "transition": "cut", "items": [{"text": "a", "bg": "#ffffff"}, {"text": "b", "bg": "#f4f4f4"}]},
             [{"t": 0.5 + i * 0.1, "step": i % 2, "ease": "hold"} for i in range(20)])
    assert not flags(f)


def test_beats_cut_between_dark_and_light_colour_fields_flash():
    keys = [{"t": 0.5 + i * 0.12, "step": 0.0 if i % 2 else 0.99, "ease": "hold"} for i in range(24)]
    items = [{"text": "a", "bg": "#101030"}, {"text": "b", "bg": "#e8e8f0"}]
    assert flags(film({"type": "motion_beats", "transition": "cut", "items": items}, keys, duration=5))
    slow = [{"t": 0.5 + i * 0.5, "step": 0.0 if i % 2 else 0.99, "ease": "hold"} for i in range(8)]
    assert not flags(film({"type": "motion_beats", "transition": "cut", "items": items}, slow, duration=5))


def test_red_flash_is_reported_separately_from_the_general_flash():
    # a dim saturated red pulse changes luminance by under 10% but is still a red flash
    f = film({"type": "motion_flash", "color": "#ff0000", "strength": 0.3}, pulses(5, 10), background="#000000")
    assert flags(f, "flash-red") and not flags(f)
    assert not flags(film({"type": "motion_flash", "color": "#ff0000", "strength": 0.3}, pulses(3, 9), background="#000000"), "flash-red")
    pale = film({"type": "motion_flash", "color": "#ff9999", "strength": 0.3}, pulses(5, 10), background="#000000")
    assert not flags(pale, "flash-red")             # not saturated red, so the red rule does not apply


def test_a_parent_layer_that_flashes_counts_for_its_children():
    f = {"type": "motion_timeline", "duration": 6, "blocks": [{"type": "motion_layer", "id": "lay", "blocks": [{"type": "motion_text", "id": "x", "text": "hi"}]}],
         "tracks": [{"target": "lay", "keys": blink(5, 10)}]}
    assert flags(f)


def test_bpm_beats_and_junk_never_crash():
    f = film({"type": "motion_flash"}, [{"beat": 1, "p": 0}, {"beat": 2, "p": 1}], bpm=120)
    assert isinstance(ml.lint(f), list)
    for junk in ({"blocks": [{"id": "a", "type": "motion_flash"}], "tracks": [{"target": "a", "keys": [{"t": "z", "p": 1}, {"t": 1, "p": "q"}]}]},
                 {"blocks": [{"id": "a", "type": "motion_beats", "items": "x"}], "tracks": [{"target": "a", "keys": [{"t": 0, "step": 0}, {"t": 1, "step": 3}]}]},
                 {"blocks": [{"id": "a", "place": "x"}], "tracks": [{"target": "a", "keys": [{"t": 0, "opacity": 0}, {"t": 1, "opacity": 1}]}], "duration": "x"}):
        assert isinstance(ml.lint(junk), list)


def test_the_step_key_reaches_the_showpiece_dial_rules():
    f = {"type": "motion_timeline", "duration": 6, "blocks": [{"type": "motion_flag", "id": "x", "text": "x", "cycles": 6}], "tracks": [{"target": "x", "keys": [{"t": 0, "step": 0}, {"t": 1.5, "step": 1}]}]}
    assert "wave-fast" in {x["rule"] for x in ml.lint(f)}
