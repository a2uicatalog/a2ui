// atoms_atc.gs — atc_vectoring: playable approach control.
//
// Spec: a2ui-private/spec/atc-vectoring-v0.1.md
//
// DESIGN NOTES (the decisions, so they are not re-litigated by inspection):
//
//  • FULLSCREEN-ONLY, and it says so. Separation IS the game; at 22nm on a
//    ~560px inline card 3nm is a handful of pixels. Inline is not a degraded
//    experience here, it is an unplayable one, so the board REFUSES to render
//    inline and shows an explanation instead. It keys off html.a2ui-inline —
//    the same host-display-mode hook added 2026-08-01 for the deck clamp — so
//    the refusal is driven by what the host actually reported, not a guess.
//    Only hub and playbook trigger _maybeRequestFullscreen, so this atom must
//    be composed INSIDE A PLAYBOOK or it will never be offered the mode.
//
//  • STATIC PLAN VIEW. airspace_command_deck's camera is cinematic (intro
//    zoom that changes NM scale mid-animation, LOCKED cycling on a timer).
//    Every part of that is hostile to continuous spatial judgement, so none
//    of it is here: fixed scale, north-up, selection owned by the player.
//
//  • NOT ISOMETRIC. Foreshortening destroys the one judgement the game is
//    about — is that 3nm or 6nm. Plan view for the same reason real radar is.
//
//  • The 60-SECOND PREDICTED VECTOR is not polish. Without it a conflict is
//    only visible once it already exists, which makes the game unfair rather
//    than hard.
//
//  • SESSION-ONLY. No localStorage: it throws on an opaque-origin sandbox
//    (same class as the window.history bug fixed 2026-08-01 — the object
//    exists, the ACCESS throws). Score dies with the view, by design.
//
//  • NO KEYBOARD. Chat hosts capture keys. Taps only, finger-sized targets.
//
//  • NO VIEWPORT UNITS anywhere except the fullscreen path. An MCP Apps card
//    auto-fits its iframe to content, so vh inside it is circular.

_RENDERERS['atc_vectoring'] = function (b) {
  var uid = 'atc' + Math.random().toString(36).substr(2, 6);

  var zoom         = Number(b.zoom) || 22;                  // nm radius shown
  var difficulty   = b.difficulty || 'standard';
  var runway       = String(b.ils_runway || '32L');
  var interceptAlt = Number(b.ils_intercept_alt) || 3000;
  var grace        = Number(b.conflict_grace_s) || 8;
  var roundSec     = Number(b.round_seconds) || 180;
  var weatherSrc   = b.weather_source || '';
  var title        = b.title || 'LFBO APPROACH — VECTORING';

  // Runway designator -> localiser course. "32L" -> 320°.
  var rwyNum = parseInt(runway.replace(/[^0-9]/g, ''), 10);
  var course = (isNaN(rwyNum) ? 32 : rwyNum) * 10 % 360;

  // ── Traffic ────────────────────────────────────────────────────────────
  // Supplied verbatim when the caller gives it (the agent authors the
  // scenario); otherwise generated from difficulty so a bare call still
  // produces a playable round.
  var COUNTS = { training: 3, standard: 5, busy: 7 };
  var fleet = b.aircraft;
  if (!fleet || !fleet.length) {
    var n = COUNTS[difficulty] || 5;
    var CALLS = ['AFR6129', 'EZY4218', 'RYR109B', 'IBE3421', 'AFR7734',
                 'TAP456', 'VLG2201', 'BAW382', 'DLH98C'];
    var TYPES = ['A320', 'A319', 'B738', 'A321', 'B777', 'A20N', 'A332'];
    fleet = [];
    for (var i = 0; i < n; i++) {
      // Spread entry bearings so the opening picture is never degenerate,
      // then jitter so successive rounds differ.
      var brg = Math.round((i * (360 / n) + Math.random() * 25) % 360);
      fleet.push({
        callsign: CALLS[i % CALLS.length],
        type: TYPES[i % TYPES.length],
        bearing: brg,
        dist_nm: Math.round(zoom * 0.55 + Math.random() * zoom * 0.35),
        alt_ft: 4000 + Math.round(Math.random() * 5) * 1000,
        speed_kt: 210 + Math.round(Math.random() * 8) * 10
      });
    }
  }

  var FLEET_JSON = JSON.stringify(fleet.map(function (f) {
    return {
      c: String(f.callsign || '????'),
      t: String(f.type || 'A320'),
      brg: Number(f.bearing) || 0,
      d: Number(f.dist_nm) || 15,
      alt: Number(f.alt_ft) || 5000,
      spd: Number(f.speed_kt) || 240
    };
  }));

  var CFG = JSON.stringify({
    zoom: zoom, course: course, interceptAlt: interceptAlt,
    grace: grace, roundSec: roundSec, runway: runway
  });

  // ── Styles ─────────────────────────────────────────────────────────────
  // Fullscreen breakout mirrors airspace_command_deck's, plus the inline
  // refusal: board hidden, notice shown, when the host reports inline.
  var css = '<style>' +
    'html,body{margin:0;padding:0;overflow:hidden;}' +
    '.asw-page{max-width:none!important;padding:0!important;margin:0!important;}' +
    '.asw-page>h1{display:none!important;}' +
    '#' + uid + 'notice{display:none;}' +
    'html.a2ui-inline #' + uid + 'board{display:none!important;}' +
    'html.a2ui-inline #' + uid + 'notice{display:flex!important;}' +
    '#' + uid + 'board{position:relative;width:100%;height:100vh;background:#050810;' +
      'font-family:\'Courier New\',monospace;overflow:hidden;}' +
    '#' + uid + 'notice{height:320px;background:#050810;color:#e2e8f0;' +
      'align-items:center;justify-content:center;flex-direction:column;gap:14px;' +
      'font-family:\'Courier New\',monospace;text-align:center;padding:28px;box-sizing:border-box;}' +
    '#' + uid + 'cmd button{font-family:\'Courier New\',monospace;font-size:0.78rem;' +
      'font-weight:700;padding:14px 0;min-width:76px;flex:1 1 0;border:none;border-radius:6px;' +
      'background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.55);cursor:pointer;' +
      'letter-spacing:0.06em;transition:background .12s,color .12s;}' +
    '#' + uid + 'cmd button:enabled{background:rgba(0,242,255,0.16);color:#00f2ff;}' +
    '#' + uid + 'cmd button.land:enabled{background:rgba(0,255,65,0.18);color:#00ff41;}' +
    '</style>';

  // ── Markup ─────────────────────────────────────────────────────────────
  var html = css +
    '<div id="' + uid + 'notice">' +
      '<div style="color:#f59e0b;font-size:0.95rem;font-weight:700;letter-spacing:0.12em;">' +
        '⚠ NEEDS FULL SCREEN</div>' +
      '<div style="font-size:0.8rem;line-height:1.6;max-width:520px;opacity:0.75;">' +
        'Separation is the whole game, and at ' + zoom + 'nm in an inline card ' +
        '3nm is a few pixels wide — the board would be unreadable rather than hard. ' +
        'This atom renders only when the host grants full screen. Compose it inside ' +
        'a <b>playbook</b>, which is what requests the mode.</div>' +
    '</div>' +
    '<div id="' + uid + 'board">' +
      '<canvas id="' + uid + 'c" style="display:block;width:100%;height:100%;"></canvas>' +
      // chyron
      '<div style="position:absolute;top:14px;left:18px;pointer-events:none;">' +
        '<div style="color:#00f2ff;font-size:0.95rem;font-weight:700;letter-spacing:0.1em;">' +
          _esc(title) + '</div>' +
        '<div id="' + uid + 'sub" style="color:rgba(255,255,255,0.5);font-size:0.68rem;margin-top:3px;">' +
          'RWY ' + _esc(runway) + ' · INTERCEPT ' + interceptAlt + 'FT · ' + zoom + 'NM</div>' +
      '</div>' +
      // scoreboard
      '<div id="' + uid + 'score" style="position:absolute;top:14px;right:18px;text-align:right;' +
        'color:rgba(255,255,255,0.75);font-size:0.7rem;line-height:1.7;pointer-events:none;"></div>' +
      // selected-aircraft HUD
      '<div id="' + uid + 'hud" style="position:absolute;left:18px;bottom:96px;min-width:210px;' +
        'background:rgba(0,0,0,0.66);border:1px solid rgba(0,242,255,0.22);border-radius:8px;' +
        'padding:10px 14px;color:#e2e8f0;font-size:0.7rem;line-height:1.7;pointer-events:none;">' +
        '<span style="opacity:0.55;">NO AIRCRAFT SELECTED — TAP A TARGET</span></div>' +
      // command bar
      '<div id="' + uid + 'cmd" style="position:absolute;left:50%;transform:translateX(-50%);' +
        'bottom:20px;display:flex;gap:8px;width:min(640px,92vw);' +
        'background:rgba(0,0,0,0.8);border:1px solid rgba(0,242,255,0.18);border-radius:10px;' +
        'padding:8px;backdrop-filter:blur(12px);">' +
        '<button data-a="l" disabled>&#9664; L20</button>' +
        '<button data-a="r" disabled>R20 &#9654;</button>' +
        '<button data-a="u" disabled>&#9650; CLIMB</button>' +
        '<button data-a="d" disabled>&#9660; DESCEND</button>' +
        '<button data-a="k" class="land" disabled>&#9992; CLEARED</button>' +
      '</div>' +
    '</div>';

  // ── Game ───────────────────────────────────────────────────────────────
  var js = '<script>(function(){' +
    'var CFG=' + CFG + ',SEED=' + FLEET_JSON + ';' +
    'var board=document.getElementById("' + uid + 'board");' +
    'var c=document.getElementById("' + uid + 'c"),ctx=c.getContext("2d");' +
    'var hud=document.getElementById("' + uid + 'hud");' +
    'var scoreEl=document.getElementById("' + uid + 'score");' +
    'var cmd=document.getElementById("' + uid + 'cmd");' +
    'var subEl=document.getElementById("' + uid + 'sub");' +
    'var W=0,H=0,CX=0,CY=0,NM=8;' +

    // Aircraft state. hdg/tgtHdg and alt/tgtAlt are separate so commands are
    // instructions the aircraft flies out, not teleports.
    'var AC=SEED.map(function(s){' +
      'var rad=s.brg*Math.PI/180;' +
      'return {c:s.c,t:s.t,x:Math.sin(rad)*s.d,y:Math.cos(rad)*s.d,' +
        'hdg:(s.brg+180)%360,tgt:(s.brg+180)%360,alt:s.alt,talt:s.alt,' +
        'spd:s.spd,trail:[],landed:false,lost:false};' +
    '});' +
    'var SEL=null,landed=0,lostAc=0,conflictS=0,t0=Date.now(),over=false,last=Date.now();' +

    'function norm(a){while(a<0)a+=360;return a%360;}' +
    'function delta(a,b){var d=norm(a-b);return d>180?d-360:d;}' +

    'function resize(){' +
      'var w=c.offsetWidth||700,h=c.offsetHeight||520;' +
      'if(w!==c.width||h!==c.height){c.width=w;c.height=h;}' +
      'W=c.width;H=c.height;CX=W/2;CY=H/2;' +
      'NM=Math.min(W,H)*0.46/CFG.zoom;' +           // px per nm — fits the ring
    '}' +
    'function px(a){return {x:CX+a.x*NM,y:CY-a.y*NM};}' +

    // ── advance ──
    'function step(dt){' +
      'for(var i=0;i<AC.length;i++){var a=AC[i];if(a.landed||a.lost)continue;' +
        // standard-rate turn, 3 deg/s
        'var dh=delta(a.tgt,a.hdg);var mx=3*dt;' +
        'if(Math.abs(dh)<=mx)a.hdg=a.tgt;else a.hdg=norm(a.hdg+(dh>0?mx:-mx));' +
        // 1500 fpm
        'var da=a.talt-a.alt;var ma=25*dt*60;' +
        'if(Math.abs(da)<=ma)a.alt=a.talt;else a.alt+=(da>0?ma:-ma);' +
        // position: nm travelled = kt * hours
        'var nmps=a.spd/3600;var r=a.hdg*Math.PI/180;' +
        'a.x+=Math.sin(r)*nmps*dt;a.y+=Math.cos(r)*nmps*dt;' +
        'a.trail.push({x:a.x,y:a.y});if(a.trail.length>90)a.trail.shift();' +
        'if(Math.sqrt(a.x*a.x+a.y*a.y)>CFG.zoom*1.12){a.lost=true;lostAc++;if(SEL===a.c)SEL=null;}' +
      '}' +
    '}' +

    // ── conflicts: 3nm lateral AND under 1000ft vertical, exactly the rule
    // airspace_command_deck already draws.
    'function conflicts(){' +
      'var out=[];' +
      'for(var i=0;i<AC.length;i++){for(var j=i+1;j<AC.length;j++){' +
        'var p=AC[i],q=AC[j];if(p.landed||q.landed||p.lost||q.lost)continue;' +
        'var dx=p.x-q.x,dy=p.y-q.y;var d=Math.sqrt(dx*dx+dy*dy);' +
        'if(d<3&&Math.abs(p.alt-q.alt)<1000)out.push({p:p,q:q,d:d});' +
      '}}' +
      'return out;' +
    '}' +

    // ── ILS gate: lined up on the localiser, inside the funnel, at height.
    'function onIls(a){' +
      'var brg=norm(Math.atan2(a.x,a.y)*180/Math.PI);' +          // bearing FROM field
      'var appr=norm(CFG.course+180);' +                           // aircraft sits on the reciprocal
      'var d=Math.sqrt(a.x*a.x+a.y*a.y);' +
      'return Math.abs(delta(brg,appr))<10 && d>2.5 && d<12 &&' +
        'Math.abs(delta(a.hdg,CFG.course))<30 &&' +
        'Math.abs(a.alt-CFG.interceptAlt)<600;' +
    '}' +

    // ── draw ──
    'function altColour(alt){' +
      'if(alt<3000)return "#00ff41";if(alt<6000)return "#00f2ff";' +
      'if(alt<9000)return "#ffffff";return "#94a3b8";' +
    '}' +
    'function draw(){' +
      'ctx.clearRect(0,0,W,H);' +
      // range rings
      'ctx.strokeStyle="rgba(0,242,255,0.13)";ctx.lineWidth=1;' +
      'for(var r=5;r<=CFG.zoom;r+=5){ctx.beginPath();ctx.arc(CX,CY,r*NM,0,Math.PI*2);ctx.stroke();' +
        'ctx.fillStyle="rgba(0,242,255,0.28)";ctx.font="9px \'Courier New\'";ctx.textAlign="left";' +
        'ctx.fillText(r+"nm",CX+4,CY-r*NM-3);}' +
      // localiser funnel
      'var ar=norm(CFG.course+180)*Math.PI/180;' +
      'ctx.save();ctx.strokeStyle="rgba(0,255,65,0.35)";ctx.setLineDash([5,5]);' +
      '[-10,0,10].forEach(function(off){' +
        'var rr=(norm(CFG.course+180+off))*Math.PI/180;' +
        'ctx.beginPath();ctx.moveTo(CX,CY);' +
        'ctx.lineTo(CX+Math.sin(rr)*12*NM,CY-Math.cos(rr)*12*NM);ctx.stroke();});' +
      'ctx.setLineDash([]);ctx.restore();' +
      // field
      'ctx.fillStyle="#00ff41";ctx.beginPath();ctx.arc(CX,CY,4,0,Math.PI*2);ctx.fill();' +
      'ctx.font="bold 9px \'Courier New\'";ctx.textAlign="center";' +
      'ctx.fillText("RWY "+CFG.runway,CX,CY+16);' +
      // conflict lines
      'var cf=conflicts();' +
      'ctx.save();ctx.strokeStyle="#f59e0b";ctx.lineWidth=1.5;ctx.setLineDash([4,4]);' +
      'cf.forEach(function(k){var a=px(k.p),bb=px(k.q);' +
        'ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(bb.x,bb.y);ctx.stroke();' +
        'ctx.fillStyle="#f59e0b";ctx.font="bold 9px \'Courier New\'";ctx.textAlign="center";' +
        'ctx.fillText("\\u26a1 "+k.d.toFixed(1)+"nm",(a.x+bb.x)/2,(a.y+bb.y)/2-8);});' +
      'ctx.setLineDash([]);ctx.restore();' +
      // aircraft
      'AC.forEach(function(a){if(a.landed||a.lost)return;' +
        'var p=px(a),col=altColour(a.alt),sel=(SEL===a.c);' +
        // trail
        'ctx.strokeStyle=col;ctx.globalAlpha=0.28;ctx.lineWidth=1;ctx.beginPath();' +
        'a.trail.forEach(function(tp,ix){var q=px(tp);' +
          'if(ix===0)ctx.moveTo(q.x,q.y);else ctx.lineTo(q.x,q.y);});ctx.stroke();ctx.globalAlpha=1;' +
        // 60s predicted vector — the aid that makes vectoring possible
        'var nmps=a.spd/3600,rr=a.hdg*Math.PI/180;' +
        'var fx=a.x+Math.sin(rr)*nmps*60,fy=a.y+Math.cos(rr)*nmps*60;var f=px({x:fx,y:fy});' +
        'ctx.strokeStyle=col;ctx.globalAlpha=0.5;ctx.beginPath();' +
        'ctx.moveTo(p.x,p.y);ctx.lineTo(f.x,f.y);ctx.stroke();ctx.globalAlpha=1;' +
        // blip
        'ctx.fillStyle=col;ctx.fillRect(p.x-3,p.y-3,6,6);' +
        'if(sel){ctx.strokeStyle="#fff";ctx.lineWidth=1.5;' +
          'ctx.strokeRect(p.x-9,p.y-9,18,18);}' +
        // label: callsign / altitude always visible — plan view cannot imply it
        'ctx.fillStyle=sel?"#fff":col;ctx.font="bold 9px \'Courier New\'";ctx.textAlign="left";' +
        'ctx.fillText(a.c,p.x+11,p.y-1);' +
        'ctx.fillStyle="rgba(255,255,255,0.6)";ctx.font="8px \'Courier New\'";' +
        'ctx.fillText(Math.round(a.alt/100)+" "+Math.round(a.spd),p.x+11,p.y+9);' +
        'if(onIls(a)){ctx.fillStyle="#00ff41";ctx.font="bold 8px \'Courier New\'";' +
          'ctx.fillText("ILS",p.x+11,p.y+19);}' +
      '});' +
    '}' +

    // ── HUD + scoreboard ──
    'function sel(){for(var i=0;i<AC.length;i++)if(AC[i].c===SEL)return AC[i];return null;}' +
    'function refresh(){' +
      'var a=sel();' +
      'var btns=cmd.querySelectorAll("button");' +
      'for(var i=0;i<btns.length;i++){' +
        'var act=btns[i].getAttribute("data-a");' +
        'btns[i].disabled=over||!a||(act==="k"&&!onIls(a));}' +
      'if(!a){hud.innerHTML="<span style=\\"opacity:0.55;\\">NO AIRCRAFT SELECTED — TAP A TARGET</span>";}' +
      'else{hud.innerHTML="<b style=\\"color:#00f2ff;\\">"+a.c+"</b> "+a.t+"<br>"+' +
        '"ALT "+Math.round(a.alt)+" \\u2192 "+a.talt+"<br>"+' +
        '"HDG "+Math.round(a.hdg)+"\\u00b0 \\u2192 "+Math.round(a.tgt)+"\\u00b0<br>"+' +
        '"SPD "+a.spd+"kt"+(onIls(a)?"<br><b style=\\"color:#00ff41;\\">ESTABLISHED — CLEAR TO LAND</b>":"");}' +
      'var left=Math.max(0,CFG.roundSec-Math.floor((Date.now()-t0)/1000));' +
      'var live=AC.filter(function(a){return !a.landed&&!a.lost;}).length;' +
      'scoreEl.innerHTML="LANDED <b style=\\"color:#00ff41;\\">"+landed+"</b>"+' +
        "\"<br>AIRBORNE \"+live+" +
        '"<br>CONFLICT <b style=\\"color:#f59e0b;\\">"+Math.floor(conflictS)+"s</b>"+' +
        '"<br>TIME "+Math.floor(left/60)+":"+("0"+(left%60)).slice(-2);' +
      'if(!over&&(left<=0||live===0)){' +
        'over=true;' +
        'var pts=landed*100-Math.floor(conflictS)*5-lostAc*50+Math.floor(left);' +
        'hud.innerHTML="<b style=\\"color:#00f2ff;\\">ROUND COMPLETE</b><br>"+' +
          '"Landed "+landed+" \\u00b7 Lost "+lostAc+"<br>"+' +
          '"Conflict "+Math.floor(conflictS)+"s<br><b>SCORE "+pts+"</b>";' +
        'refreshBtns();}' +
    '}' +
    'function refreshBtns(){var bs=cmd.querySelectorAll("button");' +
      'for(var i=0;i<bs.length;i++)bs[i].disabled=true;}' +

    // ── input: tap the board to select the nearest aircraft ──
    'c.addEventListener("click",function(e){' +
      'if(over)return;' +
      'var r=c.getBoundingClientRect();' +
      'var mx=e.clientX-r.left,my=e.clientY-r.top,best=null,bd=1e9;' +
      'AC.forEach(function(a){if(a.landed||a.lost)return;var p=px(a);' +
        'var d=Math.sqrt((p.x-mx)*(p.x-mx)+(p.y-my)*(p.y-my));' +
        'if(d<bd){bd=d;best=a;}});' +
      'SEL=(best&&bd<40)?best.c:null;refresh();' +
    '});' +
    'cmd.addEventListener("click",function(e){' +
      'var btn=e.target.closest?e.target.closest("button"):null;' +
      'if(!btn||btn.disabled)return;var a=sel();if(!a)return;' +
      'var act=btn.getAttribute("data-a");' +
      'if(act==="l")a.tgt=norm(a.tgt-20);' +
      'else if(act==="r")a.tgt=norm(a.tgt+20);' +
      'else if(act==="u")a.talt=Math.min(12000,a.talt+1000);' +
      'else if(act==="d")a.talt=Math.max(1000,a.talt-1000);' +
      'else if(act==="k"&&onIls(a)){a.landed=true;landed++;SEL=null;}' +
      'refresh();' +
    '});' +

    // ── live weather into the subtitle, when a metar_feed is wired ──
    (weatherSrc ?
      'window.A2UI_DATA=window.A2UI_DATA||{};window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
      '(function(){function wx(d){if(!d)return;' +
        'subEl.textContent="RWY ' + _esc(runway) + ' \\u00b7 INTERCEPT ' + interceptAlt + 'FT \\u00b7 "+' +
          '(d.wind||"")+" "+(d.temp||"")+" "+(d.qnh||"");}' +
        'var prev=window.A2UI_CALLBACKS["' + _esc(weatherSrc) + '"];' +
        'window.A2UI_CALLBACKS["' + _esc(weatherSrc) + '"]=function(d){wx(d);if(typeof prev==="function")prev(d);};' +
        'if(window.A2UI_DATA["' + _esc(weatherSrc) + '"])wx(window.A2UI_DATA["' + _esc(weatherSrc) + '"]);' +
      '})();' : '') +

    // ── loop ──
    'function frame(){' +
      'var now=Date.now(),dt=Math.min(0.25,(now-last)/1000);last=now;' +
      'resize();' +
      'if(!over){step(dt);conflictS+=conflicts().length?dt:0;}' +
      'draw();refresh();' +
      'requestAnimationFrame(frame);' +
    '}' +
    'resize();refresh();requestAnimationFrame(frame);' +
    '})();<\/script>';

  return html + js;
};
