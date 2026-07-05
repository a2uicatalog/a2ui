// atoms_airspace.gs — Toulouse TMA Airspace Command Deck
// Canvas radar + HTML/CSS overlay for crisp chyron and ticker text.
// Surfaces: G W
//
// DATA BINDING:
//   data_source    — name of an adsb_feed atom to subscribe to for live flight positions
//   weather_source — name of a metar_feed atom to subscribe to for live weather
//   When feeds are present the atom registers window.A2UI_CALLBACKS[name] and the
//   data atoms dispatch on load and on each refresh interval.
//   Falls back to simulated flights if no data_source is set.

// ── airspace_command_deck ─────────────────────────────────────────────────────
//   chyron_title      — top-left headline
//   chyron_subtitle   — top-left subtitle (supports interpolated {{tags}})
//   ticker_text       — scrolling bottom bar text
//   ticker_speed      — scroll speed px/s (default 45)
//   panel_type        — 'supervisor' | 'target' | '' (default: clean deck)
//   panel_title       — HUD panel heading
//   lockedCallsign    — highlight + reticle on this callsign (target panel)
//   zoom              — nm radius shown (default 35)
//   height            — canvas height px | 'fullscreen'
//   data_source       — adsb_feed name to subscribe to for live flights
//   weather_source    — metar_feed name to subscribe to for live weather panel
//   show_slate        — render calibration slate instead of radar
//   slate_title / slate_description
//   poll_question / poll_options / poll_values
_RENDERERS['airspace_command_deck'] = function(b) {
  var uid           = 'asd' + Math.random().toString(36).substr(2, 6);
  var fullscreen    = b.height === 'fullscreen';
  var h             = fullscreen ? '100vh' : (b.height || 520) + 'px';
  var zoom          = b.zoom           || 35;
  var zoomIn        = b.zoom_in        || 0;   // 0 = no animation
  var zoomPeriod    = b.zoom_period    || 20000; // ms for one full cycle
  var locked        = b.lockedCallsign || '';
  var panelType     = b.panel_type     || '';
  var panelTitle    = b.panel_title    || '';
  var dataSource    = b.data_source    || '';
  var weatherSource = b.weather_source || '';
  var chyronTitle  = b.chyron_title    || 'LFBO TMA';
  var chyronSub    = b.chyron_subtitle || 'Toulouse Blagnac Approach Control';
  var tickerText   = b.ticker_text  || '✈ TOULOUSE AIRSPACE ✈';
  var tickerSpeed  = b.ticker_speed || 45;
  var showSlate    = b.show_slate   || false;
  var slateTitle   = b.slate_title  || 'CALIBRATING';
  var slateSub     = b.slate_description || 'Booting radar...';
  var pollQ        = b.poll_question || '';
  var pollOpts     = b.poll_options  || [];
  var pollVals     = b.poll_values   || [];

  // ── Simulated flights ─────────────────────────────────────────────────────
  // Each flight: {callsign, type, alt ft, spd kt, bearing° from LFBO, dist nm, status, colour}
  // Bearing 0° = north. Flights inside 35nm TMA moving toward the airport.
  var FLIGHTS = JSON.stringify([
    {c:'AFR6129', t:'A320', alt:3200,  spd:210, brg:148, dist:12, status:'ILS 32L',  col:'#00f2ff'},
    {c:'EZY4218', t:'A319', alt:4500,  spd:240, brg:88,  dist:19, status:'APPROACH', col:'#00ff41'},
    {c:'RYR109B', t:'B738', alt:6000,  spd:280, brg:225, dist:24, status:'DESCENT',  col:'#ffffff'},
    {c:'IBE3421', t:'A321', alt:8500,  spd:310, brg:55,  dist:30, status:'EN-ROUTE', col:'#ffffff'},
    {c:'AFR7734', t:'B777', alt:2100,  spd:180, brg:165, dist:7,  status:'FINAL',    col:'#00ff41'},
    {c:'TAP456',  t:'A20N', alt:5500,  spd:260, brg:272, dist:22, status:'VECTOR',   col:'#ffffff'},
    {c:'VLG2201', t:'A320', alt:7200,  spd:295, brg:310, dist:28, status:'DESCENT',  col:'#ffffff'}
  ]);

  // ── Slate mode ────────────────────────────────────────────────────────────
  if (showSlate) {
    return '<div style="background:#050810;border-radius:' + (fullscreen?'0':'10px') + ';height:' + h + ';' +
      'display:flex;flex-direction:column;align-items:center;justify-content:center;' +
      'font-family:\'Courier New\',monospace;position:relative;overflow:hidden;">' +
      '<div style="color:#00f2ff;font-size:0.65rem;letter-spacing:0.25em;opacity:0.5;margin-bottom:32px;">A2UI · AIRSPACE COMMAND DECK · BOOT SEQUENCE</div>' +
      '<div style="font-size:clamp(1rem,2.5vw,1.4rem);font-weight:700;color:#00ff41;letter-spacing:0.12em;text-align:center;margin-bottom:12px;">' + _esc(slateTitle) + '</div>' +
      '<div style="font-size:0.78rem;color:#00f2ff;opacity:0.7;text-align:center;max-width:500px;">' + _esc(slateSub) + '</div>' +
      '<div id="' + uid + 'prog" style="margin-top:40px;width:280px;height:3px;background:#0a1628;border-radius:2px;overflow:hidden;">' +
        '<div id="' + uid + 'bar" style="height:100%;width:0%;background:#00f2ff;transition:width 0.1s linear;"></div>' +
      '</div>' +
      '<div id="' + uid + 'pct" style="margin-top:8px;font-size:0.65rem;color:#00f2ff;letter-spacing:0.15em;">0%</div>' +
      '<script>(function(){' +
        'var bar=document.getElementById("' + uid + 'bar");' +
        'var pct=document.getElementById("' + uid + 'pct");' +
        'var w=0;var t=setInterval(function(){' +
          'w+=Math.random()*3+0.5;if(w>100)w=100;' +
          'bar.style.width=w.toFixed(1)+"%";' +
          'pct.textContent=Math.round(w)+"%";' +
          'if(w>=100)clearInterval(t);' +
        '},80);' +
      '})();<\/script>' +
      '</div>';
  }

  // ── Poll overlay (if poll_question set) ──────────────────────────────────
  var pollHtml = '';
  if (pollQ && pollOpts.length > 0) {
    var totalVotes = 0;
    for (var pi = 0; pi < pollVals.length; pi++) totalVotes += (pollVals[pi] || 0);
    if (totalVotes === 0) totalVotes = 1;
    var pollRows = '';
    for (var pi = 0; pi < pollOpts.length; pi++) {
      var pct = Math.round(((pollVals[pi] || 0) / totalVotes) * 100);
      pollRows +=
        '<div style="margin-bottom:10px;">' +
        '<div style="font-size:0.7rem;color:rgba(255,255,255,0.75);margin-bottom:4px;">' + _esc(pollOpts[pi]) + '</div>' +
        '<div style="display:flex;align-items:center;gap:8px;">' +
        '<div style="flex:1;height:6px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">' +
        '<div style="width:' + pct + '%;height:100%;background:#00f2ff;border-radius:3px;box-shadow:0 0 8px #00f2ff88;"></div></div>' +
        '<span style="font-size:0.65rem;color:#00f2ff;width:28px;text-align:right;">' + pct + '%</span>' +
        '</div></div>';
    }
    pollHtml =
      '<div style="position:absolute;right:12px;bottom:44px;width:280px;' +
      'background:rgba(0,8,20,0.88);border:1px solid rgba(0,242,255,0.25);border-radius:8px;' +
      'padding:14px;backdrop-filter:blur(6px);">' +
      '<div style="font-size:0.65rem;color:#00f2ff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">' + _esc(pollQ) + '</div>' +
      pollRows +
      '<div style="font-size:0.6rem;color:rgba(255,255,255,0.25);margin-top:8px;">' + totalVotes + ' votes</div>' +
      '</div>';
  }

  // ── Supervisor panel ──────────────────────────────────────────────────────
  var panelHtml = '';
  if (panelType === 'supervisor') {
    panelHtml =
      '<div style="position:absolute;left:12px;bottom:44px;width:240px;' +
      'background:rgba(0,8,20,0.88);border:1px solid rgba(0,242,255,0.2);border-radius:8px;' +
      'padding:12px;font-family:\'Courier New\',monospace;">' +
      '<div style="font-size:0.6rem;color:#00f2ff;letter-spacing:0.12em;text-transform:uppercase;' +
      'border-bottom:1px solid rgba(0,242,255,0.15);padding-bottom:6px;margin-bottom:8px;">' + _esc(panelTitle) + '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 52px 38px 52px;gap:0 6px;' +
        'font-size:0.52rem;color:rgba(0,242,255,0.4);margin-bottom:6px;letter-spacing:0.08em;">' +
        '<span>FLIGHT</span><span>AIRLINE</span><span>FL</span><span>STATUS</span></div>' +
      '<div id="' + uid + 'flist" style="font-size:0.58rem;color:rgba(255,255,255,0.75);"></div>' +
      '</div>';
  }
  if (panelType === 'target') {
    panelHtml =
      '<div style="position:absolute;left:12px;bottom:44px;width:240px;' +
      'background:rgba(0,8,20,0.88);border:1px solid rgba(0,242,255,0.2);border-radius:8px;' +
      'padding:12px;font-family:\'Courier New\',monospace;">' +
      '<div style="font-size:0.6rem;color:#00f2ff;letter-spacing:0.12em;text-transform:uppercase;' +
      'border-bottom:1px solid rgba(0,242,255,0.15);padding-bottom:6px;margin-bottom:8px;">' + _esc(panelTitle) + '</div>' +
      '<canvas id="' + uid + 'iso" width="216" height="110" ' +
        'style="width:216px;height:110px;display:block;margin:0 auto 10px;border-radius:4px;' +
        'background:rgba(0,0,0,0.3);"></canvas>' +
      '<div id="' + uid + 'flist" style="font-size:0.58rem;color:rgba(255,255,255,0.75);"></div>' +
      '</div>';
  }

  // ── Full HTML structure ───────────────────────────────────────────────────
  var tickerDur = Math.round(tickerText.length * 0.18 / (tickerSpeed / 45)) + 's';

  return '<style>' +
    '@keyframes ' + uid + 'tk{from{transform:translateX(100vw);}to{transform:translateX(-100%);}}'  +
    '@keyframes ' + uid + 'blink{0%,100%{opacity:1;}50%{opacity:0.2;}}' +
    '@keyframes ' + uid + 'reticle{from{transform:translate(-50%,-50%) rotate(0deg);}to{transform:translate(-50%,-50%) rotate(360deg);}}' +
    '</style>' +
    '<div style="position:relative;background:#050810;border-radius:' + (fullscreen?'0':'10px') + ';overflow:hidden;height:' + h + ';font-family:\'Courier New\',monospace;">' +

    // Canvas — radar layer
    '<canvas id="' + uid + '" style="position:absolute;inset:0;width:100%;height:100%;"></canvas>' +

    // Chyron — top left
    '<div style="position:absolute;top:14px;left:14px;' +
      'background:rgba(0,0,0,0.6);border-left:2px solid #00f2ff;padding:8px 14px;border-radius:0 6px 6px 0;' +
      'backdrop-filter:blur(4px);">' +
      '<div style="font-size:clamp(0.75rem,1.8vw,1rem);font-weight:700;color:#00f2ff;letter-spacing:0.08em;text-transform:uppercase;">' + _esc(chyronTitle) + '</div>' +
      '<div id="' + uid + 'csub" style="font-size:0.65rem;color:rgba(255,255,255,0.55);letter-spacing:0.04em;margin-top:2px;">' + _esc(chyronSub) + '</div>' +
    '</div>' +

    // Weather panel + data status indicator — top right
    '<div style="position:absolute;top:14px;right:14px;display:flex;flex-direction:column;gap:6px;align-items:flex-end;">' +
      '<div id="' + uid + 'wx" style="' +
        'background:rgba(0,0,0,0.6);border:1px solid rgba(0,242,255,0.2);padding:8px 14px;border-radius:6px;' +
        'backdrop-filter:blur(4px);font-size:0.6rem;color:rgba(255,255,255,0.65);line-height:1.8;">' +
        '<div style="color:#00ff41;font-size:0.58rem;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">LFBO METAR</div>' +
        '<div>WIND &nbsp;<span style="color:#fff;" id="' + uid + 'wind">—</span></div>' +
        '<div>TEMP &nbsp;<span style="color:#fff;" id="' + uid + 'temp">—</span></div>' +
        '<div>QNH &nbsp;&nbsp;<span style="color:#fff;" id="' + uid + 'qnh">—</span></div>' +
      '</div>' +
      // Data source status pill — starts SIM/red, flips to LIVE/green when adsb_feed dispatches
      '<div id="' + uid + 'status" style="' +
        'display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:100px;' +
        'background:rgba(255,59,48,0.12);border:1px solid rgba(255,59,48,0.3);' +
        'font-family:\'Courier New\',monospace;font-size:0.58rem;letter-spacing:0.1em;color:#ff3b30;">' +
        '<span id="' + uid + 'sdot" style="width:6px;height:6px;border-radius:50%;' +
          'background:#ff3b30;box-shadow:0 0 6px #ff3b30;flex-shrink:0;"></span>' +
        '<span id="' + uid + 'slbl">SIM</span>' +
      '</div>' +
    '</div>' +

    // Supervisor / target panel
    panelHtml +
    pollHtml +

    // Ticker — bottom bar
    '<div style="position:absolute;bottom:0;left:0;right:0;height:32px;' +
      'background:rgba(0,0,0,0.85);border-top:1px solid rgba(0,242,255,0.15);' +
      'overflow:hidden;display:flex;align-items:center;">' +
      '<div style="flex-shrink:0;padding:0 10px;font-size:0.58rem;color:#00f2ff;' +
        'letter-spacing:0.12em;border-right:1px solid rgba(0,242,255,0.2);white-space:nowrap;">LFBO ATC</div>' +
      '<div style="overflow:hidden;flex:1;">' +
        '<div id="' + uid + 'tkr" style="white-space:nowrap;font-size:0.62rem;color:rgba(255,255,255,0.7);' +
          'animation:' + uid + 'tk ' + tickerDur + ' linear infinite;">' +
          _esc(tickerText) + ' &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + _esc(tickerText) +
        '</div>' +
      '</div>' +
    '</div>' +

    // Canvas radar engine
    '<script>(function(){' +
      'var c=document.getElementById("' + uid + '");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'c.width=c.offsetWidth||window.innerWidth||700;c.height=c.offsetHeight||window.innerHeight||520;' +
      'var W=c.width,H=c.height;' +
      'var CX=W/2,CY=H*0.48;' +
      'var ZOOM_WIDE=' + zoom + ';' +
      'var ZOOM_TIGHT=' + (zoomIn || zoom) + ';' +
      'var ZOOM_PERIOD=' + zoomPeriod + ';' +
      'var _ZOOM_ANIM=' + (zoomIn ? 'true' : 'false') + ';' +
      'var _ZOOM_T0=Date.now();' +
      'var ZOOM=ZOOM_WIDE;' +
      'var NM=Math.min(W,H)*0.42/ZOOM;' +
      'var LOCKED="' + _esc(locked) + '";' +
      'var FLIGHTS=' + FLIGHTS + ';' +
      // Animate each flight toward LFBO slowly (approach speed ~4nm/min sim)
      'FLIGHTS.forEach(function(f){' +
        'f.px=CX+Math.sin(f.brg*Math.PI/180)*f.dist*NM;' +
        'f.py=CY-Math.cos(f.brg*Math.PI/180)*f.dist*NM;' +
        'f.hdg=(f.brg+180)%360;' +
        'f.vx=-Math.sin(f.brg*Math.PI/180)*0.12;' +
        'f.vy= Math.cos(f.brg*Math.PI/180)*0.12;' +
        'f.trail=[];f.tick=0;' +
      '});' +
      'var sweep=0;var isoYaw=0;' +
      'var blink=true;setInterval(function(){blink=!blink;},800);' +

      // Airline ICAO prefix → short name + accent colour
      'var AL={' +
        'AFR:{n:"Air France",    c:"#002395"},' +
        'EZY:{n:"easyJet",       c:"#FF6600"},' +
        'EJU:{n:"easyJet Eur",   c:"#FF6600"},' +
        'EZS:{n:"easyJet CH",    c:"#FF6600"},' +
        'RYR:{n:"Ryanair",       c:"#073590"},' +
        'RUK:{n:"Ryanair UK",    c:"#073590"},' +
        'IBE:{n:"Iberia",        c:"#CC0000"},' +
        'IBS:{n:"Iberia Exp",    c:"#CC0000"},' +
        'VLG:{n:"Vueling",       c:"#FFC300"},' +
        'TAP:{n:"TAP Portugal",  c:"#50C878"},' +
        'BAW:{n:"Brit Airways",  c:"#075AAA"},' +
        'DLH:{n:"Lufthansa",     c:"#1a3c8f"},' +
        'KLM:{n:"KLM",           c:"#009DBB"},' +
        'NAX:{n:"Norwegian",     c:"#D81F26"},' +
        'THY:{n:"Turkish",       c:"#C70000"},' +
        'SAS:{n:"SAS",           c:"#0065BD"},' +
        'TRA:{n:"Transavia",     c:"#00a86b"},' +
        'TVF:{n:"Transavia FR",  c:"#00a86b"},' +
        'HOP:{n:"HOP!",          c:"#e2001a"},' +
        'WZZ:{n:"Wizz Air",      c:"#c6007e"},' +
        'RAM:{n:"Royal Air Maroc",c:"#009e60"},' +
        'SWR:{n:"Swiss",         c:"#e10019"},' +
        'AUA:{n:"Austrian",      c:"#bd0026"},' +
        'BEL:{n:"Brussels Air",  c:"#003f8a"},' +
        'GWI:{n:"Eurowings",     c:"#6f1d77"},' +
        'DAH:{n:"Air Algerie",   c:"#006c35"},' +
        'TSC:{n:"Air Transat",   c:"#ff4d00"},' +
        'UAE:{n:"Emirates",      c:"#d71921"},' +
        'QTR:{n:"Qatar",         c:"#5c0632"},' +
        'BTI:{n:"airBaltic",     c:"#006e4e"},' +
        'AAF:{n:"Amapola",       c:"#c8a800"},' +
        'FDX:{n:"FedEx",         c:"#4d148c"},' +
        'UPS:{n:"UPS",           c:"#351c15"},' +
        'GTI:{n:"Atlas Air",     c:"#003087"}' +
      '};' +
      'function getAL(cs){var p=(cs||"").substr(0,3).toUpperCase();return AL[p]||{n:p,c:"#00f2ff"};}' +

      // ── Top-down aircraft silhouette, oriented by heading ─────────────────
      'function drawPlane(ctx,x,y,hdg,s,col,glow){' +
        'ctx.save();ctx.translate(x,y);ctx.rotate(hdg*Math.PI/180);' +
        'if(glow){ctx.shadowBlur=12;ctx.shadowColor=col;}' +
        'ctx.fillStyle=col;' +
        // fuselage
        'ctx.beginPath();ctx.moveTo(0,-s*3.2);ctx.lineTo(s*0.45,-s*0.2);' +
        'ctx.lineTo(s*0.3,s*2.8);ctx.lineTo(-s*0.3,s*2.8);' +
        'ctx.lineTo(-s*0.45,-s*0.2);ctx.closePath();ctx.fill();' +
        // left wing
        'ctx.beginPath();ctx.moveTo(-s*0.4,-s*0.3);ctx.lineTo(-s*3.4,s*1.4);' +
        'ctx.lineTo(-s*2.6,s*1.7);ctx.lineTo(-s*0.28,s*0.6);ctx.closePath();ctx.fill();' +
        // right wing
        'ctx.beginPath();ctx.moveTo(s*0.4,-s*0.3);ctx.lineTo(s*3.4,s*1.4);' +
        'ctx.lineTo(s*2.6,s*1.7);ctx.lineTo(s*0.28,s*0.6);ctx.closePath();ctx.fill();' +
        // left stabiliser
        'ctx.beginPath();ctx.moveTo(-s*0.28,s*2.0);ctx.lineTo(-s*1.3,s*2.9);' +
        'ctx.lineTo(-s*1.0,s*3.1);ctx.lineTo(-s*0.22,s*2.5);ctx.closePath();ctx.fill();' +
        // right stabiliser
        'ctx.beginPath();ctx.moveTo(s*0.28,s*2.0);ctx.lineTo(s*1.3,s*2.9);' +
        'ctx.lineTo(s*1.0,s*3.1);ctx.lineTo(s*0.22,s*2.5);ctx.closePath();ctx.fill();' +
        'ctx.shadowBlur=0;ctx.restore();' +
      '}' +

      // ── Isometric 3D aircraft for the locked-target panel ─────────────────
      // Projects 3D (x=right, y=up, z=fwd/nose) → ISO screen coords
      'function drawIso(cvs,color,yaw){' +
        'if(!cvs)return;' +
        'var ctx=cvs.getContext("2d");' +
        'var W=cvs.width,H=cvs.height;' +
        'ctx.clearRect(0,0,W,H);' +
        'var S=20,ox=W/2-4,oy=H*0.58;' +
        'function p3(x,y,z){' +   // rotate Y then iso project
          'var rx=x*Math.cos(yaw)+z*Math.sin(yaw);' +
          'var rz=-x*Math.sin(yaw)+z*Math.cos(yaw);' +
          'return{sx:ox+(rx-rz)*S*0.866,sy:oy-(rx+rz)*S*0.5+y*S};' +
        '}' +
        'function face(pts,fill){' +
          'var ps=pts.map(function(p){return p3(p[0],p[1],p[2]);});' +
          'ctx.beginPath();ctx.moveTo(ps[0].sx,ps[0].sy);' +
          'for(var i=1;i<ps.length;i++)ctx.lineTo(ps[i].sx,ps[i].sy);' +
          'ctx.closePath();ctx.fillStyle=fill;ctx.fill();' +
          'ctx.strokeStyle="rgba(0,0,0,0.25)";ctx.lineWidth=0.5;ctx.stroke();' +
        '}' +
        // fuselage faces
        'face([[-0.45,0.35,-4.5],[0.45,0.35,-4.5],[0.45,0.35,3.2],[-0.45,0.35,3.2]],color);' +        // top
        'face([[-0.45,-0.35,-4.5],[-0.45,0.35,-4.5],[-0.45,0.35,3.2],[-0.45,-0.35,3.2]],"rgba(0,0,0,0.35)");' + // left side
        'face([[-0.45,-0.35,-4.5],[0.45,-0.35,-4.5],[0.45,0.35,-4.5],[-0.45,0.35,-4.5]],"rgba(255,255,255,0.22)");' + // nose
        'face([[0.45,-0.35,-4.5],[-0.45,-0.35,-4.5],[-0.45,0.35,-4.5],[0.45,0.35,-4.5]],"rgba(255,255,255,0.08)");' + // tail end
        // wings
        'face([[-0.45,0.15,-0.8],[-5.5,0.15,1.6],[-4.5,0.15,1.9],[-0.45,0.15,0.5]],color);' +       // left top
        'face([[0.45,0.15,-0.8],[0.45,0.15,0.5],[4.5,0.15,1.9],[5.5,0.15,1.6]],color);' +             // right top
        'face([[-0.45,-0.05,-0.8],[-0.45,-0.05,0.5],[-4.5,-0.05,1.9],[-5.5,-0.05,1.6]],"rgba(0,0,0,0.4)");' + // left bottom
        'face([[0.45,-0.05,-0.8],[5.5,-0.05,1.6],[4.5,-0.05,1.9],[0.45,-0.05,0.5]],"rgba(0,0,0,0.4)");' + // right bottom
        // tail fins (horizontal stabilisers)
        'face([[-0.45,0.28,2.2],[-2.3,0.28,3.2],[-1.8,0.28,3.4],[-0.45,0.28,2.6]],color);' +
        'face([[0.45,0.28,2.2],[0.45,0.28,2.6],[1.8,0.28,3.4],[2.3,0.28,3.2]],color);' +
        // vertical fin
        'face([[-0.1,0.35,1.6],[0.1,0.35,1.6],[0.1,1.5,3.2],[-0.1,1.5,3.2]],"rgba(255,255,255,0.5)");' +
        // engines under wings
        '[[-2.5,1.5],[ 2.5,1.5]].forEach(function(e){' +
          'face([[e[0]-0.22,-0.55,e[1]-0.6],[e[0]+0.22,-0.55,e[1]-0.6],[e[0]+0.22,-0.55,e[1]+0.9],[e[0]-0.22,-0.55,e[1]+0.9]],"rgba(30,30,40,0.9)");' +
        '});' +
      '}' +

      // ── O(N²) separation conflict detection ──────────────────────────────
      // Uses canvas pixel distance / NM scale — works for both live and sim flights
      'function checkSeparation(ctx,flights){' +
        'for(var _i=0;_i<flights.length;_i++){' +
          'for(var _j=_i+1;_j<flights.length;_j++){' +
            'var _f1=flights[_i],_f2=flights[_j];' +
            'var _dx=_f1.px-_f2.px,_dy=_f1.py-_f2.py;' +
            'var _dist=Math.sqrt(_dx*_dx+_dy*_dy)/NM;' +
            'var _altSep=Math.abs((_f1.alt||0)-(_f2.alt||0));' +
            'if(_dist<3.0&&_altSep<1000){' +
              'ctx.save();' +
              'ctx.strokeStyle="#f59e0b";ctx.lineWidth=1.5;ctx.setLineDash([4,4]);ctx.globalAlpha=0.75;' +
              'ctx.beginPath();ctx.moveTo(_f1.px,_f1.py);ctx.lineTo(_f2.px,_f2.py);ctx.stroke();' +
              'ctx.setLineDash([]);ctx.globalAlpha=1;' +
              'var _mx=(_f1.px+_f2.px)/2,_my=(_f1.py+_f2.py)/2-8;' +
              'ctx.fillStyle="#f59e0b";ctx.font="bold 8px \'Courier New\'";ctx.textAlign="center";' +
              'ctx.shadowBlur=6;ctx.shadowColor="#f59e0b";' +
              'ctx.fillText("⚡ "+_dist.toFixed(1)+"nm / "+Math.round(_altSep)+"ft",_mx,_my);' +
              'ctx.shadowBlur=0;ctx.restore();' +
            '}' +
          '}' +
        '}' +
      '}' +

      // ── Configurable centre — defaults to LFBO Toulouse ──────────────────
      'var LFBO_LAT=' + (b.center_lat||43.629) + ',LFBO_LON=' + (b.center_lon||1.363) + ';' +
      'var CENTER_ICAO="' + _esc(b.center_icao||'LFBO') + '",CENTER_COUNTRY="' + _esc(b.country||'FR') + '";' +
      'function llToCanvas(lat,lon){' +
        'var dlat=(lat-LFBO_LAT)*60;' + // degrees → nm
        'var dlon=(lon-LFBO_LON)*60*Math.cos(LFBO_LAT*Math.PI/180);' +
        'return{x:CX+dlon*NM,y:CY-dlat*NM};' +
      '}' +

      // ── Simplified country boundaries for minimap overlay ─────────────────
      // Each polygon is [lat,lon] pairs — ~20pt simplified outlines
      'var GEO_COUNTRIES={' +
        'FR:[[51.1,2.5],[50.5,3.4],[49.5,6.4],[48.97,7.83],[47.6,7.6],[46.4,6.4],[45.9,7.0],[44.1,7.0],[43.8,7.4],[43.3,5.1],[42.3,3.2],[42.4,2.1],[43.4,-1.8],[43.5,-1.5],[47.3,-2.2],[48.3,-4.6],[48.7,-2.0],[49.6,-1.6],[50.1,-1.8],[51.1,2.5]],' +
        'GB:[[50.6,-0.9],[51.2,1.4],[52.9,1.8],[54.0,-0.2],[55.0,-1.4],[55.8,-2.0],[57.7,-1.8],[58.6,-3.6],[57.8,-5.9],[56.5,-5.6],[55.5,-5.7],[54.6,-5.9],[53.3,-4.6],[51.4,-5.1],[50.6,-0.9]],' +
        'DE:[[54.9,8.4],[54.5,11.2],[54.0,13.2],[53.9,14.4],[52.9,14.1],[51.1,15.0],[50.4,12.3],[50.0,12.5],[48.7,13.5],[47.6,12.9],[47.6,9.6],[47.7,7.6],[49.4,6.4],[49.9,6.1],[50.9,6.2],[54.9,8.4]],' +
        'ES:[[43.4,-1.8],[43.6,-1.5],[43.8,-8.1],[42.6,-8.9],[41.0,-9.0],[37.2,-7.4],[36.0,-5.4],[36.6,-4.4],[37.4,-1.8],[38.7,-0.2],[40.5,0.8],[42.3,3.2],[42.4,2.1],[43.4,-1.8]],' +
        'IT:[[47.1,10.1],[46.5,13.7],[46.1,13.7],[45.8,13.7],[44.4,12.2],[44.1,12.4],[42.7,10.3],[41.7,9.0],[38.4,15.7],[37.6,15.1],[39.9,18.5],[41.8,15.7],[44.2,13.8],[47.1,10.1]],' +
        'PT:[[42.1,-8.2],[41.9,-8.7],[40.0,-7.0],[37.2,-7.4],[37.0,-7.5],[37.0,-9.0],[39.7,-9.1],[40.2,-8.9],[42.1,-8.2]]' +
      '};' +

      // ── Country boundary overlay on main radar (subtle, at large zoom only) ─
      'function drawCountryOverlay(ctx){' +
        'var pts=GEO_COUNTRIES[CENTER_COUNTRY];if(!pts)return;' +
        'ctx.save();ctx.setLineDash([3,6]);' +
        'ctx.strokeStyle="rgba(0,120,200,0.22)";ctx.lineWidth=0.8;' +
        'ctx.fillStyle="rgba(0,60,120,0.04)";' +
        'ctx.beginPath();' +
        'var p0=llToCanvas(pts[0][0],pts[0][1]);ctx.moveTo(p0.x,p0.y);' +
        'for(var _k=1;_k<pts.length;_k++){var _p=llToCanvas(pts[_k][0],pts[_k][1]);ctx.lineTo(_p.x,_p.y);}' +
        'ctx.closePath();ctx.fill();ctx.stroke();' +
        'ctx.restore();' +
      '}' +

      // ── Minimap inset — bottom-right, shows country + TMA extent ─────────
      'function drawMiniMap(ctx){' +
        'var pts=GEO_COUNTRIES[CENTER_COUNTRY];if(!pts)return;' +
        // Compute geographic bounds of the country polygon
        'var mnLat=90,mxLat=-90,mnLon=180,mxLon=-180;' +
        'pts.forEach(function(p){mnLat=Math.min(mnLat,p[0]);mxLat=Math.max(mxLat,p[0]);mnLon=Math.min(mnLon,p[1]);mxLon=Math.max(mxLon,p[1]);});' +
        'var pad=0.5;mnLat-=pad;mxLat+=pad;mnLon-=pad;mxLon+=pad;' +
        // Minimap canvas region
        'var MW=148,MH=112,MX=W-MW-10,MY=H-MH-10;' +
        // Background + border
        'ctx.fillStyle="rgba(2,8,18,0.88)";ctx.fillRect(MX-2,MY-2,MW+4,MH+4);' +
        'ctx.strokeStyle="rgba(0,242,255,0.18)";ctx.lineWidth=0.8;ctx.setLineDash([]);' +
        'ctx.strokeRect(MX-2,MY-2,MW+4,MH+4);' +
        // Projection helpers (equirectangular within bounds)
        'var mLon=function(l){return MX+(l-mnLon)/(mxLon-mnLon)*MW;};' +
        'var mLat=function(l){return MY+MH-(l-mnLat)/(mxLat-mnLat)*MH;};' +
        // Country fill + outline
        'ctx.fillStyle="rgba(0,50,100,0.25)";' +
        'ctx.strokeStyle="rgba(0,160,255,0.5)";ctx.lineWidth=0.8;ctx.setLineDash([]);' +
        'ctx.beginPath();' +
        'ctx.moveTo(mLon(pts[0][1]),mLat(pts[0][0]));' +
        'for(var _m=1;_m<pts.length;_m++){ctx.lineTo(mLon(pts[_m][1]),mLat(pts[_m][0]));}' +
        'ctx.closePath();ctx.fill();ctx.stroke();' +
        // TMA view radius as a circle on the minimap
        'var cx_m=mLon(LFBO_LON),cy_m=mLat(LFBO_LAT);' +
        'var nmDeg=ZOOM/60;' + // zoom nm → degrees
        'var rPx=(nmDeg/(mxLon-mnLon))*MW;' +
        'ctx.beginPath();ctx.arc(cx_m,cy_m,rPx,0,Math.PI*2);' +
        'ctx.strokeStyle="rgba(0,242,255,0.35)";ctx.lineWidth=0.7;ctx.setLineDash([2,3]);ctx.stroke();ctx.setLineDash([]);' +
        // Center dot + ICAO label
        'ctx.beginPath();ctx.arc(cx_m,cy_m,3,0,Math.PI*2);' +
        'ctx.fillStyle="#00f2ff";ctx.shadowBlur=6;ctx.shadowColor="#00f2ff";ctx.fill();ctx.shadowBlur=0;' +
        'ctx.fillStyle="rgba(0,242,255,0.7)";ctx.font="7px \'Courier New\'";ctx.textAlign="left";' +
        'ctx.fillText(CENTER_ICAO,cx_m+5,cy_m+3);' +
        // Country label
        'ctx.fillStyle="rgba(0,242,255,0.3)";ctx.font="7px \'Courier New\'";ctx.textAlign="right";' +
        'ctx.fillText(CENTER_COUNTRY+" AIRSPACE",MX+MW-2,MY+10);' +
      '}' +

      // ── Live flight update from adsb_feed ────────────────────────────────
      'function setDataStatus(live,count){' +
        'var el=document.getElementById("' + uid + 'status");' +
        'var dot=document.getElementById("' + uid + 'sdot");' +
        'var lbl=document.getElementById("' + uid + 'slbl");' +
        'if(!el)return;' +
        'var c=live?"#34c759":"#ff3b30";' +
        'el.style.background=live?"rgba(52,199,89,0.12)":"rgba(255,59,48,0.12)";' +
        'el.style.borderColor=live?"rgba(52,199,89,0.3)":"rgba(255,59,48,0.3)";' +
        'el.style.color=c;' +
        'if(dot){dot.style.background=c;dot.style.boxShadow="0 0 6px "+c;}' +
        'if(lbl)lbl.textContent=live?"LIVE ("+count+")":"SIM";' +
      '}' +
      'function updateFlightsFromFeed(feeds){' +
        'FLIGHTS.length=0;' +
        'feeds.forEach(function(f){' +
          'if(f.lat===null||f.lon===null)return;' +
          'var pos=llToCanvas(f.lat,f.lon);' +
          'var dx=pos.x-CX,dy=pos.y-CY;' +
          'if(Math.sqrt(dx*dx+dy*dy)>ZOOM*NM*1.05)return;' + // clip to zoom
          'var is7700=f.squawk==="7700",is7600=f.squawk==="7600";' +
          'FLIGHTS.push({' +
            'c:f.callsign,t:"ADS-B",' +
            'alt:f.alt_ft,spd:f.spd_kt,hdg:f.hdg,' +
            'lat:f.lat,lon:f.lon,' +
            'px:pos.x,py:pos.y,' +
            'live:true,' + // reproject each frame via llToCanvas so zoom animation repositions them
            'status:f.alt_ft<2000?"FINAL":f.alt_ft<5000?"APPROACH":f.alt_ft<8000?"DESCENT":"EN-ROUTE",' +
            'col:f.callsign===LOCKED?"#00f2ff":is7700?"#ff3b30":is7600?"#ff9f0a":"#ffffff",' +
            'squawk:f.squawk,trail:[],tick:0' +
          '});' +
        '});' +
        'setDataStatus(FLIGHTS.length>0,FLIGHTS.length);' +
      '}' +

      // Template strings for client-side {{weather.*}} interpolation
      'var _CSUB=' + JSON.stringify(chyronSub) + ';' +
      'var _TKRT=' + JSON.stringify(tickerText) + ';' +

      // ── Weather panel update from metar_feed ─────────────────────────────
      'function updateWeather(wx){' +
        'var we=document.getElementById("' + uid + 'wind");' +
        'var te=document.getElementById("' + uid + 'temp");' +
        'var qe=document.getElementById("' + uid + 'qnh");' +
        'if(we&&wx.wind)we.textContent=wx.wind;' +
        'if(te&&wx.temp)te.textContent=wx.temp;' +
        'if(qe&&wx.qnh)qe.textContent=wx.qnh;' +
        // Client-side template interpolation for chyron subtitle and ticker
        'function _wi(s){' +
          'return s.replace(/\\{\\{weather\\.wind\\}\\}/g,wx.wind||"—")' +
                  '.replace(/\\{\\{weather\\.temp\\}\\}/g,wx.temp||"—")' +
                  '.replace(/\\{\\{weather\\.pressure\\}\\}/g,wx.qnh||"—")' +
                  '.replace(/\\{\\{weather\\.raw\\}\\}/g,wx.raw||"");' +
        '}' +
        'var cs=document.getElementById("' + uid + 'csub");' +
        'if(cs)cs.textContent=_wi(_CSUB);' +
        'var tk=document.getElementById("' + uid + 'tkr");' +
        'if(tk){var t=_wi(_TKRT);tk.textContent=t+"     "+t;}' +
      '}' +

      // ── Subscribe to data feeds (chained so multiple slides share one feed) ──
      'window.A2UI_DATA=window.A2UI_DATA||{};' +
      'window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
      (dataSource ?
        '(function(){var prev=window.A2UI_CALLBACKS["' + _esc(dataSource) + '"];' +
        'window.A2UI_CALLBACKS["' + _esc(dataSource) + '"]=function(d){updateFlightsFromFeed(d);if(typeof prev==="function")prev(d);};})();' +
        'if(window.A2UI_DATA["' + _esc(dataSource) + '"])' +
          'updateFlightsFromFeed(window.A2UI_DATA["' + _esc(dataSource) + '"]);' : '') +
      (weatherSource ?
        '(function(){var prev=window.A2UI_CALLBACKS["' + _esc(weatherSource) + '"];' +
        'window.A2UI_CALLBACKS["' + _esc(weatherSource) + '"]=function(d){updateWeather(d);if(typeof prev==="function")prev(d);};})();' +
        'if(window.A2UI_DATA["' + _esc(weatherSource) + '"])' +
          'updateWeather(window.A2UI_DATA["' + _esc(weatherSource) + '"]);' : '') +

      // Update flight list + iso panel
      'function updateFlightList(){' +
        'var el=document.getElementById("' + uid + 'flist");' +
        'if(!el)return;' +
        'var html="";' +
        'var isSuper=' + (panelType === 'supervisor' ? 'true' : 'false') + ';' +
        'FLIGHTS.forEach(function(f){' +
          'var lk=LOCKED&&f.c===LOCKED;' +
          'var col=lk?"#00f2ff":f.col;' +
          'var al=getAL(f.c);' +
          'if(isSuper){' +
            'html+="<div style=\'display:grid;grid-template-columns:1fr 52px 36px 56px;gap:0 4px;' +
              'padding:3px 0;border-bottom:1px solid rgba(0,242,255,0.06);color:"+col+"\'>"' +
              '+"<span style=\'font-weight:"+(lk?"bold":"normal")+"\'>"+f.c+"</span>"' +
              '+"<span style=\'color:rgba(255,255,255,0.45);font-size:0.5rem;\'>"+al.n+"</span>"' +
              '+"<span>FL"+Math.round((f.alt||0)/100)+"</span>"' +
              '+"<span style=\'color:rgba(255,255,255,0.55);font-size:0.5rem;\'>"+f.status+"</span>"' +
            '+"</div>";' +
          '} else {' +
            'if(LOCKED&&!lk)return;' +
            // 3° glideslope profiler: 318ft/nm descent to runway threshold
            'var _dxg=f.px-CX,_dyg=f.py-CY;' +
            'var _dNM=Math.sqrt(_dxg*_dxg+_dyg*_dyg)/NM;' +
            'var _ideal=Math.max(0,_dNM*318);' +
            'var _dev=(f.alt||0)-_ideal;' +
            'var _gsCol=Math.abs(_dev)<250?"#00ff41":_dev>0?"#f59e0b":"#ff3b30";' +
            'var _gsTxt=Math.abs(_dev)<250?"ON GLIDE":(_dev>0?"+":"")+Math.round(_dev)+"ft";' +
            'html+="<div style=\'color:"+col+";\'>"' +
              '+"<div style=\'font-size:0.72rem;font-weight:bold;letter-spacing:0.06em;\'>"+f.c+"</div>"' +
              '+"<div style=\'color:"+al.c+";font-size:0.6rem;margin-bottom:6px;\'>"+al.n+"</div>"' +
              '+"<div style=\'display:grid;grid-template-columns:52px 1fr;gap:3px 0;font-size:0.55rem;\'>"' +
                '+"<span style=\'color:rgba(0,242,255,0.6);\'>ALT</span><span style=\'color:#fff;\'>FL"+Math.round((f.alt||0)/100)+"</span>"' +
                '+"<span style=\'color:rgba(0,242,255,0.6);\'>SPD</span><span style=\'color:#fff;\'>"+(f.spd||0)+"kt</span>"' +
                '+"<span style=\'color:rgba(0,242,255,0.6);\'>HDG</span><span style=\'color:#fff;\'>"+Math.round(f.hdg||0)+"°</span>"' +
                '+"<span style=\'color:rgba(0,242,255,0.6);\'>SQK</span>"' +
                '+"<span style=\'color:"+(f.squawk==="7700"?"#ff3b30":f.squawk==="7600"?"#ff9f0a":"#fff")+";\'>"+(f.squawk||"----")+"</span>"' +
                '+"<span style=\'color:rgba(0,242,255,0.6);\'>STATUS</span><span style=\'color:#00ff41;\'>"+f.status+"</span>"' +
                '+"<span style=\'color:rgba(0,242,255,0.6);\'>GLIDE</span><span style=\'color:"+_gsCol+";font-weight:bold;\'>"  +_gsTxt+"</span>"' +
              '+"</div>"' +
            '+"</div>";' +
          '}' +
        '});' +
        'el.innerHTML=html;' +
        'if(LOCKED){' +
          'var lf=null;for(var _i=0;_i<FLIGHTS.length;_i++){if(FLIGHTS[_i].c===LOCKED){lf=FLIGHTS[_i];break;}}' +
          'var icvs=document.getElementById("' + uid + 'iso");' +
          'if(icvs&&lf){var ac=getAL(lf.c);drawIso(icvs,ac.c||"#00f2ff",isoYaw);}' +
        '}' +
      '}' +

      'function frame(){' +
        'if(_ZOOM_ANIM){' +
          'var _t=((Date.now()-_ZOOM_T0)%ZOOM_PERIOD)/ZOOM_PERIOD;' +
          'var _e=(1-Math.cos(Math.PI*2*_t))/2;' +
          'ZOOM=ZOOM_WIDE-(ZOOM_WIDE-ZOOM_TIGHT)*_e;' +
          'NM=Math.min(W,H)*0.42/ZOOM;' +
        '}' +
        'ctx.clearRect(0,0,W,H);' +

        // Background gradient
        'var bg=ctx.createRadialGradient(CX,CY,0,CX,CY,Math.max(W,H)*0.7);' +
        'bg.addColorStop(0,"#060d1a");bg.addColorStop(1,"#020509");' +
        'ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);' +

        // Radar sweep (trailing gradient arc)
        'sweep+=0.008;' +
        'var sw=ctx.createConicalGradient?null:null;' + // conical not in all browsers
        // Draw sweep as rotating sector
        'ctx.save();' +
        'ctx.translate(CX,CY);ctx.rotate(sweep);' +
        'var sweepGrd=ctx.createLinearGradient(0,0,0,-Math.min(W,H)*0.5);' +
        'sweepGrd.addColorStop(0,"rgba(0,242,255,0.18)");sweepGrd.addColorStop(1,"rgba(0,242,255,0)");' +
        'ctx.beginPath();ctx.moveTo(0,0);' +
        'ctx.arc(0,0,Math.min(W,H)*0.5,-Math.PI/2,-Math.PI/2+0.4,false);' +
        'ctx.closePath();ctx.fillStyle=sweepGrd;ctx.fill();' +
        'ctx.restore();' +

        // Range rings
        '[10,20,30].forEach(function(nm){' +
          'var r=nm*NM;' +
          'ctx.beginPath();ctx.arc(CX,CY,r,0,Math.PI*2);' +
          'ctx.strokeStyle=nm<=ZOOM?"rgba(0,242,255,0.12)":"rgba(0,242,255,0.04)";' +
          'ctx.lineWidth=0.8;ctx.stroke();' +
          'if(nm<=ZOOM+5){' +
            'ctx.fillStyle="rgba(0,242,255,0.25)";ctx.font="9px \'Courier New\'";ctx.textAlign="left";' +
            'ctx.fillText(nm+"nm",CX+4,CY-r+12);' +
          '}' +
        '});' +

        // Crosshair
        'ctx.strokeStyle="rgba(0,242,255,0.08)";ctx.lineWidth=0.5;' +
        'ctx.beginPath();ctx.moveTo(CX,0);ctx.lineTo(CX,H);ctx.stroke();' +
        'ctx.beginPath();ctx.moveTo(0,CY);ctx.lineTo(W,CY);ctx.stroke();' +

        // VOR beacons
        '[{lbl:"TOU",brg:183,d:8},{lbl:"BGC",brg:348,d:4},{lbl:"CNA",brg:72,d:20}].forEach(function(v){' +
          'var vx=CX+Math.sin(v.brg*Math.PI/180)*v.d*NM;' +
          'var vy=CY-Math.cos(v.brg*Math.PI/180)*v.d*NM;' +
          'ctx.strokeStyle="#f59e0b";ctx.lineWidth=1;' +
          'ctx.strokeRect(vx-4,vy-4,8,8);' +
          'ctx.fillStyle="#f59e0b88";ctx.fillRect(vx-4,vy-4,8,8);' +
          'ctx.fillStyle="#f59e0b";ctx.font="9px \'Courier New\'";ctx.textAlign="center";' +
          'ctx.fillText(v.lbl,vx,vy-8);' +
        '});' +

        // Approach path — dashed line at RWY 32 heading (315°) extending 18nm
        'ctx.setLineDash([4,4]);ctx.strokeStyle="rgba(0,255,65,0.2)";ctx.lineWidth=1;' +
        'ctx.beginPath();' +
        'ctx.moveTo(CX,CY);' +
        'ctx.lineTo(CX+Math.sin(135*Math.PI/180)*18*NM, CY-Math.cos(135*Math.PI/180)*18*NM);' +
        'ctx.stroke();ctx.setLineDash([]);' +

        // LFBO runway symbol
        'ctx.save();ctx.translate(CX,CY);ctx.rotate(-45*Math.PI/180);' + // RWY 32 ≈ 315°
        'ctx.fillStyle="#00ff41";ctx.fillRect(-2,-20,4,40);' + // runway strip
        'ctx.strokeStyle="#00ff41";ctx.lineWidth=0.5;' +
        'ctx.strokeRect(-8,-20,16,40);' +
        'ctx.restore();' +
        'ctx.fillStyle="#00f2ff";ctx.font="bold 9px \'Courier New\'";ctx.textAlign="center";' +
        'ctx.fillText(CENTER_ICAO,CX,CY+28);' +

        // Flights — live positions from adsb_feed; simulated positions animate toward airport
        'FLIGHTS.forEach(function(f){' +
          'if(f.live){' +
            'var _lp=llToCanvas(f.lat,f.lon);f.px=_lp.x;f.py=_lp.y;' +
          '}else{' +
            'f.dist=Math.max(0.5,f.dist-0.015);' +
            'f.px=CX+Math.sin(f.brg*Math.PI/180)*f.dist*NM;' +
            'f.py=CY-Math.cos(f.brg*Math.PI/180)*f.dist*NM;' +
          '}' +
          // Trail — lat/lon for live (reprojects with zoom), dist+brg for sim
          'f.tick++;if(f.tick%8===0){' +
            'f.trail.push(f.live?{lat:f.lat,lon:f.lon}:{d:f.dist,b:f.brg});' +
            'if(f.trail.length>6)f.trail.shift();' +
          '}' +
          'for(var ti=0;ti<f.trail.length;ti++){' +
            'var _td=f.trail[ti];var _tp;' +
            'if(_td.lat!==undefined){_tp=llToCanvas(_td.lat,_td.lon);}' +
            'else{_tp={x:CX+Math.sin(_td.b*Math.PI/180)*_td.d*NM,y:CY-Math.cos(_td.b*Math.PI/180)*_td.d*NM};}' +
            'var _tx=_tp.x,_ty=_tp.y;' +
            'var a=(ti+1)/f.trail.length*0.35;' +
            'ctx.beginPath();ctx.arc(_tx,_ty,1,0,Math.PI*2);' +
            'ctx.fillStyle="rgba(0,242,255,"+a+")";ctx.fill();' +
          '}' +
          // Reticle for locked callsign
          'var isLocked=LOCKED&&f.c===LOCKED;' +
          'if(isLocked){' +
            'ctx.save();ctx.translate(f.px,f.py);' +
            'var rot=(Date.now()/1000)%(Math.PI*2);ctx.rotate(rot);' +
            'ctx.strokeStyle="#00f2ff";ctx.lineWidth=1;ctx.setLineDash([3,3]);' +
            'ctx.beginPath();ctx.arc(0,0,22,0,Math.PI*2);ctx.stroke();' +
            'ctx.setLineDash([]);ctx.restore();' +
          '}' +
          // Aircraft silhouette (top-down plan view, oriented by heading)
          'if(blink||isLocked){' +
            'var fc=isLocked?"#00f2ff":f.col;' +
            'drawPlane(ctx,f.px,f.py,f.hdg||0,isLocked?5.5:3.2,fc,isLocked);' +
          '}' +
          // Labels: callsign + FL + speed + airline
          'var lx=f.px+14,ly=f.py-4;' +
          'var al=getAL(f.c);' +
          'ctx.fillStyle=isLocked?"#00f2ff":f.col;' +
          'ctx.font=(isLocked?"bold ":"")+"9px \'Courier New\'";ctx.textAlign="left";' +
          'ctx.fillText(f.c,lx,ly);' +
          'ctx.fillStyle="rgba(255,255,255,0.45)";ctx.font="8px \'Courier New\'";' +
          'ctx.fillText("FL"+Math.round((f.alt||0)/100)+"  "+(f.spd||0)+"kt",lx,ly+10);' +
          'if(al.n){ctx.fillStyle="rgba(255,255,255,0.3)";ctx.font="7.5px \'Courier New\'";ctx.fillText(al.n,lx,ly+20);}' +
        '});' +

        // Separation conflict vectors (O(N²), amber dashed lines + badge)
        'checkSeparation(ctx,FLIGHTS);' +

        // Country boundary overlay (subtle, helps orient position within FIR)
        'drawCountryOverlay(ctx);' +

        // Overlay corner — mode / count label
        'ctx.fillStyle="rgba(0,242,255,0.15)";ctx.font="8px \'Courier New\'";ctx.textAlign="right";' +
        'ctx.fillText(FLIGHTS.length + " TFC · RWY 32L/R ACTIVE",W-12,H-38);' +

        // Minimap inset — country shape + TMA extent circle
        'drawMiniMap(ctx);' +

        'isoYaw+=0.008;' +
        'updateFlightList();' +
        'requestAnimationFrame(frame);' +
      '}' +
      'frame();' +
    '})();<\/script>' +
    '</div>';
};

// ── playbook ──────────────────────────────────────────────────────────────────
// Multi-slide deck rendered client-side — no page reloads, no URL encoding.
// Navigation is JS-only; location.hash reflects the active slide.
// Shared data atoms (adsb_feed, metar_feed) go in shared_blocks and run once.
//
// Schema:
//   shared_blocks  — atoms rendered once outside slides (data feeds)
//   slides[]       — each: { id, label, blocks[] }
//   transition     — 'fade' | 'instant' (default 'fade')
_RENDERERS['playbook'] = function(b) {
  var uid        = 'pbk' + Math.random().toString(36).substr(2, 6);
  var slides     = b.slides     || [];
  var sharedBlks = b.shared_blocks || [];
  var transition = b.transition || 'fade';
  if (!slides.length) return '';

  // Shared atoms (data feeds, styles) — rendered once, before slide divs
  var sharedHtml = sharedBlks.length ? renderAtoms(sharedBlks, { theme: 'dark' }) : '';

  // Each slide rendered into its own absolutely-positioned container
  var slideDivs = '';
  slides.forEach(function(slide, idx) {
    var sid     = slide.id || String(idx);
    var content = (slide.blocks || []).length ? renderAtoms(slide.blocks, { theme: 'dark' }) : '';
    slideDivs +=
      '<div id="' + uid + 's_' + _esc(sid) + '" class="' + uid + 'sl" ' +
      'style="display:none;width:100%;min-height:100vh;padding-bottom:80px;box-sizing:border-box;">' +
      content + '</div>';
  });

  // Nav pill buttons
  var navBtns = '';
  slides.forEach(function(slide, idx) {
    var sid = _esc(slide.id || String(idx));
    navBtns +=
      '<button id="' + uid + 'n_' + sid + '" ' +
      'onclick="' + uid + 'go(\'' + sid + '\')" ' +
      'style="font-family:\'Courier New\',monospace;font-size:0.75rem;padding:6px 14px;' +
      'border-radius:6px;border:1px solid rgba(255,255,255,0.1);background:transparent;' +
      'color:rgba(255,255,255,0.5);cursor:pointer;white-space:nowrap;transition:all 0.15s;">' +
      _esc(slide.label || slide.id || String(idx)) + '</button>';
  });

  var firstId = _esc(slides[0].id || '0');
  var fadeCss = transition === 'fade' ?
    '@keyframes ' + uid + 'fi{from{opacity:0}to{opacity:1}}' +
    '.' + uid + 'sl[style*="block"]{animation:' + uid + 'fi 0.35s ease;}' : '';

  return '<style>' +
    fadeCss +
    // Break out of asw-page's 860px max-width container — playbook is always full-page
    'html,body{margin:0;padding:0;overflow-x:hidden;}' +
    '.asw-page{max-width:none!important;padding:0!important;margin:0!important;}' +
    '.asw-page>h1{display:none!important;}' +
    '</style>' +
    '<div style="width:100vw;background:#050810;">' +
    sharedHtml +
    slideDivs +
    '<div id="' + uid + 'nav" style="position:fixed;bottom:20px;left:50%;transform:translateX(-50%);' +
    'display:flex;gap:8px;z-index:9999;flex-wrap:wrap;justify-content:center;' +
    'background:rgba(0,0,0,0.8);border:1px solid rgba(0,242,255,0.18);' +
    'border-radius:10px;padding:8px 14px;backdrop-filter:blur(12px);">' +
    navBtns + '</div>' +
    '<script>(function(){' +
    'window.' + uid + 'go=function(id){' +
      'document.querySelectorAll(".' + uid + 'sl").forEach(function(e){e.style.display="none";});' +
      'document.querySelectorAll("#' + uid + 'nav button").forEach(function(btn){' +
        'btn.style.background="transparent";btn.style.color="rgba(255,255,255,0.5)";' +
        'btn.style.borderColor="rgba(255,255,255,0.1)";' +
      '});' +
      'var el=document.getElementById("' + uid + 's_"+id);' +
      'if(el)el.style.display="block";' +
      'var bn=document.getElementById("' + uid + 'n_"+id);' +
      'if(bn){bn.style.background="rgba(0,242,255,0.18)";bn.style.color="#00f2ff";' +
        'bn.style.borderColor="rgba(0,242,255,0.5)";}' +
      'window.scrollTo(0,0);' +
      'if(window.history)window.history.replaceState(null,"","#"+id);' +
    '};' +
    'var hash=window.location.hash.slice(1);' +
    'window.' + uid + 'go(hash||"' + firstId + '");' +
    '})();<\/script>' +
    '</div>';
};
