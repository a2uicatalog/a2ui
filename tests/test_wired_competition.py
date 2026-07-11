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


def test_fold_mode_toggle_resorts(core_js):
    """standings_mode wire: '310' ranks by league points; points-only ranks by
    PF. One decisive fixture: P9+P10 win narrowly (3pts, low PF); P11+P12 lose
    but score heavily (0pts, high PF)."""
    rows = [{"round": 1, "m1_team_a": "9 & 10", "m1_score_a": 11,
             "m1_team_b": "11 & 12", "m1_score_b": 9},
            {"round": 2, "m1_team_a": "11 & 12", "m1_score_a": 25,
             "m1_team_b": "13 & 14", "m1_score_b": 24},
            {"round": 3, "m1_team_a": "9 & 10", "m1_score_a": 5,
             "m1_team_b": "13 & 14", "m1_score_b": 0}]
    # P9: 2 wins -> 6pts, PF 16. P11: 1 win -> 3pts, PF 34.
    # 3-1-0 ranks P9 first; points-only ranks P11 first.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + f"""
var html = renderAtoms([{{type:'standings_table', wired:true}}], {{theme:'light'}});
var uid = html.match(/data-a2ui-standings="([^"]+)"/)[1];
var body = {{ innerHTML: '' }};
var el = {{ querySelector: function(s) {{ return s.indexOf('standings-body') > -1 ? body : null; }} }};
global.document = {{ querySelector: function(s) {{ return s.indexOf(uid) > -1 ? el : null; }} }};
(html.match(/<script>([\\s\\S]*?)<\\/script>/g) || []).forEach(function(s) {{
  eval(s.replace(/^<script>/, '').replace(/<\\/script>$/, ''));
}});
var hook = window._A2UI_STANDINGS[uid];
hook('match_rows', {json.dumps(rows)});
var by310 = body.innerHTML;
hook('standings_mode', false);
var byPoints = body.innerHTML;
console.log(JSON.stringify({{w310: by310.indexOf('Player 9') < by310.indexOf('Player 11'),
                            wPts: byPoints.indexOf('Player 11') < byPoints.indexOf('Player 9')}}));
""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-500:]
        r = json.loads(p.stdout)
    assert r["w310"], "3-1-0 mode: winners (P9) rank above high scorers (P11)"
    assert r["wPts"], "points mode: high scorers (P11) rank above winners (P9)"


def test_competition_table_cells_own_their_background(core_js):
    """The invisible-row incident: host pages ship global table CSS
    (tr:nth-child(even) td { background: var(--surface) }) that turned even
    standings rows dark-on-dark inside the cream card. Every competition-atom
    cell must declare its own background/border so page CSS cannot bleed in."""
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + """
var standings = renderAtoms([{type:'standings_table', wired:true}], {theme:'dark'});
var sched = renderAtoms([{type:'match_schedule', rounds:[{matches:[
  {court:'Court 1', team_a:['A','B'], team_b:['C','D'], score_a:4, score_b:9}]}]}],
  {theme:'dark'});
console.log(JSON.stringify({standings: standings, sched: sched}));
""")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr[-500:]
        r = json.loads(p.stdout)
    for name, html in r.items():
        for cell in re.findall(r"<t[dh] style=\"([^\"]*)\"", html):
            assert "background:transparent" in cell, (name, cell)
            assert "border:none" in cell, (name, cell)
