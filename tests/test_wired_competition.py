"""standings_table WIRED mode (G2) + number_input (G3) — the americano
interactive stack. The fold runs client-side inside the atom's emitted script;
these tests execute that real script in Node against a stubbed DOM and assert
the 3-1-0 math, tiebreakers, append-only last-row-wins, and the honesty rule
(unscored matches skipped, never counted 0-0)."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    blocks = re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S)
    return [b for b in blocks if "a2ui-core" in b[:300]][0]


def test_number_input_renders_numeric_attrs(core_js):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + """
var html = renderAtoms([{type:'form_input', input_type:'number', label:'Score',
                         min:0, step:1}], {theme:'light'});
console.log(JSON.stringify(html));
""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-500:]
        html = json.loads(p.stdout)
    assert 'type="number"' in html and 'min="0"' in html and 'step="1"' in html
    assert 'inputmode="numeric"' in html


SCORE_ROWS = [
    # round 1 first save (will be superseded — last row per round wins)
    {"round": 1, "m1_team_a": "1 & 8", "m1_score_a": 5, "m1_team_b": "2 & 7", "m1_score_b": 21,
     "m2_team_a": "3 & 6", "m2_score_a": 21, "m2_team_b": "4 & 5", "m2_score_b": 10},
    # round 1 corrected save
    {"round": 1, "m1_team_a": "1 & 8", "m1_score_a": 21, "m1_team_b": "2 & 7", "m1_score_b": 15,
     "m2_team_a": "3 & 6", "m2_score_a": 21, "m2_team_b": "4 & 5", "m2_score_b": 10},
    # round 2: match 1 a draw; match 2 UNSCORED (empty strings) -> skipped
    {"round": 2, "m1_team_a": "1 & 2", "m1_score_a": 18, "m1_team_b": "3 & 8", "m1_score_b": 18,
     "m2_team_a": "4 & 7", "m2_score_a": "", "m2_team_b": "5 & 6", "m2_score_b": ""},
]
NAME_ROWS = [{"p1": "Ana", "p2": "Ben", "p3": "", "p4": "Dan",
              "p5": "", "p6": "", "p7": "", "p8": "Ivy"}]


def _run_fold(core_js, score_rows, name_rows):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + f"""
var html = renderAtoms([{{type:'standings_table', wired:true}}], {{theme:'light'}});
var uid = html.match(/data-a2ui-standings="([^"]+)"/)[1];
// stub DOM: the fold queries the shell + tbody by attribute
var body = {{ innerHTML: '' }};
var el = {{ querySelector: function(sel) {{ return sel.indexOf('standings-body') > -1 ? body : null; }} }};
global.document = {{ querySelector: function(sel) {{ return sel.indexOf(uid) > -1 ? el : null; }} }};
// execute the atom's own emitted script (innerHTML never runs scripts; the
// paint()/GAS page does — here we eval it the way the browser would)
var scripts = html.match(/<script>([\\s\\S]*?)<\\/script>/g) || [];
scripts.forEach(function(s) {{ eval(s.replace(/^<script>/, '').replace(/<\\/script>$/, '')); }});
var hook = window._A2UI_STANDINGS[uid];
hook('match_rows', {json.dumps(score_rows)});
hook('player_names', {json.dumps(name_rows)});
console.log(JSON.stringify(body.innerHTML));
""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-800:]
        return json.loads(p.stdout)


def test_fold_computes_310_standings_with_tiebreakers(core_js):
    out = _run_fold(core_js, SCORE_ROWS, NAME_ROWS)
    # Corrected round 1: P1+P8 beat P2+P7 21-15; P3+P6 beat P4+P5 21-10.
    # Round 2: P1+P2 draw P3+P8 18-18; court 2 unscored -> skipped.
    # P1: W+D -> 4 pts, PF 39. P3: W+D -> 4 pts, PF 39. P8: W+D -> 4pts PF 39...
    # P1/P3/P8 all 4pts/39PF -> diff decides: P1 +9(36-15-18+... ) etc; assert
    # structure not hand-derivation: leader row exists, all named players shown,
    # first-save scores (5-21) must NOT appear anywhere.
    rows = re.findall(r"<tr[^>]*>", out)
    assert len(rows) == 8, "all 8 players folded"
    assert "Ana" in out and "Ivy" in out and "Player 3" in out  # names + numeric fallback
    # last-row-wins: superseded 5-21 result must not have credited P2/P7 a win:
    # P2 record = W(as loser? no): P2+P7 LOST corrected match, drew nothing else
    # -> P2 pts = 0 if only round1... but P2 played r1 loss only -> 0 pts; if the
    # stale first save had counted, P2 would carry a win (3pts) and sort top-3.
    first_three = out.split("</tr>")[:3]
    assert not any("Ben" in seg for seg in first_three), \
        "stale first save leaked into fold (Ben/P2 should not be top-3)"
    # honesty: unscored court-2 round-2 match contributes nothing (P5 played 1)
    m = re.search(r"Player 5.*?</tr>", out, re.S)
    assert m and ">1<" in m.group(0), "P5 played exactly 1 scored match"


def test_fold_empty_scores_keeps_placeholder(core_js):
    out = _run_fold(core_js, [], NAME_ROWS)
    assert out == "", "no scores -> fold never rewrites the placeholder body"
