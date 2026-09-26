#!/usr/bin/env python3
"""Build public/bricksdemo/design/index.html -- the live "describe a build" page (a2uicatalog.ai/bricksdemo/design).

The page calls POST /api/brick-design, shows tokens in / out / cost per render, lets the visitor pick Gemini model
or the Jev / Laya System-1 engines, and mounts the result in the real brick_build_3d atom. The atom's HTML is
rendered here (Python twin of the web renderer) around a sentinel partsModel; the page swaps the sentinel for the
model the Worker returns and loads it in an iframe srcdoc. Deterministic: same renderer in, same page out.

  python3 scripts/brick_models/build_design_page.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from renderers import web_article as w  # noqa: E402

OUT = ROOT / "public" / "bricksdemo" / "design" / "index.html"
SENTINEL = [["3005", 10, -24, 10, 0, 4]]
CODES = [0, 1, 2, 4, 14, 15, 19, 25, 27, 28, 70, 71, 72, 272, 288, 320, 484]

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<title>Brick Design Lab</title>
<meta name="description" content="Describe a LEGO build in a few words. A model designs it, real parts are validated, and the token and cost of every render is shown.">
<meta name="robots" content="noindex, nofollow">
<style>
:root{--bg:#f3f5f7;--fg:#0f1c28;--mute:#55636f;--rule:#d5dce3;--card:#fff;--acc:#c91a09;--ok:#1e7a45;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#10171e;--fg:#e6ecf1;--mute:#93a1ad;--rule:#26323d;--card:#16202a;--acc:#ff5a4a;--ok:#4cc38a;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#10171e;--fg:#e6ecf1;--mute:#93a1ad;--rule:#26323d;--card:#16202a;--acc:#ff5a4a;--ok:#4cc38a;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);padding-inline:16px;padding-block:24px;font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:960px;margin:0 auto;display:flex;flex-direction:column;gap:16px}
h1{font-size:20px;margin:0;text-wrap:balance}
p{margin:0;color:var(--mute);font-size:13px;max-width:72ch}
.panel{background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:14px;display:flex;flex-direction:column;gap:12px}
textarea{width:100%;min-height:64px;resize:vertical;font:inherit;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:8px}
.row{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font:inherit;font-size:12px;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:99px;padding:3px 10px;cursor:pointer}
label{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
select,button.go{font:inherit;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:6px 10px}
button.go{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600;cursor:pointer}
button.go:disabled{opacity:.55;cursor:progress}
.count{margin-left:auto;font-size:12px;color:var(--mute);font-variant-numeric:tabular-nums}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px}
.stat{border:1px solid var(--rule);border-radius:6px;padding:8px 10px}
.stat b{display:block;font-size:18px;font-variant-numeric:tabular-nums}
.stat span{font-size:11px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}
iframe{width:100%;height:640px;border:1px solid var(--rule);border-radius:8px;background:var(--card)}
.err{color:var(--acc);font-size:13px}
.note{font-size:12px}
.tbl{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:4px 8px;border-bottom:1px solid var(--rule);white-space:nowrap}
th{color:var(--mute);font-weight:500}
footer{border-top:1px solid var(--rule);padding-top:12px}
footer p{font-size:12px}
a{color:inherit}
</style>
</head>
<body>
<main>
<div>
<h1>Brick Design Lab</h1>
<p>Describe a build. A model designs it as a compact voxel grid, the server repairs and tiles it with real LEGO parts, and the brick_build_3d atom checks collisions, anchoring and balance live. Every render shows its tokens and cost.</p>
</div>
<section class="panel">
<textarea id="prompt" maxlength="150" placeholder="e.g. a giant red castle with four towers" aria-label="Describe a LEGO build"></textarea>
<div class="chips" id="chips"></div>
<div class="row">
<label>Gemini model
<select id="model">
<option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite &mdash; $0.10 in / $0.40 out per M</option>
<option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite &mdash; $0.30 in / $2.50 out per M</option>
<option value="gemini-3.7-flash" selected>gemini-3.7-flash &mdash; $0.75 in / $3.75 out per M</option>
</select></label>
<label><input type="checkbox" id="jev"> Use Jev instead (picks a template, no generation)</label>
<label><input type="checkbox" id="laya"> Use Laya instead (hosted, picks a template)</label>
</div>
<div class="row">
<button class="go" id="go" type="button">Design it</button>
<span id="err" class="err" role="alert"></span>
<span class="count" id="count">0 / 150</span>
</div>
</section>
<section class="panel" id="result" hidden>
<div class="stats" id="stats"></div>
<p class="note" id="how"></p>
<iframe id="view" title="3D build" sandbox="allow-scripts allow-same-origin"></iframe>
</section>
<section class="panel tbl" id="histp" hidden>
<table id="hist"><thead><tr><th>#</th><th>Engine / model</th><th>Prompt</th><th>Tokens in</th><th>Tokens out</th><th>Cost</th><th>Bricks</th><th>Time</th></tr></thead><tbody></tbody></table>
</section>
<footer>
<p>Cost is computed from the token counts the model returns and the published per-million-token price (Gemini 3.7 Flash is an introductory rate). Jev and Laya only choose a template, colour and size, so they generate no output tokens; Jev's per-token price is not published, and Laya is a free hosted service by <a href="https://laya.pensero.ai">Pensero</a>. Renders use real LDraw parts (CC BY 4.0). Fan-made, not affiliated with the LEGO Group.</p>
</footer>
</main>
<script>
(function(){
var PRE=__PRE__, POST=__POST__, HEX=__HEX__, EDGE=__EDGE__;
var $=function(id){return document.getElementById(id)};
var EX=['a giant red castle','a tall blue lighthouse','a cosy cottage','a tiny green pyramid','a long grey wall'];
EX.forEach(function(t){var b=document.createElement('button');b.type='button';b.className='chip';b.textContent=t;
  b.onclick=function(){$('prompt').value=t;upd()};$('chips').appendChild(b)});
function upd(){$('count').textContent=$('prompt').value.length+' / 150'}
$('prompt').addEventListener('input',upd);
$('jev').onchange=function(){if(this.checked)$('laya').checked=false;sync()};
$('laya').onchange=function(){if(this.checked)$('jev').checked=false;sync()};
function sync(){$('model').disabled=$('jev').checked||$('laya').checked}
function usd(v){return v==null?'—':(v<0.01?'$'+v.toFixed(5):'$'+v.toFixed(4))}
function n(v){return v==null?'—':Number(v).toLocaleString('en-GB')}
function show(model){
  var parts=(model.partsModel||[]).filter(function(p){return Array.isArray(p)&&/^[0-9a-z]{1,12}$/.test(p[0])}).map(function(p){
    var c=p[5]|0;return {p:p[0],x:+p[1]||0,y:+p[2]||0,z:+p[3]||0,r:p[4]|0,c:HEX[c]||'#c91a09',edge:EDGE[c]||'#333333'}});
  $('view').srcdoc='<!doctype html><meta charset="utf-8"><body style="margin:0;font:14px system-ui">'+PRE+JSON.stringify(parts)+POST+'</body>';
}
var runs=0;
$('go').onclick=function(){
  var prompt=$('prompt').value.trim();
  if(!prompt){$('err').textContent='Describe a build first.';return}
  var engine=$('jev').checked?'jev':$('laya').checked?'laya':'gemini';
  $('err').textContent='';$('go').disabled=true;$('go').textContent='Designing…';
  var t0=Date.now();
  fetch('/api/brick-design',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({prompt:prompt,engine:engine,model:engine==='gemini'?$('model').value:undefined})})
  .then(function(r){return r.json().catch(function(){return {ok:false,error:'unexpected response'}}).then(function(j){return {r:r,j:j}})})
  .then(function(x){
    var j=x.j;
    if(!j.ok){$('err').textContent=j.error||'Something went wrong.';return}
    var u=j.usage||{};
    $('result').hidden=false;
    $('stats').innerHTML='';
    [['Tokens in',n(u.promptTokens)],['Tokens out',n(u.outputTokens)],
     ['Cost',engine==='gemini'?usd(j.cost_usd):(engine==='laya'?'free':'n/a')],['Bricks',n(j.parts)],['Time',(j.ms/1000).toFixed(1)+' s']]
    .forEach(function(s){var d=document.createElement('div');d.className='stat';
      var b=document.createElement('b');b.textContent=s[1];var sp=document.createElement('span');sp.textContent=s[0];d.appendChild(b);d.appendChild(sp);$('stats').appendChild(d)});
    var how=engine==='gemini'?('Designed by '+j.model+' as a voxel grid'+(j.repaired&&j.repaired.dropped_cells?'; '+j.repaired.dropped_cells+' unanchored cells were dropped':'')+'.')
      :((engine==='jev'?'Jev':'Laya')+' chose "'+(j.choice&&j.choice.archetype)+'" (size '+(j.choice&&j.choice.size)+(j.choice&&j.choice.confidence!=null?', confidence '+(+j.choice.confidence).toFixed(2):'')+'); a deterministic generator built it. No text was generated.');
    $('how').textContent=how;
    show(j);
    runs++;$('histp').hidden=false;
    var tr=document.createElement('tr');
    [runs,engine==='gemini'?j.model:engine,prompt.length>34?prompt.slice(0,33)+'…':prompt,n(u.promptTokens),n(u.outputTokens),
     engine==='gemini'?usd(j.cost_usd):(engine==='laya'?'free':'n/a'),n(j.parts),(j.ms/1000).toFixed(1)+' s']
    .forEach(function(v){var td=document.createElement('td');td.textContent=v;tr.appendChild(td)});
    $('hist').tBodies[0].insertBefore(tr,$('hist').tBodies[0].firstChild);
  })
  .catch(function(){$('err').textContent='Could not reach the design service.'})
  .then(function(){$('go').disabled=false;$('go').textContent='Design it'});
};
sync();upd();
})();
</script>
</body>
</html>
"""


def build():
    atom = w._RENDERERS["brick_build_3d"]({"partsModel": SENTINEL, "height": 500, "parts": True})
    probe = [{"p": "3005", "x": 10, "y": -24, "z": 10, "r": 0, "c": "#c91a09", "edge": "#333333"}]
    needle = json.dumps(probe, separators=(",", ":"))
    assert atom.count(needle) == 1, "sentinel partsModel not found exactly once in the rendered atom"
    pre, post = atom.split(needle)
    hexes = {c: w._LDRAW_COLOURS[c] for c in CODES}
    edges = {c: w._LDRAW_EDGE.get(c, "#333333") for c in CODES}
    esc = lambda s: json.dumps(s).replace("</", "<\\/")  # noqa: E731
    return (PAGE.replace("__PRE__", esc(pre)).replace("__POST__", esc(post))
            .replace("__HEX__", json.dumps(hexes)).replace("__EDGE__", json.dumps(edges)))


def main(out=OUT):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
