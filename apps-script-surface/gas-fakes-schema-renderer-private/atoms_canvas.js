// atoms_canvas.gs — High-spec HTML5 canvas atoms
// Zero dependencies. Pure canvas + requestAnimationFrame. GAS CSP-safe.
// Surfaces: G M W

// ── canvas_plexus ─────────────────────────────────────────────────────────────
// Floating particle network: nodes drift independently, connect with
// proximity-weighted lines, repel from cursor with inverse-gravity physics.
// Fields:
//   count              — node count (default 80)
//   colour             — node + line colour hex (default #6366f1)
//   max_dist           — max distance for line draw px (default 110)
//   speed              — base particle speed (default 0.7)
//   dot_size           — node radius px (default 2.5)
//   repulsion_radius   — mouse repulsion field radius px (default 100)
//   repulsion_strength — force multiplier (default 5)
//   height             — canvas height px (default 280)
//   bg                 — background CSS colour (default #0a0f1d)
_RENDERERS['canvas_plexus'] = function(b) {
  var count  = b.count    || 80;
  var colour = b.colour   || '#6366f1';
  var maxD   = b.max_dist || 110;
  var speed  = b.speed    !== undefined ? b.speed : 0.7;
  var dotS   = b.dot_size || 2.5;
  var repR   = b.repulsion_radius   !== undefined ? b.repulsion_radius   : 100;
  var repS   = b.repulsion_strength !== undefined ? b.repulsion_strength : 5;
  var h      = b.height   || 280;
  var bg     = b.bg       || '#0a0f1d';
  var uid    = 'plx' + Math.random().toString(36).substr(2, 6);

  // Hex → r,g,b string for rgba() use in canvas
  var r16 = parseInt(colour.slice(1, 3), 16);
  var g16 = parseInt(colour.slice(3, 5), 16);
  var b16 = parseInt(colour.slice(5, 7), 16);
  var rgb = r16 + ',' + g16 + ',' + b16;

  return '<div style="border-radius:14px;overflow:hidden;">' +
    '<canvas id="' + uid + '" height="' + h + '" ' +
      'style="width:100%;display:block;background:' + _esc(bg) + ';cursor:crosshair;">' +
    '</canvas>' +
    '</div>' +
    '<script>(function(){' +
      'var c=document.getElementById("' + uid + '");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'c.width=c.offsetWidth||600;' +
      'var W=c.width,H=c.height;' +
      'var N=' + count + ',MD=' + maxD + ',SPD=' + speed + ',DS=' + dotS + ';' +
      'var RR=' + repR + ',RS=' + repS + ';' +
      'var RGB="' + rgb + '";' +
      'var nodes=[];' +
      'for(var i=0;i<N;i++){' +
        'nodes.push({' +
          'x:Math.random()*W,' +
          'y:Math.random()*H,' +
          'vx:(Math.random()-0.5)*SPD*2,' +
          'vy:(Math.random()-0.5)*SPD*2' +
        '});' +
      '}' +
      'var mx=null,my=null;' +
      'c.addEventListener("mousemove",function(e){' +
        'var r=c.getBoundingClientRect();' +
        'mx=(e.clientX-r.left)*(W/r.width);' +
        'my=(e.clientY-r.top)*(H/r.height);' +
      '});' +
      'c.addEventListener("mouseleave",function(){mx=null;my=null;});' +
      'window.addEventListener("resize",function(){' +
        'var nw=c.offsetWidth||600;' +
        'if(nw===W)return;' +
        'var sx=nw/W;W=nw;c.width=W;' +
        'nodes.forEach(function(n){n.x*=sx;});' +
      '});' +
      'function frame(){' +
        'ctx.clearRect(0,0,W,H);' +
        // Move + bounce + repel
        'for(var i=0;i<N;i++){' +
          'var n=nodes[i];' +
          'n.x+=n.vx;n.y+=n.vy;' +
          'if(n.x<0||n.x>W)n.vx*=-1;' +
          'if(n.y<0||n.y>H)n.vy*=-1;' +
          'if(mx!==null){' +
            'var dx=n.x-mx,dy=n.y-my,d=Math.sqrt(dx*dx+dy*dy);' +
            'if(d<RR&&d>1){var f=(RR-d)/RR;n.x+=dx/d*f*RS;n.y+=dy/d*f*RS;}' +
          '}' +
        '}' +
        // Proximity lines
        'for(var i=0;i<N-1;i++){' +
          'for(var j=i+1;j<N;j++){' +
            'var dx=nodes[i].x-nodes[j].x,dy=nodes[i].y-nodes[j].y;' +
            'var d=Math.sqrt(dx*dx+dy*dy);' +
            'if(d<MD){' +
              'ctx.beginPath();' +
              'ctx.strokeStyle="rgba("+RGB+","+(1-d/MD)*0.55+")";' +
              'ctx.lineWidth=0.7;' +
              'ctx.moveTo(nodes[i].x,nodes[i].y);' +
              'ctx.lineTo(nodes[j].x,nodes[j].y);' +
              'ctx.stroke();' +
            '}' +
          '}' +
        '}' +
        // Nodes
        'ctx.fillStyle="rgba("+RGB+",0.85)";' +
        'for(var i=0;i<N;i++){' +
          'ctx.beginPath();' +
          'ctx.arc(nodes[i].x,nodes[i].y,DS,0,Math.PI*2);' +
          'ctx.fill();' +
        '}' +
        'requestAnimationFrame(frame);' +
      '}' +
      'frame();' +
    '})();<\/script>';
};

// ── spring_nodes ──────────────────────────────────────────────────────────────
// Mass-spring graph layout: nodes repel each other (Coulomb), edges attract
// (Hooke). Starts jumbled at centre, settles naturally. Click-drag any node.
// Fields:
//   nodes    — array of {id, label} objects
//   edges    — array of {from, to, label?} using node ids
//   colour   — accent colour for nodes (default #6366f1)
//   height   — canvas height px (default 340)
//   bg       — background colour (default #0d1117)
//   spring   — spring constant (default 0.003)
//   repulsion— Coulomb constant (default 2400)
//   rest_len — spring rest length px (default 130)
_RENDERERS['spring_nodes'] = function(b) {
  var nodes    = b.nodes || [
    {id:'web',   label:'Web'},
    {id:'api',   label:'API'},
    {id:'db',    label:'Database'},
    {id:'auth',  label:'Auth'},
    {id:'cache', label:'Cache'}
  ];
  var edges    = b.edges || [
    {from:'web',  to:'api'},
    {from:'api',  to:'db'},
    {from:'api',  to:'auth'},
    {from:'api',  to:'cache'},
    {from:'web',  to:'auth'}
  ];
  var colour   = b.colour   || '#6366f1';
  var h        = b.height   || 340;
  var bg       = b.bg       || '#0d1117';
  var KS       = b.spring   !== undefined ? b.spring    : 0.003;
  var KR       = b.repulsion!== undefined ? b.repulsion : 2400;
  var RL       = b.rest_len !== undefined ? b.rest_len  : 130;
  var uid      = 'spn' + Math.random().toString(36).substr(2, 6);

  return '<canvas id="' + uid + '" height="' + h + '" ' +
    'style="width:100%;display:block;border-radius:14px;background:' + _esc(bg) + ';cursor:grab;">' +
    '</canvas>' +
    '<script>(function(){' +
      'var c=document.getElementById("' + uid + '");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'c.width=c.offsetWidth||600;' +
      'var W=c.width,H=c.height;' +
      'var COL="' + _esc(colour) + '";' +
      'var KS=' + KS + ',KR=' + KR + ',RL=' + RL + ',DMP=0.86;' +
      'var nodeDefs=' + JSON.stringify(nodes) + ';' +
      'var edgeDefs=' + JSON.stringify(edges) + ';' +
      // Init nodes bunched at centre with small jitter
      'var ns=nodeDefs.map(function(d){return{' +
        'id:d.id,label:d.label||d.id,' +
        'x:W/2+(Math.random()-0.5)*50,' +
        'y:H/2+(Math.random()-0.5)*50,' +
        'vx:(Math.random()-0.5)*4,' +
        'vy:(Math.random()-0.5)*4,' +
        'r:28,pinned:false' +
      '};});' +
      'var idx={};ns.forEach(function(n,i){idx[n.id]=i;});' +
      // Drag
      'var drag=-1;' +
      'function ptOnCanvas(e){var r=c.getBoundingClientRect();return{x:(e.clientX-r.left)*(W/r.width),y:(e.clientY-r.top)*(H/r.height)};}' +
      'function hitNode(x,y){for(var i=0;i<ns.length;i++){var n=ns[i],dx=x-n.x,dy=y-n.y;if(dx*dx+dy*dy<n.r*n.r)return i;}return -1;}' +
      'c.addEventListener("mousedown",function(e){var p=ptOnCanvas(e);drag=hitNode(p.x,p.y);if(drag>=0){ns[drag].pinned=true;c.style.cursor="grabbing";}});' +
      'window.addEventListener("mousemove",function(e){if(drag<0)return;var p=ptOnCanvas(e);ns[drag].x=p.x;ns[drag].y=p.y;ns[drag].vx=0;ns[drag].vy=0;});' +
      'window.addEventListener("mouseup",function(){if(drag>=0)ns[drag].pinned=false;drag=-1;c.style.cursor="grab";});' +
      // Physics
      'function step(){' +
        // Pairwise repulsion
        'for(var i=0;i<ns.length;i++){' +
          'for(var j=i+1;j<ns.length;j++){' +
            'var dx=ns[i].x-ns[j].x,dy=ns[i].y-ns[j].y;' +
            'var d2=Math.max(dx*dx+dy*dy,100);var d=Math.sqrt(d2);' +
            'var f=Math.min(KR/d2,8);' +
            'var fx=dx/d*f,fy=dy/d*f;' +
            'if(!ns[i].pinned){ns[i].vx+=fx;ns[i].vy+=fy;}' +
            'if(!ns[j].pinned){ns[j].vx-=fx;ns[j].vy-=fy;}' +
          '}' +
        '}' +
        // Spring attraction on edges
        'for(var e=0;e<edgeDefs.length;e++){' +
          'var ed=edgeDefs[e];' +
          'var na=ns[idx[ed.from]],nb=ns[idx[ed.to]];' +
          'if(!na||!nb)continue;' +
          'var dx=nb.x-na.x,dy=nb.y-na.y;' +
          'var d=Math.sqrt(dx*dx+dy*dy)||1;' +
          'var f=KS*(d-RL);' +
          'var fx=dx/d*f,fy=dy/d*f;' +
          'if(!na.pinned){na.vx+=fx;na.vy+=fy;}' +
          'if(!nb.pinned){nb.vx-=fx;nb.vy-=fy;}' +
        '}' +
        // Integrate + dampen + boundary
        'for(var i=0;i<ns.length;i++){' +
          'var n=ns[i];if(n.pinned)continue;' +
          'n.vx*=DMP;n.vy*=DMP;' +
          'n.x+=n.vx;n.y+=n.vy;' +
          'n.x=Math.max(n.r+4,Math.min(W-n.r-4,n.x));' +
          'n.y=Math.max(n.r+4,Math.min(H-n.r-4,n.y));' +
        '}' +
      '}' +
      // Draw
      'function draw(){' +
        'ctx.clearRect(0,0,W,H);' +
        // Edges
        'for(var e=0;e<edgeDefs.length;e++){' +
          'var ed=edgeDefs[e];' +
          'var na=ns[idx[ed.from]],nb=ns[idx[ed.to]];' +
          'if(!na||!nb)continue;' +
          'ctx.beginPath();' +
          'ctx.strokeStyle="rgba(255,255,255,0.1)";' +
          'ctx.lineWidth=1.5;' +
          'ctx.moveTo(na.x,na.y);ctx.lineTo(nb.x,nb.y);' +
          'ctx.stroke();' +
          'if(ed.label){' +
            'ctx.fillStyle="rgba(255,255,255,0.25)";ctx.font="9px system-ui";ctx.textAlign="center";' +
            'ctx.fillText(ed.label,(na.x+nb.x)/2,(na.y+nb.y)/2-5);' +
          '}' +
        '}' +
        // Nodes
        'for(var i=0;i<ns.length;i++){' +
          'var n=ns[i];' +
          // Glow
          'var grd=ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,n.r*2.2);' +
          'grd.addColorStop(0,COL+"44");grd.addColorStop(1,"rgba(0,0,0,0)");' +
          'ctx.fillStyle=grd;ctx.beginPath();ctx.arc(n.x,n.y,n.r*2.2,0,Math.PI*2);ctx.fill();' +
          // Circle fill
          'ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,Math.PI*2);' +
          'ctx.fillStyle=COL+"1a";ctx.fill();' +
          'ctx.strokeStyle=COL;ctx.lineWidth=n.pinned?2.5:1.5;ctx.stroke();' +
          // Label
          'ctx.fillStyle="rgba(255,255,255,0.9)";' +
          'ctx.font="bold 10px system-ui";ctx.textAlign="center";ctx.textBaseline="middle";' +
          'ctx.fillText(n.label,n.x,n.y);' +
        '}' +
      '}' +
      'function loop(){step();draw();requestAnimationFrame(loop);}' +
      'loop();' +
    '})();<\/script>';
};

// ── isometric_mesh ────────────────────────────────────────────────────────────
// 3D surface mesh from a 2D data matrix. Drag rotates on both axes.
// Inherits the globe_3d drag model. Auto-rotates until first drag.
// Fields:
//   matrix  — 2D array of numbers (generates a Gaussian hill if omitted)
//   colour  — base tint for the colour gradient (default #6366f1)
//   height  — canvas height px (default 320)
//   bg      — background colour (default #0d1117)
//   label   — optional title drawn top-left
//   auto_rotate — slow auto-spin before first drag (default true)
_RENDERERS['isometric_mesh'] = function(b) {
  var matrix     = b.matrix || null;
  var colour     = b.colour || '#6366f1';
  var h          = b.height || 320;
  var bg         = b.bg     || '#0d1117';
  var label      = b.label  || '';
  var autoRotate = b.auto_rotate !== false;
  var uid        = 'iso' + Math.random().toString(36).substr(2, 6);

  // Default: 16×16 Gaussian hill if no matrix provided
  var defaultMatrix = null;
  if (!matrix) {
    defaultMatrix = [];
    for (var ri = 0; ri < 16; ri++) {
      var row = [];
      for (var ci = 0; ci < 16; ci++) {
        var dx = ci - 7.5, dy = ri - 7.5;
        row.push(Math.round(Math.exp(-(dx * dx + dy * dy) / 18) * 1000) / 1000);
      }
      defaultMatrix.push(row);
    }
  }
  var matData = JSON.stringify(matrix || defaultMatrix);

  return '<canvas id="' + uid + '" height="' + h + '" ' +
    'style="width:100%;display:block;border-radius:14px;background:' + _esc(bg) + ';cursor:grab;">' +
    '</canvas>' +
    '<script>(function(){' +
      'var c=document.getElementById("' + uid + '");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'c.width=c.offsetWidth||600;' +
      'var W=c.width,H=c.height;' +
      'var MAT=' + matData + ';' +
      'var ROWS=MAT.length,COLS=MAT[0].length;' +
      'var LBL="' + _esc(label) + '";' +
      // Find data range
      'var vmin=Infinity,vmax=-Infinity;' +
      'for(var r=0;r<ROWS;r++)for(var ci=0;ci<COLS;ci++){var v=MAT[r][ci];if(v<vmin)vmin=v;if(v>vmax)vmax=v;}' +
      'var vrng=vmax-vmin||1;' +
      // View state
      'var theta=0.55,phi=0.38;' +
      'var dragging=false,lx=0,ly=0,everDragged=false;' +
      'var tileSize=Math.min(W*0.7,H*0.8)/Math.max(ROWS,COLS);' +
      'var hScale=tileSize*2.8;' +
      // Project grid point to screen
      'function proj(ci,ri,val){' +
        'var x3=( ci-COLS/2)*tileSize;' +
        'var y3=((val-vmin)/vrng)*hScale;' +
        'var z3=( ri-ROWS/2)*tileSize;' +
        // Y-axis rotation (horizontal drag)
        'var xr= x3*Math.cos(theta)+z3*Math.sin(theta);' +
        'var zr=-x3*Math.sin(theta)+z3*Math.cos(theta);' +
        // X-axis tilt (vertical drag)
        'var yr=y3*Math.cos(phi)-zr*Math.sin(phi);' +
        'return{sx:xr+W/2, sy:-yr+H*0.6};' +
      '}' +
      // Height → colour: low=#1e1b4b, high=accent colour
      'function hcol(val,alpha){' +
        'var t=(val-vmin)/vrng;' +
        'var r=Math.round(30+t*69),g=Math.round(27+t*75),b=Math.round(75+t*166);' +
        'return"rgba("+r+","+g+","+b+","+(alpha||0.7)+")";' +
      '}' +
      'function draw(){' +
        'ctx.clearRect(0,0,W,H);' +
        // Draw mesh — row lines
        'for(var ri=0;ri<ROWS;ri++){' +
          'ctx.beginPath();' +
          'var p0=proj(0,ri,MAT[ri][0]);' +
          'ctx.moveTo(p0.sx,p0.sy);' +
          'for(var ci=1;ci<COLS;ci++){' +
            'var p=proj(ci,ri,MAT[ri][ci]);ctx.lineTo(p.sx,p.sy);' +
          '}' +
          'ctx.strokeStyle=hcol(MAT[ri][Math.floor(COLS/2)],0.5);' +
          'ctx.lineWidth=0.7;ctx.stroke();' +
        '}' +
        // Col lines
        'for(var ci=0;ci<COLS;ci++){' +
          'ctx.beginPath();' +
          'var p0=proj(ci,0,MAT[0][ci]);' +
          'ctx.moveTo(p0.sx,p0.sy);' +
          'for(var ri=1;ri<ROWS;ri++){' +
            'var p=proj(ci,ri,MAT[ri][ci]);ctx.lineTo(p.sx,p.sy);' +
          '}' +
          'ctx.strokeStyle=hcol(MAT[Math.floor(ROWS/2)][ci],0.5);' +
          'ctx.lineWidth=0.7;ctx.stroke();' +
        '}' +
        // Peak dots — only points above 75th percentile
        'var thresh=vmin+vrng*0.75;' +
        'for(var ri=0;ri<ROWS;ri++){' +
          'for(var ci=0;ci<COLS;ci++){' +
            'if(MAT[ri][ci]>thresh){' +
              'var p=proj(ci,ri,MAT[ri][ci]);' +
              'ctx.beginPath();ctx.arc(p.sx,p.sy,2,0,Math.PI*2);' +
              'ctx.fillStyle=hcol(MAT[ri][ci],0.9);ctx.fill();' +
            '}' +
          '}' +
        '}' +
        // Label
        'if(LBL){' +
          'ctx.fillStyle="rgba(255,255,255,0.35)";' +
          'ctx.font="11px system-ui";ctx.textAlign="left";ctx.textBaseline="top";' +
          'ctx.fillText(LBL,12,10);' +
        '}' +
        // Drag hint
        'if(!everDragged){' +
          'ctx.fillStyle="rgba(255,255,255,0.15)";' +
          'ctx.font="10px system-ui";ctx.textAlign="right";ctx.textBaseline="bottom";' +
          'ctx.fillText("drag to rotate",W-10,H-8);' +
        '}' +
      '}' +
      // Drag interaction
      'c.addEventListener("mousedown",function(e){dragging=true;lx=e.clientX;ly=e.clientY;c.style.cursor="grabbing";});' +
      'window.addEventListener("mousemove",function(e){' +
        'if(!dragging)return;' +
        'everDragged=true;' +
        'theta+=(e.clientX-lx)*0.009;' +
        'phi=Math.max(-0.05,Math.min(1.3,phi-(e.clientY-ly)*0.006));' +
        'lx=e.clientX;ly=e.clientY;' +
        'draw();' +
      '});' +
      'window.addEventListener("mouseup",function(){dragging=false;c.style.cursor="grab";});' +
      // Auto-rotate
      'var AR=' + (autoRotate ? 'true' : 'false') + ';' +
      'c.addEventListener("mousedown",function(){AR=false;});' +
      '(function spin(){' +
        'if(AR){theta+=0.004;draw();}' +
        'requestAnimationFrame(spin);' +
      '})();' +
      'draw();' +
    '})();<\/script>';
};

// ── geo_mercator_radar ────────────────────────────────────────────────────────
// Draggable equirectangular map with location pins, link vectors, value labels.
// Inertia-drift physics on pan release. Zero external dependencies.
// Fields:
//   title   — header label
//   color   — accent hex (default #00f2ff)
//   nodes[] — { id, name, lat, lon, value? }
//   links[] — { from: id, to: id }
//   height  — canvas height px (default 450)
_RENDERERS['geo_mercator_radar'] = function(b) {
  var uid   = 'gmr' + Math.random().toString(36).substr(2, 6);
  var title = b.title  || 'GEOGRAPHIC MONITOR';
  var color = b.color  || '#00f2ff';
  var h     = (b.height || 450) + 'px';
  var nodes = JSON.stringify(b.nodes || []);
  var links = JSON.stringify(b.links || []);

  return '<div style="position:relative;width:100%;height:' + h + ';background:#070a13;' +
    'border:1px solid rgba(255,255,255,0.08);border-radius:12px;overflow:hidden;font-family:monospace;user-select:none;">' +
    '<canvas id="' + uid + '" style="position:absolute;inset:0;width:100%;height:100%;cursor:grab;"></canvas>' +
    '<div style="position:absolute;top:16px;left:16px;background:rgba(11,16,29,0.85);backdrop-filter:blur(8px);' +
      'padding:10px 16px;border-radius:6px;border:1px solid ' + color + '33;color:#fff;pointer-events:none;">' +
      '<div style="font-size:0.65rem;font-weight:bold;color:' + color + ';letter-spacing:0.1em;margin-bottom:2px;">A2UI · GEO PROJECTION</div>' +
      '<div style="font-size:0.95rem;font-weight:800;">' + _esc(title) + '</div>' +
    '</div>' +
    '<script>(function(){' +
      'var c=document.getElementById("' + uid + '");' +
      'var ctx=c.getContext("2d");' +
      'var NODES=' + nodes + ',LINKS=' + links + ';' +
      'var panX=0,panY=0,drag=false,lx=0,ly=0,vx=0,vy=0,zoom=1.0;' +
      'function resize(){' +
        'c.width=c.offsetWidth*2;c.height=c.offsetHeight*2;' +
        'ctx.scale(2,2);' +
        'if(panX===0){panX=c.offsetWidth/2;panY=c.offsetHeight/2;}' +
      '}' +
      'window.addEventListener("resize",resize);resize();' +
      'function toScreen(lat,lon){' +
        'return{x:lon*4.5*zoom+panX,y:-lat*6.5*zoom+panY};' +
      '}' +
      'function nodeById(id){for(var i=0;i<NODES.length;i++){if(NODES[i].id===id)return NODES[i];}return null;}' +
      'var t=0;' +
      'function draw(){' +
        'var W=c.width/2,H=c.height/2;' +
        'ctx.clearRect(0,0,W,H);' +
        'if(!drag){panX+=vx;panY+=vy;vx*=0.94;vy*=0.94;}' +
        't+=0.003;' +
        // Grid lines
        'ctx.strokeStyle="rgba(255,255,255,0.03)";ctx.lineWidth=1;' +
        'for(var i=0;i<W;i+=40){ctx.beginPath();ctx.moveTo(i,0);ctx.lineTo(i,H);ctx.stroke();}' +
        'for(var j=0;j<H;j+=40){ctx.beginPath();ctx.moveTo(0,j);ctx.lineTo(W,j);ctx.stroke();}' +
        // Link vectors
        'ctx.strokeStyle="' + color + '44";ctx.lineWidth=1.5;ctx.setLineDash([4,4]);' +
        'LINKS.forEach(function(l){' +
          'var n1=nodeById(l.from),n2=nodeById(l.to);' +
          'if(!n1||!n2)return;' +
          'var p1=toScreen(n1.lat,n1.lon),p2=toScreen(n2.lat,n2.lon);' +
          'ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.stroke();' +
        '});' +
        'ctx.setLineDash([]);' +
        // Nodes
        'NODES.forEach(function(n){' +
          'var p=toScreen(n.lat,n.lon);' +
          // Pulse ring
          'ctx.strokeStyle="' + color + '22";ctx.lineWidth=1;' +
          'ctx.beginPath();ctx.arc(p.x,p.y,10+Math.sin(t+n.lat)*2,0,Math.PI*2);ctx.stroke();' +
          // Pin dot
          'ctx.fillStyle="' + color + '";' +
          'ctx.beginPath();ctx.arc(p.x,p.y,4,0,Math.PI*2);ctx.fill();' +
          // Labels
          'ctx.fillStyle="#fff";ctx.font="bold 10px monospace";ctx.textAlign="left";' +
          'ctx.fillText(n.name,p.x+10,p.y-2);' +
          'if(n.value){ctx.fillStyle="rgba(255,255,255,0.45)";ctx.font="9px monospace";ctx.fillText(n.value,p.x+10,p.y+9);}' +
        '});' +
        'requestAnimationFrame(draw);' +
      '}' +
      'c.addEventListener("mousedown",function(e){drag=true;lx=e.clientX;ly=e.clientY;c.style.cursor="grabbing";});' +
      'document.addEventListener("mouseup",function(){drag=false;c.style.cursor="grab";});' +
      'document.addEventListener("mousemove",function(e){' +
        'if(!drag)return;' +
        'vx=e.clientX-lx;vy=e.clientY-ly;panX+=vx;panY+=vy;lx=e.clientX;ly=e.clientY;' +
      '});' +
      'draw();' +
    '})();<\/script></div>';
};

// ── geo_contour_waves ─────────────────────────────────────────────────────────
// Animated isobaric / atmospheric wave field. Fluid procedural contours
// driven by sin/cos scalar fields. Draggable with inertia.
// Fields:
//   title     — overlay label
//   color     — wave colour hex (default #a78bfa)
//   intensity — number of wave bands (default 4, max ~8)
//   height    — canvas height px (default 350)
_RENDERERS['geo_contour_waves'] = function(b) {
  var uid       = 'gcw' + Math.random().toString(36).substr(2, 6);
  var title     = b.title     || 'ATMOSPHERIC FRONT MATRIX';
  var color     = b.color     || '#a78bfa';
  var intensity = Math.min(b.intensity || 4, 8);
  var h         = (b.height || 350) + 'px';

  return '<div style="position:relative;width:100%;height:' + h + ';background:#070714;' +
    'border-radius:12px;overflow:hidden;font-family:monospace;user-select:none;">' +
    '<canvas id="' + uid + '" style="position:absolute;inset:0;width:100%;height:100%;cursor:grab;"></canvas>' +
    '<div style="position:absolute;top:14px;left:16px;color:' + color + ';font-size:0.65rem;' +
      'letter-spacing:0.1em;text-transform:uppercase;pointer-events:none;font-weight:bold;">' +
      _esc(title) +
    '</div>' +
    '<div style="position:absolute;bottom:14px;left:16px;color:' + color + ';font-size:0.65rem;' +
      'letter-spacing:0.05em;opacity:0.6;pointer-events:none;">' +
      '⚡ ISOBARIC WAVE SCALAR FIELD · ' + intensity + ' BANDS' +
    '</div>' +
    '<script>(function(){' +
      'var c=document.getElementById("' + uid + '");' +
      'var ctx=c.getContext("2d");' +
      'var offset=0,panX=0,panY=0,drag=false,lx=0,ly=0,vx=0,vy=0;' +
      'var BANDS=' + intensity + ';' +
      // Precomputed alpha hex values — avoids padStart/toString(16) in rAF
      'var ALPHAS=["ff","e8","cc","aa","88","66","44","22"];' +
      'function resize(){' +
        'c.width=c.offsetWidth*2;c.height=c.offsetHeight*2;ctx.scale(2,2);' +
      '}' +
      'window.addEventListener("resize",resize);resize();' +
      'function draw(){' +
        'var W=c.width/2,H=c.height/2;' +
        'ctx.clearRect(0,0,W,H);' +
        'if(!drag){panX+=vx;panY+=vy;vx*=0.95;vy*=0.95;}' +
        'offset+=0.01;' +
        'ctx.lineWidth=1.5;' +
        'for(var k=0;k<BANDS;k++){' +
          'var alpha=ALPHAS[k]||"22";' +
          'ctx.strokeStyle="' + color + '"+alpha;' +
          'ctx.beginPath();' +
          'var first=true;' +
          'for(var x=0;x<W;x+=8){' +
            'var y=(H/2)+Math.sin(x*0.008+offset+(k*0.4)+(panX*0.005))*35' +
                    '+Math.cos(x*0.015-offset+(panY*0.004))*15+panY*0.2;' +
            'if(first){ctx.moveTo(x,y);first=false;}else{ctx.lineTo(x,y);}' +
          '}' +
          'ctx.stroke();' +
        '}' +
        'requestAnimationFrame(draw);' +
      '}' +
      'c.addEventListener("mousedown",function(e){drag=true;lx=e.clientX;ly=e.clientY;c.style.cursor="grabbing";});' +
      'document.addEventListener("mouseup",function(){drag=false;c.style.cursor="grab";});' +
      'document.addEventListener("mousemove",function(e){' +
        'if(!drag)return;' +
        'vx=e.clientX-lx;vy=e.clientY-ly;panX+=vx;panY+=vy;lx=e.clientX;ly=e.clientY;' +
      '});' +
      'draw();' +
    '})();<\/script></div>';
};

// ── multi_surface ─────────────────────────────────────────────────────────────
// One atomic data pool → three surface rendering engines (fullscreen).
// Desktop: animated SVG spatial map. Mobile: phone-frame card list.
// Watch/IoT: circular focus face + secondary list. All fed from nodes[].
// Fields: title, nodes[{id,type,label,temp,value,intensity(0–100),coords:{x,y}}]
_RENDERERS['multi_surface'] = function(b) {
  var uid   = 'msx' + Math.random().toString(36).substr(2, 6);
  var title = b.title || 'MULTI-SURFACE ATOM ENGINE';
  var nodes = JSON.stringify(b.nodes || []);

  return '<style>' +
    'html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;}' +
    '#' + uid + '{' +
      'display:grid;grid-template-rows:52px 1fr 22px;grid-template-columns:1fr 270px 214px;' +
      'height:100vh;width:100vw;gap:1px;background:#0a1020;' +
      'font-family:"Courier New",monospace;color:#e2e8f0;' +
    '}' +
    '#' + uid + ' .msh{' +
      'grid-column:1/-1;display:flex;align-items:center;gap:14px;padding:0 18px;' +
      'background:#060c18;border-bottom:1px solid #0f1e35;' +
    '}' +
    '#' + uid + ' .msh-ttl{font-size:9px;letter-spacing:0.22em;color:#00f2ff;text-transform:uppercase;flex-shrink:0;}' +
    '#' + uid + ' .msh-pool{display:flex;gap:7px;overflow-x:auto;align-items:center;flex:1;scrollbar-width:none;}' +
    '#' + uid + ' .msp{flex-shrink:0;padding:2px 9px;border-radius:10px;font-size:8px;font-weight:700;letter-spacing:0.04em;border:1px solid;}' +
    '#' + uid + ' .msh-engs{display:flex;gap:14px;flex-shrink:0;}' +
    '#' + uid + ' .ms-eng{font-size:7px;color:#334155;display:flex;align-items:center;gap:4px;letter-spacing:0.1em;text-transform:uppercase;}' +
    '#' + uid + ' .ms-dot{width:6px;height:6px;border-radius:50%;}' +
    '@keyframes mspul{0%,100%{opacity:1;}50%{opacity:0.2;}}' +
    '#' + uid + ' .mspanel{background:#060c18;overflow:hidden;position:relative;}' +
    '#' + uid + ' .mspanel-lbl{' +
      'position:absolute;bottom:0;left:0;right:0;padding:5px 10px;' +
      'font-size:7px;letter-spacing:0.12em;color:#1e3a5f;text-transform:uppercase;' +
      'background:linear-gradient(transparent,#060c18 70%);pointer-events:none;z-index:10;' +
    '}' +
    '#' + uid + ' .msfoot{' +
      'grid-column:1/-1;display:flex;align-items:center;justify-content:center;gap:28px;' +
      'background:#060c18;border-top:1px solid #0a1628;' +
      'font-size:6px;letter-spacing:0.15em;color:#1e3a5f;text-transform:uppercase;' +
    '}' +
    // Mobile panel styles
    '#' + uid + 'mob{height:100%;display:flex;align-items:center;justify-content:center;padding:12px 8px;}' +
    '#' + uid + 'mob .ph{' +
      'width:100%;max-width:220px;background:#08111e;border-radius:28px;' +
      'border:2px solid #1e293b;overflow:hidden;display:flex;flex-direction:column;' +
      'max-height:calc(100% - 8px);box-shadow:0 0 30px rgba(59,130,246,0.12);' +
    '}' +
    '#' + uid + 'mob .phst{display:flex;justify-content:space-between;padding:10px 14px 5px;font-size:8px;color:#334155;}' +
    '#' + uid + 'mob .phhd{padding:6px 14px 10px;border-bottom:1px solid #0d1e33;display:flex;align-items:center;gap:8px;}' +
    '#' + uid + 'mob .phhd-t{font-size:13px;font-weight:600;color:#e2e8f0;font-family:system-ui,sans-serif;}' +
    '#' + uid + 'mob .phls{overflow-y:auto;flex:1;padding:6px 8px;scrollbar-width:none;}' +
    '#' + uid + 'mob .phc{display:flex;align-items:center;gap:9px;padding:8px 8px;border-radius:9px;margin-bottom:5px;background:#0d1a2e;}' +
    '#' + uid + 'mob .phc-ic{width:30px;height:30px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;}' +
    '#' + uid + 'mob .phc-bd{flex:1;min-width:0;}' +
    '#' + uid + 'mob .phc-ct{font-size:10px;font-weight:600;color:#e2e8f0;font-family:system-ui;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}' +
    '#' + uid + 'mob .phc-vl{font-size:8px;color:#475569;margin-top:1px;}' +
    '#' + uid + 'mob .phc-br{height:2px;border-radius:1px;margin-top:4px;background:#0f1e35;}' +
    '#' + uid + 'mob .phc-bf{height:100%;border-radius:1px;}' +
    '#' + uid + 'mob .phc-tp{font-size:16px;font-weight:300;color:#e2e8f0;font-family:system-ui;flex-shrink:0;}' +
    '#' + uid + 'mob .phtb{display:flex;justify-content:space-around;padding:7px 0;border-top:1px solid #0d1e33;}' +
    '#' + uid + 'mob .phtb-i{font-size:14px;opacity:0.25;}' +
    '#' + uid + 'mob .phtb-i.on{opacity:1;}' +
    // Watch panel styles
    '#' + uid + 'wtch{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:12px 8px;}' +
    '#' + uid + 'wtch .wl{width:100%;max-width:180px;}' +
    '#' + uid + 'wtch .wi{display:flex;justify-content:space-between;align-items:center;padding:3px 5px;border-radius:3px;font-size:7px;color:#334155;margin-bottom:2px;}' +
    '#' + uid + 'wtch .wb{font-size:7px;letter-spacing:0.12em;color:#1e3a5f;text-transform:uppercase;text-align:center;}' +
    '</style>' +

    '<div id="' + uid + '">' +
      '<div class="msh">' +
        '<div class="msh-ttl">' + _esc(title) + '</div>' +
        '<div class="msh-pool" id="' + uid + 'pool"></div>' +
        '<div class="msh-engs">' +
          '<div class="ms-eng"><div class="ms-dot" style="background:#00f2ff;animation:mspul 1.8s infinite;"></div>Desktop</div>' +
          '<div class="ms-eng"><div class="ms-dot" style="background:#3b82f6;animation:mspul 1.8s 0.6s infinite;"></div>Mobile</div>' +
          '<div class="ms-eng"><div class="ms-dot" style="background:#f59e0b;animation:mspul 1.8s 1.2s infinite;"></div>Watch</div>' +
        '</div>' +
      '</div>' +
      '<div class="mspanel"><svg id="' + uid + 'desk" width="100%" height="100%" style="display:block;"></svg><div class="mspanel-lbl">Engine · Desktop · SVG Spatial Renderer — all nodes, spatial layout, animated</div></div>' +
      '<div class="mspanel"><div id="' + uid + 'mob"></div><div class="mspanel-lbl">Engine · Mobile · Card Renderer — compact list, intensity bars, phone constraints</div></div>' +
      '<div class="mspanel"><div id="' + uid + 'wtch"></div><div class="mspanel-lbl">Engine · Watch/IoT · Focus Renderer — autonomous focal selection by intensity</div></div>' +
      '<div class="msfoot"><span>A2UI MULTI-SURFACE PARADIGM</span><span>ONE ATOMIC DATA POOL · THREE INDEPENDENT RENDERING ENGINES</span><span>SURFACE AUTONOMY — EACH ENGINE APPLIES ITS OWN CONSTRAINTS</span></div>' +
    '</div>' +

    '<script>(function(){' +
      'var UID="' + uid + '";' +
      'var NODES=' + nodes + ';' +
      'var COL={sunny:"#fbbf24",rain:"#38bdf8",cloudy:"#94a3b8",storm:"#f43f5e",snow:"#a5f3fc",fog:"#78716c"};' +
      'var ICO={sunny:"☀",rain:"🌧",cloudy:"☁",storm:"⛈",snow:"❄",fog:"🌫"};' +

      // Pool chips
      '(function(){' +
        'var pool=document.getElementById(UID+"pool");' +
        'NODES.forEach(function(n){' +
          'var c=COL[n.type]||"#475569";' +
          'var ch=document.createElement("div");' +
          'ch.className="msp";' +
          'ch.style.color=c;ch.style.borderColor=c+"55";ch.style.background=c+"15";' +
          'ch.textContent=n.label+" "+n.temp;' +
          'pool.appendChild(ch);' +
        '});' +
      '})();' +

      // ── Desktop SVG engine (createElementNS — no string-escaping issues)
      '(function(){' +
        'var svg=document.getElementById(UID+"desk");' +
        'var W=svg.clientWidth||700,H=svg.clientHeight||400;' +
        'svg.setAttribute("viewBox","0 0 "+W+" "+H);' +
        'var NS="http://www.w3.org/2000/svg";' +
        'function mk(tag,a,p){' +
          'var e=document.createElementNS(NS,tag);' +
          'if(a)Object.keys(a).forEach(function(k){e.setAttribute(k,a[k]);});' +
          'if(p)p.appendChild(e);return e;' +
        '}' +
        // Defs
        'var defs=mk("defs",{},svg);' +
        // Grid pattern
        'var pat=mk("pattern",{id:UID+"gp",width:"40",height:"40",patternUnits:"userSpaceOnUse"},defs);' +
        'mk("path",{d:"M 40 0 L 0 0 0 40",fill:"none",stroke:"#0d2040","stroke-width":"0.5"},pat);' +
        // Radial vignette gradient
        'var rg=mk("radialGradient",{id:UID+"rg",cx:"50%",cy:"50%",r:"65%"},defs);' +
        'mk("stop",{offset:"0%","stop-color":"#050810","stop-opacity":"0"},rg);' +
        'mk("stop",{offset:"100%","stop-color":"#050810","stop-opacity":"0.75"},rg);' +
        // Background layers
        'mk("rect",{width:W,height:H,fill:"url(#"+UID+"gp)"},svg);' +
        'mk("rect",{width:W,height:H,fill:"url(#"+UID+"rg)"},svg);' +
        // Scale: node coords use 0-800 x, 0-400 y space
        'var SX=W/800,SY=H/400;' +
        // Connection lines
        'for(var ci=0;ci<NODES.length-1;ci++){' +
          'var na=NODES[ci],nb=NODES[ci+1];' +
          'mk("line",{' +
            'x1:na.coords.x*SX,y1:na.coords.y*SY,' +
            'x2:nb.coords.x*SX,y2:nb.coords.y*SY,' +
            'stroke:"#1e3a5f","stroke-width":"1.5","stroke-dasharray":"5 5"' +
          '},svg);' +
        '}' +
        // Nodes
        'NODES.forEach(function(n){' +
          'var x=n.coords.x*SX,y=n.coords.y*SY;' +
          'var c=COL[n.type]||"#475569";' +
          'var g=mk("g",{transform:"translate("+x+","+y+")"},svg);' +
          // Three staggered pulse rings using SMIL animate
          'for(var ri=0;ri<3;ri++){' +
            '(function(i){' +
              'var ring=mk("circle",{cx:0,cy:0,r:14,fill:"none",stroke:c,"stroke-width":"1",opacity:0},g);' +
              'var aR=mk("animate",{attributeName:"r",values:"14;52",dur:"2.8s",begin:(i*0.93)+"s",repeatCount:"indefinite"},ring);' +
              'mk("animate",{attributeName:"opacity",values:"0.7;0",dur:"2.8s",begin:(i*0.93)+"s",repeatCount:"indefinite"},ring);' +
            '})(ri);' +
          '}' +
          // Core glow
          'mk("circle",{cx:0,cy:0,r:12,fill:c+"20",stroke:c,"stroke-width":"1.5"},g);' +
          'mk("circle",{cx:0,cy:0,r:5,fill:c},g);' +
          // Intensity arc around node
          'var pct=Math.min(1,parseFloat(n.intensity||0)/100);' +
          'if(pct>0.01){' +
            'var ar=18,aang=pct*2*Math.PI-Math.PI/2;' +
            'var ax=ar*Math.cos(aang),ay=ar*Math.sin(aang);' +
            'var lgf=pct>0.5?"1":"0";' +
            'mk("path",{' +
              'd:"M 0 -"+ar+" A "+ar+" "+ar+" 0 "+lgf+" 1 "+ax.toFixed(2)+" "+ay.toFixed(2),' +
              'fill:"none",stroke:c,"stroke-width":"2.5","stroke-linecap":"round"' +
            '},g);' +
          '}' +
          // Label card
          'mk("rect",{x:-48,y:18,width:96,height:38,rx:4,fill:"#08111e",stroke:c+"40","stroke-width":"1"},g);' +
          // City name
          'var lt=mk("text",{' +
            'x:0,y:31,"text-anchor":"middle",' +
            'fill:c,"font-size":"9","font-family":"Courier New","font-weight":"700","letter-spacing":"0.06em"' +
          '},g);lt.textContent=n.label;' +
          // Temp + value
          'var tt=mk("text",{x:-36,y:48,"text-anchor":"start",fill:"#e2e8f0","font-size":"13","font-family":"system-ui","font-weight":"300"},g);' +
          'tt.textContent=n.temp;' +
          'var vt=mk("text",{x:8,y:48,"text-anchor":"start",fill:"#334155","font-size":"8","font-family":"Courier New"},g);' +
          'vt.textContent=n.value;' +
        '});' +
      '})();' +

      // ── Mobile card engine (phone-frame UI)
      '(function(){' +
        'var mob=document.getElementById(UID+"mob");' +
        'var cards="";' +
        'NODES.forEach(function(n){' +
          'var c=COL[n.type]||"#475569";' +
          'var pct=Math.min(100,parseFloat(n.intensity||0));' +
          'cards+=`<div class="phc">' +
            '<div class="phc-ic" style="background:${c}22">${ICO[n.type]||"?"}</div>' +
            '<div class="phc-bd">' +
              '<div class="phc-ct">${n.label}</div>' +
              '<div class="phc-vl">${n.value}</div>' +
              '<div class="phc-br"><div class="phc-bf" style="width:${pct}%;background:${c}"></div></div>' +
            '</div>' +
            '<div class="phc-tp">${n.temp}</div>' +
          '</div>`;' +
        '});' +
        'mob.innerHTML=`<div class="ph">' +
          '<div class="phst"><span>9:41</span><span>●●●●○ ☀ ██▉</span></div>' +
          '<div class="phhd"><span style="font-size:16px;color:#3b82f6;">◀</span><span class="phhd-t">Weather</span></div>' +
          '<div class="phls">${cards}</div>' +
          '<div class="phtb">' +
            '<div class="phtb-i on">🏠</div>' +
            '<div class="phtb-i">🗺</div>' +
            '<div class="phtb-i">⚙️</div>' +
          '</div>' +
        '</div>`;' +
      '})();' +

      // ── Watch/IoT engine (autonomous focal selection + circular SVG face)
      '(function(){' +
        'var focal=NODES[0];' +
        'NODES.forEach(function(n){if(parseFloat(n.intensity||0)>parseFloat(focal.intensity||0))focal=n;});' +
        'var others=NODES.filter(function(n){return n.id!==focal.id;});' +
        'var fc=COL[focal.type]||"#f59e0b";' +
        'var NS="http://www.w3.org/2000/svg";' +
        'var wtch=document.getElementById(UID+"wtch");' +
        // Build watch SVG
        'var W=178,H=178,cx=89,cy=89,OR=84,IR=66;' +
        'var svgEl=document.createElementNS(NS,"svg");' +
        'svgEl.setAttribute("width",W);svgEl.setAttribute("height",H);' +
        'svgEl.setAttribute("viewBox","0 0 "+W+" "+H);' +
        'function mk(tag,a,p){' +
          'var e=document.createElementNS(NS,tag);' +
          'if(a)Object.keys(a).forEach(function(k){e.setAttribute(k,a[k]);});' +
          'if(p)p.appendChild(e);return e;' +
        '}' +
        // Outer bezel
        'mk("circle",{cx:cx,cy:cy,r:OR+3,fill:"none",stroke:"#1e293b","stroke-width":"4"},svgEl);' +
        // Face fill
        'mk("circle",{cx:cx,cy:cy,r:OR,fill:"#050810"},svgEl);' +
        // Hour ticks
        'for(var ti=0;ti<12;ti++){' +
          'var ta=ti*Math.PI/6;' +
          'var major=ti%3===0;' +
          'var tr1=OR-1,tr2=OR-(major?10:6);' +
          'mk("line",{' +
            'x1:(cx+tr1*Math.sin(ta)).toFixed(2),y1:(cy-tr1*Math.cos(ta)).toFixed(2),' +
            'x2:(cx+tr2*Math.sin(ta)).toFixed(2),y2:(cy-tr2*Math.cos(ta)).toFixed(2),' +
            'stroke:major?"#334155":"#1e293b","stroke-width":major?"2":"1","stroke-linecap":"round"' +
          '},svgEl);' +
        '}' +
        // Intensity arc (clockwise from 12)
        'var pct=Math.min(1,parseFloat(focal.intensity||0)/100);' +
        'if(pct>0.01){' +
          'var ar=OR-6;' +
          'var aang=pct*2*Math.PI;' +
          'var eax=(cx+ar*Math.sin(aang)).toFixed(2),eay=(cy-ar*Math.cos(aang)).toFixed(2);' +
          'mk("path",{' +
            'd:"M "+cx+" "+(cy-ar)+" A "+ar+" "+ar+" 0 "+(pct>0.5?"1":"0")+" 1 "+eax+" "+eay,' +
            'fill:"none",stroke:fc,"stroke-width":"5","stroke-linecap":"round"' +
          '},svgEl);' +
        '}' +
        // Inner face ring
        'mk("circle",{cx:cx,cy:cy,r:IR,fill:"#07101e"},svgEl);' +
        // City name (top of face)
        'var ct=mk("text",{x:cx,y:cy-30,"text-anchor":"middle",fill:"#334155","font-size":"8","font-family":"Courier New","font-weight":"700","letter-spacing":"0.12em"},svgEl);' +
        'ct.textContent=focal.label.toUpperCase();' +
        // Temperature (center)
        'var tt=mk("text",{x:cx,y:cy+10,"text-anchor":"middle",fill:"#e2e8f0","font-size":"30","font-family":"system-ui","font-weight":"200"},svgEl);' +
        'tt.textContent=focal.temp;' +
        // Condition (below temp)
        'var vt=mk("text",{x:cx,y:cy+24,"text-anchor":"middle",fill:fc,"font-size":"8","font-family":"Courier New"},svgEl);' +
        'vt.textContent=focal.value;' +
        // Second hand from current time
        'var now=new Date();' +
        'var sa=(now.getSeconds()+now.getMilliseconds()/1000)*Math.PI/30;' +
        'mk("line",{' +
          'x1:cx,y1:cy,' +
          'x2:(cx+(IR-6)*Math.sin(sa)).toFixed(2),y2:(cy-(IR-6)*Math.cos(sa)).toFixed(2),' +
          'stroke:"#f43f5e","stroke-width":"1.5","stroke-linecap":"round"' +
        '},svgEl);' +
        'mk("circle",{cx:cx,cy:cy,r:3,fill:"#f43f5e"},svgEl);' +
        'wtch.appendChild(svgEl);' +
        // Secondary list — other nodes
        'if(others.length){' +
          'var wlEl=document.createElement("div");' +
          'wlEl.className="wl";' +
          'others.forEach(function(n){' +
            'var nc=COL[n.type]||"#475569";' +
            'var row=document.createElement("div");' +
            'row.className="wi";' +
            'row.innerHTML=`<span style="color:${nc}">${n.label}</span><span>${n.temp}</span><span style="color:#1e3a5f">${n.value}</span>`;' +
            'wlEl.appendChild(row);' +
          '});' +
          'wtch.appendChild(wlEl);' +
        '}' +
        // Autonomy label
        'var badge=document.createElement("div");' +
        'badge.className="wb";' +
        'badge.textContent="FOCAL: "+focal.label.toUpperCase()+" ("+Math.round(parseFloat(focal.intensity||0))+"% INTENSITY)";' +
        'wtch.appendChild(badge);' +
      '})();' +

    '})();<\/script>';
};



// ── geo_europe_airspace ──────────────────────────────────────────────────────
// Europe-wide aviation canvas — Mercator projection, fullscreen, draggable.
// Click any airport to open its TMA playbook. LFBO launches the full Toulouse deck.
// DATA ATOMS (reusable schema — same feeds plug into any country):
//   adsb_feed  — live ADS-B (server-side, shared_blocks)
//   metar_feed — airport METAR weather
//   sim_flights — [{hex,flight,lat,lon,alt_baro,gs,track}] for demo mode
// Fields: title, focus (ISO country), sim_flights[], airports (bool)
_RENDERERS['geo_europe_airspace'] = function(b) {
  var uid    = 'eur' + Math.random().toString(36).substr(2, 6);
  var title  = b.title || 'EUROPEAN AIRSPACE';
  var focus  = b.focus || b.country || '';
  var simFlt = JSON.stringify(b.sim_flights || []);
  var showAP = b.airports !== false;

  return '<style>' +
    '#' + uid + 'wrap{position:relative;background:#050810;width:100%;height:100%;overflow:hidden;font-family:"Courier New",monospace;}' +
    '#' + uid + 'hdr{position:absolute;top:0;left:0;right:0;height:34px;z-index:5;display:flex;align-items:center;gap:10px;padding:0 14px;background:linear-gradient(#060d1aee,transparent);}' +
    '#' + uid + 'tip{position:absolute;pointer-events:none;z-index:20;display:none;background:rgba(2,8,20,0.92);border:1px solid rgba(0,242,255,0.3);border-radius:6px;padding:6px 10px;font-size:9px;color:#e2e8f0;white-space:nowrap;}' +
    '#' + uid + 'tip b{color:#00f2ff;display:block;margin-bottom:2px;}' +
    '#' + uid + 'tip small{color:#334155;}' +
    '#' + uid + 'nav{display:none;position:absolute;bottom:16px;left:50%;transform:translateX(-50%);z-index:50;' +
      'background:linear-gradient(135deg,#001a2e,#002a40);border:1px solid #00f2ff;border-radius:8px;' +
      'padding:10px 22px;font-family:"Courier New",monospace;text-align:center;box-shadow:0 0 24px rgba(0,242,255,0.3);}' +
    '#' + uid + 'nav span{display:block;font-size:8px;color:#334155;letter-spacing:0.15em;margin-bottom:6px;}' +
    '#' + uid + 'nava{display:block;font-size:12px;font-weight:bold;color:#00f2ff;text-decoration:none;letter-spacing:0.1em;}' +
    '#' + uid + 'nava:hover{color:#fff;}' +
    '</style>' +
    '<div id="' + uid + 'wrap">' +
      '<div id="' + uid + 'hdr">' +
        '<span style="font-size:9px;letter-spacing:0.2em;color:#00f2ff;text-transform:uppercase;">' + _esc(title) + '</span>' +
        '<span id="' + uid + 'fltlbl" style="font-size:8px;color:#334155;margin-left:4px;"></span>' +
        '<span style="margin-left:auto;font-size:7px;color:#1e3a5f;letter-spacing:0.1em;">DRAG · SCROLL ZOOM · CLICK AIRPORT TO OPEN TMA PLAYBOOK</span>' +
      '</div>' +
      '<canvas id="' + uid + '" style="width:100%;height:100%;display:block;cursor:grab;"></canvas>' +
      '<div id="' + uid + 'tip"><b id="' + uid + 'tipicao"></b><span id="' + uid + 'tipname"></span><br><small>Click to open TMA playbook</small></div>' +
      '<div id="' + uid + 'nav"><span>TMA PLAYBOOK</span><a id="' + uid + 'nava" target="_top">▶ OPEN PLAYBOOK</a></div>' +
    '</div>' +

    '<script>(function(){' +
      'var c=document.getElementById("' + uid + '");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'c.width=c.offsetWidth||window.innerWidth||1100;c.height=c.offsetHeight||window.innerHeight||640;' +
      'var W=c.width,H=c.height;' +
      'var FOCUS="' + focus.toUpperCase() + '";' +
      'var SIM_FLIGHTS=' + simFlt + ';' +
      'var SHOW_AP=' + (showAP?'true':'false') + ';' +

      // ── Country boundary polygons ─────────────────────────────────────────
      'var COUNTRIES=[' +
        '{c:"FR",n:"FRANCE",     fill:"#0a1e3a",line:"#1a5fb4",' +
          'pts:[[51.1,2.5],[50.5,3.4],[49.5,6.4],[48.97,7.83],[47.6,7.6],[46.4,6.4],[45.9,7.0],[44.1,7.0],[43.8,7.4],[43.3,5.1],[42.3,3.2],[42.4,2.1],[43.4,-1.8],[43.5,-1.5],[47.3,-2.2],[48.3,-4.6],[48.7,-2.0],[49.6,-1.6],[50.1,-1.8],[51.1,2.5]]},' +
        '{c:"ES",n:"SPAIN",      fill:"#1a0a0a",line:"#8b3a3a",' +
          'pts:[[43.4,-1.8],[43.6,-1.5],[43.8,-8.1],[42.6,-8.9],[41.0,-9.0],[39.5,-7.0],[37.2,-7.4],[36.0,-5.4],[36.6,-4.4],[37.4,-1.8],[38.7,-0.2],[40.5,0.8],[42.3,3.2],[42.4,2.1],[43.4,-1.8]]},' +
        '{c:"PT",n:"PORTUGAL",   fill:"#0f1a0a",line:"#3a8b3a",' +
          'pts:[[42.1,-8.2],[41.9,-8.7],[40.0,-7.0],[37.2,-7.4],[37.0,-7.5],[37.0,-9.0],[38.7,-9.5],[39.7,-9.1],[40.2,-8.9],[42.1,-8.2]]},' +
        '{c:"GB",n:"UK",         fill:"#0a1a1a",line:"#3a8b8b",' +
          'pts:[[50.6,-0.9],[51.2,1.4],[52.9,1.8],[54.0,-0.2],[55.0,-1.4],[55.8,-2.0],[57.7,-1.8],[58.6,-3.6],[57.8,-5.9],[56.5,-5.6],[55.5,-5.7],[54.6,-5.9],[53.3,-4.6],[51.4,-5.1],[50.6,-0.9]]},' +
        '{c:"IE",n:"IRELAND",    fill:"#0a1a0a",line:"#3a7a3a",' +
          'pts:[[55.4,-7.9],[54.2,-5.9],[53.3,-6.0],[51.9,-8.5],[51.4,-9.8],[53.3,-10.0],[54.7,-8.2],[55.4,-7.9]]},' +
        '{c:"BE",n:"BELGIUM",    fill:"#1a1a0a",line:"#8b8b3a",' +
          'pts:[[51.5,2.5],[51.1,4.0],[51.3,4.8],[50.8,5.7],[50.5,5.8],[49.5,6.4],[50.1,5.6],[50.9,4.8],[50.7,3.4],[51.5,2.5]]},' +
        '{c:"NL",n:"NETHERLANDS",fill:"#0a0a1a",line:"#3a3a8b",' +
          'pts:[[53.5,6.8],[53.0,7.2],[52.4,7.1],[51.9,6.5],[51.5,4.2],[51.3,4.8],[51.9,4.3],[52.7,4.9],[53.5,6.8]]},' +
        '{c:"DE",n:"GERMANY",    fill:"#0a0a1a",line:"#4a4a9a",' +
          'pts:[[54.9,8.4],[54.5,11.2],[54.0,13.2],[53.9,14.4],[52.9,14.1],[51.1,15.0],[50.4,12.3],[50.0,12.5],[48.7,13.5],[47.6,12.9],[47.6,9.6],[47.7,7.6],[49.4,6.4],[49.9,6.1],[50.9,6.2],[52.2,7.0],[53.0,7.2],[54.9,8.4]]},' +
        '{c:"CH",n:"SWITZERLAND",fill:"#1a0a1a",line:"#8b3a8b",' +
          'pts:[[47.7,7.6],[47.6,8.6],[47.6,9.6],[47.0,9.5],[46.3,10.1],[45.9,7.0],[46.4,6.4],[47.7,7.6]]},' +
        '{c:"AT",n:"AUSTRIA",    fill:"#1a0a0a",line:"#9a3a3a",' +
          'pts:[[48.6,13.8],[47.6,12.9],[47.6,9.6],[47.0,9.5],[46.3,10.1],[46.7,10.5],[47.1,10.1],[46.8,13.5],[47.1,15.0],[48.6,13.8]]},' +
        '{c:"IT",n:"ITALY",      fill:"#1a1a0a",line:"#7a7a2a",' +
          'pts:[[47.1,10.1],[46.5,13.7],[46.1,13.7],[45.8,13.7],[44.4,12.2],[44.1,12.4],[42.7,10.3],[41.7,9.0],[38.4,15.7],[37.6,15.1],[39.9,18.5],[41.8,15.7],[44.2,13.8],[47.1,10.1]]},' +
        '{c:"DK",n:"DENMARK",    fill:"#0a1a1a",line:"#2a6a6a",' +
          'pts:[[55.0,8.4],[54.9,12.0],[55.7,12.6],[56.1,10.6],[57.7,10.6],[57.5,9.7],[57.1,8.6],[55.5,8.0],[55.0,8.4]]},' +
        '{c:"NO",n:"NORWAY",     fill:"#0a0f1a",line:"#2a4a7a",' +
          'pts:[[57.9,7.0],[58.1,8.0],[59.1,5.4],[61.1,5.0],[63.0,8.0],[65.8,14.3],[68.0,15.8],[70.5,22.0],[71.0,25.7],[67.0,15.0],[62.8,7.7],[59.1,5.4],[57.9,7.0]]},' +
        '{c:"SE",n:"SWEDEN",     fill:"#0a0f1a",line:"#2a3a6a",' +
          'pts:[[55.4,12.9],[55.7,12.6],[57.7,10.6],[59.3,10.6],[60.6,5.1],[63.5,8.6],[65.7,14.2],[68.0,15.8],[67.9,17.7],[65.0,14.6],[62.0,17.5],[59.0,18.5],[55.4,12.9]]}' +
      '];' +

      // ── Airport registry — pluggable into any geo_airspace_radar ─────────
      'var AIRPORTS=[' +
        '{i:"LFPG",n:"Paris CDG",      lat:49.009,lon:2.548,  ctry:"FR"},' +
        '{i:"LFBO",n:"Toulouse TLS",   lat:43.629,lon:1.363,  ctry:"FR"},' +
        '{i:"LFML",n:"Marseille MRS",  lat:43.439,lon:5.221,  ctry:"FR"},' +
        '{i:"LFMN",n:"Nice NCE",       lat:43.665,lon:7.215,  ctry:"FR"},' +
        '{i:"EGLL",n:"London LHR",     lat:51.477,lon:-0.461, ctry:"GB"},' +
        '{i:"EGPH",n:"Edinburgh EDI",  lat:55.950,lon:-3.372, ctry:"GB"},' +
        '{i:"EHAM",n:"Amsterdam AMS",  lat:52.309,lon:4.763,  ctry:"NL"},' +
        '{i:"EDDF",n:"Frankfurt FRA",  lat:50.033,lon:8.571,  ctry:"DE"},' +
        '{i:"LEMD",n:"Madrid MAD",     lat:40.472,lon:-3.561, ctry:"ES"},' +
        '{i:"LEBL",n:"Barcelona BCN",  lat:41.297,lon:2.078,  ctry:"ES"},' +
        '{i:"LIRF",n:"Rome FCO",       lat:41.800,lon:12.239, ctry:"IT"},' +
        '{i:"LSZH",n:"Zurich ZRH",     lat:47.458,lon:8.548,  ctry:"CH"},' +
        '{i:"EBBR",n:"Brussels BRU",   lat:50.902,lon:4.484,  ctry:"BE"},' +
        '{i:"LPPT",n:"Lisbon LIS",     lat:38.774,lon:-9.134, ctry:"PT"},' +
        '{i:"EIDW",n:"Dublin DUB",     lat:53.421,lon:-6.270, ctry:"IE"},' +
        '{i:"LOWW",n:"Vienna VIE",     lat:48.110,lon:16.569, ctry:"AT"},' +
        '{i:"EKCH",n:"Copenhagen CPH", lat:55.618,lon:12.656, ctry:"DK"},' +
        '{i:"ENGM",n:"Oslo OSL",       lat:60.197,lon:11.100, ctry:"NO"},' +
        '{i:"ESSA",n:"Stockholm ARN",  lat:59.652,lon:17.919, ctry:"SE"}' +
      '];' +

      // ── FIR label positions ───────────────────────────────────────────────
      'var FIRS=[' +
        '{n:"BREST",lat:47.5,lon:-4.0},{n:"PARIS",lat:48.8,lon:2.8},' +
        '{n:"BORDEAUX",lat:44.8,lon:0.5},{n:"MARSEILLE",lat:43.5,lon:5.5},' +
        '{n:"LONDON",lat:52.5,lon:-1.5},{n:"SCOTTISH",lat:57.0,lon:-3.5},' +
        '{n:"RHEIN",lat:50.5,lon:8.5},{n:"MÜNCHEN",lat:48.5,lon:11.5},' +
        '{n:"MADRID",lat:40.5,lon:-3.5},{n:"BARCELONA",lat:41.5,lon:2.0},' +
        '{n:"LISBOA",lat:39.5,lon:-8.0},{n:"AMSTERDAM",lat:52.5,lon:5.5},' +
        '{n:"ROMA",lat:42.0,lon:12.5},{n:"SHANNON",lat:53.0,lon:-8.0}' +
      '];' +

      // ── Playbook factory — builds payloads for airport click navigation ───
      // LFBO gets the full Toulouse TMA multi-slide deck; others get a radar view
      'function makePlaybook(ap){' +
        'if(ap.i==="LFBO"){' +
          'return [{type:"playbook",' +
            'title:"LFBO TMA • Toulouse Blagnac Approach Control",' +
            'shared_blocks:[' +
              '{id:"wx",  type:"metar_feed",icao:"LFBO"},' +
              '{id:"live",type:"adsb_feed", lat:43.629,lon:1.363,dist:40}' +
            '],' +
            'slides:[' +
              '{id:"approach",label:"🎯 Approach Control",blocks:[{' +
                'type:"airspace_command_deck",center_lat:43.629,center_lon:1.363,' +
                'center_icao:"LFBO",country:"FR",zoom:35,height:"fullscreen",' +
                'adsb_feed:"live",metar_feed:"wx",' +
                'panel_type:"supervisor",panel_title:"📡 Supervisor Live Console",' +
                'chyron_title:"LFBO TMA APPROACH CONTROL",' +
                'chyron_subtitle:"Toulouse Blagnac • Runway 32L/R Active • TMA Class D/E",' +
                'ticker_text:"📍 LFBO Terminal Information • RUNWAY 32L/R ACTIVE • WIND: {{weather.wind}} • TEMP: {{weather.temp}} • QNH: {{weather.pressure}} • {{weather.raw}} •",' +
                'ticker_speed:50' +
              '}]},' +
              '{id:"enroute",label:"🗺️ En-Route 80nm",blocks:[{' +
                'type:"airspace_command_deck",center_lat:43.629,center_lon:1.363,' +
                'center_icao:"LFBO",country:"FR",zoom:80,height:"fullscreen",' +
                'adsb_feed:"live",metar_feed:"wx",' +
                'panel_type:"supervisor",panel_title:"📡 Sector Radar",' +
                'chyron_title:"TOULOUSE FIR • SECTOR VIEW",' +
                'chyron_subtitle:"Upper + Lower Airspace • SW France FIR",' +
                'ticker_text:"📍 TOULOUSE FIR • SW FRANCE • WIND: {{weather.wind}} • {{weather.raw}} •",' +
                'ticker_speed:40' +
              '}]},' +
              '{id:"country",label:"🇫🇷 France Overview",blocks:[{' +
                'type:"geo_europe_airspace",focus:"FR",airports:true' +
              '}]}' +
            ']' +
          '}];' +
        '}' +
        // Generic TMA radar for any other airport
        'return [{' +
          'type:"airspace_command_deck",' +
          'center_lat:ap.lat,center_lon:ap.lon,center_icao:ap.i,country:ap.ctry,' +
          'zoom:40,height:"fullscreen",' +
          'panel_type:"supervisor",panel_title:ap.i+" TMA",' +
          'chyron_title:ap.i+" TMA • "+ap.n,' +
          'chyron_subtitle:"Approach Control • Live ADS-B Feed",' +
          'adsb_feed_lat:ap.lat,adsb_feed_lon:ap.lon' +
        '}];' +
      '}' +

      // ── URL builder (client-side base64url encode → GAS ?p= param) ────────
      'function makeUrl(payload){' +
        'var json=JSON.stringify(payload);' +
        'var b64=btoa(unescape(encodeURIComponent(json)));' +
        'var safe=b64.replace(/\\+/g,"-").replace(/\\//g,"_").replace(/=/g,"");' +
        'return window.top.location.href.split("?")[0]+"?p="+safe;' +
      '}' +

      // ── Mercator projection with pan + zoom ───────────────────────────────
      'var panX=0,panY=0,scale=1;' +
      'var LAT_MIN=33,LAT_MAX=72,LON_MIN=-22,LON_MAX=45;' +
      'function mercY(lat){' +
        'var r=lat*Math.PI/180;' +
        'var mn=Math.log(Math.tan(Math.PI/4+LAT_MIN*Math.PI/360));' +
        'var mx=Math.log(Math.tan(Math.PI/4+LAT_MAX*Math.PI/360));' +
        'return H-(Math.log(Math.tan(Math.PI/4+r/2))-mn)/(mx-mn)*H;' +
      '}' +
      'function llX(lon){return (lon-LON_MIN)/(LON_MAX-LON_MIN)*W;}' +
      'function toC(lat,lon){return{x:llX(lon)*scale+panX,y:mercY(lat)*scale+panY};}' +
      // Inverse projection (canvas → lat/lon) for hit testing
      'function fromC(cx,cy){' +
        'var nx=(cx-panX)/(scale*W),ny=1-(cy-panY)/(scale*H);' +
        'var lon=nx*(LON_MAX-LON_MIN)+LON_MIN;' +
        'var mn=Math.log(Math.tan(Math.PI/4+LAT_MIN*Math.PI/360));' +
        'var mx=Math.log(Math.tan(Math.PI/4+LAT_MAX*Math.PI/360));' +
        'var m=ny*(mx-mn)+mn;' +
        'var lat=(2*Math.atan(Math.exp(m))-Math.PI/2)*180/Math.PI;' +
        'return{lat:lat,lon:lon};' +
      '}' +

      // ── Nearest airport finder for click/hover ────────────────────────────
      'function nearestAirport(cx,cy,thresh){' +
        'var best=null,bestD=Infinity;' +
        'AIRPORTS.forEach(function(a){' +
          'var ap=toC(a.lat,a.lon);' +
          'var d=Math.sqrt((ap.x-cx)*(ap.x-cx)+(ap.y-cy)*(ap.y-cy));' +
          'if(d<thresh&&d<bestD){bestD=d;best=a;}' +
        '});' +
        'return best;' +
      '}' +

      // ── Draw ──────────────────────────────────────────────────────────────
      'function draw(){' +
        'ctx.clearRect(0,0,W,H);' +
        'ctx.fillStyle="#050810";ctx.fillRect(0,0,W,H);' +
        // Graticule
        'ctx.strokeStyle="rgba(0,40,80,0.45)";ctx.lineWidth=0.4;ctx.setLineDash([]);' +
        'for(var glon=-20;glon<=44;glon+=10){' +
          'var gp0=toC(33,glon),gp1=toC(72,glon);' +
          'ctx.beginPath();ctx.moveTo(gp0.x,gp0.y);ctx.lineTo(gp1.x,gp1.y);ctx.stroke();' +
          'ctx.fillStyle="rgba(0,80,120,0.35)";ctx.font="7px \'Courier New\'";ctx.textAlign="center";' +
          'ctx.fillText(glon+(glon>=0?"°E":"°"),gp0.x,H-5);' +
        '}' +
        'for(var glat=35;glat<=70;glat+=10){' +
          'var gq0=toC(glat,-22),gq1=toC(glat,45);' +
          'ctx.beginPath();ctx.moveTo(gq0.x,gq0.y);ctx.lineTo(gq1.x,gq1.y);ctx.stroke();' +
          'ctx.fillStyle="rgba(0,80,120,0.35)";ctx.font="7px \'Courier New\'";ctx.textAlign="right";' +
          'ctx.fillText(glat+"°N",gq0.x+28,gq0.y+4);' +
        '}' +
        // Countries
        'COUNTRIES.forEach(function(co){' +
          'var isFocus=(FOCUS&&co.c===FOCUS);' +
          'ctx.fillStyle=isFocus?"rgba(0,60,160,0.28)":co.fill;' +
          'ctx.strokeStyle=isFocus?"rgba(0,162,255,0.85)":co.line;' +
          'ctx.lineWidth=isFocus?1.5:0.7;ctx.setLineDash([]);' +
          'ctx.beginPath();' +
          'var p0=toC(co.pts[0][0],co.pts[0][1]);ctx.moveTo(p0.x,p0.y);' +
          'for(var pi=1;pi<co.pts.length;pi++){var pp=toC(co.pts[pi][0],co.pts[pi][1]);ctx.lineTo(pp.x,pp.y);}' +
          'ctx.closePath();ctx.fill();ctx.stroke();' +
          // Centroid label
          'var cla=0,clo=0;for(var ci=0;ci<co.pts.length-1;ci++){cla+=co.pts[ci][0];clo+=co.pts[ci][1];}' +
          'cla/=(co.pts.length-1);clo/=(co.pts.length-1);' +
          'var ctr=toC(cla,clo);' +
          'ctx.fillStyle=isFocus?"rgba(0,162,255,0.85)":"rgba(80,110,160,0.4)";' +
          'ctx.font=(isFocus?"bold ":"")+"8px \'Courier New\'";ctx.textAlign="center";' +
          'ctx.fillText(co.c,ctr.x,ctr.y);' +
        '});' +
        // FIR labels
        'ctx.fillStyle="rgba(0,80,140,0.45)";ctx.font="7px \'Courier New\'";ctx.textAlign="center";' +
        'FIRS.forEach(function(f){var fp=toC(f.lat,f.lon);ctx.fillText(f.n,fp.x,fp.y);});' +
        // Airports
        'if(SHOW_AP){' +
          'AIRPORTS.forEach(function(a){' +
            'var ap=toC(a.lat,a.lon);' +
            'var hasPlaybook=(a.i==="LFBO");' +
            'var isFocused=(FOCUS&&a.ctry===FOCUS);' +
            // Outer glow ring for airports with a full playbook
            'if(hasPlaybook){' +
              'ctx.beginPath();ctx.arc(ap.x,ap.y,7,0,Math.PI*2);' +
              'ctx.strokeStyle="rgba(0,242,255,0.3)";ctx.lineWidth=1;ctx.stroke();' +
            '}' +
            'ctx.beginPath();ctx.arc(ap.x,ap.y,isFocused||hasPlaybook?3.5:2,0,Math.PI*2);' +
            'ctx.fillStyle=hasPlaybook?"#00f2ff":isFocused?"rgba(0,200,255,0.9)":"rgba(80,140,180,0.65)";ctx.fill();' +
            'ctx.fillStyle=hasPlaybook?"rgba(0,242,255,0.9)":isFocused?"rgba(0,200,255,0.8)":"rgba(80,140,180,0.55)";' +
            'ctx.font=(hasPlaybook?"bold ":"")+"7px \'Courier New\'";ctx.textAlign="left";' +
            'ctx.fillText(a.i,ap.x+5,ap.y+3);' +
          '});' +
        '}' +
        // Sim flights
        'SIM_FLIGHTS.forEach(function(f){' +
          'if(f.lat==null||f.lon==null)return;' +
          'var fp=toC(f.lat,f.lon);' +
          'var hdg=(f.track||f.hdg||0)*Math.PI/180;' +
          'ctx.save();ctx.translate(fp.x,fp.y);ctx.rotate(hdg);' +
          'ctx.strokeStyle="#00f2ff";ctx.fillStyle="#00f2ff88";ctx.lineWidth=0.8;' +
          'ctx.beginPath();ctx.moveTo(0,-4);ctx.lineTo(-2,3);ctx.lineTo(0,1);ctx.lineTo(2,3);ctx.closePath();' +
          'ctx.fill();ctx.stroke();ctx.restore();' +
          'ctx.fillStyle="rgba(0,242,255,0.6)";ctx.font="7px \'Courier New\'";ctx.textAlign="left";' +
          'ctx.fillText((f.flight||f.hex||"").trim(),fp.x+5,fp.y-2);' +
        '});' +
        // Flight count label
        'var lbl=document.getElementById("' + uid + 'fltlbl");' +
        'if(lbl&&SIM_FLIGHTS.length)lbl.textContent="● "+SIM_FLIGHTS.length+" AIRCRAFT (SIM)";' +
      '}' +

      // ── Tooltip element ───────────────────────────────────────────────────
      'var TIP=document.getElementById("' + uid + 'tip");' +
      'var TIP_ICAO=document.getElementById("' + uid + 'tipicao");' +
      'var TIP_NAME=document.getElementById("' + uid + 'tipname");' +
      'var NAV=document.getElementById("' + uid + 'nav");' +

      // ── Interaction: pan + zoom + click ───────────────────────────────────
      // Use start/end position delta (not mousemove tracking) to distinguish
      // click from drag — mousemove-based moved=true fires on tiny wobble.
      'var drag=false,lx=0,ly=0,vx=0,vy=0,startX=0,startY=0;' +
      'c.addEventListener("mousedown",function(e){' +
        'drag=true;lx=e.clientX;ly=e.clientY;startX=e.clientX;startY=e.clientY;vx=0;vy=0;c.style.cursor="grabbing";' +
      '});' +
      'document.addEventListener("mouseup",function(e){' +
        'if(!drag)return;drag=false;c.style.cursor="grab";' +
        // If mouse didn't travel >6px total it's a click, not a drag
        'var totalMove=Math.abs(e.clientX-startX)+Math.abs(e.clientY-startY);' +
        'if(totalMove<6){' +
          'var rect=c.getBoundingClientRect();' +
          'var ap=nearestAirport(e.clientX-rect.left,e.clientY-rect.top,26);' +
          'if(ap){' +
            'var u=makeUrl(makePlaybook(ap));' +
            'var nav=document.getElementById("' + uid + 'nav");' +
            'var nava=document.getElementById("' + uid + 'nava");' +
            'if(nav&&nava){nava.href=u;nava.textContent="▶ OPEN "+ap.i+" PLAYBOOK";nav.style.display="block";}' +
            'try{window.top.location.href=u;}catch(ignore){}' +
          '}' +
        '}' +
      '});' +
      'document.addEventListener("mousemove",function(e){' +
        'if(drag){vx=e.clientX-lx;vy=e.clientY-ly;panX+=vx;panY+=vy;lx=e.clientX;ly=e.clientY;draw();}' +
        // Hover tooltip
        'var rect=c.getBoundingClientRect();' +
        'var cx=e.clientX-rect.left,cy=e.clientY-rect.top;' +
        'var ap=nearestAirport(cx,cy,26);' +
        'if(ap){' +
          'TIP.style.display="block";TIP.style.left=(cx+12)+"px";TIP.style.top=(cy-10)+"px";' +
          'TIP_ICAO.textContent=ap.i;TIP_NAME.textContent=ap.n;' +
          'if(!drag)c.style.cursor="pointer";' +
        '}else{' +
          'TIP.style.display="none";' +
          'if(!drag){c.style.cursor="grab";if(NAV)NAV.style.display="none";}' +
        '}' +
      '});' +
      'c.addEventListener("wheel",function(e){' +
        'e.preventDefault();' +
        'var factor=e.deltaY<0?1.12:0.89;' +
        'var mx=e.offsetX,my=e.offsetY;' +
        'panX=(panX-mx)*factor+mx;panY=(panY-my)*factor+my;scale*=factor;draw();' +
      '},{passive:false});' +
      // Inertia loop
      '(function tick(){vx*=0.88;vy*=0.88;if(!drag&&(Math.abs(vx)>0.3||Math.abs(vy)>0.3)){panX+=vx;panY+=vy;draw();}requestAnimationFrame(tick);})();' +

      'draw();' +
    '})();<\/script>';
};

// ── geo_iso_takeoff ── A321neo isometric takeoff simulation ──────────────────
_RENDERERS['geo_iso_takeoff'] = function(b) {
  var uid     = 'gito' + Math.random().toString(36).substr(2, 6);
  var title   = _esc(b.title   || 'LFBO RWY 32L — A321neo DEPARTURE');
  var airline = ((b.airline     || 'AIB') + '').toUpperCase();
  var acType  = ((b.aircraft_type || 'A21N') + '').toUpperCase();
  // Initial accent for HUD / LIVE RADAR button
  var accentMap = {AIB:'#009ace',EZY:'#ff6600',AFR:'#0050a0',BAW:'#eb2226',DLH:'#1a3c8f',RYR:'#073590'};
  var accent  = accentMap[airline] || '#009ace';

  var lS = acType === 'A21N' ? 1.25 : 1.0;
  var wS = acType === 'A21N' ? 1.10 : 1.0;

  // Pre-generate radar URL server-side — bypasses client btoa issues
  var radarPayload = JSON.stringify([{
    type:'airspace_command_deck', height:'fullscreen',
    center_lat:43.629, center_lon:1.363, center_icao:'LFBO', country:'FR', zoom:35,
    chyron_title:'LFBO TMA — APPROACH CONTROL',
    chyron_subtitle:'Runway 32L/R Active • Toulouse Blagnac',
    ticker_text:'✈️ TOULOUSE BLAGNAC APPROACH CONTROL • RUNWAY 32L/R ACTIVE • LIVE ADS-B ACTIVE •',
    ticker_speed: 45
  }]);
  var radarUrl = ScriptApp.getService().getUrl() + '?p=' +
    Utilities.base64EncodeWebSafe(Utilities.newBlob(radarPayload).getBytes()).replace(/=/g, '');

  return '<style>' +
    '#' + uid + 'w{position:relative;width:100%;height:100vh;background:#02040c;overflow:hidden;font-family:"Courier New",monospace;}' +
    '#' + uid + 'c{position:absolute;inset:0;width:100%;height:100%;}' +
    '#' + uid + 'hud{position:absolute;top:18px;left:18px;z-index:10;pointer-events:none;' +
      'background:rgba(2,8,20,.9);border:1px solid rgba(0,242,255,.2);border-radius:6px;padding:12px 18px;}' +
    '#' + uid + 'hud .hl{font-size:7px;letter-spacing:.18em;color:#00f2ff;margin-bottom:4px;}' +
    '#' + uid + 'hud .ht{font-size:13px;font-weight:700;color:#fff;}' +
    '#' + uid + 'hud .hd{font-size:8px;color:#475569;margin-top:6px;min-width:320px;}' +
    '#' + uid + 'sel-wrap{position:absolute;top:18px;right:18px;z-index:20;' +
      'background:rgba(2,8,20,.88);border:1px solid rgba(255,255,255,.1);border-radius:6px;padding:8px 12px;' +
      'display:flex;align-items:center;gap:8px;}' +
    '#' + uid + 'sel-label{font-size:7px;color:rgba(255,255,255,.4);letter-spacing:.1em;}' +
    '#' + uid + 'sel{background:#0d1220;color:#00f2ff;border:1px solid rgba(0,242,255,.25);' +
      'border-radius:4px;font-family:"Courier New",monospace;font-size:9px;padding:4px 8px;' +
      'outline:none;cursor:pointer;font-weight:700;}' +
    '#' + uid + 'btn{position:absolute;bottom:28px;right:28px;z-index:20;' +
      'background:' + accent + ';color:#000;font:700 11px "Courier New",monospace;' +
      'padding:11px 22px;border-radius:4px;text-decoration:none;letter-spacing:.12em;}' +
    '#' + uid + 'btn:hover{opacity:.8;}' +
    '</style>' +
    '<div id="' + uid + 'w">' +
      '<canvas id="' + uid + 'c"></canvas>' +
      '<div id="' + uid + 'hud">' +
        '<div class="hl">' + acType + ' · TOULOUSE-BLAGNAC · LIVERY SIM</div>' +
        '<div class="ht">' + title + '</div>' +
        '<div class="hd" id="' + uid + 'tel">AWAITING TAKEOFF CLEARANCE</div>' +
      '</div>' +
      '<div id="' + uid + 'sel-wrap">' +
        '<span id="' + uid + 'sel-label">LIVERY</span>' +
        '<select id="' + uid + 'sel">' +
          '<option value="AIB"' + (airline==='AIB'?' selected':'') + '>AIRBUS FACTORY HOUSE</option>' +
          '<option value="EZY"' + (airline==='EZY'?' selected':'') + '>EASYJET ORANGE</option>' +
          '<option value="AFR"' + (airline==='AFR'?' selected':'') + '>AIR FRANCE FLAGSHIP</option>' +
          '<option value="BAW"' + (airline==='BAW'?' selected':'') + '>BRITISH AIRWAYS</option>' +
          '<option value="DLH"' + (airline==='DLH'?' selected':'') + '>LUFTHANSA NAVY</option>' +
          '<option value="RYR"' + (airline==='RYR'?' selected':'') + '>RYANAIR DARK BLUE</option>' +
        '</select>' +
      '</div>' +
      '<a id="' + uid + 'btn" href="' + radarUrl + '" target="_top">LIVE RADAR →</a>' +
    '</div>' +

    '<script>(function(){' +
      'var c=document.getElementById("' + uid + 'c");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'var tel=document.getElementById("' + uid + 'tel");' +
      'var sel=document.getElementById("' + uid + 'sel");' +
      'var W=0,H=0;' +
      'function resize(){c.width=c.offsetWidth||window.innerWidth;c.height=c.offsetHeight||window.innerHeight;W=c.width;H=c.height;}' +
      'window.addEventListener("resize",resize);resize();' +

      // ── A2UI Airline Livery Database ─────────────────────────────────────
      // body=fuselage/nose, tail=fin, sk=sharklet tips, accent=display color
      'var AL={' +
        'AIB:{name:"Airbus Factory House",body:{r:245,g:247,b:250},tail:{r:10,g:34,b:84},sk:{r:0,g:154,b:206}},' +
        'EZY:{name:"easyJet",body:{r:255,g:102,b:0},tail:{r:255,g:102,b:0},sk:{r:255,g:102,b:0}},' +
        'AFR:{name:"Air France",body:{r:245,g:247,b:250},tail:{r:0,g:35,b:149},sk:{r:0,g:35,b:149}},' +
        'BAW:{name:"British Airways",body:{r:245,g:247,b:250},tail:{r:7,g:90,b:170},sk:{r:7,g:90,b:170}},' +
        'DLH:{name:"Lufthansa",body:{r:245,g:247,b:250},tail:{r:26,g:60,b:143},sk:{r:26,g:60,b:143}},' +
        'RYR:{name:"Ryanair",body:{r:7,g:53,b:144},tail:{r:7,g:53,b:144},sk:{r:7,g:53,b:144}}' +
      '};' +
      'var activeLivery=AL["' + airline + '"]||AL.AIB;' +
      'sel.addEventListener("change",function(e){activeLivery=AL[e.target.value]||AL.AIB;});' +

      'var LS=' + lS + ',WS=' + wS + ';' +
      'var SC=3.5;' +
      'var COS30=0.866,SIN30=0.5;' +

      // ── Isometric projection (x=right, y=up, z=depth) ─────────────────────
      // In isometric: +Z → lower-left (near), -Z → upper-right (far/away)
      // Aircraft flies in -Z direction (away into distance)
      'function proj(x,y,z){' +
        'return{x:W*0.5+(x-z)*COS30*SC, y:H*0.8+(x+z)*SIN30*SC-y*SC};' +
      '}' +

      // ── A321neo unified mesh: 47 nodes, 66 lines + wing flex + depth opacity ─
      'var nodes=[' +
        '{x:54,y:-1.5,z:0},' +    // 0  nose tip
        // Nose taper ring
        '{x:44,y:2,z:2.5},' +     // 1
        '{x:44,y:0.5,z:3.5},' +   // 2
        '{x:44,y:-2,z:2.5},' +    // 3
        '{x:44,y:-2,z:-2.5},' +   // 4
        '{x:44,y:0.5,z:-3.5},' +  // 5
        '{x:44,y:2,z:-2.5},' +    // 6
        // Cockpit hex ring
        '{x:34,y:5,z:4.5},' +     // 7
        '{x:34,y:1.5,z:6},' +     // 8
        '{x:34,y:-4,z:4.5},' +    // 9
        '{x:34,y:-4,z:-4.5},' +   // 10
        '{x:34,y:1.5,z:-6},' +    // 11
        '{x:34,y:5,z:-4.5},' +    // 12
        // Mid-cabin hex ring
        '{x:-20,y:5.5,z:4.5},' +  // 13
        '{x:-20,y:1.5,z:6},' +    // 14
        '{x:-20,y:-4,z:4.5},' +   // 15
        '{x:-20,y:-4,z:-4.5},' +  // 16
        '{x:-20,y:1.5,z:-6},' +   // 17
        '{x:-20,y:5.5,z:-4.5},' + // 18
        // Aft hex ring
        '{x:-65,y:3.5,z:2},' +    // 19
        '{x:-65,y:1,z:3.5},' +    // 20
        '{x:-65,y:-2,z:2},' +     // 21
        '{x:-65,y:-2,z:-2},' +    // 22
        '{x:-65,y:1,z:-3.5},' +   // 23
        '{x:-65,y:3.5,z:-2},' +   // 24
        '{x:-78,y:0.5,z:0},' +    // 25 APU
        // Empennage
        '{x:-74,y:24,z:0},' +     // 26 v-stab apex
        '{x:-74,y:1.5,z:18},' +   // 27 stbd tailplane
        '{x:-74,y:1.5,z:-18},' +  // 28 port tailplane
        // L wing
        '{x:12,y:-2.5,z:-6},' +   // 29 L root LE
        '{x:-12,y:-2.5,z:-6},' +  // 30 L root TE
        '{x:-24,y:-0.5,z:-52},' + // 31 L tip TE
        '{x:-18,y:-0.5,z:-52},' + // 32 L tip LE
        '{x:-18,y:7,z:-52},' +    // 33 L sharklet
        // R wing
        '{x:12,y:-2.5,z:6},' +    // 34 R root LE
        '{x:-12,y:-2.5,z:6},' +   // 35 R root TE
        '{x:-24,y:-0.5,z:52},' +  // 36 R tip TE
        '{x:-18,y:-0.5,z:52},' +  // 37 R tip LE
        '{x:-18,y:7,z:52},' +     // 38 R sharklet
        // LEAP-1A nacelles — top rail
        '{x:16,y:-6.5,z:-16},' +  // 39 L intake top
        '{x:2,y:-5.5,z:-16},' +   // 40 L exhaust top
        '{x:16,y:-6.5,z:16},' +   // 41 R intake top
        '{x:2,y:-5.5,z:16},' +    // 42 R exhaust top
        // LEAP-1A nacelles — bottom rail
        '{x:16,y:-9.5,z:-16},' +  // 43 L intake bottom
        '{x:2,y:-8.5,z:-16},' +   // 44 L exhaust bottom
        '{x:16,y:-9.5,z:16},' +   // 45 R intake bottom
        '{x:2,y:-8.5,z:16},' +    // 46 R exhaust bottom
        // Pylon anchor stations — aligns engine pods parallel to fuselage
        '{x:6,y:-2.1,z:-16},' +   // 47 L mid-wing pylon anchor
        '{x:6,y:-2.1,z:16}' +     // 48 R mid-wing pylon anchor
      '];' +
      // ── Solid face matrix — Painter's Algorithm + Lambertian shading ─────────
      // Types: "f"=fuselage, "n"=nose, "fin"=vertical fin, "s"=stabiliser,
      //        "w"=wing, "sk"=sharklet, "e"=engine nacelle
      'var faces=[' +
        // Tail cone
        '{n:[19,20,25],t:"f"},{n:[24,19,25],t:"f"},' +
        '{n:[20,21,25],t:"f"},{n:[23,24,25],t:"f"},' +
        // Vertical fin + tailplanes
        '{n:[19,24,26],t:"fin"},' +
        '{n:[20,25,27],t:"s"},{n:[23,25,28],t:"s"},' +
        // Aft tube panels (mid→aft ring)
        '{n:[13,14,20,19],t:"f"},{n:[14,15,21,20],t:"f"},' +
        '{n:[15,16,22,21],t:"f"},{n:[16,17,23,22],t:"f"},' +
        '{n:[17,18,24,23],t:"f"},{n:[18,13,19,24],t:"f"},' +
        // Main cabin panels (cockpit→mid ring)
        '{n:[7,8,14,13],t:"f"},{n:[8,9,15,14],t:"f"},' +
        '{n:[9,10,16,15],t:"f"},{n:[10,11,17,16],t:"f"},' +
        '{n:[11,12,18,17],t:"f"},{n:[12,7,13,18],t:"f"},' +
        // Nose cone + taper panels
        '{n:[1,2,8,7],t:"f"},{n:[2,3,9,8],t:"f"},' +
        '{n:[3,4,10,9],t:"f"},{n:[4,5,11,10],t:"f"},' +
        '{n:[5,6,12,11],t:"f"},{n:[6,1,7,12],t:"f"},' +
        '{n:[0,1,2],t:"n"},{n:[0,2,3],t:"n"},{n:[0,3,4],t:"n"},' +
        '{n:[0,4,5],t:"n"},{n:[0,5,6],t:"n"},{n:[0,6,1],t:"n"},' +
        // Wings — winding: root-LE → tip-LE → tip-TE → root-TE gives upward normals
        '{n:[29,32,31,30],t:"w"},{n:[32,33,31],t:"sk"},' +
        '{n:[34,37,36,35],t:"w"},{n:[37,38,36],t:"sk"},' +
        // LEAP-1A nacelles — anchored to pylon nodes 47/48 only (not wing roots 29/30/34/35)
        '{n:[47,39,40],t:"e"},{n:[47,44,43],t:"e"},{n:[39,43,44,40],t:"e"},' +
        '{n:[48,41,42],t:"e"},{n:[48,46,45],t:"e"},{n:[41,45,46,42],t:"e"}' +
      '];' +

      // ── drawAC: Painter's Algorithm with Lambertian flat shading ──────────
      'function drawAC(pz,py,ang){' +
        'var co=Math.cos(ang),si=Math.sin(ang);' +
        'var flex=py>0?Math.min(4.5,py*0.07):0;' +
        'var pts=nodes.map(function(v,idx){' +
          'var wy=v.y;' +
          'if(Math.abs(v.z)>5.5&&idx>=29){wy+=Math.pow(Math.abs(v.z)/52,2)*flex;}' +
          'var rx=v.x*co-wy*si,ry=v.x*si+wy*co;' +
          'var sp=proj(v.z,ry+py,pz-rx);' +
          'sp.wx=v.z;sp.wy=ry+py;sp.wz=pz-rx;' +
          'return sp;' +
        '});' +
        // Ground shadow
        'var sN=proj(0,0,pz-54),sT=proj(0,0,pz+78);' +
        'ctx.strokeStyle="rgba(0,0,0,.42)";ctx.lineWidth=4;' +
        'ctx.beginPath();ctx.moveTo(sN.x,sN.y);ctx.lineTo(sT.x,sT.y);ctx.stroke();' +
        // Sun behind camera, slightly left — key light over viewer's shoulder
        'var sx=-0.1,sy=0.8,sz=0.6;' +
        'var sm=Math.sqrt(sx*sx+sy*sy+sz*sz);sx/=sm;sy/=sm;sz/=sm;' +
        // Sort faces back-to-front
        'var sf=faces.map(function(f){' +
          'var d=0;f.n.forEach(function(i){d+=pts[i].wz;});' +
          'return{n:f.n,t:f.t,d:d/f.n.length};' +
        '}).sort(function(a,b){return b.d-a.d;});' +
        // Paint each face — material driven by activeLivery
        'sf.forEach(function(f){' +
          'var p0=pts[f.n[0]],p1=pts[f.n[1]],p2=pts[f.n[2]];' +
          'var ux=p1.wx-p0.wx,uy=p1.wy-p0.wy,uz=p1.wz-p0.wz;' +
          'var vx=p2.wx-p0.wx,vy=p2.wy-p0.wy,vz=p2.wz-p0.wz;' +
          'var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;' +
          'var nm=Math.sqrt(nx*nx+ny*ny+nz*nz);' +
          'if(nm>0){nx/=nm;ny/=nm;nz/=nm;}' +
          'var lit=Math.min(1,Math.max(0.46,nx*sx+ny*sy+nz*sz));' +
          // A2UI livery dispatch
          'var mc;' +
          'if(f.t==="fin"){mc=activeLivery.tail;}' +
          'else if(f.t==="sk"){mc=activeLivery.sk;}' +
          'else if(f.t==="w"||f.t==="s"){mc={r:168,g:174,b:182};}' +
          'else if(f.t==="e"){mc={r:245,g:247,b:250};}' +
          'else{mc=activeLivery.body;}' +
          'ctx.fillStyle="rgb("+Math.round(mc.r*lit)+","+Math.round(mc.g*lit)+","+Math.round(mc.b*lit)+")";' +
          'ctx.strokeStyle="rgba("+Math.round(mc.r*1.02)+","+Math.round(mc.g*1.02)+","+Math.round(mc.b*1.02)+",.18)";' +
          'ctx.lineWidth=0.7;' +
          'ctx.beginPath();' +
          'f.n.forEach(function(ni,i){i===0?ctx.moveTo(pts[ni].x,pts[ni].y):ctx.lineTo(pts[ni].x,pts[ni].y);});' +
          'ctx.closePath();ctx.fill();ctx.stroke();' +
        '});' +
      '}' +

      // ── Runway ground plane & markings ─────────────────────────────────────
      'function drawRunway(acZ){' +
        // Wide grid
        'ctx.strokeStyle="rgba(0,40,80,.35)";ctx.lineWidth=0.5;ctx.setLineDash([]);' +
        'for(var g=-80;g<=160;g+=25){' +
          'var a=proj(-30,0,g),b=proj(30,0,g);' +
          'ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();' +
        '}' +
        'for(var g=-30;g<=30;g+=15){' +
          'var a=proj(g,0,-80),b=proj(g,0,160);' +
          'ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();' +
        '}' +
        // Runway edges
        'ctx.strokeStyle="rgba(80,90,120,.9)";ctx.lineWidth=2;' +
        'var re1a=proj(-12,0,-80),re1b=proj(-12,0,160);' +
        'var re2a=proj(12,0,-80),re2b=proj(12,0,160);' +
        'ctx.beginPath();ctx.moveTo(re1a.x,re1a.y);ctx.lineTo(re1b.x,re1b.y);ctx.stroke();' +
        'ctx.beginPath();ctx.moveTo(re2a.x,re2a.y);ctx.lineTo(re2b.x,re2b.y);ctx.stroke();' +
        // Runway centreline dashes
        'ctx.strokeStyle="rgba(255,245,80,.45)";ctx.lineWidth=1;ctx.setLineDash([10,14]);' +
        'for(var d=-80;d<160;d+=24){' +
          'var a=proj(0,0,d),b=proj(0,0,d+12);' +
          'ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();' +
        '}' +
        'ctx.setLineDash([]);' +
        // Runway edge lights (ahead of aircraft)
        'ctx.fillStyle="#fff8c0";' +
        'for(var lz=acZ-10;lz>-80;lz-=18){' +
          'var lp1=proj(-12,0.3,lz),lp2=proj(12,0.3,lz);' +
          'ctx.beginPath();ctx.arc(lp1.x,lp1.y,2,0,6.28);ctx.fill();' +
          'ctx.beginPath();ctx.arc(lp2.x,lp2.y,2,0,6.28);ctx.fill();' +
        '}' +
        // Touchdown zone — amber lights on the near side
        'ctx.fillStyle="#ffa500";' +
        'for(var lz=acZ+2;lz<160&&lz<acZ+60;lz+=18){' +
          'var lp1=proj(-10,0.3,lz),lp2=proj(10,0.3,lz);' +
          'ctx.beginPath();ctx.arc(lp1.x,lp1.y,1.5,0,6.28);ctx.fill();' +
          'ctx.beginPath();ctx.arc(lp2.x,lp2.y,1.5,0,6.28);ctx.fill();' +
        '}' +
      '}' +

      // ── Exhaust particles ──────────────────────────────────────────────────
      'var particles=[];' +
      'function spawnExhaust(ox,oy,oz){' +
        // Two engines, laterally offset, below wing
        'var engs=[[-16,-8.5,oz],[16,-8.5,oz]];' +
        'engs.forEach(function(e){' +
          'for(var i=0;i<2;i++){' +
            'particles.push({' +
              'x:e[0]+(Math.random()-.5)*3,' +
              'y:e[1]+oy+(Math.random()-.5),' +
              'z:e[2]+(Math.random()-.5)*2,' +
              'vx:(Math.random()-.5)*.4,' +
              'vy:.1+Math.random()*.3,' +
              'vz:.8+Math.random()*1.8,' + // +Z = behind aircraft (which moves in -Z)
              'life:1.0,sz:1.5+Math.random()*2.5' +
            '});' +
          '}' +
        '});' +
      '}' +
      'function drawParticles(){' +
        'particles.forEach(function(p){' +
          'p.x+=p.vx;p.y+=p.vy;p.z+=p.vz;p.life-=0.025;' +
          'if(p.life<=0)return;' +
          'var alpha=p.life*.8;' +
          'ctx.fillStyle="rgba(255,"+(120+Math.round(100*p.life))+",40,"+alpha+")";' +
          'var sp=proj(p.x,p.y,p.z);' +
          'ctx.beginPath();ctx.arc(sp.x,sp.y,p.sz*p.life,0,6.28);ctx.fill();' +
        '});' +
        'particles=particles.filter(function(p){return p.life>0;});' +
      '}' +

      // ── Background rocket — draws Ariane 6 launching far-right of scene ────
      'var rky=0,rVY=0,rBoff=0,rT=0;' +
      'function drawRocketBg(){' +
        'var ox=62,oz=130,sc=0.4;' +
        'var sun={x:-0.1,y:0.8,z:0.6};' +
        'var sm=Math.sqrt(sun.x*sun.x+sun.y*sun.y+sun.z*sun.z);sun.x/=sm;sun.y/=sm;sun.z/=sm;' +
        // 6-point ring — coordinates pre-scaled by sc
        'function rk(h,r){' +
          'var p=[];' +
          'for(var i=0;i<6;i++){var a=i/6*6.2832;p.push({x:Math.cos(a)*r*sc,y:h*sc,z:Math.sin(a)*r*sc});}' +
          'return p;' +
        '}' +
        // Solid quad cylinder — winding [base_i→top_i→top_n→base_n] = outward normals
        'function drawSolidBgSeg(h1,r1,h2,r2,dx,dz,rgb){' +
          'var r1p=rk(h1,r1),r2p=rk(h2,r2),fl=[];' +
          'for(var i=0;i<6;i++){' +
            'var n=(i+1)%6;' +
            'var v0=r1p[i],v1=r2p[i],v2=r2p[n],v3=r1p[n];' +
            'var p0=proj(v0.x+dx+ox,v0.y+rky,v0.z+dz+oz);p0.wx=v0.x+dx;p0.wy=v0.y+rky;p0.wz=v0.z+dz;' +
            'var p1=proj(v1.x+dx+ox,v1.y+rky,v1.z+dz+oz);p1.wx=v1.x+dx;p1.wy=v1.y+rky;p1.wz=v1.z+dz;' +
            'var p2=proj(v2.x+dx+ox,v2.y+rky,v2.z+dz+oz);p2.wx=v2.x+dx;p2.wy=v2.y+rky;p2.wz=v2.z+dz;' +
            'var p3=proj(v3.x+dx+ox,v3.y+rky,v3.z+dz+oz);p3.wx=v3.x+dx;p3.wy=v3.y+rky;p3.wz=v3.z+dz;' +
            'var d=(p0.wx+p0.wz+p1.wx+p1.wz+p2.wx+p2.wz+p3.wx+p3.wz)/4;' +
            'fl.push({pts:[p0,p1,p2,p3],d:d});' +
          '}' +
          'fl.sort(function(a,b){return a.d-b.d;});' +
          'fl.forEach(function(f){' +
            'var o0=f.pts[0],o1=f.pts[1],o2=f.pts[2];' +
            'var ux=o1.wx-o0.wx,uy=o1.wy-o0.wy,uz=o1.wz-o0.wz;' +
            'var vx=o2.wx-o0.wx,vy=o2.wy-o0.wy,vz=o2.wz-o0.wz;' +
            'var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;' +
            'var nm=Math.sqrt(nx*nx+ny*ny+nz*nz);if(nm>0){nx/=nm;ny/=nm;nz/=nm;}' +
            'var lit=Math.min(1,Math.max(0.42,nx*sun.x+ny*sun.y+nz*sun.z));' +
            'ctx.fillStyle="rgb("+Math.round(rgb.r*lit)+","+Math.round(rgb.g*lit)+","+Math.round(rgb.b*lit)+")";' +
            'ctx.strokeStyle="rgba("+Math.round(rgb.r*1.02)+","+Math.round(rgb.g*1.02)+","+Math.round(rgb.b*1.02)+",.12)";' +
            'ctx.lineWidth=0.5;' +
            'ctx.beginPath();ctx.moveTo(f.pts[0].x,f.pts[0].y);' +
            'ctx.lineTo(f.pts[1].x,f.pts[1].y);ctx.lineTo(f.pts[2].x,f.pts[2].y);ctx.lineTo(f.pts[3].x,f.pts[3].y);' +
            'ctx.closePath();ctx.fill();ctx.stroke();' +
          '});' +
        '}' +
        // SRBs → core → fairing
        '[{sign:-1},{sign:1}].forEach(function(srb){' +
          'var bx=(srb.sign*9*sc)+(srb.sign*rBoff*sc);' +
          'var by=rBoff*0.3;' +
          'drawSolidBgSeg(-by,2.5,35-by,2.5,bx,0,{r:56,g:189,b:248});' +
        '});' +
        'drawSolidBgSeg(0,7,55,7,0,0,{r:245,g:247,b:250});' +
        'drawSolidBgSeg(55,7,73,0.2,0,0,{r:90,g:98,b:105});' +
        // Core flame glow
        'var fp=proj(ox,rky,oz);' +
        'var cg=ctx.createRadialGradient(fp.x,fp.y,0,fp.x,fp.y,28);' +
        'cg.addColorStop(0,"rgba(255,248,220,0.92)");' +
        'cg.addColorStop(0.3,"rgba(255,150,50,0.65)");' +
        'cg.addColorStop(0.7,"rgba(200,60,20,0.3)");' +
        'cg.addColorStop(1,"rgba(0,0,0,0)");' +
        'ctx.fillStyle=cg;ctx.beginPath();ctx.arc(fp.x,fp.y,28,0,6.28);ctx.fill();' +
        'if(rBoff<5){' +
          '[{bx:-9*sc},{bx:9*sc}].forEach(function(s){' +
            'var sfp=proj(s.bx+ox,rky,oz);' +
            'var sg=ctx.createRadialGradient(sfp.x,sfp.y,0,sfp.x,sfp.y,16);' +
            'sg.addColorStop(0,"rgba(255,220,140,0.8)");' +
            'sg.addColorStop(1,"rgba(0,0,0,0)");' +
            'ctx.fillStyle=sg;ctx.beginPath();ctx.arc(sfp.x,sfp.y,16,0,6.28);ctx.fill();' +
          '});' +
        '}' +
      '}' +

      // ── Animation state ────────────────────────────────────────────────────
      'var t=0,posZ=80,posY=0,pitchAng=0,speed=0;' +

      'function frame(){' +
        't++;' +

        // Phase 1: ground roll (0→90)
        'if(t<=90){' +
          'speed=Math.min(speed+0.55,38);' +
          'posZ-=speed*0.075;' +
          'posY=0;pitchAng=0;' +
          'tel.textContent="RWY 32L — GROUND ROLL — "+(Math.round(speed*3.7))+"kt";' +

        // Phase 2: rotation (90→130)
        '}else if(t<=130){' +
          'speed=Math.min(speed+0.2,42);' +
          'posZ-=speed*0.075;' +
          'pitchAng=Math.min(pitchAng+0.009,0.24);' +
          'posY+=Math.sin(pitchAng)*speed*0.05;' +
          'tel.textContent="ROTATE — Vr 140kt — POSITIVE CLIMB — ALT "+(Math.round(posY*9))+"ft";' +

        // Phase 3: climb out (130→230)
        '}else if(t<=230){' +
          'speed=Math.min(speed+0.06,46);' +
          'posZ-=speed*0.075;' +
          'posY+=Math.sin(pitchAng)*speed*0.09;' +
          'tel.textContent="GEAR UP — FLAPS 1 — CLIMB — ALT "+(Math.round(posY*9))+"ft — "+(Math.round(speed*3.7))+"kt";' +

        // Reset
        '}else{' +
          't=0;posZ=80;posY=0;pitchAng=0;speed=0;particles=[];' +
        '}' +

        // Rocket background — independent 290-frame cycle
        'rT++;' +
        'if(rT<=200){rVY+=0.012;rky+=rVY;}' +
        'else if(rT<=290){rVY+=0.008;rky+=rVY;rBoff=Math.min(18,(rT-200)*0.2);}' +
        'else{rT=0;rky=0;rVY=0;rBoff=0;}' +

        // ── Draw frame ──────────────────────────────────────────────────────
        'ctx.clearRect(0,0,W,H);' +
        'ctx.fillStyle="#02040c";ctx.fillRect(0,0,W,H);' +

        // Static star field
        'ctx.fillStyle="rgba(255,255,255,.25)";' +
        '[.08,.19,.35,.52,.67,.81,.91].forEach(function(s,i){' +
          'ctx.fillRect(s*W,(i%3*.05+.02)*H,i%2?1:2,i%2?1:2);' +
        '});' +

        'drawRocketBg();' +
        'drawRunway(posZ);' +
        'if(t>2)spawnExhaust(0,posY,posZ);' +
        'drawParticles();' +
        'drawAC(posZ,posY,pitchAng);' +

        'requestAnimationFrame(frame);' +
      '}' +
      'frame();' +
    '})();<\/script>';
};

// ── geo_iso_rocket_launch ── Ariane 6 / heavy-lift solid-surface launch ──────
_RENDERERS['geo_iso_rocket_launch'] = function(b) {
  var uid         = 'girl' + Math.random().toString(36).substr(2, 6);
  var title       = _esc(b.title   || 'KOUROU ELA-4 — HEAVY LIFT INJECTION PROFILE');
  var vehicle     = ((b.vehicle    || 'ARIANE_6') + '').toUpperCase();
  var accentColor = vehicle === 'ARIANE_6' ? '#38bdf8' : '#a78bfa';

  return '<style>' +
    '#' + uid + 'w{position:relative;width:100%;height:100vh;background:#05070f;overflow:hidden;font-family:monospace;}' +
    '#' + uid + 'c{position:absolute;inset:0;width:100%;height:100%;}' +
    '#' + uid + 'hud{position:absolute;top:20px;left:20px;background:rgba(9,11,20,.85);backdrop-filter:blur(10px);' +
      'padding:14px 20px;border-radius:10px;border:1px solid rgba(255,255,255,.1);pointer-events:none;z-index:10;}' +
    '#' + uid + 'hud .hl{font-size:7px;font-weight:700;color:' + accentColor + ';letter-spacing:.15em;margin-bottom:2px;}' +
    '#' + uid + 'hud .ht{font-size:14px;font-weight:800;color:#fff;}' +
    '#' + uid + 'hud .hd{font-size:8px;color:#4b5563;margin-top:6px;min-width:280px;}' +
    '</style>' +
    '<div id="' + uid + 'w">' +
      '<canvas id="' + uid + 'c"></canvas>' +
      '<div id="' + uid + 'hud">' +
        '<div class="hl">TACTICAL TELEMETRY STREAM</div>' +
        '<div class="ht">' + title + '</div>' +
        '<div class="hd" id="' + uid + 'tel">T+000S | VEL: 0M/S | ALT: 0KM</div>' +
      '</div>' +
    '</div>' +

    '<script>(function(){' +
      'var c=document.getElementById("' + uid + 'c");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'var tel=document.getElementById("' + uid + 'tel");' +
      'var ACC="' + accentColor + '";' +

      'function resize(){c.width=c.offsetWidth*2;c.height=c.offsetHeight*2;ctx.scale(2,2);}' +
      'window.addEventListener("resize",resize);resize();' +

      // Isometric projection — SC=3 for rocket atom
      'var COS30=0.866,SIN30=0.5;' +
      'function proj(x,y,z){' +
        'var W=c.offsetWidth,H=c.offsetHeight;' +
        'return{x:W*.5+(x-z)*COS30*3,y:H*.85+(x+z)*SIN30*3-y*3};' +
      '}' +

      // Hex ring builder
      'function ring(h,r,segs){' +
        'var pts=[];' +
        'for(var i=0;i<segs;i++){' +
          'var a=i/segs*Math.PI*2;' +
          'pts.push({x:Math.cos(a)*r,y:h,z:Math.sin(a)*r});' +
        '}' +
        'return pts;' +
      '}' +

      // Solid cylinder — Painter's Algorithm + Lambertian
      // Winding: [base_i, top_i, top_n, base_n] → outward normals for +Y cylinder
      'function drawSolidRocketCylinder(h1,r1,h2,r2,segs,dx,dy,dz,type){' +
        'var r1p=ring(h1,r1,segs),r2p=ring(h2,r2,segs);' +
        'var sun={x:-0.1,y:0.8,z:0.6};' +
        'var sm=Math.sqrt(sun.x*sun.x+sun.y*sun.y+sun.z*sun.z);sun.x/=sm;sun.y/=sm;sun.z/=sm;' +
        'var fl=[];' +
        'for(var i=0;i<segs;i++){' +
          'var n=(i+1)%segs;' +
          // v0=base_i, v1=top_i, v2=top_n, v3=base_n
          'var v0=r1p[i],v1=r2p[i],v2=r2p[n],v3=r1p[n];' +
          'var p0=proj(v0.x+dx,v0.y+dy,v0.z+dz);p0.wx=v0.x+dx;p0.wy=v0.y+dy;p0.wz=v0.z+dz;' +
          'var p1=proj(v1.x+dx,v1.y+dy,v1.z+dz);p1.wx=v1.x+dx;p1.wy=v1.y+dy;p1.wz=v1.z+dz;' +
          'var p2=proj(v2.x+dx,v2.y+dy,v2.z+dz);p2.wx=v2.x+dx;p2.wy=v2.y+dy;p2.wz=v2.z+dz;' +
          'var p3=proj(v3.x+dx,v3.y+dy,v3.z+dz);p3.wx=v3.x+dx;p3.wy=v3.y+dy;p3.wz=v3.z+dz;' +
          // Isometric depth = (wx+wz) averaged — ascending sort = back first
          'var depth=(p0.wx+p0.wz+p1.wx+p1.wz+p2.wx+p2.wz+p3.wx+p3.wz)/4;' +
          'fl.push({pts:[p0,p1,p2,p3],d:depth,type:type});' +
        '}' +
        'fl.sort(function(a,b){return a.d-b.d;});' +
        'fl.forEach(function(f){' +
          'var o0=f.pts[0],o1=f.pts[1],o2=f.pts[2];' +
          'var ux=o1.wx-o0.wx,uy=o1.wy-o0.wy,uz=o1.wz-o0.wz;' +
          'var vx=o2.wx-o0.wx,vy=o2.wy-o0.wy,vz=o2.wz-o0.wz;' +
          'var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;' +
          'var nm=Math.sqrt(nx*nx+ny*ny+nz*nz);if(nm>0){nx/=nm;ny/=nm;nz/=nm;}' +
          'var lit=Math.min(1,Math.max(0.42,nx*sun.x+ny*sun.y+nz*sun.z));' +
          'var r=245,g=247,b=250;' +
          'if(f.type==="booster"){r=56;g=189;b=248;}' +
          'else if(f.type==="payload"){r=90;g=98;b=105;}' +
          'ctx.fillStyle="rgb("+Math.round(r*lit)+","+Math.round(g*lit)+","+Math.round(b*lit)+")";' +
          'ctx.strokeStyle="rgba("+Math.round(r*1.02)+","+Math.round(g*1.02)+","+Math.round(b*1.02)+",.16)";' +
          'ctx.lineWidth=0.7;' +
          'ctx.beginPath();ctx.moveTo(f.pts[0].x,f.pts[0].y);' +
          'ctx.lineTo(f.pts[1].x,f.pts[1].y);ctx.lineTo(f.pts[2].x,f.pts[2].y);ctx.lineTo(f.pts[3].x,f.pts[3].y);' +
          'ctx.closePath();ctx.fill();ctx.stroke();' +
        '});' +
      '}' +

      'var posY=0,velY=0,acc=0.04,t=0,boostOff=0;' +
      'var particles=[];' +

      'function spawnFlame(){' +
        'particles.push({x:(Math.random()-.5)*4,y:posY-5,z:(Math.random()-.5)*4,' +
          'vx:(Math.random()-.5)*.3,vy:-1.5-Math.random()*1,vz:(Math.random()-.5)*.3,' +
          'life:1,sz:2+Math.random()*3});' +
        'if(t<120){' +
          '[[-12,0],[12,0]].forEach(function(e){' +
            'particles.push({x:e[0]+(Math.random()-.5)*2,y:posY-5,z:e[1]+(Math.random()-.5)*2,' +
              'vx:(Math.random()-.5)*.4,vy:-1.2-Math.random()*.8,vz:(Math.random()-.5)*.4,' +
              'life:1,sz:1+Math.random()*2});' +
          '});' +
        '}' +
      '}' +

      'function drawParticles(){' +
        'particles.forEach(function(p){' +
          'p.x+=p.vx;p.y+=p.vy;p.z+=p.vz;p.life-=0.04;' +
          'if(p.life<=0)return;' +
          'var sp=proj(p.x,p.y,p.z);' +
          'var r=244,g=Math.round(63+100*p.life),bl=94;' +
          'ctx.fillStyle="rgba("+r+","+g+","+bl+","+p.life*.7+")";' +
          'ctx.beginPath();ctx.arc(sp.x,sp.y,Math.max(.2,p.sz*p.life),0,6.28);ctx.fill();' +
        '});' +
        'particles=particles.filter(function(p){return p.life>0;});' +
      '}' +

      'function draw(){' +
        'var W=c.offsetWidth,H=c.offsetHeight;' +
        't+=0.4;' +
        'if(t<120){' +
          'velY+=acc;posY+=velY;' +
          'tel.textContent="CORE ASCENT │ BOOSTERS ACTIVE │ ALT: "+Math.round(posY*.3)+"KM │ VEL: "+Math.round(velY*45)+"M/S";' +
        '}else if(t<220){' +
          'velY+=0.02;posY+=velY;boostOff+=0.8;' +
          'tel.textContent="STAGE SEP │ BOOSTERS JETTISONED │ ALT: "+Math.round(posY*.3)+"KM │ VEL: "+Math.round(velY*45)+"M/S";' +
        '}else{' +
          'posY=0;velY=0;t=0;boostOff=0;particles=[];' +
        '}' +
        'ctx.clearRect(0,0,W,H);' +
        'ctx.fillStyle="#05070f";ctx.fillRect(0,0,W,H);' +
        '[.06,.14,.26,.38,.51,.62,.74,.85,.92].forEach(function(s,i){' +
          'ctx.fillStyle="rgba(255,255,255,"+(0.15+i*.07)+")";' +
          'ctx.fillRect(s*W,(i%4*.07+.01)*H,i%3?1:2,i%3?1:2);' +
        '});' +
        'ctx.strokeStyle="rgba(255,255,255,.03)";ctx.lineWidth=1;' +
        'for(var g=-120;g<=120;g+=30){' +
          'var a=proj(g,0,-120),b2=proj(g,0,120);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b2.x,b2.y);ctx.stroke();' +
          'var a2=proj(-120,0,g),b3=proj(120,0,g);ctx.beginPath();ctx.moveTo(a2.x,a2.y);ctx.lineTo(b3.x,b3.y);ctx.stroke();' +
        '}' +
        'if(t>2)spawnFlame();' +
        'drawParticles();' +
        'var segs=6;' +
        'var b1x=-10-boostOff,b1y=posY-(boostOff*.5);' +
        'var b2x=10+boostOff,b2y=posY-(boostOff*.5);' +
        // SRBs drawn first, then core, then fairing — correct front-to-back layering
        'drawSolidRocketCylinder(0,2.8,35,2.5,segs,b1x,b1y,0,"booster");' +
        'drawSolidRocketCylinder(0,2.8,35,2.5,segs,b2x,b2y,0,"booster");' +
        'drawSolidRocketCylinder(0,7,55,7,segs,0,posY,0,"core");' +
        'drawSolidRocketCylinder(55,7,75,0.2,segs,0,posY,0,"payload");' +
        'requestAnimationFrame(draw);' +
      '}' +
      'draw();' +
    '})();<\/script>';
};

// ── geo_iso_heli_hover ── Airbus H160 solid-surface interactive rotary simulation ─────
_RENDERERS['geo_iso_heli_hover'] = function(b) {
  var uid    = 'gihh' + Math.random().toString(36).substr(2, 6);
  var title  = _esc(b.title  || 'LFBO HELIPAD 2 — AIRBUS H160 HOVER PROFILE');
  var livery = ((b.livery    || 'AIB') + '').toUpperCase();

  return '<style>' +
    '#' + uid + 'w{position:relative;width:100%;height:100vh;background:#05070f;overflow:hidden;font-family:"Courier New",monospace;user-select:none;}' +
    '#' + uid + 'c{position:absolute;inset:0;width:100%;height:100%;}' +
    '#' + uid + 'hud{position:absolute;top:18px;left:18px;z-index:10;pointer-events:none;' +
      'background:rgba(2,8,20,.9);border:1px solid rgba(0,242,255,.2);border-radius:6px;padding:12px 18px;}' +
    '#' + uid + 'hud .hl{font-size:7px;letter-spacing:.18em;color:#00f2ff;margin-bottom:4px;}' +
    '#' + uid + 'hud .ht{font-size:13px;font-weight:700;color:#fff;}' +
    '#' + uid + 'hud .hd{font-size:8px;color:#475569;margin-top:6px;min-width:320px;}' +
    '#' + uid + 'sel-wrap{position:absolute;top:18px;right:18px;z-index:20;' +
      'background:rgba(2,8,20,.88);border:1px solid rgba(255,255,255,.1);border-radius:6px;padding:8px 12px;' +
      'display:flex;align-items:center;gap:8px;}' +
    '#' + uid + 'sel-label{font-size:7px;color:rgba(255,255,255,.4);letter-spacing:.1em;}' +
    '#' + uid + 'sel{background:#0d1220;color:#00f2ff;border:1px solid rgba(0,242,255,.25);' +
      'border-radius:4px;font-family:"Courier New",monospace;font-size:9px;padding:4px 8px;' +
      'outline:none;cursor:pointer;font-weight:700;}' +
    '</style>' +
    '<div id="' + uid + 'w">' +
      '<canvas id="' + uid + 'c"></canvas>' +
      '<div id="' + uid + 'hud">' +
        '<div class="hl">ROTARY FLIGHT DECK │ SYSTEMS ACTIVE</div>' +
        '<div class="ht">' + title + '</div>' +
        '<div class="hd" id="' + uid + 'tel">ROTORS COLD &amp; DARK</div>' +
      '</div>' +
      '<div id="' + uid + 'sel-wrap">' +
        '<span id="' + uid + 'sel-label">LIVERY</span>' +
        '<select id="' + uid + 'sel">' +
          '<option value="AIB"' + (livery==='AIB'?' selected':'') + '>AIRBUS FACTORY WHITE</option>' +
          '<option value="VIP"' + (livery==='VIP'?' selected':'') + '>ACH STEALTH CARBON</option>' +
          '<option value="SAR"' + (livery==='SAR'?' selected':'') + '>REGA HELI-RESCUE</option>' +
        '</select>' +
      '</div>' +
    '</div>' +

    '<script>(function(){' +
      'var c=document.getElementById("' + uid + 'c");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'var tel=document.getElementById("' + uid + 'tel");' +
      'var sel=document.getElementById("' + uid + 'sel");' +
      'var W=0,H=0;' +
      'function resize(){c.width=c.offsetWidth||window.innerWidth;c.height=c.offsetHeight||window.innerHeight;W=c.width;H=c.height;}' +
      'window.addEventListener("resize",resize);resize();' +

      'var AL={' +
        'AIB:{name:"Airbus Factory",body:{r:245,g:247,b:250},accent:{r:10,g:34,b:84},skid:{r:140,g:148,b:158}},' +
        'VIP:{name:"ACH Corporate",body:{r:40,g:44,b:52},accent:{r:212,g:175,b:55},skid:{r:30,g:32,b:38}},' +
        'SAR:{name:"Rega Rescue",body:{r:220,g:20,b:40},accent:{r:255,g:255,b:255},skid:{r:240,g:240,b:245}}' +
      '};' +
      'var activeLivery=AL["' + livery + '"]||AL.AIB;' +
      'sel.addEventListener("change",function(e){activeLivery=AL[e.target.value]||AL.AIB;});' +

      'var SC=4.5,COS30=0.866,SIN30=0.5;' +
      'function proj(x,y,z){return{x:W*0.25+(x-z)*COS30*SC,y:H*0.72+(x+z)*SIN30*SC-y*SC};}' +

      // H160 volumetric node tree — calibrated proportions
      'var nodes=[' +
        '{x:34,  y:-2.5, z:0},' +    // 0  nose tip
        '{x:26,  y:3.5,  z:2.2},' +  // 1  cockpit top-stbd
        '{x:26,  y:0.5,  z:3.8},' +  // 2  cockpit mid-stbd
        '{x:26,  y:-3.5, z:2.2},' +  // 3  cockpit bot-stbd
        '{x:26,  y:-3.5, z:-2.2},' + // 4  cockpit bot-port
        '{x:26,  y:0.5,  z:-3.8},' + // 5  cockpit mid-port
        '{x:26,  y:3.5,  z:-2.2},' + // 6  cockpit top-port
        '{x:8,   y:5.5,  z:4.2},' +  // 7  cabin top-stbd
        '{x:8,   y:1.0,  z:5.4},' +  // 8  cabin mid-stbd
        '{x:8,   y:-4.5, z:4.2},' +  // 9  cabin bot-stbd
        '{x:8,   y:-4.5, z:-4.2},' + // 10 cabin bot-port
        '{x:8,   y:1.0,  z:-5.4},' + // 11 cabin mid-port
        '{x:8,   y:5.5,  z:-4.2},' + // 12 cabin top-port
        '{x:-12, y:5.0,  z:3.2},' +  // 13 doghouse top-stbd
        '{x:-12, y:0.5,  z:4.2},' +  // 14 doghouse mid-stbd
        '{x:-12, y:-4.0, z:3.2},' +  // 15 doghouse bot-stbd
        '{x:-12, y:-4.0, z:-3.2},' + // 16 doghouse bot-port
        '{x:-12, y:0.5,  z:-4.2},' + // 17 doghouse mid-port
        '{x:-12, y:5.0,  z:-3.2},' + // 18 doghouse top-port
        '{x:-38, y:1.8,  z:1.0},' +  // 19 boom top-stbd
        '{x:-38, y:-1.2, z:1.0},' +  // 20 boom bot-stbd
        '{x:-38, y:-1.2, z:-1.0},' + // 21 boom bot-port
        '{x:-38, y:1.8,  z:-1.0},' + // 22 boom top-port
        '{x:-56, y:13.5, z:0},' +    // 23 fin apex
        '{x:-60, y:0,    z:0},' +    // 24 fin heel
        '{x:0,   y:7.8,  z:0},' +    // 25 main rotor hub
        '{x:-53, y:5.0,  z:0},' +    // 26 fenestron hub
        '{x:18,  y:-8,   z:-5.5},' + // 27 L skid fwd
        '{x:-8,  y:-8,   z:-5.5},' + // 28 L skid aft
        '{x:18,  y:-8,   z:5.5},' +  // 29 R skid fwd
        '{x:-8,  y:-8,   z:5.5}' +   // 30 R skid aft
      '];' +

      // Face catalog — tris: [0,1,2] fan gives outward normals; quads reversed for outward
      // Duplicate roof face removed; belly forced to fixed grey in material pass
      'var faces=[' +
        // Nose taper fan — original CCW order gives outward normals
        '{n:[0,1,2],t:"nose"},{n:[0,2,3],t:"nose"},{n:[0,3,4],t:"belly"},{n:[0,4,5],t:"belly"},{n:[0,5,6],t:"nose"},{n:[0,6,1],t:"nose"},' +
        // Cockpit → cabin: quads reversed for outward normals; belly quads also reversed
        '{n:[1,7,8,2],t:"canopy"},{n:[2,8,9,3],t:"canopy"},{n:[3,9,10,4],t:"belly"},{n:[4,10,11,5],t:"belly"},{n:[5,11,12,6],t:"canopy"},{n:[6,12,7,1],t:"canopy"},' +
        // Cabin → doghouse: reversed quads; roof panel [12,7,13,18] NOT duplicated by doghouse cap
        '{n:[7,13,14,8],t:"body"},{n:[8,14,15,9],t:"body"},{n:[9,15,16,10],t:"belly"},{n:[10,16,17,11],t:"belly"},{n:[11,17,18,12],t:"body"},{n:[12,7,13,18],t:"body"},' +
        // Doghouse cap — single upward-facing surface, type engine = accent colour
        '{n:[7,13,18,12],t:"engine"},' +
        // Tail boom taper — reversed quads, original tri winding (already outward)
        '{n:[13,19,20,14],t:"body"},{n:[14,15,20],t:"body"},{n:[15,16,21,20],t:"belly"},{n:[16,17,21],t:"body"},{n:[17,18,22,21],t:"body"},{n:[18,13,19,22],t:"body"},' +
        // Fenestron fin
        '{n:[19,23,24,20],t:"fin"}' +
      '];' +

      'var posX=0,posY=0,posZ=0,pitch=0;' +
      'var rRPM=0,rAng=0,timeline=0;' +

      'function frame(){' +
        'timeline+=0.5;' +
        'if(timeline<60){' +
          'rRPM=Math.min(0.28,rRPM+0.003);rAng+=rRPM;' +
          'tel.textContent="ENG 1/2 START RUNUP │ ROTOR RPM: "+Math.round(rRPM*780)+" │ ALT: GND";' +
        '}else if(timeline<120){' +
          'rAng+=rRPM;posY+=0.18;' +
          'tel.textContent="VERTICAL LIFTOFF │ HOVER PROFILE │ ALT: "+Math.round(posY*1.8)+"FT │ IN GROUND EFFECT";' +
        '}else if(timeline<190){' +
          'rAng+=rRPM;posY+=0.04;pitch=Math.min(0.09,pitch+0.002);posX+=0.9;' +
          'tel.textContent="TORQUE TRANSITION │ NOSE DOWN MOMENT │ PITCH: "+Math.round(pitch*180/Math.PI)+"° │ VEL: 45KTS";' +
        '}else if(timeline<280){' +
          'rAng+=rRPM;posY+=0.22;posX+=2.2;pitch=Math.max(0.02,pitch-0.001);' +
          'tel.textContent="CLIMB OUT SPEED DEPARTURE │ AIRSPEED: 120KTS │ ALT: "+Math.round(posY*1.8)+"FT";' +
        '}else{' +
          'posX=0;posY=0;pitch=0;rAng=0;rRPM=0;timeline=0;' +
        '}' +

        'ctx.clearRect(0,0,W,H);' +
        'ctx.fillStyle="#05070f";ctx.fillRect(0,0,W,H);' +

        // Stars
        '[.08,.18,.30,.42,.54,.65,.77,.88,.95].forEach(function(s,i){' +
          'ctx.fillStyle="rgba(255,255,255,"+(0.12+i*.07)+")";' +
          'ctx.fillRect(s*W,(i%4*.08+.02)*H,i%3?1:2,i%3?1:2);' +
        '});' +

        // Ground pad circle
        'var shAnchor=proj(posZ,0,posX);' +
        'ctx.strokeStyle="rgba(0,242,255,.06)";ctx.lineWidth=1.5;' +
        'ctx.beginPath();ctx.arc(shAnchor.x,shAnchor.y,22,0,6.28);ctx.stroke();' +

        'var sun={x:-0.1,y:0.8,z:0.6};' +
        'var sm=Math.sqrt(sun.x*sun.x+sun.y*sun.y+sun.z*sun.z);sun.x/=sm;sun.y/=sm;sun.z/=sm;' +

        // Pitch-transform all nodes into world + screen coords
        'var co=Math.cos(pitch),si=Math.sin(pitch);' +
        'var pts=nodes.map(function(v){' +
          'var rx=v.x*co-v.y*si,ry=v.x*si+v.y*co;' +
          'var sp=proj(v.z+posZ,ry+posY,posX-rx);' +
          'sp.wx=v.z;sp.wy=ry+posY;sp.wz=posX-rx;' +
          'return sp;' +
        '});' +

        // Painter's sort — wz descends = tail first, nose last
        'var sorted=faces.map(function(f){' +
          'var sd=0;f.n.forEach(function(i){sd+=pts[i].wz;});' +
          'return{n:f.n,t:f.t,avgZ:sd/f.n.length};' +
        '}).sort(function(a,b){return b.avgZ-a.avgZ;});' +

        // Rasterize hull panels
        'sorted.forEach(function(f){' +
          'var p0=pts[f.n[0]],p1=pts[f.n[1]],p2=pts[f.n[2]];' +
          'var ux=p1.wx-p0.wx,uy=p1.wy-p0.wy,uz=p1.wz-p0.wz;' +
          'var vx=p2.wx-p0.wx,vy=p2.wy-p0.wy,vz=p2.wz-p0.wz;' +
          'var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;' +
          'var nm=Math.sqrt(nx*nx+ny*ny+nz*nz);if(nm>0){nx/=nm;ny/=nm;nz/=nm;}' +
          'var dot=nx*sun.x+ny*sun.y+nz*sun.z;' +
          'var intensity=Math.min(1,Math.max(0.46,dot));' +
          'var mc;' +
          'if(f.t==="fin"||f.t==="engine"){mc=activeLivery.accent;}' +
          'else if(f.t==="canopy"){mc={r:30,g:45,b:70};}' +   // glassy tint
          'else if(f.t==="belly"){mc={r:145,g:152,b:162};}' + // structural underside
          'else{mc=activeLivery.body;}' +
          'ctx.fillStyle="rgb("+Math.round(mc.r*intensity)+","+Math.round(mc.g*intensity)+","+Math.round(mc.b*intensity)+")";' +
          'ctx.strokeStyle="rgba("+Math.round(mc.r*1.02)+","+Math.round(mc.g*1.02)+","+Math.round(mc.b*1.02)+",.16)";' +
          'ctx.lineWidth=0.7;' +
          'ctx.beginPath();' +
          'f.n.forEach(function(ni,i){i===0?ctx.moveTo(pts[ni].x,pts[ni].y):ctx.lineTo(pts[ni].x,pts[ni].y);});' +
          'ctx.closePath();ctx.fill();ctx.stroke();' +
        '});' +

        // Landing skids
        'ctx.strokeStyle="rgb("+activeLivery.skid.r+","+activeLivery.skid.g+","+activeLivery.skid.b+")";ctx.lineWidth=1.5;' +
        'ctx.beginPath();ctx.moveTo(pts[27].x,pts[27].y);ctx.lineTo(pts[28].x,pts[28].y);ctx.stroke();' +
        'ctx.beginPath();ctx.moveTo(pts[29].x,pts[29].y);ctx.lineTo(pts[30].x,pts[30].y);ctx.stroke();' +

        // Concentric ring blur — no solid fill; outer vortex ring + inner chord ring + 8-pass quadratic blade fan
        'var hub=pts[25],bLen=46,dSegs=16,dPts=[],innerPts=[];' +
        'for(var d=0;d<dSegs;d++){' +
          'var dAng=d/dSegs*Math.PI*2;' +
          'var deX=nodes[25].z+Math.sin(dAng)*bLen,deZ=nodes[25].x+Math.cos(dAng)*bLen;' +
          'var drx=deZ*co-nodes[25].y*si,dry=deZ*si+nodes[25].y*co;' +
          'dPts.push(proj(deX+posZ,dry+posY,posX-drx));' +
          'var ieX=nodes[25].z+Math.sin(dAng)*bLen*0.75,ieZ=nodes[25].x+Math.cos(dAng)*bLen*0.75;' +
          'var irx=ieZ*co-nodes[25].y*si,iry=ieZ*si+nodes[25].y*co;' +
          'innerPts.push(proj(ieX+posZ,iry+posY,posX-irx));' +
        '}' +
        // Outer tip-vortex ring
        'ctx.strokeStyle="rgba(0,242,255,.08)";ctx.lineWidth=0.6;' +
        'ctx.beginPath();ctx.moveTo(dPts[0].x,dPts[0].y);' +
        'for(var d=1;d<dSegs;d++){ctx.lineTo(dPts[d].x,dPts[d].y);}' +
        'ctx.closePath();ctx.stroke();' +
        // Inner chord ring
        'ctx.strokeStyle="rgba(140,148,158,.04)";' +
        'ctx.beginPath();ctx.moveTo(innerPts[0].x,innerPts[0].y);' +
        'for(var d=1;d<dSegs;d++){ctx.lineTo(innerPts[d].x,innerPts[d].y);}' +
        'ctx.closePath();ctx.stroke();' +
        // 5 blades × 8 quadratic-decay ghost arcs
        'for(var bi=0;bi<5;bi++){' +
          'var blAng=rAng+(bi*Math.PI*2/5);' +
          'for(var tr=0;tr<8;tr++){' +
            'var cAng=blAng-(tr*0.035);' +
            'var tX=nodes[25].z+Math.sin(cAng)*bLen,tZ=nodes[25].x+Math.cos(cAng)*bLen;' +
            'var trx=tZ*co-nodes[25].y*si,trY=tZ*si+nodes[25].y*co;' +
            'var tip=proj(tX+posZ,trY+posY,posX-trx);' +
            'var al=Math.pow(1-tr/8,2)*0.38;' +
            'ctx.strokeStyle="rgba(45,50,58,"+al+")";ctx.lineWidth=1.5-tr*0.16;' +
            'ctx.beginPath();ctx.moveTo(hub.x,hub.y);ctx.lineTo(tip.x,tip.y);ctx.stroke();' +
            'if(tr===0){ctx.fillStyle="rgba(0,242,255,.75)";ctx.beginPath();ctx.arc(tip.x,tip.y,1.0,0,6.28);ctx.fill();}' +
          '}' +
        '}' +
        // Rotor mast cap
        'ctx.fillStyle="rgba(10,34,84,.95)";ctx.strokeStyle="rgba(255,255,255,.25)";ctx.lineWidth=0.8;' +
        'ctx.beginPath();ctx.arc(hub.x,hub.y,3.5,0,6.28);ctx.fill();ctx.stroke();' +

        // Fenestron blur disc
        'var fHub=pts[26],fR=5.5*SC*0.4;' +
        'ctx.strokeStyle="rgba(0,242,255,"+(0.06+Math.random()*.06)+")";' +
        'ctx.fillStyle="rgba(45,50,60,.15)";' +
        'ctx.beginPath();ctx.arc(fHub.x,fHub.y,fR,0,6.28);ctx.fill();ctx.stroke();' +
        'ctx.lineWidth=1;ctx.strokeStyle="rgba(255,255,255,.12)";' +
        'for(var k=0;k<3;k++){' +
          'var fAng=rAng*3.5+(k*Math.PI/3);' +
          'ctx.beginPath();ctx.moveTo(fHub.x-Math.sin(fAng)*fR,fHub.y-Math.cos(fAng)*fR);' +
          'ctx.lineTo(fHub.x+Math.sin(fAng)*fR,fHub.y+Math.cos(fAng)*fR);ctx.stroke();' +
        '}' +

        'requestAnimationFrame(frame);' +
      '}' +
      'frame();' +
    '})();<\/script>';
};

// ── geo_iso_fleet: Combined Fleet Deck — A321neo + Ariane 6 + H160 ──────────
_RENDERERS['geo_iso_fleet'] = function(b){
  var uid  = 'gifl'+Math.random().toString(36).substr(2,6);
  var iAC  = ((b.airline||'AIB')+'').toUpperCase();
  var iRK  = ((b.rocket ||'ESA')+'').toUpperCase();
  var iHH  = ((b.livery ||'AIB')+'').toUpperCase();
  var iTab = ((b.tab    ||'ac') +'').toLowerCase();
  if(iTab!=='ac'&&iTab!=='rk'&&iTab!=='hh') iTab='ac';
  var SVRTITLES = {ac:'A321neo DEPARTURE',rk:'ARIANE 6 HEAVY LIFT',hh:'H160 HOVER PROFILE'};
  var initTitle = SVRTITLES[iTab]||SVRTITLES.ac;

  return '<style>'+
    '#'+uid+'w{position:relative;width:100%;height:100vh;background:#05070f;overflow:hidden;font-family:"Courier New",monospace}'+
    '#'+uid+'c{position:absolute;inset:0;width:100%;height:100%}'+
    '#'+uid+'tabs{position:absolute;top:18px;left:50%;transform:translateX(-50%);z-index:20;display:flex;gap:4px}'+
    '#'+uid+'tabs button{background:rgba(2,8,20,.9);border:1px solid rgba(255,255,255,.1);border-radius:4px;color:rgba(255,255,255,.32);font-family:"Courier New",monospace;font-size:7px;letter-spacing:.14em;padding:6px 18px;cursor:pointer;font-weight:700;text-transform:uppercase;transition:all .2s}'+
    '#'+uid+'tabs button.on{border-color:rgba(0,242,255,.4);color:#00f2ff;background:rgba(0,20,40,.9)}'+
    '#'+uid+'hud{position:absolute;top:18px;left:18px;z-index:10;pointer-events:none;background:rgba(2,8,20,.88);border:1px solid rgba(0,242,255,.2);border-radius:6px;padding:12px 18px}'+
    '.'+uid+'hl{font-size:7px;letter-spacing:.16em;color:#00f2ff;margin-bottom:4px}'+
    '.'+uid+'ht{font-size:13px;font-weight:700;color:#fff}'+
    '.'+uid+'hd{font-size:8px;color:#475569;margin-top:6px;min-width:260px}'+
    '#'+uid+'sp{position:absolute;top:18px;right:18px;z-index:20;background:rgba(2,8,20,.88);border:1px solid rgba(255,255,255,.1);border-radius:6px;padding:10px 14px;display:flex;flex-direction:column;gap:9px}'+
    '.'+uid+'row{display:flex;align-items:center;gap:8px}'+
    '.'+uid+'lbl{font-size:6px;color:rgba(255,255,255,.28);letter-spacing:.1em;min-width:54px;text-transform:uppercase}'+
    '.'+uid+'dd{background:#0d1220;color:#00f2ff;border:1px solid rgba(0,242,255,.22);border-radius:3px;font-family:"Courier New",monospace;font-size:7px;padding:3px 7px;outline:none;cursor:pointer;font-weight:700}'+
    '</style>'+
    '<div id="'+uid+'w">'+
      '<canvas id="'+uid+'c"></canvas>'+
      '<div id="'+uid+'hud">'+
        '<div class="'+uid+'hl">AIRBUS FLEET DECK</div>'+
        '<div class="'+uid+'ht" id="'+uid+'ht">'+initTitle+'</div>'+
        '<div class="'+uid+'hd" id="'+uid+'tel">—</div>'+
      '</div>'+
      '<div id="'+uid+'tabs">'+
        '<button'+(iTab==='ac'?' class="on"':'')+' data-t="ac">A321neo</button>'+
        '<button'+(iTab==='rk'?' class="on"':'')+' data-t="rk">ARIANE 6</button>'+
        '<button'+(iTab==='hh'?' class="on"':'')+' data-t="hh">H160</button>'+
        '<button id="'+uid+'pb" style="margin-left:6px;border-color:rgba(255,255,255,.15)">⊞ ALL</button>'+
      '</div>'+
      '<div id="'+uid+'sp">'+
        '<div class="'+uid+'row"><span class="'+uid+'lbl">A321neo</span>'+
          '<select class="'+uid+'dd" id="'+uid+'da">'+
            '<option value="AIB">AIRBUS HOUSE</option>'+
            '<option value="EZY">EASYJET</option>'+
            '<option value="AFR">AIR FRANCE</option>'+
            '<option value="BAW">BRIT AIRWAYS</option>'+
            '<option value="DLH">LUFTHANSA</option>'+
            '<option value="RYR">RYANAIR</option>'+
          '</select></div>'+
        '<div class="'+uid+'row"><span class="'+uid+'lbl">Ariane 6</span>'+
          '<select class="'+uid+'dd" id="'+uid+'dr">'+
            '<option value="ESA">ESA STANDARD</option>'+
            '<option value="ARIA">LAUNCH CONFIG</option>'+
            '<option value="DARK">STEALTH OPS</option>'+
          '</select></div>'+
        '<div class="'+uid+'row"><span class="'+uid+'lbl">H160</span>'+
          '<select class="'+uid+'dd" id="'+uid+'dh">'+
            '<option value="AIB">AIRBUS FACTORY</option>'+
            '<option value="VIP">ACH CORPORATE</option>'+
            '<option value="SAR">REGA RESCUE</option>'+
          '</select></div>'+
      '</div>'+
    '</div>'+
    '<script>(function(){'+
      'var c=document.getElementById("'+uid+'c");if(!c)return;'+
      'var ctx=c.getContext("2d"),W=0,H=0;'+
      'function resize(){c.width=c.offsetWidth||window.innerWidth;c.height=c.offsetHeight||window.innerHeight;W=c.width;H=c.height;}'+
      'window.addEventListener("resize",resize);resize();'+
      'var tel=document.getElementById("'+uid+'tel"),ht=document.getElementById("'+uid+'ht");'+
      'var SC=3.5,OY=0,C30=0.866,S30=0.5;'+
      'function proj(x,y,z){return{x:W*0.5+(x-z)*C30*SC,y:OY+(x+z)*S30*SC-y*SC};}'+
      'var SX=-0.0995,SY=0.796,SZ=0.597;'+
      'function paintFaces(sf,pts,getC,amb){'+
        'sf.forEach(function(f){'+
          'var p0=pts[f.n[0]],p1=pts[f.n[1]],p2=pts[f.n[2]];'+
          'var ux=p1.wx-p0.wx,uy=p1.wy-p0.wy,uz=p1.wz-p0.wz;'+
          'var vx=p2.wx-p0.wx,vy=p2.wy-p0.wy,vz=p2.wz-p0.wz;'+
          'var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;'+
          'var nm=Math.sqrt(nx*nx+ny*ny+nz*nz);if(nm>0){nx/=nm;ny/=nm;nz/=nm;}'+
          'var lit=Math.min(1,Math.max(amb,nx*SX+ny*SY+nz*SZ));'+
          'var mc=getC(f.t);'+
          'ctx.fillStyle="rgb("+Math.round(mc.r*lit)+","+Math.round(mc.g*lit)+","+Math.round(mc.b*lit)+")";'+
          'ctx.strokeStyle="rgba("+Math.round(mc.r*1.02)+","+Math.round(mc.g*1.02)+","+Math.round(mc.b*1.02)+",.18)";'+
          'ctx.lineWidth=0.7;ctx.beginPath();'+
          'f.n.forEach(function(ni,i){i===0?ctx.moveTo(pts[ni].x,pts[ni].y):ctx.lineTo(pts[ni].x,pts[ni].y);});'+
          'ctx.closePath();ctx.fill();ctx.stroke();'+
        '});'+
      '}'+
      'var LA={'+
        'AIB:{body:{r:245,g:247,b:250},tail:{r:10,g:34,b:84},sk:{r:0,g:154,b:206}},'+
        'EZY:{body:{r:255,g:102,b:0},tail:{r:255,g:102,b:0},sk:{r:255,g:102,b:0}},'+
        'AFR:{body:{r:245,g:247,b:250},tail:{r:0,g:35,b:149},sk:{r:0,g:35,b:149}},'+
        'BAW:{body:{r:245,g:247,b:250},tail:{r:7,g:90,b:170},sk:{r:7,g:90,b:170}},'+
        'DLH:{body:{r:245,g:247,b:250},tail:{r:26,g:60,b:143},sk:{r:240,g:200,b:0}},'+
        'RYR:{body:{r:7,g:53,b:144},tail:{r:7,g:53,b:144},sk:{r:7,g:53,b:144}}'+
      '};'+
      'var LR={'+
        'ESA:{core:{r:245,g:247,b:250},booster:{r:56,g:189,b:248},payload:{r:90,g:98,b:105}},'+
        'ARIA:{core:{r:200,g:210,b:222},booster:{r:255,g:118,b:28},payload:{r:70,g:80,b:90}},'+
        'DARK:{core:{r:44,g:50,b:60},booster:{r:180,g:28,b:48},payload:{r:36,g:42,b:50}}'+
      '};'+
      'var LH={'+
        'AIB:{body:{r:245,g:247,b:250},accent:{r:10,g:34,b:84},skid:{r:140,g:148,b:158}},'+
        'VIP:{body:{r:40,g:44,b:52},accent:{r:212,g:175,b:55},skid:{r:30,g:32,b:38}},'+
        'SAR:{body:{r:220,g:20,b:40},accent:{r:255,g:255,b:255},skid:{r:240,g:240,b:245}}'+
      '};'+
      'var lavAC=LA["'+iAC+'"]||LA.AIB;'+
      'var lavRK=LR["'+iRK+'"]||LR.ESA;'+
      'var lavHH=LH["'+iHH+'"]||LH.AIB;'+
      'document.getElementById("'+uid+'da").value="'+iAC+'";'+
      'document.getElementById("'+uid+'dr").value="'+iRK+'";'+
      'document.getElementById("'+uid+'dh").value="'+iHH+'";'+
      'document.getElementById("'+uid+'da").addEventListener("change",function(e){lavAC=LA[e.target.value]||LA.AIB;});'+
      'document.getElementById("'+uid+'dr").addEventListener("change",function(e){lavRK=LR[e.target.value]||LR.ESA;});'+
      'document.getElementById("'+uid+'dh").addEventListener("change",function(e){lavHH=LH[e.target.value]||LH.AIB;});'+
      'var aN=['+
        '{x:54,y:-1.5,z:0},'+
        '{x:44,y:2,z:2.5},{x:44,y:.5,z:3.5},{x:44,y:-2,z:2.5},{x:44,y:-2,z:-2.5},{x:44,y:.5,z:-3.5},{x:44,y:2,z:-2.5},'+
        '{x:34,y:5,z:4.5},{x:34,y:1.5,z:6},{x:34,y:-4,z:4.5},{x:34,y:-4,z:-4.5},{x:34,y:1.5,z:-6},{x:34,y:5,z:-4.5},'+
        '{x:-20,y:5.5,z:4.5},{x:-20,y:1.5,z:6},{x:-20,y:-4,z:4.5},{x:-20,y:-4,z:-4.5},{x:-20,y:1.5,z:-6},{x:-20,y:5.5,z:-4.5},'+
        '{x:-65,y:3.5,z:2},{x:-65,y:1,z:3.5},{x:-65,y:-2,z:2},{x:-65,y:-2,z:-2},{x:-65,y:1,z:-3.5},{x:-65,y:3.5,z:-2},'+
        '{x:-78,y:.5,z:0},'+
        '{x:-74,y:24,z:0},{x:-74,y:1.5,z:18},{x:-74,y:1.5,z:-18},'+
        '{x:12,y:-2.5,z:-6},{x:-12,y:-2.5,z:-6},{x:-24,y:-.5,z:-52},{x:-18,y:-.5,z:-52},{x:-18,y:7,z:-52},'+
        '{x:12,y:-2.5,z:6},{x:-12,y:-2.5,z:6},{x:-24,y:-.5,z:52},{x:-18,y:-.5,z:52},{x:-18,y:7,z:52},'+
        '{x:16,y:-6.5,z:-16},{x:2,y:-5.5,z:-16},{x:16,y:-6.5,z:16},{x:2,y:-5.5,z:16},'+
        '{x:16,y:-9.5,z:-16},{x:2,y:-8.5,z:-16},{x:16,y:-9.5,z:16},{x:2,y:-8.5,z:16},'+
        '{x:6,y:-2.1,z:-16},{x:6,y:-2.1,z:16}'+
      '];'+
      'var aF=['+
        '{n:[19,20,25],t:"f"},{n:[24,19,25],t:"f"},{n:[20,21,25],t:"f"},{n:[23,24,25],t:"f"},'+
        '{n:[19,24,26],t:"fin"},'+
        '{n:[20,25,27],t:"s"},{n:[23,25,28],t:"s"},'+
        '{n:[13,14,20,19],t:"f"},{n:[14,15,21,20],t:"f"},{n:[15,16,22,21],t:"f"},{n:[16,17,23,22],t:"f"},{n:[17,18,24,23],t:"f"},{n:[18,13,19,24],t:"f"},'+
        '{n:[7,8,14,13],t:"f"},{n:[8,9,15,14],t:"f"},{n:[9,10,16,15],t:"f"},{n:[10,11,17,16],t:"f"},{n:[11,12,18,17],t:"f"},{n:[12,7,13,18],t:"f"},'+
        '{n:[1,2,8,7],t:"f"},{n:[2,3,9,8],t:"f"},{n:[3,4,10,9],t:"f"},{n:[4,5,11,10],t:"f"},{n:[5,6,12,11],t:"f"},{n:[6,1,7,12],t:"f"},'+
        '{n:[0,1,2],t:"n"},{n:[0,2,3],t:"n"},{n:[0,3,4],t:"n"},{n:[0,4,5],t:"n"},{n:[0,5,6],t:"n"},{n:[0,6,1],t:"n"},'+
        '{n:[29,32,31,30],t:"w"},{n:[32,33,31],t:"sk"},{n:[34,37,36,35],t:"w"},{n:[37,38,36],t:"sk"},'+
        '{n:[47,39,40],t:"e"},{n:[47,44,43],t:"e"},{n:[39,43,44,40],t:"e"},'+
        '{n:[48,41,42],t:"e"},{n:[48,46,45],t:"e"},{n:[41,45,46,42],t:"e"}'+
      '];'+
      'var acT=0,acPZ=80,acPY=0,acA=0,acSpd=0;'+
      'function drawAC(){'+
        'SC=3.5;OY=H*.8;'+
        'acT++;'+
        'if(acT<90){acSpd=Math.min(38,acSpd+.55);acPZ-=acSpd*.075;tel.textContent="GND ROLL │ "+Math.round(acSpd*3.7)+"KTS │ FLAP 1";}'+
        'else if(acT<130){acSpd=Math.min(42,acSpd+.2);acPZ-=acSpd*.075;acA=Math.min(.24,(acT-90)*.009);acPY+=Math.sin(acA)*acSpd*.05;tel.textContent="ROTATION │ PITCH "+Math.round(acA*57.3)+"\xb0 │ "+Math.round(acSpd*3.7)+"KTS";}'+
        'else if(acT<230){acSpd=Math.min(46,acSpd+.06);acPZ-=acSpd*.075;acPY+=Math.sin(acA)*acSpd*.09;tel.textContent="CLIMB │ ALT: "+Math.round(acPY*9)+"FT │ GEAR UP │ "+Math.round(acSpd*3.7)+"KTS";}'+
        'else{acT=0;acPZ=80;acPY=0;acA=0;acSpd=0;}'+
        'ctx.strokeStyle="rgba(0,40,80,.35)";ctx.lineWidth=.5;ctx.setLineDash([]);'+
        'for(var g=-80;g<=160;g+=25){var rr1=proj(-30,0,g),rr2=proj(30,0,g);ctx.beginPath();ctx.moveTo(rr1.x,rr1.y);ctx.lineTo(rr2.x,rr2.y);ctx.stroke();}'+
        'for(var g=-30;g<=30;g+=15){var rr1=proj(g,0,-80),rr2=proj(g,0,160);ctx.beginPath();ctx.moveTo(rr1.x,rr1.y);ctx.lineTo(rr2.x,rr2.y);ctx.stroke();}'+
        'ctx.strokeStyle="rgba(80,90,120,.9)";ctx.lineWidth=2;'+
        'var re1=proj(-12,0,-80),re2=proj(-12,0,160);ctx.beginPath();ctx.moveTo(re1.x,re1.y);ctx.lineTo(re2.x,re2.y);ctx.stroke();'+
        'var re3=proj(12,0,-80),re4=proj(12,0,160);ctx.beginPath();ctx.moveTo(re3.x,re3.y);ctx.lineTo(re4.x,re4.y);ctx.stroke();'+
        'ctx.strokeStyle="rgba(255,245,80,.45)";ctx.lineWidth=1;ctx.setLineDash([10,14]);'+
        'for(var d=-80;d<160;d+=24){var da=proj(0,0,d),db=proj(0,0,d+12);ctx.beginPath();ctx.moveTo(da.x,da.y);ctx.lineTo(db.x,db.y);ctx.stroke();}'+
        'ctx.setLineDash([]);'+
        'ctx.fillStyle="#fff8c0";for(var lz=acPZ-10;lz>-80;lz-=18){var lp1=proj(-12,.3,lz),lp2=proj(12,.3,lz);ctx.beginPath();ctx.arc(lp1.x,lp1.y,2,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(lp2.x,lp2.y,2,0,6.28);ctx.fill();}'+
        'ctx.fillStyle="#ffa500";for(var lz=acPZ+2;lz<160&&lz<acPZ+60;lz+=18){var lp1=proj(-10,.3,lz),lp2=proj(10,.3,lz);ctx.beginPath();ctx.arc(lp1.x,lp1.y,1.5,0,6.28);ctx.fill();ctx.beginPath();ctx.arc(lp2.x,lp2.y,1.5,0,6.28);ctx.fill();}'+
        'var sN=proj(0,0,acPZ-54),sT=proj(0,0,acPZ+78);ctx.strokeStyle="rgba(0,0,0,.4)";ctx.lineWidth=4;'+
        'ctx.beginPath();ctx.moveTo(sN.x,sN.y);ctx.lineTo(sT.x,sT.y);ctx.stroke();'+
        'var co=Math.cos(acA),si=Math.sin(acA);'+
        'var fl=acPY>0?Math.min(4.5,acPY*.07):0;'+
        'var pts=aN.map(function(v,idx){'+
          'var wy=v.y;'+
          'if(Math.abs(v.z)>5.5&&idx>=29){wy+=Math.pow(Math.abs(v.z)/52,2)*fl;}'+
          'var rx=v.x*co-wy*si,ry=v.x*si+wy*co;'+
          'var sp=proj(v.z,ry+acPY,acPZ-rx);sp.wx=v.z;sp.wy=ry+acPY;sp.wz=acPZ-rx;return sp;'+
        '});'+
        'var sf=aF.map(function(f){var d=0;f.n.forEach(function(i){d+=pts[i].wz;});return{n:f.n,t:f.t,d:d/f.n.length};}).sort(function(a,b){return b.d-a.d;});'+
        'paintFaces(sf,pts,function(t){return t==="fin"?lavAC.tail:t==="sk"?lavAC.sk:t==="w"||t==="s"?{r:168,g:174,b:182}:t==="e"?{r:245,g:247,b:250}:lavAC.body;},0.46);'+
      '}'+
      'function mkRing(h,r,n){var p=[];for(var i=0;i<n;i++){var a=i/n*6.2832;p.push({x:Math.cos(a)*r,y:h,z:Math.sin(a)*r});}return p;}'+
      'var rkT=0,rkPY=0,rkVY=0,rkBO=0,rkP=[];'+
      'function drawSC(h1,r1,h2,r2,n,dx,dy,dz,mc){'+
        'var g1=mkRing(h1,r1,n),g2=mkRing(h2,r2,n);'+
        'function pj(v){var px=v.x+dx,py2=v.y+dy,pz=v.z+dz;var sp=proj(px,py2,pz);sp.wx=px;sp.wy=py2;sp.wz=pz;return sp;}'+
        'var fl=[];'+
        'for(var i=0;i<n;i++){var j=(i+1)%n;var q0=pj(g1[i]),q1=pj(g2[i]),q2=pj(g2[j]),q3=pj(g1[j]);'+
          'fl.push({pts:[q0,q1,q2,q3],d:(q0.wx+q0.wz+q1.wx+q1.wz+q2.wx+q2.wz+q3.wx+q3.wz)/4});'+
        '}'+
        'fl.sort(function(a,b){return a.d-b.d;});'+
        'fl.forEach(function(f){'+
          'var p0=f.pts[0],p1=f.pts[1],p2=f.pts[2];'+
          'var ux=p1.wx-p0.wx,uy=p1.wy-p0.wy,uz=p1.wz-p0.wz;'+
          'var vx=p2.wx-p0.wx,vy=p2.wy-p0.wy,vz=p2.wz-p0.wz;'+
          'var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;'+
          'var nm=Math.sqrt(nx*nx+ny*ny+nz*nz);if(nm>0){nx/=nm;ny/=nm;nz/=nm;}'+
          'var lit=Math.min(1,Math.max(.42,nx*SX+ny*SY+nz*SZ));'+
          'ctx.fillStyle="rgb("+Math.round(mc.r*lit)+","+Math.round(mc.g*lit)+","+Math.round(mc.b*lit)+")";'+
          'ctx.strokeStyle="rgba("+Math.round(mc.r*1.02)+","+Math.round(mc.g*1.02)+","+Math.round(mc.b*1.02)+",.15)";'+
          'ctx.lineWidth=.7;ctx.beginPath();'+
          'f.pts.forEach(function(p,k){k===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});'+
          'ctx.closePath();ctx.fill();ctx.stroke();'+
        '});'+
      '}'+
      'function drawRK(){'+
        'SC=3.2;OY=H*.82;'+
        'rkT+=.4;'+
        'var b1x=-10,b1y=0,b2x=10,b2y=0;'+
        'if(rkT<120){'+
          'rkVY+=.04;rkPY+=rkVY;b1y=rkPY;b2y=rkPY;'+
          'tel.textContent="CORE ASCENT │ BOOSTERS ACTIVE │ ALT: "+Math.round(rkPY*.3)+"KM";'+
          'rkP.push({x:(Math.random()-.5)*4,y:rkPY-5,z:(Math.random()-.5)*4,vx:(Math.random()-.5)*.3,vy:-1.5-Math.random(),vz:(Math.random()-.5)*.3,life:1,sz:2+Math.random()*3});'+
          '[b1x,b2x].forEach(function(bx){rkP.push({x:bx+(Math.random()-.5)*2,y:rkPY-5,z:(Math.random()-.5)*2,vx:(Math.random()-.5)*.4,vy:-1.2-Math.random()*.8,vz:(Math.random()-.5)*.4,life:1,sz:1+Math.random()*2});});'+
        '}else if(rkT<220){'+
          'rkVY+=.02;rkPY+=rkVY;rkBO+=.8;b1x=-10-rkBO;b1y=rkPY-rkBO*.5;b2x=10+rkBO;b2y=rkPY-rkBO*.5;'+
          'tel.textContent="STAGE SEP │ SRBs JETTISONED │ ALT: "+Math.round(rkPY*.3)+"KM";'+
          'rkP.push({x:(Math.random()-.5)*4,y:rkPY-5,z:(Math.random()-.5)*4,vx:(Math.random()-.5)*.3,vy:-1.5-Math.random(),vz:(Math.random()-.5)*.3,life:1,sz:2+Math.random()*3});'+
        '}else{rkT=0;rkPY=0;rkVY=0;rkBO=0;rkP=[];}'+
        'rkP.forEach(function(p){p.x+=p.vx;p.y+=p.vy;p.z+=p.vz;p.life-=.04;if(p.life<=0)return;var sp=proj(p.x,p.y,p.z);ctx.fillStyle="rgba(244,"+Math.round(63+100*p.life)+",94,"+p.life*.7+")";ctx.beginPath();ctx.arc(sp.x,sp.y,Math.max(.2,p.sz*p.life),0,6.28);ctx.fill();});'+
        'rkP=rkP.filter(function(p){return p.life>0;});'+
        'ctx.strokeStyle="rgba(255,255,255,.02)";ctx.lineWidth=1;'+
        'for(var g=-100;g<=100;g+=30){var ga=proj(g,0,-80),gb=proj(g,0,80);ctx.beginPath();ctx.moveTo(ga.x,ga.y);ctx.lineTo(gb.x,gb.y);ctx.stroke();var gc=proj(-80,0,g),gd=proj(80,0,g);ctx.beginPath();ctx.moveTo(gc.x,gc.y);ctx.lineTo(gd.x,gd.y);ctx.stroke();}'+
        'var segs=6;'+
        'drawSC(0,2.8,35,2.5,segs,b1x,b1y,0,lavRK.booster);'+
        'drawSC(0,2.8,35,2.5,segs,b2x,b2y,0,lavRK.booster);'+
        'drawSC(0,7,55,7,segs,0,rkPY,0,lavRK.core);'+
        'drawSC(55,7,75,.2,segs,0,rkPY,0,lavRK.payload);'+
      '}'+
      'var hN=['+
        '{x:34,y:-2.5,z:0},'+
        '{x:26,y:3.5,z:2.2},{x:26,y:.5,z:3.8},{x:26,y:-3.5,z:2.2},{x:26,y:-3.5,z:-2.2},{x:26,y:.5,z:-3.8},{x:26,y:3.5,z:-2.2},'+
        '{x:8,y:5.5,z:4.2},{x:8,y:1,z:5.4},{x:8,y:-4.5,z:4.2},{x:8,y:-4.5,z:-4.2},{x:8,y:1,z:-5.4},{x:8,y:5.5,z:-4.2},'+
        '{x:-12,y:5,z:3.2},{x:-12,y:.5,z:4.2},{x:-12,y:-4,z:3.2},{x:-12,y:-4,z:-3.2},{x:-12,y:.5,z:-4.2},{x:-12,y:5,z:-3.2},'+
        '{x:-38,y:1.8,z:1},{x:-38,y:-1.2,z:1},{x:-38,y:-1.2,z:-1},{x:-38,y:1.8,z:-1},'+
        '{x:-56,y:13.5,z:0},{x:-60,y:0,z:0},'+
        '{x:0,y:7.8,z:0},{x:-53,y:5,z:0},'+
        '{x:18,y:-8,z:-5.5},{x:-8,y:-8,z:-5.5},{x:18,y:-8,z:5.5},{x:-8,y:-8,z:5.5}'+
      '];'+
      'var hF=['+
        '{n:[0,1,2],t:"nose"},{n:[0,2,3],t:"nose"},{n:[0,3,4],t:"belly"},{n:[0,4,5],t:"belly"},{n:[0,5,6],t:"nose"},{n:[0,6,1],t:"nose"},'+
        '{n:[1,7,8,2],t:"canopy"},{n:[2,8,9,3],t:"canopy"},{n:[3,9,10,4],t:"belly"},{n:[4,10,11,5],t:"belly"},{n:[5,11,12,6],t:"canopy"},{n:[6,12,7,1],t:"canopy"},'+
        '{n:[7,13,14,8],t:"body"},{n:[8,14,15,9],t:"body"},{n:[9,15,16,10],t:"belly"},{n:[10,16,17,11],t:"belly"},{n:[11,17,18,12],t:"body"},{n:[12,7,13,18],t:"body"},'+
        '{n:[7,13,18,12],t:"engine"},'+
        '{n:[13,19,20,14],t:"body"},{n:[14,15,20],t:"body"},{n:[15,16,21,20],t:"belly"},{n:[16,17,21],t:"body"},{n:[17,18,22,21],t:"body"},{n:[18,13,19,22],t:"body"},'+
        '{n:[19,23,24,20],t:"fin"}'+
      '];'+
      'var hhPX=0,hhPY=0,hhPZ=0,hhP=0,hhRPM=0,hhAng=0,hhTL=0;'+
      'function drawHH(){'+
        'SC=4.2;OY=H*.72;'+
        'hhTL+=.5;'+
        'if(hhTL<60){hhRPM=Math.min(.28,hhRPM+.003);hhAng+=hhRPM;tel.textContent="ENG 1/2 START RUNUP │ ROTOR RPM: "+Math.round(hhRPM*780)+" │ ALT: GND";}'+
        'else if(hhTL<120){hhAng+=hhRPM;hhPY+=.18;tel.textContent="VERTICAL LIFTOFF │ ALT: "+Math.round(hhPY*1.8)+"FT │ IN GROUND EFFECT";}'+
        'else if(hhTL<190){hhAng+=hhRPM;hhPY+=.04;hhP=Math.min(.09,hhP+.002);hhPX+=.9;tel.textContent="TORQUE TRANSITION │ PITCH: "+Math.round(hhP*57.3)+"\xb0 │ 45KTS";}'+
        'else if(hhTL<280){hhAng+=hhRPM;hhPY+=.22;hhPX+=2.2;hhP=Math.max(.02,hhP-.001);tel.textContent="CLIMB OUT │ AIRSPEED: 120KTS │ ALT: "+Math.round(hhPY*1.8)+"FT";}'+
        'else{hhPX=0;hhPY=0;hhP=0;hhAng=0;hhRPM=0;hhTL=0;}'+
        'var pa=proj(hhPZ,0,hhPX);ctx.strokeStyle="rgba(0,242,255,.06)";ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(pa.x,pa.y,22,0,6.28);ctx.stroke();'+
        'var co=Math.cos(hhP),si=Math.sin(hhP);'+
        'var pts=hN.map(function(v){var rx=v.x*co-v.y*si,ry=v.x*si+v.y*co;var sp=proj(v.z+hhPZ,ry+hhPY,hhPX-rx);sp.wx=v.z;sp.wy=ry+hhPY;sp.wz=hhPX-rx;return sp;});'+
        'var sf=hF.map(function(f){var d=0;f.n.forEach(function(i){d+=pts[i].wz;});return{n:f.n,t:f.t,d:d/f.n.length};}).sort(function(a,b){return b.d-a.d;});'+
        'paintFaces(sf,pts,function(t){return t==="fin"||t==="engine"?lavHH.accent:t==="canopy"?{r:30,g:45,b:70}:t==="belly"?{r:145,g:152,b:162}:lavHH.body;},0.46);'+
        'ctx.strokeStyle="rgb("+lavHH.skid.r+","+lavHH.skid.g+","+lavHH.skid.b+")";ctx.lineWidth=1.5;'+
        'ctx.beginPath();ctx.moveTo(pts[27].x,pts[27].y);ctx.lineTo(pts[28].x,pts[28].y);ctx.stroke();'+
        'ctx.beginPath();ctx.moveTo(pts[29].x,pts[29].y);ctx.lineTo(pts[30].x,pts[30].y);ctx.stroke();'+
        'var hub=pts[25],bLen=46,dSeg=16,dPts=[],iPts=[];'+
        'for(var d=0;d<dSeg;d++){'+
          'var da=d/dSeg*6.2832;'+
          'var deX=hN[25].z+Math.sin(da)*bLen,deZ=hN[25].x+Math.cos(da)*bLen;'+
          'var drx=deZ*co-hN[25].y*si,dry=deZ*si+hN[25].y*co;'+
          'dPts.push(proj(deX+hhPZ,dry+hhPY,hhPX-drx));'+
          'var ieX=hN[25].z+Math.sin(da)*bLen*.75,ieZ=hN[25].x+Math.cos(da)*bLen*.75;'+
          'var irx=ieZ*co-hN[25].y*si,iry=ieZ*si+hN[25].y*co;'+
          'iPts.push(proj(ieX+hhPZ,iry+hhPY,hhPX-irx));'+
        '}'+
        'ctx.strokeStyle="rgba(0,242,255,.08)";ctx.lineWidth=.6;'+
        'ctx.beginPath();ctx.moveTo(dPts[0].x,dPts[0].y);for(var d=1;d<dSeg;d++){ctx.lineTo(dPts[d].x,dPts[d].y);}ctx.closePath();ctx.stroke();'+
        'ctx.strokeStyle="rgba(140,148,158,.04)";'+
        'ctx.beginPath();ctx.moveTo(iPts[0].x,iPts[0].y);for(var d=1;d<dSeg;d++){ctx.lineTo(iPts[d].x,iPts[d].y);}ctx.closePath();ctx.stroke();'+
        'for(var bi=0;bi<5;bi++){var blA=hhAng+(bi*Math.PI*2/5);'+
          'for(var tr=0;tr<8;tr++){var cA=blA-(tr*.035);'+
            'var tX=hN[25].z+Math.sin(cA)*bLen,tZ=hN[25].x+Math.cos(cA)*bLen;'+
            'var trx2=tZ*co-hN[25].y*si,trY=tZ*si+hN[25].y*co;'+
            'var tip=proj(tX+hhPZ,trY+hhPY,hhPX-trx2);'+
            'var al=Math.pow(1-tr/8,2)*.38;'+
            'ctx.strokeStyle="rgba(45,50,58,"+al+")";ctx.lineWidth=1.5-tr*.16;'+
            'ctx.beginPath();ctx.moveTo(hub.x,hub.y);ctx.lineTo(tip.x,tip.y);ctx.stroke();'+
            'if(tr===0){ctx.fillStyle="rgba(0,242,255,.75)";ctx.beginPath();ctx.arc(tip.x,tip.y,1,0,6.28);ctx.fill();}'+
          '}'+
        '}'+
        'var fHub=pts[26],fR=5.5*SC*.4;'+
        'ctx.strokeStyle="rgba(0,242,255,"+(0.06+Math.random()*.06)+")";ctx.fillStyle="rgba(45,50,60,.15)";'+
        'ctx.beginPath();ctx.arc(fHub.x,fHub.y,fR,0,6.28);ctx.fill();ctx.stroke();'+
        'ctx.lineWidth=1;ctx.strokeStyle="rgba(255,255,255,.12)";'+
        'for(var k=0;k<3;k++){var fA=hhAng*3.5+(k*Math.PI/3);'+
          'ctx.beginPath();ctx.moveTo(fHub.x-Math.sin(fA)*fR,fHub.y-Math.cos(fA)*fR);'+
          'ctx.lineTo(fHub.x+Math.sin(fA)*fR,fHub.y+Math.cos(fA)*fR);ctx.stroke();'+
        '}'+
        'ctx.fillStyle="rgba(10,34,84,.95)";ctx.strokeStyle="rgba(255,255,255,.25)";ctx.lineWidth=.8;'+
        'ctx.beginPath();ctx.arc(hub.x,hub.y,3.5,0,6.28);ctx.fill();ctx.stroke();'+
      '}'+
      'var tab="'+iTab+'",pano=false;'+
      'var TITLE={ac:"A321neo DEPARTURE",rk:"ARIANE 6 HEAVY LIFT",hh:"H160 HOVER PROFILE"};'+
      'function switchTab(t){'+
        'pano=false;document.getElementById("'+uid+'pb").classList.remove("on");'+
        'tab=t;ht.textContent=TITLE[t];'+
        'document.querySelectorAll("#'+uid+'tabs button[data-t]").forEach(function(b2){b2.classList.toggle("on",b2.dataset.t===t);});'+
        'if(t==="ac"){acT=0;acPZ=80;acPY=0;acA=0;acSpd=0;}'+
        'if(t==="rk"){rkT=0;rkPY=0;rkVY=0;rkBO=0;rkP=[];}'+
        'if(t==="hh"){hhPX=0;hhPY=0;hhP=0;hhAng=0;hhRPM=0;hhTL=0;}'+
      '}'+
      'document.querySelectorAll("#'+uid+'tabs button[data-t]").forEach(function(b2){b2.addEventListener("click",function(){switchTab(b2.dataset.t);});});'+
      'document.getElementById("'+uid+'pb").addEventListener("click",function(){'+
        'pano=!pano;'+
        'if(pano){ht.textContent="FLEET PANORAMA";tel.textContent="3 AIRCRAFT ACTIVE";this.classList.add("on");'+
          'document.querySelectorAll("#'+uid+'tabs button[data-t]").forEach(function(b2){b2.classList.remove("on");});'+
        '}else{this.classList.remove("on");switchTab(tab);}'+
      '});'+
      'function loop(){'+
        'ctx.clearRect(0,0,W,H);ctx.fillStyle="#05070f";ctx.fillRect(0,0,W,H);'+
        '[.08,.18,.30,.42,.54,.65,.77,.88,.95].forEach(function(s,i){'+
          'ctx.fillStyle="rgba(255,255,255,"+(0.12+i*.07)+")";'+
          'ctx.fillRect(s*W,(i%4*.08+.02)*H,i%3?1:2,i%3?1:2);'+
        '});'+
        'if(pano){'+
          'ctx.save();ctx.translate(-W*.28,0);drawAC();ctx.restore();'+
          'ctx.save();ctx.translate(W*.08,0);drawRK();ctx.restore();'+
          'ctx.save();ctx.translate(W*.25,0);drawHH();ctx.restore();'+
        '}else if(tab==="ac")drawAC();'+
        'else if(tab==="rk")drawRK();'+
        'else drawHH();'+
        'requestAnimationFrame(loop);'+
      '}'+
      'loop();'+
    '})();<\/script>';
};
