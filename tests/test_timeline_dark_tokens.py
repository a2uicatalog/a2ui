"""A dark motion_timeline stage re-points the page-level --a2ui-* / --text token family at the repo's dark palette, so the data
atoms embedded in a film (choropleth_map, geo_map, sankey_flow, charts) are readable. Light stages emit nothing (unchanged).

  1. Unit: the luminance gate and the token string, on both twins (Python renderers/web_article.py, GAS atoms_motion.gs).
  2. Twins: Python and GAS render the same stage tokens (modulo random ids).
  3. Browser: a dark film holding the four data atoms, on a page whose own tokens are the light defaults, paints every text node
     with contrast >= 4.5:1 against the nearest painted ancestor (computed with getComputedStyle in headless Chromium).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gen_mcp_apps_bundle as gen  # noqa: E402

from renderers import web_article as wa  # noqa: E402

IBERIA = {"lon_min": -12, "lon_max": 4, "lat_min": 36, "lat_max": 44}
LIS, MAD = (38.72, -9.14), (40.42, -3.70)
GEO = {"type": "geo_map", "id": "geo", "title": "Trip", "projection": "mercator", "frame": IBERIA,
       "points": [{"label": "Lisbon", "lat": LIS[0], "lon": LIS[1]}, {"label": "Madrid", "lat": MAD[0], "lon": MAD[1]}],
       "lines": [{"id": "l1", "label": "Leg 1", "path": [{"lat": LIS[0], "lon": LIS[1]}, {"lat": MAD[0], "lon": MAD[1]}]}],
       "regions": [{"id": "PRT", "category": "visited"}, {"id": "ESP", "category": "visited"}], "categories": ["visited", "planned"],
       "place": {"x": 2, "y": 4, "w": 46, "h": 44}}
CHORO = {"type": "choropleth_map", "id": "cho", "title": "Population", "region_set": "europe-countries",
         "values": [{"id": "PRT", "value": 10}, {"id": "ESP", "value": 47}, {"id": "FRA", "value": 68}, {"id": "ITA", "value": 59}],
         "place": {"x": 52, "y": 4, "w": 46, "h": 44}}
SANKEY = {"type": "sankey_flow", "id": "snk", "title": "Flow", "nodes": [{"id": "a", "label": "Source"}, {"id": "b", "label": "Mid"}, {"id": "c", "label": "Sink"}],
          "links": [{"source": "a", "target": "b", "value": 5}, {"source": "b", "target": "c", "value": 3}],
          "place": {"x": 2, "y": 52, "w": 46, "h": 44}}
CHART = {"type": "histogram", "id": "his", "title": "Spread", "values": [1, 2, 2, 3, 3, 3, 4, 4, 5, 8, 9], "place": {"x": 52, "y": 52, "w": 46, "h": 44}}
DATA = [GEO, CHORO, SANKEY, CHART]


def film(**kw) -> dict:
    return {"type": "motion_timeline", "duration": 6, "controls": False, "blocks": json.loads(json.dumps(DATA)), "tracks": [], **kw}


def _py(b: dict) -> str:
    return wa._RENDERERS["motion_timeline"](b)


@pytest.fixture(scope="module")
def core_js():
    bundle = gen.build_bundle()
    return [b for b in re.findall(r"<script>\n(.*?)\n</script>", bundle, re.S) if "a2ui-core" in b[:300]][0]


def _gas(core_js: str, blocks: list[dict]) -> list[str]:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "d.js"
        d.write_text("global.window = global;\n" + core_js + "\nvar B = " + json.dumps(blocks)
                     + ";console.log(JSON.stringify(B.map(function(b){ return renderAtoms([b], {}); })));")
        p = subprocess.run(["node", str(d)], capture_output=True, text=True, timeout=120)
        assert p.returncode == 0, p.stderr[-1500:]
        return json.loads(p.stdout.strip().split("\n")[-1])


def _stage_style(html: str) -> str:
    m = re.search(r'<div class="mt-st" style="([^"]*)"', html)
    assert m
    return m.group(1)


TOKEN_RE = re.compile(r"--a2ui-text:[^;]+;")
CASES = {"default (dark theme)": {}, "theme dark": {"theme": "dark"}, "dark custom bg": {"background": "#101820", "theme": "light"},
         "theme light": {"theme": "light"}, "light custom bg": {"background": "#ffffff"}, "mid grey bg": {"background": "#808080"}}
DARK = {"default (dark theme)", "theme dark", "dark custom bg"}


def test_dark_stage_sets_the_token_family_and_light_stage_sets_none():
    for name, kw in CASES.items():
        style = _stage_style(_py(film(**kw)))
        if name in DARK:
            for tok in ("--a2ui-text", "--a2ui-muted", "--a2ui-faint", "--a2ui-surface", "--a2ui-surface-muted", "--a2ui-border",
                        "--a2ui-border-soft", "--a2ui-shadow", "--text", "--muted", "--text-muted", "--surface", "--border"):
                assert tok + ":" in style, (name, tok)
            assert "--a2ui-text:" + wa._CV_THEMES["dark"]["ink"] in style
        else:
            assert "--a2ui-" not in style and "--text:" not in style, name


def test_light_stage_output_is_unchanged_by_the_token_code():
    # a dark stage differs from the light path only by the one token run; light stages carry no declaration at all
    d = _py(film())
    assert len(re.findall(r"--a2ui-text:", d)) == 1
    assert "--a2ui-text:" not in re.sub(r"--a2ui-text:.*?--bg:#[0-9a-f]{6};", "", d)
    for kw in ({"theme": "light"}, {"background": "#ffffff"}):
        assert "--a2ui-text:" not in _py(film(**kw))


def _norm(h: str) -> str:
    h = re.sub(r"(?<=[a-z\d])-[a-z0-9]{6}\b", "-X", h)
    toks = [x for t in re.findall(r'id="([a-z0-9]{7})"|@keyframes ([a-z0-9]{7})\b', h) for x in t if x]
    for i, u in enumerate(dict.fromkeys(toks)):
        h = h.replace(u, "RID%d" % i)
    for i, u in enumerate(dict.fromkeys(re.findall(r'id="(?:mt|mo)-([a-z0-9]{6})"', h))):
        h = h.replace(u, "UID%d" % i)
    return h


def test_twins_emit_the_same_stage_tokens(core_js):
    blocks = [film(**kw) for kw in CASES.values()]
    gas = _gas(core_js, blocks)
    for (name, _), b, g in zip(CASES.items(), blocks, gas):
        assert _stage_style(_norm(g)) == _stage_style(_norm(_py(b))), name
        assert (("--a2ui-text:" in g) == (name in DARK)), name


CHROMIUM = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")

PROBE = r"""
<script>
function lum(c){var a=c.map(function(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)});return 0.2126*a[0]+0.7152*a[1]+0.0722*a[2]}
function rgba(s){var m=s.match(/rgba?\(([^)]+)\)/);if(!m)return null;var p=m[1].split(/[ ,\/]+/).map(parseFloat);return [p[0],p[1],p[2],p.length>3?p[3]:1]}
function over(f,b){var a=f[3];return [f[0]*a+b[0]*(1-a),f[1]*a+b[1]*(1-a),f[2]*a+b[2]*(1-a),1]}
function backdrop(el){var stack=[];for(var e=el;e&&e.nodeType===1;e=e.parentElement){var c=rgba(getComputedStyle(e).backgroundColor);if(c&&c[3]>0)stack.push(c);if(c&&c[3]>=1)break}
  var b=[255,255,255,1];for(var i=stack.length-1;i>=0;i--)b=over(stack[i],b);return b}
window.addEventListener('load',function(){setTimeout(function(){
  var out=[],st=document.querySelector('.mt-st');
  var w=document.createTreeWalker(st,NodeFilter.SHOW_TEXT);
  while(w.nextNode()){var n=w.currentNode,t=n.nodeValue.trim();if(!t)continue;var el=n.parentElement;
    if(el.closest('script,style,.sr-only'))continue;
    var hid=false;for(var a=el;a&&a!==st;a=a.parentElement){var ac=getComputedStyle(a),ar=a.getBoundingClientRect();if(ac.display==='none'||ac.visibility==='hidden'||(ac.clip&&ac.clip!=='auto')||ar.width<=1.5||ar.height<=1.5){hid=true;break}}if(hid)continue;
    var cs=getComputedStyle(el),r=el.getBoundingClientRect();if(r.width<2||r.height<2||cs.display==='none')continue;
    var isSvg=el instanceof SVGElement,col=rgba(isSvg?cs.fill:cs.color);if(!col)continue;
    var bg=backdrop(el),fg=over(col,bg),l1=lum(fg),l2=lum(bg),cr=(Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05);
    out.push({t:t.slice(0,40),ratio:Math.round(cr*100)/100,atom:(el.closest('[data-mt-id]')||{dataset:{}}).dataset.mtId||'',fg:cs.fill&&isSvg?cs.fill:cs.color,bg:'rgb('+bg.slice(0,3).map(Math.round)+')'})}
  var pre=document.createElement('pre');pre.id='probe';pre.textContent=JSON.stringify(out);document.body.appendChild(pre)},300)});
</script>
"""


def probe(b: dict) -> list[dict]:
    # a PAGE whose own tokens are the light defaults (nothing defines --a2ui-* or --text), as an article is
    html = "<!doctype html><meta charset=utf-8><body style='margin:0;background:#fff;color:#171717;width:1000px'>" + _py(b) + PROBE
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "p.html"
        f.write_text(html)
        out = subprocess.run([CHROMIUM, "--headless=new", "--password-store=basic", "--no-sandbox", "--disable-gpu", "--window-size=1100,900",
                              "--virtual-time-budget=2500", "--dump-dom", f"file://{f}#t=3"], capture_output=True, text=True, timeout=120).stdout
    m = re.search(r'<pre id="probe">(.*?)</pre>', out, re.S)
    assert m, out[:400]
    import html as _h
    return json.loads(_h.unescape(m.group(1)))


@pytest.mark.skipif(not CHROMIUM, reason="no Chromium installed")
def test_dark_film_data_atoms_meet_contrast_in_a_real_browser():
    rows = probe(film())
    seen = {r["atom"] for r in rows}
    assert {"geo", "cho", "snk", "his"} <= seen, seen
    bad = [r for r in rows if r["ratio"] < 4.5]
    assert not bad, bad[:8]
    print("min contrast", min(r["ratio"] for r in rows), "over", len(rows), "text nodes")
