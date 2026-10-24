import copy
import json
import re
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import film_still  # noqa: E402
import film_vtt  # noqa: E402
from renderers import web_article as wa  # noqa: E402
from test_gas_twins import _gas_batch, _norm_ids  # noqa: E402
from test_motion_atoms import _norm, _py, core_js  # noqa: F401, E402

FILMS = [
    "landing/film-wide-dark.json",
    "landing/film-wide-light.json",
    "landing/film-tall-dark.json",
    "landing/film-tall-light.json",
    "content/what-is-a2ui.film.json",
]

VTT_FILMS = [
    "landing/film-wide-dark.json",
    "landing/film-wide-light.json",
    "landing/film-tall-dark.json",
]


def _strip_mt_id(html):
    return _norm(html)   # the film's uid is derived from its payload, so it changes with the transcript field; _norm replaces it


def _load_film(rel_path):
    p = ROOT / rel_path
    data = json.loads(p.read_text(encoding="utf-8"))
    return data["blocks"][0] if "blocks" in data and data["blocks"] else data


@pytest.mark.parametrize("fpath", FILMS)
def test_absent_field_adds_nothing(fpath):
    film = _load_film(fpath)
    b_absent = copy.deepcopy(film)
    b_absent.pop("transcript", None)

    b_false = copy.deepcopy(film)
    b_false["transcript"] = False

    b_true = copy.deepcopy(film)
    b_true["transcript"] = True

    html_absent = _strip_mt_id(_py(b_absent))
    html_false = _strip_mt_id(_py(b_false))
    html_true = _strip_mt_id(_py(b_true))

    assert "mt-tr" not in html_absent
    assert html_absent == html_false

    html_stripped = re.sub(r'<details class="mt-tr".*?</details>', "", html_true, flags=re.S)
    assert html_stripped == html_absent


def _parse_transcript_rows(html):
    pattern = re.compile(
        r'<tr><td style="[^"]*white-space:nowrap;">(?P<start>[0-9:.]+)\s*-\s*(?P<end>[0-9:.]+)</td>'
        r'<td style="[^"]*">(?P<scene>.*?)</td><td style="[^"]*">(?P<text>.*?)</td></tr>'
    )
    return [m.groupdict() for m in pattern.finditer(html)]


@pytest.mark.parametrize("fpath", VTT_FILMS)
def test_rows_follow_film_vtt(fpath):
    film = _load_film(fpath)
    film_with_tr = copy.deepcopy(film)
    film_with_tr["transcript"] = True

    vtt = film_vtt.film_to_vtt(film)
    vtt_cues = []
    cue_pattern = re.compile(r'(\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}\.\d{3})\n(.*)')
    for block in vtt.split("\n\n"):
        m = cue_pattern.search(block.strip())
        if m:
            vtt_cues.append((m.group(1), m.group(2), m.group(3).strip()))

    html = _py(film_with_tr)
    rows = _parse_transcript_rows(html)

    for i in range(len(rows) - 1):
        def to_sec(clk):
            m, s = clk.split(":")
            return int(m) * 60 + float(s)
        assert to_sec(rows[i]["start"]) <= to_sec(rows[i + 1]["start"])

    for start_raw, _, text in vtt_cues:
        mins, secs = start_raw.split(":")
        sec_f = float(secs)
        clock_tenth = f"{int(mins)}:{int(sec_f):02d}.{int(round(sec_f * 1000) // 100) % 10}"
        matching = [r for r in rows if r["text"] == text]
        assert matching, f"Text {text} not found in transcript rows"
        assert any(r["start"] == clock_tenth for r in matching)


def _fixture_film():
    return {
        "type": "motion_timeline", "duration": 6, "transcript": True, "controls": False,
        "scenes": [{"layer": "s1", "t": 0}],
        "blocks": [{"type": "motion_layer", "id": "s1", "blocks": [
            {"type": "demo_kpis", "items": [{"label": "Pipeline", "value": 2400, "prefix": "$", "delta": "+12%"}]},
            {"type": "demo_chart", "title": "Sales", "labels": ["Q1", "Q2"], "data": [1, 2.5], "callout": "Peak"},
            {"type": "demo_progress", "label": "Done", "to": 80, "suffix": "%"},
            {"type": "motion_counter", "label": "Users", "to": 1234},
            {"type": "demo_caption", "id": "cap1", "lines": [{"who": "user", "text": "Hi"}, {"who": "agent", "text": "Hello"}]},
        ]}],
        "tracks": [{"target": "cap1", "keys": [{"t": 0, "step": 0}, {"t": 2, "step": 0}, {"t": 3, "step": 1}]}],
    }


def test_values_from_data_atoms():
    rows = _parse_transcript_rows(_py(_fixture_film()))
    texts = [r["text"] for r in rows]
    for want in ("Pipeline: $2,400 (+12%)", "Sales: Q1 1, Q2 2.50. Peak", "Done: 80%", "Users: 1,234", "user: Hi", "agent: Hello"):
        assert want in texts, (want, texts)
    assert {r["scene"] for r in rows} == {"s1"}
    hi = next(r for r in rows if r["text"] == "user: Hi")
    hello = next(r for r in rows if r["text"] == "agent: Hello")
    assert hi["start"] < hello["start"]


def test_hidden_text_gets_no_row():
    film = {"type": "motion_timeline", "duration": 5, "transcript": True, "blocks": [
        {"type": "motion_text", "id": "ghost", "text": "Invisible words"}, {"type": "motion_text", "id": "seen", "text": "Visible words"}],
        "tracks": [{"target": "ghost", "keys": [{"t": 0, "opacity": 0}, {"t": 5, "opacity": 0}]}]}
    rows = _parse_transcript_rows(_py(film))
    assert [r["text"] for r in rows] == ["Visible words"]
    film["blocks"] = film["blocks"][:1]
    assert "This film shows no text." in _py(film)


def test_poster_keeps_the_transcript_without_script():
    h = film_still.film_poster_html(_fixture_film())
    assert "Transcript" in h and "<table" in h and "Users: 1,234" in h
    assert "<script" not in h and "animation" not in h.lower()


def test_only_true_turns_it_on():
    base = {"type": "motion_timeline", "duration": 4, "blocks": [{"type": "motion_text", "text": "T"}]}
    for v in (1, "yes", None, "true", 0):
        assert "mt-tr" not in _py(dict(base, transcript=v))
    assert "mt-tr" in _py(dict(base, transcript=True))


ATTACK = '"><img src=x onerror=alert(1)><script>alert(2)</script>\'`${x}'


def _tl(blocks, **kw):
    return dict({"type": "motion_timeline", "duration": 6, "transcript": True, "controls": False, "autoplay": False, "blocks": blocks}, **kw)


PAYLOADS = [_fixture_film()] + [dict(_load_film(f), transcript=True) for f in FILMS] + [
    _tl([]),
    _tl([{"type": "motion_text", "id": "a1", "text": ATTACK}, {"type": "demo_caption", "lines": [{"who": ATTACK, "text": ATTACK}, "plain", None, {"who": 5, "text": 7}]},
         {"type": "demo_kpis", "items": [{"label": ATTACK, "value": "abc", "decimals": 9, "delta": ATTACK}, "str", None]},
         {"type": "demo_chart", "title": ATTACK, "labels": [ATTACK, 3, None], "data": [1.5, "x", -2, 1e12], "callout": ATTACK}]),
    _tl([{"type": "motion_text", "id": "constructor", "text": "Constructor text"}, {"type": "motion_text", "id": "toString", "text": "ToString text"},
         {"type": "motion_text", "id": "hasOwnProperty", "text": "Own text"}],
        tracks=[{"target": "constructor", "keys": [{"t": 0, "opacity": 0}, {"t": 2, "opacity": 1}]}]),
    _tl([{"type": "demo_window", "title": "W", "blocks": [{"type": "motion_text", "text": "Inside window"}, {"type": "motion_pill", "text": "Window *pill*"},
                                                         {"type": "motion_checklist", "title": "List", "items": ["One", {"text": "Two"}, {"x": 1}, 5, ""]},
                                                         {"type": "demo_toggle_grid", "cards": [{"title": "Card", "sub": "sub"}, "bare", {"sub": "only sub"}]}]}]),
    _tl([{"type": "motion_layer", "id": "s1", "blocks": [{"type": "motion_text", "id": "t1", "text": "One *two*\nthree"}]},
         {"type": "motion_layer", "id": "s2", "blocks": [{"type": "motion_text", "id": "t2", "text": "Second"}]}],
        scenes=[{"layer": "s1", "t": 0}, {"layer": "s2", "t": 3}], duration=8),
    _tl([{"type": "motion_text", "id": "b1", "text": "Beat text"}], bpm=120, duration=8,
        tracks=[{"target": "b1", "keys": [{"beat": 0, "p": 0}, {"beat": 2, "p": 1, "ease": "expo-out"}]}]),
    _tl([{"type": "motion_counter", "to": 1234567.891, "decimals": 2, "prefix": "$", "suffix": " k", "label": "Rev"}, {"type": "demo_progress", "to": "x"}, {"type": "demo_chart"}]),
] + [_tl([{"type": "motion_text", "text": "T"}], transcript=v) for v in (1, "yes", None, False)]


REAL = set(range(1, 1 + len(FILMS))) | {8}   # 8: ids named like Object.prototype members, which the GAS film already drops (older difference, same with transcript off)


def test_gas_matches_python(core_js):
    gas = _gas_batch(core_js, PAYLOADS)
    assert len(gas) == len(PAYLOADS)
    for i, payload in enumerate(PAYLOADS):
        py = _py(payload)
        if i in REAL:   # older, separate py/GAS differences outside the transcript; the transcript itself must match exactly
            tr = re.compile(r'<details class="mt-tr".*?</details>', re.S)
            assert tr.findall(gas[i]) == tr.findall(py) and tr.findall(py), i
        else:
            assert _norm_ids(gas[i]) == _norm_ids(py), i
