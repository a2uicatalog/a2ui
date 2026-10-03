#!/usr/bin/env python3
"""build_promo_studio.py -- public/bricksdemo/studio/index.html, "Brick Set Studio": search or pick any real
LEGO set, import it live (GET /api/brick-omr, already deployed on the production Worker -- see
a2ui-private/mcp-worker/src/omr-import.js), then play it flying together and snapping into place with the
studio shader look (motion_bricks `motion`, 2026-10-03 -- see briefs/opus-lego-rotation-capability.md and
briefs/lego-brick-motion-assembly.md). One live page, works for any set the OMR library has a model for, not
a pre-baked series: the gallery (set_gallery.json) is a curated, ranked starting point, exactly the same role
it already plays on the Brick Design Lab (build_design_page.py) -- this page does not replace that one or
touch any of its code, it is a separate, focused experience built around the single new capability.

The lego rendering engine itself (_brickKit, atoms_brick.gs) is NEVER touched by anything on this page -- only
WHICH set is loaded and the page-level backdrop preset change; the brick shader, materials and motion math are
read once from the real renderer source (same _brick_fn_src/_brick_material_profile_src helpers
_render_motion_bricks itself uses, renderers/web_article.py) so this page can never drift from the live engine.

  python3 scripts/brick_models/build_promo_studio.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "public" / "bricksdemo" / "studio" / "index.html"

sys.path.insert(0, str(ROOT / "scripts"))
import generate_atom_pages as _site  # noqa: E402  the site's shared chrome -- one definition

sys.path.insert(0, str(ROOT))
from renderers import web_article as w  # noqa: E402

BRICK_KIT_SRC = w._brick_fn_src("_brickKit")
MATERIAL_PROFILE_SRC = w._brick_material_profile_src()

PAGE_CSS = """
.wrap{max-width:1040px}
.layout{display:grid;grid-template-columns:300px 1fr;gap:18px}
@media (max-width:820px){.layout{grid-template-columns:1fr}}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px;display:flex;flex-direction:column;gap:10px}
.panel h2{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 2px}
#setnum{display:flex;gap:6px}
#setnum input{flex:1;min-width:0;padding:7px 9px;border:1px solid var(--border);border-radius:6px;background:var(--surface-2);color:inherit;font:inherit}
#setnum button,#search input{padding:7px 10px;border:1px solid var(--border);border-radius:6px;background:var(--surface-2);color:inherit;font:inherit;cursor:pointer}
#setnum button:hover{border-color:var(--accent,#5b8def)}
#search input{width:100%;cursor:text}
#searchres,#gallery{display:flex;flex-direction:column;gap:6px;max-height:360px;overflow:auto}
.scard{display:flex;gap:8px;align-items:center;text-align:left;padding:6px;border:1px solid var(--border);border-radius:6px;background:var(--surface-2);cursor:pointer;font:inherit;color:inherit}
.scard:hover{border-color:var(--accent,#5b8def)}
.scard img{width:36px;height:36px;object-fit:contain;border-radius:4px;background:#fff;flex:none}
.scard .st{font-size:.78rem;font-weight:600;line-height:1.25}
.scard .sp{font-size:.7rem;color:var(--muted)}
.note{font-size:.78rem;color:var(--muted);min-height:1.2em}
#stage-wrap{border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;transition:background .25s}
#cv{width:100%;aspect-ratio:16/9;display:block;touch-action:none;cursor:grab}
.ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}
.ctl button,.ctl select{padding:6px 10px;border:1px solid var(--border);border-radius:6px;background:var(--surface-2);color:inherit;font:inherit;cursor:pointer}
.ctl button:hover{border-color:var(--accent,#5b8def)}
.swatch{width:26px;height:26px;border-radius:50%;border:2px solid transparent;padding:0;cursor:pointer}
.swatch[aria-pressed="true"]{border-color:var(--ink,#111)}
.ctl label{font-size:.78rem;color:var(--muted);display:flex;align-items:center;gap:6px}
#stats{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:.8rem}
#stats b{display:block;font-size:1.05rem}
#stats span{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em}
.wrap footer{border-top:1px solid var(--border);padding-top:12px;margin-top:20px}
.wrap footer p{font-size:12px;color:var(--muted)}
"""

BODY = """
  <div>
    <h1 style="font-size:1.4rem;font-weight:800;margin-bottom:8px;">Brick Set Studio</h1>
    <p style="color:var(--muted);font-size:13px;max-width:70ch;margin-bottom:18px;">Search or pick any real set below and watch it fly together, piece by piece, with the studio shader look -- glossy ABS, softbox reflections, no outlines. The rendering engine never changes; only which set is loaded and the backdrop do. Geometry comes live from the LDraw Official Model Repository, the same import already used by the <a href="/bricksdemo/design/">Brick Design Lab</a>.</p>
  </div>
  <div class="layout">
    <div>
      <div class="panel">
        <h2>Set number</h2>
        <div id="setnum"><input id="setid" placeholder="e.g. 21005-1" autocomplete="off"><button id="setgo" type="button">Load</button></div>
        <p class="note" id="setnote"></p>
      </div>
      <div class="panel">
        <h2>Search by name</h2>
        <div id="search"><input id="q" placeholder="Search LEGO sets&hellip;" autocomplete="off"></div>
        <div id="searchres"></div>
        <p class="note" id="searchnote"></p>
      </div>
      <div class="panel">
        <h2>Browse (ranked by real coverage)</h2>
        <div id="gallery"></div>
        <p class="note" id="gallerynote">Loading&hellip;</p>
      </div>
    </div>
    <div>
      <div id="stage-wrap">
        <canvas id="cv"></canvas>
      </div>
      <div class="ctl">
        <button id="replay" type="button">Replay</button>
        <label>Backdrop <select id="bdstyle" aria-label="Backdrop style">
          <option value="glow">Glow</option>
          <option value="grid">Grid</option>
          <option value="flat">Flat</option>
        </select></label>
        <label>Theme <select id="bdtheme" aria-label="Theme">
          <option value="dark">Dark</option>
          <option value="light">Light</option>
        </select></label>
        <span id="swatches" role="group" aria-label="Accent colour"></span>
        <label><input id="bdvignette" type="checkbox" checked> Vignette</label>
      </div>
      <div id="stats"></div>
      <div id="details" class="panel" hidden style="flex-direction:row;gap:14px;align-items:flex-start;margin-top:12px">
        <img id="det-img" alt="" style="width:76px;height:76px;object-fit:contain;background:#fff;border-radius:6px;flex:none">
        <div>
          <div id="det-name" style="font-weight:700;font-size:1rem"></div>
          <div id="det-meta" class="note" style="margin:2px 0 6px"></div>
          <a id="det-link" href="#" target="_blank" rel="noopener" style="font-size:.78rem">View on Rebrickable &#8599;</a>
        </div>
      </div>
      <p class="note" id="stagenote">Pick a set to begin.</p>
    </div>
  </div>
  <footer>
    <p>Import is live from the LDraw Official Model Repository (library.ldraw.org, CC BY 2.0) via the same route the Brick Design Lab uses. Set names and reference images in search and the gallery are from Rebrickable. The engine (the brick motion/studio shader) is <a href="https://github.com/a2uicatalog/a2ui">open source, MIT</a>. Fan-made, not affiliated with or endorsed by the LEGO Group. LEGO&reg; is a trademark of the LEGO Group, which does not sponsor, authorize or endorse this content.</p>
  </footer>
"""

PAGE_SCRIPT = f"""
{MATERIAL_PROFILE_SRC}
var K=({BRICK_KIT_SRC})();
var cv=document.getElementById('cv');
// Same origin (deployed on a2uicatalog.ai): relative paths, as every other page on the site uses. Any other
// origin (a local preview, a mirror): absolute, since relative paths would otherwise resolve against whatever
// is hosting THIS page, not the real API. The live Worker CORS-allows '*', so this works from anywhere.
var API_ORIGIN=(location.hostname==='a2uicatalog.ai')?'':'https://a2uicatalog.ai';
var atom=null,reduced=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
var DUR=5.2,playT0=null,playing=false,raf=0;
function n(x){{return (x||0).toLocaleString()}}
function esc(s){{return String(s).replace(/[&<>"']/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]}})}}

function frame(now){{
  raf=requestAnimationFrame(frame);
  if(!playing)return;
  if(playT0===null)playT0=now;
  var t=Math.min(1,(now-playT0)/1000/DUR);
  cv.style.setProperty('--p',String(t));
  if(t>=1)playing=false;
}}
raf=requestAnimationFrame(frame);

function play(){{
  if(reduced){{cv.style.setProperty('--p','1');return}}
  playT0=null;playing=true;
}}

var coloursFetch=null;
function colours(){{
  if(!coloursFetch)coloursFetch=fetch('/bricksdemo/ldraw_colours_full.json').then(function(r){{return r.json()}}).catch(function(){{return {{}}}});
  return coloursFetch;
}}
// /api/brick-omr returns partsModel as [id,x,y,z,r,colourIndex,step] arrays (same shape to_parts_model/omr-import.js
// produce) -- K.create() expects the OBJECT form {{p,x,y,z,r,c}} (see _partsModelSanitise, atoms_brick.gs), the same
// conversion the Brick Design Lab's own importSet() already does for its "parts" list. Skipping this was the real
// bug behind an earlier blank canvas on a real multi-part set: fetchPartMesh was being called with id=undefined
// for every entry, because array[i].p is undefined on a plain array.
function toObjectForm(partsModel,colourTable){{
  return (partsModel||[]).filter(function(p){{return Array.isArray(p)&&/^[0-9a-z-]{{1,24}}$/.test(p[0])}}).map(function(p){{
    var ci=p[5]|0,row=colourTable[ci]||{{}};
    return {{p:p[0],x:+p[1]||0,y:+p[2]||0,z:+p[3]||0,r:p[4]|0,c:row.hex||'#c91a09',edge:row.edge||'#333333'}};
  }});
}}

function loadSet(id,note){{
  note=note||document.getElementById('stagenote');
  if(!id)return;
  document.getElementById('setid').value=id;
  note.textContent='Importing '+id+'\\u2026';
  document.getElementById('setgo').disabled=true;
  Promise.all([
    fetch(API_ORIGIN+'/api/brick-omr?set='+encodeURIComponent(id)).then(function(r){{return r.json().catch(function(){{return {{ok:false,error:'unexpected response'}}}})}}),
    colours(),
    // Real set facts (name, year, part count, official box art, Rebrickable link) -- never invented copy.
    // Best-effort: the import still proceeds if this particular lookup fails or the set isn't in Rebrickable.
    fetch(API_ORIGIN+'/api/data/rebrickable_set?set_num='+encodeURIComponent(id)).then(function(r){{return r.ok?r.json():null}}).catch(function(){{return null}})
  ]).then(function(res){{
      var j=res[0],colourTable=res[1],meta=res[2];
      if(!j.ok){{note.textContent=j.error||'Could not import that set.';return}}
      var c=j.coverage||{{}};
      document.getElementById('stats').innerHTML=[['Set',j.set],['Real parts',n(c.parts)],['Rendered',n(c.renderable)],['Coverage',(c.fraction?Math.round(c.fraction*100):0)+'%']]
        .map(function(s){{return '<div><b>'+esc(String(s[1]))+'</b><span>'+esc(s[0])+'</span></div>'}}).join('');
      var det=document.getElementById('details');
      if(meta&&meta.name){{
        det.hidden=false;
        document.getElementById('det-img').src=meta.set_img_url||'';
        document.getElementById('det-name').textContent=meta.name;
        document.getElementById('det-meta').textContent=[meta.year,meta.num_parts?n(meta.num_parts)+' pieces (official count)':null,meta.set_num].filter(Boolean).join(' \\u00b7 ');
        document.getElementById('det-link').href=meta.set_url||('https://rebrickable.com/sets/'+encodeURIComponent(id)+'/');
      }}else{{det.hidden=true}}
      var pm=toObjectForm(j.partsModel,colourTable);
      atom=K.create(cv,{{partsModel:pm,clock:'film',azDeg:20,elDeg:26,turns:0.35,base:null,look:'studio',
        motion:{{order:'diagonal',from:'above',window:2.4,flight:0.62,distance:9,tilt:70,spin:0.5}}}});
      note.textContent=j.name+': '+n(c.renderable)+' of '+n(c.parts)+' real parts rendered ('+(c.fraction?Math.round(c.fraction*100):0)+'%).'+(c.tilted?(' '+n(c.tilted)+' sit at an angle not yet placed.'):'');
      cv.style.setProperty('--p','0');
      play();
    }})
    .catch(function(){{note.textContent='Could not reach the import service.'}})
    .then(function(){{document.getElementById('setgo').disabled=false}});
}}

document.getElementById('setgo').onclick=function(){{loadSet(document.getElementById('setid').value.trim())}};
document.getElementById('setid').addEventListener('keydown',function(e){{if(e.key==='Enter')loadSet(this.value.trim())}});
document.getElementById('replay').onclick=play;
cv.addEventListener('pointerdown',function(){{}});   // _brickKit's own drag-to-orbit already listens on the canvas

// Backdrop: the same three styles and formula as motion_timeline's own stage background (atoms_motion.gs
// _moTimeline -- glow/grid/flat, hex->rgb for the CSS gradient), "studio aligned options" rather than a
// separate ad hoc preset list. theme sets the base colour; accent tints glow/grid. No change to the brick
// engine itself -- this is page-level CSS on #stage-wrap, painted behind the canvas, never the shader.
var THEME_BG={{dark:'#06050a',light:'#f6f5f2'}},THEME_INK={{dark:'#eef0f4',light:'#15131c'}};
var ACCENTS=[['#38bdf8','Cyan'],['#e9b25b','Amber'],['#f06595','Rose'],['#51cf66','Green'],['#a78bfa','Violet']];
var bdState={{style:'glow',theme:'dark',accent:ACCENTS[0][0],vignette:true}};
function hexRgb(h){{h=h.replace('#','');return [0,2,4].map(function(i){{return parseInt(h.slice(i,i+2),16)}}).join(',')}}
// Vignette (2026-10-03, same reasoning as briefs/motion-stage-passes-grain-vignette-bloom.md's findings from the
// hand-roll-and-analyse pass earlier this session): a simple radial darkening toward the edges, the one of those
// three passes cheap enough to add here directly as page-level CSS -- draws the eye to the model, reads as a
// deliberate shot rather than a flat screenshot. Grain/bloom are real follow-ups, not done here (see that brief).
function applyBackdrop(){{
  var wrap=document.getElementById('stage-wrap'),bg=THEME_BG[bdState.theme],ink=THEME_INK[bdState.theme],acc=bdState.accent;
  var layers=[];
  if(bdState.style==='glow')layers.push('radial-gradient(ellipse at 50% 0%, rgba('+hexRgb(acc)+',0.22) 0%, rgba('+hexRgb(acc)+',0) 62%)');
  else if(bdState.style==='grid')layers.push('linear-gradient(rgba('+hexRgb(ink)+',0.08) 1px,transparent 1px),linear-gradient(90deg,rgba('+hexRgb(ink)+',0.08) 1px,transparent 1px)');
  if(bdState.vignette)layers.push('radial-gradient(ellipse 75% 75% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,.4) 100%)');
  wrap.style.background=bg;
  wrap.style.backgroundImage=layers.join(',');
  wrap.style.backgroundSize=bdState.style==='grid'?'48px 48px, 48px 48px, 100% 100%':'';
}}
applyBackdrop();
document.getElementById('bdstyle').addEventListener('change',function(){{bdState.style=this.value;applyBackdrop()}});
document.getElementById('bdtheme').addEventListener('change',function(){{bdState.theme=this.value;applyBackdrop()}});
document.getElementById('bdvignette').addEventListener('change',function(){{bdState.vignette=this.checked;applyBackdrop()}});
var swBox=document.getElementById('swatches');
ACCENTS.forEach(function(a,i){{
  var b=document.createElement('button');b.type='button';b.className='swatch';b.style.background=a[0];b.title=a[1];b.setAttribute('aria-label',a[1]);
  b.setAttribute('aria-pressed',i===0?'true':'false');
  b.onclick=function(){{bdState.accent=a[0];applyBackdrop();Array.prototype.forEach.call(swBox.children,function(c){{c.setAttribute('aria-pressed',c===b?'true':'false')}})}};
  swBox.appendChild(b);
}});

// Set gallery: same manifest and the same honest-coverage framing as the Brick Design Lab's gallery panel.
fetch('/bricksdemo/set_gallery.json').then(function(r){{return r.json()}}).then(function(j){{
  var sets=j.sets||[];
  var box=document.getElementById('gallery');box.innerHTML='';
  sets.slice(0,40).forEach(function(s){{
    var b=document.createElement('button');b.type='button';b.className='scard';
    var img=s.img_url?'<img src="'+esc(s.img_url)+'" alt="" loading="lazy">':'';
    b.innerHTML=img+'<span><span class="st">'+esc(s.title)+'</span><br><span class="sp">'+s.set+' \\u00b7 '+s.coverage_pct+'% renderable</span></span>';
    b.onclick=function(){{loadSet(s.set,document.getElementById('gallerynote'))}};
    box.appendChild(b);
  }});
  document.getElementById('gallerynote').textContent=sets.length?(n(sets.length)+' real sets, ranked by coverage.'):'No sets available.';
}}).catch(function(){{document.getElementById('gallerynote').textContent='Could not load the set gallery.'}});

// Live search, same endpoint the Brick Design Lab's search panel already calls.
var searchSeq=0,searchTimer=null;
document.getElementById('q').addEventListener('input',function(){{
  clearTimeout(searchTimer);
  var q=this.value.trim();
  var res=document.getElementById('searchres'),note=document.getElementById('searchnote');
  if(!q){{res.innerHTML='';note.textContent='';return}}
  searchTimer=setTimeout(function(){{
    var seq=++searchSeq;note.textContent='Searching\\u2026';
    fetch(API_ORIGIN+'/api/data/rebrickable_set_search?query='+encodeURIComponent(q))
      .then(function(r){{return r.json()}})
      .then(function(j){{
        if(seq!==searchSeq)return;
        var items=(j&&j.results)||[];
        res.innerHTML='';
        items.slice(0,12).forEach(function(s){{
          var b=document.createElement('button');b.type='button';b.className='scard';
          var img=s.img_url?'<img src="'+esc(s.img_url)+'" alt="" loading="lazy">':'';
          b.innerHTML=img+'<span><span class="st">'+esc(s.title||s.name||s.set)+'</span><br><span class="sp">'+esc(s.set||'')+'</span></span>';
          b.onclick=function(){{loadSet(s.set,note)}};
          res.appendChild(b);
        }});
        note.textContent=items.length?(items.length+' result(s). Not every result has a matching OMR model -- Load reports that honestly.'):'No matches.';
      }})
      .catch(function(){{if(seq===searchSeq)note.textContent='Search unavailable.'}});
  }},320);
}});
"""


def render():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brick Set Studio</title>
<meta name="description" content="Search or pick any real LEGO set and watch it fly together with the studio shader look, imported live from the LDraw Official Model Repository. Fan-made, not affiliated with or endorsed by the LEGO Group.">
<meta name="robots" content="noindex, nofollow">
{_site.SITE_HEAD_JS}
<style>{_site.SITE_BASE_CSS}
{PAGE_CSS}</style>
</head>
<body>
{_site.site_header("")}
<div class="wrap">
{BODY}
</div>
<script>{PAGE_SCRIPT}</script>
<script>
{_site.SITE_FOOT_JS.replace("<script>", "").replace("</script>", "")}
</script>
</body>
</html>
"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
