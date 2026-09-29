#!/usr/bin/env python3
"""Build public/bricksdemo/design/index.html -- the live "describe a build" page (a2uicatalog.ai/bricksdemo/design).

Two modes: "Design with Gemini" (free-form prompt, one forced tool call builds a voxel grid) or "Pick a template"
(direct archetype/colour/size selection, no model call, instant, zero tokens). The Jev/Laya System-1 "chooser"
engines were removed 2026-09-27 (Curtis's call: the archetype/colour/size space is 6x15x4, fully enumerable, so a
router/chooser model adds nothing over a plain selector -- see a2ui-private's brick-jev-laya-showdown.md for the
shelved comparison angle).

The page calls POST /api/brick-design (`engine: "gemini"` or `"template"`) and mounts the result in the real
brick_build_3d atom. The atom's HTML is rendered here (Python twin of the web renderer) around a sentinel
partsModel; the page swaps the sentinel for the model the Worker returns and loads it in an iframe srcdoc.
Deterministic: same renderer in, same page out.

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
# Real source of truth for the "View in Three.js" viewer's rotation/placement/camera-fit math -- read and
# embedded verbatim below (same "read the real file, embed it" pattern web_article.py uses for atoms_brick.gs's
# _brickMount/_brickKit), so tests/... scripts/test_threejs_view_math.mjs tests the SAME text this page ships,
# not a hand-copied twin.
THREEJS_VIEW_MATH = (HERE / "threejs_view_math.js").read_text(encoding="utf-8")
SENTINEL = [["3005", 10, -24, 10, 0, 4]]
CODES = [0, 1, 2, 4, 14, 15, 19, 25, 27, 28, 70, 71, 72, 272, 288, 320, 484]

CNAMES = {0: 'Black', 1: 'Blue', 2: 'Green', 4: 'Red', 14: 'Yellow', 15: 'White', 19: 'Tan', 25: 'Orange', 27: 'Lime',
          28: 'Dark Tan', 70: 'Reddish Brown', 71: 'Light Bluish Gray', 72: 'Dark Bluish Gray', 272: 'Dark Blue',
          288: 'Dark Green', 320: 'Dark Red', 484: 'Dark Orange'}

# Template picker options -- these literal values must match a2ui-private/mcp-worker/src/brick-design.js's
# ARCHETYPES keys and COLOURS letters exactly (the Worker validates against its own tables; an unknown value there
# just falls back to a default, it does not error, so a typo here would silently pick the wrong template/colour
# rather than fail loudly -- keep this list and that file's keys in sync by hand).
ARCHETYPES = [('house', 'House / cottage'), ('tower', 'Tower / lighthouse'), ('pyramid', 'Pyramid'),
              ('castle', 'Castle'), ('wall', 'Wall'), ('block', 'Block')]
TCOLOURS = [('r', 'Red'), ('b', 'Blue'), ('g', 'Green'), ('y', 'Yellow'), ('w', 'White'), ('k', 'Black'),
            ('o', 'Orange'), ('l', 'Light grey'), ('d', 'Dark grey'), ('t', 'Tan'), ('n', 'Brown'), ('m', 'Maroon'),
            ('e', 'Dark green'), ('u', 'Navy'), ('i', 'Lime')]
TSIZES = [('small', 'Small'), ('medium', 'Medium'), ('large', 'Large'), ('huge', 'Huge')]

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<title>Brick Design Lab</title>
<meta name="description" content="Design a LEGO build with Gemini, or pick a template directly. Real parts are validated, and the token and cost of every render is shown.">
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
#csearch,#omrset,#setsearch{width:100%;font:inherit;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:8px}
textarea{width:100%;min-height:64px;resize:vertical;font:inherit;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:8px}
.row{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font:inherit;font-size:12px;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:99px;padding:3px 10px;cursor:pointer}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;max-height:440px;overflow-y:auto;padding-right:4px}
.gcard{border:1px solid var(--rule);border-radius:8px;overflow:hidden;background:var(--bg);cursor:pointer;text-align:left;font:inherit;color:inherit;padding:0;display:flex;flex-direction:column}
.gcard:hover{border-color:var(--acc)}
.gcard img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;display:block}
.gcard .gc-body{padding:6px 8px;display:flex;flex-direction:column;gap:2px}
.gcard .gc-title{font-size:12px;font-weight:600;line-height:1.25;max-height:2.5em;overflow:hidden;color:var(--fg)}
.gcard .gc-pct{font-size:11px;font-variant-numeric:tabular-nums;color:var(--acc)}
.gcard .gc-pct.hi{color:var(--ok)}
label{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
select,button.go{font:inherit;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:6px 10px}
button.go{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600;cursor:pointer}
button.go:disabled{opacity:.55;cursor:progress}
button.alt{background:var(--bg);color:var(--fg);border-color:var(--rule)}
button.alt[aria-pressed="true"]{border-color:var(--acc);color:var(--acc);font-weight:600}
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
#tjscanvas{width:100%;height:480px;border:1px solid var(--rule);border-radius:8px;display:block;background:radial-gradient(120% 90% at 50% 30%,#fafbfd,#cdd6e0)}
</style>
<script type="importmap">
{
  "imports": {
    "three": "/vendors/threejs/three.module.js",
    "three/addons/controls/OrbitControls.js": "/vendors/threejs/addons/controls/OrbitControls.js",
    "three/addons/environments/RoomEnvironment.js": "/vendors/threejs/addons/environments/RoomEnvironment.js"
  }
}
</script>
</head>
<body>
<main>
<div>
<h1>Brick Design Lab</h1>
<p>Design with Gemini (a free-form prompt, built as a compact voxel grid and tiled with real LEGO parts), sketch with Gemini (the same prompt, but planned as real stud/plate-sized volumes with real carved openings -- better proportions and real windows/doors, fewer, bigger model calls), or pick a template directly (instant, no model call, zero tokens). The brick_build_3d atom checks collisions, anchoring and balance live.</p>
</div>
<section class="panel">
<div class="row" role="tablist" aria-label="Design mode">
<button class="go alt" id="modeGemini" type="button" aria-pressed="true">Design with Gemini</button>
<button class="go alt" id="modeSketch" type="button" aria-pressed="false">Sketch with Gemini</button>
<button class="go alt" id="modeTemplate" type="button" aria-pressed="false">Pick a template</button>
</div>
<div id="geminiControls">
<textarea id="prompt" maxlength="150" placeholder="e.g. a giant red castle with four towers" aria-label="Describe a LEGO build"></textarea>
<div class="chips" id="chips"></div>
<div class="row">
<label>Gemini model
<select id="model">
<option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite &mdash; $0.10 in / $0.40 out per M</option>
<option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite &mdash; $0.30 in / $2.50 out per M</option>
<option value="gemini-3.7-flash" selected>gemini-3.7-flash &mdash; $0.75 in / $3.75 out per M</option>
</select></label>
</div>
</div>
<div id="templateControls" hidden>
<div class="row">
<label>Shape
<select id="tArch">__ARCH_OPTS__</select></label>
<label>Colour
<select id="tColour">__COLOUR_OPTS__</select></label>
<label>Size
<select id="tSize">__SIZE_OPTS__</select></label>
</div>
<p class="note">No model call -- built directly from your picks, instant and free.</p>
</div>
<div class="row">
<button class="go" id="go" type="button">Design it</button>
<span id="err" class="err" role="alert"></span>
<span class="count" id="count">0 / 150</span>
</div>
</section>
<section class="panel" id="charp">
<label for="csearch"><b>Browse the parts catalogue</b> <span class="note">search real LEGO parts and minifigures by id or name, then pick one to add beside your build</span></label>
<input id="csearch" type="search" placeholder="e.g. 3001, slope, arch, knight, plate 2 x 4" aria-label="Search the parts catalogue" autocomplete="off">
<div class="chips" id="cres" aria-live="polite"></div>
<div class="row"><button class="go alt" id="cclear" type="button" hidden>Remove added parts</button><span class="note" id="cnote"></span></div>
</section>
<section class="panel">
<label><b>Browse real sets by coverage</b> <span class="note">honestly ranked by how much of each real official set this catalogue can render today (50%+ shown, nothing hidden behind a pass/fail cutoff) -- click a card to import it</span></label>
<div class="gallery" id="gallery"></div>
<p class="note" id="gallerynote">Loading…</p>
</section>
<section class="panel">
<label for="setsearch"><b>Find a real LEGO set</b> <span class="note">search by name (e.g. "Harry Potter", "Hogwarts", "Millennium Falcon") via Rebrickable, then pick one to import -- replaces the current build</span></label>
<input id="setsearch" type="search" placeholder="e.g. Harry Potter" aria-label="Search real LEGO sets by name" autocomplete="off">
<div class="chips" id="setres" aria-live="polite"></div>
<p class="note" id="setnote"></p>
<label for="omrset">Or enter a set number directly</label>
<div class="row"><input id="omrset" type="text" placeholder="e.g. 75978-1" aria-label="LEGO set number" autocomplete="off" style="max-width:180px">
<button class="go alt" id="omrgo" type="button">Import set</button><span class="note" id="omrnote"></span></div>
</section>
<section class="panel" id="result" hidden>
<div class="stats" id="stats"></div>
<p class="note" id="how"></p>
<div class="row"><button class="go" id="manual" type="button">Build manual</button>
<button class="go alt" id="csv" type="button">Rebrickable list (CSV)</button>
<button class="go alt" id="tjsgo" type="button" aria-pressed="false">View in Three.js</button><span class="note" id="mstat"></span></div>
<iframe id="view" title="3D build" sandbox="allow-scripts allow-same-origin"></iframe>
<div id="tjswrap" hidden>
<canvas id="tjscanvas" role="img" aria-label="Three.js 3D build view"></canvas>
<div class="row" id="tjscontrols" hidden style="gap:10px">
<button class="go alt" id="tjsplay" type="button" aria-pressed="false">Animate</button>
<span id="tjsstepwrap" style="display:flex;gap:10px;align-items:center;flex:1">
<label for="tjsstep" style="font-size:12px;color:var(--mute)">Build step</label>
<input type="range" id="tjsstep" min="1" max="1" value="1" style="flex:1">
<span class="note" id="tjsstepnote"></span>
</span>
</div>
<p class="note" id="tjsstatus"></p>
</div>
</section>
<section class="panel tbl" id="histp" hidden>
<table id="hist"><thead><tr><th>#</th><th>Engine / model</th><th>Prompt / picks</th><th>Tokens in</th><th>Tokens out</th><th>Cost</th><th>Bricks</th><th>Time</th></tr></thead><tbody></tbody></table>
</section>
<footer>
<p>Cost is computed from the token counts the model returns and the published per-million-token price (Gemini 3.7 Flash is an introductory rate). The template picker makes no model call, so it generates no text and costs nothing. Renders use real LDraw parts (CC BY 4.0). Set names and images in the coverage gallery and search are from Rebrickable. Fan-made, not affiliated with or endorsed by the LEGO Group. LEGO&reg; is a trademark of the LEGO Group, which does not sponsor, authorize or endorse this content.</p>
<p>The main 3D view is rendered with this catalogue's own WebGL renderer. The "View in Three.js" button renders the SAME real build with <a href="https://threejs.org/">three.js</a> (MIT License, &copy; 2010-2026 three.js authors, vendored at <code>/vendors/threejs/</code>, never loaded from a CDN -- see <a href="/THIRD-PARTY-NOTICES.md">THIRD-PARTY-NOTICES.md</a>) instead, with real per-part material appearance (trans-clear, chrome, metal, pearlescent, rubber) from each part's real LDraw colour -- an appearance axis the live renderer's hand-rolled shader has no concept of at all.</p>
</footer>
</main>
<script>
(function(){
var PRE=__PRE__, POST=__POST__, HEX=__HEX__, EDGE=__EDGE__, CNAME=__CNAME__;
var $=function(id){return document.getElementById(id)};
var EX=['a giant red castle','a tall blue lighthouse','a cosy cottage','a tiny green pyramid','a long grey wall'];
EX.forEach(function(t){var b=document.createElement('button');b.type='button';b.className='chip';b.textContent=t;
  b.onclick=function(){$('prompt').value=t;upd()};$('chips').appendChild(b)});
function upd(){$('count').textContent=$('prompt').value.length+' / 150'}
$('prompt').addEventListener('input',upd);
var MODE='gemini';
function setMode(m){
  MODE=m;
  $('modeGemini').setAttribute('aria-pressed',String(m==='gemini'));
  $('modeSketch').setAttribute('aria-pressed',String(m==='sketch'));
  $('modeTemplate').setAttribute('aria-pressed',String(m==='template'));
  $('geminiControls').hidden=m==='template';
  $('templateControls').hidden=m!=='template';
  $('model').disabled=m==='template';
}
$('modeGemini').onclick=function(){setMode('gemini')};
$('modeSketch').onclick=function(){setMode('sketch')};
$('modeTemplate').onclick=function(){setMode('template')};
var LABEL={gemini:'Gemini',sketch:'Sketch',template:'Template'};
function costText(j,e){return e==='template'?'free':usd(j.cost_usd)}
function usd(v){return v==null?'—':(v<0.01?'$'+v.toFixed(5):'$'+v.toFixed(4))}
function n(v){return v==null?'—':Number(v).toLocaleString('en-GB')}
function show(model){
  var parts=(model.partsModel||[]).filter(function(p){return Array.isArray(p)&&/^[0-9a-z-]{1,24}$/.test(p[0])}).map(function(p){
    var c=p[5]|0;return {p:p[0],x:+p[1]||0,y:+p[2]||0,z:+p[3]||0,r:p[4]|0,c:HEX[c]||'#c91a09',edge:EDGE[c]||'#333333'}});
  $('view').srcdoc='<!doctype html><meta charset="utf-8"><body style="margin:0;font:14px system-ui">'+PRE+JSON.stringify(parts)+POST+'</body>';
}

var PIDX=null,QUANT=1,last=null;
fetch('/parts/index.json').then(function(r){return r.json()}).then(function(j){PIDX=j.parts;QUANT=j.quant||1;csearch()}).catch(function(){});
function pname(id){return (PIDX&&PIDX[id]&&PIDX[id].title||id).replace(/\s+/g,' ').trim()}
function esc(t){return String(t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function hexOf(cssColour){var m=/rgb\((\d+), (\d+), (\d+)\)/.exec(cssColour);if(!m)return cssColour;
  return '#'+[1,2,3].map(function(i){return ('0'+(+m[i]).toString(16)).slice(-2)}).join('')}
function codeOfHex(h){for(var k in HEX)if(HEX[k]===h)return +k;return null}
function agg(parts){var g={};parts.forEach(function(p){var k=p[0]+'|'+p[5];g[k]=(g[k]||0)+1});
  return Object.keys(g).sort().map(function(k){var a=k.split('|');return {id:a[0],col:+a[1],n:g[k]}})}
$('csv').onclick=function(){
  if(!last)return;
  var rows={};
  agg(last.partsModel).filter(function(r){return !isChar(r.id)}).forEach(function(r){var rb=/^\d+[a-z]$/.test(r.id)?r.id.slice(0,-1):r.id,k=rb+','+r.col;rows[k]=(rows[k]||0)+r.n});
  var csv='Part,Color,Quantity\n'+Object.keys(rows).sort().map(function(k){return k+','+rows[k]}).join('\n')+'\n';
  var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='wanted-list.csv';
  document.body.appendChild(a);a.click();a.remove()};
function frameDoc(parts,orbit){
  return '<!doctype html><meta charset="utf-8"><body style="margin:0;font:14px system-ui">'+(orbit?PRE:PRE.replace('"orbit":true','"orbit":false'))+JSON.stringify(parts)+POST+'</body>'}
function until(fn,ms){return new Promise(function(res){var t0=Date.now();(function tick(){var v;try{v=fn()}catch(e){}
  if(v||Date.now()-t0>ms)res(v);else setTimeout(tick,250)})()})}
function hookFrames(win,doc){var orig=win.requestAnimationFrame;
  win.__cap=null;
  win.requestAnimationFrame=function(cb){return orig.call(win,function(t){cb(t);
    var c=win.__cap;if(c&&++c.n>=3){win.__cap=null;
      // Composite onto a plain white backing (same technique the atom's own screenshot harness uses) before
      // encoding to JPEG: the canvas's own background is transparent by design (alpha:true, no cfg.bg here), and
      // JPEG has no alpha channel, so encoding it directly leaves every transparent pixel solid BLACK -- real
      // instruction booklets have white pages, not black ones.
      var cv=doc.querySelector('canvas'),o=document.createElement('canvas');o.width=cv.width;o.height=cv.height;
      var g=o.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,o.width,o.height);g.drawImage(cv,0,0);
      c.res(o.toDataURL('image/jpeg',0.9))}})}}
function grab(win){return new Promise(function(res){win.__cap={n:0,res:res}})}
$('manual').onclick=function(){
  if(!last)return;
  var win=window.open('','_blank');
  if(!win){$('mstat').textContent='Allow pop-ups to open the manual.';return}
  win.document.write('<title>Building manual</title><body style="font:16px system-ui;padding:24px">Rendering build steps…</body>');
  var btn=$('manual');btn.disabled=true;$('mstat').textContent='Rendering steps…';
  var fr=document.createElement('iframe');
  // Positioned ON-screen (opacity-hidden, not off-screen): brick_build_3d's WebGL renderer pauses its own draw
  // loop via IntersectionObserver once its canvas stops intersecting the viewport (a real, deliberate perf
  // optimisation for the normal case of a build scrolling off-screen on a real page) -- an off-screen iframe
  // never intersects, so it never draws a single frame and every captured image comes back fully transparent.
  // opacity near-zero plus pointer-events:none keeps it invisible to the visitor without breaking that check.
  fr.style.cssText='position:fixed;left:0;top:0;width:900px;height:720px;border:0;opacity:0.01;pointer-events:none;z-index:-1';
  fr.srcdoc=frameDoc(last.parts,false);document.body.appendChild(fr);
  var doc,w2,steps=[];
  until(function(){doc=fr.contentDocument;w2=fr.contentWindow;return doc&&doc.querySelector('input[type=range]')&&/Every part anchored/.test(doc.body.innerText)&&!/not checked|Loading/.test(doc.body.innerText)},60000)
  .then(function(){
    var b=[].slice.call(doc.querySelectorAll('button')).filter(function(x){return x.textContent.trim()==='Instructions'})[0];if(b)b.click();
    hookFrames(w2,doc);
    var rg=doc.querySelector('input[type=range]'),S=+rg.max,k=0;
    function box(){var sp=[].slice.call(doc.querySelectorAll('span')).filter(function(x){return x.textContent==='New this step:'})[0];return sp&&sp.parentNode}
    return new Promise(function(done){(function next(){
      if(++k>S){done();return}
      rg.value=k;rg.dispatchEvent(new w2.Event('input',{bubbles:true}));rg.dispatchEvent(new w2.Event('change',{bubbles:true}));
      grab(w2).then(function(img){
        var chips=[],bx=box();
        if(bx)[].slice.call(bx.children).slice(1).forEach(function(c){var m=/^×(\d+) (.+)$/.exec(c.textContent),sw=c.firstChild;
          chips.push({n:m?+m[1]:1,id:m?m[2]:c.textContent,col:codeOfHex(hexOf(sw.style.backgroundColor))})});
        steps.push({img:img,chips:chips});$('mstat').textContent='Rendering steps… '+k+' / '+S;next()})})()})})
  .then(function(){
    fr.remove();
    var j=last.j,total=last.partsModel.length,list=agg(last.partsModel);
    var css='@page{size:A4;margin:12mm}*{box-sizing:border-box}body{margin:0;font:14px/1.4 system-ui,sans-serif;color:#111;background:#fff}'+
      '.pg{page-break-after:always;min-height:270mm;display:flex;flex-direction:column;padding:6mm}.pg:last-child{page-break-after:auto}'+
      'h1{font-size:34px;margin:0 0 6px}h2{font-size:18px;margin:0 0 10px}.mut{color:#555}.step{font-size:64px;font-weight:800;color:#c91a09;line-height:1}'+
      '.img{flex:1;display:flex;align-items:center;justify-content:center}.img img{max-width:100%;max-height:200mm;border:1px solid #ddd;border-radius:6px}'+
      '.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.chip{display:inline-flex;align-items:center;gap:6px;border:1.5px solid #888;border-radius:8px;padding:6px 12px;font-size:20px;font-weight:700}'+
      '.chip i{width:16px;height:16px;border-radius:3px;border:1px solid rgba(0,0,0,.4);display:inline-block}.chip small{font-weight:400;font-size:12px;color:#555}'+
      'table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:4px 8px;text-align:left;font-size:13px}.sw{width:14px;height:14px;display:inline-block;border:1px solid #888;border-radius:2px;vertical-align:-2px;margin-right:6px}'+
      '.bar{position:sticky;top:0;background:#111;color:#fff;padding:8px 14px;font-size:13px}@media print{.bar{display:none}}';
    var h='<!doctype html><meta charset="utf-8"><title>'+esc(j.name||'Building manual')+' — building manual</title><style>'+css+'</style>'+
      '<div class="bar">Print this page (Ctrl/Cmd+P) and choose “Save as PDF”.</div>'+
      '<div class="pg"><div style="margin:auto 0"><div class="mut">Building manual</div><h1>'+esc(j.name||'Custom build')+'</h1>'+
      '<p class="mut">“'+esc(j.prompt||'')+'”</p><p><b>'+total+'</b> bricks · <b>'+steps.length+'</b> steps · '+list.length+' distinct part/colour lines</p>'+
      '<p class="mut">Checked in the browser: no collisions, every part anchored to the baseplate, stud connections engaged, centre of mass over the footprint.</p></div>'+
      '<div class="img">'+(steps.length?'<img src="'+steps[steps.length-1].img+'" alt="finished build">':'')+'</div></div>';
    steps.forEach(function(st,i){
      h+='<div class="pg"><div class="step">'+(i+1)+'</div><div class="img"><img src="'+st.img+'" alt="step '+(i+1)+'"></div><div class="chips">'+
        st.chips.map(function(c){return '<span class="chip"><i style="background:'+(HEX[c.col]||'#c91a09')+'"></i>'+c.n+'× <small>'+esc(c.id)+' '+esc(pname(c.id))+'</small></span>'}).join('')+'</div></div>'});
    h+='<div class="pg"><h2>Parts list</h2><table><tr><th>Qty</th><th>Part</th><th>Description</th><th>Colour</th></tr>'+
      list.map(function(r){return '<tr><td>'+r.n+'</td><td>'+esc(r.id)+'</td><td>'+esc(pname(r.id))+'</td><td><span class="sw" style="background:'+(HEX[r.col]||'#c91a09')+'"></span>'+esc(CNAME[r.col]||r.col)+'</td></tr>'}).join('')+
      '</table><p class="mut" style="margin-top:14px;font-size:12px">Part geometry from the LDraw parts library (CC BY 4.0), part numbers per Rebrickable. Fan-made instructions, not affiliated with or endorsed by the LEGO Group. LEGO is a trademark of the LEGO Group.</p></div>';
    win.document.open();win.document.write(h);win.document.close();
    btn.disabled=false;$('mstat').textContent='Manual opened ('+steps.length+' steps).'})
  .catch(function(){btn.disabled=false;$('mstat').textContent='Could not build the manual.'})};
// ---- Catalogue browser: search every baked part (public/parts/index.json, real LDraw geometry) or minifigure
// character (baked by scripts/ldraw/characters.py as single parts mf-<id>, listed with {name, tags}) and add one
// beside the build client-side -- no server round trip, same pattern proven for characters before this was
// generalised. A character stands on a 1x2 stud pair: its origin is the neck, feet 72 LDU below, and its sockets
// at local x=+-10, z=0 land on the baseplate grid when x is a multiple of 20 and z is 10 mod 20 -- that placement
// stays hardcoded (every character shares the same rig). A general part has no such convention, so it's floored
// onto y=0 using its own baked bounds (index.json bounds are in quantised units -- divide by QUANT for real LDU).
function isChar(id){return /^mf-/.test(id)}
function footprint(id){
  var b=PIDX[id]&&PIDX[id].bounds;
  if(!b)return {w:20,yOff:0};
  return {w:Math.max(b.max[0]-b.min[0],b.max[2]-b.min[2])/QUANT,yOff:-b.min[1]/QUANT}}
function catalogHits(words){
  return Object.keys(PIDX).filter(function(k){
    var e=PIDX[k];
    if(!e.character&&/^[~=]/.test(e.title))return false;  // obsolete/"moved to"/stub entries -- never real picks
    var hay=(k+' '+e.title+(e.character?(' '+e.character.name+' '+e.character.tags.join(' ')):'')).toLowerCase();
    return words.every(function(w){return hay.indexOf(w)>=0})})}
function csearch(){
  var box=$('cres');box.innerHTML='';
  if(!PIDX){$('cnote').textContent='Loading catalogue…';return}
  var words=$('csearch').value.toLowerCase().split(/\s+/).filter(Boolean);
  if(!words.length){$('cnote').textContent='Type to search '+Object.keys(PIDX).length+' parts and minifigures.';return}
  var hits=catalogHits(words),shown=hits.slice(0,40);
  $('cnote').textContent=hits.length?(hits.length+' match'+(hits.length===1?'':'es')+(hits.length>40?' (showing 40)':'')):'No matches.';
  shown.forEach(function(id){var b=document.createElement('button');b.type='button';b.className='chip';
    b.title=id+' — '+pname(id);b.textContent=PIDX[id].character?PIDX[id].character.name:(id+' '+pname(id));
    b.onclick=function(){addPart(id)};box.appendChild(b)})}
function addPart(id){
  if(!last)last={j:{name:pname(id),prompt:''},partsModel:[],parts:[],staged:0};
  if(last.staged===undefined)last.staged=0;
  if(last.trayX===undefined){
    var built=last.parts.slice(0,last.parts.length-last.staged);
    var maxX=built.reduce(function(m,p){return Math.max(m,p.x)},-Infinity);
    // beside the build, first gap 80 LDU (4 studs): a stock brick reaches up to 40 LDU from its origin and a
    // figure's arms 31 LDU from its own (arms are cosmetic, not in the collision boxes), so the gap has to be real
    last.trayX=(isFinite(maxX)?maxX:0)+80}
  var fp=footprint(id),half=Math.max(fp.w/2,20),x=Math.ceil((last.trayX+half)/20)*20;
  var y=isChar(id)?-72:Math.round(fp.yOff),z=isChar(id)?10:0,col=isChar(id)?14:4;
  last.partsModel.push([id,x,y,z,0,col]);
  last.parts.push({p:id,x:x,y:y,z:z,r:0,c:HEX[col],edge:EDGE[col]});
  last.staged++;last.trayX=x+half+20;
  $('result').hidden=false;$('cclear').hidden=false;
  $('view').srcdoc=frameDoc(last.parts,true);
  $('cnote').textContent='Added '+pname(id)+(isChar(id)?'. Minifigures appear in the build manual; the Rebrickable CSV lists bricks only.':'.')}
$('csearch').addEventListener('input',csearch);
$('cclear').onclick=function(){if(!last||!last.staged)return;
  var n=last.staged;
  last.partsModel=last.partsModel.slice(0,-n);last.parts=last.parts.slice(0,-n);
  last.staged=0;last.trayX=undefined;
  $('cclear').hidden=true;$('cnote').textContent='';
  if(last.parts.length)$('view').srcdoc=frameDoc(last.parts,true);else $('result').hidden=true};
// ---- Real set import: GET /api/brick-omr?set=<id> parses the actual LDraw OMR model file for that set (real
// parts, positions, rotations, colours and build steps) and normalises it -- see mcp-worker/src/omr-import.js.
// Coverage is never hidden: a set with parts this catalogue can't yet render or that sit at a tilted (non-axis-
// aligned) angle is reported honestly, not silently dropped without comment.
function importSet(id,note){
  note=note||$('omrnote');
  if(!id){note.textContent='Enter a set number first.';return}
  $('omrset').value=id;
  note.textContent='';$('omrgo').disabled=true;$('omrgo').textContent='Importing…';
  fetch('/api/brick-omr?set='+encodeURIComponent(id))
  .then(function(r){return r.json().catch(function(){return {ok:false,error:'unexpected response'}}).then(function(j){return {r:r,j:j}})})
  .then(function(x){
    var j=x.j;
    if(!j.ok){note.textContent=j.error||'Could not import that set.';return}
    var c=j.coverage||{};
    $('result').hidden=false;$('cclear').hidden=true;$('cnote').textContent='';
    $('stats').innerHTML='';
    [['Set',j.set],['Total parts',n(c.parts)],['Renderable',n(c.renderable)],
     ['Not yet baked',n(c.parts-c.baked)],['Tilted (skipped)',n(c.tilted)]]
    .forEach(function(s){var d=document.createElement('div');d.className='stat';
      var b=document.createElement('b');b.textContent=s[1];var sp=document.createElement('span');sp.textContent=s[0];d.appendChild(b);d.appendChild(sp);$('stats').appendChild(d)});
    var pct=c.parts?Math.round(100*c.renderable/c.parts):0;
    $('how').textContent=(j.layout==='tray'
      ?('This set has no model in the LDraw Official Model Repository, so this is its real Rebrickable parts list laid out as a browsable tray, NOT an assembled recreation: '
        +n(c.renderable)+' of '+n(c.parts)+' real parts ('+pct+'%) are in this catalogue and shown. ')
      :('Imported from the LDraw Official Model Repository: '+n(c.renderable)+' of '+n(c.parts)+' parts ('+pct+'%) could be rendered -- '
        +'the rest are either not yet in this catalogue or sit at an angle this importer does not yet place. '))
      +(j.truncated?('Showing '+n(j.shown)+' of '+n(j.total)+' real instances (capped for a readable tray). '):'')
      +j.attribution;
    last={j:{name:j.name,prompt:''},partsModel:j.partsModel,parts:(function(){return (j.partsModel||[]).filter(function(p){return Array.isArray(p)&&/^[0-9a-z-]{1,24}$/.test(p[0])}).map(function(p){var c=p[5]|0;return {p:p[0],x:+p[1]||0,y:+p[2]||0,z:+p[3]||0,r:p[4]|0,c:HEX[c]||'#c91a09',edge:EDGE[c]||'#333333'}})})()};
    show({partsModel:j.partsModel});
    note.textContent='Imported '+j.name+'.'})
  .catch(function(){note.textContent='Could not reach the import service.'})
  .then(function(){$('omrgo').disabled=false;$('omrgo').textContent='Import set'})}
$('omrgo').onclick=function(){importSet($('omrset').value.trim(),$('omrnote'))};
// ---- Set gallery: GET /set_gallery.json, a static manifest built by scripts/ldraw/gen_set_gallery.py from a
// real real_set_coverage.py run (live OMR-vs-catalogue diff) + real Rebrickable titles/images. Ranked by honest
// coverage %, not gated behind a single pass/fail line -- the gradient is the point. Clicking a card reuses
// importSet() exactly like a hand-typed set number or a search-result chip; this panel is just a curated,
// pre-scored starting point, not a separate import path.
fetch('/bricksdemo/set_gallery.json').then(function(r){return r.json()}).then(function(j){
  var sets=j.sets||[];
  var box=$('gallery');box.innerHTML='';
  sets.forEach(function(s){
    var b=document.createElement('button');b.type='button';b.className='gcard';
    b.title=s.set+' -- '+n(s.instances)+' piece instances';
    var img=s.img_url?'<img src="'+esc(s.img_url)+'" alt="" loading="lazy">':'';
    var pctClass=s.coverage_pct>=90?'hi':'';
    b.innerHTML=img+'<div class="gc-body"><div class="gc-title">'+esc(s.title)+'</div>'
      +'<div class="gc-pct '+pctClass+'">'+s.coverage_pct+'% renderable</div></div>';
    b.onclick=function(){$('gallerynote').textContent='Importing '+s.title+'…';importSet(s.set,$('gallerynote'))};
    box.appendChild(b)});
  $('gallerynote').textContent=sets.length?
    (n(sets.length)+' real sets, ranked by honest catalogue coverage as of '+(j.generatedAt||'').slice(0,10)+' (50%+ shown; hundreds more fall below that line today).'):
    'No sets currently clear the coverage floor.';
}).catch(function(){$('gallerynote').textContent='Could not load the set gallery.'});
// ---- Set search: GET /api/data/rebrickable_set_search?query=<name> (declared in atoms/data-sources.yaml, real
// Rebrickable set data -- NOT every result has a matching OMR file; importSet() reports that honestly per-click,
// same as a hand-typed set number, rather than pre-filtering results against the OMR library on every keystroke.
var setSearchSeq=0,setSearchTimer=null;
function setSearch(){
  clearTimeout(setSearchTimer);
  var q=$('setsearch').value.trim();
  if(!q){$('setres').innerHTML='';$('setnote').textContent='';return}
  setSearchTimer=setTimeout(function(){
    var seq=++setSearchSeq;
    $('setnote').textContent='Searching…';
    fetch('/api/data/rebrickable_set_search?query='+encodeURIComponent(q))
    .then(function(r){return r.json()})
    .then(function(j){
      if(seq!==setSearchSeq)return;   // a later keystroke's request already landed
      var box=$('setres');box.innerHTML='';
      var all=Array.isArray(j&&j.results)?j.results:[];
      // Rebrickable's set search also returns books/magazines with a LEGO tie-in, catalogued under an ISBN
      // (e.g. "9788828795346-1") instead of a real LEGO set number -- these can never have an OMR file, and
      // importSet() would only report a confusing "set must look like a LEGO set number" instead of the honest
      // "not available" message a real-but-unbaked set gets. SET_RE below mirrors the server's own omr-import.js
      // shape check (2-7 digits, optional -N) so only genuinely buildable-looking sets are offered as chips.
      var SET_RE=/^[0-9]{2,7}(-[0-9]{1,3})?$/;
      var hits=all.filter(function(s){return SET_RE.test(s.set_num)}),hidden=all.length-hits.length;
      $('setnote').textContent=hits.length?(hits.length+' set'+(hits.length===1?'':'s')+' -- click one to import'+(hidden?' ('+hidden+' book/magazine tie-in'+(hidden===1?'':'s')+' hidden)':'')):
        (hidden?'Only book/magazine tie-ins found for that search, no buildable sets.':'No sets found.');
      hits.forEach(function(s){var b=document.createElement('button');b.type='button';b.className='chip';
        b.title=s.set_num+(s.num_parts?' -- '+n(s.num_parts)+' parts':'');
        b.textContent=s.name+(s.year?' ('+s.year+')':'');
        b.onclick=function(){$('setnote').textContent='Importing '+s.name+'…';importSet(s.set_num,$('setnote'))};
        box.appendChild(b)})})
    .catch(function(){if(seq===setSearchSeq)$('setnote').textContent='Could not reach the set search.'})
  },350)}
$('setsearch').addEventListener('input',setSearch);
var runs=0;
function logHistory(eng,j,label,u){
  runs++;$('histp').hidden=false;
  var tr=document.createElement('tr');
  [runs,eng!=='template'?j.model:'Template',label,n(u.promptTokens),n(u.outputTokens),
   costText(j,eng),n(j.parts),(j.ms/1000).toFixed(1)+' s']
  .forEach(function(v){var td=document.createElement('td');td.textContent=v;tr.appendChild(td)});
  $('hist').tBodies[0].insertBefore(tr,$('hist').tBodies[0].firstChild);
}
function howText(eng,j){
  if(eng==='gemini')return 'Designed by '+j.model+' as a voxel grid'+(j.repaired&&j.repaired.dropped_cells?'; '+j.repaired.dropped_cells+' unanchored cells were dropped':'')+'.';
  if(eng==='sketch'){var r=j.repaired||{};var bits=[];
    if(r.dropped_shapes)bits.push(r.dropped_shapes+' unsupported shape'+(r.dropped_shapes===1?'':'s')+' were dropped');
    if(r.dropped_cells)bits.push(r.dropped_cells+' unanchored cell'+(r.dropped_cells===1?'':'s')+' were dropped');
    return 'Sketched by '+j.model+' as real stud/plate volumes, with carved openings'+(bits.length?'; '+bits.join('; '):'')+'.';}
  var c=j.choice||{};
  return 'Built directly from your picks ("'+c.archetype+'", size '+c.size+') -- no model call, zero tokens.';
}
$('go').onclick=function(){
  var body;
  if(MODE==='gemini'||MODE==='sketch'){
    var prompt=$('prompt').value.trim();
    if(!prompt){$('err').textContent='Describe a build first.';return}
    body={prompt:prompt,engine:MODE,model:$('model').value};
  } else {
    body={engine:'template',archetype:$('tArch').value,colour:$('tColour').value,size:$('tSize').value};
  }
  $('err').textContent='';$('go').disabled=true;$('go').textContent='Designing…';
  fetch('/api/brick-design',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  .then(function(r){return r.json().catch(function(){return {ok:false,error:'unexpected response'}})})
  .then(function(j){
    if(!j.ok){$('err').textContent=j.error||'Something went wrong.';return}
    var u=j.usage||{};
    $('result').hidden=false;$('cclear').hidden=true;
    $('stats').innerHTML='';
    [['Tokens in',n(u.promptTokens)],['Tokens out',n(u.outputTokens)],
     ['Cost',costText(j,MODE)],['Bricks',n(j.parts)],['Time',(j.ms/1000).toFixed(1)+' s']]
    .forEach(function(s){var d=document.createElement('div');d.className='stat';
      var b=document.createElement('b');b.textContent=s[1];var sp=document.createElement('span');sp.textContent=s[0];d.appendChild(b);d.appendChild(sp);$('stats').appendChild(d)});
    $('how').textContent=howText(MODE,j);
    last={j:j,partsModel:j.partsModel,parts:(function(){return (j.partsModel||[]).filter(function(p){return Array.isArray(p)&&/^[0-9a-z-]{1,24}$/.test(p[0])}).map(function(p){var c=p[5]|0;return {p:p[0],x:+p[1]||0,y:+p[2]||0,z:+p[3]||0,r:p[4]|0,c:HEX[c]||'#c91a09',edge:EDGE[c]||'#333333'}})})()};
    show(j);
    var label=MODE!=='template'?(body.prompt.length>34?body.prompt.slice(0,33)+'…':body.prompt):(body.archetype+'/'+body.colour+'/'+body.size);
    logHistory(MODE,j,label,u);
  })
  .catch(function(){$('err').textContent='Could not reach the design service.'})
  .then(function(){$('go').disabled=false;$('go').textContent='Design it'});
};
// ---- View in Three.js: renders the SAME real build (last.partsModel) through three.js instead of the live
// WebGL renderer, with real per-part material appearance (trans-clear/chrome/metal/pearlescent/rubber) from
// each part's real LDraw colour -- see /bricksdemo/ldraw_colours_full.json (the full ~322-colour table,
// generated by scripts/ldraw/gen_ldraw_colours_full.py from the real LDConfig.ldr; NOT the small HEX/EDGE
// picker palette above, which has no transparency/finish concept at all).
__THREEJS_VIEW_MATH__
var TJS=(function(){
  var colours=null, colourFetch=null, meshCache={}, mod=null, modFetch=null;
  var scene=null, camera=null, renderer=null, controls=null, group=null, loopStarted=false;

  function fetchColours(){
    if(colours)return Promise.resolve(colours);
    if(!colourFetch)colourFetch=fetch('/bricksdemo/ldraw_colours_full.json').then(function(r){return r.json()}).then(function(j){colours=j;return j});
    return colourFetch;
  }
  function fetchMesh(id){
    if(meshCache[id])return meshCache[id];
    meshCache[id]=fetch('/parts/'+id+'.json').then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json()});
    return meshCache[id];
  }
  function loadThree(){
    if(mod)return Promise.resolve(mod);
    if(!modFetch)modFetch=Promise.all([
      import('three'),
      import('three/addons/controls/OrbitControls.js'),
      import('three/addons/environments/RoomEnvironment.js'),
    ]).then(function(r){mod={THREE:r[0],OrbitControls:r[1].OrbitControls,RoomEnvironment:r[2].RoomEnvironment};return mod});
    return modFetch;
  }
  // Builds one {geo, colourKey} pair PER triangle group, not one merged geometry for the whole part -- a
  // part's own mesh JSON can carry multiple groups with different colours (printed faces, stickers: a fixed
  // '#rrggbb' already resolved by resolve.py's ColourTable, not the LDraw code 'main' every plain group
  // uses), and merging them into one geometry would force the WHOLE part to the instance's colour, painting
  // over any printed detail. colourKey is null for a 'main' group (tint to the instance's real colour) or
  // the group's own fixed hex string (print colour, independent of the instance).
  function geometriesFor(THREE,part,r,instPos){
    var q=part.quant||1,out=[];
    part.triangles.forEach(function(g){
      if(g.colour==='edge')return;   // edge-line colour groups carry no fill triangles worth rendering here
      var positions=[],verts=g.pos;
      for(var i=0;i+2<verts.length;i+=3){
        // handedness flips under tjsToWorld's Y-negate, same fix as the standalone demo: swap the last two
        // vertices per triangle to keep outward-facing winding (confirmed visually, see threejs-demo).
        var a=tjsToWorld(verts[i],q,r,instPos),b=tjsToWorld(verts[i+1],q,r,instPos),c=tjsToWorld(verts[i+2],q,r,instPos);
        positions.push(a[0],a[1],a[2],c[0],c[1],c[2],b[0],b[1],b[2]);
      }
      if(!positions.length)return;
      var geo=new THREE.BufferGeometry();
      geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
      geo.computeVertexNormals();
      out.push({geo:geo,colourKey:g.colour==='main'?null:g.colour});
    });
    return out;
  }
  var matCache={};
  function materialForCode(THREE,code,colourTable){
    if(matCache[code])return matCache[code];
    var info=colourTable[code],hex=parseInt(((info&&info.hex)||'#c91a09').slice(1),16),m;
    if(!info){m=new THREE.MeshStandardMaterial({color:hex,roughness:0.85,metalness:0.05})}
    else if(info.finish==='chrome')m=new THREE.MeshPhysicalMaterial({color:hex,metalness:1,roughness:0.08,clearcoat:1,clearcoatRoughness:0.05});
    else if(info.finish==='metal')m=new THREE.MeshStandardMaterial({color:hex,metalness:0.9,roughness:0.25});
    else if(info.finish==='pearlescent')m=new THREE.MeshPhysicalMaterial({color:hex,metalness:0.35,roughness:0.22,clearcoat:0.6,clearcoatRoughness:0.2});
    // Real transmission (refraction), not flat opacity blending: a genuinely colourless material (Trans_
    // Clear, hex #fcfcfc) at ~50% flat alpha nearly vanishes against a light background -- physically
    // accurate (real clear glass does the same against a white backdrop) but not a useful "this is glass"
    // cue on its own. Transmission gives it visible depth/distortion that reads as transparent regardless
    // of background colour, since the viewer's cue is refraction, not contrast against whatever's behind
    // it. ior=1.5 matches typical clear plastic/glass; thickness is in world (stud) units, matching a real
    // part's own real scale, not an arbitrary constant.
    else if(info.alpha<255)m=new THREE.MeshPhysicalMaterial({color:hex,transmission:1,opacity:1,roughness:0.04,
      metalness:0,ior:1.5,thickness:0.6,clearcoat:1,clearcoatRoughness:0.05});
    else m=new THREE.MeshStandardMaterial({color:hex,roughness:0.85,metalness:0.05});
    matCache[code]=m;
    return m;
  }
  // Fixed print/sticker colours (an already-resolved '#rrggbb' from the part's own mesh JSON, independent
  // of the instance colour) get a simple opaque matte finish -- LDraw doesn't carry finish/alpha metadata
  // for these baked-in colours the way it does for real numbered colour codes, so matte is the honest
  // default rather than guessing a finish for them.
  function materialForFixedHex(THREE,hexStr){
    var key='#'+hexStr;
    if(matCache[key])return matCache[key];
    var m=new THREE.MeshStandardMaterial({color:parseInt(hexStr.replace('#',''),16),roughness:0.85,metalness:0.05});
    matCache[key]=m;
    return m;
  }
  function ensureScene(THREE,OrbitControls,RoomEnvironment){
    if(scene)return;
    var canvas=$('tjscanvas');
    // No scene.background / opaque clear: the canvas's own CSS background (the same light radial gradient
    // the main WebGL view already uses, #fafbfd -> #cdd6e0) shows through a transparent WebGL clear instead
    // -- keeps the two views visually consistent rather than a jarring dark-vs-light switch on toggle.
    scene=new THREE.Scene();
    camera=new THREE.PerspectiveCamera(45,1,0.1,800);
    renderer=new THREE.WebGLRenderer({canvas:canvas,antialias:true,alpha:true});
    renderer.setClearAlpha(0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
    renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
    renderer.outputColorSpace=THREE.SRGBColorSpace;
    // scene.environment (distinct from scene.background above): a real, procedural studio-lighting map
    // (RoomEnvironment -> PMREMGenerator, no external HDRI asset) so chrome/metal/pearlescent materials get
    // REAL reflections and trans-clear parts get real refraction, instead of flat colour with no surroundings
    // to reflect. Every MeshStandardMaterial/MeshPhysicalMaterial in the scene picks this up automatically
    // (three.js's own default behaviour) -- materialForCode/materialForFixedHex don't need to reference it.
    var pmrem=new THREE.PMREMGenerator(renderer);
    scene.environment=pmrem.fromScene(new RoomEnvironment(),0.04).texture;
    pmrem.dispose();
    controls=new OrbitControls(camera,renderer.domElement);
    controls.enableDamping=true;
    scene.add(new THREE.AmbientLight(0xffffff,0.55));
    var key=new THREE.DirectionalLight(0xffffff,1.4);key.position.set(25,40,20);scene.add(key);
    var fill=new THREE.DirectionalLight(0xbcd2ff,0.4);fill.position.set(-20,10,-15);scene.add(fill);
    var floor=new THREE.Mesh(new THREE.PlaneGeometry(300,300),new THREE.MeshStandardMaterial({color:0xd8dee4,roughness:1,metalness:0}));
    floor.rotation.x=-Math.PI/2;scene.add(floor);
    group=new THREE.Group();scene.add(group);
    function resize(){
      var w=canvas.clientWidth||canvas.parentElement.clientWidth,h=canvas.clientHeight||480;
      renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
    }
    window.addEventListener('resize',resize);resize();
    if(!loopStarted){loopStarted=true;(function loop(){requestAnimationFrame(loop);controls.update();renderer.render(scene,camera)})()}
  }
  function clearGroup(THREE){
    while(group.children.length){
      var m=group.children.pop();
      if(m.geometry)m.geometry.dispose();
      group.remove(m);
    }
  }
  // Frames the camera on whatever was actually loaded, via the shared tjsFitCamera() (see
  // threejs_view_math.js -- the pure corner-projection math is tested directly there, not re-derived here).
  function fitCamera(THREE){
    var box=new THREE.Box3().setFromObject(group);
    if(box.isEmpty())return;
    var fit=tjsFitCamera([box.min.x,box.min.y,box.min.z],[box.max.x,box.max.y,box.max.z],
                          [0.6,0.5,0.6],camera.fov,camera.aspect,1.15);
    camera.position.set(fit.position[0],fit.position[1],fit.position[2]);
    camera.near=fit.near;camera.far=fit.far;camera.updateProjectionMatrix();
    controls.target.set(fit.target[0],fit.target[1],fit.target[2]);controls.update();
  }
  // partEntries: one entry per partsModel ROW (not per mesh -- a decorated part's multiple colour-group
  // meshes must move together), {meshes:[...], step}. Shared by both the Phase 1 scrubber and Phase 2
  // animate loop below.
  var partEntries=[];
  // Build-step scrubber (Phase 1 of the "View in Three.js" motion work) -- a static cumulative reveal via
  // partsModel's own real `step` field (row[6], already present in every real build). All meshes are built
  // and added to `group` once (so fitCamera sees the FULL final build and the camera never jumps as you
  // scrub); the scrubber only ever toggles mesh.visible, never rebuilds geometry.
  function applyStep(step){
    partEntries.forEach(function(e){e.meshes.forEach(function(m){m.visible=e.step<=step;});});
  }
  // Phase 2: the live canvas renderer's continuous drop/bounce/settle/hold/lift-out "Animate" loop, ported
  // from atoms_brick.gs's status(t) (constants FALL/SETTLE/HOLD/LIFT/DROP and the stagger/dst timing are
  // copied from there verbatim -- this is the same real motion, not a reinvented one). Runs per-frame on
  // partEntries (not partsModel directly), reusing the exact meshes the scrubber already built.
  //
  // Materials are cached/shared by colour (materialForCode/materialForFixedHex) so many parts of the same
  // colour reuse ONE material object -- mutating .opacity per frame would then wrongly fade every part of
  // that colour together, not just the one currently animating. Each mesh gets its OWN cloned material for
  // the duration of animate mode (restored to the shared cache instance on stop, so scrubbing/static view
  // stay cheap and unaffected).
  var animRAF=null,animLastT=0,animT=0,animPlaying=false;
  function stopAnimate(){
    animPlaying=false;
    if(animRAF)cancelAnimationFrame(animRAF);
    animRAF=null;
    partEntries.forEach(function(e){e.meshes.forEach(function(m){
      m.position.set(0,0,0);
      if(m.userData.sharedMaterial){m.material=m.userData.sharedMaterial;delete m.userData.sharedMaterial;}
    });});
  }
  function startAnimate(){
    var N=partEntries.length;
    if(!N)return;
    var FALL=0.55,SETTLE=0.45,HOLD=3,LIFT=0.7,DROP=7;
    var stagger=Math.min(0.12,5/N),dst=1.4/N;
    var tBuild=N*stagger+FALL+SETTLE;
    var tCycle=tBuild+HOLD+N*dst+LIFT+0.5;
    partEntries.forEach(function(e,i){
      e.t0=i*stagger;e.td=tBuild+HOLD+(N-1-i)*dst;
      e.jx=(Math.random()-0.5)*7;e.jz=(Math.random()-0.5)*7;
      e.meshes.forEach(function(m){
        m.userData.sharedMaterial=m.material;
        m.material=m.material.clone();
        m.material.transparent=true;   // opacity now animates every frame regardless of the base material's own mode
      });
    });
    var reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    animT=reduced?tBuild+1:tBuild*0.7;
    animLastT=performance.now();
    animPlaying=true;
    (function frame(now){
      if(!animPlaying)return;
      var dt=Math.min(0.05,(now-animLastT)/1000);animLastT=now;
      if(!reduced){animT+=dt;if(animT>=tCycle)animT-=tCycle;}
      partEntries.forEach(function(e){
        var tf=animT-e.t0,td=animT-e.td,s,ox=0,oy=0,oz=0,a=1;
        if(td>=0){var q=td/LIFT;if(q>=1){s=-1;}else{s=1;oy=DROP*q*q;a=1-q;}}
        else if(tf<0)s=-1;
        else if(tf<FALL){var p=tf/FALL,ee=1-p;s=1;oy=DROP*(1-p*p);ox=e.jx*ee*ee;oz=e.jz*ee*ee;a=Math.min(1,p*5);}
        else{var tb=tf-FALL;if(tb<SETTLE){s=1;oy=0.22*Math.exp(-9*tb)*Math.abs(Math.sin(15*tb));}else s=0;}
        e.meshes.forEach(function(m){
          m.visible=(s!==-1);
          m.position.set(ox,oy,oz);
          m.material.opacity=a;
        });
      });
      animRAF=requestAnimationFrame(frame);
    })(animLastT);
  }
  function render(partsModel){
    var status=$('tjsstatus');
    stopAnimate();
    status.textContent='Loading three.js…';
    loadThree().then(function(mm){
      status.textContent='Loading real colour data…';
      return fetchColours().then(function(ct){return {mm:mm,ct:ct}});
    }).then(function(x){
      var THREE=x.mm.THREE,ct=x.ct;
      ensureScene(THREE,x.mm.OrbitControls,x.mm.RoomEnvironment);
      clearGroup(THREE);
      partEntries=[];
      status.textContent='Loading '+partsModel.length+' real part'+(partsModel.length===1?'':'s')+'…';
      var ids=Array.from(new Set(partsModel.map(function(row){return row[0]})));
      return Promise.all(ids.map(function(id){return fetchMesh(id).catch(function(){return null})})).then(function(meshes){
        var byId={};ids.forEach(function(id,i){byId[id]=meshes[i]});
        var ok=0,skipped=0,maxStep=1;
        partsModel.forEach(function(row){
          var mesh=byId[row[0]];
          if(!mesh){skipped++;return}
          var instPos=[row[1],row[2],row[3]],r=row[4]|0,code=row[5]|0,step=row[6]|0||1;
          maxStep=Math.max(maxStep,step);
          var entryMeshes=[];
          geometriesFor(THREE,mesh,r,instPos).forEach(function(g){
            var mat=g.colourKey?materialForFixedHex(THREE,g.colourKey):materialForCode(THREE,code,ct);
            var m=new THREE.Mesh(g.geo,mat);
            group.add(m);
            entryMeshes.push(m);
          });
          if(entryMeshes.length)partEntries.push({meshes:entryMeshes,step:step});
          ok++;
        });
        fitCamera(THREE);
        var slider=$('tjsstep'),playBtn=$('tjsplay');
        $('tjscontrols').hidden=false;
        if(maxStep>1){
          $('tjsstepwrap').style.display='flex';
          slider.min=1;slider.max=maxStep;slider.value=maxStep;
          $('tjsstepnote').textContent='step '+maxStep+' of '+maxStep;
          slider.oninput=function(){
            if(animPlaying)return;
            var v=parseInt(slider.value,10)||1;
            applyStep(v);
            $('tjsstepnote').textContent='step '+v+' of '+maxStep;
          };
        }else{
          $('tjsstepwrap').style.display='none';
          applyStep(1);
        }
        playBtn.setAttribute('aria-pressed','false');
        playBtn.textContent='Animate';
        playBtn.onclick=function(){
          if(animPlaying){
            stopAnimate();
            playBtn.setAttribute('aria-pressed','false');playBtn.textContent='Animate';
            slider.disabled=false;
            applyStep(parseInt(slider.value,10)||maxStep);
          }else{
            startAnimate();
            playBtn.setAttribute('aria-pressed','true');playBtn.textContent='Stop';
            slider.disabled=true;
          }
        };
        status.textContent=ok+' of '+partsModel.length+' real parts rendered'+(skipped?' ('+skipped+' not yet in the baked catalogue)':'')+
          ' — drag to orbit, scroll to zoom.';
      });
    }).catch(function(err){
      status.textContent='Could not load the three.js view ('+err.message+').';
    });
  }
  return {render:render};
})();
// The main WebGL view's own render loop already skips its expensive draw work when the canvas isn't
// intersecting the viewport (an IntersectionObserver-driven `visible` flag, see atoms_brick.gs's loop()) --
// but requestAnimationFrame itself keeps getting rescheduled every frame regardless (`if(!visible)return`
// is the SECOND line, not a guard around the reschedule), a real if small residual cost while the Three.js
// view is open. Clearing the iframe's srcdoc navigates it to an empty document, tearing down that JS
// context entirely (zero cost, not just skipped draws) -- rebuilt via the same show() used everywhere else
// when switching back, not a special-cased reconstruction.
$('tjsgo').onclick=function(){
  var showing=$('tjsgo').getAttribute('aria-pressed')==='true';
  if(showing){
    $('tjsgo').setAttribute('aria-pressed','false');
    $('tjswrap').hidden=true;$('view').hidden=false;
    // last.partsModel (not last.j.partsModel) -- last.j's own shape differs across the three places that
    // set `last` (design/template carries the full API response, but the "add real part" and "import set"
    // paths only carry {name,prompt} on .j); last.partsModel is the one field all three set consistently.
    if(last)show({partsModel:last.partsModel});
    return;
  }
  if(!last||!last.partsModel||!last.partsModel.length){
    $('tjsstatus').textContent='No real parts model for this build yet -- design or import one first.';
    $('tjswrap').hidden=false;$('view').hidden=true;
    $('tjsgo').setAttribute('aria-pressed','true');
    return;
  }
  $('tjsgo').setAttribute('aria-pressed','true');
  $('view').hidden=true;$('tjswrap').hidden=false;
  $('view').srcdoc='';
  TJS.render(last.partsModel);
};
setMode('gemini');upd();
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
    names = {c: CNAMES[c] for c in CODES}
    arch_opts = "".join(f'<option value="{k}">{label}</option>' for k, label in ARCHETYPES)
    colour_opts = "".join(f'<option value="{k}">{label}</option>' for k, label in TCOLOURS)
    size_opts = "".join(f'<option value="{k}"{" selected" if k == "medium" else ""}>{label}</option>' for k, label in TSIZES)
    return (PAGE.replace("__PRE__", esc(pre)).replace("__POST__", esc(post))
            .replace("__CNAME__", json.dumps(names)).replace("__HEX__", json.dumps(hexes)).replace("__EDGE__", json.dumps(edges))
            .replace("__ARCH_OPTS__", arch_opts).replace("__COLOUR_OPTS__", colour_opts).replace("__SIZE_OPTS__", size_opts)
            .replace("__THREEJS_VIEW_MATH__", THREEJS_VIEW_MATH))


def main(out=OUT):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
