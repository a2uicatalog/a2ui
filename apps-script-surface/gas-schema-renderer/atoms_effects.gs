// atoms_effects.gs — Cursor & interaction effect atoms
// All pure inline JS/CSS — no CDN, GAS CSP-safe, surfaces: G M W
// Each effect is page-scoped and guarded against double-init.

// ── cursor_glow ───────────────────────────────────────────────────────────────
// Ambient radial gradient orb that smoothly follows the cursor.
// Fields:
//   colour  — glow colour (default #6366f1)
//   size    — orb diameter px (default 380)
//   opacity — 0–1 (default 0.18)
//   speed   — lerp factor 0–1: 0=instant, 0.05=dreamy lag (default 0.1)
//   blend   — CSS mix-blend-mode (default 'screen')
_RENDERERS['cursor_glow'] = function(b) {
  var colour  = b.colour  || '#6366f1';
  var size    = b.size    || 380;
  var opacity = b.opacity !== undefined ? b.opacity : 0.18;
  var speed   = b.speed   !== undefined ? b.speed   : 0.1;
  var blend   = b.blend   || 'screen';
  var half    = Math.floor(size / 2);

  return '<script>(function(){' +
    'if(window.__a2uiCursorGlow)return;window.__a2uiCursorGlow=true;' +
    'var el=document.createElement("div");' +
    'el.style.cssText="position:fixed;pointer-events:none;z-index:9000;border-radius:50%;' +
      'width:' + size + 'px;height:' + size + 'px;' +
      'background:radial-gradient(circle at 38% 38%,' + colour + ' 0%,transparent 68%);' +
      'opacity:' + opacity + ';' +
      'mix-blend-mode:' + blend + ';' +
      'will-change:transform;' +
      'transform:translate(-50%,-50%);' +
      'top:-600px;left:-600px;";' +
    'document.body.appendChild(el);' +
    'var tx=-600,ty=-600,mx=tx,my=ty;' +
    'window.addEventListener("mousemove",function(e){mx=e.clientX;my=e.clientY;});' +
    '(function loop(){' +
      'tx+=(mx-tx)*' + speed + ';' +
      'ty+=(my-ty)*' + speed + ';' +
      'el.style.left=tx.toFixed(1)+"px";' +
      'el.style.top=ty.toFixed(1)+"px";' +
      'requestAnimationFrame(loop);' +
    '})();' +
  '})();<\/script>';
};

// ── magnetic_element ──────────────────────────────────────────────────────────
// Wraps any HTML content — element drifts toward cursor when nearby.
// Fields:
//   content  — inner HTML (default: styled button label)
//   label    — shorthand text label (used if content not set)
//   radius   — activation distance in px (default 120)
//   strength — pull factor 0–1 (default 0.4)
//   accent   — background accent colour for the default pill style
_RENDERERS['magnetic_element'] = function(b) {
  var radius   = b.radius   || 120;
  var strength = b.strength || 0.4;
  var accent   = b.accent   || '#6366f1';
  var label    = b.label    || 'Hover me';
  var content  = b.content  ||
    '<span style="display:inline-block;padding:12px 28px;border-radius:100px;' +
    'background:' + _esc(accent) + ';color:#fff;font-size:0.9rem;font-weight:700;' +
    'letter-spacing:0.02em;cursor:default;user-select:none;">' + _esc(label) + '</span>';
  var uid = 'mag' + Math.random().toString(36).substr(2, 6);

  return '<div style="display:flex;justify-content:center;padding:32px 0;">' +
    '<div id="' + uid + '" style="display:inline-block;will-change:transform;">' +
      content +
    '</div>' +
  '</div>' +
  '<script>(function(){' +
    'var el=document.getElementById("' + uid + '");' +
    'if(!el)return;' +
    'function onMove(e){' +
      'var r=el.getBoundingClientRect();' +
      'var cx=r.left+r.width/2,cy=r.top+r.height/2;' +
      'var dx=e.clientX-cx,dy=e.clientY-cy;' +
      'var dist=Math.sqrt(dx*dx+dy*dy);' +
      'if(dist<' + radius + '){' +
        'var f=(1-dist/' + radius + ')*' + strength + ';' +
        'el.style.transition="transform 0.06s ease";' +
        'el.style.transform="translate("+(dx*f).toFixed(1)+"px,"+(dy*f).toFixed(1)+"px)";' +
      '}else{' +
        'el.style.transition="transform 0.5s cubic-bezier(0.175,0.885,0.32,1.275)";' +
        'el.style.transform="translate(0,0)";' +
      '}' +
    '}' +
    'window.addEventListener("mousemove",onMove);' +
  '})();<\/script>';
};

// ── particle_burst ────────────────────────────────────────────────────────────
// Click anywhere on the page → burst of coloured particles from click point.
// Fields:
//   count    — particles per click (default 14)
//   colours  — array of hex colours
//   size     — particle diameter px (default 8)
//   duration — animation ms (default 700)
//   gravity  — downward pull factor (default 1.2)
_RENDERERS['particle_burst'] = function(b) {
  var count    = b.count    || 14;
  var colours  = b.colours  || ['#6366f1','#8b5cf6','#ec4899','#f59e0b','#34d399','#60a5fa'];
  var psize    = b.size     || 8;
  var duration = b.duration || 700;
  var gravity  = b.gravity  !== undefined ? b.gravity : 1.2;
  var half     = Math.floor(psize / 2);

  return '<script>(function(){' +
    'if(window.__a2uiBurst)return;window.__a2uiBurst=true;' +
    'var C=' + JSON.stringify(colours) + ';' +
    'var N=' + count + ',D=' + duration + ',G=' + gravity + ',S=' + psize + ',H=' + half + ';' +
    'window.addEventListener("click",function(e){' +
      'for(var i=0;i<N;i++){' +
        '(function(){' +
          'var p=document.createElement("div");' +
          'var angle=Math.random()*Math.PI*2;' +
          'var speed=40+Math.random()*90;' +
          'var vx=Math.cos(angle)*speed,vy=Math.sin(angle)*speed;' +
          'p.style.cssText="position:fixed;pointer-events:none;z-index:9999;border-radius:50%;' +
            'width:"+S+"px;height:"+S+"px;background:"+C[Math.floor(Math.random()*C.length)]+";"+ ' +
            '"left:"+(e.clientX-H)+"px;top:"+(e.clientY-H)+"px;";' +
          'document.body.appendChild(p);' +
          'var start=null;' +
          'requestAnimationFrame(function tick(ts){' +
            'if(!start)start=ts;' +
            'var t=Math.min(1,(ts-start)/D);' +
            'var ease=1-Math.pow(1-t,3);' +
            'p.style.transform="translate("+(vx*ease).toFixed(1)+"px,"+(vy*ease+G*speed*t*t).toFixed(1)+"px)";' +
            'p.style.opacity=1-t;' +
            'if(t<1)requestAnimationFrame(tick);else p.remove();' +
          '});' +
        '})();' +
      '}' +
    '});' +
  '})();<\/script>';
};

// ── spotlight_cursor ──────────────────────────────────────────────────────────
// Dark overlay with a circular cutout that follows the cursor — torch effect.
// Fields:
//   radius    — spotlight radius px (default 180)
//   darkness  — overlay opacity 0–1 (default 0.82)
//   colour    — overlay colour (default #000)
//   soft_edge — feather px beyond radius (default 60)
_RENDERERS['spotlight_cursor'] = function(b) {
  var radius    = b.radius    || 180;
  var darkness  = b.darkness  !== undefined ? b.darkness : 0.82;
  var colour    = b.colour    || '#000';
  var soft      = b.soft_edge !== undefined ? b.soft_edge : 60;
  var outer     = radius + soft;

  return '<script>(function(){' +
    'if(window.__a2uiSpotlight)return;window.__a2uiSpotlight=true;' +
    'var el=document.createElement("div");' +
    'el.style.cssText="position:fixed;inset:0;pointer-events:none;z-index:8900;' +
      'background:' + colour + ';opacity:' + darkness + ';transition:opacity 0.4s;";' +
    'document.body.appendChild(el);' +
    'function setMask(x,y){' +
      'var m="radial-gradient(circle at "+x+"px "+y+"px,' +
        'transparent ' + radius + 'px,rgba(0,0,0,0.6) ' + outer + 'px,black ' + (outer + 20) + 'px)";' +
      'el.style.webkitMaskImage=m;' +
      'el.style.maskImage=m;' +
    '}' +
    'setMask(-600,-600);' +
    'window.addEventListener("mousemove",function(e){setMask(e.clientX,e.clientY);});' +
  '})();<\/script>';
};

// ── tilt_card ─────────────────────────────────────────────────────────────────
// A card that tilts in 3D perspective as the cursor moves across it.
// Fields:
//   content  — inner HTML rendered inside the card
//   title    — optional heading
//   max_tilt — max rotation degrees (default 14)
//   glare    — show glare highlight (default true)
//   accent   — glare colour (default rgba(255,255,255,0.15))
//   padding  — inner padding (default 28px)
_RENDERERS['tilt_card'] = function(b) {
  var maxTilt = b.max_tilt !== undefined ? b.max_tilt : 14;
  var glare   = b.glare   !== false;
  var accent  = b.accent  || 'rgba(255,255,255,0.15)';
  var padding = b.padding || '28px';
  var title   = b.title   || '';
  var content = b.content || '<p style="margin:0;font-size:0.9rem;opacity:0.8;">Move your cursor over this card.</p>';
  var uid     = 'tlt' + Math.random().toString(36).substr(2, 6);

  var glareHtml = glare
    ? '<div id="' + uid + 'g" style="position:absolute;inset:0;border-radius:inherit;pointer-events:none;opacity:0;' +
      'background:radial-gradient(circle at 50% 50%,' + _esc(accent) + ' 0%,transparent 60%);transition:opacity 0.2s;"></div>'
    : '';

  var titleHtml = title
    ? '<div style="font-size:1rem;font-weight:700;margin-bottom:12px;color:var(--text);">' + _esc(title) + '</div>'
    : '';

  return '<div id="' + uid + '" style="position:relative;border-radius:16px;padding:' + _esc(padding) + ';' +
    'background:var(--surface2,#1e2235);border:1px solid var(--border,#334155);' +
    'transform-style:preserve-3d;transform:perspective(800px) rotateX(0deg) rotateY(0deg);' +
    'transition:transform 0.15s ease,box-shadow 0.15s ease;' +
    'box-shadow:0 4px 24px rgba(0,0,0,0.15);cursor:default;overflow:hidden;">' +
    glareHtml +
    titleHtml +
    content +
  '</div>' +
  '<script>(function(){' +
    'var el=document.getElementById("' + uid + '");' +
    'var gl=document.getElementById("' + uid + 'g");' +
    'if(!el)return;' +
    'var T=' + maxTilt + ';' +
    'el.addEventListener("mousemove",function(e){' +
      'var r=el.getBoundingClientRect();' +
      'var nx=(e.clientX-r.left)/r.width-0.5;' +  // -0.5 to 0.5
      'var ny=(e.clientY-r.top)/r.height-0.5;' +
      'el.style.transform="perspective(800px) rotateY("+(nx*T*2).toFixed(2)+"deg) rotateX("+(-ny*T*2).toFixed(2)+"deg)";' +
      'el.style.boxShadow="'+(maxTilt > 0 ? '' : '')+'"+(-nx*20)+"px "+(-ny*20)+"px 40px rgba(0,0,0,0.25)";' +
      'if(gl){' +
        'gl.style.opacity="1";' +
        'gl.style.background="radial-gradient(circle at "+(nx*100+50)+"% "+(ny*100+50)+"%,' + _esc(accent) + ' 0%,transparent 60%)";' +
      '}' +
    '});' +
    'el.addEventListener("mouseleave",function(){' +
      'el.style.transform="perspective(800px) rotateX(0deg) rotateY(0deg)";' +
      'el.style.boxShadow="0 4px 24px rgba(0,0,0,0.15)";' +
      'if(gl)gl.style.opacity="0";' +
    '});' +
  '})();<\/script>';
};

// ── cursor_trail ──────────────────────────────────────────────────────────────
// Fading dot trail that follows the cursor with a worm-like lag.
// Fields:
//   length   — number of trail dots (default 16)
//   colour   — dot colour (default #6366f1)
//   size     — lead dot size px (default 10)
//   speed    — lerp factor per dot (default 0.35)
_RENDERERS['cursor_trail'] = function(b) {
  var length  = b.length || 16;
  var colour  = b.colour || '#6366f1';
  var size    = b.size   || 10;
  var speed   = b.speed  !== undefined ? b.speed : 0.35;

  return '<script>(function(){' +
    'if(window.__a2uiTrail)return;window.__a2uiTrail=true;' +
    'var N=' + length + ',C="' + colour.replace(/"/g,'\\"') + '",S=' + size + ',SPD=' + speed + ';' +
    'var pts=[];' +
    'for(var i=0;i<N;i++){' +
      'var d=document.createElement("div");' +
      'var sc=1-(i/N)*0.7;' +
      'var op=1-(i/N)*0.85;' +
      'd.style.cssText="position:fixed;pointer-events:none;z-index:9001;border-radius:50%;' +
        'width:"+(S*sc)+"px;height:"+(S*sc)+"px;background:"+C+";"+ ' +
        '"opacity:"+op+";transform:translate(-50%,-50%);will-change:left,top;top:-300px;left:-300px;";' +
      'document.body.appendChild(d);' +
      'pts.push({el:d,x:-300,y:-300});' +
    '}' +
    'var mx=-300,my=-300;' +
    'window.addEventListener("mousemove",function(e){mx=e.clientX;my=e.clientY;});' +
    '(function loop(){' +
      'pts[0].x+=(mx-pts[0].x)*SPD;' +
      'pts[0].y+=(my-pts[0].y)*SPD;' +
      'for(var i=1;i<N;i++){' +
        'pts[i].x+=(pts[i-1].x-pts[i].x)*SPD;' +
        'pts[i].y+=(pts[i-1].y-pts[i].y)*SPD;' +
      '}' +
      'for(var i=0;i<N;i++){' +
        'pts[i].el.style.left=pts[i].x.toFixed(1)+"px";' +
        'pts[i].el.style.top=pts[i].y.toFixed(1)+"px";' +
      '}' +
      'requestAnimationFrame(loop);' +
    '})();' +
  '})();<\/script>';
};
