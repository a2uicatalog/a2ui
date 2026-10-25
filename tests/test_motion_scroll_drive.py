import hashlib
import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from test_motion_atoms import CHROMIUM, TIMELINE, _gas_batch, _norm, _py, core_js  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent

# sha256 of the uid-normalised Python output of each film, taken from origin/main 935844645 (before the scroll drive existed).
TIME_MODE_DIGESTS = {
    "landing/film-wide-dark.json": "c52e501bff4f90a51bfc80ef38840b39304a455cf338a923a8dbe7152424171c",
    "landing/film-wide-light.json": "43708fbeb90a78a7966874294bffa52ed8f2d4a50e8958d46ea5ea344fdfa69f",
    "landing/film-tall-dark.json": "9f86fd1d0a17db6b6c85315de5c00a841c7d2aff437a3dfd1f79f4c36f1e6645",
    "landing/film-tall-light.json": "adbd486e08404532cecf2e5a6dc9b2de519416ce2e902778f94340fcabf2b16f",
    "content/what-is-a2ui.film.json": "96d6a4e6fa26909654d91c66885d4e11f64b26d69b80c335964761863953c161",
}


def _render(renderer, cjs, block):
    if renderer == "py":
        return _py(block)
    return _gas_batch(cjs, [block])[0]


@pytest.mark.parametrize("renderer", ["py", "gas"])
def test_markup(renderer, core_js):
    b16 = dict(TIMELINE, drive="scroll", controls=True, autoplay=True)
    h16 = _render(renderer, core_js, b16)
    assert 'class="mt-run"' in h16
    assert "height:300vh" in h16
    assert 'class="mt-pin"' in h16
    assert "position:sticky;top:0" in h16
    assert "drv:1" in h16
    assert "auto:false" in h16
    assert 'class="mt-play"' not in h16
    assert 'class="mt-rng"' in h16
    assert 'class="mt-tm"' in h16
    assert "width:min(100%,177.78vh)" in h16
    assert "prefers-reduced-motion:reduce" in h16
    assert "{passive:true}" in h16

    b9 = dict(TIMELINE, drive="scroll", aspect="9:16", controls=False)
    h9 = _render(renderer, core_js, b9)
    assert "width:min(100%,56.25vh)" in h9
    assert 'class="mt-rng"' not in h9


@pytest.mark.parametrize(
    ("scroll_len", "expected_vh"),
    [
        (10, "height:150vh"),
        (99999, "height:1000vh"),
        ("x", "height:300vh"),
        (450, "height:450vh"),
        (None, "height:300vh"),
    ],
)
@pytest.mark.parametrize("renderer", ["py", "gas"])
def test_clamping(renderer, core_js, scroll_len, expected_vh):
    blk = dict(TIMELINE, drive="scroll")
    if scroll_len is not None:
        blk["scroll_length"] = scroll_len
    h = _render(renderer, core_js, blk)
    assert expected_vh in h


@pytest.mark.parametrize(
    "invalid_drive",
    ["time", "SCROLL", 5, None, "__absent__"],
)
@pytest.mark.parametrize("renderer", ["py", "gas"])
def test_absent_field_identity(renderer, core_js, invalid_drive):
    baseline = dict(TIMELINE)
    baseline.pop("drive", None)
    baseline.pop("scroll_length", None)
    ref = _norm(_render(renderer, core_js, baseline))

    variant = dict(TIMELINE, scroll_length=450)
    if invalid_drive == "__absent__":
        variant.pop("drive", None)
    else:
        variant["drive"] = invalid_drive
    out = _norm(_render(renderer, core_js, variant))

    assert "mt-run" not in out
    assert "mt-pin" not in out
    assert "drv:" not in out
    assert "min(100%" not in out
    assert out == ref


@pytest.mark.parametrize(
    "payload",
    [
        dict(TIMELINE, drive="scroll"),
        dict(TIMELINE, drive="scroll", scroll_length=10),
        dict(TIMELINE, drive="scroll", scroll_length=99999),
        dict(TIMELINE, drive="scroll", scroll_length="x"),
        dict(TIMELINE, drive="scroll", scroll_length=450),
        dict(TIMELINE, drive="scroll", controls=False),
        dict(TIMELINE, drive="scroll", aspect="9:16"),
        dict(TIMELINE, drive="scroll", autoplay=True),
        dict(TIMELINE, drive="scroll", theme="light"),
        dict(TIMELINE, drive="time"),
    ],
)
def test_twins_identical(core_js, payload):
    py_html = _norm(_py(payload))
    gas_html = _norm(_gas_batch(core_js, [payload])[0])
    assert py_html == gas_html


def test_pinned_digests_of_time_mode():
    for rel_path, expected_digest in TIME_MODE_DIGESTS.items():
        with open(ROOT / rel_path, encoding="utf-8") as f:
            block = json.load(f)["blocks"][0]
        html_out = _norm(_py(block))
        digest = hashlib.sha256(html_out.encode("utf-8")).hexdigest()
        assert digest == expected_digest


# Headless virtual time never produces animation frames (so neither requestAnimationFrame nor the browser's own scroll events
# fire): a timer stands in for rAF, and the harness dispatches the scroll event after each scrollTo. The handler, the progress
# maths and the seek are the real ones.
RAF_SHIM = "<script>window.requestAnimationFrame=function(f){return setTimeout(function(){f(performance.now())},16)};</script>"


def _run_browser(html_content, extra_flags=None):
    flags = [
        CHROMIUM,
        "--headless=new",
        "--password-store=basic",
        "--no-sandbox",
        "--disable-gpu",
        "--window-size=1200,800",
        "--virtual-time-budget=4000",
    ]
    if extra_flags:
        flags.extend(extra_flags)
    u_dir = tempfile.mkdtemp()
    flags.append("--user-data-dir=" + u_dir)
    try:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "page.html"
            p.write_text(html_content, encoding="utf-8")
            cmd = flags + ["--dump-dom", p.as_uri()]
            res = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=20
            )
            m = re.search(r'<pre id="out">(.*?)</pre>', res.stdout, re.DOTALL)
            assert m, "missing <pre id='out'> in output"
            return json.loads(html.unescape(m.group(1)))
    finally:
        shutil.rmtree(u_dir, ignore_errors=True)


@pytest.mark.skipif(not CHROMIUM, reason="Chromium not found")
@pytest.mark.parametrize("renderer", ["py", "gas"])
def test_browser_scroll_drive(renderer, core_js):
    blk = dict(TIMELINE, drive="scroll", poster=5, controls=True)
    film_html = _render(renderer, core_js, blk)
    harness = """
    window.addEventListener('load', function() {
      setTimeout(function() {
        var tm = document.querySelector('.mt-tm');
        var rng = document.querySelector('.mt-rng');
        var run = document.querySelector('.mt-run');
        var pin = document.querySelector('.mt-pin');
        var r0 = rng ? Number(rng.value) : null;
        var c0 = tm ? tm.textContent : null;
        var r = run.getBoundingClientRect();
        var travel = r.height - window.innerHeight;
        var top0 = window.pageYOffset + r.top;
        window.scrollTo(0, top0 + travel * 0.5); window.dispatchEvent(new Event('scroll'));
        setTimeout(function() {
          var rMid = rng ? Number(rng.value) : null;
          var cMid = tm ? tm.textContent : null;
          var pinTop = pin.getBoundingClientRect().top;
          window.scrollTo(0, top0 + travel); window.dispatchEvent(new Event('scroll'));
          setTimeout(function() {
            var rEnd = rng ? Number(rng.value) : null;
            var cEnd = tm ? tm.textContent : null;
            window.scrollTo(0, 0); window.dispatchEvent(new Event('scroll'));
            setTimeout(function() {
              var rBack = rng ? Number(rng.value) : null;
              var data = {
                rng0: r0, clock0: c0,
                mid: rMid, clockMid: cMid, pinTop: pinTop,
                end: rEnd, clockEnd: cEnd,
                top: rBack
              };
              document.getElementById('out').textContent = JSON.stringify(data);
            }, 400);
          }, 400);
        }, 400);
      }, 200);
    });
    """
    page = (
        '<!doctype html><meta charset=utf-8><body style="margin:0">'
        '<div style="height:1500px">before</div>'
        + RAF_SHIM
        + film_html
        + '<div style="height:1500px">after</div>'
        '<pre id="out"></pre><script>' + harness + "</script></body>"
    )
    res = _run_browser(page)
    assert res["rng0"] == 0
    assert 480 <= res["mid"] <= 520
    assert res["clockMid"].startswith("0:04")
    assert res["end"] == 1000
    assert res["top"] == 0
    assert abs(res["pinTop"]) < 2


@pytest.mark.skipif(not CHROMIUM, reason="Chromium not found")
@pytest.mark.parametrize("renderer", ["py", "gas"])
def test_browser_reduced_motion(renderer, core_js):
    blk = dict(TIMELINE, drive="scroll", poster=5, controls=True)
    film_html = _render(renderer, core_js, blk)
    harness = """
    window.addEventListener('load', function() {
      setTimeout(function() {
        var pin = document.querySelector('.mt-pin');
        var tm = document.querySelector('.mt-tm');
        var pos = window.getComputedStyle(pin).position;
        var clock = tm ? tm.textContent : '';
        document.getElementById('out').textContent = JSON.stringify({
          position: pos,
          clock: clock
        });
      }, 200);
    });
    """
    page = (
        '<!doctype html><meta charset=utf-8><body style="margin:0">'
        + film_html
        + '<pre id="out"></pre><script>' + harness + "</script></body>"
    )
    res = _run_browser(page, extra_flags=["--force-prefers-reduced-motion"])
    assert res["position"] == "static"
    assert res["clock"].startswith("0:05")
