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
  var zoomIn        = b.zoom_in        || 0;
  var zoomPeriod    = b.zoom_period    || 20000;
  var spotlight     = b.spotlight      || false;
  var splDwell      = b.spotlight_dwell || 3000;
  var splIntro      = b.spotlight_intro || 3500;  // ms of wide runway view before first lock
  var splCount      = b.spotlight_count || 10;
  var locked        = b.lockedCallsign || '';
  var panelType     = b.panel_type     || '';
  var panelTitle    = b.panel_title    || '';
  var dataSource    = b.data_source    || '';
  var weatherSource = b.weather_source || '';
  var chyronTitle  = b.chyron_title    || 'LFBO TMA';
  var chyronSub    = b.chyron_subtitle || 'Toulouse Blagnac Approach Control';
  var tickerText   = b.ticker_text  || '✈ TOULOUSE AIRSPACE ✈';
  var tickerSpeed  = b.ticker_speed || 45;
  var titleSize    = b.title_size   || (fullscreen ? 'clamp(1rem,2.2vw,1.4rem)' : 'clamp(0.75rem,1.8vw,1rem)');
  var subSize      = b.sub_size     || (fullscreen ? '0.82rem' : '0.65rem');
  var tickerSize   = b.ticker_size  || (fullscreen ? '0.88rem' : '0.72rem');
  var tickerH      = fullscreen ? '44px' : '32px';
  var showSlate    = b.show_slate   || false;
  var slateTitle   = b.slate_title  || 'CALIBRATING';
  var slateSub     = b.slate_description || 'Booting radar...';
  var pollQ        = b.poll_question    || '';
  var pollQid      = b.poll_question_id || '';
  var pollOpts     = b.poll_options     || [];
  var pollVals     = b.poll_values      || [];

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

  // ── Poll overlay ──────────────────────────────────────────────────────────
  // Live interactive mode when poll_question_id is set; falls back to static display.
  var pollHtml = '';
  if (pollQ && pollOpts.length > 0) {
    if (pollQid) {
      // ── Interactive live poll (Firestore-backed) ─────────────────────────
      var puid = 'atcpl' + uid;
      var pollBtns = '', pollBars = '';
      for (var pi = 0; pi < pollOpts.length; pi++) {
        var opt = pollOpts[pi];
        var val   = (typeof opt === 'object') ? (opt.value || '') : opt;
        var lbl   = (typeof opt === 'object') ? (opt.label || opt.value || '') : opt;
        var emoji = (typeof opt === 'object') ? (opt.emoji || '') : '';
        pollBtns +=
          '<button onclick="window[\'' + puid + '\'].vote(\'' + _esc(val) + '\')" ' +
          'style="flex:1;padding:9px 6px;border:1px solid rgba(0,242,255,0.35);border-radius:6px;' +
          'background:transparent;color:rgba(255,255,255,0.85);cursor:pointer;' +
          'font-size:0.7rem;font-weight:700;font-family:\'Courier New\',monospace;' +
          'letter-spacing:0.06em;transition:all 0.15s;" ' +
          'onmouseover="this.style.background=\'rgba(0,242,255,0.12)\'" ' +
          'onmouseout="this.style.background=\'transparent\'">' +
          _esc(emoji) + ' ' + _esc(lbl) + '</button>';
        pollBars +=
          '<div style="margin:5px 0;">' +
          '<div style="display:flex;justify-content:space-between;font-size:0.58rem;color:rgba(255,255,255,0.45);margin-bottom:2px;">' +
          '<span>' + _esc(emoji) + ' ' + _esc(lbl) + '</span>' +
          '<span id="' + puid + 'n_' + _esc(val) + '">—</span></div>' +
          '<div style="background:rgba(255,255,255,0.07);border-radius:100px;height:4px;">' +
          '<div id="' + puid + 'b_' + _esc(val) + '" style="height:100%;border-radius:100px;' +
          'background:#00f2ff;width:0%;transition:width 0.45s;box-shadow:0 0 6px #00f2ff66;"></div></div></div>';
      }
      pollHtml =
        '<div style="position:absolute;right:12px;bottom:' + tickerH + ';margin-bottom:8px;width:258px;' +
        'background:rgba(0,6,18,0.92);border:1px solid rgba(0,242,255,0.3);border-radius:8px;' +
        'padding:14px;backdrop-filter:blur(10px);font-family:\'Courier New\',monospace;">' +
        '<div style="font-size:0.58rem;color:#00f2ff;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:10px;">' + _esc(pollQ) + '</div>' +
        '<div id="' + puid + 'btns" style="display:flex;gap:6px;">' + pollBtns + '</div>' +
        '<div id="' + puid + 'results" style="display:none;margin-top:8px;">' + pollBars +
        '<div id="' + puid + 'total" style="font-size:0.53rem;color:rgba(255,255,255,0.22);text-align:right;margin-top:6px;"></div>' +
        '</div></div>' +
        '<script>(function(){' +
        'var voted=false;' +
        'window["' + puid + '"]={' +
        'vote:function(opt){' +
          'if(voted)return;voted=true;' +
          'document.getElementById("' + puid + 'btns").style.opacity="0.35";' +
          'document.getElementById("' + puid + 'btns").style.pointerEvents="none";' +
          'if(typeof google!=="undefined"&&google.script){' +
            'google.script.run' +
              '.withSuccessHandler(function(t){window["' + puid + '"].show(t);})' +
              '.withFailureHandler(function(){})' +
              '.submitPollVote("' + _esc(pollQid) + '",opt);' +
          '}' +
        '},' +
        'show:function(tally){' +
          'tally=tally||{};' +
          'var keys=Object.keys(tally);' +
          'var total=keys.reduce(function(s,k){return s+(tally[k]||0);},0);' +
          'keys.forEach(function(k){' +
            'var n=document.getElementById("' + puid + 'n_"+k);' +
            'var bar=document.getElementById("' + puid + 'b_"+k);' +
            'if(n)n.textContent=tally[k]||0;' +
            'if(bar)bar.style.width=(total?Math.round((tally[k]||0)/total*100):0)+"%";' +
          '});' +
          'var t=document.getElementById("' + puid + 'total");' +
          'if(t)t.textContent=total>0?total+" vote"+(total!==1?"s":"")+" total":"Thanks for voting!";' +
          'document.getElementById("' + puid + 'btns").style.display="none";' +
          'document.getElementById("' + puid + 'results").style.display="block";' +
        '}}' +
        '})();<\/script>';
    } else {
      // ── Static display poll (pre-computed percentages) ───────────────────
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
        '<div style="position:absolute;right:12px;bottom:' + tickerH + ';margin-bottom:8px;width:258px;' +
        'background:rgba(0,8,20,0.88);border:1px solid rgba(0,242,255,0.25);border-radius:8px;' +
        'padding:14px;backdrop-filter:blur(6px);font-family:\'Courier New\',monospace;">' +
        '<div style="font-size:0.65rem;color:#00f2ff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">' + _esc(pollQ) + '</div>' +
        pollRows +
        '<div style="font-size:0.6rem;color:rgba(255,255,255,0.25);margin-top:8px;">' + totalVotes + ' votes</div>' +
        '</div>';
    }
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
      '<div style="font-size:' + titleSize + ';font-weight:700;color:#00f2ff;letter-spacing:0.08em;text-transform:uppercase;">' + _esc(chyronTitle) + '</div>' +
      '<div id="' + uid + 'csub" style="font-size:' + subSize + ';color:rgba(255,255,255,0.55);letter-spacing:0.04em;margin-top:2px;">' + _esc(chyronSub) + '</div>' +
    '</div>' +

    // Weather panel + data status indicator — top right (3× size)
    '<div style="position:absolute;top:14px;right:14px;display:flex;flex-direction:column;gap:10px;align-items:flex-end;">' +
      '<div id="' + uid + 'wx" style="' +
        'background:rgba(0,0,0,0.7);border:1px solid rgba(0,242,255,0.25);padding:18px 28px;border-radius:10px;' +
        'backdrop-filter:blur(6px);font-size:1.6rem;color:rgba(255,255,255,0.75);line-height:1.7;">' +
        '<div style="color:#00ff41;font-size:1.2rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;">LFBO METAR</div>' +
        '<div>WIND &nbsp;<span style="color:#fff;font-weight:600;" id="' + uid + 'wind">—</span></div>' +
        '<div>TEMP &nbsp;<span style="color:#fff;font-weight:600;" id="' + uid + 'temp">—</span></div>' +
        '<div>QNH &nbsp;&nbsp;<span style="color:#fff;font-weight:600;" id="' + uid + 'qnh">—</span></div>' +
      '</div>' +
      // Data source status pill — starts SIM/red, flips to LIVE/green when adsb_feed dispatches
      '<div id="' + uid + 'status" style="' +
        'display:inline-flex;align-items:center;gap:10px;padding:8px 24px;border-radius:100px;' +
        'background:rgba(255,59,48,0.12);border:1px solid rgba(255,59,48,0.3);' +
        'font-family:\'Courier New\',monospace;font-size:1.4rem;letter-spacing:0.1em;color:#ff3b30;">' +
        '<span id="' + uid + 'sdot" style="width:14px;height:14px;border-radius:50%;' +
          'background:#ff3b30;box-shadow:0 0 10px #ff3b30;flex-shrink:0;"></span>' +
        '<span id="' + uid + 'slbl">SIM</span>' +
      '</div>' +
    '</div>' +

    // Supervisor / target panel
    panelHtml +
    pollHtml +

    // Ticker — bottom bar
    '<div style="position:absolute;bottom:0;left:0;right:0;height:' + tickerH + ';' +
      'background:rgba(0,0,0,0.9);border-top:1px solid rgba(0,242,255,0.2);' +
      'overflow:hidden;display:flex;align-items:center;">' +
      '<div style="flex-shrink:0;padding:0 12px;font-size:' + (fullscreen ? '0.72rem' : '0.58rem') + ';color:#00f2ff;' +
        'font-weight:700;letter-spacing:0.14em;border-right:1px solid rgba(0,242,255,0.25);white-space:nowrap;">LFBO ATC</div>' +
      '<div style="overflow:hidden;flex:1;">' +
        '<div id="' + uid + 'tkr" style="white-space:nowrap;font-size:' + tickerSize + ';font-weight:700;color:rgba(255,255,255,0.88);' +
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
      (spotlight
        ? (function(){
            // Sort server-side — embed as pure integer arrays (zero string-encoding risk)
            var orig = JSON.parse(FLIGHTS);
            var fl = orig.slice().sort(function(a,b){return a.dist-b.dist;}).slice(0, splCount);
            return 'var ZOOM=4;var NM=Math.min(W,H)*0.42/ZOOM;' + // start zoomed into runway
                   'var LOCKED=null;';
          })()
        : 'var ZOOM_TIGHT=' + (zoomIn || zoom) + ';' +
          'var ZOOM_PERIOD=' + zoomPeriod + ';' +
          'var _ZOOM_ANIM=' + (zoomIn ? 'true' : 'false') + ';' +
          'var _ZOOM_T0=Date.now()-ZOOM_PERIOD/2;' +
          'var ZOOM=_ZOOM_ANIM?ZOOM_TIGHT:ZOOM_WIDE;' +
          'var NM=Math.min(W,H)*0.42/ZOOM;' +
          'var LOCKED="' + _esc(locked) + '";'
      ) +
      'var FLIGHTS=' + FLIGHTS + ';' +
      'FLIGHTS.forEach(function(f){' +
        'f.px=CX+Math.sin(f.brg*Math.PI/180)*f.dist*NM;' +
        'f.py=CY-Math.cos(f.brg*Math.PI/180)*f.dist*NM;' +
        'f.hdg=(f.brg+180)%360;' +
        'f.vx=-Math.sin(f.brg*Math.PI/180)*0.12;' +
        'f.vy= Math.cos(f.brg*Math.PI/180)*0.12;' +
        'f.trail=[];f.tick=0;' +
      '});' +
      // Spotlight: drive rotation with setInterval (avoids per-frame index crash risk)
      (spotlight
        ? (function(){
            // Build callsigns via String.fromCharCode — zero string-encoding risk
            var orig = JSON.parse(FLIGHTS);
            var fl = orig.slice().sort(function(a,b){return a.dist-b.dist;}).slice(0,splCount);
            var distArr = fl.map(function(f){return f.dist;});
            var codeArr = fl.map(function(f){
              return 'String.fromCharCode(' + f.c.split('').map(function(ch){return ch.charCodeAt(0);}).join(',') + ')';
            });
            return 'var _SPL_CALLS=[' + codeArr.join(',') + '];' +
                   'var _SPL_DISTS=[' + distArr.join(',') + '];' +
                   'var _SPL_I=0;' +
                   // Runway intro: wide view for splIntro ms, then engage spotlight cycling
                   'LOCKED=null;' +
                   'setTimeout(function(){' +
                     'LOCKED=_SPL_CALLS[0];' +
                     'setInterval(function(){' +
                       '_SPL_I=(_SPL_I+1)%_SPL_CALLS.length;' +
                       'LOCKED=_SPL_CALLS[_SPL_I];' +
                     '},' + splDwell + ');' +
                   '},' + splIntro + ');' +
                   // Click-to-lock overrides auto cycling
                   'c.onclick=function(e){' +
                     'var r=c.getBoundingClientRect();' +
                     'var mx=(e.clientX-r.left)*(c.width/r.width),my=(e.clientY-r.top)*(c.height/r.height);' +
                     'var best=null,bd=50;' +
                     'for(var _i=0;_i<FLIGHTS.length;_i++){var _f=FLIGHTS[_i],_d=Math.sqrt((_f.px-mx)*(_f.px-mx)+(_f.py-my)*(_f.py-my));if(_d<bd){bd=_d;best=_f;}}' +
                     'if(best){LOCKED=best.c;if(window._a2uiFlightClick)window._a2uiFlightClick({callsign:best.c,alt:best.alt,spd:best.spd,hdg:best.hdg,lat:best.lat,lon:best.lon,status:best.status});}' +
                   '};';
          })()
        : // Non-spotlight: always allow click-to-lock any aircraft
          'c.onclick=function(e){' +
            'var r=c.getBoundingClientRect();' +
            'var mx=(e.clientX-r.left)*(c.width/r.width),my=(e.clientY-r.top)*(c.height/r.height);' +
            'var best=null,bd=50;' +
            'for(var _i=0;_i<FLIGHTS.length;_i++){var _f=FLIGHTS[_i],_d=Math.sqrt((_f.px-mx)*(_f.px-mx)+(_f.py-my)*(_f.py-my));if(_d<bd){bd=_d;best=_f;}}' +
            'if(best){LOCKED=best.c;if(window._a2uiFlightClick)window._a2uiFlightClick({callsign:best.c,alt:best.alt,spd:best.spd,hdg:best.hdg,lat:best.lat,lon:best.lon,status:best.status});}' +
          '};'
      ) +
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
          // clip in NM units so intro zoom-in (NM changes) never discards flights that are in range
          'if(Math.sqrt(dx*dx+dy*dy)/NM>ZOOM_WIDE*1.1)return;' +
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
        // When live data arrives with spotlight active, cycle through 10 closest real callsigns.
        // In non-spotlight mode, if the configured lockedCallsign isn't in the real feed, pick the nearest.
        'if(typeof _SPL_CALLS!=="undefined"&&FLIGHTS.length>0){' +
          'var _sorted=FLIGHTS.slice().sort(function(a,b){' +
            'var da=Math.sqrt((a.px-CX)*(a.px-CX)+(a.py-CY)*(a.py-CY));' +
            'var db=Math.sqrt((b.px-CX)*(b.px-CX)+(b.py-CY)*(b.py-CY));' +
            'return da-db;' +
          '});' +
          '_SPL_CALLS=_sorted.slice(0,10).map(function(f){return f.c;});' +
          '_SPL_I=Math.min(_SPL_I||0,_SPL_CALLS.length-1);' +
          'if(!LOCKED||FLIGHTS.every(function(f){return f.c!==LOCKED;})){LOCKED=_SPL_CALLS[0];}' +
        '}else if(LOCKED&&FLIGHTS.length>0&&FLIGHTS.every(function(f){return f.c!==LOCKED;})){' +
          // lockedCallsign from config isn't in the real ADS-B feed — transfer lock to nearest flight
          'var _nr=FLIGHTS.slice().sort(function(a,b){var da=Math.sqrt((a.px-CX)*(a.px-CX)+(a.py-CY)*(a.py-CY));var db=Math.sqrt((b.px-CX)*(b.px-CX)+(b.py-CY)*(b.py-CY));return da-db;});' +
          'LOCKED=_nr[0].c;' +
        '}' +
        'setDataStatus(FLIGHTS.length>0,FLIGHTS.length);' +
      '}' +

      // ── A2UI-State: inbound flight data via direct global function ───────
      'window._a2uiInboundFlights=function(data){if(Array.isArray(data))updateFlightsFromFeed(data);};' +

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
        'requestAnimationFrame(frame);' +
        // Resize canvas if it was initialised while hidden (slide was display:none)
        'var _cw=c.offsetWidth||window.innerWidth||700,_ch=c.offsetHeight||window.innerHeight||520;' +
        'if(_cw!==c.width||_ch!==c.height){c.width=_cw;c.height=_ch;W=_cw;H=_ch;CX=W/2;CY=H*0.48;}' +
        (spotlight
          ? // zoom to 30% wider than locked flight's live distance, min 3nm, fallback to wide
            'var _lf=null;for(var _li=0;_li<FLIGHTS.length;_li++){if(FLIGHTS[_li].c===LOCKED){_lf=FLIGHTS[_li];break;}}' +
            'var _sd=_lf?Math.sqrt((_lf.px-CX)*(_lf.px-CX)+(_lf.py-CY)*(_lf.py-CY))/NM:ZOOM_WIDE;' +
            'var _zTgt=LOCKED&&_lf?Math.max(3,Math.min(_sd*1.3,ZOOM_WIDE)):Math.min(ZOOM_WIDE,20);' +
            'ZOOM+=(_zTgt-ZOOM)*0.08;' +
            'NM=Math.min(W,H)*0.42/ZOOM;'
          : 'if(_ZOOM_ANIM){' +
              'var _t=((Date.now()-_ZOOM_T0)%ZOOM_PERIOD)/ZOOM_PERIOD;' +
              'var _e=(1-Math.cos(Math.PI*2*_t))/2;' +
              'ZOOM=ZOOM_WIDE-(ZOOM_WIDE-ZOOM_TIGHT)*_e;' +
              'NM=Math.min(W,H)*0.42/ZOOM;' +
            '}'
        ) +
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
            // Reproject from lat/lon so zoom animation repositions live aircraft correctly
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
          // Reticle for locked callsign — large pulsing ring so it's unmissable
          'var isLocked=LOCKED&&f.c===LOCKED;' +
          'if(isLocked){' +
            'var _pulse=0.5+0.5*Math.sin(Date.now()/200);' + // 0..1 pulse
            'var _r1=28+_pulse*14;' + // 28–42px
            'ctx.save();ctx.translate(f.px,f.py);' +
            'ctx.strokeStyle="rgba(0,242,255,"+(0.9-_pulse*0.3)+")";ctx.lineWidth=2;' +
            'ctx.beginPath();ctx.arc(0,0,_r1,0,Math.PI*2);ctx.stroke();' +
            'ctx.strokeStyle="rgba(0,242,255,0.25)";ctx.lineWidth=1;' +
            'ctx.beginPath();ctx.arc(0,0,_r1+10,0,Math.PI*2);ctx.stroke();' +
            'ctx.restore();' +
          '}' +
          // Aircraft silhouette (top-down plan view, oriented by heading)
          'if(blink||isLocked){' +
            'var fc=isLocked?"#00f2ff":f.col;' +
            'var _ps=Math.max(3.5,4.5*Math.sqrt(ZOOM_WIDE/ZOOM));' +
            'drawPlane(ctx,f.px,f.py,f.hdg||0,isLocked?_ps*1.6:_ps,fc,isLocked);' +
          '}' +
          // Labels: rich card for spotlight/locked, compact otherwise
          'var al=getAL(f.c);' +
          'if(isLocked){' +
            'var _cw=168,_ch=72;' +
            'var _cx=f.px+20,_cy=f.py-40;' +
            'if(_cx+_cw>W-8)_cx=f.px-_cw-12;' +
            'if(_cy<8)_cy=f.py+12;' +
            'ctx.save();' +
            'ctx.fillStyle="rgba(0,8,24,0.88)";ctx.strokeStyle="#00f2ff";ctx.lineWidth=1.2;' +
            'ctx.shadowBlur=10;ctx.shadowColor="rgba(0,242,255,0.35)";' +
            'ctx.beginPath();ctx.roundRect(_cx,_cy,_cw,_ch,5);ctx.fill();ctx.stroke();' +
            'ctx.shadowBlur=0;' +
            // callsign large
            'ctx.fillStyle="#00f2ff";ctx.font="bold 13px \'Courier New\'";ctx.textAlign="left";' +
            'ctx.fillText(f.c,_cx+8,_cy+18);' +
            // aircraft type top-right
            'ctx.fillStyle="rgba(0,242,255,0.5)";ctx.font="9px \'Courier New\'";ctx.textAlign="right";' +
            'ctx.fillText(f.t||"",_cx+_cw-8,_cy+18);' +
            // airline name
            'if(al.n){ctx.fillStyle="rgba(255,255,255,0.65)";ctx.font="9px \'Courier New\'";ctx.textAlign="left";ctx.fillText(al.n,_cx+8,_cy+32);}' +
            // FL + speed
            'ctx.fillStyle="rgba(0,242,255,0.8)";ctx.font="10px \'Courier New\'";' +
            'ctx.fillText("FL"+Math.round((f.alt||0)/100)+"  ▸  "+(f.spd||0)+"kt",_cx+8,_cy+48);' +
            // status bar
            'ctx.fillStyle="#00ff41";ctx.font="bold 8px \'Courier New\'";' +
            'ctx.fillText(f.status||"",_cx+8,_cy+64);' +
            'ctx.restore();' +
          '}else{' +
            'var lx=f.px+14,ly=f.py-4;' +
            'ctx.fillStyle=f.col;ctx.font="9px \'Courier New\'";ctx.textAlign="left";' +
            'ctx.fillText(f.c,lx,ly);' +
            'ctx.fillStyle="rgba(255,255,255,0.45)";ctx.font="8px \'Courier New\'";' +
            'ctx.fillText("FL"+Math.round((f.alt||0)/100)+"  "+(f.spd||0)+"kt",lx,ly+10);' +
            'if(al.n){ctx.fillStyle="rgba(255,255,255,0.3)";ctx.font="7.5px \'Courier New\'";ctx.fillText(al.n,lx,ly+20);}' +
          '}' +
        '});' +

        // Separation conflict vectors (O(N²), amber dashed lines + badge)
        'checkSeparation(ctx,FLIGHTS);' +

        // Country boundary overlay (subtle, helps orient position within FIR)
        'drawCountryOverlay(ctx);' +

        // Overlay corner — mode / count label + zoom readout
        'ctx.fillStyle="rgba(0,242,255,0.15)";ctx.font="8px \'Courier New\'";ctx.textAlign="right";' +
        'ctx.fillText(FLIGHTS.length + " TFC · RWY 32L/R ACTIVE",W-12,H-38);' +
        // Debug readout top-left — visible callsign + zoom so any screenshot confirms state
        'ctx.fillStyle="rgba(0,242,255,0.55)";ctx.font="9px \'Courier New\'";ctx.textAlign="left";' +
        'ctx.fillText((LOCKED||"--")+" Z:"+Math.round(ZOOM)+"nm",12,16);' +

        // Minimap inset — country shape + TMA extent circle
        'drawMiniMap(ctx);' +

        'isoYaw+=0.008;' +
        'updateFlightList();' +
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

  // Nav pill buttons — solid fill style, per-slide accent when active
  var navBtns = '';
  slides.forEach(function(slide, idx) {
    var sid   = _esc(slide.id || String(idx));
    var sacc  = _esc(slide.accent || '#00f2ff');
    navBtns +=
      '<button id="' + uid + 'n_' + sid + '" ' +
      'data-acc="' + sacc + '" ' +
      'onclick="' + uid + 'go(\'' + sid + '\')" ' +
      'style="font-family:\'Courier New\',monospace;font-size:0.72rem;font-weight:700;padding:9px 20px;' +
      'border-radius:4px;border:none;background:rgba(255,255,255,0.06);' +
      'color:rgba(255,255,255,0.4);cursor:pointer;white-space:nowrap;letter-spacing:0.1em;transition:all 0.15s;">' +
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
    // duration/next map for auto-advance
    'var _dur=' + JSON.stringify((function() {
      var d = {};
      slides.forEach(function(s) { if (s.duration) d[s.id || ''] = s.duration; });
      return d;
    })()) + ';' +
    'var _nxt=' + JSON.stringify((function() {
      var n = {};
      slides.forEach(function(s, i) {
        var nextId = s.next || (slides[(i + 1) % slides.length] || {}).id || '0';
        n[s.id || ''] = nextId;
      });
      return n;
    })()) + ';' +
    'var _tmr=null;' +
    'window.' + uid + 'go=function(id){' +
      'if(_tmr)clearTimeout(_tmr);' +
      'document.querySelectorAll(".' + uid + 'sl").forEach(function(e){e.style.display="none";});' +
      'document.querySelectorAll("#' + uid + 'nav button").forEach(function(btn){' +
        'btn.style.background="rgba(255,255,255,0.06)";btn.style.color="rgba(255,255,255,0.4)";' +
      '});' +
      'var el=document.getElementById("' + uid + 's_"+id);' +
      'if(el)el.style.display="block";' +
      'var bn=document.getElementById("' + uid + 'n_"+id);' +
      'if(bn){var acc=bn.getAttribute("data-acc")||"#00f2ff";' +
        'bn.style.background=acc;bn.style.color="#000";}' +
      'window.scrollTo(0,0);' +
      'if(window.history)window.history.replaceState(null,"","#"+id);' +
      'if(_dur[id])_tmr=setTimeout(function(){window.' + uid + 'go(_nxt[id]);},_dur[id]);' +
    '};' +
    'window._A2UI_GO=window.' + uid + 'go;' +
    'var hash=window.location.hash.slice(1);' +
    'window.' + uid + 'go(hash||"' + firstId + '");' +
    '})();<\/script>' +
    '</div>';
};

// ── fids_board ────────────────────────────────────────────────────────────────
// Airport split-flap departure/arrival board.
// Connects to adsb_feed via data_source to update status of real flights.
// Falls back to a simulated LFBO schedule when no live data is available.
//
// Fields:
//   mode          — 'departures' | 'arrivals' (default 'departures')
//   airport       — ICAO code displayed top-right (default 'LFBO')
//   airport_name  — full name displayed (default 'TOULOUSE-BLAGNAC')
//   rows          — number of rows (default 10)
//   height        — px number or 'fullscreen' (default 'fullscreen')
//   data_source   — adsb_feed name to subscribe to for live callsign status
//   refresh_ms    — board refresh interval ms (default 9000)
_RENDERERS['fids_board'] = function(b) {
  var uid         = 'fids' + Math.random().toString(36).substr(2, 6);
  var mode        = b.mode === 'arrivals' ? 'arrivals' : 'departures';
  var modeLabel   = mode === 'arrivals' ? 'ARRIVÉES' : 'DÉPARTS';
  var airport     = (b.airport || 'LFBO').toUpperCase();
  var airportName = b.airport_name || 'TOULOUSE-BLAGNAC';
  var rows        = Math.min(b.rows || 10, 15);
  var fullscreen  = b.height === 'fullscreen';
  var h           = fullscreen ? '100vh' : (b.height || 600) + 'px';
  var dataSource  = b.data_source || '';
  var refreshMs   = b.refresh_ms !== undefined ? b.refresh_ms : 9000;

  // ── Simulated LFBO schedule ────────────────────────────────────────────────
  var SCHED_DEP = JSON.stringify([
    {call:'AFR7201',dest:'PARIS CDG',           gate:'D42'},
    {call:'EZY4821',dest:'LONDON GATWICK',       gate:'C18'},
    {call:'VLG2241',dest:'BARCELONA-EL PRAT',   gate:'A07'},
    {call:'RYR8432',dest:'MILAN BERGAMO',        gate:'B22'},
    {call:'IBE3421',dest:'MADRID BARAJAS',       gate:'D31'},
    {call:'TAP456', dest:'LISBOA HUMBERTO D.',   gate:'C09'},
    {call:'AFR6129',dest:'NICE CÔTE D\'AZUR',   gate:'A15'},
    {call:'EZY6234',dest:'GENÈVE',               gate:'B08'},
    {call:'RYR109B',dest:'PORTO FRANCISCO S.',   gate:'C24'},
    {call:'TO5421', dest:'AMSTERDAM SCHIPHOL',   gate:'D12'},
    {call:'VLG8832',dest:'ROME FIUMICINO',       gate:'A03'},
    {call:'RYR2248',dest:'MARRAKECH MENARA',     gate:'B17'},
    {call:'HOP7734',dest:'LYON SAINT-EXUPÉRY',  gate:'D38'},
    {call:'EZY3112',dest:'BERLIN BRANDEBOURG',   gate:'C11'},
    {call:'RAM4521',dest:'CASABLANCA MED V',     gate:'A19'}
  ]);

  var SCHED_ARR = JSON.stringify([
    {call:'BAW345', dest:'LONDON HEATHROW',      gate:'D44'},
    {call:'DLH892', dest:'FRANCFORT AM MAIN',    gate:'C20'},
    {call:'KLM2187',dest:'AMSTERDAM SCHIPHOL',   gate:'A09'},
    {call:'AZA211', dest:'ROME FIUMICINO',       gate:'B24'},
    {call:'SWR1834',dest:'ZURICH KLOTEN',        gate:'D33'},
    {call:'BEL3712',dest:'BRUXELLES ZAVENTEM',   gate:'C10'},
    {call:'TUI6623',dest:'PALMA DE MAJORQUE',    gate:'A17'},
    {call:'AFR1842',dest:'PARIS ORLY',           gate:'B10'},
    {call:'VLG4491',dest:'VALENCE MANISES',      gate:'C26'},
    {call:'RYR5523',dest:'DUBLIN',               gate:'D14'},
    {call:'EZY7781',dest:'ÉDIMBOURG',            gate:'A05'},
    {call:'TSC8834',dest:'MONTRÉAL TRUDEAU',     gate:'B19'},
    {call:'RAM974', dest:'CASABLANCA MED V',     gate:'D40'},
    {call:'AEA2812',dest:'MADRID BARAJAS',        gate:'C13'},
    {call:'THY316', dest:'ISTANBUL SABIHA',      gate:'A21'}
  ]);

  // ── Static row HTML (cells have IDs for JS updates) ────────────────────────
  var headerRow =
    '<div style="display:grid;grid-template-columns:68px 90px 1fr 140px 56px;' +
    'gap:0 2px;padding:0 12px;margin-bottom:4px;">' +
    ['HEURE','VOL', mode === 'arrivals' ? 'PROVENANCE' : 'DESTINATION','STATUT','PORTE'].map(function(h) {
      return '<div style="font-size:0.52rem;color:rgba(245,158,11,0.45);letter-spacing:0.18em;padding:4px 6px;">' + h + '</div>';
    }).join('') + '</div>';

  var rowDivs = '';
  for (var ri = 0; ri < rows; ri++) {
    rowDivs +=
      '<div id="' + uid + 'r' + ri + '" style="display:grid;grid-template-columns:68px 90px 1fr 140px 56px;' +
      'gap:0 2px;padding:0 12px;border-top:1px solid rgba(245,158,11,0.07);">' +
      '<div id="' + uid + 'r' + ri + '_t" class="' + uid + 'cell" style="font-size:0.82rem;color:rgba(245,158,11,0.7);padding:7px 6px;">——:——</div>' +
      '<div id="' + uid + 'r' + ri + '_c" class="' + uid + 'cell" style="font-size:0.82rem;color:#fff;font-weight:700;padding:7px 6px;">————————</div>' +
      '<div id="' + uid + 'r' + ri + '_d" class="' + uid + 'cell" style="font-size:0.8rem;color:rgba(255,255,255,0.85);padding:7px 6px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">—</div>' +
      '<div id="' + uid + 'r' + ri + '_s" class="' + uid + 'cell" style="font-size:0.75rem;padding:7px 6px;"></div>' +
      '<div id="' + uid + 'r' + ri + '_g" class="' + uid + 'cell" style="font-size:0.82rem;color:rgba(245,158,11,0.8);padding:7px 6px;">—</div>' +
      '</div>';
  }

  return '<style>' +
    '@keyframes ' + uid + 'fl{0%{transform:perspective(300px) rotateX(0deg);opacity:1}' +
      '45%{transform:perspective(300px) rotateX(-90deg);opacity:0}' +
      '55%{transform:perspective(300px) rotateX(90deg);opacity:0}' +
      '100%{transform:perspective(300px) rotateX(0deg);opacity:1}}' +
    '.' + uid + 'flip{animation:' + uid + 'fl 0.42s ease-in-out;}' +
    '.' + uid + 'cell{font-family:"Courier New",monospace;letter-spacing:0.05em;transition:color 0.2s;}' +
    '</style>' +
    '<div style="position:relative;background:#050400;border-radius:' + (fullscreen?'0':'10px') + ';' +
    'overflow:hidden;height:' + h + ';font-family:\'Courier New\',monospace;' +
    'display:flex;flex-direction:column;justify-content:center;">' +

    // Header
    '<div style="padding:20px 18px 12px;border-bottom:2px solid rgba(245,158,11,0.2);">' +
      '<div style="display:flex;justify-content:space-between;align-items:flex-end;">' +
        '<div>' +
          '<div style="font-size:0.52rem;color:rgba(245,158,11,0.5);letter-spacing:0.22em;margin-bottom:2px;">A2UI · TOULOUSE-BLAGNAC · INFORMATION VOLS</div>' +
          '<div style="font-size:clamp(1rem,2.2vw,1.35rem);font-weight:700;color:#f59e0b;letter-spacing:0.1em;text-transform:uppercase;">' + _esc(airportName) + '</div>' +
        '</div>' +
        '<div style="text-align:right;">' +
          '<div style="font-size:1.4rem;font-weight:900;color:#f59e0b;letter-spacing:0.08em;">' + _esc(airport) + '</div>' +
          '<div id="' + uid + 'mode" style="font-size:0.62rem;color:rgba(245,158,11,0.6);letter-spacing:0.2em;margin-top:2px;">' + _esc(modeLabel) + '</div>' +
        '</div>' +
      '</div>' +
    '</div>' +

    // Column headers
    headerRow +

    // Rows
    '<div style="flex:1;overflow:hidden;">' + rowDivs + '</div>' +

    // Bottom bar — live indicator + time
    '<div style="padding:8px 18px;border-top:1px solid rgba(245,158,11,0.12);' +
    'display:flex;justify-content:space-between;align-items:center;">' +
      '<div style="display:flex;align-items:center;gap:6px;">' +
        '<span id="' + uid + 'sdot" style="display:inline-block;width:6px;height:6px;border-radius:50%;' +
          'background:#f59e0b;box-shadow:0 0 8px #f59e0b;animation:' + uid + 'blink 2s infinite;"></span>' +
        '<span style="font-size:0.58rem;color:rgba(245,158,11,0.6);letter-spacing:0.14em;" id="' + uid + 'src">DONNÉES SIMULÉES</span>' +
      '</div>' +
      '<div id="' + uid + 'clk" style="font-size:0.78rem;color:rgba(245,158,11,0.7);letter-spacing:0.1em;font-weight:700;"></div>' +
    '</div>' +

    '</div>' +

    '<style>@keyframes ' + uid + 'blink{0%,100%{opacity:1;}50%{opacity:0.25;}}</style>' +

    '<script>(function(){' +
      'var SCHED=' + (mode === 'arrivals' ? SCHED_ARR : SCHED_DEP) + ';' +
      'var ROWS=' + rows + ';' +
      'var LIVE_SCHED=null;' +
      'var ARR_MODE=' + (mode === 'arrivals' ? 'true' : 'false') + ';' +
      'var STATUSES_DEP=["À L\'HEURE","À L\'HEURE","À L\'HEURE","EMBARQUEMENT","EMBARQUEMENT","EN COURS","RETARDÉ"];' +
      'var STATUSES_ARR=["À L\'HEURE","À L\'HEURE","ATTERRI","ATTERRI","DÉBARQUEMENT","EN APPROCHE","RETARDÉ"];' +
      'var STATUSES=' + (mode === 'arrivals' ? 'STATUSES_ARR' : 'STATUSES_DEP') + ';' +
      'var STATUS_COLORS={"À L\'HEURE":"#22c55e","EMBARQUEMENT":"#00f2ff","EN COURS":"#00f2ff","RETARDÉ":"#ef4444","EN ROUTE":"#a3a3a3","ATTERRI":"#22c55e","DÉBARQUEMENT":"#00f2ff","EN APPROCHE":"#f59e0b","SURVEILLANCE":"#f59e0b"};' +
      // Airline prefix → likely city for display hint
      'var AIRLINE_MAP={"AFR":"PARIS CDG","EZY":"LONDON GATWICK","RYR":"DUBLIN","BAW":"LONDON HEATHROW","DLH":"FRANCFORT","KLM":"AMSTERDAM","VLG":"BARCELONE","IBE":"MADRID","TAP":"LISBONNE","SWR":"ZURICH","BEL":"BRUXELLES","TUI":"PALMA","RAM":"CASABLANCA","THY":"ISTANBUL","TSC":"MONTRÉAL","HOP":"PARIS ORLY","AZA":"ROME","TO_":"AMSTERDAM","AEA":"MADRID","EJU":"AMSTERDAM"};' +

      // Clock
      'function tick(){' +
        'var n=new Date();' +
        'var h=n.getHours().toString().padStart(2,"0");' +
        'var m=n.getMinutes().toString().padStart(2,"0");' +
        'var s=n.getSeconds().toString().padStart(2,"0");' +
        'var el=document.getElementById("' + uid + 'clk");' +
        'if(el)el.textContent=h+":"+m+":"+s+" LT";' +
      '}' +
      'setInterval(tick,1000);tick();' +

      // Flip animation helper
      'function flipCell(el,val,color){' +
        'if(!el)return;' +
        'el.classList.add("' + uid + 'flip");' +
        'setTimeout(function(){' +
          'el.textContent=val;' +
          'if(color)el.style.color=color;' +
        '},210);' +
        'setTimeout(function(){el.classList.remove("' + uid + 'flip");},440);' +
      '}' +

      // Build board rows — live ADS-B data when available, simulated fallback
      'function buildRows(){' +
        'var now=new Date();' +
        'var out=[];' +
        'var h=now.getHours().toString().padStart(2,"0");' +
        'var m=now.getMinutes().toString().padStart(2,"0");' +
        'if(LIVE_SCHED&&LIVE_SCHED.length){' +
          // Live mode: real aircraft from ADS-B feed
          'for(var i=0;i<Math.min(ROWS,LIVE_SCHED.length);i++){' +
            'var s=LIVE_SCHED[i];' +
            'out.push({t:h+":"+m,c:s.call,d:s.dest,s:s.status,g:s.gate});' +
          '}' +
        '}else{' +
          // Simulated fallback
          'for(var i=0;i<ROWS;i++){' +
            'var sched=SCHED[i%SCHED.length];' +
            'var dep=new Date(now.getTime()+(ARR_MODE?(i*4-16)*60000:(i*5+2)*60000));' +
            'var hh=dep.getHours().toString().padStart(2,"0");' +
            'var mm=dep.getMinutes().toString().padStart(2,"0");' +
            'var st=i===0?"EN COURS":i===1?"EMBARQUEMENT":STATUSES[i%STATUSES.length];' +
            'out.push({t:hh+":"+mm,c:sched.call,d:sched.dest,s:st,g:sched.gate});' +
          '}' +
        '}' +
        'return out;' +
      '}' +

      // Set a cell directly (no animation) — used for initial render
      'function setCell(el,val,color){if(!el)return;el.textContent=val;if(color)el.style.color=color;}' +

      // Update all rows — direct set on first render, flip animation on updates
      'var _rows=null;' +
      'function updateBoard(){' +
        'var next=buildRows();' +
        'var first=!_rows;' +
        'for(var i=0;i<ROWS;i++){' +
          'var prev=_rows?_rows[i]:{};' +
          'var row=next[i];' +
          'var et=document.getElementById("' + uid + 'r"+i+"_t");' +
          'var ec=document.getElementById("' + uid + 'r"+i+"_c");' +
          'var ed=document.getElementById("' + uid + 'r"+i+"_d");' +
          'var es=document.getElementById("' + uid + 'r"+i+"_s");' +
          'var eg=document.getElementById("' + uid + 'r"+i+"_g");' +
          'if(first){' +
            // First render: set directly (slide may be hidden, animations won't run)
            'setCell(et,row.t,"rgba(245,158,11,0.7)");' +
            'setCell(ec,row.c,"#ffffff");' +
            'setCell(ed,row.d,"rgba(255,255,255,0.85)");' +
            'setCell(es,row.s,STATUS_COLORS[row.s]||"#f59e0b");' +
            'setCell(eg,row.g,"rgba(245,158,11,0.8)");' +
          '}else{' +
            // Subsequent renders: staggered flip animation
            '(function(ri,r,p,_et,_ec,_ed,_es,_eg){' +
              'setTimeout(function(){' +
                'if(p.t!==r.t)flipCell(_et,r.t,"rgba(245,158,11,0.7)");' +
                'if(p.c!==r.c)flipCell(_ec,r.c,"#ffffff");' +
                'if(p.d!==r.d)flipCell(_ed,r.d,"rgba(255,255,255,0.85)");' +
                'if(p.s!==r.s)flipCell(_es,r.s,STATUS_COLORS[r.s]||"#f59e0b");' +
                'if(p.g!==r.g)flipCell(_eg,r.g,"rgba(245,158,11,0.8)");' +
              '},ri*38);' +
            '})(i,row,prev,et,ec,ed,es,eg);' +
          '}' +
        '}' +
        '_rows=next;' +
      '}' +
      'updateBoard();' +
      (refreshMs > 0 ? 'setInterval(updateBoard,' + refreshMs + ');' : '') +

      // ── OpenSky: real routes with actual destinations ─────────────────────────
      // Primary source: real callsigns + real DESTINATION/PROVENANCE from OpenSky.
      // Secondary: ADS-B onFeed() overlays live STATUS on matched callsigns.
      'window.A2UI_DATA=window.A2UI_DATA||{};' +
      'window.A2UI_CALLBACKS=window.A2UI_CALLBACKS||{};' +
      'var ADSB_STATUS={};' + // callsign → live status from ADS-B
      // ICAO airport → display name lookup
      'var AIRPORT_NAMES={' +
        '"LFPG":"PARIS CDG","LFPO":"PARIS ORLY","EGLL":"LONDON HEATHROW",' +
        '"EGKK":"LONDON GATWICK","EHAM":"AMSTERDAM","EDDF":"FRANCFORT",' +
        '"LEBL":"BARCELONE","LEMD":"MADRID","LPPT":"LISBONNE",' +
        '"LSZH":"ZURICH","EBBR":"BRUXELLES","LFRS":"NANTES",' +
        '"LFML":"MARSEILLE","LFMN":"NICE","LFLL":"LYON",' +
        '"LFBD":"BORDEAUX","LFRN":"RENNES","LFQQ":"LILLE",' +
        '"GCFV":"FUERTEVENTURA","GCLP":"LAS PALMAS","LEPA":"PALMA",' +
        '"LIRF":"ROME FCO","LIMC":"MILAN","LICJ":"PALERME",' +
        '"EGPH":"EDINBURGH","EGCC":"MANCHESTER","EIDW":"DUBLIN",' +
        '"LOWW":"VIENNE","LKPR":"PRAGUE","EPWA":"VARSOVIE",' +
        '"LTFM":"ISTANBUL","LTBA":"ISTANBUL ATATURK",' +
        '"GMMN":"CASABLANCA","DTTA":"TUNIS","DAAG":"ALGER",' +
        '"CYUL":"MONTRÉAL","KJFK":"NEW YORK","OMDB":"DUBAI"' +
      '};' +
      // Fetch real flight data from OpenSky via GAS backend
      'google.script.run' +
        '.withSuccessHandler(function(result){' +
          'if(!result||result.error||!result.flights)return;' +
          'var now=new Date();' +
          'var h=now.getHours().toString().padStart(2,"0");' +
          'var m=now.getMinutes().toString().padStart(2,"0");' +
          'LIVE_SCHED=result.flights.slice(0,' + rows + ').map(function(f){' +
            'var ts=new Date(f.time*1000);' +
            'var th=ts.getHours().toString().padStart(2,"0");' +
            'var tm=ts.getMinutes().toString().padStart(2,"0");' +
            'var airportName=AIRPORT_NAMES[f.airport]||(f.airport||"---");' +
            'var liveStatus=ADSB_STATUS[f.callsign];' +
            'var defaultStatus=ARR_MODE?"ATTERRI":"À L\'HEURE";' +
            'return{call:f.callsign,dest:airportName,status:liveStatus||defaultStatus,gate:h+":"+m};' +
          '});' +
          'updateBoard();' +
          'var srcEl=document.getElementById("' + uid + 'src");' +
          'if(srcEl)srcEl.textContent="DONNÉES LIVE OPENSKY · " + result.flights.length + " VOLS";' +
        '})' +
        '.getFlightsLFBO("' + _esc(mode) + '","' + _esc(airport) + '");' +
      // ADS-B: overlay live status on board rows that match real callsigns
      (dataSource ?
        '(function(){' +
          'var LFBO_LAT=43.629,LFBO_LON=1.363;' +
          'function bearingTo(lat1,lon1,lat2,lon2){' +
            'var dL=(lon2-lon1)*Math.PI/180;' +
            'lat1=lat1*Math.PI/180;lat2=lat2*Math.PI/180;' +
            'var y=Math.sin(dL)*Math.cos(lat2);' +
            'var x=Math.cos(lat1)*Math.sin(lat2)-Math.sin(lat1)*Math.cos(lat2)*Math.cos(dL);' +
            'return(Math.atan2(y,x)*180/Math.PI+360)%360;' +
          '}' +
          'function onFeed(flights){' +
            'ADSB_STATUS={};' +
            'flights.forEach(function(f){' +
              'if(!f.callsign)return;' +
              'var hdgToLFBO=bearingTo(f.lat,f.lon,LFBO_LAT,LFBO_LON);' +
              'var diff=Math.abs(((f.hdg-hdgToLFBO+180)%360)-180);' +
              'var approaching=diff<70;' +
              'var st=f.alt_ft<1500?(approaching?"ATTERRI":"EN COURS"):' +
                     'f.alt_ft<8000?(approaching?"EN APPROCHE":"EN COURS"):"EN ROUTE";' +
              'ADSB_STATUS[f.callsign.trim()]=st;' +
            '});' +
            // Update status column on existing rows if callsign matches
            'if(LIVE_SCHED){' +
              'LIVE_SCHED.forEach(function(r){' +
                'if(ADSB_STATUS[r.call])r.status=ADSB_STATUS[r.call];' +
              '});' +
              'updateBoard();' +
            '}' +
          '}' +
          'var prev=window.A2UI_CALLBACKS["' + _esc(dataSource) + '"];' +
          'window.A2UI_CALLBACKS["' + _esc(dataSource) + '"]=function(d){onFeed(d);if(typeof prev==="function")prev(d);};' +
          'if(window.A2UI_DATA["' + _esc(dataSource) + '"])onFeed(window.A2UI_DATA["' + _esc(dataSource) + '"]);' +
        '})();' : '') +

    '})();<\/script>';
};
