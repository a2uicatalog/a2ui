// atoms_brick.gs — brick_build_3d: equation-driven LEGO-style models that assemble stud by stud
// Zero dependencies. Pure canvas 2D + requestAnimationFrame. GAS CSP-safe. Surfaces: G M W
//
// A software 3D pipeline (perspective projection, backface culling, depth-sorted faces, Lambert shading,
// projected shadows) in real LEGO proportions: 8 mm stud pitch, 9.6 mm brick, 3.2 mm plate, 4.8 mm stud.
// Models are either a named shape (implicit surfaces voxelised to the stud grid, tiled with running-bond
// bricks and trimmed until every brick is anchored) or an explicit `bricks` array from an agent.
//
// Nothing about a design is taken on trust: validate() runs deterministic geometry checks (collisions,
// anchoring through stud connections, connection count, centre of mass over the ground footprint) and the
// atom shows the verdict beside the model. The same checks exist in Python (renderers/brick_validate.py)
// and tests/fixtures/bricks/parity_cases.json keeps the two in lockstep.
//
// _brickKit() holds ALL the logic and no DOM access outside create(), so the renderer can serialise it into
// the page with Function.prototype.toString (no string escaping of a 400-line engine) and Node can load it
// straight from this file for the parity test (scripts/test_brick_validate_js.mjs).
//
// Fields:
//   shape      — heart | sphere | torus | helix | pyramid | house (default heart). Ignored when bricks is set.
//   bricks     — explicit model: [{x,y,z,w,d,h,c}] (stud x/z, layer y, footprint w×d, height h in bricks,
//                hex colour c). Bound values arrive already resolved ({path:'/bricks'} → the array).
//   mode       — animate | steps (default animate)
//   step       — initial instruction step in steps mode (default 1)
//   speed      — animation speed multiplier (default 1)
//   orbit      — slow auto-orbit (default true); dragging always orbits
//   height     — canvas height px (default 380)
//   bg         — canvas background colour; transparent on the studio gradient when omitted
//   scrubber   — show the animate/instructions toggle and step slider (default true)
//   checks     — show the build-check verdicts (default true)
//   parts      — show the parts list with an indicative cost (default false)

function _brickKit() {
  /* ---------- constants: real LEGO proportions, in stud-pitch units (1 = 8 mm) ---------- */
  var BH=1.2, PL=0.4, SR=0.3, SH=0.18, SN=10;         // brick 9.6mm, plate 3.2mm, stud r 2.4mm, stud h 1.4mm
  var RB=['#c91a09','#fe8a18','#f2cd37','#a5ca18','#237841','#36aebf','#0055bf','#6a3a9c'];
  var LD=(function(){var v=[-0.5,1,0.6],l=Math.hypot(v[0],v[1],v[2]);return v.map(function(x){return x/l;});})();
  var COS=[],SIN=[];for(var s=0;s<SN;s++){COS.push(Math.cos(2*Math.PI*s/SN));SIN.push(Math.sin(2*Math.PI*s/SN));}

  var shadeCache={};
  function shade(hex,q){
    var qi=Math.round(q*40),k=hex+qi,c=shadeCache[k];if(c)return c;
    var m=qi/40,r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
    c='rgb('+Math.min(255,r*m|0)+','+Math.min(255,g*m|0)+','+Math.min(255,b*m|0)+')';
    return shadeCache[k]=c;
  }

  /* ---------- models: implicit surfaces voxelised to stud grid, merged to running-bond bricks ---------- */
  function tileLayers(fn,b){
    // Tile each layer with 1-4 stud runs, paired to 2 deep where possible. Run boundaries shift by 2 studs in x
    // and by 1 stud in z on alternate layers, so every layer overlaps the one below in both directions.
    var out=[];
    for(var y=b[2];y<=b[3];y++){
      var taken={},par=(y&1)*2,zp=y&1;
      for(var z=b[4];z<=b[5];z++)for(var x=b[0];x<=b[1];x++){
        if(taken[x+','+z])continue;
        var c=fn(x,y,z);if(!c)continue;
        var e=x+1;
        while(e<=b[1]&&e-x<4&&(e+par)%4!==0&&fn(e,y,z)===c&&!taken[e+','+z])e++;
        var d=1;
        if(((z+zp)%2+2)%2===0&&z+1<=b[5]){
          var e2=x;                                   // pair only as far as the row behind has the same colour
          while(e2<e&&fn(e2,y,z+1)===c&&!taken[e2+','+(z+1)])e2++;
          if(e2>x){e=e2;d=2;}
        }
        for(var zz=z;zz<z+d;zz++)for(var q2=x;q2<e;q2++)taken[q2+','+zz]=1;
        out.push({x:x,y:y,z:z,w:e-x,d:d,h:1,c:c});
      }
    }
    return out;
  }
  // bricks with no stud path to the lowest layer (raw, un-normalised coordinates)
  function unanchored(bricks,b){
    var owner={},adj=bricks.map(function(){return [];}),seen={},queue=[],out=[],y0=1e9;
    bricks.forEach(function(br){y0=Math.min(y0,br.y);});
    function K(x,y,z){return ckey(x-b[0],y-b[2],z-b[4]);}
    bricks.forEach(function(br,i){for(var z=br.z;z<br.z+br.d;z++)for(var x=br.x;x<br.x+br.w;x++)owner[K(x,br.y,z)]=i;});
    bricks.forEach(function(br,i){
      if(br.y===y0){seen[i]=1;queue.push(i);return;}
      for(var z=br.z;z<br.z+br.d;z++)for(var x=br.x;x<br.x+br.w;x++){
        var j=owner[K(x,br.y-1,z)];if(j!==undefined){adj[i].push(j);adj[j].push(i);}
      }
    });
    while(queue.length){var c=queue.pop();adj[c].forEach(function(n){if(!seen[n]){seen[n]=1;queue.push(n);}});}
    bricks.forEach(function(br,i){if(!seen[i])out.push(i);});
    return out;
  }
  // Tile, then trim cells that end up on unanchored bricks and re-tile until stable, the way a designer
  // would shave an unsupported sliver off a model. `trimmed` reports how many cells were removed.
  function voxelBricks(fn,b){
    var cut={},trimmed=0,bricks,pass=0,fl;
    function f(x,y,z){return cut[x+','+y+','+z]?null:fn(x,y,z);}
    do{
      bricks=tileLayers(f,b);
      fl=unanchored(bricks,b);
      fl.forEach(function(i){var br=bricks[i];
        for(var z=br.z;z<br.z+br.d;z++)for(var x=br.x;x<br.x+br.w;x++){cut[x+','+br.y+','+z]=1;trimmed++;}});
    }while(fl.length&&++pass<8);
    bricks.trimmed=trimmed;
    return bricks;
  }
  function normalise(bricks){
    if(!bricks.length)throw new Error('a model needs at least one brick');
    var mx=1e9,my=1e9,mz=1e9;
    bricks.forEach(function(b){mx=Math.min(mx,b.x);my=Math.min(my,b.y);mz=Math.min(mz,b.z);});
    var W=0,D=0,L=0;
    bricks.forEach(function(b){b.x-=mx;b.y-=my;b.z-=mz;W=Math.max(W,b.x+b.w);D=Math.max(D,b.z+b.d);L=Math.max(L,b.y+b.h);});
    bricks.sort(function(a,b){
      if(a.y!==b.y)return a.y-b.y;
      return Math.atan2(a.z+a.d/2-D/2,a.x+a.w/2-W/2)-Math.atan2(b.z+b.d/2-D/2,b.x+b.w/2-W/2);
    });
    var step=0,lastY=-1,cnt=0;                      // instruction steps: one layer at a time, at most 6 bricks each
    bricks.forEach(function(b){if(b.y!==lastY||cnt>=6){step++;cnt=0;lastY=b.y;}b.step=step;cnt++;});
    return {bricks:bricks,W:W,D:D,L:L,steps:step};
  }

  /* ---------- validator: pure function of a brick list, no rendering state ---------- */
  var PALNAME={'#c91a09':'red','#fe8a18':'orange','#f2cd37':'yellow','#a5ca18':'lime','#237841':'green','#36aebf':'azure',
    '#0055bf':'blue','#6a3a9c':'purple','#f2f3f2':'white','#1b2a34':'black','#6b2f1a':'brown','#e4adc8':'pink'};
  function ckey(x,y,z){return (y*4096+z)*4096+x;}
  function hull2(pts){
    pts=pts.slice().sort(function(a,b){return a[0]-b[0]||a[1]-b[1];});
    function cr(o,a,b){return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);}
    var lo=[],up=[],i;
    for(i=0;i<pts.length;i++){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],pts[i])<=0)lo.pop();lo.push(pts[i]);}
    for(i=pts.length-1;i>=0;i--){while(up.length>=2&&cr(up[up.length-2],up[up.length-1],pts[i])<=0)up.pop();up.push(pts[i]);}
    lo.pop();up.pop();return lo.concat(up);
  }
  function validate(bricks){
    if(!bricks.length)throw new Error('a model needs at least one brick');
    var owner={},overlapCells=0,pairs={},adj=bricks.map(function(){return {};}),conn=0,i,x,y,z;
    bricks.forEach(function(b,i){
      for(y=b.y;y<b.y+b.h;y++)for(z=b.z;z<b.z+b.d;z++)for(x=b.x;x<b.x+b.w;x++){
        var k=ckey(x,y,z);
        if(owner[k]!==undefined){overlapCells++;pairs[Math.min(i,owner[k])+'-'+Math.max(i,owner[k])]=1;}else owner[k]=i;
      }
    });
    var grounded=[];
    bricks.forEach(function(b,i){
      for(z=b.z;z<b.z+b.d;z++)for(x=b.x;x<b.x+b.w;x++){
        if(b.y===0){conn++;grounded.push(i);continue;}       // studs of the baseplate
        var j=owner[ckey(x,b.y-1,z)];
        if(j!==undefined&&j!==i){conn++;adj[i][j]=1;adj[j][i]=1;}
      }
    });
    var seen={},queue=[];
    grounded.forEach(function(g){if(!seen[g]){seen[g]=1;queue.push(g);}});
    while(queue.length){var c=queue.pop();for(var n in adj[c])if(!seen[n]){seen[n]=1;queue.push(+n);}}
    var floating=0;for(i=0;i<bricks.length;i++)if(!seen[i])floating++;
    var m=0,cx=0,cz=0,foot=[];
    bricks.forEach(function(b){var v=b.w*b.d*b.h;m+=v;cx+=(b.x+b.w/2)*v;cz+=(b.z+b.d/2)*v;
      if(b.y===0)foot.push([b.x,b.z],[b.x+b.w,b.z],[b.x+b.w,b.z+b.d],[b.x,b.z+b.d]);});
    cx/=m;cz/=m;
    var margin=-1;
    if(foot.length){
      var hp=hull2(foot);margin=1e9;
      for(i=0;i<hp.length;i++){var a=hp[i],bb=hp[(i+1)%hp.length];
        margin=Math.min(margin,((bb[0]-a[0])*(cz-a[1])-(bb[1]-a[1])*(cx-a[0]))/Math.hypot(bb[0]-a[0],bb[1]-a[1]));}
    }
    var partMap={};
    bricks.forEach(function(b){
      var col=PALNAME[b.c]||b.c,key=b.w+'×'+b.d+'|'+col;
      (partMap[key]=partMap[key]||{size:b.w+'×'+b.d,colour:col,hex:b.c,count:0,unit:0.03+0.04*b.w*b.d}).count++;
    });
    var parts=Object.keys(partMap).map(function(k){var p=partMap[k];p.line=p.count*p.unit;return p;})
      .sort(function(a,b){return b.count-a.count;});
    var cost=parts.reduce(function(s,p){return s+p.line;},0);
    var np=Object.keys(pairs).length;
    var checks=[
      {id:'collisions',label:'No collisions',status:np?'fail':'pass',
        detail:np?np+' brick pair'+(np>1?'s':'')+' share '+overlapCells+' stud cell'+(overlapCells>1?'s':''):'0 shared cells'},
      {id:'anchored',label:'Every brick anchored',status:floating?'fail':'pass',
        detail:floating?floating+' brick'+(floating>1?'s':'')+' not connected to the baseplate':'all '+bricks.length+' bricks reach the baseplate'},
      {id:'connections',label:'Stud connections',status:conn?'pass':'fail',detail:conn+' engaged'},
      {id:'balance',label:'Centre of mass over footprint',status:margin<0?'fail':margin<0.5?'warn':'pass',
        detail:'('+cx.toFixed(1)+', '+cz.toFixed(1)+') · '+(margin<0?'outside by ':'margin ')+Math.abs(margin).toFixed(2)+' studs'}
    ];
    return {ok:checks.every(function(c){return c.status!=='fail';}),checks:checks,connections:conn,
      overlaps:np,floating:floating,com:{x:cx,z:cz,margin:margin},parts:parts,cost:cost};
  }
  var SHAPES={
    heart:{label:'Heart',eq:'(x² + 9/4·y² + z² − 1)³ − x²z³ − 9/80·y²z³ ≤ 0',
      b:[-9,9,-9,10,-6,6],
      fn:function(x,y,z){var s=6.4,X=x/s,U=y/s,D=z/s,t=X*X+2.25*D*D+U*U-1;
        return t*t*t-X*X*U*U*U-0.1125*D*D*U*U*U<=0?'#c91a09':null;}},
    sphere:{label:'Sphere',eq:'x² + y² + z² ≤ 5.2²',b:[-6,6,-6,6,-6,6],
      fn:function(x,y,z){return x*x+y*y+z*z<=27?RB[Math.floor((y+6)/2)%RB.length]:null;}},
    torus:{label:'Torus',eq:'(√(x² + z²) − 4.6)² + y² ≤ 2.1²',b:[-8,8,-3,3,-8,8],
      fn:function(x,y,z){var q=Math.hypot(x,z)-4.6;if(q*q+y*y>4.41)return null;
        return RB[(y+3)%RB.length];}},
    helix:{label:'Helix',eq:'‖(x,z) − 4.2·(cos θ, sin θ)‖ < 1.65,  θ = 0.20·layer + 2πk/3',b:[-7,7,0,22,-7,7],
      fn:function(x,y,z){for(var k=0;k<3;k++){var th=y*0.2+k*2*Math.PI/3;
        if(Math.hypot(x-4.2*Math.cos(th),z-4.2*Math.sin(th))<1.65)return ['#c91a09','#f2cd37','#0055bf'][k];}return null;}},
    pyramid:{label:'Pyramid',eq:'max(|x|, |z|) ≤ 6 − layer  (2-stud shell)',b:[-6,6,0,6,-6,6],
      fn:function(x,y,z){var m=Math.max(Math.abs(x),Math.abs(z)),h=6-y;return m<=h&&m>=h-1?RB[y%RB.length]:null;}},
    house:{label:'House',eq:'walls 10×7 studs · roof steps in 1 stud per layer',b:[-1,9,0,10,0,6],
      fn:function(x,y,z){
        if(y>=7&&y<=10&&(x===7||x===8)&&(z===2||z===3))return '#6b2f1a';
        if(y>=5&&y<=8){var k=y-5;return z>=k&&z<=6-k?'#c91a09':null;}
        if(y>4||x<0||x>9)return null;
        if(!(x===0||x===9||z===0||z===6))return null;
        if(z===0&&(x===4||x===5)&&y<=2)return '#0055bf';
        if(y>=2&&y<=3&&((z===0||z===6)&&(x===1||x===2||x===7||x===8)||(x===0||x===9)&&(z===2||z===3)))return '#f2cd37';
        return '#f2f3f2';}}
  };

  /* ---------- geometry generation ---------- */
  function pushF(out,p,n,c,m,a){
    var cx=0,cy=0,cz=0,k=p.length/3;
    for(var i=0;i<p.length;i+=3){cx+=p[i];cy+=p[i+1];cz+=p[i+2];}
    out.push({p:p,n:n,c:c,m:m,a:a,cx:cx/k,cy:cy/k,cz:cz/k});
  }
  function stud(out,cx,T,cz,c,a){
    var top=[];
    for(var s=0;s<SN;s++){
      var s2=(s+1)%SN,x0=cx+SR*COS[s],z0=cz+SR*SIN[s],x1=cx+SR*COS[s2],z1=cz+SR*SIN[s2];
      var mx=COS[s]+COS[s2],mz=SIN[s]+SIN[s2],l=Math.hypot(mx,mz);
      pushF(out,[x0,T,z0,x1,T,z1,x1,T+SH,z1,x0,T+SH,z0],[mx/l,0,mz/l],c,0,a);
      top.push(x0,T+SH,z0);
    }
    pushF(out,top,[0,1,0],c,0,a);
  }
  function genBrick(b,occ,ox,oy,oz,a,out){
    var x=b.x,y=b.y,z=b.z,w=b.w,d=b.d,h=b.h,c=b.c,s,k,l,i;
    for(s=-1;s<=1;s+=2){
      var X=(s>0?x+w:x)+ox,nbx=s>0?x+w:x-1;
      for(k=z;k<z+d;k++)for(l=y;l<y+h;l++){
        if(occ(nbx,l,k))continue;
        var Y0=PL+l*BH+oy,Y1=Y0+BH,Z0=k+oz;
        pushF(out,[X,Y0,Z0,X,Y0,Z0+1,X,Y1,Z0+1,X,Y1,Z0],[s,0,0],c,
          (l===y?1:0)|(k===z+d-1?2:0)|(l===y+h-1?4:0)|(k===z?8:0),a);
      }
      var Z=(s>0?z+d:z)+oz,nbz=s>0?z+d:z-1;
      for(i=x;i<x+w;i++)for(l=y;l<y+h;l++){
        if(occ(i,l,nbz))continue;
        var Yb=PL+l*BH+oy,Yt=Yb+BH,Xa=i+ox;
        pushF(out,[Xa,Yb,Z,Xa+1,Yb,Z,Xa+1,Yt,Z,Xa,Yt,Z],[0,0,s],c,
          (l===y?1:0)|(i===x+w-1?2:0)|(l===y+h-1?4:0)|(i===x?8:0),a);
      }
    }
    var T=PL+(y+h)*BH+oy;
    for(k=z;k<z+d;k++)for(i=x;i<x+w;i++){
      if(occ(i,y+h,k))continue;
      var xa=i+ox,za=k+oz;
      pushF(out,[xa,T,za,xa+1,T,za,xa+1,T,za+1,xa,T,za+1],[0,1,0],c,
        (k===z?1:0)|(i===x+w-1?2:0)|(k===z+d-1?4:0)|(i===x?8:0),a);
      stud(out,xa+0.5,T,za+0.5,c,a);
    }
  }
  var BASE='#3f9a55',MARGIN=2;
  function genBase(M,occ,out){
    var x0=-MARGIN,x1=M.W+MARGIN,z0=-MARGIN,z1=M.D+MARGIN,x,z;
    for(z=z0;z<z1;z++)for(x=x0;x<x1;x++){
      if(occ(x,0,z))continue;
      pushF(out,[x,PL,z,x+1,PL,z,x+1,PL,z+1,x,PL,z+1],[0,1,0],BASE,
        (z===z0?1:0)|(x===x1-1?2:0)|(z===z1-1?4:0)|(x===x0?8:0),1);
      stud(out,x+0.5,PL,z+0.5,BASE,1);
    }
    for(x=x0;x<x1;x++){
      pushF(out,[x,0,z1,x+1,0,z1,x+1,PL,z1,x,PL,z1],[0,0,1],BASE,4,1);
      pushF(out,[x,0,z0,x+1,0,z0,x+1,PL,z0,x,PL,z0],[0,0,-1],BASE,4,1);
    }
    for(z=z0;z<z1;z++){
      pushF(out,[x1,0,z,x1,0,z+1,x1,PL,z+1,x1,PL,z],[1,0,0],BASE,4,1);
      pushF(out,[x0,0,z,x0,0,z+1,x0,PL,z+1,x0,PL,z],[-1,0,0],BASE,4,1);
    }
  }

  /* ---------- the atom ---------- */
  function createBrickBuild(canvas,opts){
    var ctx=canvas.getContext('2d');
    var o={shape:'heart',speed:1,orbit:true,bg:null,bricks:null,mode:'animate',step:1};
    for(var k in opts)o[k]=opts[k];
    var reduced=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
    var M,bricks,N,st,OX,OY,OZ,AL,grid,statics,hl=[],dyn=[],vis=[];
    var FALL=0.55,SETTLE=0.45,HOLD=3,LIFT=0.7,DROP=7;
    var tBuild,tCycle,T0,tNow=0,az=0.7,el=0.52,userAz=0,userEl=0,dragging=false,lastX=0,lastY=0;
    var W=0,H=0,dpr=1,visible=true,dirtyView=true,fps=0,frames=0,lastStat=0,onStats=null,raf=0;

    function occ(x,y,z){
      if(x<0||z<0||y<0||x>=M.W||z>=M.D||y>=M.L)return 0;
      return grid[(y*M.D+z)*M.W+x];
    }
    function noOcc(){return 0;}

    function load(shape){
      o.shape=shape;
      var raw=o.bricks?o.bricks.map(function(b){return {x:b.x,y:b.y,z:b.z,w:b.w||1,d:b.d||1,h:b.h||1,c:b.c||'#c91a09'};})
                      :voxelBricks(SHAPES[shape].fn,SHAPES[shape].b);
      M=normalise(raw);M.trimmed=raw.trimmed||0;bricks=M.bricks;N=bricks.length;
      grid=new Uint8Array(M.W*M.D*M.L);
      st=new Int8Array(N).fill(-2);OX=new Float32Array(N);OY=new Float32Array(N);OZ=new Float32Array(N);AL=new Float32Array(N);
      var stagger=Math.min(0.12,5/N),dst=1.4/N,seed=1;
      function rnd(){seed=(seed*16807)%2147483647;return seed/2147483647-0.5;}
      tBuild=N*stagger+FALL+SETTLE;
      tCycle=tBuild+HOLD+N*dst+LIFT+0.5;
      bricks.forEach(function(b,i){b.t0=i*stagger;b.td=tBuild+HOLD+(N-1-i)*dst;b.jx=rnd()*7;b.jz=rnd()*7;});
      T0=tBuild*0.7;                       // open partly built so the first frame is never empty
      if(reduced)T0=tBuild+1;
      tNow=T0;dirtyView=true;
      // exposed studs on the finished model, for the readout
      var g=new Uint8Array(M.W*M.D*M.L);
      bricks.forEach(function(b){for(var y=b.y;y<b.y+b.h;y++)for(var z=b.z;z<b.z+b.d;z++)for(var x=b.x;x<b.x+b.w;x++)g[(y*M.D+z)*M.W+x]=1;});
      var studs=0;
      for(var y=0;y<M.L;y++)for(var z=0;z<M.D;z++)for(var x=0;x<M.W;x++)
        if(g[(y*M.D+z)*M.W+x]&&(y+1>=M.L||!g[((y+1)*M.D+z)*M.W+x]))studs++;
      M.studs=studs;
      if(o.step>M.steps)o.step=M.steps;
      if(onStats)onStats(info());
    }
    function info(){
      return {bricks:N,studs:M.studs,trimmed:M.trimmed,W:M.W,D:M.D,L:M.L,steps:M.steps,cycle:tCycle,fps:fps,faces:vis.length};
    }

    function status(t){
      var dirty=false,byStep=o.mode==='steps';
      for(var i=0;i<N;i++){
        var b=bricks[i],tf=t-b.t0,td=t-b.td,s,ox=0,oy=0,oz=0,a=1;
        if(byStep)s=b.step<o.step?0:b.step===o.step?2:-1;   // 2 = brick placed in this step, drawn highlighted
        else if(tf<0)s=-1;
        else if(td>=0){var q=td/LIFT;if(q>=1)s=-1;else{s=1;oy=DROP*q*q;a=1-q;}}
        else if(tf<FALL){var p=tf/FALL,e=1-p;s=1;oy=DROP*(1-p*p);ox=b.jx*e*e;oz=b.jz*e*e;a=Math.min(1,p*5);}
        else{var tb=tf-FALL;if(tb<SETTLE){s=1;oy=0.22*Math.exp(-9*tb)*Math.abs(Math.sin(15*tb));}else s=0;}
        if(st[i]!==s){dirty=true;st[i]=s;}
        OX[i]=ox;OY[i]=oy;OZ[i]=oz;AL[i]=a;
      }
      if(dirty)rebuild();
    }
    function rebuild(){
      grid.fill(0);
      for(var i=0;i<N;i++)if(st[i]===0||st[i]===2){var b=bricks[i];
        for(var y=b.y;y<b.y+b.h;y++)for(var z=b.z;z<b.z+b.d;z++)for(var x=b.x;x<b.x+b.w;x++)grid[(y*M.D+z)*M.W+x]=1;}
      statics=[];hl=[];
      genBase(M,occ,statics);
      for(i=0;i<N;i++){
        if(st[i]===0)genBrick(bricks[i],occ,0,0,0,1,statics);
        else if(st[i]===2)genBrick(bricks[i],occ,0,0,0,1,hl);
      }
      hl.forEach(function(f){f.hl=1;});
    }

    /* camera */
    var ca,sa,ce,se,tx,ty,tz,dist,foc,scx,scy,camx,camy,camz,P=[0,0,0];
    function setCamera(){
      var az2=az+userAz,el2=Math.max(0.12,Math.min(1.3,el+userEl));
      ca=Math.cos(az2);sa=Math.sin(az2);ce=Math.cos(el2);se=Math.sin(el2);
      var bw=M.W+2*MARGIN,bd=M.D+2*MARGIN,hh=PL+M.L*BH;
      tx=M.W/2;tz=M.D/2;ty=hh*0.42;
      var R=0.5*Math.hypot(bw,bd,hh*1.1);
      dist=R*3.6;foc=0.39*Math.min(W,H*1.25)*dist/R;
      scx=W/2;scy=H*0.5;
      camx=tx+dist*ce*sa;camy=ty+dist*se;camz=tz+dist*ce*ca;
    }
    function proj(x,y,z){
      var qx=x-tx,qy=y-ty,qz=z-tz;
      var x1=qx*ca-qz*sa,z1=qx*sa+qz*ca,y2=qy*ce-z1*se,z2=qy*se+z1*ce,d=dist-z2;
      P[0]=scx+foc*x1/d;P[1]=scy-foc*y2/d;P[2]=d;
    }
    function hull(pts){
      pts.sort(function(a,b){return a[0]-b[0]||a[1]-b[1];});
      function cr(o,a,b){return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);}
      var lo=[],up=[],i;
      for(i=0;i<pts.length;i++){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],pts[i])<=0)lo.pop();lo.push(pts[i]);}
      for(i=pts.length-1;i>=0;i--){while(up.length>=2&&cr(up[up.length-2],up[up.length-1],pts[i])<=0)up.pop();up.push(pts[i]);}
      lo.pop();up.pop();return lo.concat(up);
    }

    function draw(){
      ctx.setTransform(dpr,0,0,dpr,0,0);
      ctx.clearRect(0,0,W,H);
      if(o.bg){ctx.fillStyle=o.bg;ctx.fillRect(0,0,W,H);}
      setCamera();
      var i,j,f;
      /* shadows: brick boxes projected along the light onto the baseplate, filled once so overlaps do not double up */
      ctx.save();
      ctx.beginPath();
      var bx0=-MARGIN,bx1=M.W+MARGIN,bz0=-MARGIN,bz1=M.D+MARGIN;
      [[bx0,bz0],[bx1,bz0],[bx1,bz1],[bx0,bz1]].forEach(function(c,n){proj(c[0],PL,c[1]);n?ctx.lineTo(P[0],P[1]):ctx.moveTo(P[0],P[1]);});
      ctx.closePath();ctx.clip();
      ctx.beginPath();
      for(i=0;i<N;i++){
        if(st[i]<0)continue;
        var b=bricks[i],pts=[];
        for(var cx=0;cx<2;cx++)for(var cy=0;cy<2;cy++)for(var cz=0;cz<2;cz++){
          var X=b.x+cx*b.w+OX[i],Y=PL+(b.y+cy*b.h)*BH+OY[i],Z=b.z+cz*b.d+OZ[i],t=(Y-PL)/LD[1];
          proj(X-LD[0]*t,PL,Z-LD[2]*t);pts.push([P[0],P[1]]);
        }
        var hp=hull(pts);
        ctx.moveTo(hp[0][0],hp[0][1]);for(j=1;j<hp.length;j++)ctx.lineTo(hp[j][0],hp[j][1]);ctx.closePath();
      }
      ctx.fillStyle='rgba(10,20,30,0.26)';ctx.fill();
      ctx.restore();

      /* collect faces: cached static geometry + bricks currently in motion */
      dyn.length=0;
      for(i=0;i<N;i++)if(st[i]===1)genBrick(bricks[i],noOcc,OX[i],OY[i],OZ[i],AL[i],dyn);
      vis.length=0;
      for(j=0;j<3;j++){
        var list=j===2?hl:j?dyn:statics;
        for(i=0;i<list.length;i++){
          f=list[i];
          if(f.n[0]*(camx-f.cx)+f.n[1]*(camy-f.cy)+f.n[2]*(camz-f.cz)<=0)continue;
          proj(f.cx,f.cy,f.cz);
          vis.push({f:f,d:P[2]});
        }
      }
      vis.sort(function(a,b){return b.d-a.d;});
      ctx.lineJoin='round';
      var alpha=1;
      for(i=0;i<vis.length;i++){
        f=vis[i].f;
        if(f.a!==alpha){ctx.globalAlpha=alpha=f.a;}
        var q=0.5+0.56*Math.max(0,f.n[0]*LD[0]+f.n[1]*LD[1]+f.n[2]*LD[2]);
        if(f.hl)q=Math.min(1.3,q*1.12+0.16);
        var col=shade(f.c,q),p=f.p,n=p.length/3,sx=new Array(n),sy=new Array(n),k;
        ctx.beginPath();
        for(k=0;k<n;k++){proj(p[3*k],p[3*k+1],p[3*k+2]);sx[k]=P[0];sy[k]=P[1];k?ctx.lineTo(P[0],P[1]):ctx.moveTo(P[0],P[1]);}
        ctx.closePath();
        ctx.fillStyle=col;ctx.strokeStyle=col;ctx.lineWidth=0.8;
        ctx.fill();ctx.stroke();
        if(f.m){
          ctx.beginPath();
          for(k=0;k<4;k++)if(f.m&(1<<k)){var k2=(k+1)%4;ctx.moveTo(sx[k],sy[k]);ctx.lineTo(sx[k2],sy[k2]);}
          ctx.strokeStyle=f.hl?'rgba(255,255,255,0.95)':'rgba(0,0,0,0.3)';ctx.lineWidth=f.hl?1.8:1;ctx.stroke();
        }
      }
      ctx.globalAlpha=1;
    }

    function resize(){
      var r=canvas.getBoundingClientRect();
      dpr=Math.min(2,window.devicePixelRatio||1);
      W=Math.max(1,r.width);H=Math.max(1,r.height);
      canvas.width=Math.round(W*dpr);canvas.height=Math.round(H*dpr);
      dirtyView=true;
    }
    var last=0;
    function loop(now){
      raf=requestAnimationFrame(loop);
      if(!visible)return;
      var dt=Math.min(0.05,(now-last)/1000);last=now;
      if(!reduced){
        if(o.mode!=='steps'){tNow+=dt*o.speed;if(tNow>=tCycle)tNow-=tCycle;}
        if(o.orbit&&!dragging)az+=dt*0.22*o.speed;
        dirtyView=true;
      }
      if(!dirtyView)return;
      dirtyView=false;
      status(tNow);draw();
      frames++;
      if(now-lastStat>600){fps=Math.round(frames*1000/(now-lastStat));frames=0;lastStat=now;if(onStats)onStats(info());}
    }

    canvas.addEventListener('pointerdown',function(e){dragging=true;lastX=e.clientX;lastY=e.clientY;try{canvas.setPointerCapture(e.pointerId);}catch(_){}});
    canvas.addEventListener('pointermove',function(e){
      if(!dragging)return;
      userAz-=(e.clientX-lastX)*0.008;userEl+=(e.clientY-lastY)*0.006;
      lastX=e.clientX;lastY=e.clientY;dirtyView=true;
    });
    function up(){dragging=false;}
    canvas.addEventListener('pointerup',up);canvas.addEventListener('pointercancel',up);
    if('ResizeObserver' in window)new ResizeObserver(resize).observe(canvas);else window.addEventListener('resize',resize);
    if('IntersectionObserver' in window)new IntersectionObserver(function(e){visible=e[0].isIntersecting;}).observe(canvas);

    load(o.shape);resize();
    raf=requestAnimationFrame(loop);
    return {
      setShape:function(s){userAz=0;userEl=0;o.bricks=null;load(s);},
      setBricks:function(list){o.bricks=list;load(o.shape);},
      setMode:function(m){o.mode=m;dirtyView=true;},
      setStep:function(n){o.step=n;dirtyView=true;},
      model:function(){return M;},
      replay:function(){tNow=0;dirtyView=true;},
      set:function(k,v){o[k]=v;},
      onStats:function(fn){onStats=fn;fn(info());},
      destroy:function(){cancelAnimationFrame(raf);}
    };
  }
  return {SHAPES: SHAPES, PALNAME: PALNAME, voxelBricks: voxelBricks, normalise: normalise,
          validate: validate, create: createBrickBuild};
}

var _BRICK_MAX = 3000;   // bricks per model — the depth sort is O(n log n) per frame
var _BRICK_MODELS_MAX = 8;   // named models the picker will list

// Coerce an agent-supplied brick list into integers and #rrggbb colours, or return null if it is unusable.
// renderers/web_article.py (_render_brick_build_3d) is a hand-kept twin of this function and of the shell
// below; tests/test_brick_web_twin.py renders both and compares. Edit BOTH.
function _brickSanitise(list) {
  if (!Array.isArray(list) || !list.length) return null;
  var out = [];
  for (var i = 0; i < list.length && out.length < _BRICK_MAX; i++) {
    var r = list[i];
    if (!r || typeof r !== 'object') continue;
    var n = function(v, lo, hi, dflt) {
      v = Math.floor(Number(v));
      return isFinite(v) ? Math.max(lo, Math.min(hi, v)) : dflt;
    };
    var c = typeof r.c === 'string' && /^#[0-9a-fA-F]{6}$/.test(r.c) ? r.c.toLowerCase() : '#c91a09';
    out.push({x: n(r.x, 0, 255, 0), y: n(r.y, 0, 255, 0), z: n(r.z, 0, 255, 0),
              w: n(r.w, 1, 32, 1), d: n(r.d, 1, 32, 1), h: n(r.h, 1, 8, 1), c: c});
  }
  return out.length ? out : null;
}

// Named models for the picker: up to _BRICK_MODELS_MAX of {name, bricks}, each brick list sanitised like `bricks`.
// Entries whose brick list is unusable are skipped; a missing name becomes 'Model N'. Twinned in web_article.py.
function _brickModels(list) {
  var out = [];
  if (!Array.isArray(list)) return out;
  for (var i = 0; i < list.length && out.length < _BRICK_MODELS_MAX; i++) {
    var m = list[i];
    if (!m || typeof m !== 'object') continue;
    var bl = _brickSanitise(m.bricks);
    if (!bl) continue;
    var nm = typeof m.name === 'string' ? m.name.trim().slice(0, 40) : '';
    out.push({name: nm || 'Model ' + (out.length + 1), bricks: bl});
  }
  return out;
}

// The atom's page wiring: canvas engine + scrubber + verdicts + parts table. Serialised into the page next to
// _brickKit (Function.prototype.toString), and read out of this file by the Python web_article twin, so the
// browser code has ONE source. Plain ES5, no closure over anything outside its arguments.
function _brickMount(K, cfg, U) {
  var $ = function(s) { return document.getElementById(U + s); };
  var cv = $('c');
  if (!cv) return;
  function E(tag, css, text) {
    var e = document.createElement(tag);
    if (css) e.style.cssText = css;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  var atom = K.create(cv, {shape: cfg.shape, bricks: cfg.bricks, speed: cfg.speed, orbit: cfg.orbit,
                           bg: cfg.bg, mode: cfg.mode, step: cfg.step});
  var mode = cfg.mode, report = null, last = null, range = null, info = null, btns = {};
  var COL = {pass: '#1e7a45', warn: '#9a6700', fail: '#c4161a'};

  function stepText() {
    var M = atom.model(), n = +range.value, k = 0;
    M.bricks.forEach(function(b) { if (b.step === n) k++; });
    info.textContent = mode === 'steps'
      ? 'step ' + n + ' of ' + M.steps + ' · +' + k + ' brick' + (k === 1 ? '' : 's')
      : M.steps + ' steps · ' + M.bricks.length + ' bricks';
  }
  function setMode(m) {
    mode = m;
    atom.setMode(m);
    for (var k in btns) {
      btns[k].style.background = k === m ? '#d01012' : '#f7f9fb';
      btns[k].style.color = k === m ? '#fff' : '#0f1c28';
    }
    stepText();
  }
  function buildPicker(row) {
    var sel = E('select', 'font:inherit;font-weight:600;border:1px solid #b8c2cc;border-radius:6px;padding:4px 8px;' +
                          'background:#f7f9fb;color:#0f1c28;cursor:pointer;max-width:min(240px,100%);');
    sel.setAttribute('aria-label', 'Model');
    function opt(v, t) { var o = E('option', '', t); o.value = v; sel.appendChild(o); }
    if (cfg.bricks && cfg.start < 0) opt('c', 'Custom model');
    for (var k in K.SHAPES) opt('s:' + k, K.SHAPES[k].label);
    cfg.models.forEach(function(m, i) { opt('m:' + i, m.name); });
    sel.value = cfg.start >= 0 ? 'm:' + cfg.start : cfg.bricks ? 'c' : 's:' + cfg.shape;
    sel.addEventListener('change', function() {
      var v = sel.value;
      if (v.charAt(0) === 's') atom.setShape(v.slice(2));
      else atom.setBricks(v === 'c' ? cfg.bricks : cfg.models[+v.slice(2)].bricks);
    });
    row.appendChild(sel);
  }
  function buildScrubber() {
    var row = $('s');
    if (!row) return;
    if (cfg.picker) buildPicker(row);
    if (!cfg.scrubber) return;
    var bs = 'font:inherit;font-weight:600;border:1px solid #b8c2cc;border-radius:6px;padding:4px 10px;cursor:pointer;';
    [['animate', 'Animate'], ['steps', 'Instructions']].forEach(function(p) {
      var b = E('button', bs, p[1]);
      b.type = 'button';
      b.addEventListener('click', function() { setMode(p[0]); });
      btns[p[0]] = b;
      row.appendChild(b);
    });
    range = E('input');
    range.type = 'range'; range.min = 1; range.max = atom.model().steps; range.value = cfg.step;
    range.style.width = 'min(260px,50vw)';
    range.setAttribute('aria-label', 'Instruction step');
    range.addEventListener('input', function() {
      if (mode !== 'steps') setMode('steps');
      atom.setStep(+range.value);
      stepText();
    });
    row.appendChild(range);
    info = E('span', 'font-variant-numeric:tabular-nums;color:#55636f;');
    row.appendChild(info);
    setMode(cfg.mode);
  }
  function drawChecks() {
    var ul = $('k');
    if (!cfg.checks || !ul) return;
    ul.textContent = '';
    report.checks.forEach(function(c) {
      var li = E('li', 'display:flex;gap:6px;align-items:baseline;');
      li.title = c.detail;
      li.appendChild(E('span', 'font-weight:700;color:' + COL[c.status] + ';',
                       c.status === 'pass' ? '✓' : c.status === 'warn' ? '!' : '✗'));
      li.appendChild(E('span', 'font-weight:600;', c.label));
      li.appendChild(E('span', 'color:#55636f;', c.detail));
      ul.appendChild(li);
    });
  }
  function drawParts() {
    var box = $('p');
    if (!cfg.parts || !box) return;
    box.textContent = '';
    var t = E('table', 'border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums;');
    var hr = E('tr');
    ['part', 'qty', 'est.'].forEach(function(x, i) {
      hr.appendChild(E('th', 'text-align:' + (i ? 'right' : 'left') + ';font-weight:500;color:#55636f;padding:2px 12px 2px 0;', x));
    });
    t.appendChild(hr);
    report.parts.forEach(function(p) {
      var r = E('tr'), c0 = E('td', 'padding:2px 12px 2px 0;');
      c0.appendChild(E('span', 'display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;' +
                               'border:1px solid rgba(0,0,0,.25);background:' + p.hex + ';'));
      c0.appendChild(document.createTextNode(p.size + ' ' + p.colour));
      r.appendChild(c0);
      r.appendChild(E('td', 'text-align:right;padding:2px 12px 2px 0;', String(p.count)));
      r.appendChild(E('td', 'text-align:right;padding:2px 0;', '€' + p.line.toFixed(2)));
      t.appendChild(r);
    });
    box.appendChild(t);
    box.appendChild(E('div', 'color:#55636f;font-size:11px;padding-top:4px;',
                      'indicative pricing formula, not BrickLink data · total €' + report.cost.toFixed(2)));
  }

  buildScrubber();
  atom.onStats(function() {
    var M = atom.model();
    if (M === last) return;
    last = M;
    report = K.validate(M.bricks);
    if (range) { range.max = M.steps; if (+range.value > M.steps) range.value = M.steps; stepText(); }
    drawChecks();
    drawParts();
  });
}

_RENDERERS['brick_build_3d'] = function(b) {
  var kit    = _brickKit();
  var shape  = Object.prototype.hasOwnProperty.call(kit.SHAPES, b.shape) ? b.shape : 'heart';
  var bricks = _brickSanitise(b.bricks);          // '' (unresolved binding) and junk fall back to shape
  var models = _brickModels(b.models), start = -1;
  if (!bricks && typeof b.model === 'string') {
    for (var j = 0; j < models.length; j++) if (models[j].name === b.model) { start = j; break; }
    if (start >= 0) bricks = models[start].bricks;
  }
  var h      = Math.max(160, Math.min(900, parseInt(b.height, 10) || 380));
  var cfg = {
    shape: shape, bricks: bricks,
    mode:  b.mode === 'steps' ? 'steps' : 'animate',
    step:  Math.max(1, parseInt(b.step, 10) || 1),
    speed: b.speed !== undefined && isFinite(Number(b.speed)) ? Math.max(0.1, Math.min(4, Number(b.speed))) : 1,
    orbit: b.orbit !== false,
    bg:    typeof b.bg === 'string' && /^#[0-9a-fA-F]{3,8}$/.test(b.bg) ? b.bg : null,
    scrubber: b.scrubber !== false, checks: b.checks !== false, parts: b.parts === true,
    models: models, picker: b.picker === false ? false : (b.picker === true || models.length > 0), start: start
  };
  var uid  = 'brk' + Math.random().toString(36).substr(2, 6);
  var json = JSON.stringify(cfg).replace(/</g, '\\u003c');

  return '<div style="border-radius:14px;overflow:hidden;color:#0f1c28;' +
      'font:13px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;' +
      'background:radial-gradient(120% 90% at 50% 30%,#fafbfd,#cdd6e0);">' +
    '<div style="position:relative;height:' + h + 'px;">' +
      '<canvas id="' + uid + 'c" role="img" aria-label="Animated 3D brick model" ' +
        'style="position:absolute;top:0;left:0;width:100%;height:100%;display:block;touch-action:pan-y;cursor:grab;"></canvas>' +
    '</div>' +
    '<div id="' + uid + 's" style="display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;padding:8px 14px 0;"></div>' +
    '<ul id="' + uid + 'k" style="list-style:none;margin:0;padding:8px 14px;display:flex;flex-wrap:wrap;gap:4px 16px;font-size:12px;"></ul>' +
    '<div id="' + uid + 'p" style="overflow-x:auto;padding:0 14px 12px;"></div>' +
    '</div>' +
    '<script>(function(){(' + _brickMount.toString() + ')((' + _brickKit.toString() + ')(),' + json + ',"' + uid + '");})();</script>';
};
