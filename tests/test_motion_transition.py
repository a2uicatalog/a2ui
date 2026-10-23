"""motion_transition (I75): T(A, B, p) joins two atoms' build-contract elements by data key, in headless Chromium.

At p = 0 every matched B element sits on its A partner's box (exact key), on the union of its A descendants' boxes (a B key that
is the path prefix of A keys: a breakdown collapses into its total) or on its A ancestor's box. At p = 1 every B element is exactly
where B alone puts it and A is transparent. With reduced motion A is not shown and B is static at any p. Labels never transform.
Checked at three widths, so the measuring holds for any container. Python and GAS emit the same wrapper.
"""
from __future__ import annotations

import html as _h
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_motion_atoms import _node_raw as _node, _norm, _py_keyed as _py, core_js  # noqa: E402,F401
from test_motion_build import CHROMIUM, browser  # noqa: E402

ITEMS = [{"name": "VMs", "value": 420, "path": ["Cloud"]}, {"name": "Storage", "value": 180, "path": ["Cloud"]},
         {"name": "Network", "value": 90, "path": ["Cloud"]}, {"name": "Eng", "value": 300, "path": ["People"]},
         {"name": "Sales", "value": 150, "path": ["People"]}, {"name": "SaaS", "value": 120, "path": ["Tools"]},
         {"name": "Licences", "value": 60, "path": ["Tools"]}]
TOTALS = [{"name": "Cloud", "value": 690}, {"name": "People", "value": 450}, {"name": "Tools", "value": 180}]
TREEMAP = {"type": "treemap", "title": "Spend", "items": ITEMS}
ICICLE = {"type": "sunburst", "title": "Spend", "layout": "icicle", "items": ITEMS}
SUNBURST = {"type": "sunburst", "title": "Spend", "items": ITEMS}
SUN_TOTALS = {"type": "sunburst", "title": "Spend", "items": TOTALS}

CIRCLES = {"type": "circle_pack", "title": "Spend", "items": ITEMS}
PAIRS = {
    "treemap->icicle": (TREEMAP, ICICLE),        # HTML boxes to HTML boxes: leaves exact, groups from their leaves (prefix)
    "treemap->sunburst": (TREEMAP, SUNBURST),    # HTML boxes to SVG arcs (user units through the screen CTM)
    "treemap->totals": (TREEMAP, SUN_TOTALS),    # a pure prefix collapse: Cloud/VMs, Cloud/Storage, Cloud/Network -> Cloud
    "sunburst->circle_pack": (SUNBURST, CIRCLES),  # curved to curved, arc by arc
}

PROBE = r"""
function keyed(r){var o={},l=r.querySelectorAll('[data-cb][data-key],[data-cb] [data-key]');
 for(var i=0;i<l.length;i++){var e=l[i],c=e.closest('[data-cb]');if(c&&c.getAttribute('data-cb')==='label')continue;
  if(e.querySelector('[data-key]'))continue;var b=e.getBoundingClientRect();o[e.getAttribute('data-key')]=[b.left,b.top,b.width,b.height,+getComputedStyle(e).opacity,!e.ownerSVGElement||/^(rect|polygon|g)$/i.test(e.tagName)]}return o}
function labels(r){return [].map.call(r.querySelectorAll('[data-cb=label]'),function(e){var s=getComputedStyle(e);return [s.translate,s.scale,+s.opacity]})}
var w=document.querySelector('.mo-tr'),out={};
if(w){var A=w.querySelector('.mtr-a'),B=w.querySelector('.mtr-b');out.a=keyed(A);out.b=keyed(B);out.lab=labels(B);
 out.aop=+getComputedStyle(A).opacity;out.adisp=getComputedStyle(A).display}else{out.b=keyed(document.body)}
return out;"""


TOPS = r"""var w=document.querySelector('.mo-tr');function first(r){var e=r;while(e.firstElementChild&&!e.textContent.trim().length===false&&e.firstElementChild.tagName!=='SVG'&&e.firstElementChild.firstElementChild)e=e.firstElementChild;return e}
return {atop:first(w.querySelector('.mtr-a')).getBoundingClientRect().top,btop:first(w.querySelector('.mtr-b')).getBoundingClientRect().top};"""


def _page(block, p, width, flags=(), js=False):
    probe = ("document.body.style.setProperty('--p'," + json.dumps(p) + ");" if p is not None else "") + (TOPS if js else PROBE)
    page = ("<!doctype html><meta charset=utf-8><body style='margin:0;padding:8px'>" + _py(block)
            + "<script>window.addEventListener('load',function(){setTimeout(function(){document.documentElement.setAttribute('data-probe',"   # a timer, not rAF: headless virtual time may never paint a frame
            + "JSON.stringify((function(){" + probe + "})()))},100)});</script>")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(page)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                              "--window-size=%d,1400" % width, "--virtual-time-budget=8000", "--use-angle=swiftshader", "--user-data-dir=" + td + "/prof",
                              *flags, "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=90).stdout
    m = re.search(r"data-probe='([^']*)'|data-probe=\"([^\"]*)\"", out)
    assert m, out[:400]
    return json.loads(_h.unescape(m.group(1) or m.group(2)))


def _union(rects):
    x0, y0 = min(r[0] for r in rects), min(r[1] for r in rects)
    return [x0, y0, max(r[0] + r[2] for r in rects) - x0, max(r[1] + r[3] for r in rects) - y0]


def _expected_start(a, k):
    if k in a:
        return a[k][:4]
    kids = [v for q, v in a.items() if q.startswith(k + "/")]
    if kids:
        return _union(kids)
    parts = k.split("/")
    for j in range(len(parts) - 1, 0, -1):
        if "/".join(parts[:j]) in a:
            return a["/".join(parts[:j])][:4]
    return None


def _close(r, s, tol):
    return all(abs(x - y) <= tol for x, y in zip(r[:4], s[:4]))


@browser
@pytest.mark.parametrize("width", [360, 800, 1280])
@pytest.mark.parametrize("pair", list(PAIRS))
def test_at_p0_every_matched_element_sits_on_its_a_partner(pair, width):
    a_blk, b_blk = PAIRS[pair]
    got = _page({"type": "motion_transition", "from": a_blk, "to": b_blk}, 0, width)
    matched = 0
    for k, r in got["b"].items():
        s = _expected_start(got["a"], k)
        if s is None:
            assert r[4] == pytest.approx(0, abs=0.01), ("a B-only element is hidden at p = 0", k)
            continue
        matched += 1
        rect_a = all(v[5] for q, v in got["a"].items() if q == k or q.startswith(k + "/") or k.startswith(q + "/"))
        if r[5] and rect_a:   # box to box: exactly on the partner's box
            assert _close(r, s, 2.5), (k, [round(x, 1) for x in r[:4]], [round(x, 1) for x in s])
        else:                 # a curved shape keeps its proportions: fitted inside the partner's box, centred on it
            assert abs(r[0] + r[2] / 2 - s[0] - s[2] / 2) <= 2.5 and abs(r[1] + r[3] / 2 - s[1] - s[3] / 2) <= 2.5, (k, r[:4], s)
            assert r[2] <= s[2] + 2.5 and r[3] <= s[3] + 2.5 and (abs(r[2] - s[2]) <= 2.5 or abs(r[3] - s[3]) <= 2.5), (k, r[:4], s)
    assert matched >= 3
    assert got["aop"] == pytest.approx(1)


@browser
@pytest.mark.parametrize("width", [360, 800, 1280])
@pytest.mark.parametrize("pair", list(PAIRS))
def test_at_p1_the_page_is_b(pair, width):
    a_blk, b_blk = PAIRS[pair]
    got = _page({"type": "motion_transition", "from": a_blk, "to": b_blk}, 1, width)
    alone = _page(b_blk, None, width)["b"]
    assert set(got["b"]) == set(alone)
    for k, r in got["b"].items():
        assert _close(r, alone[k], 0.6), (k, r, alone[k])
        assert r[4] == pytest.approx(1)
    assert got["aop"] == pytest.approx(0)
    assert all(t[0] == "none" and t[1] == "none" for t in got["lab"]), "labels never transform"


@browser
@pytest.mark.parametrize("pair", list(PAIRS))
def test_midway_elements_are_between_a_and_b_and_labels_only_fade(pair):
    a_blk, b_blk = PAIRS[pair]
    blk = {"type": "motion_transition", "from": a_blk, "to": b_blk}
    p0, mid, p1 = _page(blk, 0, 800), _page(blk, 0.5, 800), _page(blk, 1, 800)
    moved = 0
    for k, r in mid["b"].items():
        if _expected_start(p0["a"], k) is None:
            continue
        lo, hi = p0["b"][k], p1["b"][k]
        for i in (0, 1):
            assert min(lo[i], hi[i]) - 1 <= r[i] <= max(lo[i], hi[i]) + 1, (k, i, lo[i], r[i], hi[i])
        moved += abs(lo[0] - hi[0]) + abs(lo[1] - hi[1]) > 4
    assert moved >= 2
    assert all(t[0] == "none" and t[1] == "none" for t in mid["lab"])


@browser
@pytest.mark.parametrize("pair", ["treemap->sunburst", "sunburst->circle_pack"])
def test_nothing_curved_is_stretched_and_a_stays_still(pair):
    a_blk, b_blk = PAIRS[pair]
    blk = {"type": "motion_transition", "from": a_blk, "to": b_blk}
    p0, mid, end = _page(blk, 0, 800), _page(blk, 0.5, 800), _page(blk, 1, 800)
    for k, r in mid["b"].items():   # a curved element: only a uniform scale on its way
        if not r[5]:
            e = end["b"][k]
            assert r[2] / e[2] == pytest.approx(r[3] / e[3], rel=0.02), k
    for k, r in mid["a"].items():
        assert _close(r, p0["a"][k], 0.6), ("A never moves", k)


@browser
@pytest.mark.parametrize("pair", list(PAIRS))
def test_a_and_b_start_at_the_same_top(pair):
    """A's first block drops its top margin (B's collapses out of the wrapper): the two titles coincide instead of doubling."""
    a_blk, b_blk = PAIRS[pair]
    t = _page({"type": "motion_transition", "from": a_blk, "to": b_blk}, 0.15, 800, js=True)
    assert abs(t["atop"] - t["btop"]) <= 0.6, t


@browser
@pytest.mark.parametrize("pair", list(PAIRS))
def test_reduced_motion_shows_b_static_at_any_p(pair):
    a_blk, b_blk = PAIRS[pair]
    got = _page({"type": "motion_transition", "from": a_blk, "to": b_blk}, 0, 800, ("--force-prefers-reduced-motion",))
    alone = _page(b_blk, None, 800)["b"]
    assert got["adisp"] == "none"
    for k, r in got["b"].items():
        assert _close(r, alone[k], 0.6), k


@browser
def test_exact_match_turns_the_path_rules_off():
    got = _page({"type": "motion_transition", "from": TREEMAP, "to": SUN_TOTALS, "match": "exact"}, 0, 800)
    assert all(r[4] == pytest.approx(0, abs=0.01) for r in got["b"].values()), "no shared key: every B element enters"


@browser
def test_key_map_renames_a_keys_before_the_join():
    renamed = [dict(i, path=["Infra" if i["path"] == ["Cloud"] else i["path"][0]]) for i in ITEMS]
    b_blk = {"type": "sunburst", "title": "Spend", "layout": "icicle", "items": renamed}
    km = {"Cloud/" + i["name"]: "Infra/" + i["name"] for i in ITEMS if i["path"] == ["Cloud"]}
    plain = _page({"type": "motion_transition", "from": TREEMAP, "to": b_blk}, 0, 800)
    mapped = _page({"type": "motion_transition", "from": TREEMAP, "to": b_blk, "key_map": km}, 0, 800)
    assert plain["b"]["Infra/VMs"][4] == pytest.approx(0, abs=0.01)       # no key in common: it enters
    assert _close(mapped["b"]["Infra/VMs"], mapped["a"]["Cloud/VMs"], 2.5)   # mapped: it starts on Cloud/VMs (both boxes)


def test_python_and_gas_emit_the_same_wrapper(core_js):
    for pair, (a_blk, b_blk) in PAIRS.items():
        blk = {"type": "motion_transition", "from": a_blk, "to": b_blk, "key_map": {"Cloud/VMs": "Compute"}}
        assert _norm(_py(blk)) == _norm(_node(core_js, "console.log(JSON.stringify([renderAtoms([%s], {})]))" % json.dumps(blk))[0]), pair


def test_hostile_input_is_inert():
    out = _py({"type": "motion_transition", "from": "x", "to": TREEMAP, "match": "<script>", "key_map": {"a\"><script>": "b'><img>", "c": 5}})
    assert 'data-mtr-match="path"' in out and "<script>" not in out.split("<script>(function", 1)[0].split('class="mo-tr"', 1)[1][:400]
    assert _py({"type": "motion_transition"}).startswith("<!-- a2ui: motion_transition needs")


def test_the_gas_twin_never_writes_a_literal_closing_script_tag():
    """The MCP Apps bundle inlines the GAS source in a <script> element: a literal </script> in it would end that element."""
    src = (Path(__file__).parent.parent / "apps-script-surface/gas-wired-renderer/atoms_motion_candidates.gs").read_text()
    section = src[src.index("// motion_transition (I75"):src.index("_RENDERERS['motion_transition']") + 2000]
    assert "</script>" not in section


TEAM = {"type": "org_chart", "title": "The team", "nodes": [
    {"id": "curtis", "label": "Curtis", "parent_id": ""}, {"id": "curtis/sonnet", "label": "Sonnet", "parent_id": "curtis"},
    {"id": "curtis/opus", "label": "Opus", "parent_id": "curtis"}, {"id": "curtis/gemini", "label": "Gemini", "parent_id": "curtis"}]}
PATCH = [{"op": "copy", "from": "/nodes/2", "path": "/nodes/-"},                       # Opus is copied ...
         {"op": "replace", "path": "/nodes/4/id", "value": "curtis/opus2"},           # ... into a second reviewer
         {"op": "replace", "path": "/nodes/4/label", "value": "Opus 2"},
         {"op": "move", "from": "/nodes/1", "path": "/nodes/3"},                      # Sonnet changes seat
         {"op": "add", "path": "/nodes/-", "value": {"id": "curtis/pm", "label": "PM", "parent_id": "curtis"}}]


@browser
def test_a_patch_animates_as_its_own_diff():
    """from + an RFC 6902 patch: the copy starts on its source, the moved node on its old seat, the new node on its parent."""
    got = _page({"type": "motion_transition", "from": TEAM, "patch": PATCH}, 0, 900)
    a, b = got["a"], got["b"]
    assert _close(b["curtis/opus2"], a["curtis/opus"], 2.5), "the copy grows out of its source"
    assert _close(b["curtis/sonnet"], a["curtis/sonnet"], 2.5), "the moved node starts where it was"
    assert _close(b["curtis/pm"], a["curtis"], 2.5), "the added node comes out of its parent (path rule)"
    end = _page({"type": "motion_transition", "from": TEAM, "patch": PATCH}, 1, 900)
    alone = _page(wa_after(), None, 900)["b"]
    assert set(end["b"]) == set(alone) and all(_close(r, alone[k], 0.6) for k, r in end["b"].items())


def wa_after():
    import renderers.web_article as wa
    return wa._mtr_from_patch(TEAM, PATCH)[0]


def test_a_rejected_patch_shows_from_and_says_why():
    out = _py({"type": "motion_transition", "from": TEAM, "patch": [{"op": "remove", "path": "/nodes/9"}]})
    assert "patch not applied" in out and ' data-mtr-src="' not in out.split('>', 1)[0]   # no provenance attribute on the wrapper


def test_the_patch_path_emits_the_same_markup_in_both_twins(core_js):
    """The reviewer's gap: the patch path (applied patch, provenance attribute, rejection note) is byte-compared too."""
    for blk in ({"type": "motion_transition", "from": TEAM, "patch": PATCH},
                {"type": "motion_transition", "from": TEAM, "patch": PATCH, "key_map": {"curtis/gemini": "curtis/pm"}},
                {"type": "motion_transition", "from": TEAM, "patch": [{"op": "remove", "path": "/nodes/9"}]}):
        gas = _node(core_js, "console.log(JSON.stringify([renderAtoms([%s], {})]))" % json.dumps(blk))[0]
        assert _norm(_py(blk)) == _norm(gas)


TEXT_PROBE = r"""var w=document.querySelector('.mo-tr');var e=w.querySelector('.mtr-b .mtr-m');var s=getComputedStyle(e);
return {fill:s.webkitTextFillColor,color:s.color,scale:s.scale,text:e.textContent.trim().slice(0,20)};"""


@browser
def test_text_inside_a_moving_box_is_hidden_until_the_box_has_landed():
    """Text never transforms (it blurs on Android WebView): a moving tile's text is invisible while the tile is scaled, and
    fades in only once it is at rest (p >= 0.85, where its scale is exactly 1)."""
    import test_motion_transition as t
    blk = {"type": "motion_transition", "from": TREEMAP, "to": ICICLE}
    saved, t.PROBE = t.PROBE, TEXT_PROBE
    try:
        mid, rest, end = _page(blk, 0.5, 800), _page(blk, 0.85, 800), _page(blk, 1, 800)
    finally:
        t.PROBE = saved
    alpha = lambda c: float(c.split("/")[-1].strip(" )")) if "/" in c else (float(c.rsplit(",", 1)[-1].strip(" )")) if c.startswith("rgba") else 1.0)
    assert mid["text"] and alpha(mid["fill"]) == pytest.approx(0, abs=0.01) and mid["scale"] != "none", mid
    assert rest["scale"] in ("none", "1", "1 1"), rest
    assert alpha(end["fill"]) == pytest.approx(1, abs=0.01), end   # Chromium spells the colour color(srgb ...): compare alpha only
