// brick_validate_shared.js -- the real LDraw-parts collision/connector validator (studs, sockets, pins,
// hinges, axles, clips, bars, towballs, ball-sockets), extracted verbatim from apps-script-surface/
// gas-wired-renderer/atoms_brick.gs's validateParts() and its pure helper functions (connWorld, worldBoxes,
// boxesOverlap, hingesWorld, hingeKindsMate, axlesWorld, clipsWorld, barsWorld, towballsWorld,
// ballSocketsWorld, pairHoles, rotLDU, dot3/dist3/add3, pointLineDist, onGrid, hull2), so a second consumer
// (scripts/brick_models/build_design_page.py's Three.js viewer) can show the SAME real validation checklist
// atoms_brick.gs's drawChecks() already does, without a second hand-written copy of this logic quietly
// drifting from the first.
//
// atoms_brick.gs is deliberately left untouched by this extraction (a live, deployed Google Apps Script
// renderer -- CLAUDE.md documents six prior "deployed != reachable" incidents for changes to files like it,
// and this repo has no existing build step that assembles atoms_brick.gs from smaller pieces the way
// build_design_page.py assembles its own page). Refactoring atoms_brick.gs's own K.validateParts down to a
// thin wrapper around this file is a real, separate follow-up (same live-file review/deploy-verify
// discipline as any other atoms_brick.gs change), not bundled into this extraction.
//
// Parity with atoms_brick.gs's own copy is enforced the SAME way this project already keeps its Python twin
// (renderers/brick_parts_validate.py) honest: a fixture-based parity test
// (tests/test_brick_parts_validate.mjs), not manual code review. atoms_brick.gs's K.validateParts is the
// spec of record (tested directly against all 15 real fixtures in
// tests/fixtures/bricks/parts_fixtures-v0.1.json); this file is a second copy proven to match it and those
// same fixtures, exactly the role the Python twin already plays.
//
// Depends on TJS_PART_ROT (threejs_view_math.js) already being in scope -- the 24 fixed part-rotation
// matrices are identical to atoms_brick.gs's own PART_ROT (verified byte-for-byte, see the commit that added
// this file), so this deliberately reuses that table instead of embedding a third copy of it.
//
// validatePartsPure(list, meshes) differs from atoms_brick.gs's validateParts(list) in exactly one place:
// meshes are passed explicitly (meshes[i] for list[i]), matching Python's validate_parts(parts, meshes)
// signature, instead of being read from atoms_brick.gs's own module-scope partMeshCache. Every other line is
// an unmodified copy.

function rotLDU(r,p){var Rm=Array.isArray(r)?r:TJS_PART_ROT[r];return [Rm[0]*p[0]+Rm[1]*p[1]+Rm[2]*p[2],Rm[3]*p[0]+Rm[4]*p[1]+Rm[5]*p[2],Rm[6]*p[0]+Rm[7]*p[1]+Rm[8]*p[2]];}

function dot3(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
function dist3(a,b){return Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);}
function add3(a,b){return [a[0]+b[0],a[1]+b[1],a[2]+b[2]];}
function pointLineDist(p,a,b){
  var ab=[b[0]-a[0],b[1]-a[1],b[2]-a[2]],ap=[p[0]-a[0],p[1]-a[1],p[2]-a[2]],L2=dot3(ab,ab)||1e-9,t=dot3(ap,ab)/L2;
  var proj=[a[0]+ab[0]*t,a[1]+ab[1]*t,a[2]+ab[2]*t];
  return {dist:dist3(p,proj),t:t};
}
function onGrid(v){var m=((v-10)%20+20)%20;return m<0.5||m>19.5;}
function hull2(pts){
  pts=pts.slice().sort(function(a,b){return a[0]-b[0]||a[1]-b[1];});
  function cr(o,a,b){return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);}
  var lo=[],up=[],i;
  for(i=0;i<pts.length;i++){while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],pts[i])<=0)lo.pop();lo.push(pts[i]);}
  for(i=pts.length-1;i>=0;i--){while(up.length>=2&&cr(up[up.length-2],up[up.length-1],pts[i])<=0)up.pop();up.push(pts[i]);}
  lo.pop();up.pop();return lo.concat(up);
}

function connWorld(mesh,kind,r,ex,ey,ez){
  var list=(mesh.connectors&&mesh.connectors[kind])||[],q=mesh.quant;
  return list.map(function(c){
    var lp=[c.pos[0]/q,c.pos[1]/q,c.pos[2]/q],wp=rotLDU(r,lp),wd=rotLDU(r,c.dir);
    return {pos:[wp[0]+ex,wp[1]+ey,wp[2]+ez],dir:wd};
  });
}
// Twin of Python's _world_boxes: plain 6-tuple AABBs (Array) for the legacy int-index rotation path, OBB
// objects ({center,extents,axes,aabb}) for a general matrix rotation -- see boxesOverlap for the SAT this
// enables. axes are world-space unit vectors of the box's local x/y/z, derived from the rotation matrix's rows.
function worldBoxes(mesh,r,ex,ey,ez){
  if(!mesh.occupancy)return null;
  if(!Array.isArray(r)){
    return mesh.occupancy.map(function(b){
      var c0=rotLDU(r,[b[0],b[2],b[4]]),c1=rotLDU(r,[b[1],b[3],b[5]]);
      return [Math.min(c0[0],c1[0])+ex,Math.max(c0[0],c1[0])+ex,
              Math.min(c0[1],c1[1])+ey,Math.max(c0[1],c1[1])+ey,
              Math.min(c0[2],c1[2])+ez,Math.max(c0[2],c1[2])+ez];
    });
  }
  var u0=[r[0],r[3],r[6]],u1=[r[1],r[4],r[7]],u2=[r[2],r[5],r[8]];
  return mesh.occupancy.map(function(b){
    var cloc=[(b[0]+b[1])*0.5,(b[2]+b[3])*0.5,(b[4]+b[5])*0.5];
    var e=[Math.abs(b[1]-b[0])*0.5,Math.abs(b[3]-b[2])*0.5,Math.abs(b[5]-b[4])*0.5];
    var crot=rotLDU(r,cloc),cw=[crot[0]+ex,crot[1]+ey,crot[2]+ez];
    var rx=e[0]*Math.abs(u0[0])+e[1]*Math.abs(u1[0])+e[2]*Math.abs(u2[0]);
    var ry=e[0]*Math.abs(u0[1])+e[1]*Math.abs(u1[1])+e[2]*Math.abs(u2[1]);
    var rz=e[0]*Math.abs(u0[2])+e[1]*Math.abs(u1[2])+e[2]*Math.abs(u2[2]);
    return {center:cw,extents:e,axes:[u0,u1,u2],
            aabb:[cw[0]-rx,cw[0]+rx,cw[1]-ry,cw[1]+ry,cw[2]-rz,cw[2]+rz]};
  });
}
// Twin of Python's _boxes_overlap: fast 6-tuple interval check when both boxes are plain AABBs (Array), full
// 15-axis SAT (3+3 face normals + 9 edge cross-products) when either is an OBB object -- a plain AABB is
// synthesised into an axis-aligned OBB wrapper so the same SAT loop handles OBB-vs-AABB and OBB-vs-OBB alike.
function boxesOverlap(a,b){
  if(Array.isArray(a)&&Array.isArray(b)){
    var ox=Math.min(a[1],b[1])-Math.max(a[0],b[0]),oy=Math.min(a[3],b[3])-Math.max(a[2],b[2]),
        oz=Math.min(a[5],b[5])-Math.max(a[4],b[4]);
    return ox>0.5&&oy>0.5&&oz>0.5;
  }
  var oa=Array.isArray(a)?{center:[(a[0]+a[1])*0.5,(a[2]+a[3])*0.5,(a[4]+a[5])*0.5],
      extents:[Math.abs(a[1]-a[0])*0.5,Math.abs(a[3]-a[2])*0.5,Math.abs(a[5]-a[4])*0.5],
      axes:[[1,0,0],[0,1,0],[0,0,1]]}:a;
  var ob=Array.isArray(b)?{center:[(b[0]+b[1])*0.5,(b[2]+b[3])*0.5,(b[4]+b[5])*0.5],
      extents:[Math.abs(b[1]-b[0])*0.5,Math.abs(b[3]-b[2])*0.5,Math.abs(b[5]-b[4])*0.5],
      axes:[[1,0,0],[0,1,0],[0,0,1]]}:b;
  var ca=oa.center,ea=oa.extents,ua=oa.axes,cb=ob.center,eb=ob.extents,ub=ob.axes;
  var dx=cb[0]-ca[0],dy=cb[1]-ca[1],dz=cb[2]-ca[2];
  var axes=[
    ua[0],ua[1],ua[2],
    ub[0],ub[1],ub[2],
    [ua[0][1]*ub[0][2]-ua[0][2]*ub[0][1],ua[0][2]*ub[0][0]-ua[0][0]*ub[0][2],ua[0][0]*ub[0][1]-ua[0][1]*ub[0][0]],
    [ua[0][1]*ub[1][2]-ua[0][2]*ub[1][1],ua[0][2]*ub[1][0]-ua[0][0]*ub[1][2],ua[0][0]*ub[1][1]-ua[0][1]*ub[1][0]],
    [ua[0][1]*ub[2][2]-ua[0][2]*ub[2][1],ua[0][2]*ub[2][0]-ua[0][0]*ub[2][2],ua[0][0]*ub[2][1]-ua[0][1]*ub[2][0]],
    [ua[1][1]*ub[0][2]-ua[1][2]*ub[0][1],ua[1][2]*ub[0][0]-ua[1][0]*ub[0][2],ua[1][0]*ub[0][1]-ua[1][1]*ub[0][0]],
    [ua[1][1]*ub[1][2]-ua[1][2]*ub[1][1],ua[1][2]*ub[1][0]-ua[1][0]*ub[1][2],ua[1][0]*ub[1][1]-ua[1][1]*ub[1][0]],
    [ua[1][1]*ub[2][2]-ua[1][2]*ub[2][1],ua[1][2]*ub[2][0]-ua[1][0]*ub[2][2],ua[1][0]*ub[2][1]-ua[1][1]*ub[2][0]],
    [ua[2][1]*ub[0][2]-ua[2][2]*ub[0][1],ua[2][2]*ub[0][0]-ua[2][0]*ub[0][2],ua[2][0]*ub[0][1]-ua[2][1]*ub[0][0]],
    [ua[2][1]*ub[1][2]-ua[2][2]*ub[1][1],ua[2][2]*ub[1][0]-ua[2][0]*ub[1][2],ua[2][0]*ub[1][1]-ua[2][1]*ub[1][0]],
    [ua[2][1]*ub[2][2]-ua[2][2]*ub[2][1],ua[2][2]*ub[2][0]-ua[2][0]*ub[2][2],ua[2][0]*ub[2][1]-ua[2][1]*ub[2][0]]
  ];
  for(var ai=0;ai<axes.length;ai++){
    var lx=axes[ai][0],ly=axes[ai][1],lz=axes[ai][2];
    var l2=lx*lx+ly*ly+lz*lz;
    if(l2<1e-9)continue;
    var normL=Math.sqrt(l2);
    var dist=Math.abs(dx*lx+dy*ly+dz*lz);
    var ra=ea[0]*Math.abs(ua[0][0]*lx+ua[0][1]*ly+ua[0][2]*lz)+
            ea[1]*Math.abs(ua[1][0]*lx+ua[1][1]*ly+ua[1][2]*lz)+
            ea[2]*Math.abs(ua[2][0]*lx+ua[2][1]*ly+ua[2][2]*lz);
    var rb=eb[0]*Math.abs(ub[0][0]*lx+ub[0][1]*ly+ub[0][2]*lz)+
            eb[1]*Math.abs(ub[1][0]*lx+ub[1][1]*ly+ub[1][2]*lz)+
            eb[2]*Math.abs(ub[2][0]*lx+ub[2][1]*ly+ub[2][2]*lz);
    if((ra+rb)-dist<=0.5*normL)return false;
  }
  return true;
}

var CURATED_HINGES={
  '2429':[{pos:[0,0,0],dir:[0,1,0],kind:'plate_hinge_base'}],
  '2430':[{pos:[0,0,0],dir:[0,1,0],kind:'plate_hinge_top'}],
  '3830':[{pos:[0,0,0],dir:[0,1,0],kind:'swivel_base'}],
  '3831':[{pos:[0,0,0],dir:[0,1,0],kind:'swivel_top'}]
};
// Twin of _hinges_world (brick_parts_validate.py) -- pos/dir rotate+translate like connWorld, but each
// entry also carries a `kind` (not a rotatable quantity) that connWorld's generic pos/dir extraction drops.
function hingesWorld(mesh,r,ex,ey,ez){
  var list=(mesh.connectors&&mesh.connectors.hinges)||[];
  if(!list.length&&CURATED_HINGES[mesh.id]){
    return CURATED_HINGES[mesh.id].map(function(h){
      var wp=rotLDU(r,h.pos),wd=rotLDU(r,h.dir);
      return {pos:[wp[0]+ex,wp[1]+ey,wp[2]+ez],dir:wd,kind:h.kind};
    });
  }
  var q=mesh.quant||16;
  return list.map(function(h){
    var lp=[h.pos[0]/q,h.pos[1]/q,h.pos[2]/q],wp=rotLDU(r,lp),wd=rotLDU(r,h.dir);
    return {pos:[wp[0]+ex,wp[1]+ey,wp[2]+ez],dir:wd,kind:h.kind};
  });
}
// Twin of _hinge_kinds_mate -- see its Python comment for the real physical mating rule.
function hingeKindsMate(ka,kb){
  var complements={
    finger2:'finger3',finger3:'finger2',
    plate_hinge_base:'plate_hinge_top',plate_hinge_top:'plate_hinge_base',
    swivel_base:'swivel_top',swivel_top:'swivel_base'
  };
  if(complements[ka]||complements[kb])return complements[ka]===kb;
  return ka===kb&&ka==='knuckle';
}
// Twin of _axles_world (brick_parts_validate.py)
function axlesWorld(mesh,r,ex,ey,ez){
  if(!mesh)return [];
  var q=mesh.quant||16,out=[];
  var list=(mesh.connectors&&mesh.connectors.axles)||[];
  if(list.length){
    list.forEach(function(ax){
      var la,lb;
      if(ax.a&&ax.b){
        la=[ax.a[0]/q,ax.a[1]/q,ax.a[2]/q];
        lb=[ax.b[0]/q,ax.b[1]/q,ax.b[2]/q];
      }else if(ax.pos&&ax.dir){
        la=[ax.pos[0]/q,ax.pos[1]/q,ax.pos[2]/q];
        var len=ax.len||0;
        lb=[la[0]+ax.dir[0]*len,la[1]+ax.dir[1]*len,la[2]+ax.dir[2]*len];
      }else{return;}
      var wa=add3(rotLDU(r,la),[ex,ey,ez]),wb=add3(rotLDU(r,lb),[ex,ey,ez]);
      out.push({a:wa,b:wb});
    });
    return out;
  }
  var tl=(mesh.title||'').toLowerCase();
  var tClean=tl.replace(/^[~=_\s|0-9]*/,'').trim();
  var isAxle=/\baxle\b/.test(tClean)&&!/\b(with.*hole|with.*holes|axlehole|axle hole)\b/.test(tClean);
  if(!isAxle)return [];
  if(mesh.occupancy){
    mesh.occupancy.forEach(function(b){
      var dx=b[1]-b[0],dy=b[3]-b[2],dz=b[5]-b[4];
      if(dx>=15&&Math.abs(b[2]+6)<=0.6&&Math.abs(b[3]-6)<=0.6&&Math.abs(b[4]+6)<=0.6&&Math.abs(b[5]-6)<=0.6){
        var la=[b[0],0,0],lb=[b[1],0,0];
        out.push({a:add3(rotLDU(r,la),[ex,ey,ez]),b:add3(rotLDU(r,lb),[ex,ey,ez])});
      }else if(dz>=15&&Math.abs(b[0]+6)<=0.6&&Math.abs(b[1]-6)<=0.6&&Math.abs(b[2]+6)<=0.6&&Math.abs(b[3]-6)<=0.6){
        var la=[0,0,b[4]],lb=[0,0,b[5]];
        out.push({a:add3(rotLDU(r,la),[ex,ey,ez]),b:add3(rotLDU(r,lb),[ex,ey,ez])});
      }
    });
  }
  return out;
}
var CURATED_CLIPS={
  '4085a':[{pos:[0,4,-20],dir:[0,1,0]}],
  '4085b':[{pos:[0,4,-20],dir:[0,1,0]}],
  '4085c':[{pos:[0,4,-20],dir:[0,1,0]}],
  '60897':[{pos:[0,4,-20],dir:[0,1,0]}],
  '6019': [{pos:[0,2,-20],dir:[1,0,0]}],
  '61252':[{pos:[0,2,-20],dir:[1,0,0]}],
  '60476':[{pos:[0,10,-20],dir:[1,0,0]}],
  '60470a':[{pos:[-10,2,-20],dir:[1,0,0]},{pos:[10,2,-20],dir:[1,0,0]}],
  '60470b':[{pos:[-10,2,-20],dir:[1,0,0]},{pos:[10,2,-20],dir:[1,0,0]}],
  '11476':[{pos:[0,2,-20],dir:[1,0,0]}],
  '44861':[{pos:[10,-6,0],dir:[0,0,1]}],
  '92280':[{pos:[10,-6,0],dir:[0,0,1]}],
  '78256':[{pos:[30,4,0],dir:[0,1,0]}],
  '15712':[{pos:[0,-6,0],dir:[0,0,1]}],
  '2555': [{pos:[0,-6,0],dir:[0,0,1]}],
  '30237':[{pos:[0,12,-20],dir:[0,1,0]}],
  '60475a':[{pos:[0,12,-20],dir:[0,1,0]}],
  '60475b':[{pos:[0,12,-20],dir:[0,1,0]}],
  '95820':[{pos:[0,12,-20],dir:[0,1,0]}]
};
var CURATED_BARS={
  '2540':   [{a:[-20,2,-20],b:[20,2,-20]}],
  '2921':   [{a:[0,0,-20],b:[0,24,-20]}],
  '292126': [{a:[0,0,-20],b:[0,24,-20]}],
  '30236':  [{a:[-20,10,-20],b:[20,10,-20]}],
  '48336':  [{a:[-14,2,-20],b:[14,2,-20]}],
  '30374':  [{a:[0,0,0],b:[0,80,0]}],
  '4095':   [{a:[0,-120,0],b:[0,12,0]}],
  '63965':  [{a:[0,-102.5,0],b:[0,18,0]}],
  '2714a':  [{a:[0,-137.5,0],b:[0,18,0]}],
  '25893a': [{a:[-10,8,0],b:[10,8,0]}]
};
// Towball/ball-socket connectors (2026-09-29, mated-connector-exemption-towballs). Curated only, same
// basis as the Python twin -- see scripts/ldraw/MATED_CONNECTOR_EXEMPTION_INVESTIGATION.md section 6 for
// how these were measured (ball side exact, socket side a real but disclosed-uncertainty mesh fit).
var CURATED_TOWBALLS={
  '15456':[{pos:[0,4,-40],r:8.0}],
  '2508': [{pos:[0,4,-90],r:8.0}],
  '3184': [{pos:[0,4,-28],r:8.0}],
  '3614a':[{pos:[0,4,-19],r:8.0}],
  '3731': [{pos:[0,4,-40],r:8.0}],
  '3729': [{pos:[0,4,-40],r:8.0}],
  '4089': [{pos:[0,12,20],r:8.0}]
};
var CURATED_BALL_SOCKETS={
  '3491': [{pos:[-52.0,13.0,0],r:8.0}],
  '3730': [{pos:[0,3.8,-28.9],r:8.0}],
  '3183a':[{pos:[0,4.0,-19.6],r:8.0}],
  '3183b':[{pos:[0,4.0,-19.6],r:8.0}],
  '3183c':[{pos:[0,4.0,-17.5],r:8.0}]
};
var BALL_SOCKET_MATCH_TOL=3.0;
function towballsWorld(mesh,r,ex,ey,ez){
  if(!mesh)return [];
  var pid=mesh.id,q=mesh.quant||16,out=[];
  var list=(mesh.connectors&&mesh.connectors.towballs)||[];
  if(list.length){
    list.forEach(function(t){
      var lp=[t.pos[0]/q,t.pos[1]/q,t.pos[2]/q],wp=rotLDU(r,lp);
      out.push({pos:[wp[0]+ex,wp[1]+ey,wp[2]+ez],r:t.r});
    });
    return out;
  }
  if(CURATED_TOWBALLS[pid]){
    CURATED_TOWBALLS[pid].forEach(function(t){
      var wp=rotLDU(r,t.pos);
      out.push({pos:[wp[0]+ex,wp[1]+ey,wp[2]+ez],r:t.r});
    });
  }
  return out;
}
function ballSocketsWorld(mesh,r,ex,ey,ez){
  if(!mesh)return [];
  var pid=mesh.id,q=mesh.quant||16,out=[];
  var list=(mesh.connectors&&mesh.connectors.ball_sockets)||[];
  if(list.length){
    list.forEach(function(s){
      var lp=[s.pos[0]/q,s.pos[1]/q,s.pos[2]/q],wp=rotLDU(r,lp);
      out.push({pos:[wp[0]+ex,wp[1]+ey,wp[2]+ez],r:s.r});
    });
    return out;
  }
  if(CURATED_BALL_SOCKETS[pid]){
    CURATED_BALL_SOCKETS[pid].forEach(function(s){
      var wp=rotLDU(r,s.pos);
      out.push({pos:[wp[0]+ex,wp[1]+ey,wp[2]+ez],r:s.r});
    });
  }
  return out;
}
function clipsWorld(mesh,r,ex,ey,ez){
  if(!mesh)return [];
  var pid=mesh.id,q=mesh.quant||16,out=[];
  var list=(mesh.connectors&&mesh.connectors.clips)||[];
  if(list.length){
    list.forEach(function(c){
      var lp=[c.pos[0]/q,c.pos[1]/q,c.pos[2]/q];
      var wp=add3(rotLDU(r,lp),[ex,ey,ez]);
      var wd=rotLDU(r,c.dir);
      out.push({pos:wp,dir:wd});
    });
    return out;
  }
  if(CURATED_CLIPS[pid]){
    CURATED_CLIPS[pid].forEach(function(c){
      var wp=add3(rotLDU(r,c.pos),[ex,ey,ez]);
      var wd=rotLDU(r,c.dir);
      out.push({pos:wp,dir:wd});
    });
    return out;
  }
  var tl=(mesh.title||'').toLowerCase();
  if(tl.indexOf('clip')!==-1&&tl.indexOf('clipboard')===-1){
    var rawBars=(mesh.connectors&&mesh.connectors.bars)||[];
    rawBars.forEach(function(b){
      var lp=[b.pos[0]/q,b.pos[1]/q,b.pos[2]/q];
      var wp=add3(rotLDU(r,lp),[ex,ey,ez]);
      var wd=rotLDU(r,b.dir);
      out.push({pos:wp,dir:wd});
    });
  }
  return out;
}
function barsWorld(mesh,r,ex,ey,ez){
  if(!mesh)return [];
  var pid=mesh.id,q=mesh.quant||16,out=[];
  var tl=(mesh.title||'').toLowerCase();
  if((tl.indexOf('clip')!==-1&&tl.indexOf('clipboard')===-1)||CURATED_CLIPS[pid])return [];
  if(CURATED_BARS[pid]){
    CURATED_BARS[pid].forEach(function(b){
      out.push({a:add3(rotLDU(r,b.a),[ex,ey,ez]),b:add3(rotLDU(r,b.b),[ex,ey,ez])});
    });
    return out;
  }
  var rawBars=(mesh.connectors&&mesh.connectors.bars)||[];
  if(!rawBars.length)return [];
  if(rawBars.some(function(b){return b.a&&b.b;})){
    rawBars.forEach(function(b){
      if(b.a&&b.b){
        var la=[b.a[0]/q,b.a[1]/q,b.a[2]/q],lb=[b.b[0]/q,b.b[1]/q,b.b[2]/q];
        out.push({a:add3(rotLDU(r,la),[ex,ey,ez]),b:add3(rotLDU(r,lb),[ex,ey,ez])});
      }
    });
    return out;
  }
  if(rawBars.some(function(b){return b.len;})){
    rawBars.forEach(function(b){
      var la=[b.pos[0]/q,b.pos[1]/q,b.pos[2]/q],blen=b.len||0,d=b.dir||[1,0,0];
      var lb=[la[0]+d[0]*blen,la[1]+d[1]*blen,la[2]+d[2]*blen];
      out.push({a:add3(rotLDU(r,la),[ex,ey,ez]),b:add3(rotLDU(r,lb),[ex,ey,ez])});
    });
    return out;
  }
  if(rawBars.length>=2){
    var p0=[rawBars[0].pos[0]/q,rawBars[0].pos[1]/q,rawBars[0].pos[2]/q];
    var p1=[rawBars[1].pos[0]/q,rawBars[1].pos[1]/q,rawBars[1].pos[2]/q];
    out.push({a:add3(rotLDU(r,p0),[ex,ey,ez]),b:add3(rotLDU(r,p1),[ex,ey,ez])});
    return out;
  }
  if(rawBars.length===1&&mesh.bounds){
    var p0=[rawBars[0].pos[0]/q,rawBars[0].pos[1]/q,rawBars[0].pos[2]/q];
    var d=rawBars[0].dir||[1,0,0];
    var bmin=[mesh.bounds.min[0]/q,mesh.bounds.min[1]/q,mesh.bounds.min[2]/q];
    var bmax=[mesh.bounds.max[0]/q,mesh.bounds.max[1]/q,mesh.bounds.max[2]/q];
    var axis=Math.abs(d[0])>0.5?0:Math.abs(d[1])>0.5?1:2;
    var la=p0.slice(),lb=p0.slice();
    la[axis]=bmin[axis];lb[axis]=bmax[axis];
    out.push({a:add3(rotLDU(r,la),[ex,ey,ez]),b:add3(rotLDU(r,lb),[ex,ey,ez])});
    return out;
  }
  return out;
}
// Pair a mesh's local hole entries (one {pos,dir} per face) into {a,b} segments: greedy nearest
// opposite-direction match, in LOCAL (unquantised LDU) space -- spec §2's "the segment between the pair is
// the hole axis".
function pairHoles(mesh){
  var q=mesh.quant;
  var holes=((mesh.connectors&&mesh.connectors.holes)||[]).map(function(h){
    return {pos:[h.pos[0]/q,h.pos[1]/q,h.pos[2]/q],dir:h.dir};
  });
  var used=new Array(holes.length),segs=[],i,j;
  for(i=0;i<holes.length;i++){
    if(used[i])continue;
    var best=-1,bestD=Infinity;
    for(j=i+1;j<holes.length;j++){
      if(used[j]||dot3(holes[i].dir,holes[j].dir)>-0.9)continue;
      var d=dist3(holes[i].pos,holes[j].pos);
      if(d<bestD){bestD=d;best=j;}
    }
    if(best>=0){used[i]=1;used[best]=1;segs.push({a:holes[i].pos,b:holes[best].pos});}
  }
  return segs;
}

// Real LDraw-parts validator (spec/brick-parts-v0.1.md §2-4, Phase 3): real LDU positions/rotations and each
// part's own baked connectors/occupancy, validated entirely in real LDU world coordinates via rotLDU rather
// than grid cells. meshes[i] is list[i]'s already-resolved part JSON (or null/undefined/'loading'/'error' if
// unavailable -- the part is then counted as "not checked", not silently skipped from the report).
function validatePartsPure(list,meshes){
  var n=list.length,i,j;
  var studs=[],sockets=[],pins=[],boxes=[],holeSegsWorld=[],hinges=[],axles=[],clips=[],bars=[],towballs=[],ballSockets=[],notChecked=0;
  for(i=0;i<n;i++){
    var e=list[i],m=meshes[i];
    if(!m||m==='loading'||m==='error'){studs.push([]);sockets.push([]);pins.push([]);boxes.push(null);holeSegsWorld.push([]);hinges.push([]);axles.push([]);clips.push([]);bars.push([]);towballs.push([]);ballSockets.push([]);notChecked++;continue;}
    studs.push(connWorld(m,'studs',e.r,e.x,e.y,e.z));
    sockets.push(connWorld(m,'sockets',e.r,e.x,e.y,e.z));
    pins.push(connWorld(m,'pins',e.r,e.x,e.y,e.z));
    hinges.push(hingesWorld(m,e.r,e.x,e.y,e.z));
    axles.push(axlesWorld(m,e.r,e.x,e.y,e.z));
    clips.push(clipsWorld(m,e.r,e.x,e.y,e.z));
    bars.push(barsWorld(m,e.r,e.x,e.y,e.z));
    towballs.push(towballsWorld(m,e.r,e.x,e.y,e.z));
    ballSockets.push(ballSocketsWorld(m,e.r,e.x,e.y,e.z));
    boxes.push(worldBoxes(m,e.r,e.x,e.y,e.z));
    if(!m.occupancy)notChecked++;
    var localSegs=pairHoles(m);
    holeSegsWorld.push(localSegs.map(function(s){return {a:add3(rotLDU(e.r,s.a),[e.x,e.y,e.z]),b:add3(rotLDU(e.r,s.b),[e.x,e.y,e.z])};}));
  }
  var studConn=0,pinConn=0,adj=[],baseAdj={};
  for(i=0;i<n;i++)adj.push({});
  // Sockets bucketed by rounded world position so each stud probes only the 27 neighbouring 1-LDU cells
  // instead of every other part's every socket (the naive all-pairs loop took ~60 s at 1,000 parts -- found by
  // tests/test_brick_parts_stress.mjs); the 0.5-LDU match tolerance can straddle one rounding boundary, hence
  // the +/-1 probe. Same pairs are matched, so counts are identical to the all-pairs version.
  var sockHash={};
  for(j=0;j<n;j++)sockets[j].forEach(function(k){
    var hk=Math.round(k.pos[0])+','+Math.round(k.pos[1])+','+Math.round(k.pos[2]);
    (sockHash[hk]=sockHash[hk]||[]).push({j:j,k:k});
  });
  for(i=0;i<n;i++){
    studs[i].forEach(function(s){
      var bx=Math.round(s.pos[0]),by=Math.round(s.pos[1]),bz=Math.round(s.pos[2]);
      for(var dx=-1;dx<=1;dx++)for(var dy=-1;dy<=1;dy++)for(var dz=-1;dz<=1;dz++){
        var cell=sockHash[(bx+dx)+','+(by+dy)+','+(bz+dz)];
        if(!cell)continue;
        cell.forEach(function(e2){
          if(e2.j===i)return;
          if(dist3(s.pos,e2.k.pos)<0.5&&dot3(s.dir,e2.k.dir)<-0.5){studConn++;adj[i][e2.j]=1;adj[e2.j][i]=1;}
        });
      }
    });
    sockets[i].forEach(function(k){
      if(Math.abs(k.pos[1])<0.5&&onGrid(k.pos[0])&&onGrid(k.pos[2])&&dot3(k.dir,[0,-1,0])<-0.5){baseAdj[i]=1;studConn++;}
    });
  }
  // Parts whose connectors are known to physically interpenetrate on purpose (a pin genuinely passing
  // through a hole, an axle genuinely passing through a hole, or two hinge halves genuinely sharing a pivot axis) --
  // exempted from the collision check below. Twin of Python's `mated_pairs` -- see its comment for why a coarse
  // whole-pair exemption is the spec-safe direction to err in.
  var matedPairs={};
  for(i=0;i<n;i++){
    pins[i].forEach(function(p){
      for(j=0;j<n;j++){
        if(i===j)continue;
        holeSegsWorld[j].forEach(function(seg){
          var half=add3(p.pos,p.dir.map(function(d){return d*20;})),mid=add3(p.pos,p.dir.map(function(d){return d*10;}));
          var d1=pointLineDist(p.pos,seg.a,seg.b),d2=pointLineDist(half,seg.a,seg.b),dm=pointLineDist(mid,seg.a,seg.b);
          if(d1.dist<0.5&&d2.dist<0.5&&dm.t>=-0.02&&dm.t<=1.02){pinConn++;adj[i][j]=1;adj[j][i]=1;matedPairs[Math.min(i,j)+','+Math.max(i,j)]=1;}
        });
      }
    });
  }
  var hingeConn=0;
  for(i=0;i<n;i++){
    hinges[i].forEach(function(ha){
      for(j=i+1;j<n;j++){
        hinges[j].forEach(function(hb){
          if(!hingeKindsMate(ha.kind,hb.kind))return;
          if(Math.abs(dot3(ha.dir,hb.dir))<=0.99)return;
          var hbEnd=add3(hb.pos,hb.dir),d=pointLineDist(ha.pos,hb.pos,hbEnd);
          if(d.dist<0.5){hingeConn++;adj[i][j]=1;adj[j][i]=1;matedPairs[i+','+j]=1;}
        });
      }
    });
  }
  var axleConn=0;
  for(i=0;i<n;i++){
    axles[i].forEach(function(ax){
      var vs=[ax.b[0]-ax.a[0],ax.b[1]-ax.a[1],ax.b[2]-ax.a[2]];
      var ls=Math.hypot(vs[0],vs[1],vs[2]);
      if(ls<1e-6)return;
      var us=[vs[0]/ls,vs[1]/ls,vs[2]/ls];
      for(j=0;j<n;j++){
        if(i===j)continue;
        holeSegsWorld[j].forEach(function(seg){
          var vh=[seg.b[0]-seg.a[0],seg.b[1]-seg.a[1],seg.b[2]-seg.a[2]];
          var lh=Math.hypot(vh[0],vh[1],vh[2]);
          if(lh<1e-6)return;
          var uh=[vh[0]/lh,vh[1]/lh,vh[2]/lh];
          if(Math.abs(dot3(us,uh))<=0.99)return;
          var d1=pointLineDist(seg.a,ax.a,ax.b),d2=pointLineDist(seg.b,ax.a,ax.b);
          if(d1.dist>=0.5||d2.dist>=0.5)return;
          var ta=(seg.a[0]-ax.a[0])*us[0]+(seg.a[1]-ax.a[1])*us[1]+(seg.a[2]-ax.a[2])*us[2];
          var tb=(seg.b[0]-ax.a[0])*us[0]+(seg.b[1]-ax.a[1])*us[1]+(seg.b[2]-ax.a[2])*us[2];
          var tmin=Math.min(ta,tb),tmax=Math.max(ta,tb);
          var oStart=Math.max(tmin,0),oEnd=Math.min(tmax,ls);
          if(oEnd-oStart>=1.0){
            axleConn++;
            adj[i][j]=1;
            adj[j][i]=1;
            matedPairs[Math.min(i,j)+','+Math.max(i,j)]=1;
          }
        });
      }
    });
  }
  var clipConn=0;
  for(i=0;i<n;i++){
    clips[i].forEach(function(c){
      var lc=Math.hypot(c.dir[0],c.dir[1],c.dir[2]);
      if(lc<1e-6)return;
      var uc=[c.dir[0]/lc,c.dir[1]/lc,c.dir[2]/lc];
      for(j=0;j<n;j++){
        if(i===j)continue;
        bars[j].forEach(function(bar){
          var vb=[bar.b[0]-bar.a[0],bar.b[1]-bar.a[1],bar.b[2]-bar.a[2]];
          var lb=Math.hypot(vb[0],vb[1],vb[2]);
          if(lb<1e-6)return;
          var ub=[vb[0]/lb,vb[1]/lb,vb[2]/lb];
          if(Math.abs(dot3(uc,ub))<=0.99)return;
          var pld=pointLineDist(c.pos,bar.a,bar.b);
          if(pld.dist>=0.5)return;
          var tDist=pld.t*lb;
          if(tDist>=-2.0&&tDist<=lb+2.0){
            clipConn++;
            adj[i][j]=1;
            adj[j][i]=1;
            matedPairs[Math.min(i,j)+','+Math.max(i,j)]=1;
          }
        });
      }
    });
  }
  // Towball<->ball-socket mating: point-vs-point distance only, wider tolerance than pin/hole/hinge
  // since these positions carry real, disclosed fit uncertainty -- see CURATED_BALL_SOCKETS's own comment.
  var towballConn=0;
  for(i=0;i<n;i++){
    towballs[i].forEach(function(t){
      for(j=0;j<n;j++){
        if(i===j)continue;
        ballSockets[j].forEach(function(s){
          if(dist3(t.pos,s.pos)<BALL_SOCKET_MATCH_TOL){
            towballConn++;
            adj[i][j]=1;
            adj[j][i]=1;
            matedPairs[Math.min(i,j)+','+Math.max(i,j)]=1;
          }
        });
      }
    });
  }
  var seen={},queue=Object.keys(baseAdj).map(Number);
  queue.forEach(function(k){seen[k]=1;});
  while(queue.length){var c=queue.pop();for(var nb in adj[c])if(!seen[nb]){seen[nb]=1;queue.push(+nb);}}
  var floating=[];
  for(i=0;i<n;i++)if(!seen[i])floating.push(i);
  var collisions=[];
  for(i=0;i<n;i++){
    if(!boxes[i])continue;
    for(var bi=0;bi<boxes[i].length;bi++){
      var bx=boxes[i][bi],yMax=Array.isArray(bx)?bx[3]:bx.aabb[3];
      if(yMax>0.5){collisions.push([-1,i]);break;}
    }
  }
  // Part-vs-part boxes: coarse 80-LDU grid over each part's overall AABB, test only parts sharing a cell (all-pairs
  // was O(n^2) box-list scans); pairs are deduped and emitted in the same (i asc, j asc) order as before.
  // Grid bucketing always uses each box's aabb (an OBB object's world-aligned bounding aabb, same shape as a
  // plain AABB) -- the broadphase only needs to be conservative, the SAT in boxesOverlap does the real test.
  var grid={},pairSeen={},pairs=[];
  for(i=0;i<n;i++){
    if(!boxes[i])continue;
    var lo=[1e9,1e9,1e9],hi=[-1e9,-1e9,-1e9];
    boxes[i].forEach(function(b){var ab=Array.isArray(b)?b:b.aabb;for(var ax=0;ax<3;ax++){lo[ax]=Math.min(lo[ax],ab[ax*2]);hi[ax]=Math.max(hi[ax],ab[ax*2+1]);}});
    for(var gx=Math.floor(lo[0]/80);gx<=Math.floor(hi[0]/80);gx++)for(var gy=Math.floor(lo[1]/80);gy<=Math.floor(hi[1]/80);gy++)
      for(var gz=Math.floor(lo[2]/80);gz<=Math.floor(hi[2]/80);gz++){
        var gk=gx+','+gy+','+gz,cellp=grid[gk]=grid[gk]||[];
        cellp.forEach(function(o){var pk=o+','+i;if(!pairSeen[pk]){pairSeen[pk]=1;pairs.push([o,i]);}});
        cellp.push(i);
      }
  }
  pairs.sort(function(a,b){return a[0]-b[0]||a[1]-b[1];});
  pairs.forEach(function(pr){
    if(matedPairs[pr[0]+','+pr[1]])return;
    var bi2=boxes[pr[0]],bj2=boxes[pr[1]],hit=false;
    for(var a=0;a<bi2.length&&!hit;a++)for(var b=0;b<bj2.length;b++)if(boxesOverlap(bi2[a],bj2[b])){hit=true;break;}
    if(hit)collisions.push([pr[0],pr[1]]);
  });
  var restIdx=Object.keys(baseAdj).map(Number),balance='none',margin=null;
  if(restIdx.length){
    var m2=0,cx=0,cz=0,foot=[];
    for(i=0;i<n;i++)if(boxes[i])boxes[i].forEach(function(b){
      if(Array.isArray(b)){
        var vol=(b[1]-b[0])*(b[3]-b[2])*(b[5]-b[4]),cxb=(b[0]+b[1])/2,czb=(b[4]+b[5])/2;
        m2+=vol;cx+=cxb*vol;cz+=czb*vol;
      }else{
        var e=b.extents,vol2=8.0*e[0]*e[1]*e[2];
        m2+=vol2;cx+=b.center[0]*vol2;cz+=b.center[2]*vol2;
      }
    });
    cx/=m2;cz/=m2;
    restIdx.forEach(function(k){if(boxes[k])boxes[k].forEach(function(b){
      var ab=Array.isArray(b)?b:b.aabb;
      foot.push([ab[0],ab[4]],[ab[1],ab[4]],[ab[1],ab[5]],[ab[0],ab[5]]);
    });});
    var hp=hull2(foot);
    margin=1e9;
    for(i=0;i<hp.length;i++){var pa=hp[i],pb=hp[(i+1)%hp.length];
      margin=Math.min(margin,((pb[0]-pa[0])*(cz-pa[1])-(pb[1]-pa[1])*(cx-pa[0]))/Math.hypot(pb[0]-pa[0],pb[1]-pa[1]));}
    margin/=20;
    balance=margin<0?'fail':margin<0.5?'warn':'pass';
  }
  var np=collisions.filter(function(c){return c[0]!==-1;}).length;
  var checks=[
    {id:'collisions',label:'No collisions',status:np?'fail':'pass',
      detail:(np?np+' part pair'+(np>1?'s':'')+' overlap':'0 overlaps')+(notChecked?' ('+notChecked+' part'+(notChecked>1?'s':'')+' not checked, no occupancy data yet)':'')},
    {id:'anchored',label:'Every part anchored',status:floating.length?'fail':'pass',
      detail:floating.length?floating.length+' part'+(floating.length>1?'s':'')+' not connected to the baseplate':'all '+n+' parts reach the baseplate'},
    {id:'connections',label:'Stud + pin + hinge connections',status:(studConn+pinConn+hingeConn+axleConn+clipConn+towballConn)?'pass':'fail',
      detail:studConn+' stud + '+pinConn+' pin + '+hingeConn+' hinge'+(axleConn?' + '+axleConn+' axle':'')+(clipConn?' + '+clipConn+' clip':'')+(towballConn?' + '+towballConn+' towball':'')},
    {id:'balance',label:'Centre of mass over footprint',status:balance==='none'?'fail':balance,
      detail:balance==='none'?'no part rests on the baseplate to measure':
        '('+ (margin!==null?'margin '+Math.abs(margin).toFixed(2):'')+' studs'+(balance==='fail'?', outside footprint':'')+')'}
  ];
  return {ok:checks.every(function(c){return c.status!=='fail';}),checks:checks,connections:studConn+pinConn+hingeConn+axleConn+clipConn+towballConn,
    studConnections:studConn,pinConnections:pinConn,hingeConnections:hingeConn,axleConnections:axleConn,clipConnections:clipConn,towballConnections:towballConn,collisions:collisions,
    overlaps:np,floating:floating,balance:balance,com:{margin:margin},parts:[],cost:0};
}
