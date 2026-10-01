"""scripts/check_motion_style.py: the advisory motion-style lint (benchmark: a2ui-private/briefs/motion-style-benchmark.md).

Each rule gets one payload that trips it and one that must not, so a rule cannot quietly start over- or under-firing.
Advisory only: the script exits 0 unless --strict."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_motion_style as cms  # noqa: E402


def tl(**kw):
    base = {"type": "motion_timeline", "duration": 12, "bpm": 120, "blocks": [{"type": "demo_orb", "id": "a"}], "tracks": []}
    base.update(kw)
    return [base]


def msgs(payload, level=None):
    return [f["message"] for f in cms.lint(payload) if level in (None, f["level"])]


def has(payload, needle, level=None):
    return any(needle in m for m in msgs(payload, level))


def test_clean_timeline_has_no_warnings():
    p = tl(tracks=[{"target": "a", "keys": [{"beat": 0, "opacity": 0}, {"beat": 1, "opacity": 1, "ease": "expo-out"}]}])
    assert msgs(p, "warn") == []


def test_bouncy_easing_more_than_once_warns_once_is_fine():
    one = tl(tracks=[{"target": "a", "keys": [{"beat": 0, "scale": 1}, {"beat": 2, "scale": 1.1, "ease": "overshoot"}]}])
    two = tl(tracks=[{"target": "a", "keys": [{"beat": 0, "scale": 1}, {"beat": 2, "scale": 1.1, "ease": "overshoot"}, {"beat": 4, "scale": 1, "ease": "anticipate"}]}])
    assert not has(one, "overshoot/anticipate", "warn")
    assert has(two, "2 overshoot/anticipate segments", "warn")


def test_linear_is_fine_for_progress_and_not_for_position():
    ok = tl(tracks=[{"target": "a", "keys": [{"beat": 0, "p": 0}, {"beat": 4, "p": 1, "ease": "linear"}]}])
    bad = tl(tracks=[{"target": "a", "keys": [{"beat": 0, "x": 0}, {"beat": 4, "x": 50, "ease": "linear"}]}])
    assert not has(ok, "linear", "warn")
    assert has(bad, "a.x", "warn") and has(bad, "linear easing on x", "warn")


def test_entrance_slower_than_600ms_warns_exit_does_not():
    slow = tl(tracks=[{"target": "a", "keys": [{"beat": 0, "opacity": 0}, {"beat": 1.6, "opacity": 1, "ease": "expo-out"}]}])  # 0.8 s
    fast = tl(tracks=[{"target": "a", "keys": [{"beat": 0, "opacity": 0}, {"beat": 1.2, "opacity": 1, "ease": "expo-out"}]}])  # 0.6 s
    exit_ = tl(tracks=[{"target": "a", "keys": [{"beat": 0, "opacity": 1}, {"beat": 3, "opacity": 0, "ease": "accelerate"}]}])
    assert has(slow, "enters over 800 ms", "warn")
    assert not has(fast, "enters over", "warn") and not has(exit_, "enters over", "warn")


def test_off_grid_keys_warn_only_when_bpm_is_set():
    off = tl(tracks=[{"target": "a", "keys": [{"t": 0.1, "x": 1}, {"t": 0.9, "x": 2}]}])
    on = tl(tracks=[{"target": "a", "keys": [{"t": 0.25, "x": 1}, {"t": 1.0, "x": 2}]}])      # half beats at 120 bpm
    nobpm = tl(bpm=0, tracks=[{"target": "a", "keys": [{"t": 0.1, "x": 1}]}])
    assert has(off, "off the 120 BPM grid", "warn")
    assert not has(on, "off the", "warn")
    assert not has(nobpm, "off the", "warn") and has(nobpm, "no bpm", "info")


def test_first_key_after_zero_is_informational_not_a_warning():
    p = tl(tracks=[{"target": "a", "keys": [{"beat": 4, "opacity": 0}, {"beat": 5, "opacity": 1, "ease": "expo-out"}]}])
    assert has(p, "first key at 2.00s", "info") and msgs(p, "warn") == []
    quiet = tl(tracks=[{"target": "a", "keys": [{"beat": 4, "p": 0}, {"beat": 8, "p": 1}]}])
    assert not has(quiet, "first key at", "info"), "p holding 0 until its key is the default, not news"


def test_camera_shake_needs_more_than_two_direction_changes():
    calm = tl(camera={"keys": [{"beat": 0, "rz": 0}, {"beat": 4, "rz": 2}, {"beat": 8, "rz": 0}]})
    shake = tl(camera={"keys": [{"beat": i, "rz": (-1) ** i * 3} for i in range(8)]})
    assert not has(calm, "shake", "warn") and has(shake, "reads as shake", "warn")


def test_enter_prop_and_motion_group_are_checked_too():
    slow = [{"type": "demo_orb", "enter": {"effect": "rise", "duration": 900}}]
    token = [{"type": "motion_group", "duration": "cinematic", "blocks": []}]
    pops = [{"type": "demo_orb", "enter": "pop"}, {"type": "demo_orb", "enter": {"effect": "fade", "ease": "overshoot"}}]
    fine = [{"type": "demo_orb", "enter": {"effect": "rise", "duration": "base"}}]
    assert has(slow, "lasts 900 ms", "warn") and has(token, "lasts 1000 ms", "warn")
    assert has(pops, "2 bouncy entrances", "warn")
    assert msgs(fine, "warn") == []


def test_cli_is_advisory_unless_strict(tmp_path):
    f = tmp_path / "p.json"
    f.write_text(json.dumps(tl(tracks=[{"target": "a", "keys": [{"beat": 0, "x": 0}, {"beat": 4, "x": 9, "ease": "linear"}]}])))
    run = lambda *a: subprocess.run([sys.executable, str(ROOT / "scripts" / "check_motion_style.py"), str(f), *a], capture_output=True, text=True)
    assert run().returncode == 0 and "1 warn" in run().stdout
    assert run("--strict").returncode == 1
