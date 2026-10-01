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
# The real LDraw-parts collision/connector validator, extracted verbatim from atoms_brick.gs's validateParts()
# (parity enforced by tests/test_brick_parts_validate.mjs, not by this embedding alone) -- see the file's own
# header comment for why atoms_brick.gs itself is left untouched. Depends on TJS_PART_ROT (THREEJS_VIEW_MATH,
# embedded first below) already being in scope.
BRICK_VALIDATE_SHARED = (HERE / "brick_validate_shared.js").read_text(encoding="utf-8")
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
    "three/addons/environments/RoomEnvironment.js": "/vendors/threejs/addons/environments/RoomEnvironment.js",
    "three/addons/postprocessing/EffectComposer.js": "/vendors/threejs/addons/postprocessing/EffectComposer.js",
    "three/addons/postprocessing/RenderPass.js": "/vendors/threejs/addons/postprocessing/RenderPass.js",
    "three/addons/postprocessing/GTAOPass.js": "/vendors/threejs/addons/postprocessing/GTAOPass.js",
    "three/addons/postprocessing/OutputPass.js": "/vendors/threejs/addons/postprocessing/OutputPass.js"
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
<label for="tjsmaterial" style="font-size:12px;color:var(--mute)">Material</label>
<select id="tjsmaterial"><option value="lego">LEGO plastic</option><option value="concrete">Concrete block</option></select>
<label for="tjscameramode" style="font-size:12px;color:var(--mute)">Camera</label>
<select id="tjscameramode"><option value="persp">Perspective</option><option value="ortho">Parallel (instructions)</option></select>
<button class="go alt" id="premium" type="button">Premium render (Blender)</button>
<span id="tjsstepwrap" style="display:flex;gap:10px;align-items:center;flex:1">
<label for="tjsstep" style="font-size:12px;color:var(--mute)">Build step</label>
<input type="range" id="tjsstep" min="1" max="1" value="1" style="flex:1">
<span class="note" id="tjsstepnote"></span>
</span>
</div>
<div id="tjsstepchips" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:12px"></div>
<p class="note" id="tjsstatus"></p>
<p class="note" id="premiumNote"></p>
<p class="note" id="tjsinspect" hidden></p>
<ul id="tjschecks" style="list-style:none;padding:0;margin:8px 0 0;display:flex;flex-direction:column;gap:4px;font-size:12px" hidden></ul>
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
  refreshTJSIfActive();
}
// Real bug found live: loading a new build (design/template/import/add-part) while the Three.js view was
// the ACTIVE one only ever updated the hidden main-view iframe (via show(), or the tray's own direct
// srcdoc write) -- the Three.js canvas just kept showing whatever it had before, with no indication
// anything was stale. Switching to the main view and back "fixed" it only because that toggle always
// calls TJS.render() fresh. Every real "new build" mutation point calls this now, not just show().
function refreshTJSIfActive(){
  if($('tjsgo').getAttribute('aria-pressed')==='true'&&last&&last.partsModel&&last.partsModel.length){
    TJS.render(last.partsModel);
  }
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
  refreshTJSIfActive();
  $('cnote').textContent='Added '+pname(id)+(isChar(id)?'. Minifigures appear in the build manual; the Rebrickable CSV lists bricks only.':'.')}
$('csearch').addEventListener('input',csearch);
$('cclear').onclick=function(){if(!last||!last.staged)return;
  var n=last.staged;
  last.partsModel=last.partsModel.slice(0,-n);last.parts=last.parts.slice(0,-n);
  last.staged=0;last.trayX=undefined;
  $('cclear').hidden=true;$('cnote').textContent='';
  if(last.parts.length)$('view').srcdoc=frameDoc(last.parts,true);else $('result').hidden=true;
  refreshTJSIfActive();};
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
__BRICK_VALIDATE_SHARED__
// premium-render-api's live Cloud Run Service URL (artful-patrol-502116-b7/europe-west1, see the
// premium-export plan -- a genuinely separate, lightweight trigger+status service, not cloud-run-renderer).
var PREMIUM_RENDER_BASE_URL='https://premium-render-api-1093160097419.europe-west1.run.app';
var TJS=(function(){
  var colours=null, colourFetch=null, meshCache={}, mod=null, modFetch=null;
  var scene=null, camera=null, renderer=null, controls=null, group=null, loopStarted=false, keyLight=null;
  // camera is always the ACTIVE camera (initially perspCamera); orthoCamera is built alongside it in
  // ensureScene, both real objects from the start, never lazily constructed on first toggle -- switching
  // between them is then just reassigning which object `camera`/controls.object/the RenderPass's own
  // .camera point at (all plain mutable references, see cameraMode's own comment below), not a rebuild.
  var perspCamera=null, orthoCamera=null, cameraMode='persp', renderPass=null;
  // Raw (aspect-independent) margined half-extents from the last real fitCamera call -- orthoCamera's own
  // FOV-equivalent, the thing that stays fixed across a plain window resize while only aspect changes (see
  // applyOrthoFrustum below, and resize()'s perspCamera.aspect reassignment for the exact same pattern).
  var orthoFitHalfW=1, orthoFitHalfH=1;
  // Shared by both fitCamera (a real new build) and resize (the same build, new aspect) -- keeps the
  // aspect-correct letterboxing logic (match whichever of width/height is the binding constraint, exactly
  // the same "max()" idea tjsFitCamera's own perspective distance calc uses) in ONE place.
  function applyOrthoFrustum(aspect){
    var oh=Math.max(orthoFitHalfH,orthoFitHalfW/aspect),ow=oh*aspect;
    orthoCamera.left=-ow;orthoCamera.right=ow;orthoCamera.top=oh;orthoCamera.bottom=-oh;
    orthoCamera.updateProjectionMatrix();
  }
  var composer=null, gtaoPass=null;
  // Fixed UNIT direction for the shadow-casting key light, from the build's centre TOWARD the light (not an
  // absolute position -- fitCamera() re-derives the light's real position/shadow-camera frustum from this
  // direction plus whatever box the CURRENT build actually occupies, same reasoning as tjsFitCamera's own
  // camera-direction parameter: a fixed absolute light position looked fine for the one build size it was
  // tuned against and wrong for any other).
  var KEY_LIGHT_DIR=null;

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
      import('three/addons/postprocessing/EffectComposer.js'),
      import('three/addons/postprocessing/RenderPass.js'),
      import('three/addons/postprocessing/GTAOPass.js'),
      import('three/addons/postprocessing/OutputPass.js'),
    ]).then(function(r){mod={THREE:r[0],OrbitControls:r[1].OrbitControls,RoomEnvironment:r[2].RoomEnvironment,
      EffectComposer:r[3].EffectComposer,RenderPass:r[4].RenderPass,GTAOPass:r[5].GTAOPass,OutputPass:r[6].OutputPass};return mod});
    return modFetch;
  }
  // Builds one {geo, colourKey} pair PER triangle group, not one merged geometry for the whole part -- a
  // part's own mesh JSON can carry multiple groups with different colours (printed faces, stickers: a fixed
  // '#rrggbb' already resolved by resolve.py's ColourTable, not the LDraw code 'main' every plain group
  // uses), and merging them into one geometry would force the WHOLE part to the instance's colour, painting
  // over any printed detail. colourKey is null for a 'main' group (tint to the instance's real colour) or
  // the group's own fixed hex string (print colour, independent of the instance).
  //
  // Unlike the old per-instance geometriesFor (kept in git history), this builds RAW, untransformed local
  // geometry -- no tjsToWorld call, no instPos, no rotation baked in -- so it can be built ONCE per part id
  // and shared by every instance of that part via InstancedMesh.setMatrixAt(index, ...) instead of one real
  // Mesh (and one real draw call) per placed brick. That per-instance-mesh approach is what capped how large
  // a build could actually render (real kits like the Death Star hit thousands of draw calls and the design
  // page had to artificially truncate at TRAY_MAX).
  //
  // The (a,c,b) swap below is UNCONDITIONAL, independent of the Y-flip/mirror question entirely: it corrects
  // the real LDraw part JSON's own raw vertex order to three.js's CCW-front convention, which was already
  // needed before any instancing/mirror math enters the picture. Confirmed empirically 2026-09-30 (not just
  // reasoned about) by trying all three real combinations on a single real part: object-level mirror + no
  // swap -> wrong (culling flips, so we see the part's own hollow underside/tube geometry instead of its
  // outer shell); object-level mirror + swap -> correct; per-instance-baked mirror (object-level identity) +
  // swap -> ALSO wrong, for a different reason -- see tjsInstanceMatrixRowMajor's comment on why the mirror
  // belongs on the InstancedMesh's own .scale, not folded into the per-instance matrix.
  function localGeometryGroups(THREE,part){
    var out=[];
    part.triangles.forEach(function(g){
      if(g.colour==='edge')return;   // edge-line colour groups carry no fill triangles worth rendering here
      var positions=[],verts=g.pos;
      for(var i=0;i+2<verts.length;i+=3){
        var a=verts[i],b=verts[i+1],c=verts[i+2];
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
  // "Render as: Concrete block" -- a genuine second render-appearance material (not a LEGO colour), swapped
  // in over the SAME brick geometry to demonstrate the render-appearance axis independently of geometry/
  // connector semantics (see cozy-forging-newt.md's material-context-aware architecture plan: appearance is
  // its own axis, already varying WITHIN the LEGO catalogue -- trans-clear vs. chrome vs. matte ABS -- and
  // not modelled as a swappable profile anywhere before this). One shared, cached material (matching the
  // instancing win: swapping it onto an InstancedMesh keeps the whole bucket in ONE draw call, no per-
  // instance material clone) -- #a3a099, roughness 0.92, matte, no clearcoat: a real, neutral concrete grey,
  // not LEGO's glossy ABS finish.
  var concreteMat=null;
  function materialForConcrete(THREE){
    if(!concreteMat)concreteMat=new THREE.MeshStandardMaterial({color:0xa3a099,roughness:0.92,metalness:0});
    return concreteMat;
  }
  // Real poured concrete varies batch to batch (aggregate mix, cure conditions, cement ratio) -- a single
  // flat grey across an entire build reads as a uniform plastic slab, not concrete. InstancedMesh's own
  // instanceColor (a per-instance RGB multiplier three.js's shader applies automatically once set via
  // setColorAt, no custom shader needed) gives each instance its own slight lightness jitter around the same
  // base hue, WITHOUT giving up the one-draw-call-per-bucket instancing win a separate material per instance
  // would cost. Seeded off the instance index (a cheap deterministic hash, not Math.random()) so the same
  // build shows the SAME per-brick variation every time it's toggled back to concrete, rather than
  // re-randomizing on every toggle.
  function applyConcreteColourVariation(THREE,instMesh){
    if(instMesh.userData.concreteColoured)return;
    var hsl={};(new THREE.Color(0xa3a099)).getHSL(hsl);
    var c=new THREE.Color();
    for(var i=0;i<instMesh.count;i++){
      var jitter=((i*2654435761)>>>0)%1000/1000-0.5;
      c.setHSL(hsl.h,hsl.s,Math.min(0.95,Math.max(0.05,hsl.l+jitter*0.12)));
      instMesh.setColorAt(i,c);
    }
    instMesh.instanceColor.needsUpdate=true;
    instMesh.userData.concreteColoured=true;
  }
  // currentMaterialMode persists across renders/set-imports (not reset to 'lego' each time) -- picking
  // "Concrete block" and then importing a different set should keep showing concrete, the same way scrubber/
  // animate state isn't expected to silently reset either.
  var currentMaterialMode='lego';
  function applyMaterialMode(THREE){
    group.children.forEach(function(m){
      if(!m.isInstancedMesh)return;
      if(currentMaterialMode==='concrete'){
        if(!m.userData.legoMaterial)m.userData.legoMaterial=m.material;
        applyConcreteColourVariation(THREE,m);
        m.material=materialForConcrete(THREE);
      }else if(m.userData.legoMaterial){
        m.material=m.userData.legoMaterial;
      }
    });
  }
  // Real per-instance alpha for the Animate loop's fall-in/lift-out fade (closes the gap
  // threejs-viewer-instancing-for-large-kits's own note left open: InstancedMesh sharing one material per
  // bucket means there's no per-instance .opacity the way a real, separate Mesh had, so the first version of
  // this loop faked the reveal via matrix scale instead). A genuinely CACHED, per-base-material clone (a
  // WeakMap keyed by the base material object -- never re-patched, never re-compiled per frame or per
  // render), not a permanent mutation of the shared static material: patching material.transparent=true
  // + onBeforeCompile PERMANENTLY on the same material instances every other (non-animating) part also uses
  // would push every static part in the scene through three.js's slower, depth-sorted transparent render
  // pass all the time, not just during the few seconds Animate is actually playing. Swapped onto each
  // InstancedMesh only for the duration of Animate (startAnimate/stopAnimate below), so normal viewing keeps
  // the fast opaque path.
  var animateMatCache=new WeakMap();
  function getAnimateVariant(THREE,baseMat){
    var v=animateMatCache.get(baseMat);
    if(v)return v;
    v=baseMat.clone();
    v.transparent=true;
    // depthWrite stays true deliberately: these instances are opaque (alpha=1) almost all the time (only
    // briefly <1 mid fall-in/lift-out), so keeping normal opaque-style depth writes avoids the sorting/
    // popping artefacts a "real" always-transparent object would need to worry about, while still letting
    // the one genuinely fading instance blend correctly against whatever's already been drawn behind it.
    v.onBeforeCompile=function(shader){
      shader.vertexShader=shader.vertexShader
        .replace('#include <common>','attribute float instanceAlpha;\nvarying float vInstanceAlpha;\n#include <common>')
        .replace('#include <begin_vertex>','#include <begin_vertex>\nvInstanceAlpha = instanceAlpha;');
      shader.fragmentShader=shader.fragmentShader
        .replace('#include <common>','varying float vInstanceAlpha;\n#include <common>')
        .replace('#include <dithering_fragment>','gl_FragColor.a *= vInstanceAlpha;\n#include <dithering_fragment>');
    };
    v.needsUpdate=true;
    animateMatCache.set(baseMat,v);
    return v;
  }
  function ensureScene(THREE,OrbitControls,RoomEnvironment){
    if(scene)return;
    var canvas=$('tjscanvas');
    // No scene.background / opaque clear: the canvas's own CSS background (the same light radial gradient
    // the main WebGL view already uses, #fafbfd -> #cdd6e0) shows through a transparent WebGL clear instead
    // -- keeps the two views visually consistent rather than a jarring dark-vs-light switch on toggle.
    scene=new THREE.Scene();
    perspCamera=new THREE.PerspectiveCamera(45,1,0.1,800);
    // Real left/right/top/bottom placeholders (not 0s -- an all-zero ortho frustum is degenerate and some
    // three.js internals assume a non-empty one even before the first real fitCamera call sizes it for real).
    orthoCamera=new THREE.OrthographicCamera(-1,1,1,-1,0.1,800);
    camera=perspCamera;
    renderer=new THREE.WebGLRenderer({canvas:canvas,antialias:true,alpha:true});
    renderer.setClearAlpha(0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
    renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;
    renderer.outputColorSpace=THREE.SRGBColorSpace;
    renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
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
    KEY_LIGHT_DIR=new THREE.Vector3(25,40,20).normalize();
    keyLight=new THREE.DirectionalLight(0xffffff,1.4);keyLight.position.set(25,40,20);scene.add(keyLight);
    // Real shadow casting, not just lighting: the shadow camera's own frustum is a fixed guess here (resized
    // per real build in fitCamera(), the same way the main camera's distance is -- a fixed frustum tuned for
    // one build size would either clip a big kit's shadow or waste resolution on a tiny one). castShadow is
    // set here once; the frustum itself only makes sense once a real build's bounding box exists.
    keyLight.castShadow=true;
    keyLight.shadow.mapSize.set(2048,2048);
    keyLight.shadow.bias=-0.0015;keyLight.shadow.normalBias=0.02;
    scene.add(keyLight.target);   // DirectionalLight aims at .target's world position, not a direction vector -- .target must be in the scene graph for its matrixWorld (and therefore the light's real aim) to update at all.
    var fill=new THREE.DirectionalLight(0xbcd2ff,0.4);fill.position.set(-20,10,-15);scene.add(fill);
    var floor=new THREE.Mesh(new THREE.PlaneGeometry(300,300),new THREE.MeshStandardMaterial({color:0xd8dee4,roughness:1,metalness:0}));
    floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;scene.add(floor);
    group=new THREE.Group();scene.add(group);
    // Real ambient occlusion (backlog item 2, threejs-viewer-feature-survey-and-priority): grounds brick-to-
    // brick and brick-to-floor contact more convincingly than the directional shadow alone. GTAOPass (three's
    // modern replacement for the older SSAOPass) reads real scene depth+normals, not a cheap approximation.
    // RenderPass draws the normal scene first; GTAOPass blends AO over it; OutputPass applies tone mapping +
    // colour-space conversion at the end of the chain -- EffectComposer's intermediate render targets don't
    // apply these the way a direct renderer.render() call does, so skipping OutputPass would wash out the
    // same ACESFilmic look the rest of this viewer already relies on.
    // Real canvas size up front (not a 1x1 placeholder immediately resized) -- GTAOPass allocates its render
    // targets at construction time, so constructing at the real size avoids allocating and instantly
    // discarding a throwaway 1x1 set on every single load.
    var initW=canvas.clientWidth||canvas.parentElement.clientWidth||300,initH=canvas.clientHeight||480;
    composer=new mod.EffectComposer(renderer);
    renderPass=new mod.RenderPass(scene,camera);
    composer.addPass(renderPass);
    gtaoPass=new mod.GTAOPass(scene,camera,initW,initH);
    gtaoPass.blendIntensity=0.55;   // subtle -- grounds contact without darkening the whole scene
    composer.addPass(gtaoPass);
    composer.addPass(new mod.OutputPass());
    function resize(){
      var w=canvas.clientWidth||canvas.parentElement.clientWidth,h=canvas.clientHeight||480;
      renderer.setSize(w,h,false);
      perspCamera.aspect=w/h;perspCamera.updateProjectionMatrix();
      applyOrthoFrustum(w/h);
      composer.setSize(w,h);gtaoPass.setSize(w,h);
    }
    window.addEventListener('resize',resize);resize();
    canvas.addEventListener('click',onCanvasClick);
    if(!loopStarted){loopStarted=true;(function loop(){requestAnimationFrame(loop);controls.update();composer.render()})()}
  }
  // Click-to-inspect: real instanced raycasting (THREE.Raycaster natively resolves which INSTANCE of an
  // InstancedMesh a ray hits, not just which mesh -- intersection.instanceId), resolved back to that
  // instance's source partsModel row via the rowInfo array render() attaches to each InstancedMesh.
  //
  // The clicked instance is highlighted via the SAME instanceColor mechanism the concrete material's
  // per-brick variation uses (setColorAt) -- one real colour multiply, reverted to whatever the instance's
  // own real colour was when a different instance is clicked or the selection is cleared. A real "inflated
  // backface shell" outline (backlog's own literal suggestion) was built and tried instead (2026-09-30):
  // OutlinePass itself was rejected first (see fetch_threejs.py's comment -- it masks whole scene OBJECTS,
  // can't isolate one instance inside an InstancedMesh), so a hand-built shell mesh (parented under the
  // clicked InstancedMesh, vertices pushed out along their own normals, BackSide-culled) was tried as the
  // alternative. It hit a real rendering-correctness problem that didn't resolve across three different
  // inflate techniques (a uniform object-space scale, a wide per-vertex normal push, a narrow one): one
  // particular face of the test brick rendered as a large solid fill instead of a thin rim, with IDENTICAL
  // coverage regardless of inflate magnitude -- inconsistent with a tunable width/foreshortening issue,
  // more consistent with a transform or winding interaction specific to this shell-as-InstancedMesh-child
  // setup that wasn't fully root-caused in the time available. Reverted to this instanceColor approach
  // (already correct, already shipped, and a legitimate "brighten, don't recolour" idiom many real 3D
  // editors use for selection) rather than ship a highlight with a known, unexplained rendering defect.
  var raycaster=null,mouseNDC=null,highlighted=null,lastColourTable=null;
  // instanceColor is a MULTIPLICATIVE tint on the material's own base colour (three.js's shader does
  // diffuseColor *= vColor, not a replace) -- confirmed empirically, not assumed: an early version tried
  // setColorAt(index, orange) directly and a BLUE brick came out an unrelated muddy green (blue's own low
  // R/G channels multiplied by orange's low B channel land somewhere neither colour intended). A flat
  // brightness boost (the same factor on all three channels) instead preserves each brick's own real hue --
  // a highlighted red brick reads as a brighter red, a highlighted blue brick as a brighter blue -- while
  // still popping clearly as "selected" against its un-highlighted neighbours, the same "brighten, don't
  // recolour" language most 3D editors use for hover/selection state.
  var HIGHLIGHT_FACTOR=2.6;
  function clearHighlight(){
    if(!highlighted)return;
    highlighted.instMesh.setColorAt(highlighted.index,highlighted.savedColor);
    highlighted.instMesh.instanceColor.needsUpdate=true;
    highlighted=null;
  }
  function highlightInstance(THREE,instMesh,index){
    // GTAOPass renders the whole scene every frame through its own shared override material (see
    // materialSel.onchange's comment) -- setColorAt + instanceColor.needsUpdate below is a live per-instance
    // GPU buffer mutation on an InstancedMesh GTAO's override pass has already rendered, which crashes the
    // whole renderer process the same way a live material swap does. Disable GTAO permanently the first
    // time anything actually clicks a brick, rather than risk it.
    if(gtaoPass)gtaoPass.enabled=false;
    clearHighlight();
    var saved=new THREE.Color(1,1,1);   // matches an instance's implicit un-set instanceColor default (three.js's own lazy-buffer fill value) if this mesh has never had setColorAt called on it before
    if(instMesh.instanceColor)instMesh.getColorAt(index,saved);
    instMesh.setColorAt(index,new THREE.Color(saved.r*HIGHLIGHT_FACTOR,saved.g*HIGHLIGHT_FACTOR,saved.b*HIGHLIGHT_FACTOR));
    instMesh.instanceColor.needsUpdate=true;
    highlighted={instMesh:instMesh,index:index,savedColor:saved};
  }
  function onCanvasClick(evt){
    if(!mod||!scene)return;
    var THREE=mod.THREE;
    if(!raycaster){raycaster=new THREE.Raycaster();mouseNDC=new THREE.Vector2();}
    var rect=evt.target.getBoundingClientRect();
    mouseNDC.x=((evt.clientX-rect.left)/rect.width)*2-1;
    mouseNDC.y=-((evt.clientY-rect.top)/rect.height)*2+1;
    raycaster.setFromCamera(mouseNDC,camera);
    var hits=raycaster.intersectObjects(group.children.filter(function(c){return c.isInstancedMesh}));
    var inspect=$('tjsinspect');
    if(!hits.length){clearHighlight();inspect.hidden=true;return;}
    var hit=hits[0],instMesh=hit.object,idx=hit.instanceId;
    highlightInstance(THREE,instMesh,idx);
    var info=(instMesh.userData.rowInfo&&instMesh.userData.rowInfo[idx])||{};
    var colourInfo=lastColourTable&&lastColourTable[info.code];
    var colourName=(colourInfo&&colourInfo.name)||('colour '+info.code);
    inspect.hidden=false;
    inspect.textContent='Selected: '+(info.partId||'?')+' ('+colourName+')';
  }
  function clearGroup(THREE){
    highlighted=null;   // the highlighted InstancedMesh is about to be disposed below -- drop the stale reference, not restore a colour on a mesh that won't exist
    var inspectEl=$('tjsinspect');if(inspectEl)inspectEl.hidden=true;
    var chipsEl=$('tjsstepchips');if(chipsEl)chipsEl.textContent='';
    var checksEl=$('tjschecks');if(checksEl){checksEl.textContent='';checksEl.hidden=true;}
    while(group.children.length){
      var m=group.children.pop();
      if(m.geometry)m.geometry.dispose();
      // InstancedMesh owns a second GPU resource beyond its geometry -- the per-instance matrix buffer --
      // freed via its own dispose() (fires the 'dispose' event the renderer listens for). Materials are
      // deliberately NOT disposed here: materialForCode/materialForFixedHex cache and reuse them across
      // renders (switching sets shouldn't pay to rebuild the same colour's material every time).
      if(m.isInstancedMesh)m.dispose();
      group.remove(m);
    }
  }
  // Frames the camera on whatever was actually loaded, via the shared tjsFitCamera() (see
  // threejs_view_math.js -- the pure corner-projection math is tested directly there, not re-derived here).
  function fitCamera(THREE){
    var box=new THREE.Box3().setFromObject(group);
    if(box.isEmpty())return;
    // Real canvas aspect, not camera.aspect -- camera may currently BE orthoCamera (no .aspect property),
    // and either way both cameras below need fitting together regardless of which one is on screen right
    // now, so switching modes later shows the correct framing immediately with no re-fit needed.
    var w=renderer.domElement.clientWidth||300,h=renderer.domElement.clientHeight||480,aspect=w/h;
    var fit=tjsFitCamera([box.min.x,box.min.y,box.min.z],[box.max.x,box.max.y,box.max.z],
                          [0.6,0.5,0.6],perspCamera.fov,aspect,1.15);
    perspCamera.position.set(fit.position[0],fit.position[1],fit.position[2]);
    perspCamera.near=fit.near;perspCamera.far=fit.far;perspCamera.updateProjectionMatrix();
    // Same position/target/near/far as perspCamera -- an orthographic camera's on-screen SIZE never depends
    // on its distance (parallel projection), only its left/right/top/bottom frustum does, so there's no
    // reason for the two cameras to sit anywhere different; toggling between them needs no repositioning.
    orthoCamera.position.set(fit.position[0],fit.position[1],fit.position[2]);
    orthoCamera.near=fit.near;orthoCamera.far=fit.far;
    orthoFitHalfW=fit.ortho.halfW;orthoFitHalfH=fit.ortho.halfH;
    applyOrthoFrustum(aspect);
    controls.target.set(fit.target[0],fit.target[1],fit.target[2]);controls.update();
    // Shadow camera: sized off this SAME real box, not a fixed guess -- a frustum tuned for one build size
    // would clip a big kit's shadow or waste resolution (shadow acne) on a tiny one. radius covers the box's
    // own diagonal-ish extent regardless of which way the key light leans, with a margin for the light's own
    // angle (a light arriving at ~50 degrees from vertical casts a shadow longer than the object's own size).
    var center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());
    var radius=Math.max(size.x,size.y,size.z)*1.2+0.5;
    var lightDist=radius*3+5;
    keyLight.position.copy(center).addScaledVector(KEY_LIGHT_DIR,lightDist);
    keyLight.target.position.copy(center);keyLight.target.updateMatrixWorld();
    var sc=keyLight.shadow.camera;
    sc.left=-radius;sc.right=radius;sc.top=radius;sc.bottom=-radius;
    sc.near=Math.max(lightDist-radius*2,0.1);sc.far=lightDist+radius*2;
    sc.updateProjectionMatrix();
  }
  // Level of detail (threejs-viewer-feature-survey-and-priority item 5): the largest real kits (Death Star,
  // 7,757 real parts) are still capped to 3,000 by _BRICK_MAX (renderers/web_article.py, a twin of the
  // LIVE atoms_brick.gs's own _partsModelSanitise) -- a DATA-level cap, not a rendering one, and raising it
  // for real needs a deploy-and-verify cycle on the live renderer this session deliberately didn't take on
  // (see this commit's own message). What IS in scope here: making the viewer itself cheaper per part, so
  // whatever count DOES arrive costs less GPU work, and so there's real headroom already built in whenever
  // that data-side cap is eventually revisited. For a kit this size, a large fraction of parts are small
  // interior/background detail that resolves to only a handful of SCREEN pixels at the initial fitted
  // camera distance -- rendering their full, often-hundreds-of-triangles mesh there is paying real GPU cost
  // for visual detail nobody can actually see. Swaps those buckets' geometry for a simple 12-triangle box
  // matching the part's own bounding box (applyBoxProxy below) instead.
  //
  // Deliberately a ONE-TIME, load-time decision (using the fitCamera distance just computed above), not a
  // live per-frame/per-instance system: three.js's own THREE.LOD class swaps whole Object3D children by
  // distance, which doesn't map onto ONE InstancedMesh representing many different instances at once (the
  // same "can't isolate one instance" problem OutlinePass hit, see fetch_threejs.py's comment) -- true
  // dynamic LOD would mean re-bucketing individual INSTANCES between a detailed and a proxy InstancedMesh
  // as the camera moves, real added complexity for a viewer whose camera is fit once and then user-orbited,
  // not a flythrough. A load-time, per-bucket static decision is the honest scope for what this session can
  // verify, and (see GTAOPass's own history tonight) every attempt at LIVE scene-graph mutation under this
  // renderer has cost real debugging time to get right -- not repeating that pattern without a concrete need.
  var LOD_PROXY_PIXEL_THRESHOLD=4;
  function applyBoxProxy(THREE,instMesh){
    instMesh.geometry.computeBoundingBox();
    var bb=instMesh.geometry.boundingBox,size=new THREE.Vector3(),center=new THREE.Vector3();
    bb.getSize(size);bb.getCenter(center);
    // A degenerate (near-zero) dimension -- a flat printed-decal triangle group, say -- would make
    // BoxGeometry's constructor choke on a 0-size axis; floor every axis to a small real thickness instead.
    var box=new THREE.BoxGeometry(Math.max(size.x,0.5),Math.max(size.y,0.5),Math.max(size.z,0.5));
    box.translate(center.x,center.y,center.z);   // the part's own local geometry isn't necessarily centred on its origin -- keep the proxy where the real mesh actually was, not recentred on (0,0,0)
    instMesh.geometry.setAttribute('position',box.attributes.position);
    instMesh.geometry.setAttribute('normal',box.attributes.normal);
    instMesh.geometry.setIndex(box.index);
    instMesh.geometry.computeBoundingSphere();
    instMesh.userData.lodProxy=true;
  }
  function applyLOD(THREE){
    // Screen pixels per world-unit-of-size at distance=1 from a perspective camera with this vertical FOV;
    // dividing by a bucket's own real distance below gives its actual projected size in pixels. Using
    // perspCamera's own fov/position specifically (not whichever camera is currently active) since this is
    // a one-time, load-time heuristic, not a per-frame thing tied to the live view -- see fitCamera's own
    // comment on why both cameras always share one fitted position regardless of which is on screen.
    var canvasH=renderer.domElement.clientHeight||480;
    var pixelsPerUnitAtUnitDistance=canvasH/(2*Math.tan(perspCamera.fov*Math.PI/180/2));
    var swapped=0,total=0;
    group.children.forEach(function(instMesh){
      if(!instMesh.isInstancedMesh||!instMesh.userData.centroidLDU)return;
      total++;
      var c=instMesh.userData.centroidLDU;
      // D=diag(1/20,-1/20,1/20), the SAME LDraw-Y-down-to-three.js-Y-up mirror + LDU-to-world scale every
      // instance matrix gets via instMesh.scale (see tjsInstanceMatrixRowMajor's own comment) -- applied by
      // hand here since this reads the bucket's OWN stored centroid directly, not through setMatrixAt.
      var worldCentroid=new THREE.Vector3(c[0]/20,-c[1]/20,c[2]/20);
      var dist=Math.max(worldCentroid.distanceTo(perspCamera.position),0.01);
      instMesh.geometry.computeBoundingBox();
      var size=new THREE.Vector3();instMesh.geometry.boundingBox.getSize(size);
      // Raw vertex positions are quant-scaled (see tjsToWorld's own p[0]/q), not already LDU -- divide by
      // the part's own quant FIRST, matching the SAME two-stage scale every instance matrix gets (1/q baked
      // into the matrix, 1/20 baked into instMesh.scale), or this overstates real part size by a factor of
      // q (confirmed live 2026-09-30: without the /quant step, a 2x2x2 brick measured as ~96 world units --
      // roughly the size of the WHOLE Death Star kit -- because its raw geometry is quant=20-scaled).
      var worldSize=Math.max(size.x,size.y,size.z)/(instMesh.userData.quant||1)/20;
      var projectedPx=worldSize*pixelsPerUnitAtUnitDistance/dist;
      if(projectedPx<LOD_PROXY_PIXEL_THRESHOLD){applyBoxProxy(THREE,instMesh);swapped++;}
    });
    return {swapped:swapped,total:total};
  }
  // partEntries: one entry per partsModel ROW (not per instance slot -- a decorated part's multiple
  // colour-group instances must move together), {refs:[...], step}. Each ref is {instMesh, index, matrix}:
  // matrix is that row's own real placement (row-major, see tjsInstanceMatrixRowMajor), instMesh/index say
  // WHERE inside a shared InstancedMesh this row's geometry lives. Shared by both the Phase 1 scrubber and
  // Phase 2 animate loop below.
  var partEntries=[];
  // A pure zero-scale transform: every vertex collapses to the origin, zero screen area, effectively
  // invisible -- the InstancedMesh equivalent of the old per-Mesh `.visible=false` (InstancedMesh has no
  // native per-instance visibility flag; this is the standard, version-agnostic way to hide one instance
  // without touching the shared geometry or material, or reshuffling other instances' indices).
  var HIDDEN_ROW_MAJOR=[0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,1];
  function markGroupDirty(){
    group.children.forEach(function(c){
      if(!c.isInstancedMesh)return;
      c.instanceMatrix.needsUpdate=true;
      var ia=c.geometry.attributes.instanceAlpha;if(ia)ia.needsUpdate=true;
    });
  }
  // Step-parts chip list -- parity with the main WebGL view's own drawStepParts() (atoms_brick.gs): for the
  // CURRENT scrubbed step, group the real parts newly placed at that step by (part id, colour), with a count
  // and a colour swatch, under the same "New this step:" label. Pure data grouping over partsModel/the
  // colour table the viewer already has -- no validation engine involved (see drawValidationChecks below for
  // the one that does).
  function drawStepChips(partsModel,ct,step){
    var box=$('tjsstepchips');
    box.textContent='';
    var groups={},order=[];
    partsModel.forEach(function(row){
      if((row[6]|0||1)!==step)return;
      var code=row[5]|0,key=row[0]+'|'+code;
      if(!groups[key]){groups[key]={partId:row[0],code:code,count:0};order.push(key);}
      groups[key].count++;
    });
    if(!order.length)return;
    var label=document.createElement('span');
    label.style.cssText='font-weight:600;color:var(--mute)';label.textContent='New this step:';
    box.appendChild(label);
    order.forEach(function(key){
      var g=groups[key],hex=(ct[g.code]&&ct[g.code].hex)||'#c91a09';
      var chip=document.createElement('span');
      chip.style.cssText='display:inline-flex;align-items:center;gap:5px;border:1px solid #b8c2cc;border-radius:6px;padding:2px 8px;background:#f7f9fb';
      var swatch=document.createElement('span');
      swatch.style.cssText='display:inline-block;width:10px;height:10px;border-radius:2px;border:1px solid rgba(0,0,0,.25);background:'+hex;
      chip.appendChild(swatch);
      chip.appendChild(document.createTextNode('×'+g.count+' '+g.partId));
      box.appendChild(chip);
    });
  }
  // Validation checklist -- parity with the main WebGL view's own drawChecks() (atoms_brick.gs), driven by
  // the SAME real collision/connector validator (validatePartsPure, extracted verbatim into
  // brick_validate_shared.js and embedded above -- see that file's own header for why atoms_brick.gs itself
  // stays untouched and how parity with it is enforced). Same visual convention: a checkmark/warning/cross
  // per check, colour-coded, with a `title` tooltip carrying the same detail text also shown inline.
  var TJS_CHECK_COLOUR={pass:'#1e7a45',warn:'#9a6700',fail:'#c4161a'};
  var TJS_CHECK_MARK={pass:'✓',warn:'!',fail:'✗'};
  function drawValidationChecks(partsModel,byId){
    var ul=$('tjschecks');
    var list=partsModel.map(function(row){return {p:row[0],x:row[1],y:row[2],z:row[3],r:row[4]|0};});
    var meshes=partsModel.map(function(row){return byId[row[0]];});
    var report=validatePartsPure(list,meshes);
    ul.textContent='';
    report.checks.forEach(function(c){
      var li=document.createElement('li');
      li.style.cssText='display:flex;gap:6px;align-items:baseline';
      li.title=c.detail;
      var mark=document.createElement('span');
      mark.style.cssText='font-weight:700;color:'+TJS_CHECK_COLOUR[c.status];
      mark.textContent=TJS_CHECK_MARK[c.status];
      var label=document.createElement('span');
      label.style.fontWeight='600';label.textContent=c.label;
      var detail=document.createElement('span');
      detail.style.color='var(--mute)';detail.textContent=c.detail;
      li.appendChild(mark);li.appendChild(label);li.appendChild(detail);
      ul.appendChild(li);
    });
    ul.hidden=!report.checks.length;
  }
  // Build-step scrubber (Phase 1 of the "View in Three.js" motion work) -- a static cumulative reveal via
  // partsModel's own real `step` field (row[6], already present in every real build). Every instance is
  // placed once at render() time (so fitCamera sees the FULL final build and the camera never jumps as you
  // scrub); the scrubber only ever swaps an instance's matrix between its real placement and the hidden
  // (zero-scale) one, never rebuilds geometry.
  function applyStep(step){
    var THREE=mod.THREE,m4=new THREE.Matrix4();
    partEntries.forEach(function(e){
      var els=e.step<=step?null:HIDDEN_ROW_MAJOR;
      e.refs.forEach(function(ref){
        m4.set.apply(m4,els||ref.matrix);
        ref.instMesh.setMatrixAt(ref.index,m4);
      });
    });
    markGroupDirty();
  }
  // Phase 2: the live canvas renderer's continuous drop/bounce/settle/hold/lift-out "Animate" loop, ported
  // from atoms_brick.gs's status(t) (constants FALL/SETTLE/HOLD/LIFT/DROP and the stagger/dst timing are
  // copied from there verbatim -- this is the same real motion, not a reinvented one). Runs per-frame on
  // partEntries (not partsModel directly), reusing the same instance slots the scrubber already placed.
  //
  // Real per-instance alpha (getAnimateVariant, defined above ensureScene): the fall-in/lift-out fade is
  // genuine alpha blending now, not the scale-based grow/shrink stand-in the first version of this loop
  // used while InstancedMesh's one-material-per-bucket sharing had no per-instance opacity to drive.
  var animRAF=null,animLastT=0,animT=0,animPlaying=false;
  function stopAnimate(){
    animPlaying=false;
    if(animRAF)cancelAnimationFrame(animRAF);
    animRAF=null;
    // Restore each bucket's real (opaque, fast) material -- swapped to the Animate-variant clone in
    // startAnimate below. No per-instance matrix/alpha to restore here: every stop site (the Animate button,
    // and render() itself at the top of a fresh load) immediately calls applyStep() right after, which sets
    // every instance's matrix back to a consistent state; instanceAlpha simply stops being read once the
    // material is back to its non-patched, static form. group is null on the very first call: render()
    // calls stopAnimate() as its own first line, before ensureScene() has ever created it.
    if(group)group.children.forEach(function(c){
      if(c.isInstancedMesh&&c.userData.staticMaterial){c.material=c.userData.staticMaterial;delete c.userData.staticMaterial;}
    });
  }
  function startAnimate(){
    var N=partEntries.length;
    if(!N)return;
    var THREE=mod.THREE;
    // Same live InstancedMesh.material reassignment GTAOPass can't survive, see materialSel.onchange's
    // comment above (the concrete/LEGO toggle) -- applies identically here, just triggered by Animate
    // instead of the material selector. Disable GTAO permanently once this has ever happened, rather than
    // risk the exact same crash the first time anyone hits Play.
    if(gtaoPass)gtaoPass.enabled=false;
    group.children.forEach(function(c){
      if(!c.isInstancedMesh)return;
      c.userData.staticMaterial=c.material;
      c.material=getAnimateVariant(THREE,c.material);
    });
    var FALL=0.55,SETTLE=0.45,HOLD=3,LIFT=0.7,DROP=7;
    var stagger=Math.min(0.12,5/N),dst=1.4/N;
    var tBuild=N*stagger+FALL+SETTLE;
    var tCycle=tBuild+HOLD+N*dst+LIFT+0.5;
    partEntries.forEach(function(e,i){
      e.t0=i*stagger;e.td=tBuild+HOLD+(N-1-i)*dst;
      e.jx=(Math.random()-0.5)*7;e.jz=(Math.random()-0.5)*7;
    });
    var reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    animT=reduced?tBuild+1:tBuild*0.7;
    animLastT=performance.now();
    animPlaying=true;
    var m4=new THREE.Matrix4();
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
        e.refs.forEach(function(ref){
          var alphaAttr=ref.instMesh.geometry.attributes.instanceAlpha;
          if(s===-1){
            m4.set.apply(m4,HIDDEN_ROW_MAJOR);
            alphaAttr.array[ref.index]=0;
          }else{
            // ox/oy/oz are real world-unit offsets (DROP etc. are tuned in world units, matching the live
            // canvas renderer's own physics constants). ref.matrix is the PRE-D matrix now (see
            // tjsInstanceMatrixRowMajor's comment) -- its translation is in raw LDU units, D-scaled down by
            // the InstancedMesh's own object-level .scale AFTER this. So the offset needs D's inverse
            // (diag(20,-20,20)) applied here first, or it would land 20x too small and Y unflipped once D
            // is applied on top. Scale is no longer touched here (always full size, matching atoms_brick.gs's
            // own real behaviour) -- `a` now drives instanceAlpha instead.
            var els=ref.matrix;
            m4.set(els[0],els[1],els[2],els[3]+ox*20,
                   els[4],els[5],els[6],els[7]-oy*20,
                   els[8],els[9],els[10],els[11]+oz*20,
                   0,0,0,1);
            alphaAttr.array[ref.index]=a;
          }
          ref.instMesh.setMatrixAt(ref.index,m4);
        });
      });
      markGroupDirty();
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
      lastColourTable=ct;   // read by click-to-inspect to show a real colour name, not just a numeric code
      ensureScene(THREE,x.mm.OrbitControls,x.mm.RoomEnvironment);
      clearGroup(THREE);
      partEntries=[];
      status.textContent='Loading '+partsModel.length+' real part'+(partsModel.length===1?'':'s')+'…';
      var ids=Array.from(new Set(partsModel.map(function(row){return row[0]})));
      return Promise.all(ids.map(function(id){return fetchMesh(id).catch(function(){return null})})).then(function(meshes){
        var byId={};ids.forEach(function(id,i){byId[id]=meshes[i]});
        // localGeoCache: one shared, untransformed geometry set per part id, built once and reused by every
        // instance of that part below (fresh per render() call -- clearGroup() disposed the previous
        // render's geometries, so this must not persist across calls). buckets: one entry per (part id,
        // triangle-group index, resolved material) combination -- every instance sharing a bucket becomes
        // ONE InstancedMesh, which is the actual performance win over one real Mesh (and draw call) per
        // placed brick. ref objects are pushed into BOTH a bucket's own list and that row's partEntries
        // entry, then filled in-place with {instMesh,index} once each bucket's InstancedMesh exists below --
        // so partEntries end up fully resolved with no separate key-matching pass needed.
        var localGeoCache={},buckets={},ok=0,skipped=0,maxStep=1;
        partsModel.forEach(function(row){
          var mesh=byId[row[0]];
          if(!mesh){skipped++;return}
          var instPos=[row[1],row[2],row[3]],r=row[4]|0,code=row[5]|0,step=row[6]|0||1;
          maxStep=Math.max(maxStep,step);
          if(!localGeoCache[row[0]])localGeoCache[row[0]]=localGeometryGroups(THREE,mesh);
          var groups=localGeoCache[row[0]];
          if(!groups.length){skipped++;return}
          var mrow=tjsInstanceMatrixRowMajor(r,instPos,mesh.quant||1);
          var refs=[];
          groups.forEach(function(g,gi){
            var matKey=g.colourKey?('h'+g.colourKey):('c'+code);
            var key=row[0]+'|'+gi+'|'+matKey;
            if(!buckets[key])buckets[key]={rawGeo:g.geo,colourKey:g.colourKey,code:code,quant:mesh.quant||1,refs:[]};
            var ref={matrix:mrow,instMesh:null,index:-1,partId:row[0],code:code};
            buckets[key].refs.push(ref);
            refs.push(ref);
          });
          partEntries.push({refs:refs,step:step});
          ok++;
        });
        var m4=new THREE.Matrix4();
        Object.keys(buckets).forEach(function(key){
          var b=buckets[key];
          var mat=b.colourKey?materialForFixedHex(THREE,b.colourKey):materialForCode(THREE,b.code,ct);
          // Per-bucket geometry WRAPPER, not the shared localGeoCache geometry directly: position/normal
          // attribute OBJECTS are reused by reference (three.js caches the GPU buffer by attribute identity,
          // so this costs nothing extra on the GPU -- no vertex data is duplicated), but each bucket needs
          // its OWN instanceAlpha buffer below, and that's a per-InstancedMesh-sized array -- two DIFFERENT
          // buckets of the SAME part (e.g. a red 3005 and a blue 3005) share the SAME raw geometry from
          // localGeoCache but have DIFFERENT instance counts, so they cannot share one instanceAlpha array.
          // (instanceMatrix/instanceColor don't have this problem -- three.js keeps those on the InstancedMesh
          // object itself, not the geometry; instanceAlpha is a custom attribute with no such special slot.)
          var geo=new THREE.BufferGeometry();
          geo.setAttribute('position',b.rawGeo.attributes.position);
          geo.setAttribute('normal',b.rawGeo.attributes.normal);
          var instMesh=new THREE.InstancedMesh(geo,mat,b.refs.length);
          instMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);   // scrubber/animate rewrite this every step/frame
          instMesh.castShadow=true;instMesh.receiveShadow=true;   // bricks both cast onto the floor/each other and catch shadows from taller neighbours
          // The LDraw-Y-down -> three.js-Y-up mirror + /20 LDU-to-world scale (tjsToWorld's own D, see
          // tjsInstanceMatrixRowMajor's comment) lives HERE, once per bucket, not inside any instance matrix.
          instMesh.scale.set(1/20,-1/20,1/20);
          instMesh.userData.rowInfo=[];   // index -> {partId,code}, for click-to-inspect resolving a raycast hit back to its source part
          // Real per-instance alpha (Animate's fall-in/lift-out fade): a custom instanced attribute, not a
          // three.js built-in the way instanceColor is -- declared here at 1.0 (fully opaque) for every
          // instance; the animate loop below writes real 0..1 values into it while the Animate-variant
          // material (see getAnimateVariant) is active, via a fragment-shader multiply injected through
          // onBeforeCompile. Kept on EVERY bucket unconditionally (not lazily added only when Animate starts)
          // so the wiring is uniform and simple -- the cost is one small Float32Array per bucket, not a
          // per-frame or per-render cost.
          var alpha=new Float32Array(b.refs.length).fill(1);
          var alphaAttr=new THREE.InstancedBufferAttribute(alpha,1);
          alphaAttr.setUsage(THREE.DynamicDrawUsage);
          geo.setAttribute('instanceAlpha',alphaAttr);
          // Pre-allocate instanceColor (all-white, i.e. a no-op multiplier) up front, at the SAME time as
          // instanceAlpha above, rather than leaving it lazily created later by setColorAt() the first time
          // Concrete mode is picked (applyConcreteColourVariation). GTAOPass renders the whole scene every
          // frame through ONE shared override material (scene.overrideMaterial = its own MeshNormalMaterial,
          // see GTAOPass.js's _renderOverride) -- if instanceColor appears on an InstancedMesh mid-session,
          // BOTH the real material's and that shared override material's compiled program variant for this
          // object change (USE_INSTANCING_COLOR flips on) and must recompile, live, while the override pass
          // is already in use. Confirmed live (2026-09-30): switching LEGO->Concrete crashed the whole
          // headless Chromium renderer process outright (not a catchable WebGL error) under SwiftShader
          // specifically when GTAO was active; the identical switch was clean with GTAO's composer bypassed.
          // Matching three.js's own InstancedMesh.setColorAt lazy-init exactly (white-filled Float32Array,
          // stride 3) means the attribute -- and therefore every program variant that depends on its
          // presence -- exists from the very first frame, before GTAOPass ever compiles anything, so no
          // mid-session recompile under the override pass ever happens again.
          instMesh.instanceColor=new THREE.InstancedBufferAttribute(new Float32Array(b.refs.length*3).fill(1),3);
          // Centroid of this bucket's own instance positions (LDU, pre-D -- same space ref.matrix's own
          // translation columns [3],[7],[11] are already in, see tjsInstanceMatrixRowMajor), accumulated
          // for free in the SAME loop that's already touching every ref. Used by applyLOD below (after
          // fitCamera has a real camera position to measure against) as a cheap per-bucket distance
          // estimate -- not exact for a bucket whose instances are spread across a huge kit, but a coarse,
          // honest one: the goal is catching bricks that are SMALL ON SCREEN (background/interior detail
          // too tiny to resolve, not literally the single occasional outlier instance), and centroid
          // distance is the right cost/precision trade-off for a decision made once at load time, not
          // something recomputed every frame per instance.
          var cx=0,cy=0,cz=0;
          b.refs.forEach(function(ref,idx){
            m4.set.apply(m4,ref.matrix);
            instMesh.setMatrixAt(idx,m4);
            ref.instMesh=instMesh;ref.index=idx;
            instMesh.userData.rowInfo[idx]={partId:ref.partId,code:ref.code};
            cx+=ref.matrix[3];cy+=ref.matrix[7];cz+=ref.matrix[11];
          });
          instMesh.instanceMatrix.needsUpdate=true;
          instMesh.userData.centroidLDU=[cx/b.refs.length,cy/b.refs.length,cz/b.refs.length];
          instMesh.userData.quant=b.quant;   // raw vertex positions are quant-scaled, not already LDU -- see tjsToWorld's own p[0]/q; applyLOD's worldSize needs the SAME /q before the /20 D-scale, or it overstates a part's real size by a factor of q
          group.add(instMesh);
        });
        // Force-compile BOTH the LEGO and Concrete material program variants for every bucket now, up
        // front, synchronously -- before the render loop's very next frame runs through GTAOPass's composer
        // -- rather than leaving whichever variant hasn't been used yet to compile lazily on the first live
        // switch. Confirmed live (2026-09-30): a runtime LEGO->Concrete switch crashed the whole headless
        // Chromium renderer process outright (not a catchable WebGL error, no console message) under
        // SwiftShader once GTAO's composer was already several frames into its own render loop; the
        // IDENTICAL material was completely stable when it was the mode from the very first frame instead
        // (confirmed both ways: GTAO composer bypassed entirely -> stable; Concrete picked as the initial
        // mode with GTAO active, no live switch -> also stable). renderer.compile() forces eager shader
        // compilation the same way three.js recommends for avoiding first-use runtime stutter -- used here
        // for crash-safety under this driver, not performance.
        (function precompileMaterialVariants(){
          var prevMode=currentMaterialMode;
          currentMaterialMode='concrete';applyMaterialMode(THREE);renderer.compile(scene,camera);
          currentMaterialMode='lego';applyMaterialMode(THREE);renderer.compile(scene,camera);
          currentMaterialMode=prevMode;applyMaterialMode(THREE);
        })();
        fitCamera(THREE);
        var lodResult=applyLOD(THREE);
        drawValidationChecks(partsModel,byId);
        var slider=$('tjsstep'),playBtn=$('tjsplay'),materialSel=$('tjsmaterial');
        $('tjscontrols').hidden=false;
        materialSel.value=currentMaterialMode;
        // GTAOPass renders the whole scene every frame through its OWN shared override material
        // (scene.overrideMaterial, see GTAOPass.js's _renderOverride) -- confirmed live (2026-09-30) that
        // reassigning InstancedMesh.material to a DIFFERENT material object (LEGO<->Concrete) crashes the
        // whole headless Chromium renderer process outright under SwiftShader (not a catchable WebGL error,
        // no console message at all) the moment GTAOPass's override pass next touches that object. Isolated
        // by elimination -- each tried and confirmed independently: NOT a first-time shader-compile cost
        // (both variants precompiled up front via precompileMaterialVariants above, crash persisted); NOT
        // the concrete-colour instanceColor jitter (crash persisted with that loop disabled); NOT the
        // Concrete material itself (rock solid as the INITIAL mode from page load, GTAO active throughout);
        // NOT EffectComposer/OutputPass generally (rock solid with gtaoPass.enabled left permanently false
        // from construction); NOT stale state on the specific GTAOPass instance (briefly disabling then
        // re-enabling it around the switch still crashed; swapping in a genuinely NEW GTAOPass instance
        // post-switch still crashed too). The one thing that stayed rock solid, every time: GTAOPass never
        // rendering a single frame against an object whose material has ever changed identity at runtime.
        // Pragmatic fix, not a perfect one: once a material switch happens, leave GTAO off for the rest of
        // this session rather than trying to resume it (every resume attempt reproduced the crash) --
        // trades a subtle ambient-occlusion enhancement for a viewer that never crashes, which is the right
        // side of that trade for a secondary visual toggle.
        materialSel.onchange=function(){
          currentMaterialMode=materialSel.value;
          applyMaterialMode(THREE);
          if(gtaoPass)gtaoPass.enabled=false;
        };
        // Parallel-projection ("Camera: Parallel (instructions)") view, matching real LEGO instruction-
        // booklet framing -- OrthographicCamera instead of PerspectiveCamera. OrbitControls natively
        // supports either camera type (checks object.isOrthographicCamera itself in several places, e.g.
        // its own dolly/zoom handling), but it recomputes its internal spherical angle/distance state FROM
        // controls.object.position on the very next update() -- so the two cameras must actually SHARE a
        // position at the moment of the switch, not just have started from the same fitCamera position
        // once at load. Confirmed live (2026-09-30) they drift apart the instant the user orbits in EITHER
        // mode before switching: each camera object only moves when it's the one actively being dragged,
        // so toggling modes after orbiting jumped the view back to its original load-time angle instead of
        // preserving whatever angle the user had actually reached. Copying position across explicitly, every
        // switch, fixes it -- a real position copy IS needed, every time, not just once at setup.
        var cameraModeSel=$('tjscameramode');
        if(cameraModeSel){
          cameraModeSel.value=cameraMode;
          cameraModeSel.onchange=function(){
            var newCamera=(cameraModeSel.value==='ortho')?orthoCamera:perspCamera;
            newCamera.position.copy(camera.position);
            cameraMode=cameraModeSel.value;
            camera=newCamera;
            controls.object=camera;
            if(renderPass)renderPass.camera=camera;
            if(gtaoPass){
              gtaoPass.camera=camera;
              // Same GTAOPass fragility as the material/Animate/click-to-inspect sites above: its own
              // render-time code reads this.camera.isPerspectiveCamera to set a shader DEFINE every frame
              // (see the vendored GTAOPass.js), so flipping camera TYPE here would force the exact same
              // class of live shader recompile mid-session that crashed the renderer under SwiftShader for
              // those three. Not independently re-tested here (once was already three times) -- disabled
              // permanently the first time this toggle is used, same as the others, on the same reasoning.
              gtaoPass.enabled=false;
            }
            controls.update();
          };
        }
        // Premium render (Blender/Cycles, offline): triggers a real async Cloud Run Job execution via
        // premium-render-api (see the premium-export plan -- a genuinely separate service from this static
        // page's own origin, NOT cloud-run-renderer, which is IAM-gated and has a 60s synchronous-request
        // timeout far too short for a multi-minute Cycles render). This is this page's FIRST cross-origin
        // fetch (confirmed before this change: nothing else here calls off-origin) -- premium-render-api
        // responds with Access-Control-Allow-Origin:* for exactly this reason. Wiring matches #go's own
        // established convention (disable+relabel before the call, reset in every terminal branch, write
        // failures to a .note element) -- no progress bar, this codebase's convention throughout.
        var premiumBtn=$('premium'),premiumNote=$('premiumNote');
        if(premiumBtn){
          premiumBtn.onclick=function(){
            if(!last||!last.partsModel||!last.partsModel.length){premiumNote.textContent='Design something first.';return}
            premiumNote.textContent='';premiumBtn.disabled=true;premiumBtn.textContent='Rendering…';
            fetch(PREMIUM_RENDER_BASE_URL+'/trigger',{method:'POST',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({partsModel:last.partsModel})})
            .then(function(r){return r.json().catch(function(){return {ok:false,error:'unexpected response'}})})
            .then(function(j){
              if(!j.ok){
                premiumNote.textContent=j.error||'Could not start the render.';
                premiumBtn.disabled=false;premiumBtn.textContent='Premium render (Blender)';
                return;
              }
              premiumNote.textContent='Rendering your premium view — this can take several minutes…';
              var started=Date.now(),maxWaitMs=20*60*1000;
              var iv=setInterval(function(){
                if(Date.now()-started>maxWaitMs){
                  clearInterval(iv);
                  premiumNote.textContent='Still not done after a while — try again later.';
                  premiumBtn.disabled=false;premiumBtn.textContent='Premium render (Blender)';
                  return;
                }
                fetch(PREMIUM_RENDER_BASE_URL+'/status?jobId='+encodeURIComponent(j.jobId)+'&renderId='+encodeURIComponent(j.renderId))
                .then(function(r){return r.json()})
                .then(function(s){
                  if(s.state==='running')return;
                  clearInterval(iv);
                  if(!s.ok){
                    premiumNote.textContent=s.error||'Render failed.';
                  }else{
                    premiumNote.innerHTML='Ready: <a href="'+s.heroUrl+'" target="_blank" rel="noopener">still</a>'+
                      (s.turntableUrl?' &middot; <a href="'+s.turntableUrl+'" target="_blank" rel="noopener">turntable</a>':'');
                  }
                  premiumBtn.disabled=false;premiumBtn.textContent='Premium render (Blender)';
                }).catch(function(){});   // silent-fail per retry -- same style public/surfaces/mcp-apps/renderer-bundle.html's own poll loop uses
              },8000);
            })
            .catch(function(){
              premiumNote.textContent='Could not reach the render service.';
              premiumBtn.disabled=false;premiumBtn.textContent='Premium render (Blender)';
            });
          };
        }
        if(maxStep>1){
          $('tjsstepwrap').style.display='flex';
          slider.min=1;slider.max=maxStep;slider.value=maxStep;
          $('tjsstepnote').textContent='step '+maxStep+' of '+maxStep;
          drawStepChips(partsModel,ct,maxStep);
          slider.oninput=function(){
            if(animPlaying)return;
            var v=parseInt(slider.value,10)||1;
            applyStep(v);
            $('tjsstepnote').textContent='step '+v+' of '+maxStep;
            drawStepChips(partsModel,ct,v);
          };
        }else{
          $('tjsstepwrap').style.display='none';
          applyStep(1);
          drawStepChips(partsModel,ct,1);
        }
        playBtn.setAttribute('aria-pressed','false');
        playBtn.textContent='Animate';
        playBtn.onclick=function(){
          if(animPlaying){
            stopAnimate();
            playBtn.setAttribute('aria-pressed','false');playBtn.textContent='Animate';
            slider.disabled=false;
            var v=parseInt(slider.value,10)||maxStep;
            applyStep(v);
            drawStepChips(partsModel,ct,v);
          }else{
            startAnimate();
            playBtn.setAttribute('aria-pressed','true');playBtn.textContent='Stop';
            slider.disabled=true;
            $('tjsstepchips').textContent='';   // matches atoms_brick.gs's own drawStepParts(), which only shows in step-scrub mode, not during continuous animate
          }
        };
        status.textContent=ok+' of '+partsModel.length+' real parts rendered'+(skipped?' ('+skipped+' not yet in the baked catalogue)':'')+
          (lodResult.swapped?' ('+lodResult.swapped+' of '+lodResult.total+' part groups simplified for distance/size)':'')+
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
            .replace("__THREEJS_VIEW_MATH__", THREEJS_VIEW_MATH)
            .replace("__BRICK_VALIDATE_SHARED__", BRICK_VALIDATE_SHARED))


def main(out=OUT):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
