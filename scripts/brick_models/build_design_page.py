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

CNAMES = {0: 'Black', 1: 'Blue', 2: 'Green', 4: 'Red', 14: 'Yellow', 15: 'White', 19: 'Tan', 25: 'Orange', 27: 'Lime',
          28: 'Dark Tan', 70: 'Reddish Brown', 71: 'Light Bluish Gray', 72: 'Dark Bluish Gray', 272: 'Dark Blue',
          288: 'Dark Green', 320: 'Dark Red', 484: 'Dark Orange'}

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
#csearch{width:100%;font:inherit;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:8px}
textarea{width:100%;min-height:64px;resize:vertical;font:inherit;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:8px}
.row{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font:inherit;font-size:12px;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:99px;padding:3px 10px;cursor:pointer}
label{display:inline-flex;gap:6px;align-items:center;cursor:pointer}
select,button.go{font:inherit;color:inherit;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:6px 10px}
button.go{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600;cursor:pointer}
button.go:disabled{opacity:.55;cursor:progress}
button.alt{background:var(--bg);color:var(--fg);border-color:var(--rule)}
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
<label><input type="checkbox" data-eng="jev"> Jev (picks a template, no generation)</label>
<label><input type="checkbox" data-eng="laya"> Laya (hosted, picks a template)</label>
<label><input type="checkbox" data-eng="jevini"> Jevini (Jev, then Gemini refines if needed)</label>
<label><input type="checkbox" data-eng="layini"> Layini (Laya, then Gemini refines if needed)</label>
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
<section class="panel" id="result" hidden>
<div class="stats" id="stats"></div>
<p class="note" id="how"></p>
<div class="row"><button class="go" id="manual" type="button">Build manual</button>
<button class="go alt" id="csv" type="button">Rebrickable list (CSV)</button><span class="note" id="mstat"></span></div>
<iframe id="view" title="3D build" sandbox="allow-scripts allow-same-origin"></iframe>
</section>
<section class="panel tbl" id="histp" hidden>
<table id="hist"><thead><tr><th>#</th><th>Engine / model</th><th>Prompt</th><th>Tokens in</th><th>Tokens out</th><th>Cost</th><th>Bricks</th><th>Time</th></tr></thead><tbody></tbody></table>
</section>
<footer>
<p>Cost is computed from the token counts the model returns and the published per-million-token price (Gemini 3.7 Flash is an introductory rate). Jev and Laya only choose a template, colour and size, so they generate no text; Jevini and Layini add a Gemini stage only when the template is not confident or the prompt needs detail, and the cost shown is that Gemini stage. Jev's per-token price is not published, and Laya is a free hosted service by <a href="https://laya.pensero.ai">Pensero</a>. Renders use real LDraw parts (CC BY 4.0). Fan-made, not affiliated with the LEGO Group.</p>
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
var BOXES=Array.prototype.slice.call(document.querySelectorAll('input[data-eng]'));
BOXES.forEach(function(b){b.onchange=function(){if(b.checked)BOXES.forEach(function(o){if(o!==b)o.checked=false});sync()}});
function engine(){var on=BOXES.filter(function(b){return b.checked})[0];return on?on.getAttribute('data-eng'):'gemini'}
function sync(){var e=engine();$('model').disabled=!(e==='gemini'||e==='jevini'||e==='layini')}
var LABEL={jev:'Jev',laya:'Laya',jevini:'Jevini',layini:'Layini'};
function costText(j,e){if(e==='gemini')return usd(j.cost_usd);if(e==='jev')return 'n/a';if(e==='laya')return 'free';
  return j.gemini_called?usd(j.cost_usd)+' (Gemini stage)':(e==='layini'?'free':'n/a')}
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
var runs=0;
$('go').onclick=function(){
  var prompt=$('prompt').value.trim();
  if(!prompt){$('err').textContent='Describe a build first.';return}
  var eng=engine();
  $('err').textContent='';$('go').disabled=true;$('go').textContent='Designing…';
  var t0=Date.now();
  fetch('/api/brick-design',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({prompt:prompt,engine:eng,model:(eng==='gemini'||eng==='jevini'||eng==='layini')?$('model').value:undefined})})
  .then(function(r){return r.json().catch(function(){return {ok:false,error:'unexpected response'}}).then(function(j){return {r:r,j:j}})})
  .then(function(x){
    var j=x.j;
    if(!j.ok){$('err').textContent=j.error||'Something went wrong.';return}
    var u=j.usage||{};
    $('result').hidden=false;
    $('stats').innerHTML='';
    [['Tokens in',n(u.promptTokens)],['Tokens out',n(u.outputTokens)],
     ['Cost',costText(j,eng)],['Bricks',n(j.parts)],['Time',(j.ms/1000).toFixed(1)+' s']]
    .forEach(function(s){var d=document.createElement('div');d.className='stat';
      var b=document.createElement('b');b.textContent=s[1];var sp=document.createElement('span');sp.textContent=s[0];d.appendChild(b);d.appendChild(sp);$('stats').appendChild(d)});
    var how;
    if(eng==='gemini')how='Designed by '+j.model+' as a voxel grid'+(j.repaired&&j.repaired.dropped_cells?'; '+j.repaired.dropped_cells+' unanchored cells were dropped':'')+'.';
    else{var c=j.choice||{},sys=(eng==='jev'||eng==='jevini')?'Jev':'Laya';
      how=sys+' chose "'+c.archetype+'" (size '+c.size+(c.confidence!=null?', confidence '+(+c.confidence).toFixed(2):'')+(c.detail!=null?', detail needed '+(+c.detail).toFixed(2):'')+'). ';
      if(eng==='jev'||eng==='laya')how+='A deterministic generator built it; no text was generated.';
      else if(j.gemini_called){var g=(j.stages||[])[1]||{};how+='That was not enough, so '+j.model+' refined it with '+(g.edits||0)+' edits ('+n(g.usage&&g.usage.promptTokens)+' in / '+n(g.usage&&g.usage.outputTokens)+' out).'}
      else if(((j.stages||[])[1]||{}).failed)how+='Refinement was attempted but failed, so the plain template is shown.';
      else how+='That was confident enough, so Gemini was never called.'}
    $('how').textContent=how;
    last={j:j,partsModel:j.partsModel,parts:(function(){return (j.partsModel||[]).filter(function(p){return Array.isArray(p)&&/^[0-9a-z-]{1,24}$/.test(p[0])}).map(function(p){var c=p[5]|0;return {p:p[0],x:+p[1]||0,y:+p[2]||0,z:+p[3]||0,r:p[4]|0,c:HEX[c]||'#c91a09',edge:EDGE[c]||'#333333'}})})()};
    show(j);
    runs++;$('histp').hidden=false;
    var tr=document.createElement('tr');
    [runs,eng==='gemini'?j.model:(j.gemini_called?LABEL[eng]+'+'+j.model:LABEL[eng]),prompt.length>34?prompt.slice(0,33)+'…':prompt,n(u.promptTokens),n(u.outputTokens),
     costText(j,eng),n(j.parts),(j.ms/1000).toFixed(1)+' s']
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
    names = {c: CNAMES[c] for c in CODES}
    return (PAGE.replace("__PRE__", esc(pre)).replace("__POST__", esc(post))
            .replace("__CNAME__", json.dumps(names)).replace("__HEX__", json.dumps(hexes)).replace("__EDGE__", json.dumps(edges)))


def main(out=OUT):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
