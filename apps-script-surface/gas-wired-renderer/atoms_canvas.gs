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
      // Auto-advance to next playbook slide after auto_next_ms if _A2UI_GO is defined
      (b.auto_next && b.auto_next_ms
        ? 'setTimeout(function(){if(typeof window._A2UI_GO==="function")window._A2UI_GO(' + JSON.stringify(String(b.auto_next)) + ');},' + Number(b.auto_next_ms) + ');'
        : '') +
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

// ── gdm_rocket_panel ── isometric launch canvas animation with HUD telemetry ──────────
// GRADUATED preview → stable: started life as hand-curated content ported from the
// Meet Stage add-on's gdm-rocket-panel Lit component (gemini/addons/meetstudio,
// "Apps Script is now a Workspace Core Service" playbook), shipped field-less through
// the mcp-apps off-catalog slot, then earned typed fields:
//   side:  "right" (default) | "left"  — which viewport half the overlay claims
//   layer: "back" (default, z-index 50) | "front" (z-index 150) — the original
//          Lit component's two layer variants
//   loop:  false (default, launch once and hold at apex — a static page reads an
//          endless relaunch as glitchy) | true (the original's ambient relaunch loop)
_RENDERERS['gdm_rocket_panel'] = function(b) {
  var uid  = 'grp' + Math.random().toString(36).substr(2, 6);
  var side = b.side === 'left' ? 'left' : 'right';
  var z    = b.layer === 'front' ? 150 : 50;
  var loop = b.loop === true;
  return (
    // Matches the original gdm-rocket-panel Lit component's layout:
    // fixed, half-width, full height, non-interactive overlay.
    '<div id="' + uid + 'w" data-a2ui-overlay="' + side + '-half" style="position:fixed;top:0;' +
      (side === 'left' ? 'left:0;' : 'right:0;') + 'width:50%;height:100%;' +
      'pointer-events:none;z-index:' + z + ';background:transparent;">' +
      '<canvas id="' + uid + 'c" style="position:absolute;inset:0;width:100%;height:100%;display:block;"></canvas>' +
    '</div>' +
    '<script>(function(){' +
      'var canvas=document.getElementById("' + uid + 'c");if(!canvas)return;' +
      'var ctx=canvas.getContext("2d");' +
      'var LOOP=' + (loop ? 'true' : 'false') + ',holdT=null;' +
      'var logo=null;' +
      'var img=new Image();' +
      'img.src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgwIiBoZWlnaHQ9IjE4MCIgdmlld0JveD0iMCAwIDE4MCAxODAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxnIGNsaXAtcGF0aD0idXJsKCNjbGlwMF8xOV8xMykiPgo8cGF0aCBkPSJNMTggODQuODUyOEw4NS44ODIyIDE2Ljk3MDZDOTUuMjU0OCA3LjU5Nzk4IDExMC40NTEgNy41OTc5OCAxMTkuODIzIDE2Ljk3MDZWMTYuOTcwNkMxMjkuMTk2IDI2LjM0MzEgMTI5LjE5NiA0MS41MzkxIDExOS44MjMgNTAuOTExN0w2OC41NTgxIDEwMi4xNzciIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMTIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8cGF0aCBkPSJNNjkuMjY1MiAxMDEuNDdMMTE5LjgyMyA1MC45MTE3QzEyOS4xOTYgNDEuNTM5MSAxNDQuMzkyIDQxLjUzOTEgMTUzLjc2NSA1MC45MTE3TDE1NC4xMTggNTEuMjY1MkMxNjMuNDkxIDYwLjYzNzggMTYzLjQ5MSA3NS44MzM4IDE1NC4xMTggODUuMjA2M0w5Mi43MjQ4IDE0Ni42Qzg5LjYwMDYgMTQ5LjcyNCA4OS42MDA2IDE1NC43ODkgOTIuNzI0OCAxNTcuOTEzTDEwNS4zMzEgMTcwLjUyIiBzdHJva2U9ImJsYWNrIiBzdHJva2Utd2lkdGg9IjEyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KPHBhdGggZD0iTTEwMi44NTMgMzMuOTQxMUw1Mi42NDgyIDg0LjE0NTdDNDMuMjc1NiA5My41MTgzIDQzLjI3NTYgMTA4LjcxNCA1Mi42NDgyIDExOC4wODdWMTE4LjA4N0M2Mi4wMjA4IDEyNy40NTkgNzcuMjE2NyAxMjcuNDU5IDg2LjU4OTMgMTE4LjA4N0wxMzYuNzk0IDY3Ljg4MjIiIHN0cm9rZT0iYmxhY2siIHN0cm9rZS13aWR0aD0iMTIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L2c+CjxkZWZzPgo8Y2xpcFBhdGggaWQ9ImNsaXAwXzE5XzEzIj4KPHJlY3Qgd2lkdGg9IjE4MCIgaGVpZ2h0PSIxODAiIGZpbGw9IndoaXRlIi8+CjwvY2xpcFBhdGg+CjwvZGVmcz4KPC9zdmc+Cg==";' +
      'img.onload=function(){logo=img;};' +
      'var y=1.2,trail=[],sparks=[],raf=null,landed=false;' +

      'function resize(){canvas.width=canvas.offsetWidth||540;canvas.height=canvas.offsetHeight||960;}' +
      'window.addEventListener("resize",resize);resize();' +

      'function drawRocket(cx,cy,w,h){' +
        'var s=Math.min(w,h)/7;' +
        'var pulse=0.85+0.15*Math.sin(Date.now()/90);' +
        'var glow=ctx.createRadialGradient(cx,cy+s*1.05,0,cx,cy+s*1.05,s*1.5*pulse);' +
        'glow.addColorStop(0,"rgba(255,255,200,0.98)");' +
        'glow.addColorStop(0.12,"rgba(255,180,0,0.9)");' +
        'glow.addColorStop(0.4,"rgba(255,60,0,0.55)");' +
        'glow.addColorStop(1,"rgba(255,20,0,0)");' +
        'ctx.beginPath();ctx.arc(cx,cy+s*1.05,s*1.5*pulse,0,Math.PI*2);' +
        'ctx.fillStyle=glow;ctx.fill();' +

        'ctx.save();ctx.translate(cx,cy);' +

        'ctx.beginPath();' +
        'ctx.moveTo(-s*0.28,s*0.55);ctx.lineTo(-s*0.72,s*1.02);ctx.lineTo(-s*0.28,s*0.82);' +
        'ctx.closePath();ctx.fillStyle="#0077b6";ctx.fill();' +

        'ctx.beginPath();' +
        'ctx.moveTo(s*0.28,s*0.55);ctx.lineTo(s*0.72,s*1.02);ctx.lineTo(s*0.28,s*0.82);' +
        'ctx.closePath();ctx.fillStyle="#0077b6";ctx.fill();' +

        'ctx.beginPath();' +
        'ctx.moveTo(-s*0.22,s*0.68);ctx.lineTo(-s*0.3,s*0.98);ctx.lineTo(s*0.3,s*0.98);ctx.lineTo(s*0.22,s*0.68);' +
        'ctx.closePath();' +
        'var bell=ctx.createLinearGradient(-s*0.3,0,s*0.3,0);' +
        'bell.addColorStop(0,"#4cc9f0");bell.addColorStop(0.5,"#e0f7ff");bell.addColorStop(1,"#4cc9f0");' +
        'ctx.fillStyle=bell;ctx.fill();' +

        'var body=ctx.createLinearGradient(-s*0.28,0,s*0.28,0);' +
        'body.addColorStop(0,"#0a8cce");body.addColorStop(0.25,"#00c8f0");body.addColorStop(0.55,"#c8f4ff");' +
        'body.addColorStop(0.8,"#00c8f0");body.addColorStop(1,"#0a6ca0");' +
        'ctx.beginPath();ctx.roundRect(-s*0.28,-s*0.6,s*0.56,s*1.3,s*0.05);' +
        'ctx.fillStyle=body;ctx.fill();' +

        'ctx.beginPath();' +
        'ctx.moveTo(0,-s*1.05);' +
        'ctx.bezierCurveTo(-s*0.07,-s*0.78,-s*0.24,-s*0.68,-s*0.28,-s*0.6);' +
        'ctx.lineTo(s*0.28,-s*0.6);' +
        'ctx.bezierCurveTo(s*0.24,-s*0.68,s*0.07,-s*0.78,0,-s*1.05);' +
        'ctx.closePath();' +
        'var nose=ctx.createLinearGradient(-s*0.28,0,s*0.28,0);' +
        'nose.addColorStop(0,"#0a6ca0");nose.addColorStop(0.45,"#d8f8ff");nose.addColorStop(1,"#0a6ca0");' +
        'ctx.fillStyle=nose;ctx.fill();' +

        'var badgeSize=s*0.38,badgeX=-badgeSize/2,badgeY=-s*0.38;' +
        'ctx.beginPath();' +
        'ctx.roundRect(badgeX-s*0.03,badgeY-s*0.03,badgeSize+s*0.06,badgeSize+s*0.06,s*0.06);' +
        'ctx.fillStyle="rgba(255,255,255,0.92)";ctx.fill();' +
        'if(logo){ctx.drawImage(logo,badgeX,badgeY,badgeSize,badgeSize);}' +
        'else{' +
          'ctx.beginPath();ctx.arc(0,badgeY+badgeSize/2,badgeSize*0.4,0,Math.PI*2);' +
          'ctx.fillStyle="#00c8f0";ctx.fill();' +
        '}' +

        'ctx.beginPath();ctx.roundRect(-s*0.28,s*0.2,s*0.56,s*0.06,s*0.02);' +
        'ctx.fillStyle="rgba(255,255,255,0.25)";ctx.fill();' +

        'ctx.restore();' +
      '}' +

      'function drawHud(w,h){' +
        'var fs=Math.min(w,h)*0.026;' +
        'var progress=Math.max(0,(1.2-y)/1.5);' +
        'var altStr=y<0.05?"∞":Math.round(progress*28000).toLocaleString()+" ft";' +
        'var spdStr=y<0.05?"MACH ∞":Math.round(Math.min(380,80+progress*2200))+" kt";' +
        'ctx.font=fs+"px monospace";ctx.textAlign="right";' +
        'ctx.fillStyle="rgba(0,255,136,0.42)";' +
        'ctx.fillText("ALT "+altStr+"  SPD "+spdStr+"  ·  MCP APPS · A2UI CATALOG",w-10,h-10);' +
      '}' +

      'function loop(){' +
        'if(!canvas.isConnected)return;' +
        'var w=canvas.width,h=canvas.height,cx=w*0.5,s=Math.min(w,h)/7;' +
        'ctx.clearRect(0,0,w,h);' +

        'if(!landed){' +
          'y-=0.012+(1.2-y)*0.002;' +
          'if(y<=0.08){y=0.08;landed=true;}' +
        '}' +
        'var cy=y*h;' +

        'if(!landed){' +
          'trail.push({x:cx+(Math.random()-0.5)*s*0.08,y:cy+s*0.98,t:Date.now(),r:3+Math.random()*4});' +
        '}' +
        'trail=trail.filter(function(p){return Date.now()-p.t<260;});' +
        'trail.forEach(function(p){' +
          'var age=(Date.now()-p.t)/260;' +
          'var a=(1-age)*0.75;' +
          'var r=p.r*(1+age*3);' +
          'var g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r);' +
          'g.addColorStop(0,"rgba(255,230,100,"+a+")");' +
          'g.addColorStop(0.4,"rgba(255,90,0,"+(a*0.7)+")");' +
          'g.addColorStop(1,"rgba(255,20,0,0)");' +
          'ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fillStyle=g;ctx.fill();' +
        '});' +

        'if(!landed&&Math.random()<0.45){' +
          'sparks.push({x:cx+(Math.random()-0.5)*s*0.35,y:cy+s*0.98,' +
            'vx:(Math.random()-0.5)*3,vy:1.5+Math.random()*4,life:1});' +
        '}' +
        'sparks=sparks.filter(function(sp){return sp.life>0;});' +
        'sparks.forEach(function(sp){' +
          'ctx.beginPath();ctx.arc(sp.x,sp.y,sp.life*2.8,0,Math.PI*2);' +
          'ctx.fillStyle="rgba(255,"+Math.round(180+sp.life*75)+",40,"+sp.life+")";' +
          'ctx.fill();' +
          'sp.x+=sp.vx;sp.y+=sp.vy;sp.life-=0.065;' +
        '});' +

        'drawRocket(cx,cy,w,h);' +
        'drawHud(w,h);' +

        'if(landed&&trail.length===0&&sparks.length===0){' +
          // loop:true restores the original Lit component's ambient relaunch —
          // hold ~2.6s at apex, then reset to the pad and fly again.
          'if(LOOP&&!holdT){holdT=setTimeout(function(){' +
            'holdT=null;y=1.2;landed=false;raf=requestAnimationFrame(loop);' +
          '},2600);}' +
          'return;' +
        '}' +
        'raf=requestAnimationFrame(loop);' +
      '}' +
      'loop();' +
    '})();<\/script>'
  );
};

// ── iso_fireworks_panel ── isometric fireworks canvas — the off-catalog resident ──────
// Hand-curated content, NOT schema-generated: stage:preview, fields:{} by design.
// This is the current occupant of the mcp-apps page's off-catalog slot — the living
// demo that curated content and catalog atoms ride the same mediated channel. The
// previous occupant (gdm_rocket_panel) graduated to a stable typed atom; this piece
// holds the doorway until it earns fields of its own.
// Slowly-rotating isometric ground grid, shells launched from grid points, bursts as
// true 3D particle spheres projected through the same iso transform, ground
// reflections, additive glow. Ambient randomized cadence (episodic bursts read as
// ambient, unlike a relaunching rocket). prefers-reduced-motion → one static frame.
_RENDERERS['iso_fireworks_panel'] = function(b) {
  var uid = 'ifw' + Math.random().toString(36).substr(2, 6);
  return (
    '<div id="' + uid + 'w" data-a2ui-overlay="right-half" style="position:fixed;top:0;right:0;width:50%;height:100%;' +
      'pointer-events:none;z-index:50;background:transparent;">' +
      '<canvas id="' + uid + 'c" style="position:absolute;inset:0;width:100%;height:100%;display:block;"></canvas>' +
    '</div>' +
    '<script>(function(){' +
      'var canvas=document.getElementById("' + uid + 'c");if(!canvas)return;' +
      'var ctx=canvas.getContext("2d");' +
      'function resize(){canvas.width=canvas.offsetWidth||540;canvas.height=canvas.offsetHeight||960;}' +
      'window.addEventListener("resize",resize);resize();' +

      // Isometric projection with a slow global yaw — the whole scene (grid,
      // shells, bursts) rotates through one transform, which is what sells 3D.
      'var CA=0.866,SA=0.5,rot=0;' +
      'function iso(x,y,z){' +
        'var w=canvas.width,h=canvas.height,s=Math.min(w,h)/16;' +
        'var c=Math.cos(rot),sn=Math.sin(rot);' +
        'var xr=x*c+z*sn,zr=z*c-x*sn;' +
        'return{x:w*0.5+(xr-zr)*CA*s,y:h*0.82+(xr+zr)*SA*s*0.55-y*s};}' +

      'var PALETTES=[' +
        '["255,224,130","255,150,0"],' +      // gold
        '["190,244,255","0,200,240"],' +      // cyan (rocket family blues)
        '["255,190,240","236,72,153"],' +     // magenta
        '["235,235,255","140,150,255"]' +     // ice white/indigo
      '];' +
      'var PADS=[[-2.4,-1.1],[0,-2.6],[2.4,-0.6],[1.1,2.1]];' +
      'var shells=[],parts=[],nextLaunch=Date.now()+400;' +

      'function drawGrid(){' +
        'ctx.strokeStyle="rgba(99,102,241,0.16)";ctx.lineWidth=1;' +
        'for(var i=-4;i<=4;i++){' +
          'var a=iso(i,0,-4),b2=iso(i,0,4);' +
          'ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b2.x,b2.y);ctx.stroke();' +
          'var c2=iso(-4,0,i),d=iso(4,0,i);' +
          'ctx.beginPath();ctx.moveTo(c2.x,c2.y);ctx.lineTo(d.x,d.y);ctx.stroke();' +
        '}' +
        'PADS.forEach(function(p){' +
          'var q=iso(p[0],0,p[1]);' +
          'ctx.beginPath();ctx.arc(q.x,q.y,2.5,0,Math.PI*2);' +
          'ctx.fillStyle="rgba(99,102,241,0.5)";ctx.fill();' +
        '});' +
      '}' +

      'function burst(x,y,z){' +
        'var pal=PALETTES[Math.floor(Math.random()*PALETTES.length)];' +
        'var n=70+Math.floor(Math.random()*40);' +
        'for(var i=0;i<n;i++){' +
          // uniform-ish sphere: random 3-vector, normalized, random speed
          'var ux=Math.random()*2-1,uy=Math.random()*2-1,uz=Math.random()*2-1;' +
          'var m=Math.sqrt(ux*ux+uy*uy+uz*uz)||1,sp=(0.045+Math.random()*0.05);' +
          'parts.push({x:x,y:y,z:z,vx:ux/m*sp,vy:uy/m*sp,vz:uz/m*sp,' +
            'life:1,decay:0.008+Math.random()*0.007,col:pal});' +
        '}' +
      '}' +

      'function step(){' +
        'var now=Date.now();' +
        'if(now>nextLaunch&&shells.length<3){' +
          'var pad=PADS[Math.floor(Math.random()*PADS.length)];' +
          'shells.push({x:pad[0],z:pad[1],y:0,vy:0.13+Math.random()*0.04,' +
            'apex:4.2+Math.random()*2.2,tw:[]});' +
          'nextLaunch=now+1200+Math.random()*1400;' +
        '}' +
        'shells=shells.filter(function(s){' +
          's.y+=s.vy;s.vy-=0.0011;' +
          's.tw.push({x:s.x,y:s.y,z:s.z,life:1});' +
          'if(s.tw.length>14)s.tw.shift();' +
          'if(s.vy<=0.015||s.y>=s.apex){' +
            'burst(s.x,s.y,s.z);' +
            'if(Math.random()<0.28)burst(s.x,s.y*0.92,s.z);' + // occasional double-burst
            'return false;}' +
          'return true;});' +
        'parts=parts.filter(function(p){' +
          'p.x+=p.vx;p.y+=p.vy;p.z+=p.vz;' +
          'p.vy-=0.0016;p.vx*=0.985;p.vz*=0.985;' + // gravity + drag
          'p.life-=p.decay;return p.life>0&&p.y>-0.2;});' +
      '}' +

      'function draw(){' +
        'var w=canvas.width,h=canvas.height;' +
        'ctx.clearRect(0,0,w,h);' +
        'drawGrid();' +
        'ctx.globalCompositeOperation="lighter";' +
        'shells.forEach(function(s){' +
          's.tw.forEach(function(t,i){' +
            'var q=iso(t.x,t.y,t.z),a=(i/s.tw.length)*0.6;' +
            'ctx.beginPath();ctx.arc(q.x,q.y,1.6,0,Math.PI*2);' +
            'ctx.fillStyle="rgba(255,214,120,"+a+")";ctx.fill();});' +
          'var q2=iso(s.x,s.y,s.z);' +
          'ctx.beginPath();ctx.arc(q2.x,q2.y,2.4,0,Math.PI*2);' +
          'ctx.fillStyle="rgba(255,240,190,0.95)";ctx.fill();});' +
        'parts.forEach(function(p){' +
          'var q=iso(p.x,p.y,p.z),r=1.1+p.life*1.9;' +
          'var g=ctx.createRadialGradient(q.x,q.y,0,q.x,q.y,r*2.4);' +
          'g.addColorStop(0,"rgba("+p.col[0]+","+p.life+")");' +
          'g.addColorStop(0.5,"rgba("+p.col[1]+","+(p.life*0.55)+")");' +
          'g.addColorStop(1,"rgba("+p.col[1]+",0)");' +
          'ctx.beginPath();ctx.arc(q.x,q.y,r*2.4,0,Math.PI*2);ctx.fillStyle=g;ctx.fill();' +
          // ground reflection: same particle projected below the grid plane
          'if(p.y>0){var qr=iso(p.x,-p.y*0.55,p.z);' +
            'ctx.beginPath();ctx.arc(qr.x,qr.y,r*1.4,0,Math.PI*2);' +
            'ctx.fillStyle="rgba("+p.col[1]+","+(p.life*0.12)+")";ctx.fill();}' +
        '});' +
        'ctx.globalCompositeOperation="source-over";' +
      '}' +

      'var RM=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;' +
      'if(RM){' +
        // one static mid-life burst, no animation
        'burst(0,3.4,0);' +
        'for(var i=0;i<24;i++)step();' +
        'draw();return;' +
      '}' +
      'function frame(){' +
        'if(!canvas.isConnected)return;' +
        'rot+=0.0012;step();draw();' +
        'requestAnimationFrame(frame);' +
      '}' +
      'frame();' +
    '})();<\/script>'
  );
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

// ── globe_3d ───────────────────────────────────────────────────────────────────
// Interactive spinning 3-D wireframe or earth globe on HTML5 canvas.
// Draggable with inertia. Supports dot pins and great-circle arcs.
// Fields:
//   size   — diameter px (default 300)
//   color  — accent hex (default #6366f1)
//   speed  — auto-spin radians/frame (default 0.006)
//   lines  — latitude line count (default 10)
//   theme  — wire|earth (default wire)
//   dots   — [{lat,lon,label?,color?}] pins
//   arcs   — [{from:[lat,lon],to:[lat,lon],color?}] great-circle arcs
_RENDERERS['globe_3d'] = function(b) {
  var size  = b.size  || 300;
  var color = b.color || '#6366f1';
  var speed = b.speed !== undefined ? b.speed : 0.006;
  var lines = b.lines || 10;
  var theme = b.theme || 'wire';
  var dots  = JSON.stringify(b.dots || []);
  var arcs  = JSON.stringify(b.arcs || []);
  var uid   = 'glb' + Math.random().toString(36).substr(2,6);

  return (
    '<div style="display:flex;justify-content:center;margin:1.2rem 0;">' +
      '<canvas id="' + uid + '" width="' + size + '" height="' + size + '" ' +
        'style="border-radius:50%;cursor:grab;display:block;">' +
      '</canvas>' +
    '</div>' +
    '<script>(function(){' +
      'var c=document.getElementById("' + uid + '");' +
      'if(!c)return;' +
      'var ctx=c.getContext("2d");' +
      'var W=c.width,H=c.height,R=W*0.42,cx=W/2,cy=H/2;' +
      'var COLOR="' + _esc(color) + '",THEME="' + _esc(theme) + '";' +
      'var LINES=' + lines + ',SPEED=' + speed + ';' +
      'var DOTS=' + dots + ',ARCS=' + arcs + ';' +

      // Rotation + inertia state
      'var ry=0,rx=0.3,vy=SPEED,vx=0;' +
      'var drag=false,lx=0,ly=0;' +

      // Mouse drag
      'c.addEventListener("mousedown",function(e){drag=true;lx=e.clientX;ly=e.clientY;vy=0;vx=0;c.style.cursor="grabbing";});' +
      'window.addEventListener("mouseup",function(){drag=false;c.style.cursor="grab";});' +
      'window.addEventListener("mousemove",function(e){' +
        'if(!drag)return;' +
        'var dx=e.clientX-lx,dy=e.clientY-ly;' +
        'vy=dx*0.008;vx=dy*0.008;' +
        'ry+=vy;rx+=vx;lx=e.clientX;ly=e.clientY;' +
      '});' +

      // Touch drag
      'var lt=null;' +
      'c.addEventListener("touchstart",function(e){e.preventDefault();lt=e.touches[0];vy=0;vx=0;},{passive:false});' +
      'c.addEventListener("touchmove",function(e){e.preventDefault();' +
        'if(!lt)return;var t=e.touches[0];' +
        'var dx=t.clientX-lt.clientX,dy=t.clientY-lt.clientY;' +
        'vy=dx*0.008;vx=dy*0.008;ry+=vy;rx+=vx;lt=t;' +
      '},{passive:false});' +
      'c.addEventListener("touchend",function(){lt=null;},{passive:false});' +

      // Project lat/lon → screen {x,y,z}. z>0 = front hemisphere.
      // Convention: lat=0,lon=0 faces viewer; lat=90 = north pole up.
      'function proj(lat,lon){' +
        'var ph=lat*Math.PI/180,th=lon*Math.PI/180;' +
        'var x=Math.cos(ph)*Math.sin(th),y=Math.sin(ph),z=Math.cos(ph)*Math.cos(th);' +
        'var x1=x*Math.cos(ry)+z*Math.sin(ry),z1=-x*Math.sin(ry)+z*Math.cos(ry);' +
        'var y2=y*Math.cos(rx)-z1*Math.sin(rx),z2=y*Math.sin(rx)+z1*Math.cos(rx);' +
        'return{x:cx+R*x1,y:cy-R*y2,z:z2};' +
      '}' +

      // Draw a [lat,lon] polyline, skipping back-facing segments
      'function poly(pts,stroke,alpha,lw){' +
        'ctx.save();ctx.strokeStyle=stroke;ctx.globalAlpha=alpha;ctx.lineWidth=lw||0.7;' +
        'ctx.beginPath();var go=false;' +
        'for(var i=0;i<pts.length;i++){' +
          'var p=proj(pts[i][0],pts[i][1]);' +
          'if(p.z<0){go=false;continue;}' +
          'if(!go){ctx.moveTo(p.x,p.y);go=true;}else{ctx.lineTo(p.x,p.y);}' +
        '}' +
        'ctx.stroke();ctx.restore();' +
      '}' +

      // Great-circle arc: slerp in Cartesian space, apply rotation inline
      'function arc(from,to,col){' +
        'var la1=from[0]*Math.PI/180,lo1=from[1]*Math.PI/180;' +
        'var la2=to[0]*Math.PI/180,lo2=to[1]*Math.PI/180;' +
        'var ax=Math.cos(la1)*Math.sin(lo1),ay=Math.sin(la1),az=Math.cos(la1)*Math.cos(lo1);' +
        'var bx=Math.cos(la2)*Math.sin(lo2),by=Math.sin(la2),bz=Math.cos(la2)*Math.cos(lo2);' +
        'ctx.save();ctx.strokeStyle=col||"#f59e0b";ctx.lineWidth=1.5;ctx.globalAlpha=0.9;' +
        'ctx.beginPath();var go=false;' +
        'for(var i=0;i<=60;i++){' +
          'var t=i/60,x=ax*(1-t)+bx*t,y=ay*(1-t)+by*t,z=az*(1-t)+bz*t;' +
          'var m=Math.sqrt(x*x+y*y+z*z);x/=m;y/=m;z/=m;' +
          'var x1=x*Math.cos(ry)+z*Math.sin(ry),z1=-x*Math.sin(ry)+z*Math.cos(ry);' +
          'var y2=y*Math.cos(rx)-z1*Math.sin(rx),z2=y*Math.sin(rx)+z1*Math.cos(rx);' +
          'if(z2<0){go=false;continue;}' +
          'var px=cx+R*x1,py=cy-R*y2;' +
          'if(!go){ctx.moveTo(px,py);go=true;}else{ctx.lineTo(px,py);}' +
        '}' +
        'ctx.stroke();ctx.restore();' +
      '}' +

      // Simplified continent outlines
      'var CONT=[' +
        '[[73,-141],[71,-90],[61,-94],[50,-55],[44,-67],[25,-80],[15,-85],[9,-79],[25,-110],[32,-117],[49,-124],[73,-141]],' +
        '[[-3,-78],[3,-52],[-3,-43],[-23,-43],[-34,-58],[-55,-68],[-50,-75],[-18,-70],[-3,-78]],' +
        '[[71,28],[61,5],[43,-5],[36,5],[37,35],[48,40],[60,30],[71,28]],' +
        '[[37,10],[37,36],[12,44],[0,42],[-5,40],[-34,26],[-34,18],[0,10],[15,-17],[37,10]],' +
        '[[71,30],[71,140],[53,142],[25,122],[1,104],[15,50],[12,44],[37,36],[48,40],[71,30]],' +
        '[[-18,122],[-25,114],[-38,145],[-18,148],[-12,136],[-18,122]]' +
      '];' +

      'function draw(){' +
        'ctx.clearRect(0,0,W,H);' +
        // Atmosphere glow
        'var ag=ctx.createRadialGradient(cx,cy,R*0.88,cx,cy,R*1.12);' +
        'ag.addColorStop(0,"rgba(99,102,241,0.10)");ag.addColorStop(1,"rgba(0,0,0,0)");' +
        'ctx.beginPath();ctx.arc(cx,cy,R*1.12,0,Math.PI*2);ctx.fillStyle=ag;ctx.fill();' +
        // Sphere base
        'var sg=ctx.createRadialGradient(cx-R*0.3,cy-R*0.3,0,cx,cy,R);' +
        'sg.addColorStop(0,"rgba(25,25,55,0.95)");sg.addColorStop(1,"rgba(5,5,18,0.98)");' +
        'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.fillStyle=sg;ctx.fill();' +
        // Clip all geo content to sphere
        'ctx.save();ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.clip();' +
        // Latitude lines
        'for(var i=1;i<LINES;i++){' +
          'var lat=90-(180*i/LINES),pts=[];' +
          'for(var j=0;j<=120;j++){pts.push([lat,j*3-180]);}' +
          'poly(pts,COLOR,0.18,0.6);' +
        '}' +
        // Longitude lines
        'for(var i=0;i<LINES*2;i++){' +
          'var lon=(i*360/(LINES*2))-180,pts=[];' +
          'for(var j=0;j<=60;j++){pts.push([-90+j*3,lon]);}' +
          'poly(pts,COLOR,0.18,0.6);' +
        '}' +
        // Continent outlines (earth theme)
        'if(THEME==="earth"){' +
          'for(var ci=0;ci<CONT.length;ci++){poly(CONT[ci],"#4ade80",0.75,1.3);}' +
        '}' +
        // Arcs
        'for(var ai=0;ai<ARCS.length;ai++){arc(ARCS[ai].from,ARCS[ai].to,ARCS[ai].color);}' +
        'ctx.restore();' +
        // Dot pins — drawn after clip restore so labels aren't cut
        'for(var di=0;di<DOTS.length;di++){' +
          'var d=DOTS[di],p=proj(d.lat,d.lon);' +
          'if(p.z<0.05)continue;' +
          'ctx.beginPath();ctx.arc(p.x,p.y,6,0,Math.PI*2);' +
          'ctx.strokeStyle=d.color||"#f59e0b";ctx.lineWidth=1;ctx.globalAlpha=0.35;ctx.stroke();ctx.globalAlpha=1;' +
          'ctx.beginPath();ctx.arc(p.x,p.y,3.5,0,Math.PI*2);' +
          'ctx.fillStyle=d.color||"#f59e0b";ctx.fill();' +
          'ctx.strokeStyle="#fff";ctx.lineWidth=1.2;ctx.stroke();' +
          'if(d.label){ctx.fillStyle="#fff";ctx.font="bold 11px sans-serif";ctx.globalAlpha=0.9;ctx.fillText(d.label,p.x+8,p.y+4);ctx.globalAlpha=1;}' +
        '}' +
        // Specular highlight
        'var hl=ctx.createRadialGradient(cx-R*0.38,cy-R*0.38,0,cx-R*0.38,cy-R*0.38,R*0.55);' +
        'hl.addColorStop(0,"rgba(255,255,255,0.13)");hl.addColorStop(1,"rgba(255,255,255,0)");' +
        'ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.fillStyle=hl;ctx.fill();' +
      '}' +

      // Animation loop: inertia decay → resume auto-spin
      'function loop(){' +
        'if(!drag){' +
          'ry+=vy;rx+=vx;' +
          'vy=vy*0.97+(Math.abs(vy)<0.0005?SPEED:0);' +
          'vx*=0.95;' +
        '}' +
        'draw();requestAnimationFrame(loop);' +
      '}' +
      'loop();' +
    '})();<\/script>'
  );
};

// ── canvas hero kit + the flow_field / *_type family ─────────────────────────
// Shared by flow_field, particle_type, light_type, living_type (2026-09-18).
// _A2UI_CANVAS_KIT_JS is emitted inside EVERY atom's own inline <script>, guarded
// by window._a2uiCK so it defines itself once per page: seeded value noise,
// DPR-aware resize, prefers-reduced-motion still frame (N synchronous steps,
// no loop), IntersectionObserver pause when offscreen, pointer tracking, and
// fitText (binary-search font size so agent-supplied lines fit the panel).
// Each atom then supplies only init(k) + draw(k).
//
// Hardening, by construction, for the whole family: every option is an ENUM
// or a clamped int, colours must match #rrggbb, and agent-supplied TEXT is
// JSON-encoded with "<" escaped to < so it can never close the script
// element. The config object is inserted with a function replacer so "$&"
// in text cannot expand. Python twins in renderers/web_article.py emit
// identical markup modulo uid; tests/test_flow_field.py and
// tests/test_agentic_type.py hold the two sides together. Edit BOTH.
//
// flow_field   — streams on a noise field converging on a glowing focus, copy overlay
// particle_type — the agent's words assemble from particles; pointer scatters them
// light_type   — the agent's words rendered as flowing light, masked to the glyphs
// living_type  — letters breathe on a noise field and lean toward the pointer
var _A2UI_CANVAS_KIT_JS =
  'window._a2uiCK=window._a2uiCK||(function(){' +
  'var P=new Uint8Array(512);' +
  '(function(){var s=1337,i,j,k;for(i=0;i<256;i++)P[i]=i;for(i=255;i>0;i--){s=(s*16807)%2147483647;j=s%(i+1);k=P[i];P[i]=P[j];P[j]=k;}for(i=0;i<256;i++)P[i+256]=P[i];})();' +
  'function hs(x,y,z){return P[(P[(P[x&255]+y)&255]+z)&255]/255;}' +
  'function fd(v){return v*v*(3-2*v);}' +
  'function L(a,b,v){return a+(b-a)*v;}' +
  'function noise(x,y,z){var X=Math.floor(x),Y=Math.floor(y),Z=Math.floor(z);x-=X;y-=Y;z-=Z;var u=fd(x),v=fd(y),w=fd(z);' +
  'return L(L(L(hs(X,Y,Z),hs(X+1,Y,Z),u),L(hs(X,Y+1,Z),hs(X+1,Y+1,Z),u),v),L(L(hs(X,Y,Z+1),hs(X+1,Y,Z+1),u),L(hs(X,Y+1,Z+1),hs(X+1,Y+1,Z+1),u),v),w);}' +
  'function fitText(ctx,lines,maxW,maxH,font,weight){var lo=8,hi=400;while(hi-lo>1){var m=(lo+hi)/2;ctx.font=weight+" "+m+"px "+font;var w=0;for(var i=0;i<lines.length;i++)w=Math.max(w,ctx.measureText(lines[i]).width);if(w<=maxW&&m*1.1*lines.length<=maxH)lo=m;else hi=m;}return lo;}' +
  'function mount(id,o){var c=document.getElementById(id);if(!c)return;var ctx=c.getContext("2d");if(!ctx)return;' +
  'var k={c:c,ctx:ctx,W:0,H:0,t:0,mx:null,my:null,noise:noise,dpr:Math.min(window.devicePixelRatio||1,2)},raf=0,vis=true;' +
  'var RM=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;' +
  'function resize(){var w=c.clientWidth||600,h=c.clientHeight||360;if(w===k.W&&h===k.H)return;k.W=w;k.H=h;c.width=Math.round(w*k.dpr);c.height=Math.round(h*k.dpr);ctx.setTransform(k.dpr,0,0,k.dpr,0,0);if(o.init)o.init(k);}' +
  'function step(){k.t+=0.0028*(o.speed||1);o.draw(k);}' +
  'function loop(){if(!vis){raf=0;return;}step();raf=requestAnimationFrame(loop);}' +
  'resize();' +
  'if(RM){var n=o.still||220;for(var i=0;i<n;i++)step();return;}' +
  'window.addEventListener("resize",resize);' +
  'if(o.interactive!==false){var box=c.parentNode;box.addEventListener("pointermove",function(e){var r=c.getBoundingClientRect();k.mx=e.clientX-r.left;k.my=e.clientY-r.top;});box.addEventListener("pointerleave",function(){k.mx=null;k.my=null;});}' +
  'if(window.IntersectionObserver){new IntersectionObserver(function(es){vis=es[0].isIntersecting;if(vis&&!raf)loop();}).observe(c);}' +
  'raf=requestAnimationFrame(loop);}' +
  'return {noise:noise,mount:mount,fitText:fitText};' +
  '})();';
var _FLOW_FIELD_JS =
  '(function(){' +
  'var C=%%CFG%%;var pts=[],N=0,fx=0,fy=0,FR=0;' +
  'function focus(k){if(C.focus==="none"){FR=0;return;}fx=k.W*(C.focus==="left"?0.26:C.focus==="center"?0.5:0.74);fy=k.H*0.5;FR=Math.min(k.W,k.H)*0.11;}' +
  'function spawn(p,k){p.x=Math.random()*k.W;p.y=Math.random()*k.H;p.px=p.x;p.py=p.y;p.life=90+Math.random()*180;p.sv=0.7+Math.random()*0.6;' +
  'p.ci=Math.floor(k.noise(p.x*C.sc*0.6,p.y*C.sc*0.6,7.3)*C.pal.length*1.3)%C.pal.length;return p;}' +
  'function init(k){var ctx=k.ctx;ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,k.W,k.H);focus(k);' +
  'N=Math.round(C.n*Math.min(2,Math.max(0.35,(k.W*k.H)/288000)));while(pts.length<N)pts.push(spawn({},k));pts.length=N;}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,t=k.t;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle="rgba("+C.bgRgb+","+C.trail+")";ctx.fillRect(0,0,W,H);' +
  'ctx.globalCompositeOperation="lighter";ctx.lineWidth=1.15;ctx.lineCap="round";' +
  'var i,p,a,dx,dy,d,vx,vy,f,ca,sa,nx;' +
  'for(i=0;i<N;i++){p=pts[i];p.px=p.x;p.py=p.y;' +
  'a=k.noise(p.x*C.sc,p.y*C.sc,t)*12.566;vx=Math.cos(a);vy=Math.sin(a);' +
  'if(FR){dx=fx-p.x;dy=fy-p.y;d=Math.sqrt(dx*dx+dy*dy)||1;if(d<FR*0.35){spawn(p,k);continue;}f=0.22+0.5*Math.max(0,1-d/(FR*4));vx+=dx/d*f;vy+=dy/d*f;}' +
  'if(k.mx!==null){dx=p.x-k.mx;dy=p.y-k.my;d=Math.sqrt(dx*dx+dy*dy);if(d<140&&d>0.5){f=(1-d/140)*1.4;ca=Math.cos(f);sa=Math.sin(f);nx=vx*ca-vy*sa;vy=vx*sa+vy*ca;vx=nx+dx/d*f*0.6;vy+=dy/d*f*0.6;}}' +
  'd=Math.sqrt(vx*vx+vy*vy)||1;f=C.spd*1.25*p.sv/d;p.x+=vx*f;p.y+=vy*f;' +
  'if(--p.life<0||p.x<-2||p.x>W+2||p.y<-2||p.y>H+2)spawn(p,k);}' +
  'for(var ci=0;ci<C.pal.length;ci++){ctx.strokeStyle="rgba("+C.pal[ci]+",0.55)";ctx.beginPath();' +
  'for(i=0;i<N;i++){p=pts[i];if(p.ci!==ci||(p.px===p.x&&p.py===p.y))continue;ctx.moveTo(p.px,p.py);ctx.lineTo(p.x,p.y);}ctx.stroke();}' +
  'if(FR){var g=ctx.createRadialGradient(fx,fy,0,fx,fy,FR*2.2);g.addColorStop(0,"rgba("+C.pal[0]+","+(0.5*C.trail)+")");g.addColorStop(0.35,"rgba("+C.pal[0]+","+(0.12*C.trail)+")");g.addColorStop(1,"rgba("+C.pal[0]+",0)");' +
  'ctx.fillStyle=g;ctx.beginPath();ctx.arc(fx,fy,FR*2.2,0,6.2832);ctx.fill();}}' +
  '_a2uiCK.mount("ff-%%UID%%",{init:init,draw:draw,speed:C.spd,interactive:C.inter,still:220});' +
  '})();';
var _PARTICLE_TYPE_JS =
  '(function(){' +
  'var C=%%CFG%%;var pts=[],pal=C.pal;' +
  'function build(k){var W=k.W,H=k.H,oc=document.createElement("canvas");oc.width=W;oc.height=H;var o=oc.getContext("2d");' +
  'var fs=_a2uiCK.fitText(o,C.lines,W*0.86,H*0.72,C.font,C.weight);o.font=C.weight+" "+fs+"px "+C.font;o.textAlign="center";o.textBaseline="middle";o.fillStyle="#fff";' +
  'var lh=fs*1.1,y0=H/2-lh*(C.lines.length-1)/2;for(var i=0;i<C.lines.length;i++)o.fillText(C.lines[i],W/2,y0+i*lh);' +
  'var d=o.getImageData(0,0,W,H).data,gap=2,tg;' +
  'do{tg=[];for(var y=0;y<H;y+=gap)for(var x=0;x<W;x+=gap){if(d[(y*W+x)*4+3]>120)tg.push([x,y]);}gap++;}while(tg.length>C.cap&&gap<10);' +
  'var old=pts;pts=[];for(var j=0;j<tg.length;j++){var q=old[j]||{x:Math.random()*W,y:Math.random()*H,vx:0,vy:0};q.tx=tg[j][0];q.ty=tg[j][1];' +
  'q.ci=Math.max(0,Math.min(pal.length-1,Math.floor((q.tx/W+(k.noise(q.tx*0.02,q.ty*0.02,1.5)-0.5)*0.18)*pal.length)));pts.push(q);}}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,i,p,dx,dy,d,f,ax,ay;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle="rgba("+C.bgRgb+",0.4)";ctx.fillRect(0,0,W,H);' +
  'for(i=0;i<pts.length;i++){p=pts[i];ax=(p.tx-p.x)*0.06;ay=(p.ty-p.y)*0.06;' +
  'if(k.mx!==null){dx=p.x-k.mx;dy=p.y-k.my;d=Math.sqrt(dx*dx+dy*dy);if(d<110&&d>0.5){f=(1-d/110)*5;ax+=dx/d*f;ay+=dy/d*f;}}' +
  'p.vx=(p.vx+ax)*0.82;p.vy=(p.vy+ay)*0.82;p.x+=p.vx;p.y+=p.vy;}' +
  'for(var ci=0;ci<pal.length;ci++){ctx.fillStyle="rgb("+pal[ci]+")";ctx.beginPath();for(i=0;i<pts.length;i++){p=pts[i];if(p.ci!==ci)continue;ctx.moveTo(p.x+C.dot,p.y);ctx.arc(p.x,p.y,C.dot,0,6.2832);}ctx.fill();}}' +
  '_a2uiCK.mount("pt-%%UID%%",{init:build,draw:draw,speed:1,interactive:C.inter,still:200});' +
  '})();';
var _LIGHT_TYPE_JS =
  '(function(){' +
  'var C=%%CFG%%;var pts=[],mask=null,N=0,fc=null,fx=null,MW=0,MH=0;' +
  'function text(o,W,H){var fs=_a2uiCK.fitText(o,C.lines,W*0.86,H*0.72,C.font,C.weight);o.font=C.weight+" "+fs+"px "+C.font;o.textAlign="center";o.textBaseline="middle";var lh=fs*1.1,y0=H/2-lh*(C.lines.length-1)/2;for(var i=0;i<C.lines.length;i++)o.fillText(C.lines[i],W/2,y0+i*lh);}' +
  'function spawn(p){var tries=0;do{p.x=Math.random()*MW;p.y=Math.random()*MH;tries++;}while(tries<40&&!mask[Math.floor(p.y)*MW+Math.floor(p.x)]);' +
  'p.px=p.x;p.py=p.y;p.life=60+Math.random()*140;p.sv=0.6+Math.random()*0.7;p.ci=Math.floor(Math.min(0.999,p.x/MW)*C.pal.length);return p;}' +
  'function init(k){var W=k.W,H=k.H;MW=W;MH=H;var oc=document.createElement("canvas");oc.width=W;oc.height=H;var o=oc.getContext("2d");o.fillStyle="#fff";text(o,W,H);' +
  'var d=o.getImageData(0,0,W,H).data;mask=new Uint8Array(W*H);var on=0;for(var i=0;i<W*H;i++){if(d[i*4+3]>100){mask[i]=1;on++;}}' +
  'fc=document.createElement("canvas");fc.width=k.c.width;fc.height=k.c.height;fx=fc.getContext("2d");fx.setTransform(k.dpr,0,0,k.dpr,0,0);fx.fillStyle=C.bg;fx.fillRect(0,0,W,H);' +
  'N=Math.min(C.cap,Math.max(40,Math.round(on/C.per)));pts=[];for(var j=0;j<N;j++)pts.push(spawn({}));}' +
  'function draw(k){var W=k.W,H=k.H,ctx=k.ctx,t=k.t,i,p,a,vx,vy,d,dx,dy,f,ca,sa,nx;' +
  'fx.globalCompositeOperation="source-over";fx.fillStyle="rgba("+C.bgRgb+","+C.trail+")";fx.fillRect(0,0,W,H);' +
  'fx.globalCompositeOperation="lighter";fx.lineWidth=1.2;fx.lineCap="round";' +
  'for(i=0;i<N;i++){p=pts[i];p.px=p.x;p.py=p.y;a=k.noise(p.x*C.sc,p.y*C.sc,t)*12.566;vx=Math.cos(a);vy=Math.sin(a);' +
  'if(k.mx!==null){dx=p.x-k.mx;dy=p.y-k.my;d=Math.sqrt(dx*dx+dy*dy);if(d<120&&d>0.5){f=(1-d/120)*1.3;ca=Math.cos(f);sa=Math.sin(f);nx=vx*ca-vy*sa;vy=vx*sa+vy*ca;vx=nx;}}' +
  'p.x+=vx*C.spd*p.sv;p.y+=vy*C.spd*p.sv;' +
  'if(--p.life<0||p.x<0||p.y<0||p.x>=W||p.y>=H||!mask[Math.floor(p.y)*W+Math.floor(p.x)])spawn(p);}' +
  'for(var ci=0;ci<C.pal.length;ci++){fx.strokeStyle="rgba("+C.pal[ci]+",0.7)";fx.beginPath();for(i=0;i<N;i++){p=pts[i];if(p.ci!==ci||(p.px===p.x&&p.py===p.y))continue;fx.moveTo(p.px,p.py);fx.lineTo(p.x,p.y);}fx.stroke();}' +
  'ctx.setTransform(1,0,0,1,0,0);ctx.globalCompositeOperation="source-over";ctx.clearRect(0,0,k.c.width,k.c.height);ctx.setTransform(k.dpr,0,0,k.dpr,0,0);' +
  'ctx.fillStyle="#fff";text(ctx,W,H);ctx.globalCompositeOperation="source-in";ctx.setTransform(1,0,0,1,0,0);ctx.drawImage(fc,0,0);ctx.setTransform(k.dpr,0,0,k.dpr,0,0);' +
  'ctx.globalCompositeOperation="destination-over";' +
  'if(C.glow){ctx.save();ctx.shadowColor="rgba("+C.pal[0]+",0.6)";ctx.shadowBlur=30;ctx.fillStyle="rgba("+C.pal[0]+",0.1)";text(ctx,W,H);ctx.restore();}' +
  'ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);ctx.globalCompositeOperation="source-over";}' +
  '_a2uiCK.mount("lt-%%UID%%",{init:init,draw:draw,speed:C.spd,interactive:C.inter,still:220});' +
  '})();';
var _LIVING_TYPE_JS =
  '(function(){' +
  'var C=%%CFG%%;var G=[],fs=0;' +
  'function layout(k){var ctx=k.ctx,W=k.W,H=k.H;fs=_a2uiCK.fitText(ctx,C.lines,W*0.84,H*0.6,C.font,C.weight);ctx.font=C.weight+" "+fs+"px "+C.font;G=[];var lh=fs*1.15,y0=H/2-lh*(C.lines.length-1)/2;' +
  'for(var li=0;li<C.lines.length;li++){var s=C.lines[li],w=ctx.measureText(s).width,x=W/2-w/2,y=y0+li*lh;for(var i=0;i<s.length;i++){var ch=s.charAt(i),cw=ctx.measureText(ch).width;G.push({ch:ch,x:x+cw/2,y:y,i:G.length,ci:0});x+=cw;}}' +
  'for(var j=0;j<G.length;j++)G[j].ci=Math.floor(Math.min(0.999,G[j].x/W)*C.pal.length);}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,t=k.t*4;ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);ctx.font=C.weight+" "+fs+"px "+C.font;ctx.textAlign="center";ctx.textBaseline="middle";' +
  'for(var i=0;i<G.length;i++){var g=G[i];if(g.ch===" ")continue;var n1=k.noise(g.i*0.35,t,3.1)-0.5,n2=k.noise(g.i*0.35,t,9.7)-0.5,n3=k.noise(g.i*0.35,t,5.5)-0.5;' +
  'var ox=n1*C.amp*0.6,oy=n2*C.amp*1.2,rot=n3*C.amp*0.005,sc=1+n3*C.amp*0.004;' +
  'if(k.mx!==null){var dx=k.mx-g.x,dy=k.my-g.y,d=Math.sqrt(dx*dx+dy*dy);if(d<170&&d>0.5){var f=1-d/170;ox+=dx/d*f*C.amp;oy+=dy/d*f*C.amp;sc+=f*0.22;}}' +
  'ctx.save();ctx.translate(g.x+ox,g.y+oy);ctx.rotate(rot);ctx.scale(sc,sc);ctx.fillStyle="rgb("+C.pal[g.ci]+")";ctx.fillText(g.ch,0,0);ctx.restore();}}' +
  '_a2uiCK.mount("lv-%%UID%%",{init:layout,draw:draw,speed:C.spd,interactive:C.inter,still:1});' +
  '})();';
var _ORBIT_MARK_JS =
  '(function(){' +
  'var C=%%CFG%%;var pts=[],N=0,cx=0,cy=0,R=0,band=0,P1=C.pal[1]||C.pal[0];' +
  'var rings=[{a:-0.5585,d:1},{a:0.5585,d:-1},{a:1.5708,d:1}];' +
  'for(var q=0;q<3;q++){rings[q].c=Math.cos(rings[q].a);rings[q].s=Math.sin(rings[q].a);}' +
  'function spawn(p,k){p.x=Math.random()*k.W;p.y=Math.random()*k.H;p.px=p.x;p.py=p.y;p.life=120+Math.random()*240;p.sv=0.7+Math.random()*0.6;' +
  'p.ci=Math.floor(k.noise(p.x*C.sc*0.6,p.y*C.sc*0.6,7.3)*C.pal.length*1.3)%C.pal.length;return p;}' +
  'function init(k){var W=k.W,H=k.H;R=Math.min(W,H)*C.size*0.5;cx=W*(C.pos==="left"?0.28:C.pos==="right"?0.72:0.5);cy=H*0.5;band=R*0.16;' +
  'var ctx=k.ctx;ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);' +
  'N=Math.round(C.n*Math.min(2,Math.max(0.35,(W*H)/288000)));while(pts.length<N)pts.push(spawn({},k));pts.length=N;}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,t=k.t,rx=R,ry=R*0.44;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle="rgba("+C.bgRgb+","+C.trail+")";ctx.fillRect(0,0,W,H);' +
  'ctx.globalCompositeOperation="lighter";ctx.lineWidth=1.15;ctx.lineCap="round";' +
  'var i,p,a,dx,dy,d,vx,vy,f,j,rg,lx,ly,nr,dd,w,ph,tx,ty,tl,gx,gy,px,py,pl,ca,sa,nx;' +
  'for(i=0;i<N;i++){p=pts[i];p.px=p.x;p.py=p.y;a=k.noise(p.x*C.sc,p.y*C.sc,t)*12.566;vx=Math.cos(a);vy=Math.sin(a);' +
  'dx=p.x-cx;dy=p.y-cy;d=Math.sqrt(dx*dx+dy*dy);if(d<R*0.16){spawn(p,k);continue;}' +
  'for(j=0;j<3;j++){rg=rings[j];lx=dx*rg.c+dy*rg.s;ly=-dx*rg.s+dy*rg.c;nr=Math.sqrt((lx*lx)/(rx*rx)+(ly*ly)/(ry*ry));dd=(nr-1)*(rx+ry)*0.5;' +
  'if(dd>-band&&dd<band){w=1-Math.abs(dd)/band;ph=Math.atan2(ly/ry,lx/rx);tx=-rx*Math.sin(ph)*rg.d;ty=ry*Math.cos(ph)*rg.d;tl=Math.sqrt(tx*tx+ty*ty)||1;tx/=tl;ty/=tl;' +
  'px=lx/(rx*rx);py=ly/(ry*ry);pl=Math.sqrt(px*px+py*py)||1;px=-px/pl*dd/band*0.8;py=-py/pl*dd/band*0.8;' +
  'gx=(tx+px)*rg.c-(ty+py)*rg.s;gy=(tx+px)*rg.s+(ty+py)*rg.c;vx=vx*(1-w*0.9)+gx*w*1.4;vy=vy*(1-w*0.9)+gy*w*1.4;}}' +
  'if(k.mx!==null){dx=p.x-k.mx;dy=p.y-k.my;d=Math.sqrt(dx*dx+dy*dy);if(d<140&&d>0.5){f=(1-d/140)*1.4;ca=Math.cos(f);sa=Math.sin(f);nx=vx*ca-vy*sa;vy=vx*sa+vy*ca;vx=nx+dx/d*f*0.6;vy+=dy/d*f*0.6;}}' +
  'f=Math.sqrt(vx*vx+vy*vy)||1;f=C.spd*1.2*p.sv/f;p.x+=vx*f;p.y+=vy*f;' +
  'if(--p.life<0||p.x<-2||p.x>W+2||p.y<-2||p.y>H+2)spawn(p,k);}' +
  'for(var ci=0;ci<C.pal.length;ci++){ctx.strokeStyle="rgba("+C.pal[ci]+",0.55)";ctx.beginPath();' +
  'for(i=0;i<N;i++){p=pts[i];if(p.ci!==ci||(p.px===p.x&&p.py===p.y))continue;ctx.moveTo(p.px,p.py);ctx.lineTo(p.x,p.y);}ctx.stroke();}' +
  'var g=ctx.createRadialGradient(cx,cy,0,cx,cy,R*0.55);g.addColorStop(0,"rgba("+C.pal[0]+","+(0.7*C.trail)+")");g.addColorStop(1,"rgba("+C.pal[0]+",0)");' +
  'ctx.fillStyle=g;ctx.beginPath();ctx.arc(cx,cy,R*0.55,0,6.2832);ctx.fill();' +
  'ctx.globalCompositeOperation="source-over";' +
  'for(j=0;j<3;j++){rg=rings[j];ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,rg.a,0,6.2832);ctx.strokeStyle="rgba("+(j===1?P1:C.pal[0])+","+(j===2?0.3:0.85)+")";ctx.lineWidth=j===2?1.2:1.8;ctx.stroke();}' +
  'ctx.beginPath();ctx.arc(cx,cy,R*0.27,0,6.2832);ctx.fillStyle="rgb("+C.pal[0]+")";ctx.fill();' +
  'if(C.el){ph=t*12;lx=rx*Math.cos(ph);ly=ry*Math.sin(ph);rg=rings[0];var ex=cx+lx*rg.c-ly*rg.s,ey=cy+lx*rg.s+ly*rg.c;' +
  'ctx.beginPath();ctx.arc(ex,ey,R*0.125,0,6.2832);ctx.fillStyle="rgb("+P1+")";ctx.fill();}}' +
  '_a2uiCK.mount("om-%%UID%%",{init:init,draw:draw,speed:C.spd,interactive:C.inter,still:220});' +
  '})();';
function _ffHex(v, dflt) {
  return (typeof v === 'string' && /^#[0-9a-fA-F]{6}$/.test(v)) ? v.toLowerCase() : dflt;
}
function _ffRgb(hex) {
  return parseInt(hex.slice(1, 3), 16) + ',' + parseInt(hex.slice(3, 5), 16) + ',' + parseInt(hex.slice(5, 7), 16);
}
function _ffPick(v, table, dflt) {
  return (typeof v === 'string' && Object.prototype.hasOwnProperty.call(table, v)) ? table[v] : table[dflt];
}
function _ffInt(v, dflt, lo, hi) {
  var n = parseInt(v, 10);
  if (isNaN(n)) n = dflt;
  return Math.max(lo, Math.min(hi, n));
}
function _ffPal(colors, dflt) {
  var pal = [], cols = Array.isArray(colors) ? colors : [];
  for (var i = 0; i < cols.length && pal.length < 4; i++) {
    var h = _ffHex(cols[i], null);
    if (h) pal.push(_ffRgb(h));
  }
  return pal.length ? pal : dflt.slice();
}
// Agent-supplied copy -> up to 3 non-empty lines of at most 40 chars, JSON-encoded
// for the script with "<" escaped (a line containing "</script>" must never end the element).
function _ffLines(text, dflt) {
  var out = [], raw = (typeof text === 'string' ? text : '').split('\n');
  for (var i = 0; i < raw.length && out.length < 3; i++) {
    var s = raw[i].trim();
    if (s) out.push(s.slice(0, 40));
  }
  return out.length ? out : [dflt];
}
function _ffLinesJs(lines) {
  return JSON.stringify(lines).replace(/</g, '\\u003c');
}
var _FF_FONTS = {
  sans: 'system-ui,-apple-system,Segoe UI,Helvetica Neue,Arial,sans-serif',
  serif: 'Georgia,Times New Roman,serif',
  mono: 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace',
  display: 'Arial Black,Impact,Helvetica Neue,Arial,sans-serif'
};
var _FF_WEIGHTS = {regular: '400', bold: '700', black: '900'};
var _FF_DEFAULT_PAL = ['56,189,248', '129,140,248', '244,114,182'];
function _ffScript(js, uid, cfg) {
  return '<script>' + _A2UI_CANVAS_KIT_JS + js.replace(/%%UID%%/g, uid).replace(/%%CFG%%/g, function() { return cfg; }) + '<\/script>';
}
// Visually hidden copy so the words the canvas draws stay readable and selectable.
function _ffSrText(lines) {
  return '<span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;">' + _esc(lines.join(' ')) + '</span>';
}
function _ffPanel(height, bg, inner) {
  return '<div style="position:relative;height:' + height + 'px;margin:1rem 0;border-radius:16px;overflow:hidden;background:' + bg + ';">' + inner + '</div>';
}
function _ffCanvas(id) {
  return '<canvas id="' + id + '" aria-hidden="true" style="position:absolute;top:0;left:0;width:100%;height:100%;display:block;"></canvas>';
}

// Copy overlay shared by flow_field and orbit_mark: a readability veil on the
// copy's side plus eyebrow/title/body; empty string when there is no copy.
function _ffOverlay(align, bgRgb, pal, eyebrow, title, body, ink) {
  if (!(title || eyebrow || body)) return '';
  ink = ink || '#ffffff';
  var inkRgb = _ffRgb(ink);
  var veil = align === 'center'
    ? 'radial-gradient(ellipse at center,rgba(' + bgRgb + ',0.75) 0%,rgba(' + bgRgb + ',0.25) 45%,rgba(' + bgRgb + ',0) 75%)'
    : 'linear-gradient(to ' + (align === 'left' ? 'right' : 'left') + ',rgba(' + bgRgb + ',0.92) 0%,rgba(' + bgRgb + ',0.55) 38%,rgba(' + bgRgb + ',0) 68%)';
  return '<div style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;background:' + veil + ';"></div>'
    + '<div style="position:absolute;top:0;left:0;width:100%;height:100%;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;align-items:'
    + (align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start')
    + ';text-align:' + align + ';padding:32px 40px;pointer-events:none;">'
    + '<div style="max-width:' + (align === 'center' ? '80%' : '58%') + ';">'
    + (eyebrow ? '<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:rgb(' + pal[0] + ');margin-bottom:12px;">' + _esc(eyebrow) + '</div>' : '')
    + (title ? '<div style="font-size:2rem;line-height:1.1;font-weight:800;color:' + ink + ';letter-spacing:-0.02em;margin-bottom:12px;">' + _esc(title) + '</div>' : '')
    + (body ? '<div style="font-size:1rem;line-height:1.6;color:rgba(' + inkRgb + ',0.78);">' + _markdownToHtml(body) + '</div>' : '')
    + '</div></div>';
}

_RENDERERS['flow_field'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var bg = _ffHex(b.background, '#070a12');
  var pal = _ffPal(b.colors, _FF_DEFAULT_PAL);
  var n     = _ffPick(b.density, {low: '350', normal: '650', high: '1100'}, 'normal');
  var spd   = _ffPick(b.speed,   {slow: '0.6', normal: '1', fast: '1.6'}, 'normal');
  var trail = _ffPick(b.trail,   {short: '0.16', normal: '0.07', long: '0.035'}, 'normal');
  var sc    = _ffPick(b.scale,   {fine: '0.006', normal: '0.0034', broad: '0.0019'}, 'normal');
  var focus = _ffPick(b.focus,   {right: 'right', center: 'center', left: 'left', none: 'none'}, 'right');
  var align = _ffPick(b.align,   {left: 'left', center: 'center', right: 'right'}, 'left');
  var height = _ffInt(b.height, 360, 200, 900);
  var inter = b.interactive === false ? 'false' : 'true';
  var title = b.title || '', eyebrow = b.eyebrow || '', body = b.body || '';
  var bgRgb = _ffRgb(bg);
  var cfg = '{n:' + n + ',spd:' + spd + ',trail:' + trail + ',sc:' + sc
    + ',pal:["' + pal.join('","') + '"],bg:"' + bg + '",bgRgb:"' + bgRgb
    + '",focus:"' + focus + '",inter:' + inter + '}';
  var text = _ffOverlay(align, bgRgb, pal, eyebrow, title, body);
  return _ffPanel(height, bg, _ffCanvas('ff-' + uid) + text + _ffScript(_FLOW_FIELD_JS, uid, cfg));
};

// Shared field parsing for the three typography atoms.
function _ffTypeBase(b, dfltHeight) {
  var bg = _ffHex(b.background, '#070a12');
  return {
    lines: _ffLines(b.text, 'A2UI'),
    font: _ffPick(b.font, _FF_FONTS, 'sans'),
    weight: _ffPick(b.weight, _FF_WEIGHTS, 'black'),
    pal: _ffPal(b.colors, _FF_DEFAULT_PAL),
    bg: bg, bgRgb: _ffRgb(bg),
    height: _ffInt(b.height, dfltHeight, 160, 900),
    inter: b.interactive === false ? 'false' : 'true'
  };
}
function _ffTypeCfgHead(t) {
  return '{lines:' + _ffLinesJs(t.lines) + ',font:"' + t.font + '",weight:"' + t.weight
    + '",pal:["' + t.pal.join('","') + '"],bg:"' + t.bg + '",bgRgb:"' + t.bgRgb + '"';
}

_RENDERERS['particle_type'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var t = _ffTypeBase(b, 320);
  var cap = _ffPick(b.density, {low: '1200', normal: '2400', high: '4200'}, 'normal');
  var dot = _ffPick(b.dot, {fine: '1.1', normal: '1.5', bold: '2.1'}, 'normal');
  var cfg = _ffTypeCfgHead(t) + ',cap:' + cap + ',dot:' + dot + ',inter:' + t.inter + '}';
  return _ffPanel(t.height, t.bg, _ffCanvas('pt-' + uid) + _ffSrText(t.lines) + _ffScript(_PARTICLE_TYPE_JS, uid, cfg));
};

_RENDERERS['light_type'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var t = _ffTypeBase(b, 320);
  var per   = _ffPick(b.density, {low: '220', normal: '120', high: '70'}, 'normal');
  var spd   = _ffPick(b.speed,   {slow: '0.5', normal: '0.9', fast: '1.5'}, 'normal');
  var trail = _ffPick(b.trail,   {short: '0.16', normal: '0.07', long: '0.035'}, 'normal');
  var sc    = _ffPick(b.scale,   {fine: '0.012', normal: '0.006', broad: '0.003'}, 'normal');
  var glow  = b.glow === false ? 'false' : 'true';
  var cfg = _ffTypeCfgHead(t) + ',cap:3000,per:' + per + ',spd:' + spd + ',trail:' + trail + ',sc:' + sc + ',glow:' + glow + ',inter:' + t.inter + '}';
  return _ffPanel(t.height, t.bg, _ffCanvas('lt-' + uid) + _ffSrText(t.lines) + _ffScript(_LIGHT_TYPE_JS, uid, cfg));
};

_RENDERERS['living_type'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var t = _ffTypeBase(b, 240);
  var amp = _ffPick(b.motion, {subtle: '8', normal: '16', wild: '32'}, 'normal');
  var spd = _ffPick(b.speed,  {slow: '0.5', normal: '1', fast: '1.8'}, 'normal');
  var cfg = _ffTypeCfgHead(t) + ',amp:' + amp + ',spd:' + spd + ',inter:' + t.inter + '}';
  return _ffPanel(t.height, t.bg, _ffCanvas('lv-' + uid) + _ffSrText(t.lines) + _ffScript(_LIVING_TYPE_JS, uid, cfg));
};

// The catalog's own orbit mark (header wordmark .logo-atom geometry: three
// rx:ry = 1:0.44 ellipses at -32deg, 32deg, 90deg, nucleus r = 0.27R, electron
// r = 0.125R) with streams from the flow-field kit captured into its orbits.
_RENDERERS['orbit_mark'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var bg = _ffHex(b.background, '#070a12');
  var pal = _ffPal(b.colors, ['99,102,241', '168,85,247', '34,211,238']);
  var n     = _ffPick(b.density, {low: '260', normal: '500', high: '900'}, 'normal');
  var spd   = _ffPick(b.speed,   {slow: '0.6', normal: '1', fast: '1.6'}, 'normal');
  var trail = _ffPick(b.trail,   {short: '0.16', normal: '0.07', long: '0.035'}, 'normal');
  var size  = _ffPick(b.size,    {small: '0.5', normal: '0.78', large: '0.95'}, 'normal');
  var pos   = _ffPick(b.mark_position, {center: 'center', right: 'right', left: 'left'}, 'center');
  var align = _ffPick(b.align,   {left: 'left', center: 'center', right: 'right'}, 'left');
  var height = _ffInt(b.height, 360, 200, 900);
  var inter = b.interactive === false ? 'false' : 'true';
  var el = b.electron === false ? 'false' : 'true';
  var bgRgb = _ffRgb(bg);
  var cfg = '{n:' + n + ',spd:' + spd + ',trail:' + trail + ',sc:0.0034,pal:["' + pal.join('","') + '"],bg:"' + bg
    + '",bgRgb:"' + bgRgb + '",pos:"' + pos + '",size:' + size + ',el:' + el + ',inter:' + inter + '}';
  var text = _ffOverlay(align, bgRgb, pal, b.eyebrow || '', b.title || '', b.body || '');
  return _ffPanel(height, bg, _ffCanvas('om-' + uid) + text + _ffScript(_ORBIT_MARK_JS, uid, cfg));
};

// floating_particles and parallax_section were schema-declared "canvas fallback
// placeholders" until 2026-09-19: a dashed box on GAS/MCP Apps, a 12-div CSS
// stand-in on the web. Both are now real canvas atoms on the hero kit.
var _FLOATING_PARTICLES_JS =
  '(function(){' +
  'var C=%%CFG%%;var pts=[],N=0;' +
  'function spawn(p,k,fresh){p.x=Math.random()*k.W;p.y=fresh?Math.random()*k.H:k.H+10;p.z=0.3+Math.random()*0.7;p.r=(1.5+Math.random()*3.5)*p.z;p.v=(0.15+Math.random()*0.35)*p.z;p.ci=Math.floor(Math.random()*C.pal.length);p.a=0.25+p.z*0.55;return p;}' +
  'function init(k){N=Math.round(C.n*Math.min(2,Math.max(0.35,(k.W*k.H)/288000)));pts=[];for(var i=0;i<N;i++)pts.push(spawn({},k,true));}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,t=k.t;ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);ctx.globalCompositeOperation="lighter";' +
  'for(var i=0;i<N;i++){var p=pts[i],sway=(k.noise(p.x*0.004,p.y*0.004,t*2)-0.5)*1.6*p.z;p.x+=sway*C.spd;p.y-=p.v*C.spd;' +
  'if(k.mx!==null){var dx=p.x-k.mx,dy=p.y-k.my,d=Math.sqrt(dx*dx+dy*dy);if(d<120&&d>0.5){var f=(1-d/120)*2.2*p.z;p.x+=dx/d*f;p.y+=dy/d*f;}}' +
  'if(p.y<-12||p.x<-12||p.x>W+12)spawn(p,k,false);' +
  'var g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r*3);g.addColorStop(0,"rgba("+C.pal[p.ci]+","+p.a+")");g.addColorStop(0.5,"rgba("+C.pal[p.ci]+","+(p.a*0.35)+")");g.addColorStop(1,"rgba("+C.pal[p.ci]+",0)");' +
  'ctx.fillStyle=g;ctx.beginPath();ctx.arc(p.x,p.y,p.r*3,0,6.2832);ctx.fill();}}' +
  '_a2uiCK.mount("fp-%%UID%%",{init:init,draw:draw,speed:C.spd,interactive:C.inter,still:1});' +
  '})();';
var _PARALLAX_SECTION_JS =
  '(function(){' +
  'var C=%%CFG%%;var L=[];' +
  'function init(k){L=[];for(var li=0;li<3;li++){var items=[],n=C.n[li],base=li===0?0.22:li===1?0.12:0.05;for(var i=0;i<n;i++)items.push({x:Math.random(),y:Math.random(),r:base*(0.6+Math.random()*0.8),ci:Math.floor(Math.random()*C.pal.length)});L.push(items);}}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,t=k.t;ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);' +
  'var px=k.mx===null?0:(k.mx/W-0.5),py=k.my===null?0:(k.my/H-0.5),ax=Math.sin(t*3)*0.02,ay=Math.cos(t*2.3)*0.02;' +
  'for(var li=0;li<3;li++){var depth=(li+1)/3,sh=C.depth*depth,items=L[li],ox=-(px+ax)*sh*W,oy=-(py+ay)*sh*H,al=li===0?0.22:li===1?0.32:0.55,bl=li===0?0.9:li===1?0.7:0.35;' +
  'for(var i=0;i<items.length;i++){var o=items[i],x=o.x*W+ox,y=o.y*H+oy,r=o.r*Math.min(W,H);var g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,"rgba("+C.pal[o.ci]+","+al+")");g.addColorStop(bl,"rgba("+C.pal[o.ci]+","+(al*0.4)+")");g.addColorStop(1,"rgba("+C.pal[o.ci]+",0)");ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,r,0,6.2832);ctx.fill();}}}' +
  '_a2uiCK.mount("px-%%UID%%",{init:init,draw:draw,speed:1,interactive:C.inter,still:1});' +
  '})();';
function _ffHund(h) {
  var s = Math.floor(h / 100) + '.' + (h % 100 < 10 ? '0' : '') + (h % 100);
  return s.replace(/0+$/, '').replace(/\.$/, '');
}
_RENDERERS['floating_particles'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var bg = _ffHex(b.background, '#0f172a');
  var pal = _ffPal(b.colors, ['99,102,241', '139,92,246', '236,72,153', '6,182,212']);
  var n = _ffPick(b.density, {low: '60', normal: '120', high: '220'}, 'normal');
  var spd = _ffPick(b.speed, {slow: '0.6', normal: '1', fast: '1.7'}, 'normal');
  var height = _ffInt(b.height, 240, 120, 900);
  var inter = b.interactive === false ? 'false' : 'true';
  var title = b.title || b.label || b.text || '';
  var cfg = '{n:' + n + ',spd:' + spd + ',pal:["' + pal.join('","') + '"],bg:"' + bg + '",inter:' + inter + '}';
  var text = _ffOverlay('center', _ffRgb(bg), pal, b.eyebrow || '', title, b.body || '');
  return _ffPanel(height, bg, _ffCanvas('fp-' + uid) + text + _ffScript(_FLOATING_PARTICLES_JS, uid, cfg));
};
_RENDERERS['parallax_section'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var bg = _ffHex(b.background, '#0f172a');
  var pal = _ffPal(b.colors, ['99,102,241', '236,72,153', '6,182,212']);
  var depth = _ffPick(b.depth, {subtle: '0.04', normal: '0.08', deep: '0.14'}, 'normal');
  var height = _ffInt(b.height, 300, 160, 900);
  var inter = b.interactive === false ? 'false' : 'true';
  var title = b.title || b.label || b.text || '';
  var cfg = '{n:[3,6,14],depth:' + depth + ',pal:["' + pal.join('","') + '"],bg:"' + bg + '",inter:' + inter + '}';
  var text = _ffOverlay('center', _ffRgb(bg), pal, b.eyebrow || '', title, b.body || '');
  return _ffPanel(height, bg, _ffCanvas('px-' + uid) + text + _ffScript(_PARALLAX_SECTION_JS, uid, cfg));
};

// ── halftone_wave / message_lanes (2026-09-19) ────────────────────────────────
// halftone_wave: the one canvas hero that works on a WHITE page -- a dot grid
// whose dot size follows a travelling wave (noise, ripple from a focus, or a
// diagonal sweep), like animated print halftone; peaks tint to the accent.
// message_lanes: the A2UI pitch drawn -- packets stream from an agent node down
// curved lanes into a surface node, and every arrival unfolds a small card.
var _HALFTONE_WAVE_JS =
  '(function(){' +
  'var C=%%CFG%%;var fx=0,fy=0;' +
  'function init(k){fx=k.W*(C.focus==="left"?0.25:C.focus==="right"?0.75:0.5);fy=k.H*0.5;}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,t=k.t*C.spd,S=C.sp,R=S*0.48,D=Math.sqrt(W*W+H*H);' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.paper;ctx.fillRect(0,0,W,H);' +
  'var ink=[],acc=[],x,y,v,d,r,dx,dy;' +
  'for(y=S*0.5;y<H;y+=S){for(x=S*0.5;x<W;x+=S){' +
  'if(C.wave==="ripple"){dx=x-fx;dy=y-fy;d=Math.sqrt(dx*dx+dy*dy);v=0.5+0.5*Math.sin(d*0.045-t*9)*(1-Math.min(1,d/D));v=v*0.8+k.noise(x*0.006,y*0.006,t*0.7)*0.2;}' +
  'else if(C.wave==="sweep"){v=0.5+0.5*Math.sin((x+y)*0.018-t*10);v=v*0.7+k.noise(x*0.008,y*0.008,t)*0.3;}' +
  'else{v=k.noise(x*C.sc,y*C.sc,t*1.5);v=Math.max(0,Math.min(1,(v-0.25)*1.8));}' +
  'if(k.mx!==null){dx=x-k.mx;dy=y-k.my;d=Math.sqrt(dx*dx+dy*dy);if(d<140)v=Math.min(1,v+(1-d/140)*0.6);}' +
  'r=v*v*R;if(r<0.35)continue;(v>0.72&&C.hasAcc?acc:ink).push(x,y,r);}}' +
  'ctx.fillStyle=C.ink;ctx.beginPath();for(var i=0;i<ink.length;i+=3){ctx.moveTo(ink[i]+ink[i+2],ink[i+1]);ctx.arc(ink[i],ink[i+1],ink[i+2],0,6.2832);}ctx.fill();' +
  'if(acc.length){ctx.fillStyle=C.acc;ctx.beginPath();for(var j=0;j<acc.length;j+=3){ctx.moveTo(acc[j]+acc[j+2],acc[j+1]);ctx.arc(acc[j],acc[j+1],acc[j+2],0,6.2832);}ctx.fill();}}' +
  '_a2uiCK.mount("hw-%%UID%%",{init:init,draw:draw,speed:1,interactive:C.inter,still:1});' +
  '})();';
var _MESSAGE_LANES_JS =
  '(function(){' +
  'var C=%%CFG%%;var lanes=[],pk=[],cards=[],ax=0,ay=0,ar=0,sx=0,sy=0,sw=0,sh=0,flash=0;' +
  'function spawn(p){p.l=Math.floor(Math.random()*lanes.length);p.u=-Math.random()*0.3;p.v=(0.0035+Math.random()*0.004)*C.rate;p.ci=Math.floor(Math.random()*C.pal.length);p.w=10+Math.random()*8;return p;}' +
  'function pt(l,u){var L=lanes[l],a=1-u;return [a*a*L.x0+2*a*u*L.cx+u*u*L.x1,a*a*L.y0+2*a*u*L.cy+u*u*L.y1];}' +
  'function init(k){var W=k.W,H=k.H;ar=Math.min(H*0.12,34);ax=W*0.14;ay=H*0.5;sw=Math.min(W*0.22,170);sh=H*0.56;sx=W*0.86-sw/2;sy=H*0.5-sh/2;' +
  'lanes=[];for(var i=0;i<C.lanes;i++){var f=C.lanes===1?0.5:i/(C.lanes-1);lanes.push({x0:ax+ar,y0:ay+(f-0.5)*ar*1.4,x1:sx,y1:sy+sh*(0.15+0.7*f),cx:(ax+sx)/2,cy:ay+(f-0.5)*H*0.55});}' +
  'pk=[];var n=C.lanes*3;for(var j=0;j<n;j++)pk.push(spawn({}));cards=[];' +
  'var ctx=k.ctx;ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);}' +
  'function rr(ctx,x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,i,p,q,q2,a;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle="rgba("+C.bgRgb+",0.28)";ctx.fillRect(0,0,W,H);' +
  'ctx.lineWidth=1;for(i=0;i<lanes.length;i++){var L=lanes[i];ctx.strokeStyle="rgba("+C.pal[0]+",0.14)";ctx.beginPath();ctx.moveTo(L.x0,L.y0);ctx.quadraticCurveTo(L.cx,L.cy,L.x1,L.y1);ctx.stroke();}' +
  'ctx.globalCompositeOperation="lighter";ctx.lineCap="round";' +
  'for(i=0;i<pk.length;i++){p=pk[i];p.u+=p.v;if(p.u>=1){flash=1;cards.unshift({age:0,ci:p.ci});if(cards.length>3)cards.length=3;spawn(p);continue;}if(p.u<0)continue;' +
  'q=pt(p.l,p.u);q2=pt(p.l,Math.max(0,p.u-0.02));a=Math.atan2(q[1]-q2[1],q[0]-q2[0]);' +
  'ctx.save();ctx.translate(q[0],q[1]);ctx.rotate(a);ctx.fillStyle="rgba("+C.pal[p.ci]+",0.95)";rr(ctx,-p.w/2,-3,p.w,6,3);ctx.fill();' +
  'ctx.fillStyle="rgba("+C.bgRgb+",0.9)";ctx.fillRect(-p.w/2+3,-1,p.w*0.35,2);ctx.fillRect(-p.w/2+3+p.w*0.42,-1,p.w*0.22,2);ctx.restore();}' +
  'ctx.globalCompositeOperation="source-over";' +
  'var g=ctx.createRadialGradient(ax,ay,ar*0.2,ax,ay,ar*2.2);g.addColorStop(0,"rgba("+C.pal[0]+",0.35)");g.addColorStop(1,"rgba("+C.pal[0]+",0)");ctx.fillStyle=g;ctx.beginPath();ctx.arc(ax,ay,ar*2.2,0,6.2832);ctx.fill();' +
  'ctx.fillStyle=C.bg;ctx.beginPath();ctx.arc(ax,ay,ar,0,6.2832);ctx.fill();ctx.strokeStyle="rgb("+C.pal[0]+")";ctx.lineWidth=2;ctx.stroke();' +
  'ctx.beginPath();ctx.arc(ax,ay,ar*0.32,0,6.2832);ctx.fillStyle="rgb("+C.pal[0]+")";ctx.fill();' +
  'flash*=0.9;ctx.strokeStyle="rgba("+C.pal[1]+","+(0.35+flash*0.65)+")";ctx.lineWidth=1.5+flash*2;rr(ctx,sx,sy,sw,sh,10);ctx.fillStyle="rgba("+C.bgRgb+",0.85)";ctx.fill();ctx.stroke();' +
  'var cy=sy+12;for(i=0;i<cards.length;i++){var c=cards[i];c.age++;var grow=Math.min(1,c.age/18),ch=(sh-24-8*2)/3,al=i===2?Math.max(0,1-(c.age-160)/60):1;if(al<=0)continue;' +
  'ctx.globalAlpha=al;ctx.fillStyle="rgba("+C.pal[c.ci]+",0.18)";ctx.strokeStyle="rgba("+C.pal[c.ci]+",0.8)";ctx.lineWidth=1;rr(ctx,sx+10,cy,sw-20,ch*grow,5);ctx.fill();ctx.stroke();' +
  'if(grow>0.6){ctx.fillStyle="rgba("+C.pal[c.ci]+",0.9)";ctx.fillRect(sx+18,cy+8,(sw-36)*0.55,3);ctx.fillRect(sx+18,cy+15,(sw-36)*0.8,2);ctx.fillRect(sx+18,cy+20,(sw-36)*0.4,2);}' +
  'ctx.globalAlpha=1;cy+=ch+8;}' +
  'ctx.fillStyle="rgba(255,255,255,0.8)";ctx.font="600 11px system-ui,sans-serif";ctx.textAlign="center";ctx.textBaseline="top";ctx.fillText(C.from,ax,ay+ar+8);ctx.fillText(C.to,sx+sw/2,sy+sh+8);}' +
  '_a2uiCK.mount("ml-%%UID%%",{init:init,draw:draw,speed:1,interactive:false,still:260});' +
  '})();';
_RENDERERS['halftone_wave'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var paper = _ffHex(b.paper, '#f7f7f5'), ink = _ffHex(b.ink, '#0f172a');
  var acc = _ffHex(b.accent, null);
  var sp = _ffPick(b.spacing, {fine: '10', normal: '14', coarse: '20'}, 'normal');
  var spd = _ffPick(b.speed, {slow: '0.5', normal: '1', fast: '1.8'}, 'normal');
  var wave = _ffPick(b.wave, {noise: 'noise', ripple: 'ripple', sweep: 'sweep'}, 'noise');
  var focus = _ffPick(b.focus, {center: 'center', left: 'left', right: 'right'}, 'center');
  var align = _ffPick(b.align, {left: 'left', center: 'center', right: 'right'}, 'left');
  var height = _ffInt(b.height, 320, 160, 900);
  var inter = b.interactive === false ? 'false' : 'true';
  var cfg = '{sp:' + sp + ',sc:0.0045,spd:' + spd + ',wave:"' + wave + '",focus:"' + focus + '",ink:"' + ink + '",paper:"' + paper + '",acc:"' + (acc || ink) + '",hasAcc:' + (acc ? 'true' : 'false') + ',inter:' + inter + '}';
  var pal = [_ffRgb(acc || ink)];
  var text = _ffOverlay(align, _ffRgb(paper), pal, b.eyebrow || '', b.title || '', b.body || '', ink);
  return _ffPanel(height, paper, _ffCanvas('hw-' + uid) + text + _ffScript(_HALFTONE_WAVE_JS, uid, cfg));
};
_RENDERERS['message_lanes'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var bg = _ffHex(b.background, '#070a12');
  var pal = _ffPal(b.colors, ['56,189,248', '167,139,250', '244,114,182']);
  if (pal.length < 2) pal.push(pal[0]);
  var lanes = _ffInt(b.lanes, 4, 1, 6);
  var rate = _ffPick(b.rate, {slow: '0.6', normal: '1', fast: '1.7'}, 'normal');
  var height = _ffInt(b.height, 320, 200, 900);
  var from = _ffLinesJs([(typeof b.from_label === 'string' ? b.from_label : 'agent').trim().slice(0, 24) || 'agent']).slice(1, -1);
  var to = _ffLinesJs([(typeof b.to_label === 'string' ? b.to_label : 'surface').trim().slice(0, 24) || 'surface']).slice(1, -1);
  var align = _ffPick(b.align, {left: 'left', center: 'center', right: 'right'}, 'center');
  var cfg = '{lanes:' + lanes + ',rate:' + rate + ',pal:["' + pal.join('","') + '"],bg:"' + bg + '",bgRgb:"' + _ffRgb(bg) + '",from:' + from + ',to:' + to + '}';
  var text = _ffOverlay(align, _ffRgb(bg), pal, b.eyebrow || '', b.title || '', b.body || '');
  return _ffPanel(height, bg, _ffCanvas('ml-' + uid) + text + _ffScript(_MESSAGE_LANES_JS, uid, cfg));
};

// signal_tunnel (2026-09-19) — radial light streaks through a fixed vanishing
// point, converging ("in") or radiating ("out"). Sibling of flow_field on the
// same kit; streaks travel purely along their spawn angle (no 2D noise
// wander) and accelerate as they near the vanishing point, giving the tunnel
// its depth cue without any real 3D projection.
var _SIGNAL_TUNNEL_JS =
  '(function(){' +
  'var C=%%CFG%%;var pts=[],N=0,cx=0,cy=0,maxR=0,DIR=C.dir==="out"?1:-1;' +
  'function spawn(p,k){var a=Math.random()*6.2832;p.a=a;p.r=DIR<0?maxR*(0.5+Math.random()*0.5):maxR*0.02*(0.2+Math.random());' +
  'p.ci=Math.floor(((a/6.2832)%1)*C.pal.length);p.sv=0.7+Math.random()*0.6;return p;}' +
  'function init(k){var ctx=k.ctx;ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,k.W,k.H);' +
  'cx=k.W*(C.pos==="left"?0.26:C.pos==="center"?0.5:0.74);cy=k.H*0.5;maxR=Math.sqrt(Math.pow(Math.max(cx,k.W-cx),2)+cy*cy)*1.05;' +
  'N=Math.round(C.n*Math.min(2,Math.max(0.35,(k.W*k.H)/288000)));pts=[];while(pts.length<N)pts.push(spawn({},k));}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,i,p,x,y,px,py,f,pf,dx,dy,d;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle="rgba("+C.bgRgb+","+C.trail+")";ctx.fillRect(0,0,W,H);' +
  'ctx.globalCompositeOperation="lighter";ctx.lineWidth=1.3;ctx.lineCap="round";' +
  'for(i=0;i<N;i++){p=pts[i];px=cx+Math.cos(p.a)*p.r;py=cy+Math.sin(p.a)*p.r;' +
  'f=1-p.r/maxR;f=0.6+f*f*3.2;p.r+=DIR*C.spd*f*p.sv*2.2;' +
  'if(p.r<maxR*0.015||p.r>maxR){spawn(p,k);continue;}' +
  'x=cx+Math.cos(p.a)*p.r;y=cy+Math.sin(p.a)*p.r;' +
  'if(k.mx!==null){dx=x-k.mx;dy=y-k.my;d=Math.sqrt(dx*dx+dy*dy);if(d<120&&d>0.5){pf=(1-d/120)*4;x+=dx/d*pf;y+=dy/d*pf;}}' +
  'ctx.strokeStyle="rgba("+C.pal[p.ci]+","+(0.35+0.55*(p.r/maxR)).toFixed(3)+")";' +
  'ctx.beginPath();ctx.moveTo(px,py);ctx.lineTo(x,y);ctx.stroke();}' +
  'var g=ctx.createRadialGradient(cx,cy,0,cx,cy,maxR*0.16);g.addColorStop(0,"rgba("+C.pal[0]+",0.85)");g.addColorStop(1,"rgba("+C.pal[0]+",0)");' +
  'ctx.fillStyle=g;ctx.beginPath();ctx.arc(cx,cy,maxR*0.16,0,6.2832);ctx.fill();' +
  'ctx.globalCompositeOperation="source-over";}' +
  '_a2uiCK.mount("st-%%UID%%",{init:init,draw:draw,speed:C.spd,interactive:C.inter,still:220});' +
  '})();';
_RENDERERS['signal_tunnel'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var bg = _ffHex(b.background, '#070a12');
  var pal = _ffPal(b.colors, _FF_DEFAULT_PAL);
  var n     = _ffPick(b.density, {low: '250', normal: '450', high: '750'}, 'normal');
  var spd   = _ffPick(b.speed,   {slow: '0.6', normal: '1', fast: '1.7'}, 'normal');
  var trail = _ffPick(b.trail,   {short: '0.16', normal: '0.07', long: '0.035'}, 'normal');
  var dir   = _ffPick(b.direction, {'in': 'in', out: 'out'}, 'in');
  var pos   = _ffPick(b.position, {right: 'right', center: 'center', left: 'left'}, 'right');
  var align = _ffPick(b.align,   {left: 'left', center: 'center', right: 'right'}, 'left');
  var height = _ffInt(b.height, 360, 200, 900);
  var inter = b.interactive === false ? 'false' : 'true';
  var title = b.title || '', eyebrow = b.eyebrow || '', body = b.body || '';
  var bgRgb = _ffRgb(bg);
  var cfg = '{n:' + n + ',spd:' + spd + ',trail:' + trail
    + ',pal:["' + pal.join('","') + '"],bg:"' + bg + '",bgRgb:"' + bgRgb
    + '",dir:"' + dir + '",pos:"' + pos + '",inter:' + inter + '}';
  var text = _ffOverlay(align, bgRgb, pal, eyebrow, title, body);
  return _ffPanel(height, bg, _ffCanvas('st-' + uid) + text + _ffScript(_SIGNAL_TUNNEL_JS, uid, cfg));
};

// gradient_mesh_live (2026-09-19) — soft colour blobs on a Vogel-disk layout,
// drifting on the shared value-noise field (never loops, unlike a CSS
// @keyframes mesh gradient). Animated sibling of the static mesh_gradient
// atom and the CSS-only aurora_background.
var _GRADIENT_MESH_LIVE_JS =
  '(function(){' +
  'var C=%%CFG%%;var bx=[],by=[],R=0,amp=0;' +
  'function init(k){var W=k.W,H=k.H,i,ang,rad;bx=[];by=[];' +
  'R=Math.max(W,H)*0.42;amp=Math.min(W,H)*C.amp;' +
  'for(i=0;i<C.n;i++){ang=i*2.399963;rad=Math.sqrt((i+0.5)/C.n);bx.push(W*0.5+Math.cos(ang)*rad*W*0.42);by.push(H*0.5+Math.sin(ang)*rad*H*0.42);}' +
  'var ctx=k.ctx;ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,t=k.t,i,x,y,rr,dx,dy,d,f,g;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);' +
  'ctx.globalCompositeOperation="lighter";' +
  'for(i=0;i<C.n;i++){' +
  'x=bx[i]+(k.noise(i*11.3,0,t)-0.5)*2*amp;y=by[i]+(k.noise(i*11.3+50,0,t)-0.5)*2*amp;' +
  'rr=R*(0.82+0.32*k.noise(i*7.1,3.3,t));' +
  'if(k.mx!==null){dx=k.mx-x;dy=k.my-y;d=Math.sqrt(dx*dx+dy*dy);if(d<rr*0.9&&d>0.5){f=(1-d/(rr*0.9))*amp;x+=dx/d*f;y+=dy/d*f;}}' +
  'g=ctx.createRadialGradient(x,y,0,x,y,rr);g.addColorStop(0,"rgba("+C.pal[i%C.pal.length]+",0.85)");g.addColorStop(1,"rgba("+C.pal[i%C.pal.length]+",0)");' +
  'ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,rr,0,6.2832);ctx.fill();}' +
  'ctx.globalCompositeOperation="source-over";}' +
  '_a2uiCK.mount("gm-%%UID%%",{init:init,draw:draw,speed:C.spd,interactive:C.inter,still:180});' +
  '})();';
_RENDERERS['gradient_mesh_live'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var bg = _ffHex(b.background, '#070a12');
  var pal = _ffPal(b.colors, _FF_DEFAULT_PAL);
  var n     = _ffPick(b.density, {low: '3', normal: '4', high: '6'}, 'normal');
  var spd   = _ffPick(b.speed,   {slow: '0.5', normal: '1', fast: '1.8'}, 'normal');
  var amp   = _ffPick(b.motion,  {subtle: '0.14', normal: '0.22', wild: '0.34'}, 'normal');
  var align = _ffPick(b.align,   {left: 'left', center: 'center', right: 'right'}, 'left');
  var height = _ffInt(b.height, 360, 200, 900);
  var inter = b.interactive === false ? 'false' : 'true';
  var title = b.title || '', eyebrow = b.eyebrow || '', body = b.body || '';
  var bgRgb = _ffRgb(bg);
  var cfg = '{n:' + n + ',spd:' + spd + ',amp:' + amp
    + ',pal:["' + pal.join('","') + '"],bg:"' + bg + '",inter:' + inter + '}';
  var text = _ffOverlay(align, bgRgb, pal, eyebrow, title, body);
  return _ffPanel(height, bg, _ffCanvas('gm-' + uid) + text + _ffScript(_GRADIENT_MESH_LIVE_JS, uid, cfg));
};

// wave_terrain (2026-09-19) — a live terrain flyover: ridgeline rows scroll toward
// the viewer while their heights evolve on the shared value-noise field; each
// row is filled with the background so nearer rows occlude farther ones.
// Live sibling of the static, drag-to-rotate isometric_mesh.
var _WAVE_TERRAIN_JS =
  '(function(){' +
  'var C=%%CFG%%;var M=64,PN=[],PX=[],PY=[],sh=0;' +
  'function init(k){PN=[];PX=[];PY=[];var i,s;for(i=0;i<C.pal.length;i++){s=C.pal[i].split(",");PN.push([+s[0],+s[1],+s[2]]);}for(i=0;i<=M;i++){PX.push(0);PY.push(0);}}' +
  'function col(q,al){var L=PN.length,f=q*(L-1),a=Math.floor(f),b=Math.min(L-1,a+1),m=f-a,A=PN[a],B=PN[b];return "rgba("+Math.round(A[0]+(B[0]-A[0])*m)+","+Math.round(A[1]+(B[1]-A[1])*m)+","+Math.round(A[2]+(B[2]-A[2])*m)+","+al.toFixed(3)+")";}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,t=k.t,s=t*24,i0=Math.floor(s),fr=s-i0,hy=H*0.36,j,i,d,q,gy,sc,u,e,h,m,tg;' +
  'tg=k.mx===null?0:k.mx/W-0.5;sh+=(tg-sh)*0.06;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);' +
  'var g=ctx.createLinearGradient(0,hy-H*0.3,0,hy+H*0.04);g.addColorStop(0,"rgba("+C.pal[0]+",0)");g.addColorStop(1,"rgba("+C.pal[0]+",0.22)");ctx.fillStyle=g;ctx.fillRect(0,hy-H*0.3,W,H*0.34);' +
  'ctx.lineJoin="round";' +
  'for(j=C.n;j>=0;j--){i=i0+j;d=(j-fr)/C.n;q=Math.max(0,Math.min(1,1-d));gy=hy+(H*1.02-hy)*q*q;sc=0.2+1.5*q;' +
  'for(m=0;m<=M;m++){u=m/M;e=Math.min(1,Math.abs(u-0.5)*2.4);e=0.1+0.9*Math.pow(e,1.4);h=k.noise(u*C.fx,i*0.21,t*0.6+3.7);' +
  'PX[m]=W*0.5+(u-0.5)*W*sc+sh*W*0.35*(1-q);PY[m]=gy-h*C.amp*H*e*(0.25+q*1.1);}' +
  'ctx.beginPath();ctx.moveTo(PX[0],PY[0]);for(m=1;m<=M;m++)ctx.lineTo(PX[m],PY[m]);ctx.lineTo(PX[M],H+2);ctx.lineTo(PX[0],H+2);ctx.closePath();ctx.fillStyle=C.bg;ctx.fill();' +
  'ctx.beginPath();ctx.moveTo(PX[0],PY[0]);for(m=1;m<=M;m++)ctx.lineTo(PX[m],PY[m]);ctx.strokeStyle=col(q,0.25+0.7*q);ctx.lineWidth=0.7+1.5*q;ctx.stroke();}}' +
  '_a2uiCK.mount("wt-%%UID%%",{init:init,draw:draw,speed:C.spd,interactive:C.inter,still:1});' +
  '})();';
_RENDERERS['wave_terrain'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6);
  var bg = _ffHex(b.background, '#070a12');
  var pal = _ffPal(b.colors, _FF_DEFAULT_PAL);
  var n      = _ffPick(b.density, {low: '22', normal: '34', high: '48'}, 'normal');
  var spd    = _ffPick(b.speed,   {slow: '0.5', normal: '1', fast: '1.8'}, 'normal');
  var amp    = _ffPick(b.relief,  {low: '0.18', normal: '0.3', high: '0.46'}, 'normal');
  var fx     = _ffPick(b.scale,   {fine: '5', normal: '3.2', broad: '2'}, 'normal');
  var align  = _ffPick(b.align,   {left: 'left', center: 'center', right: 'right'}, 'left');
  var height = _ffInt(b.height, 380, 200, 900);
  var inter = b.interactive === false ? 'false' : 'true';
  var title = b.title || '', eyebrow = b.eyebrow || '', body = b.body || '';
  var bgRgb = _ffRgb(bg);
  var cfg = '{n:' + n + ',spd:' + spd + ',amp:' + amp + ',fx:' + fx
    + ',pal:["' + pal.join('","') + '"],bg:"' + bg + '",inter:' + inter + '}';
  var text = _ffOverlay(align, bgRgb, pal, eyebrow, title, body);
  return _ffPanel(height, bg, _ffCanvas('wt-' + uid) + text + _ffScript(_WAVE_TERRAIN_JS, uid, cfg));
};


// ── computed canvas tools: sun_path / great_circle / bezier_easing / tonal_scale ──
// 2026-09-19. Calcs baked into the atom's own script (NOAA solar position,
// haversine + bearings, cubic-bezier evaluation, OKLab tonal ramps) so the
// SERVER only bakes validated inputs: both renderers emit the identical
// script text and the maths runs once, on the client, the same everywhere.
// Numbers are baked through _ffNum (fixed decimals via integer floor, sign
// handled) so GAS and Python never disagree on a float's spelling.
// tests/test_computed_canvas.py. Edit BOTH.
var _SUN_PATH_JS =
  '(function(){' +
  'var C=%%CFG%%;var R=Math.PI/180,D=180/Math.PI;' +
  'function jd(y,m,d){if(m<=2){y--;m+=12;}var A=Math.floor(y/100),B=2-A+Math.floor(A/4);return Math.floor(365.25*(y+4716))+Math.floor(30.6001*(m+1))+d+B-1524.5;}' +
  'function solar(J){var T=(J-2451545)/36525,L0=(280.46646+T*(36000.76983+T*0.0003032))%360,M=357.52911+T*(35999.05029-0.0001537*T),e=0.016708634-T*(0.000042037+0.0000001267*T);' +
  'var Cc=Math.sin(M*R)*(1.914602-T*(0.004817+0.000014*T))+Math.sin(2*M*R)*(0.019993-0.000101*T)+Math.sin(3*M*R)*0.000289;var tl=L0+Cc,om=125.04-1934.136*T,lam=tl-0.00569-0.00478*Math.sin(om*R);' +
  'var e0=23+(26+((21.448-T*(46.815+T*(0.00059-T*0.001813))))/60)/60,eps=e0+0.00256*Math.cos(om*R);var dec=Math.asin(Math.sin(eps*R)*Math.sin(lam*R))*D;' +
  'var y=Math.tan(eps*R/2);y*=y;var eot=4*D*(y*Math.sin(2*L0*R)-2*e*Math.sin(M*R)+4*e*y*Math.sin(M*R)*Math.cos(2*L0*R)-0.5*y*y*Math.sin(4*L0*R)-1.25*e*e*Math.sin(2*M*R));return {dec:dec,eot:eot};}' +
  'function ha(lat,dec,z){var c=(Math.cos(z*R)/(Math.cos(lat*R)*Math.cos(dec*R)))-Math.tan(lat*R)*Math.tan(dec*R);return c>1?null:c<-1?false:Math.acos(c)*D;}' +
  'function alt(lat,dec,h){return Math.asin(Math.sin(lat*R)*Math.sin(dec*R)+Math.cos(lat*R)*Math.cos(dec*R)*Math.cos(h*R))*D;}' +
  'function hm(m){m=((m%1440)+1440)%1440;var h=Math.floor(m/60),mm=Math.floor(m%60);return (h<10?"0":"")+h+":"+(mm<10?"0":"")+mm;}' +
  'var now=new Date(),date=C.date?C.date.split("-").map(Number):[now.getUTCFullYear(),now.getUTCMonth()+1,now.getUTCDate()];' +
  'var tz=C.tz===null?-now.getTimezoneOffset()/60:C.tz;var J=jd(date[0],date[1],date[2]);var s=solar(J+0.5-tz/24);' +
  'var noon=720-4*C.lon-s.eot+tz*60;var H=ha(C.lat,s.dec,90.833),Hc=ha(C.lat,s.dec,96),Hg=ha(C.lat,s.dec,84);' +
  'var rise=H===null||H===false?null:noon-4*H,set=H===null||H===false?null:noon+4*H;var polar=H===null?"polar night":H===false?"midnight sun":null;' +
  'function draw(k){var ctx=k.ctx,W=k.W,H2=k.H,pad=34,x0=pad,x1=W-pad,yh=H2*0.66,amp=H2*0.5;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H2);' +
  'function xa(m){return x0+(x1-x0)*(m/1440);}function ya(a){return yh-a/90*amp;}' +
  'var g=ctx.createLinearGradient(0,0,0,yh);g.addColorStop(0,"rgba("+C.acc+",0.12)");g.addColorStop(1,"rgba("+C.acc+",0)");ctx.fillStyle=g;ctx.fillRect(x0,0,x1-x0,yh);' +
  'if(Hc!==null&&Hc!==false){ctx.fillStyle="rgba("+C.acc+",0.08)";ctx.fillRect(xa(noon-4*Hc),0,xa(noon+4*Hc)-xa(noon-4*Hc),yh);}' +
  'if(Hg!==null&&Hg!==false&&rise!==null){ctx.fillStyle="rgba(251,191,36,0.16)";ctx.fillRect(xa(rise),0,xa(noon-4*Hg)-xa(rise),yh);ctx.fillRect(xa(noon+4*Hg),0,xa(set)-xa(noon+4*Hg),yh);}' +
  'ctx.strokeStyle="rgba("+C.ink+",0.18)";ctx.lineWidth=1;for(var h=0;h<=24;h+=3){var x=xa(h*60);ctx.beginPath();ctx.moveTo(x,yh);ctx.lineTo(x,yh+6);ctx.stroke();ctx.fillStyle="rgba("+C.ink+",0.55)";ctx.font="10px ui-monospace,monospace";ctx.textAlign="center";ctx.textBaseline="top";ctx.fillText((h<10?"0":"")+h,x,yh+9);}' +
  'ctx.strokeStyle="rgba("+C.ink+",0.45)";ctx.beginPath();ctx.moveTo(x0,yh);ctx.lineTo(x1,yh);ctx.stroke();' +
  'ctx.beginPath();for(var m=0;m<=1440;m+=6){var a=alt(C.lat,s.dec,(m-noon)/4);var xx=xa(m),yy=ya(Math.max(-90,a));if(m===0)ctx.moveTo(xx,yy);else ctx.lineTo(xx,yy);}' +
  'ctx.strokeStyle="rgba("+C.acc+",0.35)";ctx.lineWidth=1.5;ctx.stroke();' +
  'ctx.save();ctx.beginPath();ctx.rect(x0,0,x1-x0,yh);ctx.clip();ctx.beginPath();for(var m2=0;m2<=1440;m2+=6){var a2=alt(C.lat,s.dec,(m2-noon)/4);var x2=xa(m2),y2=ya(a2);if(m2===0)ctx.moveTo(x2,y2);else ctx.lineTo(x2,y2);}ctx.strokeStyle="rgb("+C.acc+")";ctx.lineWidth=2.5;ctx.stroke();ctx.restore();' +
  'function mark(m,label,up){if(m===null)return;var x=xa(m);ctx.fillStyle="rgb("+C.acc+")";ctx.beginPath();ctx.arc(x,yh,4,0,6.2832);ctx.fill();ctx.fillStyle="rgba("+C.ink+",0.9)";ctx.font="600 11px system-ui,sans-serif";ctx.textAlign="center";ctx.textBaseline=up?"bottom":"top";ctx.fillText(label+" "+hm(m),x,up?yh-10:yh+24);}' +
  'mark(rise,"rise",true);mark(set,"set",true);' +
  'var na=alt(C.lat,s.dec,0);ctx.fillStyle="rgba("+C.ink+",0.9)";ctx.font="600 11px system-ui,sans-serif";ctx.textAlign="center";ctx.textBaseline="bottom";ctx.fillText("noon "+hm(noon)+" · "+Math.floor(na+0.5)+"°",xa(noon),ya(Math.max(0,na))-12);' +
  'if(C.live){var lm=(now.getUTCHours()*60+now.getUTCMinutes())+tz*60;var la=alt(C.lat,s.dec,(lm-noon)/4),lx=xa(((lm%1440)+1440)%1440),ly=ya(la);' +
  'var gg=ctx.createRadialGradient(lx,ly,0,lx,ly,26);gg.addColorStop(0,"rgba(251,191,36,0.55)");gg.addColorStop(1,"rgba(251,191,36,0)");ctx.fillStyle=gg;ctx.beginPath();ctx.arc(lx,ly,26,0,6.2832);ctx.fill();' +
  'ctx.fillStyle=la>=0?"#fbbf24":"rgba("+C.ink+",0.35)";ctx.beginPath();ctx.arc(lx,ly,7,0,6.2832);ctx.fill();}' +
  'ctx.fillStyle="rgba("+C.ink+",0.9)";ctx.font="700 13px system-ui,sans-serif";ctx.textAlign="left";ctx.textBaseline="top";ctx.fillText(C.label,x0,10);' +
  'ctx.font="11px ui-monospace,monospace";ctx.fillStyle="rgba("+C.ink+",0.6)";var dl=rise===null?polar:hm(set-rise)+" of daylight";ctx.fillText(date[0]+"-"+(date[1]<10?"0":"")+date[1]+"-"+(date[2]<10?"0":"")+date[2]+" · UTC"+(tz>=0?"+":"")+tz+" · "+dl,x0,28);}' +
  '_a2uiCK.mount("sun-%%UID%%",{init:function(){},draw:draw,speed:1,interactive:false,still:1});' +
  'if(C.live&&!(window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches)){setInterval(function(){now=new Date();},60000);}' +
  '})();';
var _GREAT_CIRCLE_JS =
  '(function(){' +
  'var C=%%CFG%%;var R=Math.PI/180,D=180/Math.PI;' +
  'var la1=C.a[0]*R,lo1=C.a[1]*R,la2=C.b[0]*R,lo2=C.b[1]*R;' +
  'var dlat=la2-la1,dlon=lo2-lo1,h=Math.sin(dlat/2)*Math.sin(dlat/2)+Math.cos(la1)*Math.cos(la2)*Math.sin(dlon/2)*Math.sin(dlon/2),ang=2*Math.atan2(Math.sqrt(h),Math.sqrt(1-h));' +
  'var km=6371.0088*ang,nm=km/1.852,mi=km/1.609344;var dist=C.units==="km"?km:C.units==="mi"?mi:nm;' +
  'var brg=(Math.atan2(Math.sin(dlon)*Math.cos(la2),Math.cos(la1)*Math.sin(la2)-Math.sin(la1)*Math.cos(la2)*Math.cos(dlon))*D+360)%360;' +
  'var fb=(Math.atan2(Math.sin(-dlon)*Math.cos(la1),Math.cos(la2)*Math.sin(la1)-Math.sin(la2)*Math.cos(la1)*Math.cos(-dlon))*D+180)%360;' +
  'function ip(f){var A=Math.sin((1-f)*ang)/Math.sin(ang),B=Math.sin(f*ang)/Math.sin(ang);var x=A*Math.cos(la1)*Math.cos(lo1)+B*Math.cos(la2)*Math.cos(lo2),y=A*Math.cos(la1)*Math.sin(lo1)+B*Math.cos(la2)*Math.sin(lo2),z=A*Math.sin(la1)+B*Math.sin(la2);return [Math.atan2(z,Math.sqrt(x*x+y*y))*D,Math.atan2(y,x)*D];}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,mh=H-64,x0=0,y0=0;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);' +
  'function px(lat,lon){return [x0+(lon+180)/360*W,y0+(90-lat)/180*mh];}' +
  'ctx.strokeStyle="rgba("+C.ink+",0.14)";ctx.lineWidth=1;for(var lo=-180;lo<=180;lo+=30){var p=px(0,lo);ctx.beginPath();ctx.moveTo(p[0],y0);ctx.lineTo(p[0],y0+mh);ctx.stroke();}' +
  'for(var la=-60;la<=60;la+=30){var q=px(la,0);ctx.beginPath();ctx.moveTo(x0,q[1]);ctx.lineTo(W,q[1]);ctx.stroke();}' +
  'var eq=px(0,0);ctx.strokeStyle="rgba("+C.ink+",0.3)";ctx.beginPath();ctx.moveTo(x0,eq[1]);ctx.lineTo(W,eq[1]);ctx.stroke();' +
  'ctx.strokeStyle="rgb("+C.acc+")";ctx.lineWidth=2.2;ctx.lineJoin="round";ctx.beginPath();var prev=null;' +
  'for(var i=0;i<=96;i++){var g=ang<1e-9?[C.a[0],C.a[1]]:ip(i/96),pt=px(g[0],g[1]);if(prev&&Math.abs(pt[0]-prev[0])>W/2){ctx.stroke();ctx.beginPath();ctx.moveTo(pt[0],pt[1]);}else if(!prev)ctx.moveTo(pt[0],pt[1]);else ctx.lineTo(pt[0],pt[1]);prev=pt;}' +
  'ctx.stroke();' +
  'var mid=ang<1e-9?[C.a[0],C.a[1]]:ip(0.5),mp=px(mid[0],mid[1]);' +
  'function node(lat,lon,label,al){var p=px(lat,lon);ctx.fillStyle=C.bg;ctx.beginPath();ctx.arc(p[0],p[1],6,0,6.2832);ctx.fill();ctx.strokeStyle="rgb("+C.acc+")";ctx.lineWidth=2;ctx.stroke();ctx.fillStyle="rgb("+C.acc+")";ctx.beginPath();ctx.arc(p[0],p[1],2.5,0,6.2832);ctx.fill();' +
  'ctx.fillStyle="rgba("+C.ink+",0.95)";ctx.font="600 11px system-ui,sans-serif";ctx.textAlign=al;ctx.textBaseline="bottom";ctx.fillText(label,p[0]+(al==="left"?9:-9),p[1]-6);}' +
  'node(C.a[0],C.a[1],C.al,"right");node(C.b[0],C.b[1],C.bl,"left");' +
  'ctx.fillStyle="rgba("+C.acc+",0.9)";ctx.beginPath();ctx.arc(mp[0],mp[1],3,0,6.2832);ctx.fill();' +
  'var u=C.units;ctx.fillStyle="rgba("+C.ink+",0.95)";ctx.font="800 22px system-ui,sans-serif";ctx.textAlign="left";ctx.textBaseline="top";ctx.fillText(Math.floor(dist+0.5).toLocaleString()+" "+u,14,y0+mh+12);' +
  'ctx.font="11px ui-monospace,monospace";ctx.fillStyle="rgba("+C.ink+",0.62)";ctx.fillText("great circle · initial bearing "+(Math.floor(brg+0.5)%360)+"° · final "+(Math.floor(fb+0.5)%360)+"° · "+Math.floor(km+0.5).toLocaleString()+" km · midpoint "+mid[0].toFixed(1)+", "+mid[1].toFixed(1),14,y0+mh+40);' +
  'var cx=W-40,cy=y0+mh+32,r=22;ctx.strokeStyle="rgba("+C.ink+",0.35)";ctx.lineWidth=1;ctx.beginPath();ctx.arc(cx,cy,r,0,6.2832);ctx.stroke();' +
  'ctx.fillStyle="rgba("+C.ink+",0.6)";ctx.font="9px ui-monospace,monospace";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText("N",cx,cy-r-7);' +
  'var bx=cx+Math.sin(brg*R)*r*0.85,by=cy-Math.cos(brg*R)*r*0.85;ctx.strokeStyle="rgb("+C.acc+")";ctx.lineWidth=2.5;ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(bx,by);ctx.stroke();ctx.fillStyle="rgb("+C.acc+")";ctx.beginPath();ctx.arc(bx,by,3,0,6.2832);ctx.fill();}' +
  '_a2uiCK.mount("gc-%%UID%%",{init:function(){},draw:draw,speed:1,interactive:false,still:1});' +
  '})();';
var _BEZIER_EASING_JS =
  '(function(){' +
  'var C=%%CFG%%;var P=[C.x1,C.y1,C.x2,C.y2],drag=-1,run=true,t0=0;' +
  'var host=document.getElementById("bz-%%UID%%"),lab=document.getElementById("bzl-%%UID%%"),ball=document.getElementById("bzb-%%UID%%"),cv=null;' +
  'var RM=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;' +
  'function bez(a,b,t){var u=1-t;return 3*u*u*t*a+3*u*t*t*b+t*t*t;}' +
  'function solve(x){var lo=0,hi=1,t=x;for(var i=0;i<24;i++){t=(lo+hi)/2;if(bez(P[0],P[2],t)<x)lo=t;else hi=t;}return t;}' +
  'function css(){return "cubic-bezier("+P.map(function(v){return Math.floor(v*1000+0.5)/1000;}).join(", ")+")";}' +
  'function apply(){if(lab)lab.textContent=css();}' +
  'function draw(k){var ctx=k.ctx,W=k.W,H=k.H,m=28,gw=W-2*m,gh=H*0.62,gy=H*0.19+gh;cv=k;' +
  'ctx.globalCompositeOperation="source-over";ctx.fillStyle=C.bg;ctx.fillRect(0,0,W,H);' +
  'function X(x){return m+x*gw;}function Y(y){return gy-y*gh;}' +
  'ctx.strokeStyle="rgba("+C.ink+",0.12)";ctx.lineWidth=1;for(var i=0;i<=4;i++){ctx.beginPath();ctx.moveTo(X(i/4),Y(0));ctx.lineTo(X(i/4),Y(1));ctx.stroke();ctx.beginPath();ctx.moveTo(X(0),Y(i/4));ctx.lineTo(X(1),Y(i/4));ctx.stroke();}' +
  'ctx.strokeStyle="rgba("+C.ink+",0.35)";ctx.strokeRect(X(0),Y(1),gw,gh);' +
  'ctx.setLineDash([4,4]);ctx.strokeStyle="rgba("+C.ink+",0.25)";ctx.beginPath();ctx.moveTo(X(0),Y(0));ctx.lineTo(X(1),Y(1));ctx.stroke();ctx.setLineDash([]);' +
  'ctx.strokeStyle="rgba("+C.acc+",0.5)";ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(X(0),Y(0));ctx.lineTo(X(P[0]),Y(P[1]));ctx.stroke();ctx.beginPath();ctx.moveTo(X(1),Y(1));ctx.lineTo(X(P[2]),Y(P[3]));ctx.stroke();' +
  'ctx.strokeStyle="rgb("+C.acc+")";ctx.lineWidth=3;ctx.beginPath();for(var j=0;j<=80;j++){var t=j/80,x=bez(P[0],P[2],t),y=bez(P[1],P[3],t);if(j===0)ctx.moveTo(X(x),Y(y));else ctx.lineTo(X(x),Y(y));}ctx.stroke();' +
  'for(var h=0;h<2;h++){var hx=X(P[h*2]),hy=Y(P[h*2+1]);ctx.fillStyle=C.bg;ctx.beginPath();ctx.arc(hx,hy,7,0,6.2832);ctx.fill();ctx.strokeStyle="rgb("+C.acc+")";ctx.lineWidth=2;ctx.stroke();ctx.fillStyle=drag===h?"rgb("+C.acc+")":"rgba("+C.acc+",0.4)";ctx.beginPath();ctx.arc(hx,hy,3.5,0,6.2832);ctx.fill();}' +
  'if(run&&!RM){var el=((Date.now()-t0)%(C.dur+600))/C.dur,pr=Math.min(1,el),tt=solve(pr),py=bez(P[1],P[3],tt);ctx.fillStyle="rgb("+C.acc+")";ctx.beginPath();ctx.arc(X(pr),Y(py),5,0,6.2832);ctx.fill();' +
  'if(ball)ball.style.transform="translateX("+(py*100)+"%)";}' +
  'ctx.fillStyle="rgba("+C.ink+",0.5)";ctx.font="10px ui-monospace,monospace";ctx.textAlign="left";ctx.textBaseline="top";ctx.fillText("time →",X(0),Y(0)+6);ctx.save();ctx.translate(X(0)-8,Y(1));ctx.rotate(-Math.PI/2);ctx.textAlign="right";ctx.fillText("progress →",0,0);ctx.restore();}' +
  'if(C.edit&&host){var c=host.querySelector("canvas");' +
  'function pos(e){var r=c.getBoundingClientRect();var W=r.width,H=r.height,m=28,gw=W-2*m,gh=H*0.62,gy=H*0.19+gh;return [(e.clientX-r.left-m)/gw,(gy-(e.clientY-r.top))/gh];}' +
  'host.addEventListener("pointerdown",function(e){var p=pos(e),best=-1,bd=0.08;for(var h=0;h<2;h++){var d=Math.sqrt(Math.pow(p[0]-P[h*2],2)+Math.pow(p[1]-P[h*2+1],2));if(d<bd){bd=d;best=h;}}drag=best;if(drag>=0){e.preventDefault();try{host.setPointerCapture(e.pointerId);}catch(x){}}});' +
  'host.addEventListener("pointermove",function(e){if(drag<0)return;var p=pos(e);P[drag*2]=Math.max(0,Math.min(1,p[0]));P[drag*2+1]=Math.max(-1,Math.min(2,p[1]));apply();});' +
  'host.addEventListener("pointerup",function(){drag=-1;});host.addEventListener("pointercancel",function(){drag=-1;});}' +
  't0=Date.now();apply();' +
  '_a2uiCK.mount("bzc-%%UID%%",{init:function(){},draw:draw,speed:1,interactive:false,still:1});' +
  '})();';
var _TONAL_SCALE_JS =
  '(function(){' +
  'var C=%%CFG%%;var host=document.getElementById("tn-%%UID%%"),code=document.getElementById("tnc-%%UID%%");if(!host)return;' +
  'function lin(c){c/=255;return c<=0.04045?c/12.92:Math.pow((c+0.055)/1.055,2.4);}' +
  'function gam(c){c=Math.max(0,Math.min(1,c));return c<=0.0031308?c*12.92:1.055*Math.pow(c,1/2.4)-0.055;}' +
  'function toLab(r,g,b){var R=lin(r),G=lin(g),B=lin(b);var l=Math.cbrt(0.4122214708*R+0.5363325363*G+0.0514459929*B),m=Math.cbrt(0.2119034982*R+0.6806995451*G+0.1073969566*B),s=Math.cbrt(0.0883024619*R+0.2817188376*G+0.6299787005*B);' +
  'return [0.2104542553*l+0.7936177850*m-0.0040720468*s,1.9779984951*l-2.4285922050*m+0.4505937099*s,0.0259040371*l+0.7827717662*m-0.8086757660*s];}' +
  'function toRgb(L,a,b){var l=L+0.3963377774*a+0.2158037573*b,m=L-0.1055613458*a-0.0638541728*b,s=L-0.0894841775*a-1.2914855480*b;l=l*l*l;m=m*m*m;s=s*s*s;' +
  'return [4.0767416621*l-3.3077115913*m+0.2309699292*s,-1.2684380046*l+2.6097574011*m-0.3413193965*s,-0.0041960863*l-0.7034186147*m+1.7076147010*s];}' +
  'function inG(c){return c[0]>=-0.001&&c[0]<=1.001&&c[1]>=-0.001&&c[1]<=1.001&&c[2]>=-0.001&&c[2]<=1.001;}' +
  'function hex(c){var s="#";for(var i=0;i<3;i++){var v=Math.floor(gam(c[i])*255+0.5);s+=(v<16?"0":"")+v.toString(16);}return s;}' +
  'function lum(c){return 0.2126*Math.max(0,Math.min(1,c[0]))+0.7152*Math.max(0,Math.min(1,c[1]))+0.0722*Math.max(0,Math.min(1,c[2]));}' +
  'function el(tag,st,txt){var e=document.createElement(tag);for(var k in st)e.style[k]=st[k];if(txt!==undefined)e.textContent=txt;return e;}' +
  'var r=parseInt(C.hex.slice(1,3),16),g=parseInt(C.hex.slice(3,5),16),b=parseInt(C.hex.slice(5,7),16),lab=toLab(r,g,b),L0=lab[0],chroma=Math.sqrt(lab[1]*lab[1]+lab[2]*lab[2]),hue=Math.atan2(lab[2],lab[1]);' +
  'var n=C.steps,NL=String.fromCharCode(10),vars=":root {";host.innerHTML="";' +
  'for(var i=0;i<n;i++){var f=i/(n-1),L=0.975-f*0.83,cs=chroma*(1-Math.pow(Math.abs(L-0.55)/0.55,1.6)*0.85),c=cs,rgb;' +
  'for(var k=0;k<24;k++){rgb=toRgb(L,c*Math.cos(hue),c*Math.sin(hue));if(inG(rgb))break;c*=0.9;}' +
  'var hx=hex(rgb),y=lum(rgb),cw=1.05/(y+0.05),cb=(y+0.05)/0.05,tone=Math.floor(50+f*850+0.5),tx=cw>=cb?"#ffffff":"#0f172a",near=Math.abs(L-L0)<0.045;' +
  'var sw=el("div",{flex:"1 1 0",minWidth:"0",background:hx,color:tx,padding:"14px 6px 10px",textAlign:"center",fontFamily:"ui-monospace,monospace",fontSize:"10px",lineHeight:"1.4"});sw.title=hx;' +
  'if(near){sw.style.outline="2px solid "+tx;sw.style.outlineOffset="-4px";}' +
  'sw.appendChild(el("div",{fontWeight:"700",fontSize:"11px"},""+tone));sw.appendChild(el("div",{},hx));' +
  'if(C.contrast)sw.appendChild(el("div",{opacity:"0.8"},(Math.floor(Math.max(cw,cb)*10+0.5)/10)+":1"));' +
  'host.appendChild(sw);vars+=NL+"  --"+C.name+"-"+tone+": "+hx+";";}' +
  'if(code)code.textContent=vars+NL+"}";' +
  '})();';
function _ffNum(v, dflt, lo, hi, places) {
  var x = typeof v === 'number' ? v : parseFloat(v);
  if (isNaN(x)) x = dflt;
  x = Math.max(lo, Math.min(hi, x));
  var m = Math.pow(10, places), n = Math.floor(Math.abs(x) * m + 0.5), ip = Math.floor(n / m), fp = '' + (n % m);
  while (fp.length < places) fp = '0' + fp;
  fp = fp.replace(/0+$/, '');
  return (x < 0 && n > 0 ? '-' : '') + ip + (fp ? '.' + fp : '');
}
function _ffTheme(b) { return _ffPick(b.theme, _CV_THEMES, 'dark'); }
function _ffJsStr(s, max, dflt) { return _ffLinesJs([(typeof s === 'string' ? s.trim().slice(0, max) : '') || dflt]).slice(1, -1); }

_RENDERERS['sun_path'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6), th = _ffTheme(b), acc = _ffHex(b.accent, '#38bdf8');
  var lat = _ffNum(b.lat, 48.8566, -90, 90, 4), lon = _ffNum(b.lon, 2.3522, -180, 180, 4);
  var date = (typeof b.date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(b.date)) ? b.date : '';
  var tz = (b.tz === 'local' || b.tz === undefined || b.tz === null) ? 'null' : _ffNum(b.tz, 0, -12, 14, 2);
  var height = _ffInt(b.height, 300, 200, 600), live = b.live === false ? 'false' : 'true';
  var cfg = '{lat:' + lat + ',lon:' + lon + ',date:"' + date + '",tz:' + tz + ',label:' + _ffJsStr(b.label, 40, 'Sun') + ',bg:"' + th.bg + '",ink:"' + _ffRgb(th.ink) + '",acc:"' + _ffRgb(acc) + '",live:' + live + '}';
  return _ffPanel(height, th.bg, _ffCanvas('sun-' + uid) + _ffScript(_SUN_PATH_JS, uid, cfg));
};

_RENDERERS['great_circle'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6), th = _ffTheme(b), acc = _ffHex(b.accent, '#38bdf8');
  var f = b.from && typeof b.from === 'object' ? b.from : {}, t = b.to && typeof b.to === 'object' ? b.to : {};
  var a = [_ffNum(f.lat, 51.47, -90, 90, 4), _ffNum(f.lon, -0.4614, -180, 180, 4)], c = [_ffNum(t.lat, 40.6413, -90, 90, 4), _ffNum(t.lon, -73.7781, -180, 180, 4)];
  var units = _ffPick(b.units, {nm: 'nm', km: 'km', mi: 'mi'}, 'nm'), height = _ffInt(b.height, 320, 240, 600);
  var cfg = '{a:[' + a.join(',') + '],b:[' + c.join(',') + '],al:' + _ffJsStr(f.label, 24, 'A') + ',bl:' + _ffJsStr(t.label, 24, 'B') + ',units:"' + units + '",bg:"' + th.bg + '",ink:"' + _ffRgb(th.ink) + '",acc:"' + _ffRgb(acc) + '"}';
  return _ffPanel(height, th.bg, _ffCanvas('gc-' + uid) + _ffScript(_GREAT_CIRCLE_JS, uid, cfg));
};

var _BZ_PRESETS = {ease: [0.25, 0.1, 0.25, 1], 'ease-in': [0.42, 0, 1, 1], 'ease-out': [0, 0, 0.58, 1], 'ease-in-out': [0.42, 0, 0.58, 1], overshoot: [0.34, 1.56, 0.64, 1], anticipate: [0.68, -0.55, 0.27, 1.55]};
_RENDERERS['bezier_easing'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6), th = _ffTheme(b), acc = _ffHex(b.accent, '#38bdf8');
  var pre = (typeof b.preset === 'string' && Object.prototype.hasOwnProperty.call(_BZ_PRESETS, b.preset)) ? _BZ_PRESETS[b.preset] : null;
  var P = pre ? [_ffNum(pre[0], 0, 0, 1, 3), _ffNum(pre[1], 0, -1, 2, 3), _ffNum(pre[2], 0, 0, 1, 3), _ffNum(pre[3], 0, -1, 2, 3)]
    : [_ffNum(b.x1, 0.25, 0, 1, 3), _ffNum(b.y1, 0.1, -1, 2, 3), _ffNum(b.x2, 0.25, 0, 1, 3), _ffNum(b.y2, 1, -1, 2, 3)];
  var dur = _ffInt(b.duration, 1200, 200, 4000), edit = b.editable === false ? 'false' : 'true', height = _ffInt(b.height, 300, 200, 500);
  var label = typeof b.label === 'string' ? b.label.trim().slice(0, 60) : '';
  var cfg = '{x1:' + P[0] + ',y1:' + P[1] + ',x2:' + P[2] + ',y2:' + P[3] + ',dur:' + dur + ',edit:' + edit + ',bg:"' + th.bg + '",ink:"' + _ffRgb(th.ink) + '",acc:"' + _ffRgb(acc) + '"}';
  var cssStr = 'cubic-bezier(' + P.join(', ') + ')';
  return '<div style="margin:1rem 0;border-radius:16px;overflow:hidden;background:' + th.bg + ';border:1px solid ' + th.line + ';">'
    + '<div id="bz-' + uid + '" style="position:relative;height:' + height + 'px;touch-action:none;cursor:' + (edit === 'true' ? 'crosshair' : 'default') + ';">' + _ffCanvas('bzc-' + uid) + '</div>'
    + '<div style="padding:12px 16px 14px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;color:' + th.ink + ';">'
    + '<div style="flex:1 1 180px;height:10px;border-radius:5px;background:' + th.line + ';position:relative;"><div id="bzb-' + uid + '" style="position:absolute;top:-5px;left:0;width:calc(100% - 20px);height:20px;pointer-events:none;"><div style="width:20px;height:20px;border-radius:50%;background:' + acc + ';"></div></div></div>'
    + '<code id="bzl-' + uid + '" style="font-family:' + _CV_VOICES.mono + ';font-size:0.78rem;color:' + th.mute + ';">' + cssStr + '</code>'
    + (label ? '<span style="font-size:0.8rem;color:' + th.mute + ';">' + _esc(label) + '</span>' : '')
    + '</div>' + _ffScript(_BEZIER_EASING_JS, uid, cfg) + '</div>';
};

_RENDERERS['tonal_scale'] = function(b) {
  var uid = Math.random().toString(36).substr(2, 6), th = _ffTheme(b);
  var hex = _ffHex(b.accent, '#0e7bb8'), steps = _ffInt(b.steps, 11, 5, 13);
  var name = (typeof b.name === 'string' && /^[a-z][a-z0-9-]{0,19}$/.test(b.name)) ? b.name : 'accent';
  var contrast = b.show_contrast === false ? 'false' : 'true', showCode = b.show_code === false ? false : true;
  var cfg = '{hex:"' + hex + '",steps:' + steps + ',name:"' + name + '",contrast:' + contrast + '}';
  var inner = '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:12px;">'
    + '<div style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:' + th.mute + ';">tonal scale · OKLCH</div>'
    + '<div style="font-family:' + _CV_VOICES.mono + ';font-size:0.78rem;color:' + th.mute + ';">' + hex + ' · ' + steps + ' tones</div></div>'
    + '<div id="tn-' + uid + '" style="display:flex;border-radius:10px;overflow:hidden;min-height:72px;border:1px solid ' + th.line + ';"><div style="flex:1;background:' + hex + ';"></div></div>'
    + (showCode ? '<pre id="tnc-' + uid + '" style="margin:14px 0 0;padding:12px 14px;border-radius:8px;background:' + th.soft + ';border:1px solid ' + th.line + ';font-family:' + _CV_VOICES.mono + ';font-size:0.72rem;line-height:1.5;color:' + th.ink + ';overflow-x:auto;">:root {\n  --' + name + '-500: ' + hex + ';\n}</pre>' : '')
    + '<script>' + _TONAL_SCALE_JS.replace(/%%UID%%/g, uid).replace(/%%CFG%%/g, function() { return cfg; }) + '<\/script>';
  return _cvCard(th, inner);
};
